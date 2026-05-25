#!/usr/bin/env python3
"""Tests for Phase 2 skill-dir prevention (writer + gate v2.0).

v2.0: Glob/Grep are READ_ONLY and always pass. Only executing tools
(Bash, Write, Edit) are scope-gated by the skill context state file.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from UserPromptSubmit_modules.skill_context_writer import (
    _extract_skill_from_prompt,
    _resolve_skill_dir,
    _safe_id,
    skill_context_writer,
)
from UserPromptSubmit_modules.base import HookContext

# Import gate via plugin path
sys.path.insert(0, str(Path(r"P:\packages\skill-guard\src")))
from skill_guard.PreToolUse.PreToolUse_skill_dir_gate import run as gate_run

# ---------------------------------------------------------------------------
# Writer tests
# ---------------------------------------------------------------------------

class TestSkillContextWriter:
    """Tests for skill_context_writer.py."""

    def test_skill_found_file_written(self, tmp_path: Path):
        with (
            patch(
                "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
                tmp_path / "state" / "skill_context",
            ),
            patch(
                "UserPromptSubmit_modules.skill_context_writer._resolve_skill_dir",
                return_value=".claude/skills/ai-pcli",
            ),
        ):
            ctx = HookContext(
                prompt="/ai-pcli do something",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert sf.exists()
            data = json.loads(sf.read_text(encoding="utf-8"))
            assert data["expected_skill"] == "ai-pcli"
            assert data["expected_dir"] == ".claude/skills/ai-pcli"
            assert data["resolved"] is True
            assert data["terminal_id"] == "term-1"

    def test_no_skill_file_cleared(self, tmp_path: Path):
        state_dir = tmp_path / "state" / "skill_context"
        state_dir.mkdir(parents=True)
        sf = state_dir / "skill_context_term-1.json"
        sf.write_text("{}")

        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            state_dir,
        ):
            ctx = HookContext(
                prompt="what time is it",
                data={},
                session_id="sess-1",
                terminal_id="term-1",
            )
            skill_context_writer(ctx)

        assert not sf.exists()

    def test_false_positive_single_char_excluded(self, tmp_path: Path):
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            tmp_path / "state" / "skill_context",
        ):
            ctx = HookContext(prompt="/v do something", data={}, session_id="sess-1", terminal_id="term-1")
            skill_context_writer(ctx)
            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert not sf.exists()

    def test_known_non_skill_excluded(self, tmp_path: Path):
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._STATE_DIR",
            tmp_path / "state" / "skill_context",
        ):
            ctx = HookContext(prompt="/README do something", data={}, session_id="sess-1", terminal_id="term-1")
            skill_context_writer(ctx)
            sf = tmp_path / "state" / "skill_context" / "skill_context_term-1.json"
            assert not sf.exists()

    def test_extract_skill_from_prompt(self):
        assert _extract_skill_from_prompt("/ai-pcli do something") == "ai-pcli"
        assert _extract_skill_from_prompt("use /search now") == "search"
        assert _extract_skill_from_prompt("no skill here") is None
        assert _extract_skill_from_prompt("/v") is None
        assert _extract_skill_from_prompt("/README") is None

    def test_safe_id(self):
        assert _safe_id("term-1") == "term-1"
        assert _safe_id("term:1") == "term_1"
        assert _safe_id("term/1") == "term_1"


# ---------------------------------------------------------------------------
# Resolver tests
# ---------------------------------------------------------------------------

class TestResolveSkillDir:
    """Tests for _resolve_skill_dir."""

    def test_nonexistent_returns_none(self):
        assert _resolve_skill_dir("xyz-nonexistent-skill-12345") is None

    def test_local_skill_if_exists(self, tmp_path: Path):
        with patch(
            "UserPromptSubmit_modules.skill_context_writer._LOCAL_SKILLS_DIR",
            tmp_path / "skills",
        ):
            (tmp_path / "skills" / "my-skill").mkdir(parents=True)
            result = _resolve_skill_dir("my-skill")
            assert result == ".claude/skills/my-skill"

    def test_plugin_cache_skill(self):
        result = _resolve_skill_dir("chs")
        if result is not None:
            assert "search-research" in result
            assert "chs" in result


# ---------------------------------------------------------------------------
# Gate tests — v2.0: read-only tools pass, executing tools scope-gated
# ---------------------------------------------------------------------------

REAL_STATE_DIR = Path(r"P:/.claude/hooks/state/skill_context")


def _write_state(terminal_id: str, state_data: dict | None) -> None:
    sf = REAL_STATE_DIR / f"skill_context_{terminal_id}.json"
    if state_data is not None:
        REAL_STATE_DIR.mkdir(parents=True, exist_ok=True)
        sf.write_text(json.dumps(state_data), encoding="utf-8")
    elif sf.exists():
        sf.unlink()


def _cleanup_state(terminal_id: str) -> None:
    sf = REAL_STATE_DIR / f"skill_context_{terminal_id}.json"
    if sf.exists():
        try:
            sf.unlink()
        except OSError:
            pass


class TestReadOnlyToolsAlwaysPass:
    """v2.0: Glob, Grep, Read always pass regardless of skill context."""

    def test_glob_always_allowed(self):
        tid = "ro-glob"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Glob", "tool_input": {"pattern": "**/*.md"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_grep_always_allowed(self):
        tid = "ro-grep"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Grep", "tool_input": {"path": "src/**/*.py"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_read_always_allowed(self):
        tid = "ro-read"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Read", "tool_input": {"file_path": "/some/random/path.py"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)


class TestExecuteToolsScoped:
    """v2.0: Bash, Write, Edit are scope-gated by skill context."""

    def test_scoped_bash_allowed(self):
        tid = "ex-scop"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Bash", "tool_input": {"command": "ls .claude/skills/ai-pcli/"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_unscoped_bash_blocked(self):
        tid = "ex-unscop"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Bash", "tool_input": {"command": "ls /tmp/"}, "terminal_id": tid})
            assert result["continue"] is False
            assert "BLOCKED" in result["reason"]
        finally:
            _cleanup_state(tid)

    def test_scoped_write_allowed(self):
        tid = "ex-scop-w"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Write", "tool_input": {"file_path": "P:/.claude/skills/ai-pcli/config.json"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_unscoped_write_blocked(self):
        tid = "ex-unscop-w"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Write", "tool_input": {"file_path": "P:/some/other/path.json"}, "terminal_id": tid})
            assert result["continue"] is False
            assert "BLOCKED" in result["reason"]
        finally:
            _cleanup_state(tid)

    def test_no_state_file_allow(self):
        tid = "ex-nostate"
        _cleanup_state(tid)
        try:
            result = gate_run({"tool_name": "Bash", "tool_input": {"command": "ls /tmp/"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_unknown_tool_allow(self):
        tid = "ex-unknown"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "SomeUnknownTool", "tool_input": {"arg": "value"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_backslash_normalization_bash(self):
        tid = "ex-bslash"
        state = {"expected_skill": "ai-pcli", "expected_dir": ".claude/skills/ai-pcli"}
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Bash", "tool_input": {"command": "dir .claude\\skills\\ai-pcli\\"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)


class TestPluginSkillResolution:
    """Plugin skill dirs resolved from C-drive cache should match in gate."""

    def test_skill_name_segment_in_bash(self):
        tid = "plug-name"
        state = {
            "expected_skill": "chs",
            "expected_dir": "C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.9/skills/chs",
        }
        try:
            _write_state(tid, state)
            result = gate_run({"tool_name": "Bash", "tool_input": {"command": "python skills/chs/scripts/chs_cli.py"}, "terminal_id": tid})
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)

    def test_full_cache_path_in_write(self):
        tid = "plug-full"
        state = {
            "expected_skill": "chs",
            "expected_dir": "C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.9/skills/chs",
        }
        try:
            _write_state(tid, state)
            result = gate_run({
                "tool_name": "Write",
                "tool_input": {"file_path": "C:/Users/brsth/.claude/plugins/cache/local/search-research/0.1.9/skills/chs/scripts/test.py"},
                "terminal_id": tid,
            })
            assert result["continue"] is True
        finally:
            _cleanup_state(tid)