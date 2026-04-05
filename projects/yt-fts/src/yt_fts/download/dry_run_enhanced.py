"""
Enhanced Dry-Run Mode for Batch Downloads

Provides detailed preview of what would be downloaded without
actually performing downloads or using API quota.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from rich.console import Console
from rich.table import Table

# Import dependencies for dry-run preview
try:
    from yt_fts.core.database import get_channel_id_from_input, get_num_vids
    from yt_fts.download.fast_channel_resolver import create_fast_resolver
    from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

    _IMPORTS_AVAILABLE = True
except ImportError:
    _IMPORTS_AVAILABLE = False


class PreviewStatus(Enum):
    """Status codes for dry-run preview."""
    SUCCESS = "success"
    CHANNEL_INVALID = "channel_invalid"
    CHANNEL_EXISTS = "channel_exists"
    NEW_VIDEOS = "new_videos"
    RSS_SKIP = "rss_skip"
    API_SKIP = "api_skip"


@dataclass(slots=True)
class ChannelPreview:
    """Preview information for a single channel."""
    channel_input: str
    status: PreviewStatus
    channel_id: str | None = None
    channel_name: str | None = None
    videos_in_db: int = 0
    estimated_new_videos: int = 0
    quota_cost: int = 0
    message: str = ""
    would_download: bool = False


@dataclass(slots=True)
class DryRunSummary:
    """Summary of dry-run preview across all channels."""
    total_channels: int = 0
    valid_channels: int = 0
    channels_with_new_videos: int = 0
    estimated_quota_cost: int = 0
    estimated_new_videos: int = 0
    channels_previewed: list[ChannelPreview] | None = None

    def get_table(self) -> Table:
        """Get Rich Table representation of the summary."""
        table = Table(title="Dry Run Preview Summary")

        table.add_column("Channel", style="cyan")
        table.add_column("Status", style="bold")
        table.add_column("Videos in DB", justify="right")
        table.add_column("Est. New", justify="right")
        table.add_column("Quota", justify="right")
        table.add_column("Message", style="dim")

        for preview in (self.channels_previewed or []):
            # Format status
            status_emoji = {
                PreviewStatus.SUCCESS: "✓",
                PreviewStatus.CHANNEL_INVALID: "✗",
                PreviewStatus.CHANNEL_EXISTS: "≡",
                PreviewStatus.NEW_VIDEOS: "↓",
                PreviewStatus.RSS_SKIP: "⊘",
                PreviewStatus.API_SKIP: "⊘",
            }.get(preview.status, "?")

            # Format quota cost
            quota = f"{preview.quota_cost}" if preview.quota_cost > 0 else "—"

            table.add_row(
                preview.channel_input[:40],
                f"{status_emoji} {preview.status.value}",
                str(preview.videos_in_db),
                str(preview.estimated_new_videos),
                quota,
                preview.message[:50],
            )

        return table


class DryRunPreview:
    """
    Enhanced dry-run preview for batch downloads.

    Provides detailed information about what would happen during
    a batch download without actually performing any downloads.

    Usage:
        preview = DryRunPreview(console=console)

        # Preview channels
        summary = preview.preview_channels(
            channels=["@channel1", "@channel2"],
            cookies_from_browser="firefox",
        )

        # Display summary
        console.print(summary.get_table())
    """

    def __init__(
        self,
        console: Console | None = None,
        verbose: bool = True,
    ) -> None:
        """
        Initialize dry-run preview.

        Args:
            console: Optional Console instance for output
            verbose: Whether to show verbose output
        """
        self.console = console or Console()
        self.verbose = verbose
        self.logger = logging.getLogger(__name__)

    def preview_channels(  # noqa: PLR0913
        self,
        channels: list[str],
        cookies_from_browser: str | None = None,
        max_videos: int | None = None,  # noqa: ARG002
        target_downloads: int | None = None,
        check_rss: bool = True,
        check_api: bool = True,
    ) -> DryRunSummary:
        """
        Preview what would happen during batch download.

        Args:
            channels: List of channel URLs/handles
            cookies_from_browser: Browser for cookie extraction
            max_videos: Max videos per channel
            target_downloads: Target number of channels with downloads
            check_rss: Whether to simulate RSS checks
            check_api: Whether to simulate API checks

        Returns:
            DryRunSummary with preview information
        """
        summary = DryRunSummary()
        summary.total_channels = len(channels)
        summary.channels_previewed = []

        self.console.print("[yellow]── DRY RUN MODE ──[/yellow]")
        self.console.print(
            "[dim]No quota will be used. No downloads will be performed.[/dim]"
        )
        self.console.print("")

        # Check imports availability
        if not _IMPORTS_AVAILABLE:
            self.console.print("[red]Error: Required modules not available[/red]")
            return summary

        # Show quota status
        api_backfill = YouTubeAPIBackfill()
        quota_lines = api_backfill.format_quota_lines()
        self.console.print("[cyan]Current yt-api quota[/cyan]")
        if quota_lines:
            for line in quota_lines:
                self.console.print(f"[cyan]  {line}[/cyan]")
        else:
            self.console.print("[cyan]  No quota data[/cyan]")
        self.console.print("")

        # Resolve channels
        if self.verbose:
            self.console.print(f"[cyan]Resolving {len(channels)} channel(s)...[/cyan]")

        resolver = create_fast_resolver(
            cookies_from_browser=cookies_from_browser,
            console=self.console,
        )
        resolved_channels = resolver.batch_resolve(channels, max_workers=3)

        # Preview each channel
        target_count = 0

        for _idx, (original_input, resolved_url) in enumerate(resolved_channels.items(), 1):
            preview = ChannelPreview(
                channel_input=original_input,
                status=PreviewStatus.SUCCESS,
                quota_cost=0,
                would_download=False,
            )

            # Try to get channel ID
            try:
                channel_id = get_channel_id_from_input(resolved_url)
                preview.channel_id = channel_id
            except (ValueError, KeyError, OSError) as e:
                preview.status = PreviewStatus.CHANNEL_INVALID
                preview.message = f"Failed to resolve channel: {e}"
                summary.channels_previewed.append(preview)
                continue

            summary.valid_channels += 1

            # Check current DB state
            try:
                videos_in_db = get_num_vids(channel_id)
                preview.videos_in_db = videos_in_db
            except (ValueError, OSError):
                preview.videos_in_db = 0

            # Simulate RSS check (lightweight)
            if check_rss:
                preview.quota_cost += 0  # RSS is free
                # In a real scenario, we'd check RSS here
                # For dry-run, we estimate
                preview.estimated_new_videos = 0  # Unknown until actual check
                preview.message = "Would check RSS feed (no quota)"

            # Simulate API check if RSS finds gaps
            if check_api:
                preview.quota_cost += 1  # API stats check costs 1 quota
                preview.message += " + API stats check if RSS finds gaps (1 quota)"

            # Estimate if download would happen
            # For dry-run, we can't know for sure without actually checking
            preview.would_download = True  # Assume yes for preview
            preview.status = PreviewStatus.NEW_VIDEOS
            summary.channels_with_new_videos += 1
            summary.estimated_quota_cost += preview.quota_cost

            target_count += 1
            summary.channels_previewed.append(preview)

            # Stop at target downloads
            if target_downloads and target_count >= target_downloads:
                break

        summary.estimated_new_videos = sum(
            p.estimated_new_videos for p in summary.channels_previewed or []
        )

        # Display summary
        self._display_summary(summary)

        return summary

    def _display_summary(self, summary: DryRunSummary) -> None:
        """Display the dry-run summary to console."""
        self.console.print("")
        self.console.print(summary.get_table())
        self.console.print("")

        # Show totals
        self.console.print(f"[cyan]Valid channels: {summary.valid_channels} / {summary.total_channels}[/cyan]")
        self.console.print(f"[cyan]Channels with downloads: ~{summary.channels_with_new_videos}[/cyan]")
        self.console.print(f"[cyan]Estimated quota cost: {summary.estimated_quota_cost}[/cyan]")
        self.console.print(
            "[dim]Note: Actual new video count unknown until RSS check runs[/dim]"
        )
        self.console.print("")
        self.console.print("[yellow]── Run without --dry-run to execute ──[/yellow]")

    def export_preview(self, summary: DryRunSummary, output_path: Path) -> bool:
        """
        Export dry-run preview to a file.

        Args:
            summary: DryRunSummary to export
            output_path: Path to output file

        Returns:
            True if export was successful
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            with output_path.open("w", encoding="utf-8") as f:
                f.write("# Dry Run Preview Summary\n\n")
                f.write(f"Total channels: {summary.total_channels}\n")
                f.write(f"Valid channels: {summary.valid_channels}\n")
                f.write(f"Channels with downloads: {summary.channels_with_new_videos}\n")
                f.write(f"Estimated quota cost: {summary.estimated_quota_cost}\n\n")

                f.write("## Channel Details\n\n")
                for preview in (summary.channels_previewed or []):
                    f.write(f"- {preview.channel_input}\n")
                    f.write(f"  Status: {preview.status.value}\n")
                    f.write(f"  Videos in DB: {preview.videos_in_db}\n")
                    f.write(f"  Est. new videos: {preview.estimated_new_videos}\n")
                    f.write(f"  Quota cost: {preview.quota_cost}\n")
                    f.write(f"  Message: {preview.message}\n\n")

            return True  # noqa: TRY300

        except OSError:
            self.logger.exception("Failed to export dry-run preview")
            return False


# Convenience function
def preview_batch_download(
    channels: list[str],
    console: Console | None = None,
    cookies_from_browser: str | None = None,
) -> DryRunSummary:
    """
    Preview a batch download without executing.

    Convenience function for quick preview.

    Args:
        channels: List of channel URLs/handles
        console: Optional Console instance
        cookies_from_browser: Browser for cookie extraction

    Returns:
        DryRunSummary with preview information
    """
    preview = DryRunPreview(console=console)
    return preview.preview_channels(
        channels=channels,
        cookies_from_browser=cookies_from_browser,
    )
