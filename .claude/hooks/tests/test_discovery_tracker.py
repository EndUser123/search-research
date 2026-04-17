"""Tests for the discovery tracker state handoff."""

import json
from pathlib import Path

from PreToolUse_discovery_tracker import main


def test_tracker_marks_discovery_done_for_tool_name(tmp_path, monkeypatch):
    """tool_name-based discovery events should write the session state file."""
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    session_id = "session-123"
    result = main({"tool_name": "/explore", "session_id": session_id})

    assert result is None

    state_file = Path(tmp_path) / ".claude" / f"discovery_state_{session_id}.json"
    assert state_file.exists()

    state = json.loads(state_file.read_text(encoding="utf-8"))
    assert state["session_id"] == session_id
    assert state["discovery_done"] is True
