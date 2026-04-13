from __future__ import annotations

import os
import sys
import tempfile
from pathlib import Path

_hooks_dir = Path(__file__).resolve().parent.parent.parent
if str(_hooks_dir) not in sys.path:
    sys.path.insert(0, str(_hooks_dir))

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.anti_sycophancy_injector import run_anti_sycophancy_injector
from UserPromptSubmit_modules.claim_risk_router import claim_risk_router
from UserPromptSubmit_modules.testing_strategy_router import strategy_router
from UserPromptSubmit_modules.think_trigger import think_trigger


SNAPSHOT_DIR = Path(__file__).resolve().parent / "snapshots"


def _normalize(text: str) -> str:
    return "\n".join(line.rstrip() for line in text.replace("\r\n", "\n").strip().split("\n"))


def _snapshot(name: str) -> str:
    return _normalize((SNAPSHOT_DIR / name).read_text(encoding="utf-8"))


def _state_file(session_id: str, terminal_id: str) -> Path:
    safe_session = "".join(c if c.isalnum() or c in "._-" else "_" for c in session_id)
    safe_terminal = "".join(c if c.isalnum() or c in "._-" else "_" for c in terminal_id)
    return Path(tempfile.gettempdir()) / "claude_hooks" / "state" / "anti_sycophancy_injector" / f"{safe_session}__{safe_terminal}.json"


def test_explicit_think_hook_snapshot_matches() -> None:
    context = HookContext(
        prompt="We should THINK through this cache design carefully.",
        data={},
        session_id="snap-explicit",
        terminal_id="term-explicit",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("think.explicit.additional_context.txt")


def test_evidence_audit_hook_snapshot_matches() -> None:
    context = HookContext(
        prompt="Can you verify whether this is actually implemented?",
        data={},
        session_id="snap-evidence",
        terminal_id="term-evidence",
    )

    result = think_trigger(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("think.evidence_audit.additional_context.txt")


def test_anti_sycophancy_light_protocol_snapshot_matches() -> None:
    os.environ["ANTI_SYCOPHANCY_ENABLED"] = "true"
    state = _state_file("snap-anti", "term-anti")
    state.unlink(missing_ok=True)
    context = HookContext(
        prompt="are you sure this is needed?",
        data={"session_id": "snap-anti", "terminal_id": "term-anti"},
        session_id="snap-anti",
        terminal_id="term-anti",
    )

    result = run_anti_sycophancy_injector(context)

    assert result is not None
    assert _normalize(result.context) == _snapshot("anti_sycophancy.light_protocol.txt")


def test_claim_risk_router_root_cause_snapshot_matches() -> None:
    context = HookContext(
        prompt="Why did this regression happen in production?",
        data={},
        session_id="snap-claim",
        terminal_id="term-claim",
    )

    result = claim_risk_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("claim_risk_router.root_cause.additional_context.txt")


def test_claim_risk_router_path_layout_snapshot_matches() -> None:
    context = HookContext(
        prompt="Why is P:\\.claude\\skills\\yt-channel a junction?",
        data={},
        session_id="snap-path",
        terminal_id="term-path",
    )

    result = claim_risk_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("claim_risk_router.path_layout.additional_context.txt")


def test_testing_strategy_router_regression_snapshot_matches() -> None:
    context = HookContext(
        prompt="/tdd fix this regression in a parser",
        data={},
        session_id="snap-test-regression",
        terminal_id="term-test-regression",
    )

    result = strategy_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("testing_strategy_router.regression_first.additional_context.txt")


def test_testing_strategy_router_unit_snapshot_matches() -> None:
    context = HookContext(
        prompt="/t write tests for a pure validation helper",
        data={},
        session_id="snap-test-unit",
        terminal_id="term-test-unit",
    )

    result = strategy_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("testing_strategy_router.unit_first.additional_context.txt")


def test_testing_strategy_router_integration_snapshot_matches() -> None:
    context = HookContext(
        prompt="/t add tests for a hook/router/stateful workflow",
        data={},
        session_id="snap-test-integration",
        terminal_id="term-test-integration",
    )

    result = strategy_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("testing_strategy_router.integration_first.additional_context.txt")


def test_testing_strategy_router_snapshot_snapshot_matches() -> None:
    context = HookContext(
        prompt="/tdd add a snapshot test for rendered output and generated docs",
        data={},
        session_id="snap-test-snapshot",
        terminal_id="term-test-snapshot",
    )

    result = strategy_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("testing_strategy_router.snapshot_first.additional_context.txt")


def test_testing_strategy_router_code_snapshot_matches() -> None:
    context = HookContext(
        prompt="/code implement a feature with proper tests",
        data={},
        session_id="snap-test-code",
        terminal_id="term-test-code",
    )

    result = strategy_router(context)

    assert not result.is_empty()
    assert _normalize(result.context["additionalContext"]) == _snapshot("testing_strategy_router.code.additional_context.txt")


def test_testing_strategy_router_quality_slash_commands_inject_contract() -> None:
    for prompt in ["/sqa", "/sqd", "/verify", "/qa"]:
        context = HookContext(
            prompt=prompt,
            data={},
            session_id=f"snap-{prompt.strip('/')}",
            terminal_id=f"term-{prompt.strip('/')}",
        )

        result = strategy_router(context)

        assert not result.is_empty()
        assert result.context["additionalContext"].startswith("**TEST STRATEGY CONTRACT**")
