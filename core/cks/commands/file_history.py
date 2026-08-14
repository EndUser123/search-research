"""Query CKS for all lessons related to a specific file.

Provides query_file_history() function to retrieve CKS entries
by file path metadata or title matching.

Uses direct SQL queries to ensure immediate retrieval of newly stored entries.
"""

from __future__ import annotations

import json
import sqlite3
import sys


def query_file_history(file_path: str) -> list[dict]:
    """Query CKS for all entries mentioning a specific file.

    Matches entries by:
    1. metadata["file_path"] exact match
    2. file_path appears in entry title

    Args:
        file_path: File name or path (e.g., "contract_api.py")

    Returns:
        List of entries with metadata including:
        - id: Entry ID
        - type: Entry type
        - title: Entry title
        - content: Entry content
        - file_path: Extracted from metadata if present
        - line_number: Extracted from metadata if present
        - category: Category from metadata
        - created_at: Creation timestamp

    """
    sys.path.insert(0, "P:\\\\\\__csf")
    from src.cks.unified import CKS

    results = []

    with CKS() as cks:
        # Direct SQL query - bypasses semantic search to find newly stored entries
        conn = sqlite3.connect(str(cks.db_path))
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Query entries with file_path in metadata OR file name in title
        cursor.execute(
            """
            SELECT id, type, title, content, metadata, created_at
            FROM entries
            WHERE metadata LIKE ? OR title LIKE ?
            ORDER BY created_at DESC
            LIMIT 100
        """,
            (f'%"file_path": "{file_path}"%', f"%{file_path}%"),
        )

        for row in cursor.fetchall():
            # Parse metadata JSON (CKS stores nested: {metadata: {...}})
            outer_metadata = {}
            inner_metadata = {}
            if row["metadata"]:
                try:
                    outer_metadata = json.loads(row["metadata"])
                    # Actual data is in nested 'metadata' key
                    inner_metadata = outer_metadata.get("metadata", {})
                except json.JSONDecodeError:
                    pass

            # Filter to only exact file_path matches or title matches
            metadata_file_path = inner_metadata.get("file_path")
            if metadata_file_path == file_path or file_path in row["title"]:
                results.append(
                    {
                        "id": row["id"],
                        "type": row["type"],
                        "title": row["title"],
                        "content": row["content"],
                        "file_path": metadata_file_path,
                        "line_number": inner_metadata.get("line_number"),
                        "category": inner_metadata.get("category"),
                        "created_at": row["created_at"],
                    }
                )

        conn.close()

    return results
