"""Tests for conversation_gate question/conversation intent detection."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookContext, HookResult
from UserPromptSubmit.conversation_gate import (
    CONVERSATION_CONTEXT,
    is_conversation_mode,
    run_conversation_gate,
    score_conversation_intent,
)


@pytest.mark.parametrize(
    ("prompt", "expected"),
    [
        ("What do you think about moving this to packages?", True),
        ("Should we use hatchling or setuptools?", True),
        ("I didn't tell you to do anything. I was asking questions.", True),
        ("Not really. Look at P:/packages.", True),
        ("Let me think about this first.", True),
        ("/package prompting-framework", False),
        ("Fix the bug in auth.py", False),
        ("Create a new endpoint for users", False),
        ("Build the package now", False),
        ("Can you explain how the hooks work?", True),
    ],
)
def test_conversation_mode_cases(prompt: str, expected: bool) -> None:
    assert is_conversation_mode(prompt) is expected


def test_pushback_scores_highly() -> None:
    prompt = "I didn't ask for implementation. I was asking."
    assert score_conversation_intent(prompt) >= 4


def test_run_conversation_gate_returns_none_when_not_triggered() -> None:
    context = HookContext(prompt="Fix the build script", data={})
    result = run_conversation_gate(context)
    assert result is None


def test_run_conversation_gate_returns_hook_result_when_triggered() -> None:
    context = HookContext(prompt="What do you think we should do?", data={})
    result = run_conversation_gate(context)
    assert isinstance(result, HookResult)
    assert result.context == CONVERSATION_CONTEXT
    assert result.tokens > 0
