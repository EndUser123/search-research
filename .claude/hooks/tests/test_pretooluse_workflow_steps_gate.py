#!/usr/bin/env python3
"""Unit tests for PreToolUse_workflow_steps_gate.py

Tests the workflow_steps gate that enforces Skill tool usage for skills
with declared workflow_steps before allowing other tools.
"""

import json
import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path for imports
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from PreToolUse_workflow_steps_gate import (
    _clear_pending_intent,
    _get_intent_file,
    _get_terminal_id,
    _read_pending_intent,
    _safe_id,
    run,
)


@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state"
        state_dir.mkdir()

        # Patch the STATE_DIR in the module
        with patch("PreToolUse_workflow_steps_gate.STATE_DIR", state_dir):
            yield state_dir


@pytest.fixture
def mock_terminal_id():
    """Provide a mock terminal ID."""
    with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test_terminal_123"}):
        yield "test_terminal_123"


@pytest.fixture
def sample_intent_file(temp_state_dir, mock_terminal_id):
    """Create a sample pending intent file."""
    terminal_safe = _safe_id(mock_terminal_id)
    intent_file = temp_state_dir / f"pending_command_intent_{terminal_safe}.json"

    intent_data = {
        "skill": "pre-mortem",
        "prompt": "/pre-mortem",
        "prompt_fingerprint": "abc123",
        "timestamp": datetime.now().isoformat(),
        "session_id": "test_session",
        "terminal_id": mock_terminal_id,
    }

    intent_file.write_text(json.dumps(intent_data), encoding="utf-8")
    return intent_file


class TestSafeId:
    """Tests for _safe_id() function."""

    def test_safe_id_sanitizes_special_chars(self):
        """Test that special characters are replaced with underscores."""
        assert _safe_id("test-terminal_123") == "test-terminal_123"
        assert _safe_id("test/terminal\\123") == "test_terminal_123"
        assert _safe_id("test:terminal@123") == "test_terminal_123"


class TestTerminalIdDetection:
    """Tests for terminal ID detection."""

    def test_get_terminal_id_from_env(self):
        """Test getting terminal ID from CLAUDE_TERMINAL_ID env var."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "env_terminal_456"}):
            assert _get_terminal_id() == "env_terminal_456"

    def test_get_terminal_id_fallback_to_detection(self):
        """Test fallback to terminal_detection module."""
        with patch.dict(os.environ, {}, clear=False):
            # Remove all terminal ID env vars
            os.environ.pop("CLAUDE_TERMINAL_ID", None)
            os.environ.pop("TERMINAL_ID", None)

            # Mock the detection function
            with patch("skill_guard.utils.terminal_detection.detect_terminal_id", return_value="detected_789"):
                result = _get_terminal_id()
                assert result == "detected_789"

    def test_get_terminal_id_no_source(self):
        """Test when no terminal ID source is available."""
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CLAUDE_TERMINAL_ID", None)
            os.environ.pop("TERMINAL_ID", None)

            # Mock detection to return None
            with patch("skill_guard.utils.terminal_detection.detect_terminal_id", return_value=None):
                result = _get_terminal_id()
                assert result == ""


class TestIntentFileOperations:
    """Tests for intent file operations."""

    def test_read_pending_intent_success(self, sample_intent_file):
        """Test successfully reading pending intent."""
        intent = _read_pending_intent()
        assert intent is not None
        assert intent["skill"] == "pre-mortem"
        assert intent["prompt"] == "/pre-mortem"

    def test_read_pending_intent_missing_file(self, temp_state_dir):
        """Test reading when intent file doesn't exist."""
        intent = _read_pending_intent()
        assert intent is None

    def test_read_pending_intent_no_terminal_id(self):
        """Test reading when no terminal ID is available."""
        with patch("PreToolUse_workflow_steps_gate._get_terminal_id", return_value=""):
            result = _get_intent_file()
            assert result is None

    def test_clear_pending_intent(self, sample_intent_file):
        """Test clearing pending intent file."""
        # Verify file exists
        assert sample_intent_file.exists()

        # Clear it
        _clear_pending_intent()

        # Verify file is gone
        assert not sample_intent_file.exists()

    def test_clear_pending_intent_missing_file(self, temp_state_dir):
        """Test clearing when intent file doesn't exist (should not error)."""
        # Should not raise exception
        _clear_pending_intent()


class TestWorkflowStepsGate:
    """Tests for the main run() function."""

    def test_skill_tool_allowed_unconditionally(self, sample_intent_file):
        """Test that Skill tool is always allowed."""
        data = {"tool_name": "Skill"}
        result = run(data)
        assert result is None  # None means allow

        # Intent should be cleared
        intent = _read_pending_intent()
        assert intent is None

    def test_no_pending_intent_allows(self):
        """Test that tools are allowed when there's no pending intent."""
        with patch("PreToolUse_workflow_steps_gate._read_pending_intent", return_value=None):
            data = {"tool_name": "Read"}
            result = run(data)
            assert result is None

    @patch("skill_guard.breadcrumb.tracker._load_workflow_steps")
    def test_skill_with_workflow_steps_blocked(self, mock_load_steps, sample_intent_file):
        """Test that tools are blocked for skills with workflow_steps."""
        # Mock workflow_steps
        mock_load_steps.return_value = ["step1", "step2", "step3"]

        data = {"tool_name": "Read"}
        result = run(data)

        assert result is not None
        assert result["continue"] is False
        assert "SKILL WITH WORKFLOW STEPS DETECTED" in result["reason"]
        assert "/pre-mortem" in result["reason"]
        assert "3 declared workflow steps" in result["reason"]

    @patch("skill_guard.breadcrumb.tracker._load_workflow_steps")
    def test_skill_without_workflow_steps_allowed(self, mock_load_steps, sample_intent_file):
        """Test that tools are allowed for skills without workflow_steps (knowledge skills)."""
        # Mock no workflow_steps
        mock_load_steps.return_value = []

        data = {"tool_name": "Read"}
        result = run(data)
        assert result is None  # None means allow

    @patch("skill_guard.breadcrumb.tracker._load_workflow_steps")
    def test_load_workflow_steps_exception_fails_open(self, mock_load_steps, sample_intent_file):
        """Test that exceptions in _load_workflow_steps fail open (allow)."""
        # Mock exception
        mock_load_steps.side_effect = Exception("Test error")

        data = {"tool_name": "Read"}
        result = run(data)
        assert result is None  # Fail open - don't block

    def test_disabled_gate_allows_all(self, sample_intent_file):
        """Test that when gate is disabled, all tools are allowed."""
        with patch.dict(os.environ, {"WORKFLOW_STEPS_GATE_ENABLED": "false"}):
            data = {"tool_name": "Read"}
            result = run(data)
            assert result is None

    @patch("skill_guard.breadcrumb.tracker._load_workflow_steps")
    def test_stale_intent_is_cleared_and_allowed(self, mock_load_steps, sample_intent_file):
        """Old terminal-scoped intents should not block unrelated later prompts."""
        mock_load_steps.return_value = ["step1", "step2"]

        stale_intent = {
            "skill": "pre-mortem",
            "prompt": "/pre-mortem",
            "prompt_fingerprint": "abc123",
            "timestamp": (datetime.now() - timedelta(hours=1)).isoformat(),
            "session_id": "test_session",
            "terminal_id": "test_terminal_123",
        }
        sample_intent_file.write_text(json.dumps(stale_intent), encoding="utf-8")

        data = {"tool_name": "Read", "session_id": "test_session"}
        result = run(data)

        assert result is None
        assert not sample_intent_file.exists()

    @patch("skill_guard.breadcrumb.tracker._load_workflow_steps")
    def test_mismatched_terminal_metadata_is_cleared(self, mock_load_steps, sample_intent_file):
        """Intent files with mismatched terminal metadata should be discarded."""
        mock_load_steps.return_value = ["step1"]

        mismatched_terminal = {
            "skill": "pre-mortem",
            "prompt": "/pre-mortem",
            "timestamp": datetime.now().isoformat(),
            "session_id": "test_session",
            "terminal_id": "other_terminal",
        }
        sample_intent_file.write_text(json.dumps(mismatched_terminal), encoding="utf-8")

        data = {"tool_name": "Read", "session_id": "test_session"}
        result = run(data)

        assert result is None
        assert not sample_intent_file.exists()


class TestTerminalIsolation:
    """Tests for terminal isolation."""

    def test_terminal_scoped_intent_files(self, temp_state_dir):
        """Test that each terminal gets its own intent file."""
        # Terminal 1
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "terminal_1"}):
            file_1 = _get_intent_file()
            assert "terminal_1" in str(file_1)

        # Terminal 2
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "terminal_2"}):
            file_2 = _get_intent_file()
            assert "terminal_2" in str(file_2)

        # Files should be different
        assert file_1 != file_2

    def test_no_cross_terminal_contamination(self, temp_state_dir):
        """Test that intent from one terminal doesn't affect another."""
        # Terminal 1 writes intent
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "terminal_1"}):
            file_1 = _get_intent_file()
            file_1.write_text(json.dumps({"skill": "skill1"}))

        # Terminal 2 should not see terminal 1's intent
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "terminal_2"}):
            intent = _read_pending_intent()
            assert intent is None  # Should not see terminal_1's intent


class TestErrorHandling:
    """Tests for error handling and edge cases."""

    def test_malformed_intent_file(self, temp_state_dir, mock_terminal_id):
        """Test handling of malformed JSON in intent file."""
        terminal_safe = _safe_id(mock_terminal_id)
        intent_file = temp_state_dir / f"pending_command_intent_{terminal_safe}.json"

        # Write invalid JSON
        intent_file.write_text("{invalid json}")

        # Should return None (graceful degradation)
        intent = _read_pending_intent()
        assert intent is None

    def test_intent_without_skill_field(self, temp_state_dir, mock_terminal_id):
        """Test intent file missing the 'skill' field."""
        terminal_safe = _safe_id(mock_terminal_id)
        intent_file = temp_state_dir / f"pending_command_intent_{terminal_safe}.json"

        intent_data = {
            "prompt": "/test",
            # Missing "skill" field
        }

        intent_file.write_text(json.dumps(intent_data))

        # Should allow (no skill to check)
        with patch("skill_guard.breadcrumb.tracker._load_workflow_steps", return_value=[]):
            data = {"tool_name": "Read"}
            result = run(data)
            assert result is None

    def test_empty_tool_name(self, sample_intent_file):
        """Test handling of empty tool_name."""
        with patch("skill_guard.breadcrumb.tracker._load_workflow_steps", return_value=[]):
            data = {"tool_name": ""}
            result = run(data)
            # Empty tool_name is treated like any other non-Skill tool
            # But without workflow_steps, it should be allowed
            assert result is None
