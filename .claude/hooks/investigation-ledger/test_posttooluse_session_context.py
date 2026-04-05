"""Tests for PostToolUse router session-context pinning."""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from PostToolUse_router import _set_session_terminal_context  # noqa: E402


def test_sets_session_context_from_top_level_fields(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)

    _set_session_terminal_context({
        "session_id": "194b664d-0fc4-4032-a05b-ad4b56d9c955",
    })

    assert os.environ["CLAUDE_SESSION_ID"] == "194b664d-0fc4-4032-a05b-ad4b56d9c955"
    assert os.environ["CLAUDE_TERMINAL_ID"] == "session_194b664d-0fc4-4032-a05b-ad4b56d9c955"


def test_preserves_existing_terminal_id(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", "console_existing")
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)

    _set_session_terminal_context({
        "tool_input": {"session_id": "194b664d-0fc4-4032-a05b-ad4b56d9c955"},
    })

    assert os.environ["CLAUDE_TERMINAL_ID"] == "console_existing"
    assert os.environ["CLAUDE_SESSION_ID"] == "194b664d-0fc4-4032-a05b-ad4b56d9c955"


def test_ignores_invalid_session_ids(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)

    _set_session_terminal_context({"session_id": "not-a-uuid"})

    assert "CLAUDE_SESSION_ID" not in os.environ
