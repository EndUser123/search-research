"""
Pipeline display plugin - chronological phase organization.

Gemini Solution 1: Pipeline View (Chronological)

Best for: Debugging startup failures or configuration errors

Visual Layout:
    [PHASE 1: BOOTSTRAP]
    Command: python -m yt_fts batch-download --parallel-workers 4 ...
    Source:  database (channels) | Workers: 4 | Cookies: firefox
    Env:     Loaded from P:\\projects\\yt-fts\\.env

    [PHASE 2: PRE-FLIGHT & STATE]
    Quota:   AGGRESSIVE mode | 65/20,000 used
    System:  3,539 Channels | 150,267 Videos | 21,036,455 Subtitles
    Input:   C:\\...\tmpm1vbwi4p_channels.txt (3538 valid, 1 dupe removed)
    Config:  Language: en | Delay: 60.0s | Mode: ThreadPoolExecutor

    [PHASE 3: EXECUTION STREAM]
    [Start] Initializing 4 worker threads...
    [Quota] Key 1: 10k | Key 2: 10k | Key 3: 10k
    ---------------------------------------------------
    [Thread 1] Starting https://www.youtube.com/channel/UCFig...
               1. ● TÂCHES TEACHES
                  ⎿ RSS: new channel, switching to yt-api for full scan
                  ⎿ ⚠ Inconsistent: DB has 0/165 videos
"""
from __future__ import annotations

from typing import Any

from rich.console import Console

from .base import RSS_STATUS_ICONS_RICH, DisplayPlugin


class PipelineViewDisplayPlugin(DisplayPlugin):
    """
    Pipeline view display plugin - chronological organization.

    Groups output into three phases:
    1. BOOTSTRAP - Command and environment setup
    2. PRE-FLIGHT - Resource loading and validation
    3. EXECUTION - Active worker output, grouped by thread

    This solves interleaving by showing phase transitions clearly.
    """
    name = "pipeline_view"
    description = "Chronological phase organization showing bootstrap, pre-flight, and execution stages"
    category = "monitoring"

    def __init__(self, console: Console | None = None) -> None:
        super().__init__(console)
        self._phase = "BOOTSTRAP"
        self._worker_count = 0

    def _show_phase_header(self, phase: str, title: str) -> None:
        """Show a phase transition header."""
        if self._phase != phase:
            self._phase = phase
            self.console.print(f"\n[bold cyan]━ PHASE {phase}: {title} ━[/bold cyan]\n")

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display channel header - transition to execution phase."""
        self._show_phase_header("3", "EXECUTION STREAM")

        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]

        # Simulate worker assignment (4 workers)
        worker_id = (index - 1) % 4 + 1

        self.console.print(
            f"[dim][Thread {worker_id}][/dim] Starting channel {index}/{total}: [yellow]{name}[/yellow]"
        )

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display RSS status as worker detail."""
        message = rss_info["message"]
        status = rss_info["status"]

        icon = RSS_STATUS_ICONS_RICH.get(status, "→")

        self.console.print(f"           {icon} {message}")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display download result."""
        success = result_info["success"]

        if success:
            videos_count = result_info.get("videos_count", 0)
            time_taken = result_info.get("time_taken", "")
            quota_used = result_info.get("quota_used", 0)

            parts = []
            if videos_count > 0:
                parts.append(f"[green]✓[/green] {videos_count} videos")
            if time_taken:
                parts.append(f"time: {time_taken}")
            if quota_used > 0:
                parts.append(f"[dim]quota: +{quota_used}[/dim]")

            if parts:
                self.console.print(f"           {' | '.join(parts)}")
            else:
                self.console.print("           [dim]✓ Cached[/dim]")
        else:
            error = result_info.get("error", "Unknown")
            self.console.print(f"           [red]✗[/red] {error}")

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final pipeline summary."""
        self._show_phase_header("COMPLETE", "PIPELINE SUMMARY")

        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_channels = summary_info["total_channels"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print(
            f"  Channels processed: [cyan]{len(successful) + len(failed)}[/cyan]/{total_channels}"
        )
        self.console.print(
            f"  Successful: [green]{len(successful)}[/green] | Failed: [red]{len(failed)}[/red]"
        )
        self.console.print(
            f"  Videos downloaded: [cyan]{total_videos}[/cyan]"
        )

        if failed:
            self.console.print("\n  [red]Failed channels:[/red]")
            for result in failed[:5]:
                error = result.get("error", "Unknown")[:50]
                self.console.print(f"    • {result.get('channel', 'Unknown')}: {error}")
