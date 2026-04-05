import sqlite3


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
        from yt_fts.db.infra import get_db_path

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        curr = conn.cursor()

        # Check if language_code column exists (backward compatibility)
        curr.execute("PRAGMA table_info(Subtitles)")
        columns = [row[1] for row in curr.fetchall()]
        has_language = "language_code" in columns

        # Use proximity-aware query parsing if options provided
        if proximity is not None or near_term is not None:
            from yt_fts.core.database import parse_query_with_proximity

            fts5_query = parse_query_with_proximity(text, proximity, near_term)
        else:
            from yt_fts.core.database import parse_query

            fts5_query = parse_query(text)

        # Build query conditionally based on schema
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
            if has_language:
                curr.execute(
                    sql,
                    (
                        fts5_query,
                        after_date,
                        after_date,
                        before_date,
                        before_date,
                        language,
                        language,
                        limit,
                    ),
                )
            else:
                curr.execute(
                    sql,
                    (
                        fts5_query,
                        after_date,
                        after_date,
                        before_date,
                        before_date,
                        limit,
                    ),
                )
        elif has_language:
            curr.execute(
                sql,
                (
                    fts5_query,
                    after_date,
                    after_date,
                    before_date,
                    before_date,
                    language,
                    language,
                ),
            )
        else:
            curr.execute(
                sql, (fts5_query, after_date, after_date, before_date, before_date)
            )

        res = curr.fetchall()

        formatted_res = []

        for row in res:
            video_id = row[2]
            formatted_res.append(
                {
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
            )

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
    from yt_fts.db.infra import get_db_path

    db_path = get_db_path()
    conn = sqlite3.connect(db_path)
    curr = conn.cursor()

    # Check if language_code column exists (backward compatibility)
    curr.execute("PRAGMA table_info(Subtitles)")
    columns = [row[1] for row in curr.fetchall()]
    has_language = "language_code" in columns

    # Use proximity-aware query parsing if options provided
    if proximity is not None or near_term is not None:
        from yt_fts.core.database import parse_query_with_proximity

        fts5_query = parse_query_with_proximity(text, proximity, near_term)
    else:
        from yt_fts.core.database import parse_query

        fts5_query = parse_query(text)

    # Build query conditionally based on schema
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
        if has_language:
            curr.execute(
                query,
                (
                    fts5_query,
                    channel_id,
                    after_date,
                    after_date,
                    before_date,
                    before_date,
                    language,
                    language,
                    limit,
                ),
            )
        else:
            curr.execute(
                query,
                (
                    fts5_query,
                    channel_id,
                    after_date,
                    after_date,
                    before_date,
                    before_date,
                    limit,
                ),
            )
    elif has_language:
        curr.execute(
            query,
            (
                fts5_query,
                channel_id,
                after_date,
                after_date,
                before_date,
                before_date,
                language,
                language,
            ),
        )
    else:
        curr.execute(
            query,
            (fts5_query, channel_id, after_date, after_date, before_date, before_date),
        )

    res = curr.fetchall()
    formatted_res = []
    for row in res:
        formatted_res.append(
            {
                "rowid": row[0],
                "subtitle_id": row[1],
                "video_id": row[2],
                "start_time": row[3],
                "stop_time": row[4],
                "text": row[5],
            }
        )
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
        from yt_fts.db.infra import get_db_path

        db_path = get_db_path()
        conn = sqlite3.connect(db_path)
        curr = conn.cursor()

        # Check if language_code column exists (backward compatibility)
        curr.execute("PRAGMA table_info(Subtitles)")
        columns = [row[1] for row in curr.fetchall()]
        has_language = "language_code" in columns

        # Use proximity-aware query parsing if options provided
        if proximity is not None or near_term is not None:
            from yt_fts.core.database import parse_query_with_proximity

            fts5_query = parse_query_with_proximity(text, proximity, near_term)
        else:
            from yt_fts.core.database import parse_query

            fts5_query = parse_query(text)

        # Build query conditionally based on schema
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
            s.text
        FROM
            Subtitles_fts fts
        JOIN
            Subtitles s ON fts.rowid = s.rowid
        JOIN
            Videos v ON s.video_id = v.video_id
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
            if has_language:
                curr.execute(
                    sql,
                    (
                        video_id,
                        fts5_query,
                        after_date,
                        after_date,
                        before_date,
                        before_date,
                        language,
                        language,
                        limit,
                    ),
                )
            else:
                curr.execute(
                    sql,
                    (
                        video_id,
                        fts5_query,
                        after_date,
                        after_date,
                        before_date,
                        before_date,
                        limit,
                    ),
                )
        elif has_language:
            curr.execute(
                sql,
                (
                    video_id,
                    fts5_query,
                    after_date,
                    after_date,
                    before_date,
                    before_date,
                    language,
                    language,
                ),
            )
        else:
            curr.execute(
                sql,
                (
                    video_id,
                    fts5_query,
                    after_date,
                    after_date,
                    before_date,
                    before_date,
                ),
            )

        res = curr.fetchall()

        formatted_res = []

        for row in res:
            video_id = row[2]
            formatted_res.append(
                {
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
            )

        conn.close()
        return formatted_res

    except Exception as e:
        print(e)
        raise
