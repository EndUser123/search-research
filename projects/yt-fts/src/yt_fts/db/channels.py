
from __future__ import annotations
import asyncio
import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from sqlite_utils import Database
from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path

logger = logging.getLogger(__name__)


def _is_valid_channel_identifier(channel_id: str, channel_url: str) -> bool:
    """
    Validate that channel_id and channel_url are valid YouTube identifiers.

    Rejects:
    - Windows file paths (containing backslashes or drive letters)
    - File names like "channels.txt"
    - Absolute paths starting with / or backslashes
    - Paths with colon separators (Windows drive letters)

    Args:
        channel_id: Channel ID to validate
        channel_url: Channel URL to validate

    Returns:
        True if valid, False if invalid
    """
    backslash = chr(92)  # Backslash character

    # Reject Windows file paths (backslash is clear indicator)
    if backslash in channel_id or backslash in channel_url:
        logger.debug("_is_valid_channel_identifier: rejected (backslash)")
        return False

    # Reject file paths with drive letters (e.g., "C:", "D:")
    if len(channel_id) >= 2 and channel_id[1] == ":" and channel_id[0].isalpha():
        logger.debug("_is_valid_channel_identifier: rejected (drive letter)")
        return False

    # Reject obvious file names
    invalid_filenames = ("channels.txt", "channels.txt/videos", "input.txt", "temp.txt")
    if channel_id.lower().endswith(invalid_filenames) or channel_url.lower().endswith(invalid_filenames):
        logger.debug("_is_valid_channel_identifier: rejected (filename)")
        return False

    # Reject URLs that look like file paths
    if "Users" in channel_url or "Temp" in channel_url or "AppData" in channel_url:
        logger.debug("_is_valid_channel_identifier: rejected (path in URL)")
        return False

    # Valid YouTube channel identifiers should be:
    # - UC... (24 chars)
    # - @handle
    # - For channel_id: can be these or temporary handle_ prefixed during discovery
    if channel_id.startswith("UC") and len(channel_id) >= 20:
        # Valid channel_id - now check URL
        if channel_url.startswith("https://www.youtube.com/") or channel_url.startswith("http://www.youtube.com/"):
            return True
    if channel_id.startswith("@"):
        # Valid handle - now check URL
        if channel_url.startswith("https://www.youtube.com/") or channel_url.startswith("http://www.youtube.com/"):
            return True
    if channel_id.startswith("handle_"):  # Temporary prefix during discovery
        # Valid temporary prefix - now check URL
        if channel_url.startswith("https://www.youtube.com/") or channel_url.startswith("http://www.youtube.com/"):
            return True

    # If we get here, channel_id or channel_url is invalid - reject
    logger.debug("_is_valid_channel_identifier: rejected (invalid channel_id or URL)")
    return False


def get_channels() -> list[sqlite3.Row]:
    """
    Get all channels from the database.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT channel_id, channel_name, channel_url FROM Channels"
        )
        return cursor.fetchall()


def check_if_channel_exists(channel_id: str) -> bool:
    """
    Check if a channel exists in the database.
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_id = ?", (channel_id,)
        )
        return cursor.fetchone() is not None


def add_channel_info(
    channel_id: str,
    channel_name: str,
    channel_url: str,
    *,
    subscriber_count: int | None = None,
    is_verified: bool | None = None,
    description: str | None = None,
    thumbnail_url: str | None = None,
    subscriber_count_last_updated: str | None = None,
    playlist_count: int | None = None,
) -> None:
    """
    Add or update a channel in the database with optional metadata.

    Prevents duplicate channel_url entries by checking if the URL already exists
    (with or without /videos suffix) before inserting. If URL exists with a
    different channel_id, updates the existing row's name/url instead of creating
    a duplicate.

    Args:
        channel_id: Channel ID (UC... or @handle)
        channel_name: Channel name/title
        channel_url: Channel URL
        subscriber_count: Optional subscriber/follower count
        is_verified: Optional verification status
        description: Optional channel description
        thumbnail_url: Optional channel thumbnail URL
        subscriber_count_last_updated: Optional timestamp for subscriber count
        playlist_count: Optional number of public playlists
    """
    # Reject invalid inputs (file paths, etc.)
    if not _is_valid_channel_identifier(channel_id, channel_url):
        logger.warning(
            "add_channel_info: rejected invalid channel_id=%s, channel_url=%s",
            channel_id[:50] if channel_id else None,
            channel_url[:50] if channel_url else None,
        )
        return

    with get_db_connection() as conn:
        # Normalize URL for checking (remove /videos suffix)
        url_without_videos = channel_url.removesuffix("/videos").rstrip("/")

        # Check if this URL (or its /videos variant) already exists with a DIFFERENT channel_id
        existing = conn.execute(
            """
            SELECT channel_id, channel_url FROM Channels
            WHERE (channel_url = ? OR channel_url = ? OR channel_url = ?)
            AND channel_id != ?
            LIMIT 1
            """,
            (
                channel_url,
                url_without_videos,
                f"{url_without_videos}/videos",
                channel_id,
            ),
        ).fetchone()

        if existing:
            # URL exists with different channel_id
            existing_id, existing_url = existing
            
            # If we're inserting @handle and existing is UC, delete the @handle entry
            if channel_id.startswith("@") and existing_id.startswith("UC"):
                conn.execute(
                    "DELETE FROM Channels WHERE channel_id = ?",
                    (channel_id,),
                )
                conn.commit()
                conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                logger.debug(
                    f"add_channel_info URL dedup: Kept UC {existing_id}, deleted @handle {channel_id}"
                )
                return
            
            # Otherwise update existing row
            _update_channel_metadata(
                conn,
                existing_id,
                channel_name,
                channel_url,
                subscriber_count,
                is_verified,
                description,
                thumbnail_url,
                subscriber_count_last_updated,
            )
            logger.debug(
                f"add_channel_info URL dedup: updated existing {existing_id} (skipped insert for {channel_id})"
            )
            return

        # Handle @handle vs UC channel deduplication
        # If we're inserting a UC channel, check if an @handle entry with same name exists
        # If we're inserting an @handle channel, check if a UC entry with same name exists
        # This ensures we keep only one canonical entry (prefer UC over @handle)
        if channel_name:
            if channel_id.startswith("UC"):
                # We're inserting a UC entry - check for duplicate @handle entry
                handle_entry = conn.execute(
                    "SELECT channel_id FROM Channels WHERE channel_name = ? AND channel_id LIKE '@%'",
                    (channel_name,),
                ).fetchone()
                if handle_entry:
                    # Delete the @handle entry since UC is canonical
                    conn.execute(
                        "DELETE FROM Channels WHERE channel_id = ?",
                        (handle_entry[0],),
                    )
                    logger.debug(
                        f"add_channel_info: Removed @{handle_entry[0]} in favor of {channel_id}"
                    )
            elif channel_id.startswith("@"):
                # We're inserting an @handle entry - check if UC entry already exists
                uc_entry = conn.execute(
                    "SELECT channel_id FROM Channels WHERE channel_name = ? AND channel_id LIKE 'UC%'",
                    (channel_name,),
                ).fetchone()
                if uc_entry:
                    # UC entry exists, update it with this URL, skip inserting @handle entry
                    _update_channel_metadata(
                        conn,
                        uc_entry[0],
                        channel_name,
                        channel_url,  # Update to the @handle URL (which may be preferred)
                        subscriber_count,
                        is_verified,
                        description,
                        thumbnail_url,
                        subscriber_count_last_updated,
                        playlist_count,
                    )
                    # Also delete the @handle entry if it exists (it's now redundant)
                    conn.execute(
                        "DELETE FROM Channels WHERE channel_id = ?",
                        (channel_id,),
                    )
                    conn.commit()
                    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
                    logger.debug(
                        f"add_channel_info: Updated UC {uc_entry[0]} and deleted @handle {channel_id}"
                    )
                    return

        # No duplicate URL found, proceed with insert or update by channel_id
        try:
            # Build insert query with metadata
            columns = ["channel_id", "channel_name", "channel_url"]
            values = [channel_id, channel_name, channel_url]
            placeholders = ["?", "?", "?"]

            if subscriber_count is not None:
                columns.append("subscriber_count")
                values.append(subscriber_count)
                placeholders.append("?")
            if is_verified is not None:
                columns.append("is_verified")
                values.append(1 if is_verified else 0)
                placeholders.append("?")
            if description is not None:
                columns.append("description")
                values.append(description)
                placeholders.append("?")
            if thumbnail_url is not None:
                columns.append("thumbnail_url")
                values.append(thumbnail_url)
                placeholders.append("?")
            if subscriber_count_last_updated is not None:
                columns.append("subscriber_count_last_updated")
                values.append(subscriber_count_last_updated)
                placeholders.append("?")
            if playlist_count is not None:
                columns.append("playlist_count")
                values.append(playlist_count)
                placeholders.append("?")

            conn.execute(
                f"INSERT INTO Channels ({', '.join(columns)}) VALUES ({', '.join(placeholders)})",
                values,
            )
            conn.commit()
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            logger.debug(
                f"add_channel_info INSERT committed: {channel_id} -> {channel_name}"
            )
        except sqlite3.IntegrityError:
            # channel_id already exists, update with metadata
            _update_channel_metadata(
                conn,
                channel_id,
                channel_name,
                channel_url,
                subscriber_count,
                is_verified,
                description,
                thumbnail_url,
                subscriber_count_last_updated,
            )


def _update_channel_metadata(
    conn: sqlite3.Connection,
    channel_id: str,
    channel_name: str,
    channel_url: str,
    subscriber_count: int | None = None,
    is_verified: bool | None = None,
    description: str | None = None,
    thumbnail_url: str | None = None,
    subscriber_count_last_updated: str | None = None,
    playlist_count: int | None = None,
) -> None:
    """Helper function to update channel metadata in-place."""
    # Build UPDATE query with only provided metadata
    updates = ["channel_name = ?", "channel_url = ?"]
    values = [channel_name, channel_url]

    if subscriber_count is not None:
        updates.append("subscriber_count = ?")
        values.append(subscriber_count)
    if is_verified is not None:
        updates.append("is_verified = ?")
        values.append(1 if is_verified else 0)
    if description is not None:
        updates.append("description = ?")
        values.append(description)
    if thumbnail_url is not None:
        updates.append("thumbnail_url = ?")
        values.append(thumbnail_url)
    if subscriber_count_last_updated is not None:
        updates.append("subscriber_count_last_updated = ?")
        values.append(subscriber_count_last_updated)
    if playlist_count is not None:
        updates.append("playlist_count = ?")
        values.append(playlist_count)

    values.append(channel_id)  # For WHERE clause

    conn.execute(
        f"UPDATE Channels SET {', '.join(updates)} WHERE channel_id = ?",
        values,
    )
    conn.commit()
    conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
    logger.debug(f"add_channel_info UPDATE committed: {channel_id} -> {channel_name}")


def update_channel_id(old_channel_id: str, new_channel_id: str) -> None:
    """
    Update channel_id (e.g. migrating from @handle to UC ID).
    """
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE Channels SET channel_id = ? WHERE channel_id = ?",
            (new_channel_id, old_channel_id),
        )
        conn.commit()


def get_channel_id_from_input(input_value: str | int) -> str:
    """
    Resolve a channel ID from various input formats.

    Supports:
    - Integer rowid (database row ID)
    - Channel ID (UC...)
    - Channel name (exact match)
    - Channel URL
    - @handle (resolved via unified_channel_processor)

    Args:
        input_value: Channel identifier (rowid, channel_id, name, URL, or @handle)

    Returns:
        str: The resolved channel ID

    Raises:
        ValueError: If input is invalid or channel cannot be resolved
    """
    # Input validation
    if input_value is None:
        raise ValueError("Channel input cannot be None")

    if isinstance(input_value, int):
        if input_value <= 0:
            raise ValueError("Row ID must be a positive integer")
        # Handle integer rowid lookup
        result = get_channel_id_from_rowid(input_value)
        if result is None:
            raise ValueError(f"Row ID {input_value} not found in database")
        return result

    if not isinstance(input_value, str):
        raise ValueError("Channel input must be string or integer")

    # Strip whitespace
    input_value = input_value.strip()

    if not input_value:
        raise ValueError("Channel input cannot be empty")

    # Try database lookup first (fast path)
    # 1. Check if input is a direct channel_id
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_id = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

        # 2. Check if input matches a stored channel_url
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_url = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

        # 3. Check exact name match
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_name = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

    # Not in database - try unified_channel_processor for external resolution
    try:
        from yt_fts.services.unified_channel_processor import create_processor_for_cli

        processor = create_processor_for_cli()
        result = asyncio.run(processor.process_channel_input(input_value))

        if result.success and result.channel_id:
            # Cache to database
            if result.channel_info:
                try:
                    channel_name = result.channel_info.name or input_value
                    channel_url = result.channel_info.url or f"https://www.youtube.com/channel/{result.channel_id}"
                    from yt_fts.db.channels import check_if_channel_exists
                    if not check_if_channel_exists(result.channel_id):
                        add_channel_info(
                            result.channel_id,
                            channel_name,
                            channel_url,
                        )
                except (sqlite3.Error, OSError):
                    # Ignore caching errors - still return the channel_id
                    pass
            return result.channel_id

        # Resolution failed
        error_msg = result.error if result.error else "Unknown error"
        if result.suggestions:
            suggestions = result.suggestions
            nl = chr(10)  # Use chr(10) for newline to avoid escape issues
            suggestions_text = nl + "Suggestions:" + nl + nl.join(f"  - {s}" for s in suggestions)
            raise ValueError(f"Could not resolve channel '{input_value}': {error_msg}{suggestions_text}")
        else:
            raise ValueError(f"Could not resolve channel '{input_value}': {error_msg}")

    except ValueError:
        # Re-raise ValueError with our context
        raise
    except Exception as e:
        # Wrap unexpected errors
        raise ValueError(f"Unexpected error resolving channel '{input_value}': {e}")



def get_channel_name_from_db(channel_id: str) -> str | None:
    """
    Get channel name from database.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_name FROM Channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        if res:
            return res[0]
    return None


def get_channel_list_by_id(channel_id: str) -> list[sqlite3.Row]:
    """
    Get channel info as a list of rows by channel ID.

    Args:
        channel_id: YouTube channel ID

    Returns:
        List containing one row with channel_id, channel_name, channel_url
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT channel_id, channel_name, channel_url FROM Channels WHERE channel_id = ?",
            (channel_id,),
        )
        return cursor.fetchall()


def get_channel_id_by_url_exact(url: str) -> str | None:
    """
    Get channel ID by exact URL match.

    Args:
        url: Exact channel URL to match

    Returns:
        Channel ID if found, None otherwise
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_url = ?", (url,)
        ).fetchone()
        if res:
            return res[0]
    return None


def get_channel_id_by_handle_substring(handle: str) -> str | None:
    """
    Get channel ID by exact handle URL match.
    
    Args:
        handle: The channel handle (with or without @ prefix)
    
    Returns:
        UC channel ID if found, None otherwise
    
    Note:
        This uses exact URL matching only. If the handle is not found,
        the caller should resolve it via yt-dlp or YouTube API.
    """
    # Normalize handle - ensure it starts with @
    if not handle.startswith("@"):
        handle = f"@{handle}"
    
    with get_db_connection() as conn:
        # Try exact handle URL match
        urls_to_try = [
            f"https://www.youtube.com/{handle}",
            f"https://www.youtube.com/{handle}/videos",
            f"http://www.youtube.com/{handle}",
            f"http://www.youtube.com/{handle}/videos",
        ]
        
        for url in urls_to_try:
            res = conn.execute(
                "SELECT channel_id FROM Channels WHERE channel_url = ?",
                (url,)
            ).fetchone()
            if res:
                return res[0]
    
    return None


def add_channel_info_batch(
    channels: list[tuple[str, str, str]], chunk_size: int = 100
) -> int:
    """
    Add multiple channels to the database in batches.
    """

    if not channels:
        return 0
    db = Database(get_db_path())
    existing_urls = set()
    for row in db.execute("SELECT channel_url FROM Channels").fetchall():
        url = row[0]
        existing_urls.add(url)
        existing_urls.add(url.removesuffix("/videos"))

    new_channels = [
        {"channel_id": cid, "channel_name": name, "channel_url": url}
        for cid, name, url in channels
        if url not in existing_urls and url.removesuffix("/videos") not in existing_urls
    ]

    if not new_channels:
        return 0

    total_inserted = 0
    for i in range(0, len(new_channels), chunk_size):
        chunk = new_channels[i : i + chunk_size]
        try:
            db["Channels"].insert_all(chunk)
            total_inserted += len(chunk)
        except (sqlite3.Error, ValueError, TypeError):
            pass
    return total_inserted


def get_channel_api_total(channel_id: str) -> int | None:
    try:
        with get_db_connection() as conn:
            res = conn.execute(
                "SELECT api_total_video_count FROM Channels WHERE channel_id = ?",
                (channel_id,),
            ).fetchone()
            return int(res[0]) if res and res[0] is not None else None
    except (sqlite3.Error, ValueError, TypeError):
        return None


def set_channel_api_total(channel_id: str, api_total: int) -> None:
    try:
        with get_db_connection() as conn:
            timestamp = datetime.now(timezone.utc).isoformat()
            conn.execute(
                "UPDATE Channels SET api_total_video_count = ?, api_total_last_checked = ? WHERE channel_id = ?",
                (api_total, timestamp, channel_id),
            )
            conn.commit()
    except sqlite3.Error:
        pass


def get_channel_id_from_name(channel_name: str) -> str | None:
    """
    Retrieve a channel ID given its name.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_name = ?", (channel_name,)
        ).fetchall()

        if len(res) > 1:
            # Multiple channels with same name - return first one
            return res[0][0]
        if len(res) == 1:
            return res[0][0]
        return None


def get_channel_id_from_rowid(rowid: str | int) -> str | None:
    """
    Retrieve a channel ID given its database row ID.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE ROWID = ?", (rowid,)
        ).fetchone()
        return res[0] if res else None


def delete_channel(channel_id: str) -> None:
    """
    Delete a channel and all its associated data from the database.

    This will delete:
    - The channel entry from Channels table
    - All videos for this channel from Videos table
    - All subtitles for this channel's videos from Subtitles table

    Args:
        channel_id: YouTube channel ID to delete
    """

    with get_db_connection() as conn:
        # Delete subtitles (through cascade or manually)
        # First get all video IDs for this channel
        videos = conn.execute(
            "SELECT video_id FROM Videos WHERE channel_id = ?", (channel_id,)
        ).fetchall()

        # Delete subtitles for each video
        for (video_id,) in videos:
            conn.execute("DELETE FROM Subtitles WHERE video_id = ?", (video_id,))

        # Delete videos
        conn.execute("DELETE FROM Videos WHERE channel_id = ?", (channel_id,))

        # Delete channel
        conn.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))

        conn.commit()


def update_channel_metadata(
    channel_id: str,
    *,
    subscriber_count: int | None = None,
    is_verified: bool | None = None,
    description: str | None = None,
    thumbnail_url: str | None = None,
    subscriber_count_last_updated: str | None = None,
    playlist_count: int | None = None,
) -> None:
    """Update metadata for an existing channel.

    This function updates only the provided metadata fields for a channel
    that already exists in the database.

    Args:
        channel_id: YouTube channel ID to update
        subscriber_count: Optional subscriber/follower count
        is_verified: Optional verification status
        description: Optional channel description
        thumbnail_url: Optional channel thumbnail URL
        subscriber_count_last_updated: Optional timestamp for subscriber count
        playlist_count: Optional number of public playlists
    """
    # First get existing channel info
    with get_db_connection() as conn:
        existing = conn.execute(
            "SELECT channel_name, channel_url FROM Channels WHERE channel_id = ?",
            (channel_id,),
        ).fetchone()

        if not existing:
            logger.warning(
                f"Cannot update metadata for non-existent channel: {channel_id}"
            )
            return

        channel_name, channel_url = existing

    # Use the internal _update_channel_metadata helper
    with get_db_connection() as conn:
        _update_channel_metadata(
            conn,
            channel_id,
            channel_name,
            channel_url,
            subscriber_count,
            is_verified,
            description,
            thumbnail_url,
            subscriber_count_last_updated,
            playlist_count,
        )


# Alias for backward compatibility
get_channel_name_from_id = get_channel_name_from_db


def get_batch_channel_ids_from_urls(urls: list[str]) -> dict[str, str | None]:
    """BATCH resolve channel URLs/handles to channel_ids using the Channels table.

    This is much faster than individual lookups or yt-dlp calls.

    Args:
        urls: List of channel URLs/handles in any format

    Returns:
        Dictionary mapping original URL -> channel_id (or None if not found)
    """
    if not urls:
        return {}

    with get_db_connection() as conn:
        # Normalize URLs for matching (try multiple patterns)
        # For each input URL, create possible matches:
        # 1. Exact URL match
        # 2. URL with /videos suffix
        # 3. URL with /videos suffix removed
        url_patterns = []
        for url in urls:
            url_patterns.append((url, url))
            if not url.endswith("/videos"):
                url_patterns.append((url, url + "/videos"))
            else:
                url_patterns.append((url, url.rstrip("/videos")))

        # Build query with IN clause for all patterns
        placeholders = ",".join(["?" for _ in url_patterns])
        query = f"""
            SELECT channel_url, channel_id
            FROM Channels
            WHERE channel_url IN ({placeholders})
        """

        # Create URL -> channel_id map from results
        url_to_id = {}
        rows = conn.execute(query, [pattern for _, pattern in url_patterns]).fetchall()
        for row in rows:
            url_to_id[row[0]] = row[1]

        # Map original URLs to channel_ids
        result = {}
        for original_url, _ in url_patterns:
            if original_url not in result:
                # Try exact match first
                if original_url in url_to_id:
                    result[original_url] = url_to_id[original_url]
                # Try with /videos suffix
                elif (original_url + "/videos") in url_to_id:
                    result[original_url] = url_to_id[original_url + "/videos"]
                # Try without /videos suffix
                elif original_url.endswith("/videos"):
                    base_url = original_url.rstrip("/videos")
                    result[original_url] = url_to_id.get(base_url)
                else:
                    result[original_url] = None

        return result


def get_fresh_channels(channel_ids: list[str], hours: int = 6) -> set[str]:
    """Get set of channel_ids that were checked within N hours.

    This is a BATCH query that checks all channels at once, much faster
    than individual queries for each channel.

    Args:
        channel_ids: List of channel IDs to check
        hours: Freshness threshold in hours

    Returns:
        Set of channel_ids that are fresh (recently checked)
    """
    if not channel_ids:
        return set()

    with get_db_connection() as conn:
        threshold = datetime.now(timezone.utc) - timedelta(hours=hours)
        threshold_iso = threshold.isoformat()

        # Single query to get all fresh channels
        placeholders = ",".join(["?" for _ in channel_ids])
        query = f"""
            SELECT DISTINCT channel_id
            FROM Videos
            WHERE channel_id IN ({placeholders})
              AND last_checked IS NOT NULL
              AND datetime(last_checked) > datetime(?)
        """

        rows = conn.execute(query, [*channel_ids, threshold_iso]).fetchall()
        return {row[0] for row in rows}


def get_channel_stats(channel_id: str) -> dict[str, int]:
    """
    Get video statistics for a channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Dictionary with video counts: total, with_transcripts, without_transcripts,
        scheduled, members_only, unavailable, shorts, and subscriber_count
    """
    stats = {
        "total": 0,
        "with_transcripts": 0,
        "without_transcripts": 0,
        "scheduled": 0,
        "members_only": 0,
        "unavailable": 0,
        "shorts": 0,
        "subscriber_count": None,
    }

    with get_db_connection() as conn:
        # Get total videos
        res = conn.execute(
            "SELECT COUNT(*) FROM Videos WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        stats["total"] = res[0] if res else 0

        # Get videos with transcripts
        res = conn.execute(
            """
            SELECT COUNT(DISTINCT v.video_id)
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id = ? AND s.subtitle_id IS NOT NULL
            """,
            (channel_id,),
        ).fetchone()
        stats["with_transcripts"] = res[0] if res else 0

        # Get unavailable videos (WITHOUT transcripts)
        res = conn.execute(
            """
            SELECT COUNT(DISTINCT v.video_id)
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id = ?
            AND v.video_title LIKE '[Unavailable%'
            AND s.subtitle_id IS NULL
            """,
            (channel_id,),
        ).fetchone()
        stats["unavailable"] = res[0] if res else 0

        # Get scheduled videos (WITHOUT transcripts)
        res = conn.execute(
            """
            SELECT COUNT(DISTINCT v.video_id)
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id = ?
            AND v.video_title LIKE '[Scheduled%'
            AND s.subtitle_id IS NULL
            """,
            (channel_id,),
        ).fetchone()
        stats["scheduled"] = res[0] if res else 0

        # Get members-only videos (WITHOUT transcripts)
        res = conn.execute(
            """
            SELECT COUNT(DISTINCT v.video_id)
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id = ?
            AND v.video_title LIKE '[Members only%'
            AND s.subtitle_id IS NULL
            """,
            (channel_id,),
        ).fetchone()
        stats["members_only"] = res[0] if res else 0

        # Get shorts (Metadata only, not disjoint)
        res = conn.execute(
            "SELECT COUNT(*) FROM Videos WHERE channel_id = ? AND is_short = 1",
            (channel_id,),
        ).fetchone()
        stats["shorts"] = res[0] if res else 0

        # Calculate pure "no subs" (actionable videos)
        # Total = With_Transcripts + Scheduled(no_sub) + Members(no_sub) + Unavailable(no_sub) + No_Subs(Other)
        stats["without_transcripts"] = max(
            0,
            stats["total"]
            - stats["with_transcripts"]
            - stats["scheduled"]
            - stats["members_only"]
            - stats["unavailable"],
        )

    return stats


def get_batch_channel_stats(channel_ids: list[str]) -> dict[str, dict[str, int]]:
    """
    Get video statistics for multiple channels.

    OPTIMIZED: Uses GROUP BY queries instead of N+1 individual queries.
    For N channels, this executes 6 queries total (one per metric) instead of 6*N.

    Args:
        channel_ids: List of YouTube channel IDs

    Returns:
        Dictionary mapping channel_id to stats dict with keys: total, with_transcripts,
        without_transcripts, scheduled, members_only, unavailable, shorts
    """
    if not channel_ids:
        return {}

    # Initialize all channels with zeros
    stats_by_channel = {
        cid: {
            "total": 0,
            "with_transcripts": 0,
            "without_transcripts": 0,
            "scheduled": 0,
            "members_only": 0,
            "unavailable": 0,
            "shorts": 0,
        }
        for cid in channel_ids
    }

    placeholders = ",".join(["?"] * len(channel_ids))

    with get_db_connection() as conn:
        # Query 1: Total videos per channel
        res = conn.execute(
            f"SELECT channel_id, COUNT(*) as total FROM Videos WHERE channel_id IN ({placeholders}) GROUP BY channel_id",
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["total"] = row[1]

        # Query 2: Videos with transcripts (DISTINCT video_id where subtitle exists)
        res = conn.execute(
            f"""
            SELECT v.channel_id, COUNT(DISTINCT v.video_id) as with_transcripts
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id IN ({placeholders}) AND s.subtitle_id IS NOT NULL
            GROUP BY v.channel_id
            """,
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["with_transcripts"] = row[1]

        # Query 3: Shorts
        res = conn.execute(
            f"SELECT channel_id, COUNT(*) as shorts FROM Videos WHERE channel_id IN ({placeholders}) AND is_short = 1 GROUP BY channel_id",
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["shorts"] = row[1]

        # Query 4: Scheduled videos (title LIKE '[Scheduled%', no subtitles)
        res = conn.execute(
            f"""
            SELECT v.channel_id, COUNT(DISTINCT v.video_id) as scheduled
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id IN ({placeholders})
                AND v.video_title LIKE '[Scheduled%'
                AND s.subtitle_id IS NULL
            GROUP BY v.channel_id
            """,
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["scheduled"] = row[1]

        # Query 5: Members only videos (title LIKE '[Members only%', no subtitles)
        res = conn.execute(
            f"""
            SELECT v.channel_id, COUNT(DISTINCT v.video_id) as members_only
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id IN ({placeholders})
                AND v.video_title LIKE '[Members only%'
                AND s.subtitle_id IS NULL
            GROUP BY v.channel_id
            """,
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["members_only"] = row[1]

        # Query 6: Unavailable videos (title LIKE '[Unavailable%', no subtitles)
        res = conn.execute(
            f"""
            SELECT v.channel_id, COUNT(DISTINCT v.video_id) as unavailable
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            WHERE v.channel_id IN ({placeholders})
                AND v.video_title LIKE '[Unavailable%'
                AND s.subtitle_id IS NULL
            GROUP BY v.channel_id
            """,
            channel_ids,
        ).fetchall()
        for row in res:
            stats_by_channel[row[0]]["unavailable"] = row[1]

    # Calculate "no subs" for each channel
    for cid in stats_by_channel:
        stats = stats_by_channel[cid]
        stats["without_transcripts"] = max(
            0,
            stats["total"]
            - stats["with_transcripts"]
            - stats["scheduled"]
            - stats["members_only"]
            - stats["unavailable"],
        )

    return stats_by_channel


def get_channel_stats_with_subs(channel_id: str) -> dict[str, int]:
    """
    Get video statistics for a channel including subscriber count.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Dictionary with video counts and subscriber count
    """
    stats = get_channel_stats(channel_id)

    # Add subscriber count from Channels table
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT subscriber_count FROM Channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        stats["subscriber_count"] = res[0] if res else None

    return stats


def get_playlist_count(channel_id: str) -> int | None:
    """
    Get playlist count for a channel.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Playlist count or None if not available
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT playlist_count FROM Channels WHERE channel_id = ?", (channel_id,)
        ).fetchone()
        return res[0] if res else None


def get_channel_stats_with_subs_and_playlists(channel_id: str) -> dict[str, int]:
    """
    Get video statistics for a channel including subscriber and playlist counts.

    OPTIMIZED: Single query combines video stats with channel metadata.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Dictionary with video counts, subscriber count, playlist count, and unavailable subtypes
    """
    stats = {
        "total": 0,
        "with_transcripts": 0,
        "without_transcripts": 0,
        "scheduled": 0,
        "members_only": 0,
        "unavailable": 0,
        "unavail_deleted": 0,
        "unavail_private": 0,
        "unavail_geo": 0,
        "unavail_resolvable": 0,  # Age-restricted, potentially solvable with cookies
        "shorts": 0,
        "no_subtitles_available": 0,  # Audio-only videos (no cc on YouTube)
        "cc_available": 0,  # Videos with cc available but not downloaded
        "subscriber_count": None,
        "playlist_count": None,
    }

    with get_db_connection() as conn:
        # Single query to get all video stats and channel metadata
        # Uses conditional aggregation to compute all stats in one pass
        res = conn.execute(
            """
            SELECT
                -- Video counts using conditional aggregation
                COUNT(DISTINCT v.video_id) as total,
                COUNT(CASE WHEN s.subtitle_id IS NOT NULL THEN 1 END) as with_transcripts,
                COUNT(CASE WHEN v.video_title LIKE '[Scheduled%' AND s.subtitle_id IS NULL THEN 1 END) as scheduled,
                COUNT(CASE WHEN v.video_title LIKE '[Members only%' AND s.subtitle_id IS NULL THEN 1 END) as members_only,
                COUNT(CASE WHEN v.video_title LIKE '[Unavailable%' AND s.subtitle_id IS NULL THEN 1 END) as unavailable,
                COUNT(CASE WHEN v.video_title = '[Unavailable/Deleted]' AND s.subtitle_id IS NULL THEN 1 END) as unavail_deleted,
                COUNT(CASE WHEN v.video_title = '[Unavailable/Private]' AND s.subtitle_id IS NULL THEN 1 END) as unavail_private,
                COUNT(CASE WHEN v.video_title = '[Unavailable/Geo-blocked]' AND s.subtitle_id IS NULL THEN 1 END) as unavail_geo,
                COUNT(CASE WHEN v.video_title = '[Unavailable]' AND s.subtitle_id IS NULL THEN 1 END) as unavail_generic,
                COUNT(CASE WHEN v.is_short = 1 THEN 1 END) as shorts,
                COUNT(CASE WHEN v.video_title = '[No Subtitles]' AND s.subtitle_id IS NULL THEN 1 END) as no_subtitles_available,
                -- Channel metadata
                c.subscriber_count,
                c.playlist_count
            FROM Videos v
            LEFT JOIN Subtitles s ON v.video_id = s.video_id
            LEFT JOIN Channels c ON v.channel_id = c.channel_id
            WHERE v.channel_id = ?
            """,
            (channel_id,),
        ).fetchone()

        if res:
            stats["total"] = res[0] or 0
            stats["with_transcripts"] = res[1] or 0
            stats["scheduled"] = res[2] or 0
            stats["members_only"] = res[3] or 0
            stats["unavailable"] = res[4] or 0
            stats["unavail_deleted"] = res[5] or 0
            stats["unavail_private"] = res[6] or 0
            stats["unavail_geo"] = res[7] or 0
            # Generic unavailable may be age-restricted (resolvable with cookies)
            stats["unavail_resolvable"] = res[8] or 0
            stats["shorts"] = res[9] or 0
            stats["no_subtitles_available"] = res[10] or 0
            stats["subscriber_count"] = res[11]
            stats["playlist_count"] = res[12]

        # Calculate without_transcripts (pure actionable videos)
        stats["without_transcripts"] = max(
            0,
            stats["total"]
            - stats["with_transcripts"]
            - stats["scheduled"]
            - stats["members_only"]
            - stats["unavailable"],
        )

        # Calculate cc_available: videos with cc available but not downloaded
        # This is without_transcripts minus shorts and no_subtitles_available (audio-only)
        stats["cc_available"] = max(
            0,
            stats["without_transcripts"]
            - stats["shorts"]
            - stats["no_subtitles_available"],
        )

    return stats


def update_channel_stats(channel_id: str) -> dict[str, int]:
    """
    Update and return channel statistics.

    This function is called by the inconsistency repair system to ensure
    channel statistics are current. Since get_channel_stats() calculates
    stats on-the-fly from the database, this function serves as a
    consistency check and future extension point for API refreshes.

    Args:
        channel_id: YouTube channel ID

    Returns:
        Dictionary with current channel statistics
    """
    # Currently a no-op wrapper around get_channel_stats
    # In the future, this could trigger a metadata refresh from the API
    return get_channel_stats(channel_id)