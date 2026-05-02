"""Tests for PreToolUse_skill_question_gate.py and Stop_skill_question_marker.py.

Tests the one-question-max enforcement mechanism.

From ADR-20260329-llm-consultation-pattern-fix.md — CHANGE-003
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

# Add __lib to path for FileLock
sys.path.insert(0, str(Path(__file__).parent.parent / "__lib"))

# Plugin src for skill-guard hooks (single source of truth)
_PLUGIN_SRC = Path("P:/packages/skill-guard/src")
if _PLUGIN_SRC.exists():
    sys.path.insert(1, str(_PLUGIN_SRC))

from skill_guard.PreToolUse.PreToolUse_skill_question_gate import run as pre_run
import skill_guard.PreToolUse.PreToolUse_skill_question_gate as pre_mod
import Stop_skill_question_marker as stop_mod
from Stop_skill_question_marker import run as stop_run


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def session_id():
    """Unique session ID for test isolation."""
    return f"test_session_{os.getpid()}_{id(object())}"


@pytest.fixture
def state_dir(tmp_path, monkeypatch):
    """Temporary state directory for test markers."""
    state = tmp_path / ".claude" / "hooks" / "state"
    state.mkdir(parents=True)

    # Override the module-level _STATE_DIR to use our temp directory
    monkeypatch.setattr(pre_mod, "_STATE_DIR", state)
    monkeypatch.setattr(stop_mod, "_STATE_DIR", state)

    monkeypatch.setenv("HOME", str(tmp_path))  # Ensure Path.home() returns tmp_path
    return state


@pytest.fixture
def disable_gates(monkeypatch):
    """Disable env-gate checks for unit testing."""
    monkeypatch.setenv("SKILL_QUESTION_GATE_ENABLED", "true")
    monkeypatch.setenv("STOP_QUESTION_MARKER_ENABLED", "true")
    return True  # suppress unused warning


# ---------------------------------------------------------------------------
# PreToolUse_skill_question_gate.py tests
# ---------------------------------------------------------------------------

class TestPreToolUseSkillQuestionGate:
    """Tests for PreToolUse_skill_question_gate."""

    def test_skill_invocation_creates_marker(self, session_id, state_dir, disable_gates):
        """Skill invocation should create skill_invoked marker and clear question marker."""
        # Create a mock question marker to verify it gets cleared
        question_marker = state_dir / f"question_asked_{session_id}.json"
        question_marker.parent.mkdir(parents=True, exist_ok=True)
        question_marker.write_text(json.dumps({"count": 5}))

        data = {
            "tool_name": "Skill",
            "session_id": session_id,
            "tool_input": {"skill": "/planning"},
        }

        result = pre_run(data)

        assert result["continue"] is True
        # Skill marker should exist
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        assert skill_marker.exists()
        # Question marker should be cleared
        assert not question_marker.exists()

    def test_non_skill_tool_clears_markers_after_execution(self, session_id, state_dir, disable_gates):
        """Non-Skill tool execution should clear markers after skill was invoked."""
        # Pre-create skill marker (simulating skill was invoked earlier)
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        data = {
            "tool_name": "Bash",
            "session_id": session_id,
            "tool_input": {},
        }

        result = pre_run(data)

        assert result["continue"] is True
        # Markers should be cleared after execution
        assert not skill_marker.exists()

    def test_one_question_allowed(self, session_id, state_dir, disable_gates):
        """Exactly one question should be allowed — not blocked."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        question_marker = state_dir / f"question_asked_{session_id}.json"
        question_marker.write_text(json.dumps({"count": 1, "questions_seen": 1}))

        data = {
            "tool_name": "Bash",
            "session_id": session_id,
            "tool_input": {},
        }

        result = pre_run(data)

        assert result["continue"] is True

    def test_more_than_one_question_blocked(self, session_id, state_dir, disable_gates):
        """More than one question should be blocked."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        question_marker = state_dir / f"question_asked_{session_id}.json"
        question_marker.write_text(json.dumps({"count": 2, "questions_seen": 2}))

        data = {
            "tool_name": "Bash",
            "session_id": session_id,
            "tool_input": {},
        }

        result = pre_run(data)

        assert result["continue"] is False
        assert "ONE-QUESTION-MAX EXCEEDED" in result["reason"]

    def test_no_skill_invoked_allows_all_tools(self, session_id, state_dir, disable_gates):
        """Without a skill invocation, all tools should be allowed."""
        data = {
            "tool_name": "Bash",
            "session_id": session_id,
            "tool_input": {},
        }

        result = pre_run(data)

        assert result["continue"] is True

    def test_disabled_via_env_var(self, session_id, state_dir, monkeypatch):
        """Gate should be disabled when env var is false."""
        monkeypatch.setenv("SKILL_QUESTION_GATE_ENABLED", "false")

        data = {
            "tool_name": "Skill",
            "session_id": session_id,
            "tool_input": {"skill": "/planning"},
        }

        result = pre_run(data)

        assert result["continue"] is True


# ---------------------------------------------------------------------------
# Stop_skill_question_marker.py tests
# ---------------------------------------------------------------------------

class TestStopSkillQuestionMarker:
    """Tests for Stop_skill_question_marker."""

    def test_question_mark_increments_count(self, session_id, state_dir, disable_gates):
        """A question mark in response should increment the question count."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        data = {
            "session_id": session_id,
            "response_text": "What would you like me to plan?",
        }

        result = stop_run(data)

        assert result["allow"] is True
        question_marker = state_dir / f"question_asked_{session_id}.json"
        assert question_marker.exists()
        state = json.loads(question_marker.read_text())
        assert state["count"] == 1

    def test_multiple_questions_count_each_mark(self, session_id, state_dir, disable_gates):
        """Each question mark should be counted separately."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        data = {
            "session_id": session_id,
            "response_text": "What? How? Why?",
        }

        result = stop_run(data)

        question_marker = state_dir / f"question_asked_{session_id}.json"
        state = json.loads(question_marker.read_text())
        assert state["count"] == 3  # 3 question marks

    def test_no_skill_no_tracking(self, session_id, state_dir, disable_gates):
        """Without a skill invocation, questions should not be tracked."""
        data = {
            "session_id": session_id,
            "response_text": "What would you like me to do?",
        }

        result = stop_run(data)

        assert result["allow"] is True
        question_marker = state_dir / f"question_asked_{session_id}.json"
        assert not question_marker.exists()

    def test_no_question_text_allowed(self, session_id, state_dir, disable_gates):
        """Response without question marks should be allowed."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        data = {
            "session_id": session_id,
            "response_text": "I'll help you with that.",
        }

        result = stop_run(data)

        assert result["allow"] is True

    def test_accumulates_across_turns(self, session_id, state_dir, disable_gates):
        """Question count should accumulate across multiple turns."""
        skill_marker = state_dir / f"skill_invoked_{session_id}.json"
        skill_marker.parent.mkdir(parents=True, exist_ok=True)
        skill_marker.write_text(json.dumps({"invoked": True}))

        question_marker = state_dir / f"question_asked_{session_id}.json"
        question_marker.write_text(json.dumps({"count": 1, "questions_seen": 1}))

        data = {
            "session_id": session_id,
            "response_text": "Another question?",
        }

        result = stop_run(data)

        state = json.loads(question_marker.read_text())
        assert state["count"] == 2  # accumulated

    def test_disabled_via_env_var(self, session_id, state_dir, monkeypatch):
        """Marker should be disabled when env var is false."""
        monkeypatch.setenv("STOP_QUESTION_MARKER_ENABLED", "false")

        data = {
            "session_id": session_id,
            "response_text": "What?",
        }

        result = stop_run(data)

        assert result["allow"] is True
