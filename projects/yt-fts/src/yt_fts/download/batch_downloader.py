"""Batch downloader for multiple YouTube channels with duplicate-free progress bars.
"""
from __future__ import annotations

# Standard library imports
import logging
import os
import re
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

# Third-party imports
from rich.progress import BarColumn, Progress, TaskID, TextColumn
from rich.table import Column

# Local imports
from yt_fts.config import (
    BATCH_PROGRESS_CONFIG,
    SINGLE_CHANNEL_PROGRESS_CONFIG,
)
from yt_fts.core.database import BatchCommitManager, get_batch_manager
from yt_fts.db.channels import (
    get_channel_stats,
    get_channel_stats_with_subs_and_playlists,
)
from yt_fts.download.progress_tracker import YTDLP_PROGRESS_DESC
from yt_fts.utils.config import get_db_path
from yt_fts.utils.dual_sink_logger import (
    get_logger,
    log_operation,
    log_technical_error,
    log_user_message,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("download.log", mode="a")],
)

# Initialize logger
logger = get_logger(__name__)

# Relative imports
@dataclass(slots=True)
class BatchDownloaderConfig:
    """Configuration for BatchDownloader.

    Reduces constructor from 24 parameters to a single config object.
    """
    # Core
    channels: list[str]
    jobs: int = 2
    language: str = "en"

    # Retry & Error Handling
    cookies_from_browser: str | None = None
    delay_between_channels: float = 3.0
    max_retries: int = 3
    continue_on_error: bool = True

    # Time Limits
    time_per_channel: float | None = None
    time_per_video: float | None = None
    time_per_batch: float | None = None

    # Video Limits
    max_videos: int | None = None
    min_saved: int | None = None
    target_downloads: int | None = None
    videos_download_per_batch: int | None = None

    # Features
    auto_backfill: bool = False
    dry_run: bool = False
    freshness_hours: int = 6
    resume: bool = False

    # Quota & Transcription
    quota_strategy: Any = None
    whisper_model: str = "base"
    keep_audio: bool = False

    # UI & Display
    rich_formatter: Any = None
    rich_mode: str | None = None
    display_plugin: str | None = None
    suppress_quota_print: bool = False
    suppress_verbose: bool = False

    # File tracking
    file_stats: dict[str, int] | None = None

from .batch_channel_helpers import (
    determine_rss_status,
    format_rss_status_message,
    recheck_unavailable_videos,
)
from .batch_checkpoint import reset_checkpoint
from .batch_downloader_constants import (
    BATCH_COMMIT_INTERVAL,
    DB_CONNECTION_SHORT_TIMEOUT,
    DB_CONNECTION_TIMEOUT,
    DEFAULT_QUOTA_PERCENTAGE,
    DISPLAY_COLUMN_WIDTH,
    INVALID_CHANNEL_MARKER,
    SECONDS_PER_HOUR,
    SUBSCRIBER_COUNT_MILLION,
    SUBSCRIBER_COUNT_TEN_THOUSAND,
)
from .channel_cache import (
    get_cached_channels,
    report_cache_status,
    save_resolved_channels,
)
from .channel_diagnostics import display_channel_diagnostics
from .channel_prefetch_queue import ChannelPrefetchQueue
from .channel_resolution_service import ChannelResolutionService
from .channel_validator import ChannelValidator
from .download_handler import DownloadHandler
from .error_recovery import ErrorRecoveryManager
from .exceptions import (
    BaseURLFallbackFailed,
    ChannelEmptyError,
    DownloadTimeoutException,
)
from .metadata_backfill import MetadataBackfill
from .output_utils import StderrCapture
from .progress_coordinator import ThreadSafeProgressCoordinator
from .quota_display import QuotaDisplay
from .rich_layout import RichLayoutDownloader
from .summary import export_report, print_summary, validate_channels
from .unified_discovery import UnifiedChannelDiscovery

# Pre-compiled regex for stripping Rich markup tags
# Pattern matches [tag] and [/tag] like [red], [/red], [bold], [/bold], etc.
RICH_TAG_PATTERN = re.compile(r"\[/?[^\]]+\]")


def _strip_rich_tags(text: str) -> str:
    """Strip Rich markup tags from a string.

    Removes tags like [red], [/red], [green], [/green], etc.

    Args:
        text: String that may contain Rich markup tags

    Returns:
        String with Rich tags removed
    """
    return RICH_TAG_PATTERN.sub("", text)


class BatchDownloader:
    """
    Efficient batch downloader for multiple YouTube channels with duplicate-free progress bars.

    Features:
    - Smart rate limiting between channels
    - Cookie support for reduced rate limiting
    """

    def __init__(
        self,
        config: BatchDownloaderConfig | list[str] | None = None,
        rich_formatter: Any = None,
        **kwargs
    ) -> None:
        """
        Initialize the BatchDownloader.

        Args:
            config: BatchDownloaderConfig object, or list of channel URLs (backward compat)
            rich_formatter: Optional RichYouTubeFormatter for enhanced UI
            **kwargs: Backward compatibility - individual config options (channels, jobs, etc.)

        Backward compatibility: If config is a list[str], treats it as channels.
                          If kwargs provided, creates BatchDownloaderConfig from them.
        """
        # Backward compatibility: handle old-style individual keyword arguments
        if kwargs:
            # Old-style call: BatchDownloader(channels=["..."], jobs=2, ...)
            # Merge with config if provided
            if config is None and "channels" not in kwargs:
                raise ValueError("channels must be provided")
            if isinstance(config, list):
                kwargs["channels"] = config
            elif isinstance(config, BatchDownloaderConfig):
                # Config object takes precedence over kwargs
                pass
            else:
                # Filter out new-style config objects that BatchDownloaderConfig doesn't accept
                # These are handled separately by the caller
                config_kwargs = {
                    k: v for k, v in kwargs.items()
                    if k not in ("execution_config", "limits_config", "content_config",
                                "ui_config", "transcript_config", "rich_formatter", "file_stats",
                                "reset_checkpoint", "prefetch_channel_names")
                }
                # Create config from filtered kwargs
                config = BatchDownloaderConfig(**config_kwargs)

                # Handle file_stats, resume, prefetch_channel_names, and reset_checkpoint from kwargs if present
                # (These may have been filtered out above but need to be set on the instance)
                if "file_stats" in kwargs:
                    config.file_stats = kwargs["file_stats"]
                if "resume" in kwargs:
                    config.resume = kwargs["resume"]
                # Store prefetch_channel_names flag for use in batch_download
                self._prefetch_channel_names = kwargs.get("prefetch_channel_names", False)
                # Store reset_checkpoint flag for use in __init__
                self._reset_checkpoint_flag = kwargs.get("reset_checkpoint", False)

                # Extract and store UI configuration from ui_config parameter
                if "ui_config" in kwargs:
                    ui_config = kwargs["ui_config"]
                    self._rich_mode_from_ui_config = ui_config.rich_mode
                    self._display_plugin_from_ui_config = ui_config.display_plugin
                    self._suppress_verbose_from_ui_config = ui_config.suppress_verbose

        elif isinstance(config, list):
            config = BatchDownloaderConfig(channels=config)
        elif config is None:
            raise ValueError("config must be BatchDownloaderConfig, list[str], or kwargs provided")

        # Extract all values from config
        self.channels = config.channels
        self.jobs = config.jobs
        self.language = config.language
        self.cookies_from_browser = config.cookies_from_browser
        self.delay_between_channels = config.delay_between_channels
        self.max_retries = config.max_retries
        self.continue_on_error = config.continue_on_error
        self.min_saved = config.min_saved
        self.rich_formatter = rich_formatter or config.rich_formatter
        # Use rich_mode from ui_config if available, otherwise from config
        self.rich_mode = getattr(self, "_rich_mode_from_ui_config", config.rich_mode)
        self.time_per_channel = config.time_per_channel
        self.time_per_video = config.time_per_video
        self.time_per_batch = config.time_per_batch
        self.batch_start_time: float = 0.0
        self.max_videos = config.max_videos
        self.target_downloads = config.target_downloads
        self.videos_download_per_batch = config.videos_download_per_batch
        self.auto_backfill = config.auto_backfill
        self.dry_run = config.dry_run
        self.freshness_hours = config.freshness_hours
        self._checkpoint_file = str(Path(get_db_path()).parent / "batch_checkpoint.json")
        # Handle reset_checkpoint flag: delete checkpoint file if flag is True
        if hasattr(self, "_reset_checkpoint_flag") and self._reset_checkpoint_flag:
            reset_checkpoint(self._checkpoint_file)
        self.quota_strategy = config.quota_strategy
        self.suppress_quota_print = config.suppress_quota_print
        self.suppress_verbose = config.suppress_verbose
        self.whisper_model = config.whisper_model
        self.keep_audio = config.keep_audio
        self.file_stats = config.file_stats or {}
        self.resume = config.resume

        # Initialize video-level checkpoint if resume is enabled
        self.download_checkpoint = None
        if self.resume:
            from yt_fts.download.download_checkpoint import DownloadCheckpoint
            self.download_checkpoint = DownloadCheckpoint(console=self.console, auto_save=True)

        # Initialize thread-local storage for database connections
        import threading
        self._thread_local = threading.local()
        self._all_conns = []
        self._conns_lock = threading.Lock()
        # Lock for protecting shared state in process_single_channel (metadata_backfill, quota_strategy)
        self._lock = threading.RLock()
        from yt_fts.utils.rich_console import get_console, get_stderr_console

        force_terminal = bool(os.getenv("WT_SESSION"))
        self.console = get_console(force_terminal=force_terminal)
        self.progress_console = get_stderr_console(force_terminal=force_terminal)
        self.batch_manager: BatchCommitManager | None = None
        if self.min_saved == 0:
            self.batch_manager = get_batch_manager(commit_interval=BATCH_COMMIT_INTERVAL)

        # Determine display plugin
        display_plugin = config.display_plugin if hasattr(config, "display_plugin") else None
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
            options={"verbose": not self.suppress_verbose},
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
            cookies_from_browser=self.cookies_from_browser
        )
        self.channel_resolution_service = ChannelResolutionService(
            cookies_from_browser=self.cookies_from_browser
        )
        self.executor = None
        # Initialize error recovery manager for intelligent retry strategies
        self.error_recovery = ErrorRecoveryManager(
            max_retries=self.max_retries,
            continue_on_error=self.continue_on_error,
        )
        # Initialize quota display handler
        self.quota_display = QuotaDisplay(console=self.console)
        # Initialize channel validator
        self.channel_validator = ChannelValidator()
        # Initialize metadata backfill handler
        self.metadata_backfill = MetadataBackfill(
            console=self.console,
            display_plugin=self.display_plugin,
            suppress_verbose=self.suppress_verbose,
            quota_strategy=self.quota_strategy,
        )
        self.results = None

    def _print_quota_status(self, header: str) -> None:
        """Print quota status using QuotaDisplay handler.

        Args:
            header: Header text to display (e.g., "yt-api quota")
        """
        self.quota_display.print_quota_status(header)

    def _print_db_stats_legend(self) -> None:
        """Print the database statistics legend.

        Explains what each field in the 'db:' line means, including
        total, dt, mt, vt, nt, shorts, unavailable, etc.
        """
        self.console.print("")
        self.console.print("[dim]Database Statistics Legend:[/dim]")
        self.console.print(
            "[dim]  Example: db: 230 total, 244 mt, 122 dt | +180 vt, +123 nt | -1 shorts | 50.4K subs[/dim]"
        )
        self.console.print("")
        self.console.print("[dim]  Field     Description[/dim]")
        self.console.print("[dim]  ─────     ──────────────────────────────────────────────────────────[/dim]")
        self.console.print("[dim]  total     All videos in database[/dim]")
        self.console.print("[dim]  dt        Downloaded transcripts (stored locally)[/dim]")
        self.console.print("[dim]  mt        Max possible transcripts (total - shorts - unavailable - scheduled - audio)[/dim]")
        self.console.print("[dim]  vt        Video transcripts available on YouTube (closed captions)[/dim]")
        self.console.print("[dim]  nt        No downloaded transcripts[/dim]")
        self.console.print("[dim]  shorts    YouTube Shorts (cannot have transcripts)[/dim]")
        self.console.print("[dim]  unavail   Unavailable (deleted, private, geo-blocked, age-restricted)[/dim]")
        self.console.print("[dim]  scheduled Upcoming/live streams not yet published[/dim]")
        self.console.print("[dim]  members   Members-only (requires authentication)[/dim]")
        self.console.print("[dim]  pl        Playlist count on the channel[/dim]")
        self.console.print("[dim]  subs      Subscriber count (K = thousands, M = millions)[/dim]")
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

    @staticmethod
    def _normalize_resolved_to_tuples(resolved_urls: dict[str, str]) -> dict[str, tuple[str, str]]:
        """Normalize resolved URLs to (channel_id, resolved_url) tuples.

        Extracts channel_id from resolved_url using same logic as save_resolved_channels.

        Args:
            resolved_urls: {input: resolved_url} mapping from fast_resolver

        Returns:
            {input: (channel_id, resolved_url)} mapping matching cached_channels format
        """
        normalized = {}
        for original_input, resolved_url in resolved_urls.items():
            channel_id = None

            if "/channel/" in resolved_url:
                # Extract channel ID from /channel/ URLs
                channel_id = resolved_url.split("/channel/")[1].split("/")[0]
            elif "/@" in resolved_url:
                # Extract handle from /@/ URLs
                handle = resolved_url.split("/@")[1].split("/")[0]
                channel_id = f"@{handle}"
            else:
                # For custom URLs or other formats, use the URL itself as identifier
                clean_url = resolved_url.replace("https://", "").replace("http://", "").rstrip("/")
                channel_id = f"url:{clean_url}"

            if channel_id:
                normalized[original_input] = (channel_id, resolved_url)

        return normalized

    def _extract_channel_downloads(
        self, resolved_channels: dict[str, tuple[str, str]]
    ) -> list[tuple[str, str, str | None]]:
        """Extract channel IDs and deduplicate based on resolved ID/URL.

        Uses cached (channel_id, resolved_url) tuples to construct canonical
        /channel/{UC_ID} URLs for more reliable downloads. This auto-heals
        stale/wrong handle URLs in the database.
        """
        channel_downloads = []
        seen_ids = set()

        for original_channel, (cached_channel_id, resolved_url) in resolved_channels.items():
            channel_id = None
            download_url = resolved_url

            # Use canonical /channel/{UC_ID} URL if we have the UC ID
            # This auto-heals stale/wrong handle URLs in the database
            if cached_channel_id and cached_channel_id.startswith("UC"):
                canonical_url = f"https://www.youtube.com/channel/{cached_channel_id}"
                download_url = canonical_url
                channel_id = cached_channel_id
            elif "/channel/" in resolved_url:
                channel_id = resolved_url.split("/channel/")[1].split("/")[0]
            elif "@" in resolved_url:
                # For handle URLs, the cached_channel_id may be a handle or UC ID
                if cached_channel_id and cached_channel_id.startswith("UC"):
                    channel_id = cached_channel_id

            # Deduplication key: Use channel_id if available (most reliable),
            # otherwise fall back to download_url
            dedupe_key = channel_id if channel_id else download_url

            if dedupe_key in seen_ids:
                continue

            seen_ids.add(dedupe_key)
            channel_downloads.append((original_channel, download_url, channel_id))

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
        db_subscriber_count: int | None = None,
        db_playlist_count: int | None = None,
        db_cc_available: int = 0,
        db_no_subtitles_available: int = 0,
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
        import logging

        logger = logging.getLogger(__name__)

        # Calculate transcript coverage metrics
        # vt = videos with transcripts (what we have)
        # mt = max transcripts (videos that could potentially have transcripts)
        # nt = no transcripts (videos without transcripts)
        vt = db_with_subs  # videos with transcripts
        mt = (
            db_count
            - db_shorts
            - db_unavailable
            - db_scheduled
            - db_no_subtitles_available
        )
        nt = db_no_subs  # no transcripts

        # Build format: "{total} total, {mt} mt, {dt} dt | +{vt} vt, +{nt} nt | -{shorts} shorts | {extras}"
        # Section 1: Basic counts
        section1_parts = []
        section1_parts.append(f"{db_count} total")
        section1_parts.append(f"{mt} mt")
        section1_parts.append(f"{vt} dt")  # dt = transcripts (downloaded)

        section1 = ", ".join(section1_parts)

        # Section 2: Transcript availability with + prefix
        section2_parts = []
        section2_parts.append(f"+{vt} vt")
        section2_parts.append(f"+{nt} nt")

        section2 = ", ".join(section2_parts)

        # Section 3: Shorts with - prefix (exclusion indicator)
        section3 = f"-{db_shorts} shorts"

        # Section 4: Extras (subscriber count, playlist count)
        extras = []
        # Playlist count (channel scope)
        if db_playlist_count is not None and db_playlist_count > 0:
            extras.append(f"{db_playlist_count} pl")
        # Subscriber count (channel size)
        if db_subscriber_count is not None and db_subscriber_count > 0:
            if db_subscriber_count >= SUBSCRIBER_COUNT_MILLION:
                sub_str = f"{db_subscriber_count / SUBSCRIBER_COUNT_MILLION:.1f}M subs"
            elif db_subscriber_count >= SUBSCRIBER_COUNT_TEN_THOUSAND:
                sub_str = f"{db_subscriber_count / 1000:.1f}K subs"
            else:
                sub_str = f"{db_subscriber_count} subs"
            extras.append(sub_str)

        # Combine all sections with | separator
        result_parts = [section1, section2, section3]
        if extras:
            result_parts.append(" | ".join(extras))

        db_stats = " | ".join(result_parts)

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

        # Strip Rich markup tags from stats string for tests
        stats_clean = _strip_rich_tags(db_stats)

        return {
            "stats": stats_clean,
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
        if existing_name and not self.channel_validator.is_raw_channel_id(existing_name):
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

    def _fetch_channel_metadata_yt_dlp(
        self, url_or_id: str
    ) -> tuple[str | None, str | None]:
        """Fetch channel name and URL from yt-dlp."""
        import shutil
        import subprocess

        if not shutil.which("yt-dlp"):
            return None, None

        # Validate input to prevent command injection
        if not self.channel_validator.validate_channel_input(url_or_id):
            logger.debug("_fetch_channel_metadata_yt_dlp: Invalid input rejected: %s", url_or_id[:50])
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
                "--extractor-args",
                "youtubetab:skip=webpage",
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
        except (subprocess.TimeoutExpired, subprocess.CalledProcessError, FileNotFoundError, OSError) as e:
            logger.debug("_fetch_channel_metadata_yt_dlp: subprocess error: %s", e)
        return None, None

    def _fetch_channel_metadata_rss(
        self, url_or_id: str
    ) -> tuple[str | None, str | None]:
        """Fetch channel name and URL from RSS feed (fast, ~100ms).

        RSS is significantly faster than yt-dlp (1-3s) and doesn't consume
        YouTube API quota. Falls back to None if RSS fetch fails.
        
        Args:
            url_or_id: Channel URL or channel ID (UCxxx format)
            
        Returns:
            Tuple of (channel_name: str | None, channel_url: str | None)
        """
        from yt_fts.services.rss_precheck import RssPreChecker

        # Validate input to prevent command injection
        if not self.channel_validator.validate_channel_input(url_or_id):
            logger.debug("_fetch_channel_metadata_rss: Invalid input rejected: %s", url_or_id[:50])
            return None, None

        # Construct URL if ID provided
        if url_or_id.startswith("UC") and len(url_or_id) > 20:
            url = f"https://www.youtube.com/channel/{url_or_id}"
        elif url_or_id.startswith("@"):
            url = f"https://www.youtube.com/{url_or_id}"
        else:
            url = url_or_id

        try:
            # Use RSS prechecker to fetch channel name
            rss_checker = RssPreChecker(timeout=DB_CONNECTION_SHORT_TIMEOUT)

            # Build RSS URL
            channel_id = url_or_id if url_or_id.startswith("UC") else None
            rss_url = rss_checker._build_rss_url(channel_id, None, url)

            if not rss_url:
                return None, None

            # Fetch RSS feed
            import requests
            response = requests.get(
                rss_url,
                headers={"User-Agent": rss_checker.user_agent},
                timeout=rss_checker.timeout
            )

            if response.status_code != 200:
                return None, None

            # Extract channel name from RSS feed
            channel_name = rss_checker._extract_channel_name_from_feed(response.text)

            if channel_name:
                return channel_name, url

        except (requests.RequestException, OSError) as e:
            logger.debug("_fetch_channel_metadata_rss: fetch error: %s", e)

        return None, None

    def _prefetch_channel_names_parallel(
        self, channel_downloads: list[tuple[str, str, str | None]]
    ) -> None:
        """Pre-fetch missing channel names in parallel to reduce startup latency.

        OPTIMIZED: Uses ChannelPrefetchQueue with background thread + RSS (fast, ~100ms per channel)
        instead of blocking parallel fetches.

        NON-BLOCKING: Returns immediately after starting background prefetch thread.
        Channel names are fetched asynchronously and available for subsequent display.
        """
        # Extract channel IDs
        channel_ids = [cid for _, _, cid in channel_downloads if cid]
        if not channel_ids:
            return

        # Create fetcher function that wraps _fetch_channel_metadata_rss
        def fetcher(channel_id: str) -> tuple[str | None, str | None]:
            """Fetch metadata for a single channel."""
            # Find the URL for this channel_id
            url = None
            for _, resolved_url, cid in channel_downloads:
                if cid == channel_id:
                    url = (
                        f"https://www.youtube.com/channel/{channel_id}"
                        if channel_id.startswith("UC")
                        else resolved_url
                    )
                    break

            if not url:
                return None, None

            return self._fetch_channel_metadata_rss(url)

        # Create and start prefetch queue (non-blocking)
        queue = ChannelPrefetchQueue(
            channel_ids=channel_ids,
            fetcher=fetcher,
            console=self.console,
            suppress_verbose=self.suppress_verbose,
            max_workers=8,
        )
        queue.start()

        # Note: We don't wait for completion here.
        # The queue runs in background and fetches channel names asynchronously.
        # Subsequent calls to _get_channel_display_name will use the fetched names
        # as they become available in the database.

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
                if self.channel_validator.is_raw_channel_id(name):
                    logger.debug(
                        "_get_channel_display_name: db name looks like raw ID, falling through"
                    )
                    # Treat as not cached, fall through to progressive display
                else:
                    logger.debug(
                        f"_get_channel_display_name: returning db name: {name!r}"
                    )
                    return name  # Real cached name, no warning needed
        except (sqlite3.OperationalError, sqlite3.DatabaseError, ValueError, TypeError) as e:
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

        logging.getLogger("yt_dlp").setLevel(logging.ERROR)
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
            # Print db statistics legend before quota status
            self._print_db_stats_legend()
            self._print_quota_status("yt-api quota")
        return results, total_videos_saved

    def _resolve_and_validate_channels(
        self,
        file_stats: dict[str, int] | None = None,
    ) -> tuple[list[tuple[str, str, str]] | None, list[str]]:
        """
        Resolve channel URLs to channel IDs and validate them.

        Args:
            file_stats: Optional dict with keys 'raw', 'filtered', 'duplicates_removed', 'invalid_removed'

        Returns:
            tuple: (channel_downloads list or None if rich mode, invalid_channels list)
        """
        # Show progress before blocking DB operations
        if not self.suppress_verbose:
            self.console.print("[dim]Initializing database cache...[/dim]", end="")

        from yt_fts.core.database import enable_wal_mode, get_db_connection
        from yt_fts.db.infra import ensure_db_indexes

        enable_wal_mode()
        ensure_db_indexes()  # Create indexes for optimized queries
        conn = get_db_connection(timeout=DB_CONNECTION_TIMEOUT)
        try:
            cached_channels, channels_to_resolve = get_cached_channels(
                self.channels, conn
            )
        finally:
            conn.close()
        # Skip individual cache status - will show in consolidated block
        report_cache_status(
            self.console,
            cached_count=len(cached_channels),
            resolve_count=len(channels_to_resolve),
        )

        # Clear the "Initializing..." line
        if not self.suppress_verbose:
            self.console.print()
        newly_resolved = {}
        # Skip upfront channel resolution - validate per-channel during download via RSS
        # RSS precheck in download_handler is faster (~100ms vs 1-3s for yt-dlp)
        newly_resolved = {}
        resolved_channels = {**cached_channels}
        validated_channels = {**cached_channels}
        invalid_channels: list[str] = []
        successful_resolutions = len(resolved_channels)
        failed_resolutions = len(invalid_channels)
        if failed_resolutions > 0:
            self.console.print(
                f"[dim]  → {successful_resolutions} valid, {failed_resolutions} not found[/dim]"
            )
        if newly_resolved:
            save_resolved_channels(newly_resolved, console=self.console)
        channel_downloads = self._extract_channel_downloads(resolved_channels)

        # Display consolidated channel diagnostics
        total_resolved = len(resolved_channels)
        unique_count = len(channel_downloads)

        # Extract file stats if provided
        raw = file_stats.get("raw") if file_stats else 0
        filtered = file_stats.get("filtered") if file_stats else 0
        dupes = file_stats.get("duplicates_removed") if file_stats else 0
        invalid = file_stats.get("invalid_removed") if file_stats else 0

        if not self.suppress_verbose:
            display_channel_diagnostics(
                console=self.console,
                raw_lines=raw,
                filtered_valid=filtered,
                duplicates_removed=dupes,
                invalid_removed=invalid,
                cached_count=len(cached_channels),
                new_count=len(channels_to_resolve),
                unique_count=unique_count,
            )
        if self.rich_mode == "new":
            # Suppress API quota progress prints to prevent Rich Layout flickering
            # Rich Layout captures stdout anyway, so manual progress updates conflict
            suppress_quota_print_original = self.suppress_quota_print
            self.suppress_quota_print = True
            try:
                rich_layout_downloader = RichLayoutDownloader(
                    console=self.console,
                    batch_downloader=self,
                    cookies_from_browser=self.cookies_from_browser,
                    max_videos=self.max_videos,
                )
                rich_layout_downloader.download_with_layout(
                    channel_downloads, invalid_channels
                )
            finally:
                self.suppress_quota_print = suppress_quota_print_original
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
            Channel ID if found, INVALID_CHANNEL_MARKER if 404, or None
        """
        try:
            from yt_fts.db.channels import (
                get_channel_id_by_handle_substring,  # Checks exact ID, URL, Name
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

                    from .output_utils import YtdlpSilentLogger

                    ydl_opts = {
                        "quiet": True,
                        "no_warnings": True,
                        "noprogress": True,
                        "extract_flat": True,
                        "extractor_args": {"youtubetab": ["skip=authcheck", "skip=webpage"]},
                        "logger": YtdlpSilentLogger(),
                    }
                    with StderrCapture():
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
                        return INVALID_CHANNEL_MARKER
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
            db_state.get("db_cc_available", 0),
            db_state.get("db_no_subtitles_available", 0),
            status_name,
            channel_id,
            channel_display_name,
            db_state.get("db_subscriber_count"),
            db_state.get("db_playlist_count"),
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
                / SECONDS_PER_HOUR
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
        stats = get_channel_stats_with_subs_and_playlists(channel_id)
        db_state["db_count"] = stats["total"]
        db_state["db_with_subs"] = stats["with_transcripts"]
        db_state["db_scheduled"] = stats["scheduled"]
        db_state["db_members"] = stats["members_only"]
        db_state["db_unavailable"] = stats["unavailable"]
        db_state["db_unavail_deleted"] = stats.get("unavail_deleted", 0)
        db_state["db_unavail_private"] = stats.get("unavail_private", 0)
        db_state["db_unavail_geo"] = stats.get("unavail_geo", 0)
        db_state["db_unavail_resolvable"] = stats.get("unavail_resolvable", 0)
        db_state["db_shorts"] = stats["shorts"]
        db_state["db_no_subs"] = stats["without_transcripts"]
        db_state["db_subscriber_count"] = stats.get("subscriber_count")
        db_state["db_playlist_count"] = stats.get("playlist_count")

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
                # Progress shown in Rich bar, no verbose status needed
                return True
        return False

    def _get_thread_db_connection(self, get_db_connection: callable) -> Any:
        """
        Get or create a database connection for the current thread.

        Uses thread-local storage to ensure each thread has its own connection.
        All connections are tracked for cleanup.

        Thread-safe: Uses double-checked locking pattern to avoid race
        condition during connection creation.

        Args:
            get_db_connection: Function to create a new DB connection

        Returns:
            Database connection for the current thread
        """
        # Check if current thread already has a connection
        # Note: hasattr() on threading.local() checks the current thread's namespace
        if hasattr(self._thread_local, "conn"):
            return self._thread_local.conn

        # Current thread doesn't have a connection - create one
        # Use lock to prevent multiple threads from creating connections simultaneously
        with self._conns_lock:
            # Double-check: another thread might have created while we waited for lock
            if hasattr(self._thread_local, "conn"):
                return self._thread_local.conn

            # Create new connection for this thread
            conn = get_db_connection(timeout=30.0)
            self._thread_local.conn = conn
            self._all_conns.append(conn)
            return conn

    def _initialize_thread_local_storage(self) -> None:
        """Initialize thread-local storage for database connections.
        
        DEPRECATED: Initialization now happens in __init__ to avoid race conditions.
        This method is kept for compatibility but should not be called.
        """
        import threading
        if not hasattr(self, "_thread_local"):
            self._thread_local = threading.local()
        if not hasattr(self, "_conns_lock"):
            self._conns_lock = threading.Lock()
        if not hasattr(self, "_all_conns"):
            self._all_conns = []

    def _backfill_new_channel_metadata(
        self,
        channel_id: str,
        channel_display_name: str,
        db_state: dict[str, Any],
        coordinator: object | None = None,
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

        # Resolve handle to UC channel_id before API calls
        # YouTube API requires UC format, not @handle format
        if channel_id and not channel_id.startswith("UC"):
            from yt_fts.db.channels import get_channel_id_by_handle_substring
            handle = None
            if channel_id.startswith("@"):
                handle = channel_id[1:]
            if handle:
                resolved_id = get_channel_id_by_handle_substring(handle)
                if resolved_id and resolved_id.startswith("UC"):
                    channel_id = resolved_id
                    logger.debug("Resolved handle to UC channel_id: %s", channel_id)
                else:
                    # Handle not found in database (new channel)
                    # Use yt-dlp to resolve the handle to UC channel_id
                    logger.debug("Handle %s not found in DB, resolving via yt-dlp", handle)
                    import yt_dlp

                    from .output_utils import YtdlpSilentLogger
                    handle_url = f"https://www.youtube.com/@{handle}"
                    try:
                        ydl_opts = {
                            "quiet": True,
                            "no_warnings": True,
                            "noprogress": True,
                            "extract_flat": True,
                            "extractor_args": {"youtubetab": ["skip=authcheck", "skip=webpage"]},
                            "logger": YtdlpSilentLogger(),
                            "cookiefile": self.cookie_file if hasattr(self, "cookie_file") else None,
                            "socket_timeout": 10,  # Prevent indefinite hangs on network issues
                        }
                        # Filter out None cookiefile
                        ydl_opts = {k: v for k, v in ydl_opts.items() if v is not None}

                        with StderrCapture():
                            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                                info = ydl.extract_info(handle_url, download=False)
                        resolved_channel_id = info.get("channel_id") or info.get("uploader_id")
                        if resolved_channel_id and resolved_channel_id.startswith("UC"):
                            channel_id = resolved_channel_id
                            logger.debug("Resolved handle to UC channel_id via yt-dlp: %s", channel_id)
                            # Store in database for future lookups
                            from yt_fts.core.database import add_channel_info
                            add_channel_info(
                                channel_id,
                                info.get("channel_name") or info.get("uploader") or handle,
                                handle_url
                            )
                        else:
                            logger.warning("Failed to resolve handle %s to UC channel_id", handle)
                            # Skip API backfill for unresolvable handles
                            return api_total_mismatch, False, "unresolvable_handle"
                    except Exception as e:
                        logger.debug("Failed to resolve handle %s via yt-dlp: %s", handle, e)
                        # Fall back to yt-dlp for download instead of API
                        return api_total_mismatch, False, "resolution_failed"

        try:
            # Thread-safe coordinator pattern for channel API discovery
            if coordinator is not None and not self.suppress_quota_print:
                # Use parent coordinator to create a task for this channel
                # NOTE: Must use add_task_sync to ensure task exists before YouTubeAPIBackfill starts
                task = coordinator.add_task_sync(
                    "   ⎿ yt-api:",
                    channel_name=channel_display_name,
                    total=100,
                    visible=True,
                    fields={"stats": ""}
                )
                if task is None:
                    # Fall back to no progress if task creation failed
                    task = None
                backfill = YouTubeAPIBackfill(
                    console=self.console,
                    show_progress=(coordinator, task, channel_display_name) if not self.suppress_quota_print else False,
                )
                videos_data = backfill.fetch_all_videos_from_channel(
                    channel_id,
                    progress_task=task
                )
                # Remove task when done to prevent line wrapping
                coordinator.remove_task_sync(channel_display_name)
            else:
                # No coordinator - disable progress or use standalone mode
                backfill = YouTubeAPIBackfill(
                    console=self.console,
                    show_progress=False,
                )
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

                # Removed redundant 'new videos saved' message - progress bar shows the count
                db_state["db_count"] = len(videos_data)
                api_total_mismatch = False
                if stored_api_total and db_state["db_count"] == stored_api_total:
                    self.display_plugin.info(
                        f"All {db_state['db_count']} videos have metadata"
                    )
                else:
                    # Removed 'videos already in database' message - progress bar shows the count
                    db_state["db_count"] = len(videos_data)
                    api_total_mismatch = False
                    if stored_api_total and db_state["db_count"] == stored_api_total:
                        self.display_plugin.info(
                            f"All {db_state['db_count']} videos have metadata"
                        )

                # Always run yt-dlp to download subtitles
                # yt-api provides metadata but not subtitles
                should_skip_download = False
            else:
                self.display_plugin.warning(
                    "yt-api: returned 0 objects, falling back to yt-dlp"
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

        # Direct API call - no nested Status (parent progress handles display if present)
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

        self.display_plugin.display_ytapi_status({
            "message": (
                f"✓ {added_count} videos metadata updated "
                f"({quota_info['used']:,} quota used, {total_remaining:,} remaining)"
            )
        })

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
        use_api_for_metadata = self.metadata_backfill.should_use_api_for_metadata(db_state["db_count"])

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
        coordinator: object | None = None,
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
        from rich.progress import BarColumn, Progress, TextColumn

        from yt_fts.core.database import add_videos_bulk, get_vid_ids_by_channel_id
        from yt_fts.db.channels import set_channel_api_total
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        should_skip_download = False
        skip_reason = None
        rss_video_ids_for_download = None

        # Parent-owned progress pattern: create Progress context, pass to service
        # CRITICAL: Use coordinator when provided to avoid duplicate progress bars
        if coordinator is not None and not self.suppress_quota_print:
            # Use parent coordinator to create a task for this channel
            task = coordinator.add_task_sync(
                "   ⎿ yt-api:",
                channel_name=channel_display_name,
                total=100,
                visible=True,
                fields={"stats": ""}
            )
            if task is None:
                # Fall back to no progress if task creation failed
                task = None

            backfill = YouTubeAPIBackfill(
                console=self.console,
                show_progress=(coordinator, task, channel_display_name) if not self.suppress_quota_print else False,
            )

            if not self.suppress_verbose:
                self.display_plugin.info(
                    "   ⎿ [yellow]![/yellow] Gap detected in video history - fetching full list from yt-api to identify missing videos..."
                )

            videos_data = backfill.fetch_all_videos_from_channel(
                channel_id,
                progress_task=task
            )

            # Remove task when done to prevent line wrapping
            coordinator.remove_task_sync(channel_display_name)
        elif coordinator is None and not self.suppress_quota_print:
            # Create parent Progress for yt-api operations (standalone mode)
            with Progress(
                TextColumn("   ⎿ yt-api:"),
                BarColumn(bar_width=20),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("{task.fields[stats]}"),
                console=self.console,
                transient=False,
                refresh_per_second=4,
            ) as progress:
                task = progress.add_task("verify", total=100, stats="0")

                # Pass Progress object to service (parent-owned pattern)
                backfill = YouTubeAPIBackfill(
                    console=self.console,
                    show_progress=progress,  # Pass Progress object instead of bool
                )

                if not self.suppress_verbose:
                    self.display_plugin.info(
                        "   ⎿ [yellow]![/yellow] Gap detected in video history - fetching full list from yt-api to identify missing videos..."
                    )

                # Pass parent task ID for nested updates
                videos_data = backfill.fetch_all_videos_from_channel(
                    channel_id,
                    progress_task=task
                )
        else:
            # Suppress progress mode (simple mode)
            backfill = YouTubeAPIBackfill(
                console=self.console,
                show_progress=False,
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
                # Refresh db_state after setting api_total to show UPDATED stats
                from yt_fts.db.channels import load_channel_db_stats
                try:
                    updated_db_state = load_channel_db_stats(
                        channel_id,
                        get_vid_ids_by_channel_id,
                        get_channel_stats,
                        logging.getLogger(__name__),
                    )
                    db_state.update(updated_db_state)
                except Exception:
                    pass  # Keep existing db_state on refresh error
                self.display_plugin.info(
                    f"   ⎿ [green]✓[/green] db: {self._format_db_stats(
                        db_state.get('db_count') or 0,
                        db_state.get('db_with_subs') or 0,
                        db_state.get('db_no_subs') or 0,
                        db_state.get('db_scheduled') or 0,
                        db_state.get('db_members') or 0,
                        db_state.get('db_unavail_deleted') or 0,
                        db_state.get('db_unavail_private') or 0,
                        db_state.get('db_unavail_geo') or 0,
                        db_state.get('db_unavailable') or 0,
                        db_state.get('db_shorts') or 0,
                        'complete',
                        channel_id=None,
                        channel_display_name=None,
                        db_subscriber_count=db_state.get('db_subscriber_count'),
                        db_playlist_count=db_state.get('db_playlist_count'),
                    )['stats']} in database"
                )
            else:
                add_videos_bulk(
                    channel_id,
                    missing_videos,
                    batch_manager=self.batch_manager,
                )
                # Refresh db_state after adding new videos to show UPDATED stats
                from yt_fts.db.channels import load_channel_db_stats
                try:
                    updated_db_state = load_channel_db_stats(
                        channel_id,
                        get_vid_ids_by_channel_id,
                        get_channel_stats,
                        logging.getLogger(__name__),
                    )
                    # Update the local db_state for downstream use
                    db_state.update(updated_db_state)
                except Exception:
                    pass  # Keep existing db_state on refresh error
                quota_info = YouTubeAPIBackfill.get_global_quota_info()
                num_keys = len(YouTubeAPIBackfill()._load_api_keys())
                total_remaining = quota_info["remaining"] * num_keys
                self.display_plugin.display_ytapi_status({
                    "message": (
                        f"{len(videos_data)} objects total, {db_state['db_count']} in db, "
                        f"{missing_count} new ({quota_info['used']:,} quota used, "
                        f"{total_remaining:,} remaining)"
                    )
                })
                rss_video_ids_for_download = [v["video_id"] for v in missing_videos]
                self.display_plugin.display_ytdlp_operation({
                    "operation": "will download",
                    "message": f"{missing_count} missing videos"
                })
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
        # Consult quota strategy before using API for gap detection
        use_api_for_metadata = self.metadata_backfill.should_use_api_for_metadata(
            db_state.get("db_count", 0)
        )

        if not (
            (rss_status in ("gap_detected", "error") or api_total_mismatch)
            and channel_id
            and (not should_skip_download)
            and use_api_for_metadata  # Only use API if quota strategy allows
        ):
            return should_skip_download, skip_reason, rss_video_ids_for_download

        try:
            return self._handle_gap_detected(
                channel_id,
                channel_display_name,
                db_state,
                get_vid_ids_by_channel_id,
                coordinator,
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

        For channels where db_no_subs > 0 and min_saved > 0,
        fetch videos that don't have subtitles yet.

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

        backfill_needed = False
        backfill_video_ids = []

        if (
            channel_id
            and (db_state["db_no_subs"] or 0) > 0
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

        if backfill_needed:
            # Show explicit reason for yt-dlp backfill
            if not self.suppress_verbose:
                if db_state["db_no_subs"] > 0:
                    backfill_reason = f"backfill: {db_state['db_no_subs']} video(s) without subtitles"
                elif rss_missing_count > 0:
                    backfill_reason = f"backfill: {rss_missing_count} video(s) missing from database"
                else:
                    backfill_reason = "backfill: downloading missing transcripts"
                self.display_plugin.display_rss_status(
                    {"status": "backfill", "message": backfill_reason}
                )

            def _backfill_log_callback(msg: str) -> None:
                """Wrapper to convert single-arg callback to log_operation format."""
                if msg and msg.strip():
                    log_operation("backfill", msg, level=10)


            future = executor.submit(
                self._download_single_channel_optimized,
                original_channel=original_channel,
                resolved_url=resolved_url,
                channel_id=channel_id,
                coordinator=coordinator,
                log_callback=_backfill_log_callback,
                rich_mode=False,
                video_ids=backfill_video_ids,
                display_plugin=self.display_plugin,
            )

            completed_count_increment = 0
            result = None
            try:
                result = future.result()
            except Exception as e:
                result = {"success": False, "error": str(e)}

            # Remove progress bar BEFORE printing any output (fixes line wrapping)
            coordinator.remove_task_sync(original_channel, keep_visible=False)

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
                # Check for skip marker (empty channel - not an error condition)
                if result.get("skip"):
                    self.display_plugin.warning(f"Skipping channel: {error_msg}")
                    results["skipped"].append(
                        {
                            "channel": original_channel,
                            "message": error_msg,
                        }
                    )
                    return True, 0  # Continue to next channel
                # Actual error - log and optionally crash
                self.display_plugin.error(f"Backfill failed: {error_msg}")
                results["failed"].append(
                    {
                        "channel": original_channel,
                        "error": error_msg,
                    }
                )
                if not self.continue_on_error:
                    msg = f"Backfill failed for {original_channel}: {error_msg}"
                    raise Exception(msg)

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
            stats = get_channel_stats_with_subs_and_playlists(channel_id)
            db_state["db_count"] = stats["total"]
            db_state["db_with_subs"] = stats["with_transcripts"]
            db_state["db_scheduled"] = stats["scheduled"]
            db_state["db_members"] = stats["members_only"]
            db_state["db_unavailable"] = stats["unavailable"]
            db_state["db_unavail_deleted"] = stats.get("unavail_deleted", 0)
            db_state["db_unavail_private"] = stats.get("unavail_private", 0)
            db_state["db_unavail_geo"] = stats.get("unavail_geo", 0)
            db_state["db_unavail_resolvable"] = stats.get("unavail_resolvable", 0)
            db_state["db_shorts"] = stats["shorts"]
            db_state["db_no_subs"] = stats["without_transcripts"]
            db_state["db_subscriber_count"] = stats["subscriber_count"]
            db_state["db_playlist_count"] = stats["playlist_count"]

            return channel_id, discovery_source

        return None, "none"


    def _create_progress_task(
        self,
        coordinator: Any,
        original_channel: str,
        rss_video_ids_for_download: list[str] | None,
    ) -> bool:
        """
        Create progress task for the channel download if videos are present.

        Args:
            coordinator: Progress coordinator
            original_channel: Original channel identifier
            rss_video_ids_for_download: Video IDs from RSS to download

        Returns:
            bool: True if task was created, False otherwise
        """
        task_created = rss_video_ids_for_download is not None and len(rss_video_ids_for_download) > 0
        if task_created:
            coordinator.add_task(
                description=YTDLP_PROGRESS_DESC,
                channel_name=original_channel,
                total=100,
                visible=True,
                fields={"stats": ""},
            )
        return task_created

    def _execute_download_with_handler(
        self,
        executor: Any,
        original_channel: str,
        resolved_url: str,
        channel_id: str,
        coordinator: Any,
        rss_video_ids_for_download: list[str] | None,
    ) -> tuple[Any | None, bool]:
        """
        Execute download via thread executor and handle timeout.

        Args:
            executor: Thread executor
            original_channel: Original channel identifier
            resolved_url: Resolved channel URL
            channel_id: Channel ID
            coordinator: Progress coordinator
            rss_video_ids_for_download: Video IDs from RSS to download

        Returns:
            tuple: (result, should_return_early)
        """
        future = executor.submit(
            self._download_single_channel_optimized,
            original_channel,
            resolved_url,
            channel_id,
            coordinator,
            None,
            False,
            rss_video_ids_for_download,
            self.display_plugin,
        )

        try:
            if self.time_per_batch and self.time_per_batch > 0:
                remaining_time = self.time_per_batch - (
                    time.time() - self.batch_start_time
                )
                if remaining_time <= 0:
                    self.display_plugin.warning("Total batch timeout reached")
                    return None, True
                result = future.result(timeout=remaining_time)
            else:
                result = future.result()

            return result, False

        except TimeoutError:
            return None, False



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
        results: dict[str, Any],
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
            results: Results dict to track skipped channels

        Returns:
            tuple: (completed_count_increment, successful_downloads_increment, total_videos_saved_increment)
        """
        completed_count_inc = 1
        successful_downloads_inc = 0
        total_videos_saved_inc = 0

        # Only create progress task if there are videos to download (prevents visual flashing)
        task_created = self._create_progress_task(coordinator, original_channel, rss_video_ids_for_download)

        # Execute download via handler
        result, should_return_early = self._execute_download_with_handler(
            executor,
            original_channel,
            resolved_url,
            channel_id,
            coordinator,
            rss_video_ids_for_download,
        )

        if should_return_early:
            return completed_count_inc, successful_downloads_inc, total_videos_saved_inc

        # Remove progress bar before printing results to prevent line wrapping
        if task_created and result is not None:
            coordinator.remove_task_sync(original_channel, keep_visible=False)
            # Force newline to clear any residual progress bar content
            if coordinator.progress:
                coordinator.progress.console.print("")

            # Check for skip marker (empty channel - not an error condition)
            if result.get("skip"):
                error_msg = result.get("error", "Unknown error")
                self.display_plugin.warning(f"Skipping channel: {error_msg}")
                results["skipped"].append(
                    {
                        "channel": original_channel,
                        "message": error_msg,
                    }
                )
                return completed_count_inc, successful_downloads_inc, total_videos_saved_inc

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
                            # New channel with 0 videos - yt-api found nothing
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

        # Handle timeout error from download execution
        if result is None:
            if task_created:
                coordinator.remove_task_sync(original_channel, keep_visible=False)
            self.display_plugin.warning(
                f"Total batch timeout reached ({self.time_per_batch}s). Stopping..."
            )

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
            # Skip expensive discovery for UC channels - we already have the channel_id
            # Discovery is only needed for handle-only channels or to get metadata
            discovery_source = "database"  # We have the channel_id, treat as database hit
            discovery = None  # Don't call discover() for UC channels
        # Skip handle discovery if we already have a UC channel_id (prevents hangs on Windows)
        elif (
            (not channel_id or (channel_id and channel_id.startswith("handle_")))
            and self.min_saved == 0
            and ("@" in resolved_url or "/" in resolved_url.split("/")[-2:])
        ):
            try:
                # Only do API discovery if we don't already have a valid UC channel_id
                if not (channel_id and channel_id.startswith("UC")):
                    channel_id, discovery_source = (
                        self._discover_channel_via_api_and_update_state(
                            resolved_url, db_state, get_channel_stats
                        )
                    )
                else:
                    # Already have UC channel_id, skip API call
                    discovery_source = "database"
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

    def _check_rss_freshness(
        self,
        channel_id: str | None,
        rss_checker: Any,
        get_videos_needing_recheck: Any,
        update_video_last_checked: Any,
        suppress_verbose: bool,
    ) -> tuple[list, int | None, bool]:
        """
        Check if previously unavailable videos are now available.

        Args:
            channel_id: Channel ID (may be None for handle-only channels)
            rss_checker: RSS checker instance
            get_videos_needing_recheck: Database function to get videos needing recheck
            update_video_last_checked: Database function to update last checked time
            suppress_verbose: Whether to suppress verbose output

        Returns:
            tuple: (recheck_available, rss_missing_count, rss_skip)
        """
        recheck_available = []
        rss_missing_count = None
        rss_skip = False

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
                rss_missing_count = len(recheck_available)
                rss_skip = False

        return recheck_available, rss_missing_count, rss_skip


    def _determine_skip_status(
        self,
        channel_id: str | None,
        handle: str,
        resolved_url: str,
        db_state: dict[str, Any],
        original_channel: str,
        suppress_verbose: bool,
        rss_checker: Any,
        add_video: Any,
        initial_skip: bool,
        initial_missing_count: int | None,
    ) -> tuple[bool, int | None, list | None, str | None, Any, bool]:
        """
        Determine RSS skip status by checking RSS feed and handling various states.

        Args:
            channel_id: Channel ID (may be None for handle-only channels)
            handle: Channel handle
            resolved_url: Resolved channel URL
            db_state: Database state dict
            original_channel: Original channel identifier
            suppress_verbose: Whether to suppress verbose output
            rss_checker: RSS checker instance
            add_video: Database function to add videos
            initial_skip: Initial skip status from freshness check
            initial_missing_count: Initial missing count from freshness check

        Returns:
            tuple: (rss_skip, rss_missing_count, rss_video_ids_for_download, 
                    rss_error_msg, rss_result, new_channel_skipped_rss)
        """
        rss_skip = initial_skip
        rss_missing_count = initial_missing_count
        rss_video_ids_for_download = None
        rss_error_msg = None
        new_channel_skipped_rss = False

        # Determine RSS skip status by checking RSS feed
        rss_skip, rss_missing_count, rss_video_ids_for_download, rss_error_msg, rss_result, new_channel_skipped_rss = (
            self._determine_skip_status(
                channel_id,
                handle,
                resolved_url,
                db_state,
                original_channel,
                suppress_verbose,
                rss_checker,
                add_video,
                rss_skip,
                rss_missing_count,
            )
        )

        return rss_skip, rss_missing_count, rss_video_ids_for_download, rss_error_msg, rss_result, new_channel_skipped_rss


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
            tuple: (
            status, message, rss_skip, rss_missing_count,
            rss_video_ids_for_download, new_channel_skipped_rss, rss_result
        )
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
        new_channel_skipped_rss = False

        # Check if previously unavailable videos are now available
        recheck_available, rss_missing_count, rss_skip = self._check_rss_freshness(
            channel_id,
            rss_checker,
            get_videos_needing_recheck,
            update_video_last_checked,
            suppress_verbose,
        )
        if recheck_available:
            rss_video_ids_for_download = recheck_available

        # Determine RSS skip status by checking RSS feed
        rss_skip, rss_missing_count, rss_video_ids_for_download, rss_error_msg, rss_result, new_channel_skipped_rss = (
            self._determine_skip_status(
                channel_id,
                handle,
                resolved_url,
                db_state,
                original_channel,
                suppress_verbose,
                rss_checker,
                add_video,
                rss_skip,
                rss_missing_count,
            )
        )

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

    def _validate_and_resolve_channels(
        self, suppress_quota_print_original: bool
    ) -> tuple[list | None, dict | None, list | None, list]:
        """
        Validate and resolve channels for batch download.
        
        Args:
            suppress_quota_print_original: Original suppress_quota_print value
            
        Returns:
            tuple: (channel_downloads, results, invalid_channels, empty_results_dict)
        """
        results, total_videos_saved = self._initialize_batch_download()
        if results is None:  # Early return from dry_run
            return None, {
                "successful": [],
                "failed": [],
                "skipped": [],
                "invalid_channels": [],
            }, [], {
                "successful": [],
                "failed": [],
                "skipped": [],
                "invalid_channels": [],
            }

        channel_downloads, invalid_channels = self._resolve_and_validate_channels(
            file_stats=self.file_stats
        )
        if channel_downloads is None:  # Rich mode early return
            return None, None, invalid_channels, {
                "successful": [],
                "failed": [],
                "skipped": [],
                "invalid_channels": [],
            }

        return channel_downloads, results, invalid_channels, None

    def _initialize_progress_tracking(
        self, channel_downloads: list
    ) -> tuple:
        """
        Initialize progress tracking and prefetch channel names.
        
        Args:
            channel_downloads: List of (channel, url, channel_id) tuples
            
        Returns:
            tuple: (progress_ctx, suppress_verbose)
        """
        suppress_verbose = self.suppress_verbose
        # Use centralized config for batch progress (stacked bars, multi-channel)
        progress_ctx = Progress(
            TextColumn(
                "[bold blue]{task.description}[/bold blue]",
                table_column=Column(width=15),
            ),
            BarColumn(bar_width=20),
            TextColumn(
                "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage]"
            ),
            TextColumn("{task.fields[stats]}", table_column=Column(width=DISPLAY_COLUMN_WIDTH)),
            console=self.progress_console,
            **BATCH_PROGRESS_CONFIG,  # Unpack config: auto_refresh, redirect_stderr, transient, etc.
        )
        if not self.suppress_verbose:
            self.console.print(
                f"[cyan]Processing {len(channel_downloads)} channels...[/cyan]"
            )

        # Optimization: Pre-fetch missing channel names in parallel (if enabled)
        if self._prefetch_channel_names:
            self._prefetch_channel_names_parallel(channel_downloads)

        return progress_ctx, suppress_verbose


    def download_all(self) -> dict[str, Any]:
        """
        Download all channels with progress tracking and optimized parallel resolution.

        Returns:
            dict: Results with success/failure status for each channel
        """
        # DEBUG: Check what rich_mode actually is

        # Suppress API quota progress prints in Rich Layout mode to prevent flickering
        suppress_quota_print_original = self.suppress_quota_print
        if self.rich_mode == "new":
            self.suppress_quota_print = True

        # Step 1: Validate and resolve channels
        channel_downloads, results, _invalid_channels, early_return = (
            self._validate_and_resolve_channels(suppress_quota_print_original)
        )
        if early_return is not None:
            return early_return

        # Step 2: Initialize progress tracking
        progress_ctx, suppress_verbose = self._initialize_progress_tracking(
            channel_downloads
        )

        # Step 3: Coordinate parallel downloads
        results = self._coordinate_parallel_downloads(
            channel_downloads=channel_downloads,
            results=results,
            progress_ctx=progress_ctx,
            suppress_verbose=suppress_verbose,
        )

        # Step 4: Collect and report statistics
        return self._collect_and_report_statistics(results)


    def _create_download_handler(
        self,
        channel_id: str,
        channel_display_name: str,
        coordinator: ThreadSafeProgressCoordinator,
        original_channel: str,
        log_callback: Callable[[str], None] | None,
        rich_mode: bool,
        display_plugin: Any,
        video_ids: list[str] | None,
    ) -> DownloadHandler:
        """
        Create and configure a DownloadHandler instance.

        Args:
            channel_id: Channel ID for the download
            channel_display_name: Display name from database
            coordinator: Progress coordinator instance
            original_channel: Original channel input
            log_callback: Optional log callback
            rich_mode: Whether using Rich UI
            display_plugin: Display plugin instance
            video_ids: Optional list of specific video IDs

        Returns:
            Configured DownloadHandler instance
        """
        from yt_fts.download.download_handler import DownloadHandler

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
            whisper_model=self.whisper_model,
            keep_audio=self.keep_audio,
            include_channel_name_in_messages=False,
            display_plugin=display_plugin,
            download_checkpoint=self.download_checkpoint,
        )
        # Set the actual channel name from database
        handler.channel_id = channel_id
        handler.channel_name = channel_display_name
        handler.set_progress_tracker(coordinator, original_channel)
        if video_ids:
            handler.video_ids = video_ids
            handler.min_saved = self.min_saved
        return handler

    def _check_empty_video_list(
        self,
        video_ids: list[str] | None,
        original_channel: str,
        resolved_url: str,
        channel_id: str,
    ) -> dict[str, Any] | None:
        """
        Check if video list is empty and return early result.

        Args:
            video_ids: List of video IDs (None = not checked, empty = checked and empty)
            original_channel: Original channel input
            resolved_url: Resolved channel URL
            channel_id: Channel ID

        Returns:
            Skip result dict if empty, None otherwise
        """
        if video_ids is not None and len(video_ids) == 0:
            log_operation(
                "channel_skip",
                f"Skipping download - RSS found no new videos: {original_channel}",
                channel=original_channel,
                channel_id=channel_id,
                level=10,
            )
            return {
                "success": True,
                "channel": original_channel,
                "resolved_url": resolved_url,
                "channel_id": channel_id,
                "message": "No new subtitles",
                "videos_count": 0,
                "videos_without_subtitles": 0,
                "total_videos": 0,
            }
        return None

        return handler

    def _download_single_channel_optimized(
        self,
        original_channel: str,
        resolved_url: str,
        channel_id: str,
        coordinator: ThreadSafeProgressCoordinator,
        log_callback: Callable[[str], None] | None = None,
        rich_mode: bool = False,
        video_ids: list[str] | None = None,
        display_plugin: Any = None,
        cached_channel_id: str | None = None,
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
            display_plugin: Display plugin instance for formatted output
            cached_channel_id: UC channel ID from cache (prioritize over resolved_url for fetching)

        Returns:
            dict: Result with success status and details
        """

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
                handler = self._create_download_handler(
                    channel_id,
                    channel_display_name,
                    coordinator,
                    original_channel,
                    log_callback,
                    rich_mode,
                    display_plugin,
                    video_ids,
                )
                # Early return when RSS determined no new videos (empty list, not None)
                # This prevents unnecessary yt-dlp invocation when we already know there's nothing to download
                skip_result = self._check_empty_video_list(
                    video_ids, original_channel, resolved_url, channel_id
                )
                if skip_result:
                    return skip_result
                try:
                    return self._execute_channel_download(
                        handler,
                        cached_channel_id,
                        original_channel,
                        resolved_url,
                        channel_id,
                    )
                except Exception:
                    raise
            except KeyboardInterrupt:
                if "handler" in locals():
                    handler.cleanup_progress()
                raise
            except ChannelEmptyError as e:
                return self._handle_empty_channel_error(
                    e, handler, original_channel, resolved_url, rich_mode, log_callback
                )
            except DownloadTimeoutException as e:
                return self._handle_timeout_error(
                    e, handler, original_channel, resolved_url, channel_id, rich_mode, log_callback
                )
            except BaseURLFallbackFailed as e:
                from yt_fts.utils.retry_classifier import should_skip_retry
                error_msg = str(e)
                if should_skip_retry(error_msg):
                    return {
                        "success": False,
                        "error": error_msg,
                        "skipped_retry": True,
                    }
                return {"success": False, "error": error_msg}
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
                return self._handle_retry_or_failure(
                    e,
                    error_msg,
                    attempt,
                    original_channel,
                    resolved_url,
                    channel_id,
                    rich_mode,
                    log_callback,
                )
        return {"success": False, "error": "Max retries exceeded"}

    def _download_single_channel_resolved(
        self,
        original_channel: str,
        resolved_channel: str,
        progress: Progress,
        main_task_id: TaskID,
        display_plugin: Any = None,
    ) -> dict[str, Any]:
        """
        Download a single channel with retry logic (already resolved).

        Args:
            original_channel: Original channel input for display
            resolved_channel: Resolved channel ID for downloading
            progress: Progress bar object
            main_task_id: Main progress task ID
            display_plugin: Display plugin for formatted output

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
                                whisper_model=self.whisper_model,
                    keep_audio=self.keep_audio,
                    display_plugin=display_plugin,
                download_checkpoint=self.download_checkpoint)
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


    # =============================================================================
    # State-Based Discovery Integration
    # =============================================================================

    def _perform_state_based_discovery_for_channel(
        self,
        channel_id: str,
        handle: str,
        resolved_url: str,
        db_video_ids: set,
        db_count: int,
        rss_checker,
    ) -> tuple[list[str] | None, str, str]:
        """
        Perform state-based discovery for a channel.
        
        Replaces the RSS-first approach with intelligent state detection.
        
        Args:
            channel_id: Channel ID
            handle: Channel handle
            resolved_url: Resolved channel URL
            db_video_ids: Set of existing video IDs in DB
            db_count: Count of videos in DB
            rss_checker: RSS checker instance
            
        Returns:
            tuple: (video_ids, status, message)
        """
        from yt_fts.discovery.state_detection import (
            ChannelState,
            DiscoveryMethod,
            detect_channel_state,
            recovery_strategy,
            steady_state_strategy,
            transition_strategy,
        )

        quota_pct = DEFAULT_QUOTA_PERCENTAGE

        state = detect_channel_state(channel_id)

        if state == ChannelState.TRANSITION:
            method = transition_strategy(channel_id, quota_pct)
        elif state == ChannelState.STEADY_STATE:
            method = steady_state_strategy(channel_id)
        else:
            method = recovery_strategy(channel_id, quota_pct)

        if method == DiscoveryMethod.RSS:
            rss_result = rss_checker.check(
                channel_id=channel_id,
                handle=handle,
                resolved_url=resolved_url,
                db_video_ids=db_video_ids,
            )

            if rss_result:
                if rss_result.status == "skip":
                    return None, "skip", "Up to date"
                if rss_result.status == "new_videos":
                    return rss_result.video_ids, "new_videos", f"RSS: {len(rss_result.video_ids)} new"
                if rss_result.status == "gap_detected":
                    pass
                else:
                    return None, "error", f"RSS error: {rss_result.status}"

        if (
            method == DiscoveryMethod.API or
            (method == DiscoveryMethod.RSS and rss_result and rss_result.status == "gap_detected")
        ):
            from rich.progress import BarColumn, Progress, TextColumn

            from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

            try:
                # Parent-owned progress pattern for state-based discovery
                with Progress(
                    TextColumn("   ⎿ yt-api:"),
                    BarColumn(bar_width=20),
                    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                    TextColumn("{task.fields[stats]}"),
                    console=self.console,
                    transient=False,
                    refresh_per_second=4,
                ) as progress:
                    task = progress.add_task("0", total=100)
                    # Conditionally pass progress object based on suppress_quota_print

                    backfill = YouTubeAPIBackfill(

                        console=self.console,

                        show_progress=progress if not self.suppress_quota_print else False,

                    )
                    videos_data = backfill.fetch_all_videos_from_channel(
                        channel_id,
                        progress_task=task
                    )

                if videos_data:
                    video_ids = [
                        v.get("video_id", v.get("id"))
                        for v in videos_data
                        if v.get("video_id") or v.get("id")
                    ]

                    from yt_fts.db.channels import set_channel_api_total
                    set_channel_api_total(channel_id, len(videos_data))

                    return video_ids, "new_videos", f"API: {len(video_ids)} videos"
                return None, "error", "API: No videos found"
            except Exception as e:
                if method == DiscoveryMethod.API:
                    pass
                else:
                    return None, "error", f"API error: {e}"

        if method == DiscoveryMethod.YTDLP:
            from yt_fts.download.download_handler import DownloadHandler

            handler = DownloadHandler(
                number_of_jobs=1,
                language=self.language,
                cookies_from_browser=self.cookies_from_browser,
                console=self.console,
                suppress_status_messages=True,
            )

            try:
                videos_data = handler.get_playlist_data(resolved_url)

                if videos_data:
                    video_ids = [
                        v.get("video_id", v.get("id"))
                        for v in videos_data
                        if v.get("video_id") or v.get("id")
                    ]

                    from yt_fts.db.channels import set_channel_api_total
                    set_channel_api_total(channel_id, len(video_ids))

                    return video_ids, "new_videos", f"yt-dlp: {len(video_ids)} videos"
                return None, "error", "yt-dlp: Failed"
            except Exception as e:
                return None, "error", f"yt-dlp error: {e}"

        return None, "skip", "No discovery method succeeded"

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
            get_db_connection,
            get_vid_ids_by_channel_id,
            is_channel_skipped,
        )
        from yt_fts.services.rss_precheck import create_rss_checker

        from .channel_cache import get_cached_channels, save_resolved_channels
        from .fast_channel_resolver import create_fast_resolver

        results = {"successful": [], "failed": [], "skipped": []}
        enable_wal_mode()
        conn = get_db_connection(timeout=DB_CONNECTION_TIMEOUT)
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
            # Normalize newly_resolved (str->str) to tuples (str->tuple) to match cached_channels format
            newly_resolved_tuples = self._normalize_resolved_to_tuples(newly_resolved) if newly_resolved else {}
            resolved_channels.update(newly_resolved_tuples)
            if newly_resolved:
                save_resolved_channels(newly_resolved, console=self.console)
        if not resolved_channels:
            results["failed"].append(
                {"channel": channel, "error": "Failed to resolve channel"}
            )
            return results
        # Extract channel_id and resolved_url from cached tuples
        first_entry = next(iter(resolved_channels.values()))
        if isinstance(first_entry, tuple) and len(first_entry) == 2:
            cached_channel_id, resolved_url = first_entry
        else:
            cached_channel_id, resolved_url = None, first_entry
        # DEBUG: Trace resolved_url to find truncation point
        log_operation(
            "process_single_channel",
            f"[DEBUG] resolved_url from cache: {resolved_url}",
            level=10,
        )
        # Store the original channel identifier for reporting
        original_channel = channel
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
        channel_id = None
        if "/channel/" in resolved_url:
            channel_id = resolved_url.split("/channel/")[1].split("/")[0]
        db_count = 0
        db_video_ids = set()
        # Track metadata for display purposes
        db_subscriber_count = None
        db_playlist_count = None

        if channel_id:
            try:
                local_vid_ids = [v[0] for v in get_vid_ids_by_channel_id(channel_id)]
                db_video_ids = set(local_vid_ids)
                stats = get_channel_stats_with_subs_and_playlists(channel_id)
                db_count = stats["total"]
                stats["with_transcripts"]
                stats["scheduled"]
                stats["members_only"]
                stats["without_transcripts"]
                db_subscriber_count = stats.get("subscriber_count")
                db_playlist_count = stats.get("playlist_count")

                # Check if metadata backfill is needed
                if db_subscriber_count is None and channel_id:
                    self.metadata_backfill.backfill_channel_metadata_if_needed(channel_id)
                    # Refresh stats after backfill to show new values
                    stats = get_channel_stats_with_subs_and_playlists(channel_id)
                    db_subscriber_count = stats.get("subscriber_count")
                    db_playlist_count = stats.get("playlist_count")

                # Backfill playlist_count if NULL (via yt-dlp)
                if db_playlist_count is None and channel_id:
                    self.metadata_backfill.backfill_playlist_count_if_needed(channel_id)
                    # Refresh stats after backfill to show new values
                    stats = get_channel_stats_with_subs_and_playlists(channel_id)
                    db_subscriber_count = stats.get("subscriber_count")
                    db_playlist_count = stats.get("playlist_count")
            except Exception:
                db_video_ids = set()
                db_count = 0
        # State-based discovery: Choose method based on channel state
        rss_checker = create_rss_checker(timeout=DB_CONNECTION_TIMEOUT)

        # Use state-based discovery instead of RSS-only
        video_ids, status, message = self._perform_state_based_discovery_for_channel(
            channel_id=channel_id,
            handle=(
                resolved_url.split("@")[-1].split("/")[0]
                if "@" in resolved_url
                else None
            ),
            resolved_url=resolved_url,
            db_video_ids=db_video_ids,
            db_count=db_count,
            rss_checker=rss_checker,
        )

        if video_ids:
            rss_video_ids_for_download = video_ids
        else:
            rss_video_ids_for_download = None

        if status == "skip" and (not rss_video_ids_for_download):
            results["skipped"].append(
                {"channel": original_channel, "message": message}
            )
            return results
        if coordinator is None and (not self.suppress_verbose):
            from rich.progress import BarColumn, Progress, TextColumn

            from .progress_coordinator import ThreadSafeProgressCoordinator

            # Use centralized config for single-channel progress
            progress_ctx = Progress(
                TextColumn("[bold blue]{task.description}[/bold blue]"),
                BarColumn(bar_width=20),
                TextColumn(
                    "[progress.percentage]{task.percentage:>3.0f}%[/progress.percentage]"
                ),
                console=self.console,
                **SINGLE_CHANNEL_PROGRESS_CONFIG,  # Unpack config: auto_refresh=False, transient, etc.
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
                display_plugin=self.display_plugin,
                cached_channel_id=cached_channel_id,
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
# DUF test comment
