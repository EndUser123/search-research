"""Batch and Queue CLI commands for yt-fts.

This module contains the Click command groups for batch and queue operations.
These are registered in cli.py via add_command().
"""

import json
from datetime import datetime

import click

from yt_fts.utils.rich_console import get_console

console = get_console()


# ============================================================================
# Batch Commands
# ============================================================================

@click.group(name="batch", help="Batch operations on videos")
def batch_group() -> None:
    """Batch operation commands."""


@batch_group.command(name="delete", help="Delete multiple videos")
@click.argument("video_ids", nargs=-1, required=True)
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def batch_delete_cmd(video_ids: tuple, yes: bool) -> None:
    """Delete multiple videos from the database.

    This deletes both the video record and all associated subtitles.

    Example: yt-fts batch delete abc123 def456
    Example: yt-fts batch delete abc123 --yes
    """
    from .batch import batch_delete_videos

    if not video_ids:
        click.secho("Error: At least one video ID is required", fg="red")
        raise SystemExit(1)

    # Convert tuple to list
    video_id_list = list(video_ids)

    # Confirmation prompt
    if not yes:
        count = len(video_id_list)
        click.echo(f"About to delete {count} video(s) from the database.")
        click.echo("This will delete the video record and all subtitles.")
        click.secho(f"Video IDs: {' '.join(video_id_list[:5])}{'...' if count > 5 else ''}", fg="yellow")
        if not click.confirm("\nContinue?", default=False):
            click.echo("Operation cancelled.")
            raise SystemExit(0)

    result = batch_delete_videos(video_id_list, confirmed=True)

    # Report results
    if result["count"] > 0:
        click.secho(f"Deleted {result['count']} video(s)", fg="green")
        for vid in result["deleted"][:10]:
            click.echo(f"  - {vid}")
        if len(result["deleted"]) > 10:
            click.echo(f"  ... and {len(result['deleted']) - 10} more")

    if result["not_found"]:
        click.secho(f"Video(s) not found: {' '.join(result['not_found'][:10])}", fg="yellow")
        if len(result["not_found"]) > 10:
            click.secho(f"  ... and {len(result['not_found']) - 10} more", fg="yellow")


@batch_group.command(name="export", help="Export multiple videos")
@click.argument("video_ids", nargs=-1, required=True)
@click.option(
    "--format", "-f",
    type=click.Choice(["txt", "srt", "json"]),
    default="txt",
    help="Export format (default: txt)"
)
@click.option("--output", "-o", "output_dir", help="Output directory (default: current directory)")
@click.option("--zip", "zip_output", is_flag=True, help="Create a zip file")
@click.option("--zip-path", help="Path for zip file (required with --zip)")
def batch_export_cmd(
    video_ids: tuple,
    format: str,
    output_dir: str | None,
    zip_output: bool,
    zip_path: str | None,
) -> None:
    """Export multiple videos to files.

    Supported formats: txt, srt, json

    Example: yt-fts batch export abc123 def456 --format txt
    Example: yt-fts batch export abc123 --format srt --output ./exports
    Example: yt-fts batch export abc123 def456 --format txt --zip --zip-path exports.zip
    """
    from .batch import batch_export_videos

    if not video_ids:
        click.secho("Error: At least one video ID is required", fg="red")
        raise SystemExit(1)

    if zip_output and not zip_path:
        click.secho("Error: --zip-path is required when using --zip", fg="red")
        raise SystemExit(1)

    # Convert tuple to list
    video_id_list = list(video_ids)

    # Show progress
    with click.progressbar(video_id_list, label="Exporting") as bar:
        result = batch_export_videos(
            video_id_list,
            format=format,
            output_dir=output_dir,
            zip_output=zip_output,
            zip_path=zip_path,
        )
        for _ in bar:
            pass

    # Report results
    if result["count"] > 0:
        click.secho(f"Exported {result['count']} video(s)", fg="green")
        if zip_output and result["zip_file"]:
            click.echo(f"  Archive: {result['zip_file']}")
        else:
            for file_path in result["files"][:5]:
                click.echo(f"  - {file_path}")
            if len(result["files"]) > 5:
                click.echo(f"  ... and {len(result['files']) - 5} more")

    if result["not_found"]:
        click.secho(f"Video(s) not found: {' '.join(result['not_found'][:10])}", fg="yellow")
        if len(result["not_found"]) > 10:
            click.secho(f"  ... and {len(result['not_found']) - 10} more", fg="yellow")

    if result["failed"]:
        click.secho(f"Failed to export: {' '.join(result['failed'][:10])}", fg="red")
        if len(result["failed"]) > 10:
            click.secho(f"  ... and {len(result['failed']) - 10} more", fg="red")


@batch_group.command(name="add-to-playlist", help="Add multiple videos to a playlist")
@click.argument("playlist_name")
@click.argument("video_ids", nargs=-1, required=True)
def batch_add_to_playlist_cmd(playlist_name: str, video_ids: tuple) -> None:
    """Add multiple videos to a playlist.

    Example: yt-fts batch add-to-playlist "My Favorites" abc123 def456
    """
    from .batch import batch_add_to_playlist

    if not video_ids:
        click.secho("Error: At least one video ID is required", fg="red")
        raise SystemExit(1)

    video_id_list = list(video_ids)

    try:
        result = batch_add_to_playlist(playlist_name, video_id_list)

        if result["count"] > 0:
            click.secho(f"Added {result['count']} video(s) to '{playlist_name}'", fg="green")
            for vid in result["added"][:10]:
                click.echo(f"  - {vid}")
            if len(result["added"]) > 10:
                click.echo(f"  ... and {len(result['added']) - 10} more")

        if result["not_found"]:
            click.secho(f"Video(s) not found: {' '.join(result['not_found'][:10])}", fg="yellow")
            if len(result["not_found"]) > 10:
                click.secho(f"  ... and {len(result['not_found']) - 10} more", fg="yellow")

        if result["already_in_playlist"]:
            click.secho(f"Already in playlist: {' '.join(result['already_in_playlist'][:10])}", fg="dim")
            if len(result["already_in_playlist"]) > 10:
                click.secho(f"  ... and {len(result['already_in_playlist']) - 10} more", fg="dim")

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


# ============================================================================
# Queue Commands
# ============================================================================

@click.group(name="queue", help="Manage watch queue")
def queue_group() -> None:
    """Watch queue management commands."""


@queue_group.command(name="add", help="Add video to watch queue")
@click.argument("video_id")
@click.option(
    "--priority", "-p",
    type=click.Choice(["low", "normal", "high"]),
    default="normal",
    help="Priority level (default: normal)"
)
@click.option("--notes", "-n", help="Optional notes")
def queue_add_cmd(video_id: str, priority: str, notes: str | None) -> None:
    """Add a video to the watch queue.

    Example: yt-fts queue add abc123
    Example: yt-fts queue add abc123 --priority high
    Example: yt-fts queue add abc123 --notes "Check this out"
    """
    from .queue import queue_add

    try:
        result = queue_add(video_id, priority, notes)
        click.secho(f"Added '{video_id}' to queue at position {result['position']}", fg="green")
        if priority != "normal":
            click.echo(f"  Priority: {priority}")
        if notes:
            click.echo(f"  Notes: {notes}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@queue_group.command(name="list", help="List watch queue")
@click.option(
    "--filter", "-f",
    type=click.Choice(["all", "low", "normal", "high"]),
    default="all",
    help="Filter by priority (default: all)"
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
def queue_list_cmd(filter: str, output_format: str) -> None:
    """List all videos in the watch queue.

    Example: yt-fts queue list
    Example: yt-fts queue list --filter high
    Example: yt-fts queue list --format json
    """
    from rich.table import Table

    from .queue import queue_list

    items = queue_list(filter_priority=filter)

    if output_format == "json":
        click.echo(json.dumps(items, indent=2))
        return

    if not items:
        click.secho("Queue is empty.", fg="yellow")
        return

    # Build plain text output for testability
    for item in items:
        click.echo(f"{item['position']}. {item['video_id']} - {item.get('video_title', 'Unknown')} ({item['priority']})")

    # Also show Rich table for interactive use
    table = Table(title=f"Watch Queue ({len(items)} items)")
    table.add_column("#", justify="right", width=4)
    table.add_column("Video ID", style="cyan")
    table.add_column("Title", style="green")
    table.add_column("Priority", width=8)
    table.add_column("Added", style="dim")

    for item in items:
        # Format priority
        priority = item["priority"]
        priority_style = {
            "high": "red",
            "normal": "white",
            "low": "dim",
        }.get(priority, "")

        # Format added_at
        try:
            dt = datetime.fromisoformat(item["added_at"])
            added_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            added_str = item["added_at"]

        # Truncate title (handle None when video was deleted)
        title_raw = item.get("video_title") or ""
        title = title_raw[:40]
        if len(title_raw) > 40:
            title += "..."

        table.add_row(
            str(item["position"]),
            item["video_id"],
            title,
            f"[{priority_style}]{priority}[/{priority_style}]",
            added_str,
        )

    console.print(table)


@queue_group.command(name="remove", help="Remove video from queue")
@click.argument("position", type=int)
def queue_remove_cmd(position: int) -> None:
    """Remove a video from the queue by position.

    Example: yt-fts queue remove 1
    """
    from .queue import queue_remove

    try:
        result = queue_remove(position)
        click.secho(f"Removed video at position {position}", fg="green")
        click.echo(f"  Video ID: {result['video_id']}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@queue_group.command(name="promote", help="Move video up in queue")
@click.argument("position", type=int)
@click.option("--to", "to_position", type=int, help="Target position")
def queue_promote_cmd(position: int, to_position: int | None) -> None:
    """Promote a video in the queue (move it up).

    Example: yt-fts queue promote 3
    Example: yt-fts queue promote 5 --to 2
    """
    from .queue import queue_promote

    try:
        result = queue_promote(position, to_position)
        if result["moved"]:
            click.secho(
                f"Moved '{result['video_id']}' from position {result['from_position']} to {result['to_position']}",
                fg="green"
            )
        else:
            click.echo(f"Already at target position {position}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@queue_group.command(name="demote", help="Move video down in queue")
@click.argument("position", type=int)
@click.option("--to", "to_position", type=int, help="Target position")
def queue_demote_cmd(position: int, to_position: int | None) -> None:
    """Demote a video in the queue (move it down).

    Example: yt-fts queue demote 1
    Example: yt-fts queue demote 1 --to 4
    """
    from .queue import queue_demote

    try:
        result = queue_demote(position, to_position)
        if result["moved"]:
            click.secho(
                f"Moved '{result['video_id']}' from position {result['from_position']} to {result['to_position']}",
                fg="green"
            )
        else:
            click.echo(f"Already at target position {position}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@queue_group.command(name="save", help="Save queue to file")
@click.option("--file", "file_path", help="Output file path")
def queue_save_cmd(file_path: str | None) -> None:
    """Save the watch queue to a JSON file.

    Example: yt-fts queue save
    Example: yt-fts queue save --file backup.json
    """
    from .queue import queue_save

    result = queue_save(file_path)
    click.secho(f"Saved {result['items_saved']} item(s) to: {result['file']}", fg="green")


@queue_group.command(name="load", help="Load queue from file")
@click.option("--file", "file_path", help="Input file path")
@click.option("--replace", is_flag=True, help="Replace existing queue")
def queue_load_cmd(file_path: str | None, replace: bool) -> None:
    """Load the watch queue from a JSON file.

    Example: yt-fts queue load
    Example: yt-fts queue load --file backup.json
    Example: yt-fts queue load --replace
    """
    from .queue import queue_load

    try:
        result = queue_load(file_path, replace=replace)

        if result["added"]:
            click.secho(f"Added {len(result['added'])} video(s) to queue", fg="green")
            for vid in result["added"][:5]:
                click.echo(f"  - {vid}")
            if len(result["added"]) > 5:
                click.echo(f"  ... and {len(result['added']) - 5} more")

        if result["duplicates"]:
            click.secho(f"Already in queue: {' '.join(result['duplicates'][:5])}", fg="bright_black")
            if len(result["duplicates"]) > 5:
                click.secho(f"  ... and {len(result['duplicates']) - 5} more", fg="bright_black")

        if result["errors"]:
            click.secho(f"Errors: {len(result['errors'])}", fg="red")

    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@queue_group.command(name="clear", help="Clear all items from queue")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation")
def queue_clear_cmd(yes: bool) -> None:
    """Remove all items from the watch queue.

    Example: yt-fts queue clear
    Example: yt-fts queue clear --yes
    """
    from .queue import queue_clear

    if not yes and not click.confirm("Clear all items from the queue?", default=False):
            click.echo("Operation cancelled.")
            raise SystemExit(0)

    count = queue_clear(confirmed=True)
    click.secho(f"Cleared {count} item(s) from queue", fg="green")


@queue_group.command(name="stats", help="Show queue statistics")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (default: table)"
)
def queue_stats_cmd(output_format: str) -> None:
    """Show statistics about the watch queue.

    Example: yt-fts queue stats
    Example: yt-fts queue stats --format json
    """
    from .queue import queue_stats

    stats = queue_stats()

    if output_format == "json":
        click.echo(json.dumps(stats, indent=2))
        return

    click.secho("Queue Statistics", fg="cyan", bold=True)
    click.echo(f"  Total items: {stats['total']}")
    click.echo("  By priority:")
    for priority, count in stats["by_priority"].items():
        click.echo(f"    - {priority}: {count}")
    if stats["oldest_at"]:
        click.echo(f"  Oldest: {stats['oldest_at']}")
    if stats["newest_at"]:
        click.echo(f"  Newest: {stats['newest_at']}")
