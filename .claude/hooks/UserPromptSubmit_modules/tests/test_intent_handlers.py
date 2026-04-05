"""Tests for intent_handlers research question behavior."""

from __future__ import annotations

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit.base import HookContext
from UserPromptSubmit.intent_handlers import run_intent_handlers


def test_research_question_uses_answer_first_wording() -> None:
    context = HookContext(prompt="Can you research this?", data={})
    result = run_intent_handlers(context)
    assert result is not None
    assert "Answer the user's question" in result.context
    assert "Do not start executing work unless explicitly asked." in result.context


def test_research_statement_keeps_information_gathering_wording() -> None:
    context = HookContext(prompt="Research the dependency graph", data={})
    result = run_intent_handlers(context)
    assert result is not None
    assert "Focus on gathering information before proposing solutions." in result.context
