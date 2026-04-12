from __future__ import annotations

import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.claim_risk_router import claim_risk_router
from UserPromptSubmit_modules.cognitive_guardrails import process_prompt
from UserPromptSubmit_modules.reasoning_contract import (
    append_reasoning_contract,
    build_reasoning_contract,
    contract_clauses,
)
from UserPromptSubmit_modules.reasoning_mode_selector import reasoning_mode_selector
from UserPromptSubmit_modules.sequential_thinking import sequential_thinking_hook
from UserPromptSubmit_modules.think_trigger import think_trigger


def test_reasoning_contract_includes_baseline_clauses() -> None:
    contract = build_reasoning_contract()
    lower = contract.lower()

    assert "reasoning contract" in lower
    assert "verify repo/runtime facts" in lower
    assert "counterexample" in lower
    assert "negative example" in lower
    assert "search existing implementations first" in lower
    assert "rollback or fallback" in lower
    assert "evidence would change the answer" in lower


def test_reasoning_contract_flags_trim_expected_clauses() -> None:
    contract = build_reasoning_contract(
        include_discovery=False,
        include_rollback=False,
        include_counterexample=True,
        include_verification=True,
        include_evidence=True,
    )
    lower = contract.lower()

    assert "counterexample" in lower
    assert "search existing implementations first" not in lower
    assert "rollback or fallback" not in lower


def test_append_reasoning_contract_is_idempotent() -> None:
    base_text = "Base block"
    once = append_reasoning_contract(base_text)
    twice = append_reasoning_contract(once)

    assert once == twice
    assert once.startswith("Base block")
    assert "counterexample" in once.lower()


def test_contract_clauses_match_expected_baseline() -> None:
    clauses = contract_clauses()

    assert clauses[0] == "**REASONING CONTRACT**"
    assert any("counterexample" in clause.lower() for clause in clauses)
    assert any("negative example" in clause.lower() for clause in clauses)


def test_think_trigger_includes_shared_contract() -> None:
    context = HookContext(
        prompt="Should we use Redis or Memcached for caching in this service?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    text = result.context["additionalContext"]
    assert "counterexample" in text.lower()
    assert "rollback or fallback" in text.lower()


def test_sequential_thinking_includes_shared_contract() -> None:
    context = HookContext(
        prompt="Why does this keep failing in production and how do we fix it?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = sequential_thinking_hook(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    text = result.context["additionalContext"]
    assert "counterexample" in text.lower()
    assert "negative example" in text.lower()


def test_reasoning_mode_selector_includes_shared_contract() -> None:
    context = HookContext(
        prompt="Compare Redis and Memcached for caching in this service.",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = reasoning_mode_selector(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    assert "systemContext" in result.context
    assert "counterexample" in result.context["systemContext"].lower()


def test_claim_risk_router_includes_shared_contract() -> None:
    context = HookContext(
        prompt="did you just remove functionality without even considering it?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = claim_risk_router(context)

    assert not result.is_empty()
    assert isinstance(result.context, dict)
    text = result.context["additionalContext"]
    assert "counterexample" in text.lower()
    assert "verify repo/runtime facts" in text.lower()


def test_cognitive_guardrails_include_shared_contract() -> None:
    result = process_prompt({"prompt": "design a hook that detects regressions"})

    assert "counterexample" in result["additionalContext"].lower()
    assert "search existing implementations first" in result["additionalContext"].lower()
