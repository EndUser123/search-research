"""
Minimal display plugin - ultra-quiet output for batch downloads.
"""
from __future__ import annotations

from typing import Any

from .base import DisplayPlugin


class MinimalDisplayPlugin(DisplayPlugin):
    """
    Minimal display plugin that shows only essential information.

    Shows only:
    - Final success/failure counts
    - No per-channel details
    - Silent operation
    """

    name = "minimal"
    description = "Ultra-quiet output showing only final summary counts"
    category = "core"

    def __init__(self, console: Any = None) -> None:
        """Initialize minimal plugin."""
        super().__init__(console)
        self.inconsistencies_found = 0

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Check for inconsistencies and show warnings."""
        if channel_info.get("inconsistent", False):
            self.inconsistencies_found += 1
            # Show warnings even in minimal mode since they're important diagnostics
            inconsistency_reason = channel_info.get("inconsistency_reason", "")
            channel_name = channel_info.get("name", "Unknown")
            self.console.print(
                f"⚠️ DB inconsistency: {channel_name} - {inconsistency_reason}"
            )

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """No output for RSS status."""

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """No output for individual results."""

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display only final summary."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(f"✓{len(successful)} ✗{len(failed)} ({total_videos} videos)")
