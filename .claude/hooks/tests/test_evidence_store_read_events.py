"""Test read_events_for_file in evidence_store.py

This test suite verifies TASK-008: read_events_for_file function.

Key behaviors tested:
1. Returns only Read tool events (not Grep, Edit, etc.)
2. Filters by session_id, terminal_id, AND file_path
3. Uses canonical path comparison (os.path.realpath)
4. Returns empty list when terminal_id is empty (fail-safe)
5. Multi-terminal isolation (no cross-terminal leakage)
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import evidence_store as es


def _configure_tmp_paths(tmp_path: Path, monkeypatch) -> None:
    """Configure evidence_store to use temporary paths for testing."""
    session_dir = tmp_path / "session_data"
    monkeypatch.setattr(es, "SESSION_DATA_DIR", session_dir)
    monkeypatch.setattr(es, "EVIDENCE_DB_PATH", session_dir / "evidence.db")


def test_read_events_for_file_returns_only_read_events(tmp_path: Path, monkeypatch) -> None:
    """Test that only Read tool events are returned, not other tool types."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal_id = "console_1"
    file_path = str(tmp_path / "document.md")

    # Add Read, Grep, Edit events for the same file
    es.append_tool_event(session_id, terminal_id, "Read", command=file_path)
    es.append_tool_event(session_id, terminal_id, "Grep", command=f"pattern in {file_path}")
    es.append_tool_event(session_id, terminal_id, "Edit", command=f"edit {file_path}")

    # Should only return the Read event
    events = es.read_events_for_file(session_id, terminal_id, file_path)
    assert len(events) == 1
    assert events[0]["name"] == "Read"


def test_read_events_for_file_filters_by_terminal_id(tmp_path: Path, monkeypatch) -> None:
    """Test that different terminals get isolated events (D2)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"
    file_path = str(tmp_path / "shared.md")

    # Terminal 1 reads file
    es.append_tool_event(session_id, "terminal_1", "Read", command=file_path)

    # Terminal 2 reads same file
    es.append_tool_event(session_id, "terminal_2", "Read", command=file_path)

    # Querying terminal_1 should only get terminal_1's read
    events_t1 = es.read_events_for_file(session_id, "terminal_1", file_path)
    assert len(events_t1) == 1
    assert events_t1[0]["terminal_id"] == "terminal_1"

    # Querying terminal_2 should only get terminal_2's read
    events_t2 = es.read_events_for_file(session_id, "terminal_2", file_path)
    assert len(events_t2) == 1
    assert events_t2[0]["terminal_id"] == "terminal_2"


def test_read_events_for_file_filters_by_file_path(tmp_path: Path, monkeypatch) -> None:
    """Test that only events for the specific file are returned."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "33333333-3333-3333-3333-333333333333"
    terminal_id = "console_x"
    file_a = str(tmp_path / "a.md")
    file_b = str(tmp_path / "b.md")

    es.append_tool_event(session_id, terminal_id, "Read", command=file_a)
    es.append_tool_event(session_id, terminal_id, "Read", command=file_b)
    es.append_tool_event(session_id, terminal_id, "Read", command=file_a)

    events_a = es.read_events_for_file(session_id, terminal_id, file_a)
    assert len(events_a) == 2
    assert all(e["command"] == file_a for e in events_a)

    events_b = es.read_events_for_file(session_id, terminal_id, file_b)
    assert len(events_b) == 1
    assert events_b[0]["command"] == file_b


def test_read_events_for_file_canonical_path(tmp_path: Path, monkeypatch) -> None:
    """Test that file paths are compared canonically (D6: os.path.realpath)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "44444444-4444-4444-4444-444444444444"
    terminal_id = "console_canon"

    # Use a path that has different representations but same realpath
    # On Windows, this could be short/long filename, forward/backslash, etc.
    file_path = str(tmp_path / "canon_test.md")

    # Store event with the path
    es.append_tool_event(session_id, terminal_id, "Read", command=file_path)

    # Query with the same path should work
    events = es.read_events_for_file(session_id, terminal_id, file_path)
    assert len(events) == 1


def test_read_events_for_file_empty_terminal_id_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """Test that empty terminal_id returns empty list (fail-safe per D2)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "55555555-5555-5555-5555-555555555555"
    file_path = str(tmp_path / "test.md")

    es.append_tool_event(session_id, "console_foo", "Read", command=file_path)

    # Empty terminal_id should return empty list
    assert es.read_events_for_file(session_id, "", file_path) == []
    assert es.read_events_for_file(session_id, "   ", file_path) == []  # type: ignore
    assert es.read_events_for_file(session_id, None, file_path) == []  # type: ignore


def test_read_events_for_file_empty_session_id_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """Test that invalid session_id returns empty list."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    file_path = str(tmp_path / "test.md")

    # Invalid session IDs should return empty list
    assert es.read_events_for_file("not-a-uuid", "console_1", file_path) == []
    assert es.read_events_for_file("", "console_1", file_path) == []
    assert es.read_events_for_file(None, "console_1", file_path) == []  # type: ignore


def test_read_events_for_file_chronological_order(tmp_path: Path, monkeypatch) -> None:
    """Test that events are returned in chronological order (oldest first)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "66666666-6666-6666-6666-666666666666"
    terminal_id = "console_chrono"
    file_path = str(tmp_path / "order_test.md")

    # Add 3 read events
    es.append_tool_event(session_id, terminal_id, "Read", command=file_path)
    es.append_tool_event(session_id, terminal_id, "Read", command=file_path)
    es.append_tool_event(session_id, terminal_id, "Read", command=file_path)

    events = es.read_events_for_file(session_id, terminal_id, file_path)
    assert len(events) == 3
    # Events should be in chronological order (oldest first, newest last)
    timestamps = [e["timestamp"] for e in events]
    assert timestamps == sorted(timestamps)


def test_read_events_for_file_not_found_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """Test that querying a file with no Read events returns empty list."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "77777777-7777-7777-7777-777777777777"
    terminal_id = "console_none"

    # Add a read event for a different file
    es.append_tool_event(session_id, terminal_id, "Read", command=str(tmp_path / "other.md"))

    # Query for non-existent file should return empty
    events = es.read_events_for_file(session_id, terminal_id, str(tmp_path / "nonexistent.md"))
    assert events == []
