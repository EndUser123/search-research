"""
Adapter for legacy UI display plugins to work with the new display system.

This module provides a compatibility layer that allows legacy display plugins
(from ui.plugins) to work with the new display plugin system. The adapter wraps
legacy plugins and emits deprecation warnings to guide migration.
"""
from __future__ import annotations

import warnings
from typing import Any

from yt_fts.utils.types import (
    ChannelDisplayInfo,
    DownloadResultInfo,
    ImportProgressInfo,
    ImportResultInfo,
    RssInfo,
    SearchResults,
)

from .base import DisplayPlugin, PluginContext


class LegacyDisplayPluginAdapter(DisplayPlugin):
    """
    Adapter for legacy UI display plugins to work with new system.

    This class wraps a legacy DisplayPlugin from ui.plugins and adapts its
    interface to work with the new display.base.DisplayPlugin interface.

    Legacy plugins are primarily designed for batch download operations,
    so this adapter only supports the 'download' command.

    Attributes:
        legacy_plugin: The wrapped legacy plugin instance
        _warning_emitted: Tracks whether deprecation warning was shown
    """

    # Legacy plugins only support batch download operations
    supported_commands: list[str] = ["download"]

    def __init__(self, context: PluginContext, legacy_plugin: Any) -> None:
        """
        Initialize the adapter with a legacy plugin instance.

        Args:
            context: Plugin context with command info and options
            legacy_plugin: Instance of legacy ui.plugins.DisplayPlugin

        Raises:
            TypeError: If legacy_plugin is not a valid legacy plugin
        """
        super().__init__(context)

        # Validate that the legacy plugin has the expected interface
        required_methods = [
            "display_channel_header",
            "display_rss_status",
            "display_download_result",
            "display_batch_summary",
        ]
        for method_name in required_methods:
            if not hasattr(legacy_plugin, method_name):
                msg = f"Legacy plugin must have method '{method_name}'"
                raise TypeError(
                    msg
                )

        self.legacy_plugin = legacy_plugin

        # Emit deprecation warning once at initialization
        warnings.warn(
            f"Legacy plugin '{legacy_plugin.__class__.__name__}' is deprecated. "
            f"Use the new display.plugins system instead. "
            f"Migrate by inheriting from display.base.DisplayPlugin.",
            DeprecationWarning,
            stacklevel=3,
        )

    def get_name(self) -> str:
        """
        Get the plugin name.

        Returns:
            Plugin name with 'legacy_' prefix
        """
        return f"legacy_{self.legacy_plugin.__class__.__name__}"

    def configure(self, options: dict[str, Any]) -> None:
        """
        Configure the adapter.

        Note: Legacy plugins don't support runtime configuration,
        so this method only updates the adapter's options.

        Args:
            options: Dictionary of configuration options (not passed to legacy)
        """
        self.options.update(options)

    # Download-specific display methods (delegated to legacy plugin)

    def display_channel_header(self, channel_info: ChannelDisplayInfo) -> None:
        """
        Display channel processing header.

        Delegates to the legacy plugin's display_channel_header method.

        Args:
            channel_info: ChannelDisplayInfo TypedDict containing channel display info
        """
        self.legacy_plugin.display_channel_header(channel_info)

    def display_rss_status(self, rss_info: RssInfo) -> None:
        """
        Display RSS feed check results.

        Delegates to the legacy plugin's display_rss_status method.

        Args:
            rss_info: RssInfo TypedDict containing RSS check results
        """
        self.legacy_plugin.display_rss_status(rss_info)

    def display_download_result(self, result_info: DownloadResultInfo) -> None:
        """
        Display download result for a channel.

        Delegates to the legacy plugin's display_download_result method.

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
        self.legacy_plugin.display_download_result(result_info)

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """
        Display final batch download summary.

        Delegates to the legacy plugin's display_batch_summary method.

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
        self.legacy_plugin.display_batch_summary(summary_info)

    # Methods not supported by legacy plugins - provide default no-op implementations

    def display_search_results(self, results: SearchResults) -> None:
        """
        Display search results.

        Legacy plugins don't support search operations.
        This method does nothing (no-op).

        Args:
            results: Search results dictionary
        """

    def display_status(self, status_info: dict[str, Any]) -> None:
        """
        Display system status information.

        Legacy plugins don't support status display.
        This method does nothing (no-op).

        Args:
            status_info: Status information dictionary
        """

    def display_import_progress(self, import_info: ImportProgressInfo) -> None:
        """
        Display import progress.

        Legacy plugins don't support import operations.
        This method does nothing (no-op).

        Args:
            import_info: Import progress information
        """

    def display_import_result(self, result_info: ImportResultInfo) -> None:
        """
        Display import completion result.

        Legacy plugins don't support import operations.
        This method does nothing (no-op).

        Args:
            result_info: Import result information
        """

    def display(self, data: dict[str, Any]) -> None:
        """
        Generic display method.

        For legacy plugins, this delegates to the console directly.

        Args:
            data: Dictionary of data to display
        """
        self.console.print(data)

    def cleanup(self) -> None:
        """
        Cleanup method.

        Delegates to the legacy plugin's cleanup method if it exists.

        If the legacy plugin doesn't have a cleanup method, this is a no-op.
        """
        if hasattr(self.legacy_plugin, "cleanup"):
            self.legacy_plugin.cleanup()


def wrap_legacy_plugin(
    legacy_plugin_class: type,
    context: PluginContext,
) -> LegacyDisplayPluginAdapter:
    """
    Wrap a legacy plugin class in the adapter.

    Factory function to create a legacy plugin instance and wrap it
    in the adapter. Handles different legacy plugin signatures.

    Args:
        legacy_plugin_class: The legacy plugin class to wrap
        context: Plugin context to pass to the adapter

    Returns:
        LegacyDisplayPluginAdapter wrapping the legacy plugin instance

    Example:
        >>> from ..ui.plugins.default import DefaultDisplayPlugin as LegacyDefault
        >>> adapter = wrap_legacy_plugin(LegacyDefault, context)
    """
    import inspect

    # Create legacy plugin instance
    # Different legacy plugins have different signatures, so we inspect and adapt
    try:
        sig = inspect.signature(legacy_plugin_class.__init__)
        params = list(sig.parameters.keys())

        # Remove 'self' from parameters
        if params and params[0] == "self":
            params = params[1:]

        if "verbose" in params and "console" in params:
            # Full signature with both console and verbose
            legacy_instance = legacy_plugin_class(
                console=context.console,
                verbose=context.options.get("verbose", True),
            )
        elif "console" in params:
            # Only console parameter (most common)
            legacy_instance = legacy_plugin_class(console=context.console)
        elif not params:
            # No parameters
            legacy_instance = legacy_plugin_class()
        else:
            # Fall back: try with console only
            legacy_instance = legacy_plugin_class(console=context.console)
    except (OSError, ValueError, TypeError):
        # Last resort: try with console only
        legacy_instance = legacy_plugin_class(console=context.console)

    return LegacyDisplayPluginAdapter(context, legacy_instance)
