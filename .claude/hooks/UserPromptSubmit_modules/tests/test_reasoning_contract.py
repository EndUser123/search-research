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
from UserPromptSubmit_modules.think_trigger import _detect_profile, _PROFILES, think_trigger


def test_reasoning_contract_includes_baseline_clauses() -> None:
    contract = build_reasoning_contract()
    lower = contract.lower()

    assert "reasoning contract" in lower
    assert "verify repo/runtime facts" in lower
    assert "counterexample" in lower
    assert "negative example" in lower
    assert "search existing implementations first" in lower
    assert "smallest discriminating test" in lower
    assert "rollback or fallback" in lower
    assert "evidence would change the answer" in lower
    assert "falsification condition" in lower
    assert "this would be wrong if" in lower
    assert "comparison axis" in lower
    assert "before celebrating a fix" in lower
    assert "user's reported gap is actually closed" in lower


def test_reasoning_contract_flags_trim_expected_clauses() -> None:
    contract = build_reasoning_contract(
        include_discovery=False,
        include_investigation=False,
        include_rollback=False,
        include_premortem_checklist=False,
        include_fix_closure_check=False,
        include_counterexample=True,
        include_verification=True,
        include_evidence=True,
        include_falsification=True,
    )
    lower = contract.lower()

    assert "counterexample" in lower
    assert "search existing implementations first" not in lower
    assert "smallest discriminating test" not in lower
    assert "rollback or fallback" not in lower
    assert "before celebrating a fix" not in lower
    assert "user's reported gap is actually closed" not in lower


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
    assert any("smallest discriminating test" in clause.lower() for clause in clauses)
    assert any("falsification condition" in clause.lower() for clause in clauses)
    assert any("comparison axis" in clause.lower() for clause in clauses)
    assert any("before celebrating a fix" in clause.lower() for clause in clauses)
    assert any("user's reported gap is actually closed" in clause.lower() for clause in clauses)


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
    assert "smallest discriminating test" in text.lower()
    assert "rollback or fallback" in text.lower()
    assert "falsification condition" in text.lower()
    assert "before celebrating a fix" in text.lower()
    assert "user's reported gap is actually closed" in text.lower()


def test_explicit_think_profile_requires_internal_alternatives() -> None:
    template = _PROFILES["explicit_think"].lower()

    assert "at least 2 plausible approaches" in template
    assert "rejected" in template
    assert "2-3 alternative approaches" not in template


def test_explicit_think_keyword_routes_to_explicit_profile() -> None:
    assert _detect_profile("We should THINK through this cache design carefully.") == "explicit_think"


def test_explicit_think_hook_asks_for_internal_alternatives_but_one_path() -> None:
    context = HookContext(
        prompt="We should THINK through this cache design carefully.",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    text = result.context["additionalContext"].lower()
    assert "at least 2 plausible approaches" in text
    assert "rejected" in text
    assert "2-3 alternative approaches" not in text


def test_evidence_audit_keyword_routes_to_evidence_profile() -> None:
    assert _detect_profile("Can you verify whether this is actually implemented?") == "evidence_audit"


def test_evidence_audit_hook_injects_verification_template() -> None:
    context = HookContext(
        prompt="Can you verify whether this is actually implemented?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    text = result.context["additionalContext"].lower()
    assert "evidence audit" in text
    assert "verified, refuted, or still uncertain" in text
    assert "counterexample" in text


def test_tradeoff_profile_stays_lightweight() -> None:
    template = _PROFILES["tradeoff_decision"].lower()

    assert "light precheck" in template
    assert "compare 2 options plus the simplest fallback" in template
    assert "5 dimensions" not in template
    assert "state transition" not in template


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
    assert "falsification condition" in text.lower()


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
    assert "falsification condition" in result.context["systemContext"].lower()


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
    assert "smallest discriminating test" in text.lower()
    assert "falsification condition" in text.lower()
    assert "before celebrating a fix" in text.lower()
    assert "user's reported gap is actually closed" in text.lower()


def test_cognitive_guardrails_include_shared_contract() -> None:
    result = process_prompt({"prompt": "design a hook that detects regressions"})

    assert "counterexample" in result["additionalContext"].lower()
    assert "search existing implementations first" in result["additionalContext"].lower()
    assert "smallest discriminating test" in result["additionalContext"].lower()
    assert "falsification condition" in result["additionalContext"].lower()
    assert "before celebrating a fix" in result["additionalContext"].lower()
    assert "user's reported gap is actually closed" in result["additionalContext"].lower()


def test_reasoning_contract_snapshot_matches() -> None:
    snapshot = Path(__file__).resolve().parent / "snapshots" / "reasoning_contract.full.txt"
    assert build_reasoning_contract() == snapshot.read_text(encoding="utf-8").strip()
