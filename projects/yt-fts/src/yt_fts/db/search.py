
from __future__ import annotations
import sqlite3



def _check_language_column(curr):
    """Check if language_code column exists in Subtitles table.
    
    Args:
        curr: SQLite cursor object.
        
    Returns:
        bool: True if language_code column exists, False otherwise.
    """
    curr.execute("PRAGMA table_info(Subtitles)")
    columns = [row[1] for row in curr.fetchall()]
    return "language_code" in columns


def _parse_search_query(text, proximity, near_term):
    """Parse search query with optional proximity support.
    
    Args:
        text: Search query text.
        proximity: Maximum word distance for NEAR queries.
        near_term: Optional term to find all query terms near.
        
    Returns:
        str: FTS5 query string.
    """
    if proximity is not None or near_term is not None:
        from yt_fts.core.database import parse_query_with_proximity
        return parse_query_with_proximity(text, proximity, near_term)
    else:
        from yt_fts.core.database import parse_query
        return parse_query(text)


def _build_search_params(fts5_query, after_date, before_date, language, limit, has_language, *extra_params):
    """Build parameter tuple for search query execution.
    
    Args:
        fts5_query: Parsed FTS5 query string.
        after_date: Filter videos after this date.
        before_date: Filter videos before this date.
        language: Filter subtitles by language code.
        limit: Maximum number of results.
        has_language: Whether language_code column exists.
        *extra_params: Additional query-specific parameters (e.g., channel_id, video_id).
        
    Returns:
        tuple: Parameters for cursor.execute().
    """
    params = list(extra_params)
    params.extend([fts5_query, after_date, after_date, before_date, before_date])
    
    if has_language:
        params.extend([language, language])
    
    if limit is not None:
        params.append(limit)
    
    return tuple(params)



def _format_search_result_full(row):
    """Format a database row with full metadata (title, channel, link).
    
    Args:
        row: Database row with subtitle match data including video and channel info.
        
    Returns:
        dict: Formatted result with all fields including link.
    """
    video_id = row[2]
    return {
        "rowid": row[0],
        "subtitle_id": row[1],
        "video_id": video_id,
        "start_time": row[3],
        "stop_time": row[4],
        "text": row[5],
        "title": row[6],
        "channel_id": row[7],
        "channel_name": row[8],
        "link": f"https://youtu.be/{video_id}",
    }


def _format_search_result_minimal(row):
    """Format a database row with minimal fields (no title, channel, link).
    
    Args:
        row: Database row with subtitle match data.
        
    Returns:
        dict: Formatted result with essential fields only.
    """
    return {
        "rowid": row[0],
        "subtitle_id": row[1],
        "video_id": row[2],
        "start_time": row[3],
        "stop_time": row[4],
        "text": row[5],
    }


def _format_search_results(res, formatter):
    """Format all database rows using the provided formatter function.
    
    Args:
        res: List of database rows.
        formatter: Function to format each row.
        
    Returns:
        list: Formatted result dictionaries.
    """
    return [formatter(row) for row in res]




def search_all(
    text: str,
    limit: int | None = None,
    proximity: int | None = None,
    near_term: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    language: str | None = None,
) -> list[dict[str, int | str]]:
    """Search for subtitle text across all channels and videos.

    Performs a full-text search across all subtitles in the database.
    Supports optional proximity search, date filtering, and language filtering.

    Args:
        text: Search query text.
        limit: Maximum number of results to return.
        proximity: Maximum word distance for NEAR queries.
        near_term: Optional term to find all query terms near.
        after_date: Filter to videos published on or after this date (ISO format).
        before_date: Filter to videos published on or before this date (ISO format).
        language: Filter to subtitles with this language code.

    Returns:
        A list of dictionaries containing subtitle match details including
        rowid, subtitle_id, video_id, start_time, stop_time, text, title,
        channel_id, channel_name, and link.
    """
    try:
        from yt_fts.db.infra import get_db_connection

        conn = get_db_connection()
        curr = conn.cursor()

        has_language = _check_language_column(curr)
        fts5_query = _parse_search_query(text, proximity, near_term)

        language_clause = (
            "AND (? IS NULL OR s.language_code = ?)" if has_language else ""
        )

        sql = f"""
            SELECT
                s.rowid,
                s.subtitle_id,
                s.video_id,
                s.start_time,
                s.stop_time,
                s.text,
                v.video_title,
                v.channel_id,
                c.channel_name
            FROM
                Subtitles_fts fts
            JOIN
                Subtitles s ON fts.rowid = s.rowid
            JOIN
                Videos v ON s.video_id = v.video_id
            JOIN
                Channels c ON v.channel_id = c.channel_id
            WHERE
                fts.text MATCH ?
                AND (? IS NULL OR v.video_date >= ?)
                AND (? IS NULL OR v.video_date <= ?)
                {language_clause}
            ORDER BY
                rank
        """

        if limit is not None:
            sql += " LIMIT ?"

        params = _build_search_params(
            fts5_query, after_date, before_date, language, limit, has_language
        )

        curr.execute(sql, params)
        res = curr.fetchall()

        formatted_res = _format_search_results(res, _format_search_result_full)

        conn.close()
        return formatted_res

    except Exception as e:
        print(e)
        raise
def search_channel(
    channel_id: str,
    text: str,
    limit: int | None = None,
    proximity: int | None = None,
    near_term: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    language: str | None = None,
) -> list[dict[str, int | str]]:
    """Search for subtitle text within a specific channel.

    Performs a full-text search across all subtitles for videos belonging to
    the specified channel. Supports optional proximity search, date filtering,
    and language filtering.

    Args:
        channel_id: YouTube channel ID to search within.
        text: Search query text.
        limit: Maximum number of results to return.
        proximity: Maximum word distance for NEAR queries.
        near_term: Optional term to find all query terms near.
        after_date: Filter to videos published on or after this date (ISO format).
        before_date: Filter to videos published on or before this date (ISO format).
        language: Filter to subtitles with this language code.

    Returns:
        A list of dictionaries containing subtitle match details including
        rowid, subtitle_id, video_id, start_time, stop_time, text, title,
        channel_id, channel_name, and link.
    """
    from yt_fts.db.infra import get_db_connection

    conn = get_db_connection()
    curr = conn.cursor()

    has_language = _check_language_column(curr)
    fts5_query = _parse_search_query(text, proximity, near_term)

    language_clause = "AND (? IS NULL OR s.language_code = ?)" if has_language else ""

    query = f"""
        SELECT
            s.rowid,
            s.subtitle_id,
            s.video_id,
            s.start_time,
            s.stop_time,
            s.text
        FROM
            Subtitles_fts fts
        JOIN
            Subtitles s ON fts.rowid = s.rowid
        JOIN
            Videos v ON s.video_id = v.video_id
        WHERE
            fts.text MATCH ?
            AND v.channel_id = ?
            AND (? IS NULL OR v.video_date >= ?)
            AND (? IS NULL OR v.video_date <= ?)
            {language_clause}
        ORDER BY
            rank
    """

    if limit is not None:
        query += " LIMIT ?"

    params = _build_search_params(
        fts5_query, after_date, before_date, language, limit, has_language, channel_id
    )

    curr.execute(query, params)
    res = curr.fetchall()
    formatted_res = _format_search_results(res, _format_search_result_minimal)
    conn.close()

    return formatted_res
def search_video(
    video_id: str,
    text: str,
    limit: int | None = None,
    proximity: int | None = None,
    near_term: str | None = None,
    after_date: str | None = None,
    before_date: str | None = None,
    language: str | None = None,
) -> list[dict[str, int | str]]:
    """Search for subtitle text within a specific video.

    Performs a full-text search across subtitles for a single video.
    Supports optional proximity search, date filtering, and language filtering.

    Args:
        video_id: YouTube video ID to search within.
        text: Search query text.
        limit: Maximum number of results to return.
        proximity: Maximum word distance for NEAR queries.
        near_term: Optional term to find all query terms near.
        after_date: Filter to videos published on or after this date (ISO format).
        before_date: Filter to videos published on or before this date (ISO format).
        language: Filter to subtitles with this language code.

    Returns:
        A list of dictionaries containing subtitle match details including
        rowid, subtitle_id, video_id, start_time, stop_time, text, title,
        channel_id, channel_name, and link.
    """
    try:
        from yt_fts.db.infra import get_db_connection

        conn = get_db_connection()
        curr = conn.cursor()

        has_language = _check_language_column(curr)
        fts5_query = _parse_search_query(text, proximity, near_term)

        language_clause = (
            "AND (? IS NULL OR s.language_code = ?)" if has_language else ""
        )

        sql = f"""
        SELECT
            s.rowid,
            s.subtitle_id,
            s.video_id,
            s.start_time,
            s.stop_time,
            s.text,
            v.video_title,
            v.channel_id,
            c.channel_name
        FROM
            Subtitles_fts fts
        JOIN
            Subtitles s ON fts.rowid = s.rowid
        JOIN
            Videos v ON s.video_id = v.video_id
        JOIN
            Channels c ON v.channel_id = c.channel_id
        WHERE
            s.video_id = ?
        AND
            fts.text MATCH ?
            AND (? IS NULL OR v.video_date >= ?)
            AND (? IS NULL OR v.video_date <= ?)
            {language_clause}
        """

        if limit is not None:
            sql += " LIMIT ?"

        params = _build_search_params(
            fts5_query, after_date, before_date, language, limit, has_language, video_id
        )

        curr.execute(sql, params)
        res = curr.fetchall()

        formatted_res = _format_search_results(res, _format_search_result_full)

        conn.close()
        return formatted_res

    except Exception as e:
        print(e)
        raise
