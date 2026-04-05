"""
Batch downloader for multiple YouTube channels with duplicate-free progress bars.
"""

import logging
import os
import time

from yt_fts.utils.dual_sink_logger import (
    get_logger,
    log_operation,
    log_technical_error,
    log_user_message,
)

logger = get_logger(__name__)
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from rich.progress import BarColumn, Progress, TaskID, TextColumn
from rich.table import Column

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("download.log", mode="a")],
)
import contextlib

from yt_fts.core.database import BatchCommitManager, get_batch_manager

from .batch_channel_helpers import (
    determine_rss_status,
    determine_status_name,
    extract_handle,
    format_rss_status_message,
    initialize_channel_state,
    load_channel_db_stats,
    perform_rss_check,
    process_unavailable_videos,
    recheck_unavailable_videos,
)
from .channel_cache import (
    get_cached_channels,
    report_cache_status,
    save_resolved_channels,
)
from .download_handler import DownloadHandler
from .exceptions import BaseURLFallbackFailed, DownloadTimeoutException
from .progress_coordinator import ThreadSafeProgressCoordinator
from .rich_layout import RichLayoutDownloader
from .summary import export_report, print_summary, validate_channels
from .unified_discovery import UnifiedChannelDiscovery

# from .reprocess_no_subs import get_no_subs_videos_for_channel, reprocess_channel_no_subs  # Removed - reprocess disabled


class BatchDownloader:
    """
    Efficient batch downloader for multiple YouTube channels with duplicate-free progress bars.

    Features:
    - Smart rate limiting between channels
    - Cookie support for reduced rate limiting
    """

    def __init__(
        self,
        channels: list[str],
        jobs: int = 2,
        language: str = "en",
        cookies_from_browser: str | None = None,
        delay_between_channels: float = 3.0,
        max_retries: int = 3,
        continue_on_error: bool = True,
        rich_formatter: Any = None,
        rich_mode: str | None = None,
        time_per_channel: float | None = None,
        time_per_video: float | None = None,
        time_per_batch: float | None = None,
        max_videos: int | None = None,
        min_saved: int | None = None,
        target_downloads: int | None = None,
        videos_download_per_batch: int | None = None,
        display_plugin: str | None = None,
        auto_backfill: bool = False,
        dry_run: bool = False,
        freshness_hours: int = 6,
        quota_strategy: Any = None,
        suppress_quota_print: bool = False,
        suppress_verbose: bool = False,
        transcribe_audio_only: bool = True,
        whisper_model: str = "base",
        keep_audio: bool = False,
    ) -> None:
        """
        Initialize the BatchDownloader.

        Args:
            channels: List of YouTube channel URLs or handles
            jobs: Number of concurrent download jobs
            language: Language for subtitles
            cookies_from_browser: Browser to extract cookies from
            delay_between_channels: Delay between processing channels (seconds)
            max_retries: Maximum number of retries per channel
            continue_on_error: Continue with other channels if one fails
            rich_formatter: Optional RichYouTubeFormatter for enhanced UI
            rich_mode: Rich UI mode - 'new' (footer layout), 'old' (legacy), or None
            time_per_channel: Maximum time to spend downloading per channel (None for unlimited)
            time_per_video: Maximum time per video yt-dlp call (None for unlimited)
            time_per_batch: Maximum time for entire batch download (None for unlimited)
            max_videos: Maximum number of videos to attempt per channel (None for unlimited)
            min_saved: Minimum number of videos to successfully save per channel (continues until met)
            display_plugin: Display plugin to use for output
            auto_backfill: Automatically backfill metadata after each channel download
            dry_run: Preview mode - show what would be done without downloading
            videos_download_per_batch: Maximum total videos to download across all channels (None for unlimited)
            quota_strategy: Optional QuotaStrategy for adaptive API usage (None = no quota management)
            transcribe_audio_only: Enable Whisper transcription for videos without subtitles
            whisper_model: Whisper model size for transcription (default: base)
            keep_audio: Preserve downloaded audio files after transcription (for debugging/iteration)
        """
        self.channels = channels
        self.jobs = jobs
        self.language = language
        self.cookies_from_browser = cookies_from_browser
        self.delay_between_channels = delay_between_channels
        self.max_retries = max_retries
        self.continue_on_error = continue_on_error
        self.min_saved = min_saved
        self.rich_formatter = rich_formatter
        self.rich_mode = rich_mode
        self.time_per_channel = time_per_channel
        self.time_per_video = time_per_video
        self.time_per_batch = time_per_batch
        self.batch_start_time: float = 0.0
        self.max_videos = max_videos
        self.target_downloads = target_downloads
        self.videos_download_per_batch = videos_download_per_batch
        self.auto_backfill = auto_backfill
        self.dry_run = dry_run
        self.freshness_hours = freshness_hours
        self.quota_strategy = quota_strategy
        self.suppress_quota_print = suppress_quota_print
        self.suppress_verbose = suppress_verbose
        self.transcribe_audio_only = transcribe_audio_only
        self.whisper_model = whisper_model
        self.keep_audio = keep_audio
        from yt_fts.utils.rich_console import get_console, get_stderr_console

        force_terminal = bool(os.getenv("WT_SESSION"))
        self.console = get_console(force_terminal=force_terminal)
        self.progress_console = get_stderr_console(force_terminal=force_terminal)
        self.batch_manager: BatchCommitManager | None = None
        if min_saved == 0:
            self.batch_manager = get_batch_manager(commit_interval=50)
        plugin_map = {
            "1": "pipeline_view",
            "2": "dashboard_view",
            "3": "entity_view",
            "4": "job_monitor",
            "5": "forensic_view",
            "6": "exception_first",
        }
        plugin_name = plugin_map.get(display_plugin, display_plugin)
        if not plugin_name or plugin_name == "default":
            plugin_name = "download_default"

        from yt_fts.display import create_plugin as create_display_plugin
        from yt_fts.display import load_builtin_plugins
        from yt_fts.display.base import PluginContext
        from yt_fts.display.legacy_adapter import wrap_legacy_plugin
        from yt_fts.ui.plugins import get_plugin as get_legacy_plugin

        load_builtin_plugins()
        context = PluginContext(
            command="download",
            console=self.console,
            options={"verbose": not suppress_verbose},
        )
        legacy_names = {
            "compact",
            "detailed",
            "minimal",
            "progress",
            "table",
            "pipeline_view",
            "dashboard_view",
            "entity_view",
            "job_monitor",
            "forensic_view",
            "exception_first",
        }
        if plugin_name in legacy_names:
            try:
                legacy_class = get_legacy_plugin(plugin_name)
                self.display_plugin = wrap_legacy_plugin(legacy_class, context)
            except Exception:
                self.display_plugin = create_display_plugin("download_default", context)
        else:
            try:
                self.display_plugin = create_display_plugin(plugin_name, context)
            except Exception:
                try:
                    legacy_class = get_legacy_plugin(plugin_name)
                    self.display_plugin = wrap_legacy_plugin(legacy_class, context)
                except Exception:
                    self.display_plugin = create_display_plugin(
                        "download_default",
                        context,
                    )
        self.unified_discovery = UnifiedChannelDiscovery(
            cookies_from_browser=cookies_from_browser
        )
        self.executor = None
        self.results = None

    def _print_quota_status(self, header: str) -> None:
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        api_backfill = YouTubeAPIBackfill()
        quota_lines = api_backfill.format_quota_lines()
        self.console.print(f"[cyan]{header}[/cyan]")
        if quota_lines:
            for line in quota_lines:
                self.console.print(f"[cyan]  {line}[/cyan]")
        else:
            self.console.print("[cyan]  No quota data[/cyan]")
        self.console.print("")

    def _print_channel_section_header(self, channel_name: str) -> None:
        self.console.print("")
        self.console.print(f"[cyan]Channel: {channel_name}[/cyan]")

    def _dry_run_channels(self) -> dict[str, Any]:
        """Dry run mode: Show what would be done without using quota or downloading.

        Returns:
            dict: Mock results with skipped channels
        """
        self.console.print("[yellow]── DRY RUN MODE ──[/yellow]")
        self.console.print(
            "[dim]No quota will be used. No downloads will be performed.[/dim]"
        )
        self.console.print("")
        results = {"successful": [], "failed": [], "skipped": []}
        quota_estimate = 0
        self._print_quota_status("Current yt-api quota")
        for idx, channel in enumerate(
            (
                self.channels[: self.target_downloads]
                if self.target_downloads
                else self.channels
            ),
            1,
        ):
            self.console.print(f"[dim]{idx}. {channel}[/dim]")
            quota_estimate += 1
            self.console.print(
                "     [dim]→ Would check channel stats (1 quota if RSS finds gaps)[/dim]"
            )
            results["skipped"].append(
                {"channel": channel, "message": "Dry run - would check RSS and yt-api"}
            )
        self.console.print("")
        self.console.print(f"[cyan]Estimated max quota usage: {quota_estimate}[/cyan]")
        self.console.print(
            "[cyan]Estimated videos to download: unknown until actual RSS check[/cyan]"
        )
        self.console.print("")
        self.console.print("[yellow]── Run without --dry-run to execute ──[/yellow]")
        return results

    def _extract_channel_downloads(
        self, resolved_channels: dict[str, str]
    ) -> list[tuple[str, str, str | None]]:
        """Extract channel IDs and deduplicate based on resolved ID/URL."""
        channel_downloads = []
        seen_ids = set()

        for original_channel, resolved_url in resolved_channels.items():
            channel_id = None
            if "/channel/" in resolved_url:
                channel_id = resolved_url.split("/channel/")[1].split("/")[0]

            # Deduplication key: Use channel_id if available (most reliable),
            # otherwise fall back to resolved_url
            dedupe_key = channel_id if channel_id else resolved_url

            if dedupe_key in seen_ids:
                continue

            seen_ids.add(dedupe_key)
            channel_downloads.append((original_channel, resolved_url, channel_id))

        return channel_downloads

    def _format_db_stats(
        self,
        db_count: int,
        db_with_subs: int,
        db_no_subs: int,
        db_scheduled: int,
        db_members: int,
        db_unavail_deleted: int,
        db_unavail_private: int,
        db_unavail_geo: int,
        db_unavailable: int,
        db_shorts: int,
        status_name: str,
        channel_id: str | None = None,
        channel_display_name: str | None = None,
    ) -> dict[str, Any]:
        """Format database statistics for display with enhanced inconsistency detection.

        Returns:
            dict: {
                'stats': str - formatted stats string,
                'inconsistent': bool - whether stats are inconsistent,
                'reason': str - explanation of inconsistency,
                'severity': str - severity level,
                'type': str - inconsistency type,
                'details': dict - raw stats for display,
                'inconsistency_id': int - logged inconsistency ID (if logged)
            }
        """
        """Format database statistics for display."""
        import logging

        logger = logging.getLogger(__name__)
        parts = []
        parts.append(f"{db_count} total")
        video_parts = []
        video_parts.append(f"{db_with_subs} with transcripts")
        # Checksum components: always display even when 0 so user can verify the math
        video_parts.append(f"{db_no_subs} no subs")
        video_parts.append(f"{db_scheduled} sch")
        video_parts.append(f"{db_members} mem")
        if db_unavail_deleted > 0:
            video_parts.append(f"{db_unavail_deleted} unavail_del")
        if db_unavail_private > 0:
            video_parts.append(f"{db_unavail_private} unavail_priv")
        if db_unavail_geo > 0:
            video_parts.append(f"{db_unavail_geo} unavail_geo")
        parts.append(", ".join(video_parts))
        main_stats = " | ".join(parts)
        extras = []
        if db_shorts > 0:
            extras.append(f"{db_shorts} shorts")
        db_stats = f"{main_stats} | {', '.join(extras)}" if extras else main_stats

        inconsistent = False
        reason = ""
        severity = "low"
        inconsistency_type = ""
        inconsistency_id = None

        # Initialize checksum variables (used for logging inconsistency details)
        special_total = 0
        unexplained_gap = 0

        if db_count > 0:
            # Enhanced inconsistency detection with severity levels
            impossible = (
                db_with_subs > db_count
                or db_scheduled > db_count
                or db_unavailable > db_count
                or (db_shorts > db_count)
                or (db_members > db_count)
            )

            # Check for impossible values (critical)
            if impossible:
                inconsistent = True
                severity = "critical"
                if db_with_subs > db_count:
                    reason = f"with_subs ({db_with_subs}) > total ({db_count})"
                    inconsistency_type = "impossible_count"
                elif db_scheduled > db_count:
                    reason = f"scheduled ({db_scheduled}) > total ({db_count})"
                    inconsistency_type = "impossible_count"
                elif db_unavailable > db_count:
                    reason = f"unavailable ({db_unavailable}) > total ({db_count})"
                    inconsistency_type = "impossible_count"
                elif db_shorts > db_count:
                    reason = f"shorts ({db_shorts}) > total ({db_count})"
                    inconsistency_type = "impossible_count"
                elif db_members > db_count:
                    reason = f"members ({db_members}) > total ({db_count})"
                    inconsistency_type = "impossible_count"

            # Check for unexplained gaps (high priority)
            else:
                special_total = db_scheduled + db_unavailable + db_members + db_no_subs
                unexplained_gap = db_count - db_with_subs - special_total

                if unexplained_gap > 5:  # Significant gap
                    inconsistent = True
                    severity = "high"
                    reason = f"{unexplained_gap} videos not accounted for in special categories"
                    inconsistency_type = "video_gap"
                elif unexplained_gap > 0:  # Small gap
                    inconsistent = True
                    severity = "medium"
                    reason = f"{unexplained_gap} videos not accounted for in special categories"
                    inconsistency_type = "video_gap"
                elif unexplained_gap < -2:  # Over-accounting (less common)
                    inconsistent = True
                    severity = "medium"
                    reason = f"Over-accounting by {-unexplained_gap} videos in special categories"
                    inconsistency_type = "over_counting"

            if inconsistent:
                db_stats = f"[red]{db_stats}[/red]"

                # Log inconsistency for tracking and auto-repair
                if channel_id:
                    try:
                        from yt_fts.core.inconsistency_logger import (
                            AutoRepairManager,
                            InconsistencyLogger,
                        )

                        logger_instance = InconsistencyLogger()
                        inconsistency_id = logger_instance.log_inconsistency(
                            channel_id=channel_id,
                            channel_name=channel_display_name,
                            inconsistency_type=inconsistency_type,
                            severity=severity,
                            details=reason,
                            stats={
                                "total": db_count,
                                "with_subs": db_with_subs,
                                "no_subs": db_no_subs,
                                "scheduled": db_scheduled,
                                "members": db_members,
                                "unavailable": db_unavailable,
                                "shorts": db_shorts,
                                "special_total": special_total,
                                "unexplained_gap": unexplained_gap,
                            },
                        )

                        # Attempt auto-repair for certain types
                        if inconsistency_type in ["video_gap", "impossible_count"]:
                            repair_manager = AutoRepairManager(logger_instance)
                            repair_data = {
                                "type": inconsistency_type,
                                "channel_id": channel_id,
                                "stats": {
                                    "total": db_count,
                                    "with_subs": db_with_subs,
                                    "no_subs": db_no_subs,
                                    "scheduled": db_scheduled,
                                    "members": db_members,
                                    "unavailable": db_unavailable,
                                    "shorts": db_shorts,
                                },
                            }
                            repair_success = repair_manager.attempt_repair(
                                inconsistency_id, repair_data
                            )
                            if repair_success:
                                # Mark as resolved in display
                                db_stats = f"[green]{db_stats} ✓[/green]"
                                reason += " (auto-repaired)"

                    except Exception as e:
                        logger.debug(f"Failed to log/repair inconsistency: {e}")

        return {
            "stats": db_stats,
            "inconsistent": inconsistent,
            "reason": reason,
            "severity": severity,
            "type": inconsistency_type,
            "details": {
                "total": db_count,
                "with_subs": db_with_subs,
                "no_subs": db_no_subs,
                "scheduled": db_scheduled,
                "members": db_members,
                "unavailable": db_unavailable,
                "shorts": db_shorts,
            },
            "inconsistency_id": inconsistency_id,
        }

    def _ensure_channel_name_in_db(self, channel_id: str | None) -> str | None:
        """Quick check for cached channel name - NO API calls, NO blocking.

        Lazy loading: This only checks if name is already cached.
        If no cached name exists, returns immediately without blocking.
        The actual channel name will be fetched later via existing RSS/API flow.

        Args:
            channel_id: YouTube channel ID (may be None)

        Returns:
            The channel_id unchanged (no API discovery here)
        """
        if not channel_id:
            return channel_id

        # Quick check if name already exists in database - NO API call
        from yt_fts.db.channels import get_channel_name_from_db

        existing_name = get_channel_name_from_db(channel_id)
        if existing_name and not self._is_raw_channel_id(existing_name):
            # Have a valid human-readable name cached
            logger.debug(
                f"_ensure_channel_name_in_db: cached name '{existing_name}' for {channel_id}"
            )
        else:
            # No cached name - return immediately (lazy load later via RSS/API)
            logger.debug(
                f"_ensure_channel_name_in_db: no cached name for {channel_id}, will lazy load"
            )

        # Return channel_id unchanged - no blocking API call
        return channel_id

    def _is_raw_channel_id(self, name: str) -> bool:
        """Check if a name is a raw channel ID rather than a human-readable name.

        Args:
            name: The channel name to check

        Returns:
            True if the name appears to be a raw channel ID
        """
        return (
            name.startswith("Channel UC")
            or (name.startswith("UC") and len(name) >= 20)
            or name == "__INVALID_CHANNEL__"
        )

    def _fetch_channel_metadata_yt_dlp(
        self, url_or_id: str
    ) -> tuple[str | None, str | None]:
        """Fetch channel name and URL from yt-dlp."""
        import shutil
        import subprocess

        if not shutil.which("yt-dlp"):
            return None, None

        # Construct URL if ID provided
        if url_or_id.startswith("UC") and len(url_or_id) > 20:
            url = f"https://www.youtube.com/channel/{url_or_id}"
        elif url_or_id.startswith("@"):
            url = f"https://www.youtube.com/{url_or_id}"
        else:
            url = url_or_id

        try:
            # --flat-playlist is fast, --playlist-end 1 ensures we don't scan much
            cmd = [
                "yt-dlp",
                "--flat-playlist",
                "--playlist-end",
                "1",
                "--print",
                "channel",
                "--print",
                "channel_url",
                url,
            ]
            # Use quick timeout (5s) to avoid stalling batch headers
            # We suppress stderr to keep console clean
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=5, check=True
            )
            lines = result.stdout.strip().splitlines()
            if len(lines) >= 2:
                return lines[0], lines[1]  # Name, URL
            if len(lines) == 1:
                return lines[0], None  # Just Name
        except Exception:
            pass
        return None, None

    def _prefetch_channel_names_parallel(
        self, channel_downloads: list[tuple[str, str, str | None]]
    ) -> None:
        """Pre-fetch missing channel names in parallel to reduce startup latency.

        Identifies channels that have missing or raw names in the DB and fetches
        them concurrently using yt-dlp. Handles deleted channels by marking them
        to prevent future fetch delays.
        """
        from concurrent.futures import as_completed

        from yt_fts.db.channels import add_channel_info, get_channel_name_from_db

        # Identify channels that need fetching
        channels_to_fetch = []
        for _, resolved_url, channel_id in channel_downloads:
            if not channel_id:
                continue

            # Check if name needs fetching (missing or raw ID)
            name = get_channel_name_from_db(channel_id)
            if not name or self._is_raw_channel_id(name):
                fetch_input = (
                    f"https://www.youtube.com/channel/{channel_id}"
                    if channel_id.startswith("UC")
                    else resolved_url
                )
                channels_to_fetch.append((channel_id, fetch_input))

        if not channels_to_fetch:
            return

        if not self.suppress_verbose:
            self.console.print(
                f"[cyan]Pre-fetching metadata for {len(channels_to_fetch)} channels in parallel...[/cyan]"
            )

        # Run parallel fetches
        # Cap workers to avoid attempting too many simultaneous connections
        max_workers = min(8, len(channels_to_fetch))
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_channel = {
                executor.submit(self._fetch_channel_metadata_yt_dlp, url): (cid, url)
                for cid, url in channels_to_fetch
            }

            completed = 0
            for future in as_completed(future_to_channel):
                channel_id, url = future_to_channel[future]
                completed += 1
                try:
                    name, channel_url = future.result()
                    if name:
                        save_url = channel_url if channel_url else url
                        add_channel_info(channel_id, name, save_url)
                    else:
                        # Mark as not found/deleted to prevent future retries (save 5s per run)
                        # We use a format that _is_raw_channel_id() checks will accept as "valid"
                        # so it doesn't retry fetching.
                        failed_name = f"[Channel Not Found] {channel_id}"
                        add_channel_info(channel_id, failed_name, url)
                except Exception:
                    pass

    def _get_channel_display_name(
        self, channel_id: str | None, status_name: str
    ) -> str:
        """Get actual channel name from database for display.

        Progressive Handle Display (Option A):
        1. Prefer cached database name (no warning)
        2. Fall back to @handle from input (with ⚠️ warning)
        3. Extract @handle from URL (with ⚠️ warning)
        4. Truncated channel_id as last resort (with ⚠️ warning)
        NEVER show full raw channel_id like UC1weYqfC7x6g5Y4z1W2X3V4U
        """
        import logging

        logger = logging.getLogger(__name__)

        if not channel_id:
            # When no channel_id, return status_name as-is
            return status_name

        try:
            from yt_fts.db.channels import get_channel_name_from_db

            name = get_channel_name_from_db(channel_id)
            logger.debug(
                f"_get_channel_display_name: channel_id={channel_id}, db_name={name!r}"
            )
            if name:
                # Check if cached name is actually just a raw channel ID (not human-readable)
                # Patterns that indicate NOT a real human-readable name:
                # 1. "Channel UC..." format (old database entries)
                # 2. Starts with UC and is 20+ chars (raw channel ID)
                if self._is_raw_channel_id(name):
                    logger.debug(
                        "_get_channel_display_name: db name looks like raw ID, falling through"
                    )
                    # Treat as not cached, fall through to progressive display
                else:
                    logger.debug(
                        f"_get_channel_display_name: returning db name: {name!r}"
                    )
                    return name  # Real cached name, no warning needed
        except Exception as e:
            logger.debug(
                f"_get_channel_display_name: exception getting name from DB: {e}"
            )

        # 3. If db name missing/invalid, try fetching from yt-dlp
        # Only try if we have a valid channel_id to save to
        if channel_id:
            try:
                # Use channel_id to construct URL or fallback to status_name
                fetch_input = (
                    f"https://www.youtube.com/channel/{channel_id}"
                    if channel_id
                    else status_name
                )
                fetched_name, fetched_url = self._fetch_channel_metadata_yt_dlp(
                    fetch_input
                )

                if fetched_name:
                    logger.debug(
                        f"_get_channel_display_name: fetched name '{fetched_name}' from yt-dlp"
                    )
                    # Update DB so we don't fetch again
                    from yt_fts.db.channels import add_channel_info

                    # Ensure we have a URL for add_channel_info
                    save_url = (
                        fetched_url
                        if fetched_url
                        else f"https://www.youtube.com/channel/{channel_id}/videos"
                    )
                    add_channel_info(channel_id, fetched_name, save_url)
                    return fetched_name
            except Exception as e:
                logger.debug(f"_get_channel_display_name: fetch failed: {e}")

        # Fallback: progressive handle display with ⚠️ warning
        warning = "⚠️ "

        # 1. If status_name is already @handle format
        if status_name.startswith("@"):
            return f"{warning}{status_name}"

        # 2. Extract @handle from URL
        if "youtube.com/@" in status_name:
            handle_part = status_name.split("youtube.com/@")[-1].split("/")[0]
            return f"{warning}@{handle_part}"

        # 3. If status_name is 'channel/UC...', truncate the channel_id
        if status_name.startswith("channel/"):
            # Truncate to first ~10 chars + ...
            truncated = (channel_id or status_name.split("/")[-1])[:10]
            return f"{warning}{truncated}..."

        # 4. If status_name is a raw channel_id, truncate it
        if status_name.startswith("UC") and len(status_name) > 15:
            return f"{warning}{status_name[:10]}..."

        # 5. Default: return status_name with warning
        return f"{warning}{status_name}"

    def _initialize_batch_download(self) -> tuple[dict[str, Any] | None, int]:
        """
        Initialize batch download: setup logging, results dict, timing, and check dry run.

        Returns:
            tuple: (results dict or None if dry_run, total_videos_saved starting at 0)
        """
        import logging
        import time

        logging.getLogger("yt_dlp").setLevel(logging.WARNING)
        logging.getLogger("technical").setLevel(logging.CRITICAL)
        results = {
            "successful": [],
            "failed": [],
            "skipped": [],
            "invalid_channels": [],
        }
        self.batch_start_time = time.time()
        total_videos_saved = 0
        log_user_message(
            20, f"🚀 Starting batch download of {len(self.channels)} channels"
        )
        log_operation(
            "batch_download",
            "Batch download initiated",
            total_channels=len(self.channels),
            jobs=self.jobs,
            language=self.language,
        )
        if self.dry_run:
            self._dry_run_channels()
            return None, 0
        if not self.suppress_quota_print:
            self._print_quota_status("yt-api quota")
        return results, total_videos_saved

    def _resolve_and_validate_channels(
        self,
    ) -> tuple[list[tuple[str, str, str]] | None, list[str]]:
        """
        Resolve channel URLs to channel IDs and validate them.

        Returns:
            tuple: (channel_downloads list or None if rich mode, invalid_channels list)
        """
        # Show progress before blocking DB operations
        if not self.suppress_verbose:
            self.console.print("[dim]Initializing database cache...[/dim]", end="")

        from yt_fts.core.database import enable_wal_mode, get_db_connection

        enable_wal_mode()
        conn = get_db_connection(timeout=10.0)
        try:
            cached_channels, channels_to_resolve = get_cached_channels(
                self.channels, conn
            )
        finally:
            conn.close()
        report_cache_status(
            self.console,
            cached_count=len(cached_channels),
            resolve_count=len(channels_to_resolve),
        )

        # Clear the "Initializing..." line and print actual cache status
        if not self.suppress_verbose:
            self.console.print()  # Clear the "Initializing..." line
            from .channel_cache import print_aggregated_cache_status

            print_aggregated_cache_status(self.console)
        newly_resolved = {}
        if channels_to_resolve:
            from .fast_channel_resolver import create_fast_resolver

            fast_resolver = create_fast_resolver(
                cookies_from_browser=self.cookies_from_browser, console=self.console
            )
            newly_resolved = fast_resolver.batch_resolve(
                channels_to_resolve, max_workers=3
            )
        resolved_channels = {**cached_channels, **newly_resolved}
        validated_channels = {**cached_channels, **newly_resolved}
        invalid_channels: list[str] = []
        resolved_channels = validated_channels
        successful_resolutions = len(resolved_channels)
        failed_resolutions = len(invalid_channels)
        if failed_resolutions > 0:
            self.console.print(
                f"[dim]  → {successful_resolutions} valid, {failed_resolutions} not found[/dim]"
            )
        if newly_resolved:
            save_resolved_channels(newly_resolved, console=self.console)
        channel_downloads = self._extract_channel_downloads(resolved_channels)

        # Report deduplication results if any were removed
        total_resolved = len(resolved_channels)
        unique_count = len(channel_downloads)
        duplicates_removed = total_resolved - unique_count

        if duplicates_removed > 0:
            self.console.print(
                f"[dim]  → De-duplicated {duplicates_removed} channels "
                f"({total_resolved} → {unique_count} unique)[/dim]"
            )
        if self.rich_mode == "new":
            rich_layout_downloader = RichLayoutDownloader(
                console=self.console,
                batch_downloader=self,
                cookies_from_browser=self.cookies_from_browser,
                max_videos=self.max_videos,
            )
            rich_layout_downloader.download_with_layout(
                channel_downloads, invalid_channels
            )
            return None, invalid_channels
        return channel_downloads, invalid_channels

    def _get_known_video_ids(self, video_ids: list[str]) -> set[str]:
        """
        Get set of video IDs that already exist in database.

        Args:
            video_ids: List of video IDs to check

        Returns:
            Set of video IDs that exist in the Videos table
        """
        if not video_ids:
            return set()
        from yt_fts.db.videos import get_existing_video_ids

        return get_existing_video_ids(video_ids)

    def _get_channel_id_by_url(self, resolved_url: str) -> str | None:
        """
        Look up channel_id from Channels table using URL.

        Args:
            resolved_url: The resolved channel URL

        Returns:
            Channel ID if found, "__INVALID_CHANNEL__" if 404, or None
        """
        try:
            from yt_fts.db.channels import (  # Checks exact ID, URL, Name
                get_channel_id_by_handle_substring,
                get_channel_id_by_url_exact,
                get_channel_id_from_input,
            )

            # 1. Try exact match on resolved_url
            chan_id = get_channel_id_by_url_exact(resolved_url)
            if chan_id:
                return chan_id

            # 2. Try stripped URL
            url_clean = resolved_url.removesuffix("/videos")
            chan_id = get_channel_id_by_url_exact(url_clean)
            if chan_id:
                return chan_id

            if "@" in resolved_url:
                handle = resolved_url.split("@")[-1].split("/")[0]
                # 3. Fuzzy handle match
                chan_id = get_channel_id_by_handle_substring(handle)
                if chan_id:
                    return chan_id

                # 4. Fallback to yt-dlp check (using get_channel_id_from_input for result verification)
                try:
                    import yt_dlp

                    ydl_opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "noprogress": True,
                        "extract_flat": True,
                    }
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = ydl.extract_info(resolved_url, download=False)
                        resolved_channel_id = info.get("channel_id") or info.get(
                            "uploader_id"
                        )

                        if resolved_channel_id and resolved_channel_id.startswith("UC"):
                            # Check if this ID exists in DB
                            return get_channel_id_from_input(resolved_channel_id)
                except Exception as e:
                    error_msg = str(e).lower()
                    if (
                        "404" in error_msg
                        or "not found" in error_msg
                        or "does not exist" in error_msg
                    ):
                        return "__INVALID_CHANNEL__"
            return None
        except Exception:
            return None

    def _display_and_format_channel_header(
        self,
        channel_id: str,
        status_name: str,
        db_state: dict[str, Any],
        channel_idx: int,
        target: int,
        suppress_verbose: bool,
        completed_count: int,
        resolved_url: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """
        Format and display the channel header with database statistics.

        Args:
            channel_id: The channel ID
            status_name: Display status name
            db_state: Current database state dict
            channel_idx: Channel index (1-based)
            target: Total target channels
            suppress_verbose: Whether to suppress verbose output
            completed_count: Number of completed downloads

        Returns:
            tuple: (channel_display_name, db_stats dict)
        """
        channel_display_name = self._get_channel_display_name(channel_id, status_name)
        db_stats = self._format_db_stats(
            db_state["db_count"] or 0,
            db_state["db_with_subs"] or 0,
            db_state["db_no_subs"] or 0,
            db_state["db_scheduled"] or 0,
            db_state["db_members"] or 0,
            db_state["db_unavail_deleted"] or 0,
            db_state["db_unavail_private"] or 0,
            db_state["db_unavail_geo"] or 0,
            db_state["db_unavailable"] or 0,
            db_state["db_shorts"] or 0,
            status_name,
            channel_id,
            channel_display_name,
        )
        if not suppress_verbose:
            self.display_plugin.display_channel_header(
                {
                    "index": channel_idx,
                    "total": target,
                    "name": channel_display_name,
                    "channel_url": resolved_url,
                    "db_stats": db_stats["stats"],
                    "inconsistent": db_stats["inconsistent"],
                    "inconsistency_reason": db_stats["reason"],
                    "db_stats_details": db_stats["details"],
                    "successful_downloads": completed_count,
                }
            )
        return channel_display_name, db_stats

    def _check_channel_freshness(
        self,
        channel_id: str,
        original_channel: str,
        results: dict[str, Any],
    ) -> bool:
        """
        Check if channel was recently checked and should be skipped.

        Args:
            channel_id: The channel ID to check
            original_channel: Original channel input for results
            results: Results dict to append skipped channels

        Returns:
            bool: True if channel is fresh (should skip), False otherwise
        """
        if not (self.min_saved == 0 and self.freshness_hours > 0):
            return False
        from yt_fts.core.database import is_channel_fresh

        is_fresh, last_checked = is_channel_fresh(channel_id, self.freshness_hours)
        if is_fresh:
            from datetime import datetime

            hours_ago = int(
                (datetime.now() - datetime.fromisoformat(last_checked)).total_seconds()
                / 3600
            )
            results["skipped"].append(
                {
                    "channel": original_channel,
                    "message": f"Recently checked ({hours_ago}h ago)",
                }
            )
        return is_fresh

    def _refresh_db_state(
        self,
        channel_id: str,
        db_state: dict[str, Any],
        get_vid_ids_by_channel_id: callable,
        get_channel_stats: callable,
    ) -> None:
        """
        Refresh database state with current channel statistics.

        Args:
            channel_id: Channel ID to refresh stats for
            db_state: Database state dict (modified in-place)
            get_vid_ids_by_channel_id: Function to get video IDs
            get_channel_stats: Function to get channel stats
        """
        local_vid_ids = [v[0] for v in get_vid_ids_by_channel_id(channel_id)]
        db_state["db_video_ids"] = set(local_vid_ids)
        stats = get_channel_stats(channel_id)
        db_state["db_count"] = stats["total"]
        db_state["db_with_subs"] = stats["with_transcripts"]
        db_state["db_scheduled"] = stats["scheduled"]
        db_state["db_members"] = stats["members_only"]
        db_state["db_unavailable"] = stats["unavailable"]
        db_state["db_shorts"] = stats["shorts"]
        db_state["db_no_subs"] = stats["without_transcripts"]

    def _check_and_display_api_mismatch(
        self,
        channel_id: str,
        db_state: dict[str, Any],
    ) -> bool:
        """
        Check if API total differs from DB count and display warning.

        Args:
            channel_id: Channel ID to check
            db_state: Database state dict

        Returns:
            bool: True if there's a mismatch, False otherwise
        """
        from yt_fts.db.channels import get_channel_api_total

        stored_api_total = get_channel_api_total(channel_id)
        if stored_api_total is not None and (db_state["db_count"] or 0) >= 0:
            if stored_api_total > db_state["db_count"]:
                missing_count = stored_api_total - db_state["db_count"]
                self.display_plugin.info(
                    f"{db_state['db_count']}/{stored_api_total} videos ({missing_count} not yet downloaded)"
                )
                return True
        return False

    def _should_use_api_for_metadata(self, db_count: int) -> bool:
        """
        Determine if API should be used for metadata fetching.

        Args:
            db_count: Current database video count

        Returns:
            bool: True if API should be used, False otherwise
        """
        use_api = True
        if self.quota_strategy:
            use_api = self.quota_strategy.should_use_api_for_metadata(db_count)
            if not use_api and not self.suppress_verbose:
                self.display_plugin.info(
                    "💰 Quota conservation: skipping yt-api, using yt-dlp instead"
                )
        return use_api

    def _get_thread_db_connection(self, get_db_connection: callable) -> Any:
        """
        Get or create a database connection for the current thread.

        Uses thread-local storage to ensure each thread has its own connection.
        All connections are tracked for cleanup.

        Args:
            get_db_connection: Function to create a new DB connection

        Returns:
            Database connection for the current thread
        """
        if not hasattr(self._thread_local, "conn"):
            conn = get_db_connection(timeout=30.0)
            self._thread_local.conn = conn
            with self._conns_lock:
                self._all_conns.append(conn)
        return self._thread_local.conn

    def _initialize_thread_local_storage(self) -> None:
        """Initialize thread-local storage for database connections."""
        import threading

        self._thread_local = threading.local()
        self._all_conns = []
        self._conns_lock = threading.Lock()

    def _backfill_new_channel_metadata(
        self,
        channel_id: str,
        channel_display_name: str,
        db_state: dict[str, Any],
    ) -> tuple[bool, bool, str | None]:
        """
        Fetch and store metadata for a new channel using yt-api.

        For brand new channels (db_count=0) with new videos, fetch all
        video metadata from yt-api and store it. This avoids running yt-dlp
        just to get video IDs.

        Args:
            channel_id: Channel ID to fetch metadata for
            channel_display_name: Display name for messages
            db_state: Database state dict (modified in-place)

        Returns:
            tuple: (api_total_mismatch, should_skip_download, skip_reason)
        """
        from yt_fts.core.database import add_videos_bulk
        from yt_fts.db.channels import get_channel_api_total, set_channel_api_total
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        should_skip_download = False
        skip_reason = None
        api_total_mismatch = False
        stored_api_total = get_channel_api_total(channel_id)

        try:
            backfill = YouTubeAPIBackfill(
                console=self.console,
                show_progress=not self.suppress_quota_print,
            )
            if not self.suppress_verbose:
                self.display_plugin.info("Fetching all videos via yt-api...")
            videos_data = backfill.fetch_all_videos_from_channel(channel_id)

            if videos_data:
                set_channel_api_total(channel_id, len(videos_data))
                added_count = add_videos_bulk(
                    channel_id,
                    videos_data,
                    batch_manager=self.batch_manager,
                )
                quota_info = YouTubeAPIBackfill.get_global_quota_info()
                num_keys = len(YouTubeAPIBackfill()._load_api_keys())
                total_remaining = quota_info["remaining"] * num_keys

                if (added_count or 0) > 0:
                    self.display_plugin.info(
                        f"✓ yt-api: {added_count} new videos saved "
                        f"({quota_info['used']:,} quota used, {total_remaining:,} remaining)"
                    )
                    db_state["db_count"] = len(videos_data)
                    api_total_mismatch = False
                    if stored_api_total and db_state["db_count"] == stored_api_total:
                        self.display_plugin.info(
                            f"✓ {channel_display_name}: All {db_state['db_count']} videos have metadata"
                        )
                else:
                    self.display_plugin.info(
                        f"✓ yt-api: {len(videos_data)} videos already in database "
                        f"({quota_info['used']:,} quota used, {total_remaining:,} remaining)"
                    )
                    db_state["db_count"] = len(videos_data)
                    api_total_mismatch = False
                    if stored_api_total and db_state["db_count"] == stored_api_total:
                        self.display_plugin.info(
                            f"✓ {channel_display_name}: All {db_state['db_count']} videos have metadata"
                        )

                if self.transcribe_audio_only:
                    should_skip_download = False
                else:
                    should_skip_download = True
                    skip_reason = f"metadata captured for {added_count} videos (subtitles pending)"
            else:
                self.display_plugin.warning(
                    f"{channel_display_name}: yt-api returned 0 objects"
                )
        except Exception as e:
            logger.debug("yt-api video discovery failed: %s", e)
            self.display_plugin.warning(
                f"{channel_display_name}: yt-api discovery failed: {e}"
            )

        return api_total_mismatch, should_skip_download, skip_reason

    def _backfill_new_videos_metadata(
        self,
        channel_id: str,
        new_video_ids: list[str],
        db_state: dict[str, Any],
    ) -> tuple[bool, str | None]:
        """
        Fetch metadata for new videos detected via RSS using yt-api.

        For channels with existing videos (db_count > 0), fetch metadata
        for new videos discovered via RSS. This avoids running yt-dlp
        just to get metadata for new videos.

        Args:
            channel_id: Channel ID to fetch metadata for
            new_video_ids: List of new video IDs from RSS
            db_state: Database state dict

        Returns:
            tuple: (should_skip_download, skip_reason)
        """
        from yt_fts.core.database import add_videos_bulk
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        should_skip_download = False
        skip_reason = None

        backfill = YouTubeAPIBackfill(
            console=self.console,
            show_progress=not self.suppress_quota_print,
        )
        if not self.suppress_verbose:
            self.display_plugin.info(
                f"Fetching metadata for {len(new_video_ids)} new videos via yt-api..."
            )
        metadata_map = backfill._fetch_video_metadata_batch(new_video_ids)

        videos_data = []
        for video_id in new_video_ids:
            metadata = metadata_map.get(video_id, {})
            videos_data.append(
                {
                    "video_id": video_id,
                    "title": metadata.get("title") or f"Video {video_id}",
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "date": metadata.get("date") or "",
                    "duration": metadata.get("duration"),
                    "thumbnail_url": metadata.get("thumbnail_url"),
                    "view_count": metadata.get("view_count", 0),
                    "is_short": metadata.get("is_short", 0),
                }
            )

        added_count = add_videos_bulk(
            channel_id,
            videos_data,
            batch_manager=self.batch_manager,
        )
        quota_info = YouTubeAPIBackfill.get_global_quota_info()
        num_keys = len(YouTubeAPIBackfill()._load_api_keys())
        total_remaining = quota_info["remaining"] * num_keys

        self.display_plugin.info(
            f"✓ yt-api: {added_count} videos metadata updated "
            f"({quota_info['used']:,} quota used, {total_remaining:,} remaining)"
        )

        should_skip_download = True
        skip_reason = (
            f"metadata captured for {added_count} new videos (subtitles pending)"
        )

        return should_skip_download, skip_reason

    def _handle_existing_channel_metadata_backfill(
        self,
        channel_id: str,
        rss_status: str,
        db_state: dict[str, Any],
        should_skip_download: bool,
        rss_result: Any,
    ) -> tuple[bool, str | None]:
        """
        Handle metadata backfill for existing channels with new videos.

        For channels with existing videos (db_count > 0), when new videos
        are detected via RSS, fetch metadata using yt-api to avoid
        running full yt-dlp download.

        Args:
            channel_id: Channel ID to backfill
            rss_status: Current RSS status
            db_state: Database state dict
            should_skip_download: Current skip flag
            rss_result: RSS result object containing video_ids

        Returns:
            tuple: (should_skip_download, skip_reason)
        """
        use_api_for_metadata = self._should_use_api_for_metadata(db_state["db_count"])

        if not (
            rss_status == "new_videos"
            and (db_state["db_count"] or 0) > 0
            and (self.min_saved == 0)
            and channel_id
            and (not should_skip_download)
            and use_api_for_metadata
        ):
            return should_skip_download, None

        new_video_ids = rss_result.video_ids if rss_result else []
        if not new_video_ids:
            self.display_plugin.info("No new video IDs from RSS")
            return should_skip_download, None

        try:
            return self._backfill_new_videos_metadata(
                channel_id,
                new_video_ids,
                db_state,
            )
        except Exception as e:
            logger.debug("yt-api metadata fetch failed: %s", e)
            self.display_plugin.warning(f"yt-api metadata fetch failed: {e}")
            return should_skip_download, None

    def _handle_gap_detected(
        self,
        channel_id: str,
        channel_display_name: str,
        db_state: dict[str, Any],
        get_vid_ids_by_channel_id: callable,
    ) -> tuple[bool, str | None, list[str] | None]:
        """
        Handle gap detection or API total mismatch by fetching full video list.

        When RSS indicates a gap or API total doesn't match DB count, fetch
        the complete video list from yt-api to identify missing videos.

        Args:
            channel_id: Channel ID to check for gaps
            channel_display_name: Display name for messages
            db_state: Database state dict
            get_vid_ids_by_channel_id: Function to get existing video IDs

        Returns:
            tuple: (should_skip_download, skip_reason, rss_video_ids_for_download)
        """
        from yt_fts.core.database import add_videos_bulk, get_vid_ids_by_channel_id
        from yt_fts.db.channels import set_channel_api_total
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        should_skip_download = False
        skip_reason = None
        rss_video_ids_for_download = None

        backfill = YouTubeAPIBackfill(
            console=self.console,
            show_progress=not self.suppress_quota_print,
        )
        if not self.suppress_verbose:
            self.display_plugin.info(
                "   ⎿ [yellow]![/yellow] History gap detected, verifying with yt-api..."
            )
        videos_data = backfill.fetch_all_videos_from_channel(channel_id)

        if videos_data:
            set_channel_api_total(channel_id, len(videos_data))
            existing_video_ids = set()
            try:
                db_videos = get_vid_ids_by_channel_id(channel_id)
                existing_video_ids = {vid[0] for vid in db_videos}
            except Exception:
                pass

            missing_videos = []
            for video in videos_data:
                if video["video_id"] not in existing_video_ids:
                    missing_videos.append(video)
            missing_count = len(missing_videos)

            if missing_count == 0:
                should_skip_download = True
                skip_reason = f"channel complete ({len(videos_data)} videos)"
                self.display_plugin.info(
                    f"   ⎿ [green]✓[/green] db: {self._format_and_display_db_stats(db_state)} already in database"
                )
            else:
                add_videos_bulk(
                    channel_id,
                    missing_videos,
                    batch_manager=self.batch_manager,
                )
                quota_info = YouTubeAPIBackfill.get_global_quota_info()
                num_keys = len(YouTubeAPIBackfill()._load_api_keys())
                total_remaining = quota_info["remaining"] * num_keys
                self.display_plugin.info(
                    f"yt-api: {len(videos_data)} objects total, {db_state['db_count']} existing, "
                    f"{missing_count} new ({quota_info['used']:,} quota used, {total_remaining:,} remaining)"
                )
                rss_video_ids_for_download = [v["video_id"] for v in missing_videos]
                self.display_plugin.info(
                    f"yt-dlp will download {missing_count} missing videos"
                )
        else:
            self.display_plugin.warning(
                f"{channel_display_name}: yt-api returned no videos, falling back to yt-dlp"
            )

        return should_skip_download, skip_reason, rss_video_ids_for_download

    def _try_handle_gap_with_error_handling(
        self,
        channel_id: str,
        channel_display_name: str,
        db_state: dict[str, Any],
        get_vid_ids_by_channel_id: callable,
        should_skip_download: bool,
        skip_reason: str | None,
        rss_video_ids_for_download: list[str] | None,
        rss_status: str,
        api_total_mismatch: bool,
    ) -> tuple[bool, str | None, list[str] | None]:
        """
        Handle gap detection or API total mismatch with error handling.

        Wraps the gap handling logic with try-except to gracefully
        handle failures.

        Args:
            channel_id: Channel ID to check for gaps
            channel_display_name: Display name for messages
            db_state: Database state dict
            get_vid_ids_by_channel_id: Function to get existing video IDs
            should_skip_download: Current skip flag
            skip_reason: Current skip reason
            rss_video_ids_for_download: Current video IDs for download
            rss_status: Current RSS status
            api_total_mismatch: API total mismatch flag

        Returns:
            tuple: (should_skip_download, skip_reason, rss_video_ids_for_download)
        """
        if not (
            (rss_status in ("gap_detected", "error") or api_total_mismatch)
            and channel_id
            and (not should_skip_download)
        ):
            return should_skip_download, skip_reason, rss_video_ids_for_download

        try:
            return self._handle_gap_detected(
                channel_id,
                channel_display_name,
                db_state,
                get_vid_ids_by_channel_id,
            )
        except Exception as e:
            logger.debug("Gap handling failed for %s: %s", channel_id, e)
            self.display_plugin.warning(
                f"{channel_display_name}: Gap handling failed: {e}"
            )
            return should_skip_download, skip_reason, rss_video_ids_for_download

    def _handle_backfill_videos_without_subs(
        self,
        channel_id: str,
        channel_display_name: str,
        original_channel: str,
        resolved_url: str,
        db_state: dict[str, Any],
        rss_missing_count: int,
        coordinator: Any,
        executor: Any,
        results: dict[str, Any],
    ) -> tuple[bool, int]:
        """
        Handle backfill of videos without subtitles.

        For channels where db_no_subs > 0 and min_saved > 0 or transcribe_audio_only,
        fetch and transcribe videos that don't have subtitles yet.

        Args:
            channel_id: Channel ID
            channel_display_name: Display name for messages
            original_channel: Original channel identifier
            resolved_url: Resolved channel URL
            db_state: Database state dict
            rss_missing_count: Number of videos missing from RSS
            coordinator: Task coordinator
            executor: Thread executor
            results: Results dict (modified in-place)

        Returns:
            tuple: (backfill_completed, completed_count_increment)
        """
        from yt_fts.core.database import get_video_ids_without_subtitles
        from yt_fts.download.download_handler import DownloadHandler

        backfill_needed = False
        backfill_video_ids = []

        if (
            channel_id
            and (db_state["db_no_subs"] or 0) > 0
            and ((self.min_saved or 0) > 0 or self.transcribe_audio_only)
        ):
            backfill_limit = None
            if self.videos_download_per_batch:
                backfill_limit = max(
                    0,
                    self.videos_download_per_batch - rss_missing_count,
                )
            backfill_video_ids = get_video_ids_without_subtitles(
                channel_id, limit=backfill_limit
            )
            if backfill_video_ids:
                backfill_needed = True
                backfill_count = len(backfill_video_ids)
                if self.transcribe_audio_only:
                    self.display_plugin.info(f"yt-dlp: Fetching {backfill_count} audio")
                else:
                    sub_word = "subtitle" if backfill_count == 1 else "subtitles"
                    self.display_plugin.info(
                        f"yt-dlp: Fetching {backfill_count} missing {sub_word}"
                    )

        if backfill_needed:

            def _backfill_log_callback(msg: str) -> None:
                """Wrapper to convert single-arg callback to log_operation format."""
                if msg and msg.strip():
                    log_operation("backfill", msg, level=10)

            handler = DownloadHandler(
                number_of_jobs=1,
                language=self.language,
                cookies_from_browser=self.cookies_from_browser,
                log_callback=_backfill_log_callback,
                transcribe_audio_only=self.transcribe_audio_only,
                whisper_model=self.whisper_model,
                keep_audio=self.keep_audio,
                include_channel_name_in_messages=False,
            )
            handler.channel_id = channel_id
            handler.video_ids = backfill_video_ids
            handler.resolved_url = resolved_url
            handler.channel_name = channel_display_name
            handler.suppress_status_messages = True
            handler._max_videos = None

            coordinator.add_task(
                description="     backfill:",
                channel_name=original_channel,
                total=100,
                visible=True,
                fields={"stats": ""},
            )

            future = executor.submit(
                self._download_single_channel_optimized,
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=coordinator,
                log_callback=_backfill_log_callback,
                rich_mode=False,
                video_ids=backfill_video_ids,
            )

            completed_count_increment = 0
            try:
                result = future.result()
                if result.get("success"):
                    downloaded = result.get("videos_count") or 0
                    without_subs = result.get("videos_without_subtitles") or 0
                    if downloaded > 0:
                        self.display_plugin.display_download_result(
                            {
                                "success": True,
                                "videos_count": downloaded,
                                "message": f"Backfilled {downloaded} subtitles",
                            }
                        )
                        results["successful"].append(
                            {
                                "channel": original_channel,
                                "videos_count": downloaded,
                            }
                        )
                        completed_count_increment = 1
                    elif without_subs > 0:
                        word = "video" if without_subs == 1 else "videos"
                        verb = "has" if without_subs == 1 else "have"
                        self.display_plugin.warning(
                            f"{without_subs} {word} {verb} no subtitles available"
                        )
                        results["skipped"].append(
                            {
                                "channel": original_channel,
                                "message": f"{without_subs} videos unavailable",
                            }
                        )
                    else:
                        self.display_plugin.display_download_result(
                            {
                                "success": True,
                                "videos_count": 0,
                                "message": "No new subtitles",
                            }
                        )
                        results["skipped"].append(
                            {
                                "channel": original_channel,
                                "message": "No new subtitles",
                            }
                        )
                else:
                    error_msg = result.get("error", "Unknown error")
                    self.display_plugin.error(f"Backfill failed: {error_msg}")
                    results["failed"].append(
                        {
                            "channel": original_channel,
                            "error": error_msg,
                        }
                    )
                    if not self.continue_on_error:
                        msg = f"Backfill failed for {original_channel}: {error_msg}"
                        raise Exception(
                            msg
                        )
            except Exception as e:
                self.display_plugin.error(f"Backfill error: {e}")
                results["failed"].append(
                    {
                        "channel": original_channel,
                        "error": str(e),
                    }
                )
                if not self.continue_on_error:
                    raise

            coordinator.remove_task(original_channel)
            return True, completed_count_increment

        return False, 0

    def _discover_channel_via_api_and_update_state(
        self,
        resolved_url: str,
        db_state: dict[str, Any],
        get_channel_stats: callable,
    ) -> tuple[str | None, str]:
        """
        Discover channel via API and update database state with stats.

        For channels without a UC channel_id, use the ChannelHandleService
        to discover the real channel_id and load stats.

        Args:
            resolved_url: Channel URL to discover
            db_state: Database state dict (modified in-place)
            get_channel_stats: Function to get channel stats

        Returns:
            tuple: (channel_id, discovery_source)
        """
        from yt_fts.db.channels import add_channel_info
        from yt_fts.services.channel_service import ChannelHandleService

        if not self.suppress_verbose:
            self.display_plugin.info("Discovering channel via API...")

        handle_service = ChannelHandleService()
        handle_discovery = handle_service.discover_handle(
            resolved_url, force_refresh=True
        )

        if handle_discovery and handle_discovery.get("channel_id", "").startswith("UC"):
            channel_id = handle_discovery["channel_id"]
            discovery_source = "api"

            # Store channel name from API discovery for later display
            if handle_discovery.get("channel_name"):
                add_channel_info(
                    channel_id=channel_id,
                    channel_name=handle_discovery["channel_name"],
                    channel_url=resolved_url,
                )

            if not self.suppress_verbose:
                self.display_plugin.info(f"Found channel_id: {channel_id[:20]}...")

            # Update db_state with API-discovered stats
            stats = get_channel_stats(channel_id)
            db_state["db_count"] = stats["total"]
            db_state["db_with_subs"] = stats["with_transcripts"]
            db_state["db_scheduled"] = stats["scheduled"]
            db_state["db_members"] = stats["members_only"]
            db_state["db_unavailable"] = stats["unavailable"]
            db_state["db_shorts"] = stats["shorts"]
            db_state["db_no_subs"] = stats["without_transcripts"]

            return channel_id, discovery_source

        return None, "none"

    def _format_and_display_db_stats(self, db_state: dict[str, Any]) -> str:
        """
        Format and display database statistics.

        Args:
            db_state: Database state dict

        Returns:
            Formatted db stats string
        """
        parts = []
        parts.append(f"{db_state['db_count']} total")
        video_parts = []
        video_parts.append(f"{db_state['db_with_subs']} with transcripts")
        video_parts.append(f"{db_state['db_no_subs']} no subs")
        video_parts.append(f"{db_state['db_scheduled']} sch")
        video_parts.append(f"{db_state['db_members']} mem")
        parts.append(", ".join(video_parts))
        main_stats = " | ".join(parts)
        if (db_state["db_shorts"] or 0) > 0:
            db_stats = f"{main_stats} | {db_state['db_shorts']} shorts"
        else:
            db_stats = main_stats

        if not self.suppress_verbose:
            self.display_plugin.info(f"db: {db_stats}")

        return db_stats

    def _execute_ytdlp_download_for_channel(
        self,
        original_channel: str,
        resolved_url: str,
        channel_id: str,
        coordinator: Any,
        executor: Any,
        rss_video_ids_for_download: list[str] | None,
        suppress_verbose: bool,
        target: int,
        successful_downloads: int,
        total_videos_saved: int,
    ) -> tuple[int, int, int]:
        """
        Execute yt-dlp download for a single channel and handle the result.

        Args:
            original_channel: Original channel identifier
            resolved_url: Resolved channel URL
            channel_id: Channel ID
            coordinator: Progress coordinator
            executor: Thread executor
            rss_video_ids_for_download: Video IDs from RSS to download
            suppress_verbose: Whether to suppress verbose output
            target: Target download count
            successful_downloads: Current successful downloads count
            total_videos_saved: Current total videos saved count

        Returns:
            tuple: (completed_count_increment, successful_downloads_increment, total_videos_saved_increment)
        """
        completed_count_inc = 1
        successful_downloads_inc = 0
        total_videos_saved_inc = 0

        coordinator.add_task(
            description="     yt-dlp:",
            channel_name=original_channel,
            total=100,
            visible=True,
            fields={"stats": ""},
        )

        future = executor.submit(
            self._download_single_channel_optimized,
            original_channel,
            resolved_url,
            channel_id,
            coordinator,
            None,
            False,
            rss_video_ids_for_download,
        )

        try:
            if self.time_per_batch and self.time_per_batch > 0:
                remaining_time = self.time_per_batch - (
                    time.time() - self.batch_start_time
                )
                if remaining_time <= 0:
                    self.display_plugin.warning("Total batch timeout reached")
                    return (
                        completed_count_inc,
                        successful_downloads_inc,
                        total_videos_saved_inc,
                    )
                result = future.result(timeout=remaining_time)
            else:
                result = future.result()

            if result["success"]:
                videos_count = result.get("videos_count") or 0
                total_videos = result.get("total_videos") or videos_count
                total_videos_saved_inc = videos_count

                if videos_count > 0:
                    if (
                        self.videos_download_per_batch
                        and (successful_downloads + total_videos_saved_inc)
                        >= self.videos_download_per_batch
                    ):
                        self.display_plugin.warning(
                            "Total videos limit reached. Stopping..."
                        )
                        successful_downloads_inc = 1
                    if not suppress_verbose:
                        self.display_plugin.display_download_result(
                            {
                                "success": True,
                                "videos_count": videos_count,
                                "videos_without_subtitles": result.get(
                                    "videos_without_subtitles"
                                )
                                or 0,
                                "total_videos": total_videos,
                                "time_taken": result.get("time_taken") or "",
                                "quota_used": result.get("quota_used") or 0,
                            }
                        )
                    successful_downloads_inc = 1
                else:
                    missing_subs = result.get("videos_without_subtitles") or 0
                    total_videos = result.get("total_videos", 0)
                    filtered_count = result.get("filtered_count", 0)
                    filter_summary = result.get("filter_summary", "")

                    if missing_subs and missing_subs == total_videos:
                        skip_reason = "subtitles not available in any language"
                    elif missing_subs:
                        skip_reason = (
                            f"no subtitles for {missing_subs} of {total_videos} videos"
                        )
                    elif total_videos == 0:
                        if filtered_count > 0 and filter_summary:
                            skip_reason = f"RSS video(s) were {filter_summary}"
                        else:
                            # New channel with 0 videos - show what yt-api found
                            if not suppress_verbose:
                                self.display_plugin.info(
                                    "   ⎿ api: yt-api full scan returned 0 videos"
                                )
                            skip_reason = "no videos found for this channel"
                    else:
                        skip_reason = "no transcript to store in db"

                    if not suppress_verbose:
                        self.display_plugin.display_download_result(
                            {
                                "success": True,
                                "videos_count": 0,
                                "message": f"⏭ {skip_reason}",
                            }
                        )

        except TimeoutError:
            self.display_plugin.warning(
                f"Total batch timeout reached ({self.time_per_batch}s). Stopping..."
            )
        except Exception as exc:
            if not suppress_verbose:
                self.display_plugin.display_download_result(
                    {"success": False, "error": str(exc)}
                )

        coordinator.remove_task(original_channel)
        return completed_count_inc, successful_downloads_inc, total_videos_saved_inc

    def _resolve_channel_id_and_discovery_source(
        self,
        channel_id: str | None,
        resolved_url: str,
        db_state: dict[str, Any],
        get_vid_ids_by_channel_id: callable,
        get_channel_stats: callable,
    ) -> tuple[str | None, str, dict[str, Any]]:
        """
        Resolve channel ID and determine discovery source.

        Handles various channel ID resolution strategies:
        1. UC channel_id → use UnifiedChannelDiscovery
        2. Handle-only channels → use API discovery
        3. Handle channels with min_saved > 0 → skip API discovery

        Args:
            channel_id: Initial channel ID (may be None)
            resolved_url: Resolved channel URL
            db_state: Database state dict (modified in-place)
            get_vid_ids_by_channel_id: Function to get video IDs
            get_channel_stats: Function to get channel stats

        Returns:
            tuple: (channel_id, discovery_source, db_state)
        """
        from .unified_discovery import UnifiedChannelDiscovery

        discovery_source = "none"
        discovery = None

        if channel_id and channel_id.startswith("UC"):
            disco = UnifiedChannelDiscovery()
            discovery = disco.discover(resolved_url)
            discovery_source = discovery.get("source", "none")
        elif (
            (not channel_id or (channel_id and channel_id.startswith("handle_")))
            and self.min_saved == 0
            and ("@" in resolved_url or "/" in resolved_url.split("/")[-2:])
        ):
            try:
                channel_id, discovery_source = (
                    self._discover_channel_via_api_and_update_state(
                        resolved_url, db_state, get_channel_stats
                    )
                )
            except Exception as e:
                logger.debug("API discovery failed: %s, falling back to yt-dlp", e)
                disco = UnifiedChannelDiscovery()
                discovery = disco.discover(resolved_url)
                discovery_source = discovery.get("source", "none")
                if discovery.get("channel_id"):
                    channel_id = discovery["channel_id"]
        else:
            disco = UnifiedChannelDiscovery()
            discovery = disco.discover(resolved_url)
            discovery_source = discovery.get("source", "none")

        if (
            discovery_source == "database" and (db_state["db_count"] or 0) > 0
        ) or discovery_source == "api":
            pass
        elif discovery_source == "ytdlp":
            discovered_id = discovery.get("channel_id")
            if discovered_id and (not channel_id or channel_id.startswith("handle_")):
                channel_id = discovered_id
                self._refresh_db_state(
                    channel_id, db_state, get_vid_ids_by_channel_id, get_channel_stats
                )
                logger.debug(
                    "Refreshed db_state after ytdlp discovery: %s total, %s with subs, %s video_ids",
                    db_state["db_count"],
                    db_state["db_with_subs"],
                    len(db_state["db_video_ids"]),
                )

        if (
            channel_id
            and channel_id.startswith("handle_")
            and (db_state["db_count"] == 0)
        ):
            from yt_fts.services.channel_service import ChannelHandleService

            try:
                handle_service = ChannelHandleService()
                handle_discovery = handle_service.discover_handle(
                    resolved_url, force_refresh=True
                )
                if handle_discovery and handle_discovery.get(
                    "channel_id", ""
                ).startswith("UC"):
                    channel_id = handle_discovery["channel_id"]
                    logger.debug(
                        "Updated channel_id from handle discovery: %s",
                        channel_id,
                    )
                    self._refresh_db_state(
                        channel_id,
                        db_state,
                        get_vid_ids_by_channel_id,
                        get_channel_stats,
                    )
                    logger.debug(
                        "Refreshed db_state after channel_id resolution: %s total, %s with subs, %s video_ids",
                        db_state["db_count"],
                        db_state["db_with_subs"],
                        len(db_state["db_video_ids"]),
                    )
            except Exception as e:
                logger.debug("Failed to re-discover channel_id: %s", e)

        return channel_id, discovery_source, db_state

    def _perform_rss_check_and_determine_status(
        self,
        channel_id: str | None,
        handle: str,
        resolved_url: str,
        db_state: dict[str, Any],
        original_channel: str,
        suppress_verbose: bool,
        rss_checker: Any,
    ) -> tuple[str, str, bool, int, list[str] | None, bool, Any]:
        """
        Perform RSS check and determine the status for the channel.

        Handles recheck of unavailable videos, RSS checking, and status
        determination. Returns the RSS status, message, and related state.

        Args:
            channel_id: Channel ID (may be None for handle-only channels)
            handle: Channel handle
            resolved_url: Resolved channel URL
            db_state: Database state dict
            original_channel: Original channel identifier
            suppress_verbose: Whether to suppress verbose output
            rss_checker: RSS checker instance for channel validation

        Returns:
            tuple: (status, message, rss_skip, rss_missing_count, rss_video_ids_for_download, new_channel_skipped_rss, rss_result)
        """
        from yt_fts.core.database import (
            add_video,
            get_videos_needing_recheck,
            update_video_last_checked,
        )

        rss_missing_count = None
        rss_skip = False
        rss_error_msg = None
        rss_video_ids_for_download = None
        recheck_available = []
        new_channel_skipped_rss = False

        if channel_id:
            recheck_available = recheck_unavailable_videos(
                channel_id,
                rss_checker,
                get_videos_needing_recheck,
                update_video_last_checked,
            )
            if recheck_available:
                msg = f"{len(recheck_available)} previously unavailable video(s) now available"
                if not suppress_verbose:
                    self.display_plugin.display_rss_status(
                        {"status": "skip", "message": msg}
                    )
                rss_video_ids_for_download = recheck_available
                rss_missing_count = len(recheck_available)
                rss_skip = False

        try:
            # Display new channel message before RSS check
            if db_state["db_count"] == 0 and not suppress_verbose:
                self.display_plugin.display_rss_status(
                    {
                        "status": "new_videos",
                        "message": "new channel, switching to yt-api for full scan",
                    }
                )
            rss_result, new_channel_skipped_rss = perform_rss_check(
                channel_id,
                handle,
                resolved_url,
                db_state["db_video_ids"],
                db_state["db_count"],
                rss_checker,
                log_operation,
                original_channel,
            )
            if rss_result and rss_result.status == "skip":
                rss_skip = True
                if rss_result.unavailable_video_ids:
                    process_unavailable_videos(
                        channel_id,
                        rss_result.unavailable_video_ids,
                        rss_result.unavailable_video_status,
                        add_video,
                    )
            elif rss_result and rss_result.status == "new_videos":
                rss_video_ids_for_download = rss_result.video_ids
                rss_missing_count = len(rss_result.video_ids)
            elif rss_result and rss_result.status == "gap_detected":
                missing_in_db = [
                    vid
                    for vid in rss_result.video_ids
                    if vid not in db_state["db_video_ids"]
                ]
                rss_missing_count = len(missing_in_db)
                rss_result = rss_checker.check(
                    channel_id=None,
                    handle=handle,
                    resolved_url=resolved_url,
                    db_video_ids=set(),
                )
                if rss_result and rss_result.video_ids:
                    known_ids = self._get_known_video_ids(rss_result.video_ids)
                    rss_missing_count = len(rss_result.video_ids) - len(known_ids)
                    if rss_missing_count == 0:
                        rss_skip = True
        except Exception:
            rss_error_msg = "RSS request failed"
            rss_result = None

        if rss_missing_count == 0:
            rss_skip = True

        # Determine RSS status and format message
        rss_status = determine_rss_status(
            rss_result, rss_skip, rss_missing_count, new_channel_skipped_rss
        )
        status, message = format_rss_status_message(
            rss_status,
            rss_result,
            rss_missing_count,
            rss_error_msg,
            new_channel_skipped_rss,
        )

        return (
            status,
            message,
            rss_skip,
            rss_missing_count or 0,
            rss_video_ids_for_download,
            new_channel_skipped_rss,
            rss_result,
        )

    def download_all(self) -> dict[str, Any]:
        """
        Download all channels with progress tracking and optimized parallel resolution.

        Returns:
            dict: Results with success/failure status for each channel
        """
        results, total_videos_saved = self._initialize_batch_download()
        if results is None:  # Early return from dry_run
            return {
                "successful": [],
                "failed": [],
                "skipped": [],
                "invalid_channels": [],
            }

        channel_downloads, _invalid_channels = self._resolve_and_validate_channels()
        if channel_downloads is None:  # Rich mode early return
            return {
                "successful": [],
                "failed": [],
                "skipped": [],
                "invalid_channels": [],
            }

        suppress_verbose = self.suppress_verbose
        progress_ctx = Progress(
            TextColumn(
                "[bold blue]{task.description}[/bold blue]",
                table_column=Column(width=15),
            ),
            BarColumn(bar_width=20),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage]"
            ),
            TextColumn("{task.fields[stats]}", table_column=Column(width=40)),
            console=self.progress_console,
            auto_refresh=True,
            redirect_stderr=True,
            redirect_stdout=False,
        )
        if not self.suppress_verbose:
            self.console.print(
                f"[cyan]Processing {len(channel_downloads)} channels...[/cyan]"
            )

        # Optimization: Pre-fetch missing channel names in parallel
        self._prefetch_channel_names_parallel(channel_downloads)

        try:
            progress = progress_ctx.__enter__()
            coordinator = ThreadSafeProgressCoordinator(progress)
            coordinator.start()
            workers = self.jobs if self.min_saved == 0 else 1
            executor = ThreadPoolExecutor(max_workers=workers)
            try:
                completed_count = 0
                successful_downloads = 0
                target = (
                    self.target_downloads
                    if self.target_downloads
                    else len(channel_downloads)
                )
                from yt_fts.core.database import (
                    get_channel_stats,
                    get_vid_ids_by_channel_id,
                )
                from yt_fts.services.rss_precheck import create_rss_checker

                rss_checker = create_rss_checker(timeout=10.0)
                self._initialize_thread_local_storage()

                for channel_idx, (
                    original_channel,
                    resolved_url,
                    channel_id,
                ) in enumerate(channel_downloads, 1):
                    if self.time_per_batch and self.time_per_batch > 0:
                        elapsed = time.time() - self.batch_start_time
                        if elapsed >= self.time_per_batch:
                            self.display_plugin.warning(
                                f"Total batch timeout reached ({self.time_per_batch}s). Stopping..."
                            )
                            break
                    print()
                    # Determine status display name
                    status_name = determine_status_name(channel_id, resolved_url)
                    handle = extract_handle(resolved_url)

                    # Initialize database stats
                    db_state = initialize_channel_state()

                    if not channel_id:
                        channel_id = self._get_channel_id_by_url(resolved_url)
                    if channel_id == "__INVALID_CHANNEL__":
                        results["failed"].append(
                            {
                                "channel": original_channel,
                                "error": "Channel not found or deleted",
                            }
                        )
                        completed_count += 1
                        continue
                    if channel_id:
                        is_fresh = self._check_channel_freshness(
                            channel_id, original_channel, results
                        )
                        if is_fresh:
                            completed_count += 1
                            continue
                        try:
                            db_state = load_channel_db_stats(
                                channel_id,
                                get_vid_ids_by_channel_id,
                                get_channel_stats,
                                logging.getLogger(__name__),
                            )
                        except Exception:
                            db_state = initialize_channel_state()

                    # ENSURE channel name is available BEFORE displaying header (PRD AC.3.4)
                    # For channels without a name in database, fetch via API first
                    channel_id = self._ensure_channel_name_in_db(channel_id)

                    channel_display_name, _db_stats = (
                        self._display_and_format_channel_header(
                            channel_id,
                            status_name,
                            db_state,
                            channel_idx,
                            target,
                            suppress_verbose,
                            completed_count,
                            resolved_url,
                        )
                    )
                    channel_id, _discovery_source, db_state = (
                        self._resolve_channel_id_and_discovery_source(
                            channel_id,
                            resolved_url,
                            db_state,
                            get_vid_ids_by_channel_id,
                            get_channel_stats,
                        )
                    )
                    api_total_mismatch = False
                    (
                        _status,
                        _message,
                        rss_skip,
                        rss_missing_count,
                        rss_video_ids_for_download,
                        new_channel_skipped_rss,
                        rss_result,
                    ) = self._perform_rss_check_and_determine_status(
                        channel_id,
                        handle,
                        resolved_url,
                        db_state,
                        original_channel,
                        suppress_verbose,
                        rss_checker,
                    )
                    # Display RSS status
                    if not suppress_verbose and rss_result:
                        self.display_plugin.display_rss_status(rss_result)

                    # Determine RSS status (for conditional checks)
                    rss_status = determine_rss_status(
                        None, rss_skip, rss_missing_count, new_channel_skipped_rss
                    )
                    should_skip_download = False
                    if channel_id:
                        api_total_mismatch = self._check_and_display_api_mismatch(
                            channel_id, db_state
                        )
                    use_api_for_new_channel = self._should_use_api_for_metadata(
                        db_state["db_count"] or 0
                    )
                    if (
                        rss_status == "new_videos"
                        and db_state["db_count"] == 0
                        and channel_id
                        and use_api_for_new_channel
                    ):
                        api_total_mismatch, should_skip_download, skip_reason = (
                            self._backfill_new_channel_metadata(
                                channel_id,
                                channel_display_name,
                                db_state,
                            )
                        )
                    should_skip_download, skip_reason = (
                        self._handle_existing_channel_metadata_backfill(
                            channel_id,
                            rss_status,
                            db_state,
                            should_skip_download,
                            rss_result,
                        )
                    )
                    should_skip_download, skip_reason, rss_video_ids_for_download = (
                        self._try_handle_gap_with_error_handling(
                            channel_id,
                            channel_display_name,
                            db_state,
                            get_vid_ids_by_channel_id,
                            should_skip_download,
                            skip_reason,
                            rss_video_ids_for_download,
                            rss_status,
                            api_total_mismatch,
                        )
                    )
                    if rss_skip or should_skip_download:
                        backfill_completed, completed_increment = (
                            self._handle_backfill_videos_without_subs(
                                channel_id,
                                channel_display_name,
                                original_channel,
                                resolved_url,
                                db_state,
                                rss_missing_count,
                                coordinator,
                                executor,
                                results,
                            )
                        )
                        if backfill_completed:
                            completed_count += completed_increment
                            continue
                        # Skip section runs when backfill was not needed
                        # Reprocess removed - transcription now happens during download workflow
                        skip_reason = (
                            "No new videos (RSS check)"
                            if rss_skip
                            else "Channel complete (yt-api check)"
                        )
                        results["skipped"].append(
                            {"channel": original_channel, "message": skip_reason}
                        )
                        if should_skip_download:
                            if not suppress_verbose:
                                self.display_plugin.display_download_result(
                                    {
                                        "success": True,
                                        "videos_count": 0,
                                        "message": f"✓ {skip_reason}",
                                    }
                                )
                        elif not suppress_verbose:
                            self.display_plugin.display_download_result(
                                {
                                    "success": True,
                                    "videos_count": 0,
                                    "message": f"⏭ {skip_reason}",
                                }
                            )
                        completed_count += 1
                        if (self.min_saved or 0) > 0 and completed_count < len(
                            self.channels
                        ):
                            time.sleep(self.delay_between_channels)
                        continue
                    (
                        completed_count_inc,
                        successful_downloads_inc,
                        total_videos_saved_inc,
                    ) = self._execute_ytdlp_download_for_channel(
                        original_channel,
                        resolved_url,
                        channel_id,
                        coordinator,
                        executor,
                        rss_video_ids_for_download,
                        suppress_verbose,
                        target,
                        successful_downloads,
                        total_videos_saved,
                    )
                    completed_count += completed_count_inc
                    successful_downloads += successful_downloads_inc
                    total_videos_saved += total_videos_saved_inc

                    if completed_count_inc and total_videos_saved_inc > 0:
                        results["successful"].append(
                            {
                                "channel": original_channel,
                                "videos_count": total_videos_saved_inc,
                                "message": "Success",
                            }
                        )
                    if (
                        self.target_downloads
                        and successful_downloads >= self.target_downloads
                    ):
                        break
                    if (self.min_saved or 0) > 0 and completed_count < len(
                        self.channels
                    ):
                        time.sleep(self.delay_between_channels)
            except KeyboardInterrupt:
                if self.batch_manager:
                    self.batch_manager.flush()
                executor.shutdown(wait=False, cancel_futures=True)
                raise
            finally:
                if not executor._shutdown:
                    executor.shutdown(wait=True)
                for conn in self._all_conns:
                    with contextlib.suppress(Exception):
                        conn.close()
        except BaseException:
            raise
        finally:
            try:
                for task_id in progress.tasks:
                    progress.stop_task(task_id)
            except Exception:
                pass
            with contextlib.suppress(IndexError, Exception):
                progress_ctx.__exit__(None, None, None)
            if self.batch_manager:
                with contextlib.suppress(Exception):
                    self.batch_manager.flush()
        self.console.print()
        self.console.print("[bold cyan]─[/bold cyan]".ljust(60, "─"))
        self.console.print()
        if self.batch_manager:
            self.batch_manager.flush()
        self._print_summary(results)
        return results

    def _download_single_channel_optimized(
        self,
        original_channel: str,
        resolved_url: str,
        channel_id: str,
        coordinator: ThreadSafeProgressCoordinator,
        log_callback: Callable[[str], None] | None = None,
        rich_mode: bool = False,
        video_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        """
        Download a single channel with optimized channel ID handling.

        Args:
            original_channel: Original channel input for display
            resolved_url: Resolved channel URL
            channel_id: Extracted channel ID (or None for handles)
            coordinator: ThreadSafeProgressCoordinator for queue-based progress updates
            log_callback: Optional callback for log messages
            rich_mode: Whether to use Rich UI mode
            video_ids: Optional list of specific video IDs to download (from RSS precheck)

        Returns:
            dict: Result with success status and details
        """
        import time

        from yt_fts.utils.interrupt_handler import check_interruption

        # Get actual channel name from database for display
        channel_display_name = self._get_channel_display_name(
            channel_id, original_channel
        )

        log_operation(
            "channel_download",
            f"Starting download: {original_channel}",
            channel=original_channel,
            resolved_url=resolved_url,
            channel_id=channel_id,
            video_ids_count=len(video_ids) if video_ids else 0,
            level=10,
        )
        for attempt in range(self.max_retries + 1):
            if check_interruption():
                return {
                    "success": False,
                    "error": "Interrupted by user",
                    "interrupted": True,
                }
            try:
                handler = DownloadHandler(
                    number_of_jobs=self.jobs,
                    language=self.language,
                    cookies_from_browser=self.cookies_from_browser,
                    fail_fast=not self.continue_on_error,
                    max_time_per_channel=self.time_per_channel,
                    max_time_per_video=self.time_per_video,
                    max_videos=self.max_videos,
                    console=self.console,
                    log_callback=log_callback,
                    rich_mode=rich_mode,
                    suppress_status_messages=True,
                    transcribe_audio_only=self.transcribe_audio_only,
                    whisper_model=self.whisper_model,
                    keep_audio=self.keep_audio,
                    include_channel_name_in_messages=False,
                )
                # Set the actual channel name from database
                handler.channel_id = channel_id
                handler.channel_name = channel_display_name
                handler.set_progress_tracker(coordinator, original_channel)
                if video_ids:
                    handler.video_ids = video_ids
                    handler.min_saved = self.min_saved
                try:
                    start_time = time.time()
                    from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

                    quota_before = YouTubeAPIBackfill.get_global_quota_info()["used"]
                    handler.download_channel_optimized(
                        resolved_url, skip_resolution=True
                    )
                    videos_saved = handler.get_videos_saved() or 0
                    elapsed_seconds = time.time() - start_time
                    quota_after = YouTubeAPIBackfill.get_global_quota_info()["used"]
                    quota_used = quota_after - quota_before
                    if elapsed_seconds >= 60:
                        time_str = f"{int(elapsed_seconds // 60)}:{int(elapsed_seconds % 60):02d}"
                    else:
                        time_str = f"{int(elapsed_seconds)}s"
                    log_operation(
                        "channel_success",
                        f"Successfully downloaded: {original_channel}",
                        channel=original_channel,
                        channel_id=channel_id,
                        videos_saved=videos_saved,
                        time_taken=elapsed_seconds,
                        quota_used=quota_used,
                        level=10,
                    )
                    return {
                        "success": True,
                        "channel": original_channel,
                        "resolved_url": resolved_url,
                        "channel_id": channel_id,
                        "message": "Successfully downloaded channel",
                        "videos_count": videos_saved,
                        "videos_saved": videos_saved,
                        "videos_without_subtitles": handler.videos_without_subtitles,
                        "total_videos": (
                            handler.total_videos_found
                            if hasattr(handler, "total_videos_found")
                            and handler.total_videos_found > 0
                            else len(handler.video_ids) if handler.video_ids else 0
                        ),
                        "time_taken": time_str,
                        "quota_used": quota_used,
                        "filter_summary": (
                            handler._get_filter_summary()
                            if hasattr(handler, "_get_filter_summary")
                            else ""
                        ),
                        "filtered_count": (
                            sum(handler.filter_reasons.values())
                            if hasattr(handler, "filter_reasons")
                            else 0
                        ),
                    }
                except Exception:
                    raise
            except KeyboardInterrupt:
                if "handler" in locals():
                    handler.cleanup_progress()
                raise
            except DownloadTimeoutException as e:
                if "handler" in locals():
                    handler.cleanup_progress()
                msg = f"[yellow]⏱️  {original_channel}: {e!s}[/yellow]"
                if rich_mode and log_callback:
                    log_callback(msg)
                else:
                    self.display_plugin.info(msg)
                log_technical_error(
                    e,
                    {
                        "channel": original_channel,
                        "resolved_url": resolved_url,
                        "channel_id": channel_id,
                        "error_type": "timeout",
                    },
                )
                return {
                    "success": False,
                    "error": f"Download timeout: {e!s}",
                    "timed_out": True,
                }
            except BaseURLFallbackFailed as e:
                return {"success": False, "error": str(e)}
            except Exception as e:
                if "handler" in locals():
                    handler.cleanup_progress()
                error_msg = str(e)
                # Early-exit for genuinely empty/deleted channels (no point retrying)
                from yt_fts.utils.retry_classifier import should_skip_retry

                if should_skip_retry(error_msg):
                    log_technical_error(
                        e,
                        {
                            "channel": original_channel,
                            "resolved_url": resolved_url,
                            "skip_reason": "genuinely_empty_or_deleted",
                        },
                    )
                    return {
                        "success": False,
                        "error": str(e),
                        "skipped_retry": True,
                    }
                if attempt < self.max_retries:
                    from yt_fts.utils.retry_classifier import (
                        get_backoff_time,
                        is_rate_limit_error,
                    )

                    is_rate_limit = is_rate_limit_error(error_msg)
                    wait_time = get_backoff_time(error_msg, attempt)
                    if is_rate_limit:
                        msg = f"[yellow]⚠️  Rate limited - waiting {wait_time}s before retry[/yellow]"
                        if rich_mode and log_callback:
                            log_callback(msg)
                        else:
                            self.display_plugin.info(msg)
                    for _ in range(int(wait_time * 10)):
                        time.sleep(0.1)
                        if check_interruption():
                            raise KeyboardInterrupt
                    log_technical_error(
                        e,
                        {
                            "channel": original_channel,
                            "resolved_url": resolved_url,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries + 1,
                            "is_retry": True,
                            "is_rate_limit": is_rate_limit,
                        },
                    )
                else:
                    log_technical_error(
                        e,
                        {
                            "channel": original_channel,
                            "resolved_url": resolved_url,
                            "attempt": attempt + 1,
                            "max_retries": self.max_retries + 1,
                            "is_final_failure": True,
                        },
                    )
                    # Track permanently failed channels to skip in future runs
                    from yt_fts.core.database import (
                        add_skipped_channel,
                        should_skip_permanent,
                    )

                    should_track, skip_reason = should_skip_permanent(error_msg)
                    if should_track:
                        add_skipped_channel(
                            resolved_url, skip_reason or "permanent_failure"
                        )
                        return {
                            "success": False,
                            "error": f"Failed after {self.max_retries + 1} attempts: {e!s}",
                            "permanently_failed": True,
                            "skip_reason": skip_reason,
                        }
                    return {
                        "success": False,
                        "error": f"Failed after {self.max_retries + 1} attempts: {e!s}",
                    }
        return {"success": False, "error": "Max retries exceeded"}

    def _download_single_channel_resolved(
        self,
        original_channel: str,
        resolved_channel: str,
        progress: Progress,
        main_task_id: TaskID,
    ) -> dict[str, Any]:
        """
        Download a single channel with retry logic (already resolved).

        Args:
            original_channel: Original channel input for display
            resolved_channel: Resolved channel ID for downloading
            progress: Progress bar object
            main_task_id: Main progress task ID

        Returns:
            dict: Result with success status and details
        """
        # Get actual channel name from database for display
        channel_id = (
            resolved_channel.split("/channel/")[-1].split("/")[0]
            if "/channel/" in resolved_channel
            else None
        )
        channel_display_name = self._get_channel_display_name(
            channel_id, original_channel
        )

        for attempt in range(self.max_retries + 1):
            try:
                handler = DownloadHandler(
                    number_of_jobs=self.jobs,
                    language=self.language,
                    cookies_from_browser=self.cookies_from_browser,
                    fail_fast=not self.continue_on_error,
                    max_time_per_channel=self.time_per_channel,
                    max_time_per_video=self.time_per_video,
                    max_videos=self.max_videos,
                    console=self.console,
                    transcribe_audio_only=self.transcribe_audio_only,
                    whisper_model=self.whisper_model,
                    keep_audio=self.keep_audio,
                )
                # Set the actual channel name from database
                if channel_id:
                    handler.channel_id = channel_id
                handler.channel_name = channel_display_name
                try:
                    handler.download_channel(resolved_channel)
                    return {
                        "success": True,
                        "channel": original_channel,
                        "resolved_channel": resolved_channel,
                        "message": "Successfully downloaded channel",
                        "videos_count": handler.get_videos_saved(),
                    }
                except Exception:
                    raise
            except DownloadTimeoutException as e:
                if "handler" in locals():
                    handler.cleanup_progress()
                self.display_plugin.warning(f"  {original_channel}: {e!s}")
                return {
                    "success": False,
                    "error": f"Download timeout: {e!s}",
                    "timed_out": True,
                }
            except Exception as e:
                if "handler" in locals():
                    handler.cleanup_progress()
                error_msg = str(e)
                # Early-exit for genuinely empty/deleted channels (no point retrying)
                from yt_fts.utils.retry_classifier import should_skip_retry

                if should_skip_retry(error_msg):
                    return {
                        "success": False,
                        "error": str(e),
                        "skipped_retry": True,
                    }
                if attempt < self.max_retries:
                    from yt_fts.utils.retry_classifier import (
                        get_backoff_time,
                        is_rate_limit_error,
                    )

                    is_rate_limit = is_rate_limit_error(error_msg)
                    wait_time = get_backoff_time(error_msg, attempt)
                    if is_rate_limit:
                        self.display_plugin.warning(
                            f"  Rate limited - waiting {wait_time}s before retry"
                        )
                    time.sleep(wait_time)
                else:
                    return {
                        "success": False,
                        "error": f"Failed after {self.max_retries + 1} attempts: {e!s}",
                    }
        return {"success": False, "error": "Max retries exceeded"}

    def _print_summary(self, results: dict[str, Any]) -> None:
        """Print a comprehensive summary of the download results."""
        print_summary(self.console, results, self.channels, self.continue_on_error)

    def validate_channels(self) -> list[str]:
        """
        Validate channel formats and return valid channels.

        Returns:
            List[str]: List of valid channel URLs/handles
        """
        return validate_channels(self.channels, self.console)

    def export_report(self, filename: str) -> None:
        """Export download results to a JSON file."""
        if self.results:
            export_report(self.results, filename, self.console)

    def save_progress(self) -> None:
        """Save current download progress (placeholder implementation)."""

    def display_summary(self) -> None:
        """Display a summary of the download results."""
        if self.results:
            self._print_summary(self.results)

    def get_progress(self) -> str:
        """Get current progress as a string."""
        return "Progress tracking not implemented"

    def process_single_channel(
        self, channel: str, coordinator=None, log_callback=None
    ) -> dict[str, Any]:
        """
        Process a single channel using shared resources (flattened architecture).

        This method enables the flattened parallel architecture where a single
        BatchDownloader instance is shared across all worker threads, reducing
        overhead (no per-worker RSS checker, quota strategy, DB connections).

        Args:
            channel: YouTube channel URL or handle to process
            coordinator: Optional ThreadSafeProgressCoordinator for progress updates
            log_callback: Optional callback function for logging

        Returns:
            dict: Result with keys: successful, failed, skipped
        """
        from yt_fts.core.database import (
            enable_wal_mode,
            get_channel_stats,
            get_db_connection,
            get_vid_ids_by_channel_id,
            is_channel_skipped,
        )
        from yt_fts.services.rss_precheck import create_rss_checker

        from .channel_cache import get_cached_channels, save_resolved_channels
        from .fast_channel_resolver import create_fast_resolver

        results = {"successful": [], "failed": [], "skipped": []}
        enable_wal_mode()
        conn = get_db_connection(timeout=10.0)
        try:
            cached_channels, channels_to_resolve = get_cached_channels([channel], conn)
        finally:
            conn.close()
        resolved_channels = cached_channels.copy()
        if channels_to_resolve:
            fast_resolver = create_fast_resolver(
                cookies_from_browser=self.cookies_from_browser, console=self.console
            )
            newly_resolved = fast_resolver.batch_resolve(
                channels_to_resolve, max_workers=1
            )
            resolved_channels.update(newly_resolved)
            if newly_resolved:
                save_resolved_channels(newly_resolved, console=self.console)
        if not resolved_channels:
            results["failed"].append(
                {"channel": channel, "error": "Failed to resolve channel"}
            )
            return results
        resolved_url = next(iter(resolved_channels.values()))
        # DEBUG: Trace resolved_url to find truncation point
        log_operation(
            "process_single_channel",
            f"[DEBUG] resolved_url from cache: {resolved_url}",
            level=10,
        )
        # Check if channel is in the permanently skipped list
        is_skipped, skip_reason = is_channel_skipped(resolved_url)
        if is_skipped:
            msg = f"Skipping {original_channel}: {skip_reason}"
            if log_callback:
                log_callback(f"[dim]⏭️  {msg}[/dim]")
            results["skipped"].append(
                {"channel": original_channel, "reason": skip_reason}
            )
            return results
        original_channel = channel
        channel_id = None
        if "/channel/" in resolved_url:
            channel_id = resolved_url.split("/channel/")[1].split("/")[0]
        db_count = 0
        db_video_ids = set()
        if channel_id:
            try:
                local_vid_ids = [v[0] for v in get_vid_ids_by_channel_id(channel_id)]
                db_video_ids = set(local_vid_ids)
                stats = get_channel_stats(channel_id)
                db_count = stats["total"]
                stats["with_transcripts"]
                stats["scheduled"]
                stats["members_only"]
                stats["without_transcripts"]
            except Exception:
                db_video_ids = set()
                db_count = 0
        rss_checker = create_rss_checker(timeout=10.0)
        rss_video_ids_for_download = None
        if db_count == 0:
            rss_status = "new_videos"
        elif channel_id:
            handle = (
                resolved_url.split("@")[-1].split("/")[0]
                if "@" in resolved_url
                else None
            )
            # DEBUG: Trace handle extraction for RSS check
            log_operation(
                "process_single_channel",
                f"[DEBUG] RSS handle: @{handle} from resolved_url: {resolved_url}",
                level=10,
            )
            rss_result = rss_checker.check(
                channel_id=channel_id,
                handle=handle,
                resolved_url=resolved_url,
                db_video_ids=db_video_ids,
            )
            rss_status = rss_result.status if rss_result else "error"
            if rss_result and rss_result.video_ids:
                rss_video_ids_for_download = rss_result.video_ids
        else:
            rss_status = "error"
        if rss_status == "skip" and (not rss_video_ids_for_download):
            results["skipped"].append(
                {"channel": original_channel, "message": "No new videos"}
            )
            return results
        if coordinator is None and (not self.suppress_verbose):
            from rich.progress import BarColumn, Progress, TextColumn

            from .progress_coordinator import ThreadSafeProgressCoordinator

            progress_ctx = Progress(
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(bar_width=20),
                TextColumn(
                    "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage]"
                ),
                console=self.console,
                auto_refresh=False,
            )
            progress = progress_ctx.__enter__()
            coordinator = ThreadSafeProgressCoordinator(progress)
            coordinator.start()
        elif coordinator is None:
            from .progress_coordinator import ThreadSafeProgressCoordinator

            coordinator = ThreadSafeProgressCoordinator(None)
            coordinator.start()
        try:
            download_result = self._download_single_channel_optimized(
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id or "",
                coordinator=coordinator,
                log_callback=log_callback,
                rich_mode=False,
                video_ids=rss_video_ids_for_download,
            )
            if download_result.get("success"):
                results["successful"].append(
                    {
                        "channel": original_channel,
                        "videos": download_result.get("videos_count", 0),
                    }
                )
            else:
                error = download_result.get("error", "Unknown error")
                results["failed"].append({"channel": original_channel, "error": error})
        except Exception as e:
            results["failed"].append({"channel": original_channel, "error": str(e)})
        return results
