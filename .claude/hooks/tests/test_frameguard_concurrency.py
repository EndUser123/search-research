#!/usr/bin/env python3
"""Test FrameGuard concurrency and race conditions.

Tests that FrameGuard correctly handles concurrent access:
- WHERE handled = 0 guard prevents duplicate state updates
- INSERT OR IGNORE preserves first record
- Multiple concurrent operations don't corrupt state
- SQLite timeout handles concurrent access
- State consistency under concurrent operations
"""

from __future__ import annotations

import sqlite3
import sys
import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
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


# === Concurrency Tests ===


def test_where_handled_0_guard_prevents_duplicate_updates(tmp_path: Path, monkeypatch) -> None:
    """Test WHERE handled = 0 guard prevents duplicate state updates."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    terminal_id = "console_test"
    turn_id = "turn_concurrent_001"

    # Create initial state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Initial state",
        latent_questions=[],
    )

    # Mark as handled
    result1 = es.mark_frameguard_handled(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        handled=True,
        handled_reason="First mark",
    )
    assert result1 is True

    # Try to mark again with different reason (should be ignored due to WHERE handled = 0)
    result2 = es.mark_frameguard_handled(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        handled=False,  # Different value
        handled_reason="Second mark (should be ignored)",
    )
    assert result2 is True  # Function succeeds but UPDATE affects 0 rows

    # Verify original state is preserved
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["handled"] is True  # First mark preserved
    assert state["handled_reason"] == "First mark"  # First reason preserved


def test_insert_or_ignore_preserves_first_record(tmp_path: Path, monkeypatch) -> None:
    """Test INSERT OR IGNORE preserves first record."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    terminal_id = "console_test"
    turn_id = "turn_ignore_001"

    # Insert first record
    result1 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="First record",
        latent_questions=[{"id": "q1", "question": "First question"}],
    )
    assert result1 is True

    # Try to insert duplicate (should be ignored)
    result2 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=False,  # Different value
        trigger_reason="Second record (should be ignored)",
        latent_questions=[{"id": "q2", "question": "Second question"}],
    )
    assert result2 is True  # Function succeeds but INSERT is ignored

    # Verify first record is preserved
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["needs_systemic_frame"] is True  # First value preserved
    assert state["trigger_reason"] == "First record"  # First reason preserved
    assert state["latent_questions"] == [
        {"id": "q1", "question": "First question"}
    ]  # First questions preserved


def test_concurrent_mark_frameguard_calls_are_idempotent(tmp_path: Path, monkeypatch) -> None:
    """Test concurrent mark_frameguard_handled calls are idempotent."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    terminal_id = "console_test"
    turn_id = "turn_concurrent_mark_001"

    # Create initial state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Concurrent test",
        latent_questions=[],
    )

    # Simulate concurrent calls to mark_frameguard_handled
    results = []
    threads = []

    def mark_handled(thread_id: int):
        result = es.mark_frameguard_handled(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            handled=True,
            handled_reason=f"Thread {thread_id}",
        )
        results.append((thread_id, result))

    # Launch 10 concurrent threads
    for i in range(10):
        thread = threading.Thread(target=mark_handled, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All calls should succeed
    assert len(results) == 10
    for thread_id, result in results:
        assert result is True, f"Thread {thread_id} failed"

    # Only first mark should persist (others affected 0 rows due to WHERE handled = 0)
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["handled"] is True
    # The reason will be from whichever thread ran first (race condition acceptable here)
    assert "Thread" in state["handled_reason"]


def test_concurrent_record_frameguard_trigger_preserves_first(tmp_path: Path, monkeypatch) -> None:
    """Test concurrent record_frameguard_trigger calls preserve first record."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    terminal_id = "console_test"
    turn_id = "turn_concurrent_record_001"

    # Simulate concurrent calls to record_frameguard_trigger
    results = []
    threads = []

    def record_trigger(thread_id: int):
        result = es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=f"Thread {thread_id}",
            latent_questions=[{"id": f"q{thread_id}", "question": f"Question {thread_id}"}],
        )
        results.append((thread_id, result))

    # Launch 10 concurrent threads
    for i in range(10):
        thread = threading.Thread(target=record_trigger, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    # All calls should succeed
    assert len(results) == 10
    for thread_id, result in results:
        assert result is True, f"Thread {thread_id} failed"

    # Only first record should persist (INSERT OR IGNORE)
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["needs_systemic_frame"] is True
    # The reason will be from whichever thread ran first (race condition acceptable here)
    assert "Thread" in state["trigger_reason"]


def test_sqlite_timeout_handles_concurrent_access(tmp_path: Path, monkeypatch) -> None:
    """Test SQLite timeout (30s) handles concurrent access."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    terminal_id = "console_test"

    # Create multiple concurrent operations
    operations = []

    def concurrent_operation(op_id: int):
        turn_id = f"turn_timeout_{op_id:03d}"
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=f"Operation {op_id}",
            latent_questions=[],
        )
        es.mark_frameguard_handled(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            handled=True,
            handled_reason=f"Operation {op_id} complete",
        )
        return op_id

    # Launch 20 concurrent operations
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(concurrent_operation, i) for i in range(20)]
        for future in as_completed(futures):
            op_id = future.result()
            operations.append(op_id)

    # All operations should complete without timeout errors
    assert len(operations) == 20

    # Verify state consistency for all turns
    for op_id in range(20):
        turn_id = f"turn_timeout_{op_id:03d}"
        state = es.load_frameguard_state(session_id, terminal_id, turn_id)
        assert state is not None, f"Turn {turn_id} state not found"
        assert state["handled"] is True


def test_state_consistency_under_concurrent_operations(tmp_path: Path, monkeypatch) -> None:
    """Test state consistency under concurrent mixed operations."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    terminal_id = "console_test"
    turn_id = "turn_consistency_001"

    # Create initial state
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Consistency test",
        latent_questions=[{"id": "q1", "question": "Test question"}],
    )

    results = {"records": 0, "marks": 0, "loads": 0}
    errors = []

    def concurrent_records():
        try:
            for i in range(5):
                es.record_frameguard_trigger(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    turn_id=turn_id,
                    needs_systemic_frame=True,
                    trigger_reason=f"Record {i}",
                    latent_questions=[],
                )
                results["records"] += 1
        except Exception as e:
            errors.append(("record", e))

    def concurrent_marks():
        try:
            for i in range(5):
                es.mark_frameguard_handled(
                    session_id=session_id,
                    terminal_id=terminal_id,
                    turn_id=turn_id,
                    handled=True,
                    handled_reason=f"Mark {i}",
                )
                results["marks"] += 1
        except Exception as e:
            errors.append(("mark", e))

    def concurrent_loads():
        try:
            for i in range(5):
                state = es.load_frameguard_state(session_id, terminal_id, turn_id)
                if state:
                    results["loads"] += 1
        except Exception as e:
            errors.append(("load", e))

    # Launch all concurrent operations
    threads = [
        threading.Thread(target=concurrent_records),
        threading.Thread(target=concurrent_marks),
        threading.Thread(target=concurrent_loads),
    ]

    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # No errors should occur (database should handle concurrent access)
    assert len(errors) == 0, f"Errors occurred: {errors}"

    # At least some operations should succeed
    assert results["records"] > 0 or results["marks"] > 0 or results["loads"] > 0

    # Final state should be consistent
    final_state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert final_state is not None
    # handled should be True (from marks) or False (if no marks completed)
    assert isinstance(final_state["handled"], bool)


def test_unique_constraint_enforces_single_record_per_turn(tmp_path: Path, monkeypatch) -> None:
    """Test UNIQUE(sessionid, turn_id) constraint enforces single record per turn."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal_id = "console_test"
    turn_id = "turn_unique_001"

    # Insert first record
    result1 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="First",
        latent_questions=[],
    )
    assert result1 is True

    # Try to insert duplicate (INSERT OR IGNORE should prevent it)
    result2 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=False,
        trigger_reason="Second",
        latent_questions=[],
    )
    assert result2 is True

    # Verify only one record exists
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) FROM frameguard WHERE sessionid = ? AND turn_id = ?", (session_id, turn_id)
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1, f"Expected 1 record, found {count}"


def test_terminal_isolation_preserves_concurrent_safety(tmp_path: Path, monkeypatch) -> None:
    """Test terminal_id isolation preserves concurrent safety."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"

    # Create state for multiple terminals concurrently
    results = {}
    threads = []

    def create_terminal_state(terminal_suffix: str):
        terminal_id = f"console_{terminal_suffix}"
        turn_id = f"turn_terminal_{terminal_suffix}"

        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=f"Terminal {terminal_suffix}",
            latent_questions=[],
        )

        state = es.load_frameguard_state(session_id, terminal_id, turn_id)
        results[terminal_suffix] = state is not None

    # Launch concurrent operations for 5 different terminals
    terminals = ["A", "B", "C", "D", "E"]
    for term in terminals:
        thread = threading.Thread(target=create_terminal_state, args=(term,))
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    # All terminal operations should succeed
    assert len(results) == 5
    for term, success in results.items():
        assert success, f"Terminal {term} failed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
