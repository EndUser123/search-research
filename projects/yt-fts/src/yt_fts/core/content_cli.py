"""
Content management CLI commands for yt-fts.

This module contains commands for browsing, viewing, and managing downloaded content:
- list: Browse and view downloaded content
- export: Export transcripts
- stats: Show database statistics
- channel-stats: Show channel statistics
- watch: Watch videos with timestamps
- watch-history: Show watch history
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import click

from yt_fts.services.export import ExportHandler
from yt_fts.utils.rich_console import get_console

from .database import get_channel_id_from_input
from .stats import format_stats_as_string, get_database_stats
from .watch import add_watch, extract_video_id, get_watch_history

console = get_console()


def _handle_command_result(result: int | None = None) -> None:
    """
    Handle command execution results consistently without sys.exit().

    Args:
        result: Exit code from command execution (0=success, 1=error, 130=interrupt)
                If None, no action is taken (command handles its own flow control)
    """
    if result is not None:
        # Let Click handle the exit code naturally
        # This allows proper cleanup and maintains CLI behavior
        if result != 0:
            # For non-zero exit codes, we'll raise a SystemExit with the code
            # but this is more controlled than direct sys.exit() calls
            raise SystemExit(result)
        # For success (0), we simply return and let Click complete normally


def _time_to_seconds(time_str: str) -> int:
    """Convert time string to seconds.

    Args:
        time_str: Time string in format HH:MM:SS

    Returns:
        Total seconds (with 3 second buffer subtracted for YouTube links)
    """
    try:
        from yt_fts.utils import time_to_secs
        return time_to_secs(time_str)
    except (ValueError, TypeError, AttributeError):
        return 0


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
def content_cli() -> None:
    """Content management commands for yt-fts."""


@content_cli.command(
    name="list",
    help="""
    Browse and view downloaded content.

    Options:
    --channel <name>: Show all videos for a specific channel
    --transcript <video_id>: Show full transcript for a video

    Enhanced features:
    Channel resolution by name, ID, or @handle
    Video count and duration statistics
    Searchable video listings with metadata
    Direct links to videos and timestamps
    Export capabilities for further analysis
    """,
)
@click.option("-t", "--transcript", default=None, help="Show transcript for a video")
@click.option("-c", "--channel", default=None, help="Show list of videos for a channel")
@click.option("-l", "--library", is_flag=True, help="Show list of channels in library")
def list_command(transcript: str | None, channel: str | None, library: bool) -> None:
    """Browse and view downloaded content."""
    from yt_fts.ui.list_formatter import show_video_list, show_video_transcript

    if transcript:
        show_video_transcript(transcript)
    elif channel:
        channel_id = get_channel_id_from_input(channel)
        if channel_id is None:
            console.print(f"[red]Channel not found: {channel}[/red]")
            raise click.exceptions.Exit(1)
        show_video_list(channel_id)
    elif library:
        from yt_fts.ui.list_formatter import list_channels
        list_channels()
    else:
        from yt_fts.ui.list_formatter import list_channels
        list_channels()


@content_cli.command(
    name="export",
    help="""
    Export transcripts.

    Supported formats: txt, vtt
    """,
)
@click.option(
    "-c",
    "--channel",
    default=None,
    required=True,
    help="The name or id of the channel to export transcripts for",
)
@click.option(
    "-f",
    "--format",
    default="txt",
    help="The format to export transcripts to. Supported formats: txt, vtt",
)
def export_command(channel: str, format: str) -> None:
    """Export transcripts for a channel."""
    export_handler = ExportHandler(scope="channel", format=format, channel=channel)
    export_handler.export()


@content_cli.command(
    name="stats",
    help="""
    Show database statistics.

    Displays:
    - Total number of channels
    - Total number of videos
    - Total number of subtitles
    - Database file size
    """,
)
def stats_command() -> None:
    """Display database statistics."""
    stats_data = get_database_stats()
    output = format_stats_as_string(stats_data)
    click.echo(output, nl=False)


@content_cli.command(
    name="channel-stats",
    help="Show channel file optimization statistics and progress."
)
def channel_stats_command() -> None:
    """Display channel file optimization statistics."""
    from yt_fts.services.channel_file_updater import ChannelFileUpdater

    console = get_console()

    console.print("[bold blue] Channel File Optimization Statistics[/bold blue]")

    try:
        updater = ChannelFileUpdater(console)
        updater.display_optimization_stats()

        # Show cache directory location
        console.print(f"\n📁 [cyan]Cache Directory:[/cyan] {updater.cache_dir}")
        console.print(f"📁 [cyan]Backup Directory:[/cyan] {updater.file_backup_dir}")

    except Exception as e:
        console.print(f"❌ [red]Error loading statistics:[/red] {e!s}")


@content_cli.command(
    name="watch",
    help="""
    Mark a video as watched.

    Adds the video to your watch history with the current timestamp.
    Accepts a video ID or full YouTube URL.

    Examples:
        yt-fts watch abc123
        yt-fts watch https://youtu.be/abc123
        yt-fts watch https://www.youtube.com/watch?v=abc123
    """,
)
@click.argument("video", required=True)
def watch_command(video: str) -> None:
    """Mark a video as watched by adding it to watch history."""
    # Extract video ID from URL if needed
    video_id = extract_video_id(video)

    if video_id is None:
        console.print(f"[red]Invalid video ID or URL: {video}[/red]")
        return

    # Add to watch history
    success = add_watch(video_id)

    if success:
        watched_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        console.print(f"[green]Marked as watched: {video_id}[/green]")
        console.print(f"[dim]Watched at: {watched_at}[/dim]")
    else:
        console.print(f"[yellow]Video {video_id} not found in database[/yellow]")


@content_cli.command(
    name="watch-history",
    help="""
    Show your watch history.

    Displays recently watched videos in descending order (newest first).

    Examples:
        yt-fts watch-history
        yt-fts watch-history --days 7
        yt-fts watch-history --limit 10
        yt-fts watch-history --days 7 --limit 20 --format json
    """,
)
@click.option(
    "--days",
    "-d",
    type=int,
    default=None,
    help="Only show videos watched in the last N days",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    default=50,
    help="Maximum number of records to show (default: 50)",
)
@click.option(
    "--format",
    "output_format",
    default="table",
    type=click.Choice(["table", "json"], case_sensitive=False),
    help="Output format: table (default) or json",
)
def watch_history_command(days: int | None, limit: int, output_format: str) -> None:
    """Show watch history with optional filtering."""
    from rich.table import Table

    history = get_watch_history(days=days, limit=limit)

    if output_format == "json":
        click.echo(json.dumps(history, indent=2))
        return

    if not history:
        console.print("[yellow]No watch history found[/yellow]")
        return

    table = Table(title="Watch History")
    table.add_column("Time", style="dim")
    table.add_column("Video")
    table.add_column("Channel")

    for item in history:
        watched_at = item["watched_at"]
        # Format timestamp for display
        try:
            dt = datetime.fromisoformat(watched_at)
            time_str = dt.strftime("%Y-%m-%d %H:%M")
        except Exception:
            time_str = watched_at

        table.add_row(
            time_str,
            item["video_title"] or item["video_id"],
            item["channel_name"] or "",
        )

    console.print(table)


# Export commands for use by the main CLI
__all__ = [
    "_handle_command_result",
    "_time_to_seconds",
    "channel_stats_command",
    "content_cli",
    "export_command",
    "list_command",
    "stats_command",
    "watch_command",
    "watch_history_command",
]
