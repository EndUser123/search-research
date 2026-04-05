"""
Bookmark commands for yt-fts.

Provides CLI commands for managing video bookmarks including add, list, and remove.
"""
from __future__ import annotations

import json
from datetime import datetime
from typing import Any

import click

from yt_fts.utils.rich_console import get_console

console = get_console()


# ============================================================================
# Bookmark Commands
# ============================================================================

@click.group(name="bookmark", help="Manage video bookmarks")
def bookmark_group() -> None:
    """Bookmark management commands."""


@bookmark_group.command(name="add", help="Add a bookmark to a video")
@click.argument("video_id")
@click.argument("timestamp")
@click.argument("note", nargs=-1)  # Allow multi-line notes
def bookmark_add(video_id: str, timestamp: str, note: tuple[Any, ...]) -> None:
    """Add a bookmark at a specific timestamp.

    Example: yt-fts bookmark add abc123 1:23 "Interesting point"
    Example: yt-fts bookmark add abc123 83 "Point at 1:23"

    TIMESTAMP can be in various formats:
    - MM:SS (e.g., 1:23)
    - HH:MM:SS (e.g., 1:23:45)
    - Raw seconds (e.g., 83)
    """
    from .playlists import create_bookmark

    # Combine note arguments (allows quotes and spaces)
    note_text = " ".join(note) if note else ""

    try:
        bookmark = create_bookmark(video_id, timestamp, note_text)
        click.secho(
            f"Added bookmark at {timestamp} for '{video_id}'",
            fg="green"
        )
        click.echo(f"  ID: {bookmark['id']}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@bookmark_group.command(name="list", help="List bookmarks")
@click.option("--video", "video_id", help="Filter by video ID")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format: table (default) or json",
)
def bookmark_list(video_id: str | None, output_format: str) -> None:
    """List all bookmarks, optionally filtered by video.

    Example: yt-fts bookmark list
    Example: yt-fts bookmark list --video abc123
    """
    from rich.table import Table

    from .playlists import list_bookmarks

    bookmarks = list_bookmarks(video_id=video_id)

    if output_format == "json":
        click.echo(json.dumps(bookmarks, indent=2))
        return

    if not bookmarks:
        if video_id:
            click.secho(f"No bookmarks found for video '{video_id}'.", fg="yellow")
        else:
            click.secho("No bookmarks found.", fg="yellow")
        return

    table = Table(title="Bookmarks")
    table.add_column("ID", justify="right", width=6)
    table.add_column("Video ID", style="dim")
    table.add_column("Timestamp", style="cyan")
    table.add_column("Note")
    table.add_column("Created", style="dim")

    for bm in bookmarks:
        note = bm["note"][:40] + "..." if len(bm["note"]) > 40 else bm["note"]
        # Format created_at timestamp
        try:
            dt = datetime.fromisoformat(bm["created_at"])
            created_str = dt.strftime("%Y-%m-%d %H:%M")
        except (ValueError, TypeError):
            created_str = bm["created_at"]

        table.add_row(
            str(bm["id"]),
            bm["video_id"],
            bm["timestamp"],
            note,
            created_str,
        )

    console.print(table)


@bookmark_group.command(name="remove", help="Delete a bookmark")
@click.argument("bookmark_id", type=int)
def bookmark_remove(bookmark_id: int) -> None:
    """Delete a bookmark by its ID.

    Example: yt-fts bookmark remove 1
    """
    from .playlists import delete_bookmark

    deleted = delete_bookmark(bookmark_id)

    if deleted:
        click.secho(f"Deleted bookmark {bookmark_id}", fg="green")
    else:
        click.secho(f"Bookmark {bookmark_id} not found", fg="yellow")
