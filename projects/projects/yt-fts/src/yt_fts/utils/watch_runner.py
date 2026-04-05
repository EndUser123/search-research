"""
Watch runner - executes watch jobs to check for new videos.
"""

from rich.console import Console

from .watch_manager import WatchManager


class WatchRunner:
    """Execute watch jobs to check for and download new videos."""

    def __init__(self) -> None:
        """
        Initialize the watch runner.

        Sets up the console for output and the watch manager
        for tracking scheduled jobs.
        """
        self.console = Console()
        self.manager = WatchManager()

    def run_due_jobs(self) -> None:
        """Run all watch jobs that are due."""
        due_jobs = self.manager.get_due_jobs()

        if not due_jobs:
            self.console.print("[green]✓[/green] No jobs due to run")
            return

        self.console.print(
            f"[bold]Running {len(due_jobs)} watch job(s)[/bold]\n"
        )

        for job in due_jobs:
            self._run_job(job)

    def _run_job(self, job: dict) -> None:
        """
        Run a single watch job.

        Args:
            job: Job dictionary
        """
        channel_id = job["channel_id"]
        channel_name = job["channel_name"]
        last_count = job["last_video_count"]

        self.console.print(
            f"🔍 [cyan]Checking[/cyan] [bold]{channel_name}[/bold]..."
        )

        try:
            # Get current video count
            from yt_fts.core.database import get_vid_ids_by_channel_id

            vid_ids = get_vid_ids_by_channel_id(channel_id)
            current_count = len(vid_ids)

            # Check for new videos
            new_videos = current_count - last_count

            if new_videos > 0:
                self.console.print(
                    f"  [green]✓[/green] Found [bold]{new_videos}[/bold] new video(s)!"
                )

                # Download new videos
                self._download_new_videos(channel_id, channel_name)

                # Update job
                self.manager.update_job_run(job["job_id"], current_count)

            elif new_videos == 0:
                self.console.print("  [grey62]No new videos[/grey62]")

                # Update last_run time even if no new videos
                self.manager.update_job_run(job["job_id"], current_count)

            else:
                # Videos were deleted (count decreased)
                self.console.print(
                    f"  [yellow]⚠[/yellow] Video count decreased "
                    f"({last_count} → {current_count})"
                )
                self.manager.update_job_run(job["job_id"], current_count)

        except Exception as e:
            self.console.print(f"  [red]Error:[/red] {e}")

    def _download_new_videos(self, channel_id: str, channel_name: str) -> None:
        """
        Download new videos for a channel.

        Args:
            channel_id: Channel ID
            channel_name: Channel name
        """
        try:
            from yt_fts.download.download_handler import DownloadHandler

            self.console.print("  📥 [blue]Downloading[/blue] new videos...")

            # Use DownloadHandler to download channel
            handler = DownloadHandler(channel_id)
            handler.download_channel()

            self.console.print("  [green]✓[/green] Download complete")

        except Exception as e:
            self.console.print(f"  [red]Download failed:[/red] {e}")

    def run_once(self) -> None:
        """Run all due jobs once (for CLI invocation)."""
        self.console.print("[bold]Watch Mode - Checking for updates[/bold]\n")
        self.run_due_jobs()
        self.console.print("\n[green]✓[/green] Watch run complete")

    def start_daemon(self, interval_minutes: int = 60) -> None:
        """
        Start watch daemon that runs continuously.

        Args:
            interval_minutes: How often to check for due jobs (default: 60 minutes)
        """
        import time

        self.console.print(
            f"[bold]Starting watch daemon[/bold]\n"
            f"  Check interval: [cyan]{interval_minutes}[/cyan] minutes\n"
            f"  Press [bold]Ctrl+C[/bold] to stop\n"
        )

        try:
            while True:
                self.run_due_jobs()
                self.console.print(
                    f"\n[grey62]Next check in {interval_minutes} minutes...[/grey62]\n"
                )
                time.sleep(interval_minutes * 60)

        except KeyboardInterrupt:
            self.console.print("\n[yellow]Watch daemon stopped[/yellow]")
