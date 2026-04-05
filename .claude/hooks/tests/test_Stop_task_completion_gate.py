#!/usr/bin/env python3
"""Tests for Stop_task_completion_gate.py."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Import the module directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from Stop_task_completion_gate import (
    _is_task_completion,
    _load_task_data,
    check,
    run,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def temp_state_dir(monkeypatch, tmp_path):
    """Create a temporary state directory for task data."""
    state_dir = tmp_path / "task_tracker"
    state_dir.mkdir()
    monkeypatch.setenv("TASK_TRACKER_STATE_DIR", str(state_dir))
    return state_dir


@pytest.fixture
def sample_task_state(temp_state_dir):
    """Create a sample task state file."""
    state_file = temp_state_dir / "console_test_tasks.json"
    state = {
        "tasks": {
            "123": {
                "subject": "Fix authentication bug in login flow",
                "description": "When users try to login with special characters in password, the system shows error and crashes",
            },
            "456": {
                "subject": "short",  # too short
                "description": "fix",  # too short, missing indicators
            },
            "789": {
                "subject": "Update documentation for API",
                "description": "",  # empty description
            },
        }
    }
    state_file.write_text(json.dumps(state))
    return state_file


# ---------------------------------------------------------------------------
# _is_task_completion
# ---------------------------------------------------------------------------

class TestIsTaskCompletion:
    """Tests for _is_task_completion helper."""

    def test_task_update_completed(self):
        """TaskUpdate with status=completed returns True."""
        events = [
            {"name": "TaskUpdate", "input": {"status": "completed", "taskId": "123"}}
        ]
        is_compl, _, task_id = _is_task_completion(events)
        assert is_compl is True
        assert task_id == "123"

    def test_task_update_in_progress(self):
        """TaskUpdate with status=in_progress returns False."""
        events = [
            {"name": "TaskUpdate", "input": {"status": "in_progress", "taskId": "123"}}
        ]
        is_compl, _, _ = _is_task_completion(events)
        assert is_compl is False

    def test_task_update_pending(self):
        """TaskUpdate with status=pending returns False."""
        events = [
            {"name": "TaskUpdate", "input": {"status": "pending", "taskId": "123"}}
        ]
        is_compl, _, _ = _is_task_completion(events)
        assert is_compl is False

    def test_no_tool_events(self):
        """Empty tool events returns False."""
        is_compl, _, _ = _is_task_completion([])
        assert is_compl is False

    def test_other_tool_event(self):
        """Non-TaskUpdate tool event returns False."""
        events = [{"name": "Read", "input": {"file_path": "foo.py"}}]
        is_compl, _, _ = _is_task_completion(events)
        assert is_compl is False


# ---------------------------------------------------------------------------
# _load_task_data
# ---------------------------------------------------------------------------

class TestLoadTaskData:
    """Tests for _load_task_data helper."""

    def test_load_valid_task(self, sample_task_state):
        """Successfully loads a valid task by ID."""
        task = _load_task_data("123")
        assert task is not None
        assert task["subject"] == "Fix authentication bug in login flow"

    def test_task_not_found(self, sample_task_state):
        """Returns None for non-existent task ID."""
        task = _load_task_data("999")
        assert task is None

    def test_no_state_file(self, temp_state_dir):
        """Returns None when no state file exists."""
        # Remove the state file
        for f in temp_state_dir.glob("*_tasks.json"):
            f.unlink()
        task = _load_task_data("123")
        assert task is None


# ---------------------------------------------------------------------------
# check() / run()
# ---------------------------------------------------------------------------

class TestBlockTaskCompletionWithoutDocs:
    """Tests for blocking task completion without self-documentation."""

    def test_block_task_with_short_subject(self, sample_task_state, monkeypatch):
        """Blocks when subject is fewer than 10 characters."""
        # Mock the task state path to point to our sample
        def mock_get_state_path(terminal_id=None):
            return sample_task_state

        monkeypatch.setattr(
            "Stop_task_completion_gate._get_task_state_path",
            mock_get_state_path,
        )

        data = {
            "tool_events": [
                {"name": "TaskUpdate", "input": {"status": "completed", "taskId": "456"}}
            ]
        }
        result = check(data)
        assert result is not None
        assert result.get("decision") == "block"

    def test_block_task_missing_description(self, sample_task_state, monkeypatch):
        """Blocks when description is empty."""
        def mock_get_state_path(terminal_id=None):
            return sample_task_state

        monkeypatch.setattr(
            "Stop_task_completion_gate._get_task_state_path",
            mock_get_state_path,
        )

        data = {
            "tool_events": [
                {"name": "TaskUpdate", "input": {"status": "completed", "taskId": "789"}}
            ]
        }
        result = check(data)
        assert result is not None
        assert result.get("decision") == "block"

    def test_allow_properly_documented_task(self, sample_task_state, monkeypatch):
        """Allows task with proper self-documentation (subject 10+, desc 50+)."""
        def mock_get_state_path(terminal_id=None):
            return sample_task_state

        monkeypatch.setattr(
            "Stop_task_completion_gate._get_task_state_path",
            mock_get_state_path,
        )

        data = {
            "tool_events": [
                {"name": "TaskUpdate", "input": {"status": "completed", "taskId": "123"}}
            ]
        }
        result = check(data)
        # A properly documented task should not be blocked
        assert result is None or result.get("decision") != "block"


class TestRunFunction:
    """Tests for the run() entry point."""

    def test_run_passes_through_check_result(self, sample_task_state, monkeypatch):
        """run() wraps check() result correctly."""
        def mock_get_state_path(terminal_id=None):
            return sample_task_state

        monkeypatch.setattr(
            "Stop_task_completion_gate._get_task_state_path",
            mock_get_state_path,
        )

        data = {
            "tool_events": [
                {"name": "TaskUpdate", "input": {"status": "completed", "taskId": "456"}}
            ]
        }
        result = run(data)
        assert result is not None
        assert result.get("block") is True
        assert "reason" in result
        assert result.get("blocking_hook") == "Stop_task_completion_gate"

    def test_run_no_task_completion(self, sample_task_state, monkeypatch):
        """run() returns None when no task completion event."""
        def mock_get_state_path(terminal_id=None):
            return sample_task_state

        monkeypatch.setattr(
            "Stop_task_completion_gate._get_task_state_path",
            mock_get_state_path,
        )

        data = {
            "tool_events": [
                {"name": "Read", "input": {"file_path": "foo.py"}}
            ]
        }
        result = run(data)
        assert result is None
