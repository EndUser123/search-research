"""
Base classes and interfaces for display plugins.
"""

from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console

# RSS status constants
RSS_STATUS_SKIP = "skip"
RSS_STATUS_NEW_VIDEOS = "new_videos"
RSS_STATUS_GAP_DETECTED = "gap_detected"
RSS_STATUS_ERROR = "error"

# Common icon mappings for RSS status
RSS_STATUS_ICONS = {
    RSS_STATUS_SKIP: "",
    RSS_STATUS_NEW_VIDEOS: "",
    RSS_STATUS_GAP_DETECTED: "",
    RSS_STATUS_ERROR: "",
}

# Rich-formatted icon mappings for RSS status
RSS_STATUS_ICONS_RICH = {
    RSS_STATUS_SKIP: "[dim]⏭️[/dim]",
    RSS_STATUS_NEW_VIDEOS: "[green]🆕[/green]",
    RSS_STATUS_GAP_DETECTED: "[yellow]🔍[/yellow]",
    RSS_STATUS_ERROR: "[red]❌[/red]",
}


def truncate_string(text: str, max_length: int, suffix: str = "...") -> str:
    """
    Truncate a string to a maximum length, adding suffix if truncated.

    Args:
        text: The string to truncate
        max_length: Maximum length including suffix
        suffix: String to add if truncated (default "...")

    Returns:
        Truncated string with suffix if needed, or original string if short enough
    """
    if len(text) <= max_length:
        return text
    suffix_len = len(suffix)
    return text[:max_length - suffix_len] + suffix


class DisplayPlugin(ABC):
    """
    Abstract base class for display plugins.

    Each plugin implements a different visual style for batch download output.
    """

    def __init__(self, console: Console | None = None, verbose: bool = True) -> None:
        """
        Initialize the display plugin.

        Args:
            console: Rich console instance for output (defaults to new Console())
            verbose: Whether to show verbose output
        """
        self.console = console or Console()
        self.verbose = verbose

    @abstractmethod
    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """
        Display channel processing header.

        Args:
            channel_info: Dict containing:
                - index: Channel index in batch (1-based)
                - total: Total channels in batch
                - name: Channel display name
                - db_count: Number of videos in database
                - db_stats: Detailed db statistics string
        """

    @abstractmethod
    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """
        Display RSS feed check results.

        Args:
            rss_info: Dict containing:
                - status: 'skip', 'new_videos', 'gap_detected', 'error'
                - message: Human-readable status message
                - missing_count: Number of missing videos (if applicable)
                - scan_count: Number to scan (after max_videos limit)
                - error_msg: Error message (if status == 'error')
        """

    @abstractmethod
    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """
        Display download result for a channel.

        Args:
            result_info: Dict containing:
                - success: Boolean success status
                - videos_count: Number of videos downloaded
                - videos_without_subtitles: Videos that had no subtitles
                - total_videos: Total videos found
                - error: Error message (if failed)
                - message: Success message
                - target_reached: Boolean indicating if min_saved target was reached
        """

    @abstractmethod
    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """
        Display final batch download summary.

        Args:
            summary_info: Dict containing:
                - successful: List of successful downloads
                - failed: List of failed downloads
                - total_channels: Total channels processed
                - total_videos: Total videos downloaded
                - duration: Processing duration
                - successful_downloads: Number of channels with successful downloads
                - target: Target number of channels to download
        """

    def info(self, message: str) -> None:
        """
        Display an informational message (intermediate progress).

        Used for progress updates during channel processing:
        - "Discovering channel via API..."
        - "Querying YouTube API for video list..."
        - "Gap detected → querying YouTube API for full video list..."

        Default implementation formats as a dimmed continuation line.
        Subclasses can override for different styling.

        Args:
            message: The informational message to display
        """
        self.console.print(f"   ⎿ [dim]{message}[/dim]")

    def warning(self, message: str) -> None:
        """
        Display a warning message.

        Default implementation formats with a warning icon and yellow color.
        Subclasses can override for different styling.

        Args:
            message: The warning message to display
        """
        self.console.print(f"   ⎿ [yellow]⚠️ {message}[/yellow]")

    def error(self, message: str) -> None:
        """
        Display an error message.

        Default implementation formats with an error icon and red color.
        Subclasses can override for different styling.

        Args:
            message: The error message to display
        """
        self.console.print(f"   ⎿ [red]❌ {message}[/red]")

    def cleanup(self) -> None:
        """Optional cleanup method called when plugin is done."""
