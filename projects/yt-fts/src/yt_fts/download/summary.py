"""
Summary and reporting utilities for batch download operations.

Provides functions for displaying download results, exporting reports,
and validating channels.
"""
from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console


def print_summary(
    console: Console,
    results: dict,
    all_channels: list,
    continue_on_error: bool = True,
) -> None:
    """
    Print a comprehensive summary of the download results.

    Args:
        console: Rich console instance
        results: Results dict with successful, failed, skipped, invalid_channels keys
        all_channels: List of all channels that were processed
        continue_on_error: Whether errors allow continuing to other channels
    """
    from yt_fts.core.database import cleanup_channels
    from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

    # Run automatic database cleanup
    cleanup_result = cleanup_channels()

    successful_count = len(results["successful"])
    failed_count = len(results["failed"])
    total_count = successful_count + failed_count

    # Count channels that actually had downloads (videos saved)
    channels_with_downloads = sum(
        1 for r in results["successful"] if r.get("videos_count", 0) > 0
    )
    channels_skipped = successful_count - channels_with_downloads

    # Calculate progress
    total_channels = len(all_channels)
    channels_remaining = total_channels - total_count
    progress_pct = (total_count / total_channels * 100) if total_channels > 0 else 0

    # Video counts
    total_videos = sum(r.get("videos_count", 0) for r in results["successful"])

    # Quota info
    quota_info = YouTubeAPIBackfill.get_global_quota_info()
    # quota_info already contains TOTAL limit across all keys (no need to multiply by num_keys)
    total_limit = quota_info["limit"]
    quota_remaining = quota_info["remaining"]
    quota_pct = quota_info.get("percentage", 0)

    console.print("\n[bold cyan]╭────────────────────────────────────────────────╮[/bold cyan]")
    console.print("[bold cyan]│[/bold cyan] [bold]Batch Download Summary[/bold]                    [bold cyan]│[/bold cyan]")
    console.print("[bold cyan]╰────────────────────────────────────────────────╯[/bold cyan]\n")

    # Channel Results
    console.print("[bold]Channels:[/bold]")
    console.print(f"  ✓ With downloads:  [green]{channels_with_downloads}[/green]")
    if channels_skipped > 0:
        console.print(f"  ⏭ Skipped (no new): [dim]{channels_skipped}[/dim]")
    if failed_count > 0:
        console.print(f"  ✗ Failed: [red]{failed_count}[/red]")
    console.print()

    # Progress
    console.print("[bold]Progress:[/bold]")
    console.print(f"  Processed: {total_count}/{total_channels} ({progress_pct:.1f}%)")
    console.print(f"  Remaining: {channels_remaining} channels")
    console.print()

    # Videos
    console.print("[bold]Videos:[/bold]")
    console.print(f"  Downloaded: [cyan]{total_videos}[/cyan]")
    console.print()

    # Quota
    console.print("[bold]Quota:[/bold]")
    console.print(f"  Used: {quota_info['used']:,} / {total_limit:,} ({quota_pct:.1f}%)")
    console.print(f"  Remaining: [green]{quota_remaining:,}[/green]")
    console.print()

    # Database Cleanup (automatic)
    if cleanup_result["skipped_removed"] > 0:
        console.print("[bold]Database Cleanup:[/bold]")
        console.print(
            f"  ✗ Removed: [red]{cleanup_result['skipped_removed']}[/red] failed channels"
        )
        console.print()

    # Show channels that don't exist (404s filtered during pre-validation)
    if results.get("invalid_channels"):
        count = len(results["invalid_channels"])
        console.print(f"[bold]Channels not found: {count}[/bold]")
        # Only list them if there are fewer than 10
        if count < 10:
            for channel in results["invalid_channels"]:
                console.print(f"  ✗ {channel}")
        console.print()

    # Error message for failures
    if results["failed"] and not continue_on_error:
        console.print(
            "[yellow]💡 Use --continue-on-error to continue with other channels[/yellow]"
        )


def export_report(results: dict, filename: str, console: Console) -> None:
    """
    Export download results to a JSON file.

    Args:
        results: Results dict to export
        filename: Path to output file
        console: Rich console instance for error messages
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
    except FileNotFoundError:
        console.print(
            f"[red]Error: Directory does not exist: {Path(filename).parent}[/red]"
        )
    except PermissionError:
        console.print(
            f"[red]Error: Permission denied writing to: {filename}[/red]"
        )
    except OSError as e:
        console.print(
            f"[red]Error writing report to {filename}: {e}[/red]"
        )
    except Exception as e:
        console.print(f"[red]Unexpected error writing report: {e}[/red]")


def validate_channels(channels: list[str], console: Console) -> list[str]:
    """
    Validate channel formats and return valid channels.

    Args:
        channels: List of channel inputs to validate
        console: Rich console instance for warning messages

    Returns:
        List[str]: List of valid channel URLs/handles
    """
    valid_channels = []
    for channel in channels:
        channel = channel.strip()
        if not channel:
            continue

        # Basic validation - check if it looks like a YouTube channel
        if (
            channel.startswith("@")
            or "youtube.com/channel/" in channel
            or "youtube.com/c/" in channel
            or "youtube.com/@" in channel
            or "youtu.be/" in channel
        ):
            valid_channels.append(channel)
        else:
            console.print(
                f"[yellow]Warning: '{channel}' doesn't look like a valid YouTube channel[/yellow]"
            )

    return valid_channels
