"""Claude History Search Backend - Python wrapper for claude-history CLI.

This backend provides fast keyword search over Claude Code chat history
using the Rust-based claude-history CLI tool.
"""

from __future__ import annotations

import json
import logging
import sqlite3
import subprocess
from pathlib import Path
from typing import Any

from .base_local_backend import BaseLocalBackend

SearchResult = dict[str, Any]

logger = logging.getLogger(__name__)

# Score normalization constants
FTS5_SCORE_MIN = 0.7  # Lowest score for least-relevant FTS5 results
FTS5_SCORE_SPREAD = 0.3  # Spread between best and worst FTS5 scores
FTS5_RANK_DEFAULT = 0.5  # Default rank when all BM25 ranks are equal

# LIKE search score tiers
LIKE_SCORE_EXACT_PREFIX = 0.9  # Exact prefix match (content LIKE 'query%')
LIKE_SCORE_WORD_BOUNDARY = 0.8  # Word boundary match (content LIKE '% query %')
LIKE_SCORE_CONTAINS = 0.7  # Contains match (content LIKE '%query%')

# Result set limits
DIVERSIFICATION_MAX_PER_SESSION = 2  # Default max results per session during round-robin
FETCH_LIMIT_MULTIPLIER = 3  # Fetch this multiple of limit for diversification headroom
FETCH_LIMIT_MAX = 100  # Maximum fetch limit cap
SNIPPET_LENGTH = 200  # Default truncation length for content snippets

# Search source modes
SOURCE_JSONL = "jsonl"  # CLI-based search via claude-history executable
SOURCE_DB = "db"  # Direct SQLite FTS5 search (default, recommended)


class ClaudeHistoryBackend(BaseLocalBackend):
    """Search backend for Claude Code chat history.

    Uses the claude-history Rust CLI for fast keyword search over
    archived conversations.
    """

    name = "claude-history"
    description = "Fast keyword search for Claude Code chat history using SQLite FTS5"
    source_types = ["chat", "history"]

    def __init__(
        self,
        root_paths: list[str] | None = None,
        exclude_patterns: set[str] | None = None,
        cli_path: str | None = None,
        db_path: str | None = None,
        default_source: str = "db",
    ):
        """Initialize the Claude history backend.

        Args:
            root_paths: Not used for chat history (kept for BaseLocalBackend compatibility)
            exclude_patterns: Not used for chat history (kept for BaseLocalBackend compatibility)
            cli_path: Path to claude-history.exe (defaults to P:\\\\packages/claude-history/target/release/claude-history.exe)
            db_path: Path to SQLite database (defaults to P:\\\\__csf/data/chat_history.db)
            default_source: Default data source ("jsonl" or "db")
        """
        super().__init__(root_paths, exclude_patterns)
        if cli_path is None:
            cli_path = "P:\\\\packages/claude-history/target/release/claude-history.exe"
        if db_path is None:
            db_path = "P:\\\\__csf/data/chat_history.db"

        self.cli_path = Path(cli_path)
        self.db_path = Path(db_path)
        self.default_source = default_source

        # Verify CLI exists (optional - may not be used if db_source works)
        if not self.cli_path.exists():
            logger.debug(
                f"claude-history CLI not found at {self.cli_path}. Direct SQLite search will be used."
            )

    def build_index(self) -> None:
        """Build index (not applicable for CLI wrapper)."""
        pass

    def _search_sqlite_direct(
        self,
        query: str,
        limit: int = 10,
        *,
        project: str | None = None,
    ) -> list[SearchResult]:
        """Search SQLite database directly (alternative path to CLI).

        Args:
            query: Search query string
            limit: Maximum number of results (default 10)
            project: Filter by project path (optional)

        Returns:
            List of search result dictionaries with keys:
            - title: Formatted title with message type and timestamp
            - content: Message content
            - score: Relevance score (0.0-1.0, higher is better)
            - metadata: Dictionary with session_id, message_type, timestamp, project, snippet
        """
        # Empty query returns no results
        if not query or not query.strip():
            return []

        # Check if database exists
        if not self.db_path.exists():
            logger.debug(f"Database not found at {self.db_path}")
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

        Note: Uses two-query approach (rowids first, then join) to avoid
        SQLite's slow bm25() sorting in Python. The bm25() function is fast
        in the CLI's Rust FTS5 but slow in Python's SQLite.
        """
        # Escape FTS5 special characters: * " - + ( )
        fts_query = query.replace('"', '""')
        fts_query = f'"{fts_query}"'

        try:
            # Step 1: Get rowids and BM25 scores from FTS5 (fast: ~2ms)
            # Project filter applied in Python after fetch since FTS5 result is limited
            cursor.execute(
                "SELECT rowid, bm25(messages_fts) as rank FROM messages_fts WHERE messages_fts MATCH ? ORDER BY rank LIMIT ?",
                [fts_query, str(limit)],
            )
            fts_rows = cursor.fetchall()

            if not fts_rows:
                return []

            # Step 2: Build rowid→score map
            rowid_scores: dict[int, float] = {row["rowid"]: row["rank"] for row in fts_rows}

            # Step 3: Fetch message content by id (fast: ~2ms)
            # Note: messages.id IS the rowid (INTEGER PRIMARY KEY), so we use m.id
            placeholders = ",".join("?" * len(rowid_scores))
            cursor.execute(
                f"""
                SELECT m.id, m.session_id, m.role as message_type,
                       m.content, m.timestamp, s.project_id
                FROM messages m
                LEFT JOIN sessions s ON s.session_key = m.session_id
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
                score = 1.0 - (norm_rank * FTS5_SCORE_SPREAD)  # Range [0.7, 1.0]

                # Apply project filter in Python (FTS5 result is already limited)
                if project and row["project_id"] != project:
                    continue

                results.append(
                    {
                        "title": f"{row['message_type']} - {row['timestamp']}",
                        "content": row["content"],
                        "score": round(score, 3),
                        "metadata": {
                            "session_id": row["session_id"],
                            "message_type": row["message_type"],
                            "timestamp": row["timestamp"],
                            "project": row["project_id"],
                            "snippet": row["content"][:SNIPPET_LENGTH],
                        },
                    }
                )

            return results

        except (sqlite3.Error, IndexError, KeyError) as e:
            logger.debug(f"FTS5 MATCH failed, falling back to LIKE: {e}")
            raise  # Re-raise so caller can catch and try LIKE fallback

    def _like_search(
        self,
        cursor: sqlite3.Cursor,
        query: str,
        limit: int,
        project: str | None,
    ) -> list[SearchResult]:
        """LIKE-based search with position-based ranking.

        Used as fallback when FTS5 is unavailable. Ranks results by:
        1. Exact prefix match (content LIKE 'query%') - highest
        2. Word boundary match (content LIKE '% query %')
        3. Contains match (content LIKE '%query%') - lowest
        """
        import re as re_module
        # Build query with LIKE for keyword search
        sql = """
            SELECT
                m.session_id,
                m.role as message_type,
                m.content,
                m.timestamp,
                s.project_id,
                CASE
                    WHEN m.content LIKE ? THEN 3      -- exact prefix (LIKE_SCORE_EXACT_PREFIX)
                    WHEN m.content LIKE ? THEN 2    -- word boundary (LIKE_SCORE_WORD_BOUNDARY)
                    WHEN m.content LIKE ? THEN 1    -- contains (LIKE_SCORE_CONTAINS)
                    ELSE 0
                END as match_level
            FROM messages m
            LEFT JOIN sessions s ON s.session_key = m.session_id
            WHERE m.content LIKE ?
        """
        # Escape LIKE wildcards in query to treat literal % and _ as characters
        escaped_query = re_module.escape(query)
        prefix_q = f"{escaped_query}%"
        boundary_q = f"% {escaped_query} %"
        contains_q = f"%{escaped_query}%"

        params = [prefix_q, boundary_q, contains_q, contains_q]

        if project:
            # Use INNER JOIN when filtering by project to avoid NULL comparison issues
            # (LEFT JOIN returns NULL for unmatched sessions, and NULL=? is always false)
            sql = sql.replace("LEFT JOIN sessions s", "JOIN sessions s")
            sql += " AND s.project_id = ?"
            params.append(project)

        sql += " ORDER BY match_level DESC, length(m.content) ASC LIMIT ?"
        params.append(str(limit))

        cursor.execute(sql, params)
        rows = cursor.fetchall()

        results = []
        for row in rows:
            # Score based on match level: exact=LIKE_SCORE_EXACT_PREFIX, boundary=LIKE_SCORE_WORD_BOUNDARY, contains=LIKE_SCORE_CONTAINS
            match_level = row["match_level"]
            score = LIKE_SCORE_EXACT_PREFIX if match_level == 3 else (LIKE_SCORE_WORD_BOUNDARY if match_level == 2 else LIKE_SCORE_CONTAINS)

            results.append(
                {
                    "title": f"{row['message_type']} - {row['timestamp']}",
                    "content": row["content"],
                    "score": score,
                    "metadata": {
                        "session_id": row["session_id"],
                        "message_type": row["message_type"],
                        "timestamp": row["timestamp"],
                        "project": row["project_id"],
                        "snippet": row["content"][:200],
                    },
                }
            )
        return results

    def _diversify_results(
        self,
        results: list[SearchResult],
        limit: int,
        max_per_session: int = 2,
    ) -> list[SearchResult]:
        """Diversify search results across sessions.

        Groups results by session_id and limits results per session to ensure
        diverse coverage. Results within each session are ordered by score.

        The algorithm:
        1. Groups results by session_id
        2. Sorts results within each session by score (descending)
        3. Round-robins across sessions, taking up to max_per_session per session
        4. If limit not reached, fills remaining slots with score-sorted fallback

        Note: When limit < number of sessions, some sessions may receive zero
        results (round-robin exhausts before all sessions get a turn).

        Args:
            results: Raw search results from FTS5 or LIKE search
            limit: Maximum number of results to return
            max_per_session: Maximum results to return per session (default 2)

        Returns:
            Diversified list of results with session diversity
        """
        if not results:
            return results

        # Guard: if max_per_session <= 0, return score-sorted results without diversification
        if max_per_session <= 0:
            sorted_results = sorted(results, key=lambda x: x.get("score", 0), reverse=True)
            return sorted_results[:limit]

        # Group by session_id
        session_groups: dict[str, list[SearchResult]] = {}
        for result in results:
            # Normalize metadata: None or non-dict becomes {}
            metadata = result.get("metadata") or {}
            session_id = metadata.get("session_id", "unknown")
            if session_id not in session_groups:
                session_groups[session_id] = []
            session_groups[session_id].append(result)

        # Sort results within each session by score (descending)
        for session_id in session_groups:
            session_groups[session_id].sort(key=lambda x: x.get("score", 0), reverse=True)

        # Interleave results from different sessions
        diversified: list[SearchResult] = []
        session_iters = {
            sid: iter(group[:max_per_session]) for sid, group in session_groups.items()
        }

        # Round-robin through sessions, taking top results per session
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

        # If we still need more results, add remaining results sorted by score
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
        source: str | None = None,
        project: str | None = None,
    ) -> list[SearchResult]:
        """Search chat history for matching messages.

        Args:
            query: Search query string
            source: Data source ("jsonl" or "db", defaults to self.default_source)
            project: Filter by project path (optional)
            limit: Maximum number of results (default 10)

        Returns:
            List of search result dictionaries with keys:
            - session_id: Session identifier
            - message_type: Type of message (assistant/user/system)
            - timestamp: Message timestamp
            - content: Message content
            - project: Project path
            - score: BM25 score (if using db source)
            - snippet: Content snippet
        """
        source = source or self.default_source

        # Route to direct SQLite for db source (alternative path, not default)
        if source == "db":
            return self._search_sqlite_direct(query, limit, project=project)

        # Build command
        cmd = [
            str(self.cli_path),
            "search",
            query,
            "--source",
            source,
            "--limit",
            str(limit),
            "--format",
            "json",
        ]

        if project:
            cmd.extend(["--project", project])

        # Execute CLI
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"claude-history search failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude-history search timed out after 30 seconds")

        # Parse JSON output
        try:
            raw_results = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse claude-history JSON output: {e}") from e

        # Convert to router-expected format
        results = []
        for raw in raw_results:
            # Map claude-history format to SearchResult format
            # Use 0.9 to match CKS priority for chat history queries
            # Chat history is highly relevant for "what did we discuss" queries
            results.append(
                {
                    "title": f"{raw.get('message_type', 'unknown')} - {raw.get('timestamp', '')}",
                    "content": raw.get("content", ""),
                    "score": raw.get("score") or 0.9,
                    "metadata": {
                        "session_id": raw.get("session_id"),
                        "message_type": raw.get("message_type"),
                        "timestamp": raw.get("timestamp"),
                        "project": raw.get("project"),
                        "snippet": raw.get("snippet"),
                    },
                }
            )

        return results

    def get_session(self, session_id: str) -> list[SearchResult]:
        """Get all messages for a specific session.

        Args:
            session_id: Session identifier

        Returns:
            List of message dictionaries
        """
        cmd = [
            str(self.cli_path),
            "get",
            session_id,
            "--format",
            "json",
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"claude-history get failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude-history get timed out after 30 seconds")

        try:
            messages = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Failed to parse claude-history JSON output: {e}") from e

        return messages

    def list_sessions(
        self,
        project: str | None = None,
        sort: str = "recent",
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """List recent sessions.

        Args:
            project: Filter by project path (optional)
            sort: Sort order ("recent", "oldest", "project")
            limit: Maximum number of sessions (default 20)

        Returns:
            List of session summary dictionaries
        """
        cmd = [
            str(self.cli_path),
            "list",
            "--sort",
            sort,
            "--limit",
            str(limit),
        ]

        if project:
            cmd.extend(["--project", project])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"claude-history list failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude-history list timed out after 30 seconds")

        # Parse text output (not JSON for list command)
        sessions = []
        for line in result.stdout.strip().split("\n"):
            if line.startswith("Session "):
                # Parse session ID from line like "Session xxx (N messages):"
                parts = line.split()
                if len(parts) >= 2:
                    session_id = parts[1]
                    sessions.append({"session_id": session_id})

        return sessions

    def stats(self) -> dict[str, Any]:
        """Get database and index statistics.

        Returns:
            Dictionary with keys:
            - total_sessions: Total number of sessions
            - total_messages: Total number of messages
            - indexed_messages: Number of indexed messages
            - projects: List of project paths
            - db_path: Path to SQLite database
            - jsonl_path: Path to JSONL file
        """
        cmd = [str(self.cli_path), "stats"]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30,
                check=True,
            )
        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"claude-history stats failed: {e.stderr}") from e
        except subprocess.TimeoutExpired:
            raise RuntimeError("claude-history stats timed out after 30 seconds")

        # Parse text output
        stats = {}
        for line in result.stdout.strip().split("\n"):
            if ":" in line:
                key, value = line.split(":", 1)
                key = key.strip().lower().replace(" ", "_")
                value = value.strip()
                stats[key] = value

        return stats


# Backend factory
def create_claude_history_backend(**kwargs) -> ClaudeHistoryBackend:
    """Factory function to create a ClaudeHistoryBackend.

    Args:
        **kwargs: Arguments passed to ClaudeHistoryBackend constructor

    Returns:
        Configured ClaudeHistoryBackend instance
    """
    return ClaudeHistoryBackend(**kwargs)


# Backend constants for registration
BACKEND_CLAUDE_HISTORY = {
    "name": "claude-history",
    "class": ClaudeHistoryBackend,
    "factory": create_claude_history_backend,
    "description": "Fast keyword search for Claude Code chat history",
    "source_types": ["chat", "history"],
}
