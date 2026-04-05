#!/usr/bin/env python3
"""Tests for three-tier .claude sensitive edit policy."""

from __future__ import annotations

import io
import json
import sys
import types
from pathlib import Path

import pytest

# Add hooks directory to import path
HOOKS_DIR = Path(__file__).resolve().parent.parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import PreToolUse_path_validator
import SessionStart
from __lib import pre_tool_use_logic
from __lib.path_validator import PathValidator


@pytest.fixture
def isolated_consent_dirs(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> dict[str, Path]:
    """Redirect consent token storage to temp directories."""
    primary = tmp_path / "primary"
    fallback = tmp_path / "fallback"
    temp = tmp_path / "temp"

    monkeypatch.setattr(pre_tool_use_logic, "EDIT_CONSENT_DIR_PRIMARY", primary)
    monkeypatch.setattr(pre_tool_use_logic, "EDIT_CONSENT_DIR_FALLBACK", fallback)
    monkeypatch.setattr(pre_tool_use_logic, "EDIT_CONSENT_DIR_TEMP", temp)
    return {"primary": primary, "fallback": fallback, "temp": temp}


class TestTieredPolicy:
    """Tier behavior in path validation."""

    def test_safe_root_config_is_auto_allowed(self, monkeypatch: pytest.MonkeyPatch) -> None:
        validator = PathValidator()
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.setattr(validator, "_is_git_tracked", lambda _path: False)

        is_safe, violation = validator.is_path_safe("P:/.claude/notes.md")
        assert is_safe is True
        assert violation == "SAFE_CLAUDE_CONFIG"

    def test_sensitive_paths_require_sensitive_edit_violation(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        validator = PathValidator()
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.setattr(validator, "_is_git_tracked", lambda _path: False)

        is_safe_hooks, violation_hooks = validator.is_path_safe(
            "P:/.claude/hooks/nonexistent_sensitive_gate.py"
        )
        assert is_safe_hooks is True
        assert violation_hooks == "SAFE_SUBDIRECTORY"

        is_safe_settings, violation_settings = validator.is_path_safe("P:/.claude/settings.json")
        assert is_safe_settings is False
        assert violation_settings == "CLAUDE_SENSITIVE_EDIT"

    def test_allowed_subdir_semantics_unchanged(self, monkeypatch: pytest.MonkeyPatch) -> None:
        validator = PathValidator()
        monkeypatch.delenv("CLAUDE_SESSION_ID", raising=False)
        monkeypatch.setattr(validator, "_is_git_tracked", lambda _path: False)

        is_safe, violation = validator.is_path_safe("P:/.claude/skills/example/SKILL.md")
        assert is_safe is True
        assert violation == "SAFE_SUBDIRECTORY"


class TestConsentPerMajorTask:
    """Approval token lifecycle and task-scoped pretool integration."""

    def test_pretool_allows_repeatedly_within_same_task(
        self, isolated_consent_dirs: dict[str, Path]
    ) -> None:
        file_path = "P:/.claude/settings.json"
        data = {
            "tool_name": "Edit",
            "tool_input": {"file_path": file_path},
            "session_id": "sess-approve-task",
            "terminal_id": "term-a",
            "major_task_id": "task-1",
        }

        blocked = PreToolUse_path_validator.run(data)
        assert blocked is not None
        assert blocked.get("decision") == "block"
        assert "approve edit" in (blocked.get("message") or "")

        canonical = pre_tool_use_logic.normalize_canonical_path(file_path)
        created, status = pre_tool_use_logic.create_claude_edit_consent_token(
            "sess-approve-task",
            canonical,
            terminal_id="term-a",
            major_task_id="task-1",
        )
        assert created is True
        assert status in {"created", "already_exists"}

        allowed_first = PreToolUse_path_validator.run(data)
        assert allowed_first is None

        allowed_again = PreToolUse_path_validator.run(data)
        assert allowed_again is None

    def test_pretool_allows_after_task_switch(self, isolated_consent_dirs: dict[str, Path]) -> None:
        file_path = "P:/.claude/settings.json"
        canonical = pre_tool_use_logic.normalize_canonical_path(file_path)
        created, status = pre_tool_use_logic.create_claude_edit_consent_token(
            "sess-approve-task",
            canonical,
            terminal_id="term-a",
            major_task_id="task-1",
        )
        assert created is True
        assert status in {"created", "already_exists"}

        switched = PreToolUse_path_validator.run(
            {
                "tool_name": "Edit",
                "tool_input": {"file_path": file_path},
                "session_id": "sess-approve-task",
                "terminal_id": "term-a",
                "major_task_id": "task-2",
            }
        )
        assert switched is None

    def test_mismatched_session_token_is_ignored(
        self, isolated_consent_dirs: dict[str, Path]
    ) -> None:
        canonical = pre_tool_use_logic.normalize_canonical_path("P:/.claude/hooks/PreToolUse.py")
        created, _ = pre_tool_use_logic.create_claude_edit_consent_token("sess-a", canonical)
        assert created is True

        ok, reason, _ = pre_tool_use_logic.check_claude_edit_consent(
            {"session_id": "sess-b"}, canonical
        )
        assert ok is False
        assert reason == "token_not_found"


class TestSessionStartScopedCleanup:
    """SessionStart cleanup behavior and scoping."""

    def test_cleanup_keeps_session_scoped_tokens_for_current_session_terminal(
        self, isolated_consent_dirs: dict[str, Path]
    ) -> None:
        path_a = "p:/.claude/hooks/a.py"
        path_b = "p:/.claude/hooks/b.py"
        path_c = "p:/.claude/hooks/c.py"

        # Same session+terminal, stale task -> should be removed
        assert (
            pre_tool_use_logic.create_claude_edit_consent_token(
                "sess-a", path_a, terminal_id="term-a", major_task_id="task-old"
            )[0]
            is True
        )
        # Same session+terminal, active task -> should remain
        assert (
            pre_tool_use_logic.create_claude_edit_consent_token(
                "sess-a", path_b, terminal_id="term-a", major_task_id="task-active"
            )[0]
            is True
        )
        # Different terminal -> should remain untouched
        assert (
            pre_tool_use_logic.create_claude_edit_consent_token(
                "sess-a", path_c, terminal_id="term-b", major_task_id="task-old"
            )[0]
            is True
        )

        removed = pre_tool_use_logic.cleanup_session_edit_consent_tokens(
            "sess-a", terminal_id="term-a", major_task_id="task-active"
        )
        assert removed == 0

        ok_active, reason_active, _ = pre_tool_use_logic.check_claude_edit_consent(
            {"session_id": "sess-a", "terminal_id": "term-a", "major_task_id": "task-active"},
            path_b,
        )
        assert ok_active is True
        assert reason_active == "consent_granted"

        ok_stale_task, reason_stale_task, _ = pre_tool_use_logic.check_claude_edit_consent(
            {"session_id": "sess-a", "terminal_id": "term-a", "major_task_id": "task-active"},
            path_a,
        )
        assert ok_stale_task is True
        assert reason_stale_task == "consent_granted"

        ok_other_terminal, reason_other_terminal, _ = pre_tool_use_logic.check_claude_edit_consent(
            {"session_id": "sess-a", "terminal_id": "term-b", "major_task_id": "task-old"}, path_c
        )
        assert ok_other_terminal is True
        assert reason_other_terminal == "consent_granted"

    def test_sessionstart_calls_cleanup_for_resolved_session(
        self, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        calls: list[str] = []

        fake_pre_tool = types.SimpleNamespace(
            resolve_session_id=lambda _data: "sess-main",
            resolve_terminal_id=lambda _data: "term-main",
            resolve_major_task_id=lambda _data, terminal_id=None: "task-main",
            cleanup_session_edit_consent_tokens=lambda sid,
            terminal_id=None,
            major_task_id=None: calls.append(f"{sid}|{terminal_id}|{major_task_id}"),
        )
        fake_retention = types.SimpleNamespace(cleanup=lambda: None)

        monkeypatch.setitem(sys.modules, "pre_tool_use_logic", fake_pre_tool)
        monkeypatch.setitem(sys.modules, "session_data_retention", fake_retention)
        monkeypatch.setattr(SessionStart, "SETUP_SEQUENCE", [])
        monkeypatch.setattr(
            sys, "stdin", io.StringIO(json.dumps({"hook_event_name": "SessionStart"}))
        )

        with pytest.raises(SystemExit) as exc_info:
            SessionStart.main()
        assert exc_info.value.code == 0

        assert calls == ["sess-main|term-main|task-main"]
        out = capsys.readouterr().out
        assert "{}" in out
