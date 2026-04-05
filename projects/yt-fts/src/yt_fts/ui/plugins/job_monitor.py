"""
Job Monitor display plugin - tabular status tracking.

Gemini Solution 4: Job Monitor (Tabular)

Best for: Debugging errors and tracking status at a glance
"""
from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

from .base import RSS_STATUS_ICONS_RICH, DisplayPlugin


class JobMonitorDisplayPlugin(DisplayPlugin):
    """
    Job monitor display plugin - tabular status tracking.

    Displays all active jobs in a table format with status indicators.
    Best for debugging errors and monitoring progress at a glance.
    """
    name = "job_monitor"
    description = "Tabular status tracking for debugging errors and monitoring progress"
    category = "monitoring"

    def __init__(self, console: Console | None = None) -> None:
        super().__init__(console)
        self._job_table: Table | None = None
        self._jobs: dict[str, dict[str, Any]] = {}

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display job table on first channel, then add row for this job."""
        if self._job_table is None:
            self._show_job_table()

        index = channel_info["index"]
        name = channel_info["name"]
        db_stats = channel_info.get("db_stats", "")
        worker_id = (index - 1) % 4 + 1

        if "inconsistent" in db_stats.lower():
            status = "[yellow]⚠ Inconsistent[/yellow]"
        elif "new channel" in db_stats.lower():
            status = "[dim]🔄 New[/dim]"
        else:
            status = "[green]✓ OK[/green]"

        videos = db_stats if db_stats else "-"
        self.console.print(
            f"  [{worker_id}]     {name:<20}  {status:<15}  {videos:<10}"
        )
        self._jobs[name] = {"worker": worker_id, "status": status}

    def _show_job_table(self) -> None:
        """Display the job monitoring table header."""
        table = Table(title="[bold cyan]JOB MONITOR[/bold cyan]", show_header=True, header_style="bold magenta")
        table.add_column("Worker", style="cyan", width=6)
        table.add_column("Channel", style="yellow", width=25)
        table.add_column("Status", style="green", width=20)
        table.add_column("Videos", style="white", width=10)
        table.add_column("Quota", style="magenta", width=10)

        self.console.print("\n" + str(table))
        self._job_table = table

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status update."""
        message = rss_info["message"]
        status = rss_info["status"]

        icon = RSS_STATUS_ICONS_RICH.get(status, "•")

        self.console.print(f"      └─ {icon} {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result in job row."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
            quota_used = result_info.get("quota_used", 0)
            quota_str = f"+{quota_used}" if quota_used > 0 else "0"
            self.console.print(f"      └─ [green]✓[/green] {videos_count} videos | quota: {quota_str}")
        else:
            error = result_info.get("error", "Unknown")
            if len(error) > 30:
                error = error[:27] + "..."
            self.console.print(f"      └─ [red]✗[/red] {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final job summary."""
        self.console.print("\n" + "─" * 80)
        self.console.print("[bold cyan]JOB SUMMARY[/bold cyan]")
        self.console.print("─" * 80)

        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(f"  Jobs completed: [green]{len(successful)}[/green]")
        self.console.print(f"  Jobs failed:    [red]{len(failed)}[/red]")
        self.console.print(f"  Total videos:   {total_videos}")

        if failed:
            self.console.print("\n  [red]Failed jobs:[/red]")
            for result in failed[:5]:
                error = result.get("error", "Unknown")[:40]
                self.console.print(f"    • {result.get('channel', 'Unknown')}: {error}")
