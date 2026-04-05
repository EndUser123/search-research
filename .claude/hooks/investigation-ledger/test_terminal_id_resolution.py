"""Tests for stable terminal/session ID resolution in ledger."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

HOOK_DIR = Path(__file__).resolve().parent
if str(HOOK_DIR) not in sys.path:
    sys.path.insert(0, str(HOOK_DIR))

from ledger import _resolve_terminal_id  # noqa: E402


def test_resolve_terminal_id_prefers_explicit_terminal(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", "console:abc/123")
    monkeypatch.setenv("CLAUDE_SESSION_ID", "194b664d-0fc4-4032-a05b-ad4b56d9c955")
    assert _resolve_terminal_id() == "console_abc_123"


def test_resolve_terminal_id_uses_session_when_terminal_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)
    monkeypatch.setenv("CLAUDE_SESSION_ID", "194b664d-0fc4-4032-a05b-ad4b56d9c955")
    assert _resolve_terminal_id() == "session_194b664d-0fc4-4032-a05b-ad4b56d9c955"


def test_resolve_terminal_id_returns_empty_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("CLAUDE_TERMINAL_ID", raising=False)
    monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
    assert _resolve_terminal_id() == ""
