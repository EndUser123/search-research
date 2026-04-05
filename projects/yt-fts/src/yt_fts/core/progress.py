"""
Unified Progress Display System for yt-fts.

Provides a consistent progress interface across all commands with:
- Rich progress bars and tables when Rich is available
- Fallback to simple console output when Rich is not installed
- Thread-safe operations for parallel processing
"""
from __future__ import annotations

import sys
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

# Try importing Rich - handle gracefully if not available
RICH_AVAILABLE = False
Console: Any = None
Progress: Any = None
BarColumn: Any = None
SpinnerColumn: Any = None
TextColumn: Any = None
TimeRemainingColumn: Any = None
TaskID: Any = None
Live: Any = None
Table: Any = None

try:
    from rich.console import Console
    from rich.live import Live
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TaskID,
        TextColumn,
        TimeRemainingColumn,
    )
    from rich.table import Table
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False
    Console = None
    Live = None
    Progress = None
    Table = None


def _format_timedelta(seconds: float) -> str:
    """Format seconds as HH:MM:SS."""
    if seconds < 0:
        return "--:--:--"
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def _shorten_string(s: str, max_len: int = 35) -> str:
    """Shorten string for display."""
    if len(s) <= max_len:
        return s
    return s[:max_len - 3] + "..."


@dataclass
class TaskProgress:
    """Track progress for a single task."""

    name: str
    total: int = 0
    completed: int = 0
    status: str = "pending"  # pending, running, complete, error
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
        if self.total > 0:
            return min(100, (self.completed / self.total) * 100)
        return 0

    @property
    def eta(self) -> str:
        """Estimated time remaining as formatted string."""
        if self.total > 0 and self.completed > 0:
            remaining = self.total - self.completed
            rate = self.completed / self.elapsed if self.elapsed > 0 else 1
            eta_seconds = remaining / rate if rate > 0 else 0
            return _format_timedelta(eta_seconds)
        return "--:--:--"


class UnifiedProgress:
    """
    Unified progress display for yt-fts commands.

    Supports multiple display modes:
    - "bar": Rich progress bar (default when Rich available)
    - "table": Rich live table view
    - "simple": Simple text output (fallback or when Rich disabled)

    Example:
        progress = UnifiedProgress(use_rich=True, display_mode="bar")
        progress.start()

        task_id = progress.add_task("Processing videos", total=100)
        for i in range(100):
            progress.update(task_id, completed=i+1)

        progress.stop()
    """

    def __init__(
        self,
        use_rich: bool = True,
        display_mode: Literal["auto", "bar", "table", "simple"] = "auto",
        console: Console | None = None,
    ):
        """
        Initialize the unified progress display.

        Args:
            use_rich: Enable Rich display when available
            display_mode: Display mode preference
            console: Rich console (uses default if None)
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.console = console or (Console(stderr=True) if self.use_rich else None)

        # Determine display mode
        if display_mode == "auto":
            self.display_mode = "bar" if self.use_rich else "simple"
        else:
            self.display_mode = display_mode

        # If Rich requested but not available, fall back to simple
        if self.display_mode in ("bar", "table") and not self.use_rich:
            self.display_mode = "simple"

        self._rich_progress: Progress | None = None
        self._rich_live: Live | None = None
        self._tasks: dict[str, TaskID] = {}  # task_key -> TaskID
        self._task_data: dict[str, TaskProgress] = {}
        self._lock = threading.Lock()
        self._active = False

    def start(self) -> None:
        """Start the progress display."""
        self._active = True

        if self.display_mode == "bar":
            self._start_progress_bar()
        elif self.display_mode == "table":
            self._start_live_table()
        # For "simple", just print initial message

    def _start_progress_bar(self) -> None:
        """Start Rich progress bar display."""
        if not self.use_rich:
            return

        from rich.progress import Progress as RichProgress

        self._rich_progress = RichProgress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(bar_width=30),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TextColumn("({task.completed}/{task.total})"),
            TimeRemainingColumn(),
            TextColumn("{task.fields[status]}"),
            console=self.console,
            expand=False,
        )
        self._rich_live = Live(
            self._rich_progress,
            console=self.console,
            refresh_per_second=4
        )
        self._rich_live.start()

    def _start_live_table(self) -> None:
        """Start Rich live table display."""
        if not self.use_rich:
            return

        self._rich_live = Live(
            self._generate_table(),
            console=self.console,
            refresh_per_second=4
        )
        self._rich_live.start()

    def _generate_table(self) -> Table | None:
        """Generate the live table from current task data."""
        if not self.use_rich:
            return None

        table = Table(show_header=True, header_style="bold magenta", box=None)
        table.add_column("Task", width=35)
        table.add_column("Progress", width=30)
        table.add_column("Count", width=12)
        table.add_column("Elapsed", width=8)
        table.add_column("Status", width=10)

        with self._lock:
            sorted_tasks = sorted(
                self._task_data.items(),
                key=lambda x: (x[1].status != "complete", x[1].start_time)
            )

            for _task_key, data in sorted_tasks:
                name = _shorten_string(data.name)
                percent = data.percent_complete

                # Progress bar
                filled = int(30 * percent / 100)
                bar = "█" * filled + "░" * (30 - filled)

                # Status indicator
                status_map = {
                    "pending": "[dim]pending[/dim]",
                    "running": "[blue]running[/blue]",
                    "complete": "[green]✓[/green]",
                    "error": "[red]✗[/red]",
                }
                status = status_map.get(data.status, data.status)

                table.add_row(
                    name,
                    f"{bar} {percent:.0f}%",
                    f"{data.completed:,}/{data.total:,}" if data.total > 0 else f"{data.completed:,}",
                    _format_timedelta(data.elapsed),
                    status,
                )

        return table

    def add_task(
        self,
        name: str,
        task_key: str | None = None,
        total: int = 0,
    ) -> str:
        """
        Add a task to track.

        Args:
            name: Display name for the task
            task_key: Unique key (defaults to name if not provided)
            total: Estimated total items to process

        Returns:
            Task key for updates
        """
        if task_key is None:
            task_key = name

        with self._lock:
            self._task_data[task_key] = TaskProgress(
                name=name,
                total=total,
            )

            if self.display_mode == "bar" and self._rich_progress:
                task_id = self._rich_progress.add_task(
                    _shorten_string(name, 40),
                    total=total if total > 0 else 100,
                    completed=0,
                    status="[dim]pending[/dim]",
                )
                self._tasks[task_key] = task_id

        return task_key

    def update(
        self,
        task_key: str,
        completed: int | None = None,
        total: int | None = None,
        status: str | None = None,
    ) -> None:
        """
        Update progress for a task.

        Thread-safe - can be called from worker threads.

        Args:
            task_key: Task key returned by add_task()
            completed: Current completed count (advances by 1 if None)
            total: Update estimated total
            status: New status (pending, running, complete, error)
        """
        with self._lock:
            data = self._task_data.get(task_key)
            if not data:
                return

            if completed is not None:
                data.completed = completed
            else:
                data.completed += 1

            if total is not None:
                data.total = total

            if status is not None:
                data.status = status
            elif data.completed > 0 and data.status == "pending":
                data.status = "running"

            data.last_update = time.time()

            # Update Rich progress bar
            if self.display_mode == "bar" and self._rich_progress and task_key in self._tasks:
                task_id = self._tasks[task_key]
                status_display = {
                    "pending": "[dim]pending[/dim]",
                    "running": "[blue]running[/blue]",
                    "complete": "[green]✓[/green]",
                    "error": "[red]✗[/red]",
                }.get(data.status, data.status)

                self._rich_progress.update(
                    task_id,
                    completed=data.completed,
                    total=data.total if data.total > 0 else 100,
                    description=_shorten_string(data.name, 40),
                    status=status_display,
                )

            # Update table display
            elif self.display_mode == "table" and self._rich_live:
                self._rich_live.update(self._generate_table())

            # Simple mode: print update
            elif self.display_mode == "simple":
                name = data.name[:30]
                total_str = str(data.total) if data.total > 0 else "?"
                print(f"\r{name:30} {data.completed:5}/{total_str:>5} {data.status}",
                      file=sys.stderr, end="", flush=True)

    def set_error(self, task_key: str, error_message: str) -> None:
        """Mark a task as failed with error message."""
        with self._lock:
            data = self._task_data.get(task_key)
            if data:
                data.status = "error"
                data.error_message = error_message
                self.update(task_key, status="error")

    def complete(self, task_key: str, final_count: int | None = None) -> None:
        """Mark a task as complete."""
        with self._lock:
            data = self._task_data.get(task_key)
            if data:
                if final_count is not None:
                    data.completed = final_count
                data.status = "complete"
                self.update(task_key, status="complete")

    def stop(self) -> None:
        """Stop the progress display and show final summary."""
        self._active = False

        if self._rich_live:
            if self.display_mode == "table":
                self._rich_live.update(self._generate_table())
            self._rich_live.stop()

        # Print summary
        with self._lock:
            if self._task_data:
                complete = sum(1 for d in self._task_data.values() if d.status == "complete")
                error = sum(1 for d in self._task_data.values() if d.status == "error")
                total = len(self._task_data)

                if self.use_rich and self.console:
                    self.console.print(
                        f"\n[bold]Summary:[/bold] {complete} complete, "
                        f"{error} failed, {total} total"
                    )
                else:
                    print(file=sys.stderr)
                    print(f"Summary: {complete} complete, {error} failed, {total} total",
                          file=sys.stderr)

    def get_callback(self, task_key: str) -> Callable[[int], None]:
        """
        Get a callback function for progress updates.

        Useful for passing to functions that expect a progress callback.

        Args:
            task_key: Task key

        Returns:
            Callback function that accepts completed count
        """
        def callback(completed: int) -> None:
            self.update(task_key, completed=completed)
        return callback

    def is_rich_available(self) -> bool:
        """Check if Rich is available."""
        return RICH_AVAILABLE

    @classmethod
    def create(
        cls,
        use_rich: bool = True,
        display_mode: Literal["auto", "bar", "table", "simple"] = "auto",
        console: Console | None = None,
    ) -> "UnifiedProgress":
        """
        Create a progress display instance.

        Factory method that returns an appropriate implementation.

        Args:
            use_rich: Enable Rich display when available
            display_mode: Display mode preference
            console: Rich console (uses default if None)

        Returns:
            UnifiedProgress instance
        """
        return cls(use_rich=use_rich, display_mode=display_mode, console=console)


def progress_context(
    use_rich: bool = True,
    display_mode: Literal["auto", "bar", "table", "simple"] = "auto",
    console: Console | None = None,
) -> Any:
    """
    Context manager for automatic progress cleanup.

    Example:
        with progress_context(use_rich=True) as progress:
            task = progress.add_task("Processing", total=100)
            for i in range(100):
                progress.update(task, i+1)
    """
    class _ProgressContext:
        def __init__(self) -> None:
            self.progress = UnifiedProgress.create(use_rich, display_mode, console)

        def __enter__(self) -> Any:
            self.progress.start()
            return self.progress

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> Literal[False]:
            self.progress.stop()
            return False

    return _ProgressContext()
