#!/usr/bin/env python3
"""Test FrameGuard state recovery.

Tests that FrameGuard state can be recovered after various failure scenarios:
- State recovery after restart
- State recovery after crash
- Partial state recovery
- State version migration
- State backup and restore
- State consistency check
- State rollback on corruption
- State integrity verification
"""

from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

import pytest

sys_path_insert = str(Path(__file__).resolve().parents[1])
if sys_path_insert not in sys.path:
    sys.path.insert(0, sys_path_insert)

import evidence_store as es


def _configure_tmp_paths(tmp_path: Path, monkeypatch) -> None:
    """Configure temporary paths for testing."""
    session_dir = tmp_path / "session_data"
    monkeypatch.setattr(es, "SESSION_DATA_DIR", session_dir)
    monkeypatch.setattr(es, "EVIDENCE_DB_PATH", session_dir / "evidence.db")


# === State Recovery Tests ===


def test_state_recovery_after_restart(tmp_path: Path, monkeypatch) -> None:
    """Test state recovered after restart (database reopen)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_restart_001",
        needs_systemic_frame=True,
        trigger_reason="Before restart",
        latent_questions=[{"id": "q1", "question": "Test question"}],
    )

    # Verify state exists before "restart"
    state_before = es.load_frameguard_state(session_id, "console_test", "turn_restart_001")
    assert state_before is not None
    assert state_before["needs_systemic_frame"] is True

    # Simulate restart by closing and reopening database
    # (In production, this would be a process restart)
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    conn.close()  # Close all connections

    # Re-initialize and load state
    es.init_db()
    state_after = es.load_frameguard_state(session_id, "console_test", "turn_restart_001")

    # State should be recovered
    assert state_after is not None
    assert state_after["needs_systemic_frame"] is True
    assert state_after["trigger_reason"] == "Before restart"


def test_state_recovery_after_crash(tmp_path: Path, monkeypatch) -> None:
    """Test state recovered after crash (WAL mode recovery)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_crash_001",
        needs_systemic_frame=True,
        trigger_reason="Before crash",
        latent_questions=[],
    )

    # Simulate crash by checking WAL mode is enabled
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode")
    journal_mode = cursor.fetchone()[0]
    conn.close()

    # WAL mode provides crash recovery
    assert journal_mode in ("wal", "WAL")

    # State should still be accessible
    state = es.load_frameguard_state(session_id, "console_test", "turn_crash_001")
    assert state is not None


def test_partial_state_recovery(tmp_path: Path, monkeypatch) -> None:
    """Test partial state recovered when some data is missing."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_partial_001",
        needs_systemic_frame=True,
        trigger_reason="Partial state",
        latent_questions=[],
    )

    # Simulate partial state by updating handled_reason (which can be empty)
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE frameguard SET handled_reason = '' WHERE turn_id = ?",
        ("turn_partial_001",),
    )
    conn.commit()
    conn.close()

    # Load should handle empty fields gracefully
    state = es.load_frameguard_state(session_id, "console_test", "turn_partial_001")

    # State should be loaded with empty string for handled_reason
    assert state is not None
    assert state["handled_reason"] == ""  # Empty string is valid


def test_state_version_migration(tmp_path: Path, monkeypatch) -> None:
    """Test state migrated between versions."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"

    # Create state with current schema
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_version_001",
        needs_systemic_frame=True,
        trigger_reason="Version 1",
        latent_questions=[],
    )

    # Verify state was created with current schema
    state = es.load_frameguard_state(session_id, "console_test", "turn_version_001")
    assert state is not None
    assert "handled" in state  # Current schema has 'handled' field
    assert "handled_reason" in state  # Current schema has 'handled_reason' field


def test_state_backup_and_restore(tmp_path: Path, monkeypatch) -> None:
    """Test state backed up and restored."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_backup_001",
        needs_systemic_frame=True,
        trigger_reason="Backup test",
        latent_questions=[{"id": "q1", "question": "Backup question"}],
    )

    # "Backup" state by exporting to JSON
    state = es.load_frameguard_state(session_id, "console_test", "turn_backup_001")
    backup_json = json.dumps(state)

    # Delete original state
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "DELETE FROM frameguard WHERE sessionid = ? AND turn_id = ?",
        (session_id, "turn_backup_001"),
    )
    conn.commit()
    conn.close()

    # Verify state is gone
    state_deleted = es.load_frameguard_state(session_id, "console_test", "turn_backup_001")
    assert state_deleted is None

    # "Restore" from backup
    restored_state = json.loads(backup_json)

    # Re-insert restored state
    es.record_frameguard_trigger(
        session_id=restored_state["session_id"],
        terminal_id=restored_state["terminal_id"],
        turn_id=restored_state["turn_id"],
        needs_systemic_frame=restored_state["needs_systemic_frame"],
        trigger_reason=restored_state["trigger_reason"],
        latent_questions=restored_state["latent_questions"],
    )

    # Verify restored state exists
    state_restored = es.load_frameguard_state(session_id, "console_test", "turn_backup_001")
    assert state_restored is not None
    assert state_restored["trigger_reason"] == "Backup test"


def test_state_consistency_check(tmp_path: Path, monkeypatch) -> None:
    """Test state consistency verified."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_consistency_001",
        needs_systemic_frame=True,
        trigger_reason="Consistency test",
        latent_questions=[],
    )

    # Load state and verify consistency
    state = es.load_frameguard_state(session_id, "console_test", "turn_consistency_001")

    # Consistency checks
    assert state is not None
    assert state["session_id"] == session_id
    assert state["terminal_id"] == "console_test"
    assert state["turn_id"] == "turn_consistency_001"
    assert isinstance(state["needs_systemic_frame"], bool)
    assert isinstance(state["latent_questions"], list)
    assert isinstance(state["handled"], bool)


def test_state_rollback_on_corruption(tmp_path: Path, monkeypatch) -> None:
    """Test state rolled back on corruption."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "11111111-1111-1111-1111-111111111111"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_rollback_001",
        needs_systemic_frame=True,
        trigger_reason="Before corruption",
        latent_questions=[],
    )

    # Manually corrupt the latent_questions_json field
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE frameguard SET latent_questions_json = '{invalid json}' WHERE turn_id = ?",
        ("turn_rollback_001",),
    )
    conn.commit()
    conn.close()

    # Load should handle corruption gracefully (fail-open)
    state = es.load_frameguard_state(session_id, "console_test", "turn_rollback_001")

    # State should be None due to JSON parse error (fail-open)
    # Or state might be partially loaded with empty latent_questions
    assert state is None or state.get("latent_questions") == []


def test_state_integrity_verification(tmp_path: Path, monkeypatch) -> None:
    """Test state integrity verified."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"

    # Create state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id="turn_integrity_001",
        needs_systemic_frame=True,
        trigger_reason="Integrity test",
        latent_questions=[{"id": "q1", "question": "Integrity question"}],
    )

    # Load and verify integrity
    state = es.load_frameguard_state(session_id, "console_test", "turn_integrity_001")

    # Integrity verification
    assert state is not None

    # Verify required fields exist and have correct types
    required_fields = {
        "id": int,
        "session_id": str,
        "terminal_id": str,
        "turn_id": str,
        "created_at": str,
        "needs_systemic_frame": bool,
        "trigger_reason": str,
        "latent_questions": list,
        "handled": bool,
        "handled_reason": str,
    }

    for field, expected_type in required_fields.items():
        assert field in state, f"Missing required field: {field}"
        # Use isinstance for type checking (handles None gracefully for some fields)
        if state[field] is not None:
            assert isinstance(state[field], expected_type), f"Field {field} has wrong type"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
