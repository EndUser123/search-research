"""
Stats module for yt-fts.

Provides database statistics and display formatting for the stats command.
"""

import os

from rich.table import Table

from yt_fts.db.factory import open_connection
from yt_fts.utils.config import get_db_path


# Monkey-patch Rich Table to have a proper __str__ method for testing
# This allows tests to verify table content using str(table)
def _patch_table_str() -> None:
    """Add __str__ method to Rich Table class for testing."""
    from io import StringIO

    from rich.console import Console
    from rich.table import Table  # type: ignore[unused-ignore]

    if not hasattr(Table, "__yt_fts_str_patched"):
        original_str = Table.__str__

        def __str__(self) -> str:
            try:
                console = Console(file=StringIO(), force_terminal=True, width=80)
                console.print(self)
                return console.file.getvalue()  # type: ignore[attr-defined]
            except Exception:
                return original_str(self)

        Table.__str__ = __str__  # type: ignore[method-assign]
        Table.__yt_fts_str_patched = True  # type: ignore[attr-defined]


_patch_table_str()


def get_database_stats() -> dict[str, int | str]:
    """Get database statistics including counts and file size.

    Returns:
        Dictionary with keys:
        - total_channels: Number of channels in the database
        - total_videos: Number of videos in the database
        - total_subtitles: Number of subtitle entries
        - db_size_bytes: Size of the database file in bytes
    """

    db_path = get_db_path()
    stats = {
        "total_channels": 0,
        "total_videos": 0,
        "total_subtitles": 0,
        "db_size_bytes": 0,
    }

    try:
        conn = open_connection(db_path)
        cur = conn.cursor()

        # Count channels
        cur.execute("SELECT COUNT(*) FROM Channels")
        stats["total_channels"] = cur.fetchone()[0]

        # Count videos
        cur.execute("SELECT COUNT(*) FROM Videos")
        stats["total_videos"] = cur.fetchone()[0]

        # Count subtitles
        cur.execute("SELECT COUNT(*) FROM Subtitles")
        stats["total_subtitles"] = cur.fetchone()[0]

        conn.close()

    except Exception:
        # Return zeros if database queries fail
        pass

    # Get database file size
    stats["db_size_bytes"] = get_database_size()

    return stats


def get_database_size() -> int:
    """Get the database file size in bytes.

    Returns:
        Size of the database file in bytes, or 0 if file doesn't exist.
    """
    db_path = get_db_path()

    try:
        if os.path.exists(db_path):
            return os.path.getsize(db_path)
    except Exception:
        pass

    return 0


def format_stats_for_display(stats: dict[str, int | str]) -> Table:
    """Format stats dictionary for display as a Rich table.

    Args:
        stats: Dictionary with database statistics.

    Returns:
        Rich Table instance with formatted stats.
    """
    from yt_fts.display.rich_table_builder import RichTableBuilder

    # Use RichTableBuilder for cleaner table creation
    builder = RichTableBuilder(title="Database Statistics", header_style="bold magenta")
    builder.add_column("Metric", style="cyan")
    builder.add_column("Value", style="green")

    # Add rows for each stat
    builder.add_row("Channels", str(stats.get("total_channels", 0)))
    builder.add_row("Videos", str(stats.get("total_videos", 0)))
    builder.add_row("Subtitles", str(stats.get("total_subtitles", 0)))

    # Format file size in human-readable format
    db_size_bytes = stats.get("db_size_bytes", 0)
    builder.add_row("Database Size", _format_bytes(db_size_bytes))

    return builder.build()


def format_stats_as_string(stats: dict[str, int | str]) -> str:
    """Format stats dictionary as a string for Click output.

    Args:
        stats: Dictionary with database statistics.

    Returns:
        Rendered table as string.
    """
    from yt_fts.display.rich_table_builder import render_table_as_string

    table = format_stats_for_display(stats)
    return render_table_as_string(table)


def _format_bytes(size_bytes: int) -> str:
    """Convert bytes to human-readable format.

    Args:
        size_bytes: Size in bytes.

    Returns:
        Human-readable string (e.g., "1.23 MB").
    """
    if size_bytes == 0:
        return "0 B"

    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    return f"{size:.2f} {units[unit_index]}"
