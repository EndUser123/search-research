"""
RSS Feed Pre-Check for YouTube Channels

Uses YouTube's RSS feeds to quickly check for new videos without
the overhead of yt-dlp extraction. Falls back to yt-dlp when
a gap in video history is detected.

RSS Feed URL format:
    https://www.youtube.com/feeds/videos.xml?channel_id=UCxxxxx
    https://www.youtube.com/feeds/videos.xml?user=username
    https://www.youtube.com/feeds/videos.xml?handle=@handle
"""
from __future__ import annotations

import json
import logging
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import Literal
from urllib.parse import quote, urlparse

import requests


def _get_rss_logger() -> logging.Logger:
    """
    Get or create the RSS logger with file handler.

    Returns:
        Logger instance that writes to download.log
    """
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.FileHandler("download.log", mode="a")
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger


@dataclass
class RssCheckResult:
    """Result of RSS pre-check."""

    status: Literal["skip", "new_videos", "gap_detected", "error"]
    video_ids: list[str]  # Video IDs from RSS (max ~15)
    newest_id: str | None
    oldest_id: str | None
    message: str
    gap_start_id: str | None = None  # If gap detected, this is where gap starts
    unavailable_video_ids: list[str] = (
        None  # Videos that are unavailable/scheduled (to be added to DB)
    )
    unavailable_video_status: dict[str, str] = (
        None  # video_id -> status ("scheduled", "unavailable", "members_only")
    )
    # NEW: Video metadata extracted from RSS feed (video_id -> {title, date, url})
    video_metadata: dict[str, dict[str, str]] = (
        None  # {"video_id": {"title": "...", "date": "...", "url": "..."}}
    )


class RssPreChecker:
    """
    Fast pre-check using YouTube RSS feeds.

    Returns quick decisions without full yt-dlp extraction:
    - "skip": All RSS videos already in database (up to date)
    - "new_videos": New videos found, no gaps (download RSS videos)
    - "gap_detected": Gap in history detected (need yt-dlp for full list)
    - "error": RSS fetch failed
    """

    RSS_URL_FORMATS = {
        "channel_id": "https://www.youtube.com/feeds/videos.xml?channel_id={id}",
        "user": "https://www.youtube.com/feeds/videos.xml?user={id}",
        "handle": "https://www.youtube.com/feeds/videos.xml?handle={id}",
    }

    # YouTube XML namespace
    YT_NS = {"yt": "http://www.youtube.com/xml/schemas/2015"}
    ATOM_NS = {"atom": "http://www.w3.org/2005/Atom"}

    def __init__(
        self,
        timeout: float = 30.0,
        user_agent: str = "Mozilla/5.0 (compatible; yt-fts/2.0)",
        cache_ttl: int = 900,  # 15 minutes default
        use_cache: bool = True,
    ):
        """
        Initialize RSS pre-checker.

        Args:
            timeout: HTTP request timeout in seconds
            user_agent: User-Agent string for HTTP requests
            cache_ttl: Cache time-to-live in seconds (default: 900 = 15 minutes)
            use_cache: Whether to use caching (default: True)
        """
        self.timeout = timeout
        self.user_agent = user_agent
        self._channel_id_cache: dict[str, str] = {}
        self.cache_ttl = cache_ttl
        self.use_cache = use_cache
        self._memory_cache: dict[str, tuple[float, dict]] = (
            {}
        )  # (timestamp, result_data)
        self._cache_dir = Path("data/cache/rss")
        if self.use_cache:
            self._cache_dir.mkdir(parents=True, exist_ok=True)

    def _build_rss_url(
        self, channel_id: str | None, handle: str | None, resolved_url: str
    ) -> str | None:
        """Build RSS feed URL from channel identifier.

        Priority:
        1. If we have a channel_id (UCxxxx format), use it directly
        2. Extract RSS link from HTML page (most reliable - YouTube embeds it)
        3. Extract channel ID from HTML JSON
        4. Parse URL for channel/handle patterns
        """
        import re

        # 1. If we have a channel_id (UCxxxx format), use it directly
        if channel_id and channel_id.startswith("UC"):
            return self.RSS_URL_FORMATS["channel_id"].format(id=channel_id)

        # 2. Extract RSS link from HTML page (most reliable)
        try:
            response = requests.get(
                resolved_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                # Look for the RSS link in the HTML head
                rss_match = re.search(
                    r'<link\s+rel="alternate"\s+type="application/rss\+xml"\s+[^>]*href="([^"]+)"',
                    response.text,
                )
                if rss_match:
                    # HTML encodes & as &amp;
                    return rss_match.group(1).replace("&amp;", "&")
        except requests.RequestException:
            pass

        # 3. Extract channel ID from HTML JSON
        try:
            response = requests.get(
                resolved_url,
                headers={"User-Agent": self.user_agent},
                timeout=self.timeout,
            )
            if response.status_code == 200:
                # YouTube embeds channel ID in JSON in the HTML
                matches = re.findall(r'"channelId":"([^"]+)"', response.text)
                if matches:
                    extracted_id = matches[0]
                    if extracted_id.startswith("UC"):
                        return self.RSS_URL_FORMATS["channel_id"].format(
                            id=extracted_id
                        )
        except requests.RequestException:
            pass

        # 4. Parse URL for channel ID or handle
        parsed = urlparse(resolved_url)

        # Extract from /channel/UCxxxxx
        if "/channel/" in parsed.path:
            parts = parsed.path.split("/channel/")
            if len(parts) > 1:
                cid = parts[1].split("/")[0]
                if cid.startswith("UC"):
                    return self.RSS_URL_FORMATS["channel_id"].format(id=cid)

        # Extract from /@handle
        if "/@" in parsed.path:
            parts = parsed.path.split("/@")
            if len(parts) > 1:
                handle = parts[1].split("/")[0]
                return self.RSS_URL_FORMATS["handle"].format(id=f"@{handle}")

        # Extract from /user/username
        if "/user/" in parsed.path:
            parts = parsed.path.split("/user/")
            if len(parts) > 1:
                username = parts[1].split("/")[0]
                return self.RSS_URL_FORMATS["user"].format(id=username)

        return None

    def _build_handle_urls(self, handle: str) -> list[str]:
        """Build candidate handle RSS URLs with and without '@', plus lowercase."""
        normalized = handle.lstrip("@")
        lower = normalized.lower()
        return [
            self.RSS_URL_FORMATS["handle"].format(id=f"@{normalized}"),
            self.RSS_URL_FORMATS["handle"].format(id=normalized),
            self.RSS_URL_FORMATS["handle"].format(id=f"@{lower}"),
            self.RSS_URL_FORMATS["handle"].format(id=lower),
        ]

    def _parse_video_ids(self, xml_text: str) -> list[str]:
        """Extract video IDs from RSS feed XML, filtering out Shorts."""
        try:
            root = ET.fromstring(xml_text)

            # YouTube RSS uses Atom namespace with entry elements
            # Video ID is in yt:videoId element
            # Shorts are identified by /shorts/ in the link href
            video_ids = []
            shorts_count = 0

            for entry in root.findall("atom:entry", self.ATOM_NS):
                video_id_elem = entry.find("yt:videoId", self.YT_NS)
                if video_id_elem is None or not video_id_elem.text:
                    continue

                # Check if this is a Short by examining the link href
                # Shorts have: https://www.youtube.com/shorts/{video_id}
                # Regular videos have: https://www.youtube.com/watch?v={video_id}
                link_elem = entry.find("atom:link[@rel='alternate']", self.ATOM_NS)
                if link_elem is not None:
                    href = link_elem.get("href", "")
                    if "/shorts/" in href:
                        shorts_count += 1
                        continue  # Skip Shorts

                video_ids.append(video_id_elem.text)

            if shorts_count > 0:
                logger = _get_rss_logger()
                logger.info(
                    "Filtered out %d Shorts from RSS feed, %d regular videos remaining",
                    shorts_count,
                    len(video_ids),
                )

            return video_ids
        except ET.ParseError:
            return []

    def _parse_video_ids_with_metadata(
        self, xml_text: str
    ) -> dict[str, dict[str, str]]:
        """Extract video IDs and metadata from RSS feed XML.

        Returns a dict mapping video_id to {title, date, url}.

        This is used to persist video metadata to the database when RSS discovers
        new videos, so they don't appear as "new" on subsequent runs.
        """
        try:
            root = ET.fromstring(xml_text)
            video_metadata = {}

            for entry in root.findall("atom:entry", self.ATOM_NS):
                video_id_elem = entry.find("yt:videoId", self.YT_NS)
                if video_id_elem is None or not video_id_elem.text:
                    continue

                video_id = video_id_elem.text

                # Extract title
                title_elem = entry.find("atom:title", self.ATOM_NS)
                title = title_elem.text if title_elem is not None else "Unknown"

                # Extract published date
                published_elem = entry.find("atom:published", self.ATOM_NS)
                date = published_elem.text if published_elem is not None else ""

                # Extract URL from link
                link_elem = entry.find("atom:link[@rel='alternate']", self.ATOM_NS)
                if link_elem is None:
                    continue  # Skip entries without URL

                url = link_elem.get("href", "")
                # Skip Shorts
                if "/shorts/" in url:
                    continue

                video_metadata[video_id] = {
                    "title": title,
                    "date": date,
                    "url": url,
                }

            return video_metadata
        except ET.ParseError:
            return {}

    def _extract_channel_name_from_feed(self, xml_text: str) -> str | None:
        """Extract channel name from RSS feed XML.

        YouTube RSS feeds have the channel name in:
        - feed/atom:title (the feed title)
        - feed/atom:author/atom:name (the author name)

        Returns the channel name or None if not found.
        """
        try:
            root = ET.fromstring(xml_text)

            # Try to get channel name from feed title first
            # Format is usually: "Channel Name - Videos" or just "Channel Name"
            title_elem = root.find("atom:title", self.ATOM_NS)
            if title_elem is not None and title_elem.text:
                title = title_elem.text.strip()
                # Remove common suffixes
                for suffix in [" - Videos", " videos", " Videos"]:
                    if title.endswith(suffix):
                        title = title[: -len(suffix)].strip()
                if title and len(title) > 2:  # Basic validation
                    return title

            # Try author name as fallback
            author_elem = root.find("atom:author/atom:name", self.ATOM_NS)
            if author_elem is not None and author_elem.text:
                name = author_elem.text.strip()
                if name and len(name) > 2:
                    return name

            return None
        except ET.ParseError:
            return None

    def _escalate_channel_name_via_api(self, channel_id: str) -> str | None:
        """Escalate to YouTube API to fetch channel name when RSS fails.

        This is called when RSS feed doesn't contain a parsable channel name.
        Uses the YouTube Data API v3 channels endpoint with part=snippet.

        Args:
            channel_id: YouTube channel ID (starts with UC)

        Returns:
            Channel name from API, or None if fetch fails
        """
        import logging
        import os

        logger = logging.getLogger(__name__)

        # Load API key from environment
        api_key = os.getenv("YOUTUBE_API_KEY")
        if not api_key:
            # Try alternative keys
            for i in range(2, 6):
                api_key = os.getenv(f"YOUTUBE_API_KEY_{i}")
                if api_key:
                    break

        if not api_key:
            logger.debug("No YouTube API key found for channel name escalation")
            return None

        try:
            params = {
                "part": "snippet",
                "id": channel_id,
                "key": api_key,
            }
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params=params,
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    snippet = data["items"][0].get("snippet", {})
                    title = snippet.get("title")
                    if title:
                        logger.info(
                            "Escalated to API for channel name: %s -> %s",
                            channel_id[:20],
                            title,
                        )
                        return title
            logger.debug(
                "API returned %s for channel %s", response.status_code, channel_id[:20]
            )
        except requests.Timeout:
            logger.debug(
                "Timeout escalating to API for channel name: %s", channel_id[:20]
            )
        except Exception as e:
            logger.debug("Error escalating to API for channel name: %s", e)

        return None

    def _check_video_availability(self, video_ids: list[str]) -> dict[str, str]:
        """Check if videos are scheduled, unavailable, or available.

        Returns dict mapping video_id -> status with specific unavailable reasons:
        - 'scheduled': Premiere or scheduled stream
        - 'members_only': Members-only content
        - 'unavailable/deleted': Video removed/deleted
        - 'unavailable/private': Private video
        - 'unavailable/geo': Geo-blocked content
        - 'unavailable': Other unavailable (generic)
        - 'available': Video is accessible (includes age-restricted - cookie-solvable)
        - 'unknown': Could not determine status

        Note: Age-restriction is NOT detected here as it's solvable with cookies during download.
        """
        import re

        results = {}
        for vid in video_ids:
            try:
                resp = requests.get(
                    f"https://www.youtube.com/watch?v={vid}",
                    headers={"User-Agent": self.user_agent},
                    timeout=5,
                )
                text = resp.text

                # Check for specific unavailable states first (more specific to less specific)
                # Note: Age-restriction is NOT checked here - it's cookie-solvable, not true unavailability

                # Private video
                if re.search(
                    r"This video is private|Private[- ]?video", text, re.IGNORECASE
                ):
                    results[vid] = "unavailable/private"
                # Geo-blocked
                elif re.search(
                    r"Not available in your country|geo[- ]?blocked|not available.*region|video is unavailable in your country",
                    text,
                    re.IGNORECASE,
                ):
                    results[vid] = "unavailable/geo"
                # Deleted/removed video
                elif re.search(
                    r"This video is not available|Video unavailable|This live stream is not available|has been removed|no longer exists",
                    text,
                    re.IGNORECASE,
                ):
                    results[vid] = "unavailable/deleted"
                # Generic unavailable (catch remaining patterns)
                elif re.search(r"isUnavailable|is not available", text):
                    results[vid] = "unavailable"
                # Scheduled/premiere
                elif re.search(r"scheduled|premiere|starts in", text, re.IGNORECASE):
                    results[vid] = "scheduled"
                # Members only
                elif re.search(
                    r"Members[- ]?only|Become a member|Join this channel",
                    text,
                    re.IGNORECASE,
                ):
                    results[vid] = "members_only"
                else:
                    results[vid] = "available"
            except requests.RequestException:
                results[vid] = "unknown"
        return results

    def _get_cache_key(
        self, channel_id: str | None, handle: str | None, resolved_url: str
    ) -> str:
        """Generate a unique cache key for this channel."""
        if channel_id:
            return f"cid_{channel_id}"
        if handle:
            return f"handle_{handle.lstrip('@').lower()}"
        # Hash the URL as fallback
        import hashlib

        return f"url_{hashlib.md5(resolved_url.encode(), usedforsecurity=False).hexdigest()}"

    def _get_cached_result(self, cache_key: str) -> RssCheckResult | None:
        """Get cached RSS result if available and fresh."""
        if not self.use_cache:
            return None

        current_time = time.time()

        # Check memory cache first
        if cache_key in self._memory_cache:
            timestamp, result_data = self._memory_cache[cache_key]
            if current_time - timestamp < self.cache_ttl:
                return RssCheckResult(**result_data)
            # Expired, remove from memory
            del self._memory_cache[cache_key]

        # Check disk cache
        cache_file = self._cache_dir / f"{cache_key}.json"
        if cache_file.exists():
            try:
                with open(cache_file, encoding="utf-8") as f:
                    cache_data = json.load(f)
                if current_time - cache_data.get("timestamp", 0) < self.cache_ttl:
                    # Convert dict back to RssCheckResult
                    result_dict = cache_data.get("result", {})
                    # Handle lists that should be converted
                    return RssCheckResult(
                        status=result_dict.get("status", "error"),
                        video_ids=result_dict.get("video_ids", []),
                        newest_id=result_dict.get("newest_id"),
                        oldest_id=result_dict.get("oldest_id"),
                        message=result_dict.get("message", ""),
                        gap_start_id=result_dict.get("gap_start_id"),
                        unavailable_video_ids=result_dict.get(
                            "unavailable_video_ids", []
                        ),
                        unavailable_video_status=result_dict.get(
                            "unavailable_video_status", {}
                        ),
                    )
            except (json.JSONDecodeError, KeyError, TypeError):
                # Invalid cache file, remove it
                cache_file.unlink(missing_ok=True)

        return None

    def _save_cached_result(self, cache_key: str, result: RssCheckResult) -> None:
        """Save RSS result to cache."""
        if not self.use_cache:
            return

        current_time = time.time()

        # Save to memory cache
        result_data = {
            "status": result.status,
            "video_ids": result.video_ids,
            "newest_id": result.newest_id,
            "oldest_id": result.oldest_id,
            "message": result.message,
            "gap_start_id": result.gap_start_id,
            "unavailable_video_ids": result.unavailable_video_ids or [],
            "unavailable_video_status": result.unavailable_video_status or {},
        }
        self._memory_cache[cache_key] = (current_time, result_data)

        # Save to disk cache
        cache_file = self._cache_dir / f"{cache_key}.json"
        try:
            cache_data = {"timestamp": current_time, "result": result_data}
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, indent=2)
        except (OSError, TypeError):
            # Fail silently - caching is optional
            pass

    def check(
        self,
        channel_id: str | None,
        handle: str | None,
        resolved_url: str,
        db_video_ids: set[str],
    ) -> RssCheckResult:
        """
        Check RSS feed for new videos.

        Args:
            channel_id: YouTube channel ID (UCxxxxx format)
            handle: Channel handle (@username format)
            resolved_url: Full channel URL
            db_video_ids: Set of video IDs already in database

        Returns:
            RssCheckResult with status and video list
        """
        import re

        # Check RSS result cache first (before any HTTP requests)
        cache_key = self._get_cache_key(channel_id, handle, resolved_url)
        cached_result = self._get_cached_result(cache_key)
        if cached_result is not None:
            return cached_result

        # Priority 1: Use cached channel_id if available
        if handle and not channel_id:
            cached = self._channel_id_cache.get(handle.lstrip("@").lower())
            if cached and cached.startswith("UC"):
                channel_id = cached

        # Priority 2: Extract channel_id from HTML BEFORE trying RSS URLs
        # This is more reliable than handle-based RSS URLs which can return 400
        if not channel_id and handle:
            candidate_pages = []
            if resolved_url:
                candidate_pages.append(resolved_url)
            # Also try the direct handle URL
            candidate_pages.append(
                f"https://www.youtube.com/@{quote(handle.lstrip('@'), safe="")}"
            )

            for page_url in candidate_pages:
                try:
                    page = requests.get(
                        page_url,
                        headers={"User-Agent": self.user_agent},
                        timeout=self.timeout,
                    )
                    if page.status_code == 200:
                        matches = re.findall(r'"channelId":"([^"]+)"', page.text)
                        if matches:
                            candidate_id = matches[0]
                            if candidate_id.startswith("UC"):
                                channel_id = candidate_id
                                # Cache for future use (in-memory)
                                self._channel_id_cache[handle.lstrip("@").lower()] = (
                                    candidate_id
                                )

                                # Persist to Channels table for future runs
                                # Always update channel name when discovered via RSS,
                                # even if channel already exists (fixes stale "Channel UC..." names)
                                try:
                                    from yt_fts.core.database import add_channel_info

                                    # Extract channel name from HTML if available
                                    name_matches = re.findall(
                                        r'"ownerText":{"runs":[{"text":"([^"]+)"',
                                        page.text,
                                    )
                                    channel_name = (
                                        name_matches[0]
                                        if name_matches
                                        else handle.lstrip("@")
                                    )
                                    add_channel_info(
                                        candidate_id, channel_name, page_url
                                    )
                                    _get_rss_logger().info(
                                        "Persisted channel %s (%s) to database",
                                        candidate_id,
                                        channel_name,
                                    )
                                except Exception as db_error:
                                    # Don't fail if we can't persist - the in-memory cache still works
                                    _get_rss_logger().debug(
                                        "Could not persist channel to database: %s",
                                        db_error,
                                    )

                                _get_rss_logger().info(
                                    "Extracted channel_id %s from %s",
                                    channel_id,
                                    page_url,
                                )
                                break
                except requests.RequestException:
                    continue

        # Now build RSS URLs with the best channel identifier we have
        rss_url = self._build_rss_url(channel_id, handle, resolved_url)
        candidate_urls = []
        if rss_url:
            candidate_urls.append(rss_url)
        # Only add handle URLs if we don't have a channel_id
        if handle and not channel_id:
            candidate_urls.extend(self._build_handle_urls(handle))

        if not candidate_urls:
            _result = RssCheckResult(
                status="error",
                video_ids=[],
                newest_id=None,
                oldest_id=None,
                message="Could not build RSS URL from channel info",
            )

        # De-duplicate candidates while preserving order
        seen = set()
        deduped = []
        for url in candidate_urls:
            if url not in seen:
                deduped.append(url)
                seen.add(url)
        candidate_urls = deduped

        logger = _get_rss_logger()
        response = None
        last_error = None
        last_status_code = None

        # Retry with exponential backoff for rate limiting (429) and server errors (500, 503)
        max_retries = 3
        base_delay = 2.0  # seconds

        for candidate in candidate_urls:
            for attempt in range(max_retries):
                try:
                    response = requests.get(
                        candidate,
                        headers={"User-Agent": self.user_agent},
                        timeout=self.timeout,
                    )
                    if response is not None:
                        logger.info(
                            "RSS GET %s -> %s (attempt %d)",
                            candidate,
                            response.status_code,
                            attempt + 1,
                        )

                    # Check for rate limiting or server errors that might be transient
                    if response.status_code in (429, 500, 502, 503, 504):
                        if attempt < max_retries - 1:
                            # Exponential backoff: 2s, 4s, 8s
                            delay = base_delay * (2**attempt)
                            logger.info(
                                "RSS rate limited/server error (HTTP %s), retrying in %.1fs...",
                                response.status_code,
                                delay,
                            )
                            time.sleep(delay)
                            continue
                        last_error = f"HTTP {response.status_code} (rate limited after {max_retries} retries)"
                        last_status_code = response.status_code
                        response = None
                        break

                    response.raise_for_status()
                    break  # Success - move to next candidate

                except requests.RequestException as e:
                    # Extract status code if available (for better error messages)
                    if hasattr(e, "response") and e.response is not None:
                        last_status_code = e.response.status_code

                    if attempt < max_retries - 1:
                        delay = base_delay * (2**attempt)
                        logger.info(
                            "RSS GET failed %s: %s, retrying in %.1fs...",
                            candidate,
                            e,
                            delay,
                        )
                        time.sleep(delay)
                    else:
                        logger.info(
                            "RSS GET failed %s: %s (final attempt)", candidate, e
                        )
                        last_error = e
                        response = None

            if response is not None:
                break  # Got a successful response from this candidate

        if response is None:
            # Even when RSS fails, try to get channel name via API escalation
            # This helps with channels that don't have RSS feeds
            if channel_id:
                try:
                    channel_name = self._escalate_channel_name_via_api(channel_id)
                    if channel_name:
                        from yt_fts.db.channels import add_channel_info

                        logger.info(
                            "Calling add_channel_info (API escalation after RSS fail): %s -> %s",
                            channel_id,
                            channel_name,
                        )
                        add_channel_info(
                            channel_id,
                            channel_name,
                            resolved_url
                            or f"https://www.youtube.com/channel/{channel_id}",
                        )
                        logger.info(
                            "Successfully updated channel name via API escalation (RSS failed): %s -> %s",
                            channel_id,
                            channel_name,
                        )
                except Exception as escalate_error:
                    logger.debug(
                        "API escalation failed after RSS error: %s", escalate_error
                    )

            # Build more descriptive error message
            if last_status_code:
                if last_status_code == 429:
                    msg = "Rate limited by YouTube (HTTP 429) - try again later"
                elif last_status_code == 404:
                    msg = (
                        "Channel/feed not found (HTTP 404) - may be private or deleted"
                    )
                elif last_status_code >= 500:
                    msg = f"YouTube server error (HTTP {last_status_code}) - temporary issue"
                else:
                    msg = f"RSS fetch failed: HTTP {last_status_code}"
            else:
                msg = f"RSS fetch failed: {last_error}"

            _result = RssCheckResult(
                status="error",
                video_ids=[],
                newest_id=None,
                oldest_id=None,
                message=msg,
            )
            return self._save_to_cache_and_return(cache_key, _result)

        # Extract channel name from RSS feed and update database
        # This ensures stale names like "Channel UC..." get updated to real names
        if channel_id:
            try:
                channel_name = self._extract_channel_name_from_feed(response.text)
                if channel_name:
                    from yt_fts.db.channels import add_channel_info

                    logger.info(
                        "Calling add_channel_info: %s -> %s", channel_id, channel_name
                    )
                    add_channel_info(
                        channel_id,
                        channel_name,
                        resolved_url or f"https://www.youtube.com/channel/{channel_id}",
                    )
                    logger.info(
                        "Successfully updated channel name from RSS: %s -> %s",
                        channel_id,
                        channel_name,
                    )
                else:
                    # Escalate to yt-api when RSS doesn't contain a parsable channel name
                    logger.debug(
                        "Could not extract channel name from RSS feed for %s, escalating to API",
                        channel_id,
                    )
                    channel_name = self._escalate_channel_name_via_api(channel_id)
                    if channel_name:
                        from yt_fts.db.channels import add_channel_info

                        logger.info(
                            "Calling add_channel_info (from API escalation): %s -> %s",
                            channel_id,
                            channel_name,
                        )
                        add_channel_info(
                            channel_id,
                            channel_name,
                            resolved_url
                            or f"https://www.youtube.com/channel/{channel_id}",
                        )
                        logger.info(
                            "Successfully updated channel name from API escalation: %s -> %s",
                            channel_id,
                            channel_name,
                        )
            except Exception as name_error:
                logger.exception(
                    "Could not update channel name from RSS/API: %s", name_error
                )

        # Parse video IDs and metadata
        video_ids = self._parse_video_ids(response.text)
        video_metadata = self._parse_video_ids_with_metadata(response.text)

        if not video_ids:
            _result = RssCheckResult(
                status="error",
                video_ids=[],
                newest_id=None,
                oldest_id=None,
                message="No videos found in RSS feed",
            )

        newest_id = video_ids[0]  # RSS returns newest first
        oldest_id = video_ids[-1]

        # Check for overlap with database
        videos_in_db = [vid for vid in video_ids if vid in db_video_ids]
        videos_not_in_db = [vid for vid in video_ids if vid not in db_video_ids]

        # Scenario 1: All RSS videos in database = up to date
        if len(videos_in_db) == len(video_ids):
            _result = RssCheckResult(
                status="skip",
                video_ids=video_ids,
                newest_id=newest_id,
                oldest_id=oldest_id,
                message=f"All {len(video_ids)} RSS videos already in database",
            )

        # Scenario 2: Newest video in database, but not all = gap detected
        # This means we have older videos but are missing some in between
        if newest_id in db_video_ids and len(videos_in_db) < len(video_ids):
            # Check if missing videos are actually available
            availability = self._check_video_availability(videos_not_in_db)

            scheduled_count = sum(1 for v in availability.values() if v == "scheduled")
            unavailable_count = sum(
                1 for v in availability.values() if v in ("unavailable", "members_only")
            )
            available_count = sum(1 for v in availability.values() if v == "available")

            # If all checked missing videos are scheduled/unavailable, skip with details
            if available_count == 0 and len(availability) > 0:
                parts = []
                if scheduled_count:
                    parts.append(f"{scheduled_count} scheduled")
                if unavailable_count:
                    parts.append(f"{unavailable_count} unavailable")

                return RssCheckResult(
                    status="skip",
                    video_ids=[],
                    newest_id=newest_id,
                    oldest_id=oldest_id,
                    message=f"All RSS videos in DB ({', '.join(parts) if parts else 'unavailable content'})",
                    unavailable_video_ids=videos_not_in_db,  # Track these to add to DB
                    unavailable_video_status=availability,  # Track individual statuses
                )

            # Dynamic threshold: if small gap with available videos, treat as new
            # (not skipping, since availability check confirmed they're downloadable)
            db_size = len(db_video_ids)
            gap_threshold = 10 if db_size >= 100 else 3

            if len(videos_not_in_db) <= gap_threshold and available_count > 0:
                # Small gap with available videos - return as new_videos for download
                # Filter to only available videos for downloading
                available_video_ids = [
                    vid
                    for vid in videos_not_in_db
                    if availability.get(vid) == "available"
                ]
                return RssCheckResult(
                    status="new_videos",
                    video_ids=available_video_ids,
                    newest_id=newest_id,
                    oldest_id=oldest_id,
                    message=f"{len(available_video_ids)} new video(s) available (small gap)",
                )

            # Find the gap - first video in RSS that's NOT in DB
            gap_start = None
            for vid in video_ids:
                if vid not in db_video_ids:
                    gap_start = vid
                    break

            return RssCheckResult(
                status="gap_detected",
                video_ids=video_ids,
                newest_id=newest_id,
                oldest_id=oldest_id,
                message=f"Gap detected: {len(videos_not_in_db)} videos in RSS not in DB, but newest is",
                gap_start_id=gap_start,
            )

        # Scenario 3: Newest video NOT in database = new videos to download
        # No gap - just purely new videos
        # Distinguish new channel (no videos in DB) from existing channel with new content
        if len(db_video_ids) == 0:
            # New channel - all videos are new, will use yt-dlp
            message = "all new videos, using yt-dlp"
        else:
            # Existing channel with new videos
            message = f"{len(videos_not_in_db)} new video(s) found"
            # Save RSS-discovered videos to database so they don't appear as "new" next time
            _save_rss_videos_to_db(channel_id, videos_not_in_db, video_metadata)

        return RssCheckResult(
            status="new_videos",
            video_ids=videos_not_in_db,  # Only return videos to download
            newest_id=newest_id,
            oldest_id=oldest_id,
            message=message,
            video_metadata=video_metadata,  # Include metadata for downstream use
        )


def _save_rss_videos_to_db(
    channel_id: str, video_ids: list[str], video_metadata: dict[str, dict[str, str]]
) -> None:
    """Save RSS-discovered videos to database with metadata.

    This ensures that videos discovered via RSS are tracked in the database,
    so subsequent runs don't treat them as "new" again.

    Args:
        channel_id: YouTube channel ID
        video_ids: List of video IDs to save
        video_metadata: Dict mapping video_id to {title, date, url}
    """
    if not video_ids:
        return

    from yt_fts.db.videos import add_video

    for video_id in video_ids:
        metadata = video_metadata.get(video_id, {})
        title = metadata.get("title", "RSS Discovery")
        date = metadata.get("date", "")
        url = metadata.get("url", f"https://www.youtube.com/watch?v={video_id}")

        try:
            add_video(
                channel_id=channel_id,
                video_id=video_id,
                video_title=title,
                video_url=url,
                video_date=date,
                last_checked=None,  # Will be set when transcript is downloaded
            )
            _get_rss_logger().debug(
                "Saved RSS-discovered video to DB: %s - %s", video_id, title
            )
        except Exception as e:
            _get_rss_logger().debug(
                "Failed to save RSS video to DB: %s - %s", video_id, e
            )


def create_rss_checker(timeout: float = 30.0) -> RssPreChecker:
    """Factory function to create RssPreChecker instance."""
    return RssPreChecker(timeout=timeout)


def extract_yt_video_count(channel_url: str, timeout: float = 5.0) -> int | None:
    """Extract total video count from YouTube channel.

    Note: YouTube doesn't easily expose total video count through public APIs.
    This function is a placeholder for future implementation.

    Args:
        channel_url: Channel URL (e.g., https://www.youtube.com/@handle)
        timeout: Request timeout in seconds

    Returns:
        Total video count or None if not available
    """
    # YouTube's API no longer provides channel video count reliably
    # The channel_video_count field in yt-dlp often returns "NA"
    # For now, we return None and display "?" for YouTube total
    return None
