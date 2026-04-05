"""
Search History and Saved Queries Database Operations

This module handles saving search history and managing saved queries.
"""

from datetime import datetime, timezone

from yt_fts.db.infra import get_db_connection


def save_search(
    query: str,
    scope: str,
    result_count: int,
    channel_id: str | None = None,
) -> int:
    """
    Save a search to history.

    Args:
        query: The search query text
        scope: The search scope ('all', 'channel', 'video')
        result_count: Number of results returned
        channel_id: Optional channel ID for channel-scoped searches

    Returns:
        The search_id of the inserted record
    """
    with get_db_connection() as conn:
        timestamp = datetime.now(timezone.utc).isoformat()

        conn.execute(
            """
            INSERT INTO SearchHistory (query, timestamp, scope, result_count, channel_id)
            VALUES (?, ?, ?, ?, ?)
            """,
            (query, timestamp, scope, result_count, channel_id),
        )
        conn.commit()

        # Get the last inserted row ID
        cursor = conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]



def get_search_history(limit: int = 20) -> list[dict]:
    """
    Get recent search history.

    Args:
        limit: Maximum number of history entries to return

    Returns:
        List of search history dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT search_id, query, timestamp, scope, result_count, channel_id
            FROM SearchHistory
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cursor.fetchall()

        return [
            {
                "search_id": row[0],
                "query": row[1],
                "timestamp": row[2],
                "scope": row[3],
                "result_count": row[4],
                "channel_id": row[5],
            }
            for row in rows
        ]


def save_query(
    name: str,
    query: str,
    scope: str | None = None,
    channel_id: str | None = None,
) -> int:
    """
    Save a query for reuse.

    Args:
        name: Name to identify the saved query
        query: The search query text
        scope: Optional search scope (None means use current scope)
        channel_id: Optional channel ID for channel-specific queries

    Returns:
        The query_id of the inserted/updated record
    """
    with get_db_connection() as conn:
        timestamp = datetime.now(timezone.utc).isoformat()

        # Check if query with this name already exists
        cursor = conn.execute(
            "SELECT query_id FROM SavedQueries WHERE name = ?", (name,)
        )
        existing = cursor.fetchone()

        if existing:
            # Update existing query
            conn.execute(
                """
                UPDATE SavedQueries
                SET query = ?, scope = ?, channel_id = ?, timestamp = ?
                WHERE name = ?
                """,
                (query, scope, channel_id, timestamp, name),
            )
            conn.commit()
            return existing[0]

        # Insert new query
        conn.execute(
            """
            INSERT INTO SavedQueries (name, query, scope, channel_id, timestamp)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, query, scope, channel_id, timestamp),
        )
        conn.commit()

        cursor = conn.execute("SELECT last_insert_rowid()")
        return cursor.fetchone()[0]


def get_saved_queries() -> list[dict]:
    """
    Get all saved queries.

    Returns:
        List of saved query dictionaries
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT query_id, name, query, scope, channel_id, timestamp
            FROM SavedQueries
            ORDER BY name
            """
        )
        rows = cursor.fetchall()

        return [
            {
                "query_id": row[0],
                "name": row[1],
                "query": row[2],
                "scope": row[3],
                "channel_id": row[4],
                "timestamp": row[5],
            }
            for row in rows
        ]


def get_saved_query_by_name(name: str) -> dict | None:
    """
    Get a saved query by name.

    Args:
        name: Name of the saved query

    Returns:
        Dictionary with query details or None if not found
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            """
            SELECT query_id, name, query, scope, channel_id, timestamp
            FROM SavedQueries
            WHERE name = ?
            """,
            (name,),
        )
        row = cursor.fetchone()

        if row:
            return {
                "query_id": row[0],
                "name": row[1],
                "query": row[2],
                "scope": row[3],
                "channel_id": row[4],
                "timestamp": row[5],
            }
        return None


def delete_saved_query(name: str) -> bool:
    """
    Delete a saved query by name.

    Args:
        name: Name of the saved query to delete

    Returns:
        True if deleted, False if not found
    """
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT query_id FROM SavedQueries WHERE name = ?", (name,)
        )
        existing = cursor.fetchone()

        if not existing:
            return False

        conn.execute("DELETE FROM SavedQueries WHERE name = ?", (name,))
        conn.commit()
        return True


def clear_search_history() -> int:
    """
    Clear all search history.

    Returns:
        Number of records deleted
    """
    with get_db_connection() as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM SearchHistory")
        count = cursor.fetchone()[0]

        conn.execute("DELETE FROM SearchHistory")
        conn.commit()

        return count
