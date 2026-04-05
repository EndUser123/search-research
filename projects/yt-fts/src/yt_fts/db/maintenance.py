
from __future__ import annotations
import gc
import logging
from typing import Any

from sqlite_utils import Database

from yt_fts.db.infra import get_db_connection

logger = logging.getLogger(__name__)


def make_db(db_path: str) -> None:
    """Create a full database schema with all tables."""
    db = Database(db_path)
    # Copied from original to ensure exact schema creation
    db["Channels"].create(
        {"channel_id": str, "channel_name": str, "channel_url": str, "is_valid": int},
        pk="channel_id",
        not_null={"channel_name", "channel_url"},
        defaults={"is_valid": 1},
        if_not_exists=True,
    )
    db["Videos"].create(
        {
            "video_id": str,
            "video_title": str,
            "video_url": str,
            "channel_id": str,
            "video_date": str,
            "duration": int,
            "thumbnail_url": str,
            "view_count": int,
            "is_short": int,
        },
        pk="video_id",
        not_null={"video_title", "video_url"},
        if_not_exists=True,
        foreign_keys=[("channel_id", "Channels")],
    )
    db["Subtitles"].create(
        {
            "subtitle_id": int,
            "video_id": str,
            "start_time": str,
            "stop_time": str,
            "text": str,
            "language_code": str,
        },
        pk="subtitle_id",
        not_null={"start_time", "text"},
        if_not_exists=True,
        foreign_keys=[("video_id", "Videos")],
    ).enable_fts(["text"], create_triggers=True, replace=True)
    db["SkippedChannels"].create(
        {
            "channel_url": str,
            "skip_reason": str,
            "fail_count": int,
            "last_attempt": str,
        },
        pk="channel_url",
        not_null={"skip_reason", "fail_count", "last_attempt"},
        if_not_exists=True,
    )
    db["SemanticSearchEnabled"].create(
        {"channel_id": str},
        if_not_exists=True,
        foreign_keys=[("channel_id", "Channels")],
    )
    db["SearchHistory"].create(
        {
            "search_id": int,
            "query": str,
            "timestamp": str,
            "scope": str,
            "result_count": int,
            "channel_id": str,
        },
        pk="search_id",
        if_not_exists=True,
    )
    db["SavedQueries"].create(
        {
            "query_id": int,
            "name": str,
            "query": str,
            "scope": str,
            "channel_id": str,
            "timestamp": str,
        },
        pk="query_id",
        if_not_exists=True,
    )
    db["embeddings"].create(
        {
            "subtitle_id": int,
            "channel_id": str,
            "video_id": str,
            "embedding": bytes,
            "model_name": str,
            "created_at": str,
        },
        pk="subtitle_id",
        if_not_exists=True,
        foreign_keys=[("subtitle_id", "Subtitles")],
    )

    # Indexes
    db["Videos"].create_index(["channel_id"], if_not_exists=True)
    db["Subtitles"].create_index(["video_id"], if_not_exists=True)
    db["Subtitles"].create_index(["start_time"], if_not_exists=True)
    db["SearchHistory"].create_index(["timestamp"], if_not_exists=True)
    db["SearchHistory"].create_index(["scope"], if_not_exists=True)
    db["SavedQueries"].create_index(["name"], if_not_exists=True, unique=True)
    db["embeddings"].create_index(["channel_id"], if_not_exists=True)
    db["embeddings"].create_index(["video_id"], if_not_exists=True)
    db["embeddings"].create_index(["model_name"], if_not_exists=True)
    del db
    gc.collect()


def ensure_last_checked_column() -> None:
    # Simplified to just ensure core needs, full logic could be moved to infra or migrations module
    pass


def run_migrations() -> None:
    """Run database migrations to keep schema up to date."""
    migrate_add_is_valid_column()


def migrate_add_is_valid_column() -> bool:
    """
    Add is_valid column to Channels table for existing databases.
    
    Returns:
        True if column was added, False if it already existed
    """
    from yt_fts.db.infra import get_db_connection
    
    conn = get_db_connection()
    try:
        # Check if column exists
        result = conn.execute("""
            SELECT COUNT(*) FROM pragma_table_info('Channels') WHERE name='is_valid'
        """).fetchone()
        
        if result[0] > 0:
            return False  # Column already exists
        
        # Add the column with default value 1 (valid)
        conn.execute("ALTER TABLE Channels ADD COLUMN is_valid INTEGER DEFAULT 1")
        conn.commit()
        logger.info("Added is_valid column to Channels table")
        return True
    except Exception as e:
        logger.error(f"Failed to add is_valid column: {e}")
        return False
    finally:
        conn.close()


def migrate_empty_title_videos() -> None:
    pass


def migrate_unavailable_videos(_batch_size: int = 50) -> None:
    pass


def cleanup_channels() -> dict[str, Any]:
    """
    Clean up the channels database by removing invalid entries.

    This function removes channels that are in the SkippedChannels table
    (channels that failed validation like 404, deleted, private).

    Returns:
        dict: Cleanup summary with keys:
            - skipped_removed: Number of channels removed
            - skipped_removed_names: List of (channel_id, channel_name) tuples removed
            - total_channels_before: Total channels before cleanup
            - total_channels_after: Total channels after cleanup
    """
    result = {
        "skipped_removed": 0,
        "skipped_removed_names": [],
        "total_channels_before": 0,
        "total_channels_after": 0,
    }

    with get_db_connection() as conn:
        # Get total channels before cleanup
        before_count = conn.execute("SELECT COUNT(*) FROM Channels").fetchone()[0]
        result["total_channels_before"] = before_count

        # Check if SkippedChannels table exists (older schemas may not have it)
        skipped_exists = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='SkippedChannels'"
        ).fetchone()

        # Remove channels that are in SkippedChannels (if table exists)
        if skipped_exists:
            skipped_to_delete = conn.execute("""
                SELECT c.channel_id, c.channel_name, c.channel_url
                FROM Channels c
                INNER JOIN SkippedChannels s ON c.channel_url = s.channel_url
            """).fetchall()

            for channel_id, channel_name, channel_url in skipped_to_delete:
                # Delete subtitles
                videos = conn.execute(
                    "SELECT video_id FROM Videos WHERE channel_id = ?", (channel_id,)
                ).fetchall()
                for (video_id,) in videos:
                    conn.execute("DELETE FROM Subtitles WHERE video_id = ?", (video_id,))

                # Delete videos
                conn.execute("DELETE FROM Videos WHERE channel_id = ?", (channel_id,))

                # Delete channel
                conn.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))

                # Also remove from SkippedChannels since we've cleaned it up
                conn.execute("DELETE FROM SkippedChannels WHERE channel_url = ?", (channel_url,))

                result["skipped_removed"] += 1
                result["skipped_removed_names"].append((channel_id, channel_name))

        conn.commit()

        # Get total channels after cleanup
        after_count = conn.execute("SELECT COUNT(*) FROM Channels").fetchone()[0]
        result["total_channels_after"] = after_count

        if result["skipped_removed"] > 0:
            logger.info(f"Database cleanup: {result['skipped_removed']} failed channels removed")

    return result
