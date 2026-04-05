import contextlib
import io
import json
import os
import random
import sqlite3
import tempfile
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, TypedDict
from xml.etree import ElementTree as ET

import requests
import yt_dlp
from rich.console import Console
from rich.progress import BarColumn, SpinnerColumn, TextColumn

from yt_fts.core.database import get_db_connection
from yt_fts.db.channels import (
    add_channel_info,
    check_if_channel_exists,
    get_channel_id_from_input,
    get_channel_name_from_db,
    get_channels,
    update_channel_id,
)
from yt_fts.db.infra import _db_write_lock as db_write_lock
from yt_fts.db.videos import get_num_vids, get_vid_ids_by_channel_id
from yt_fts.exceptions.channel_processing import ChannelProcessingError
from yt_fts.services.unified_channel_processor import UnifiedChannelProcessor
from yt_fts.utils import get_date, handle_reject_consent_cookie, parse_vtt
from yt_fts.utils.dual_sink_logger import get_logger, log_operation, log_technical_error
from yt_fts.utils.interrupt_handler import check_interruption
from yt_fts.utils.retry_classifier import get_user_friendly_message

from .exceptions import (
    BaseURLFallbackFailed,
    DownloadTimeoutException,
    PerVideoTimeoutException,
)
from .logging_integration import LoggedDownloadOperation
from .output_utils import StderrCapture, YtdlpSilentLogger
from .progress_tracker import DownloadProgressTracker
from .url_utils import USER_AGENTS, validate_channel_url
from .worker_progress_tracker import WorkerProgressTracker


class DiscoveryResult(TypedDict):
    """Result of pre-flight channel discovery."""

    channel_id: str | None
    channel_name: str | None
    total_videos: int
    with_subs: int
    without_subs: int
    scheduled: int
    members_only: int
    unavailable: int


class DownloadHandler:

    def __init__(
        self,
        number_of_jobs: int = 8,
        language: str = "en",
        cookies_from_browser: str | None = None,
        per_video_delay: float = 0.0,
        fail_fast: bool = True,
        max_time_per_video: float | None = None,
        max_time_per_channel: float | None = None,
        max_videos: int | None = None,
        console: Any = None,
        log_callback: Callable[[str], None] | None = None,
        rich_mode: bool = False,
        suppress_status_messages: bool = False,
        reverse_download: bool = False,
        progress_callback: Callable[[int, int], None] | None = None,
        transcribe_audio_only: bool = False,
        whisper_model: str = "base",
        keep_audio: bool = False,
        include_channel_name_in_messages: bool = True,
    ) -> None:
        """
        Initialize the download handler.

        Args:
            number_of_jobs: Number of concurrent download threads
            language: Preferred subtitle language code
            cookies_from_browser: Browser name for cookie extraction
            per_video_delay: Delay in seconds between video downloads
            fail_fast: Stop immediately on first error if True
            max_time_per_video: Maximum time per video (yt-dlp call timeout)
            max_time_per_channel: Maximum time for entire channel download
            max_videos: Maximum videos to download per channel
            console: Rich console instance for output
            log_callback: Callback function for log messages
            rich_mode: Suppress console output for Rich TUI
            suppress_status_messages: Suppress status messages in batch mode
            reverse_download: Download oldest-to-newest for gap filling
            progress_callback: Callback for per-channel download progress
            transcribe_audio_only: Enable Whisper transcription for videos without subtitles
            whisper_model: Whisper model size for transcription (default: base)
            keep_audio: Preserve downloaded audio files after transcription (for debugging/iteration)
            include_channel_name_in_messages: Include channel name in per-channel messages
        """
        self.console = console or Console(stderr=True, legacy_windows=False)
        self.logger = get_logger(f"{__name__}.DownloadHandler")
        self.log_callback = log_callback
        self.progress_callback = progress_callback
        self.rich_mode = rich_mode
        self.suppress_status_messages = suppress_status_messages
        self.include_channel_name_in_messages = include_channel_name_in_messages
        self.cookies_from_browser = cookies_from_browser
        self.number_of_jobs = number_of_jobs
        self.language = language
        self.per_video_delay = float(per_video_delay)
        self.fail_fast = bool(fail_fast)
        self.max_time_per_video = max_time_per_video
        self.max_time_per_channel = max_time_per_channel
        self.max_videos = max_videos
        self.reverse_download = reverse_download
        self.download_start_time: float = 0.0
        self.rate_limit_count = 0
        self.session: requests.Session | None = None
        self.channel_id: str | None = None
        self._progress_tracker = DownloadProgressTracker(
            channel_name=None,
            console=self.console,
            rich_mode=self.rich_mode,
            suppress_status_messages=self.suppress_status_messages,
        )
        self.channel_processor = UnifiedChannelProcessor(cache_enabled=True)
        self.channel_name: str | None = None
        self.video_ids: list[str] = []
        self.tmp_dir: str | None = None
        self.progress_coordinator: Any = None
        self.progress_channel_name: str | None = None
        self.total_videos = 0
        self.downloaded_videos = 0
        self.videos_saved_to_db = 0
        self.videos_without_subtitles = 0
        self.total_videos_found = 0
        self._videos_saved_during_download = False
        self.min_saved = None
        self.transcribe_audio_only = transcribe_audio_only
        self.whisper_model = whisper_model
        self.keep_audio = keep_audio
        self._discovery_cache: DiscoveryResult | None = None
        self._shutdown = False
        # Per-worker progress tracking
        self._worker_progress: WorkerProgressTracker | None = None
        self._worker_assignments: dict[str, int] = {}
        self._video_count_message_printed = False
        # Filter reason tracking - track why videos were filtered
        self.filter_reasons: dict[str, int] = {
            "no_subtitles": 0,
            "shorts": 0,
            "scheduled": 0,
            "unavailable": 0,
            "members_only": 0,
        }
        self._filtered_video_ids: dict[str, str] = {}  # video_id -> reason

    def _print_message(self, *args: Any, **kwargs: Any) -> None:
        """
        Print a message to the console or log callback depending on rich_mode.
        Routes output to the log panel when running in TUI mode to prevent layout breakage.
        """
        if self.rich_mode and self.log_callback:
            if args:
                msg = " ".join(str(a) for a in args)
                if msg.strip():
                    self.log_callback(msg)
        else:
            self.console.print(*args, **kwargs)

    @staticmethod
    def _video_word(count: int) -> str:
        return "video" if count == 1 else "videos"

    def _maybe_with_channel(self, message: str, preposition: str) -> str:
        if self.include_channel_name_in_messages and self.channel_name:
            return f'{message} {preposition} "{self.channel_name}"'
        return message

    def _detail_message(self, message: str) -> str:
        if self.include_channel_name_in_messages:
            return message
        return f"   ⎿ {message}"

    def _missing_subtitles_message(self, count: int) -> str:
        if count == 1:
            return "1 video does not have subtitles"
        return f"{count} videos do not have subtitles"

    # Filter reason tracking methods

    def _initialize_filter_reasons(self) -> None:
        """Initialize or reset filter reason tracking."""
        self.filter_reasons = {
            "no_subtitles": 0,
            "shorts": 0,
            "scheduled": 0,
            "unavailable": 0,
            "members_only": 0,
        }
        self._filtered_video_ids = {}

    def _track_filter_reason(self, reason: str, video_id: str) -> None:
        """Track a video that was filtered and the reason.

        Args:
            reason: One of 'no_subtitles', 'shorts', 'scheduled', 'unavailable', 'members_only'
            video_id: The video ID that was filtered
        """
        if reason in self.filter_reasons:
            self.filter_reasons[reason] += 1
        self._filtered_video_ids[video_id] = reason

    def _get_filter_summary(self) -> str:
        """Get a summary message of why videos were filtered.

        Returns:
            String describing filter reasons, or empty string if no filters
        """
        reasons_parts = []
        total_filtered = 0

        # Map reason keys to display names
        display_names = {
            "no_subtitles": "no subs",
            "shorts": "Shorts",
            "scheduled": "scheduled",
            "unavailable": "unavailable",
            "members_only": "members-only",
        }

        for reason, count in self.filter_reasons.items():
            if count > 0:
                total_filtered += count
                name = display_names.get(reason, reason)
                reasons_parts.append(f"{count} {name}")

        if not reasons_parts:
            return ""

        if len(reasons_parts) == 1:
            return reasons_parts[0]
        if len(reasons_parts) == 2:
            return f"{reasons_parts[0]} and {reasons_parts[1]}"
        return ", ".join(reasons_parts[:-1]) + f", and {reasons_parts[-1]}"

    def _is_short_video(self, video_url: str) -> bool:
        """Check if a video URL is a YouTube Short.

        Args:
            video_url: The video URL to check

        Returns:
            True if the video is a Short
        """
        return "/shorts/" in video_url

    def _is_scheduled_video(self, info: dict) -> bool:
        """Check if a video is scheduled or upcoming.

        Args:
            info: yt-dlp info dict for the video

        Returns:
            True if the video is scheduled/upcoming
        """
        # Check live_status for upcoming
        live_status = info.get("live_status", "")
        if live_status == "is_upcoming":
            return True

        # Check release_timestamp for future datetime
        release_timestamp = info.get("release_timestamp")
        if release_timestamp:
            try:
                from datetime import datetime

                release_time = datetime.fromisoformat(
                    release_timestamp.replace("Z", "+00:00")
                )
                if release_time > datetime.now(release_time.tzinfo):
                    return True
            except Exception:
                pass

        return False

    def _has_no_subtitles(self, info: dict) -> bool:
        """Check if a video has no subtitles in any language.

        Args:
            info: yt-dlp info dict for the video

        Returns:
            True if the video has no subtitles (manual or auto)
        """
        subtitles = info.get("subtitles", {})
        auto_captions = info.get("automatic_captions", {})
        return not subtitles and not auto_captions

    def _get_no_videos_message(self) -> str:
        """Get the message to show when no videos could be downloaded.

        Returns:
            Message describing why videos were filtered, or empty if no videos were found
        """
        summary = self._get_filter_summary()
        if summary:
            return f"All new videos were {summary}"
        # No videos were found by RSS/yt-dlp, or no videos were processed
        # Return empty to avoid misleading "all videos were filtered" message
        return ""

    def _get_result_message(self) -> str:
        """Get the result message based on what was accomplished.

        Returns:
            Result message describing the outcome
        """
        if self.videos_saved_to_db > 0:
            return "Successfully downloaded channel"

        # No videos saved - check why
        summary = self._get_filter_summary()
        if summary:
            if self.filter_reasons.get("no_subtitles", 0) > 0:
                return "no transcript to store in db"
            return f"all videos filtered ({summary})"
        return "no transcript to store in db"

    def _get_progress(self, *args: Any, **kwargs: Any) -> Any:
        """Returns a Progress instance or DummyProgress depending on rich_mode."""
        return DownloadProgressTracker.get_progress(
            self.console, self.rich_mode, self.suppress_status_messages
        )

    def set_progress_tracker(
        self, progress_coordinator: Any, channel_name: str
    ) -> None:
        """
        Set progress tracking for real-time updates during batch downloads.

        Args:
            progress_coordinator: ThreadSafeProgressCoordinator object for queue-based updates
            channel_name: Channel name for display and task identification
        """
        self.progress_coordinator = progress_coordinator
        self.progress_channel_name = channel_name
        self._progress_tracker.channel_name = channel_name

    def get_videos_saved(self) -> int:
        """
        Get the number of videos successfully saved to the database.

        Returns:
            int: Number of videos saved to database with transcripts
        """
        return self.videos_saved_to_db

    def _conditional_status(self, message: str) -> Any:
        """
        Return a status context manager that suppresses output during Rich mode.

        Delegates to DownloadProgressTracker.conditional_status.

        Args:
            message: Status message to display

        Returns:
            Context manager for status or null context
        """
        return self._progress_tracker.conditional_status(message)

    def _check_shutdown(self) -> bool:
        """
        Check if shutdown has been requested.

        Returns:
            True if shutdown requested, False otherwise
        """
        return self._shutdown

    def _interrupted(self) -> bool:
        """Check for any active interruption request."""
        return self._shutdown or check_interruption()

    def _interruptible_sleep(self, seconds: float) -> bool:
        """Sleep in small increments so interrupts stop quickly.

        Returns:
            True if interrupted during sleep, False otherwise
        """
        import time as _time

        if seconds <= 0:
            return False
        deadline = _time.time() + seconds
        while _time.time() < deadline:
            if self._interrupted():
                return True
            _time.sleep(min(0.1, deadline - _time.time()))
        return False

    def _apply_max_videos_limit(self) -> None:
        """
        Apply max_videos limit to self.video_ids if set.

        This should be called after setting self.video_ids to enforce the limit.
        """
        if self.max_videos is not None and self.video_ids is not None:
            if len(self.video_ids) > self.max_videos:
                if not self.suppress_status_messages:
                    channel_display = self.channel_name or "Channel"
                    self._print_message(
                        f"[dim]Limiting {channel_display} to {self.max_videos} of {len(self.video_ids)} videos[/dim]"
                    )
                self.video_ids = self.video_ids[: self.max_videos]

    def _update_download_progress(self, current: int, total: int) -> None:
        """
        Update progress bar during video downloads using Rich Progress.

        Delegates to DownloadProgressTracker.update_progress.

        Args:
            current: Current number of videos downloaded
            total: Total number of videos to download
        """
        self._progress_tracker.channel_name = self.channel_name
        self._progress_tracker.update_progress(
            current,
            total,
            progress_coordinator=self.progress_coordinator,
            progress_channel_name=self.progress_channel_name,
        )

    def _update_rich_progress(
        self, current: int, total: int, percentage: float
    ) -> None:
        """Update Rich Progress bar for video downloads. Delegates to tracker."""
        self._progress_tracker.channel_name = self.channel_name
        self._progress_tracker._update_rich_progress(current, total, percentage)

    def _print_progress_bar(self, current: int, total: int, percentage: float) -> None:
        """Legacy method - now handled by Rich Progress."""

    def cleanup_progress(self) -> None:
        """Clean up progress bar resources. Delegates to tracker."""
        self._progress_tracker.cleanup()

    def download_channel(self, url: str) -> None:
        """
        Download channel by first resolving the URL to a channel ID,
        then delegating to download_channel_by_id for the actual download.
        """
        import time

        start_time = time.time()
        log_operation(
            "download_channel", "Starting channel download", level=10, url=url
        )
        validated_url = self.validate_channel_url(url)
        if not validated_url:
            log_operation(
                "download_channel",
                "URL validation failed",
                level=10,
                url=url,
                duration_ms=(time.time() - start_time) * 1000,
            )
            return
        validation_duration = (time.time() - start_time) * 1000
        log_operation(
            "download_channel",
            "URL validation successful",
            level=10,
            validated_url=validated_url,
            validation_duration_ms=validation_duration,
        )
        resolution_start = time.time()
        self.channel_id = get_channel_id_from_input(validated_url)
        resolution_duration = (time.time() - resolution_start) * 1000
        log_operation(
            "download_channel",
            "Channel ID resolution completed",
            level=10,
            channel_id=self.channel_id,
            resolution_duration_ms=resolution_duration,
        )
        if not self.channel_id:
            self._print_message(
                f"[red]❌ Failed to resolve channel ID from: {url}[/red]"
            )
            log_operation(
                "download_channel",
                "Channel ID resolution failed",
                level=30,
                url=url,
                duration_ms=(time.time() - start_time) * 1000,
            )
            return
        log_operation(
            "download_channel",
            "Delegating to download_channel_by_id",
            level=10,
            channel_id=self.channel_id,
            total_duration_ms=(time.time() - start_time) * 1000,
        )
        self.download_channel_by_id(self.channel_id, validated_url)

    def download_channel_optimized(
        self, url: str, skip_resolution: bool = False
    ) -> None:
        """
        Optimized channel download that can skip redundant channel resolution.

        This method is designed for cases where the channel has already been
        resolved (e.g., by batch_downloader) to avoid the 7-minute hangs
        caused by redundant async resolution in UnifiedChannelProcessor.

        Args:
            url: Pre-resolved channel URL (can be @handle or /channel/ URL)
            skip_resolution: If True, skip get_channel_id_from_input and use URL directly
        """
        import time

        start_time = time.time()
        log_operation(
            "download_channel_optimized",
            "Starting optimized channel download",
            level=10,
            url=url,
            skip_resolution=skip_resolution,
        )
        validated_url = self.validate_channel_url(url)
        if not validated_url:
            log_operation(
                "download_channel_optimized",
                "URL validation failed",
                level=10,
                url=url,
                duration_ms=(time.time() - start_time) * 1000,
            )
            return
        validation_duration = (time.time() - start_time) * 1000
        log_operation(
            "download_channel_optimized",
            "URL validation successful",
            level=10,
            validated_url=validated_url,
            validation_duration_ms=validation_duration,
        )
        if skip_resolution or "/channel/" in validated_url:
            if "/channel/" in validated_url:
                channel_id = validated_url.split("/channel/")[1].split("/")[0]
                log_operation(
                    "download_channel_optimized",
                    "Using extracted channel ID from URL",
                    level=10,
                    channel_id=channel_id,
                    skip_reason="URL contains /channel/",
                )
                self.channel_id = channel_id
            else:
                log_operation(
                    "download_channel_optimized",
                    "Skipping resolution for handle URL",
                    level=10,
                    url=validated_url,
                    skip_reason="Handle URL - will resolve during download",
                )
                self.channel_id = None
            if self.channel_id:
                self.download_channel_by_id(self.channel_id, validated_url)
            else:
                self._download_handle_direct(validated_url)
        else:
            log_operation(
                "download_channel_optimized",
                "Falling back to standard resolution",
                level=10,
                url=validated_url,
            )
            self.download_channel(validated_url)
        total_duration = (time.time() - start_time) * 1000
        log_operation(
            "download_channel_optimized",
            "Optimized download completed",
            level=10,
            total_duration_ms=total_duration,
        )

    def _download_handle_direct(self, handle_url: str) -> None:
        """
        Direct download for @handle URLs that bypasses the slow UnifiedChannelProcessor.

        This method uses the handle URL directly with yt-dlp, which will handle
        the resolution during the actual download operation much more efficiently
        than the async UnifiedChannelProcessor.
        """
        import time

        start_time = time.time()
        log_operation(
            "_download_handle_direct",
            "Starting direct handle download",
            level=10,
            handle_url=handle_url,
        )
        self._video_count_message_printed = False
        self.channel_id = handle_url
        self.channel_name = (
            handle_url.split("@")[-1].split("/")[0] if "@" in handle_url else handle_url
        )
        self.session = self.init_session(handle_url)
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            playlist_data = self.get_playlist_data(handle_url)
            if not playlist_data:
                self._log_handle_download_failed(handle_url, start_time)
                msg = f"No videos found for channel: {handle_url}"
                raise Exception(msg)
            actual_channel_id = self._extract_actual_channel_id(playlist_data)
            self._migrate_channel_if_needed(handle_url, actual_channel_id)
            if self._check_channel_exists(handle_url, actual_channel_id):
                self._handle_existing_channel(playlist_data, actual_channel_id)
            else:
                self._handle_new_channel(handle_url, playlist_data)
            if self.video_ids:
                self.download_vtts()
            if not self._videos_saved_during_download:
                self.vtt_to_db()
        duration_ms = (time.time() - start_time) * 1000
        log_operation(
            "_download_handle_direct",
            "Direct handle download completed",
            level=10,
            handle_url=handle_url,
            videos_count=len(playlist_data) if playlist_data else 0,
            duration_ms=duration_ms,
        )

    def _log_handle_download_failed(self, handle_url: str, start_time: float) -> None:
        """Log handle download failure."""
        import time

        log_operation(
            "_download_handle_direct",
            "No videos found",
            level=30,
            handle_url=handle_url,
            duration_ms=(time.time() - start_time) * 1000,
        )

    def _extract_actual_channel_id(self, playlist_data: list) -> str:
        """Extract actual YouTube channel_id from playlist data.

        Updates self.channel_id and self.channel_name with the resolved values.
        Returns the actual channel_id or empty string if not found.
        """
        if playlist_data and len(playlist_data) > 0:
            actual_channel_id = playlist_data[0].get("channel_id", "")
            actual_channel_name = playlist_data[0].get(
                "channel_name", self.channel_name
            )
            if actual_channel_id:
                self.channel_id = actual_channel_id
                self.channel_name = actual_channel_name
                log_operation(
                    "_download_handle_direct",
                    "Extracted actual channel_id from playlist_data",
                    level=10,
                    actual_channel_id=actual_channel_id,
                    channel_name=actual_channel_name,
                )
                return actual_channel_id
        return ""

    def _migrate_channel_if_needed(
        self, handle_url: str, actual_channel_id: str
    ) -> None:
        """Migrate channel from URL format to UC format if needed."""
        if not actual_channel_id:
            return
        channel_exists_with_actual_id = check_if_channel_exists(self.channel_id)
        channel_exists_with_handle_url = check_if_channel_exists(handle_url)
        if channel_exists_with_handle_url and (not channel_exists_with_actual_id):
            log_operation(
                "_download_handle_direct",
                "Migrating channel_id from URL format to UC format",
                level=10,
                old_channel_id=handle_url,
                new_channel_id=actual_channel_id,
            )
            self._print_message(
                "[cyan]Migrating channel to use standard ID format...[/cyan]"
            )
            update_channel_id(handle_url, actual_channel_id)

    def _check_channel_exists(self, handle_url: str, actual_channel_id: str) -> bool:
        """Check if channel exists in database.

        Returns True if channel exists with either actual channel_id or handle_url.
        """
        return check_if_channel_exists(self.channel_id) or check_if_channel_exists(
            handle_url
        )

    def _handle_existing_channel(
        self, playlist_data: list, actual_channel_id: str
    ) -> None:
        """Handle download for an existing channel in the database.

        Filters and sets up video_ids for only new videos.
        Preserves existing video_ids if set (e.g., during backfill).
        """
        # If video_ids is already set (backfill mode), don't overwrite it
        if self.video_ids is not None:
            return

        vid_id_tuples = get_vid_ids_by_channel_id(self.channel_id)
        local_vid_ids: list[str] = [vid_id[0] for vid_id in vid_id_tuples]
        all_video_ids = list({video["video_id"] for video in playlist_data})
        self.total_videos_found = len(all_video_ids)
        fresh_videos = [
            vid_id for vid_id in all_video_ids if vid_id not in local_vid_ids
        ]
        self.video_ids = fresh_videos
        self._apply_max_videos_limit()
        num_local_vids = len(local_vid_ids)
        num_public_vids = len(all_video_ids)
        if num_public_vids == num_local_vids:
            return
        total = len(fresh_videos)
        if total == 0:
            return
        self._print_new_videos_message(total, num_local_vids)

    def _handle_new_channel(self, handle_url: str, playlist_data: list) -> None:
        """Handle download for a new channel not in the database."""
        add_channel_info(
            channel_id=self.channel_id,
            channel_name=self.channel_name,
            channel_url=handle_url,
        )
        self.video_ids = list({video["video_id"] for video in playlist_data})
        self.total_videos_found = len(self.video_ids)
        self._apply_max_videos_limit()
        if not self._video_count_message_printed and (
            not self.suppress_status_messages
        ):
            self._video_count_message_printed = True
            channel_display = self.channel_name or "Channel"
            self._print_message()
            self._print_message(f"[cyan]📺 {channel_display}[/cyan]")
            self._print_message(
                f"[cyan]Found {len(self.video_ids)} videos on new channel[/cyan]"
            )

    def _print_new_videos_message(self, total: int, existing: int) -> None:
        """Print message about new videos found for existing channel."""
        if self._video_count_message_printed or self.suppress_status_messages:
            return
        self._video_count_message_printed = True
        channel_display = self.channel_name or "Channel"
        self._print_message()
        self._print_message(f"[cyan]📺 {channel_display}[/cyan]")
        self._print_message(
            f"[cyan]Found {total} new videos to download[/cyan] [dim]({existing:,} already in database)[/dim]"
        )

    def download_channel_by_id(
        self, channel_id: str, channel_url: str | None = None
    ) -> None:
        """
        Download channel directly using pre-resolved channel ID.
        Bypasses slow channel resolution for performance.

        Args:
            channel_id: YouTube channel ID (UC...)
            channel_url: Full channel URL (optional, will be generated if not provided)
        """
        if not channel_id.startswith("UC") or len(channel_id) != 24:
            msg = f"Invalid channel ID format: {channel_id}"
            raise ValueError(msg)
        self.channel_id = channel_id
        if not channel_url:
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
        self.session = self.init_session(channel_url)
        self.channel_name = f"Channel {channel_id[:8]}..."
        channel_exists = check_if_channel_exists(self.channel_id)
        if channel_exists and self.video_ids is None:
            # Only skip to update_channel if we're not backfilling specific videos
            if not self.suppress_status_messages:
                self._print_message(
                    f"[yellow]Channel '{self.channel_name}' already exists in database. Updating instead...[/yellow]"
                )
            self.update_channel(self.channel_id)
            return
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            if self.video_ids is None:
                channel_url = (
                    f"https://www.youtube.com/channel/{self.channel_id}/videos"
                )
                self.video_ids = self.get_videos_list(channel_url)
            self._apply_max_videos_limit()

            # Improved message for 0 videos case
            num_videos = len(self.video_ids)
            if num_videos == 0:
                message = self._get_no_videos_message()
                if (
                    message
                ):  # Only show message if videos were actually found and filtered
                    self._print_message(
                        f"[yellow]{self._detail_message(message)}[/yellow]"
                    )
                elif not self.suppress_status_messages:
                    self._print_message(
                        f"[yellow]{self._detail_message('No videos found')}[/yellow]"
                    )
            else:
                self._print_message(
                    f"[green]{self._detail_message(f"Downloading [red]{num_videos}[/red] vtt file{'s' if num_videos != 1 else ''}")}[/green]\n"
                )
                self.download_vtts()
            # Only add/update channel info if we don't already have a good name
            # This prevents overwriting good names from RSS/API escalation with "Channel UC..." format
            current_name = get_channel_name_from_db(self.channel_id)
            should_update = (
                not current_name  # No name yet
                or current_name.startswith(
                    "Channel UC"
                )  # Has generic "Channel UC..." name
                or (
                    current_name.startswith("UC") and len(current_name) >= 20
                )  # Raw channel ID
            )
            if should_update:
                add_channel_info(self.channel_id, self.channel_name, channel_url)
            if not self._videos_saved_during_download:
                self.vtt_to_db()

        # Improved "finished" message based on actual results
        videos_saved = (
            self.videos_saved_to_db if hasattr(self, "videos_saved_to_db") else 0
        )
        if videos_saved > 0:
            message = self._maybe_with_channel(
                f"   ⎿ [green]Finished downloading {videos_saved} subtitle{'s' if videos_saved != 1 else ''}[/green]",
                "for",
            )
            self._print_message(message)
        else:
            # Only show "No subtitles downloaded" if we actually had videos to process (but they were filtered/failed).
            # If we started with 0 videos, we've already handled the message (or suppression) above.
            had_videos = (
                hasattr(self, "video_ids")
                and self.video_ids is not None
                and len(self.video_ids) > 0
            )

            if had_videos:
                message = self._maybe_with_channel(
                    "   ⎿ [yellow]No subtitles downloaded[/yellow]", "for"
                )
                self._print_message(message)

    def _get_channel_name_from_youtube(self, channel_id: str) -> str:
        """Get channel name from YouTube using yt-dlp."""
        ydl_opts: dict[str, Any] = {
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "extract_flat": True,
            "socket_timeout": 5,
            "retries": 1,
        }
        if self.cookies_from_browser:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        try:
            channel_url = f"https://www.youtube.com/channel/{channel_id}"
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                result = info.get(
                    "uploader", info.get("channel", f"Channel {channel_id}")
                )
                return str(result) if result is not None else f"Channel {channel_id}"
        except Exception as e:
            self.logger.debug("Failed to get channel name for %s: %s", channel_url, e)
            return f"Channel {channel_id}"

    def download_playlist(
        self, playlist_url: str, language: str, number_of_jobs: int
    ) -> None:
        """
        Download subtitles for all videos in a playlist.

        Args:
            playlist_url: URL of the YouTube playlist
            language: Preferred subtitle language code
            number_of_jobs: Number of concurrent download threads
        """
        self.language = language
        self.number_of_jobs = number_of_jobs
        playlist_data = self.get_playlist_data(playlist_url)
        for video in playlist_data:
            channel_name = video["channel_name"]
            channel_id = video["channel_id"]
            channel_url = video["channel_url"]
            if not check_if_channel_exists(channel_id):
                add_channel_info(channel_id, channel_name, channel_url)
        self.video_ids = list({video["video_id"] for video in playlist_data})
        self._apply_max_videos_limit()
        with tempfile.TemporaryDirectory() as tmp_dir:
            self._print_message(
                f"[green][bold]Downloading [red]{len(playlist_data)}[/red] vtt files[/bold][/green]\n"
            )
            self.tmp_dir = tmp_dir
            self.download_vtts()
            if not self._videos_saved_during_download:
                self.vtt_to_db()

    def _resolve_target_channel_id(self, target_channel: str | int) -> str:
        """Resolve channel_id from target_channel (which can be channel_id or rowid).

        Args:
            target_channel: Channel ID (UC...) or rowid from database

        Returns:
            Resolved channel_id
        """
        if isinstance(target_channel, str) and len(target_channel) == 24:
            return target_channel
        return get_channel_id_from_input(target_channel)

    def _load_channel_name_from_db(self, channel_id: str) -> str | None:
        """Load channel name from database.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Channel name from database, or None if not found
        """
        try:
            from yt_fts.db.channels import get_channel_name_from_db

            return get_channel_name_from_db(channel_id)
        except Exception:
            return None

    def _handle_download_post_process(
        self, fresh_videos: list[str] | None = None
    ) -> bool:
        """Handle post-download processing and summary.

        Args:
            fresh_videos: List of video IDs that were downloaded (optional)

        Returns:
            True if processing completed, False if no videos to process
        """
        if self._videos_saved_during_download:
            saved_count = self.videos_saved_to_db
            saved_word = self._video_word(saved_count)
            message = f"Added {saved_count} new {saved_word} to the database"
            self._print_message(
                self._detail_message(self._maybe_with_channel(message, "from"))
            )
            return True
        vtt_to_parse = os.listdir(self.tmp_dir)
        if len(vtt_to_parse) == 0:
            video_count = (
                len(fresh_videos) if fresh_videos is not None else len(self.video_ids)
            )
            if video_count == 0:
                self._print_message(self._detail_message("No new videos saved"))
            else:
                message = self._missing_subtitles_message(video_count)
                combined = f"No new videos saved; {message}"
                self._print_message(
                    self._detail_message(self._maybe_with_channel(combined, "on"))
                )
            return False
        self.vtt_to_db()
        parsed_count = len(vtt_to_parse)
        parsed_word = self._video_word(parsed_count)
        message = f"Added {parsed_count} new {parsed_word} to the database"
        self._print_message(
            self._detail_message(self._maybe_with_channel(message, "from"))
        )
        return True

    def update_channel(self, target_channel: str | int) -> None:
        """
        Update an existing channel with new videos.

        Args:
            target_channel: Channel ID (UC...) or rowid from database
        """
        with tempfile.TemporaryDirectory() as tmp_dir:
            self.tmp_dir = tmp_dir
            self.channel_id = self._resolve_target_channel_id(target_channel)
            channel_url = f"https://www.youtube.com/channel/{self.channel_id}/videos"
            self.session = self.init_session(channel_url)
            self.channel_name = self.channel_id
            db_name = self._load_channel_name_from_db(self.channel_id)
            if db_name:
                self.channel_name = db_name

            # If transcribe_audio_only is enabled and video_ids not set,
            # populate video_ids with videos needing backfill
            if not self.video_ids and self.transcribe_audio_only:
                from yt_fts.db.videos import get_video_ids_without_subtitles

                backfill_video_ids = get_video_ids_without_subtitles(
                    self.channel_id, limit=50
                )
                if backfill_video_ids:
                    self.video_ids = backfill_video_ids

            if self.video_ids:
                if not self.suppress_status_messages:
                    self._print_message(f"Updating channel: {self.channel_name}")
                # When transcribing audio for videos without subtitles, don't filter out existing videos
                if self.transcribe_audio_only:
                    # Use the provided video_ids directly - they're selected because they lack subtitles
                    sub_count = len(self.video_ids)
                    if sub_count == 0:
                        self._print_message(
                            self._detail_message("No videos need subtitles")
                        )
                        return
                    sub_word = self._video_word(sub_count)
                    message = f"   ⎿ Downloading subtitles for {sub_count} {sub_word}"
                    self._print_message(self._maybe_with_channel(message, "from"))
                else:
                    # Still need to deduplicate against database when video_ids are pre-populated
                    vid_id_tuples = get_vid_ids_by_channel_id(self.channel_id)
                    local_vid_ids: list[str] = [i[0] for i in vid_id_tuples]
                    fresh_videos = [v for v in self.video_ids if v not in local_vid_ids]
                    self.video_ids = fresh_videos
                    if not self.video_ids:
                        self._print_message(
                            "[yellow]No new videos to download[/yellow]"
                        )
                        # Reprocess removed - transcription happens during download
                        return
                    new_count = len(self.video_ids)
                    new_word = self._video_word(new_count)
                    message = f"   ⎿ Downloading {new_count} new {new_word}"
                    self._print_message(self._maybe_with_channel(message, "from"))
                self.download_vtts()
                self._handle_download_post_process()
            else:
                if not self.suppress_status_messages:
                    self._print_message(f"Updating channel: {self.channel_name}")
                public_video_ids = self.get_videos_list(channel_url)
                num_public_vids = len(public_video_ids)
                num_local_vids = get_num_vids(self.channel_id)
                if num_public_vids == num_local_vids:
                    self._print_message("[yellow]No new videos to download[/yellow]")
                    # Reprocess removed - transcription happens during download
                    return
                vid_id_tuples = get_vid_ids_by_channel_id(self.channel_id)
                local_vid_ids: list[str] = [i[0] for i in vid_id_tuples]
                fresh_videos = [i for i in public_video_ids if i not in local_vid_ids]
                self.video_ids = fresh_videos
                self._apply_max_videos_limit()
                fresh_count = len(fresh_videos)
                fresh_word = self._video_word(fresh_count)
                found_message = f"Found {fresh_count} {fresh_word} not in the database"
                self._print_message(self._maybe_with_channel(found_message, "on"))
                message = f"   ⎿ Downloading {fresh_count} new {fresh_word}"
                self._print_message(self._maybe_with_channel(message, "from"))
                self.download_vtts()
                self._handle_download_post_process(fresh_videos)

    def update_all_channels(self) -> None:
        """
        Update all channels in the database with new videos.

        Iterates through all stored channels and downloads any new videos
        that have been published since the last update.
        """
        self._print_message("Updating all channels in the database")
        all_channels = get_channels()
        all_channel_row_ids = [i[0] for i in all_channels]
        for channel_row_id in all_channel_row_ids:
            self.update_channel(channel_row_id)
        self._print_message("[green]Finished updating all channels[/green]")

    def init_session(self, url: str) -> requests.Session:
        """Initialize session with logging and timeout to prevent hanging."""
        import time

        start_time = time.time()
        log_operation(
            "init_session",
            "Initializing session and handling consent cookie",
            level=10,
            url=url,
        )
        s = requests.session()
        try:
            handle_reject_consent_cookie(url, s, timeout=10)
            duration_ms = (time.time() - start_time) * 1000
            log_operation(
                "init_session",
                "Session initialized successfully",
                level=10,
                duration_ms=duration_ms,
            )
            return s
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            log_technical_error(
                e, {"operation": "init_session", "url": url, "duration_ms": duration_ms}
            )
            raise

    def _print_error_message(self, message: str) -> None:
        """Print error message in Rich or non-Rich mode.

        Args:
            message: The error message to display
        """
        if self.rich_mode and self.log_callback:
            self.log_callback(message)
        else:
            self._print_message(message)

    def _print_suggestions(
        self, suggestions: list[str], title: str = "[yellow]💡 Suggestions:[/yellow]"
    ) -> None:
        """Print suggestions in Rich or non-Rich mode.

        Args:
            suggestions: List of suggestion strings to display
            title: Optional title for the suggestions section
        """
        if not suggestions:
            return
        if self.rich_mode and self.log_callback:
            suggestion_details = " | ".join(suggestions)
            full_msg = f"{title} {suggestion_details}"
            self.log_callback(full_msg)
        else:
            self._print_message(title)
            for suggestion in suggestions:
                self._print_message(f"   • {suggestion}")

    async def get_channel_id(self, input_value: str) -> str | None:
        """
        # FIXED: Enhanced channel resolution using UnifiedChannelProcessor.

        Replaces broken HTML scraping with robust channel resolution that
        properly handles @handle, URL, channel_id, and name inputs.
        """
        try:
            result = await self.channel_processor.process_channel_input(input_value)
            if not result.success:
                self._print_error_message(
                    f"[red]❌ Channel Resolution Error:[/red] {result.error}"
                )
                if result.suggestions:
                    self._print_suggestions(result.suggestions)
                return None
            if result.channel_info and result.channel_info.name:
                self._print_message(
                    f"[green]✅ Channel resolved:[/green] {result.channel_info.name}"
                )
            self._print_message(f"[blue]📺 Channel ID:[/blue] {result.channel_id}")
            return result.channel_id
        except ChannelProcessingError as e:
            self._print_error_message(
                f"[red]❌ Channel Processing Error:[/red] {e.message}"
            )
            if e.suggestions:
                self._print_suggestions(e.suggestions)
            return None
        except Exception as e:
            error_msg = f"[red]❌ Unexpected Error:[/red] Failed to resolve channel '{input_value}': {e!s}"
            suggestions = [
                "Check if the channel exists and is public",
                "Try using the channel's @handle or full URL",
                "Verify your internet connection",
            ]
            self._print_message(error_msg)
            self._print_suggestions(suggestions, "[yellow]💡 Try:[/yellow]")
            return None

    async def get_channel_name(self, channel_id: str) -> str | None:
        """
        # FIXED: Enhanced channel name resolution using UnifiedChannelProcessor.

        Uses the unified processor's channel info retrieval with fallback logic.
        """
        try:
            channel_info = await self.channel_processor.get_channel_info(channel_id)
            if channel_info and channel_info.name:
                return channel_info.name
            return await self._get_channel_name_from_feed(channel_id)
        except Exception as e:
            self._print_error_message(
                f"[red]❌ Error getting channel name:[/red] {e!s}"
            )
            return None

    async def _get_channel_name_from_feed(self, channel_id: str) -> str | None:
        """
        Fallback method: Get channel name from YouTube feed.
        This is the original implementation preserved for compatibility.
        """
        try:
            if not self.session:
                self.session = self.init_session(
                    f"https://www.youtube.com/channel/{channel_id}"
                )
            res = self.session.get(
                f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
            )
            if res.status_code == 200:
                with self._conditional_status("[bold green]Parsing Feed..."):
                    tree = ET.fromstring(res.content)
                    name_elem = tree.find(".//{{*}}author/{{*}}name")
                    if name_elem is not None and name_elem.text is not None:
                        return name_elem.text
                    return None
            else:
                self._print_message(
                    "[yellow]⚠️ Warning:[/yellow] couldn't get the channel name from feed"
                )
                return None
        except Exception as e:
            self._print_message(f"[yellow]⚠️ Feed fallback failed:[/yellow] {e!s}")
            return None

    def get_videos_list(self, channel_url: str) -> list[str]:
        """
        Extract list of video IDs from a channel URL.

        Args:
            channel_url: YouTube channel /videos URL

        Returns:
            List of video IDs for the channel (empty list on error)
        """
        with self._conditional_status("[bold green]Scraping video urls ..."):
            ydl_opts = self._build_video_list_ydl_opts()
            list_of_videos_urls = self._extract_video_ids_from_ytdlp(
                channel_url, ydl_opts
            )
            if list_of_videos_urls is None:
                return []
            self._extend_with_stream_videos(channel_url, ydl_opts, list_of_videos_urls)
        return list_of_videos_urls

    def _build_video_list_ydl_opts(self) -> dict[str, Any]:
        """Build yt-dlp options for video list extraction."""
        headers = {
            "User-Agent": random.choice(self._user_agents),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Cache-Control": "max-age=0",
        }
        ydl_opts: dict[str, Any] = {
            "http_headers": headers,
            "extract_flat": True,
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            "nocheckcertificate": True,
            "sleep_interval": 2,
            "max_sleep_interval": 6,
            "retries": 5,
            "socket_timeout": 30,
            "extractor_args": {"youtubetab": ["skip=authcheck"]},
        }
        if self.reverse_download:
            ydl_opts["playlistreverse"] = True
        if self.cookies_from_browser is not None:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return ydl_opts

    def _extract_video_ids_from_ytdlp(
        self, channel_url: str, ydl_opts: dict[str, Any]
    ) -> list[str] | None:
        """Extract video IDs from channel using yt-dlp.

        Returns:
            List of video IDs, or None if extraction failed.
        """
        stderr_buffer = io.StringIO()
        try:
            with contextlib.redirect_stderr(stderr_buffer):
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    if info and "entries" in info:
                        return self._extract_ids_from_entries(info["entries"])
                    self._print_message(
                        "[red]Error: Could not extract video list from channel[/red]"
                    )
                    return None
        except Exception as e:
            self._handle_video_list_extraction_error(e, channel_url)
            return None

    def _extract_ids_from_entries(self, entries: list) -> list[str]:
        """Extract video IDs from yt-dlp entries."""
        return [entry.get("id") for entry in entries if entry and entry.get("id")]

    def _handle_video_list_extraction_error(
        self, error: Exception, channel_url: str
    ) -> None:
        """Handle errors during video list extraction."""
        error_msg = str(error)
        self.last_error = error_msg

        # Use user-friendly error message
        user_message = get_user_friendly_message(error_msg)
        self._print_generic_scraping_error(user_message)

    def _print_403_error_context(self) -> None:
        """Print 403 Forbidden error context."""
        error_lines = [
            "[red]403 Forbidden error when scraping channel videos[/red]",
            "[yellow]This might be due to:[/yellow]",
            "  - Channel is private or restricted",
            "  - YouTube is blocking automated access",
            "  - Missing cookies (try --cookies-from-browser)",
            "  - Rate limiting",
        ]
        if self.rich_mode and self.log_callback:
            full_msg = "\n".join(error_lines)
            self.log_callback(full_msg)
        else:
            self._print_message(error_lines[0])
            self._print_message(error_lines[1])
            for line in error_lines[2:]:
                self._print_message(line)

    def _print_generic_scraping_error(self, short_error: str) -> None:
        """Print generic scraping error."""
        error_msg = f"[red]Error scraping videos:[/red] {short_error}"
        if self.rich_mode and self.log_callback:
            self.log_callback(error_msg)
        else:
            self._print_message(error_msg)

    def _extend_with_stream_videos(
        self, channel_url: str, ydl_opts: dict[str, Any], video_list: list[str]
    ) -> None:
        """Extend video list with live streams if available."""
        streams_url = channel_url.replace("/videos", "/streams")
        try:
            ydl_opts_streams = ydl_opts.copy()
            ydl_opts_streams["quiet"] = True
            ydl_opts_streams["no_warnings"] = True
            streams_stderr_buffer = io.StringIO()
            with contextlib.redirect_stderr(streams_stderr_buffer):
                with yt_dlp.YoutubeDL(ydl_opts_streams) as ydl:
                    streams_info = ydl.extract_info(streams_url, download=False)
                    if streams_info and "entries" in streams_info:
                        live_stream_urls = self._extract_ids_from_entries(
                            streams_info["entries"]
                        )
                        if live_stream_urls:
                            video_list.extend(live_stream_urls)
        except Exception as e:
            self.logger.debug("Streams tab error for %s: %s", channel_url, e)

    def discover_channel(self, channel_url: str) -> DiscoveryResult:
        """
        Pre-flight video discovery: scan channel to count videos and subtitle availability.

        Returns:
            DiscoveryResult: TypedDict with channel metadata and video counts
        """
        discovery = self._create_discovery_result()
        ydl_opts = self._build_discovery_ydl_opts()
        try:
            self.logger.debug(
                "[DISCOVERY] Starting pre-flight scan for: %s", channel_url
            )
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(channel_url, download=False)
                self._extract_channel_info(discovery, info)
                if info and "entries" in info:
                    self._scan_video_entries(discovery, info["entries"])
        except Exception as e:
            self.logger.debug("[DISCOVERY] Error for %s: %s", channel_url, e)
        self._cache_and_log_discovery(discovery)
        return discovery

    def _create_discovery_result(self) -> DiscoveryResult:
        """Create empty discovery result dict."""
        return {
            "channel_id": None,
            "channel_name": None,
            "total_videos": 0,
            "with_subs": 0,
            "without_subs": 0,
            "scheduled": 0,
            "members_only": 0,
            "unavailable": 0,
        }

    def _build_discovery_ydl_opts(self) -> dict[str, Any]:
        """Build yt-dlp options for channel discovery."""
        from .output_utils import YtdlpSilentLogger

        return {
            "http_headers": {"User-Agent": random.choice(self._user_agents)},
            "quiet": True,
            "noprogress": True,
            "extract_flat": True,
            "listsubtitles": True,
            "socket_timeout": 30,
            "retries": 2,
            "no_warnings": True,
            "logger": YtdlpSilentLogger(),
        }

    def _extract_channel_info(
        self, discovery: DiscoveryResult, info: dict | None
    ) -> None:
        """Extract channel ID and name from yt-dlp info dict."""
        if not info:
            return
        if "channel_id" in info:
            discovery["channel_id"] = info["channel_id"]
        if "channel" in info and isinstance(info["channel"], str):
            discovery["channel_name"] = info["channel"]
        elif "uploader" in info:
            discovery["channel_name"] = info["uploader"]

    def _scan_video_entries(self, discovery: DiscoveryResult, entries: list) -> None:
        """Scan video entries and categorize by availability and subtitle status."""
        for entry in entries:
            if not entry:
                continue
            discovery["total_videos"] += 1
            availability = entry.get("availability", None)
            if availability in ("public", "unlisted"):
                self._check_subtitle_availability(discovery, entry)
            elif availability == "members_only":
                discovery["members_only"] += 1
            elif availability in (
                "private",
                "needs_auth",
                "player_only",
                "subscriber_only",
            ):
                discovery["unavailable"] += 1
            self._check_scheduled_status(discovery, entry)

    def _check_subtitle_availability(
        self, discovery: DiscoveryResult, entry: dict
    ) -> None:
        """Check if entry has subtitles and update discovery counts."""
        subtitles = entry.get("subtitles", {})
        automatic_captions = entry.get("automatic_captions", {})
        if subtitles or automatic_captions:
            discovery["with_subs"] += 1
        else:
            discovery["without_subs"] += 1

    def _check_scheduled_status(self, discovery: DiscoveryResult, entry: dict) -> None:
        """Check if video is scheduled/upcoming and update discovery counts."""
        from datetime import datetime

        release_timestamp = entry.get("release_timestamp")
        if release_timestamp:
            try:
                release_time = datetime.fromisoformat(
                    release_timestamp.replace("Z", "+00:00")
                )
                if release_time > datetime.now(release_time.tzinfo):
                    discovery["scheduled"] += 1
            except Exception:
                pass
        live_status = entry.get("live_status")
        if live_status == "is_upcoming":
            discovery["scheduled"] += 1

    def _cache_and_log_discovery(self, discovery: DiscoveryResult) -> None:
        """Cache discovery results and log summary."""
        self._discovery_cache = discovery
        self.logger.debug(
            "[DISCOVERY] Complete: %s total, %s with subs, channel_id=%s",
            discovery["total_videos"],
            discovery["with_subs"],
            discovery.get("channel_id"),
        )

    def get_discovery_cache(self) -> DiscoveryResult | None:
        """Get the cached discovery results from pre-flight scan."""
        return self._discovery_cache

    def clear_discovery_cache(self) -> None:
        """Clear the discovery cache."""
        self._discovery_cache = None

    def _process_video_entries(
        self,
        entries: list,
        parent_channel_id: str,
        parent_channel_name: str,
        include_title: bool = False,
    ) -> list[dict]:
        """Process yt-dlp video entries into standardized playlist data format.

        Args:
            entries: List of entry dictionaries from yt-dlp
            parent_channel_id: Channel ID from parent info object
            parent_channel_name: Channel name from parent info object
            include_title: If True, include 'title' field in output (for fallback path)

        Returns:
            List of processed video objects with standardized fields
        """
        playlist_data = []
        for entry in entries:
            entry_id = entry.get("id") if entry else None
            if not entry or not entry_id:
                continue
            entry_channel_id = entry.get("channel_id", "") or parent_channel_id
            entry_channel_name = entry.get("channel", "") or parent_channel_name
            duration = entry.get("duration")
            thumbnail_url = entry.get("thumbnail", "")
            view_count = entry.get("view_count", 0)
            is_short = 1 if entry.get("url", "").find("/shorts/") >= 0 else 0
            vid_obj = {
                "channel_name": entry_channel_name,
                "channel_id": entry_channel_id,
                "video_id": entry_id,
                "channel_url": f"https://www.youtube.com/channel/{entry_channel_id}/videos",
                "video_url": f"https://youtu.be/{entry_id}",
                "duration": duration,
                "thumbnail_url": thumbnail_url,
                "view_count": view_count,
                "is_short": is_short,
            }
            if include_title:
                vid_obj["title"] = entry.get("title", "Unknown")
            playlist_data.append(vid_obj)
        return playlist_data

    def _classify_and_print_ytdlp_error(self, capture, playlist_url: str) -> bool:
        """Classify and print user-friendly messages for yt-dlp stderr output.

        Args:
            capture: StderrCapture object with classified error info
            playlist_url: The playlist URL being processed

        Returns:
            True if an error was found and handled, False otherwise
        """
        if not capture.had_output():
            return False
        category, user_msg = capture.get_error_category()
        if not (category and user_msg):
            return False
        from yt_fts.utils.dual_sink_logger import log_operation

        log_operation(
            "get_playlist_data",
            "yt-dlp stderr captured and classified",
            level=20,
            category=category.value if hasattr(category, "value") else str(category),
            user_message=user_msg,
            playlist_url=playlist_url,
        )
        from yt_fts.utils.error_classifier import ErrorCategory

        if category == ErrorCategory.RATE_LIMITED:
            self._print_message(f"[yellow]⚠️  {user_msg}[/yellow]")
        elif category == ErrorCategory.CHANNEL_NOT_FOUND:
            self._print_message(f"[red]❌ {user_msg}[/red]")
        elif category == ErrorCategory.TIMEOUT:
            self._print_message(f"[yellow]⏱️  {user_msg}[/yellow]")
        elif category == ErrorCategory.NETWORK_ERROR:
            self._print_message(f"[yellow]🌐 {user_msg}[/yellow]")
        return True

    def get_playlist_data(self, playlist_url: str) -> list[dict[str, str]]:
        """
        Get playlist data with timeout, progress feedback, and comprehensive logging to diagnose delays.
        """
        import time

        start_time = time.time()
        with LoggedDownloadOperation("get_playlist_data", playlist_url=playlist_url):
            with self._conditional_status(
                "[bold green]Fetching channel video list...[/bold green]"
            ):
                log_operation(
                    "get_playlist_data",
                    "Starting yt-dlp extract_info call",
                    level=10,
                    playlist_url=playlist_url,
                    socket_timeout=30,
                    extract_flat=True,
                )
                ydl_opts: dict[str, Any] = {
                    "http_headers": {"User-Agent": random.choice(self._user_agents)},
                    "quiet": True,
                    "noprogress": True,
                    "extract_flat": True,
                    "socket_timeout": 30,
                    "retries": 2,
                    "no_warnings": True,
                    "logger": YtdlpSilentLogger(),
                }
                try:
                    extract_start = time.time()
                    capture: StderrCapture | None = None
                    with StderrCapture() as capture:
                        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                            log_operation(
                                "get_playlist_data",
                                "Calling yt-dlp extract_info",
                                level=10,
                                ydl_opts=ydl_opts,
                            )
                            info = ydl.extract_info(playlist_url, download=False)
                            extract_duration = (time.time() - extract_start) * 1000
                            log_operation(
                                "get_playlist_data",
                                "yt-dlp extract_info completed",
                                level=10,
                                duration_ms=extract_duration,
                                has_entries=bool(info and info.get("entries")),
                            )
                    self._classify_and_print_ytdlp_error(capture, playlist_url)

                    if not info or "entries" not in info:
                        msg = "No videos found for channel"
                        raise Exception(msg)
                    entries = info.get("entries", [])
                    if not entries:
                        self._print_message(
                            "[yellow]⚠️  No videos found for this channel[/yellow]"
                        )
                        log_operation("get_playlist_data", "No entries found", level=10)
                        return []
                    parent_channel_id = info.get("channel_id", "")
                    parent_channel_name = info.get(
                        "channel", info.get("uploader", "Unknown Channel")
                    )
                    log_operation(
                        "get_playlist_data",
                        "Extracted parent channel info",
                        level=10,
                        parent_channel_id=parent_channel_id,
                        parent_channel_name=parent_channel_name,
                    )
                    log_operation(
                        "get_playlist_data",
                        f"Fetching {len(entries)} video entries from YouTube",
                        level=10,
                        entry_count=len(entries),
                    )
                    processing_start = time.time()
                    playlist_data = self._process_video_entries(
                        entries, parent_channel_id, parent_channel_name
                    )
                    processing_duration = (time.time() - processing_start) * 1000
                    total_duration = (time.time() - start_time) * 1000
                    log_operation(
                        "get_playlist_data",
                        "Video entry processing completed",
                        level=10,
                        processing_duration_ms=processing_duration,
                        total_duration_ms=total_duration,
                        valid_entries=len(playlist_data),
                        total_entries=len(entries),
                    )
                    return playlist_data
                except TimeoutError:
                    timeout_duration = (time.time() - start_time) * 1000
                    log_technical_error(
                        TimeoutError("Network timeout during yt-dlp extraction"),
                        {
                            "operation": "get_playlist_data",
                            "playlist_url": playlist_url,
                            "duration_ms": timeout_duration,
                            "socket_timeout": 30,
                        },
                    )
                    self._print_message(
                        "[red]❌ Timeout while fetching channel video list[/red]"
                    )
                    msg = "Network timeout - please check your connection and try again"
                    raise Exception(msg)
                except Exception as e:
                    error_duration = (time.time() - start_time) * 1000
                    error_msg = str(e).lower()
                    # Fallback-eligible errors: /videos endpoint issues, invalid URL format, or empty channel
                    is_fallback_eligible = "/videos" in playlist_url or any(
                        phrase in error_msg
                        for phrase in [
                            "does not have a videos tab",
                            "http error 400",
                            "http error 404",
                            "no videos found",
                            "is not a valid url",
                            "unsupported url",
                        ]
                    )
                    if is_fallback_eligible:
                        # Strip /videos or /streams suffix if present
                        base_url = playlist_url.replace("/videos", "").replace(
                            "/streams", ""
                        )
                        # For handle URLs like @TwoMinutePapers, convert to full URL if needed
                        if base_url.startswith("@") and "youtube.com" not in base_url:
                            base_url = f"https://www.youtube.com/{base_url}"
                        log_operation(
                            "get_playlist_data",
                            "Channel fetch failed, trying base URL",
                            level=20,
                            original_url=playlist_url,
                            fallback_url=base_url,
                            error=error_msg[:100],
                        )
                        try:
                            with StderrCapture() as capture:
                                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                    info = ydl.extract_info(base_url, download=False)
                            if info and "entries" in info:
                                entries = info.get("entries", [])
                                if entries:
                                    parent_channel_id = info.get("channel_id", "")
                                    parent_channel_name = info.get(
                                        "channel",
                                        info.get("uploader", "Unknown Channel"),
                                    )
                                    playlist_data = self._process_video_entries(
                                        entries,
                                        parent_channel_id,
                                        parent_channel_name,
                                        include_title=True,
                                    )
                                    log_operation(
                                        "get_playlist_data",
                                        f"Base URL fallback successful: found {len(playlist_data)} videos",
                                        level=20,
                                    )
                                    return playlist_data
                                # Channel exists but has no videos
                                log_operation(
                                    "get_playlist_data",
                                    "Base URL fallback successful: channel has no videos",
                                    level=20,
                                )
                                return []
                        except Exception as fallback_error:
                            log_operation(
                                "get_playlist_data",
                                f"Base URL fallback also failed: {fallback_error}",
                                level=20,
                            )
                    # Only log technical error and raise if fallback didn't succeed
                    log_technical_error(
                        e,
                        {
                            "operation": "get_playlist_data",
                            "playlist_url": playlist_url,
                            "duration_ms": error_duration,
                            "stage": "yt_dlp_extraction",
                            "fallback_attempted": is_fallback_eligible,
                        },
                    )
                    raise BaseURLFallbackFailed(str(e)) from e

    def _cancel_remaining_futures(self, futures):
        """Cancel all pending futures.

        Args:
            futures: Dict of Future to video_id mappings
        """
        uncancelled = [f for f in futures if not f.done()]
        if uncancelled:
            self.logger.debug("Cancelling %s remaining futures", len(uncancelled))
            for f in uncancelled:
                f.cancel()

    def _handle_target_reached(self, futures: dict) -> bool:
        """Handle the case when min_saved target is reached.

        Args:
            futures: Dict of Future to video_id mappings

        Returns:
            True to signal we should break from the download loop
        """
        if self._rich_progress is not None:
            try:
                if self._rich_task_id:
                    self._rich_progress.stop_task(self._rich_task_id)
                self._rich_progress.__exit__(None, None, None)
            except Exception:
                pass
            self._rich_progress = None
            self._rich_task_id = None
        if self._progress_console:
            self._progress_console.print("")
        self._print_message(
            f"   ⎿ [cyan]✓[/cyan] Reached target of {self.min_saved} videos saved, stopping..."
        )
        for f in futures:
            if not f.done():
                remaining_vid = futures[f]
                self.videos_without_subs_list.append(remaining_vid)
        self._cancel_remaining_futures(futures)
        return True

    def _handle_videos_without_subtitles_summary(self) -> None:
        """Display summary of videos without subtitles and update database."""
        if self.videos_without_subtitles > 0:
            if not self.suppress_status_messages:
                video_word = "video" if self.videos_without_subtitles == 1 else "videos"
                self._print_message(
                    f"[yellow]⚠️  No subtitles for {self.videos_without_subtitles} {video_word}, nothing to save[/yellow]"
                )
            self._add_videos_without_subtitles_to_db()

    def _check_timeout(self, cancelling: bool = False) -> bool:
        """Check if channel timeout has been reached.

        Args:
            cancelling: True if cancelling remaining downloads, False if just stopping

        Returns:
            True if timeout was reached, False otherwise
        """
        if not (self.max_time_per_channel and self.max_time_per_channel > 0):
            return False
        import time

        elapsed = time.time() - self.download_start_time
        if elapsed >= self.max_time_per_channel:
            msg = (
                f"[yellow]⏱️  Timeout reached ({self.max_time_per_channel}s). Cancelling remaining downloads...[/yellow]"
                if cancelling
                else f"[yellow]⏱️  Timeout reached ({self.max_time_per_channel}s). Stopping downloads...[/yellow]"
            )
            self._print_message(msg)
            return True
        return False

    def download_vtts(self) -> None:
        """Download VTT files with progress tracking and optional timeout."""
        self._initialize_download_state()
        if not self.progress_coordinator:
            total_videos = len(self.video_ids)
            print(f"  Downloading {total_videos} video(s)...")
        executor, futures = self._submit_download_tasks()
        try:
            timeout_reached, target_reached = self._process_downloads(executor, futures)
            if target_reached:
                return
            if timeout_reached:
                self._handle_channel_timeout()
        finally:
            self._cleanup_executor(executor)
        self._handle_videos_without_subtitles_summary()

    def _initialize_download_state(self) -> None:
        """Initialize state for download session."""
        import time

        self._videos_saved_during_download = False
        self.videos_without_subtitles = 0
        self.videos_without_subs_list = []
        self.download_start_time = time.time()

    def _submit_download_tasks(self) -> tuple:
        """Submit download tasks to executor and return executor and futures.

        Initializes worker progress tracking and assigns worker IDs.
        Shows per-worker progress bars even in Rich TUI mode.
        """
        # Initialize worker progress tracker (enabled for all modes except suppress_status_messages)
        if not self.suppress_status_messages:
            self._worker_progress = WorkerProgressTracker(
                self.console, self.number_of_jobs
            )
            self._worker_progress.__enter__()

        executor = ThreadPoolExecutor(self.number_of_jobs)
        futures = {}

        for idx, video_id in enumerate(self.video_ids):
            if self._check_shutdown():
                self._print_message(
                    "[yellow]⚠️  Stopping new video downloads due to interrupt[/yellow]"
                )
                break
            if self._check_timeout():
                break

            # Assign worker ID (round-robin for video reuse)
            worker_id = idx % self.number_of_jobs
            self._worker_assignments[video_id] = worker_id

            # Register worker with progress tracker
            if self._worker_progress:
                self._worker_progress.register_worker(worker_id, video_id)

            video_url = f"https://www.youtube.com/watch?v={video_id}"
            future = executor.submit(
                self.get_vtt, self.tmp_dir or "", video_url, self.language
            )
            futures[future] = video_id

        return (executor, futures)

    def _process_downloads(self, executor, futures: dict) -> tuple[bool, bool]:
        """Process downloads as they complete.

        Returns:
            tuple: (timeout_reached, target_reached)
        """
        from concurrent.futures import as_completed

        total_videos = len(self.video_ids)
        completed = 0
        timeout_reached = False
        target_reached = False
        try:
            for future in as_completed(futures.keys()):
                if self._should_cancel_download(futures, future):
                    target_reached = self._handle_target_reached(futures)
                    break
                timeout_reached = self._process_single_download(
                    future, futures[future], completed, total_videos
                )
                if timeout_reached:
                    break
                completed += 1
        except KeyboardInterrupt:
            self._handle_keyboard_interrupt(futures)
            executor.shutdown(wait=False, cancel_futures=True)
            return (False, True)
        finally:
            self._cancel_remaining_futures(futures)
            # Clean up worker progress tracker
            if self._worker_progress:
                self._worker_progress.__exit__(None, None, None)
                self._worker_progress = None
            self._worker_assignments.clear()
        return (timeout_reached, target_reached)

    def _should_cancel_download(self, futures: dict, future) -> bool:
        """Check if download should be cancelled due to interrupt or timeout."""
        if self._check_shutdown():
            self._print_message("[yellow]⚠️  Download cancelled by user[/yellow]")
            return True
        return bool(self._check_timeout(cancelling=True))

    def _process_single_download(
        self, future, video_id: str, completed: int, total_videos: int
    ) -> bool:
        """Process a single download result.

        Returns:
            bool: True if timeout was reached
        """
        result_timeout = self._calculate_result_timeout()
        result = future.result(timeout=result_timeout)
        self._update_download_progress(completed + 1, total_videos)
        if result:
            self._save_video_to_db(video_id)
            return self._check_min_saved_target()
        self.videos_without_subs_list.append(video_id)
        return False

    def _calculate_result_timeout(self) -> float:
        """Calculate timeout for individual download result."""
        import time

        result_timeout = 10.0
        if self.max_time_per_channel and self.max_time_per_channel > 0:
            remaining = self.max_time_per_channel - (
                time.time() - self.download_start_time
            )
            if remaining <= 0:
                msg = "Channel timeout exceeded"
                raise TimeoutError(msg)
            result_timeout = min(result_timeout, remaining)
        return result_timeout

    def _check_min_saved_target(self) -> bool:
        """Check if min_saved target has been reached.

        Returns:
            bool: True if target was reached
        """
        return bool(self.min_saved and self.videos_saved_to_db >= self.min_saved)

    def _handle_channel_timeout(self) -> None:
        """Handle channel timeout."""
        import time

        elapsed = time.time() - self.download_start_time
        self._print_message(
            f"[yellow]⏱️  Download stopped after {elapsed:.1f}s due to timeout[/yellow]"
        )
        msg = f"Download exceeded maximum time limit of {self.max_time_per_channel}s"
        raise DownloadTimeoutException(msg)

    def _handle_keyboard_interrupt(self, futures: dict) -> None:
        """Handle Ctrl+C interrupt during downloads."""
        self._shutdown = True
        self._print_message(
            "[yellow]⚠️  Interrupted by user - cancelling downloads...[/yellow]"
        )
        if self._rich_progress is not None:
            with contextlib.suppress(Exception):
                self._rich_progress.__exit__(None, None, None)
            self._rich_progress = None
            self._rich_task_id = None
        self._cancel_remaining_futures(futures)

    def _cleanup_executor(self, executor) -> None:
        """Clean up thread pool executor."""
        if not executor._shutdown:
            executor.shutdown(wait=False, cancel_futures=True)

    def _add_videos_without_subtitles_to_db(self) -> None:
        """Add videos without subtitles to database, with optional transcription.

        Only marks videos as checked if transcription fails for a permanent reason
        (e.g., video is private, deleted, or unavailable). This ensures videos are
        retried on subsequent runs if transcription hasn't succeeded yet.
        """
        if not self.videos_without_subs_list:
            return
        from datetime import datetime

        from yt_fts.core.database import add_video, get_db_connection

        # Progress bar setup is handled within the loop block if needed

        transcribed_count = 0
        unavailable_count = 0
        failed_count = 0

        num_to_transcribe = len(self.videos_without_subs_list)

        # Define the loop iterator and context manager
        if (
            self.transcribe_audio_only
            and not self.suppress_status_messages
            and num_to_transcribe > 0
        ):
            from rich.progress import BarColumn, Progress, TextColumn

            progress = Progress(
                TextColumn("   ⎿ →"),
                BarColumn(bar_width=20),
                TextColumn("audio -> transcript Whispered"),
                console=self.console,
                transient=False,
            )
            progress.start()
            task_id = progress.add_task("transcribing", total=num_to_transcribe)
            iterator = self.videos_without_subs_list
        else:
            progress = None
            iterator = self.videos_without_subs_list

        try:
            for video_id in iterator:
                try:
                    if self.channel_id is None:
                        self.channel_id = "unknown"

                    self.logger.info(
                        "Attempting transcription for video without subtitles: %s",
                        video_id,
                    )

                    # First, ensure the video exists in the Videos table
                    # This is needed so we can UPDATE it to mark as unavailable if needed
                    add_video(
                        channel_id=self.channel_id,
                        video_id=video_id,
                        video_title="[No Subtitles]",
                        video_url=f"https://youtu.be/{video_id}",
                        video_date="",
                        last_checked=datetime.now().isoformat(),
                    )

                    # Attempt transcription - returns True if succeeded
                    transcription_succeeded = self._attempt_transcription(video_id)

                    if transcription_succeeded:
                        # Transcription succeeded - subtitles saved to DB, update title
                        with get_db_connection() as conn:
                            conn.execute(
                                "UPDATE Videos SET video_title = '[Transcribed]', last_checked = ? WHERE video_id = ?",
                                (datetime.now().isoformat(), video_id),
                            )
                            conn.commit()
                        self.logger.info(
                            "✓ Transcribed video successfully: %s", video_id
                        )
                        transcribed_count += 1
                    elif self._should_mark_video_unavailable(video_id):
                        # Video is permanently unavailable (private, deleted, region-locked, etc.)
                        with get_db_connection() as conn:
                            conn.execute(
                                "UPDATE Videos SET video_title = '[Unavailable]', last_checked = ? WHERE video_id = ?",
                                (datetime.now().isoformat(), video_id),
                            )
                            conn.commit()
                        self.logger.info("✗ Marked video as unavailable: %s", video_id)
                        unavailable_count += 1
                    else:
                        # Transcription failed for a transient reason or is still in progress
                        # Don't mark - will retry on next run (fail-fast if issue persists)
                        self.logger.warning(
                            "✗ Transcription failed for %s (will retry)", video_id
                        )
                        failed_count += 1
                    if progress:
                        progress.advance(task_id)
                except Exception as e:
                    self.logger.debug(
                        "Failed to add video %s to database: %s", video_id, e
                    )
                    failed_count += 1
                    if progress:
                        progress.advance(task_id)
        finally:
            if progress:
                progress.stop()

        # Print transcription summary
        if (
            self.transcribe_audio_only
            and not self.suppress_status_messages
            and num_to_transcribe > 0
        ):
            parts = []
            if transcribed_count > 0:
                parts.append(f"[green]✓ {transcribed_count} transcribed[/green]")
            if unavailable_count > 0:
                parts.append(
                    f"[yellow]✗ {unavailable_count} unavailable (will retry)[/yellow]"
                )
            if failed_count > 0:
                parts.append(f"[red]✗ {failed_count} failed (will retry)[/red]")
            if parts:
                self._print_message(f"  {' | '.join(parts)}")

    def _get_whisper_engine(self):
        """Lazy-load the Whisper engine for transcription."""
        if not hasattr(self, "_whisper_engine"):
            try:
                from yt_fts.transcribe import LocalWhisperEngine

                self._whisper_engine = LocalWhisperEngine(model_size=self.whisper_model)
            except ImportError as e:
                self.logger.debug("Whisper not available (import error): %s", e)
                self._whisper_engine = None
            except Exception as e:
                self.logger.debug("Whisper initialization failed: %s", e)
                self._whisper_engine = None
        return self._whisper_engine

    def _download_audio_for_transcription(
        self, video_id: str, tmp_dir: str | None = None
    ) -> str | None:
        """Download audio file for transcription using yt-dlp.

        Marks videos that fail permanently (private, deleted, region-locked) so
        they won't be retried on subsequent backfill runs.
        """
        if tmp_dir is None:
            tmp_dir = self.tmp_dir
        if tmp_dir is None:
            tmp_dir = tempfile.gettempdir()
        video_url = f"https://www.youtube.com/watch?v={video_id}"
        audio_base = Path(tmp_dir) / f"{video_id}_audio"
        ydl_opts: dict[str, Any] = {
            "format": "m4a/bestaudio/best",
            "outtmpl": str(audio_base),
            "quiet": True,
            "no_warnings": True,
            "overwrite": True,
        }
        try:
            import yt_dlp

            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])
            for ext in [".m4a", ".webm", ".mp3"]:
                candidate = audio_base.with_suffix(ext)
                if candidate.exists():
                    return str(candidate)
            if audio_base.exists():
                return str(audio_base)
            return None
        except Exception as e:
            error_msg = str(e).lower()
            # Check for permanent failure indicators
            permanent_failure_indicators = [
                "live event",
                "will begin",
                "private",
                "unavailable",
                "deleted",
                "not found",
                "region",
                "country",
                "age gate",
            ]
            is_permanent_failure = any(
                indicator in error_msg for indicator in permanent_failure_indicators
            )

            if is_permanent_failure:
                # Mark this video as permanently unavailable
                setattr(self, f"_audio_download_failed_{video_id}", True)
                self.logger.debug("Permanent failure for %s: %s", video_id, e)
            else:
                self.logger.debug("Failed to download audio for %s: %s", video_id, e)
            return None

    def _get_transcript_source_type(self, transcript):
        """Get the source type string from a Transcript object."""
        from yt_fts.transcribe.schema import SourceType

        if isinstance(transcript.source_type, SourceType):
            return transcript.source_type.value
        return str(transcript.source_type)

    def _save_transcript_to_db(self, transcript) -> None:
        """Save a transcribed transcript to the database."""
        from sqlite_utils import Database

        from yt_fts.utils.config import get_db_path

        db = Database(get_db_path())
        for chunk in transcript.chunks:
            start = int(chunk.start_time)
            duration = getattr(chunk, "duration", None)
            stop = int(start + duration) if duration else int(start + 5)
            db["Subtitles"].insert(
                {
                    "video_id": transcript.video_id,
                    "start_time": str(start),
                    "stop_time": str(stop),
                    "text": chunk.text,
                    "source_type": self._get_transcript_source_type(transcript),
                    "language_code": self.language,
                }
            )

    def _transcribe_and_cleanup(self, video_id: str, audio_path: str) -> None:
        """Transcribe audio file and clean up the temporary file."""
        engine = self._get_whisper_engine()
        if engine is None:
            self.logger.debug(
                "Whisper engine not available, skipping transcription for %s", video_id
            )
            return
        try:
            transcript = engine.transcribe(audio_path, video_id, language=self.language)
            self._save_transcript_to_db(transcript)
        except Exception as e:
            self.logger.debug("Transcription failed for %s: %s", video_id, e)
        finally:
            if not self.keep_audio:
                with contextlib.suppress(Exception):
                    Path(audio_path).unlink(missing_ok=True)

    def _attempt_transcription(self, video_id: str) -> bool:
        """Attempt to transcribe a video using Whisper.

        Returns:
            True if transcription succeeded and subtitles were saved,
            False otherwise (Whisper unavailable, download failed, or transcription failed).
        """
        engine = self._get_whisper_engine()
        if engine is None:
            self.logger.debug(
                "Whisper not available, skipping transcription for %s", video_id
            )
            return False
        audio_path = self._download_audio_for_transcription(video_id)
        if audio_path:
            try:
                self._transcribe_and_cleanup(video_id, audio_path)
                return True  # Transcription succeeded
            except Exception as e:
                self.logger.debug(
                    "Transcription attempt failed for %s: %s", video_id, e
                )
                if not self.keep_audio:
                    with contextlib.suppress(Exception):
                        Path(audio_path).unlink(missing_ok=True)
        return False  # Audio download failed or transcription error

    def _should_mark_video_unavailable(self, video_id: str) -> bool:
        """Check if a video should be marked as unavailable.

        A video should be marked unavailable if audio download failed due to
        the video being private, deleted, or region-locked (not a transient error).

        Returns:
            True if video should be marked unavailable, False otherwise.
        """
        # Check if we already tried to download audio and it failed
        # This is stored as a transient attribute during the download attempt
        return getattr(self, f"_audio_download_failed_{video_id}", False)

    def quiet_progress_hook(self, d: dict[str, Any]) -> None:
        """Truly quiet progress hook - no output during downloads."""

    def _interrupting_progress_hook(self, d: dict[str, Any]) -> None:
        """Abort downloads quickly when an interrupt is requested."""
        if self._interrupted():
            try:
                from yt_dlp.utils import DownloadCancelled

                msg = "Download cancelled by user"
                raise DownloadCancelled(msg)
            except Exception as e:
                msg = "Download cancelled by user"
                raise RuntimeError(msg) from e
        if self._worker_progress:
            self._worker_progress_hook(d)
        else:
            self.quiet_progress_hook(d)

    def _worker_progress_hook(self, d: dict[str, Any]) -> None:
        """Progress hook that updates per-worker progress bars.

        Called by yt-dlp during download to report real-time progress.
        Updates the WorkerProgressTracker with download status.

        Args:
            d: Progress dictionary from yt-dlp containing:
                - status: 'downloading', 'error', or 'finished'
                - downloaded_bytes: bytes downloaded so far
                - total_bytes: total file size
                - speed: download speed in bytes/sec
                - eta: estimated time remaining
                - filename: download filename (contains video_id)
        """
        if d.get("status") == "downloading":
            # Extract progress data
            downloaded = d.get("downloaded_bytes", 0)
            total = d.get("total_bytes") or d.get("total_bytes_estimate") or 0
            speed = d.get("speed", 0)
            eta = d.get("eta")

            # Extract video_id from filename or info_dict
            video_id = self._extract_video_id_from_progress_hook(d)

            if video_id and self._worker_progress:
                worker_id = self._worker_assignments.get(video_id)
                if worker_id is not None:
                    self._worker_progress.update_worker_progress(
                        worker_id, downloaded, total, speed, eta
                    )

        elif d.get("status") == "finished":
            # Mark worker task as complete
            video_id = self._extract_video_id_from_progress_hook(d)
            if video_id and self._worker_progress:
                worker_id = self._worker_assignments.get(video_id)
                if worker_id is not None:
                    self._worker_progress.finish_worker(worker_id, success=True)

    def _extract_video_id_from_progress_hook(self, d: dict[str, Any]) -> str | None:
        """Extract video_id from yt-dlp progress hook dictionary.

        Args:
            d: Progress dictionary from yt-dlp

        Returns:
            Video ID string or None if not found
        """
        # Try to get from filename
        filename = d.get("filename", "")
        if filename:
            # Filename format is typically: tmp_dir/video_id.ext
            import os

            basename = os.path.basename(filename)
            # Remove extension
            video_id = os.path.splitext(basename)[0]
            if len(video_id) == 11:  # YouTube video IDs are 11 characters
                return video_id

        # Try to get from info_dict
        info_dict = d.get("info_dict", {})
        if isinstance(info_dict, dict):
            video_id = info_dict.get("id")
            if video_id:
                return video_id

        return None

    def _extract_info_with_timeout(
        self, ydl, url: str, timeout: float | None
    ) -> dict | None:
        """Wrap ydl.extract_info with per-video timeout."""
        if self._interrupted():
            return None
        if timeout is None or timeout <= 0:
            return ydl.extract_info(url, download=False)
        import threading
        import time as _time

        result = [None]
        exception = [None]

        def worker():
            try:
                result[0] = ydl.extract_info(url, download=False)
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        deadline = _time.time() + timeout
        while thread.is_alive() and _time.time() < deadline:
            if self._interrupted():
                return None
            thread.join(timeout=0.1)
        if thread.is_alive():
            msg = f"extract_info exceeded {timeout}s timeout"
            raise PerVideoTimeoutException(msg)
        if exception[0] is not None:
            raise exception[0]
        return result[0]

    def _download_with_timeout(self, ydl, url: str, timeout: float | None) -> None:
        """Wrap ydl.download with per-video timeout."""
        if self._interrupted():
            return None
        if timeout is None or timeout <= 0:
            return ydl.download([url])
        import threading
        import time as _time

        result = [None]
        exception = [None]

        def worker():
            try:
                result[0] = ydl.download([url])
            except Exception as e:
                exception[0] = e

        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
        deadline = _time.time() + timeout
        while thread.is_alive() and _time.time() < deadline:
            if self._interrupted():
                return None
            thread.join(timeout=0.1)
        if thread.is_alive():
            msg = f"download exceeded {timeout}s timeout"
            raise PerVideoTimeoutException(msg)
        if exception[0] is not None:
            raise exception[0]
        return result[0]

    def get_vtt(self, tmp_dir: str, video_url: str, language: str) -> str | None:
        """
        Download VTT file for a single video.

        Returns:
            video_id (str) on success, None on failure
        """
        if self._interrupted():
            return None
        video_id = self._extract_video_id_from_url(video_url)
        if not video_id:
            return None
        if self._respect_rate_limiting_delays():
            return None
        max_retries = 5
        retry_delay = 3
        for attempt in range(max_retries):
            if self._interrupted():
                return None
            try:
                return self._attempt_vtt_download(video_url, video_id)
            except Exception as e:
                should_continue = self._handle_download_error(
                    e, attempt, max_retries, retry_delay, video_url, video_id
                )
                if not should_continue:
                    break
                if attempt < max_retries - 1:
                    retry_delay *= 2
        return None

    def _extract_video_id_from_url(self, video_url: str) -> str | None:
        """Extract video ID from YouTube URL."""
        return video_url.split("?v=")[-1].split("&")[0] if "?v=" in video_url else None

    def _respect_rate_limiting_delays(self) -> bool:
        """Apply configured and rate-limiter recommended delays."""

        if getattr(self, "per_video_delay", 0) and self.per_video_delay > 0:
            if self._interruptible_sleep(self.per_video_delay):
                return True
        try:
            if hasattr(self, "rate_limiter") and self.channel_id:
                suggested = float(self.rate_limiter.before_request(self.channel_id))
                if suggested and suggested > getattr(self, "per_video_delay", 0):
                    if self._interruptible_sleep(suggested):
                        return True
        except Exception as e:
            self.logger.debug("Rate limiter check failed: %s", e)
        return False

    def _attempt_vtt_download(self, video_url: str, video_id: str) -> tuple:
        """Attempt to download VTT file for a video.

        Returns:
            tuple: (video_id, info) on success

        Raises:
            Exception: If download fails
        """
        if self._interrupted():
            return None
        ydl_opts = self._build_vtt_ydl_options(video_id)
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            if self._interrupted():
                return None
            if self.log_callback:
                self.log_callback(f"[dim]→ {video_id}: enumerated[/dim]")
            _available_subs, _auto_subs, should_skip = (
                self._check_subtitle_availability(ydl, video_url, video_id)
            )
            if should_skip:
                return None
            if self.log_callback:
                self.log_callback(f"[dim]→ {video_id}: downloading...[/dim]")
            try:
                self._download_with_timeout(
                    ydl, video_url, getattr(self, "max_time_per_video", None)
                )
            except PerVideoTimeoutException as e:
                self.logger.warning("Download timeout for %s: %s", video_id, e)
                return None
            if self.log_callback:
                self.log_callback(f"[dim]→ {video_id}: downloaded[/dim]")
            if not self._verify_vtt_file_created(video_id):
                self.logger.debug("VTT file not created for %s", video_id)
                return None
            info_path = Path(self.tmp_dir) / f"{video_id}.info.json"
            info = {}
            if info_path.exists():
                import json

                with contextlib.suppress(Exception):
                    info = json.loads(info_path.read_text(encoding="utf-8"))
            return (video_id, info)

    def _handle_download_error(
        self,
        error: Exception,
        attempt: int,
        max_retries: int,
        retry_delay: float,
        video_url: str,
        video_id: str,
    ) -> bool:
        """Handle download error during retry loop.

        Returns:
            bool: True if should continue retrying, False to abort
        """
        if self._interrupted():
            return False
        error_msg = self._sanitize_error_message(error)
        from yt_fts.utils import summarize_error

        short = summarize_error(error_msg)
        if self._is_scheduled_live_event(error_msg):
            self._print_scheduled_live_message(short)
            return False
        if "403" in error_msg or "Forbidden" in error_msg:
            self._handle_403_error(error_msg)
            return attempt < max_retries - 1
        # 404 errors may be transient rate limits - retry with backoff
        if "404" in error_msg:
            return attempt < max_retries - 1
        if self._is_rate_limit_error(error_msg):
            return self._handle_429_error(
                error_msg, attempt, max_retries, retry_delay, video_url
            )
        return self._handle_generic_error(
            error_msg, short, attempt, max_retries, retry_delay, video_url
        )

    def _sanitize_error_message(self, error: Exception) -> str:
        """Sanitize error message, handling yt-dlp file object bugs."""
        error_msg = str(error) if error else "Unknown error"
        if isinstance(error, KeyError) and (
            "<_io." in error_msg or "mode=" in error_msg
        ):
            return "KeyError: Missing required data in download response"
        if "<_io.TextIOWrapper" in error_msg or "<iomwrappers" in error_msg:
            if error.args:
                for arg in error.args:
                    arg_str = str(arg)
                    if not any(x in arg_str for x in ["<_io.", "mode=", "encoding="]):
                        return f"{type(error).__name__}: {arg_str}"
            return f"{type(error).__name__}: Data access error during download"
        return error_msg

    def _is_scheduled_live_event(self, error_msg: str) -> bool:
        """Check if error indicates a scheduled live event."""
        low = error_msg.lower()
        return "will begin in" in low or "this live event will begin" in low

    def _print_scheduled_live_message(self, short_error: str) -> None:
        """Print message about skipping scheduled live event."""
        try:
            if not self.suppress_status_messages:
                self._print_message(
                    f"[yellow]Skipping scheduled live: {short_error}[/yellow]"
                )
        except Exception as e:
            self.logger.debug("Failed to print scheduled live message: %s", e)

    def _is_rate_limit_error(self, error_msg: str) -> bool:
        """Check if error is a rate limit response."""
        return (
            "429" in error_msg
            or "Too Many Requests" in error_msg
            or "rate-limited" in error_msg.lower()
        )

    def _handle_403_error(self, error_msg: str) -> None:
        """Handle 403 Forbidden error with diagnostic messages."""
        self.rate_limit_count += 1
        try:
            if hasattr(self, "rate_limiter") and self.channel_id:
                self.rate_limiter.on_rate_limit(self.channel_id, error_msg)
        except Exception as e:
            self.logger.debug("Failed to notify rate limiter (403): %s", e)
        self._print_message(
            "[red]403 Forbidden detected - request blocked by server[/red]"
        )
        self._print_message("[yellow]Possible causes:[/yellow]")
        self._print_message("  • Rate limiting (too many requests too quickly)")
        self._print_message("  • Missing or invalid cookies")
        self._print_message("  • IP address is blocked")
        self._print_message("  • User-Agent detection")
        self._print_message("  • Reduce parallel jobs (use -j 1-3)")
        self._print_message("  • Wait a few minutes and retry")
        self._print_message("  • Verify video availability in your region")

    def _handle_429_error(
        self,
        error_msg: str,
        attempt: int,
        max_retries: int,
        retry_delay: float,
        video_url: str,
    ) -> bool:
        """Handle 429 rate limit error.

        Returns:
            bool: True if should retry, False if exhausted
        """
        self.rate_limit_count += 1
        try:
            if hasattr(self, "rate_limiter") and self.channel_id:
                self.rate_limiter.on_rate_limit(self.channel_id, error_msg)
        except Exception as e:
            self.logger.debug("Failed to notify rate limiter (429): %s", e)
        self._print_message("[red]429 Too Many Requests - Rate limit exceeded[/red]")
        if attempt < max_retries - 1:
            wait_time = retry_delay * 5
            if not self.suppress_status_messages:
                self._print_message(
                    f"[yellow]Waiting {wait_time} seconds before retry...[/yellow]"
                )
            import time

            time.sleep(wait_time)
            return True
        self._print_message(f"[red]Rate limit exceeded for: {video_url}[/red]")
        self._print_message(
            "[yellow]Try reducing parallel jobs or wait longer[/yellow]"
        )
        return False

    def _handle_generic_error(
        self,
        error_msg: str,
        short_error: str,
        attempt: int,
        max_retries: int,
        retry_delay: float,
        video_url: str,
    ) -> bool:
        """Handle generic download error with retry logic.

        Returns:
            bool: True if should retry, False if exhausted
        """
        is_transient = (
            "Missing required data in download response" in short_error
            or "Data access error" in short_error
        )
        should_warn = not is_transient or attempt + 1 >= max_retries
        if not self.suppress_status_messages and should_warn:
            self._print_message(
                f"[yellow]Attempt {attempt + 1}/{max_retries} failed for: {video_url}[/yellow]"
            )
            self._print_message(f"[red]Warning: {short_error}[/red]")
        if attempt < max_retries - 1:
            if not self.suppress_status_messages:
                self._print_message(
                    f"[yellow]Waiting {retry_delay} seconds before retry...[/yellow]"
                )
            import time

            time.sleep(retry_delay)
            return True
        self._print_message(f"[red]Failed to get: {video_url}[/red]")
        self._print_message(f"[red]Error: {error_msg}[/red]")
        return False

    def _save_video_to_db(self, video_id: str, info: dict | None = None) -> None:
        """
        Save a single video's VTT file to the database immediately after download.

        This allows the download to be resumed if interrupted, as each video is saved
        as soon as it completes downloading rather than waiting for all downloads to finish.

        Args:
            video_id: The YouTube video ID to save
            info: yt-dlp info dict containing metadata (duration, view_count, thumbnail, etc.)
        """
        from pathlib import Path

        if not self.tmp_dir:
            return
        vtt_path = Path(self.tmp_dir) / f"{video_id}.en.vtt"
        if not Path(vtt_path).exists():
            return
        try:
            if info and isinstance(info, dict):
                vid_title = info.get("title", "")
                vid_date = (
                    get_date(info.get("upload_date", ""))
                    if info.get("upload_date")
                    else ""
                )
                channel_id = info.get("channel_id", "")
                duration = info.get("duration")
                thumbnail_url = info.get("thumbnail", "")
                view_count = info.get("view_count")
                vid_url = f"https://youtu.be/{video_id}"
            else:
                return
            from yt_fts.core.database import add_video

            self.logger.debug(
                "Saving video %s with channel_id=%s", video_id, channel_id
            )
            is_short = 1 if duration and duration < 60 else 0
            from yt_fts.db.infra import _db_write_lock as db_write_lock

            with db_write_lock:
                from datetime import datetime

                add_video(
                    channel_id,
                    video_id,
                    vid_title,
                    vid_url,
                    vid_date,
                    last_checked=datetime.now().isoformat(),
                    duration=int(duration) if duration else None,
                    thumbnail_url=thumbnail_url,
                    view_count=view_count,
                    is_short=is_short,
                )
                from yt_fts.core.database import get_db_connection
                from yt_fts.utils import parse_vtt

                vtt_json = parse_vtt(vtt_path)
                con = get_db_connection(timeout=30.0)
                cur = con.cursor()
                for sub in vtt_json:
                    start_time = sub["start_time"]
                    stop_time = sub["stop_time"]
                    text = sub["text"]
                    cur.execute(
                        "\n                        INSERT INTO Subtitles (video_id, start_time, stop_time, text)\n                        VALUES (?, ?, ?, ?)\n                        ",
                        (video_id, start_time, stop_time, text),
                    )
                con.commit()
                con.close()
            self._videos_saved_during_download = True
            self.videos_saved_to_db += 1
            if self.progress_callback:
                total = (
                    self.total_videos or len(self.video_ids)
                    if self.video_ids
                    else self.videos_saved_to_db
                )
                self.progress_callback(self.videos_saved_to_db, total)
            if self.log_callback:
                self.log_callback(f"[green]→ {video_id}: stored[/green]")
        except Exception as e:
            self._print_message(
                f"[yellow]Warning: Failed to save {video_id} to database: {e!s}[/yellow]"
            )

    def _build_vtt_ydl_options(self, video_id: str) -> dict[str, Any]:
        """Build yt-dlp options for VTT subtitle download.

        Args:
            video_id: Video ID being downloaded

        Returns:
            Dictionary of yt-dlp options
        """
        import random

        from .output_utils import YtdlpSilentLogger

        headers = {
            "User-Agent": random.choice(self._user_agents),
            "Accept": "*/*",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin",
            "X-YouTube-Client-Name": "1",
            "X-YouTube-Client-Version": "2.0",
        }
        ydl_opts: dict[str, Any] = {
            "http_headers": headers,
            "outtmpl": f"{self.tmp_dir}/%(id)s",
            "writeinfojson": True,
            "writeautomaticsub": True,
            "subtitlesformat": "vtt",
            "skip_download": True,
            "subtitleslangs": ["en", "en-US", "en-GB", "en-US,auto", "-live_chat"],
            "quiet": True,
            "no_warnings": True,
            "noprogress": True,
            # Use interrupt-aware hook to allow fast cancellation
            "progress_hooks": [self._interrupting_progress_hook],
            "nocheckcertificate": True,
            "ignoreerrors": True,
            "no_color": True,
            "sleep_interval": 5,
            "max_sleep_interval": 10,
            "retries": 8,
            "fragment_retries": 8,
            "skip_unavailable_fragments": True,
            "extractor_args": {
                "youtubetab": ["skip=authcheck"],
                "youtube": ["skip=bypass"],
                "youtube:tab": ["skip=webpage"],
            },
            "extractor_retries": 15,
            "fragment_retries": 15,
            "socket_timeout": 45,
            "extract_flat": False,
            "simulate": False,
            "logger": YtdlpSilentLogger(),
        }
        if self.cookies_from_browser is not None:
            ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return ydl_opts

    def _check_subtitle_availability(
        self, ydl, video_url: str, video_id: str
    ) -> tuple[list[str], list[str], bool]:
        """Check what subtitles are available for a video.

        Args:
            ydl: YoutubeDL instance
            video_url: Video URL
            video_id: Video ID

        Returns:
            Tuple of (available_subs, auto_subs, should_skip)
        """
        try:
            info = self._extract_info_with_timeout(
                ydl, video_url, getattr(self, "max_time_per_video", None)
            )
        except Exception:
            return ([], [], False)
        if not info:
            return ([], [], False)

        # Check for filter reasons and track them
        if self._is_short_video(video_url):
            self._track_filter_reason("shorts", video_id)
        elif self._is_scheduled_video(info):
            self._track_filter_reason("scheduled", video_id)
        elif self._has_no_subtitles(info):
            self._track_filter_reason("no_subtitles", video_id)

        available_subs = list(info.get("subtitles", {}).keys())
        auto_subs = list(info.get("automatic_captions", {}).keys())
        if available_subs:
            if self.log_callback:
                self.log_callback(
                    f"[dim]→ {video_id}: transcript available (manual)[/dim]"
                )
        elif auto_subs and self.log_callback:
            self.log_callback(f"[dim]→ {video_id}: transcript available (auto)[/dim]")
        should_skip = not available_subs and (not auto_subs)
        if should_skip:
            self.videos_without_subtitles += 1
        return (available_subs, auto_subs, should_skip)

    def _verify_vtt_file_created(self, video_id: str) -> bool:
        """Verify that at least one VTT variant was created.

        Args:
            video_id: Video ID to check

        Returns:
            True if any VTT file exists
        """
        import os

        vtt_variants = [
            f"{video_id}.en.vtt",
            f"{video_id}.en-US.vtt",
            f"{video_id}.en-GB.vtt",
            f"{video_id}.{self.language}.vtt",
        ]
        for vtt_path in [Path(self.tmp_dir) / v for v in vtt_variants]:
            if os.path.exists(vtt_path):
                return True
        return False

    def _extract_video_metadata(self, vid_json_path, vid_id):
        """Extract video metadata from info.json file.

        Args:
            vid_json_path: Path to info.json file
            vid_id: Video ID

        Returns:
            Tuple of (vid_title, vid_date, channel_id, thumbnail_url, duration, view_count, is_short, category, description)
            or None if extraction fails
        """
        import json

        try:
            with vid_json_path.open(encoding="utf-8", errors="ignore") as f:
                vid_json = json.load(f)
        except (json.JSONDecodeError, KeyError):
            return None
        vid_title = vid_json["title"]
        vid_date = get_date(vid_json["upload_date"])
        channel_id = vid_json["channel_id"]
        thumbnail_url = vid_json.get("thumbnail", "")
        duration = vid_json.get("duration")
        view_count = vid_json.get("view_count", 0)
        is_short = 1 if vid_json.get("webpage_url", "").find("/shorts/") >= 0 else 0
        categories = vid_json.get("categories", [])
        category = categories[0] if categories else ""
        description = vid_json.get("description", "")
        if len(description) > 200:
            description = description[:197] + "..."
        return (
            vid_title,
            vid_date,
            channel_id,
            thumbnail_url,
            duration,
            view_count,
            is_short,
            category,
            description,
        )

    def _upsert_video_to_db(
        self,
        cur,
        vid_id,
        vid_title,
        vid_url,
        vid_date,
        channel_id,
        duration,
        thumbnail_url,
        view_count,
        is_short,
    ):
        """Insert or update video record in database.

        Args:
            cur: Database cursor
            vid_id: Video ID
            vid_title: Video title
            vid_url: Video URL
            vid_date: Upload date
            channel_id: Channel ID
            duration: Video duration in seconds
            thumbnail_url: Thumbnail URL
            view_count: View count
            is_short: Whether video is a short
        """
        existing_video = cur.execute(
            "SELECT video_id FROM Videos WHERE video_id = ?", (vid_id,)
        ).fetchone()
        if existing_video is None:
            cur.execute(
                "\n                INSERT INTO Videos (video_id, video_title, video_url, video_date, channel_id, duration, thumbnail_url, view_count, is_short)\n                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)\n                ",
                (
                    vid_id,
                    vid_title,
                    vid_url,
                    vid_date,
                    channel_id,
                    duration,
                    thumbnail_url,
                    view_count,
                    is_short,
                ),
            )
        else:
            cur.execute(
                "\n                UPDATE Videos SET video_title = ?, video_url = ?, video_date = ?, duration = ?, thumbnail_url = ?, view_count = ?, is_short = ?\n                WHERE video_id = ?\n                ",
                (
                    vid_title,
                    vid_url,
                    vid_date,
                    duration,
                    thumbnail_url,
                    view_count,
                    is_short,
                    vid_id,
                ),
            )

    def _get_vtt_files_from_tmpdir(self, tmp_dir):
        """Get list of VTT files from tmp_dir.

        Args:
            tmp_dir: Path to temporary directory

        Returns:
            List of VTT file paths, or None if tmp_dir doesn't exist
        """
        import os
        from pathlib import Path

        if not Path(tmp_dir).exists():
            self._print_message(f"[red]❌ tmp_dir does not exist: {tmp_dir}[/red]")
            from yt_fts.utils.dual_sink_logger import log_technical_error

            log_technical_error(
                Exception(f"tmp_dir does not exist: {tmp_dir}"),
                {"operation": "vtt_to_db", "tmp_dir": tmp_dir},
            )
            return None
        try:
            items = os.listdir(tmp_dir)
        except Exception as e:
            self._print_message(f"[red]❌ Failed to list tmp_dir: {e}[/red]")
            from yt_fts.utils.dual_sink_logger import log_technical_error

            log_technical_error(e, {"operation": "vtt_to_db", "tmp_dir": tmp_dir})
            return None
        self.logger.debug("Found %s items in tmp_dir", len(items))
        if len(items) > 0:
            self.logger.debug("Sample items: %s", items[:5])
        file_paths = [Path(tmp_dir) / item for item in items if item.endswith(".vtt")]
        self.logger.debug("Found %s VTT files", len(file_paths))
        return file_paths

    def _show_failure_summary(self, failed_files: dict[str, list[str]]) -> None:
        """Display categorized failure summary.

        Args:
            failed_files: Dictionary mapping failure categories to lists of failed file paths
        """
        total_failed = sum(len(files) for files in failed_files.values())
        if total_failed == 0:
            return
        msg = f"[yellow]⚠ {total_failed} files failed to save:[/yellow]"
        self._print_error_message(msg)
        for category, files in failed_files.items():
            if files:
                detail = f"  {category}: {len(files)} files"
                self._print_error_message(detail)

    def vtt_to_db(self) -> None:
        """
        Parse downloaded VTT files and store subtitles in database.

        Reads all VTT files from tmp_dir and inserts their subtitle
        data into the Subtitles table.
        """
        from yt_fts.utils.dual_sink_logger import log_technical_error

        tmp_dir = self.tmp_dir
        self.logger.debug("tmp_dir: %s", tmp_dir)
        file_paths = self._get_vtt_files_from_tmpdir(tmp_dir)
        if file_paths is None or len(file_paths) == 0:
            return
        if not self.rich_mode:
            # Only clear live if there's an active live context
            if self.console._live_stack:
                self.console.clear_live()

        saved_count = 0
        failed_files = {
            "missing_json": [],
            "parse_error": [],
            "database_error": [],
            "network_error": [],
            "other": [],
        }

        with db_write_lock:
            with get_db_connection(timeout=30.0) as con:
                cur = con.cursor()
                with self._get_progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    BarColumn(bar_width=30),
                    transient=True,
                ) as progress:
                    task = progress.add_task(
                        "💾 Storing subtitles", total=len(file_paths)
                    )
                    for vtt in file_paths:
                        try:
                            if check_interruption():
                                self._print_message(
                                    "[yellow]⚠️ Database import interrupted by user[/yellow]"
                                )
                                break
                            base_name = Path(vtt).name
                            vid_id = base_name.split(".")[0]
                            vid_url = f"https://youtu.be/{vid_id}"
                            vid_json_path = Path(vtt).parent / f"{vid_id}.info.json"
                            if not vid_json_path.exists():
                                failed_files["missing_json"].append(vtt)
                                self._print_error_message(
                                    f"[yellow]⚠️ Missing info.json for {vid_id}[/yellow]"
                                )
                                progress.advance(task)
                                continue
                            metadata = self._extract_video_metadata(
                                vid_json_path, vid_id
                            )
                            if metadata is None:
                                failed_files["parse_error"].append(vtt)
                                self._print_error_message(
                                    f"[yellow]⚠️ JSON parse error for {vid_id}[/yellow]"
                                )
                                progress.advance(task)
                                continue
                            (
                                vid_title,
                                vid_date,
                                channel_id,
                                thumbnail_url,
                                duration,
                                view_count,
                                is_short,
                                category,
                                description,
                            ) = metadata
                            self._upsert_video_to_db(
                                cur,
                                vid_id,
                                vid_title,
                                vid_url,
                                vid_date,
                                channel_id,
                                duration,
                                thumbnail_url,
                                view_count,
                                is_short,
                            )
                            vtt_json = parse_vtt(vtt)
                            try:
                                for sub in vtt_json:
                                    start_time = sub["start_time"]
                                    stop_time = sub["stop_time"]
                                    text = sub["text"]
                                    cur.execute(
                                        "\n                                        INSERT INTO Subtitles (video_id, start_time, stop_time, text)\n                                        VALUES (?, ?, ?, ?)\n                                        ",
                                        (vid_id, start_time, stop_time, text),
                                    )
                                saved_count += 1
                                self.videos_saved_to_db += 1
                                if self.progress_callback:
                                    total = (
                                        self.total_videos or len(self.video_ids)
                                        if self.video_ids
                                        else self.videos_saved_to_db
                                    )
                                    self.progress_callback(
                                        self.videos_saved_to_db, total
                                    )
                            except sqlite3.Error as e:
                                failed_files["database_error"].append(vtt)
                                self._print_error_message(
                                    f"[red]❌ Database error for {vid_id}: {e}[/red]"
                                )
                                log_technical_error(
                                    e,
                                    {
                                        "operation": "vtt_to_db",
                                        "vtt_file": vtt,
                                        "video_id": vid_id,
                                    },
                                )
                            except (json.JSONDecodeError, KeyError, IndexError) as e:
                                failed_files["parse_error"].append(vtt)
                                self._print_error_message(
                                    f"[red]❌ Parse error for {vid_id}: {e}[/red]"
                                )
                                log_technical_error(
                                    e,
                                    {
                                        "operation": "vtt_to_db",
                                        "vtt_file": vtt,
                                        "video_id": vid_id,
                                    },
                                )
                            except Exception as e:
                                failed_files["other"].append(vtt)
                                self._print_error_message(
                                    f"[red]❌ Error processing {vtt}: {e}[/red]"
                                )
                                log_technical_error(
                                    e,
                                    {
                                        "operation": "vtt_to_db",
                                        "vtt_file": vtt,
                                        "video_id": (
                                            vid_id
                                            if "vid_id" in locals()
                                            else "unknown"
                                        ),
                                    },
                                )
                        except Exception as e:
                            failed_files["other"].append(vtt)
                            self._print_error_message(
                                f"[red]❌ Unexpected error processing {vtt}: {e}[/red]"
                            )
                            log_technical_error(
                                e, {"operation": "vtt_to_db_outer", "vtt_file": vtt}
                            )
                        progress.advance(task)
                con.commit()
                if not self.suppress_status_messages:
                    self._print_message(
                        f"[green]✓ Saved {saved_count} transcripts to database[/green]"
                    )
                self._show_failure_summary(failed_files)

    def diagnose_403_errors(
        self, test_url: str = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    ) -> None:
        """
        !SLOP GENERATED

        Diagnose potential causes of 403 errors by testing various aspects of the connection
        """
        self._print_message("[bold blue]Diagnosing 403 errors...[/bold blue]")
        self._print_message(
            "\n[bold]1. Testing basic HTTP connection to YouTube...[/bold]"
        )
        try:
            import requests

            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
            }
            response = requests.get(
                "https://www.youtube.com", headers=headers, timeout=10
            )
            if response.status_code == 200:
                self._print_message("[green]✓ Basic HTTP connection successful[/green]")
            else:
                self._print_message(
                    f"[red]✗ HTTP connection failed with status {response.status_code}[/red]"
                )
        except Exception as e:
            self._print_message(f"[red]✗ HTTP connection failed: {e}[/red]")
        self._print_message("\n[bold]2. Testing yt-dlp info extraction...[/bold]")
        try:
            ydl_opts: dict[str, Any] = {
                "quiet": True,
                "no_warnings": True,
                "noprogress": True,
                "extract_flat": True,
                "http_headers": {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                },
            }
            if self.cookies_from_browser is not None:
                ydl_opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info:
                    self._print_message(
                        "[green]✓ yt-dlp info extraction successful[/green]"
                    )
                    self._print_message(f"  Title: {info.get('title', 'N/A')}")
                else:
                    self._print_message("[red]✗ yt-dlp info extraction failed[/red]")
        except Exception as e:
            self._print_message(f"[red]✗ yt-dlp info extraction failed: {e}[/red]")
        self._print_message("\n[bold]3. Testing cookie availability...[/bold]")
        if self.cookies_from_browser is not None:
            self._print_message(
                f"[yellow]Cookies from browser: {self.cookies_from_browser}[/yellow]"
            )
            try:
                ydl_opts: dict[str, Any] = {
                    "cookiesfrombrowser": (self.cookies_from_browser,),
                    "quiet": True,
                    "no_warnings": True,
                    "noprogress": True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    self._print_message(
                        "[green]✓ Cookie extraction appears to be working[/green]"
                    )
            except Exception as e:
                self._print_message(f"[red]✗ Cookie extraction failed: {e}[/red]")
        else:
            self._print_message("[yellow]No cookies from browser specified[/yellow]")
            self._print_message(
                "[yellow]Consider using --cookies-from-browser option[/yellow]"
            )
        self._print_message("\n[bold]4. Rate limiting analysis...[/bold]")
        self._print_message(f"Current parallel jobs: {self.number_of_jobs}")
        if self.number_of_jobs > 4:
            self._print_message(
                "[yellow]⚠ High number of parallel jobs may cause rate limiting[/yellow]"
            )
            self._print_message("[yellow]Consider reducing to 2-4 jobs[/yellow]")
        else:
            self._print_message(
                "[green]✓ Parallel jobs setting looks reasonable[/green]"
            )
        self._print_message("\n[bold]5. Network connectivity test...[/bold]")
        try:
            import socket

            socket.create_connection(("www.youtube.com", 443), timeout=5)
            self._print_message(
                "[green]✓ Network connectivity to YouTube is good[/green]"
            )
        except Exception as e:
            self._print_message(f"[red]✗ Network connectivity issue: {e}[/red]")
        self._print_message(
            "\n[bold blue]Recommendations to fix 403 errors:[/bold blue]"
        )
        self._print_message("1. Use --cookies-from-browser chrome (or firefox)")
        self._print_message("2. Reduce parallel jobs: -j 2 or -j 4")
        self._print_message("3. Wait a few minutes between download attempts")
        self._print_message("4. Check if you're behind a VPN or proxy")
        self._print_message("5. Try downloading from a different network")
        self._print_message("6. Update yt-dlp: pip install --upgrade yt-dlp")

    def validate_channel_url(self, channel_url: str) -> str | None:
        """
        Validate and normalize a YouTube channel URL.

        Delegates to url_utils.validate_channel_url with print callback.

        Args:
            channel_url: Channel URL to validate

        Returns:
            Normalized channel URL or None if invalid
        """
        return validate_channel_url(channel_url, print_callback=self._print_message)

    @property
    def _user_agents(self):
        """
        Get list of user agent strings for HTTP requests.

        Returns:
            List of user agent strings from url_utils
        """
        return USER_AGENTS
