"""
Vector search functionality for chatbot context generation.

Provides transcript search using SQLite FTS5 with relevance scoring.
"""
from __future__ import annotations

import sqlite3
from dataclasses import dataclass


@dataclass
class VectorSearchResult:
    """Result from transcript search."""

    video_id: str
    video_title: str
    channel_name: str
    timestamp: str
    text: str
    score: float


def search_transcripts(
    query: str,
    db_path: str,
    max_results: int = 5,
) -> list[VectorSearchResult]:
    """Search video transcripts using FTS5.

    Args:
        query: Search query text.
        db_path: Path to SQLite database.
        max_results: Maximum number of results to return.

    Returns:
        List of VectorSearchResult objects ordered by relevance.
    """
    if not query or not query.strip():
        return []

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Check if subtitles_fts table exists
        cursor.execute(
            """
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='subtitles_fts'
        """
        )
        if not cursor.fetchone():
            return []

        # Search using FTS5 with ranking
        search_query = """
            SELECT
                s.video_id,
                v.video_title,
                v.channel_name,
                s.timestamp,
                s.text,
                bm25(subtitles_fts) as score
            FROM subtitles_fts s
            JOIN videos v ON s.video_id = v.video_id
            WHERE subtitles_fts MATCH ?
            ORDER BY score
            LIMIT ?
        """

        cursor.execute(search_query, (query, max_results))
        rows = cursor.fetchall()

        results = [
            VectorSearchResult(
                video_id=row["video_id"],
                video_title=row["video_title"] or "Unknown",
                channel_name=row["channel_name"] or "Unknown",
                timestamp=row["timestamp"] or "0:00",
                text=row["text"] or "",
                score=abs(row["score"]) if row["score"] is not None else 0.0,
            )
            for row in rows
        ]

        conn.close()
        return results

    except (sqlite3.Error, Exception):
        # Return empty list on any database error
        return []


def format_results_as_context(results: list[VectorSearchResult]) -> str:
    """Format search results as context string for LLM.

    Args:
        results: List of VectorSearchResult objects.

    Returns:
        Formatted context string.
    """
    if not results:
        return "Context: No relevant information found in the video transcripts."

    context_parts = ["Context from video transcripts:\n"]

    for i, result in enumerate(results[:3], 1):  # Use top 3 results
        context_parts.append(
            f"{i}. [{result.video_title}] by {result.channel_name} ({result.timestamp}):\n"
            f'   "{result.text[:200]}..."\n'
        )

    return "\n".join(context_parts)
