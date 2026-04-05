"""
Transcription worker with task queue checkout/check-in pattern.

Provides atomic task reservation for multi-worker transcription processing.
Workers independently checkout videos, process them, and checkin results.
"""
from __future__ import annotations

from datetime import datetime

from yt_fts.db.factory import get_connection


def checkout_video(channel_id: str, worker_id: str | None = None, max_errors: int = 3) -> dict | None:
    """
    Atomically checkout a pending video for processing.

    Uses UPDATE with subquery to atomically find and reserve a video.
    Skips videos that have failed multiple times (error_count >= max_errors).
    Returns None if no pending videos available.

    Args:
        channel_id: Channel to get videos from
        worker_id: Identifier for this worker process
        max_errors: Skip videos with error_count >= this value

    Returns:
        Video dict if checked out, None if no pending videos
    """
    if worker_id is None:
        import os
        worker_id = str(os.getpid())

    now = datetime.now().isoformat()

    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()

        # Atomic checkout: UPDATE with WHERE status='pending'
        # Order by error_count ASC (fewest errors first), then video_id
        # Skip videos with too many errors
        cursor.execute("""
            UPDATE Videos
            SET status = 'processing',
                worker_id = ?,
                processing_started_at = ?
            WHERE rowid = (
                SELECT rowid FROM Videos
                WHERE channel_id = ?
                  AND status = 'pending'
                  AND COALESCE(error_count, 0) < ?
                ORDER BY COALESCE(error_count, 0) ASC, video_id
                LIMIT 1
            )
            RETURNING video_id, channel_id, video_title, status, worker_id, processing_started_at
        """, (worker_id, now, channel_id, max_errors))

        row = cursor.fetchone()
        db.commit()

        if row is None:
            return None

        return {
            "video_id": row[0],
            "channel_id": row[1],
            "video_title": row[2],
            "status": row[3],
            "worker_id": row[4],
            "processing_started_at": row[5],
        }


def checkin_video_done(video_id: str) -> None:
    """
    Mark a video as successfully processed.

    Clears worker_id and processing_started_at as video is complete.

    Args:
        video_id: Video to mark done
    """
    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Videos
            SET status = 'done',
                worker_id = NULL,
                processing_started_at = NULL
            WHERE video_id = ?
        """, (video_id,))
        db.commit()


def checkin_video_failed(video_id: str, error_message: str | None = None) -> None:
    """
    Mark a video as failed and return it to the queue for retry.

    Increments error_count for monitoring. Videos with high error_count
    may be skipped by future workers.

    Args:
        video_id: Video to return to queue
        error_message: Optional error message for logging
    """
    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Videos
            SET status = 'pending',
                worker_id = NULL,
                processing_started_at = NULL,
                error_count = COALESCE(error_count, 0) + 1
            WHERE video_id = ?
        """, (video_id,))
        db.commit()


def get_pending_count(channel_id: str) -> int:
    """
    Get count of pending videos for a channel.

    Args:
        channel_id: Channel to count

    Returns:
        Number of videos with status='pending'
    """
    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()
        cursor.execute("""
            SELECT COUNT(*)
            FROM Videos
            WHERE channel_id = ?
              AND status = 'pending'
        """, (channel_id,))
        return cursor.fetchone()[0]


def recover_stale_checkouts(timeout_minutes: int = 30) -> int:
    """
    Return videos to pending if they've been processing too long.

    Handles worker crashes - videos checked out but never completed
    will timeout back to pending status.

    Args:
        timeout_minutes: Minutes before checkout is considered stale

    Returns:
        Number of videos recovered
    """
    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()
        cursor.execute("""
            UPDATE Videos
            SET status = 'pending',
                worker_id = NULL,
                processing_started_at = NULL
            WHERE status = 'processing'
              AND processing_started_at < datetime('now', '-' || ? || ' minutes')
        """, (timeout_minutes,))
        db.commit()
        return cursor.rowcount


def get_videos_needing_transcription(
    channel_id: str,
    limit: int | None = None,
) -> list[dict]:
    """
    Get videos marked [No Subtitles] for transcription queue.

    This is used to initially populate the task queue from existing
    [No Subtitles] entries.

    Args:
        channel_id: Channel to query
        limit: Maximum videos to return

    Returns:
        List of video dicts
    
    Raises:
        TypeError: If limit is not int or None
        ValueError: If limit is negative
    """
    # Validate limit parameter to prevent SQL injection
    if limit is not None:
        if not isinstance(limit, int):
            raise TypeError("limit must be int or None")
        if limit < 0:
            raise ValueError("limit must be positive")
    
    with get_connection(timeout=30.0) as db:
        cursor = db.cursor()

        query = """
            SELECT video_id, channel_id, video_title
            FROM Videos
            WHERE channel_id = ?
              AND video_title = '[No Subtitles]'
            ORDER BY video_id
        """
        if limit is not None:
            # SQLite doesn't support ? placeholder in LIMIT clause
            # Use explicit formatting after type validation (above)
            query += f" LIMIT {int(limit)}"

        cursor.execute(query, (channel_id,))
        rows = cursor.fetchall()

        return [
            {
                "video_id": row[0],
                "channel_id": row[1],
                "video_title": row[2],
            }
            for row in rows
        ]
