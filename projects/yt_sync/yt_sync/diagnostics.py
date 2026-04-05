# yt_sync/diagnostics.py

import logging
import subprocess

from rich.console import Console
from rich.panel import Panel
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
)

from .ytdlp_legacy_wrapper import find_ytdlp_executable

logger = logging.getLogger(__name__)
console = Console()


class RestrictedVideoFinder:
    """
    Scans YouTube channels to find a video that is age-restricted or members-only,
    providing a perfect test case for the --grab-auth feature.
    """

    def __init__(self, channel_urls: str | list[str] = None):
        if channel_urls is None:
            self.channel_urls = []
        elif isinstance(channel_urls, str):
            self.channel_urls = [channel_urls]
        else:
            self.channel_urls = channel_urls

        self.ytdlp_exec = find_ytdlp_executable()
        self.restriction_keywords = [
            "sign in to confirm your age",
            "age-restricted",
            "members-only",
            "unavailable for non-members",
            "this video is private",
        ]

    def _run_command(self, command: list[str]) -> subprocess.CompletedProcess:
        """A simplified, direct subprocess runner for this diagnostic tool."""
        logger.debug(f"Running diagnostic command: {' '.join(command)}")
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if result.stderr:
                logger.debug(
                    f"yt-dlp stderr for '{command[-1]}':\n{result.stderr.strip()}"
                )
            return result
        except Exception as e:
            logger.error(f"Exception running diagnostic command: {e}")
            return subprocess.CompletedProcess(
                args=command, returncode=1, stdout="", stderr=str(e)
            )

    def is_video_restricted(self, video_url: str) -> bool:
        """
        Checks if a single video URL is restricted. Returns True if it is, False otherwise.
        This is the core verification logic.
        """
        if not self.ytdlp_exec:
            return False

        command = [self.ytdlp_exec, "--dump-json", "--no-warnings", video_url]
        result = self._run_command(command)

        if result.returncode != 0:
            stderr_lower = result.stderr.lower()
            for keyword in self.restriction_keywords:
                if keyword in stderr_lower:
                    return True
        return False

    def _get_video_ids_for_channel(self, channel_url: str) -> list[str] | None:
        """Gets all video IDs from a single channel URL using yt-dlp."""
        command = [self.ytdlp_exec, "--flat-playlist", "--print", "%(id)s", channel_url]
        result = self._run_command(command)

        if result.returncode != 0:
            logger.error(f"Failed to get video list for {channel_url}.")
            return None

        video_ids = result.stdout.strip().splitlines()
        return video_ids if video_ids else None

    def find_first_restricted_video(self) -> str | None:
        """
        Scans all provided channels and returns the URL of the first restricted video found.
        This is the full discovery logic.
        """
        if not self.ytdlp_exec:
            logger.critical("Could not find yt-dlp executable. Cannot run diagnostic.")
            return None

        for channel_url in self.channel_urls:
            console.print(
                f"🔎 Scanning [cyan]{channel_url}[/cyan] for a restricted video..."
            )
            video_ids = self._get_video_ids_for_channel(channel_url)
            if not video_ids:
                console.print(
                    "  [yellow]No videos found or channel is inaccessible. Skipping.[/yellow]"
                )
                continue

            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
            ) as progress:
                task = progress.add_task("Checking videos...", total=len(video_ids))
                for video_id in video_ids:
                    progress.update(task, advance=1)
                    video_url = f"https://www.youtube.com/watch?v={video_id}"
                    if self.is_video_restricted(video_url):
                        return video_url
        return None

    def run_and_print(self):
        """
        Executes the finder and prints a formatted panel with the result.
        This is for the standalone --find-restricted command.
        """
        found_url = self.find_first_restricted_video()

        if found_url:
            panel_content = (
                f"Found a restricted video perfect for testing `--grab-auth`.\n\n"
                f"[bold]URL:[/bold] [link={found_url}]{found_url}[/link]\n"
            )
            console.print(
                Panel(
                    panel_content,
                    title="[bold green]✓ Restricted Video Found[/bold green]",
                    border_style="green",
                )
            )
        else:
            console.print(
                Panel(
                    "Scanned all provided channel(s) but could not find any with a clear age or membership restriction.",
                    title="[bold yellow]No Restricted Videos Found[/bold yellow]",
                    border_style="yellow",
                )
            )
