#!/usr/bin/env python3
"""
Test Stop hook empty snapshot fallback logic.

Tests that Stop hook falls back to evidence_store when supplied tool_events
is an empty list (stale snapshot scenario).

This prevents false positives where:
- git ls-files WAS executed (confirmed by system reminder)
- But Stop hook's snapshot.tool_events was empty
- Result: False positive block
"""

import json
from unittest.mock import patch, MagicMock


def test_empty_snapshot_fallback_to_evidence_store():
    """Test that empty tool_events list triggers evidence_store fallback.

    Scenario:
    1. data.get("tool_events") returns [] (stale snapshot)
    2. But _load_turn_events() returns actual tool events from DB
    3. Hook should use the DB results, not the empty snapshot
    """
    # Mock data with empty tool_events (stale snapshot scenario)
    test_data = {
        "assistant_response": "Files don't exist",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
        "tool_events": [],  # Empty list - the false positive source
    }

    # Mock _load_turn_events to return actual tool events from evidence_store
    mock_db_events = [
        {
            "id": "123",
            "name": "Bash",
            "command": "git ls-files '*.py'",
            "session_id": "test-session-123",
        }
    ]

    with patch("Stop_negative_existence_guard._load_turn_events", return_value=mock_db_events):
        # Import after patching to ensure the patch is active
        import sys
        sys.path.insert(0, "P:\\.claude\\hooks")
        import Stop_negative_existence_guard as guard

        result = guard.check(test_data)

        # Should NOT block - git ls-files was in the actual DB events
        # The empty snapshot should be ignored in favor of DB results
        assert result is None, "Should allow when evidence_store has verification tools"


def test_empty_snapshot_with_empty_evidence_store():
    """Test that when both snapshot and evidence_store are empty, block is correct.

    Scenario:
    1. data.get("tool_events") returns []
    2. _load_turn_events() also returns [] (genuinely no tools used)
    3. Hook should block (correct behavior - not a false positive)

    Note: Use a claim that doesn't match the allowlist (e.g., avoid "didn't")
    """
    test_data = {
        "assistant_response": "No config file was found for this module",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
        "tool_events": [],  # Empty list
    }

    # Mock _load_turn_events to also return empty (genuinely no tools)
    with patch("Stop_negative_existence_guard._load_turn_events", return_value=[]):
        import sys
        sys.path.insert(0, "P:\\.claude\\hooks")
        import Stop_negative_existence_guard as guard

        result = guard.check(test_data)

        # Should block - genuinely no verification tools used
        assert result is not None, "Should block when no verification tools used"
        assert result.get("decision") == "block"


def test_non_empty_snapshot_skips_evidence_store():
    """Test that non-empty snapshot is used directly (fast path).

    Scenario:
    1. data.get("tool_events") returns actual events
    2. Hook should use these directly without querying evidence_store
    """
    test_data = {
        "assistant_response": "Files don't exist",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
        "tool_events": [
            {"id": "123", "name": "Bash", "command": "git ls-files '*.py'"}
        ],  # Non-empty list
    }

    with patch("Stop_negative_existence_guard._load_turn_events") as mock_load:
        import sys
        sys.path.insert(0, "P:\\.claude\\hooks")
        import Stop_negative_existence_guard as guard

        result = guard.check(test_data)

        # Should NOT block - verification tools in snapshot
        assert result is None, "Should allow with non-empty snapshot"
        # Should NOT call _load_turn_events (fast path)
        mock_load.assert_not_called()


def test_none_tool_events_queries_evidence_store():
    """Test that None tool_events triggers evidence_store query.

    Scenario:
    1. data.get("tool_events") returns None (not provided)
    2. Hook should query evidence_store
    """
    test_data = {
        "assistant_response": "Files don't exist",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal",
        "tool_events": None,  # Not provided
    }

    mock_db_events = [
        {"id": "123", "name": "Read", "file_path": "test.py"}
    ]

    with patch("Stop_negative_existence_guard._load_turn_events", return_value=mock_db_events):
        import sys
        sys.path.insert(0, "P:\\.claude\\hooks")
        import Stop_negative_existence_guard as guard

        result = guard.check(test_data)

        # Should NOT block - Read tool was used
        assert result is None, "Should allow when evidence_store has Read"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
