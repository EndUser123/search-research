#!/usr/bin/env python3
"""
RCA Outcome Recorder

Tracks fix outcomes (RESOLVED/FAILED/PARTIAL/UNKNOWN) for continuous improvement.
This closes the loop on RCA sessions by recording whether fixes actually worked.

Usage:
    from rca.outcome_recorder import record_outcome, get_outcome_summary

    # Record that a fix worked
    record_outcome(
        session_id="rca_1234567890",
        outcome=Outcome.RESOLVED,
        notes="Fix verified - issue no longer occurs",
        verification_method="pytest test_file.py::test_specific_case -v"
    )

    # Record that a fix failed
    record_outcome(
        session_id="rca_1234567890",
        outcome=Outcome.FAILED,
        notes="Fix applied but issue persists - error still occurs",
        verification_method="Manual testing"
    )

Author: CSF Development Team
Version: 1.0.0
"""

from __future__ import annotations

import sqlite3
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path

from .metrics_tracker import get_metrics_tracker

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
class Outcome(Enum):
    """Possible outcomes of a fix attempt."""

    RESOLVED = "resolved"  # Fix worked - issue resolved
    FAILED = "failed"  # Fix didn't work - issue persists
    PARTIAL = "partial"  # Partial improvement - better but not fixed
    UNKNOWN = "unknown"  # Outcome unclear - not yet verified


@dataclass
class OutcomeRecord:
    """A recorded fix outcome."""

    session_id: str
    outcome: str
    recorded_at: str
    notes: str
    verification_method: str | None = None
    time_to_verify_minutes: float | None = None


class OutcomeRecorder:
    """
    Records and queries fix outcomes for RCA sessions.

    This enables:
    - Learning which fixes work and which don't
    - Prioritizing RESOLVED fixes in CHS results
    - Identifying recurring failed attempts
    - CKS auto-extraction from resolved incidents
    """

    def __init__(self, db_path: Path | None = None):
        """
        Initialize outcome recorder.

        Args:
            db_path: Path to metrics database. Defaults to TaskMaster DB.

        """
        if db_path is None:
            db_path = PROJECT_ROOT / ".speckit" / "taskmaster" / "tasks.db"

        self.db_path = db_path
        self._lock = threading.Lock()
        self._init_db()

    def _init_db(self) -> None:
        """Initialize outcome database schema."""
        with sqlite3.connect(self.db_path) as conn:
            # Create outcomes table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS rca_outcomes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    outcome TEXT NOT NULL,
                    recorded_at TEXT NOT NULL,
                    notes TEXT,
                    verification_method TEXT,
                    time_to_verify_minutes REAL,
                    FOREIGN KEY (session_id) REFERENCES rca_sessions(session_id)
                )
            """)

            # Create indexes for efficient queries
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rca_outcomes_session_id
                ON rca_outcomes(session_id)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rca_outcomes_outcome
                ON rca_outcomes(outcome)
            """)

            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_rca_outcomes_recorded_at
                ON rca_outcomes(recorded_at)
            """)

            conn.commit()

    def record_outcome(
        self,
        session_id: str,
        outcome: Outcome,
        notes: str = "",
        verification_method: str | None = None,
    ) -> bool:
        """
        Record the outcome of an RCA session fix.

        Args:
            session_id: The RCA session ID
            outcome: What happened (RESOLVED, FAILED, PARTIAL, UNKNOWN)
            notes: Additional context about the outcome
            verification_method: How the outcome was verified

        Returns:
            True if recorded successfully

        """
        recorded_at = datetime.now().isoformat()

        # Calculate time to verify if session has start time
        time_to_verify = None
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute(
                    "SELECT started_at FROM rca_sessions WHERE session_id = ?",
                    (session_id,),
                )
                row = cursor.fetchone()
                if row:
                    started = datetime.fromisoformat(row[0])
                    recorded = datetime.fromisoformat(recorded_at)
                    time_to_verify = (recorded - started).total_seconds() / 60
        except Exception:
            pass  # Time calculation optional

        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO rca_outcomes (
                    session_id, outcome, recorded_at, notes, verification_method, time_to_verify_minutes
                ) VALUES (?, ?, ?, ?, ?, ?)
            """,
                (
                    session_id,
                    outcome.value,
                    recorded_at,
                    notes,
                    verification_method,
                    time_to_verify,
                ),
            )
            conn.commit()

        # Update metrics tracker with outcome
        try:
            tracker = get_metrics_tracker()
            if outcome == Outcome.RESOLVED:
                tracker.record_verification(session_id, passed=True)
            elif outcome == Outcome.FAILED:
                tracker.record_verification(session_id, passed=False)
        except Exception:
            pass  # Metrics update optional

        return True

    def get_outcome(self, session_id: str) -> OutcomeRecord | None:
        """
        Get the outcome for a specific session.

        Args:
            session_id: The RCA session ID

        Returns:
            OutcomeRecord if found, None otherwise

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT session_id, outcome, recorded_at, notes, verification_method, time_to_verify_minutes
                FROM rca_outcomes
                WHERE session_id = ?
                ORDER BY recorded_at DESC
                LIMIT 1
                """,
                (session_id,),
            )
            row = cursor.fetchone()

            if row:
                return OutcomeRecord(
                    session_id=row[0],
                    outcome=row[1],
                    recorded_at=row[2],
                    notes=row[3],
                    verification_method=row[4],
                    time_to_verify_minutes=row[5],
                )

        return None

    def get_outcomes_by_problem_hash(
        self, problem_hash: str, limit: int = 10
    ) -> list[OutcomeRecord]:
        """
        Get all outcomes for sessions with the same problem hash.

        Useful for seeing what has been tried before for a recurring issue.

        Args:
            problem_hash: Hash of the problem (from metrics_tracker.problem_hash)
            limit: Maximum results to return

        Returns:
            List of OutcomeRecord for this problem

        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT o.session_id, o.outcome, o.recorded_at, o.notes, o.verification_method, o.time_to_verify_minutes
                FROM rca_outcomes o
                JOIN rca_sessions s ON o.session_id = s.session_id
                WHERE s.problem_hash = ?
                ORDER BY o.recorded_at DESC
                LIMIT ?
                """,
                (problem_hash, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    OutcomeRecord(
                        session_id=row[0],
                        outcome=row[1],
                        recorded_at=row[2],
                        notes=row[3],
                        verification_method=row[4],
                        time_to_verify_minutes=row[5],
                    )
                )

        return results

    def get_failed_outcomes(
        self, days: int = 30, limit: int = 20
    ) -> list[OutcomeRecord]:
        """
        Get recent failed fix attempts.

        These are candidates for re-investigation or escalation.

        Args:
            days: Days to look back
            limit: Maximum results

        Returns:
            List of failed OutcomeRecord

        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                """
                SELECT session_id, outcome, recorded_at, notes, verification_method, time_to_verify_minutes
                FROM rca_outcomes
                WHERE outcome = 'failed' AND recorded_at > ?
                ORDER BY recorded_at DESC
                LIMIT ?
                """,
                (cutoff, limit),
            )

            results = []
            for row in cursor.fetchall():
                results.append(
                    OutcomeRecord(
                        session_id=row[0],
                        outcome=row[1],
                        recorded_at=row[2],
                        notes=row[3],
                        verification_method=row[4],
                        time_to_verify_minutes=row[5],
                    )
                )

        return results

    def get_summary(self, days: int = 30) -> dict:
        """
        Get outcome summary statistics.

        Args:
            days: Days to look back

        Returns:
            Dict with summary statistics

        """
        cutoff = (datetime.now() - timedelta(days=days)).isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Total outcomes
            cursor = conn.execute(
                """
                SELECT COUNT(*) FROM rca_outcomes
                WHERE recorded_at > ?
                """,
                (cutoff,),
            )
            total = cursor.fetchone()[0] or 0

            # By outcome type
            cursor = conn.execute(
                """
                SELECT outcome, COUNT(*) FROM rca_outcomes
                WHERE recorded_at > ?
                GROUP BY outcome
                """,
                (cutoff,),
            )

            by_type = {}
            for row in cursor.fetchall():
                by_type[row[0]] = row[1]

            # Average time to verify
            cursor = conn.execute(
                """
                SELECT AVG(time_to_verify_minutes) FROM rca_outcomes
                WHERE recorded_at > ? AND time_to_verify_minutes IS NOT NULL
                """,
                (cutoff,),
            )
            avg_time = cursor.fetchone()[0] or 0.0

        return {
            "total_outcomes": total,
            "resolved": by_type.get("resolved", 0),
            "failed": by_type.get("failed", 0),
            "partial": by_type.get("partial", 0),
            "unknown": by_type.get("unknown", 0),
            "resolution_rate": (
                (by_type.get("resolved", 0) / total * 100) if total > 0 else 0
            ),
            "avg_time_to_verify_minutes": round(avg_time, 1),
        }


# Singleton instance with thread-safe initialization
_recorder_instance: OutcomeRecorder | None = None
_recorder_lock = threading.Lock()


def get_outcome_recorder() -> OutcomeRecorder:
    """Get or create the singleton outcome recorder instance (thread-safe)."""
    global _recorder_instance
    if _recorder_instance is not None:
        return _recorder_instance
    with _recorder_lock:
        if _recorder_instance is None:
            _recorder_instance = OutcomeRecorder()
    return _recorder_instance


def record_outcome(
    session_id: str,
    outcome: Outcome,
    notes: str = "",
    verification_method: str | None = None,
) -> bool:
    """
    Quick function to record fix outcome.

    Args:
        session_id: The RCA session ID
        outcome: What happened (RESOLVED, FAILED, PARTIAL, UNKNOWN)
        notes: Additional context
        verification_method: How outcome was verified

    Returns:
        True if recorded successfully

    """
    return get_outcome_recorder().record_outcome(
        session_id, outcome, notes, verification_method
    )


def get_outcome_summary(days: int = 30) -> dict:
    """
    Quick function to get outcome summary statistics.

    Args:
        days: Days to look back

    Returns:
        Dict with summary statistics

    """
    return get_outcome_recorder().get_summary(days)


if __name__ == "__main__":
    # Self-test
    recorder = OutcomeRecorder()

    # Test recording
    from .metrics_tracker import ProblemType, record_debug_start

    session_id = record_debug_start(
        "Test error for outcome recording",
        ProblemType.ERROR,
    )

    print(f"Created session: {session_id}")

    # Record resolved outcome
    record_outcome(
        session_id,
        Outcome.RESOLVED,
        notes="Test fix worked",
        verification_method="pytest test_outcome.py -v",
    )

    # Get outcome
    outcome = recorder.get_outcome(session_id)
    print(f"Recorded outcome: {outcome}")

    # Get summary
    summary = recorder.get_summary()
    print(f"Summary: {summary}")
