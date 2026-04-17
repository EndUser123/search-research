"""CHS v2 FTS Search Implementation with Schema Compatibility."""

from __future__ import annotations

from typing import TYPE_CHECKING

from search_research.core.chs.schema_compat import CHSSchemaCompat
from search_research.core.chs.utils import escape_fts5_query

if TYPE_CHECKING:
    import sqlite3


def search_fts_messages(db: sqlite3.Connection, query: str, limit: int = 10) -> list[dict]:
    """Search messages using FTS5 with BM25 scoring.

    Uses schema compatibility layer to work with both legacy (chat_messages)
    and v2 (messages) table schemas.

    Args:
        db: Database connection
        query: Search query
        limit: Maximum results to return

    Returns:
        List of message dicts with 'score' and 'content' keys
    """
    if not query or not query.strip():
        return []
    escaped_query = escape_fts5_query(query)
    messages_table = CHSSchemaCompat.get_messages_table(db)
    fts_table = CHSSchemaCompat.get_fts_table(db)
    try:
        cursor = db.cursor()
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name=?", (fts_table,))
        fts_schema = cursor.fetchone()
        is_contentless = fts_schema and "content=" in fts_schema[0]
        if is_contentless:
            cursor.execute(
                f"\n                    SELECT -bm25({fts_table}) AS score, content\n                    FROM {fts_table}\n                    WHERE {fts_table} MATCH ?\n                    LIMIT ?\n                ",
                (escaped_query, limit),
            )
            fts_results = cursor.fetchall()
            if not fts_results:
                return []
            results = []
            for score, content in fts_results:
                cursor.execute(
                    f"\n                        SELECT id, session_id, role, content\n                        FROM {messages_table}\n                        WHERE content = ?\n                        LIMIT 1\n                    ",
                    (content,),
                )
                msg_row = cursor.fetchone()
                if msg_row:
                    results.append(
                        {
                            "id": msg_row[0],
                            "session_id": msg_row[1],
                            "role": msg_row[2],
                            "content": msg_row[3],
                            "score": float(score),
                        }
                    )
                if len(results) >= limit:
                    break
            results.sort(key=lambda r: r["score"], reverse=True)
            return results[:limit]
        else:
            cursor.execute(
                f"\n                    SELECT\n                        m.id,\n                        m.session_id,\n                        m.role,\n                        m.content,\n                        -bm25({fts_table}) AS score\n                    FROM {messages_table} m\n                    INNER JOIN {fts_table} ON m.rowid = {fts_table}.rowid\n                    WHERE {fts_table} MATCH ?\n                    ORDER BY score DESC\n                    LIMIT ?\n                ",
                (escaped_query, limit),
            )
            results = []
            for row in cursor.fetchall():
                results.append(
                    {
                        "id": row[0],
                        "session_id": row[1],
                        "role": row[2],
                        "content": row[3],
                        "score": float(row[4]),
                    }
                )
            return results
    except Exception as e:
        import logging

        logging.getLogger(__name__).warning(f"FTS search failed: {e}")
        return []
