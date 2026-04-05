"""
Compact display plugin - minimal output for batch downloads.
"""
from __future__ import annotations

from typing import Any

from .base import DisplayPlugin


class CompactDisplayPlugin(DisplayPlugin):
    """
    Compact display plugin that shows minimal information.

    Focuses on essential information only:
    - Brief channel status
    - Simple success/failure indicators
    - Condensed summary
    """

    name = "compact"
    description = "Minimal output with essential information only"
    category = "core"

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display minimal channel header."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]

        # Check for database inconsistencies
        inconsistent = channel_info.get("inconsistent", False)

        # Add warning indicator if inconsistent
        warning = " ⚠️" if inconsistent else ""

        # Just show: "1/3 @NVIDIAdeveloper"
        self.console.print(f"{index}/{total} {name}{warning}")

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status - very brief."""
        status = rss_info["status"]

        if status == "skip":
            self.console.print("  → No new videos")
        elif status == "new_videos":
            self.console.print("  → New videos found")
        elif status == "gap_detected":
            self.console.print("  → Checking for updates")
        else:  # error
            self.console.print("  → RSS error")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result - minimal."""
        success = result_info["success"]

        if success:
            videos_count = result_info["videos_count"]
            self.console.print(f"  ✓ {videos_count} videos")
        else:
            self.console.print("  ✗ Failed")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display compact batch summary."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print("")
        self.console.print(
            f"Summary: {len(successful)}✓ {len(failed)}✗ ({total_videos} videos)"
        )
