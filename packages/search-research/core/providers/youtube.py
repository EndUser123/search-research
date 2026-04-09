"""YouTube transcript provider using yt-dlp for search and transcript fetching.

This provider:
1. Searches YouTube using yt-dlp (ytsearch: syntax)
2. Fetches transcripts using yt-dlp (subtitles extraction)
3. Returns results in standard BaseWebBackend format

Note: For the full 7-method fallback chain with Selenium/Whisper support,
use the intelligence-stream package's csf-transcripts CLI directly.
This provider provides a lightweight integration focused on search + basic transcripts.
"""

import json
import logging
import re
import urllib.request
from typing import Any

import yt_dlp

from .base_web import BaseWebBackend

logger = logging.getLogger(__name__)


class YouTubeBackend(BaseWebBackend):
    """YouTube transcript provider.

    Features:
    - Search YouTube videos by query using yt-dlp
    - Fetch transcripts using yt-dlp's subtitle extraction
    - No API key required (uses scraping)
    - Supports search queries (not direct video IDs — use search instead)

    Usage:
        backend = YouTubeBackend()
        results = await backend.search("python async tutorial", max_results=5)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "youtube"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return False

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key (not used)."""
        return "YOUTUBE_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 5):
        """Initialize YouTubeBackend.

        Args:
            api_key: Not used (kept for interface compatibility).
            max_results: Maximum number of videos to search.
        """
        self.max_results = max_results

    async def _search_youtube(self, query: str, max_results: int) -> list[dict[str, Any]]:
        """Search YouTube using yt-dlp.

        Args:
            query: Search query.
            max_results: Maximum results.

        Returns:
            List of video metadata dicts with keys: id, title, url.
        """
        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": True,  # Don't download, just get metadata
            "playlistend": max_results,
        }

        search_url = f"ytsearch{max_results}:{query}"

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(search_url, download=False)

            if not info or "entries" not in info:
                return []

            results = []
            for entry in info["entries"]:
                if entry is None:
                    continue
                results.append(
                    {
                        "id": entry.get("id", ""),
                        "title": entry.get("title", "Unknown"),
                        "url": f"https://www.youtube.com/watch?v={entry.get('id', '')}",
                    }
                )

            return results

        except Exception as e:
            logger.error(f"yt-dlp search failed: {e}")
            return []

    def _fetch_transcript_ytdlp(self, video_id: str) -> tuple[bool, str | None, str | None]:
        """Fetch transcript using yt-dlp subtitle extraction.

        Args:
            video_id: YouTube video ID.

        Returns:
            Tuple of (success, transcript_text, error_message).
        """
        video_url = f"https://www.youtube.com/watch?v={video_id}"

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsubs": True,
            "subtitleslangs": ["en"],
            "subtitlesformat": "json3",
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(video_url, download=False)

            # Check for subtitles (prefer manual, fall back to auto-generated)
            subs = (
                info.get("subtitles", {}).get("en")
                or info.get("automatic_captions", {}).get("en")
            )

            if not subs or len(subs) == 0:
                return False, None, "No transcript available for this video"

            # Get the subtitle URL (usually the first available format)
            sub_url = subs[0].get("url")
            if not sub_url:
                return False, None, "No subtitle URL in yt-dlp response"

            # Fetch the subtitle content
            req = urllib.request.Request(
                sub_url,
                headers={
                    "User-Agent": (
                        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                        "AppleWebKit/537.36 (KHTML, like Gecko) "
                        "Chrome/120.0.0.0 Safari/537.36"
                    ),
                },
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                data = json.loads(response.read().decode("utf-8"))

            # Parse timedtext JSON3 format into plain text
            text_parts = []
            for event in data.get("events", []):
                for seg in event.get("segs", []):
                    text = seg.get("utf8", "").strip()
                    if text:
                        text_parts.append(text)

            full_text = " ".join(text_parts)
            if not full_text.strip():
                return False, None, "Subtitle file was empty"

            return True, full_text.strip(), None

        except urllib.error.HTTPError as e:
            if e.code == 429:
                return False, None, "rate limited (429)"
            return False, None, f"HTTP error: {e.code}"
        except Exception as e:
            logger.error(f"Transcript fetch failed for {video_id}: {e}")
            return False, None, str(e)

    async def search(
        self,
        query: str,
        max_results: int = 5,
        timeout: float = 30.0,
        **kwargs,
    ) -> list[dict[str, Any]]:
        """Execute YouTube search and fetch transcripts.

        Args:
            query: Search query (not video ID or URL — use search instead).
            max_results: Maximum number of results to return.
            timeout: Timeout per transcript fetch (not used for yt-dlp search).
            **kwargs: Additional parameters (ignored).

        Returns:
            List of search results with keys:
                - title: Video title
                - url: Video URL
                - content: Transcript text (or error message)
                - score: Relevance score (1.0 for all results)
                - metadata: Provider-specific metadata (video_id, transcript_source, error)
        """
        import asyncio

        # Search YouTube for videos matching query
        videos = await self._search_youtube(query, max_results)

        if not videos:
            return []

        # Fetch transcripts for all videos in parallel (with timeout)
        results = []
        fetch_tasks = []

        for video in videos:
            video_id = video["id"]
            fetch_tasks.append(
                asyncio.get_event_loop().run_in_executor(
                    None, lambda vid=video_id: self._fetch_transcript_ytdlp(vid)
                )
            )

        # Wait for all transcript fetches with individual timeout
        done, _ = await asyncio.wait(
            fetch_tasks,
            timeout=timeout * len(videos),  # Total timeout for all fetches
            return_when=asyncio.ALL_COMPLETED,
        )

        # Map results back to videos
        transcript_map = {}
        for task in done:
            try:
                idx = fetch_tasks.index(task)
                video_id = videos[idx]["id"]
                success, transcript, error = task.result()
                transcript_map[video_id] = (success, transcript, error)
            except Exception:
                pass

        # Build final results
        for video in videos:
            video_id = video["id"]
            title = video["title"]
            url = video["url"]

            if video_id in transcript_map:
                success, transcript, error = transcript_map[video_id]

                if success and transcript:
                    content = transcript[:5000]  # Limit content size
                    score = 1.0
                else:
                    content = error or "No transcript available"
                    score = 0.0

                results.append(
                    {
                        "title": title,
                        "url": url,
                        "content": content,
                        "score": score,
                        "metadata": {
                            "video_id": video_id,
                            "transcript_source": "youtube",
                            "error": error if not success else None,
                        },
                    }
                )

        return results

    async def close(self):
        """Close any resources (no-op for YouTube)."""
        pass
