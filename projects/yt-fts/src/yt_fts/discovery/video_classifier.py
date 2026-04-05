"""
Video classification module.

This module classifies videos into types:
- NORMAL: Standard video with subtitles available
- SHORT: YouTube Short
- SCHEDULED: Scheduled/upcoming video
- MEMBERS_ONLY: Members-only content
- UNAVAILABLE: Unavailable/private/deleted video
- NO_SUBTITLES: Video available but no captions
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum


class VideoType(Enum):
    """Video classification type."""
    NORMAL = "normal"
    SHORT = "short"
    SCHEDULED = "scheduled"
    MEMBERS_ONLY = "members_only"
    UNAVAILABLE = "unavailable"
    NO_SUBTITLES = "no_subtitles"


def is_short_video(url: str, is_short: int | None = None) -> bool:
    """
    Check if a video is a YouTube Short.

    Args:
        url: The video URL to check
        is_short: Optional is_short flag from metadata

    Returns:
        True if the video is a Short
    """
    # Check by URL first
    if "/shorts/" in url:
        return True

    # Check by flag
    if is_short == 1:
        return True

    return False


def is_scheduled_video(info: dict) -> bool:
    """
    Check if a video is scheduled or upcoming.

    Args:
        info: yt-dlp info dict for the video

    Returns:
        True if the video is scheduled/upcoming
    """
    # Check live_status for upcoming
    live_status = info.get("live_status", "")
    if live_status == "is_upcoming":
        return True

    # Check release_timestamp for future datetime
    release_timestamp = info.get("release_timestamp")
    if release_timestamp:
        try:
            release_time = datetime.fromisoformat(release_timestamp.replace("Z", "+00:00"))
            if release_time > datetime.now(release_time.tzinfo):
                return True
        except Exception:
            pass

    return False


def has_no_subtitles(info: dict) -> bool:
    """
    Check if a video has no subtitles in any language.

    Args:
        info: yt-dlp info dict for the video

    Returns:
        True if the video has no subtitles (manual or auto)
    """
    subtitles = info.get("subtitles", {})
    auto_captions = info.get("automatic_captions", {})
    return not subtitles and not auto_captions


def classify_video(info: dict) -> dict:
    """
    Classify a video based on its metadata.

    Classification priority (highest to lowest):
    1. SCHEDULED - Not available yet
    2. MEMBERS_ONLY - Requires authentication
    3. UNAVAILABLE - Permanently unavailable
    4. SHORT - YouTube Short format
    5. NO_SUBTITLES - Available but no captions
    6. NORMAL - Standard video with subtitles

    Args:
        info: yt-dlp info dict for the video

    Returns:
        Dict with video_type, downloadable, retryable, reason
    """
    url = info.get("url", "")

    # Priority 1: Check if scheduled (highest priority)
    if is_scheduled_video(info):
        return {
            "video_id": info.get("id", ""),
            "video_type": VideoType.SCHEDULED.value,
            "url": url,
            "title": info.get("title", ""),
            "downloadable": False,
            "retryable": True,
            "reason": "Video is scheduled for future release",
        }

    # Priority 2: Check if members-only
    availability = info.get("availability", "")
    if availability == "members_only":
        return {
            "video_id": info.get("id", ""),
            "video_type": VideoType.MEMBERS_ONLY.value,
            "url": url,
            "title": info.get("title", ""),
            "downloadable": False,
            "retryable": True,  # With cookies
            "reason": "Members-only content (requires authentication)",
        }

    # Priority 3: Check if unavailable
    if availability == "unavailable" or availability == "private":
        return {
            "video_id": info.get("id", ""),
            "video_type": VideoType.UNAVAILABLE.value,
            "url": url,
            "title": info.get("title", ""),
            "downloadable": False,
            "retryable": False,
            "reason": f"Video is {availability}",
        }

    # Priority 4: Check if short
    if is_short_video(url, info.get("is_short")):
        return {
            "video_id": info.get("id", ""),
            "video_type": VideoType.SHORT.value,
            "url": url,
            "title": info.get("title", ""),
            "downloadable": True,
            "retryable": False,
            "reason": "YouTube Short format",
        }

    # Priority 5: Check if no subtitles
    if has_no_subtitles(info):
        return {
            "video_id": info.get("id", ""),
            "video_type": VideoType.NO_SUBTITLES.value,
            "url": url,
            "title": info.get("title", ""),
            "downloadable": False,
            "retryable": False,
            "reason": "No subtitles or captions available",
        }

    # Priority 6: Normal video
    return {
        "video_id": info.get("id", ""),
        "video_type": VideoType.NORMAL.value,
        "url": url,
        "title": info.get("title", ""),
        "downloadable": True,
        "retryable": False,
        "reason": "Standard video with subtitles",
    }

