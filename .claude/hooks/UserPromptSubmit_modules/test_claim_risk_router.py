from __future__ import annotations

import importlib.util
from pathlib import Path
from typing import Callable

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.claim_risk_router import claim_risk_router
from UserPromptSubmit_modules.unified_injector import classify_intent


def _load_router_helper() -> Callable[[dict], list[str]]:
    router_path = Path(__file__).resolve().parent.parent / "UserPromptSubmit.py"
    spec = importlib.util.spec_from_file_location("userpromptsubmit_router_under_test", router_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load router module from {router_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._dict_context_blocks


def test_disputed_claim_triggers_claim_risk_router() -> None:
    context = HookContext(
        prompt="did you just remove functionality without even considering it?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = claim_risk_router(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    injection = result.context["additionalContext"]
    assert "disputed-claim branch" in injection.lower()
    assert "call sites" in injection.lower()
    assert "operating_rules" in result.context["suppress"]
    assert "cognitive_enhancers" not in result.context["suppress"]
    assert "reasoning_mode_selector" not in result.context["suppress"]
    assert "sequential_thinking" not in result.context["suppress"]
    assert "analysis_protocol_gate" in result.context["suppress"]
    assert "minimal operating rules" in injection.lower()


def test_root_cause_prompt_triggers_claim_risk_router() -> None:
    context = HookContext(
        prompt="Why are we depending so much on pushback prompts if the system should identify its own problems?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = claim_risk_router(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    injection = result.context["additionalContext"]
    assert "root-cause branch" in injection.lower()
    assert "alternative hypothesis" in injection.lower()
    assert "operating_rules" in result.context["suppress"]
    assert "reasoning_mode_selector" not in result.context["suppress"]
    assert "analysis_protocol_gate" not in result.context["suppress"]


def test_system_context_is_forwarded_with_additional_context() -> None:
    dict_context_blocks = _load_router_helper()
    blocks = dict_context_blocks(
        {
            "systemContext": "SYSTEM BLOCK",
            "additionalContext": "USER BLOCK",
        }
    )

    assert blocks == ["SYSTEM BLOCK", "USER BLOCK"]


def test_pushback_prompt_classifies_as_correction() -> None:
    assert (
        classify_intent("did you just remove functionality without even considering it?")
        == "CORRECTION"
    )
