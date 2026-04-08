from __future__ import annotations

from UserPromptSubmit_modules.base import HookContext
from UserPromptSubmit_modules.verify_before_claim import (
    _REMINDER,
    verify_before_claim,
)


def test_verify_before_claim_triggers_for_comparative_reliability_prompt(monkeypatch) -> None:
    monkeypatch.setattr(
        "UserPromptSubmit_modules.verify_before_claim._is_on_cooldown",
        lambda session_id, terminal_id: False,
    )
    monkeypatch.setattr(
        "UserPromptSubmit_modules.verify_before_claim._record_fired",
        lambda session_id, terminal_id: None,
    )

    context = HookContext(
        prompt="Which method is most reliable end-to-end, and which gets bot detected the least?",
        data={},
        session_id="session-1",
        terminal_id="term-1",
    )

    result = verify_before_claim(context)

    assert result.context == _REMINDER
    assert "dependency chain" in result.context.lower()


def test_verify_before_claim_does_not_trigger_for_simple_read_request(monkeypatch) -> None:
    monkeypatch.setattr(
        "UserPromptSubmit_modules.verify_before_claim._is_on_cooldown",
        lambda session_id, terminal_id: False,
    )
    monkeypatch.setattr(
        "UserPromptSubmit_modules.verify_before_claim._record_fired",
        lambda session_id, terminal_id: None,
    )

    context = HookContext(
        prompt="Read transcript.py and explain what _fetch_via_ytdlp does.",
        data={},
        session_id="session-2",
        terminal_id="term-2",
    )

    result = verify_before_claim(context)

    assert result.is_empty()
