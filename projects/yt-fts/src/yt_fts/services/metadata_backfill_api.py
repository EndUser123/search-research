"""
YouTube Data API v3 based metadata backfill service.

This module provides fast metadata fetching using the official YouTube API
instead of yt-dlp scraping. Much faster and respects API quotas.

Quota: QUOTA_PER_KEY units/day per key (auto-calculated from config)
Cost: 1 unit per API request (up to 50 videos per request)
      Batching 50 videos per call = 98% fewer quota units vs 1 video per call
"""
from __future__ import annotations

import contextlib
import logging
import sqlite3
import sys
import time
from datetime import datetime, timezone
from itertools import cycle

import requests
from rich.console import Console
from rich.progress import BarColumn, Progress, TaskID, TextColumn

from yt_fts.config import QUOTA_PER_KEY
from yt_fts.core.database import (
    get_channel_id_from_input,
    get_db_connection,
    get_db_path,
    get_vid_ids_by_channel_id,
)

logger = logging.getLogger(__name__)


class YouTubeAPIError(Exception):
    """Custom exception for YouTube API errors."""


def _init_quota_table() -> None:
    """Initialize the quota tracking table in the database.

    Tracks quota usage per API key to properly handle key rotation.
    Each key has its own 10,000 quota limit.

    NOTE: This is a best-effort initialization. If the database is locked,
    we'll try again on the next call. The quota tracking will use defaults
    until the table is successfully created.
    """
    # NOTE: Direct sqlite3.connect() usage is intentional here.
    # We need isolation_level="IMMEDIATE" for concurrent quota tracking
    # which get_db_connection() doesn't support.
    # These connections are short-lived and properly closed.


    db_path = get_db_path()
    conn = None
    max_retries = 2
    delay = 0.1
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=2.0, isolation_level="IMMEDIATE")
            conn.execute("PRAGMA busy_timeout = 2000")
            cur = conn.cursor()
            cur.execute(
                "\n                CREATE TABLE IF NOT EXISTS yt_api_quota (\n                    date TEXT PRIMARY KEY,\n                    quota_used INTEGER DEFAULT 0,\n                    last_updated TEXT\n                )\n            "
            )
            cur.execute(
                "\n                CREATE TABLE IF NOT EXISTS yt_api_quota_per_key (\n                    date TEXT,\n                    key_index INTEGER,\n                    quota_used INTEGER DEFAULT 0,\n                    PRIMARY KEY (date, key_index)\n                )\n            "
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            logger.debug("Could not init quota table (may already exist): %s", e)
            return
        except Exception as e:
            logger.debug("Unexpected error initing quota table: %s", e)
            return
        finally:
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()


def _load_quota_from_db() -> int:
    """Load today's quota usage from the database.

    Returns:
        Quota used today (resets at midnight)
    """
    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute(
        "\n        CREATE TABLE IF NOT EXISTS yt_api_quota (\n            date TEXT PRIMARY KEY,\n            quota_used INTEGER DEFAULT 0,\n            last_updated TEXT\n        )\n    "
    )
    today = datetime.now().strftime("%Y-%m-%d")
    cur.execute("SELECT quota_used FROM yt_api_quota WHERE date = ?", (today,))
    result = cur.fetchone()
    conn.close()
    return result[0] if result else 0


def _load_quota_per_key_from_db() -> dict[int, int]:
    """Load today's quota usage per key from the database.

    Returns:
        Dict mapping key_index -> quota used for that key
    """
    db_path = get_db_path()
    conn = None
    try:
        _init_quota_table()
        conn = sqlite3.connect(db_path, timeout=2.0)
        cur = conn.cursor()
        today = datetime.now().strftime("%Y-%m-%d")
        cur.execute(
            "\n            SELECT key_index, quota_used FROM yt_api_quota_per_key \n            WHERE date = ?\n        ",
            (today,),
        )
        return {row[0]: row[1] for row in cur.fetchall()}
    except sqlite3.OperationalError as e:
        if "no such table" in str(e):
            logger.debug("Per-key quota table not ready: %s", e)
            return {}
        raise
    finally:
        if conn:
            with contextlib.suppress(Exception):
                conn.close()


def _save_quota_per_key_to_db(key_index: int, used: int) -> None:
    """Save quota usage for a specific key to the database.

    Args:
        key_index: Index of the API key (0, 1, 2, ...)
        used: Quota used for this key
    """

    logger.debug("[DEBUG] _save_quota_per_key_to_db: key=%s, used=%s", key_index, used)
    db_path = get_db_path()
    conn = None
    max_retries = 5
    delay = 0.05
    for attempt in range(max_retries):
        try:
            logger.debug(
                "[DEBUG] _save_quota_per_key_to_db: attempt %s/%s",
                attempt + 1,
                max_retries,
            )
            conn = sqlite3.connect(db_path, timeout=10.0)
            conn.execute("PRAGMA busy_timeout = 10000")
            cur = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            datetime.now().isoformat()
            cur.execute(
                "\n                INSERT OR REPLACE INTO yt_api_quota_per_key (date, key_index, quota_used)\n                VALUES (?, ?, ?)\n            ",
                (today, key_index, used),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            logger.debug("Failed to save per-key quota: %s", e)
            return
        finally:
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()


def _flush_quota_to_db() -> None:
    """Flush pending quota updates to database in one write.

    Reduces database writes from every API call to every N calls.

    Uses _db_write_lock to serialize with video metadata operations.
    """
    global _pending_quota_write, _api_calls_since_last_write, _pending_per_key_quota
    if not _pending_quota_write:
        return
    import sqlite3

    from yt_fts.db.infra import _db_write_lock

    with _db_write_lock:
        db_path = get_db_path()
        conn = None
        try:
            conn = sqlite3.connect(db_path, timeout=2.0, isolation_level="IMMEDIATE")
            conn.execute("PRAGMA busy_timeout = 2000")
            cur = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now().isoformat()
            cur.execute(
                "\n                INSERT OR REPLACE INTO yt_api_quota (date, quota_used, last_updated)\n                VALUES (?, ?, ?)\n            ",
                (today, _global_quota_used, now),
            )
            for key_idx, amount in _pending_per_key_quota.items():
                cur.execute(
                    "\n                    INSERT OR REPLACE INTO yt_api_quota_per_key (date, key_index, quota_used)\n                    VALUES (?, ?, ?)\n                ",
                    (today, key_idx, amount),
                )
            conn.commit()
            _pending_quota_write = False
            _pending_per_key_quota.clear()
            _api_calls_since_last_write = 0
        except Exception as e:
            logger.debug("Failed to flush quota to DB: %s", e)
        finally:
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()


def _save_quota_to_db(used: int) -> None:
    """Save quota usage to the database.

    Args:
        used: Total quota used today
    """
    # NOTE: Direct sqlite3.connect() usage is intentional here.
    # We need isolation_level="IMMEDIATE" for concurrent quota tracking
    # which get_db_connection() doesn't support.
    # These connections are short-lived and properly closed.


    db_path = get_db_path()
    conn = None
    max_retries = 2
    delay = 0.1
    for attempt in range(max_retries):
        try:
            conn = sqlite3.connect(db_path, timeout=2.0, isolation_level="IMMEDIATE")
            conn.execute("PRAGMA busy_timeout = 2000")
            cur = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            now = datetime.now().isoformat()
            cur.execute(
                "\n                INSERT OR REPLACE INTO yt_api_quota (date, quota_used, last_updated)\n                VALUES (?, ?, ?)\n            ",
                (today, used, now),
            )
            conn.commit()
            return
        except sqlite3.OperationalError as e:
            if "locked" in str(e).lower() and attempt < max_retries - 1:
                time.sleep(delay)
                delay *= 2
                continue
            if "locked" in str(e).lower():
                logger.debug("Database locked, skipping quota save (not critical)")
                return
            return
        except Exception as e:
            logger.debug("Failed to save quota to DB: %s", e)
            return
        finally:
            if conn:
                with contextlib.suppress(Exception):
                    conn.close()


def _reset_quota_if_new_day() -> None:
    """Reset quota counter if the day has changed since last load.

    This is called on initialization to ensure we start fresh at midnight.
    """
    global _global_quota_used, _last_checked_date, _per_key_quota_used
    today = datetime.now().strftime("%Y-%m-%d")
    if _last_checked_date != today:
        # Fresh process start (None) or crossed day boundary: reset to 0
        # Do NOT load from DB to avoid carrying over previous day's quota
        _global_quota_used = 0
        _per_key_quota_used = {}
        _last_checked_date = today


_global_quota_used = 0
_last_checked_date = None
_per_key_quota_used: dict[int, int] = {}
_pending_quota_write = False
_pending_per_key_quota: dict[int, int] = {}
_api_calls_since_last_write = 0
_BATCH_THRESHOLD = 10


def _get_key_index(keys: list[str], key: str) -> int:
    """Get the index of a key in the keys list.

    Args:
        keys: List of all API keys
        key: The key to find

    Returns:
        Index of the key, or 0 if not found
    """
    try:
        return keys.index(key)
    except ValueError:
        return 0


class YouTubeAPIBackfill:
    """Service for backfilling video metadata using YouTube Data API v3."""

    API_URL = "https://www.googleapis.com/youtube/v3/videos"
    _daily_quota_limit = QUOTA_PER_KEY

    @classmethod
    def get_global_quota_info(cls) -> dict[str, int]:
        """Get global quota usage info across all API keys.

        Returns:
            Dict with used, remaining, limit, and percentage across all keys
        """
        global _global_quota_used, _per_key_quota_used
        num_keys = len(_per_key_quota_used) if _per_key_quota_used else 0
        if num_keys == 0:
            import os

            for i in range(1, 10):
                key_name = "YOUTUBE_API_KEY" if i == 1 else f"YOUTUBE_API_KEY_{i}"
                if os.getenv(key_name):
                    num_keys += 1
            if num_keys == 0:
                num_keys = 1
        total_limit = cls._daily_quota_limit * num_keys
        total_used = (
            sum(_per_key_quota_used.values())
            if _per_key_quota_used
            else _global_quota_used
        )
        total_remaining = max(0, total_limit - total_used)
        return {
            "used": total_used,
            "limit": total_limit,
            "remaining": total_remaining,
            "percentage": (
                round(total_used / total_limit * 100, 1) if total_limit > 0 else 0
            ),
            "num_keys": num_keys,
        }


    @staticmethod
    def get_per_key_quota_info() -> list[dict[str, Any]]:
        """Get quota usage info for each API key individually.

        Returns:
            List of dicts, one per key, with:
                - key_index: Index of the key (0, 1, 2, 3)
                - key_name: Name like "YOUTUBE_API_KEY_1"
                - used: Quota used today
                - remaining: Quota remaining
                - limit: Daily quota limit
                - percentage: Percentage used
        """
        # Load per-key quota from DB for accurate current state
        per_key_from_db = _load_quota_per_key_from_db()

        # Get number of API keys
        import os
        num_keys = 0
        key_names = []
        for i in range(1, 10):
            key_name = "YOUTUBE_API_KEY" if i == 1 else f"YOUTUBE_API_KEY_{i}"
            if os.getenv(key_name):
                num_keys += 1
                key_names.append(key_name)

        if num_keys == 0:
            num_keys = 1
            key_names.append("YOUTUBE_API_KEY")

        # Build info for each key
        key_info = []
        for idx in range(num_keys):
            used = per_key_from_db.get(idx, 0)

            remaining = max(0, YouTubeAPIBackfill._daily_quota_limit - used)
            percentage = (used / YouTubeAPIBackfill._daily_quota_limit * 100) if YouTubeAPIBackfill._daily_quota_limit > 0 else 0

            key_info.append({
                "key_index": idx,
                "key_name": key_names[idx] if idx < len(key_names) else f"YOUTUBE_API_KEY_{idx + 1}",
                "used": used,
                "remaining": remaining,
                "limit": YouTubeAPIBackfill._daily_quota_limit,
                "percentage": percentage,
            })

        return key_info

    def _add_quota_and_persist(self, amount: int) -> None:
        """Add to quota usage (batched - flushed every N calls).

        Args:
            amount: Amount to add to quota usage
        """
        global _global_quota_used, _per_key_quota_used, _pending_quota_write, _api_calls_since_last_write, _pending_per_key_quota
        _reset_quota_if_new_day()
        _global_quota_used += amount
        _per_key_quota_used[self.current_key_index] = (
            _per_key_quota_used.get(self.current_key_index, 0) + amount
        )
        _pending_quota_write = True
        _pending_per_key_quota[self.current_key_index] = _per_key_quota_used[
            self.current_key_index
        ]
        _api_calls_since_last_write += 1
        if _api_calls_since_last_write >= _BATCH_THRESHOLD:
            _flush_quota_to_db()
        if _per_key_quota_used[self.current_key_index] >= self._daily_quota_limit:
            self._exhausted_keys.add(self.current_key_index)
            logger.warning(
                "API key %s exhausted (%s/%s)",
                self.current_key_index,
                _per_key_quota_used[self.current_key_index],
                self._daily_quota_limit,
            )

    @staticmethod
    def reset_quota_tracking() -> None:
        """Reset quota tracking to zero.

        Use this when:
        - The API quota has been reset (midnight Pacific Time)
        - You've switched to new API keys
        - The tracking has become desynchronized from reality
        """
        global _global_quota_used, _per_key_quota_used, _last_checked_date
        _global_quota_used = 0
        _per_key_quota_used = {}
        _last_checked_date = None
        try:
            from yt_fts.utils.config import get_db_path

            db_path = get_db_path()
            conn = sqlite3.connect(db_path)
            conn.execute(
                "DELETE FROM yt_api_quota WHERE date = ?",
                (datetime.now(timezone.utc).date().isoformat(),),
            )
            conn.execute(
                "INSERT INTO yt_api_quota (date, quota_used) VALUES (?, 0)",
                (datetime.now(timezone.utc).date().isoformat(),),
            )
            conn.commit()
            conn.close()
            print("✓ Quota tracking reset to 0")
        except Exception as e:
            print(f"Warning: Could not reset database quota: {e}")

    def format_quota_lines(self) -> list[str]:
        """Return per-key quota status as individual display lines."""
        global _per_key_quota_used
        _reset_quota_if_new_day()
        if hasattr(self, "api_keys") and self.api_keys:
            num_keys = len(self.api_keys)
            getattr(self, "current_key_index", 0)
        else:
            num_keys = (
                max(_per_key_quota_used.keys(), default=-1) + 1
                if _per_key_quota_used
                else 1
            )
        parts = []
        for idx in range(num_keys):
            used = _per_key_quota_used.get(idx, 0)
            remaining = max(0, self._daily_quota_limit - used)
            if remaining == 0:
                parts.append(f"Key {idx + 1}: [red]0 remaining[/red]")
            else:
                parts.append(f"Key {idx + 1}: {remaining:,} remaining")
        return parts

    def format_quota_display(self) -> str:
        """Format quota info for display showing per-key status (compact)."""
        parts = self.format_quota_lines()
        return " | ".join(parts) if parts else "No quota data"

    def __init__(
        self,
        api_keys: list[str] | None = None,
        console: Console | None = None,
        show_progress: bool | Progress | tuple[object, object, str] = True,
    ):
        """Initialize the YouTube API backfill service.

        Args:
            api_keys: List of YouTube API keys for rotation (auto-loads from env if None)
            console: Rich console for output
            show_progress: Show per-page progress bar (disable for parallel mode).
                          Can be bool (True/False), a Rich Progress object for nested updates,
                          or a tuple of (coordinator, task_id, channel_name) for thread-safe updates
                          via ThreadSafeProgressCoordinator. When a coordinator tuple is provided,
                          this service updates via the coordinator's queue instead of creating
                          its own progress bar.
        """
        if api_keys is None:
            api_keys = self._load_api_keys()
        if not api_keys:
            msg = "No YouTube API keys provided. Set YOUTUBE_API_KEY in .env"
            raise ValueError(msg)
        self.api_keys = api_keys
        self.key_cycle = cycle(api_keys)
        self.current_key = next(self.key_cycle)
        self.current_key_index = 0
        self.console = console or Console(force_terminal=True)
        self._quota_used = 0

        # Handle show_progress as bool | Progress | tuple[coordinator, task_id, channel_name]
        from rich.progress import Progress
        if isinstance(show_progress, tuple) and len(show_progress) >= 2:
            # Thread-safe coordinator mode: (coordinator, task_id, channel_name)
            self._coordinator, self._task_id = show_progress[0], show_progress[1]
            self._channel_name_for_progress = show_progress[2] if len(show_progress) >= 3 else None
            self._parent_progress = None
            self.show_progress = False  # Don't create nested progress
        elif isinstance(show_progress, Progress):
            # Parent provided a Progress context - use it instead of creating our own
            self._parent_progress = show_progress
            self._coordinator = None
            self._task_id = None
            self.show_progress = False  # Don't create nested progress
        else:
            # Traditional behavior: show_progress is bool
            self._parent_progress = None
            self._coordinator = None
            self._task_id = None
            self._channel_name_for_progress = None
            self.show_progress = show_progress

        _reset_quota_if_new_day()
        global _per_key_quota_used
        if not _per_key_quota_used:
            for i in range(len(api_keys)):
                _per_key_quota_used[i] = 0
        self._exhausted_keys: set[int] = {
            idx
            for idx, used in _per_key_quota_used.items()
            if used >= self._daily_quota_limit
        }

    def _load_api_keys(self) -> list[str]:
        """Load API keys from environment variables.

        Supports YOUTUBE_API_KEY, YOUTUBE_API_KEY_2, through YOUTUBE_API_KEY_5.
        Each key provides 10,000 quota per day.
        """
        import os

        keys = []
        if key1 := os.getenv("YOUTUBE_API_KEY"):
            keys.append(key1)
        for i in range(2, 6):
            env_name = f"YOUTUBE_API_KEY_{i}"
            if key := os.getenv(env_name):
                keys.append(key)
        return keys

    def _get_channel_display_name(self, channel_id: str) -> str | None:
        """Get channel display name from database."""
        try:
            from yt_fts.core.database import get_db_connection

            conn = get_db_connection()
            row = conn.execute(
                "SELECT channel_name FROM Channels WHERE channel_id = ?", (channel_id,)
            ).fetchone()
            if row and row[0]:
                return row[0]
        except (OSError, ValueError, RuntimeError):
            pass
        return None

    def _rotate_key(self) -> None:
        """Rotate to next available API key, skipping exhausted ones.

        A key is exhausted if it has used >= 10,000 quota today.
        """
        global _per_key_quota_used
        attempts = 0
        max_attempts = len(self.api_keys) * 2
        while attempts < max_attempts:
            next_key = next(self.key_cycle)
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self.current_key = next_key
            key_quota = _per_key_quota_used.get(self.current_key_index, 0)
            if key_quota < self._daily_quota_limit:
                logger.debug(
                    "Rotated to key %s (quota: %s/%s)",
                    self.current_key_index,
                    key_quota,
                    self._daily_quota_limit,
                )
                return
            logger.debug(
                "Key %s exhausted (%s/%s), skipping...",
                self.current_key_index,
                key_quota,
                self._daily_quota_limit,
            )
            attempts += 1
        logger.warning("All API keys exhausted! Consider using yt-dlp fallback.")

    def _fetch_video_metadata_batch(self, video_ids: list[str]) -> dict[str, dict]:
        """Fetch metadata for up to 50 videos in one API call.

        Args:
            video_ids: List of video IDs (max 50 per call)

        Returns:
            Dict mapping video_id -> metadata dict

        Raises:
            YouTubeAPIError: If API call fails
        """
        if not video_ids:
            return {}
        if len(video_ids) > 50:
            results = {}
            for i in range(0, len(video_ids), 50):
                batch = video_ids[i : i + 50]
                results.update(self._fetch_video_metadata_batch(batch))
            return results
        params = {
            "part": "contentDetails,statistics,snippet",
            "id": ",".join(video_ids),
            "key": self.current_key,
        }
        try:
            import time

            meta_start = time.time()
            response = requests.get(self.API_URL, params=params, timeout=10)
            meta_elapsed = time.time() - meta_start
            logger.info(
                "Metadata API call time: %ss for %s videos",
                meta_elapsed,
                len(video_ids),
            )
            self._quota_used += 1
            self._add_quota_and_persist(1)
            if response.status_code == 403:
                logger.warning(
                    "API key quota exceeded or error: %s", response.text[:200]
                )
                self._rotate_key()
                params["key"] = self.current_key
                response = requests.get(self.API_URL, params=params, timeout=10)
                self._add_quota_and_persist(1)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            msg = f"API request failed: {e}"
            raise YouTubeAPIError(msg)
        results = {}
        for item in data.get("items", []):
            video_id = item.get("id")
            if not video_id:
                continue
            duration = self._parse_duration(
                item.get("contentDetails", {}).get("duration", "PT0S")
            )
            thumbnails = item.get("snippet", {}).get("thumbnails", {})
            thumbnail_url = (
                thumbnails.get("maxRes", {}).get("url")
                or thumbnails.get("high", {}).get("url")
                or thumbnails.get("medium", {}).get("url")
                or thumbnails.get("default", {}).get("url")
                or ""
            )
            view_count = int(item.get("statistics", {}).get("viewCount", 0) or 0)
            is_short = 1 if duration > 0 and duration < 60 else 0
            results[video_id] = {
                "duration": duration,
                "thumbnail_url": thumbnail_url,
                "view_count": view_count,
                "is_short": is_short,
            }
        return results

    def _parse_duration(self, iso_duration: str) -> int:
        """Parse ISO 8601 duration to seconds.

        Args:
            iso_duration: Duration in ISO 8601 format (e.g., "PT4M13S", "PT1H23M45S")

        Returns:
            Duration in seconds
        """
        import re

        match = re.match("PT(?:(\\d+)H)?(?:(\\d+)M)?(?:(\\d+)S)?", iso_duration)
        if not match:
            return 0
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        seconds = int(match.group(3) or 0)
        return hours * 3600 + minutes * 60 + seconds

    def _get_upload_playlist_id(self, channel_id: str) -> str | None:
        """Get the upload playlist ID for a channel.

        Uses the YouTube API to get the actual uploads playlist ID.
        Falls back to "UU" transformation if API fails.

        Args:
            channel_id: YouTube channel ID (starts with UC)

        Returns:
            Upload playlist ID, or None if channel_id format is invalid
        """
        if not channel_id or not channel_id.startswith("UC"):
            logger.warning("Invalid channel_id format: %s", channel_id)
            return None
        upload_id = "UU" + channel_id[2:]
        logger.debug("Trying UU transformation: %s", upload_id)
        try:
            params = {
                "part": "contentDetails",
                "id": channel_id,
                "key": self.current_key,
            }
            logger.debug("Calling channels API for %s...", channel_id[:20])
            response = requests.get(
                "https://www.googleapis.com/youtube/v3/channels",
                params=params,
                timeout=5,
            )
            if response.status_code == 200:
                data = response.json()
                if data.get("items"):
                    related_playlists = (
                        data["items"][0]
                        .get("contentDetails", {})
                        .get("relatedPlaylists", {})
                    )
                    actual_upload_id = related_playlists.get("uploads")
                    if actual_upload_id:
                        logger.debug(
                            "Upload playlist ID from API: %s", actual_upload_id
                        )
                        return actual_upload_id
                    logger.debug("No uploads in API response, using UU transformation")
                    return upload_id
                logger.debug(
                    "Channel %s not found in API, using UU transformation", channel_id
                )
                return upload_id
            logger.debug(
                "API returned %s for %s, using UU transformation",
                response.status_code,
                channel_id,
            )
            return upload_id
        except requests.Timeout:
            logger.debug("Timeout verifying upload playlist, using UU transformation")
            return upload_id
        except Exception as e:
            logger.debug(
                "Error verifying upload playlist: %s, using UU transformation", e
            )
            return upload_id
        return upload_id


    def _should_update_progress(self) -> bool:
        """Check if enough time has elapsed for progress update (2Hz rate limit)."""
        current_time = time.time()
        if not hasattr(self, '_last_progress_time_task'):
            self._last_progress_time_task = 0

        time_since_last = current_time - self._last_progress_time_task
        if time_since_last >= 0.5:  # 2Hz = smooth updates, no flicker
            self._last_progress_time_task = current_time
            return True
        return False

    def _update_progress_via_coordinator(
        self, actual_count: int, estimated_total: int
    ) -> None:
        """Update progress via coordinator (thread-safe).
        
        Shows progress in fields (e.g., "50/20,000") without needing to update
        the task's total parameter, which Rich doesn't allow after creation.
        """
        completed_pct = min(100, int((actual_count / estimated_total * 100) if estimated_total > 0 else 100))
        stats_str = f"{actual_count:,}/{estimated_total:,}" if estimated_total > 0 else f"{actual_count:,}"

        if self._channel_name_for_progress:
            self._coordinator.update_by_channel(
                self._channel_name_for_progress,
                completed=completed_pct,
                fields={"stats": stats_str}
            )

    def _update_progress_via_rich(
        self, progress_task: TaskID, actual_count: int, estimated_total: int
    ) -> None:
        """Update progress via Rich Progress."""
        completed_pct = min(100, int((actual_count / estimated_total * 100) if estimated_total > 0 else 100))
        stats_str = f"{actual_count:,}/{estimated_total:,}" if estimated_total > 0 else f"{actual_count:,}"

        self._parent_progress.update(
            progress_task,
            completed=completed_pct,
            fields={"stats": stats_str}
        )

    def fetch_all_videos_from_channel(
        self,
        channel_id: str,
        max_results: int | None = None,
        progress_callback: callable | None = None,
        progress_task: TaskID | None = None,
    ) -> list[dict]:
        """Fetch all videos from a channel using YouTube API.

        Uses the playlistItems endpoint with the channel's upload playlist.
        This is much faster than yt-dlp scraping and provides full metadata.

        Args:
            channel_id: YouTube channel ID
            max_results: Maximum videos to fetch (None for all)
            progress_callback: Optional callback(video_count) for progress updates (legacy)
            progress_task: Optional parent Progress task ID for nested progress updates.
                          When provided, updates parent task instead of creating new progress bar.
                          Use this for parent-owned progress pattern to avoid flashing.

        Returns:
            List of video dicts with keys: video_id, title, url, date,
            duration, thumbnail_url, view_count, is_short
        """
        # Track quota before this operation
        quota_before = self._quota_used

        logger.info(
            "fetch_all_videos_from_channel: starting for %s...", channel_id[:20]
        )
        
        # Show progress indication before potentially long API call
        if self.console and self.show_progress:
            try:
                self.console.print(
                    "   ⎿ [cyan]Fetching channel metadata via yt-api (may take 10-30s)...[/cyan]"
                )
            except Exception:
                pass  # Don't fail if console print fails
        
        self._get_channel_display_name(channel_id) or channel_id[:30]
        upload_playlist_id = self._get_upload_playlist_id(channel_id)
        logger.info(
            "fetch_all_videos_from_channel: got upload_playlist_id=%s...",
            upload_playlist_id[:20] if upload_playlist_id else None,
        )
        if not upload_playlist_id:
            logger.warning("Invalid channel_id format: %s", channel_id)
            if self.console:
                self.console.print(
                    f"   ⎿ [red]yt-api: ✗ Invalid channel_id: {channel_id}[/red]"
                )
            return []
        playlist_url = "https://www.googleapis.com/youtube/v3/playlistItems"
        videos = []
        next_page_token = None
        total_fetched = 0
        estimated_total = 0
        # Track last printed progress to avoid duplicates
        _last_printed_progress = None
        _last_progress_time = time.time()  # For rate limiting (4Hz max)
        _progress_call_count = 0  # Debug: count total progress update attempts
        try:
            while True:
                if max_results and total_fetched >= max_results:
                    break
                params = {
                    "part": "snippet,contentDetails",
                    "playlistId": upload_playlist_id,
                    "maxResults": (
                        min(50, max_results - total_fetched) if max_results else 50
                    ),
                    "key": self.current_key,
                    "pageToken": next_page_token if next_page_token else "",
                }
                try:
                    api_start = time.time()
                    logger.info(
                        "About to call playlistItems API (page %s)...",
                        total_fetched // 50 + 1,
                    )
                    # FIX #1: Pre-flight quota check - skip API calls if all keys exhausted
                    global _per_key_quota_used
                    has_available_quota = any(
                        _per_key_quota_used.get(j, 0) < self._daily_quota_limit
                        for j in range(len(self.api_keys))
                    )

                    if not has_available_quota:
                        if self.console:
                            self.console.print(
                                "   - [red]⚠ All API keys quota exhausted - reset at midnight PT[/red]"
                            )
                        logger.info("All API keys exhausted, skipping yt-api and using yt-dlp fallback")
                        break  # Exit the while loop, let yt-dlp handle it
                    # END FIX #1
                    response = requests.get(playlist_url, params=params, timeout=10)
                    api_elapsed = time.time() - api_start
                    logger.info(
                        "API response received: status=%s, time=%ss",
                        response.status_code,
                        api_elapsed,
                    )
                    self._quota_used += 1
                    self._add_quota_and_persist(1)
                    if response.status_code == 403:
                        try:
                            error_data = response.json()
                            error_reason = (
                                error_data.get("error", {})
                                .get("errors", [{}])[0]
                                .get("reason", "unknown")
                            )
                            logger.info("403 reason: %s", error_reason)
                        except (ValueError, KeyError, IndexError, TypeError):
                            error_reason = "unknown"
                            logger.info("403 response: %s", response.text[:200])
                        logger.info("Got 403, rotating key and retrying...")
                        self._rotate_key()
                        params["key"] = self.current_key
                        response = requests.get(playlist_url, params=params, timeout=10)
                        logger.info("Retry response: status=%s", response.status_code)
                        self._add_quota_and_persist(1)
                        if response.status_code == 403:
                            try:
                                error_data = response.json()
                                retry_reason = (
                                    error_data.get("error", {})
                                    .get("errors", [{}])[0]
                                    .get("reason", "unknown")
                                )
                                if self.console:
                                    if retry_reason == "quotaExceeded":
                                        self.console.print(
                                            "   - [red]⚠ All API keys quota exhausted - reset at midnight PT[/red]"
                                        )
                                    else:
                                        self.console.print(
                                            f"   - [red]Retry also failed: {retry_reason}[/red]"
                                        )
                            except (ValueError, KeyError, IndexError, TypeError):
                                pass
                    response.raise_for_status()
                    data = response.json()
                    if estimated_total == 0:
                        page_info = data.get("pageInfo", {})
                        estimated_total = page_info.get("totalResults", 0)
                    items_count = len(data.get("items", []))
                    total_fetched += items_count
                    # DEBUG: Log progress state to verify RCA fix
                    logger.debug(f"[PROGRESS CHECK API] console={self.console is not None}, show_progress={self.show_progress}, progress_task={progress_task is not None}, _parent_progress={self._parent_progress is not None}")
                    if self.console and self.show_progress and progress_task is None and not self._parent_progress:
                        logger.debug("[PROGRESS PATH] → STDOUT WRITE (API block)")
                        # Rate-limited progress update (max 4Hz to prevent flashing)
                        _progress_call_count += 1
                        current_progress = (total_fetched, estimated_total)
                        logger.debug(f"[{_progress_call_count}] Progress API block: current={current_progress}, last={_last_printed_progress}, will_print={current_progress != _last_printed_progress}")
                        if current_progress != _last_printed_progress:
                            current_time = time.time()
                            time_since_last_update = current_time - _last_progress_time
                            if time_since_last_update >= 1.0:  # 1Hz = 1000ms intervals (reduced from 4Hz to prevent flickering)
                                pct = int(total_fetched / estimated_total * 100) if estimated_total > 0 else 0
                                bar_len = 20
                                filled = int(bar_len * total_fetched / estimated_total) if estimated_total > 0 else 0
                                bar = "█" * filled + "━" * (bar_len - filled)
                                # Write directly to stdout for true in-place update (Rich Console might buffer)
                                import sys
                                sys.stdout.write(f"\r   ⎿ yt-api: {bar} {pct:>3}% {total_fetched:,}/{estimated_total:,}")
                                sys.stdout.flush()
                                _last_printed_progress = current_progress
                                _last_progress_time = current_time
                    # FIX #2: Clear progress bar before error messages
                    # This prevents "0% 0ERROR" concatenation bug
                    if self.console and self.show_progress and progress_task is None and not self._parent_progress:
                        import sys
                        sys.stdout.write(chr(10))  # Clear the progress bar line (newline char)
                        sys.stdout.flush()
                    # END FIX #2

                except requests.RequestException as e:
                    logger.exception("Failed to fetch playlist items: %s", e)
                    break
                except Exception as e:
                    logger.exception("Unexpected error fetching playlist items: %s", e)
                    break
                video_ids = []
                for item in data.get("items", []):
                    resource_id = item.get("contentDetails", {}).get("videoId")
                    if resource_id:
                        video_ids.append(resource_id)
                if not video_ids:
                    break
                metadata_map = self._fetch_video_metadata_batch(video_ids)
                for item in data.get("items", []):
                    video_id = item.get("contentDetails", {}).get("videoId")
                    if not video_id:
                        continue
                    snippet = item.get("snippet", {})
                    metadata = metadata_map.get(video_id, {})
                    published_at = snippet.get("publishedAt", "")
                    videos.append(
                        {
                            "video_id": video_id,
                            "title": snippet.get("title", ""),
                            "url": f"https://www.youtube.com/watch?v={video_id}",
                            "date": published_at,
                            "duration": metadata.get("duration", 0),
                            "thumbnail_url": metadata.get("thumbnail_url", ""),
                            "view_count": metadata.get("view_count", 0),
                            "is_short": metadata.get("is_short", 0),
                                                }
                    )
                # Progress updates: parent-owned progress pattern (use actual video count)
                if progress_task is not None and self._coordinator is not None:
                    # Thread-safe coordinator mode
                    logger.debug(f"[PROGRESS PATH] → COORDINATOR UPDATE (video count={len(videos)})")
                    if self._should_update_progress():
                        self._update_progress_via_coordinator(len(videos), estimated_total)
                elif progress_task is not None and self._parent_progress is not None:
                    logger.debug(f"[PROGRESS PATH] → RICH PROGRESS UPDATE (video count={len(videos)})")
                    # Rate-limited progress update (2Hz = 0.5s intervals to prevent flickering)
                    # NOTE: Rich Progress refresh_per_second controls rendering, but we still need
                    # to throttle update frequency to avoid excessive calls when fetching many pages
                    if self._should_update_progress():
                        self._update_progress_via_rich(progress_task, len(videos), estimated_total)
                elif self.console and self.show_progress and progress_task is None and not self._parent_progress:
                    logger.debug("[PROGRESS PATH] → STDOUT WRITE (video block)")
                    # Rate-limited progress update (max 4Hz to prevent flashing)
                    _progress_call_count += 1
                    current_progress = (len(videos), estimated_total)
                    logger.debug(f"[{_progress_call_count}] Progress video block: current={current_progress}, last={_last_printed_progress}, will_print={current_progress != _last_printed_progress}")
                    if current_progress != _last_printed_progress:
                        current_time = time.time()
                        time_since_last_update = current_time - _last_progress_time
                        if time_since_last_update >= 1.0:  # 1Hz = 1000ms intervals (reduced from 4Hz to prevent flickering)
                            pct = int(len(videos) / estimated_total * 100) if estimated_total > 0 else 0
                            bar_len = 20
                            filled = int(bar_len * len(videos) / estimated_total) if estimated_total > 0 else 0
                            bar = "█" * filled + "━" * (bar_len - filled)
                            # Write directly to stdout for true in-place update (Rich Console might buffer)
                            sys.stdout.write(f"\r   ⎿ yt-api: {bar} {pct:>3}% {len(videos):,}/{estimated_total:,}")
                            sys.stdout.flush()
                            _last_printed_progress = current_progress
                            _last_progress_time = current_time
                if progress_callback:
                    progress_callback(len(videos))
                next_page_token = data.get("nextPageToken")
                if not next_page_token:
                    break
        finally:
            # Print newline to finish in-place progress bar
            if self.console and self.show_progress and self._parent_progress is None:
                self.console.print("")  # newline after progress bar
        # Final status message (only for legacy progress mode, NOT parent-owned pattern)
        # When parent progress or coordinator is active, let the parent manage display - no extra print
        if self.console and self._parent_progress is None and self._coordinator is None:
            self.console.print(f"   ⎿ yt-api: {len(videos):,} objects fetched")
        logger.info(
            "Fetched %s videos from channel %s via yt-api", len(videos), channel_id
        )
        _flush_quota_to_db()
        return videos

    def get_channel_stats(self, channel_id: str) -> dict:
        """Get channel statistics from YouTube API.

        Args:
            channel_id: YouTube channel ID

        Returns:
            Dict with total_videos, or None if failed
        """
        channel_url = "https://www.googleapis.com/youtube/v3/channels"
        params = {"part": "statistics", "id": channel_id, "key": self.current_key}
        try:
            response = requests.get(channel_url, params=params, timeout=10)
            self._quota_used += 1
            self._add_quota_and_persist(1)
            if response.status_code == 403:
                self._rotate_key()
                params["key"] = self.current_key
                response = requests.get(channel_url, params=params, timeout=10)
                self._quota_used += 1
                self._add_quota_and_persist(1)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                stats = data["items"][0].get("statistics", {})
                total_videos = int(stats.get("videoCount", 0) or 0)
                return {"total_videos": total_videos, "channel_id": channel_id}
            return None
        except Exception as e:
            logger.debug("Failed to get channel stats for %s: %s", channel_id, e)
            return None

    def backfill_channel(
        self,
        channel_input: str,
        skip_existing: bool = True,
        suppress_progress: bool = False,
    ) -> dict[str, int]:
        """Backfill metadata for all videos in a channel using YouTube API.

        Args:
            channel_input: Channel handle (@name), URL, or channel_id
            skip_existing: If True, skip videos that already have metadata
            suppress_progress: If True, do not show progress bar (avoids conflicts with parent Progress)

        Returns:
            Dict with counts: updated, skipped, errors
        """
        channel_id = get_channel_id_from_input(channel_input)
        if not channel_id:
            self.console.print(f"[red]Could not resolve channel: {channel_input}[/red]")
            return {"updated": 0, "skipped": 0, "errors": 0}
        videos = get_vid_ids_by_channel_id(channel_id)
        if not videos:
            self.console.print(
                f"[yellow]No videos found for channel: {channel_input}[/yellow]"
            )
            return {"updated": 0, "skipped": 0, "errors": 0}
        stats = {"updated": 0, "skipped": 0, "errors": 0}
        conn = get_db_connection(timeout=10.0)
        cur = conn.cursor()
        videos_to_update = []
        for (video_id,) in videos:
            if skip_existing:
                cur.execute(
                    "SELECT duration FROM Videos WHERE video_id = ? AND duration IS NOT NULL",
                    (video_id,),
                )
                if cur.fetchone():
                    stats["skipped"] += 1
                    continue
            videos_to_update.append(video_id)
        conn.close()
        if not videos_to_update:
            self.console.print(f"  All {len(videos)} videos already have metadata")
            return stats
        conn = get_db_connection(timeout=10.0)
        cur = conn.cursor()
        from rich.progress import Progress, SpinnerColumn

        total = len(videos_to_update)
        
        # PARENT-OWNED PROGRESS PATTERN: Check for parent Progress context
        # If parent Progress exists, suppress creating nested Progress context
        parent_progress_exists = self._parent_progress is not None
        
        if suppress_progress or parent_progress_exists:
            for i in range(0, len(videos_to_update), 50):
                batch = videos_to_update[i : i + 50]
                try:
                    metadata_map = self._fetch_video_metadata_batch(batch)
                    for video_id in batch:
                        metadata = metadata_map.get(video_id)
                        if metadata:
                            cur.execute(
                                "UPDATE Videos SET duration = ?, thumbnail_url = ?, view_count = ?, is_short = ? WHERE video_id = ?",
                                (
                                    metadata["duration"],
                                    metadata["thumbnail_url"],
                                    metadata["view_count"],
                                    metadata["is_short"],
                                    video_id,
                                ),
                            )
                            stats["updated"] += 1
                        else:
                            stats["errors"] += 1
                except YouTubeAPIError as e:
                    self.console.print(f"[red]API Error: {e}[/red]")
                    stats["errors"] += len(batch)
        else:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                BarColumn(bar_width=30),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TextColumn("({task.completed}/{task.total})"),
                console=self.console,
                transient=True,
                refresh_per_second=4,
            ) as progress:
                task = progress.add_task(
                    f"yt-api: [metadata] {total} videos", total=total
                )
                for i in range(0, len(videos_to_update), 50):
                    batch = videos_to_update[i : i + 50]
                    try:
                        metadata_map = self._fetch_video_metadata_batch(batch)
                        for video_id in batch:
                            metadata = metadata_map.get(video_id)
                            if metadata:
                                cur.execute(
                                    "UPDATE Videos SET duration = ?, thumbnail_url = ?, view_count = ?, is_short = ? WHERE video_id = ?",
                                    (
                                        metadata["duration"],
                                        metadata["thumbnail_url"],
                                        metadata["view_count"],
                                        metadata["is_short"],
                                        video_id,
                                    ),
                                )
                                stats["updated"] += 1
                            else:
                                stats["errors"] += 1
                        progress.update(task, advance=len(batch))
                    except YouTubeAPIError as e:
                        self.console.print(f"[red]API Error: {e}[/red]")
                        stats["errors"] += len(batch)
                        progress.update(task, advance=len(batch))
        conn.commit()
        conn.close()
        return stats


    def _fetch_channel_metadata(self, channel_id: str) -> dict | None:
        """Fetch channel metadata from YouTube API.
        
        Args:
            channel_id: YouTube channel ID (starts with UC)
            
        Returns:
            Dict with subscriber_count, is_verified (None - cannot reliably determine 
            from YouTube API v3), description, thumbnail_url or None
        """
        channel_url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            "part": "snippet,statistics,status",
            "id": channel_id,
            "key": self.current_key
        }
        try:
            import time
            start = time.time()
            response = requests.get(channel_url, params=params, timeout=10)
            elapsed = time.time() - start
            logger.debug("Channel metadata API call for %s took %ss", channel_id[:20], elapsed)
            self._quota_used += 1
            self._add_quota_and_persist(1)
            if response.status_code == 403:
                self._rotate_key()
                params["key"] = self.current_key
                response = requests.get(channel_url, params=params, timeout=10)
                self._add_quota_and_persist(1)
            response.raise_for_status()
            data = response.json()
            if data.get("items"):
                item = data["items"][0]
                snippet = item.get("snippet", {})
                statistics = item.get("statistics", {})
                status = item.get("status", {})

                # Get thumbnails from snippet
                thumbnails = snippet.get("thumbnails", {})
                thumbnail_url = (
                    thumbnails.get("maxRes", {}).get("url")
                    or thumbnails.get("high", {}).get("url")
                    or thumbnails.get("medium", {}).get("url")
                    or thumbnails.get("default", {}).get("url")
                    or ""
                )

                # YouTube API v3 doesn't provide a reliable is_verified field
                # customUrl is a weak proxy (not all verified channels have it)
                # Setting to None since we cannot reliably determine verification
                return {
                    "subscriber_count": int(statistics.get("subscriberCount", 0) or 0),
                    "is_verified": None,  # Cannot reliably determine from API
                    "description": snippet.get("description", "") or "",
                    "thumbnail_url": thumbnail_url,
                }
            return None
        except Exception as e:
            logger.debug("Failed to fetch channel metadata for %s: %s", channel_id[:20], e)
            return None

    def backfill_channel_metadata(self, channel_id: str) -> dict:
        """Backfill metadata for a single channel using YouTube API.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dict with keys: updated (bool), subscriber_count, is_verified, etc.
        """
        from yt_fts.db.channels import update_channel_metadata

        metadata = self._fetch_channel_metadata(channel_id)
        if not metadata:
            return {"updated": False, "error": "Failed to fetch metadata"}

        from datetime import datetime, timezone
        subscriber_count_last_updated = datetime.now(timezone.utc).isoformat()

        try:
            update_channel_metadata(
                channel_id=channel_id,
                subscriber_count=metadata.get("subscriber_count"),
                is_verified=metadata.get("is_verified"),
                description=metadata.get("description"),
                thumbnail_url=metadata.get("thumbnail_url"),
                subscriber_count_last_updated=subscriber_count_last_updated,
            )
            return {
                "updated": True,
                "subscriber_count": metadata.get("subscriber_count"),
                "is_verified": metadata.get("is_verified"),
            }
        except Exception as e:
            logger.debug("Failed to update channel metadata in DB: %s", e)
            return {"updated": False, "error": str(e)}

    def backfill_missing_channels_metadata(
        self,
        limit: int | None = None,
        progress_callback: callable | None = None,
    ) -> dict[str, int]:
        """Backfill metadata for channels with missing or stale subscriber_count_last_updated.
        
        Checks for:
        - NULL subscriber_count_last_updated (never fetched)
        - OR subscriber_count_last_updated > 30 days ago (stale data)
        
        Args:
            limit: Maximum number of channels to process (None for all)
            progress_callback: Optional callback(current, total) for progress updates
            
        Returns:
            Dict with counts: updated, skipped, errors
        """
        from yt_fts.core.database import get_db_connection

        conn = get_db_connection(timeout=10.0)
        try:
            query = """SELECT channel_id, channel_name 
                FROM Channels 
                WHERE subscriber_count_last_updated IS NULL
                   OR datetime(subscriber_count_last_updated) < datetime('now', '-30 days')
                AND channel_id LIKE 'UC%'
                ORDER BY channel_name"""
            if limit:
                # Use parameterized query for LIMIT to prevent SQL injection
                cursor = conn.execute(query, (limit,))
            else:
                cursor = conn.execute(query)
            channels = cursor.fetchall()
        finally:
            conn.close()

        if not channels:
            if self.console:
                self.console.print("[dim]No channels need metadata backfill[/dim]")
            return {"updated": 0, "skipped": 0, "errors": 0}

        stats = {"updated": 0, "skipped": 0, "errors": 0}
        total = len(channels)

        if self.console:
            self.console.print(f"[cyan]Metadata backfill: {total} channels need metadata[/cyan]")

        for idx, (channel_id, channel_name) in enumerate(channels, 1):
            if progress_callback:
                progress_callback(idx, total)

            quota_info = self.get_global_quota_info()
            if quota_info["remaining"] <= 10:
                if self.console:
                    self.console.print("[red]API quota nearly exhausted, stopping[/red]")
                break

            result = self.backfill_channel_metadata(channel_id)
            if result.get("updated"):
                stats["updated"] += 1
                if self.console and (not self.show_progress):
                    sub_count = result.get("subscriber_count", 0)
                    sub_str = f"{sub_count:,}" if sub_count else "N/A"
                    self.console.print(
                        f"  [{idx}/{total}] {channel_name[:30]:<30} {sub_str} subs"
                    )
            elif "error" in result:
                stats["errors"] += 1

        _flush_quota_to_db()
        return stats

    def backfill_playlist_count_ytdlp(self, channel_id: str) -> dict:
        """Backfill playlist_count for a channel using yt-dlp.
        
        YouTube API does NOT provide playlist_count, so we use yt-dlp
        to scrape the channel playlists page and count playlists.
        
        Args:
            channel_id: YouTube channel ID
            
        Returns:
            Dict with keys: updated (bool), playlist_count (int|None), error (str|None)
        """
        import yt_dlp

        from yt_fts.db.channels import update_channel_metadata

        playlist_url = f"https://www.youtube.com/channel/{channel_id}/playlists"
        playlist_count = None

        try:
            # Import YtdlpSilentLogger to suppress stderr
            from yt_fts.download.output_utils import YtdlpSilentLogger

            with yt_dlp.YoutubeDL({
                "quiet": True,
                "extract_flat": True,
                "ignoreerrors": True,
                "no_warnings": True,
                "extractor_args": {"youtubetab": ["skip=authcheck", "skip=webpage"]},
                "logger": YtdlpSilentLogger(),
            }) as ydl:
                playlist_info = ydl.extract_info(playlist_url, download=False)
                if playlist_info and "entries" in playlist_info:
                    # Count only actual playlists, not channel links
                    playlist_count = len([
                        e for e in playlist_info["entries"]
                        if e and not e.get("url", "").startswith("/channel")
                    ])

            if playlist_count is not None:
                # Only write 0 if we're confident yt-dlp succeeded
                # (has expected fields like title or id). This distinguishes
                # "channel has 0 playlists" from "yt-dlp failed silently".
                if playlist_count == 0 and not (playlist_info and (playlist_info.get("title") or playlist_info.get("id"))):
                    return {
                        "updated": False,
                        "error": "yt-dlp returned incomplete data (0 playlists but no title/id)"
                    }
                # Update database with playlist_count
                update_channel_metadata(
                    channel_id=channel_id,
                    playlist_count=playlist_count,
                )
                logger.info(
                    "Backfilled playlist_count for %s: %d playlists",
                    channel_id[:20],
                    playlist_count
                )
                return {
                    "updated": True,
                    "playlist_count": playlist_count,
                }
            return {
                "updated": False,
                "error": "No playlist entries found"
            }

        except Exception as e:
            logger.debug("Failed to backfill playlist_count for %s: %s", channel_id[:20], e)
            return {
                "updated": False,
                "error": str(e)
            }

def backfill_metadata_api(
    channel_input: str, api_keys: list[str] | None = None, skip_existing: bool = True
) -> dict[str, int]:
    """Convenience function to backfill metadata using YouTube API.

    Args:
        channel_input: Channel handle (@name), URL, or channel_id
        api_keys: List of YouTube API keys (auto-loads from env if None)
        skip_existing: If True, skip videos that already have metadata

    Returns:
        Dict with counts: updated, skipped, errors
    """
    console = Console()
    backfill = YouTubeAPIBackfill(api_keys=api_keys, console=console)
    return backfill.backfill_channel(channel_input, skip_existing=skip_existing)
