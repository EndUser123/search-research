"""Watch history module for tracking watched videos.

This module provides functionality to:
- Create and maintain the watch_history table
- Add videos to watch history
- Retrieve watch history with filtering options
- Search within watched videos
"""

from __future__ import annotations
import logging
import re
from datetime import datetime, timedelta, timezone

from sqlite_utils import Database

from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path

logger = logging.getLogger(__name__)

def ensure_watch_history_table(db_path: str | None=None) -> None:
    """Ensure the watch_history table and indexes exist.

    Creates the watch_history table if it doesn't exist, along with
    indexes for efficient querying by video_id, channel_name, and watched_at.

    Args:
        db_path: Optional database path. Uses default if not provided.
    """
    if db_path is None:
        db_path = get_db_path()
    db = Database(db_path)
    db["watch_history"].create({"id": int, "video_id": str, "video_title": str, "channel_name": str, "watched_at": str}, pk="id", if_not_exists=True)
    db["watch_history"].create_index(["video_id"], if_not_exists=True)
    db["watch_history"].create_index(["watched_at"], if_not_exists=True)
    db["watch_history"].create_index(["channel_name"], if_not_exists=True)
    db.close()

def add_watch(video_id: str, video_title: str | None=None, channel_name: str | None=None) -> bool:
    """Add or update a video in watch history.

    If the video already exists in watch_history, the watched_at timestamp
    is updated. Otherwise, a new record is created.

    Args:
        video_id: YouTube video ID
        video_title: Optional video title (fetched from Videos table if not provided)
        channel_name: Optional channel name (fetched from database if not provided)

    Returns:
        True if the watch record was added/updated successfully, False otherwise
    """
    db_path = get_db_path()
    ensure_watch_history_table(db_path)
    if video_title is None or channel_name is None:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("\n            SELECT v.video_title, c.channel_name\n            FROM Videos v\n            LEFT JOIN Channels c ON v.channel_id = c.channel_id\n            WHERE v.video_id = ?\n            ", (video_id,))
        result = cur.fetchone()
        conn.close()
        if result is None:
            logger.warning("Video %s not found in database", video_id)
            return False
        if video_title is None:
            video_title = result[0] or ""
        if channel_name is None:
            channel_name = result[1] or ""
    watched_at = datetime.now(timezone.utc).isoformat()
    db = Database(db_path)
    existing = db.execute("SELECT id FROM watch_history WHERE video_id = ?", [video_id]).fetchone()
    if existing:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("\n            UPDATE watch_history\n            SET video_title = ?, channel_name = ?, watched_at = ?\n            WHERE video_id = ?\n            ", (video_title, channel_name, watched_at, video_id))
        conn.commit()
        conn.close()
    else:
        db["watch_history"].insert({"video_id": video_id, "video_title": video_title, "channel_name": channel_name, "watched_at": watched_at})
    db.close()
    return True

def get_watch_history(days: int | None=None, limit: int=50) -> list[dict]:
    """Get watch history with optional filtering.

    Args:
        days: Optional number of days to limit results (e.g., 7 for last week)
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing watch history records
    """
    db_path = get_db_path()
    ensure_watch_history_table(db_path)
    conn = get_db_connection()
    cur = conn.cursor()
    if days is not None:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        query = "\n            SELECT video_id, video_title, channel_name, watched_at\n            FROM watch_history\n            WHERE datetime(watched_at) >= datetime(?)\n            ORDER BY watched_at DESC\n            LIMIT ?\n        "
        cur.execute(query, (cutoff_date, limit))
    else:
        query = "\n            SELECT video_id, video_title, channel_name, watched_at\n            FROM watch_history\n            ORDER BY watched_at DESC\n            LIMIT ?\n        "
        cur.execute(query, (limit,))
    rows = cur.fetchall()
    conn.close()
    return [{"video_id": row[0], "video_title": row[1], "channel_name": row[2], "watched_at": row[3]} for row in rows]

def search_watched(query: str, days: int | None=None, limit: int=20) -> list[dict]:
    """Search within watched videos by title or channel name.

    Performs a case-insensitive search across video_title and channel_name
    columns in the watch_history table.

    Args:
        query: Search query string
        days: Optional number of days to limit search (e.g., 7 for last week)
        limit: Maximum number of records to return

    Returns:
        List of dictionaries containing matching watch history records
    """
    db_path = get_db_path()
    ensure_watch_history_table(db_path)
    conn = get_db_connection()
    cur = conn.cursor()
    search_pattern = f"%{query}%"
    if days is not None:
        cutoff_date = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
        sql_query = "\n            SELECT video_id, video_title, channel_name, watched_at\n            FROM watch_history\n            WHERE (LOWER(video_title) LIKE LOWER(?) OR LOWER(channel_name) LIKE LOWER(?))\n              AND datetime(watched_at) >= datetime(?)\n            ORDER BY watched_at DESC\n            LIMIT ?\n        "
        cur.execute(sql_query, (search_pattern, search_pattern, cutoff_date, limit))
    else:
        sql_query = "\n            SELECT video_id, video_title, channel_name, watched_at\n            FROM watch_history\n            WHERE LOWER(video_title) LIKE LOWER(?) OR LOWER(channel_name) LIKE LOWER(?)\n            ORDER BY watched_at DESC\n            LIMIT ?\n        "
        cur.execute(sql_query, (search_pattern, search_pattern, limit))
    rows = cur.fetchall()
    conn.close()
    return [{"video_id": row[0], "video_title": row[1], "channel_name": row[2], "watched_at": row[3]} for row in rows]

def extract_video_id(input_str: str) -> str | None:
    """Extract video ID from various YouTube URL formats.

    Supports:
    - Direct video IDs (e.g., "abc123" or standard 11-char IDs)
    - Full YouTube URLs (e.g., "https://www.youtube.com/watch?v=abc123")
    - Short URLs (e.g., "https://youtu.be/abc123")
    - Embed URLs (e.g., "https://www.youtube.com/embed/abc123")

    Args:
        input_str: Video ID or YouTube URL

    Returns:
        Extracted video ID or None if found in URL, otherwise returns input_str if it looks like a valid ID
    """
    input_str = input_str.strip()
    patterns = ["(?:v=|/embed/|/v/|/shorts/)([a-zA-Z0-9_-]+)", "youtu\\.be/([a-zA-Z0-9_-]+)"]
    for pattern in patterns:
        match = re.search(pattern, input_str)
        if match:
            return match.group(1)
    if re.match("^[a-zA-Z0-9_-]+$", input_str):
        return input_str
    return None
