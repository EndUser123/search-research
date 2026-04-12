from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector
from UserPromptSubmit_modules.think_trigger import think_trigger


def test_think_trigger_keeps_other_reasoning_layers_available() -> None:
    context = HookContext(
        prompt="Should we use Redis or Memcached for caching in this service?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    assert "operating_rules" in result.context["suppress"]
    assert "claim_risk_router" not in result.context["suppress"]
    assert "reasoning_mode_selector" not in result.context["suppress"]
    assert "sequential_thinking" not in result.context["suppress"]
    assert "cognitive_enhancers" not in result.context["suppress"]
    assert "analysis_protocol_gate" not in result.context["suppress"]


def test_reasoning_mode_selector_keeps_other_reasoning_layers_available() -> None:
    context = HookContext(
        prompt="Should we use Redis or Memcached for caching in this service?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = reasoning_mode_selector(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    assert "operating_rules" in result.context["suppress"]
    assert "claim_risk_router" not in result.context["suppress"]
    assert "sequential_thinking" not in result.context["suppress"]
    assert "cognitive_enhancers" not in result.context["suppress"]


def test_sequential_thinking_keeps_later_reasoning_layers_available() -> None:
    from UserPromptSubmit_modules.sequential_thinking import sequential_thinking_hook

    context = HookContext(
        prompt="Why does this keep failing in production and how do we fix it?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = sequential_thinking_hook(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    assert "operating_rules" in result.context["suppress"]
    assert "claim_risk_router" not in result.context["suppress"]
    assert "reasoning_mode_selector" not in result.context["suppress"]
    assert "cognitive_enhancers" not in result.context["suppress"]
    assert "analysis_protocol_gate" not in result.context["suppress"]
