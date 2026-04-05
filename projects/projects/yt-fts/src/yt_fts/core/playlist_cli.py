"""
Playlist CLI commands for yt-fts.

This module contains all playlist-related CLI commands extracted from cli.py
for better modularity and maintainability.
"""
import json

import click

from yt_fts.utils.rich_console import get_console

console = get_console()


@click.group(name="playlist", help="Manage playlists")
def playlist_group() -> None:
    """Playlist management commands."""


@playlist_group.command(name="create", help="Create a new playlist")
@click.argument("name")
@click.option("--desc", default="", help="Playlist description", type=str)
def playlist_create(name: str, desc: str) -> None:
    """Create a new playlist.

    Example: yt-fts playlist create "My Favorites" --desc "Best videos"
    """
    from .playlists import create_playlist

    try:
        playlist = create_playlist(name, desc)
        click.secho(f"Created playlist: {playlist['name']}", fg="green")
        if desc:
            click.echo(f"Description: {desc}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@playlist_group.command(name="list", help="List all playlists")
@click.option(
    "--sort",
    "sort_by",
    type=click.Choice(["name", "date", "count"]),
    default="name",
    help="Sort by: name (default), date, or count",
)
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format: table (default) or json",
)
def playlist_list(sort_by: str, output_format: str) -> None:
    """List all playlists with video counts.

    Example: yt-fts playlist list --sort count
    """
    from rich.table import Table

    from .playlists import list_playlists

    playlists = list_playlists(sort_by=sort_by)

    if output_format == "json":
        click.echo(json.dumps(playlists, indent=2))
        return

    if not playlists:
        click.secho("No playlists found.", fg="yellow")
        return

    table = Table(title="Playlists")
    table.add_column("Name", style="cyan")
    table.add_column("Videos", justify="right")
    table.add_column("Description", style="dim")

    for pl in playlists:
        desc = pl["description"][:40] + "..." if len(pl["description"]) > 40 else pl["description"]
        table.add_row(pl["name"], str(pl["video_count"]), desc)

    console.print(table)


@playlist_group.command(name="show", help="Show playlist contents")
@click.argument("name")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format: table (default) or json",
)
def playlist_show(name: str, output_format: str) -> None:
    """Show videos in a playlist.

    Example: yt-fts playlist show "My Favorites"
    """
    from rich.table import Table

    from .playlists import get_playlist_by_name, get_playlist_videos

    playlist = get_playlist_by_name(name)
    if not playlist:
        click.secho(f"Playlist '{name}' not found.", fg="red")
        raise SystemExit(1)

    videos = get_playlist_videos(playlist["id"])

    if output_format == "json":
        output = {
            "name": playlist["name"],
            "description": playlist["description"],
            "created_at": playlist["created_at"],
            "videos": videos,
        }
        click.echo(json.dumps(output, indent=2))
        return

    if not videos:
        click.secho(f"Playlist '{name}' is empty.", fg="yellow")
        return

    table = Table(title=f"Playlist: {name}")
    table.add_column("#", justify="right", width=4)
    table.add_column("Video ID", style="dim")
    table.add_column("Title")
    table.add_column("Channel")

    for v in videos:
        title = v["video_title"][:50] + "..." if len(v["video_title"] or "") > 50 else v["video_title"]
        table.add_row(str(v["position"]), v["video_id"], title, v["channel_name"] or "")

    console.print(table)


@playlist_group.command(name="add", help="Add a video to a playlist")
@click.argument("name")
@click.argument("video_id")
@click.option(
    "--at",
    "position",
    type=int,
    help="Position to insert at (1-based). Default: append to end",
)
def playlist_add(name: str, video_id: str, position: int | None) -> None:
    """Add a video to a playlist.

    Example: yt-fts playlist add "My Favorites" abc123
    Example: yt-fts playlist add "My Favorites" def456 --at 1
    """
    from .playlists import add_video_to_playlist

    try:
        entry = add_video_to_playlist(name, video_id, position)
        click.secho(
            f"Added '{video_id}' to '{name}' at position {entry['position']}",
            fg="green"
        )
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@playlist_group.command(name="remove", help="Remove a video from a playlist")
@click.argument("name")
@click.argument("video_id")
def playlist_remove(name: str, video_id: str) -> None:
    """Remove a video from a playlist.

    Example: yt-fts playlist remove "My Favorites" abc123
    """
    from .playlists import remove_video_from_playlist

    try:
        removed = remove_video_from_playlist(name, video_id)
        if removed:
            click.secho(f"Removed '{video_id}' from '{name}'", fg="green")
        else:
            click.secho(f"Video '{video_id}' not found in '{name}'", fg="yellow")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@playlist_group.command(name="delete", help="Delete a playlist")
@click.argument("name")
@click.option("--yes", "-y", is_flag=True, help="Skip confirmation prompt")
def playlist_delete(name: str, yes: bool) -> None:
    """Delete a playlist.

    Example: yt-fts playlist delete "Old Playlist"
    """
    from .playlists import delete_playlist

    if not yes:
        click.confirm(f"Are you sure you want to delete playlist '{name}'?", abort=True)

    try:
        delete_playlist(name)
        click.secho(f"Deleted playlist: {name}", fg="green")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)


@playlist_group.command(name="export", help="Export a playlist to JSON")
@click.argument("name")
@click.option(
    "--output",
    "-o",
    "output_path",
    help="Output file path. Default: <name>.json",
)
def playlist_export_cmd(name: str, output_path: str | None) -> None:
    """Export a playlist to a JSON file.

    Example: yt-fts playlist export "My Favorites"
    Example: yt-fts playlist export "My Favorites" --output backup.json
    """
    import json as json_lib

    from .playlists import export_playlist

    try:
        data = export_playlist(name)

        # Determine output path
        if output_path is None:
            output_path = f"{name}.json"

        # Write JSON file
        with open(output_path, "w", encoding="utf-8") as f:
            json_lib.dump(data, f, indent=2, ensure_ascii=False)

        click.secho(f"Exported playlist to: {output_path}", fg="green")
        click.echo(f"  Videos: {len(data['videos'])}")
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)
    except Exception as e:
        click.secho(f"Error writing file: {e}", fg="red")
        raise SystemExit(1)


@playlist_group.command(name="import", help="Import a playlist from JSON")
@click.argument("file_path", type=click.Path(exists=True))
def playlist_import_cmd(file_path: str) -> None:
    """Import a playlist from a JSON file.

    Example: yt-fts playlist import backup.json
    """
    import json as json_lib

    from .playlists import import_playlist

    try:
        with open(file_path, encoding="utf-8") as f:
            data = json_lib.load(f)

        # Validate required fields
        if "name" not in data:
            click.secho("Error: Invalid JSON - missing 'name' field", fg="red")
            raise SystemExit(1)

        result = import_playlist(data, rename_if_duplicate=True)

        click.secho(f"Imported playlist: {result['name']}", fg="green")
        click.echo(f"  Videos added: {result['videos_added']}")
    except json_lib.JSONDecodeError as e:
        click.secho(f"Error: Invalid JSON - {e}", fg="red")
        raise SystemExit(1)
    except ValueError as e:
        click.secho(f"Error: {e}", fg="red")
        raise SystemExit(1)
    except Exception as e:
        click.secho(f"Error importing file: {e}", fg="red")
        raise SystemExit(1)
