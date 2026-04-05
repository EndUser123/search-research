"""Tests for tool sequence session/terminal filtering."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from tool_sequence_manager import (
    ToolSequenceManager,  # noqa: E402
    load_tool_sequence_filtered,  # noqa: E402
)


def test_filters_by_session_and_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {
        "session_id": "session_a",
        "tools": [
            {"name": "Read", "session_id": "session_a", "terminal_id": "term_1"},
            {"name": "Grep", "session_id": "session_b", "terminal_id": "term_1"},
            {"name": "Bash", "session_id": "session_a", "terminal_id": "term_2"},
            {"name": "Glob", "session_id": "session_a", "terminal_id": "term_1"},
        ],
    }
    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))

    tools = load_tool_sequence_filtered(session_id="session_a", terminal_id="term_1")
    assert [t["name"] for t in tools] == ["Read", "Glob"]


def test_uses_stored_session_when_unspecified(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {
        "session_id": "session_a",
        "tools": [
            {"name": "Read", "session_id": "session_a"},
            {"name": "Grep", "session_id": "session_b"},
            {"name": "Bash"},
        ],
    }
    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))

    tools = load_tool_sequence_filtered()
    assert [t["name"] for t in tools] == ["Read", "Bash"]


def test_missing_tool_metadata_is_tolerated(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {
        "session_id": "",
        "tools": [
            {"name": "Read"},
            {"name": "Grep", "terminal_id": "other"},
            {"name": "Bash", "session_id": "different"},
        ],
    }
    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))

    tools = load_tool_sequence_filtered(terminal_id="term_1", session_id="session_x")
    assert [t["name"] for t in tools] == ["Read"]


def test_strict_mode_drops_unscoped_entries(monkeypatch: pytest.MonkeyPatch) -> None:
    sample = {
        "session_id": "session_a",
        "tools": [
            {"name": "Read"},
            {"name": "Grep", "terminal_id": "term_1"},
            {"name": "Bash", "session_id": "session_a"},
            {"name": "Glob", "session_id": "session_a", "terminal_id": "term_1"},
        ],
    }
    monkeypatch.setattr(ToolSequenceManager, "get_all", classmethod(lambda cls: sample))

    tools = load_tool_sequence_filtered(
        session_id="session_a",
        terminal_id="term_1",
        require_scoped_metadata=True,
    )
    assert [t["name"] for t in tools] == ["Glob"]
