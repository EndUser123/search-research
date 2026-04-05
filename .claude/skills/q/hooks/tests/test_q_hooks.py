#!/usr/bin/env python3
"""Tests for /q hook enforcement and output contracts."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


HOOKS_DIR = Path(__file__).resolve().parent.parent
PRE_HOOK = HOOKS_DIR / "PreToolUse_q_phase_gate.py"
POST_HOOK = HOOKS_DIR / "PostToolUse_q_state_tracker.py"
HALT_HOOK = HOOKS_DIR / "StopHook_q_halt_format_validator.py"
COMPLETE_HOOK = HOOKS_DIR / "StopHook_q_completion_validator.py"


def run_hook(path: Path, payload: str | dict, env: dict | None = None) -> subprocess.CompletedProcess:
    text = payload if isinstance(payload, str) else json.dumps(payload)
    run_env = os.environ.copy()
    if env:
        run_env.update(env)
    # Prevent blue console flash on Windows
    creation_flags = 0x08000000 if sys.platform == 'win32' else 0
    return subprocess.run(
        [sys.executable, str(path)],
        input=text,
        capture_output=True,
        text=True,
        env=run_env,
        creationflags=creation_flags,
    )


def write_q_state(state_dir: Path, terminal_id: str, state: dict) -> Path:
    state_dir.mkdir(parents=True, exist_ok=True)
    file_path = state_dir / f"q-pipeline-{terminal_id}.json"
    file_path.write_text(json.dumps(state))
    return file_path


def make_local_tmp_dir(prefix: str) -> Path:
    tmp = tempfile.mkdtemp(prefix=prefix, dir=str(Path.cwd()))
    return Path(tmp)


def test_pretooluse_blocks_phase_skip() -> None:
    tmp_root = make_local_tmp_dir("qhooktest-skip-")
    state_dir = tmp_root / ".claude" / "state"
    terminal_id = "qtestskip"
    try:
        write_q_state(
            state_dir,
            terminal_id,
            {"max_passed_phase": 0, "last_result": "pass", "last_action": "q"},
        )

        hook_input = {"tool_name": "Bash", "tool_input": {"command": "/q3"}}
        result = run_hook(
            PRE_HOOK,
            hook_input,
            {"CLAUDE_STATE_DIR": str(state_dir), "CLAUDE_TERMINAL_ID": terminal_id},
        )

        assert result.returncode != 0
        assert "phase gate violation" in (result.stdout + result.stderr).lower()
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_pretooluse_allows_sequential_and_force() -> None:
    tmp_root = make_local_tmp_dir("qhooktest-allow-")
    state_dir = tmp_root / ".claude" / "state"
    terminal_id = "qtestok"
    try:
        write_q_state(
            state_dir,
            terminal_id,
            {"max_passed_phase": 0, "last_result": "pass", "last_action": "q"},
        )

        sequential = {"tool_name": "Bash", "tool_input": {"command": "/q1"}}
        seq_result = run_hook(
            PRE_HOOK,
            sequential,
            {"CLAUDE_STATE_DIR": str(state_dir), "CLAUDE_TERMINAL_ID": terminal_id},
        )
        assert seq_result.returncode == 0

        skipped_force = {"tool_name": "Bash", "tool_input": {"command": "/q5 --force"}}
        force_result = run_hook(
            PRE_HOOK,
            skipped_force,
            {"CLAUDE_STATE_DIR": str(state_dir), "CLAUDE_TERMINAL_ID": terminal_id},
        )
        assert force_result.returncode == 0
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_posttooluse_tracks_phase_progress() -> None:
    tmp_root = make_local_tmp_dir("qhooktest-track-")
    state_dir = tmp_root / ".claude" / "state"
    terminal_id = "qtrack"
    try:
        write_q_state(
            state_dir,
            terminal_id,
            {"schema_version": 1, "max_passed_phase": 0, "history": []},
        )

        hook_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "/q2"},
            "tool_result": {"exit_code": 0, "output": "ok"},
        }
        result = run_hook(
            POST_HOOK,
            hook_input,
            {"CLAUDE_STATE_DIR": str(state_dir), "CLAUDE_TERMINAL_ID": terminal_id},
        )
        assert result.returncode == 0

        saved = json.loads((state_dir / f"q-pipeline-{terminal_id}.json").read_text())
        assert saved["max_passed_phase"] == 2
        assert saved["last_action"] == "q2"
        assert saved["last_result"] == "pass"
        assert saved["history"]
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def test_halt_validator_accepts_and_rejects() -> None:
    valid = """
## Current Status Summary
- ✅ Q1: ScopeResolver - PASS
- 🛑 Q2: QuickCollectors - HALT

## Q PIPELINE HALTED
**Status:** 🛑 HALTED at Q2
**Reason:** Missing WT_SESSION

## Next Steps
1 - Export WT_SESSION
2 - Re-run q2

Then re-run: /q
"""
    good = run_hook(HALT_HOOK, valid)
    assert good.returncode == 0
    assert json.loads(good.stdout)["allow"] is True

    invalid = """
## Q PIPELINE HALTED
**Status:** 🛑 HALTED at Q2
## Next Steps
1 - Re-run
"""
    bad = run_hook(HALT_HOOK, invalid)
    assert bad.returncode != 0
    assert json.loads(bad.stdout)["allow"] is False


def test_completion_validator_accepts_and_rejects() -> None:
    valid = """
## Current Status Summary
- ✅ Q1: ScopeResolver - PASS
- ✅ Q2: QuickCollectors - PASS

## Q PIPELINE COMPLETE
**Status:** ✅ COMPLETE
**Summary:** Completed all required phases

## Next Steps
1 - Continue
"""
    good = run_hook(COMPLETE_HOOK, valid)
    assert good.returncode == 0
    assert json.loads(good.stdout)["allow"] is True

    invalid = """
## Q PIPELINE COMPLETE
**Status:** ✅ COMPLETE

## Next Steps
1 - Continue
"""
    bad = run_hook(COMPLETE_HOOK, invalid)
    assert bad.returncode != 0
    assert json.loads(bad.stdout)["allow"] is False
