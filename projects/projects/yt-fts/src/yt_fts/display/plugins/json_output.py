"""
JSON output plugin for yt-fts.

Provides machine-readable JSON output for all commands.
"""

import json
from typing import Any

from yt_fts.display.base import DisplayPlugin, PluginContext
from yt_fts.utils.types import (
    ChannelDisplayInfo,
    DownloadResultInfo,
    ImportProgressInfo,
    ImportResultInfo,
    RssInfo,
    SearchResults,
)


class JsonOutputPlugin(DisplayPlugin):
    """
    JSON output plugin for machine-readable output.

    Outputs all results as JSON objects.
    """

    supported_commands: list[str] = []  # Supports all commands

    def __init__(self, context: PluginContext):
        """Initialize the JSON output plugin."""
        super().__init__(context)
        self._results: list[dict[str, Any]] = []
        self._metadata: dict[str, Any] = {}

    def get_name(self) -> str:
        """Get the plugin name."""
        return "json"

    def configure(self, options: dict[str, Any]) -> None:
        """Configure the JSON plugin."""
        super().configure(options)
        self._pretty = options.get("pretty", False)

    def _print_json(self, data: dict[str, Any] | SearchResults) -> None:
        """Print data as JSON."""
        if self._pretty:
            self.console.print_json(data=data)
        else:
            self.console.print(json.dumps(data))

    # Search display methods

    def display_search_results(self, results: SearchResults) -> None:
        """Display search results as JSON."""
        self._print_json(results)

    # Download display methods

    def display_channel_header(self, channel_info: ChannelDisplayInfo) -> None:
        """Output channel header as JSON."""
        self.console.print(json.dumps({"event": "channel_start", **channel_info}))

    def display_rss_status(self, rss_info: RssInfo) -> None:
        """Output RSS status as JSON."""
        self.console.print(json.dumps({"event": "rss_check", **rss_info}))

    def display_download_result(self, result_info: DownloadResultInfo) -> None:
        """Output download result as JSON."""
        self.console.print(json.dumps({"event": "download_result", **result_info}))

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Output batch summary as JSON."""
        merged = {"event": "batch_summary", **summary_info}
        self._print_json(merged)

    # Status display methods

    def display_status(self, status_info: dict[str, Any]) -> None:
        """Display status as JSON."""
        self._print_json(status_info)

    # Import display methods

    def display_import_progress(self, import_info: ImportProgressInfo) -> None:
        """Output import progress as JSON."""
        self.console.print(json.dumps({"event": "import_progress", **import_info}))

    def display_import_result(self, result_info: ImportResultInfo) -> None:
        """Output import result as JSON."""
        merged: dict[str, Any] = {"event": "import_complete", **result_info}
        self._print_json(merged)
