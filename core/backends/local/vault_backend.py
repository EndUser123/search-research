"""Claude Vault Search Backend - SQLite FTS5 search for archived sessions.

This backend provides search over Claude Code sessions archived in claude-vault,
a local SQLite database of sessions and messages from the Claude Code harness.
"""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path
from typing import Any

from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

# Score normalization constants (matching ClaudeHistoryBackend)
FTS5_SCORE_MIN = 0.7
FTS5_SCORE_SPREAD = 0.3
FTS5_RANK_DEFAULT = 0.5

# LIKE search score tiers
LIKE_SCORE_EXACT_PREFIX = 0.9
LIKE_SCORE_WORD_BOUNDARY = 0.8
LIKE_SCORE_CONTAINS = 0.7

# Result set limits
DIVERSIFICATION_MAX_PER_SESSION = 2
FETCH_LIMIT_MULTIPLIER = 3
FETCH_LIMIT_MAX = 100
SNIPPET_LENGTH = 200


class VaultBackend(BaseLocalBackend):
    """Search backend for Claude Vault archived sessions.

    Uses SQLite FTS5 for fast keyword search over archived Claude Code sessions
    stored in the claude-vault database.
    """

    name = "vault"
    description = "Fast keyword search for archived Claude Code sessions using SQLite FTS5"
    source_types = ["vault", "archive"]

    def __init__(
        self,
        root_paths: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
        db_path: str | None = None,
    ):
        """Initialize the Vault backend.

        Args:
            root_paths: Not used for vault (kept for BaseLocalBackend compatibility)
            exclude_patterns: Not used for vault (kept for BaseLocalBackend compatibility)
            db_path: Path to vault SQLite database
                    (defaults to ~/.local/share/claude-vault/vault.db)
        """
        super().__init__(root_paths, exclude_patterns)

        if db_path is None:
            # Default to standard claude-vault location
            home = Path.home()
            db_path = str(home / ".local" / "share" / "claude-vault" / "vault.db")

        self.db_path = Path(db_path)

        # Log if database doesn't exist
        if not self.db_path.exists():
            logger.debug(f"Vault database not found at {self.db_path}")

    def build_index(self) -> None:
        """Build index (not applicable for SQLite FTS5)."""
        pass

    def _fts5_search(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        project: str | None,
    ) -> list[SearchResult]:
        """Attempt FTS5 MATCH search with BM25 ranking.

        Returns a list (possibly empty) on success.
        Raises sqlite3.Error on FTS5 failure so caller can fall back to LIKE.
        """
        # Escape FTS5 special characters: * " - + ( )
        fts_query = query.replace('"', '""')
        fts_query = f'"{fts_query}"'

        try:
            # Step 1: Get rowids and BM25 scores from FTS5
            cursor.execute(
                "SELECT rowid, bm25(messages_fts) as rank FROM messages_fts WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?",
                [fts_query, str(limit)],
            )
            fts_rows = cursor.fetchall()

            if not fts_rows:
                return []

            # Step 2: Build rowid→score map
            rowid_scores: dict[int, float] = {row["rowid"]: row["rank"] for row in fts_rows}

            # Step 3: Fetch message content by id
            placeholders = ",".join("?" * len(rowid_scores))
            cursor.execute(
                f"""
                SELECT m.id, m.session_id, m.role,
                       m.content, m.timestamp, s.project
                FROM messages m
                LEFT JOIN sessions s ON s.session_id = m.session_id
                WHERE m.id IN ({placeholders})
                """,
                list(rowid_scores.keys()),
            )
            msg_rows = cursor.fetchall()

            # Step 4: Normalize BM25 ranks to 0-1 scores
            ranks = list(rowid_scores.values())
            min_rank = min(ranks)
            max_rank = max(ranks)
            rank_range = max_rank - min_rank if max_rank != min_rank else 1.0

            results = []
            for row in msg_rows:
                rowid = row["id"]
                bm25_rank = rowid_scores.get(rowid, 0.0)
                norm_rank = (bm25_rank - min_rank) / rank_range if rank_range != 0 else FTS5_RANK_DEFAULT
                score = 1.0 - (norm_rank * FTS5_SCORE_SPREAD)

                # Apply project filter in Python (FTS5 result is already limited)
                if project and row["project"] != project:
                    continue

                results.append(
                    {
                        "title": f"{row['role']} - {row['timestamp']}",
                        "content": row["content"],
                        "score": round(score, 3),
                        "metadata": {
                            "session_id": row["session_id"],
                            "role": row["role"],
                            "timestamp": row["timestamp"],
                            "project": row["project"],
                            "snippet": row["content"][:SNIPPET_LENGTH],
                        },
                    }
                )

            return results

        except (sqlite3.Error, IndexError, KeyError) as e:
            logger.debug(f"FTS5 MATCH failed, falling back to LIKE: {e}")
            raise

    def _like_search(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        project: str | None,
    ) -> list[SearchResult]:
        """LIKE-based search with position-based ranking.

        Used as fallback when FTS5 is unavailable.
        """
        import re as re_module

        sql = """
            SELECT
                m.session_id,
                m.role,
                m.content,
                m.timestamp,
                s.project,
                CASE
                    WHEN m.content LIKE ? THEN 3
                    WHEN m.content LIKE ? THEN 2
                    WHEN m.content LIKE ? THEN 1
                    ELSE 0
                END as match_level
            FROM messages m
            LEFT JOIN sessions s ON s.session_id = m.session_id
            WHERE m.content LIKE ?
        """

        # Escape LIKE wildcards in query
        escaped_query = re_module.escape(query)
        prefix_q = f"{escaped_query}%"
        boundary_q = f"% {escaped_query} %"
        contains_q = f"%{escaped_query}%"

        params = [prefix_q, boundary_q, contains_q, contains_q]

        if project:
            sql = sql.replace("LEFT JOIN sessions s", "JOIN sessions s")
            sql += " AND s.project = ?"
            params.append(project)

        sql += " ORDER BY match_level DESC, length(m.content) ASC LIMIT ?"
        params.append(str(limit))

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            match_level = row["match_level"]
            score = LIKE_SCORE_EXACT_PREFIX if match_level == 3 else (LIKE_SCORE_WORD_BOUNDARY if match_level == 2 else LIKE_SCORE_CONTAINS)

            results.append(
                {
                    "title": f"{row['role']} - {row['timestamp']}",
                    "content": row["content"],
                    "score": score,
                    "metadata": {
                        "session_id": row["session_id"],
                        "role": row["role"],
                        "timestamp": row["timestamp"],
                        "project": row["project"],
                        "snippet": row["content"][:SNIPPET_LENGTH],
                    },
                }
            )
        return results

    def _diversify_results(
        self,
        results: list[SearchResult],
        limit: int,
        max_per_session: int = DIVERSIFICATION_MAX_PER_SESSION,
    ) -> list[SearchResult]:
        """Diversify search results across sessions."""
        if not results:
            return results

        if max_per_session <= 0:
            sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_results[:limit]

        # Group by session_id
        session_groups: dict[str, list[SearchResult]] = {}
        for result in results:
            metadata = result.get("metadata") or {}
            session_id = metadata.get("session_id", "unknown")
            if session_id not in session_groups:
                session_groups[session_id] = []
            session_groups[session_id].append(result)

        # Sort results within each session by score
        for session_id in session_groups:
            session_groups[session_id].sort(key=lambda x: x.get("score", 0), reverse=True)

        # Interleave results from different sessions
        diversified: list[SearchResult] = []
        session_iters = {
            sid: iter(group[:max_per_session]) for sid, group in session_groups.items()
        }

        max_rounds = max_per_session
        for _ in range(max_rounds):
            for session_id in session_iters:
                try:
                    result = next(session_iters[session_id])
                    diversified.append(result)
                    if len(diversified) >= limit:
                        return diversified
                except StopIteration:
                    pass

        # Add remaining results sorted by score
        if len(diversified) < limit:
            remaining = []
            for session_id, group in session_groups.items():
                for result in group[max_per_session:]:
                    remaining.append(result)
            remaining.sort(key=lambda x: x.get("score", 0), reverse=True)
            diversified.extend(remaining[: limit - len(diversified)])

        return diversified[:limit]

    def search(
        self,
        query: str,
        limit: int = 10,
        *,
        project: str | None = None,
    ) -> list[SearchResult]:
        """Search vault for matching messages.

        Args:
            query: Search query string
            limit: Maximum number of results (default 10)
            project: Filter by project path (optional)

        Returns:
            List of search result dictionaries with keys:
            - title: Formatted title with role and timestamp
            - content: Message content
            - score: Relevance score (0.0-1.0, higher is better)
            - metadata: Dictionary with session_id, role, timestamp, project, snippet
        """
        # Empty query returns no results
        if not query or not query.strip():
            return []

        # Check if database exists
        if not self.db_path.exists():
            logger.debug(f"Vault database not found at {self.db_path}")
            return []

        try:
            with sqlite3.connect(str(self.db_path)) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()

                # Fetch more results than needed to allow for diversification
                fetch_limit = min(limit * FETCH_LIMIT_MULTIPLIER, FETCH_LIMIT_MAX)

                # Try FTS5 MATCH first, fall back to LIKE on FTS5 error
                try:
                    fts_results = self._fts5_search(cursor, query, fetch_limit, project)
                    return self._diversify_results(fts_results, limit)
                except sqlite3.Error:
                    # FTS5 failed, fall back to LIKE
                    pass

                # Fall back to LIKE with position-based ranking
                like_results = self._like_search(cursor, query, fetch_limit, project)
                return self._diversify_results(like_results, limit)

        except sqlite3.Error as e:
            logger.debug(f"SQLite search failed: {e}")
            return []
        except Exception as e:
            logger.debug(f"Unexpected error during SQLite search: {e}")
            return []


# Backend factory
def create_vault_backend(**kwargs) -> VaultBackend:
    """Factory function to create a VaultBackend.

    Args:
        **kwargs: Arguments passed to VaultBackend constructor

    Returns:
        Configured VaultBackend instance
    """
    return VaultBackend(**kwargs)


# Backend constants for registration
BACKEND_VAULT = {
    "name": "vault",
    "class": VaultBackend,
    "factory": create_vault_backend,
    "description": "Fast keyword search for archived Claude Code sessions",
    "source_types": ["vault", "archive"],
}
