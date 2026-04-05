import pathlib
content = r"""
"""
Parallel batch processor for downloading multiple YouTube channels concurrently.
"""

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import TypedDict

from rich.console import Console
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TaskID

from ..core.database import enable_wal_mode
from .batch_downloader import BatchDownloader


class WorkerStatus:
    """Thread-safe status tracker for parallel workers."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._completed = 0
        self._failed = 0
        self._current: dict[int, str] = {}

    def start_channel(self, worker_id: int, channel: str) -> None:
        with self._lock:
            self._current[worker_id] = channel

    def complete_channel(self, worker_id: int) -> None:
        with self._lock:
            self._completed += 1
            self._current.pop(worker_id, None)

    def fail_channel(self, worker_id: int) -> None:
        with self._lock:
            self._failed += 1
            self._current.pop(worker_id, None)

    @property
    def stats(self) -> tuple[int, int, dict[int, str]]:
        with self._lock:
            return self._completed, self._failed, dict(self._current)


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
    - Real-time progress display with Rich
    - Graceful error handling with continue-on-error support
    - WAL mode enabled for better concurrent database access
    - Disables inner parallelism (ThreadPoolExecutor) since outer parallelism handles concurrency
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
        display_plugin: str | None = None,
        auto_backfill: bool = False,
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
            display_plugin: Display plugin to use
            auto_backfill: Auto-backfill metadata after downloads
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
        self._console = Console()

    def _make_empty_result(self) -> ProcessResult:
        """Create an empty result dict with proper structure.

        Returns:
            ProcessResult with empty lists
        """
        return {"successful": [], "failed": [], "skipped": []}

    def _process_single_channel(
        self,
        channel: str,
        worker_id: int,
        status: WorkerStatus,
    ) -> ProcessResult:
        """Process a single channel.

        Args:
            channel: Channel URL/handle
            worker_id: Worker thread ID
            status: Shared status tracker

        Returns:
            ProcessResult for this channel
        """
        channel_result = self._make_empty_result()
        status.start_channel(worker_id, channel)

        try:
            downloader = BatchDownloader(
                channels=[channel],
                jobs=1,
                language=self.language,
                cookies_from_browser=self.cookies_from_browser,
                delay_between_channels=0,
                max_retries=self.max_retries,
                continue_on_error=self.continue_on_error,
                time_per_channel=self.time_per_channel,
                time_per_video=self.time_per_video,
                time_per_batch=self.time_per_batch,
                min_saved=self.min_saved,
                videos_download_per_batch=self.videos_download_per_batch,
                display_plugin=self.display_plugin,
                auto_backfill=self.auto_backfill,
            )

            download_result = downloader.download_all()
            channel_result["successful"].extend(download_result.get("successful", []))
            channel_result["failed"].extend(download_result.get("failed", []))
            channel_result["skipped"].extend(download_result.get("skipped", []))

            if download_result.get("failed"):
                status.fail_channel(worker_id)
            else:
                status.complete_channel(worker_id)

        except Exception as e:
            channel_result["failed"].append({"channel": channel, "error": str(e)})
            status.fail_channel(worker_id)

        return channel_result

    def process_channels(
        self,
        channels: list[str],
        num_workers: int = 2,
        continue_on_error: bool = False,
    ) -> ProcessResult:
        """
        Process multiple channels in parallel with real-time progress display.

        Args:
            channels: List of channel URLs/handles
            num_workers: Number of parallel workers
            continue_on_error: Continue processing if a worker fails

        Returns:
            ProcessResult dict with successful, failed, and skipped channels
        """
        result = self._make_empty_result()

        if not channels:
            return result

        enable_wal_mode()

        total_channels = len(channels)
        status = WorkerStatus()

        self._console.print(
            f"[bold cyan]Parallel Mode:[/] {num_workers} workers, {total_channels} channels"
        )

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            console=self._console,
            transient=False,
        ) as progress:
            task_id: TaskID = progress.add_task(
                "[cyan]Processing channels...", total=total_channels
            )

            with ThreadPoolExecutor(max_workers=num_workers) as executor:
                future_to_channel = {
                    executor.submit(
                        self._process_single_channel, channel, i % num_workers, status
                    ): channel
                    for i, channel in enumerate(channels)
                }

                for future in as_completed(future_to_channel):
                    channel = future_to_channel[future]
                    try:
                        channel_result = future.result()
                        result["successful"].extend(channel_result.get("successful", []))
                        result["failed"].extend(channel_result.get("failed", []))
                        result["skipped"].extend(channel_result.get("skipped", []))
                    except Exception as e:
                        if continue_on_error:
                            result["failed"].append({"channel": channel, "error": str(e)})
                        else:
                            raise

                    completed, failed, current = status.stats
                    progress.update(task_id, completed=completed + failed)

                    active_str = ", ".join(
                        f"W{w}:{c[:20]}" for w, c in sorted(current.items())
                    )
                    if active_str:
                        progress.update(
                            task_id,
                            description=f"[cyan]Active: {active_str}",
                        )

        completed, failed, _ = status.stats
        self._console.print(
            f"[bold green]Complete:[/] {completed} successful, {failed} failed"
        )

        return result
"""
pathlib.Path(r'P:/projects/yt-fts/src/yt_fts/download/parallel_processor.py').write_text(content)
print('File written successfully')
