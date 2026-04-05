"""
Enhanced production-ready Rich progress bar implementation for dnld_telegram
Based on Rich library best practices and production patterns
"""

import asyncio
import signal
import time
from threading import Event

from loguru import logger
from rich.console import Console
from rich.progress import (
    BarColumn,
    FileSizeColumn,
    Progress,
    TaskID,
    TextColumn,
    TimeRemainingColumn,
    TotalFileSizeColumn,
    TransferSpeedColumn,
)

from ...ui.base import UIConfig


class ProductionProgressDisplay:
    """Production-ready Rich progress bar manager with enhanced features."""

    def __init__(
        self,
        console: Console | None = None,
        refresh_rate: float = 4.0,
        config: UIConfig | None = None,
    ):
        super().__init__(
            download_dir="", config=config
        )  # Initialize BaseUIDisplay part
        self.console = console or Console()
        self.refresh_rate = (
            1.0  # Reduced refresh rate to mitigate potential performance issues
        )

        # Combined progress display with Rich - no Live display to avoid conflicts
        self.progress = Progress(
            TextColumn("[progress.description]{task.description}", justify="left"),
            BarColumn(bar_width=30),
            "[progress.percentage]{task.percentage:>3.1f}%",
            "•",
            FileSizeColumn(),
            "/",
            TotalFileSizeColumn(),
            "•",
            TransferSpeedColumn(),
            "•",
            TimeRemainingColumn(),
            console=self.console,
            transient=True,  # Clear progress bars when done to prevent overlap
            expand=False,  # Don't expand to full terminal width
        )

        self.tasks: dict[str, TaskID] = {}
        self.download_tasks: dict[str, TaskID] = {}
        self.is_started = False
        self.console_handler = None
        self.termination_event = Event()
        self.stats = {
            "files_downloaded": 0,
            "total_bytes": 0,
            "errors": 0,
            "start_time": time.time(),
        }

        # Setup signal handlers for graceful termination
        self._setup_signal_handlers()

    def _setup_signal_handlers(self) -> None:
        """Setup signal handlers for graceful termination."""

        def signal_handler(signum, frame):
            signal_names = {signal.SIGINT: "Ctrl+C", signal.SIGTERM: "SIGTERM"}
            signal_name = signal_names.get(signum, f"Signal {signum}")

            self.console.print(
                f"\n[yellow]Warning: {signal_name} received - stopping gracefully...[/yellow]"
            )
            self.termination_event.set()

            # Also set global termination event if available
            try:
                from . import download

                if (
                    hasattr(download, "termination_event")
                    and download.termination_event
                ):
                    download.termination_event.set()
            except ImportError:
                pass

            # Update all active tasks to show stopping status
            for task_id in list(self.tasks.values()) + list(
                self.download_tasks.values()
            ):
                try:
                    if task_id in [t.id for t in self.progress.tasks]:
                        self.progress.update(
                            task_id, description="[yellow]Stopping...[/yellow]"
                        )
                except Exception:
                    pass  # Task might already be completed

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

    def is_termination_requested(self) -> bool:
        """Check if termination has been requested."""
        return self.termination_event.is_set()

    def start(self) -> None:
        """Start the progress display."""
        if self.is_started:
            return

        # Start Rich Progress - loguru and Rich should coexist with transient=True
        self.progress.start()
        self.is_started = True

    def stop(self) -> None:
        """Stop the progress display."""
        if not self.is_started:
            return

        self.progress.stop()
        self.is_started = False

    def add_main_task(
        self,
        name: str,
        operation: str,
        total: int | None = None,
        status: str = "Starting...",
    ) -> TaskID:
        """Add a new main operation task."""
        description = f"[bold blue]{operation}[/bold blue] - {status}"
        task_id = self.progress.add_task(description, total=total, start=False)
        self.tasks[name] = task_id
        return task_id

    def add_download_task(
        self, filename: str, total_size: int | None = None
    ) -> TaskID:
        """Add a new download task."""
        max_width = self.config.max_name_width if self.config else 25
        display_filename = filename
        if len(display_filename) > max_width:
            display_filename = display_filename[: max_width - 3] + "..."

        description = f"[bold green]Download[/bold green] {display_filename}"
        task_id = self.progress.add_task(description, total=total_size, start=False)
        self.download_tasks[filename] = task_id
        return task_id

    def start_main_task(self, name: str) -> None:
        """Start a main operation task."""
        if name in self.tasks:
            self.progress.start_task(self.tasks[name])

    def start_download_task(self, filename: str) -> None:
        """Start a download task."""
        if filename in self.download_tasks:
            self.progress.start_task(self.download_tasks[filename])

    def update_main_task(
        self, name: str, advance: int = 1, status: str | None = None, **kwargs
    ):
        """Update main task progress."""
        if name in self.tasks:
            self.progress.update(self.tasks[name], advance=advance, **kwargs)

    def update_download_task(self, filename: str, advance: int) -> None:
        """Update download task progress."""
        if filename in self.download_tasks:
            self.progress.update(self.download_tasks[filename], advance=advance)
            self.stats["total_bytes"] += advance

    def complete_main_task(
        self, name: str, status: str = "[green]Complete[/green]"
    ) -> None:
        """Mark a main task as complete."""
        if name in self.tasks:
            # Update description to show completion
            self.progress.update(
                self.tasks[name], description=f"[green]✓[/green] {status}"
            )
            # Mark as completed after a short delay to show result
            self.progress.update(self.tasks[name], completed=True)

    def complete_download_task(self, filename: str) -> None:
        """Mark a download task as complete."""
        if filename in self.download_tasks:
            self.progress.update(
                self.download_tasks[filename],
                description=f"[green]✓[/green] {filename}",
            )
            self.progress.update(self.download_tasks[filename], completed=True)
            self.stats["files_downloaded"] += 1
            # Remove completed task after brief display
            self.progress.remove_task(self.download_tasks[filename])
            del self.download_tasks[filename]

    def error_main_task(self, name: str, error_msg: str) -> None:
        """Mark a main task as failed."""
        if name in self.tasks:
            self.progress.update(
                self.tasks[name],
                description=f"[red]✗ Error: {error_msg}[/red]",
                completed=True,
            )
            self.stats["errors"] += 1

    def error_download_task(self, filename: str, error_msg: str) -> None:
        """Mark a download task as failed."""
        if filename in self.download_tasks:
            self.progress.update(
                self.download_tasks[filename],
                description=f"[red]✗ {filename}: {error_msg}[/red]",
                completed=True,
            )
            self.stats["errors"] += 1
            # Remove failed task after a delay
            asyncio.create_task(self._remove_task_after_delay(filename, 3.0))

    async def _remove_task_after_delay(self, filename: str, delay: float) -> None:
        """Remove a task after a delay."""
        await asyncio.sleep(delay)
        if filename in self.download_tasks:
            self.progress.remove_task(self.download_tasks[filename])
            del self.download_tasks[filename]

    def log(self, message: str, style: str = "") -> None:
        """Log a message via loguru to avoid Rich conflicts."""
        # Use loguru instead of Rich console to prevent conflicts
        logger.info(message)

    def update_stats(self, **kwargs):
        """Update statistics."""
        self.stats.update(kwargs)

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()


# Backward compatibility wrapper
class TelegramProgressDisplay(ProductionProgressDisplay):
    """Backward compatibility wrapper for existing code."""

    def add_task(
        self,
        name: str,
        operation: str,
        total: int | None = None,
        status: str = "Starting...",
    ) -> TaskID:
        """Add a task (maps to main task for compatibility)."""
        return self.add_main_task(name, operation, total, status)

    def start_task(self, name: str) -> None:
        """Start a task (maps to main task for compatibility)."""
        return self.start_main_task(name)

    def update_task(
        self, name: str, advance: int = 1, status: str | None = None, **kwargs
    ):
        """Update task (maps to main task for compatibility)."""
        return self.update_main_task(name, advance, status, **kwargs)

    def complete_task(self, name: str, status: str = "[green]Complete[/green]") -> None:
        """Complete task (maps to main task for compatibility)."""
        return self.complete_main_task(name, status)

    def error_task(self, name: str, error_msg: str) -> None:
        """Error task (maps to main task for compatibility)."""
        return self.error_main_task(name, error_msg)


class DownloadProgressDisplay(ProductionProgressDisplay):
    """Specialized download-only progress display."""

    def add_download(self, filename: str, total_size: int | None = None) -> TaskID:
        """Add a download (compatibility method)."""
        return self.add_download_task(filename, total_size)

    def start_download(self, filename: str):
        """Start a download (compatibility method)."""
        return self.start_download_task(filename)

    def update_download(self, filename: str, advance: int):
        """Update download (compatibility method)."""
        return self.update_download_task(filename, advance)

    def complete_download(self, filename: str):
        """Complete download (compatibility method)."""
        return self.complete_download_task(filename)


# Global progress display instance
_global_progress: ProductionProgressDisplay | None = None


def get_progress_display() -> ProductionProgressDisplay:
    """Get or create the global progress display instance."""
    global _global_progress
    if _global_progress is None:
        _global_progress = ProductionProgressDisplay()
    return _global_progress


def cleanup_progress_display() -> None:
    """Clean up the global progress display."""
    global _global_progress
    if _global_progress:
        _global_progress.stop()
        _global_progress = None
