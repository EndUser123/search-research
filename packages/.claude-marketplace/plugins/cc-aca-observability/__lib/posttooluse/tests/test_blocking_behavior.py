#!/usr/bin/env python3
"""Regression tests for blocking PostToolUse registry results."""

from __future__ import annotations

import io
import json
import sys
from pathlib import Path

import pytest

HOOKS_DIR = Path(__file__).resolve().parents[2]
PACKAGE_DIR = HOOKS_DIR / "posttooluse"
sys.path.insert(0, str(HOOKS_DIR))
sys.path.insert(0, str(PACKAGE_DIR))

from posttooluse.base import is_block_result

import PostToolUse
import PostToolUse_router


class FakeRegistry:
    def __init__(self, result: dict):
        self._result = result

    def run_all(self, data: dict) -> dict:
        self.last_data = data
        return self._result


@pytest.mark.parametrize(
    "result, expected",
    [
        ({"decision": "block"}, True),
        ({"block": True}, True),
        ({"allow": False}, True),
        ({"decision": "warn"}, False),
        ({}, False),
        (None, False),
    ],
)
def test_is_block_result(result: dict | None, expected: bool) -> None:
    assert is_block_result(result) is expected


def test_posttooluse_main_emits_block_json_on_block(monkeypatch, capsys) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        PostToolUse,
        "create_registry",
        lambda: FakeRegistry({"decision": "block", "reason": "registry blocked"}),
    )
    monkeypatch.setattr(
        PostToolUse,
        "append_tool_event",
        lambda *args, **kwargs: calls.append("append_tool_event"),
    )
    monkeypatch.setattr(
        PostToolUse,
        "write_tool_error_signal",
        lambda *args, **kwargs: calls.append("write_tool_error_signal"),
    )
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "Write",
                    "tool_input": {"command": "touch a.txt"},
                    "tool_result": "ok",
                    "session_id": "sess-1",
                }
            )
        ),
    )

    with pytest.raises(SystemExit) as exc:
        PostToolUse.main()

    assert exc.value.code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["decision"] == "block"
    assert payload["reason"] == "registry blocked"
    assert calls == []


def test_posttooluse_router_main_emits_block_json_on_block(monkeypatch, capsys) -> None:
    calls: list[str] = []

    monkeypatch.setattr(
        PostToolUse_router,
        "create_registry",
        lambda: FakeRegistry({"decision": "block", "reason": "router blocked"}),
    )
    monkeypatch.setattr(
        PostToolUse_router,
        "_set_session_terminal_context",
        lambda *args, **kwargs: calls.append("_set_session_terminal_context"),
    )
    monkeypatch.setattr(
        PostToolUse_router,
        "_run_auto_commit",
        lambda *args, **kwargs: calls.append("_run_auto_commit"),
    )
    monkeypatch.setattr(
        PostToolUse_router,
        "_write_error_signal",
        lambda *args, **kwargs: calls.append("_write_error_signal"),
    )
    monkeypatch.setattr(
        PostToolUse_router,
        "_clear_pending_skill_intent",
        lambda *args, **kwargs: calls.append("_clear_pending_skill_intent"),
    )
    monkeypatch.setattr(
        PostToolUse_router,
        "append_tool_event",
        lambda *args, **kwargs: calls.append("append_tool_event"),
    )
    monkeypatch.setattr(PostToolUse_router, "LEGACY_TRACKING_AVAILABLE", False)
    monkeypatch.setattr(PostToolUse_router, "EVIDENCE_AVAILABLE", False)
    monkeypatch.setattr(PostToolUse_router, "LEDGER_AVAILABLE", False)
    monkeypatch.setattr(PostToolUse_router, "get_hook_invocation_logger", None)
    monkeypatch.setattr(PostToolUse_router, "create_router_entry", None)
    monkeypatch.setattr(
        sys,
        "stdin",
        io.StringIO(
            json.dumps(
                {
                    "tool_name": "Write",
                    "tool_input": {"command": "touch a.txt"},
                    "tool_response": "ok",
                    "session_id": "sess-1",
                }
            )
        ),
    )

    with pytest.raises(SystemExit) as exc:
        PostToolUse_router.main()

    assert exc.value.code == 0
    captured = capsys.readouterr()
    payload = json.loads(captured.out.strip())
    assert payload["decision"] == "block"
    assert payload["reason"] == "router blocked"
    assert calls == []
