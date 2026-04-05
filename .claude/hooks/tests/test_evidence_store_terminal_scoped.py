"""Test terminal-scoped event loading in evidence_store.py

This test suite verifies TASK-001: load_tool_events_for_context function.

Key behaviors tested:
1. Filters by BOTH session_id AND terminal_id
2. Returns empty list if terminal_id is empty (fail-safe)
3. Reuses existing ordering and limits from load_tool_events()
4. Multi-terminal isolation (two terminals same session don't leak events)
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


def test_load_tool_events_for_context_empty_terminal_id(tmp_path: Path, monkeypatch) -> None:
    """Test that empty terminal_id returns empty list (fail-safe)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "11111111-1111-1111-1111-111111111111"

    # Add event for terminal_1
    assert es.append_tool_event(session_id, "terminal_1", "Read", command="test.py")

    # Query with empty terminal_id should return empty list
    events_empty = es.load_tool_events_for_context(session_id, "", limit=10)
    assert events_empty == []

    events_none = es.load_tool_events_for_context(session_id, None, limit=10)  # type: ignore
    assert events_none == []

    events_whitespace = es.load_tool_events_for_context(session_id, "   ", limit=10)
    assert events_whitespace == []


def test_load_tool_events_for_context_multi_terminal_isolation(tmp_path: Path, monkeypatch) -> None:
    """Test that two terminals in same session return only their own events."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "22222222-2222-2222-2222-222222222222"

    # Terminal 1 events
    assert es.append_tool_event(session_id, "terminal_1", "Read", command="a.py")
    assert es.append_tool_event(session_id, "terminal_1", "Grep", command="rg foo")

    # Terminal 2 events
    assert es.append_tool_event(session_id, "terminal_2", "Read", command="b.py")
    assert es.append_tool_event(session_id, "terminal_2", "Edit", command="edit c.py")

    # Query terminal_1 should only get terminal_1 events
    events_t1 = es.load_tool_events_for_context(session_id, "terminal_1", limit=10)
    assert [e["name"] for e in events_t1] == ["Read", "Grep"]
    assert all(e["terminal_id"] == "terminal_1" for e in events_t1)

    # Query terminal_2 should only get terminal_2 events
    events_t2 = es.load_tool_events_for_context(session_id, "terminal_2", limit=10)
    assert [e["name"] for e in events_t2] == ["Read", "Edit"]
    assert all(e["terminal_id"] == "terminal_2" for e in events_t2)


def test_load_tool_events_for_context_session_isolation(tmp_path: Path, monkeypatch) -> None:
    """Test that different sessions don't leak events."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_1 = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
    session_2 = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"

    # Same terminal, different sessions
    assert es.append_tool_event(session_1, "console_1", "Read", command="s1.py")
    assert es.append_tool_event(session_2, "console_1", "Read", command="s2.py")

    # Query session_1 should only get session_1 events
    events_s1 = es.load_tool_events_for_context(session_1, "console_1", limit=10)
    assert len(events_s1) == 1
    assert events_s1[0]["command"] == "s1.py"
    assert events_s1[0]["session_id"] == session_1

    # Query session_2 should only get session_2 events
    events_s2 = es.load_tool_events_for_context(session_2, "console_1", limit=10)
    assert len(events_s2) == 1
    assert events_s2[0]["command"] == "s2.py"
    assert events_s2[0]["session_id"] == session_2


def test_load_tool_events_for_context_chronological_order(tmp_path: Path, monkeypatch) -> None:
    """Test that events are returned in chronological order (oldest first)."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "33333333-3333-3333-3333-333333333333"

    # Add events in sequence
    assert es.append_tool_event(session_id, "terminal_a", "Read", command="1.py")
    assert es.append_tool_event(session_id, "terminal_a", "Grep", command="rg foo")
    assert es.append_tool_event(session_id, "terminal_a", "Edit", command="edit 2.py")

    events = es.load_tool_events_for_context(session_id, "terminal_a", limit=10)
    assert [e["name"] for e in events] == ["Read", "Grep", "Edit"]
    assert [e["command"] for e in events] == ["1.py", "rg foo", "edit 2.py"]


def test_load_tool_events_for_context_limit_respected(tmp_path: Path, monkeypatch) -> None:
    """Test that limit parameter is respected."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "44444444-4444-4444-4444-444444444444"

    # Add 5 events
    for i in range(5):
        assert es.append_tool_event(session_id, "terminal_x", "Bash", command=f"cmd{i}.py")

    # Query with limit=3 should return only 3 most recent events
    events = es.load_tool_events_for_context(session_id, "terminal_x", limit=3)
    assert len(events) == 3
    # Should be the last 3 events (cmd2, cmd3, cmd4) in chronological order
    assert [e["command"] for e in events] == ["cmd2.py", "cmd3.py", "cmd4.py"]


def test_load_tool_events_for_context_within_seconds_ttl(tmp_path: Path, monkeypatch) -> None:
    """Test that within_seconds parameter filters old events."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "55555555-5555-5555-5555-555555555555"

    # Add event
    assert es.append_tool_event(session_id, "terminal_y", "Read", command="old.py")

    # Query with TTL=0 should exclude all events (since they're older than 0 seconds)
    events = es.load_tool_events_for_context(session_id, "terminal_y", limit=10, within_seconds=0)
    assert len(events) == 0


def test_load_tool_events_for_context_invalid_session_id(tmp_path: Path, monkeypatch) -> None:
    """Test that invalid session_id returns empty list."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    # Invalid session IDs should return empty list
    events_invalid = es.load_tool_events_for_context("not-a-uuid", "terminal_1", limit=10)
    assert events_invalid == []

    events_empty = es.load_tool_events_for_context("", "terminal_1", limit=10)
    assert events_empty == []


def test_load_tool_events_for_context_event_structure(tmp_path: Path, monkeypatch) -> None:
    """Test that returned events have correct structure and types."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "66666666-6666-6666-6666-666666666666"

    assert es.append_tool_event(
        session_id,
        "terminal_z",
        "Bash",
        command="echo hello",
        cwd="/tmp",
        output_excerpt="hello",
        success=True
    )

    events = es.load_tool_events_for_context(session_id, "terminal_z", limit=10)
    assert len(events) == 1

    event = events[0]
    assert isinstance(event["id"], int)
    assert event["name"] == "Bash"
    assert event["command"] == "echo hello"
    assert event["cwd"] == "/tmp"
    assert event["output"] == "hello"
    assert event["session_id"] == session_id
    assert event["terminal_id"] == "terminal_z"
    assert event["success"] is True
    assert isinstance(event["timestamp"], str)


def test_load_tool_events_for_context_no_events_returns_empty_list(tmp_path: Path, monkeypatch) -> None:
    """Test that querying with no matching events returns empty list."""
    _configure_tmp_paths(tmp_path, monkeypatch)
    es.init_db()

    session_id = "77777777-7777-7777-7777-777777777777"

    # No events added, should return empty list
    events = es.load_tool_events_for_context(session_id, "terminal_nothing", limit=10)
    assert events == []
