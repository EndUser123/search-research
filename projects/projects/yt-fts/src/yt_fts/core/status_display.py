"""
Status display module for yt-fts.

Provides system status information including database stats,
quota usage, and configuration details.
"""

import threading
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from yt_fts.utils.config import get_db_path

from .database import (
    get_batch_channel_stats,
)


def _execute_with_timeout(func, timeout_seconds=5.0):
    """
    Execute a function with a timeout using threading.

    If the function doesn't complete within the timeout, returns None.
    """
    result = [None]
    exception = [None]

    def worker():
        try:
            result[0] = func()
        except Exception as e:
            exception[0] = e

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    thread.join(timeout=timeout_seconds)

    if thread.is_alive():
        # Thread is still running - timeout
        return None
    if exception[0]:
        raise exception[0]
    return result[0]


class StatusDisplay:
    """
    Display system status information.

    Provides formatted status displays for the yt-fts system including
    database statistics, quota information, and configuration details.
    """

    def __init__(self, console: Console | None = None):
        """
        Initialize the status display.

        Args:
            console: Optional Rich console instance. Creates a new one if not provided.
        """
        self.console = console or Console()
        self.db_path = get_db_path()

    def _get_all_stats(self) -> dict:
        """Get all database and quota stats efficiently.

        Optimized: Single connection for all queries (was 5 separate connections).
        Uses timeout wrapper to prevent hanging in test environments.
        """
        stats = {
            "channels": 0,
            "videos": 0,
            "subtitles": 0,
            "with_transcripts": 0,
            "quota_used": 0,
            "quota_limit": 0,  # Will be set from actual quota system
        }

        def _query_database():
            """Inner function to query database - will be wrapped with timeout."""
            import sqlite3
            from datetime import date as date_module

            local_stats = {
                "channels": 0,
                "videos": 0,
                "subtitles": 0,
                "with_transcripts": 0,
                "quota_used": 0,
            }

            # Single connection, reused for all queries
            conn = sqlite3.connect(f"file:{self.db_path}?mode=ro", uri=True, timeout=30.0)
            cursor = conn.cursor()
            today = str(date_module.today())

            # Multiple queries but same connection = much faster
            cursor.execute("SELECT COUNT(*) FROM Channels")
            local_stats["channels"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Videos")
            local_stats["videos"] = cursor.fetchone()[0]
            cursor.execute("SELECT COUNT(*) FROM Subtitles")
            local_stats["subtitles"] = cursor.fetchone()[0]
            # COUNT DISTINCT is much faster than correlated EXISTS
            cursor.execute("SELECT COUNT(DISTINCT video_id) FROM Subtitles")
            local_stats["with_transcripts"] = cursor.fetchone()[0]
            cursor.execute("SELECT COALESCE(quota_used, 0) FROM yt_api_quota WHERE date = ?", (today,))
            quota_row = cursor.fetchone()
            if quota_row:
                local_stats["quota_used"] = quota_row[0]

            cursor.close()
            conn.close()
            return local_stats

        try:
            # Use timeout wrapper to prevent hanging
            db_stats = _execute_with_timeout(_query_database, timeout_seconds=5.0)
            if db_stats:
                stats.update(db_stats)
        except Exception:
            # Database locked or unavailable - return default zeros
            pass

        # Get actual quota limit from YouTubeAPIBackfill (more accurate than hardcoded)
        try:
            from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill
            quota_info = YouTubeAPIBackfill.get_global_quota_info()
            # Use or to ensure we get a value even if quota_info has None (not missing key)
            stats["quota_limit"] = quota_info.get("limit") or 10000
            stats["quota_remaining"] = quota_info.get("remaining") or 10000
        except Exception:
            # Fallback to default if quota system unavailable
            if stats["quota_limit"] == 0:
                stats["quota_limit"] = 10000
            stats["quota_remaining"] = stats["quota_limit"] - stats["quota_used"]

        return stats

    def _get_db_stats(self) -> dict[str, Any]:
        """Get database statistics (kept for compatibility)."""
        stats = self._get_all_stats()
        return {
            "channels": stats["channels"],
            "videos": stats["videos"],
            "subtitles": stats["subtitles"],
            "with_transcripts": stats["with_transcripts"],
        }

    def _get_quota_info(self) -> dict[str, Any]:
        """Get quota info (kept for compatibility)."""
        stats = self._get_all_stats()
        return {
            "used": stats["quota_used"],
            "limit": stats["quota_limit"],
            "remaining": stats["quota_limit"] - stats["quota_used"],
        }

    def display_minimal_status(self) -> None:
        """Display minimal status information."""
        import sys
        sys.stderr.write(" Computing database stats...\r")
        sys.stderr.flush()

        stats = self._get_all_stats()
        self._get_quota_info()

        # Clear the progress line
        sys.stderr.write(" " * 40 + "\r")

        # Simple text output, no table - use stderr to ensure visibility
        sys.stderr.write(f" Channels          {stats['channels']:,}\n")
        sys.stderr.write(f" Videos            {stats['videos']:,}\n")
        sys.stderr.write(f" Subtitles         {stats['subtitles']:,}\n")
        sys.stderr.write(f" With Transcripts  {stats['with_transcripts']:,}\n")
        sys.stderr.write(f" Quota Used        {stats['quota_used']:,} / {stats['quota_limit']:,}\n")
        sys.stderr.flush()

    def display_status_line(self) -> None:
        """Display a single-line status update."""
        stats = self._get_db_stats()
        self.console.print(
            f"[dim]Channels: {stats['channels']:,} | "
            f"Videos: {stats['videos']:,} | "
            f"Subtitles: {stats['subtitles']:,}[/dim]"
        )

    def display_full_status(self) -> None:
        """Display comprehensive status information."""
        stats = self._get_db_stats()
        quota = self._get_quota_info()

        # Main status panel
        status_text = f"""[bold cyan]Database[/bold cyan]
  Channels: {stats['channels']:,}
  Videos: {stats['videos']:,}
  Subtitles: {stats['subtitles']:,}
  With Transcripts: {stats['with_transcripts']:,}
  Path: {self.db_path}
  Size: {_format_size(self.db_path)}

[bold cyan]API Quota[/bold cyan]
  Used: {stats['quota_used']:,} / {stats['quota_limit']:,}
  Remaining: {quota['remaining']:,}"""

        self.console.print(Panel(status_text, title="[bold green]System Status[/bold green]", border_style="cyan"))

    def display_config(self, active_file: str | None = None) -> None:
        """Display configuration information."""
        from yt_fts.utils.config import config_dir

        config_path = Path(config_dir())

        config_text = f"""[bold cyan]Config Directory[/bold cyan]
  {config_path}

[bold cyan]Database[/bold cyan]
  {self.db_path}"""

        if active_file:
            config_text += f"\n\n[bold cyan]Active Input File[/bold cyan]\n  {active_file}"

        self.console.print(Panel(config_text, title="[bold green]Configuration[/bold green]", border_style="cyan"))


def _format_size(path: str) -> str:
    """Format file size in human-readable format."""
    try:
        size = Path(path).stat().st_size
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
    except Exception:
        return "Unknown"


def show_status(
    detailed: bool = False,
    config: bool = True,
    active_file: str | None = None,
    console: Console | None = None
) -> None:
    """
    Show system status information.

    Args:
        detailed: Whether to show detailed status.
        config: Whether to show configuration information.
        active_file: Optional path to the active input file.
        console: Optional Rich console instance.
    """
    status = StatusDisplay(console)

    if detailed:
        status.display_full_status()
    else:
        status.display_minimal_status()

    if config:
        status.display_config(active_file)

    # Show top channels by video count if detailed
    if detailed:
        _show_top_channels(status.console)


def _show_top_channels(console: Console) -> None:
    """Show top channels by video count."""
    try:
        from yt_fts.core.database import get_channels

        channels = get_channels()

        if not channels:
            console.print("[dim]No channels in database[/dim]")
            return

        # Get stats for top 5 channels
        channel_ids = [ch[1] for ch in channels[:5]]
        stats = get_batch_channel_stats(channel_ids)

        table = Table(title="[bold cyan]Top Channels by Video Count[/bold cyan]")
        table.add_column("Channel", style="cyan")
        table.add_column("Videos", justify="right", style="green")
        table.add_column("With Subs", justify="right", style="yellow")

        has_data = False
        for channel_id, channel_name, _, _ in channels[:5]:
            if channel_id in stats:
                ch_stats = stats[channel_id]
                table.add_row(
                    channel_name[:30] if len(channel_name) > 30 else channel_name,
                    f"{ch_stats.get('total', 0):,}",
                    f"{ch_stats.get('with_transcripts', 0):,}"
                )
                has_data = True

        if has_data:
            console.print(table)
        else:
            console.print("[dim]No channel statistics available yet[/dim]")
    except Exception as e:
        console.print(f"[dim]Could not load channel stats: {e}[/dim]")
