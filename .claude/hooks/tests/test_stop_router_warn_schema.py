"""Regression tests for schema-valid advisory output from Stop_router."""

from __future__ import annotations

import sys
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import Stop_router  # type: ignore


def test_normalize_result_warn_uses_system_message_without_decision() -> None:
    result = Stop_router._normalize_result(
        "StopHook_overconfidence_detector.py",
        {"decision": "warn", "systemMessage": "advisory text"},
    )

    assert result["systemMessage"] == "advisory text"
    assert "decision" not in result


def test_route_stop_returns_schema_valid_advisory(monkeypatch) -> None:
    monkeypatch.setattr(
        Stop_router,
        "_materialize_snapshot",
        lambda data: {
            "terminal_id": "",
            "turn_id": "",
            "session_id": "test-session",
            "user_prompt": "prompt",
            "assistant_response": "response",
            "tools_used": [],
            "tool_events": [],
            "observations": [],
        },
    )
    monkeypatch.setattr(Stop_router, "_build_validator_input", lambda input_data, snapshot: {})
    monkeypatch.setattr(Stop_router, "_supports_inprocess", lambda hook_name: True)
    monkeypatch.setattr(Stop_router, "_is_enabled", lambda env_var, default_enabled: True)
    monkeypatch.setattr(
        Stop_router, "ACTIVE_RUNTIME_HOOKS", frozenset({"StopHook_overconfidence_detector.py"})
    )
    monkeypatch.setattr(
        Stop_router,
        "HOOK_SEQUENCE",
        [
            (
                "StopHook_overconfidence_detector.py",
                "OVERCONFIDENCE_DETECTOR_ENABLED",
                True,
                "inprocess",
            )
        ],
    )
    monkeypatch.setattr(
        Stop_router,
        "run_hook_inprocess",
        lambda hook_name, hook_data, timeout_seconds=5.0: {
            "decision": "warn",
            "systemMessage": "schema-valid advisory",
        },
    )
    monkeypatch.setattr(Stop_router, "_append_validator_result", lambda *args, **kwargs: None)

    result = Stop_router.route_stop({"hook_event_name": "Stop"})

    assert result == {"systemMessage": "schema-valid advisory"}


def test_route_stop_closes_turn_before_returning_block(monkeypatch) -> None:
    closed: list[tuple[str, str, dict]] = []

    monkeypatch.setattr(
        Stop_router,
        "_materialize_snapshot",
        lambda data: {
            "terminal_id": "term-1",
            "turn_id": "turn-1",
            "session_id": "test-session",
            "user_prompt": "prompt",
            "assistant_response": "response",
            "tools_used": [],
            "tool_events": [],
            "observations": [],
        },
    )
    monkeypatch.setattr(Stop_router, "_build_validator_input", lambda input_data, snapshot: {})
    monkeypatch.setattr(Stop_router, "_supports_inprocess", lambda hook_name: True)
    monkeypatch.setattr(Stop_router, "_is_enabled", lambda env_var, default_enabled: True)
    monkeypatch.setattr(
        Stop_router, "ACTIVE_RUNTIME_HOOKS", frozenset({"StopHook_overconfidence_detector.py"})
    )
    monkeypatch.setattr(
        Stop_router,
        "HOOK_SEQUENCE",
        [
            (
                "StopHook_overconfidence_detector.py",
                "OVERCONFIDENCE_DETECTOR_ENABLED",
                True,
                "inprocess",
            )
        ],
    )
    monkeypatch.setattr(
        Stop_router,
        "run_hook_inprocess",
        lambda hook_name, hook_data, timeout_seconds=5.0: {
            "decision": "block",
            "reason": "blocking reason",
            "blocking_hook": "StopHook_overconfidence_detector.py",
        },
    )
    monkeypatch.setattr(Stop_router, "_append_validator_result", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        Stop_router,
        "close_turn",
        lambda terminal_id, turn_id, outcome: closed.append((terminal_id, turn_id, outcome)),
    )

    result = Stop_router.route_stop({"hook_event_name": "Stop"})

    assert result == {
        "decision": "block",
        "reason": "blocking reason",
        "blocking_hook": "StopHook_overconfidence_detector.py",
    }
    assert closed == [
        (
            "term-1",
            "turn-1",
            {
                "status": "blocked",
                "blocking_hook": "StopHook_overconfidence_detector.py",
                "reason": "blocking reason",
                "warnings": [],
            },
        )
    ]
