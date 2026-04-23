"""Tests for _extract_slash_command_goal in PreCompact_handoff_capture.py.

Run with: pytest P:/.claude/hooks/tests/test_slash_command_goal.py -v
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from PreCompact_handoff_capture import _extract_slash_command_goal


class TestExplicitArgs:
    """Slash command with explicit argument — arg IS the subject."""

    def test_gto_with_flag(self):
        goal, origin = _extract_slash_command_goal("/gto --analyze", [])
        assert goal == "/gto --analyze"
        assert origin == "slash_command_with_args"


class TestInferredSubject:
    """Bare slash command (no args) — subject inferred from active_files."""

    def test_uses_first_active_file(self):
        goal, _ = _extract_slash_command_goal(
            "/tldr-code",
            ["packages/handoff/core.py", "packages/handoff/utils.py"],
        )
        assert "packages/handoff/core.py" in goal


class TestBareCommand:
    """Bare slash command with no files — minimal capture."""

    def test_bare_command_empty_files(self):
        goal, origin = _extract_slash_command_goal("/gto", [])
        assert goal == "/gto"
        assert origin == "slash_command_bare"


class TestNonSlashCommand:
    """Non-slash messages must return None (normal path taken)."""

    def test_plain_instruction_returns_none(self):
        assert _extract_slash_command_goal("fix the bug in parser.py", []) is None

    def test_question_returns_none(self):
        assert _extract_slash_command_goal("how does handoff work?", []) is None

    def test_empty_string_returns_none(self):
        assert _extract_slash_command_goal("", []) is None

    def test_none_input_returns_none(self):
        assert _extract_slash_command_goal(None, []) is None

    def test_unix_path_returns_none(self):
        # "/home/user/file.py" must NOT be mistaken for a slash command
        assert _extract_slash_command_goal("/home/user/file.py", []) is None
