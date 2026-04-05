
"""
Exception-First display plugin - alert-based output.

Gemini Solution 6: Exception-First Feed (Alert Based)

Best for: Monitoring production systems where only problems matter
"""

from datetime import datetime
from typing import Any

from rich.console import Console
from rich.panel import Panel

from .base import DisplayPlugin


class ExceptionFirstDisplayPlugin(DisplayPlugin):
    """
    Exception-first display plugin - alert-based output.

    Shows ONLY warnings and errors. Silent on success.
    Best for production monitoring where you only care about problems.
    """
    name = "exception_first"
    description = "Alert-based output showing only warnings and errors, silent on success"
    category = "diagnostic"

    def __init__(self, console: Console | None = None):
        super().__init__(console)
        self._alert_count = 0
        self._showed_header = False

    def _show_header(self) -> None:
        """Show alert feed header once."""
        if not self._showed_header:
            header = Panel(
                "[bold yellow]⚠ ALERT FEED[/bold yellow] [dim](warnings and errors only)[/dim]",
                border_style="yellow",
                padding=(0, 1),
            )
            self.console.print("\n" + str(header))
            self._showed_header = True

    def _timestamp(self) -> str:
        """Get current timestamp."""
        return datetime.now().strftime("%H:%M:%S")

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Only show if there's a problem (warn or error state)."""
        db_stats = channel_info.get("db_stats", "")
        name = channel_info["name"]
        worker_id = (channel_info["index"] - 1) % 4 + 1

        has_issue = False
        alert_lines = []

        if "inconsistent" in db_stats.lower() or "0/" in db_stats:
            has_issue = True
            alert_lines.append(f"→ DB inconsistent: {db_stats}")

        if has_issue:
            self._show_header()
            self._alert_count += 1
            self.console.print(f"\n[{self._timestamp()}] [yellow]⚠[/yellow]  [Worker {worker_id}] [yellow]{name}[/yellow]")
            for line in alert_lines:
                self.console.print(f"                {line}")

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Only show errors and warnings."""
        status = rss_info["status"]
        message = rss_info["message"]

        if status == "error":
            self._show_header()
            self._alert_count += 1
            self.console.print(f"\n[{self._timestamp()}] [red]✗[/red]  [ERROR] {message}")
        elif status == "gap_detected":
            self._show_header()
            self._alert_count += 1
            self.console.print(f"\n[{self._timestamp()}] [yellow]⚠[/yellow]  [GAP] {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Only show failures. Success is silent."""
        success = result_info["success"]

        if not success:
            self._show_header()
            self._alert_count += 1
            error = result_info.get("error", "Unknown error")
            self.console.print(f"\n[{self._timestamp()}] [red]✗[/red]  [DOWNLOAD FAILED]")
            self.console.print(f"                → {error}")

            if "cookies" in str(error).lower() or "NoneType" in str(error):
                self.console.print("                → [dim]Check: --cookies-from-browser or COOKIE_FILE env var[/dim]")
            elif "quota" in str(error).lower():
                self.console.print("                → [dim]Check: YouTube API quota status[/dim]")
            elif "network" in str(error).lower() or "connection" in str(error).lower():
                self.console.print("                → [dim]Check: Internet connection and proxy settings[/dim]")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Show minimal summary - always show this."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_videos = summary_info.get("total_videos", 0)

        if self._alert_count == 0:
            status_text = "[green]✓ ALL CLEAN[/green] - no issues detected"
        else:
            status_text = f"[yellow]⚠ {self._alert_count} alerts[/yellow] - see above"

        summary = Panel(
            f"{status_text}\n\n"
            f"[cyan]{len(successful)}[/cyan] channels processed | "
            f"{total_videos} videos | "
            f"[red]{len(failed)}[/red] failed",
            border_style="green" if len(failed) == 0 else "red",
            padding=(0, 1),
        )

        self.console.print("\n" + str(summary))

        if failed:
            self.console.print("\n[red]Failed channels:[/red]")
            for result in failed[:10]:
                error = result.get("error", "Unknown")[:50]
                channel = result.get("channel", "Unknown")
                self.console.print(f"  • {channel}: {error}")
            if len(failed) > 10:
                self.console.print(f"  ... and {len(failed) - 10} more")
