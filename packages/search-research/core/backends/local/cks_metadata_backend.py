"""CKS Metadata Query Backend for Per-File Learning Tracking.

Provides structured metadata queries to CKS for:
- File history (all lessons for a specific file)
- Category filtering (BUG, FIX, PATTERN, VULNERABILITY, etc.)
- Skill source filtering (rca, debug, tdd, arch, security, etc.)
- Line number queries

This backend complements semantic search with exact metadata matching.
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path
from typing import Any

from ...config import config

# Backend name constant
BACKEND_CKS_METADATA = "CKS_METADATA"


class CKSMetadataBackend:
    """CKS Metadata Query Backend for structured metadata filtering.

    Provides direct SQL queries to CKS for metadata-based searches,
    bypassing semantic search for exact metadata matches.

    This enables queries like:
    - "Show all BUG findings for contract_api.py"
    - "Show all RCA findings"
    - "Show all lessons mentioning line 142"
    """

    def __init__(self, db_path: str | None = None) -> None:
        """Initialize CKS metadata backend.

        Args:
            db_path: Path to CKS database (default: from config.CKS_DB_PATH)
        """
        if db_path is None:
            db_path = config.CKS_DB_PATH
        self.db_path = Path(db_path)

    def search(
        self,
        query: str,
        limit: int = 20,
        file_path: str | None = None,
        category: str | None = None,
        skill_source: str | None = None,
        line_number: int | None = None,
    ) -> list[dict[str, Any]]:
        """Search CKS by metadata fields.

        Args:
            query: Search query (for title/content matching)
            limit: Maximum results to return
            file_path: Filter by file_path metadata (exact or partial match)
            category: Filter by category metadata (BUG, FIX, PATTERN, etc.)
            skill_source: Filter by skill_source metadata (rca, debug, tdd, etc.)
            line_number: Filter by line_number metadata (exact match)

        Returns:
            List of entries with metadata
        """
        if not self.db_path.exists():
            return []

        results = []

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # Build SQL query with filters
            where_clauses = []
            params = []

            # Add text search (title or content)
            if query and query.strip():
                where_clauses.append("(title LIKE ? OR content LIKE ?)")
                params.extend([f"%{query}%", f"%{query}%"])

            # Add file_path filter
            if file_path:
                # Match exact file_path in metadata OR partial match in title
                where_clauses.append("(metadata LIKE ? OR title LIKE ?)")
                params.extend([f'%"file_path": "{file_path}"%', f"%{file_path}%"])

            # Add category filter
            if category:
                where_clauses.append("metadata LIKE ?")
                params.append(f'%"category": "{category}"%')

            # Add skill_source filter
            if skill_source:
                where_clauses.append("metadata LIKE ?")
                # Handle both "skill_source" and "source" fields in metadata
                params.append(f'%"skill_source": "{skill_source}"%')

            # Add line_number filter
            if line_number is not None:
                where_clauses.append("metadata LIKE ?")
                params.append(f'%"line_number": {line_number}%')

            # Build WHERE clause
            where_sql = " AND ".join(where_clauses) if where_clauses else "1=1"

            # Execute query
            sql = f"""
                SELECT id, type, title, content, metadata, created_at
                FROM entries
                WHERE {where_sql}
                ORDER BY created_at DESC
                LIMIT ?
            """
            params.append(limit)

            cursor.execute(sql, params)

            for row in cursor.fetchall():
                # Parse metadata JSON (CKS stores nested: {metadata: {...}})
                outer_metadata: dict[str, Any] = {}
                inner_metadata: dict[str, Any] = {}
                if row["metadata"]:
                    try:
                        outer_metadata = json.loads(row["metadata"])
                        inner_metadata = outer_metadata.get("metadata", {})
                    except json.JSONDecodeError:
                        pass

                # Extract metadata fields
                result = {
                    "source": BACKEND_CKS_METADATA,
                    "backend": BACKEND_CKS_METADATA,
                    "reason": "Metadata match",
                    "id": row["id"],
                    "type": row["type"],
                    "title": row["title"],
                    "content": row["content"],
                    "score": 0.9,  # High score for exact metadata matches
                    "metadata": {
                        "file_path": inner_metadata.get("file_path"),
                        "line_number": inner_metadata.get("line_number"),
                        "category": inner_metadata.get("category"),
                        "skill_source": inner_metadata.get("skill_source"),
                        "created_at": row["created_at"],
                    },
                }

                # Add citation display string
                if inner_metadata.get("file_path"):
                    citation = inner_metadata["file_path"]
                    if inner_metadata.get("line_number"):
                        citation += f":{inner_metadata['line_number']}"
                    result["title"] = f"{citation} — {row['title']}"

                results.append(result)

            # Query expansion: if 0 results and query has multiple words, try each term
            if not results and query and query.strip() and " " in query.strip():
                results = self._query_expansion(query, limit)

            conn.close()

        except sqlite3.Error:
            # Database error, return empty results
            pass

        return results

    def _query_expansion(
        self,
        query: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Try individual query terms when multi-word query returns nothing.

        This handles the case where CKS entries contain individual terms but not
        the full phrase (e.g., entries mention 'claude' or 'hooks' separately
        but not 'claude hooks' as a phrase).
        """
        terms = [t.strip() for t in query.split() if t.strip()]
        if not terms:
            return []

        all_results: dict[str, dict[str, Any]] = {}

        try:
            conn = sqlite3.connect(str(self.db_path))
            conn.row_factory = sqlite3.Row

            for term in terms:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, type, title, content, metadata, created_at
                    FROM entries
                    WHERE title LIKE ? OR content LIKE ?
                    ORDER BY created_at DESC
                    LIMIT ?
                    """,
                    (f"%{term}%", f"%{term}%", limit),
                )

                for row in cursor.fetchall():
                    row_id = row["id"]
                    if row_id in all_results:
                        continue

                    try:
                        outer_metadata = json.loads(row["metadata"]) if row["metadata"] else {}
                        inner_metadata = outer_metadata.get("metadata", {})
                    except json.JSONDecodeError:
                        outer_metadata = {}
                        inner_metadata = {}

                    title = row["title"]
                    if inner_metadata.get("file_path"):
                        citation = inner_metadata["file_path"]
                        if inner_metadata.get("line_number"):
                            citation += f":{inner_metadata['line_number']}"
                        title = f"{citation} — {row['title']}"

                    result: dict[str, Any] = {
                        "source": BACKEND_CKS_METADATA,
                        "backend": BACKEND_CKS_METADATA,
                        "reason": f"Term expansion: '{term}'",
                        "id": row_id,
                        "type": row["type"],
                        "title": title,
                        "content": row["content"],
                        "score": 0.7,
                        "metadata": {
                            "file_path": inner_metadata.get("file_path"),
                            "line_number": inner_metadata.get("line_number"),
                            "category": inner_metadata.get("category"),
                            "skill_source": inner_metadata.get("skill_source"),
                            "created_at": row["created_at"],
                            "expansion_term": term,
                        },
                    }

                    all_results[row_id] = result

            conn.close()

        except sqlite3.Error:
            pass

        return list(all_results.values())[:limit]

    def query_file_history(self, file_path: str, limit: int = 100) -> list[dict[str, Any]]:
        """Query all entries for a specific file (file history).

        This is the primary interface for Per-File Learning Tracking.

        Args:
            file_path: File name or path (e.g., "contract_api.py")
            limit: Maximum results to return

        Returns:
            List of entries with file_path metadata or title matches
        """
        return self.search(
            query="",  # No text search, only metadata filter
            limit=limit,
            file_path=file_path,
        )


def create_cks_metadata_backend(
    db_path: str | None = None,
) -> CKSMetadataBackend:
    """Create a CKS metadata backend instance.

    Args:
        db_path: Path to CKS database (default: from config.CKS_DB_PATH)

    Returns:
        CKSMetadataBackend instance
    """
    return CKSMetadataBackend(db_path=db_path)
