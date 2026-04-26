#!/usr/bin/env python3
"""Tests for Stop_skill_dir_correlation_gate.py."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Stop_skill_dir_correlation_gate import run


class TestSkillDirCorrelationGate:
    """Regression suite for Stop_skill_dir_correlation_gate.py."""

    def test_incident_repro_mismatch(self):
        """User asks about /ai-pcli but reads ai-cli/ instead — advisory fires."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-cli/SKILL.md",
                "file_path": "",
                "id": "1",
                "terminal_id": "t1",
            }
        ]
        data = {
            "session_id": "sess-test",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        assert result is not None
        assert result.get("decision") == "allow"
        msg = result.get("systemMessage", "")
        assert "ai-pcli" in msg
        assert "ai-cli" in msg

    def test_correct_skill_dir_no_advisory(self):
        """User asks about /ai-pcli and reads ai-pcli/ — no advisory."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-pcli/SKILL.md",
                "file_path": "",
                "id": "2",
                "terminal_id": "t1",
            }
        ]
        data = {
            "session_id": "sess-test",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        assert result is None

    def test_no_slash_skill_in_message(self):
        """User message has no /skill-name — no advisory."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-cli/SKILL.md",
                "file_path": "",
                "id": "3",
                "terminal_id": "t1",
            }
        ]
        data = {
            "session_id": "sess-test",
            "conversation": [{"role": "user", "content": "Tell me about recipe files"}],
        }
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        assert result is None

    def test_no_skills_dir_events(self):
        """Tool events don't reference .claude/skills/ — no advisory."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/hooks/Stop.py",
                "file_path": "",
                "id": "4",
                "terminal_id": "t1",
            }
        ]
        data = {
            "session_id": "sess-test",
            "conversation": [{"role": "user", "content": "What does /ai-pcli use?"}],
        }
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        assert result is None

    def test_no_conversation_field(self):
        """Missing conversation key returns None early."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-cli/SKILL.md",
                "file_path": "",
                "id": "5",
                "terminal_id": "t1",
            }
        ]
        data = {"session_id": "sess-test"}  # no conversation
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        assert result is None

    def test_cross_skill_pass(self):
        """User asks about /ai-pcli vs /ai-cli — reads both — no advisory (bypass)."""
        events = [
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-pcli/SKILL.md",
                "file_path": "",
                "id": "6",
                "terminal_id": "t1",
            },
            {
                "name": "Read",
                "command": "P:/.claude/skills/ai-cli/SKILL.md",
                "file_path": "",
                "id": "7",
                "terminal_id": "t1",
            },
        ]
        data = {
            "session_id": "sess-test",
            "conversation": [{"role": "user", "content": "/ai-pcli vs /ai-cli?"}],
        }
        with patch(
            "evidence_scope.load_scoped_tool_events",
            return_value=events,
        ):
            result = run(data)
        # Both skills accessed — no mismatch advisory
        assert result is None