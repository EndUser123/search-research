#!/usr/bin/env python3
"""Test FrameGuard multi-terminal isolation.

Tests that FrameGuard state is properly isolated per-terminal:
- Different terminals have separate state
- turn_id scoped to terminal
- Concurrent terminals don't interfere
- Terminal ID sanitization for isolation
- Session shared across terminals
- Cross-terminal isolation
- Unique constraint per terminal
- State cleanup scoped to terminal
"""

from __future__ import annotations

import sqlite3
import sys
from concurrent.futures import ThreadPoolExecutor
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


# === Terminal Isolation Tests ===


def test_terminal_isolated_state(tmp_path: Path, monkeypatch) -> None:
    """Test different terminals have separate state."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    terminal_a = "console_a"
    terminal_b = "console_b"
    turn_id = "test_turn_001"

    # Record state for terminal A
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_a,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Terminal A trigger",
        latent_questions=[],
    )

    # Load from terminal A - should find state
    state_a = es.load_frameguard_state(session_id, terminal_a, turn_id)
    assert state_a is not None
    assert state_a["terminal_id"] == terminal_a

    # Load from terminal B - should NOT find state (different terminal)
    state_b = es.load_frameguard_state(session_id, terminal_b, turn_id)
    assert state_b is None


def test_turn_id_per_terminal(tmp_path: Path, monkeypatch) -> None:
    """Test turn_id is globally unique per session, with per-terminal state isolation."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    terminal_a = "console_x"
    terminal_b = "console_y"
    turn_id_a = "turn_x_123"
    turn_id_b = "turn_y_456"

    # Each terminal gets its own turn_id (correct pattern)
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_a,
        turn_id=turn_id_a,
        needs_systemic_frame=True,
        trigger_reason="Terminal A",
        latent_questions=[],
    )

    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_b,
        turn_id=turn_id_b,
        needs_systemic_frame=False,
        trigger_reason="Terminal B",
        latent_questions=[],
    )

    # Both should exist independently with unique turn_ids
    state_a = es.load_frameguard_state(session_id, terminal_a, turn_id_a)
    state_b = es.load_frameguard_state(session_id, terminal_b, turn_id_b)

    assert state_a is not None
    assert state_b is not None
    assert state_a["needs_systemic_frame"] is True
    assert state_b["needs_systemic_frame"] is False
    assert state_a["terminal_id"] == terminal_a
    assert state_b["terminal_id"] == terminal_b


def test_concurrent_terminals(tmp_path: Path, monkeypatch) -> None:
    """Test concurrent terminals don't interfere."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    def record_terminal_state(terminal_id: str) -> bool:
        """Record state for a terminal."""
        turn_id = f"turn_{terminal_id}"
        return es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=f"Trigger for {terminal_id}",
            latent_questions=[],
        )

    # Record state for 5 terminals concurrently
    terminals = [f"console_{i}" for i in range(5)]

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(record_terminal_state, terminals))

    # All should succeed
    assert all(results)

    # Verify each terminal has its own state
    for terminal in terminals:
        turn_id = f"turn_{terminal}"
        state = es.load_frameguard_state(session_id, terminal, turn_id)
        assert state is not None
        assert state["terminal_id"] == terminal


def test_terminal_id_sanitization(tmp_path: Path, monkeypatch) -> None:
    """Test terminal_id sanitized for isolation."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    unsafe_terminal = "console/with:unsafe\\chars"
    turn_id = "turn_sanitize"

    # Record with unsafe terminal_id
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=unsafe_terminal,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Test sanitization",
        latent_questions=[],
    )

    # Load with unsafe terminal_id - should still work (sanitized internally)
    state = es.load_frameguard_state(session_id, unsafe_terminal, turn_id)
    assert state is not None

    # The stored terminal_id should be sanitized
    # Check database directly
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    row = cursor.execute(
        "SELECT terminalid FROM frameguard WHERE sessionid = ? AND turn_id = ?",
        (session_id, turn_id),
    ).fetchone()

    assert row is not None
    # terminal_id should be sanitized (special chars replaced with underscores)
    stored_terminal = row[0]
    assert "/" not in stored_terminal
    assert ":" not in stored_terminal
    assert "\\" not in stored_terminal

    conn.close()


def test_session_shared_across_terminals(tmp_path: Path, monkeypatch) -> None:
    """Test session_id shared, terminal_id unique."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

    # Multiple terminals share same session
    terminals = ["console_1", "console_2", "console_3"]

    for terminal in terminals:
        turn_id = f"turn_{terminal}"
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=f"{terminal} trigger",
            latent_questions=[],
        )

    # All terminals should have state under same session
    # Count records for this session
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    count = cursor.execute(
        "SELECT COUNT(*) FROM frameguard WHERE sessionid = ?", (session_id,)
    ).fetchone()[0]

    conn.close()

    # Should have 3 records (one per terminal)
    assert count == 3


def test_cross_terminal_isolation(tmp_path: Path, monkeypatch) -> None:
    """Test Terminal A doesn't see Terminal B state."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    terminal_a = "terminal_alpha"
    terminal_b = "terminal_beta"
    turn_id_a = "turn_alpha"
    turn_id_b = "turn_beta"

    # Terminal A records state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_a,
        turn_id=turn_id_a,
        needs_systemic_frame=True,
        trigger_reason="Terminal A",
        latent_questions=[],
    )

    # Terminal B records state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_b,
        turn_id=turn_id_b,
        needs_systemic_frame=True,
        trigger_reason="Terminal B",
        latent_questions=[],
    )

    # Terminal A should not see Terminal B's turn
    state_a_from_b = es.load_frameguard_state(session_id, terminal_a, turn_id_b)
    assert state_a_from_b is None

    # Terminal B should not see Terminal A's turn
    state_b_from_a = es.load_frameguard_state(session_id, terminal_b, turn_id_a)
    assert state_b_from_a is None

    # Each terminal should only see its own state
    state_a = es.load_frameguard_state(session_id, terminal_a, turn_id_a)
    state_b = es.load_frameguard_state(session_id, terminal_b, turn_id_b)

    assert state_a is not None
    assert state_b is not None
    assert state_a["terminal_id"] == terminal_a
    assert state_b["terminal_id"] == terminal_b


def test_unique_constraint_per_terminal(tmp_path: Path, monkeypatch) -> None:
    """Test UNIQUE enforced per terminal."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal = "console_unique"
    turn_id = "turn_unique_test"

    # Insert first record
    result1 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="First record",
        latent_questions=[],
    )
    assert result1 is True

    # Insert with same session_id and turn_id (should IGNORE, first record preserved)
    result2 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal,
        turn_id=turn_id,
        needs_systemic_frame=False,  # Different value
        trigger_reason="Second record (ignored)",
        latent_questions=[],
    )
    assert result2 is True  # INSERT OR IGNORE returns success even when ignored

    # Verify only one record exists with first record's values preserved
    state = es.load_frameguard_state(session_id, terminal, turn_id)
    assert state is not None
    assert state["needs_systemic_frame"] is True  # First value preserved
    assert state["trigger_reason"] == "First record"  # First reason preserved


def test_state_cleanup_by_terminal(tmp_path: Path, monkeypatch) -> None:
    """Test cleanup scoped to terminal."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"
    terminal_a = "console_cleanup_a"
    terminal_b = "console_cleanup_b"

    # Create state for both terminals
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_a,
        turn_id="turn_a",
        needs_systemic_frame=True,
        trigger_reason="Terminal A",
        latent_questions=[],
    )

    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_b,
        turn_id="turn_b",
        needs_systemic_frame=True,
        trigger_reason="Terminal B",
        latent_questions=[],
    )

    # Simulate cleanup for terminal A only
    # (In production, this would be a cleanup function)
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Delete only terminal A's state
    cursor.execute(
        "DELETE FROM frameguard WHERE sessionid = ? AND terminalid = ?", (session_id, terminal_a)
    )
    conn.commit()
    conn.close()

    # Terminal A state should be gone
    state_a = es.load_frameguard_state(session_id, terminal_a, "turn_a")
    assert state_a is None

    # Terminal B state should still exist
    state_b = es.load_frameguard_state(session_id, terminal_b, "turn_b")
    assert state_b is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
