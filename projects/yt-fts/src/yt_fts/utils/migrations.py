"""
Database migrations for yt-fts.

Handles schema updates and data migrations between versions.
"""
from __future__ import annotations

import sqlite3

from sqlite_utils import Database

from yt_fts.utils.config import get_db_path


def migrate_to_multi_language() -> None:
    """
    Migration to add multi-language subtitle support.

    Adds:
    - language_code and is_generated columns to Subtitles table
    - SubtitleLanguages table to track available languages per video
    - Indexes for efficient language-based queries
    """
    db = Database(get_db_path())

    # Add language_code column to Subtitles (default 'en' for existing data)
    try:
        db.table("Subtitles").add_column("language_code", str)  # type: ignore[union-attr]
        # Set default value for existing rows
        db.execute("UPDATE Subtitles SET language_code = 'en' WHERE language_code IS NULL")
        print("✓ Added language_code column to Subtitles table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ language_code column already exists")
        else:
            print(f"Warning: Could not add language_code column: {e}")

    # Add is_generated column to Subtitles (default 0 for manual/human subs)
    try:
        db.table("Subtitles").add_column("is_generated", int)  # type: ignore[union-attr]
        # Set default value for existing rows
        db.execute("UPDATE Subtitles SET is_generated = 0 WHERE is_generated IS NULL")
        print("✓ Added is_generated column to Subtitles table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ is_generated column already exists")
        else:
            print(f"Warning: Could not add is_generated column: {e}")

    # Create SubtitleLanguages table
    db.table("SubtitleLanguages").create(  # type: ignore[union-attr]
        {
            "id": int,
            "video_id": str,
            "language_code": str,
            "language_name": str,
            "is_generated": int,
            "download_date": str,
        },
        pk="id",
        not_null={"video_id", "language_code"},
        if_not_exists=True,
        foreign_keys=[("video_id", "Videos")],
    )

    # Create unique constraint on (video_id, language_code)
    try:
        db.execute(
            """
            CREATE UNIQUE INDEX IF NOT EXISTS idx_subtitle_languages_unique
            ON SubtitleLanguages(video_id, language_code)
        """
        )
        print("✓ Created unique index on SubtitleLanguages")
    except Exception as e:
        print(f"Warning: Could not create unique index: {e}")

    # Create index for language lookups
    try:
        db.table("Subtitles").create_index(["video_id", "language_code"], if_not_exists=True)  # type: ignore[union-attr]
        print("✓ Created index on (video_id, language_code)")
    except Exception as e:
        print(f"Warning: Could not create language index: {e}")

    print("\n✓ Multi-language migration complete!")




def migrate_to_api_total_tracking() -> None:
    """
    Migration to add API total video count tracking for completeness detection.

    Adds:
    - api_total_video_count column to Channels table (stores YouTube API video count)
    - api_total_last_checked column to Channels table (timestamp of last API check)

    This enables quota-free completeness checks by storing the baseline from first API scan.
    """

    db = Database(get_db_path())

    # Add api_total_video_count column to Channels
    try:
        db.table("Channels").add_column("api_total_video_count", int)  # type: ignore[union-attr]
        print("✓ Added api_total_video_count column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ api_total_video_count column already exists")
        else:
            print(f"Warning: Could not add api_total_video_count column: {e}")

    # Add api_total_last_checked column to Channels
    try:
        db.table("Channels").add_column("api_total_last_checked", str)  # type: ignore[union-attr]
        print("✓ Added api_total_last_checked column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ api_total_last_checked column already exists")
        else:
            print(f"Warning: Could not add api_total_last_checked column: {e}")

    # Create index for quick lookup
    try:
        db.table("Channels").create_index(["api_total_video_count"], if_not_exists=True)  # type: ignore[union-attr]
        print("✓ Created index on api_total_video_count")
    except Exception as e:
        print(f"Warning: Could not create index: {e}")

    print("\n✓ API total tracking migration complete!")



def migrate_to_source_type_tracking() -> None:
    """
    Migration to add source type tracking for subtitles.

    Adds:
    - source_type column to Subtitles table (tracks transcript source)

    This enables distinguishing between official YouTube captions,
    Whisper-generated transcripts, and other sources.
    """
    db = Database(get_db_path())

    # Add source_type column to Subtitles (default 'official' for existing data)
    try:
        db.table("Subtitles").add_column("source_type", str)  # type: ignore[union-attr]
        # Set default value for existing rows
        db.execute(
            "UPDATE Subtitles SET source_type = 'official' WHERE source_type IS NULL"
        )
        print("✓ Added source_type column to Subtitles table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ source_type column already exists")
        else:
            print(f"Warning: Could not add source_type column: {e}")

    # Create index for source type filtering
    try:
        db.table("Subtitles").create_index(["source_type"], if_not_exists=True)  # type: ignore[union-attr]
        print("✓ Created index on source_type")
    except Exception as e:
        print(f"Warning: Could not create source_type index: {e}")

    print("✓ Source type tracking migration complete!")


def migrate_to_channel_metadata() -> None:
    """
    Migration to add comprehensive channel metadata from yt-dlp and yt-api.

    Adds:
    - subscriber_count column to Channels table (stores follower/subscriber count)
    - is_verified column to Channels table (stores verification status)
    - description column to Channels table (stores channel description)
    - thumbnail_url column to Channels table (stores channel thumbnail URL)
    - subscriber_count_last_updated column to Channels table (timestamp of last subscriber count update)

    This enables storing rich channel metadata for display and tracking subscriber growth over time.
    """

    db = Database(get_db_path())

    # Add subscriber_count column to Channels
    try:
        db.table("Channels").add_column("subscriber_count", int)  # type: ignore[union-attr]
        print("✓ Added subscriber_count column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ subscriber_count column already exists")
        else:
            print(f"Warning: Could not add subscriber_count column: {e}")

    # Add is_verified column to Channels
    try:
        db.table("Channels").add_column("is_verified", int)  # type: ignore[union-attr]
        print("✓ Added is_verified column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ is_verified column already exists")
        else:
            print(f"Warning: Could not add is_verified column: {e}")

    # Add description column to Channels
    try:
        db.table("Channels").add_column("description", str)  # type: ignore[union-attr]
        print("✓ Added description column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ description column already exists")
        else:
            print(f"Warning: Could not add description column: {e}")

    # Add thumbnail_url column to Channels
    try:
        db.table("Channels").add_column("thumbnail_url", str)  # type: ignore[union-attr]
        print("✓ Added thumbnail_url column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ thumbnail_url column already exists")
        else:
            print(f"Warning: Could not add thumbnail_url column: {e}")

    # Add subscriber_count_last_updated column to Channels
    try:
        db.table("Channels").add_column("subscriber_count_last_updated", str)  # type: ignore[union-attr]
        print("✓ Added subscriber_count_last_updated column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ subscriber_count_last_updated column already exists")
        else:
            print(f"Warning: Could not add subscriber_count_last_updated column: {e}")

    print("")
    print("✓ Channel metadata migration complete!")



def check_migration_status() -> dict[str, bool]:
    """
    Check which migrations have been applied.

    Returns:
        Dictionary with migration names as keys and boolean status
    """
    db = Database(get_db_path())
    status = {}

    # Check if language_code column exists
    try:
        columns = db["Subtitles"].columns_dict
        status["multi_language"] = "language_code" in columns
    except (sqlite3.Error, ValueError, TypeError):
        status["multi_language"] = False

    # Check if api_total_video_count column exists
    try:
        columns = db["Channels"].columns_dict
        status["api_total_tracking"] = "api_total_video_count" in columns
    except (sqlite3.Error, ValueError, TypeError):
        status["api_total_tracking"] = False

    # Check if source_type column exists
    try:
        columns = db["Subtitles"].columns_dict
        status["source_type_tracking"] = "source_type" in columns
    except (sqlite3.Error, ValueError, TypeError):
        status["source_type_tracking"] = False

    # Check if subscriber_count column exists (channel metadata migration)
    try:
        columns = db["Channels"].columns_dict
        status["channel_metadata"] = "subscriber_count" in columns
    except (sqlite3.Error, ValueError, TypeError):
        status["channel_metadata"] = False

    # Check if playlist_count column exists
    try:
        columns = db["Channels"].columns_dict
        status["playlist_count"] = "playlist_count" in columns
    except (sqlite3.Error, ValueError, TypeError):
        status["playlist_count"] = False

    return status


def ensure_migrations() -> None:
    """
    Ensure all required migrations are applied.

    Call this on application startup to guarantee database schema is up to date.
    """
    status = check_migration_status()

    if not status.get("multi_language", False):
        print("Applying multi-language migration...")
        migrate_to_multi_language()

    if not status.get("api_total_tracking", False):
        print("Applying API total tracking migration...")
        migrate_to_api_total_tracking()

    if not status.get("source_type_tracking", False):
        print("Applying source type tracking migration...")
        migrate_to_source_type_tracking()

    if not status.get("channel_metadata", False):
        print("Applying channel metadata migration...")
        migrate_to_channel_metadata()

    if not status.get("playlist_count", False):
        print("Applying playlist count migration...")
        migrate_to_playlist_count()

    if (
        status.get("multi_language", False)
        and status.get("api_total_tracking", False)
        and status.get("source_type_tracking", False)
        and status.get("channel_metadata", False)
        and status.get("playlist_count", False)
    ):
        print("✓ All migrations up to date")

def migrate_to_playlist_count() -> None:
    """
    Migration to add playlist count tracking for channels.

    Adds:
    - playlist_count column to Channels table (stores number of public playlists)

    This enables displaying how many playlists a channel has.
    """

    db = Database(get_db_path())

    # Add playlist_count column to Channels
    try:
        db.table("Channels").add_column("playlist_count", int)  # type: ignore[union-attr]
        print("✓ Added playlist_count column to Channels table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("✓ playlist_count column already exists")
        else:
            print(f"Warning: Could not add playlist_count column: {e}")

    print("\n✓ Playlist count migration complete!")


