# yt_sync/auditing.py

import logging
from collections import defaultdict
from pathlib import Path
from typing import Any

from . import utils

logger = logging.getLogger(__name__)


class Auditor:
    """Handles all --audit mode logic for the filesystem and archive file."""

    def __init__(
        self,
        args: Any,
        target_dir: Path,
        archive_file: Path,
        metadata_manager=None,
        filterer=None,
        discoverer=None,
        uploads_playlist_id=None,
    ):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file
        self.metadata_manager = metadata_manager
        self.filterer = filterer
        self.discoverer = discoverer
        self.uploads_playlist_id = uploads_playlist_id

    def find_and_remove_ghost_entries(self) -> int:
        """
        Finds entries in the archive file that do not have a corresponding video file on disk
        and removes them. This self-heals the archive from deletions or cleanup.
        Returns the number of ghost entries removed.
        """
        logger.debug(
            "Checking for ghost entries in the archive (archived but not on disk)..."
        )
        archived_ids = self.read_archive_file()
        if not archived_ids:
            return 0

        video_files = utils.get_video_files_in_dir(self.target_dir)
        disk_ids = {
            utils.get_id_from_filename(f.name)
            for f in video_files
            if utils.get_id_from_filename(f.name)
        }

        ghost_ids = archived_ids - disk_ids

        if not ghost_ids:
            return 0

        logger.warning(
            f"👻 Found {len(ghost_ids)} ghost entries in the archive that are missing on disk. Removing them..."
        )
        for gid in list(ghost_ids)[:10]:
            logger.info(f"  - Removing ghost entry: {gid}")

        new_archive_ids = archived_ids - ghost_ids

        try:
            with open(self.archive_file, "w", encoding="utf-8") as f:
                for vid_id in sorted(list(new_archive_ids)):
                    f.write(f"youtube {vid_id}\n")
            logger.info(
                f"✅ Successfully removed {len(ghost_ids)} ghost entries from the archive file."
            )
            return len(ghost_ids)
        except OSError as e:
            logger.error(f"Failed to rewrite archive file to remove ghosts: {e}")
            return 0

    def auto_import_existing_files(self) -> int:
        """
        Scans for video files in the target directory that are not in the archive,
        verifies them, and adds them to the archive. Returns the count of imported files.
        """
        logger.debug("Checking for existing, unarchived files to auto-import...")
        try:
            archived_ids = self.read_archive_file()
            logger.info(f"🔎 Scanning for existing files in: {self.target_dir}")
            video_files = utils.get_video_files_in_dir(self.target_dir)

            # Filter out test files
            video_files = [f for f in video_files if not f.name.startswith("test_")]
            logger.info(
                f"  - Found {len(video_files)} video file(s) on disk (excluding test files)."
            )

            if video_files:
                filenames_to_log = [p.name for p in video_files[:10]]
                log_msg = f"  - Files found by Python: {filenames_to_log}"
                if len(video_files) > 10:
                    log_msg += f" ... and {len(video_files) - 10} more."
                logger.debug(log_msg)

            files_to_import = []
            for f_path in video_files:
                vid_id = utils.get_id_from_filename(f_path.name)
                if vid_id and vid_id not in archived_ids and f_path.stat().st_size > 0:
                    files_to_import.append(vid_id)

            if not files_to_import:
                return 0

            logger.info(
                f"Found {len(files_to_import)} existing video files not in the archive. Auto-importing..."
            )
            with open(self.archive_file, "a", encoding="utf-8") as f:
                for vid_id in files_to_import:
                    f.write(f"youtube {vid_id}\n")
            logger.info(
                f"✅ Successfully imported {len(files_to_import)} videos into the archive file."
            )
            return len(files_to_import)
        except Exception as e:
            logger.error(f"Failed during auto-import process: {e}")
            return 0

    def run_file_system_audit(self) -> tuple[set[str], list[Path]]:
        """
        Performs a full audit of the filesystem against the archive file.
        Returns the set of archived IDs and a list of unmanaged files for reconciliation.
        """
        logger.info(f"--- Starting File System Audit for {self.target_dir.name} ---")

        logger.info(f"🔎 Scanning directory: {self.target_dir}")
        video_files = utils.get_video_files_in_dir(self.target_dir)
        logger.info(f"  - Found {len(video_files)} video file(s) on disk.")

        local_files_by_id = defaultdict(list)
        files_without_id = []
        for f_path in video_files:
            vid_id = utils.get_id_from_filename(f_path.name)
            if vid_id:
                local_files_by_id[vid_id].append(f_path)
            else:
                files_without_id.append(f_path)

        local_ids_on_disk = set(local_files_by_id.keys())
        archived_ids = self.read_archive_file()

        logger.info(
            f"Found {len(video_files)} video files and {len(archived_ids)} archive entries."
        )

        orphaned_ids = local_ids_on_disk - archived_ids
        ghost_ids = archived_ids - local_ids_on_disk
        duplicate_ids = {
            vid_id for vid_id, files in local_files_by_id.items() if len(files) > 1
        }

        if files_without_id:
            logger.warning(
                f"Found {len(files_without_id)} video files with no parsable [ID]:"
            )
            for f in sorted(files_without_id)[:10]:
                logger.warning(f"  - UNPARSABLE: {f.name}")
        if orphaned_ids:
            logger.warning(
                f"Found {len(orphaned_ids)} Orphaned Video ID(s) (on disk, not in archive):"
            )
            for vid_id in sorted(list(orphaned_ids))[:10]:
                for f in local_files_by_id[vid_id]:
                    logger.warning(f"  - ORPHAN: {f.name}")
        if ghost_ids:
            logger.warning(
                f"Found {len(ghost_ids)} Ghost Entries (in archive, but file is missing):"
            )
            for vid_id in sorted(list(ghost_ids))[:10]:
                logger.warning(f"  - GHOST:  {vid_id}")
        if duplicate_ids:
            logger.warning(
                f"Found {len(duplicate_ids)} Video ID(s) with Duplicate Files:"
            )
            for vid_id in sorted(list(duplicate_ids))[:10]:
                logger.warning(
                    f"  - DUPLICATE ID '{vid_id}' has {len(local_files_by_id[vid_id])} files:"
                )
                for i, f_path in enumerate(local_files_by_id[vid_id], 1):
                    logger.warning(f"      {i}. {f_path.name}")

        if not any([orphaned_ids, ghost_ids, duplicate_ids, files_without_id]):
            logger.info(
                "✅ No orphans, ghosts, duplicates, or unparsable files found. Library is consistent."
            )

        logger.info("--- File System Audit Complete ---")
        unmanaged_files = files_without_id + [
            f for vid in orphaned_ids for f in local_files_by_id[vid]
        ]
        return archived_ids, unmanaged_files

    def read_archive_file(self) -> set[str]:
        """Read video IDs from the archive file."""
        if not self.archive_file.is_file():
            return set()

        try:
            with open(self.archive_file, encoding="utf-8") as f:
                video_ids = set()
                for line in f:
                    line = line.strip()
                    if line and " " in line:
                        parts = line.split(" ", 1)
                        if len(parts) >= 2:
                            video_ids.add(parts[1])
                return video_ids
        except Exception as e:
            logger.error(f"Error reading archive file {self.archive_file}: {e}")
            return set()

    def run_audit(self) -> dict:
        """
        Run full audit process including:
        - File system audit
        - Filter mismatches check
        - Fixing unmanaged files
        Returns audit results summary.
        """
        results = {"file_system": {}, "filter_mismatches": {}, "unmanaged_files": {}}

        # Run file system audit
        archived_ids, unmanaged_files = self.run_file_system_audit()
        results["file_system"]["archived_ids"] = archived_ids
        results["file_system"]["unmanaged_files"] = unmanaged_files

        # Check for filter mismatches (only if API available and not in local-only mode)
        if not getattr(self.args, "local_audit", False):
            try:
                filter_results = self._audit_filter_mismatches(archived_ids)
                results["filter_mismatches"] = filter_results
            except Exception as e:
                logger.warning(f"Skipping filter mismatch checks due to API error: {e}")
                results["filter_mismatches"] = {"status": "skipped_due_to_api_error"}
        else:
            logger.info("Running in local-only audit mode - skipping API checks")
            results["filter_mismatches"] = {"status": "local_only_mode"}

        # Fix unmanaged files if any
        if unmanaged_files:
            fix_results = self._fix_unmanaged_files(unmanaged_files)
            results["unmanaged_files"] = fix_results

        return results

    def _audit_filter_mismatches(self, video_ids: set[str]) -> dict:
        """
        Check for videos that pass filters but aren't in archive,
        or are in archive but shouldn't pass filters.
        Returns dict with mismatch counts and details.
        """
        if not self.filterer:
            return {"status": "no_filterer_configured"}

        results = {
            "in_archive_but_filtered": set(),
            "passed_filters_but_missing": set(),
            "errors": [],
        }

        # Check which videos in archive shouldn't be there according to filters
        for vid_id in video_ids:
            if not self.filterer.should_include(vid_id):
                results["in_archive_but_filtered"].add(vid_id)
                logger.warning(f"  - MISMATCH: {vid_id}")

        # Check which videos pass filters but aren't in archive
        if self.uploads_playlist_id and self.discoverer:
            try:
                all_uploaded = self.discoverer.get_video_ids_from_playlist(
                    self.uploads_playlist_id
                )
                for vid_id in all_uploaded:
                    if vid_id not in video_ids and self.filterer.should_include(vid_id):
                        results["passed_filters_but_missing"].add(vid_id)
                        logger.warning(f"  - MISSING: {vid_id}")
            except Exception as e:
                error_msg = f"Error checking filter mismatches: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)

        return {
            "counts": {
                "in_archive_but_filtered": len(results["in_archive_but_filtered"]),
                "passed_filters_but_missing": len(
                    results["passed_filters_but_missing"]
                ),
            },
            "details": results,
        }

    def _fix_unmanaged_files(self, unmanaged_files: list[Path]) -> dict:
        """
        Handle unmanaged files (those without IDs or not in archive).
        Options: delete, move to quarantine, or add to archive if ID can be parsed.
        Returns dict with action counts.
        """
        if not unmanaged_files:
            return {"status": "no_unmanaged_files"}

        results = {"deleted": 0, "quarantined": 0, "added_to_archive": 0}

        for file_path in unmanaged_files:
            try:
                vid_id = utils.get_id_from_filename(file_path.name)
                if vid_id:
                    # Try to add to archive if we can parse an ID
                    with open(self.archive_file, "a", encoding="utf-8") as f:
                        f.write(f"youtube {vid_id}\n")
                    results["added_to_archive"] += 1
                else:
                    # No ID - quarantine or delete based on config
                    if self.args.quarantine_unmanaged:
                        quarantine_dir = self.target_dir / "quarantine"
                        quarantine_dir.mkdir(exist_ok=True)
                        new_path = quarantine_dir / file_path.name
                        file_path.rename(new_path)
                        results["quarantined"] += 1
                    else:
                        file_path.unlink()
                        results["deleted"] += 1
            except Exception as e:
                logger.error(f"Error handling unmanaged file {file_path}: {e}")

        return results
