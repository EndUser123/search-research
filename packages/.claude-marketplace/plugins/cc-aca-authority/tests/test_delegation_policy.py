from __future__ import annotations

import importlib.util
import io
import json
import sys
import time
from pathlib import Path

PLUGIN_ROOT = Path(__file__).resolve().parents[1]
PROSPECTOR_PATH = PLUGIN_ROOT / "hooks" / "userpromptsubmit" / "delegation_prospector.py"
GATE_PATH = PLUGIN_ROOT / "hooks" / "pretool" / "PreToolUse_delegation_gate.py"


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_quoted_review_text_does_not_trigger_delegation():
    prospector = load_module("delegation_prospector_under_test", PROSPECTOR_PATH)
    prompt = """Another LLM said:

> Stop expanding scope. First make state.py importable, add __init__.py,
> then implement policy.py, render.py, and tests.

Please identify the workflow problem."""

    detected, pattern = prospector._detect_delegation_opportunity(prompt)

    assert detected is False
    assert pattern is None


def test_real_multi_surface_implementation_still_triggers_delegation():
    prospector = load_module("delegation_prospector_under_test_real", PROSPECTOR_PATH)

    detected, pattern = prospector._detect_delegation_opportunity(
        "implement policy.py, render.py, tests, and docs"
    )

    assert detected is True
    assert pattern is not None


def test_read_only_tools_are_allowed_when_delegation_state_exists(tmp_path, monkeypatch):
    gate = load_module("delegation_gate_under_test_readonly", GATE_PATH)
    monkeypatch.setattr(gate, "_get_artifacts_dir", lambda terminal_id_override=None: tmp_path)
    state_file = tmp_path / "delegation_expected.json"
    state_file.write_text(
        json.dumps(
            {
                "terminal_id": "term-1",
                "session_id": "session-1",
                "detected_at": time.time(),
                "matched_pattern": "matched: implementation list",
                "prompt_snippet": "implement policy.py, render.py, tests",
            }
        ),
        encoding="utf-8",
    )

    for tool_name in ("Read", "Grep", "Glob"):
        assert gate._should_block_tool(tool_name, {}) is False


def test_narrow_diagnostic_bash_is_allowed_when_delegation_state_exists():
    gate = load_module("delegation_gate_under_test_bash_allow", GATE_PATH)
    allowed_commands = [
        'python -c "import context_controller.state"',
        "python -m py_compile P:/.claude/hooks/context_controller/state.py",
        "git status --short",
        'rg "resolve_terminal_key" P:/.claude/hooks',
    ]

    for command in allowed_commands:
        assert gate._should_block_tool("Bash", {"command": command}) is False


def test_implementation_tools_and_broad_bash_are_blocked_when_delegation_state_exists():
    gate = load_module("delegation_gate_under_test_block", GATE_PATH)

    for tool_name in ("Edit", "Write", "MultiEdit"):
        assert gate._should_block_tool(tool_name, {}) is True

    blocked_commands = [
        "pytest",
        "python scripts/apply_all_fixes.py",
        "rm -rf P:/.claude/hooks/context_controller",
        "git commit -am fix",
    ]
    for command in blocked_commands:
        assert gate._should_block_tool("Bash", {"command": command}) is True


def test_task_agent_skill_clear_state_and_allow(tmp_path, monkeypatch):
    gate = load_module("delegation_gate_under_test_clear", GATE_PATH)
    monkeypatch.setattr(gate, "_get_artifacts_dir", lambda terminal_id_override=None: tmp_path)
    monkeypatch.setattr(gate, "_is_bypass_flagged", lambda data: False)
    monkeypatch.setattr(gate, "_detect_terminal_id_from_data", lambda data: "term-1")
    monkeypatch.setattr(gate, "_extract_session_id_from_data", lambda data: "session-1")
    monkeypatch.setattr(gate, "_log_gate_event", lambda *args, **kwargs: None)

    for tool_name in ("Task", "Agent", "Skill"):
        state_file = tmp_path / "delegation_expected.json"
        state_file.write_text(
            json.dumps(
                {
                    "terminal_id": "term-1",
                    "session_id": "session-1",
                    "detected_at": time.time(),
                    "matched_pattern": "matched: implementation list",
                    "prompt_snippet": "implement policy.py, render.py, tests",
                }
            ),
            encoding="utf-8",
        )
        old_stdin = sys.stdin
        sys.stdin = io.StringIO(
            json.dumps({"tool_name": tool_name, "terminal_id": "term-1", "session_id": "session-1"})
        )
        try:
            assert gate.main() == 0
        finally:
            sys.stdin = old_stdin
        assert not state_file.exists()
