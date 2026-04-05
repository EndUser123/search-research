
from __future__ import annotations
import logging
import sqlite3
from typing import Any

from yt_fts.db.infra import BatchCommitManager, get_db_connection

logger = logging.getLogger(__name__)


def get_vid_ids_by_channel_id(channel_id: str) -> list[sqlite3.Row]:
    """
    Get all video IDs for a given channel.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT video_id FROM Videos WHERE channel_id = ?", (channel_id,)
        )
        return cursor.fetchall()


def get_num_vids(channel_id: str) -> int:
    """
    Get the total number of videos for a channel.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT count(*) FROM Videos WHERE channel_id = ?", (channel_id,)
        )
        return cursor.fetchone()[0]


def add_video(
    channel_id: str,
    video_id: str,
    video_title: str,
    video_url: str,
    video_date: str,
    last_checked: str | None = None,
    duration: int | None = None,
    thumbnail_url: str | None = None,
    view_count: int | None = None,
    is_short: int | None = None,
) -> None:
    """
    Add a video to the database.
    """
    with get_db_connection() as conn:
        try:
            conn.execute(
                """
                INSERT INTO Videos (
                    channel_id, video_id, video_title, video_url, video_date,
                    last_checked, duration, thumbnail_url, view_count, is_short
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel_id,
                    video_id,
                    video_title,
                    video_url,
                    video_date,
                    last_checked,
                    duration,
                    thumbnail_url,
                    view_count,
                    is_short,
                ),
            )
            conn.commit()
        except sqlite3.IntegrityError:
            # Optionally update if exists
            pass


def add_videos_bulk(
    channel_id: str,
    videos: list[dict[str, Any]],
    batch_manager: BatchCommitManager | None = None,
) -> int:
    """
    Bulk add videos to the database using BatchCommitManager if provided,
    or a single transaction otherwise.
    """
    added_count = 0

    # Use provided manager or temporary context
    manager_ctx = batch_manager if batch_manager else BatchCommitManager()
    # If using local manager, we need to enter its context manually if not already in one
    # But BatchCommitManager is designed to be used as a context manager.
    # Simplified logic:

    conn = manager_ctx.conn

    for video in videos:
        try:
            conn.execute(
                """
                INSERT INTO Videos (
                    channel_id, video_id, video_title, video_url, video_date,
                    view_count, is_short, thumbnail_url, duration
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    channel_id,
                    video.get("video_id"),
                    video.get("title"),
                    video.get("url"),
                    video.get("date"),
                    video.get("view_count"),
                    video.get("is_short"),
                    video.get("thumbnail_url"),
                    video.get("duration"),
                ),
            )
            manager_ctx.record_insert()
            added_count += 1
        except sqlite3.IntegrityError:
            continue

    if not batch_manager:
        manager_ctx.close()  # Flush and close if we created it locally

    return added_count


def update_video_last_checked(video_id: str, last_checked: str | None = None) -> None:
    """
    Update the last_checked timestamp for a video.
    """
    import datetime

    if last_checked is None:
        last_checked = datetime.datetime.now().isoformat()

    with get_db_connection() as conn:
        conn.execute(
            "UPDATE Videos SET last_checked = ? WHERE video_id = ?",
            (last_checked, video_id),
        )
        conn.commit()


def get_existing_video_ids(video_ids: list[str]) -> set[str]:
    """
    Get set of video IDs that already exist in database.

    Args:
        video_ids: List of video IDs to check

    Returns:
        Set of video IDs that exist in the Videos table
    """
    if not video_ids:
        return set()

    conn = get_db_connection()
    try:
        placeholders = ",".join(["?"] * len(video_ids))
        rows = conn.execute(
            f"SELECT video_id FROM Videos WHERE video_id IN ({placeholders})",
            video_ids,
        ).fetchall()
        return {row[0] for row in rows}
    finally:
        conn.close()


def get_videos_needing_recheck(days: int = 7) -> list[tuple[str, str, str]]:
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT video_id, channel_id, video_title FROM Videos WHERE video_title LIKE '[Unavailable%]' AND (last_checked IS NULL OR datetime(last_checked) < datetime('now', '-' || ? || ' days')) LIMIT 50",
            (str(days),),
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in res]


def get_video_ids_without_subtitles(
    channel_id: str, limit: int | None = None
) -> list[str]:
    """
    Get video IDs for videos in a channel that don't have subtitles yet.

    Excludes videos that are permanently unavailable (private, deleted, etc.).

    Args:
        channel_id: YouTube channel ID
        limit: Optional maximum number of video IDs to return

    Returns:
        List of video IDs that don't have subtitles and should be retried
    """
    with get_db_connection() as conn:
        query = """
            SELECT v.video_id
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id = ?
                AND s.subtitle_id IS NULL
                AND v.video_title NOT LIKE '[Unavailable%'
                AND v.video_title != '[Scheduled]'
            ORDER BY v.video_date DESC
        """
        if limit:
            query += f" LIMIT {limit}"
        res = conn.execute(query, (channel_id,)).fetchall()
        return [row[0] for row in res]


def get_channel_name_from_video_id(video_id: str) -> str | None:
    """
    Get channel name from video ID.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            """
            SELECT c.channel_name
            FROM Channels c
            JOIN Videos v ON c.channel_id = v.channel_id
            WHERE v.video_id = ?
            """,
            (video_id,),
        ).fetchone()
        return res[0] if res else None


def get_channel_info_from_video_id(video_id: str) -> tuple[str | None, str | None]:
    """
    Get channel name and URL from video ID.

    Args:
        video_id: YouTube video ID

    Returns:
        Tuple of (channel_name, channel_url) or (None, None) if not found
    """
    with get_db_connection() as conn:
        res = conn.execute(
            """
            SELECT c.channel_name, c.channel_url
            FROM Channels c
            JOIN Videos v ON c.channel_id = v.channel_id
            WHERE v.video_id = ?
            """,
            (video_id,),
        ).fetchone()
        if res:
            return res[0], res[1]
        return None, None


def get_metadata_from_db(video_id: str) -> dict[str, str]:
    """
    Get video metadata from database.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT * FROM Videos WHERE video_id = ?", (video_id,)
        ).fetchone()
        if res:
            # Convert row to dict and format date
            from yt_fts.utils import get_date

            metadata = dict(res)
            metadata["video_date"] = get_date(metadata["video_date"])
            return metadata
        return {}


def get_subs_by_video_id(video_id: str) -> list[tuple[str, str, str]]:
    """
    Get subtitles for a video.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT start_time, stop_time, text FROM Subtitles WHERE video_id = ?",
            (video_id,),
        ).fetchall()
        return [(r[0], r[1], r[2]) for r in res]


def get_title_from_db(video_id: str) -> str:
    """
    Get video title from database.
    """
    metadata = get_metadata_from_db(video_id)
    return metadata.get("video_title", "")
