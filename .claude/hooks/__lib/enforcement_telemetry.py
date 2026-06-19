#!/usr/bin/env python3
"""
Enforcement Telemetry Module

Logs enforcement tier triggers to diagnostics.db for compliance analysis.

Purpose: Track advisory vs strict enforcement effectiveness to prevent
the "advisory warnings are ignored 80%+ of the time" failure mode.

Tables:
- enforcement_events: Records each enforcement trigger with tier, skill, outcome

Query examples:
    -- Advisory compliance rate by skill
    SELECT skill_name,
           SUM(CASE WHEN behavior_changed = 1 THEN 1 ELSE 0 END) * 100.0 / COUNT(*) as compliance_rate
    FROM enforcement_events
    WHERE tier = 'advisory'
    GROUP BY skill_name;

    -- Warning fatigue detection (same warning shown multiple times without behavior change)
    SELECT skill_name, COUNT(*) as warning_count
    FROM enforcement_events
    WHERE tier = 'advisory' AND behavior_changed = 0
    GROUP BY session_id, skill_name
    HAVING COUNT(*) > 3;
"""

from __future__ import annotations

import json
import logging
import os
import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from threading import Lock
from typing import Any

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Thread-safe singleton
_db_lock = Lock()
_db_path: Path | None = None

ENFORCEMENT_RETENTION_DAYS = int(os.environ.get("CC_ENFORCEMENT_RETENTION_DAYS", "30"))
_CLEANUP_STATE_FILE = (
    Path(os.environ.get("CSF_HOOKS_STATE_DIR", "P:/.claude/hooks/state"))
    / "enforcement_last_cleanup.txt"
)


def _get_db_path() -> Path:
    """Get or create the diagnostics database path."""
    global _db_path
    if _db_path is not None:
        return _db_path

    # Use same location as other diagnostics
    base = Path(os.environ.get("CSF_DIAGNOSTICS_DIR", "P:/.claude/hooks/logs/diagnostics"))
    base.mkdir(parents=True, exist_ok=True)
    _db_path = base / "diagnostics.db"
    return _db_path


def _open_db(db_path) -> sqlite3.Connection:
    """Open diagnostics DB with WAL mode and busy timeout."""
    conn = sqlite3.connect(str(db_path), timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=5000")
    return conn


def _ensure_table() -> None:
    """Create enforcement_events table if it doesn't exist."""
    db_path = _get_db_path()
    with _db_lock:
        try:
            conn = _open_db(db_path)
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS enforcement_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    session_id TEXT NOT NULL,
                    terminal_id TEXT,
                    skill_name TEXT NOT NULL,
                    tier TEXT NOT NULL CHECK (tier IN ('strict', 'advisory', 'none')),
                    outcome TEXT NOT NULL CHECK (outcome IN ('blocked', 'warned', 'allowed', 'bypassed')),
                    behavior_changed INTEGER DEFAULT 0,
                    trigger_context TEXT,
                    metadata TEXT
                )
            """)
            # Index for compliance queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_enforcement_skill_tier
                ON enforcement_events(skill_name, tier)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_enforcement_session
                ON enforcement_events(session_id)
            """)
            conn.commit()
            conn.close()
        except sqlite3.Error:
            logger.exception("Failed to create enforcement_events table")


def log_enforcement_event(
    session_id: str,
    skill_name: str,
    tier: str,
    outcome: str,
    terminal_id: str | None = None,
    behavior_changed: bool = False,
    trigger_context: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> bool:
    """
    Log an enforcement tier trigger event.

    Args:
        session_id: Current session identifier
        skill_name: Name of the skill being enforced
        tier: Enforcement tier ('strict', 'advisory', 'none')
        outcome: Result of enforcement ('blocked', 'warned', 'allowed', 'bypassed')
        terminal_id: Optional terminal identifier
        behavior_changed: Whether the user/AI changed behavior after enforcement
        trigger_context: What triggered the enforcement (e.g., 'missing_skill_call')
        metadata: Additional JSON metadata

    Returns:
        True if logged successfully, False otherwise
    """
    if tier not in ("strict", "advisory", "none"):
        logger.warning(f"Invalid tier: {tier}")
        return False
    if outcome not in ("blocked", "warned", "allowed", "bypassed"):
        logger.warning(f"Invalid outcome: {outcome}")
        return False

    _ensure_table()
    db_path = _get_db_path()

    timestamp = datetime.now(timezone.utc).isoformat()

    with _db_lock:
        try:
            conn = _open_db(db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO enforcement_events
                (timestamp, session_id, terminal_id, skill_name, tier, outcome, behavior_changed, trigger_context, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    timestamp,
                    session_id,
                    terminal_id,
                    skill_name,
                    tier,
                    outcome,
                    1 if behavior_changed else 0,
                    trigger_context,
                    json.dumps(metadata) if metadata else None,
                ),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            logger.exception("Failed to log enforcement event")
            return False


def get_advisory_compliance_rate(skill_name: str | None = None, days: int = 7) -> dict[str, Any]:
    """
    Get compliance rate for advisory warnings.

    Returns:
        Dict with 'rate' (0-100), 'total_warnings', 'behavior_changes', 'by_skill'
    """
    _ensure_table()
    db_path = _get_db_path()

    with _db_lock:
        try:
            conn = _open_db(db_path)
            cursor = conn.cursor()

            if skill_name:
                cursor.execute(
                    """
                    SELECT COUNT(*), SUM(behavior_changed)
                    FROM enforcement_events
                    WHERE tier = 'advisory' AND skill_name = ?
                    AND timestamp >= datetime('now', ? || ' days')
                """,
                    (skill_name, f"-{days}"),
                )
            else:
                cursor.execute(
                    """
                    SELECT COUNT(*), SUM(behavior_changed)
                    FROM enforcement_events
                    WHERE tier = 'advisory'
                    AND timestamp >= datetime('now', ? || ' days')
                """,
                    (f"-{days}",),
                )

            row = cursor.fetchone()
            total = row[0] or 0
            changes = row[1] or 0

            # Get breakdown by skill
            cursor.execute(
                """
                SELECT skill_name, COUNT(*), SUM(behavior_changed)
                FROM enforcement_events
                WHERE tier = 'advisory'
                AND timestamp >= datetime('now', ? || ' days')
                GROUP BY skill_name
                ORDER BY COUNT(*) DESC
            """,
                (f"-{days}",),
            )

            by_skill = {}
            for skill_row in cursor.fetchall():
                by_skill[skill_row[0]] = {
                    "total": skill_row[1],
                    "compliant": skill_row[2] or 0,
                    "rate": (skill_row[2] or 0) * 100.0 / skill_row[1] if skill_row[1] > 0 else 0,
                }

            conn.close()

            return {
                "rate": (changes * 100.0 / total) if total > 0 else 0,
                "total_warnings": total,
                "behavior_changes": changes,
                "by_skill": by_skill,
            }
        except sqlite3.Error:
            logger.exception("Failed to get compliance rate")
            return {"rate": 0, "total_warnings": 0, "behavior_changes": 0, "by_skill": {}}


def detect_warning_fatigue(session_id: str, threshold: int = 3) -> list[dict[str, Any]]:
    """
    Detect skills showing warning fatigue (same warning shown multiple times without behavior change).

    Args:
        session_id: Session to check
        threshold: Number of warnings before fatigue is detected (default 3)

    Returns:
        List of dicts with 'skill_name', 'warning_count' for fatigued skills
    """
    _ensure_table()
    db_path = _get_db_path()

    with _db_lock:
        try:
            conn = _open_db(db_path)
            cursor = conn.cursor()

            cursor.execute(
                """
                SELECT skill_name, COUNT(*) as warning_count
                FROM enforcement_events
                WHERE tier = 'advisory'
                AND behavior_changed = 0
                AND session_id = ?
                GROUP BY skill_name
                HAVING COUNT(*) >= ?
                ORDER BY warning_count DESC
            """,
                (session_id, threshold),
            )

            results = [{"skill_name": row[0], "warning_count": row[1]} for row in cursor.fetchall()]
            conn.close()
            return results
        except sqlite3.Error:
            logger.exception("Failed to detect warning fatigue")
            return []


def reset_db_path() -> None:
    """
    Reset the cached database path.

    For test isolation only. Clears the global _db_path so subsequent
    calls to _get_db_path() will re-read CSF_DIAGNOSTICS_DIR.
    """
    global _db_path
    _db_path = None


def _maybe_cleanup_enforcement_events() -> None:
    """Prune old enforcement events, at most once per 24 hours."""
    try:
        if _CLEANUP_STATE_FILE.exists():
            last = datetime.fromisoformat(_CLEANUP_STATE_FILE.read_text().strip())
            if (datetime.now(timezone.utc) - last).total_seconds() < 86400:
                return
    except Exception:
        pass

    _ensure_table()
    db_path = _get_db_path()
    cutoff = (datetime.now(timezone.utc) - timedelta(days=ENFORCEMENT_RETENTION_DAYS)).isoformat()
    with _db_lock:
        try:
            conn = _open_db(db_path)
            conn.execute("DELETE FROM enforcement_events WHERE timestamp < ?", (cutoff,))
            conn.commit()
            conn.close()
            _CLEANUP_STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
            _CLEANUP_STATE_FILE.write_text(datetime.now(timezone.utc).isoformat())
        except Exception:
            pass


try:
    _maybe_cleanup_enforcement_events()
except Exception:
    pass


# Self-test
if __name__ == "__main__":
    print("=== Enforcement Telemetry Self-Test ===\n")

    # Test 1: Log an advisory event
    test_session = "test_session_123"
    success = log_enforcement_event(
        session_id=test_session,
        skill_name="test_skill",
        tier="advisory",
        outcome="warned",
        behavior_changed=False,
        trigger_context="test_trigger",
    )
    print(f"1. Log advisory event: {'PASS' if success else 'FAIL'}")

    # Test 2: Log a strict event
    success = log_enforcement_event(
        session_id=test_session,
        skill_name="test_skill_strict",
        tier="strict",
        outcome="blocked",
        behavior_changed=True,
        trigger_context="missing_skill_call",
    )
    print(f"2. Log strict event: {'PASS' if success else 'FAIL'}")

    # Test 3: Get compliance rate
    rate = get_advisory_compliance_rate()
    print(f"3. Get compliance rate: {rate['rate']:.1f}% ({rate['total_warnings']} warnings)")

    # Test 4: Detect warning fatigue
    # Add more warnings to trigger fatigue
    for _ in range(5):
        log_enforcement_event(
            session_id=test_session,
            skill_name="fatigued_skill",
            tier="advisory",
            outcome="warned",
            behavior_changed=False,
        )

    fatigue = detect_warning_fatigue(test_session, threshold=3)
    print(f"4. Detect warning fatigue: {len(fatigue)} skills with fatigue")
    for f in fatigue:
        print(f"   - {f['skill_name']}: {f['warning_count']} warnings")

    # Test 5: Invalid tier should fail gracefully
    success = log_enforcement_event(
        session_id=test_session, skill_name="test", tier="invalid_tier", outcome="allowed"
    )
    print(f"5. Invalid tier rejected: {'PASS' if not success else 'FAIL'}")

    print("\n=== All tests complete ===")
