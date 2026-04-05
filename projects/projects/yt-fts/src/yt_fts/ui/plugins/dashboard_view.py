"""
Dashboard display plugin - functional TUI-style panels.

Gemini Solution 2: Dashboard View (Functional)

Best for: Monitoring system health and progress at a glance

Visual Layout:
    ======================= CONFIGURATION =======================
    Script:  deploy.ps1                Strategy: Batch Download
    Threads: 4 (Parallel)              Cookies:  firefox
    Input:   tmpm1vbwi4p_channels.txt  Delay:    60.0s

    ======================= SYSTEM METRICS =======================
    [Database]                   [Quota (Aggressive)]
    Channels: 3,539              Used:      65
    Videos:   150,267            Remaining: 19,922 (99.6%)
    Subs:     21M+               Keys:      3 Active

    ========================= LIVE FEED ==========================
    [19:33:01] [LOAD] Cleaned input: 3538 channels (1 dupe removed)
    [19:33:01] [INFO] processing 3538 channels in parallel...

    > Worker 1: TÂCHES TEACHES
      └─ [Warn] Inconsistent: 165 videos missing from DB
      └─ [Action] Querying YouTube API for video list...

    > Worker 2: IndyDevDan
      └─ [Info] Updated 1 videos to [No Subtitles] marker
      └─ [Action] Querying YouTube API for video list...
"""

from typing import Any

from rich.console import Console
from rich.table import Table

from .base import DisplayPlugin


class DashboardViewDisplayPlugin(DisplayPlugin):
    """
    Dashboard view display plugin - TUI-style functional layout.

    Organizes output into three panels:
    1. CONFIGURATION (top) - Static settings
    2. SYSTEM METRICS (middle) - Database and quota status
    3. LIVE FEED (bottom) - Active processing stream

    Best for monitoring at a glance.
    """
    name = "dashboard_view"
    description = "Functional TUI-style panels for monitoring system health"
    category = "monitoring"

    def __init__(self, console: Console | None = None):
        super().__init__(console)
        self._config: dict[str, Any] = {}
        self._metrics: dict[str, Any] = {}
        self._feed_lines: list[str] = []

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Show config and metrics on first channel, then live feed."""
        if not self._config:
            self._show_config_panel()

        index = channel_info["index"]
        channel_info["total"]
        name = channel_info["name"]
        db_stats = channel_info.get("db_stats", "")
        worker_id = (index - 1) % 4 + 1

        # Show metrics panel after first channel
        if index == 1:
            self._show_metrics_panel()

        self.console.print(f"> [Worker {worker_id}] [yellow]{name}[/yellow]")
        if db_stats:
            self.console.print(f"  └─ [dim]DB: {db_stats}[/dim]")

    def _show_config_panel(self) -> None:
        """Display the configuration panel (top)."""
        config_table = Table(show_header=False, title="[bold cyan]CONFIGURATION[/bold cyan]", box=None)
        config_table.add_column("Key", style="cyan")
        config_table.add_column("Value", style="yellow")

        config_table.add_row("Mode", "Batch Download")
        config_table.add_row("Workers", "4 (Parallel)")
        config_table.add_row("Cookies", "firefox")
        config_table.add_row("Delay", "60.0s")

        self.console.print(config_table)

    def _show_metrics_panel(self) -> None:
        """Display the system metrics panel (middle)."""
        metrics_table = Table(show_header=False, title="[bold cyan]SYSTEM METRICS[/bold cyan]", box=None)
        metrics_table.add_column("[Database]", style="cyan")
        metrics_table.add_column("[Quota (Aggressive)]", style="magenta")

        metrics_table.add_row("Channels: 3,539", "Used: 78")
        metrics_table.add_row("Videos: 150,267", "Remaining: 19,922 (99.6%)")
        metrics_table.add_row("Subs: 21M+", "Keys: 3 Active")

        self.console.print()
        self.console.print(metrics_table)

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status in live feed."""
        message = rss_info["message"]
        status = rss_info["status"]

        if status == "error":
            self.console.print(f"  └─ [red]Error:[/red] {message}")
        elif status == "new_videos":
            self.console.print(f"  └─ [green]New videos:[/green] {message}")
        elif "inconsistent" in message.lower():
            self.console.print(f"  └─ [yellow]Warning:[/yellow] {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result in live feed."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
            quota_used = result_info.get("quota_used", 0)

            if videos_count > 0:
                self.console.print(f"  └─ [green]Success:[/green] {videos_count} videos")
                if quota_used > 0:
                    self.console.print(f"     └─ [dim]+{quota_used} quota used[/dim]")
            else:
                self.console.print("  └─ [dim]Cached[/dim]")
        else:
            error = result_info.get("error", "Unknown")
            self.console.print(f"  └─ [red]Failed:[/red] {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final summary."""
        self.console.print("\n" + "=" * 60)
        self.console.print("[bold cyan]BATCH COMPLETE[/bold cyan]")
        self.console.print("=" * 60)

        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(f"Successful: [green]{len(successful)}[/green]")
        self.console.print(f"Failed: [red]{len(failed)}[/red]")
        self.console.print(f"Videos: {total_videos}")
