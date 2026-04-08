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
        default_source: str = "jsonl",
    ):
        """Initialize the Claude history backend.

        Args:
            root_paths: Not used for chat history (kept for BaseLocalBackend compatibility)
            exclude_patterns: Not used for chat history (kept for BaseLocalBackend compatibility)
            cli_path: Path to claude-history.exe (defaults to P:/packages/claude-history/target/release/claude-history.exe)
            db_path: Path to SQLite database (defaults to P:/__csf/data/chat_history.db)
            default_source: Default data source ("jsonl" or "db")
        """
        super().__init__(root_paths, exclude_patterns)
        if cli_path is None:
            cli_path = "P:/packages/claude-history/target/release/claude-history.exe"
        if db_path is None:
            db_path = "P:/__csf/data/chat_history.db"

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
            - score: Relevance score (fixed at 0.5 for LIKE queries)
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

                # Build query with LIKE for keyword search
                # Note: Using LIKE instead of FTS5 MATCH for compatibility
                # FTS5 index may not be built (indexed_messages: 0 from CLI stats)
                sql = """
                    SELECT
                        session_id,
                        role as message_type,
                        content,
                        timestamp,
                        project
                    FROM messages
                    WHERE content LIKE ?
                """
                params = [f"%{query}%"]

                # Add project filter if specified
                if project:
                    sql += " AND project = ?"
                    params.append(project)

                # Add limit
                sql += " LIMIT ?"
                params.append(str(limit))

                cursor.execute(sql, params)
                rows = cursor.fetchall()

                # Convert to SearchResult format
                results = []
                for row in rows:
                    results.append(
                        {
                            "title": f"{row['message_type']} - {row['timestamp']}",
                            "content": row["content"],
                            "score": 0.9,  # Match CKS priority for chat history
                            "metadata": {
                                "session_id": row["session_id"],
                                "message_type": row["message_type"],
                                "timestamp": row["timestamp"],
                                "project": row["project"],
                                "snippet": row["content"][:200],  # First 200 chars as snippet
                            },
                        }
                    )

                return results

        except sqlite3.Error as e:
            logger.debug(f"SQLite search failed: {e}")
            return []
        except Exception as e:
            logger.debug(f"Unexpected error during SQLite search: {e}")
            return []

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
