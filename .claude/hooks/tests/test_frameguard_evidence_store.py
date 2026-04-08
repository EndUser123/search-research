#!/usr/bin/env python3
"""Test FrameGuard evidence_store helpers.

Tests the 7 FrameGuard helper functions in evidence_store.py:
- record_frameguard_trigger()
- mark_frameguard_handled()
- load_frameguard_state()
- generate_turn_id()
- get_or_create_turn()
- sanitize_terminal_id()
- validate_latent_questions()
"""

from __future__ import annotations

import re
import sqlite3
import sys
from pathlib import Path
from unittest.mock import patch

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


# === validate_latent_questions Tests ===


def test_validate_latent_questions_valid() -> None:
    """Test valid latent_questions structure."""
    valid_questions = [
        {"id": "systemic-coverage", "question": "What is the relationship?"},
        {"id": "neighbor-elements", "question": "What other elements?"},
        {"id": "architectural-context", "question": "What is the broader context?"},
    ]
    assert es.validate_latent_questions(valid_questions) is True


def test_validate_latent_questions_invalid() -> None:
    """Test invalid latent_questions structure."""
    # Not a list - need to cast for type checker
    assert es.validate_latent_questions("not a list") is False  # type: ignore[arg-type]
    assert es.validate_latent_questions(None) is False  # type: ignore[arg-type]
    assert es.validate_latent_questions(123) is False  # type: ignore[arg-type]

    # List but wrong content
    assert es.validate_latent_questions(["not a dict"]) is False
    assert es.validate_latent_questions([{"id": "only-id"}]) is False
    assert es.validate_latent_questions([{"question": "only-question"}]) is False

    # Note: The function only checks key existence, not value types
    # So {"id": 123, "question": "wrong"} is considered valid (has both keys)
    # This is a simple structural validation, not a type validator

    # Empty list is valid (no questions)
    assert es.validate_latent_questions([]) is True


# === sanitize_terminal_id Tests ===


def test_sanitize_terminal_id() -> None:
    """Test terminal_id sanitization."""
    # Empty string returns "unknown"
    assert es.sanitize_terminal_id("") == "unknown"
    assert es.sanitize_terminal_id(None) == "unknown"  # type: ignore[arg-type]

    # Special characters replaced with underscores
    assert es.sanitize_terminal_id("console/abc") == "console_abc"
    assert es.sanitize_terminal_id("console\\abc") == "console_abc"
    assert es.sanitize_terminal_id("console:abc") == "console_abc"

    # Long strings truncated to 80 chars
    long_id = "a" * 100
    result = es.sanitize_terminal_id(long_id)
    assert len(result) == 80
    assert result == "a" * 80

    # Alphanumeric and safe chars preserved
    assert es.sanitize_terminal_id("console_abc-123.test") == "console_abc-123.test"


# === generate_turn_id Tests ===


def test_generate_turn_id_format() -> None:
    """Test turn_id format is timestamp_random."""
    turn_id = es.generate_turn_id()

    # Check format: timestamp_random (8 hex chars)
    pattern = r"^\d+_[a-f0-9]{8}$"
    assert re.match(pattern, turn_id), f"turn_id {turn_id} doesn't match pattern {pattern}"

    # Check uniqueness (generate 100, all different)
    turn_ids = [es.generate_turn_id() for _ in range(100)]
    assert len(set(turn_ids)) == 100, "turn_ids should be unique"


# === get_or_create_turn Tests ===


def test_get_or_create_turn_new(tmp_path: Path, monkeypatch) -> None:
    """Test get_or_create_turn generates new turn_id."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    terminal_id = "console_abc"

    # No existing turn, should generate new
    turn_id = es.get_or_create_turn(session_id, terminal_id)

    assert turn_id is not None
    assert isinstance(turn_id, str)
    assert re.match(r"^\d+_[a-f0-9]{8}$", turn_id)


def test_get_or_create_turn_existing(tmp_path: Path, monkeypatch) -> None:
    """Test get_or_create_turn reuses existing turn_id."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
    terminal_id = "console_xyz"

    turn_id_1 = es.start_turn(session_id=session_id, terminal_id=terminal_id)

    # get_or_create_turn should find the existing turn
    turn_id_2 = es.get_or_create_turn(session_id, terminal_id)

    assert turn_id_2 == turn_id_1


def test_start_turn_persists_active_turn_and_boundary(tmp_path: Path, monkeypatch) -> None:
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "abababab-abab-abab-abab-abababababab"
    terminal_id = "console_turn"

    # Existing event should become the turn boundary.
    assert es.append_tool_event(
        session_id=session_id,
        terminal_id=terminal_id,
        tool_name="Read",
        command="before.py",
    )

    turn_id = es.start_turn(
        session_id=session_id,
        terminal_id=terminal_id,
        prompt="check state",
        transcript_path="P:/tmp/transcript.jsonl",
    )

    assert es.get_active_turn(session_id, terminal_id) == turn_id
    assert es._load_turn_start_event_id(session_id, terminal_id) == 1


# === record_frameguard_trigger Tests ===


def test_record_frameguard_trigger_success(tmp_path: Path, monkeypatch) -> None:
    """Test successful FrameGuard trigger recording."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
    terminal_id = "console_test"
    turn_id = "test_turn_123"
    latent_questions = [
        {"id": "systemic-coverage", "question": "What is the relationship?"},
    ]

    result = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Local existence question inside system context",
        latent_questions=latent_questions,
    )

    assert result is True

    # Verify record was created
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["session_id"] == session_id
    assert state["terminal_id"] == terminal_id
    assert state["turn_id"] == turn_id
    assert state["needs_systemic_frame"] is True
    assert state["trigger_reason"] == "Local existence question inside system context"
    assert state["latent_questions"] == latent_questions
    assert state["handled"] is False


def test_record_frameguard_trigger_db_failure(tmp_path: Path, monkeypatch) -> None:
    """Test record_frameguard_trigger fails open on DB error."""
    _configure_tmp_paths(tmp_path, monkeypatch)

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"
    terminal_id = "console_fail"
    turn_id = "turn_fail"

    # Mock _connect to raise a database error
    import sqlite3

    with patch.object(es, "_connect", side_effect=sqlite3.Error("DB connection failed")):
        result = es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Test",
            latent_questions=[],
        )

    # Should return False on error (fail-open), not raise exception
    assert result is False


def test_record_frameguard_trigger_invalid_latent_questions(tmp_path: Path, monkeypatch) -> None:
    """Test invalid latent_questions are replaced with empty list."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"
    terminal_id = "console_invalid"
    turn_id = "turn_invalid"

    # Invalid latent_questions (not a list)
    result = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Test",
        latent_questions="not a list",  # type: ignore[arg-type]
    )

    # Should succeed but replace with empty list
    assert result is True

    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["latent_questions"] == []


# === mark_frameguard_handled Tests ===


def test_mark_frameguard_handled_success(tmp_path: Path, monkeypatch) -> None:
    """Test successful mark_frameguard_handled."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    terminal_id = "console_mark"
    turn_id = "turn_mark"

    # First create a record
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Test",
        latent_questions=[],
    )

    # Mark as handled
    result = es.mark_frameguard_handled(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        handled=True,
        handled_reason="Systemic frame mentioned in response",
    )

    assert result is True

    # Verify state updated
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["handled"] is True
    assert state["handled_reason"] == "Systemic frame mentioned in response"


def test_mark_frameguard_handled_db_failure(tmp_path: Path, monkeypatch) -> None:
    """Test mark_frameguard_handled fails open on DB error."""
    _configure_tmp_paths(tmp_path, monkeypatch)

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal_id = "console_mark_fail"
    turn_id = "turn_mark_fail"

    # Mock _connect to raise a database error
    with patch.object(es, "_connect", side_effect=sqlite3.Error("DB connection failed")):
        result = es.mark_frameguard_handled(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            handled=True,
            handled_reason="Test",
        )

    # Should return False on error (fail-open), not raise exception
    assert result is False


# === load_frameguard_state Tests ===


def test_load_frameguard_state_success(tmp_path: Path, monkeypatch) -> None:
    """Test successful load_frameguard_state."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"
    terminal_id = "console_load"
    turn_id = "turn_load"
    latent_questions = [
        {"id": "test-id", "question": "Test question?"},
    ]

    # Create a record
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Test trigger",
        latent_questions=latent_questions,
    )

    # Load the state
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)

    assert state is not None
    assert state["session_id"] == session_id
    assert state["terminal_id"] == terminal_id
    assert state["turn_id"] == turn_id
    assert state["needs_systemic_frame"] is True
    assert state["trigger_reason"] == "Test trigger"
    assert state["latent_questions"] == latent_questions
    assert state["handled"] is False
    assert state["handled_reason"] == ""
    assert "id" in state
    assert "created_at" in state


def test_load_frameguard_state_not_found(tmp_path: Path, monkeypatch) -> None:
    """Test load_frameguard_state returns None when not found."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    state = es.load_frameguard_state("66666666-6666-6666-6666-666666666666", "console_x", "turn_x")
    assert state is None


def test_load_frameguard_state_db_failure(tmp_path: Path, monkeypatch) -> None:
    """Test load_frameguard_state fails open on DB error."""
    _configure_tmp_paths(tmp_path, monkeypatch)

    # Don't init_db - should fail-open
    state = es.load_frameguard_state(
        "55555555-5555-5555-5555-555555555555", "console_load_fail", "turn_load_fail"
    )
    assert state is None


# === Schema and Constraint Tests ===


def test_unique_constraint_enforcement(tmp_path: Path, monkeypatch) -> None:
    """Test UNIQUE(sessionid, turn_id) constraint is enforced."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "44444444-4444-4444-4444-444444444444"
    terminal_id = "console_unique"
    turn_id = "turn_unique"

    # Insert first record
    result1 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="First record",
        latent_questions=[],
    )
    assert result1 is True

    # Insert with same session_id and turn_id (should IGNORE, not replace)
    result2 = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=False,
        trigger_reason="Second record (should be ignored)",
        latent_questions=[{"id": "new", "question": "New question?"}],
    )
    assert result2 is True  # INSERT OR IGNORE returns success even when ignored

    # Verify original record is preserved (NOT overwritten)
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is not None
    assert state["needs_systemic_frame"] is True  # Original value preserved
    assert state["trigger_reason"] == "First record"  # Original value preserved
    assert state["latent_questions"] == []  # Original value preserved


def test_turn_id_text_type(tmp_path: Path, monkeypatch) -> None:
    """Test turn_id is TEXT type (not INTEGER) to match hook_ledger."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    # Check schema directly
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get table schema
    cursor.execute("PRAGMA table_info(frameguard)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    # Verify turn_id is TEXT, not INTEGER
    assert "turn_id" in columns
    assert columns["turn_id"] == "TEXT", f"turn_id should be TEXT, got {columns['turn_id']}"

    # Verify sessionid and terminalid are also TEXT
    assert columns["sessionid"] == "TEXT"
    assert columns["terminalid"] == "TEXT"

    conn.close()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
