"""
Parallel batch processor for downloading multiple YouTube channels concurrently.
"""

# contextlib, io no longer needed with output visible
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, TypedDict

from yt_fts.core.database import enable_wal_mode
from yt_fts.utils.text_formatter import TextFormatter

# Shared formatter instance for parallel processor logging
_formatter = TextFormatter()


def _set_formatter(formatter) -> None:
    """Set the global formatter for parallel processor logging."""
    global _formatter
    _formatter = formatter


def _log(level: str, tag: str, msg: str) -> None:
    """Legacy wrapper for TextFormatter.

    Args:
        level: Log level (INFO, DONE, ERROR, WARN, PROG)
        tag: Component tag
        msg: Log message
    """
    if level == "INFO":
        _formatter.info(tag, msg)
    elif level == "DONE":
        _formatter.done(tag, msg)
    elif level == "ERROR":
        _formatter.error(tag, msg)
    elif level == "WARN":
        _formatter.warn(tag, msg)
    elif level == "PROG":
        _formatter.progress(tag, msg)
    else:
        _formatter.info(tag, msg)


def _format_eta(seconds: float) -> str:
    """Format seconds into human-readable time remaining.

    Examples:
        45 -> "45s"
        90 -> "1m 30s"
        3700 -> "1h 1m"
    """
    if seconds < 0:
        return "unknown"
    if seconds < 60:
        return f"{int(seconds)}s"
    if seconds < 3600:
        mins = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{mins}m {secs}s" if secs else f"{mins}m"
    hours = int(seconds // 3600)
    mins = int((seconds % 3600) // 60)
    return f"{hours}h {mins}m" if mins else f"{hours}h"


from .batch_downloader import BatchDownloader
from .batch_filter import pre_filter_fresh_channels
from .rate_limit_tracker import RateLimitTracker

# Import Rich progress components at module level for testability
try:
    from .rich_parallel_progress import RICH_AVAILABLE, RichParallelProgress
except ImportError:
    RICH_AVAILABLE = False
    RichParallelProgress = None


class WorkerStatus:
    """Thread-safe tracker for worker status counters and current channel.

    Used to track progress across multiple parallel workers without
    race conditions. All methods are thread-safe via a lock.
    """

    def __init__(self) -> None:
        """Initialize a WorkerStatus with zero counters and no current channel."""
        self._ok = 0
        self._err = 0
        self._skip = 0
        self._current: str = ""
        self._lock = threading.Lock()

    def add_ok(self, count: int = 1) -> None:
        """Add to the success counter.

        Args:
            count: Number to add (default: 1).
        """
        with self._lock:
            self._ok += count

    def add_err(self, count: int = 1) -> None:
        """Add to the error counter.

        Args:
            count: Number to add (default: 1).
        """
        with self._lock:
            self._err += count

    def add_skip(self, count: int = 1) -> None:
        """Add to the skip counter.

        Args:
            count: Number to add (default: 1).
        """
        with self._lock:
            self._skip += count

    def set_current(self, channel: str) -> None:
        """Set the current channel being processed.

        Args:
            channel: Channel identifier (URL/handle).
        """
        with self._lock:
            self._current = channel

    def get_counts(self) -> tuple[int, int, int, str]:
        """Get current counts and channel.

        Returns:
            Tuple of (ok, err, skip, current_channel).
        """
        with self._lock:
            return (self._ok, self._err, self._skip, self._current)


class ProcessResult(TypedDict):
    """Result of processing channels.

    Attributes:
        successful: List of successfully processed channels with metadata
        failed: List of channels that failed processing with error details
        skipped: List of channels that were skipped with reasons
    """

    successful: list[dict]
    failed: list[dict]
    skipped: list[dict]


class ParallelBatchProcessor:
    """
    Process multiple YouTube channels in parallel using ThreadPoolExecutor.

    Features:
    - Parallel channel processing with configurable workers
    - Simple clean text progress updates
    - Work queue pattern for better load balancing
    - Graceful error handling with continue-on-error support
    - WAL mode enabled for better concurrent database access
    - Suppresses inner verbose output for cleaner display
    """

    def __init__(
        self,
        language: str = "en",
        cookies_from_browser: str | None = None,
        delay_between_channels: float = 3.0,
        max_retries: int = 3,
        continue_on_error: bool = True,
        time_per_channel: float | None = None,
        time_per_video: float | None = None,
        time_per_batch: float | None = None,
        min_saved: int | None = None,
        videos_download_per_batch: int | None = None,
        display_plugin=None,
        auto_backfill: bool = False,
        freshness_hours: int = 6,
        quota_strategy=None,
        use_rich_progress: bool = False,
        rich_display_mode: str = "progress",  # "progress" or "table"
        use_phase2: bool = False,
        phase2_batch_size: int = 500,
        use_fzf: bool = False,
        use_json: bool = False,
        video_jobs: int = 1,
        auto_adjust_video_jobs: bool = False,
    ):
        """
        Initialize the ParallelBatchProcessor.

        Args:
            language: Language for subtitles (default: "en")
            cookies_from_browser: Browser to extract cookies from
            delay_between_channels: Delay between processing channels (seconds)
            max_retries: Maximum number of retries per channel
            continue_on_error: Continue processing other channels if one fails
            time_per_channel: Maximum time to spend per channel (seconds)
            time_per_video: Maximum time per video (seconds)
            time_per_batch: Maximum time for entire batch (seconds)
            min_saved: Minimum videos to save per channel
            videos_download_per_batch: Maximum videos across all channels
            display_plugin: DisplayPlugin instance for real-time logging
            auto_backfill: Auto-backfill metadata after downloads
            freshness_hours: Skip channels checked within N hours
            use_rich_progress: Use Rich progress bars/table instead of simple output
            rich_display_mode: "progress" for stacked bars, "table" for live table
            use_fzf: Output tab-separated format for fzf/awk pipelining
            use_json: Output JSON format for programmatic parsing
            video_jobs: Number of parallel jobs for video processing (default: 1)
            auto_adjust_video_jobs: Enable dynamic adjustment based on rate limits (default: False)
        """
        self.language = language
        self.cookies_from_browser = cookies_from_browser
        self.delay_between_channels = delay_between_channels
        self.max_retries = max_retries
        self.continue_on_error = continue_on_error
        self.time_per_channel = time_per_channel
        self.time_per_video = time_per_video
        self.time_per_batch = time_per_batch
        self.min_saved = min_saved
        self.videos_download_per_batch = videos_download_per_batch
        self.display_plugin = display_plugin
        self.auto_backfill = auto_backfill
        self.freshness_hours = freshness_hours
        self.quota_strategy = quota_strategy
        self.use_rich_progress = use_rich_progress
        self.rich_display_mode = rich_display_mode
        self.use_phase2 = use_phase2
        self.phase2_batch_size = phase2_batch_size
        self.use_fzf = use_fzf
        self.use_json = use_json
        self.video_jobs = video_jobs
        self.auto_adjust_video_jobs = auto_adjust_video_jobs
        self._rate_limit_tracker = None
        self._rate_limit_lock = threading.Lock()

        # Setup formatter from display plugin if available
        if self.display_plugin:
            plugin_formatter = self.display_plugin.get_formatter()
            if plugin_formatter:
                _set_formatter(plugin_formatter)

        if auto_adjust_video_jobs:
            self._rate_limit_tracker = RateLimitTracker(
                start_jobs=max(2, video_jobs),
                min_jobs=1,
                max_jobs=8,
                on_jobs_changed=self._on_video_jobs_changed,
            )
            _log(
                "INFO",
                "AUTO-ADJUST",
                f"Video jobs auto-adjust enabled (starting at {self._rate_limit_tracker.current_jobs})",
            )

    def _on_video_jobs_changed(self, new_jobs: int) -> None:
        """Callback when RateLimitTracker adjusts the worker count.

        Args:
            new_jobs: The new worker count
        """
        old_jobs = self.video_jobs
        self.video_jobs = new_jobs
        _log("INFO", "AUTO-ADJUST", f"Video jobs adjusted: {old_jobs} -> {new_jobs}")

    def _check_for_rate_limit(self, result: dict) -> str | None:
        """Check if a result contains rate limit errors.

        Args:
            result: Result dict from process_single_channel

        Returns:
            Error message if rate limit detected, None otherwise
        """
        rate_limit_indicators = [
            "429",
            "Too Many Requests",
            "rate limit",
            "quota exceeded",
        ]
        for failed in result.get("failed", []):
            error = failed.get("error", "")
            if any(
                indicator.lower() in error.lower()
                for indicator in rate_limit_indicators
            ):
                return error
        return None

    def _notify_channel_completion(
        self, channel: str, result: dict, status: str
    ) -> None:
        """Notify RateLimitTracker of channel completion.

        Args:
            channel: Channel identifier
            result: Result dict from process_single_channel
            status: Status string ('✓', '✗', '⊘')
        """
        if not self._rate_limit_tracker:
            return

        if status == "✓":
            # Success - notify tracker
            self._rate_limit_tracker.on_success(channel)
        else:
            # Check for rate limit errors
            rate_limit_error = self._check_for_rate_limit(result)
            if rate_limit_error:
                self._rate_limit_tracker.on_rate_limit(channel, rate_limit_error)

    def _make_empty_result(self) -> ProcessResult:
        """Create an empty result dict with proper structure.

        Returns:
            ProcessResult with empty lists
        """
        return {"successful": [], "failed": [], "skipped": []}

    def process_channels(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """
        Process multiple channels in parallel with progress display.

        Args:
            channels: List of channel URLs/handles
            num_workers: Number of parallel workers
            continue_on_error: Continue processing if a worker fails

        Returns:
            ProcessResult dict with successful, failed, and skipped channels
        """
        # Route to appropriate display mode (priority: fzf > json > rich > simple)
        if self.use_fzf:
            return self._process_channels_fzf(channels, num_workers, continue_on_error)
        if self.use_json:
            return self._process_channels_json(channels, num_workers, continue_on_error)
        if self.use_rich_progress:
            return self._process_channels_with_rich(
                channels, num_workers, continue_on_error
            )
        return self._process_channels_simple(channels, num_workers, continue_on_error)

    def _process_channels_with_rich(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """Process channels with Rich progress bars/table display."""
        result = self._make_empty_result()

        if not channels:
            return result

        enable_wal_mode()

        # Pre-filter fresh channels
        if self.freshness_hours > 0 and self.min_saved == 0:
            channels, _skipped_count = pre_filter_fresh_channels(
                channels=channels,
                freshness_hours=self.freshness_hours,
                min_saved=self.min_saved,
            )
            # Note: skipped_count is just a count, not a list of channels

        if not channels:
            return result

        # Import Rich progress
        from .rich_parallel_progress import RICH_AVAILABLE, RichParallelProgress

        if not RICH_AVAILABLE:
            print("⚠ Rich not installed, falling back to simple output", flush=True)
            print("  Install with: pip install rich", flush=True)
            return self._process_channels_simple(
                channels, num_workers, continue_on_error
            )

        # Show quota status
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        api_backfill = YouTubeAPIBackfill()
        display_name = (
            self.display_plugin.get_name() if self.display_plugin else "default"
        )
        rich_mode = self.rich_display_mode or "progress"
        print(
            f"📊 Quota: {api_backfill.format_quota_display()} | Display: {display_name} ({rich_mode})",
            flush=True,
        )

        progress = RichParallelProgress()
        progress.start(display_mode=self.rich_display_mode)

        len(channels)
        remaining = list(channels)
        completed = 0
        ok_count = 0
        err_count = 0
        skip_count = 0
        lock = threading.Lock()

        # FLATTENED ARCHITECTURE: Create ONE shared BatchDownloader before outer TPE
        # This eliminates nested TPEs. Jobs=1 for sequential video processing.
        from .batch_downloader import BatchDownloader

        shared_downloader = BatchDownloader(
            channels=channels,
            jobs=self.video_jobs,
            language=self.language,
            quota_strategy=self.quota_strategy,
            cookies_from_browser=self.cookies_from_browser,
            delay_between_channels=self.delay_between_channels,
            max_retries=self.max_retries,
            continue_on_error=self.continue_on_error,
            time_per_channel=self.time_per_channel,
            time_per_video=self.time_per_video,
            time_per_batch=self.time_per_batch,
            min_saved=self.min_saved,
            videos_download_per_batch=self.videos_download_per_batch,
            display_plugin=None,
            auto_backfill=self.auto_backfill,
            freshness_hours=self.freshness_hours,
            suppress_quota_print=True,
            suppress_verbose=True,
        )

        def _process_one(
            channel: str, rich_progress: RichParallelProgress
        ) -> tuple[Any, ...]:
            """Process a single channel with Rich progress updates using shared downloader."""
            channel_result = self._make_empty_result()

            # Add channel to progress display
            task_key = rich_progress.add_channel(channel, channel, estimated_total=100)

            try:
                rich_progress.update(task_key, status="fetching")

                # Use shared downloader - no per-worker BatchDownloader creation
                download_result = shared_downloader.process_single_channel(channel)

                channel_result["successful"].extend(
                    download_result.get("successful", [])
                )
                channel_result["failed"].extend(download_result.get("failed", []))
                channel_result["skipped"].extend(download_result.get("skipped", []))

                # Determine status
                if download_result.get("successful"):
                    status = "✓"
                elif download_result.get("skipped"):
                    status = "⊘"
                else:
                    status = "✗"

                # Mark complete
                rich_progress.complete(task_key)

                return channel_result, status

            except Exception as e:
                rich_progress.set_error(task_key, str(e)[:50])
                if not self.continue_on_error:
                    raise
                return channel_result, "✗"

            def _worker(channel: str) -> tuple[Any, ...]:
                """Wrapper for worker thread."""
                return _process_one(channel, progress)

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                futures: dict[Any, Any] = {}

                while remaining and len(futures) < num_workers:
                    channel = remaining.pop(0)
                    futures[executor.submit(_worker, channel)] = channel

                while futures:
                    for future in as_completed(futures):
                        channel = futures.pop(future)
                        completed += 1

                        try:
                            channel_result, status = future.result()
                            result["successful"].extend(
                                channel_result.get("successful", [])
                            )
                            result["failed"].extend(channel_result.get("failed", []))
                            result["skipped"].extend(channel_result.get("skipped", []))

                            with lock:
                                if status == "✓":
                                    ok_count += 1
                                elif status == "⊘":
                                    skip_count += 1
                                else:
                                    err_count += 1

                        except Exception as e:
                            with lock:
                                err_count += 1
                                result["failed"].append(
                                    {"channel": channel, "error": str(e)}
                                )
                            if not continue_on_error:
                                raise

                        # Submit next work
                        if remaining:
                            next_channel = remaining.pop(0)
                            futures[executor.submit(_worker, next_channel)] = (
                                next_channel
                            )
                            break

            progress.stop()
            return result

        def _process_channels_fzf(
            self,
            channels: list[str],
            num_workers: int = 2,
            continue_on_error: bool = False,
        ) -> ProcessResult:
            """Process channels with tab-separated output for fzf/awk pipelining.

            Output format per line: status\tchannel\tvideos\ttime\terror
            - status: ok, skip, err
            - channel: channel URL/handle
            - videos: number of videos downloaded
            - time: elapsed time in seconds
            - error: error message (if status=err)
            """
            result = self._make_empty_result()

            if not channels:
                return result

            enable_wal_mode()

            # Pre-filter fresh channels
            if self.freshness_hours > 0 and self.min_saved == 0:
                channels, _skipped = pre_filter_fresh_channels(
                    channels=channels,
                    freshness_hours=self.freshness_hours,
                    min_saved=self.min_saved,
                )

            len(channels)
            list(channels)
            threading.Lock()

            # FLATTENED ARCHITECTURE: Create ONE shared BatchDownloader before outer TPE
            # This eliminates nested TPEs. Jobs=1 for sequential video processing.
            shared_downloader = BatchDownloader(
                channels=channels,
                jobs=self.video_jobs,
                language=self.language,
                quota_strategy=self.quota_strategy,
                cookies_from_browser=self.cookies_from_browser,
                delay_between_channels=self.delay_between_channels,
                max_retries=self.max_retries,
                continue_on_error=self.continue_on_error,
                time_per_channel=self.time_per_channel,
                time_per_video=self.time_per_video,
                time_per_batch=self.time_per_batch,
                min_saved=self.min_saved,
                videos_download_per_batch=self.videos_download_per_batch,
                display_plugin=(
                    self.display_plugin.get_name() if self.display_plugin else None
                ),
                auto_backfill=self.auto_backfill,
                freshness_hours=self.freshness_hours,
                suppress_quota_print=True,
                suppress_verbose=True,
            )

            def _process_one(
                channel: str,
            ) -> tuple[ProcessResult, str, int, str, float]:
                """Process a single channel with fzf-style output using shared downloader."""
                channel_result = self._make_empty_result()
                import time

                start = time.time()
                videos = 0
                error = ""
                status = "ok"

                try:
                    # Use shared downloader - no per-worker BatchDownloader creation
                    download_result = shared_downloader.process_single_channel(channel)

                    channel_result["successful"].extend(
                        download_result.get("successful", [])
                    )
                    channel_result["failed"].extend(download_result.get("failed", []))
                    channel_result["skipped"].extend(download_result.get("skipped", []))

                    videos = len(download_result.get("successful", []))

                    if download_result.get("failed"):
                        status = "err"
                        error = str(
                            download_result["failed"][0].get("error", "Unknown error")
                        )
                    elif download_result.get("skipped"):
                        status = "skip"

                except Exception as e:
                    status = "err"
                    error = str(e)
                    channel_result["failed"].append(
                        {"channel": channel, "error": error}
                    )
                    if not self.continue_on_error:
                        raise

                elapsed = time.time() - start
                return channel_result, status, videos, error, elapsed
            return None

        def _worker(channel: str) -> tuple[Any, ...]:
            """Wrapper for worker thread."""
            return _process_one(channel, progress)

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures: dict[Any, Any] = {}

            while remaining and len(futures) < num_workers:
                channel = remaining.pop(0)
                futures[executor.submit(_worker, channel)] = channel

            while futures:
                for future in as_completed(futures):
                    channel = futures.pop(future)
                    completed += 1

                    try:
                        channel_result, status = future.result()
                        result["successful"].extend(
                            channel_result.get("successful", [])
                        )
                        result["failed"].extend(channel_result.get("failed", []))
                        result["skipped"].extend(channel_result.get("skipped", []))

                        with lock:
                            if status == "✓":
                                ok_count += 1
                            elif status == "⊘":
                                skip_count += 1
                            else:
                                err_count += 1

                    except Exception as e:
                        with lock:
                            err_count += 1
                            result["failed"].append(
                                {"channel": channel, "error": str(e)}
                            )
                        if not continue_on_error:
                            raise

                    # Submit next work
                    if remaining:
                        next_channel = remaining.pop(0)
                        futures[executor.submit(_worker, next_channel)] = next_channel
                        break

        progress.stop()
        return result

    def _process_channels_fzf(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """Process channels with tab-separated output for fzf/awk pipelining.

        Output format per line: status\tchannel\tvideos\ttime\terror
        - status: ok, skip, err
        - channel: channel URL/handle
        - videos: number of videos downloaded
        - time: elapsed time in seconds
        - error: error message (if status=err)
        """
        result = self._make_empty_result()

        if not channels:
            return result

        enable_wal_mode()

        # Pre-filter fresh channels
        if self.freshness_hours > 0 and self.min_saved == 0:
            channels, _skipped = pre_filter_fresh_channels(
                channels=channels,
                freshness_hours=self.freshness_hours,
                min_saved=self.min_saved,
            )

        len(channels)
        remaining = list(channels)
        completed = 0
        threading.Lock()

        # FLATTENED ARCHITECTURE: Create ONE shared BatchDownloader before outer TPE
        # This eliminates nested TPEs. Jobs=1 for sequential video processing.
        shared_downloader = BatchDownloader(
            channels=channels,
            jobs=self.video_jobs,
            language=self.language,
            quota_strategy=self.quota_strategy,
            cookies_from_browser=self.cookies_from_browser,
            delay_between_channels=self.delay_between_channels,
            max_retries=self.max_retries,
            continue_on_error=self.continue_on_error,
            time_per_channel=self.time_per_channel,
            time_per_video=self.time_per_video,
            time_per_batch=self.time_per_batch,
            min_saved=self.min_saved,
            videos_download_per_batch=self.videos_download_per_batch,
            display_plugin=(
                self.display_plugin.get_name() if self.display_plugin else None
            ),
            auto_backfill=self.auto_backfill,
            freshness_hours=self.freshness_hours,
            suppress_quota_print=True,
            suppress_verbose=True,
        )

        def _process_one(channel: str) -> tuple[ProcessResult, str, int, str, float]:
            """Process a single channel with fzf-style output using shared downloader."""
            channel_result = self._make_empty_result()
            import time

            start = time.time()

            # Use shared downloader - no per-worker BatchDownloader creation
            download_result = shared_downloader.process_single_channel(channel)
            elapsed = time.time() - start

            channel_result["successful"].extend(download_result.get("successful", []))
            channel_result["failed"].extend(download_result.get("failed", []))
            channel_result["skipped"].extend(download_result.get("skipped", []))

            # Determine status and count videos
            if download_result.get("successful"):
                status = "ok"
                video_count = sum(
                    len(r.get("videos", []))
                    for r in download_result.get("successful", [])
                )
                error_msg = ""
            elif download_result.get("skipped"):
                status = "skip"
                video_count = 0
                error_msg = ""
            else:
                status = "err"
                video_count = 0
                # Extract first error if available
                failed_list = download_result.get("failed", [])
                error_msg = (
                    failed_list[0].get("error", "unknown")[:100]
                    if failed_list
                    else "unknown"
                )

            return channel_result, status, video_count, error_msg, elapsed

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures: dict[Any, Any] = {}

            while remaining and len(futures) < num_workers:
                channel = remaining.pop(0)
                futures[executor.submit(_process_one, channel)] = channel

            while futures:
                for future in as_completed(futures):
                    channel = futures.pop(future)
                    completed += 1

                    try:
                        channel_result, status, video_count, error_msg, elapsed = (
                            future.result()
                        )
                        result["successful"].extend(
                            channel_result.get("successful", [])
                        )
                        result["failed"].extend(channel_result.get("failed", []))
                        result["skipped"].extend(channel_result.get("skipped", []))

                        # Tab-separated output: status\tchannel\tvideos\ttime\terror
                        print(
                            f"{status}\t{channel}\t{video_count}\t{elapsed:.1f}\t{error_msg}",
                            flush=True,
                        )

                    except Exception as e:
                        result["failed"].append({"channel": channel, "error": str(e)})
                        print(f"err\t{channel}\t0\t0.0\t{str(e)[:100]}", flush=True)
                        if not continue_on_error:
                            raise

                    if remaining:
                        next_channel = remaining.pop(0)
                        futures[executor.submit(_process_one, next_channel)] = (
                            next_channel
                        )
                        break

        return result

    def _process_channels_json(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """Process channels with JSON output.

        Output format: JSON objects per line with:
        - status: "ok", "skip", or "err"
        - channel: channel URL/handle
        - videos: number of videos downloaded
        - time: elapsed time in seconds
        - error: error message (if status="err")
        """
        result = self._make_empty_result()

        if not channels:
            print("[]", flush=True)
            return result

        enable_wal_mode()

        # Pre-filter fresh channels
        if self.freshness_hours > 0 and self.min_saved == 0:
            channels, _skipped = pre_filter_fresh_channels(
                channels=channels,
                freshness_hours=self.freshness_hours,
                min_saved=self.min_saved,
            )

        if not channels:
            print("[]", flush=True)
            return result

        import json
        import time

        remaining = list(channels)
        threading.Lock()

        # FLATTENED ARCHITECTURE: Create ONE shared BatchDownloader before outer TPE
        # This eliminates nested TPEs. Jobs=1 for sequential video processing.
        shared_downloader = BatchDownloader(
            channels=channels,
            jobs=self.video_jobs,
            language=self.language,
            quota_strategy=self.quota_strategy,
            cookies_from_browser=self.cookies_from_browser,
            delay_between_channels=self.delay_between_channels,
            max_retries=self.max_retries,
            continue_on_error=self.continue_on_error,
            time_per_channel=self.time_per_channel,
            time_per_video=self.time_per_video,
            time_per_batch=self.time_per_batch,
            min_saved=self.min_saved,
            videos_download_per_batch=self.videos_download_per_batch,
            display_plugin=(
                self.display_plugin.get_name() if self.display_plugin else None
            ),
            auto_backfill=self.auto_backfill,
            freshness_hours=self.freshness_hours,
            suppress_quota_print=True,
            suppress_verbose=True,
        )

        def _process_one(channel: str) -> tuple[Any, ...]:
            """Process a single channel with JSON output using shared downloader."""
            channel_result = self._make_empty_result()
            start = time.time()

            # Use shared downloader - no per-worker BatchDownloader creation
            download_result = shared_downloader.process_single_channel(channel)
            elapsed = time.time() - start

            channel_result["successful"].extend(download_result.get("successful", []))
            channel_result["failed"].extend(download_result.get("failed", []))
            channel_result["skipped"].extend(download_result.get("skipped", []))

            # Determine status and count videos
            if download_result.get("successful"):
                status = "ok"
                video_count = sum(
                    len(r.get("videos", []))
                    for r in download_result.get("successful", [])
                )
                error_msg = ""
            elif download_result.get("skipped"):
                status = "skip"
                video_count = 0
                error_msg = ""
            else:
                status = "err"
                video_count = 0
                failed_list = download_result.get("failed", [])
                error_msg = (
                    failed_list[0].get("error", "unknown")[:200]
                    if failed_list
                    else "unknown"
                )

            return channel_result, status, video_count, elapsed, error_msg

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures: dict[Any, Any] = {}

            while remaining and len(futures) < num_workers:
                channel = remaining.pop(0)
                futures[executor.submit(_process_one, channel)] = channel

            while futures:
                for future in as_completed(futures):
                    channel = futures.pop(future)

                    try:
                        channel_result, status, video_count, elapsed, error_msg = (
                            future.result()
                        )
                        result["successful"].extend(
                            channel_result.get("successful", [])
                        )
                        result["failed"].extend(channel_result.get("failed", []))
                        result["skipped"].extend(channel_result.get("skipped", []))

                        # Output JSON for this channel
                        result_obj = {
                            "status": status,
                            "channel": channel,
                            "videos": video_count,
                            "time": round(elapsed, 2),
                            "error": error_msg if error_msg else None,
                        }
                        print(json.dumps(result_obj), flush=True)

                        # Notify rate limit tracker (convert status to emoji format)
                        emoji_status = {"ok": "✓", "skip": "⊘", "err": "✗"}.get(
                            status, "✗"
                        )
                        emoji_result = {
                            "successful": channel_result.get("successful", []),
                            "failed": channel_result.get("failed", []),
                            "skipped": channel_result.get("skipped", []),
                        }
                        self._notify_channel_completion(
                            channel, emoji_result, emoji_status
                        )

                    except Exception as e:
                        result["failed"].append({"channel": channel, "error": str(e)})
                        result_obj = {
                            "status": "err",
                            "channel": channel,
                            "videos": 0,
                            "time": 0.0,
                            "error": str(e)[:200],
                        }
                        print(json.dumps(result_obj), flush=True)
                        if not continue_on_error:
                            raise

                    if remaining:
                        next_channel = remaining.pop(0)
                        futures[executor.submit(_process_one, next_channel)] = (
                            next_channel
                        )
                        break

        return result

    def _process_channels_simple(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """
        Process multiple channels in parallel with simple progress display.

        FLATTENED ARCHITECTURE: Creates a single shared BatchDownloader instance
        instead of creating a new one for each channel. This reduces overhead
        (no per-worker RSS checker, quota strategy, DB connections).

        Args:
            channels: List of channel URLs/handles
            num_workers: Number of parallel workers
            continue_on_error: Continue processing if a worker fails

        Returns:
            ProcessResult dict with successful, failed, and skipped channels
        """
        result = self._make_empty_result()

        # Handle empty channel list
        if not channels:
            return result

        # Enable WAL mode for better concurrent access
        enable_wal_mode()

        # BATCH OPTIMIZATION: Pre-filter fresh channels
        # Uses Channels table lookup + simple URL parsing (no API calls)
        if self.freshness_hours > 0 and self.min_saved == 0:
            channels, _skipped = pre_filter_fresh_channels(
                channels=channels,
                freshness_hours=self.freshness_hours,
                min_saved=self.min_saved,
            )

        total = len(channels)
        remaining = list(channels)
        completed = 0
        ok_count = 0
        err_count = 0
        skip_count = 0
        lock = threading.Lock()

        # ETA tracking
        import time

        batch_start = time.time()

        # Show initial quota status (once, not per-worker)
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        api_backfill = YouTubeAPIBackfill()
        display_name = (
            self.display_plugin.get_name() if self.display_plugin else "default"
        )
        print(
            f"📊 Quota: {api_backfill.format_quota_display()} | Display: {display_name}",
            flush=True,
        )

        # Immediate feedback
        _log("INFO", "START", f"Initializing {num_workers} worker threads...")

        # Print initial status
        display_name = (
            self.display_plugin.get_name() if self.display_plugin else "default"
        )
        print(
            f"🧵 [{num_workers} workers] Display: {display_name} | Processing {total} channels...",
            flush=True,
        )

        # FLATTENED ARCHITECTURE: Create ONE shared BatchDownloader instance
        # This instance will be reused by all worker threads
        shared_downloader = BatchDownloader(
            channels=channels,  # Pass all channels for batch-level setup
            jobs=self.video_jobs,  # Single job per channel since we're already parallelizing channels
            language=self.language,
            quota_strategy=self.quota_strategy,  # Shared quota tracking
            cookies_from_browser=self.cookies_from_browser,
            delay_between_channels=self.delay_between_channels,
            max_retries=self.max_retries,
            continue_on_error=self.continue_on_error,
            time_per_channel=self.time_per_channel,
            time_per_video=self.time_per_video,
            time_per_batch=self.time_per_batch,
            min_saved=self.min_saved,
            videos_download_per_batch=self.videos_download_per_batch,
            display_plugin=(
                self.display_plugin.get_name() if self.display_plugin else None
            ),
            auto_backfill=self.auto_backfill,
            freshness_hours=self.freshness_hours,
            suppress_quota_print=True,
            suppress_verbose=not bool(self.display_plugin),
        )

        def _process_one(channel: str) -> tuple[ProcessResult, str]:
            """Process a single channel in a worker thread using shared downloader.

            Returns:
                Tuple of (result_dict, status_string)
            """
            # Show start of processing (timestamped)
            short_channel = _formatter.shorten_channel(channel)
            _log("INFO", "PROCESS", f"Starting {short_channel}")
            print(f"[DEBUG] ParallelProcessor worker started: {channel}")

            # Track timing
            start = time.time()

            # Use shared downloader to process this single channel
            download_result = shared_downloader.process_single_channel(channel)

            time.time() - start

            channel_result = self._make_empty_result()
            channel_result["successful"].extend(download_result.get("successful", []))
            channel_result["failed"].extend(download_result.get("failed", []))
            channel_result["skipped"].extend(download_result.get("skipped", []))

            # Determine status
            if download_result.get("successful"):
                status = "✓"
            elif download_result.get("skipped"):
                status = "⊘"
            else:
                status = "✗"

            return channel_result, status

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures: dict[Any, Any] = {}

            # Submit initial work
            while remaining and len(futures) < num_workers:
                channel = remaining.pop(0)
                futures[executor.submit(_process_one, channel)] = channel

            # Process as work completes
            while futures:
                for future in as_completed(futures):
                    channel = futures.pop(future)
                    completed += 1

                    try:
                        channel_result, status = future.result()
                        result["successful"].extend(
                            channel_result.get("successful", [])
                        )
                        result["failed"].extend(channel_result.get("failed", []))
                        result["skipped"].extend(channel_result.get("skipped", []))

                        with lock:
                            if status == "✓":
                                ok_count += 1
                            elif status == "⊘":
                                skip_count += 1
                            else:
                                err_count += 1

                        # Calculate ETA
                        elapsed = time.time() - batch_start
                        if completed >= 3:  # Need some samples for stable ETA
                            avg_time = elapsed / completed
                            remaining_chs = total - completed
                            eta_seconds = avg_time * remaining_chs
                            eta_str = _format_eta(eta_seconds)
                            progress_line = f"  {status} [{completed}/{total}] ETA {eta_str} {channel[:40]}..."
                        else:
                            progress_line = (
                                f"  {status} [{completed}/{total}] {channel[:40]}..."
                            )
                        print(progress_line, flush=True)

                    except Exception as e:
                        import traceback

                        # Print full traceback for database lock debugging
                        if "database is locked" in str(e).lower():
                            print("  [DEBUG] Database lock traceback:", flush=True)
                            traceback.print_exc()
                        with lock:
                            err_count += 1
                        elapsed = time.time() - batch_start
                        if completed >= 3:
                            avg_time = elapsed / completed
                            eta_seconds = avg_time * (total - completed)
                            eta_str = _format_eta(eta_seconds)
                            print(
                                f"  ✗ [{completed}/{total}] ETA {eta_str} {channel[:30]}... - {str(e)[:30]}",
                                flush=True,
                            )
                        else:
                            print(
                                f"  ✗ [{completed}/{total}] {channel[:30]}... - {str(e)[:30]}",
                                flush=True,
                            )
                        if continue_on_error:
                            result["failed"].append(
                                {"channel": channel, "error": str(e)}
                            )
                        else:
                            raise

                    # Submit next work if available
                    if remaining:
                        next_channel = remaining.pop(0)
                        futures[executor.submit(_process_one, next_channel)] = (
                            next_channel
                        )
                        break

        # Print summary
        print(
            f"\n✓ Complete: {ok_count} ok, {err_count} err, {skip_count} skip",
            flush=True,
        )

        return result
