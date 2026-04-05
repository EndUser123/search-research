"""
Progress tracking utilities for download operations.

Provides Rich progress bar management and thread-safe progress updates
for video downloads.
"""

from __future__ import annotations
import time
from contextlib import nullcontext, suppress
from typing import Any

from rich.console import Console
from rich.progress import BarColumn, Progress, SpinnerColumn, TextColumn


# Progress bar description constants (must match SPECS.md)
YTDLP_PROGRESS_DESC = "   ⎿ yt-dlp:"


class DownloadProgressTracker:
    """
    Manages progress tracking for downloads using Rich progress bars.

    Handles both individual channel downloads and batch mode progress
    with thread-safe coordinator updates.
    """

    def __init__(
        self,
        channel_name: str | None = None,
        console: Console | None = None,
        rich_mode: bool = False,
        suppress_status_messages: bool = False,
    ) -> None:
        """
        Initialize progress tracker.

        Args:
            channel_name: Name of channel being downloaded
            console: Rich console instance
            rich_mode: If True, suppress console output for TUI
            suppress_status_messages: If True, suppress individual status messages
        """
        self.console = console or Console(stderr=True, legacy_windows=False)
        self.channel_name = channel_name
        self.rich_mode = rich_mode
        self.suppress_status_messages = suppress_status_messages

        # Progress state
        self._rich_progress: Progress | None = None
        self._rich_task_id: Any | None = None
        self._progress_console: Console | None = None
        self.download_start_time: float | None = None

    def conditional_status(self, message: str) -> Any:
        """
        Return a status context manager that suppresses output during Rich mode.

        In Rich mode, status spinners conflict with the Rich Live display,
        so we return a null context manager. Otherwise, return normal status.

        Args:
            message: Status message to display

        Returns:
            Context manager for status or null context
        """
        if self.rich_mode or self.suppress_status_messages:
            return nullcontext()
        return self.console.status(message)

    def update_progress(
        self,
        current: int,
        total: int,
        progress_coordinator: Any = None,
        progress_channel_name: str | None = None,
    ) -> None:
        """
        Update progress bar during video downloads.

        Args:
            current: Current number of videos downloaded
            total: Total number of videos to download
            progress_coordinator: Optional ThreadSafeProgressCoordinator
            progress_channel_name: Channel name for coordinator updates
        """
        # Initialize start_time on first actual progress (not 0)
        if self.download_start_time is None and current > 0:
            self.download_start_time = time.time()

        percentage = (current / total * 100) if total > 0 else 0

        # Use coordinator for per-channel progress when available (standard batch mode)
        if (
            progress_coordinator
            and progress_channel_name
            and not self.rich_mode
        ):
            eta = self._calculate_eta(current, total)

            # Queue the update via coordinator (thread-safe)
            progress_coordinator.update_by_channel(
                progress_channel_name,
                total=total,
                completed=current,
                fields={"stats": f"{current}/{total} ({percentage:.0f}%) - ETA: {eta}"},
            )
        else:
            # No coordinator - use temporary Rich progress bar
            self._update_rich_progress(current, total, percentage)

    def _calculate_eta(self, current: int, total: int) -> str:
        """Calculate ETA as human-readable string."""
        if self.download_start_time and current > 0:
            elapsed = time.time() - self.download_start_time
            avg_time_per_video = elapsed / current
            remaining = total - current
            eta_seconds = avg_time_per_video * remaining
            return format_eta(eta_seconds)
        return "calculating..."

    def _update_rich_progress(
        self, current: int, total: int, percentage: float
    ) -> None:
        """Update Rich Progress bar for video downloads."""
        # Initialize progress bar on first call
        if self._rich_progress is None:
            self._progress_console = Console(stderr=True)
            is_batch_mode = self.suppress_status_messages
            self._rich_progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(
                    bar_width=8, complete_style="green", finished_style="bright_green"
                ),
                TextColumn("{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                console=self._progress_console,
                transient=True,  # Remove progress bar when done to avoid visual gaps
                refresh_per_second=2,
            )
            self._rich_progress.__enter__()

            channel_display = self.channel_name or "Channel"
            if self.suppress_status_messages:
                description = "     yt-dlp:"
            else:
                description = f"[cyan]Downloading {channel_display}[/cyan]"
            self._rich_task_id = self._rich_progress.add_task(
                description,
                total=total,
            )
            self.download_start_time = time.time()

        # Update the progress bar
        if self._rich_progress and self._rich_task_id is not None:
            self._rich_progress.update(self._rich_task_id, completed=current)

        # Finish progress when complete
        if current >= total and self._rich_progress is not None:
            self._rich_progress.__exit__(None, None, None)
            self._rich_progress = None
            self._rich_task_id = None
            # Clear any remaining progress bar artifacts from the line
            if self._progress_console:
                import sys
                sys.stderr.write("\r\x1b[0K")  # CR + clear to end of line
                sys.stderr.flush()

    def cleanup(self) -> None:
        """Clean up progress bar resources."""
        if self._rich_progress is not None:
            with suppress(Exception):
                self._rich_progress.__exit__(None, None, None)
            self._rich_progress = None
            self._rich_task_id = None
            self._progress_console = None

    @staticmethod
    def get_progress(
        console: Console, 
        rich_mode: bool = False, 
        suppress_status: bool = False, 
        *args: Any, 
        **kwargs: Any
    ) -> Any:
        """
        Get a Progress instance or DummyProgress depending on mode.

        Args:
            console: Rich console instance
            rich_mode: If True, return DummyProgress
            suppress_status: If True, return DummyProgress
            *args: Column arguments passed to Progress() constructor
            **kwargs: Additional arguments passed to Progress() constructor

        Returns:
            Progress instance or DummyProgress
        """
        if rich_mode or suppress_status:
            return DownloadProgressTracker.DummyProgress()
        
        # If columns are provided as positional args, use them; otherwise use defaults
        if args:
            # Custom columns provided
            columns = args
        else:
            # Use default columns
            columns = (
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
            )
        
        # Ensure console is in kwargs
        if 'console' not in kwargs:
            kwargs['console'] = console
        
        return Progress(*columns, **kwargs)

    class DummyProgress:
        """Dummy progress bar that does nothing, for use in rich_mode."""

        def __enter__(self) -> Any:
            """
            Enter the dummy progress context.

            Returns:
                self: The dummy progress instance
            """
            return self

        def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
            """
            Exit the dummy progress context (no-op).

            Returns:
                None
            """

        def add_task(self, *args: Any, **kwargs: Any) -> int:
            """
            Dummy method for adding tasks (no-op).

            Returns:
                0: Dummy task ID
            """
            return 0

        def advance(self, *args: Any, **kwargs: Any) -> None:
            """
            Dummy method for advancing progress (no-op).

            Args:
                *args: Ignored positional arguments
                **kwargs: Ignored keyword arguments
            """

        def update(self, *args: Any, **kwargs: Any) -> None:
            """
            Dummy method for updating progress (no-op).

            Args:
                *args: Ignored positional arguments
                **kwargs: Ignored keyword arguments
            """
