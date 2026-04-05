# yt_sync/discovery.py

import json
import logging
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

# --- THE FIX: Import the new, correct functions ---
from .ytdlp_legacy_wrapper import build_command, run_ytdlp_subprocess

logger = logging.getLogger(__name__)


class VideoDiscoverer:
    """Discovers video IDs for a given channel from YouTube."""

    def __init__(self, args: Any, channel_url: str, api_client: Any | None):
        self.args = args
        self.channel_url = channel_url
        self.api_client = api_client

    def get_new_videos_via_rss(
        self, channel_id: str, archived_ids: set[str]
    ) -> tuple[bool, set[str]]:
        """
        Quickly checks the channel's RSS feed for new videos.
        Returns a tuple: (needs_full_scan, set_of_new_ids_from_rss)
        """
        if self.args.no_rss:
            logger.debug("RSS check skipped via --no-rss flag.")
            return True, set()

        rss_url = f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"
        logger.debug(f"Checking RSS feed for new videos: {rss_url}")

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }

        try:
            request = urllib.request.Request(rss_url, headers=headers)
            with urllib.request.urlopen(request, timeout=10) as response:
                xml_content = response.read()

            root = ET.fromstring(xml_content)
            namespaces = {
                "yt": "http://www.youtube.com/xml/schemas/2015",
                "atom": "http://www.w3.org/2005/Atom",
            }

            rss_video_ids = []
            for entry in root.findall("atom:entry", namespaces):
                video_id_elem = entry.find("yt:videoId", namespaces)
                if video_id_elem is not None and video_id_elem.text:
                    rss_video_ids.append(video_id_elem.text)

            new_ids_from_rss = {vid for vid in rss_video_ids if vid not in archived_ids}

            if not new_ids_from_rss:
                logger.info("✅ RSS feed checked. No new videos found.")
                return False, set()

            if len(new_ids_from_rss) == len(rss_video_ids) and len(rss_video_ids) > 0:
                logger.info(
                    "⚡ RSS feed contains only new videos. Triggering full API sync to find all new content."
                )
                return True, new_ids_from_rss
            else:
                logger.info(
                    f"⚡ Found {len(new_ids_from_rss)} new video(s) via RSS. Processing just these."
                )
                return False, new_ids_from_rss

        except Exception as e:
            logger.warning(
                f"Could not check RSS feed ({e}). Proceeding with full discovery."
            )
            return True, set()

    def get_all_channel_video_ids(self, uploads_playlist_id: str | None) -> set[str]:
        """
        Retrieves all video IDs for the channel. Prioritizes API, with optional yt-dlp fallback.
        """
        if self.api_client and uploads_playlist_id:
            logger.debug(
                f"Attempting full discovery via YouTube Data API for playlist {uploads_playlist_id}..."
            )
            video_ids = self.api_client.get_all_video_ids_from_playlist(
                uploads_playlist_id
            )
            if video_ids:
                logger.info(f"✅ Discovered {len(video_ids)} video IDs via API.")
                return set(video_ids)

        if self.args.allow_yt_dlp_fallback:
            logger.warning(
                "API discovery failed or was not possible. Falling back to yt-dlp."
            )
            return self._get_all_channel_video_ids_ytdlp()
        else:
            logger.error(
                "API discovery failed and --allow-yt-dlp-fallback is not set. Skipping channel."
            )
            return set()

    def _get_all_channel_video_ids_ytdlp(self) -> set[str]:
        """Retrieves all video IDs for the channel using yt-dlp (fallback method)."""
        try:
            # --- THE FIX: Use the new modular functions ---
            extra_args = ["--flat-playlist", "--dump-json"]
            command = build_command(self.args, extra_args, url=self.channel_url)

            if not command:
                logger.error(
                    "yt-dlp discovery failed: could not build command (executable not found?)."
                )
                return set()

            result = run_ytdlp_subprocess(command)
            # --- END FIX ---

            if result.returncode != 0:
                logger.error(f"yt-dlp discovery failed: {result.stderr.strip()}")
                return set()

            stdout = result.stdout.strip()
            if not stdout:
                logger.warning("yt-dlp returned no output for video discovery.")
                return set()

            video_ids = set()
            for line in stdout.splitlines():
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)
                    if isinstance(data, dict) and data.get("id"):
                        video_ids.add(data["id"])
                        logger.debug(f"Added video ID: {data['id']}")
                    else:
                        logger.debug(
                            f"Line parsed as JSON but no 'id' found: {line[:100]}"
                        )
                except json.JSONDecodeError:
                    logger.debug(
                        f"Skipping non-JSON line from yt-dlp output: {line[:100]}"
                    )
                    continue

            logger.info(f"✅ Discovered {len(video_ids)} video IDs via yt-dlp.")
            return video_ids

        except Exception as e:
            logger.error(
                f"An unexpected error occurred during yt-dlp discovery: {e}",
                exc_info=True,
            )
            return set()
