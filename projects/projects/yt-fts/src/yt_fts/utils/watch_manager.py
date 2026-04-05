"""
Watch mode for automatic channel updates.

Monitors channels for new uploads and automatically downloads transcripts.
"""

from datetime import datetime
from typing import Literal

from rich.console import Console
from sqlite_utils import Database

from yt_fts.core.database import get_channel_id_from_input, get_vid_ids_by_channel_id
from yt_fts.utils.config import get_db_path

WatchInterval = Literal["hourly", "daily", "weekly"]


class WatchManager:
    """Manage watch jobs for automatic channel updates."""

    def __init__(self) -> None:
        """
        Initialize the watch manager.

        Sets up the console for output and initializes the database connection.
        Creates the WatchJobs table if it doesn't exist.
        """
        self.console = Console()
        self.db = Database(get_db_path())

        # Ensure watch_jobs table exists
        self._ensure_table()

    def _ensure_table(self) -> None:
        """Create WatchJobs table if it doesn't exist."""
        try:
            self.db["WatchJobs"].create(
                {
                    "job_id": int,
                    "channel_id": str,
                    "channel_name": str,
                    "interval": str,  # hourly, daily, weekly
                    "last_run": str,  # ISO timestamp
                    "last_video_count": int,  # Number of videos on last run
                    "enabled": int,  # 0 = disabled, 1 = enabled
                    "created_at": str,
                },
                pk="job_id",
                not_null={"channel_id", "interval", "enabled"},
                if_not_exists=True,
            )
        except Exception as e:
            self.console.print(f"[yellow]Warning:[/yellow] Could not create WatchJobs table: {e}")

    def add_watch_job(
        self,
        channel: str,
        interval: WatchInterval | str = "daily",
        enabled: bool = True,
    ) -> bool:
        """
        Add a channel to watch list.

        Args:
            channel: Channel handle, URL, or ID
            interval: Check interval (hourly, daily, weekly)
            enabled: Whether job is enabled

        Returns:
            True if successful, False otherwise
        """
        try:
            # Resolve channel ID
            channel_id = get_channel_id_from_input(channel)

            # Check if channel exists
            vid_ids = get_vid_ids_by_channel_id(channel_id)
            if not vid_ids:
                self.console.print(
                    f"[yellow]Warning:[/yellow] Channel '{channel}' has no videos in database."
                )
                self.console.print(
                    "[i]Tip: Download the channel first with: yt-fts download {channel}[/i]"
                )

            # Get channel name
            channel_name = self.db.execute(
                "SELECT channel_name FROM Channels WHERE channel_id = ?", [channel_id]
            ).fetchone()

            if not channel_name:
                self.console.print(f"[red]Error:[/red] Channel '{channel}' not found in database")
                return False

            channel_name = channel_name[0]

            # Check if job already exists
            existing = self.db.execute(
                "SELECT job_id FROM WatchJobs WHERE channel_id = ?", [channel_id]
            ).fetchone()

            if existing:
                self.console.print(
                    f"[yellow]Warning:[/yellow] Channel '{channel_name}' is already being watched"
                )
                # Update interval if different
                self.db.execute(
                    "UPDATE WatchJobs SET interval = ? WHERE channel_id = ?",
                    [interval, channel_id],
                )
                self.console.print(f"[green]✓[/green] Updated interval to '{interval}'")
                return True

            # Add new watch job
            self.db["WatchJobs"].insert(
                {
                    "channel_id": channel_id,
                    "channel_name": channel_name,
                    "interval": interval,
                    "last_run": None,
                    "last_video_count": len(vid_ids) if vid_ids else 0,
                    "enabled": 1 if enabled else 0,
                    "created_at": datetime.now().isoformat(),
                }
            )

            self.console.print(
                f"[green]✓[/green] Added watch job for [bold]{channel_name}[/bold]\n"
                f"  Interval: [cyan]{interval}[/cyan]\n"
                f"  Videos: [yellow]{len(vid_ids) if vid_ids else 0}[/yellow]"
            )
            return True

        except Exception as e:
            self.console.print(f"[red]Error adding watch job:[/red] {e}")
            return False

    def remove_watch_job(self, channel: str) -> bool:
        """
        Remove a channel from watch list.

        Args:
            channel: Channel handle, URL, or ID

        Returns:
            True if successful, False otherwise
        """
        try:
            channel_id = get_channel_id_from_input(channel)

            # Check if job exists
            existing = self.db.execute(
                "SELECT channel_name FROM WatchJobs WHERE channel_id = ?", [channel_id]
            ).fetchone()

            if not existing:
                self.console.print(f"[yellow]Warning:[/yellow] No watch job found for '{channel}'")
                return False

            channel_name = existing[0]

            # Delete job
            self.db.execute("DELETE FROM WatchJobs WHERE channel_id = ?", [channel_id])

            self.console.print(
                f"[green]✓[/green] Removed watch job for [bold]{channel_name}[/bold]"
            )
            return True

        except Exception as e:
            self.console.print(f"[red]Error removing watch job:[/red] {e}")
            return False

    def list_watch_jobs(self) -> list[dict]:
        """
        List all watch jobs.

        Returns:
            List of watch job dictionaries
        """
        try:
            jobs = self.db.execute(
                """
                SELECT
                    job_id,
                    channel_name,
                    interval,
                    last_run,
                    last_video_count,
                    enabled
                FROM WatchJobs
                ORDER BY channel_name
                """
            ).fetchall()

            return [
                {
                    "job_id": row[0],
                    "channel_name": row[1],
                    "interval": row[2],
                    "last_run": row[3],
                    "last_video_count": row[4],
                    "enabled": bool(row[5]),
                }
                for row in jobs
            ]

        except Exception as e:
            self.console.print(f"[red]Error listing watch jobs:[/red] {e}")
            return []

    def enable_watch_job(self, channel: str) -> None:
        """Enable a watch job."""
        try:
            channel_id = get_channel_id_from_input(channel)
            self.db.execute(
                "UPDATE WatchJobs SET enabled = 1 WHERE channel_id = ?", [channel_id]
            )
            self.console.print("[green]✓[/green] Watch job enabled")
        except Exception as e:
            self.console.print(f"[red]Error enabling watch job:[/red] {e}")

    def disable_watch_job(self, channel: str) -> None:
        """Disable a watch job."""
        try:
            channel_id = get_channel_id_from_input(channel)
            self.db.execute(
                "UPDATE WatchJobs SET enabled = 0 WHERE channel_id = ?", [channel_id]
            )
            self.console.print("[green]✓[/green] Watch job disabled")
        except Exception as e:
            self.console.print(f"[red]Error disabling watch job:[/red] {e}")

    def get_due_jobs(self) -> list[dict]:
        """
        Get jobs that are due to run.

        Returns:
            List of due job dictionaries
        """
        jobs = []
        now = datetime.now()

        try:
            # Get column names
            columns = [col.name for col in self.db["WatchJobs"].columns]

            all_jobs = self.db.execute(
                "SELECT * FROM WatchJobs WHERE enabled = 1"
            ).fetchall()

            for job in all_jobs:
                job_dict = dict(zip(columns, job, strict=False))

                # Check if job is due
                if job_dict.get("last_run") is None:
                    jobs.append(job_dict)
                    continue

                try:
                    last_run = datetime.fromisoformat(job_dict["last_run"])
                    interval = job_dict["interval"]

                    # Calculate if job is due
                    if interval == "hourly" and (now - last_run).total_seconds() >= 3600:
                            jobs.append(job_dict)
                    if interval == "daily" and (now - last_run).days >= 1:
                            jobs.append(job_dict)
                    if interval == "weekly" and (now - last_run).days >= 7:
                            jobs.append(job_dict)
                except (ValueError, TypeError) as e:
                    # If last_run is invalid timestamp, consider job due
                    self.console.print(f"[yellow]Warning:[/yellow] Invalid last_run timestamp: {e}")
                    jobs.append(job_dict)

        except Exception as e:
            self.console.print(f"[red]Error checking due jobs:[/red] {e}")

        return jobs

    def update_job_run(self, job_id: int, new_video_count: int) -> None:
        """
        Update job after running.

        Args:
            job_id: Job ID
            new_video_count: Current number of videos
        """
        try:
            self.db.execute(
                """
                UPDATE WatchJobs
                SET last_run = ?, last_video_count = ?
                WHERE job_id = ?
                """,
                [datetime.now().isoformat(), new_video_count, job_id],
            )
        except Exception as e:
            self.console.print(f"[red]Error updating job:[/red] {e}")


def parse_interval(interval: str) -> WatchInterval:
    """
    Parse and validate interval string.

    Args:
        interval: Interval string

    Returns:
        Validated interval

    Raises:
        ValueError if invalid interval
    """
    valid_intervals = ["hourly", "daily", "weekly"]
    interval = interval.lower().strip()

    if interval not in valid_intervals:
        msg = f"Invalid interval '{interval}'. Must be one of: {', '.join(valid_intervals)}"
        raise ValueError(
            msg
        )

    return interval  # type: ignore
