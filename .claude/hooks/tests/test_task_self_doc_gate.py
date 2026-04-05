#!/usr/bin/env python3
"""
test_task_self_doc_gate.py - Tests for Task Self-Documentation Gate
================================================================

Tests for Stop_task_completion_gate.py and task_self_doc_validator.py.
Verifies:
1. Self-documentation validation logic
2. Task completion blocking for undocumented tasks
3. Advisory warnings for vague task creation
4. Environment variable controls

Tests run against the mocked interface, not the real Stop_router.
"""

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Import the module under test
from __lib.task_self_doc_validator import (
    DEFAULT_MIN_DESC_LEN,
    DEFAULT_MIN_SUBJECT_LEN,
    ValidationResult,
    is_task_self_documented,
    self_documentation_check,
)
from Stop_task_completion_gate import (
    _get_task_state_path,
    _is_task_completion,
    _load_task_data,
    check,
    run,
)

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def temp_state_dir():
    """Create a temporary state directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        state_dir = Path(tmpdir) / "state" / "task_tracker"
        state_dir.mkdir(parents=True, exist_ok=True)
        yield state_dir


@pytest.fixture
def sample_task_state(temp_state_dir):
    """Create a sample task state file."""
    task_data = {
        "1": {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
            "status": "in_progress",
        },
        "2": {
            "subject": "Fix bug",
            "description": "Bug in tests",
            "status": "in_progress",
        },
        "3": {
            "subject": "Improve performance",
            "description": "Make it faster",
            "status": "in_progress",
        },
        "4": {
            "subject": "",
            "description": "",
            "status": "in_progress",
        },
    }
    # State file must be in temp_state_dir which equals TASK_TRACKER_STATE_DIR
    state_file = temp_state_dir / "test-terminal_tasks.json"
    state_file.write_text(json.dumps({"tasks": task_data}), encoding="utf-8")
    return state_file


@pytest.fixture
def base_data():
    """Base hook data for Stop hook."""
    return {
        "assistant_response": "Some response",
        "response": "Some response",
        "session_id": "test-session-123",
        "terminal_id": "test-terminal-abc",
        "tool_events": [],
    }


# --- ValidationResult Tests -------------------------------------------------


class TestValidationResult:
    """Test ValidationResult NamedTuple."""

    def test_validation_result_fields(self):
        """Test ValidationResult has all required fields."""
        result = ValidationResult(
            is_valid=True,
            missing_categories=[],
            warnings=[],
            subject_length=50,
            desc_length=100,
        )
        assert result.is_valid is True
        assert result.missing_categories == []
        assert result.warnings == []
        assert result.subject_length == 50
        assert result.desc_length == 100


# --- Self-Documentation Check Tests -----------------------------------------


class TestSelfDocumentationCheck:
    """Test self_documentation_check function."""

    def test_well_documented_task(self):
        """A task with problem, situation, and symptom should be valid."""
        result = self_documentation_check(
            subject="Fix file not found error when running test suite",
            description="When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        )
        assert result.is_valid is True
        assert result.missing_categories == []
        assert result.subject_length >= DEFAULT_MIN_SUBJECT_LEN
        assert result.desc_length >= DEFAULT_MIN_DESC_LEN

    def test_vague_task_rejected(self):
        """A task with only 'bug' in description should be invalid."""
        result = self_documentation_check(
            subject="Fix bug",
            description="Bug in tests",
        )
        assert result.is_valid is False
        # "bug" matches Problem indicator
        assert "Problem" not in result.missing_categories
        # "in" matches Situation indicator
        assert "Situation" not in result.missing_categories
        # Missing Symptom
        assert any("Symptom" in m for m in result.missing_categories)

    def test_empty_task_rejected(self):
        """An empty task should be invalid."""
        result = self_documentation_check(
            subject="",
            description="",
        )
        assert result.is_valid is False
        assert len(result.missing_categories) >= 2

    def test_missing_problem_category(self):
        """Task with situation and symptom but no problem indicator should be invalid."""
        # "app crashes" - crash is a problem indicator
        # Need description with situation + symptom but NO problem words
        result = self_documentation_check(
            subject="This is a test task subject here",
            description="During startup the app shows a warning message that needs attention.",
        )
        assert result.is_valid is False
        assert any("Problem" in m for m in result.missing_categories)

    def test_missing_situation_category(self):
        """Task with problem and symptom but no situation indicator should be invalid."""
        # Need to avoid "on", "in", "during", "when", etc.
        # Use phrasing that doesn't contain any situation words
        result = self_documentation_check(
            subject="This is a test task subject here",
            description="The code returns an error and throws exception without proper input validation.",
        )
        assert result.is_valid is False
        assert any("Situation" in m for m in result.missing_categories)

    def test_missing_symptom_category(self):
        """Task with problem and situation but no symptom indicator should be invalid."""
        # "something is broken" - broken is problem, but no symptom indicators
        result = self_documentation_check(
            subject="This is a test task subject here",
            description="During initialization the code has a bug that needs fixing.",
        )
        assert result.is_valid is False
        assert any("Symptom" in m for m in result.missing_categories)

    def test_short_subject_generates_warning(self):
        """Subject shorter than minimum should add warning even if description is complete."""
        result = self_documentation_check(
            subject="Fix",
            description="When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        )
        # is_valid is False because subject is too short (even with good description)
        assert result.is_valid is False
        # But warning should still be generated about short subject
        assert any("Subject too short" in w for w in result.warnings)

    def test_short_description_warns(self):
        """Description shorter than minimum should add warning."""
        result = self_documentation_check(
            subject="Fix file not found error when running test suite",
            description="Bug",
        )
        # Should be invalid due to missing categories
        assert result.is_valid is False
        assert any("Description too short" in w for w in result.warnings)

    def test_all_problem_indicators(self):
        """Test all problem indicators are recognized."""
        problem_texts = [
            "fix the issue",
            "bug in code",
            "error handling",
            "crash reported",
            "broken pipeline",
            "fails on startup",
        ]
        for text in problem_texts:
            result = self_documentation_check(
                subject="Test task with long enough subject",
                description=text + " during some situation where something shows an error",
            )
            assert "Problem" not in result.missing_categories, f"Failed for: {text}"

    def test_all_situation_indicators(self):
        """Test all situation indicators are recognized."""
        situation_texts = [
            "when running",
            "during startup",
            "while processing",
            "after initialization",
            "in the workflow",
            "on the server",
        ]
        for text in situation_texts:
            result = self_documentation_check(
                subject="Test task with long enough subject",
                description=text + " the system shows an error that returns exception",
            )
            assert "Situation" not in result.missing_categories, f"Failed for: {text}"

    def test_all_symptom_indicators(self):
        """Test all symptom indicators are recognized."""
        symptom_texts = [
            "shows an error",
            "returns null",
            "throws exception",
            "produces warning",
            "outputs log",
            "error message",
            "exception occurred",
        ]
        for text in symptom_texts:
            result = self_documentation_check(
                subject="Test task with long enough subject",
                description="When running the app " + text,
            )
            assert "Symptom" not in result.missing_categories, f"Failed for: {text}"

    def test_case_insensitive_matching(self):
        """Test that indicator matching is case insensitive."""
        result = self_documentation_check(
            subject="Test task with long enough subject here",
            description="WHEN running the app it ERROR out and SHOWS exception",
        )
        assert "Problem" not in result.missing_categories
        assert "Situation" not in result.missing_categories
        assert "Symptom" not in result.missing_categories

    def test_require_all_false(self):
        """Test with require_all=False, any one category is enough."""
        result = self_documentation_check(
            subject="Task subject here",
            description="Bug",  # Only has Problem indicator
            require_all=False,
        )
        assert result.is_valid is True

    def test_require_all_false_strict_subject(self):
        """Test require_all=False still requires minimum subject length."""
        result = self_documentation_check(
            subject="",
            description="Bug",
            require_all=False,
        )
        assert result.is_valid is False


class TestIsTaskSelfDocumented:
    """Test is_task_self_documented convenience function."""

    def test_valid_task_returns_true(self):
        """Valid task should return True."""
        result = is_task_self_documented(
            subject="Fix file not found error when running test suite",
            description="When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        )
        assert result is True

    def test_invalid_task_returns_false(self):
        """Invalid task should return False."""
        result = is_task_self_documented(
            subject="Fix bug",
            description="Bug in tests",
        )
        assert result is False


# --- _is_task_completion Tests ----------------------------------------------


class TestIsTaskCompletion:
    """Test _is_task_completion helper."""

    def test_detects_task_update_to_completed(self):
        """Should detect TaskUpdate to completed status."""
        tool_events = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "1", "status": "completed"},
            }
        ]
        is_completion, input_data, task_id = _is_task_completion(tool_events)
        assert is_completion is True
        assert input_data["status"] == "completed"
        assert task_id == "1"

    def test_ignores_other_tool_events(self):
        """Should ignore non-TaskUpdate events."""
        tool_events = [
            {"name": "Read", "input": {"file_path": "test.py"}},
        ]
        is_completion, _, _ = _is_task_completion(tool_events)
        assert is_completion is False

    def test_ignores_incomplete_task(self):
        """Should ignore TaskUpdate to non-completed status."""
        tool_events = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "1", "status": "in_progress"},
            }
        ]
        is_completion, _, _ = _is_task_completion(tool_events)
        assert is_completion is False

    def test_handles_alternate_field_names(self):
        """Should handle both taskId and task_id field names."""
        tool_events = [
            {
                "name": "TaskUpdate",
                "input": {"task_id": "2", "status": "completed"},
            }
        ]
        is_completion, _, task_id = _is_task_completion(tool_events)
        assert is_completion is True
        assert task_id == "2"


# --- _get_task_state_path Tests ---------------------------------------------


class TestGetTaskStatePath:
    """Test _get_task_state_path helper."""

    def test_returns_normalized_path(self, temp_state_dir):
        """Should return normalized path for terminal ID with colons."""
        terminal_id = "console:abc:123"
        # Create the file with the normalized name first
        normalized_name = "console_abc_123"
        state_file = temp_state_dir / f"{normalized_name}_tasks.json"
        state_file.write_text("{}", encoding="utf-8")

        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": terminal_id}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                result = _get_task_state_path()
                expected = temp_state_dir / "console_abc_123_tasks.json"
                assert result == expected

    def test_returns_none_for_missing_terminal(self, temp_state_dir):
        """Should return None if no terminal ID and no state file."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": ""}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                result = _get_task_state_path()
                assert result is None


# --- _load_task_data Tests --------------------------------------------------


class TestLoadTaskData:
    """Test _load_task_data helper."""

    def test_loads_existing_task(self, sample_task_state, temp_state_dir):
        """Should load task data for existing task."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                result = _load_task_data("1")
        assert result is not None
        assert result["subject"] == "Fix file not found error when running test suite"

    def test_returns_none_for_missing_task(self, sample_task_state, temp_state_dir):
        """Should return None for non-existent task."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                result = _load_task_data("999")
        assert result is None

    def test_returns_none_for_missing_state_file(self, temp_state_dir):
        """Should return None if state file doesn't exist."""
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "nonexistent-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                result = _load_task_data("1")
        assert result is None


# --- Check Function Tests ----------------------------------------------------


class TestCheckFunction:
    """Test check function for Stop hook."""

    def test_blocks_completion_of_undocumented_task(
        self, sample_task_state, temp_state_dir, base_data
    ):
        """Should block completion of task without self-documentation."""
        # Task 2 has subject "Fix bug" and description "Bug in tests" - undocumented
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        assert result is not None
        assert result["decision"] == "block"
        assert "TASK SELF-DOCUMENTATION REQUIRED" in result["reason"]

    def test_allows_completion_of_documented_task(
        self, sample_task_state, temp_state_dir, base_data
    ):
        """Should allow completion of well-documented task."""
        # Task 1 is well-documented
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "1", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        assert result is None

    def test_allows_non_task_update_events(self, base_data):
        """Should allow events that are not TaskUpdate to completed."""
        base_data["tool_events"] = [
            {"name": "Read", "input": {"file_path": "test.py"}},
        ]
        result = check(base_data)
        assert result is None

    def test_disabled_when_env_false(self, sample_task_state, temp_state_dir, base_data):
        """Should not block when TASK_SELF_DOC_ENABLED is false."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "false"}):
                    result = check(base_data)
        assert result is None

    def test_advisory_only_mode(self, sample_task_state, temp_state_dir, base_data):
        """Should not block when TASK_SELF_DOC_ADVISORY_ONLY is true."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ADVISORY_ONLY": "true"}):
                    result = check(base_data)
        assert result is None

    def test_returns_none_for_missing_task(self, temp_state_dir, base_data):
        """Should return None (allow) if task not found in state."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "999", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        # Task not found should be allowed (might be from different session)
        assert result is None


# --- Run Function Tests ------------------------------------------------------


class TestRunFunction:
    """Test run function for in-process execution."""

    def test_run_returns_block_dict(self, sample_task_state, temp_state_dir, base_data):
        """run() should return block dict for undocumented task."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = run(base_data)
        assert result is not None
        assert result["block"] is True
        assert "reason" in result

    def test_run_returns_none_for_documented_task(
        self, sample_task_state, temp_state_dir, base_data
    ):
        """run() should return None for well-documented task."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "1", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = run(base_data)
        assert result is None


# --- Block Message Content Tests ---------------------------------------------


class TestBlockMessageContent:
    """Test block message contains required information."""

    def test_block_message_shows_missing_categories(
        self, sample_task_state, temp_state_dir, base_data
    ):
        """Block message should list missing categories."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "3", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        assert result is not None
        reason = result["reason"]
        assert "Missing categories" in reason
        assert "Problem" in reason or "Symptom" in reason

    def test_block_message_shows_task_id(self, sample_task_state, temp_state_dir, base_data):
        """Block message should include task ID."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        assert result is not None
        assert "Task #2" in result["reason"]

    def test_block_message_explains_schema(self, sample_task_state, temp_state_dir, base_data):
        """Block message should explain the self-documentation schema."""
        base_data["tool_events"] = [
            {
                "name": "TaskUpdate",
                "input": {"taskId": "2", "status": "completed"},
            }
        ]
        with patch.dict(os.environ, {"CLAUDE_TERMINAL_ID": "test-terminal"}):
            with patch.dict(os.environ, {"TASK_TRACKER_STATE_DIR": str(temp_state_dir)}):
                with patch.dict(os.environ, {"TASK_SELF_DOC_ENABLED": "true"}):
                    result = check(base_data)
        assert result is not None
        reason = result["reason"]
        assert "Problem" in reason
        assert "Situation" in reason
        assert "Symptom" in reason
