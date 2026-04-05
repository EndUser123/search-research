"""
Message formatting and progress display utilities for download operations.

Provides console output routing and message formatting for Rich TUI compatibility.
Extracted from download_handler.py for better separation of concerns.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console

from .progress_tracker import DownloadProgressTracker


class ProgressFormatter:
    """
    Handles message formatting and console output routing for downloads.

    This class manages:
    - Console output routing (direct vs callback for Rich TUI mode)
    - Message formatting with optional channel name inclusion
    - Progress bar instantiation (via DownloadProgressTracker)

    The formatter is stateless except for console and mode configuration,
    making it easy to test and reuse across different download contexts.
    """

    def __init__(
        self,
        console: Console | None = None,
        rich_mode: bool = False,
        include_channel_name_in_messages: bool = True,
        log_callback: Any | None = None,
    ) -> None:
        """
        Initialize the progress formatter.

        Args:
            console: Rich console instance for output
            rich_mode: If True, route output to log_callback instead of console
            include_channel_name_in_messages: Include channel name in formatted messages
            log_callback: Callback function for messages in Rich TUI mode
        """
        self.console = console or Console(stderr=True, legacy_windows=False)
        self.rich_mode = rich_mode
        self.include_channel_name_in_messages = include_channel_name_in_messages
        self.log_callback = log_callback

    def print_message(self, *args: Any, **kwargs: Any) -> None:
        """
        Print a message to the console or log callback depending on rich_mode.

        In Rich TUI mode, routes output to the log panel to prevent layout breakage.
        In standard mode, prints directly to the console.

        Args:
            *args: Arguments to pass to console.print or format as message
            **kwargs: Keyword arguments for console.print
        """
        if self.rich_mode and self.log_callback:
            if args:
                msg = " ".join(str(a) for a in args)
                if msg.strip():
                    self.log_callback(msg)
        else:
            self.console.print(*args, **kwargs)

    @staticmethod
    def video_word(count: int) -> str:
        """
        Return the singular or plural form of 'video' based on count.

        Args:
            count: Number of videos

        Returns:
            "video" if count is 1, otherwise "videos"
        """
        return "video" if count == 1 else "videos"

    def maybe_with_channel(
        self, message: str, preposition: str, channel_name: str | None = None
    ) -> str:
        """
        Append channel name to message if configured and channel name available.

        Args:
            message: Base message string
            preposition: Preposition to use before channel name (e.g., "for", "from")
            channel_name: Optional channel name (uses instance config if None)

        Returns:
            Message with optional channel name appended
        """
        if self.include_channel_name_in_messages and channel_name:
            return f'{message} {preposition} "{channel_name}"'
        return message

    def detail_message(self, message: str) -> str:
        """
        Format a detail message with optional indentation.

        When channel names are included in messages, returns the message as-is.
        Otherwise, adds indentation prefix for visual hierarchy.

        Args:
            message: The detail message to format

        Returns:
            Formatted message with optional indentation
        """
        if self.include_channel_name_in_messages:
            return message
        return f"   ⎿ {message}"

    @staticmethod
    def missing_subtitles_message(count: int) -> str:
        """
        Generate a message about videos without subtitles.

        Args:
            count: Number of videos without subtitles

        Returns:
            Formatted message (singular or plural)
        """
        if count == 1:
            return "1 video does not have subtitles"
        return f"{count} videos do not have subtitles"

    def get_progress(
        self, suppress_status_messages: bool = False, *args: Any, **kwargs: Any
    ) -> Any:
        """
        Get a Progress instance or DummyProgress depending on mode.

        Delegates to DownloadProgressTracker for consistency with existing
        progress tracking infrastructure.

        Args:
            suppress_status_messages: If True, return DummyProgress
            *args: Column arguments passed to Progress() constructor
            **kwargs: Additional arguments passed to Progress() constructor
                     (e.g., transient=True, custom columns)

        Returns:
            Progress instance or DummyProgress from DownloadProgressTracker
        """
        return DownloadProgressTracker.get_progress(
            self.console, self.rich_mode, suppress_status_messages, *args, **kwargs
        )
