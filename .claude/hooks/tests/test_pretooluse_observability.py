#!/usr/bin/env python3
"""Tests for structured PreToolUse observability records."""

from __future__ import annotations

import io
import json
import sys
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import PreToolUse  # noqa: E402


def _run_main_with_payload(payload: dict) -> str:
    old_stdin = sys.stdin
    stdout = io.StringIO()
    try:
        sys.stdin = io.StringIO(json.dumps(payload))
        with redirect_stdout(stdout):
            with pytest.raises(SystemExit):
                PreToolUse.main()
    finally:
        sys.stdin = old_stdin
    return stdout.getvalue()


def test_skill_first_block_log_includes_terminal_and_prompt(monkeypatch, tmp_path):
    events: list[dict] = []

    monkeypatch.setattr(PreToolUse, "HOOKS_DIR", tmp_path)
    monkeypatch.setattr(
        PreToolUse,
        "_check_skill_first_gate",
        lambda data: {"decision": "block", "reason": "call Skill first"},
    )
    monkeypatch.setattr(PreToolUse, "_pin_terminal_env", lambda data: None)
    monkeypatch.setattr(PreToolUse, "get_active_turn", lambda terminal_id: "turn-1")
    monkeypatch.setattr(
        PreToolUse,
        "append_ledger_event",
        lambda **kwargs: events.append(kwargs) or True,
    )

    payload = {
        "tool_name": "Read",
        "tool_input": {"file_path": "P:\\file.txt"},
        "session_id": "session-1",
        "terminal_id": "console-1",
        "prompt_id": "prompt-1",
        "cwd": "P:\\workspace",
    }

    output = _run_main_with_payload(payload)
    response = json.loads(output)
    assert response["blocking_hook"] == "PreToolUse.py:skill_first_gate"

    log_path = tmp_path / "logs" / "diagnostics" / "pretooluse_blocks.jsonl"
    entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["event_kind"] == "router_gate_block"
    assert entry["blocking_hook"] == "PreToolUse.py:skill_first_gate"
    assert entry["session_id"] == "session-1"
    assert entry["terminal_id"] == "console-1"
    assert entry["prompt_id"] == "prompt-1"
    assert entry["tool_name"] == "Read"
    assert entry["file_path"] == "P:\\file.txt"
    assert entry["active_turn_id"] == "turn-1"
    assert entry["reason"] == "call Skill first"
    assert not (tmp_path / "logs" / "diagnostics" / "pretooluse_canary.log").exists()

    assert events
    assert events[-1]["payload"]["blocking_hook"] == "PreToolUse.py:skill_first_gate"


def test_final_block_log_records_artifact_path(monkeypatch, tmp_path):
    events: list[dict] = []

    monkeypatch.setattr(PreToolUse, "HOOKS_DIR", tmp_path)
    monkeypatch.setattr(PreToolUse, "_check_skill_first_gate", lambda data: None)
    monkeypatch.setattr(PreToolUse, "_pin_terminal_env", lambda data: None)
    monkeypatch.setattr(PreToolUse, "UNIVERSAL", ["FakeHook.py"])
    monkeypatch.setattr(PreToolUse, "TOOL_HOOKS", {})
    monkeypatch.setattr(
        PreToolUse,
        "run_hook",
        lambda hook, data: {
            "decision": "block",
            "reason": "read blocked",
            "blocking_hook": "FakeHook.py",
        },
    )
    monkeypatch.setattr(
        PreToolUse,
        "ground_blocked_command",
        lambda data, hook, reason: {"schema": "blocked_command", "reason": reason},
    )
    monkeypatch.setattr(PreToolUse, "get_active_turn", lambda terminal_id: "turn-2")
    monkeypatch.setattr(
        PreToolUse,
        "append_ledger_event",
        lambda **kwargs: events.append(kwargs) or True,
    )

    payload = {
        "tool_name": "Read",
        "tool_input": {"file_path": "P:\\target.txt"},
        "session_id": "session-2",
        "terminal_id": "console-2",
        "prompt_id": "prompt-2",
        "cwd": "P:\\workspace",
    }

    output = _run_main_with_payload(payload)
    response = json.loads(output)
    assert response["blocking_hook"] == "FakeHook.py"

    log_path = tmp_path / "logs" / "diagnostics" / "pretooluse_blocks.jsonl"
    entry = json.loads(log_path.read_text(encoding="utf-8").splitlines()[-1])
    assert entry["event_kind"] == "router_final_block"
    assert entry["blocking_hook"] == "FakeHook.py"
    assert entry["artifact_path"].endswith(
        "grounded_artifact_console-2_session-2.json"
    )
    assert Path(entry["artifact_path"]).exists()
    assert not (tmp_path / "logs" / "diagnostics" / "pretooluse_canary.log").exists()

    assert events
    assert events[-1]["payload"]["artifact_path"] == entry["artifact_path"]


def test_child_hook_block_uses_single_block_log(monkeypatch, tmp_path):
    monkeypatch.setattr(PreToolUse, "HOOKS_DIR", tmp_path)
    monkeypatch.setattr(PreToolUse, "CRITICAL_HOOKS", set())
    hook_file = tmp_path / "FakeChild.py"
    hook_file.write_text("# test hook\n", encoding="utf-8")

    monkeypatch.setattr(
        PreToolUse.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=2,
            stdout=b"child blocked",
            stderr=b"",
        ),
    )

    payload = {
        "tool_name": "Read",
        "tool_input": {"file_path": "P:\\child.txt"},
        "session_id": "session-3",
        "terminal_id": "console-3",
        "prompt_id": "prompt-3",
        "cwd": "P:\\workspace",
    }

    result = PreToolUse.run_hook("FakeChild.py", payload)

    assert result["decision"] == "block"
    assert (tmp_path / "logs" / "diagnostics" / "pretooluse_blocks.jsonl").exists()
    assert not (tmp_path / "logs" / "diagnostics" / "hook_blocks.jsonl").exists()
