"""
Per-worker progress tracking for parallel download operations.

Provides Rich progress bar management for individual worker threads,
showing real-time download progress (bytes, speed, ETA) for each worker.
"""
import threading
import time
from contextlib import suppress
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, TextColumn
from rich.table import Column


class WorkerProgressTracker:
    """
    Thread-safe per-worker progress tracking for Rich display.

    Shows progress bars for all workers, even when idle.
    """

    def __init__(self, console: Console, max_workers: int) -> None:
        """
        Initialize worker progress tracker.

        Args:
            console: Rich console instance
            max_workers: Maximum number of parallel workers
        """
        self.console = console
        self.max_workers = max_workers

        # Rich Progress instance with columns for worker, bar, speed, ETA
        self.progress = Progress(
            TextColumn("{task.description}"),
            BarColumn(bar_width=15),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("{task.fields[speed]}", table_column=Column(width=12)),
            TextColumn("{task.fields[eta]}", table_column=Column(width=8)),
            console=console,
            expand=False,
            refresh_per_second=10,
        )

        # Map worker_id to Rich task_id
        self.worker_tasks: dict[int, Any] = {}

        # Thread-safe lock for updates
        self.lock = threading.Lock()

        # Track start time for ETA calculation
        self.start_time: float = time.time()

        # Track completion status
        self._finished = False

    def __enter__(self) -> "WorkerProgressTracker":
        """Enter context manager and start progress display."""
        self.progress.__enter__()
        self._initialize_all_workers()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit context manager and stop progress display."""
        self._finished = True
        with suppress(Exception):
            self.progress.__exit__(exc_type, exc_val, exc_tb)

    def _initialize_all_workers(self) -> None:
        """Create progress bars for all workers upfront (detailed mode)."""
        for worker_id in range(self.max_workers):
            description = f"Worker {worker_id + 1} [Waiting...]"
            task_id = self.progress.add_task(
                description,
                total=100,
                completed=0,
                visible=True,
                speed="",
                eta="",
            )
            self.worker_tasks[worker_id] = task_id

    def register_worker(self, worker_id: int, video_id: str) -> None:
        """
        Assign a video to a worker and update its description.

        Args:
            worker_id: Worker index (0-based)
            video_id: YouTube video ID being downloaded
        """
        if worker_id not in self.worker_tasks:
            return

        # Shorten video_id for display
        video_short = video_id[:8] if len(video_id) > 8 else video_id
        description = f"Worker {worker_id + 1} [{video_short}]"

        with self.lock:
            self.progress.update(
                self.worker_tasks[worker_id],
                description=description,
                completed=0,
            )

    def update_worker_progress(
        self,
        worker_id: int,
        downloaded_bytes: int,
        total_bytes: int,
        speed: float,
        eta: int | None,
    ) -> None:
        """
        Thread-safe progress update for a worker.

        Args:
            worker_id: Worker index (0-based)
            downloaded_bytes: Bytes downloaded so far
            total_bytes: Total file size in bytes
            speed: Download speed in bytes/second
            eta: Estimated time remaining in seconds
        """
        if worker_id not in self.worker_tasks:
            return

        # Calculate percentage
        if total_bytes > 0:
            percentage = min(100, (downloaded_bytes / total_bytes) * 100)
        else:
            percentage = 0

        # Format speed (bytes/sec -> human readable)
        speed_str = self._format_bytes(speed) + "/s" if speed > 0 else ""

        # Format ETA
        if eta is not None and eta >= 0:
            eta_str = self._format_eta(eta)
        else:
            eta_str = "calculating"

        with self.lock:
            self.progress.update(
                self.worker_tasks[worker_id],
                completed=percentage,
                speed=speed_str,
                eta=eta_str,
            )

    def finish_worker(self, worker_id: int, success: bool) -> None:
        """
        Mark a worker as complete or failed.

        Args:
            worker_id: Worker index (0-based)
            success: True if download succeeded, False if failed
        """
        if worker_id not in self.worker_tasks:
            return

        with self.lock:
            if success:
                # Show completed status
                self.progress.update(
                    self.worker_tasks[worker_id],
                    completed=100,
                    speed="✓",
                    eta="Done",
                )
            else:
                # Show failed status
                self.progress.update(
                    self.worker_tasks[worker_id],
                    speed="✗",
                    eta="Failed",
                )

    def reset_worker(self, worker_id: int) -> None:
        """
        Reset a worker back to waiting state.

        Args:
            worker_id: Worker index (0-based)
        """
        if worker_id not in self.worker_tasks:
            return

        description = f"Worker {worker_id + 1} [Waiting...]"

        with self.lock:
            self.progress.update(
                self.worker_tasks[worker_id],
                description=description,
                completed=0,
                speed="",
                eta="",
            )

    @staticmethod
    def _format_bytes(byte_count: float) -> str:
        """Format bytes as human-readable string (e.g., '2.3MB')."""
        for unit in ["B", "KB", "MB", "GB"]:
            if byte_count < 1024.0:
                return f"{byte_count:.1f}{unit}"
            byte_count /= 1024.0
        return f"{byte_count:.1f}TB"

    @staticmethod
    def _format_eta(seconds: float) -> str:
        """Format ETA as human-readable string."""
        if seconds < 60:
            return f"{int(seconds)}s"
        if seconds < 3600:
            minutes = int(seconds / 60)
            secs = int(seconds % 60)
            return f"{minutes}m {secs}s"
        hours = int(seconds / 3600)
        minutes = int((seconds % 3600) / 60)
        return f"{hours}h {minutes}m"

    def cleanup(self) -> None:
        """Clean up progress bar resources."""
        if self.progress is not None:
            with suppress(Exception):
                self.progress.__exit__(None, None, None)
