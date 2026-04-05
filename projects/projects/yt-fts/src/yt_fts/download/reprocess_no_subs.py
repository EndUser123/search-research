"""
Re-process existing [No Subtitles] videos for Whisper transcription.

This module provides functionality to:
1. Query for videos marked [No Subtitles] in a channel
2. Queue them for transcription
3. Remove old [No Subtitles] entries after queuing

This allows existing videos that previously had no captions to be
automatically transcribed when their channel is re-scanned.
"""

import logging
import sqlite3
import time
from typing import TYPE_CHECKING

from yt_fts.core.database import get_db_connection
from yt_fts.db.infra import _db_write_lock

if TYPE_CHECKING:
    from collections.abc import Callable

logger = logging.getLogger(__name__)

def _retry_on_locked(func, max_retries=3, delay=0.1):
    """Retry function on database lock errors."""
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            if "database is locked" in str(e) and attempt < max_retries - 1:
                time.sleep(delay * (2 ** attempt))
                continue
            raise
    return None


def get_no_subs_videos_for_channel(
    channel_id: str,
    limit: int | None = None,
) -> list[str]:
    """
    Get video IDs marked [No Subtitles] for a specific channel.

    Args:
        channel_id: The channel ID to query
        limit: Maximum number of videos to return (None for unlimited)

    Returns:
        List of video IDs that need transcription

    Examples:
        >>> get_no_subs_videos_for_channel("UC123")
        ['vid1', 'vid2', 'vid3']
        >>> get_no_subs_videos_for_channel("UC123", limit=2)
        ['vid1', 'vid2']
    """
    def _query_with_retry():
        db = get_db_connection()
        try:
            cursor = db.cursor()

            query = """
                SELECT video_id
                FROM Videos
                WHERE channel_id = ?
                  AND video_title = '[No Subtitles]'
                ORDER BY video_id
            """

            if limit:
                query += f" LIMIT {limit}"

            cursor.execute(query, (channel_id,))
            rows = cursor.fetchall()

            return [row[0] for row in rows]
        finally:
            db.close()

    return _retry_on_locked(_query_with_retry)


def queue_videos_for_transcription(
    video_ids: list[str],
    channel_id: str,
    transcribe_fn: "Callable[[str], None]" | None = None,
) -> int:
    """
    Queue videos for transcription and clean up old [No Subtitles] entries.

    Uses _db_write_lock to serialize with other database write operations.

    Args:
        video_ids: List of video IDs to transcribe
        channel_id: Associated channel ID
        transcribe_fn: Optional function to call for each video (defaults to internal)

    Returns:
        Number of videos queued

    Examples:
        >>> queue_videos_for_transcription(['vid1', 'vid2'], 'UC123')
        2
    """
    if not video_ids:
        return 0

    queued_count = 0

    def _do_delete():
        nonlocal queued_count
        with _db_write_lock:
            db = get_db_connection(timeout=30.0)  # Longer timeout for concurrent access
            try:
                cursor = db.cursor()

                for video_id in video_ids:
                    # Delete the old [No Subtitles] entry
                    cursor.execute(
                        "DELETE FROM Videos WHERE video_id = ? AND video_title = '[No Subtitles]'",
                        (video_id,)
                    )
                    queued_count += 1

                db.commit()
            except Exception as e:
                db.rollback()
                logger.exception(f"Failed to queue videos for transcription: {e}")
                raise
            finally:
                db.close()

    # Retry with backoff if database is locked
    max_retries = 5
    retry_delay = 0.5
    for attempt in range(max_retries):
        try:
            _do_delete()
            break
        except sqlite3.OperationalError as e:
            if "database is locked" in str(e).lower() and attempt < max_retries - 1:
                logger.warning(f"Database locked during DELETE (attempt {attempt + 1}/{max_retries}), retrying...")
                time.sleep(retry_delay)
                retry_delay *= 2
            else:
                raise

    # Call transcription function OUTSIDE the database lock (long-running operation)
    if transcribe_fn:
        for video_id in video_ids:
            try:
                transcribe_fn(video_id)
            except Exception as e:
                logger.debug(f"Transcription failed for {video_id}: {e}")

    return queued_count


def get_channels_needing_reprocess(
    max_per_channel: int = 5,
    min_no_subs_count: int = 1,
) -> list[dict]:
    """
    Get channels that have [No Subtitles] videos needing re-processing.

    Args:
        max_per_channel: Maximum videos to return per channel
        min_no_subs_count: Minimum [No Subtitles] videos required to include channel

    Returns:
        List of dicts with channel_id and video_ids

    Examples:
        >>> get_channels_needing_reprocess(max_per_channel=3)
        [{'channel_id': 'UC123', 'video_ids': ['vid1', 'vid2', 'vid3']}]
    """
    db = get_db_connection()
    try:
        cursor = db.cursor()

        # Find channels with [No Subtitles] videos
        query = """
            SELECT channel_id, COUNT(*) as no_subs_count
            FROM Videos
            WHERE video_title = '[No Subtitles]'
            GROUP BY channel_id
            HAVING no_subs_count >= ?
            ORDER BY no_subs_count DESC
        """

        cursor.execute(query, (min_no_subs_count,))
        channels = cursor.fetchall()

        results = []
        for (channel_id, count) in channels:
            # Get video IDs for this channel
            video_ids = get_no_subs_videos_for_channel(
                channel_id,
                limit=max_per_channel
            )
            if video_ids:
                results.append({
                    "channel_id": channel_id,
                    "video_ids": video_ids,
                    "total_no_subs": count
                })

        return results

    finally:
        db.close()


def reprocess_channel_no_subs(
    channel_id: str,
    transcribe_fn: "Callable[[str], None]",
    limit: int | None = None,
) -> int:
    """
    Re-process all [No Subtitles] videos for a channel.

    Args:
        channel_id: The channel ID to re-process
        transcribe_fn: Function to call for transcription (video_id -> None)
        limit: Maximum number of videos to re-process (None for all)

    Returns:
        Number of videos queued for transcription

    Examples:
        >>> reprocess_channel_no_subs("UC123", transcribe_fn, limit=5)
        5
    """
    video_ids = get_no_subs_videos_for_channel(channel_id, limit=limit)
    return queue_videos_for_transcription(video_ids, channel_id, transcribe_fn)
