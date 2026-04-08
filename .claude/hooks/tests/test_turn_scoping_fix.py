#!/usr/bin/env python3
"""Test DB-backed turn scoping."""

import sys
from pathlib import Path

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

def test_turn_boundary_is_persisted_in_db():
    """Test that start_turn persists a DB-backed turn boundary."""
    from evidence_store import (
        _load_turn_start_event_id,
        append_tool_event,
        get_active_turn,
        start_turn,
    )

    session_id = "11111111-1111-1111-1111-111111111111"
    terminal_id = "test-terminal-456"

    append_tool_event(
        session_id=session_id,
        terminal_id=terminal_id,
        tool_name="Read",
        command="before.py",
    )
    turn_id = start_turn(
        session_id=session_id,
        terminal_id=terminal_id,
        prompt="Test prompt",
    )

    assert get_active_turn(session_id, terminal_id) == turn_id
    boundary = _load_turn_start_event_id(session_id, terminal_id)
    assert boundary is not None
    assert boundary > 0

def test_turn_scoping_filter():
    """Test that load_tool_events_for_context filters by turn marker."""
    from evidence_store import _load_turn_start_event_id, load_tool_events_for_context

    session_id = "22222222-2222-2222-2222-222222222222"
    terminal_id = "test-terminal-012"

    events_all = load_tool_events_for_context(
        session_id=session_id,
        terminal_id=terminal_id,
        use_turn_scoping=False,
    )
    events_turn = load_tool_events_for_context(
        session_id=session_id,
        terminal_id=terminal_id,
        use_turn_scoping=True,
    )

    all_ids = {e["id"] for e in events_all}
    turn_ids = {e["id"] for e in events_turn}
    assert turn_ids.issubset(all_ids)

    turn_start_event_id = _load_turn_start_event_id(session_id, terminal_id)
    if turn_start_event_id is not None:
        for event in events_turn:
            assert event["id"] > turn_start_event_id

if __name__ == "__main__":
    import sys

    import pytest

    sys.exit(pytest.main([__file__, "-q"]))
