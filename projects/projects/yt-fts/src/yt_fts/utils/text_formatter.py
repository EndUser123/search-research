"""
Robust plain-text formatter for yt-fts logging.

This is the base logging layer - always works, no dependencies.
Can be extended with Rich/Table formatters later.
"""

import sys
from datetime import datetime


class TextFormatter:
    """
    Robust plain-text formatter for unified logging.

    Used by both single-thread (DownloadHandler) and multi-worker
    (ParallelProcessor) code paths for consistent output.

    Format: [TIME] [LEVEL] [TAG] message
    Example: [07:50:56] [INFO] [INIT] Loaded 3538 channels
    """

    # Level constants for consistent formatting
    LEVEL_INFO = "INFO"
    LEVEL_DONE = "DONE"
    LEVEL_ERROR = "ERROR"
    LEVEL_WARN = "WARN"
    LEVEL_PROG = "PROG"

    # Fixed-width level column for alignment
    _LEVEL_WIDTH = 5

    def __init__(self, output=None):
        """
        Initialize the TextFormatter.

        Args:
            output: File object to write to (default: sys.stderr)
        """
        self._output = output if output is not None else sys.stderr

    def _write(self, level: str, tag: str, message: str) -> None:
        """
        Write a formatted log message.

        Args:
            level: Log level (INFO, DONE, ERROR, WARN, PROG)
            tag: Component tag (INIT, CH#0001, RSS, etc.)
            message: Log message
        """
        ts = datetime.now().strftime("%H:%M:%S")
        # Format: [TIME] [LEVEL] [TAG] message
        # Level is padded for alignment: [INFO ] vs [ERROR]
        level_padded = f"{level:<{self._LEVEL_WIDTH}}"
        line = f"[{ts}] [{level_padded}] [{tag}] {message}\n"
        self._output.write(line)
        self._output.flush()

    def info(self, tag: str, message: str) -> None:
        """
        Log an informational message.

        Args:
            tag: Component tag (e.g., "INIT", "LOAD", "CONFIG")
            message: Log message

        Example:
            [07:50:56] [INFO ] [INIT] Loaded 3538 channels
        """
        self._write(self.LEVEL_INFO, tag, message)

    def done(self, tag: str, message: str) -> None:
        """
        Log a completion message.

        Args:
            tag: Component tag (e.g., "CH#0001", "BATCH")
            message: Completion message

        Example:
            [07:53:54] [DONE ] [CH#0001] no-new-videos
        """
        self._write(self.LEVEL_DONE, tag, message)

    def error(self, tag: str, message: str) -> None:
        """
        Log an error message.

        Args:
            tag: Component tag (e.g., "CH#0002", "API")
            message: Error message

        Example:
            [07:54:12] [ERROR] [CH#0002] timeout
        """
        self._write(self.LEVEL_ERROR, tag, message)

    def warn(self, tag: str, message: str) -> None:
        """
        Log a warning message.

        Args:
            tag: Component tag (e.g., "RSS", "QUOTA")
            message: Warning message

        Example:
            [07:51:00] [WARN ] [RSS] feed unavailable
        """
        self._write(self.LEVEL_WARN, tag, message)

    def progress(self, current: int, total: int, eta: str, item: str) -> None:
        """
        Log progress update.

        Args:
            current: Current item number
            total: Total items
            eta: Estimated time remaining (e.g., "69h33m")
            item: Item identifier (shortened channel/URL)

        Example:
            [07:54:28] [PROG] [1/3538] ETA=69h33m UCFig7sk...
        """
        tag = f"{current}/{total}"
        message = f"ETA={eta} {item}"
        self._write(self.LEVEL_PROG, tag, message)

    def shorten_channel(self, channel: str, max_length: int = 60) -> str:
        """
        Shorten a channel URL/ID for display.

        Args:
            channel: Channel URL or ID
            max_length: Maximum length before truncation

        Returns:
            Shortened channel identifier

        Examples:
            "@channel" → "@channel"
            "https://www.youtube.com/channel/UCFig7sk..." → "channel/UCFig7sk..."
            "UCFig7skuwYrCIGy0tP2o8Rg" → "UCFig7skuwYrCIG..."
        """
        # Already short
        if len(channel) <= max_length:
            return channel

        # Handle format - keep as is unless too long
        if channel.startswith("@"):
            if len(channel) > max_length:
                return f"{channel[:max_length-3]}..."
            return channel

        # Channel ID - truncate with ellipsis
        if channel.startswith("UC") and len(channel) > 20:
            return f"{channel[:max_length-3]}..."

        # Full URL - extract and shorten channel ID
        if "/channel/" in channel:
            channel_id = channel.split("/channel/")[-1].split("/")[0]
            # Always add ellipsis for long channel IDs in URL format
            if len(channel_id) > 15:
                short_id = f"{channel_id[:15]}..."
                return f"channel/{short_id}"
            return f"channel/{channel_id}"

        # Handle in URL
        if "youtube.com/@" in channel:
            handle = channel.split("youtube.com/@")[-1].split("/")[0]
            if len(handle) > max_length - 1:
                return f"@{handle[:max_length-5]}..."
            return f"@{handle}"

        # Default: truncate with ellipsis
        return f"{channel[:max_length-3]}..."


# Singleton instance for convenient import
_default_formatter = TextFormatter()


def get_formatter() -> TextFormatter:
    """Get the default TextFormatter instance."""
    return _default_formatter


class RichTextFormatter(TextFormatter):
    """
    Rich-colored formatter for yt-fts logging.

    Extends TextFormatter with Rich styling for colored output.
    Falls back to plain text if Rich is unavailable or fails.

    Format: [TIME] [LEVEL] [TAG] message (with colors)
    Example: [07:50:56] [cyan]INFO[/cyan] [INIT] Loaded 3538 channels
    """

    # Level colors for Rich markup
    _LEVEL_COLORS = {
        "INFO": "cyan",
        "DONE": "green",
        "ERROR": "red",
        "WARN": "yellow",
        "PROG": "blue",
    }

    def __init__(self, output=None, console=None):
        """
        Initialize the RichTextFormatter.

        Args:
            output: File object to write to (default: sys.stderr)
            console: Rich Console instance (optional, will create if needed)
        """
        super().__init__(output)
        self._console = console
        self._use_rich = True

        # Try to import Rich
        try:
            from rich.console import Console

            if self._console is None:
                self._console = Console(
                    stderr=True, legacy_windows=False, force_terminal=False
                )
        except ImportError:
            self._use_rich = False

    def _write(self, level: str, tag: str, message: str) -> None:
        """
        Write a formatted log message with Rich colors.

        Args:
            level: Log level (INFO, DONE, ERROR, WARN, PROG)
            tag: Component tag (INIT, CH#0001, RSS, etc.)
            message: Log message
        """
        ts = datetime.now().strftime("%H:%M:%S")
        color = self._LEVEL_COLORS.get(level, "white")
        level_padded = f"{level:<{self._LEVEL_WIDTH}}"

        if self._use_rich and self._console:
            try:
                # Use Rich for colored output
                self._console.print(
                    f"[dim]{ts}[/dim] [{color}]{level_padded}[/{color}] [{tag}] {message}",
                    highlight=False,
                )
                return
            except Exception:
                # Fallback to plain text
                pass

        # Fallback: plain text
        line = f"[{ts}] [{level_padded}] [{tag}] {message}\n"
        self._output.write(line)
        self._output.flush()
