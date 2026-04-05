"""
Session overview components for the TUI.
"""

from datetime import datetime
from typing import Any

from textual.widget import Widget
from textual.widgets import DataTable, Static


class SessionOverview(Widget):
    """Enhanced session overview with analytics."""

    def __init__(self, total_channels: int):
        super().__init__(id="session-overview")
        self.total_channels = total_channels
        self.start_time = datetime.now()
        self.stats = {"processed": 0, "new_videos": 0, "upgrades": 0, "failed": 0}

    def compose(self):
        yield Static("📊 Session Analytics", classes="section-title")
        yield DataTable(id="session-table")
        yield Static(
            "🎯 Performance: Calculating...",
            id="performance-indicator",
            classes="performance-display",
        )

    def on_mount(self):
        """Initialize the session table."""
        table = self.query_one("#session-table", DataTable)
        table.add_column("Metric", width=18)
        table.add_column("Current", width=12)
        table.add_column("Session", width=15)
        self.update_display()

    def update_stats(self, new_stats: dict[str, Any]):
        """Update session statistics."""
        self.stats.update(new_stats)
        self.update_display()

    def update_display(self):
        """Update the statistics display."""
        try:
            table = self.query_one("#session-table", DataTable)
            perf_indicator = self.query_one("#performance-indicator", Static)

            table.clear()

            runtime = datetime.now() - self.start_time
            runtime_str = str(runtime).split(".")[0]
            completion = (
                (self.stats["processed"] / self.total_channels * 100)
                if self.total_channels > 0
                else 0
            )

            table.add_row("Runtime", runtime_str, "Current session")
            table.add_row(
                "Progress",
                f"{self.stats['processed']}/{self.total_channels}",
                f"{completion:.1f}% complete",
            )
            table.add_row("New Videos", str(self.stats["new_videos"]), "Downloaded")
            table.add_row("Upgrades", str(self.stats["upgrades"]), "Quality improved")
            table.add_row("Failed", str(self.stats["failed"]), "Errors encountered")

            if completion > 0:
                success_rate = (
                    (
                        self.stats["new_videos"]
                        + self.stats["upgrades"]
                        - self.stats["failed"]
                    )
                    / max(1, self.stats["new_videos"] + self.stats["upgrades"])
                ) * 100
                perf_indicator.update(
                    f"🎯 Performance: {success_rate:.1f}% success rate"
                )
            else:
                perf_indicator.update("🎯 Performance: Initializing...")

        except Exception:
            pass
