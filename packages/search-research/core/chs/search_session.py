"""Search Session - Conversational Search Continuum.

This module provides session-based context management for search operations,
enabling conversational search with follow-up queries and result referencing.

Usage:
    session = SearchSession()
    query_id = session.add_search("python async patterns", results)
    follow_up = session.follow_up(query_id, 3)  # Tell me more about result #3
    summary = session.get_context_summary()
    exported = session.export_to_cks()
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import tempfile
import uuid
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class SearchSession:
    """Manages search context for conversational search continuum.

    Tracks queries and results across a search session, enabling:
    - Reference to previous results by number (#3)
    - Follow-up queries on specific results
    - Session summary of search path and knowledge
    - Export to CKS for persistence

    Attributes:
        max_history: Maximum number of queries to store (default: 5)
        max_results: Maximum results per query to store (default: 10)
        queries: List of query dictionaries with timestamps
        results: Dict mapping query_id to stored results
        created_at: Session creation timestamp
    """

    def __init__(
        self, max_history: int = 5, max_results: int = 10, session_id: str | None = None
    ) -> None:
        """Initialize a new search session.

        Args:
            max_history: Maximum number of queries to keep in history
            max_results: Maximum number of results to store per query
            session_id: Optional session ID (auto-generated if not provided)
        """
        self.max_history = max_history
        self.max_results = max_results
        self.session_id = session_id or self._generate_session_id()
        self.queries: list[dict[str, Any]] = []
        self.results: dict[str, list[dict[str, Any]]] = {}
        self.created_at = datetime.now(UTC)

    def _generate_session_id(self) -> str:
        """Generate a unique session ID.

        Uses WT_SESSION environment variable if available, otherwise generates UUID.
        """
        if wt_session := os.getenv("WT_SESSION"):
            return f"sess-{wt_session}"
        return f"sess-{uuid.uuid4().hex[:12]}"

    def add_search(self, query: str, results: list[dict[str, Any]]) -> str:
        """Add a search to the session history.

        Args:
            query: The search query text
            results: List of search result dictionaries

        Returns:
            The query_id for this search (can be used for follow-up)
        """
        query_id = f"q-{len(self.queries) + 1}-{self.session_id}"
        limited_results = results[: self.max_results]
        query_entry = {
            "query_id": query_id,
            "query": query,
            "timestamp": datetime.now(UTC).isoformat(),
            "result_count": len(limited_results),
        }
        self.queries.append(query_entry)
        self.results[query_id] = limited_results
        if len(self.queries) > self.max_history:
            oldest_query = self.queries.pop(0)
            old_query_id = oldest_query["query_id"]
            self.results.pop(old_query_id, None)
        return query_id

    def follow_up(
        self, query_id: str | None = None, reference_id: int | None = None
    ) -> dict[str, Any]:
        """Get detailed information about a specific result.

        Implements "tell me more about result #3" functionality.

        Args:
            query_id: The query ID (defaults to most recent if None)
            reference_id: The result number (1-indexed) from that query

        Returns:
            Dictionary with full result details and context, or error dict
        """
        if query_id is None:
            if not self.queries:
                return {"error": "No queries in session"}
            query_id = self.queries[-1]["query_id"]
        if query_id not in self.results:
            return {"error": f"Query ID {query_id} not found"}
        results = self.results[query_id]
        if reference_id is None:
            return {
                "query_id": query_id,
                "query": self._get_query_text(query_id),
                "results": results,
                "count": len(results),
            }
        idx = reference_id - 1
        if idx < 0 or idx >= len(results):
            return {"error": f"Result #{reference_id} not found", "available": len(results)}
        result = results[idx]
        return {
            "query_id": query_id,
            "query": self._get_query_text(query_id),
            "reference_id": reference_id,
            "result": result,
            "context": self._build_context_for_result(query_id, result),
        }

    def _get_query_text(self, query_id: str) -> str:
        """Get the original query text for a query_id."""
        for q in self.queries:
            if q["query_id"] == query_id:
                return q["query"]
        return ""

    def _build_context_for_result(self, query_id: str, result: dict[str, Any]) -> dict[str, Any]:
        """Build contextual information about a result."""
        return {
            "query_position": self._get_query_position(query_id),
            "related_queries": self._get_related_queries(query_id),
            "session_age_seconds": (datetime.now(UTC) - self.created_at).total_seconds(),
        }

    def _get_query_position(self, query_id: str) -> int:
        """Get position of query in session (1-indexed)."""
        for i, q in enumerate(self.queries):
            if q["query_id"] == query_id:
                return i + 1
        return 0

    def _get_related_queries(self, query_id: str) -> list[str]:
        """Get list of related query texts (excluding current)."""
        return [q["query"] for q in self.queries if q["query_id"] != query_id]

    def get_context_summary(self) -> dict[str, Any]:
        """Generate a summary of the search session.

        Shows:
        - Number of queries performed
        - Total results accumulated
        - Topics covered (extracted from queries)
        - Session duration

        Returns:
            Dictionary containing session summary
        """
        total_results = sum(len(r) for r in self.results.values())
        topics = self._extract_topics()
        duration = (datetime.now(UTC) - self.created_at).total_seconds()
        return {
            "session_id": self.session_id,
            "query_count": len(self.queries),
            "total_results": total_results,
            "topics": topics,
            "duration_seconds": duration,
            "created_at": self.created_at.isoformat(),
            "queries": [
                {
                    "id": q["query_id"],
                    "query": q["query"],
                    "results": q["result_count"],
                    "timestamp": q["timestamp"],
                }
                for q in self.queries
            ],
        }

    def _extract_topics(self) -> list[str]:
        """Extract unique topics from query texts.

        Simple extraction: splits on common words and returns significant terms.
        """
        stop_words = {
            "the",
            "a",
            "an",
            "and",
            "or",
            "but",
            "in",
            "on",
            "at",
            "to",
            "for",
            "of",
            "with",
            "by",
            "from",
            "how",
            "what",
            "when",
            "where",
            "why",
            "which",
            "who",
            "is",
            "are",
            "was",
            "were",
            "be",
            "been",
            "being",
            "have",
            "has",
            "had",
            "do",
            "does",
            "did",
            "will",
            "would",
            "could",
            "should",
            "may",
            "might",
            "must",
            "can",
            "about",
            "into",
            "through",
            "during",
            "before",
            "after",
            "above",
            "below",
            "between",
            "tell",
            "me",
            "more",
            "show",
            "get",
            "find",
            "search",
            "result",
        }
        topics: set[str] = set()
        for q in self.queries:
            words = re.findall("\\b\\w+\\b", q["query"].lower())
            for word in words:
                if len(word) > 3 and word not in stop_words:
                    topics.add(word)
        return sorted(topics)[:10]

    def export_to_cks(self, cks_db_path: str | None = None) -> dict[str, Any]:
        """Export session knowledge to CKS storage.

        Args:
            cks_db_path: Path to CKS database (auto-detected if None)

        Returns:
            Dict with export status and details
        """
        if cks_db_path is None:
            cks_db_path = self._find_cks_database()
        if cks_db_path is None or not Path(cks_db_path).exists():
            return {"success": False, "error": "CKS database not found", "path": cks_db_path}
        try:
            conn = sqlite3.connect(cks_db_path)
            conn.execute(
                "\n                CREATE TABLE IF NOT EXISTS search_session_exports (\n                    id INTEGER PRIMARY KEY AUTOINCREMENT,\n                    session_id TEXT NOT NULL,\n                    exported_at INTEGER NOT NULL,\n                    query_count INTEGER NOT NULL,\n                    result_count INTEGER NOT NULL,\n                    topics TEXT NOT NULL,\n                    data_json TEXT NOT NULL,\n                    UNIQUE(session_id)\n                )\n            "
            )
            summary = self.get_context_summary()
            conn.execute(
                "\n                INSERT OR REPLACE INTO search_session_exports\n                (session_id, exported_at, query_count, result_count, topics, data_json)\n                VALUES (?, ?, ?, ?, ?, ?)\n            ",
                (
                    self.session_id,
                    int(datetime.now(UTC).timestamp()),
                    summary["query_count"],
                    summary["total_results"],
                    json.dumps(summary["topics"]),
                    json.dumps(summary),
                ),
            )
            conn.commit()
            conn.close()
            return {
                "success": True,
                "session_id": self.session_id,
                "path": cks_db_path,
                "queries": summary["query_count"],
                "results": summary["total_results"],
            }
        except Exception as e:
            return {"success": False, "error": str(e), "path": cks_db_path}

    def _find_cks_database(self) -> str | None:
        """Find the CKS database path.

        Uses config.CKS_DB_PATH as the authoritative single source of truth.
        Falls back to ~/.csf/cks.db only if config path doesn't exist.
        """
        # Import here to avoid circular imports and to pick up env-var overrides
        import sys as _sys
        from pathlib import Path as _Path

        _project_root = _Path(__file__).resolve().parents[2]  # P:\\\\packages/search-research
        if str(_project_root) not in _sys.path:
            _sys.path.insert(0, str(_project_root))

        try:
            from core.config import config as _cfg

            authoritative = _cfg.CKS_DB_PATH
            if authoritative and _Path(authoritative).exists():
                return authoritative
        except Exception:
            pass

        # Fallback: ~/.csf/cks.db only (not cwd-dependent)
        fallback = _Path.home() / ".csf" / "cks.db"
        if fallback.exists():
            return str(fallback)

        return None

    def cleanup(self) -> None:
        """Clean up session data after export.

        Clears all stored queries and results from memory.
        """
        self.queries.clear()
        self.results.clear()

    def parse_followup_query(self, query: str) -> dict[str, Any]:
        """Parse a follow-up query for result references.

        Detects patterns like:
        - "tell me more about result 3"
        - "show #5"
        - "more about result #2"

        Args:
            query: The follow-up query text

        Returns:
            Dict with 'reference_id' (int or None) and 'clean_query' (str)
        """
        patterns = ["result\\s*#?(\\d+)", "#(\\d+)", "number\\s*(\\d+)", "item\\s*(\\d+)"]
        reference_id = None
        clean_query = query
        for pattern in patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                reference_id = int(match.group(1))
                clean_query = re.sub(pattern, "", query, flags=re.IGNORECASE).strip()
                break
        return {"reference_id": reference_id, "clean_query": clean_query}

    def to_dict(self) -> dict[str, Any]:
        """Convert session to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "max_history": self.max_history,
            "max_results": self.max_results,
            "queries": self.queries,
            "results": {k: self._serialize_results(v) for k, v in self.results.items()},
            "created_at": self.created_at.isoformat(),
        }

    def _serialize_results(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Serialize results for JSON storage.

        Handles non-serializable types like numpy arrays.
        """
        serialized = []
        for result in results:
            serialized_result = {}
            for key, value in result.items():
                try:
                    json.dumps(value)
                    serialized_result[key] = value
                except (TypeError, ValueError):
                    serialized_result[key] = str(value)
            serialized.append(serialized_result)
        return serialized

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SearchSession:
        """Create a SearchSession from a dictionary."""
        session = cls(
            max_history=data.get("max_history", 5),
            max_results=data.get("max_results", 10),
            session_id=data.get("session_id"),
        )
        session.queries = data.get("queries", [])
        session.results = data.get("results", {})
        if created_at := data.get("created_at"):
            session.created_at = datetime.fromisoformat(created_at)
        return session


class SearchSessionManager:
    """Manages multiple search sessions.

    Provides session persistence and retrieval across CLI invocations.
    """

    def __init__(self, storage_dir: str | None = None) -> None:
        """Initialize the session manager.

        Args:
            storage_dir: Directory to store session files (auto-detected if None)
        """
        if storage_dir is None:
            storage_dir = str(Path(tempfile.gettempdir()) / "search_sessions")
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self._active_session: SearchSession | None = None

    @property
    def active_session(self) -> SearchSession | None:
        """Get the currently active session."""
        return self._active_session

    def create_session(
        self, max_history: int = 5, max_results: int = 10, session_id: str | None = None
    ) -> SearchSession:
        """Create a new search session."""
        session = SearchSession(
            max_history=max_history, max_results=max_results, session_id=session_id
        )
        self._active_session = session
        return session

    def get_or_create_session(self, session_id: str | None = None) -> SearchSession:
        """Get existing session or create new one."""
        if session_id and self._active_session and (self._active_session.session_id == session_id):
            return self._active_session
        if session_id:
            loaded = self.load_session(session_id)
            if loaded:
                self._active_session = loaded
                return loaded
        return self.create_session(session_id=session_id)

    def save_session(self, session: SearchSession) -> bool:
        """Save a session to disk."""
        try:
            session_file = self.storage_dir / f"{session.session_id}.json"
            with open(session_file, "w") as f:
                json.dump(session.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load_session(self, session_id: str) -> SearchSession | None:
        """Load a session from disk."""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if not session_file.exists():
                return None
            with open(session_file) as f:
                data = json.load(f)
            return SearchSession.from_dict(data)
        except Exception:
            return None

    def list_sessions(self) -> list[dict[str, Any]]:
        """List all stored sessions."""
        sessions = []
        for session_file in self.storage_dir.glob("*.json"):
            try:
                with open(session_file) as f:
                    data = json.load(f)
                sessions.append(
                    {
                        "session_id": data.get("session_id", session_file.stem),
                        "query_count": len(data.get("queries", [])),
                        "created_at": data.get("created_at"),
                        "file": str(session_file),
                    }
                )
            except Exception:
                continue
        return sorted(sessions, key=lambda x: x.get("created_at", ""))

    def delete_session(self, session_id: str) -> bool:
        """Delete a stored session."""
        try:
            session_file = self.storage_dir / f"{session_id}.json"
            if session_file.exists():
                session_file.unlink()
                return True
            return False
        except Exception:
            return False

    def cleanup_old_sessions(self, max_age_hours: int = 24) -> int:
        """Clean up sessions older than max_age_hours."""
        import time

        cutoff = time.time() - max_age_hours * 3600
        deleted = 0
        for session_file in self.storage_dir.glob("*.json"):
            if session_file.stat().st_mtime < cutoff:
                try:
                    session_file.unlink()
                    deleted += 1
                except Exception:
                    pass
        return deleted
