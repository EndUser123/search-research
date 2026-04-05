"""
Detailed display plugin - enhanced verbose output for batch downloads.
"""
from __future__ import annotations

from typing import Any

from .base import RSS_STATUS_ICONS, DisplayPlugin


class DetailedDisplayPlugin(DisplayPlugin):
    """
    Detailed display plugin that shows comprehensive information.

    Provides maximum verbosity with:
    - Full channel and database statistics
    - Detailed RSS status with metadata
    - Comprehensive download results with timing
    - Progress indicators and status updates
    - Enhanced error reporting with suggestions
    """

    name = "detailed"
    description = (
        "Comprehensive verbose output with full statistics and enhanced error reporting"
    )
    category = "verbose"

    def display_channel_header(self, channel_info: dict[str, Any]) -> None:
        """Display detailed channel header with full information."""
        index = channel_info["index"]
        total = channel_info["total"]
        name = channel_info["name"]
        db_stats = channel_info["db_stats"]

        # Check for database inconsistencies
        inconsistent = channel_info.get("inconsistent", False)
        inconsistency_reason = channel_info.get("inconsistency_reason", "")

        self.console.print(
            f"\n[bold cyan]Channel {index}/{total}:[/bold cyan] [yellow]{name}[/yellow]"
        )
        if inconsistent:
            self.console.print(
                f"[red]⚠️  Database inconsistency: {inconsistency_reason}[/red]"
            )
        self.console.print(f"[dim]Database status: {db_stats}[/dim]")
        self.console.print("[dim]" + "─" * 60 + "[/dim]")

    def display_rss_status(self, rss_info: dict[str, Any]) -> None:
        """Display detailed RSS status with full context."""
        status = rss_info["status"]
        message = rss_info["message"]

        status_icon = RSS_STATUS_ICONS.get(status, "❓")

        self.console.print(f"[blue]RSS Check:[/blue] {status_icon} {message}")

        if rss_info.get("missing_count"):
            self.console.print(
                f"[dim]  └─ Missing videos: {rss_info['missing_count']}[/dim]"
            )
        if rss_info.get("scan_count"):
            self.console.print(
                f"[dim]  └─ Videos to scan: {rss_info['scan_count']}[/dim]"
            )
        if rss_info.get("error_msg"):
            self.console.print(f"[red]  └─ Error: {rss_info['error_msg']}[/red]")

    def display_download_result(self, result_info: dict[str, Any]) -> None:
        """Display comprehensive download results."""
        success = result_info["success"]

        if success:
            videos_count = result_info["videos_count"]
            videos_without_subtitles = result_info.get("videos_without_subtitles", 0)
            total_videos = result_info.get("total_videos", videos_count)

            self.console.print("[green]✅ Download successful![/green]")
            self.console.print(f"  └─ Videos saved: {videos_count}")
            if videos_without_subtitles > 0:
                self.console.print(
                    f"  └─ Videos without subtitles: {videos_without_subtitles}"
                )
            self.console.print(f"  └─ Total videos processed: {total_videos}")
        else:
            error = result_info.get("error", "Unknown error")
            self.console.print("[red]❌ Download failed[/red]")
            self.console.print(f"  └─ Error: {error}")

            # Add helpful suggestions based on error type
            if "rate limit" in error.lower():
                self.console.print(
                    "  └─ [yellow]Suggestion: Try again later or use cookies[/yellow]"
                )
            elif "not found" in error.lower():
                self.console.print(
                    "  └─ [yellow]Suggestion: Verify channel URL/handle[/yellow]"
                )
            elif "timeout" in error.lower():
                self.console.print(
                    "  └─ [yellow]Suggestion: Check internet connection[/yellow]"
                )

        self.console.print()  # Extra spacing

    def display_batch_summary(self, summary_info: dict[str, Any]) -> None:
        """Display comprehensive batch summary."""
        successful = summary_info["successful"]
        failed = summary_info["failed"]
        total_channels = summary_info["total_channels"]
        total_videos = summary_info.get("total_videos", 0)

        self.console.print("\n" + "=" * 60)
        self.console.print("[bold magenta]🎯 BATCH DOWNLOAD SUMMARY[/bold magenta]")
        self.console.print("=" * 60)

        self.console.print("\n📊 [bold]Overall Statistics:[/bold]")
        self.console.print(f"  • Channels processed: {total_channels}")
        self.console.print(f"  • Channels successful: {len(successful)}")
        self.console.print(f"  • Channels failed: {len(failed)}")
        self.console.print(f"  • Total videos downloaded: {total_videos}")

        if successful:
            avg_videos = total_videos / len(successful)
            self.console.print(f"  • Average videos per channel: {avg_videos:.1f}")

        if successful:
            self.console.print("\n✅ [bold]Successful Channels:[/bold]")
            for result in successful[:5]:  # Show first 5
                videos = result.get("videos_count", 0)
                self.console.print(
                    f"  • {result.get('channel', 'Unknown')}: {videos} videos"
                )
            if len(successful) > 5:
                self.console.print(f"  • ... and {len(successful) - 5} more")

        if failed:
            self.console.print("\n❌ [bold]Failed Channels:[/bold]")
            for result in failed[:3]:  # Show first 3
                error = result.get("error", "Unknown error")[:50]
                self.console.print(f"  • {result.get('channel', 'Unknown')}: {error}")
            if len(failed) > 3:
                self.console.print(f"  • ... and {len(failed) - 3} more")

        self.console.print("\n" + "=" * 60)
