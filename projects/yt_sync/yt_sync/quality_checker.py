# yt_sync/quality_checker.py - Check video quality and identify upgrade candidates

import json
import logging
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any

from . import utils

logger = logging.getLogger(__name__)


class VideoQualityChecker:
    """Analyzes video files and identifies candidates for quality upgrades."""

    def __init__(self, args: Any, target_dir: Path, archive_file: Path):
        self.args = args
        self.target_dir = target_dir
        self.archive_file = archive_file
        self.quality_config = getattr(args, "quality_management", {})
        self.minimum_height = self.quality_config.get("minimum_height", 720)
        self.upgrade_batch_size = self.quality_config.get("upgrade_batch_size", 10)
        self.enable_upgrade = self.quality_config.get("enable_quality_upgrade", False)

    def check_for_upgrade_candidates(
        self, video_ids: set[str]
    ) -> tuple[list[str], list[Path]]:
        """
        Check existing video files for quality and return video IDs that could be upgraded.
        A file is considered a candidate if it is below the minimum resolution OR if it is
        unreadable/corrupted (i.e., ffprobe fails).
        """
        if not self.enable_upgrade:
            logger.debug("Quality upgrade checking is disabled in config.")
            return [], []

        if not self._is_ffprobe_available():
            logger.warning(
                "ffprobe not found in PATH. Disabling quality upgrade feature for this run."
            )
            self.enable_upgrade = False
            return [], []

        logger.info(
            f"🔍 Checking existing videos for quality upgrade opportunities (target: {self.minimum_height}p+ or corrupted)..."
        )

        video_files = utils.get_video_files_in_dir(self.target_dir)
        if not video_files:
            return [], []

        upgrade_candidates = []
        unparsable_files = []
        checked_count = 0
        low_quality_count = 0

        for video_file in video_files:
            video_id = utils.get_id_from_filename(video_file.name)
            if not video_id:
                unparsable_files.append(video_file)
                continue
            if video_id not in video_ids:
                continue
            checked_count += 1
            quality_info = self._get_video_quality(video_file)
            if quality_info is None:
                low_quality_count += 1
                upgrade_candidates.append(video_id)
                # Log the filename if ID is missing, otherwise log the ID.
                logger.warning(
                    f"🚨 Corrupted/unreadable file found: [{video_id or video_file.name}] - Queued for re-download."
                )
            elif quality_info["height"] < self.minimum_height:
                low_quality_count += 1
                upgrade_candidates.append(video_id)
                logger.info(
                    f"📱 Low quality found: [{video_id}] {quality_info['height']}p - Queued for upgrade."
                )

        if upgrade_candidates:
            logger.info(
                f"📊 Quality analysis: {checked_count} videos checked, {low_quality_count} are low-quality or corrupted."
            )
            logger.info(
                f"🔄 Found {len(upgrade_candidates)} videos for replacement/upgrade."
            )
        elif checked_count > 0:
            logger.info(
                f"✅ All {checked_count} checked videos meet quality standards ({self.minimum_height}p+)."
            )

        return upgrade_candidates, unparsable_files

    def _is_ffprobe_available(self) -> bool:
        """Checks if ffprobe is in the system's PATH."""
        return shutil.which("ffprobe") is not None

    def _find_video_file_by_id(self, video_id: str) -> Path | None:
        """Find video file by video ID."""
        video_files = utils.get_video_files_in_dir(self.target_dir)
        for video_file in video_files:
            if utils.get_id_from_filename(video_file.name) == video_id:
                return video_file
        return None

    def _get_video_quality(self, video_file: Path) -> dict[str, Any] | None:
        """
        Get video quality information using ffprobe.
        Returns a dictionary on success, or None on failure (indicating a corrupted file).
        """
        try:
            if video_file.stat().st_size <= 1024:  # Less than or equal to 1 KB
                raise ValueError("File size is too small to be a valid video.")

            cmd = [
                "ffprobe",
                "-v",
                "quiet",
                "-print_format",
                "json",
                "-show_streams",
                "-select_streams",
                "v:0",
                str(video_file),
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=True,
                encoding="utf-8",
            )
            data = json.loads(result.stdout)
            stream = data.get("streams", [{}])[0]

            height = stream.get("height")
            if not isinstance(height, int):
                raise ValueError("Could not parse video height from ffprobe output.")

            return {
                "width": stream.get("width", 0),
                "height": height,
            }
        except (
            subprocess.TimeoutExpired,
            subprocess.CalledProcessError,
            json.JSONDecodeError,
            IndexError,
            ValueError,
        ) as e:
            logger.debug(
                f"Could not analyze {video_file.name} with ffprobe, likely corrupted: {e}"
            )
            return None

    def prepare_for_upgrade(self, upgrade_candidates: list[str]) -> None:
        """Prepares video files for upgrade by backing them up and removing from archive."""
        if not upgrade_candidates:
            return

        logger.info(
            f"🔄 Preparing {len(upgrade_candidates)} videos for replacement/upgrade..."
        )

        if self._remove_from_archive(upgrade_candidates):
            logger.info(
                f"✅ Removed {len(upgrade_candidates)} videos from download archive to allow re-download."
            )

        if self.quality_config.get("backup_old_files", True):
            self._backup_old_files(upgrade_candidates)
        else:
            self._delete_old_files(upgrade_candidates)

    def _remove_from_archive(self, video_ids_to_remove: list[str]) -> bool:
        """Remove video IDs from the download archive file."""
        if not self.archive_file.exists():
            return False

        try:
            with open(self.archive_file, encoding="utf-8") as f:
                lines = f.readlines()

            video_ids_set = set(video_ids_to_remove)
            with open(self.archive_file, "w", encoding="utf-8") as f:
                for line in lines:
                    line_stripped = line.strip()
                    if line_stripped and not any(
                        vid_id in line_stripped for vid_id in video_ids_set
                    ):
                        f.write(line)
            return True
        except Exception as e:
            logger.error(f"Failed to update download archive: {e}")
            return False

    def _backup_old_files(self, video_ids: list[str]) -> None:
        """
        Backup old low-quality files, handling cases where backup already exists.
        """
        backup_dir = self.target_dir / "_quality_backups"
        backup_dir.mkdir(exist_ok=True)

        for video_id in video_ids:
            video_file = self._find_video_file_by_id(video_id)
            if not (video_file and video_file.exists()):
                continue

            destination_path = backup_dir / video_file.name

            try:
                if destination_path.exists():
                    # If backup already exists, the previous attempt was successful.
                    # Just delete the local source file to clear the way for a new download.
                    logger.warning(
                        f"Backup for '{video_file.name}' already exists. Deleting local low-quality copy."
                    )
                    video_file.unlink()
                else:
                    # Otherwise, perform the backup move as normal.
                    shutil.move(str(video_file), str(backup_dir))
                    logger.debug(
                        f"📦 Backed up: {video_file.name} to {backup_dir.name}"
                    )
            except Exception as e:
                # Catch any error during the file operation
                logger.error(f"Failed to process old file {video_file.name}: {e}")

    def _delete_old_files(self, video_ids: list[str]) -> None:
        """Deletes old low-quality files before upgrade."""
        for video_id in video_ids:
            video_file = self._find_video_file_by_id(video_id)
            if video_file and video_file.exists():
                try:
                    video_file.unlink()
                    logger.debug(f"🗑️ Deleted old file: {video_file.name}")
                except Exception as e:
                    logger.error(f"Failed to delete {video_file.name}: {e}")


class TempFileCleaner:
    """Cleans up temporary files left by failed or interrupted yt-dlp runs."""

    def __init__(self, target_dir: Path):
        self.target_dir = target_dir
        self.temp_file_regex = re.compile(r"\.f\d{1,4}\.\w+$")

    def cleanup(self) -> int:
        """Finds and deletes temporary download files."""
        cleaned_count = 0
        logger.debug(f"Scanning '{self.target_dir}' for leftover temporary files...")

        try:
            for f_path in self.target_dir.iterdir():
                if f_path.is_file() and self.temp_file_regex.search(f_path.name):
                    try:
                        f_path.unlink()
                        cleaned_count += 1
                        # --- LOGGING CHANGE ---
                        # Changed from .warning to .debug to keep console clean
                        logger.debug(
                            f"🧹 Cleaned up leftover temporary file: {f_path.name}"
                        )
                    except OSError as e:
                        logger.error(
                            f"Failed to delete temporary file {f_path.name}: {e}"
                        )
        except OSError as e:
            logger.error(f"Could not scan directory for temporary files: {e}")

        if cleaned_count > 0:
            logger.info(f"🧹 Cleaned up {cleaned_count} leftover temporary file(s).")

        return cleaned_count
