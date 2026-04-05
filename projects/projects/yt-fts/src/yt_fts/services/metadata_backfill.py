"""
Metadata backfill service for updating video metadata without re-downloading subtitles.

This module provides functionality to fetch and update video metadata (duration,
thumbnail_url, view_count, is_short) for existing videos in the database.
"""
import logging

import yt_dlp
from rich.console import Console
from rich.progress import BarColumn, SpinnerColumn, TextColumn

from yt_fts.core.database import (
    get_channel_id_from_input,
    get_db_connection,
    get_vid_ids_by_channel_id,
)

logger = logging.getLogger(__name__)

class MetadataBackfill:
    """Service for backfilling video metadata from YouTube."""

    def __init__(self, cookies_from_browser: str | None=None, console: Console | None=None):
        """Initialize the metadata backfill service.

        Args:
            cookies_from_browser: Browser to extract cookies from (firefox, chrome, etc.)
            console: Rich console for output
        """
        self.cookies_from_browser = cookies_from_browser
        self.console = console or Console()
        self._user_agents = ["Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36", "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36"]

    def _get_ydl_opts(self) -> dict:
        """Get yt-dlp options for metadata extraction."""
        opts = {"http_headers": {"User-Agent": self._user_agents[0]}, "quiet": True, "no_warnings": True, "extract_flat": True, "skip_download": True}
        if self.cookies_from_browser:
            opts["cookiesfrombrowser"] = (self.cookies_from_browser,)
        return opts

    def _check_video_metadata(self, video_id: str, entry: dict) -> dict:
        """Extract metadata from a yt-dlp entry.

        Args:
            video_id: Video ID
            entry: yt-dlp entry dict

        Returns:
            Dict with duration, thumbnail_url, view_count, is_short
        """
        duration = entry.get("duration")
        thumbnail_url = entry.get("thumbnail", "")
        view_count = entry.get("view_count", 0)
        url = entry.get("url", "") or entry.get("webpage_url", "")
        is_short = 1 if url.find("/shorts/") >= 0 else 0
        return {"duration": duration, "thumbnail_url": thumbnail_url, "view_count": view_count, "is_short": is_short}

    def backfill_channel(self, channel_input: str, skip_existing: bool=True) -> dict[str, int]:
        """Backfill metadata for all videos in a channel.

        Args:
            channel_input: Channel handle (@name), URL, or channel_id
            skip_existing: If True, skip videos that already have metadata

        Returns:
            Dict with counts: updated, skipped, errors
        """
        channel_id = get_channel_id_from_input(channel_input)
        if not channel_id:
            self.console.print(f"[red]❌ Could not resolve channel: {channel_input}[/red]")
            return {"updated": 0, "skipped": 0, "errors": 0}
        videos = get_vid_ids_by_channel_id(channel_id)
        if not videos:
            self.console.print(f"[yellow]No videos found for channel: {channel_input}[/yellow]")
            return {"updated": 0, "skipped": 0, "errors": 0}
        channel_url = f"https://www.youtube.com/channel/{channel_id}"
        stats = {"updated": 0, "skipped": 0, "errors": 0}
        with self._get_progress() as progress:
            task = progress.add_task(f"🔄 Fetching metadata for {len(videos)} videos...", total=len(videos))
            ydl_opts = self._get_ydl_opts()
            try:
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(channel_url, download=False)
                    if not info or not info.get("entries"):
                        self.console.print("[yellow]No videos found from yt-dlp[/yellow]")
                        return stats
                    entries_by_id = {entry.get("id", ""): entry for entry in info.get("entries", []) if entry.get("id")}
                    conn = get_db_connection(timeout=30.0)
                    cur = conn.cursor()
                    for video_id, _ in videos:
                        try:
                            entry = entries_by_id.get(video_id)
                            if not entry:
                                stats["errors"] += 1
                                progress.advance(task)
                                continue
                            if skip_existing:
                                cur.execute("\n                                    SELECT duration FROM Videos\n                                    WHERE video_id = ? AND duration IS NOT NULL\n                                    ", (video_id,))
                                if cur.fetchone():
                                    stats["skipped"] += 1
                                    progress.advance(task)
                                    continue
                            metadata = self._check_video_metadata(video_id, entry)
                            cur.execute("\n                                UPDATE Videos\n                                SET duration = ?, thumbnail_url = ?, view_count = ?, is_short = ?\n                                WHERE video_id = ?\n                                ", (metadata["duration"], metadata["thumbnail_url"], metadata["view_count"], metadata["is_short"], video_id))
                            stats["updated"] += 1
                        except Exception as e:
                            logger.debug("Error updating video %s: %s", video_id, e)
                            stats["errors"] += 1
                        finally:
                            progress.advance(task)
                    conn.commit()
                    conn.close()
            except Exception as e:
                self.console.print(f"[red]Error fetching metadata: {e}[/red]")
                logger.exception("Metadata backfill error: %s", e)
                return {"updated": 0, "skipped": 0, "errors": len(videos)}
        return stats

    def _get_progress(self):
        """Get Rich progress context."""
        from rich.progress import Progress as RichProgress
        return RichProgress(SpinnerColumn(), TextColumn("[progress.description]{task.description}"), BarColumn(bar_width=30), console=self.console, transient=True)

def backfill_metadata(channel_input: str, cookies_from_browser: str | None=None, skip_existing: bool=True) -> dict[str, int]:
    """Convenience function to backfill metadata for a channel.

    Args:
        channel_input: Channel handle (@name), URL, or channel_id
        cookies_from_browser: Browser to extract cookies from
        skip_existing: If True, skip videos that already have metadata

    Returns:
        Dict with counts: updated, skipped, errors
    """
    console = Console()
    backfill = MetadataBackfill(cookies_from_browser=cookies_from_browser, console=console)
    return backfill.backfill_channel(channel_input, skip_existing=skip_existing)
