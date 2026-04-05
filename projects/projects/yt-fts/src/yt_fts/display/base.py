"""
Base classes and interfaces for display plugins.

This module defines the standardized display plugin interface used across
all yt-fts commands (search, download, import, status, etc.).
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

from yt_fts.utils.types import (
    ChannelDisplayInfo,
    DownloadResultInfo,
    ImportProgressInfo,
    ImportResultInfo,
    RssInfo,
    SearchResults,
)


@dataclass
class PluginContext:
    """
    Context information passed to display plugins.

    Attributes:
        command: The command name (search, download, import, status, etc.)
        console: Rich console instance for output
        options: Additional command-specific options
        config_dir: Path to the configuration directory
        db_path: Path to the database file
    """

    command: str
    console: Console
    options: dict[str, Any] = field(default_factory=dict)
    config_dir: Path | None = None
    db_path: Path | None = None

    def get_option(self, key: str, default: Any = None) -> Any:
        """Get an option value with a default fallback."""
        return self.options.get(key, default)


class DisplayPlugin(ABC):
    """
    Abstract base class for display plugins.

    All display plugins must inherit from this class and implement
    the required methods. Each plugin can handle one or more command types.

    Plugin naming convention: Use snake_case, e.g., "compact", "json_output"

    Command types:
    - "search": Full-text and vector search results
    - "download": Batch download progress and results
    - "import": Channel import operations
    - "status": System status information
    - "list": Listing operations (channels, videos, etc.)
    """

    # Override this to specify which commands this plugin supports
    # Empty list means supports all commands
    supported_commands: list[str] = []

    def __init__(self, context: PluginContext):
        """
        Initialize the display plugin.

        Args:
            context: Plugin context with command info and options
        """
        self.context = context
        self.console = context.console
        self.command = context.command
        self.options = context.options

    @abstractmethod
    def get_name(self) -> str:
        """
        Get the plugin name.

        Returns:
            Plugin name/identifier
        """

    def get_formatter(self) -> Any | None:
        """
        Get a TextFormatter instance for real-time logging.

        Plugins can override this to provide custom formatting for
        worker progress, status messages, and other real-time logs.

        Returns:
            TextFormatter instance or None (uses default plain text)

        Example:
            class RichDisplayPlugin(DisplayPlugin):
                def get_formatter(self):
                    from yt_fts.utils.text_formatter import RichTextFormatter
                    return RichTextFormatter(console=self.console)
        """
        return None

    def configure(self, options: dict[str, Any]) -> None:
        """
        Configure the plugin with options.

        Called after initialization to update configuration.
        Default implementation merges options into self.options.

        Args:
            options: Dictionary of configuration options
        """
        self.options.update(options)

    def supports_command(self, command: str) -> bool:
        """
        Check if this plugin supports the given command.

        Args:
            command: Command name to check

        Returns:
            True if plugin supports the command
        """
        if not self.supported_commands:
            return True
        return command in self.supported_commands

    # Search-specific display methods

    def display_search_results(self, results: SearchResults) -> None:
        """
        Display search results.

        Args:
            results: SearchResults TypedDict containing:
                - query: Search query string [REQUIRED]
                - scope: Search scope (all, channel, video) [REQUIRED]
                - matches: List of search result matches [REQUIRED]
                - total_matches: Total count of matches [OPTIONAL]
                - total_videos: Total count of videos with matches [OPTIONAL]
                - total_channels: Total count of channels with matches [OPTIONAL]
        """

    # Download-specific display methods

    def display_channel_header(self, channel_info: ChannelDisplayInfo) -> None:
        """
        Display channel processing header.

        Args:
            channel_info: ChannelDisplayInfo TypedDict containing:
                - index: Channel index in batch (1-based) [REQUIRED]
                - total: Total channels in batch [REQUIRED]
                - name: Channel display name [REQUIRED]
                - db_count: Number of videos in database [OPTIONAL]
                - db_stats: Detailed db statistics string [OPTIONAL]
        """

    def display_rss_status(self, rss_info: RssInfo) -> None:
        """
        Display RSS feed check results.

        Args:
            rss_info: RssInfo TypedDict containing:
                - status: RSS check status ('skip', 'new_videos', 'gap_detected', 'error') [REQUIRED]
                - message: Human-readable status message [REQUIRED]
                - missing_count: Number of missing videos [OPTIONAL]
                - scan_count: Number to scan (after max_videos limit) [OPTIONAL]
                - error_msg: Error message (if status == 'error') [OPTIONAL]
        """

    def display_download_result(self, result_info: DownloadResultInfo) -> None:
        """
        Display download result for a channel.

        Args:
            result_info: DownloadResultInfo TypedDict containing:
                - success: Boolean success status [REQUIRED]
                - videos_count: Number of videos downloaded [OPTIONAL]
                - videos_without_subtitles: Videos that had no subtitles [OPTIONAL]
                - total_videos: Total videos found [OPTIONAL]
                - error: Error message (if failed) [OPTIONAL]
                - message: Success message [OPTIONAL]
                - target_reached: Boolean indicating if min_saved target was reached [OPTIONAL]
        """

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

    # Status-specific display methods

    def display_status(self, status_info: dict[str, Any]) -> None:
        """
        Display system status information.

        Args:
            status_info: Dict containing:
                - detailed: Whether to show detailed status
                - db_stats: Dictionary with database statistics
                - quota_info: Dictionary with quota information
                - config_info: Dictionary with configuration info
        """

    # Import-specific display methods

    def display_import_progress(self, import_info: ImportProgressInfo) -> None:
        """
        Display import progress.

        Args:
            import_info: ImportProgressInfo TypedDict containing:
                - source: Import source (file, url, etc.) [REQUIRED]
                - progress: Current progress (0-100) [REQUIRED]
                - message: Status message [REQUIRED]
                - imported: Number of items imported so far [OPTIONAL]
        """

    def display_import_result(self, result_info: ImportResultInfo) -> None:
        """
        Display import completion result.

        Args:
            result_info: ImportResultInfo TypedDict containing:
                - success: Boolean success status [REQUIRED]
                - imported: Number of items imported [OPTIONAL]
                - failed: Number of items that failed [OPTIONAL]
                - duration: Import duration (seconds) [OPTIONAL]
                - errors: List of error messages [OPTIONAL]
        """

    # Generic display methods

    def display(self, data: dict[str, Any]) -> None:
        """
        Generic display method for any data type.

        This is a fallback for commands that don't have specific methods.
        Plugins can override this to handle custom data types.

        Args:
            data: Dictionary of data to display
        """
        # Default: print as JSON-like structure
        self.console.print(data)

    def error(self, message: str) -> None:
        """
        Display an error message.

        Args:
            message: Error message to display
        """
        self.console.print(f"[red]Error:[/red] {message}")

    def warning(self, message: str) -> None:
        """
        Display a warning message.

        Args:
            message: Warning message to display
        """
        self.console.print(f"[yellow]Warning:[/yellow] {message}")

    def info(self, message: str) -> None:
        """
        Display an info message.

        Args:
            message: Info message to display
        """
        self.console.print(message)

    def cleanup(self) -> None:
        """
        Optional cleanup method called when plugin is done.

        Override this to release resources or close files.
        """
