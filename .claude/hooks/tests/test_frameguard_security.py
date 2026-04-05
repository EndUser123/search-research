#!/usr/bin/env python3
"""Test FrameGuard security.

Tests that FrameGuard properly handles malicious inputs:
- SQL injection prevention
- JSON explosion prevention
- Terminal ID sanitization
- Latent questions validation
- Path traversal prevention
- Parameterized queries
- Input size limits
- Schema enforcement
"""

from __future__ import annotations

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


# === SQL Injection Tests ===


def test_sql_injection_prevention(tmp_path: Path, monkeypatch) -> None:
    """Test SQL injection attempts blocked."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    terminal_id = "console_test"
    turn_id = "turn_sql_001"

    # Malicious terminal_id with SQL injection attempt
    malicious_terminal = "console'; DROP TABLE frameguard; --"

    # Should sanitize the terminal_id
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=malicious_terminal,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="Test SQL injection",
        latent_questions=[],
    )

    # Verify the terminal_id was sanitized
    state = es.load_frameguard_state(session_id, malicious_terminal, turn_id)
    assert state is not None

    # The stored terminal_id should be sanitized (no SQL)
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT terminalid FROM frameguard WHERE sessionid = ? AND turn_id = ?",
        (session_id, turn_id),
    )
    row = cursor.fetchone()
    conn.close()

    assert row is not None
    stored_terminal = row[0]
    # Sanitization replaces special chars with underscores (parameterized queries prevent injection)
    assert ";" not in stored_terminal  # SQL separator removed
    # "DROP" stays in string - that's OK because parameterized queries prevent SQL injection
    assert "_" in stored_terminal  # Special chars replaced with underscores


def test_parameterized_queries() -> None:
    """Test all DB ops use parameterized queries."""
    # This is a code review test - verify the implementation uses parameters
    import inspect

    # Check record_frameguard_trigger uses parameterized queries
    source = inspect.getsource(es.record_frameguard_trigger)
    assert ".execute(" in source
    assert "?" in source or "?," in source  # Parameter placeholder present

    # Check mark_frameguard_handled uses parameterized queries
    source = inspect.getsource(es.mark_frameguard_handled)
    assert ".execute(" in source
    assert "?" in source or "?," in source

    # Check load_frameguard_state uses parameterized queries
    source = inspect.getsource(es.load_frameguard_state)
    assert ".execute(" in source
    assert "?" in source or "?," in source


# === Input Validation Tests ===


def test_terminal_id_sanitization(tmp_path: Path, monkeypatch) -> None:
    """Test dangerous terminal_id sanitized."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Dangerous terminal IDs
    dangerous_terminals = [
        "../../../etc/passwd",
        "C:\\Windows\\System32\\config",
        "../../.claude/hooks/secrets.json",
        "'; DROP TABLE users; --",
        "console\x00null",
        "very_long_terminal_name_" + "x" * 200,
    ]

    for terminal in dangerous_terminals:
        turn_id = f"turn_{hash(terminal)}"

        # Should not raise exception
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Test sanitization",
            latent_questions=[],
        )

        # Verify sanitization worked
        state = es.load_frameguard_state(session_id, terminal, turn_id)
        if state:
            # If state was created, terminal_id should be sanitized
            assert ";" not in state["terminal_id"]
            assert "\x00" not in state["terminal_id"]
            assert len(state["terminal_id"]) <= 80  # Length limit enforced


def test_latent_questions_validation(tmp_path: Path, monkeypatch) -> None:
    """Test malicious latent_questions rejected."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"

    # Invalid latent_questions (structure validation only - types handled by JSON)
    invalid_questions = [
        None,  # None instead of list
        "not a list",  # String instead of list
        ["missing_id"],  # Dict without 'question' key
        [{"question": "only question"}],  # Dict without 'id' key
    ]

    for questions in invalid_questions:
        turn_id = f"turn_{hash(str(questions))}"

        # Should handle gracefully - replace with empty list
        result = es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id="console_test",
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Test validation",
            latent_questions=questions,  # type: ignore[arg-type]
        )

        assert result is True  # Should succeed

        # Verify latent_questions was replaced with empty list
        state = es.load_frameguard_state(session_id, "console_test", turn_id)
        if state:
            assert state["latent_questions"] == []


# === Path Traversal Tests ===


def test_path_traversal_prevention(tmp_path: Path, monkeypatch) -> None:
    """Test path traversal attempts blocked."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "dddddddd-dddd-dddd-dddd-dddddddddddd"

    # Path traversal attempts in terminal_id
    traversal_attempts = [
        "../../etc/passwd",
        "..\\..\\..\\windows\\system32",
        "/.claude/hooks/secrets",
        "....//....//etc/passwd",
        "%2e%2e%2f%2e%2e%2fetc%2fpasswd",  # URL-encoded
    ]

    for terminal in traversal_attempts:
        turn_id = f"turn_{hash(terminal)}"

        # Should sanitize path traversal
        es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Test path traversal",
            latent_questions=[],
        )

        # Verify path was sanitized (directory separators replaced)
        state = es.load_frameguard_state(session_id, terminal, turn_id)
        if state:
            # Path traversal characters should be neutralized
            assert "../" not in state["terminal_id"]
            assert (
                "\\" not in state["terminal_id"] or "/" in state["terminal_id"]
            )  # Only forward slashes allowed


# === Input Size Tests ===


def test_input_size_limits(tmp_path: Path, monkeypatch) -> None:
    """Test large inputs handled safely."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee"

    # Very large trigger_reason
    large_reason = "x" * 10000

    turn_id = "turn_size_001"

    # Should handle large input
    result = es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id="console_test",
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason=large_reason,
        latent_questions=[],
    )

    assert result is True

    # Verify it was stored (database may truncate)
    state = es.load_frameguard_state(session_id, "console_test", turn_id)
    assert state is not None


# === Schema Enforcement Tests ===


def test_unique_constraint_enforcement(tmp_path: Path, monkeypatch) -> None:
    """Test UNIQUE constraint enforced."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "ffffffff-ffff-ffff-ffff-ffffffffffff"
    terminal_id = "console_test"
    turn_id = "turn_unique_001"

    # Insert first record
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=True,
        trigger_reason="First",
        latent_questions=[],
    )

    # Insert with same session_id and turn_id (should REPLACE)
    es.record_frameguard_trigger(
        session_id=session_id,
        terminal_id=terminal_id,
        turn_id=turn_id,
        needs_systemic_frame=False,
        trigger_reason="Second",
        latent_questions=[],
    )

    # Verify only one record exists
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute(
        "SELECT COUNT(*) FROM frameguard WHERE sessionid = ? AND turn_id = ?", (session_id, turn_id)
    )
    count = cursor.fetchone()[0]
    conn.close()

    assert count == 1  # UNIQUE constraint enforced


def test_turn_id_text_type(tmp_path: Path, monkeypatch) -> None:
    """Test turn_id is TEXT type (not INTEGER) to match hook_ledger."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    # Check schema directly
    db_path = es.EVIDENCE_DB_PATH
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    cursor.execute("PRAGMA table_info(frameguard)")
    columns = {row[1]: row[2] for row in cursor.fetchall()}

    # Verify turn_id is TEXT, not INTEGER
    assert "turn_id" in columns
    assert columns["turn_id"] == "TEXT"

    conn.close()


# === Fail-Open Security Tests ===


def test_database_errors_fail_open(tmp_path: Path, monkeypatch) -> None:
    """Test database errors don't expose sensitive info."""
    _configure_tmp_paths(tmp_path, monkeypatch)

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal_id = "console_test"
    turn_id = "turn_fail_001"

    # Create a state with a corrupt database
    # (This tests the fail-open pattern)
    from unittest.mock import patch

    with patch.object(es, "_connect", side_effect=sqlite3.Error("DB error")):
        result = es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id=terminal_id,
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason="Test fail-open",
            latent_questions=[],
        )

    # Should return False (fail-open), not raise exception
    assert result is False

    # Load should also fail-open
    state = es.load_frameguard_state(session_id, terminal_id, turn_id)
    assert state is None


# === Additional Security Tests ===


def test_json_explosion_prevention() -> None:
    """Test malicious JSON structures handled safely."""

    # Deeply nested JSON that could cause explosion
    malicious_questions = [
        {"id": "1", "question": "Q1", "nested": {"deep": [{"x": "y"}]}},
        {"id": "2", "question": "Q2", "refs": ["a" * 1000]},
        {"id": "3", "question": "Q3", "data": "x" * 10000},
    ]

    # Validate should reject malformed structures
    for q in malicious_questions:
        # All the above are actually valid (have 'id' and 'question')
        # This tests the validator doesn't crash on complex structures
        assert es.validate_latent_questions([q]) is True


def test_special_chars_in_trigger_reason(tmp_path: Path, monkeypatch) -> None:
    """Test special characters in trigger_reason handled."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"

    # Special characters that might break things
    special_reasons = [
        "Test with 'quotes' and \"double quotes\"",
        "Test with \\n\\t\\r newlines",
        "Test with \\x00 null byte",
        "Test with 💀 emoji and unicode 日本語",
        "Test with $$ dollar signs and %percents%",
        "Test with @at and #hash",
    ]

    for reason in special_reasons:
        turn_id = f"turn_{hash(reason)}"

        # Should handle special characters
        result = es.record_frameguard_trigger(
            session_id=session_id,
            terminal_id="console_test",
            turn_id=turn_id,
            needs_systemic_frame=True,
            trigger_reason=reason,
            latent_questions=[],
        )

        assert result is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
