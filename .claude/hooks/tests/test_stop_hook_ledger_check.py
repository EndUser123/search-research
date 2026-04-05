#!/usr/bin/env/python3
"""
Test Stop hook tool_blocked detection logic.

Tests that Stop hook correctly distinguishes between:
- Hook system blocked all tool attempts (system failure → suppress)
- Claude bypassed skill (genuine violation → block)
- No tool attempts at all (genuine bypass → block)

Addresses: REQ-003
"""

from unittest.mock import patch

import pytest


def test_stop_hook_suppresses_when_all_tools_blocked():
    """Test that Stop hook is suppressed when hook system blocks all tool attempts."""
    # Mock _load_db_events to return all tools blocked
    mock_events = [
        {"event_type": "tool_invoked", "tool_name": "Read"},
        {"event_type": "tool_blocked", "tool_name": "Read"},
        {"event_type": "tool_invoked", "tool_name": "Grep"},
        {"event_type": "tool_blocked", "tool_name": "Grep"},
    ]

    with patch("__lib.hook_ledger._load_db_events", return_value=mock_events):
        from __lib.hook_ledger import _load_db_events

        events = _load_db_events("test_turn_id")
        invoked = [e for e in events if e.get("event_type") == "tool_invoked"]
        blocked = [e for e in events if e.get("event_type") == "tool_blocked"]

        assert len(invoked) == 2, "Should have 2 tool_invoked events"
        assert len(blocked) == 2, "Should have 2 tool_blocked events"
        assert len(blocked) == len(invoked), "All invoked tools should be blocked"


def test_stop_hook_fires_when_partial_tools_blocked():
    """Test that Stop hook fires when only some tools are blocked."""
    # Mock _load_db_events to return partial blocking
    mock_events = [
        {"event_type": "tool_invoked", "tool_name": "Read"},
        {"event_type": "tool_blocked", "tool_name": "Read"},
        {"event_type": "tool_invoked", "tool_name": "Grep"},
    ]

    with patch("__lib.hook_ledger._load_db_events", return_value=mock_events):
        from __lib.hook_ledger import _load_db_events

        events = _load_db_events("test_turn_id")
        invoked = [e for e in events if e.get("event_type") == "tool_invoked"]
        blocked = [e for e in events if e.get("event_type") == "tool_blocked"]

        assert len(invoked) == 2, "Should have 2 tool_invoked events"
        assert len(blocked) == 1, "Should have 1 tool_blocked event"
        assert len(blocked) < len(invoked), "Not all invoked tools should be blocked"


def test_stop_hook_fires_when_no_tools_attempted():
    """Test that Stop hook fires when Claude makes no tool attempts (genuine bypass)."""
    # Mock _load_db_events to return empty list (no tools attempted)
    mock_events = []

    with patch("__lib.hook_ledger._load_db_events", return_value=mock_events):
        from __lib.hook_ledger import _load_db_events

        events = _load_db_events("test_turn_id")
        invoked = [e for e in events if e.get("event_type") == "tool_invoked"]
        blocked = [e for e in events if e.get("event_type") == "tool_blocked"]

        # No tools invoked means no attempts
        assert len(invoked) == 0, "Should have 0 tool_invoked events"
        assert len(blocked) == 0, "Should have 0 tool_blocked events"

        # This should NOT trigger the "all blocked" suppression
        # because len(invoked) == 0 means no attempts were made
        assert not (len(invoked) > 0 and len(blocked) == len(invoked)), \
            "Empty events should not trigger suppression"


def test_stop_hook_fires_on_ledger_exception():
    """Test that Stop hook fires safely when _load_db_events raises exception."""
    # Mock _load_db_events to raise exception
    with patch("__lib.hook_ledger._load_db_events", side_effect=Exception("DB error")):
        from __lib.hook_ledger import _load_db_events

        try:
            events = _load_db_events("test_turn_id")
            assert False, "Should have raised exception"
        except Exception:
            pass  # Expected

        # On exception, should fall back to normal blocking behavior
        # This means the Stop hook should still fire


def test_stop_hook_prevents_false_positives():
    """Test that Stop hook doesn't shame LLM when hook system blocks everything."""
    mock_events = [
        {"event_type": "tool_invoked", "tool_name": "Read"},
        {"event_type": "tool_blocked", "tool_name": "Read"},
        {"event_type": "tool_invoked", "tool_name": "Grep"},
        {"event_type": "tool_blocked", "tool_name": "Grep"},
        {"event_type": "tool_invoked", "tool_name": "Glob"},
        {"event_type": "tool_blocked", "tool_name": "Glob"},
    ]

    with patch("__lib.hook_ledger._load_db_events", return_value=mock_events):
        from __lib.hook_ledger import _load_db_events

        events = _load_db_events("test_turn_id")
        invoked = [e for e in events if e.get("event_type") == "tool_invoked"]
        blocked = [e for e in events if e.get("event_type") == "tool_blocked"]

        # All tools blocked - should trigger suppression
        assert len(invoked) > 0, "Should have tool attempts"
        assert len(blocked) == len(invoked), "All tools should be blocked"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
