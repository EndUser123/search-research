"""
Rich Progress Display for Parallel Channel Processing.

Provides two display modes:
1. Progress bars - Stacked progress bars with ETA per channel
2. Live table - Structured data view with real-time updates

Thread-safe - Multiple workers update simultaneously without conflicts.
"""
from __future__ import annotations

import sys
import threading
import time
from .thread_safe_manager import ThreadSafeManager
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

# Try importing Rich - handle both direct and module imports
RICH_AVAILABLE = False
_console_cls: Any = None
_live_cls: Any = None
_progress_cls: Any = None
_table_cls: Any = None
_taskid_cls: Any = None
_bar_column_cls: Any = None
_spinner_column_cls: Any = None
_text_column_cls: Any = None
_time_remaining_column_cls: Any = None


try:
    # Try direct import first
    from rich.console import Console as ConsoleClass
    from rich.live import Live as LiveClass
    from rich.progress import (
        BarColumn as BarColumnClass,
    )
    from rich.progress import (
        Progress as ProgressClass,
    )
    from rich.progress import (
        SpinnerColumn as SpinnerColumnClass,
    )
    from rich.progress import (
        TaskID as TaskIDClass,
    )
    from rich.progress import (
        TextColumn as TextColumnClass,
    )
    from rich.progress import (
        TimeRemainingColumn as TimeRemainingColumnClass,
    )
    from rich.table import Table as TableClass

    RICH_AVAILABLE = True
    _console_cls = ConsoleClass
    _live_cls = LiveClass
    _progress_cls = ProgressClass
    _table_cls = TableClass
    _taskid_cls = TaskIDClass
    _bar_column_cls = BarColumnClass
    _spinner_column_cls = SpinnerColumnClass
    _text_column_cls = TextColumnClass
    _time_remaining_column_cls = TimeRemainingColumnClass
except ImportError:
    RICH_AVAILABLE = False


@dataclass(slots=True)
class ChannelProgress:
    """Track progress for a single channel."""

    channel_name: str
    channel_id: str = ""
    total_estimated: int = 0  # Estimated total videos (from API)
    completed: int = 0  # Videos fetched so far
    status: str = "pending"  # pending, fetching, complete, error
    start_time: float = field(default_factory=time.time)
    last_update: float = field(default_factory=time.time)
    error_message: str = ""

    @property
    def elapsed(self) -> float:
        """Elapsed time in seconds."""
        return time.time() - self.start_time

    @property
    def percent_complete(self) -> float:
        """Percentage complete (0-100)."""
        if self.total_estimated > 0:
            return min(100, (self.completed / self.total_estimated) * 100)
        return 0

    @property
    def eta(self) -> str:
        """Estimated time remaining as formatted string."""
        if self.total_estimated > 0 and self.completed > 0:
            remaining = self.total_estimated - self.completed
            rate = self.completed / self.elapsed if self.elapsed > 0 else 1
            eta_seconds = remaining / rate if rate > 0 else 0
            return _format_timedelta(eta_seconds)
        return "--:--:--"

    @property
    def elapsed_str(self) -> str:
        """Elapsed time as formatted string."""
        return _format_timedelta(self.elapsed)


def _format_timedelta(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        return "--:--:--"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _shorten_channel_name(name: str, max_len: int = 35) -> str:
    """Shorten channel name for display."""
    if len(name) <= max_len:
        return name.ljust(max_len)
    return name[:max_len-3] + "..."


class RichParallelProgress:
    """
    Rich Progress display for parallel channel processing.

    Shows stacked progress bars with real-time updates, ETA, and status.

    Example:
        progress = RichParallelProgress()
        progress.start()

        # For each channel, add a task
        task_id = progress.add_channel("Channel Name", estimated_total=100)

        # Update progress from worker threads
        progress.update(task_id, completed=50)

        # Mark complete
        progress.complete(task_id)

        progress.stop()
    """

    def __init__(self, console: Any = None):
        """Initialize Rich progress display.

        Args:
            console: Rich console (uses default if None)
        """
        if not RICH_AVAILABLE:
            msg = "Rich is not installed. Run: pip install rich"
            raise RuntimeError(msg)

        self.console = console or _console_cls(stderr=True)
        self.progress: Any = None
        self.live: Any = None
        self.tasks: dict[str, Any] = {}  # channel -> TaskID
        self.channel_data: dict[str, ChannelProgress] = {}
        self._tsm = ThreadSafeManager()
        self._active = False
        self._display_thread = None
        self._display_mode = "progress"  # "progress" or "table"

    def start(self, display_mode: str = "progress") -> None:
        """Start the progress display.

        Args:
            display_mode: "progress" for stacked bars, "table" for table view
        """
        self._display_mode = display_mode
        self._active = True

        if display_mode == "progress":
            self._start_progress_bars()
        else:
            self._start_live_table()

    def _start_progress_bars(self) -> None:
        """Start stacked progress bars display."""
        self.progress = _progress_cls(
            _spinner_column_cls(),
            _text_column_cls("[bold blue]{task.description}"),
            _bar_column_cls(bar_width=30),
            _text_column_cls("[progress.percentage]{task.percentage:>3.0f}%"),
            _text_column_cls("({task.completed}/{task.total})"),
            _time_remaining_column_cls(),
            _text_column_cls("{task.fields[status]}"),
            console=self.console,
            expand=False,
        )
        self.live = _live_cls(self.progress, console=self.console, refresh_per_second=4)
        self.live.start()

    def _start_live_table(self) -> None:
        """Start live table display."""
        self.live = _live_cls(self._generate_table(), console=self.console, refresh_per_second=4)
        self.live.start()

    def _generate_table(self) -> Any:
        """Generate the live table from current channel data."""
        table = _table_cls(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Channel", width=35)
        table.add_column("Progress", width=30)
        table.add_column("Videos", width=12)
        table.add_column("Elapsed", width=8)
        table.add_column("ETA", width=8)
        table.add_column("Status", width=10)

        with self._tsm.get_lock("RichParallelProgress"):
            sorted_channels = sorted(
                self.channel_data.items(),
                key=lambda x: (x[1].status != "complete", x[1].start_time)
            )

            for _channel_id, data in sorted_channels:
                name = _shorten_channel_name(data.channel_name)
                percent = data.percent_complete

                # Progress bar
                filled = int(30 * percent / 100)
                bar = "█" * filled + "░" * (30 - filled)

                # Status indicator
                status_map = {
                    "pending": "[dim]pending[/dim]",
                    "fetching": "[blue]fetching[/blue]",
                    "complete": "[green]✓[/green]",
                    "error": "[red]✗[/red]",
                }
                status = status_map.get(data.status, data.status)

                table.add_row(
                    name,
                    f"{bar} {percent:.0f}%",
                    f"{data.completed:,}/{data.total_estimated:,}" if data.total_estimated > 0 else f"{data.completed:,}",
                    data.elapsed_str,
                    data.eta if data.status == "fetching" else "--:--:--",
                    status,
                )

        return table

    def add_channel(self, channel_name: str, channel_id: str = "", estimated_total: int = 0) -> str:
        """Add a channel to track.

        Args:
            channel_name: Display name for the channel
            channel_id: Unique ID (defaults to channel_name if not provided)
            estimated_total: Estimated total videos to fetch

        Returns:
            Task ID for updates
        """
        if not channel_id:
            channel_id = channel_name

        with self._tsm.get_lock("RichParallelProgress"):
            task_key = channel_id
            self.channel_data[task_key] = ChannelProgress(
                channel_name=channel_name,
                channel_id=channel_id,
                total_estimated=estimated_total,
            )

            if self._display_mode == "progress" and self.progress:
                task_id: Any = self.progress.add_task(
                    _shorten_channel_name(channel_name, 40),
                    total=estimated_total if estimated_total > 0 else 100,
                    completed=0,
                    status="[dim]pending[/dim]",
                )
                self.tasks[task_key] = task_id

            return task_key

    def update(self, task_key: str, completed: int | None = None, total: int | None = None, status: str | None = None) -> None:
        """Update progress for a channel.

        Thread-safe - can be called from worker threads.

        Args:
            task_key: Channel ID returned by add_channel()
            completed: Current completed count (advances by 1 if None)
            total: Update estimated total
            status: New status (pending, fetching, complete, error)
        """
        with self._tsm.get_lock("RichParallelProgress"):
            data = self.channel_data.get(task_key)
            if not data:
                return

            if completed is not None:
                data.completed = completed
            else:
                data.completed += 1

            if total is not None:
                data.total_estimated = total

            if status is not None:
                data.status = status
            elif data.completed > 0 and data.status == "pending":
                data.status = "fetching"

            data.last_update = time.time()

            # Update Rich progress bar
            if self._display_mode == "progress" and self.progress and task_key in self.tasks:
                task_id = self.tasks[task_key]
                status_display = {
                    "pending": "[dim]pending[/dim]",
                    "fetching": "[blue]fetching[/blue]",
                    "complete": "[green]✓[/green]",
                    "error": "[red]✗[/red]",
                }.get(data.status, data.status)

                self.progress and self.progress.update(
                    task_id,
                    completed=data.completed,
                    total=data.total_estimated if data.total_estimated > 0 else 100,
                    description=_shorten_channel_name(data.channel_name, 40),
                    status=status_display,
                )

            # Update table display
            elif self._display_mode == "table" and self.live:
                self.live and self.live.update(self._generate_table())

    def set_error(self, task_key: str, error_message: str) -> None:
        """Mark a channel as failed with error message.

        Args:
            task_key: Channel ID
            error_message: Error description
        """
        with self._tsm.get_lock("RichParallelProgress"):
            data = self.channel_data.get(task_key)
            if data:
                data.status = "error"
                data.error_message = error_message
                self.update(task_key, status="error")

    def complete(self, task_key: str, final_count: int | None = None) -> None:
        """Mark a channel as complete.

        Args:
            task_key: Channel ID
            final_count: Final completed count (uses current if None)
        """
        with self._tsm.get_lock("RichParallelProgress"):
            data = self.channel_data.get(task_key)
            if data:
                if final_count is not None:
                    data.completed = final_count
                data.status = "complete"
                self.update(task_key, status="complete")

    def stop(self) -> None:
        """Stop the progress display and show final summary."""
        self._active = False

        if self.live:
            if self._display_mode == "table":
                self.live and self.live.update(self._generate_table())
            self.live and self.live.stop()

        # Print summary
        with self._tsm.get_lock("RichParallelProgress"):
            complete = sum(1 for d in self.channel_data.values() if d.status == "complete")
            error = sum(1 for d in self.channel_data.values() if d.status == "error")
            total = len(self.channel_data)

            self.console.print(f"\n[bold]Summary:[/bold] {complete} complete, {error} failed, {total} total")

    def get_progress_callback(self, task_key: str) -> Callable[[int], None]:
        """Get a callback function for progress updates.

        Useful for passing to functions that expect a progress callback.

        Args:
            task_key: Channel ID

        Returns:
            Callback function that accepts completed count
        """
        def callback(completed: int) -> None:
            self.update(task_key, completed=completed)
        return callback


def run_with_progress_bars(
    channels: list[str],
    worker_func: Callable[[str, RichParallelProgress], dict[str, Any]],
    num_workers: int = 4,
) -> dict[str, list[Any]]:
    """
    Run parallel processing with Rich progress bars display.

    Args:
        channels: List of channel URLs/handles
        worker_func: Function that processes a channel, receives (channel, progress)
        num_workers: Number of parallel workers

    Returns:
        Combined results from all workers
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    progress = RichParallelProgress()
    progress.start(display_mode="progress")

    results: dict[str, list[Any]] = {"successful": [], "failed": [], "skipped": []}

    def _worker(channel: str) -> tuple[str, str, dict[str, Any]]:
        task_key = progress.add_channel(channel, channel, estimated_total=0)
        try:
            progress.update(task_key, status="fetching")
            result = worker_func(channel, progress)
            progress.complete(task_key)
            return "success", channel, result
        except Exception as e:
            progress.set_error(task_key, str(e))
            return "error", channel, {"error": str(e)}

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(_worker, ch): ch for ch in channels}

        for future in as_completed(futures):
            status, _channel, result = future.result()
            if status == "success":
                results["successful"].append(result)
            else:
                results["failed"].append(result)

    progress.stop()
    return results


def run_with_live_update(
    channels: list[str],
    worker_func: Callable[[str, RichParallelProgress], dict[str, Any]],
    num_workers: int = 4,
) -> dict[str, list[Any]]:
    """
    Run parallel processing with Rich live table display.

    Args:
        channels: List of channel URLs/handles
        worker_func: Function that processes a channel, receives (channel, progress)
        num_workers: Number of parallel workers

    Returns:
        Combined results from all workers
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    progress = RichParallelProgress()
    progress.start(display_mode="table")

    results: dict[str, list[Any]] = {"successful": [], "failed": [], "skipped": []}

    def _worker(channel: str) -> tuple[str, str, dict[str, Any]]:
        task_key = progress.add_channel(channel, channel, estimated_total=0)
        try:
            progress.update(task_key, status="fetching")
            result = worker_func(channel, progress)
            progress.complete(task_key)
            return "success", channel, result
        except Exception as e:
            progress.set_error(task_key, str(e))
            return "error", channel, {"error": str(e)}

    with ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = {executor.submit(_worker, ch): ch for ch in channels}

        for future in as_completed(futures):
            status, _channel, result = future.result()
            if status == "success":
                results["successful"].append(result)
            else:
                results["failed"].append(result)

    progress.stop()
    return results


# Simple fallback if Rich is not available
class FallbackProgress:
    """Fallback progress display when Rich is not available."""

    def __init__(self) -> None:
        self.channel_data: dict[str, ChannelProgress] = {}
        self._tsm = ThreadSafeManager()

    def add_channel(self, channel_name: str, channel_id: str = "", estimated_total: int = 0) -> str:
        if not channel_id:
            channel_id = channel_name
        with self._tsm.get_lock("FallbackProgress"):
            self.channel_data[channel_id] = ChannelProgress(
                channel_name=channel_name,
                channel_id=channel_id,
                total_estimated=estimated_total,
            )
        return channel_id

    def update(self, task_key: str, completed: int | None = None, total: int | None = None, status: str | None = None) -> None:
        with self._tsm.get_lock("RichParallelProgress"):
            data = self.channel_data.get(task_key)
            if not data:
                return
            if completed is not None:
                data.completed = completed
            else:
                data.completed += 1
            if total is not None:
                data.total_estimated = total
            if status is not None:
                data.status = status

            # Print simple update
            name = data.channel_name[:30]
            print(f"\r{name:30} {data.completed:5}/{data.total_estimated or '?':5} videos", end="", file=sys.stderr, flush=True)

    def set_error(self, task_key: str, error_message: str) -> None:
        self.update(task_key, status="error")

    def complete(self, task_key: str, final_count: int | None = None) -> None:
        with self._tsm.get_lock("RichParallelProgress"):
            data = self.channel_data.get(task_key)
            if data:
                data.status = "complete"
                name = data.channel_name[:30]
                print(f"\r{name:30} ✓ {data.completed} videos complete", file=sys.stderr)

    def start(self, display_mode: str = "progress") -> None:
        pass

    def stop(self) -> None:
        print(file=sys.stderr)

    def get_progress_callback(self, task_key: str) -> Callable[[int], None]:
        def callback(completed: int) -> None:
            self.update(task_key, completed=completed)
        return callback
