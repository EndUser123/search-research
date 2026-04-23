from __future__ import annotations

import os
import sys
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.base import HookContext
import UserPromptSubmit_modules.behavior_contract as behavior_contract_module
from UserPromptSubmit_modules.behavior_contract import (
    append_behavior_contract,
    behavior_contract,
    build_behavior_contract,
    contract_clauses,
)
from UserPromptSubmit_modules.unified_detection import UnifiedDetectionResult


def test_behavior_contract_includes_core_rules() -> None:
    contract = build_behavior_contract().lower()

    assert "behavior contract" in contract
    assert "if the question is concrete" in contract
    assert "if a claim is verified" in contract
    assert "if not, mark it as inference or unknown" in contract
    assert "if you did not use a tool" in contract
    assert "if evidence is missing" in contract
    assert "decision criterion" in contract
    assert "behavioral rubric" in contract
    assert "user corrects your frame" in contract
    assert "next step is obvious" in contract
    assert "self-check" in contract
    assert "stop hooks are the backstop" in contract


def test_contract_clauses_are_non_empty() -> None:
    clauses = contract_clauses()

    assert clauses
    assert "llm behavior contract" in clauses[0].lower()
    assert any("if the question is concrete" in clause.lower() for clause in clauses)
    assert any("behavioral rubric" in clause.lower() for clause in clauses)
    assert any("stop hooks" in clause.lower() for clause in clauses)


def test_append_behavior_contract_is_idempotent() -> None:
    base_text = "Base prompt block"

    once = append_behavior_contract(base_text)
    twice = append_behavior_contract(once)

    assert once == twice
    assert once.startswith("Base prompt block")
    assert "if the question is concrete" in once.lower()
    assert "behavioral rubric" in once.lower()


def test_behavior_contract_injects_on_substantive_prompts() -> None:
    original = os.environ.get("LLM_BEHAVIOR_CONTRACT_ENABLED")
    os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = "true"

    try:
        context = HookContext(
            prompt="Refactor the stop hook flow so it is safer and more efficient.",
            data={},
            session_id="test-session",
            terminal_id="test-terminal",
        )

        result = behavior_contract(context)

        assert not result.is_empty()
        assert isinstance(result.context, str)
        text = result.context.lower()
        assert "behavior contract" in text
        assert "if the question is concrete" in text
        assert "if you did not use a tool" in text
        assert "behavioral rubric" in text
    finally:
        if original is None:
            os.environ.pop("LLM_BEHAVIOR_CONTRACT_ENABLED", None)
        else:
            os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = original


def test_behavior_contract_uses_unified_detection_signal() -> None:
    context = HookContext(
        prompt="please help with this",
        data={
            "unified_detection_result": UnifiedDetectionResult(
                matched_frameworks=[],
                matched_modes=[],
                matched_profiles=[],
                intent_classification="implementation",
            )
        },
        session_id="test-session",
        terminal_id="test-terminal",
    )

    result = behavior_contract(context)

    assert not result.is_empty()
    assert isinstance(result.context, str)


def test_behavior_contract_skips_short_and_slash_prompts() -> None:
    context_short = HookContext(
        prompt="Help me?",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )
    context_slash = HookContext(
        prompt="/plan improve behavior",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    assert behavior_contract(context_short).is_empty()
    assert behavior_contract(context_slash).is_empty()


def test_behavior_contract_skips_casual_acknowledgement() -> None:
    context = HookContext(
        prompt="thanks",
        data={},
        session_id="test-session",
        terminal_id="test-terminal",
    )

    assert behavior_contract(context).is_empty()


def test_behavior_contract_can_be_disabled() -> None:
    original = os.environ.get("LLM_BEHAVIOR_CONTRACT_ENABLED")
    os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = "false"

    try:
        context = HookContext(
            prompt="Refactor the stop hook flow so it is safer and more efficient.",
            data={},
            session_id="test-session",
            terminal_id="test-terminal",
        )

        result = behavior_contract(context)

        assert result.is_empty()
    finally:
        if original is None:
            os.environ.pop("LLM_BEHAVIOR_CONTRACT_ENABLED", None)
        else:
            os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = original


def test_behavior_contract_fires_on_documentation_request() -> None:
    """RCA verification: ensure documentation prompts trigger the contract.

    This was the gap that allowed LLM to implement when user only wanted docs.
    The contract's behavioral rubric rule: "stop at findings, do not begin implementation."
    """
    original = os.environ.get("LLM_BEHAVIOR_CONTRACT_ENABLED")
    os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = "true"
    try:
        context = HookContext(
            prompt="can you document the approach we discussed?",
            data={},
            session_id="test-session",
            terminal_id="test-terminal",
        )
        result = behavior_contract(context)
        assert not result.is_empty(), "documentation request should trigger contract"
        # Verify the documentation boundary rule is present in injected text
        text = result.context.lower()
        assert any(
            phrase in text
            for phrase in [
                "documentation",
                "findings",
                "implementation",
                "stop at",
            ]
        ), f"contract should mention documentation boundary, got: {result.context[:200]}"
    finally:
        if original is None:
            os.environ.pop("LLM_BEHAVIOR_CONTRACT_ENABLED", None)
        else:
            os.environ["LLM_BEHAVIOR_CONTRACT_ENABLED"] = original


def test_behavior_contract_logs_turn_scope(monkeypatch) -> None:
    calls: list[dict] = []

    def fake_logger(**kwargs):
        calls.append(kwargs)

    monkeypatch.setattr(behavior_contract_module, "log_hook_invocation", fake_logger)

    context = HookContext(
        prompt="Refactor the stop hook flow so it is safer and more efficient.",
        data={"turn_id": "turn-123"},
        session_id="session-123",
        terminal_id="terminal-123",
    )

    result = behavior_contract(context)

    assert not result.is_empty()
    assert len(calls) == 1
    assert calls[0]["hook_name"] == "behavior_contract"
    assert calls[0]["event_type"] == "UserPromptSubmit"
    assert calls[0]["action"] == "inject"
    assert calls[0]["turn_id"] == "turn-123"
    assert calls[0]["session_id"] == "session-123"
    assert calls[0]["terminal_id"] == "terminal-123"
