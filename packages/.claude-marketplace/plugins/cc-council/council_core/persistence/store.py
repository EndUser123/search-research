"""Persistence layer for council sessions.

Uses SQLite for durable storage of session state,
drafts, reviews, and synthesis results.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
from typing import Any

from council_core.contracts.types import (
    CouncilState,
    DraftResponse,
    ReviewResult,
    SessionMetadata,
    SynthesisResult,
)


@contextmanager
def get_connection(db_path: Path):
    """Get a SQLite connection with proper isolation."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_schema(db_path: Path) -> None:
    """Initialize the database schema for council sessions."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()

        # Sessions table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                prompt TEXT NOT NULL,
                state TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                gating_reason TEXT,
                failure_reason TEXT,
                total_rounds INTEGER DEFAULT 0,
                models_used TEXT DEFAULT '[]',
                duration_ms INTEGER DEFAULT 0
            )
        """)

        # Drafts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS drafts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                metadata TEXT DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Reviews table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                model TEXT NOT NULL,
                role TEXT NOT NULL,
                rankings TEXT NOT NULL,
                critiques TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Synthesis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS synthesis (
                session_id TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                contradiction_notes TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)

        # Indexes for performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_drafts_session
            ON drafts(session_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_reviews_session
            ON reviews(session_id)
        """)

        conn.commit()


class CouncilStore:
    """Persistent storage for council sessions."""

    def __init__(self, db_path: Path) -> None:
        """Initialize the store with a database path."""
        self.db_path = db_path
        init_schema(db_path)

    def create_session(self, metadata: SessionMetadata) -> None:
        """Create a new session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sessions (
                    session_id, prompt, state, created_at, updated_at,
                    gating_reason, failure_reason, total_rounds, models_used, duration_ms
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                metadata.session_id,
                metadata.prompt,
                metadata.state.value,
                metadata.created_at.isoformat(),
                metadata.updated_at.isoformat(),
                metadata.gating_reason,
                metadata.failure_reason,
                metadata.total_rounds,
                json.dumps(metadata.models_used),
                metadata.duration_ms,
            ))

    def update_session_state(
        self,
        session_id: str,
        state: CouncilState,
        failure_reason: str | None = None,
    ) -> None:
        """Update session state and optionally failure reason."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            updates = ["state = ?", "updated_at = ?"]
            params = [state.value, datetime.now().isoformat()]

            if failure_reason:
                updates.append("failure_reason = ?")
                params.append(failure_reason)

            params.append(session_id)
            cursor.execute(f"""
                UPDATE sessions SET {", ".join(updates)}
                WHERE session_id = ?
            """, params)

    def increment_round(self, session_id: str) -> None:
        """Increment the round counter for a session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sessions
                SET total_rounds = total_rounds + 1,
                    updated_at = ?
                WHERE session_id = ?
            """, (datetime.now().isoformat(), session_id))

    def add_model_used(self, session_id: str, model: str) -> None:
        """Add a model to the list of models used in a session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT models_used FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if row:
                models = json.loads(row["models_used"])
                if model not in models:
                    models.append(model)
                    cursor.execute("""
                        UPDATE sessions
                        SET models_used = ?, updated_at = ?
                        WHERE session_id = ?
                    """, (json.dumps(models), datetime.now().isoformat(), session_id))

    def store_draft(self, session_id: str, draft: DraftResponse) -> int:
        """Store a draft response, returning its database ID."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO drafts (
                    session_id, model, role, content, metadata, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                draft.model,
                draft.role,
                draft.content,
                json.dumps(draft.metadata),
                draft.created_at.isoformat(),
            ))
            return cursor.lastrowid

    def store_review(self, session_id: str, review: ReviewResult) -> int:
        """Store a review result, returning its database ID."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO reviews (
                    session_id, model, role, rankings, critiques, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                review.model,
                review.role,
                json.dumps(review.rankings),
                json.dumps(review.critiques),
                review.created_at.isoformat(),
            ))
            return cursor.lastrowid

    def store_synthesis(self, session_id: str, synthesis: SynthesisResult) -> None:
        """Store the final synthesis result."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT OR REPLACE INTO synthesis (
                    session_id, model, role, content, contradiction_notes, created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
            """, (
                session_id,
                synthesis.model,
                synthesis.role,
                synthesis.content,
                json.dumps(synthesis.contradiction_notes),
                synthesis.created_at.isoformat(),
            ))

    def get_session(self, session_id: str) -> SessionMetadata | None:
        """Retrieve session metadata."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM sessions WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return SessionMetadata(
                session_id=row["session_id"],
                prompt=row["prompt"],
                state=CouncilState(row["state"]),
                created_at=datetime.fromisoformat(row["created_at"]),
                updated_at=datetime.fromisoformat(row["updated_at"]),
                gating_reason=row["gating_reason"],
                failure_reason=row["failure_reason"],
                total_rounds=row["total_rounds"],
                models_used=json.loads(row["models_used"]),
                duration_ms=row["duration_ms"],
            )

    def get_drafts(self, session_id: str) -> list[DraftResponse]:
        """Retrieve all drafts for a session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM drafts WHERE session_id = ? ORDER BY id
            """, (session_id,))
            return [
                DraftResponse(
                    model=row["model"],
                    role=row["role"],
                    content=row["content"],
                    metadata=json.loads(row["metadata"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

    def get_reviews(self, session_id: str) -> list[ReviewResult]:
        """Retrieve all reviews for a session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM reviews WHERE session_id = ? ORDER BY id
            """, (session_id,))
            return [
                ReviewResult(
                    model=row["model"],
                    role=row["role"],
                    rankings=json.loads(row["rankings"]),
                    critiques=json.loads(row["critiques"]),
                    created_at=datetime.fromisoformat(row["created_at"]),
                )
                for row in cursor.fetchall()
            ]

    def get_synthesis(self, session_id: str) -> SynthesisResult | None:
        """Retrieve synthesis for a session."""
        with get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT * FROM synthesis WHERE session_id = ?
            """, (session_id,))
            row = cursor.fetchone()
            if not row:
                return None

            return SynthesisResult(
                model=row["model"],
                role=row["role"],
                content=row["content"],
                contradiction_notes=json.loads(row["contradiction_notes"]),
                created_at=datetime.fromisoformat(row["created_at"]),
            )