"""Tests for PreToolUse_git_remote_check_order_guard.py"""

from __future__ import annotations

import importlib
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent.parent


def _load_hook():
    import sys

    if str(HOOKS_DIR) not in sys.path:
        sys.path.insert(0, str(HOOKS_DIR))
    return importlib.import_module("PreToolUse_git_remote_check_order_guard")


def test_remote_ref_blocked_before_local_check(monkeypatch, tmp_path):
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-a")
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", "terminal-a")

    hook = _load_hook()
    monkeypatch.setattr(hook, "_repo_root", lambda cwd: "P:/packages/yt-is")

    result = hook.run(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git show origin/main", "cwd": "P:/packages/yt-is"},
        }
    )

    assert result is not None
    assert result["decision"] == "block"
    assert "local HEAD" in result["reason"]


def test_local_check_unlocks_remote_inspection(monkeypatch, tmp_path):
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-b")
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", "terminal-b")

    hook = _load_hook()
    monkeypatch.setattr(hook, "_repo_root", lambda cwd: "P:/packages/yt-is")

    local_result = hook.run(
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git branch --show-current",
                "cwd": "P:/packages/yt-is",
            },
        }
    )
    assert local_result is None

    remote_result = hook.run(
        {
            "tool_name": "Bash",
            "tool_input": {"command": "git diff origin/main", "cwd": "P:/packages/yt-is"},
        }
    )
    assert remote_result is None


def test_same_command_local_before_remote_is_allowed(monkeypatch, tmp_path):
    monkeypatch.setenv("CSF_STATE_DIR", str(tmp_path))
    monkeypatch.setenv("CLAUDE_SESSION_ID", "session-c")
    monkeypatch.setenv("CLAUDE_TERMINAL_ID", "terminal-c")

    hook = _load_hook()
    monkeypatch.setattr(hook, "_repo_root", lambda cwd: "P:/packages/yt-is")

    result = hook.run(
        {
            "tool_name": "Bash",
            "tool_input": {
                "command": "git branch --show-current && git show origin/main",
                "cwd": "P:/packages/yt-is",
            },
        }
    )

    assert result is None
