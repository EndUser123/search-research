"""
Table display plugin - structured tabular output for batch downloads.
"""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

from .base import RSS_STATUS_ICONS, DisplayPlugin, truncate_string


class TableDisplayPlugin(DisplayPlugin):
    """
    Table display plugin that presents information in structured tables.

    Features:
    - Channel progress table
    - RSS status table
    - Results summary table
    - Clean, organized tabular format
    """

    name = "table"
    description = "Structured tabular output for organized display"
    category = "core"

    def __init__(self, console: Console | None = None) -> None:
        """
        Initialize the table display plugin.

        Args:
            console: Rich console instance for output
        """
        super().__init__(console)
        self.channel_data: list[dict[str, Any]] = []

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Add channel to table data."""
        # Check for database inconsistencies
        inconsistent = channel_info.get("inconsistent", False)
        inconsistency_reason = channel_info.get("inconsistency_reason", "")

        # Mark database stats as inconsistent if needed
        db_stats = channel_info["db_stats"]
        if inconsistent:
            db_stats = f"[red]{db_stats}[/red]"

        self.channel_data.append(
            {
                "index": channel_info["index"],
                "name": channel_info["name"],
                "db_stats": db_stats,
                "rss_status": "",
                "result": "",
                "inconsistent": inconsistent,
                "inconsistency_reason": inconsistency_reason,
            }
        )

        # Display inconsistency warning if present
        if inconsistent and inconsistency_reason:
            self.console.print(
                f"[red]⚠️  Database inconsistency for {channel_info['name']}: {inconsistency_reason}[/red]"
            )

        # Display current table
        self._display_channel_table()

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Update RSS status in table."""
        if self.channel_data:
            status = rss_info["status"]
            message = rss_info["message"]

            status_icon = RSS_STATUS_ICONS.get(status, "?")

            self.channel_data[-1]["rss_status"] = f"{status_icon} {message}"

        # Display updated table
        self._display_channel_table()

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Update result in table."""
        if self.channel_data:
            success = result_info["success"]
            if success:
                videos_count = result_info["videos_count"]
                self.channel_data[-1]["result"] = f"✅ {videos_count} videos"
            else:
                error = result_info.get("error", "Failed")[:20]
                self.channel_data[-1]["result"] = f"❌ {error}"

        # Display updated table
        self._display_channel_table()

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final summary table."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_channels = summary_info["total_channels"]
        total_videos = summary_info.get("total_videos", 0)

        # Final summary table
        summary_table = Table(title="📊 Batch Download Summary")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="magenta")

        summary_table.add_row("Total Channels", str(total_channels))
        summary_table.add_row("Successful", str(len(successful)))
        summary_table.add_row("Failed", str(len(failed)))
        summary_table.add_row("Videos Downloaded", str(total_videos))

        if successful:
            avg = total_videos / len(successful)
            summary_table.add_row("Avg Videos/Channel", f"{avg:.1f}")

        self.console.print("\n")
        self.console.print(summary_table)

    def _display_channel_table(self) -> None:
        """Display the current channel progress table."""
        table = Table(title="📥 Channel Progress")
        table.add_column("#", style="dim", no_wrap=True)
        table.add_column("Channel", style="yellow", max_width=30)
        table.add_column("Database", style="blue", max_width=20)
        table.add_column("RSS Status", style="green", max_width=25)
        table.add_column("Result", style="magenta", max_width=20)

        for channel in self.channel_data:
            table.add_row(
                str(channel["index"]),
                truncate_string(channel["name"], 28),
                truncate_string(channel["db_stats"], 18),
                truncate_string(channel["rss_status"], 23),
                channel["result"],
            )

        self.console.print("\n")
        self.console.print(table)
        self.console.print()
