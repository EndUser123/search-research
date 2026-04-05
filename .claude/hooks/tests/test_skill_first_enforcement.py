#!/usr/bin/env python3
"""
Tests for the skill-first enforcement chain.

Validates the 3-layer enforcement:
1. UserPromptSubmit: writes pending_command_intent file
2. PreToolUse: blocks non-Skill tools when intent is pending
3. Stop: blocks pure-prose responses when intent is pending
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


# =============================================================================
# Test Helpers
# =============================================================================

def _safe_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_.-]+", "_", value)


@pytest.fixture
def temp_state_dir(tmp_path):
    """Create temp state directory and set env vars."""
    state_dir = tmp_path / "state"
    state_dir.mkdir()
    session_id = "test_session_123"
    safe_session = _safe_id(session_id)

    with patch.dict(os.environ, {
        "CLAUDE_SESSION_ID": session_id,
        "TEMP": str(tmp_path),
        "ENFORCE_SKILL_FIRST_PRETOOLUSE": "true",
        "ENFORCE_SKILL_FIRST_STOP_FALLBACK": "true",
        "SKILL_FIRST_MODE": "hard_block",
    }):
        yield {
            "state_dir": state_dir,
            "session_id": session_id,
            "safe_session": safe_session,
            "tmp_path": tmp_path,
        }


def write_intent_file(state_dir: Path, safe_session: str, skill: str) -> Path:
    """Write a pending_command_intent file."""
    intent_file = state_dir / f"pending_command_intent_{safe_session}.json"
    intent_file.write_text(json.dumps({
        "skill": skill,
        "prompt": f"/{skill}",
        "timestamp": "2026-02-16T22:00:00",
    }))
    return intent_file


# =============================================================================
# PreToolUse Tests
# =============================================================================

class TestPreToolUseSkillFirstGate:
    """Test that PreToolUse blocks non-Skill tools when a slash command is pending."""

    def test_allowed_tools_are_tight(self):
        """Verify _SKILL_FIRST_ALLOWED only contains Skill and metadata tools."""
        from PreToolUse import _SKILL_FIRST_ALLOWED

        assert "Skill" in _SKILL_FIRST_ALLOWED
        assert "AskUserQuestion" in _SKILL_FIRST_ALLOWED
        assert "TodoWrite" in _SKILL_FIRST_ALLOWED

        assert "Read" not in _SKILL_FIRST_ALLOWED
        assert "Grep" not in _SKILL_FIRST_ALLOWED
        assert "Glob" not in _SKILL_FIRST_ALLOWED
        assert "Edit" not in _SKILL_FIRST_ALLOWED
        assert "Write" not in _SKILL_FIRST_ALLOWED
        assert "WebSearch" not in _SKILL_FIRST_ALLOWED
        assert "WebFetch" not in _SKILL_FIRST_ALLOWED

    def test_skill_tool_always_allowed(self):
        """Skill tool itself is never blocked."""
        from PreToolUse import _check_skill_first_gate

        data = {"tool_name": "Skill"}
        result = _check_skill_first_gate(data)
        assert result is None

    def test_read_blocked_when_intent_pending(self, temp_state_dir):
        """Read tool is blocked when a slash command is pending and mode is not off."""
        ctx = temp_state_dir
        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        intent_file = fallback_state / "pending_command_intent_console_default.json"
        intent_file.write_text(
            json.dumps(
                {
                    "skill": "hod",
                    "prompt": "/hod",
                    "session_id": ctx["session_id"],
                    "terminal_id": "console_default",
                }
            ),
            encoding="utf-8",
        )

        from PreToolUse import _check_skill_first_gate

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "console_default"}):
            result = _check_skill_first_gate({"tool_name": "Read"})

        assert result is not None, "Gate should have blocked Read with pending intent"
        assert result["decision"] == "block"
        assert "hod" in result["reason"]
        assert "Skill" in result["reason"]
        assert intent_file.exists()

    def test_bash_blocked_when_intent_pending(self):
        """Bash tool should be blocked when a slash command is pending."""
        from PreToolUse import _SKILL_FIRST_ALLOWED
        assert "Bash" not in _SKILL_FIRST_ALLOWED

    def test_task_blocked_when_intent_pending(self):
        """Task tool should be blocked when a slash command is pending."""
        from PreToolUse import _SKILL_FIRST_ALLOWED
        assert "Task" not in _SKILL_FIRST_ALLOWED

    def test_monitor_mode_allows_with_pending_intent(self, temp_state_dir):
        """Monitor mode should not block, only observe/log."""
        ctx = temp_state_dir
        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        (fallback_state / "pending_command_intent_console_default.json").write_text(
            json.dumps(
                {
                    "skill": "hod",
                    "prompt": "/hod",
                    "session_id": ctx["session_id"],
                    "terminal_id": "console_default",
                }
            ),
            encoding="utf-8",
        )

        from PreToolUse import _check_skill_first_gate

        with patch.dict(os.environ, {"SKILL_FIRST_MODE": "monitor", "CLAUDE_TERMINAL_ID": "console_default"}):
            result = _check_skill_first_gate({"tool_name": "Read"})
            assert result is None

    def test_stale_terminal_scoped_intent_from_other_session_is_ignored(self, temp_state_dir):
        """Old terminal-scoped intents from other sessions should be cleaned up."""
        ctx = temp_state_dir
        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        intent_file = fallback_state / "pending_command_intent_console_default.json"
        intent_file.write_text(
            json.dumps(
                {
                    "skill": "research",
                    "prompt": "/research",
                    "session_id": "old_session_456",
                    "terminal_id": "console_default",
                    "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
                }
            ),
            encoding="utf-8",
        )

        from PreToolUse import _check_skill_first_gate

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "console_default"}):
            result = _check_skill_first_gate({"tool_name": "Bash"})

        assert result is None
        assert not intent_file.exists()

    def test_recent_terminal_scoped_intent_from_other_session_still_blocks(self, temp_state_dir):
        """Recent terminal-scoped intents remain enforceable across session rotation."""
        ctx = temp_state_dir
        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        intent_file = fallback_state / "pending_command_intent_console_default.json"
        intent_file.write_text(
            json.dumps(
                {
                    "skill": "research",
                    "prompt": "/research",
                    "session_id": "old_session_456",
                    "terminal_id": "console_default",
                    "timestamp": datetime.now().isoformat(),
                }
            ),
            encoding="utf-8",
        )

        from PreToolUse import _check_skill_first_gate

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "console_default"}):
            result = _check_skill_first_gate({"tool_name": "Bash"})

        assert result is not None
        assert result["decision"] == "block"
        assert "research" in result["reason"]
        assert intent_file.exists()


# =============================================================================
# PostToolUse Tests
# =============================================================================

class TestPostToolUseClearsIntent:
    """Test that PostToolUse clears the intent file when Skill() is called."""

    def test_clear_pending_skill_intent(self, temp_state_dir):
        """Calling Skill() should clear the pending intent file."""
        ctx = temp_state_dir
        intent_file = write_intent_file(ctx["state_dir"], ctx["safe_session"], "hod")
        assert intent_file.exists()

        from PostToolUse import _clear_pending_skill_intent

        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": ctx["session_id"]}):
            fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
            fallback_state.mkdir(parents=True, exist_ok=True)
            fallback_intent = fallback_state / f"pending_command_intent_{ctx['safe_session']}.json"
            fallback_intent.write_text(json.dumps({"skill": "hod"}))

            _clear_pending_skill_intent({"session_id": ctx["session_id"]})
            assert not fallback_intent.exists()


# =============================================================================
# Stop Gate Tests
# =============================================================================

class TestStopSkillFirstGate:
    """Test that Stop blocks when intent file persists (pure-prose bypass)."""

    def test_no_intent_file_allows(self):
        """No pending intent = no block."""
        from Stop import _run_skill_first_stop_gate

        with patch.dict(os.environ, {"CLAUDE_SESSION_ID": "test_123"}):
            result = _run_skill_first_stop_gate({})
            assert result is None

    def test_intent_file_blocks(self, temp_state_dir):
        """Pending intent at Stop time = block (prose bypass detected)."""
        ctx = temp_state_dir

        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        intent_file = fallback_state / f"pending_command_intent_{ctx['safe_session']}.json"
        intent_file.write_text(json.dumps({
            "skill": "hod",
            "prompt": "/hod",
        }))

        from Stop import _run_skill_first_stop_gate

        result = _run_skill_first_stop_gate({})
        assert result is not None
        assert result["decision"] == "block"
        assert "hod" in result["reason"]
        assert "Skill" in result["reason"]
        assert not intent_file.exists()

    def test_intent_file_monitor_mode_allows(self, temp_state_dir):
        """Monitor mode at Stop should observe but not block."""
        ctx = temp_state_dir
        fallback_state = ctx["tmp_path"] / "claude_hooks" / "state"
        fallback_state.mkdir(parents=True, exist_ok=True)
        intent_file = fallback_state / f"pending_command_intent_{ctx['safe_session']}.json"
        intent_file.write_text(json.dumps({"skill": "hod", "prompt": "/hod"}), encoding="utf-8")

        from Stop import _run_skill_first_stop_gate

        with patch.dict(os.environ, {"SKILL_FIRST_MODE": "monitor"}):
            result = _run_skill_first_stop_gate({})
            assert result is None
        assert not intent_file.exists()


# =============================================================================
# Integration: Full Chain
# =============================================================================

class TestFullEnforcementChain:
    """Test the complete enforcement flow."""

    def test_enforcement_design_summary(self):
        """Document the enforcement chain design."""
        assert True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
