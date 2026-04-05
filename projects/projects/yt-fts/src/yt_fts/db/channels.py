import logging
import sqlite3
from datetime import datetime, timedelta, timezone

from sqlite_utils import Database

from yt_fts.db.infra import get_db_connection
from yt_fts.utils.config import get_db_path

logger = logging.getLogger(__name__)


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


def add_channel_info(channel_id: str, channel_name: str, channel_url: str) -> None:
    """
    Add or update a channel in the database.
    """
    with get_db_connection() as conn:
        # Check if channel exists to decide insert or update
        # (Simplified logic mimicking original behavior which often assumes insert or ignore/update)
        try:
            conn.execute(
                "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
                (channel_id, channel_name, channel_url),
            )
            conn.commit()
            # Force checkpoint to ensure commit is written to disk
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            logger.debug(
                f"add_channel_info INSERT committed: {channel_id} -> {channel_name}"
            )
        except sqlite3.IntegrityError:
            # If it exists, update name and url just in case
            conn.execute(
                "UPDATE Channels SET channel_name = ?, channel_url = ? WHERE channel_id = ?",
                (channel_name, channel_url, channel_id),
            )
            conn.commit()
            # Force checkpoint to ensure commit is written to disk
            conn.execute("PRAGMA wal_checkpoint(TRUNCATE);")
            logger.debug(
                f"add_channel_info UPDATE committed: {channel_id} -> {channel_name}"
            )


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


def get_channel_id_from_input(input_value: str) -> str | None:
    """
    Try to resolve a channel ID locally from the database if input is a known name or URL.
    This is a partial extraction; complex resolution often involves scraped logic handled elsewhere,
    but this covers the DB lookups.
    """
    with get_db_connection() as conn:
        # Check if input is a channel_id
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_id = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

        # Check if input matches a stored channel_url
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_url = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

        # Check exact name match
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_name = ?", (input_value,)
        ).fetchone()
        if res:
            return res[0]

    return None


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


def get_channel_id_by_handle_substring(handle: str) -> str | None:
    """
    Get channel ID if channel name or URL contains the handle.
    Used for fuzzy matching when exact resolution fails.
    """
    with get_db_connection() as conn:
        res = conn.execute(
            "SELECT channel_id FROM Channels WHERE channel_name LIKE ? OR channel_url LIKE ?",
            (f"%{handle}%", f"%@{handle}%"),
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
        except Exception:
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
    except Exception:
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
    except Exception:
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
        scheduled, members_only, unavailable, shorts
    """
    stats = {
        "total": 0,
        "with_transcripts": 0,
        "without_transcripts": 0,
        "scheduled": 0,
        "members_only": 0,
        "unavailable": 0,
        "shorts": 0,
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

    Args:
        channel_ids: List of YouTube channel IDs

    Returns:
        Dictionary mapping channel_id to stats dict with keys: total, with_transcripts,
        without_transcripts, scheduled, members_only, unavailable, shorts
    """
    stats_by_channel = {}

    with get_db_connection() as conn:
        for channel_id in channel_ids:
            stats = {
                "total": 0,
                "with_transcripts": 0,
                "without_transcripts": 0,
                "scheduled": 0,
                "members_only": 0,
                "unavailable": 0,
                "shorts": 0,
            }

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

            # Get shorts (Metadata only, not disjoint)
            res = conn.execute(
                "SELECT COUNT(*) FROM Videos WHERE channel_id = ? AND is_short = 1",
                (channel_id,),
            ).fetchone()
            stats["shorts"] = res[0] if res else 0

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

            # Get members only videos (WITHOUT transcripts)
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

            # Calculate pure "no subs" (actionable videos)
            stats["without_transcripts"] = max(
                0,
                stats["total"]
                - stats["with_transcripts"]
                - stats["scheduled"]
                - stats["members_only"]
                - stats["unavailable"],
            )

            stats_by_channel[channel_id] = stats

    return stats_by_channel
