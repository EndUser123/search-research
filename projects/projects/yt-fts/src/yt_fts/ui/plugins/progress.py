"""
Progress display plugin - advanced animated progress bars with live updates.
"""

import time
from typing import Any

from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from .base import DisplayPlugin


class ProgressDisplayPlugin(DisplayPlugin):
    """
    Advanced progress display plugin with animated bars and live updates.

    Features:
    - Real-time progress bars with spinners
    - Live-updating statistics
    - Color-coded status indicators
    - Performance metrics (speed, ETA)
    - Animated transitions
    """

    name = "progress"
    description = "Advanced animated progress bars with live updates"
    category = "verbose"

    def __init__(self, console: Any = None) -> None:
        """
        Initialize the progress display plugin.

        Args:
            console: Rich console instance for output
        """
        super().__init__(console)
        self.channel_data: list[dict[str, Any]] = []
        self.live_display: Any = None
        self.start_time = time.time()
        self._frozen = False  # Flag to prevent updates after completion

        # Create progress display
        self.progress = Progress(
            SpinnerColumn(),
            TextColumn("[bold blue]{task.description}"),
            BarColumn(complete_style="green", finished_style="green"),
            TaskProgressColumn(),
            DownloadColumn(),
            TransferSpeedColumn(),
            TimeElapsedColumn(),
            TimeRemainingColumn(),
            TextColumn("[dim]{task.fields[status]}"),
            console=self.console,
            refresh_per_second=4,
        )

        # Initialize overall progress task
        self.overall_task_id = self.progress.add_task(
            "🔄 Initializing batch download...", total=100, status="⏳ Preparing..."
        )

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Add channel to progress tracking."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]
        db_stats = channel_info["db_stats"]

        # Check for database inconsistencies
        inconsistent = channel_info.get("inconsistent", False)
        inconsistency_reason = channel_info.get("inconsistency_reason", "")

        # Modify status to show inconsistency warning
        status_extra = ""
        if inconsistent:
            status_extra = " ⚠️ DB inconsistent"
            db_stats = f"[red]{db_stats}[/red]"

        # Update overall progress description
        self.progress.update(
            self.overall_task_id,
            description=f"📥 Processing {index}/{total}: {name}",
            status=f"📊 {db_stats}{status_extra}",
        )

        # Store channel data
        self.channel_data.append(
            {
                "index": index,
                "name": name,
                "status": f"🔄 Starting...{status_extra}",
                "progress": 0,
                "videos_found": 0,
                "videos_downloaded": 0,
                "speed": "0.0 v/s",
                "inconsistent": inconsistent,
                "inconsistency_reason": inconsistency_reason,
            }
        )

        # Show detailed inconsistency warning
        if inconsistent and inconsistency_reason:
            self.console.print(
                f"[red]⚠️  Database inconsistency for {name}: {inconsistency_reason}[/red]"
            )

        self._update_display()

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Update RSS status with animated feedback."""
        if not self.channel_data:
            return

        status = rss_info["status"]
        rss_info["message"]

        # Update current channel status
        current = self.channel_data[-1]

        if status == "skip":
            current["status"] = "⏭️ No new videos"
            current["progress"] = 100
        elif status == "new_videos":
            count = rss_info.get("scan_count", rss_info.get("missing_count", 0))
            current["status"] = f"🆕 Found {count} new videos"
            current["videos_found"] = count
            current["progress"] = 25
        elif status == "gap_detected":
            current["status"] = "🔍 Checking for updates..."
            current["progress"] = 10
        else:  # error
            current["status"] = "❌ RSS check failed"
            current["progress"] = 0

        # Update overall progress
        self.progress.update(
            self.overall_task_id,
            description=f"📥 Processing {current['index']}: {current['name']}",
            status=current["status"],
            completed=current["progress"],
        )

        self._update_display()

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Update download results with completion animation."""
        if not self.channel_data:
            return

        current = self.channel_data[-1]
        success = result_info["success"]

        if success:
            videos_count = result_info["videos_count"]
            current["videos_downloaded"] = videos_count
            current["status"] = f"✅ Completed ({videos_count} videos)"
            current["progress"] = 100

            # Calculate speed
            elapsed = time.time() - self.start_time
            if elapsed > 0:
                speed = videos_count / elapsed
                current["speed"] = f"{speed:.1f} v/s"
        else:
            error = result_info.get("error", "Failed")[:30]
            current["status"] = f"❌ Failed: {error}"
            current["progress"] = 0

        # Update overall progress
        total_channels = len(self.channel_data)
        completed_channels = sum(1 for ch in self.channel_data if ch["progress"] == 100)
        overall_progress = (
            (completed_channels / total_channels) * 100 if total_channels > 0 else 0
        )

        self.progress.update(
            self.overall_task_id,
            description=f"📥 Batch Progress: {completed_channels}/{total_channels} channels",
            status=f"⚡ {current['status']}",
            completed=overall_progress,
        )

        self._update_display()

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display final summary with performance metrics."""
        successful = summary_info["successful"]
        summary_info["failed"]
        total_channels = summary_info["total_channels"]
        total_videos = summary_info.get("total_videos", 0)

        # Calculate final metrics
        elapsed = time.time() - self.start_time
        videos_per_second = total_videos / elapsed if elapsed > 0 else 0
        channels_per_second = total_channels / elapsed if elapsed > 0 else 0

        # Update final progress
        self.progress.update(
            self.overall_task_id,
            description="🎉 Batch download complete!",
            status=f"⚡ {videos_per_second:.1f} v/s",
            completed=100,
        )

        # Final update to keep progress visible
        self._update_display()

        # Create summary table
        summary_table = Table(title="📊 Performance Summary")
        summary_table.add_column("Metric", style="cyan", no_wrap=True)
        summary_table.add_column("Value", style="green", justify="right")

        summary_table.add_row("Total Time", f"{elapsed:.1f}s")
        summary_table.add_row("Videos Downloaded", str(total_videos))
        summary_table.add_row("Channels Processed", str(total_channels))

        success_rate = (
            (len(successful) / total_channels * 100) if total_channels > 0 else 0
        )
        summary_table.add_row("Success Rate", f"{success_rate:.1f}%")

        summary_table.add_row("Videos/Second", f"{videos_per_second:.1f}")
        summary_table.add_row("Channels/Second", f"{channels_per_second:.1f}")

        # Freeze the live display (keep it visible) and show final summary below
        self._frozen = True
        if self.live_display:
            # Final refresh to ensure completed state is visible
            self.live_display.refresh()

        # Print summary below the frozen progress bar
        self.console.print("\n")
        self.console.print(summary_table)

        # Show completion message
        if success_rate == 100:
            self.console.print(
                "\n🎉 [bold green]All channels processed successfully![/bold green]"
            )
        elif success_rate >= 50:
            self.console.print(
                f"\n⚠️  [yellow]Completed with {success_rate:.0f}% success rate[/yellow]"
            )
        else:
            self.console.print(f"\n❌ [red]Low success rate: {success_rate:.0f}%[/red]")

    def _update_display(self) -> None:
        """Update the live display."""
        if self._frozen:
            return  # Don't update if display is frozen

        if not self.live_display:
            self.live_display = Live(
                self._create_display_layout(),
                console=self.console,
                refresh_per_second=4,
                transient=False,
            )
            self.live_display.start()
        else:
            self.live_display.update(self._create_display_layout())

    def _create_display_layout(self) -> Panel:
        """Create the display layout with progress and channel details."""
        # Create channel status table
        status_table = Table(show_header=True, header_style="bold blue")
        status_table.add_column("#", style="dim", width=3)
        status_table.add_column("Channel", style="yellow", max_width=25)
        status_table.add_column("Status", style="green", max_width=20)
        status_table.add_column("Progress", style="cyan", width=10)
        status_table.add_column("Videos", style="magenta", width=8)

        for channel in self.channel_data[-5:]:  # Show last 5 channels
            status_table.add_row(
                str(channel["index"]),
                (
                    channel["name"][:24] + "..."
                    if len(channel["name"]) > 24
                    else channel["name"]
                ),
                (
                    channel["status"][:19] + "..."
                    if len(channel["status"]) > 19
                    else channel["status"]
                ),
                f"{channel['progress']:.0f}%",
                str(channel["videos_downloaded"]),
            )

        # Combine progress bar and status table
        return Panel(
            f"{self.progress}\n\n{status_table}",
            title="🚀 Live Batch Download Progress",
            border_style="blue",
        )

    def cleanup(self) -> None:
        """Clean up live display after summary is printed."""
        # Now safe to stop - summary has been printed below
        if self.live_display:
            self.live_display.stop()
