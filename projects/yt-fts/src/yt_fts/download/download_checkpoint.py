"""
Download Checkpoint and Resume Feature

Tracks downloaded video IDs in a cache file to allow resuming
interrupted downloads without re-downloading already completed videos.
"""
from __future__ import annotations

import csv
import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from .thread_safe_manager import ThreadSafeManager
from typing import Any

from rich.console import Console


class CheckpointStatus(Enum):
    """Status codes for checkpoint operations."""
    SUCCESS = "success"
    NOT_FOUND = "not_found"
    WRITE_ERROR = "write_error"
    READ_ERROR = "read_error"
    ALREADY_DOWNLOADED = "already_downloaded"
    NEW_DOWNLOAD = "new_download"


@dataclass(slots=True)
class CheckpointEntry:
    """
    Single checkpoint entry representing a downloaded video.

    Attributes:
        video_id: YouTube video ID
        channel_id: Channel the video belongs to
        timestamp: When the video was downloaded (ISO format string)
        success: Whether download was successful
        error_message: Error message if download failed
    """
    video_id: str
    channel_id: str
    timestamp: str
    success: bool = True
    error_message: str | None = None


@dataclass(slots=True)
class CheckpointResult:
    """Result of a checkpoint lookup or write operation."""
    status: CheckpointStatus
    message: str
    entry: CheckpointEntry | None = None
    total_downloaded: int = 0  # Total videos in checkpoint for this channel


class DownloadCheckpoint:
    """
    Manages download checkpoint cache for resume capability.

    Tracks which videos have been successfully downloaded to avoid
    re-downloading on subsequent runs.

    Usage:
        checkpoint = DownloadCheckpoint(console=console)

        # Check if video was already downloaded
        result = checkpoint.check_video(video_id="abc123", channel_id="UCxxxx")
        if result.status == CheckpointStatus.ALREADY_DOWNLOADED:
            print(f"Video {result.entry.video_id} already downloaded at {result.entry.timestamp}")
            # Skip download
        else:
            # Download video
            # ...
            # Mark as downloaded
            checkpoint.mark_downloaded(video_id="abc123", channel_id="UCxxxx")

        # Get summary at end
        summary = checkpoint.get_summary(channel_id="UCxxxx")
    """

    DEFAULT_CHECKPOINT_DIR = Path.home() / ".config" / "yt-fts" / "checkpoints"
    CHECKPOINT_FILE = "download_cache.json"

    def __init__(
        self,
        checkpoint_dir: Path | None = None,
        console: Console | None = None,
        auto_save: bool = True,
    ) -> None:
        """
        Initialize download checkpoint manager.

        Args:
            checkpoint_dir: Directory to store checkpoint files (default: ~/.config/yt-fts/checkpoints)
            console: Optional Console instance for output
            auto_save: Whether to automatically save after each mark_downloaded call
        """
        self.console = console or Console()
        self.logger = logging.getLogger(__name__)
        self.auto_save = auto_save

        # Set checkpoint directory
        if checkpoint_dir is None:
            checkpoint_dir = self.DEFAULT_CHECKPOINT_DIR

        self.checkpoint_dir = Path(checkpoint_dir)
        self.checkpoint_file = self.checkpoint_dir / self.CHECKPOINT_FILE

        # Thread-safe lock for file operations
        self._tsm = ThreadSafeManager()

        # In-memory cache: {channel_id: {video_id: CheckpointEntry}}
        self._cache: dict[str, dict[str, CheckpointEntry]] = {}

        # Load existing checkpoint
        self._load_checkpoint()

    def _load_checkpoint(self) -> None:
        """Load checkpoint data from file."""
        if not self.checkpoint_file.exists():
            self.logger.debug("Checkpoint file not found, starting fresh")
            return

        try:
            with self.checkpoint_file.open(encoding="utf-8") as f:
                data = json.load(f)

            # Reconstruct checkpoint entries
            for channel_id, videos in data.items():
                self._cache[channel_id] = {}
                for video_id, entry_data in videos.items():
                    self._cache[channel_id][video_id] = CheckpointEntry(
                        video_id=entry_data["video_id"],
                        channel_id=entry_data["channel_id"],
                        timestamp=entry_data["timestamp"],
                        success=entry_data.get("success", True),
                        error_message=entry_data.get("error_message"),
                    )

            total_videos = sum(len(videos) for videos in self._cache.values())
            self.logger.debug("Loaded checkpoint with %s videos across %s channels", total_videos, len(self._cache))

        except (OSError, json.JSONDecodeError):
            self.logger.exception("Failed to load checkpoint")

    def _save_checkpoint(self) -> bool:
        """
        Save checkpoint data to file.

        Returns:
            True if save was successful
        """
        try:
            # Ensure directory exists
            self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

            # Convert to serializable format
            data: dict[str, Any] = {}
            for channel_id, videos in self._cache.items():
                data[channel_id] = {}
                for video_id, entry in videos.items():
                    data[channel_id][video_id] = {
                        "video_id": entry.video_id,
                        "channel_id": entry.channel_id,
                        "timestamp": entry.timestamp,
                        "success": entry.success,
                        "error_message": entry.error_message,
                    }

            # Write to file
            with self.checkpoint_file.open("w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

            return True  # noqa: TRY300

        except (OSError, TypeError):
            self.logger.exception("Failed to save checkpoint")
            return False

    def check_video(
        self,
        video_id: str,
        channel_id: str,
    ) -> CheckpointResult:
        """
        Check if a video has already been downloaded.

        Args:
            video_id: YouTube video ID to check
            channel_id: Channel ID the video belongs to

        Returns:
            CheckpointResult with status and entry if found
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            if channel_id not in self._cache:
                return CheckpointResult(
                    status=CheckpointStatus.NEW_DOWNLOAD,
                    message="Channel not in checkpoint cache",
                    total_downloaded=0,
                )

            channel_cache = self._cache[channel_id]
            if video_id not in channel_cache:
                return CheckpointResult(
                    status=CheckpointStatus.NEW_DOWNLOAD,
                    message="Video not in checkpoint cache",
                    total_downloaded=len(channel_cache),
                )

            entry = channel_cache[video_id]
            return CheckpointResult(
                status=CheckpointStatus.ALREADY_DOWNLOADED,
                message=f"Video downloaded on {entry.timestamp}",
                entry=entry,
                total_downloaded=len(channel_cache),
            )

    def mark_downloaded(
        self,
        video_id: str,
        channel_id: str,
        success: bool = True,
        error_message: str | None = None,
    ) -> CheckpointResult:
        """
        Mark a video as downloaded (or failed).

        Args:
            video_id: YouTube video ID
            channel_id: Channel ID the video belongs to
            success: Whether download was successful
            error_message: Error message if download failed

        Returns:
            CheckpointResult with status
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            # Initialize channel cache if needed
            if channel_id not in self._cache:
                self._cache[channel_id] = {}

            # Create checkpoint entry
            entry = CheckpointEntry(
                video_id=video_id,
                channel_id=channel_id,
                timestamp=datetime.now(timezone.utc).isoformat(),
                success=success,
                error_message=error_message,
            )

            # Store entry
            self._cache[channel_id][video_id] = entry

            # Auto-save if enabled
            if self.auto_save:
                if self._save_checkpoint():
                    return CheckpointResult(
                        status=CheckpointStatus.SUCCESS,
                        message="Video marked as downloaded and checkpoint saved",
                        entry=entry,
                        total_downloaded=len(self._cache[channel_id]),
                    )
                return CheckpointResult(
                    status=CheckpointStatus.WRITE_ERROR,
                    message="Video marked but checkpoint save failed",
                    entry=entry,
                    total_downloaded=len(self._cache[channel_id]),
                )

            return CheckpointResult(
                status=CheckpointStatus.SUCCESS,
                message="Video marked as downloaded",
                entry=entry,
                total_downloaded=len(self._cache[channel_id]),
            )

    def get_downloaded_videos(self, channel_id: str) -> list[str]:
        """
        Get list of video IDs downloaded for a channel.

        Args:
            channel_id: Channel ID to get videos for

        Returns:
            List of video IDs that have been downloaded
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            if channel_id not in self._cache:
                return []
            return list(self._cache[channel_id].keys())

    def get_channel_stats(self, channel_id: str) -> dict[str, int]:
        """
        Get statistics for a channel's downloads.

        Args:
            channel_id: Channel ID to get stats for

        Returns:
            Dict with 'total', 'successful', 'failed' counts
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            if channel_id not in self._cache:
                return {"total": 0, "successful": 0, "failed": 0}

            videos = self._cache[channel_id]
            successful = sum(1 for entry in videos.values() if entry.success)
            failed = len(videos) - successful

            return {
                "total": len(videos),
                "successful": successful,
                "failed": failed,
            }

    def get_summary(self, channel_id: str | None = None) -> str:
        """
        Get a human-readable summary of checkpoint data.

        Args:
            channel_id: Optional channel ID to filter by

        Returns:
            Formatted summary string
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            if channel_id:
                if channel_id not in self._cache:
                    return f"No checkpoint data for channel {channel_id}"

                stats = self.get_channel_stats(channel_id)
                lines = [
                    f"Checkpoint summary for {channel_id}:",
                    f"  Total: {stats['total']}",
                    f"  Successful: {stats['successful']}",
                    f"  Failed: {stats['failed']}",
                ]
                return "\n".join(lines)

            # Summary across all channels
            total_videos = sum(len(videos) for videos in self._cache.values())
            total_channels = len(self._cache)

            lines = [
                "Global checkpoint summary:",
                f"  Channels: {total_channels}",
                f"  Total videos: {total_videos}",
            ]

            # Top channels by video count
            if self._cache:
                lines.append("\n  Top channels:")
                sorted_channels = sorted(
                    self._cache.items(),
                    key=lambda x: len(x[1]),
                    reverse=True,
                )[:5]
                for ch_id, videos in sorted_channels:
                    lines.append(f"    {ch_id}: {len(videos)} videos")

            return "\n".join(lines)

    def clear_channel(self, channel_id: str) -> bool:
        """
        Clear checkpoint data for a specific channel.

        Useful for --force flag to re-download all videos.

        Args:
            channel_id: Channel ID to clear

        Returns:
            True if clear was successful
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            if channel_id in self._cache:
                del self._cache[channel_id]
                return self._save_checkpoint()
            return True

    def clear_all(self) -> bool:
        """
        Clear all checkpoint data.

        Returns:
            True if clear was successful
        """
        with self._tsm.get_lock("DownloadCheckpoint"):
            self._cache.clear()
            return self._save_checkpoint()

    def export_to_csv(self, output_path: Path) -> bool:
        """
        Export checkpoint data to CSV file.

        Args:
            output_path: Path to output CSV file

        Returns:
            True if export was successful
        """
        try:
            with output_path.open("w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(["video_id", "channel_id", "timestamp", "success", "error_message"])

                for _channel_id, videos in self._cache.items():
                    for entry in videos.values():
                        writer.writerow([
                            entry.video_id,
                            entry.channel_id,
                            entry.timestamp,
                            entry.success,
                            entry.error_message or "",
                        ])

            return True

        except (OSError, csv.Error):
            self.logger.exception("Failed to export checkpoint to CSV")
            return False


# Convenience functions
def get_default_checkpoint(console: Console | None = None) -> DownloadCheckpoint:
    """Get a DownloadCheckpoint instance with default settings."""
    return DownloadCheckpoint(console=console, auto_save=True)


def should_skip_video(
    video_id: str,
    channel_id: str,
    force: bool = False,
    checkpoint: DownloadCheckpoint | None = None,
) -> tuple[bool, str]:
    """
    Check if a video should be skipped based on checkpoint and force flag.

    Args:
        video_id: YouTube video ID
        channel_id: Channel ID
        force: If True, ignore checkpoint and always download
        checkpoint: Optional DownloadCheckpoint instance

    Returns:
        Tuple of (should_skip: bool, reason: str)
    """
    if force:
        return False, "Force mode enabled"

    if checkpoint is None:
        checkpoint = get_default_checkpoint()

    result = checkpoint.check_video(video_id, channel_id)
    if result.status == CheckpointStatus.ALREADY_DOWNLOADED and result.entry is not None:
        return True, f"Already downloaded on {result.entry.timestamp}"

    return False, "Not previously downloaded"
