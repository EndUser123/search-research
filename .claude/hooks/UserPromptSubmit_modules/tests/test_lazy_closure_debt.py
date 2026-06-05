"""Tests for the lazy_closure_debt compatibility wrapper."""
from __future__ import annotations

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parent.parent.parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext  # noqa: E402
from UserPromptSubmit_modules import lazy_closure_debt as LCD  # noqa: E402


def test_wrapper_maps_additional_context(monkeypatch):
    class _FakeMod:
        @staticmethod
        def run(data):
            return {"hookSpecificOutput": {"additionalContext": "debt context"}}

    monkeypatch.setattr(LCD, "_mod", _FakeMod)
    result = LCD.lazy_closure_debt(HookContext(prompt="x", data={"session_id": "s"}))
    assert result.context == "debt context"
    assert result.tokens > 0


def test_wrapper_returns_empty_when_plugin_has_no_context(monkeypatch):
    class _FakeMod:
        @staticmethod
        def run(data):
            return {"continue": True}

    monkeypatch.setattr(LCD, "_mod", _FakeMod)
    result = LCD.lazy_closure_debt(HookContext(prompt="x", data={"session_id": "s"}))
    assert result.context is None
