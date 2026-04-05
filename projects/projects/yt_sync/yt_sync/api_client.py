# yt_sync/api_client.py

import json
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

try:
    from googleapiclient.discovery import build
    from googleapiclient.errors import HttpError
except ImportError:
    build = None
    HttpError = None

logger = logging.getLogger(__name__)

DEFAULT_QUOTA = 10000
QUOTA_FILE = Path("quota.json")
COSTS = {
    "channels.list": 1,
    "playlistItems.list": 1,
    "videos.list": 1,
}


class YouTubeAPIClient:
    """Manages YouTube Data v3 API requests with multiple API key support and quota management."""

    def __init__(self, api_keys: list[str]):
        if not build or not HttpError:
            raise ImportError(
                "Google API client libraries not found. Please run: pip install google-api-python-client"
            )
        self.api_keys = api_keys
        self.current_key_index = 0
        self.services: dict[str, Any] = {}
        self.quota_exceeded_keys: set[str] = set()

        self.estimated_quota = DEFAULT_QUOTA
        self.quota_spent_session = 0
        self._read_quota_file()

    def _read_quota_file(self):
        """Reads the quota file and updates the current estimate if the date is today."""
        today = date.today().isoformat()
        if QUOTA_FILE.is_file():
            try:
                with open(QUOTA_FILE) as f:
                    data = json.load(f)
                if data.get("date") == today:
                    self.estimated_quota = int(data.get("quota", DEFAULT_QUOTA))
                    logger.info(
                        f"Loaded today's quota from file. (Est. Remaining: {self.estimated_quota})"
                    )
                else:
                    self._write_quota_file()
            except (OSError, json.JSONDecodeError):
                self._write_quota_file()
        else:
            self._write_quota_file()

    def _write_quota_file(self):
        """Saves the current estimated quota and today's date to the file."""
        today = date.today().isoformat()
        data = {"date": today, "quota": self.estimated_quota}
        try:
            with open(QUOTA_FILE, "w") as f:
                json.dump(data, f)
        except OSError as e:
            logger.error(f"Could not write to quota file: {e}")

    def _get_service(self) -> Any | None:
        if len(self.quota_exceeded_keys) == len(self.api_keys):
            logger.error("All YouTube API keys have exceeded their quota.")
            return None

        api_key = self._get_next_available_key()
        if not api_key:
            return None

        assert build is not None
        if api_key not in self.services:
            self.services[api_key] = build("youtube", "v3", developerKey=api_key)
        return self.services[api_key]

    def _get_next_available_key(self) -> str | None:
        available_keys = [
            key for key in self.api_keys if key not in self.quota_exceeded_keys
        ]
        if not available_keys:
            return None

        self.current_key_index = (self.current_key_index) % len(available_keys)
        key = available_keys[self.current_key_index]
        self.current_key_index += 1
        return key

    def _execute_request(self, request, cost: int):
        """Executes an API request, tracks quota, and saves it to disk."""
        assert HttpError is not None
        try:
            response = request.execute()
            self.estimated_quota -= cost
            self.quota_spent_session += cost
            self._write_quota_file()
            return response
        except HttpError as e:
            if "quotaExceeded" in str(e):
                current_key_match = re.search(r"key=([^&]+)", request.uri)
                if current_key_match:
                    current_key = current_key_match.group(1)
                    logger.warning(
                        f"API key ending in ...{current_key[-4:]} has exceeded its quota."
                    )
                    self.quota_exceeded_keys.add(current_key)
                raise e  # Re-raise to be handled by the caller
            else:
                raise e

    def get_quota_report(self) -> str:
        """Returns a formatted string of the current quota status."""
        return f"Session Spend: {self.quota_spent_session} | Daily Quota (Est.): {self.estimated_quota}"

    def get_channel_details_from_url(
        self, channel_url: str
    ) -> dict[str, str] | None:
        """
        Retrieves canonical channel details using the official API method.
        This is the most reliable way to get the correct uploads playlist ID.
        """
        service = self._get_service()
        if not service:
            return None

        handle_match = re.search(r"@([^/]+)", channel_url)
        if not handle_match:
            logger.error(f"Could not extract a valid @handle from URL: {channel_url}")
            return None

        handle = handle_match.group(1)
        try:
            request = service.channels().list(
                part="snippet,contentDetails", forHandle=handle
            )
            logger.debug(f"Executing API request for channel details: {request.uri}")
            response = self._execute_request(request, cost=COSTS["channels.list"])

            items = response.get("items", [])
            if not items:
                logger.error(f"API returned no items for handle: @{handle}")
                return None

            item = items[0]
            snippet = item.get("snippet", {})
            content_details = item.get("contentDetails", {}).get("relatedPlaylists", {})

            channel_id = item.get("id")
            uploads_playlist_id = content_details.get("uploads")

            if not all([channel_id, uploads_playlist_id, snippet.get("title")]):
                logger.error(
                    f"API response for @{handle} was missing critical information."
                )
                return None

            return {
                "id": channel_id,
                "handle": f"@{handle}",
                "title": snippet.get("title", "Unknown Title"),
                "uploads_playlist_id": uploads_playlist_id,
            }
        except Exception as e:
            logger.error(f"API error during channel handshake for @{handle}: {e}")
            return None

    def get_all_video_ids_from_playlist(self, playlist_id: str) -> list[str]:
        service = self._get_service()
        if not service:
            return []
        video_ids = []
        next_page_token = None
        while True:
            try:
                request = service.playlistItems().list(
                    part="contentDetails",
                    playlistId=playlist_id,
                    maxResults=50,
                    pageToken=next_page_token,
                )
                logger.debug(f"Executing API request for playlist items: {request.uri}")
                response = self._execute_request(
                    request, cost=COSTS["playlistItems.list"]
                )

                items = response.get("items", [])
                for item in items:
                    content_details = item.get("contentDetails", {})
                    video_id = content_details.get("videoId")
                    if video_id:
                        video_ids.append(video_id)

                next_page_token = response.get("nextPageToken")
                if not next_page_token:
                    break
            except Exception as e:
                logger.error(
                    f"API error fetching playlist items for playlist {playlist_id}: {e}"
                )
                break
        return video_ids

    def get_videos_metadata(self, video_ids: list[str]) -> dict[str, dict[str, Any]]:
        if not video_ids:
            return {}
        all_metadata = {}
        for i in range(0, len(video_ids), 50):
            chunk = video_ids[i : i + 50]
            try:
                service = self._get_service()
                if not service:
                    break
                request = service.videos().list(
                    part="snippet,contentDetails,statistics", id=",".join(chunk)
                )
                response = self._execute_request(request, cost=COSTS["videos.list"])

                for item in response.get("items", []):
                    video_id = item.get("id")
                    if not video_id:
                        continue

                    snippet = item.get("snippet", {})
                    content_details = item.get("contentDetails", {})
                    statistics = item.get("statistics", {})

                    duration_seconds = self._parse_iso_duration(
                        content_details.get("duration", "PT0S")
                    )
                    upload_date_raw = snippet.get("publishedAt", "")
                    upload_date = (
                        upload_date_raw[:10].replace("-", "") if upload_date_raw else ""
                    )

                    metadata = {
                        "id": video_id,
                        "title": snippet.get("title", ""),
                        "description": snippet.get("description", ""),
                        "duration": duration_seconds,
                        "upload_date": upload_date,
                        "uploader": snippet.get("channelTitle", ""),
                        "uploader_id": snippet.get("channelId", ""),
                        "view_count": int(statistics.get("viewCount", 0)),
                        "like_count": int(statistics.get("likeCount", 0)),
                        "tags": snippet.get("tags", []),
                        "categories": [snippet.get("categoryId", "")],
                        "thumbnail": snippet.get("thumbnails", {})
                        .get("high", {})
                        .get("url", ""),
                        "_api_source": "youtube_data_v3",
                    }
                    all_metadata[video_id] = metadata
            except Exception as e:
                logger.error(f"API error fetching video metadata chunk: {e}")
                continue
        return all_metadata

    def _parse_iso_duration(self, duration_str: str) -> int:
        if not duration_str or duration_str == "PT0S":
            return 0
        # Match valid ISO 8601 duration formats with H, M, S components
        match = re.fullmatch(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", duration_str)
        if not match:
            return 0

        # Check for truly incomplete formats (like "PT1H2")
        has_hours = bool(match.group(1))
        has_minutes = bool(match.group(2))
        has_seconds = bool(match.group(3))

        # Reject if has numbers but missing designators (e.g. "PT1H2")
        if (
            has_hours
            and not has_minutes
            and not has_seconds
            and "H" not in duration_str[-2:]
        ) or (has_minutes and not has_seconds and "M" not in duration_str[-2:]):
            return 0

        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds
