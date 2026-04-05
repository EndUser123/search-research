"""
Skipped/Failed channel tracking module.

This module provides functions to track channels that have permanently failed
(e.g., 404, deleted, empty) so we can skip them in future runs.
"""

import logging
from datetime import datetime, timezone

from yt_fts.db.infra import get_db_connection

logger = logging.getLogger(__name__)


# Skip reasons
SKIPPED_REASON_DELETED = "channel_deleted_or_404"
SKIPPED_REASON_EMPTY = "channel_empty_no_videos"
SKIPPED_REASON_PRIVATE = "channel_private"


def is_channel_skipped(channel_url: str) -> tuple[bool, str | None]:
    """
    Check if a channel is in the skipped list.

    Args:
        channel_url: The channel URL to check

    Returns:
        Tuple of (is_skipped: bool, skip_reason: str | None)
    """
    with get_db_connection() as conn:
        row = conn.execute(
            "SELECT skip_reason FROM SkippedChannels WHERE channel_url = ?",
            (channel_url,),
        ).fetchone()
        if row:
            return True, row[0]
    return False, None


def add_skipped_channel(
    channel_url: str,
    skip_reason: str,
    fail_count: int = 1,
) -> None:
    """
    Add or update a channel in the skipped list.

    Args:
        channel_url: The channel URL to skip
        skip_reason: Reason for skipping (e.g., "channel_deleted_or_404")
        fail_count: Number of times this channel has failed
    """
    from yt_fts.db.infra import retry_on_locked

    @retry_on_locked()
    def _add_skipped():
        with get_db_connection() as conn:
            timestamp = datetime.now(timezone.utc).isoformat()
            conn.execute(
                """
                INSERT INTO SkippedChannels (channel_url, skip_reason, fail_count, last_attempt)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(channel_url) DO UPDATE SET
                    skip_reason = excluded.skip_reason,
                    fail_count = fail_count + excluded.fail_count,
                    last_attempt = excluded.last_attempt
                """,
                (channel_url, skip_reason, fail_count, timestamp),
            )
            conn.commit()

    try:
        _add_skipped()
        logger.debug(f"Added skipped channel: {channel_url} - {skip_reason}")
    except Exception as e:
        logger.warning(f"Failed to add skipped channel {channel_url}: {e}")


def remove_skipped_channel(channel_url: str) -> bool:
    """
    Remove a channel from the skipped list (e.g., if it was re-added).

    Args:
        channel_url: The channel URL to remove

    Returns:
        True if channel was removed, False if it wasn't in the list
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "DELETE FROM SkippedChannels WHERE channel_url = ?",
            (channel_url,),
        )
        conn.commit()
        return cursor.rowcount > 0


def get_skipped_channels() -> list[dict]:
    """
    Get all skipped channels.

    Returns:
        List of dicts with keys: channel_url, skip_reason, fail_count, last_attempt
    """
    with get_db_connection() as conn:
        rows = conn.execute(
            """
            SELECT channel_url, skip_reason, fail_count, last_attempt
            FROM SkippedChannels
            ORDER BY last_attempt DESC
            """
        ).fetchall()
        return [
            {
                "channel_url": row[0],
                "skip_reason": row[1],
                "fail_count": row[2],
                "last_attempt": row[3],
            }
            for row in rows
        ]


def clear_skipped_channels() -> int:
    """
    Clear all skipped channels (e.g., for retry).

    Returns:
        Number of channels removed
    """
    with get_db_connection() as conn:
        cursor = conn.execute("DELETE FROM SkippedChannels")
        conn.commit()
        return cursor.rowcount


def should_skip_permanent(error_msg: str) -> tuple[bool, str | None]:
    """
    Determine if an error indicates a permanent failure that should be tracked.

    Args:
        error_msg: The error message to evaluate

    Returns:
        Tuple of (should_skip: bool, skip_reason: str | None)
    """
    if not error_msg:
        return False, None

    error_lower = error_msg.lower()

    # Permanent failure patterns
    if "http error 404" in error_lower or "404 not found" in error_lower:
        return True, SKIPPED_REASON_DELETED
    if "no videos found for channel" in error_lower:
        return True, SKIPPED_REASON_EMPTY
    if "channel is private" in error_lower or "private channel" in error_lower:
        return True, SKIPPED_REASON_PRIVATE

    return False, None
