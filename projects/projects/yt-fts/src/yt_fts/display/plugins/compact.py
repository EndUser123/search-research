"""
Compact display plugin for yt-fts.

Provides minimal, machine-friendly output.
"""

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


class CompactDisplayPlugin(DisplayPlugin):
    """
    Compact display plugin with minimal output.

    Focuses on essential information only.
    """

    supported_commands: list[str] = []  # Supports all commands

    def __init__(self, context: PluginContext):
        """Initialize the compact display plugin."""
        super().__init__(context)

    def get_name(self) -> str:
        """Get the plugin name."""
        return "compact"

    # Search display methods

    def display_search_results(self, results: SearchResults) -> None:
        """Display search results in compact format."""
        matches = results.get("matches", [])

        if not matches:
            self.console.print("No matches found")
            return

        for quote in matches:
            video_id = quote.get("video_id", "")
            time_stamp = quote.get("time_stamp", "")
            text = quote.get("text", quote.get("subs", ""))
            link = quote.get("link", "")

            self.console.print(f"{video_id}:{time_stamp} {text[:100]}")
            if link:
                self.console.print(f"  {link}")

        total_matches = results.get("total_matches", len(matches))
        total_videos = results.get("total_videos", 0)
        self.console.print(f"\n{total_matches} matches in {total_videos} videos")

    # Download display methods

    def display_channel_header(self, channel_info: ChannelDisplayInfo) -> None:
        """Display minimal channel header."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]

        self.console.print(f"{index}/{total} {name}")

    def display_rss_status(self, rss_info: RssInfo) -> None:
        """Display RSS status briefly."""
        status = rss_info["status"]

        if status == "skip":
            self.console.print("  → No new videos")
        elif status == "new_videos":
            self.console.print("  → New videos found")
        elif status == "gap_detected":
            self.console.print("  → Checking for updates")
        else:
            self.console.print("  → RSS error")

    def display_download_result(self, result_info: DownloadResultInfo) -> None:
        """Display download result minimally."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
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

    # Status display methods

    def display_status(self, status_info: dict[str, Any]) -> None:
        """Display system status in compact format."""
        db_stats = status_info.get("db_stats", {})
        quota_info = status_info.get("quota_info", {})

        self.console.print(f"Channels: {db_stats.get('channels', 0)}")
        self.console.print(f"Videos: {db_stats.get('videos', 0)}")
        self.console.print(f"Subtitles: {db_stats.get('subtitles', 0)}")
        self.console.print(f"Quota: {quota_info.get('used', 0)} / {quota_info.get('limit', 10000)}")

    # Import display methods

    def display_import_progress(self, import_info: ImportProgressInfo) -> None:
        """Display import progress briefly."""
        progress = import_info.get("progress", 0)
        imported = import_info.get("imported", 0)

        self.console.print(f"Progress: {progress}% ({imported} items)")

    def display_import_result(self, result_info: ImportResultInfo) -> None:
        """Display import result in compact format."""
        success = result_info.get("success", False)
        imported = result_info.get("imported", 0)
        failed = result_info.get("failed", 0)

        if success:
            self.console.print(f"✓ Imported {imported} items")
            if failed > 0:
                self.console.print(f"  {failed} failed")
        else:
            self.console.print("✗ Import failed")
