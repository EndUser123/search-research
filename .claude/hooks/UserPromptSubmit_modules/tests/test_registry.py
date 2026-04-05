"""Tests for UserPromptSubmit registry behavior."""

from __future__ import annotations

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookResult
from UserPromptSubmit.registry import HOOK_PRIORITY, HOOKS, run_hooks


def test_run_hooks_honors_priority_override() -> None:
    original_hooks = dict(HOOKS)
    original_priority = dict(HOOK_PRIORITY)
    try:
        HOOKS.clear()
        HOOK_PRIORITY.clear()

        def hook_a(context):  # type: ignore[no-untyped-def]
            return HookResult(context="A", tokens=1)

        def hook_b(context):  # type: ignore[no-untyped-def]
            return HookResult(context="B", tokens=1)

        HOOKS["a"] = hook_a
        HOOKS["b"] = hook_b
        HOOK_PRIORITY["a"] = 1.0
        HOOK_PRIORITY["b"] = 2.0

        results = run_hooks({}, "prompt", priority_dict={"a": 20.0, "b": 1.0})
        assert [r.context for r in results] == ["B", "A"]
    finally:
        HOOKS.clear()
        HOOKS.update(original_hooks)
        HOOK_PRIORITY.clear()
        HOOK_PRIORITY.update(original_priority)


def test_run_hooks_sets_context_session_and_terminal_ids() -> None:
    original_hooks = dict(HOOKS)
    original_priority = dict(HOOK_PRIORITY)
    try:
        HOOKS.clear()
        HOOK_PRIORITY.clear()

        def context_probe(context):  # type: ignore[no-untyped-def]
            payload = f"{context.session_id}|{context.terminal_id}"
            return HookResult(context=payload, tokens=1)

        HOOKS["probe"] = context_probe
        HOOK_PRIORITY["probe"] = 1.0

        data = {"session_id": "s-123", "terminal_id": "t-999"}
        results = run_hooks(data, "prompt")
        assert len(results) == 1
        assert results[0].context == "s-123|t-999"
    finally:
        HOOKS.clear()
        HOOKS.update(original_hooks)
        HOOK_PRIORITY.clear()
        HOOK_PRIORITY.update(original_priority)
