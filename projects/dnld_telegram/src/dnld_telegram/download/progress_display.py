"""
Rich progress bar implementation for dnld_telegram
Based on verified rich library documentation and examples
"""

import signal
from threading import Event
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TaskID,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)

from ...ui.base import BaseUIDisplay, UIConfig


class TelegramProgressDisplay:
    """Rich progress bar manager for Telegram operations."""

    def __init__(self) -> None:
        self.console = Console()
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.fields[operation]!s}", justify="left"),
            BarColumn(bar_width=40),
            MofNCompleteColumn(),
            "•",
            TextColumn("[progress.percentage]{task.percentage:>3.1f}%"),
            "•",
            TimeElapsedColumn(),
            "•",
            TimeRemainingColumn(),
            "•",
            TextColumn("[cyan]{task.fields[status]!s}", justify="right"),
            console=self.console,
            expand=False,
        )
        self.tasks: dict[str, TaskID] = {}
        self.live: Live | None = None
        self.termination_event = Event()

        # Setup signal handlers for graceful termination
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle termination signals gracefully."""
        signal_names: dict[int, str] = {
            signal.SIGINT: "Ctrl+C",
            signal.SIGTERM: "SIGTERM",
        }
        signal_name = signal_names.get(signum, f"Signal {signum}")

        self.console.print(
            f"\n[yellow]⚠️  {signal_name} received - stopping gracefully...[/yellow]"
        )
        self.termination_event.set()

        # Update all active tasks to show stopping status
        for task_id in self.tasks.values():
            try:
                self.progress.update(task_id, status="[yellow]Stopping...[/yellow]")
            except Exception:
                pass  # Task might already be completed

    def is_termination_requested(self) -> bool:
        """Check if termination has been requested."""
        return self.termination_event.is_set()

    def start(self) -> None:
        """Start the progress display."""
        self.live = Live(
            Panel(
                self.progress,
                title="[bold green]📱 Telegram Media Downloader[/bold green]",
                border_style="blue",
            ),
            console=self.console,
            refresh_per_second=4,
        )
        self.live.start()

    def stop(self) -> None:
        """Stop the progress display."""
        if self.live:
            self.live.stop()
            self.live = None

    def add_task(
        self,
        name: str,
        operation: str,
        total: int | None = None,
        status: str = "Starting...",
    ) -> TaskID:
        """Add a new progress task."""
        task_id = self.progress.add_task(
            name, operation=operation, status=status, total=total, start=False
        )
        self.tasks[name] = task_id
        return task_id

    def start_task(self, name: str) -> None:
        """Start a specific task."""
        if name in self.tasks:
            self.progress.start_task(self.tasks[name])

    def update_task(
        self, name: str, advance: int = 1, status: str | None = None, **kwargs: Any
    ) -> None:
        """Update task progress."""
        if name in self.tasks:
            update_kwargs: dict[str, Any] = {"advance": advance}
            if status:
                update_kwargs["status"] = status
            update_kwargs.update(kwargs)
            self.progress.update(self.tasks[name], **update_kwargs)

    def complete_task(self, name: str) -> None:
        """Mark a task as complete."""
        if name in self.tasks:
            self.progress.update(
                self.tasks[name], status="[green]✅ Complete[/green]", completed=True
            )

    def error_task(self, name: str, error_msg: str) -> None:
        """Mark a task as failed."""
        if name in self.tasks:
            self.progress.update(
                self.tasks[name],
                status=f"[red]❌ Error: {error_msg}[/red]",
                completed=True,
            )

    def log(self, message: str, style: str = "") -> None:
        """Log a message to the console."""
        if style:
            self.console.print(f"[{style}]{message}[/{style}]")
        else:
            self.console.print(message)

    def __enter__(self) -> "TelegramProgressDisplay":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


class DownloadProgressDisplay(BaseUIDisplay):
    """Specialized progress display for download operations."""

    def __init__(
        self, download_dir: str = "downloads", config: UIConfig | None = None
    ) -> None:
        super().__init__(download_dir=download_dir, config=config)
        self.console = Console()
        self.progress = Progress(
            TextColumn("[bold blue]{task.fields[filename]!s}", justify="right"),
            BarColumn(bar_width=40),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            TextColumn("[cyan]{task.fields[size]!s}", justify="right"),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
        )
        self.tasks: dict[str, TaskID] = {}
        self.live: Live | None = None
        self.termination_event = Event()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum: int, frame: Any) -> None:
        """Handle termination signals gracefully."""
        self.console.print(
            "\n[yellow]⚠️  Download interrupted - saving progress...[/yellow]"
        )
        self.termination_event.set()

    def is_termination_requested(self) -> bool:
        """Check if termination has been requested."""
        return self.termination_event.is_set()

    def start(self) -> None:
        """Start the download progress display."""
        self.live = Live(
            Panel(
                self.progress,
                title="[bold green]⬇️  Downloading Media Files[/bold green]",
                border_style="green",
            ),
            console=self.console,
            refresh_per_second=2,
        )
        self.live.start()

    def stop(self) -> None:
        """Stop the download progress display."""
        if self.live:
            self.live.stop()
            self.live = None

    def add_download(self, filename: str, total_size: int | None = None) -> TaskID:
        """Add a new download task."""
        max_width = 25
        display_filename = filename
        if len(display_filename) > max_width:
            display_filename = display_filename[: max_width - 3] + "..."
        size_text = (
            f"{total_size // 1024 // 1024:.1f} MB" if total_size else "Unknown size"
        )
        task_id = self.progress.add_task(
            "download",
            filename=display_filename,
            size=size_text,
            total=total_size,
            start=False,
        )
        self.tasks[filename] = task_id
        return task_id

    def start_download(self, filename: str) -> None:
        """Start a specific download."""
        if filename in self.tasks:
            self.progress.start_task(self.tasks[filename])

    def update_download(self, filename: str, advance: int) -> None:
        """Update download progress."""
        if filename in self.tasks:
            self.progress.update(self.tasks[filename], advance=advance)

    def complete_download(self, filename: str) -> None:
        """Mark download as complete."""
        if filename in self.tasks:
            self.progress.update(self.tasks[filename], completed=True)

    def __enter__(self) -> "DownloadProgressDisplay":
        self.start()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.stop()


# Global progress display instance
_global_progress: TelegramProgressDisplay | None = None


def get_progress_display() -> TelegramProgressDisplay:
    """Get or create the global progress display instance."""
    global _global_progress
    if _global_progress is None:
        _global_progress = TelegramProgressDisplay()
    return _global_progress


def cleanup_progress_display() -> None:
    """Clean up the global progress display."""
    global _global_progress
    if _global_progress:
        _global_progress.stop()
        _global_progress = None
