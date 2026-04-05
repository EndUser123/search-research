# yt_sync/reconciler.py

import logging
import re
from pathlib import Path
from typing import Any

from . import utils
from .discovery import VideoDiscoverer
from .filtering import VideoFilterer
from .metadata import MetadataManager

logger = logging.getLogger(__name__)

FLEXIBLE_ID_REGEX = re.compile(r"([a-zA-Z0-9_-]{11})")


class LibraryReconciler:
    """
    Handles higher-level logic for reconciling the library against changing business rules
    (like filters) and repairing metadata-dependent issues like filenames.
    """

    def __init__(
        self,
        args: Any,
        target_dir: Path,
        archive_file: Path,
        metadata_manager: MetadataManager,
        filterer: VideoFilterer,
        discoverer: VideoDiscoverer,
        uploads_playlist_id: str | None,
    ):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file
        self.metadata_manager = metadata_manager
        self.filterer = filterer
        self.discoverer = discoverer
        self.uploads_playlist_id = uploads_playlist_id

    def run_reconciliation_audit(
        self, archived_ids: set[str], unmanaged_files: list[Path]
    ):
        """Runs all reconciliation steps intended for a full audit."""
        logger.info("\n--- Starting Library Reconciliation ---")
        if self.args.audit_filters:
            self.reconcile_filters(archived_ids)
        if self.args.import_and_fix:
            self.fix_unmanaged_files(unmanaged_files)
        logger.info("--- Reconciliation Complete ---")

    def reconcile_filters(self, archived_ids: set[str]):
        """
        Checks archived videos against current filter rules to find mismatches.
        This was formerly _audit_filter_mismatches in the Auditor.
        """
        if not archived_ids:
            logger.info(
                "🔎 Skipping filter reconciliation: No videos are in the archive."
            )
            return

        logger.info(
            f"\n--- Checking {len(archived_ids)} archived videos against current filters ---"
        )

        archived_metadata = self.metadata_manager.load_metadata_for_ids(
            list(archived_ids)
        )

        successful_ids = set(archived_metadata.keys())
        if len(archived_ids) > len(successful_ids):
            logger.warning(
                f"Could not fetch metadata for {len(archived_ids) - len(successful_ids)} archived videos."
            )

        if not self.filterer.rules:
            logger.info("✅ No filter rules are defined; skipping check.")
            return

        passed_filter_ids = self.filterer.apply_filters(
            successful_ids, archived_metadata
        )
        mismatched_ids = successful_ids - passed_filter_ids

        if mismatched_ids:
            logger.warning(
                f"Found {len(mismatched_ids)} Filter Mismatches (archived, but no longer match current rules):"
            )
            for vid_id in sorted(list(mismatched_ids)):
                logger.warning(f"  - MISMATCH: {vid_id}")
        else:
            logger.info("✅ No filter mismatches found.")

    def fix_unmanaged_files(self, files_to_fix: list[Path]):
        """
        Attempts to find IDs, rename, and import a list of files.
        This was formerly _fix_unmanaged_files in the Auditor.
        """
        if not files_to_fix:
            return

        logger.info(
            f"\n--- FIX & IMPORT: Attempting to process {len(files_to_fix)} unmanaged files ---"
        )
        fixed_count = 0

        all_channel_ids = self.discoverer.get_all_channel_video_ids(
            self.uploads_playlist_id
        )
        if not all_channel_ids:
            logger.error(
                "Cannot run fix process: failed to get a definitive list of channel videos."
            )
            return

        for f_path in files_to_fix:
            potential_ids = FLEXIBLE_ID_REGEX.findall(f_path.name)
            found_id = next(
                (pid for pid in potential_ids if pid in all_channel_ids), None
            )

            if not found_id:
                logger.warning(
                    f"  - ❌ Could not find a valid channel ID in: {f_path.name}"
                )
                continue

            logger.info(
                f"  - 🔎 Found valid ID '{found_id}' in '{f_path.name}'. Fetching metadata..."
            )
            metadata = self.metadata_manager.load_metadata_for_ids([found_id])
            if not metadata.get(found_id):
                logger.error(
                    f"  - ❌ Failed to fetch metadata for {found_id}. Skipping."
                )
                continue

            sanitized_title = utils.sanitize_filename(
                metadata[found_id].get("title", "Unknown Title")
            )
            new_filename = f"{sanitized_title} [{found_id}]{f_path.suffix}"
            new_path = self.target_dir / new_filename

            counter = 1
            while new_path.exists():
                new_filename = (
                    f"{sanitized_title} [{found_id}]_{counter}{f_path.suffix}"
                )
                new_path = self.target_dir / new_filename
                counter += 1

            try:
                f_path.rename(new_path)
                logger.info(f"  - ✅ Renamed to: {new_filename}")
                with open(self.archive_file, "a", encoding="utf-8") as f:
                    f.write(f"youtube {found_id}\n")
                logger.info(f"  - ✅ Added '{found_id}' to archive.")
                fixed_count += 1
            except OSError as e:
                logger.error(f"  - ❌ Failed to rename or archive file: {e}")

        logger.info(
            f"--- FIX & IMPORT COMPLETE: Successfully processed {fixed_count} of {len(files_to_fix)} files. ---"
        )
