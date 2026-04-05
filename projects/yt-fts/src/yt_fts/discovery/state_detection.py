"""
State-based video discovery system.

This module implements the 3-state discovery system:
- TRANSITION: Bootstrap/first run (empty or nearly empty DB)
- STEADY_STATE: Maintenance mode (DB verified complete, check for new uploads)
- RECOVERY: Repair mode (gaps detected or stale data)
"""
from __future__ import annotations

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, Tuple
from functools import wraps
import time
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# Database functions (moved from lazy imports for performance)
from yt_fts.db.channels import get_channel_stats, get_channel_api_total as db_get_api_total
from yt_fts.db.videos import get_video_ids_without_subtitles


# Simple TTL cache to eliminate redundant DB calls within same request cycle
_CACHE_TTL = 60  # 60 seconds - long enough for one channel state detection cycle
_MAX_CACHE_ENTRIES = 1000  # Maximum cache size to prevent unbounded growth
_db_cache: Dict[str, Tuple[float, Any]] = {}

# State detection thresholds
_TRANSITION_MIN_VIDEO_COUNT = 10  # Videos below this count = TRANSITION state
_STALENESS_THRESHOLD_DAYS = 7  # Days after which verification is considered stale

# Strategy selection thresholds
_LARGE_CHANNEL_THRESHOLD = 500  # Videos above this count considered "large"
_QUOTA_THRESHOLD_PCT = 20  # Minimum quota percentage to use API
_GAP_THRESHOLD = 50  # Minimum gap size to use API in RECOVERY


@dataclass
class ChannelData:
    """Fetched channel data to avoid redundant DB calls.

    Attributes:
        channel_id: YouTube channel ID
        db_count: Number of videos in local database
        api_total: Total videos from YouTube API (None if never fetched)
        last_checked: Timestamp of last API verification (None if never checked)
    """
    channel_id: str
    db_count: int
    api_total: Optional[int]
    last_checked: Optional[str]


def _clear_cache() -> None:
    """Clear the DB cache. Useful for testing."""
    _db_cache.clear()


def _cached_get(channel_id: str, cache_key: str, fetch_func):
    """Get value from cache or fetch and cache it."""
    full_key = f"{cache_key}:{channel_id}"
    now = time.time()

    if full_key in _db_cache:
        timestamp, value = _db_cache[full_key]
        if now - timestamp < _CACHE_TTL:
            logger.debug(f"Cache HIT: {cache_key} for {channel_id}")
            return value
        else:
            logger.debug(f"Cache EXPIRED: {cache_key} for {channel_id} (age: {int(now - timestamp)}s)")

    # Cache miss or expired, fetch and cache
    logger.debug(f"Cache MISS: {cache_key} for {channel_id} - fetching from DB")
    value = fetch_func()

    # Enforce cache size limit (FIFO eviction)
    if len(_db_cache) >= _MAX_CACHE_ENTRIES:
        # Remove oldest entries (10% of max size)
        num_to_remove = max(1, _MAX_CACHE_ENTRIES // 10)
        oldest_keys = sorted(_db_cache.keys(), key=lambda k: _db_cache[k][0])[:num_to_remove]
        for key in oldest_keys:
            del _db_cache[key]

    _db_cache[full_key] = (now, value)
    return value


class ChannelState(Enum):
    """Channel discovery state."""
    TRANSITION = "transition"
    STEADY_STATE = "steady_state"
    RECOVERY = "recovery"


class DiscoveryMethod(Enum):
    """Discovery method for video list."""
    RSS = "rss"
    API = "api"
    YTDLP = "ytdlp"


def get_db_video_count(channel_id: str) -> int:
    """Get total video count for channel from database (with caching)."""

    def _fetch():
        stats = get_channel_stats(channel_id)
        return stats.get("total", 0)

    return _cached_get(channel_id, "db_video_count", _fetch)


def get_channel_api_total(channel_id: str) -> Optional[int]:
    """Get API total video count for channel (with caching)."""

    def _fetch():
        return db_get_api_total(channel_id)

    return _cached_get(channel_id, "api_total", _fetch)


def get_api_total_last_checked(channel_id: str) -> Optional[str]:
    """Get timestamp when API total was last checked.
    
    Returns the timestamp when the channel's video count was last verified against the YouTube API.
    Returns None if the channel has never been verified.
    """
    full_key = f"api_total:{channel_id}"
    
    if full_key in _db_cache:
        timestamp, _ = _db_cache[full_key]
        # Return ISO format timestamp
        from datetime import datetime
        return datetime.fromtimestamp(timestamp).isoformat()
    
    return None  # Never verified


def days_since(timestamp: Optional[str]) -> int:
    """Calculate days since a timestamp string.
    
    Args:
        timestamp: ISO format timestamp string, or None if never checked
        
    Returns:
        Days since timestamp (0 for None/fresh, 999 for error/very stale)
    """
    if not timestamp:
        # Never verified = fresh data, treat as 0 days old
        return 0
    try:
        dt = datetime.fromisoformat(timestamp)
        return (datetime.now() - dt).days
    except Exception:
        return 999


def detect_channel_state(channel_id: str) -> tuple[ChannelState, ChannelData]:
    """
    Detect the current discovery state for a channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Tuple of (ChannelState, ChannelData) with state and fetched data
    """
    db_count = get_db_video_count(channel_id)
    api_total = get_channel_api_total(channel_id)
    last_checked = get_api_total_last_checked(channel_id)

    # Create ChannelData object to avoid redundant DB calls
    data = ChannelData(
        channel_id=channel_id,
        db_count=db_count,
        api_total=api_total,
        last_checked=last_checked,
    )

    # TRANSITION: Empty or nearly empty DB
    if db_count < _TRANSITION_MIN_VIDEO_COUNT:
        return ChannelState.TRANSITION, data

    # TRANSITION: Never verified against API
    if api_total is None:
        return ChannelState.TRANSITION, data

    # STEADY_STATE: Verified complete and recent
    if db_count == api_total and days_since(last_checked) < _STALENESS_THRESHOLD_DAYS:
        return ChannelState.STEADY_STATE, data

    # RECOVERY: Gap detected
    if db_count < api_total:
        return ChannelState.RECOVERY, data

    # RECOVERY: Stale verification (>7 days)
    if days_since(last_checked) >= _STALENESS_THRESHOLD_DAYS:
        return ChannelState.RECOVERY, data

    # Default to STEADY_STATE
    return ChannelState.STEADY_STATE, data


def transition_strategy(channel_id: str, quota_pct: float) -> DiscoveryMethod:
    """
    Select discovery method for TRANSITION state.

    Args:
        channel_id: YouTube channel ID
        quota_pct: Quota percentage available (0-100)

    Returns:
        DiscoveryMethod to use
    """
    db_count = get_db_video_count(channel_id)

    # Large channel: API worth the quota
    if db_count > _LARGE_CHANNEL_THRESHOLD:
        return DiscoveryMethod.API if quota_pct > _QUOTA_THRESHOLD_PCT else DiscoveryMethod.YTDLP

    # Small channel: yt-dlp is fine
    return DiscoveryMethod.YTDLP


def steady_state_strategy(channel_id: str) -> DiscoveryMethod:
    """
    Select discovery method for STEADY_STATE state.

    Always use RSS for steady state (fast, free, catches new uploads).

    Args:
        channel_id: YouTube channel ID

    Returns:
        Always DiscoveryMethod.RSS
    """
    return DiscoveryMethod.RSS


def recovery_strategy(channel_id: str, quota_pct: float) -> DiscoveryMethod:
    """
    Select discovery method for RECOVERY state.

    Args:
        channel_id: YouTube channel ID
        quota_pct: Quota percentage available (0-100)

    Returns:
        DiscoveryMethod to use
    """
    api_total = get_channel_api_total(channel_id)
    db_count = get_db_video_count(channel_id)
    
    # If API total is None, we can't calculate gap - default to yt-dlp
    if api_total is None:
        return DiscoveryMethod.YTDLP
    
    gap_size = api_total - db_count

    # Large gap: API worth it
    if gap_size > _GAP_THRESHOLD:
        return DiscoveryMethod.API if quota_pct > _QUOTA_THRESHOLD_PCT else DiscoveryMethod.YTDLP

    # Small gap: yt-dlp is fine
    return DiscoveryMethod.YTDLP


def get_download_queue(channel_id: str) -> dict:
    """
    Get download queue for a channel.

    Always prioritizes missing transcripts (high priority).

    Args:
        channel_id: YouTube channel ID

    Returns:
        Dict with priority, video_ids, and reason
    """
    missing = get_video_ids_without_subtitles(channel_id)

    return {
        "priority": "high",
        "video_ids": missing,
        "reason": "missing_transcripts",
    }

