#!/usr/bin/env python3
"""
test_pretooluse_task_self_doc_gate.py - Tests for PreToolUse Task Self-Documentation Gate
======================================================================================

Tests for PreToolUse_task_self_doc_gate.py.
Verifies:
1. TaskCreate operations are validated
2. Non-TaskCreate operations pass through
3. Blocking behavior for undocumented tasks
4. Advisory mode behavior
5. Bypass flag handling

Tests run against the gate's run() function directly.
"""

import json
import os
import sys
from pathlib import Path
from unittest.mock import patch

import pytest

# Add hooks directory to path
_HOOKS_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(_HOOKS_DIR))

from __lib.task_self_doc_validator import (
    DEFAULT_MIN_SUBJECT_LEN,
)

# Import the gate module
sys.path.insert(0, str(_HOOKS_DIR))
from PreToolUse_task_self_doc_gate import run as gate_run

# --- Fixtures ---------------------------------------------------------------


@pytest.fixture
def base_data():
    """Base hook data for PreToolUse gate."""
    return {
        "tool_name": "TaskCreate",
        "tool_input": {},
        "session_id": "test-session-123",
        "terminal_id": "test-terminal-abc",
    }


# --- TaskCreate Detection Tests ---------------------------------------------


class TestTaskCreateDetection:
    """Test TaskCreate operation detection."""

    def test_accepts_task_create_operation(self, base_data):
        """Should recognize TaskCreate tool."""
        base_data["tool_name"] = "TaskCreate"
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        # Well-documented task should return None (allow)
        assert result is None

    def test_rejects_non_task_create(self, base_data):
        """Should pass through non-TaskCreate operations."""
        base_data["tool_name"] = "Bash"
        base_data["tool_input"] = {"command": "ls"}
        result = gate_run(base_data)
        assert result is None

    def test_rejects_write_operation(self, base_data):
        """Should pass through Write operations."""
        base_data["tool_name"] = "Write"
        base_data["tool_input"] = {"file_path": "test.py", "content": "x = 1"}
        result = gate_run(base_data)
        assert result is None


# --- Self-Documentation Validation Tests -------------------------------------


class TestSelfDocValidation:
    """Test self-documentation validation for TaskCreate."""

    def test_blocks_vague_task(self, base_data):
        """Should block TaskCreate with vague documentation."""
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug in tests",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "block"
        assert "Task self-documentation incomplete" in result["reason"]

    def test_blocks_empty_task(self, base_data):
        """Should block TaskCreate with empty fields."""
        base_data["tool_input"] = {
            "subject": "",
            "description": "",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "block"

    def test_allows_well_documented_task(self, base_data):
        """Should allow well-documented TaskCreate."""
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is None

    def test_missing_problem_category_blocks(self, base_data):
        """Should block when Problem category is missing."""
        # "app crashes" - crash is a problem indicator
        # Need description with situation + symptom but NO problem words
        base_data["tool_input"] = {
            "subject": "This is a test task subject here",
            "description": "During startup the app shows a warning message that needs attention.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert "Problem" in result["reason"]

    def test_missing_situation_category_blocks(self, base_data):
        """Should block when Situation category is missing."""
        base_data["tool_input"] = {
            "subject": "This is a test task subject here",
            "description": "The code returns an error and throws exception without proper input validation.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert "Situation" in result["reason"]

    def test_missing_symptom_category_blocks(self, base_data):
        """Should block when Symptom category is missing."""
        base_data["tool_input"] = {
            "subject": "This is a test task subject here",
            "description": "During initialization the code has a bug that needs fixing.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert "Symptom" in result["reason"]

    def test_short_subject_generates_warning(self, base_data):
        """Should include subject length in block message."""
        base_data["tool_input"] = {
            "subject": "Fix",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert "Subject too short" in result["reason"]
        assert f"{len('Fix')}/{DEFAULT_MIN_SUBJECT_LEN} chars" in result["reason"]

    def test_short_description_generates_warning(self, base_data):
        """Should include description length in block message."""
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "Bug",
        }
        result = gate_run(base_data)
        assert result is not None
        assert "Description too short" in result["reason"]


# --- Environment Variable Controls --------------------------------------------


class TestEnvironmentControls:
    """Test environment variable controls."""

    def test_disabled_when_env_false(self, base_data):
        """Should not block when TASK_SELF_DOC_GATE_ENABLED is false."""
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug",
        }
        with patch.dict(os.environ, {"TASK_SELF_DOC_GATE_ENABLED": "false"}):
            result = gate_run(base_data)
        assert result is None

    def test_advisory_mode_when_blocking_false(self, base_data):
        """Should not block when TASK_SELF_DOC_GATE_BLOCKING is false."""
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug",
        }
        with patch.dict(os.environ, {"TASK_SELF_DOC_GATE_BLOCKING": "false"}):
            result = gate_run(base_data)
        # In advisory mode, should return None (allow) but write warning to stderr
        assert result is None

    def test_bypass_flag_allows(self, base_data):
        """Should allow when TASK_SELF_DOC_BYPASS is set."""
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug",
        }
        with patch.dict(os.environ, {"TASK_SELF_DOC_BYPASS": "true"}):
            result = gate_run(base_data)
        assert result is None


# --- Schema Display Tests ----------------------------------------------------


class TestSchemaDisplay:
    """Test that block message shows required schema information."""

    def test_block_message_shows_schema(self, base_data):
        """Block message should explain the self-documentation schema."""
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug",
        }
        result = gate_run(base_data)
        assert result is not None
        reason = result["reason"]
        assert "Problem" in reason
        assert "Situation" in reason
        assert "Symptom" in reason

    def test_block_message_shows_char_counts(self, base_data):
        """Block message should show character counts."""
        base_data["tool_input"] = {
            "subject": "X",
            "description": "Y",
        }
        result = gate_run(base_data)
        assert result is not None
        reason = result["reason"]
        # Should contain character counts like "1/10 chars" or "1/50 chars"
        assert "chars" in reason


# --- Command-Line Interface Tests --------------------------------------------


class TestCLI:
    """Test command-line interface."""

    def test_main_allows_well_documented(self, base_data):
        """main() should exit 0 for well-documented task."""
        base_data["tool_name"] = "TaskCreate"
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        import subprocess

        result = subprocess.run(
            ["python", str(_HOOKS_DIR / "PreToolUse_task_self_doc_gate.py")],
            input=json.dumps(base_data),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

    def test_main_blocks_undocumented(self, base_data):
        """main() should exit 2 for undocumented task."""
        base_data["tool_name"] = "TaskCreate"
        base_data["tool_input"] = {
            "subject": "Fix bug",
            "description": "Bug",
        }
        import subprocess

        result = subprocess.run(
            ["python", str(_HOOKS_DIR / "PreToolUse_task_self_doc_gate.py")],
            input=json.dumps(base_data),
            capture_output=True,
            text=True,
        )
        assert result.returncode == 2


# --- Parameter Auto-Correct Tests -----------------------------------------------


class TestParamAutoCorrect:
    """Test parameter auto-correct for TaskCreate."""

    def test_auto_corrects_name_to_subject(self, base_data, capsys):
        """Should auto-correct 'name' to 'subject'."""
        base_data["tool_input"] = {
            "name": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "modify"
        assert "subject" in result["tool_input"]
        assert "name" not in result["tool_input"]
        assert result["tool_input"]["subject"] == "Fix file not found error when running test suite"
        captured = capsys.readouterr()
        assert "name" in captured.err
        assert "subject" in captured.err

    def test_auto_corrects_title_to_subject(self, base_data, capsys):
        """Should auto-correct 'title' to 'subject'."""
        base_data["tool_input"] = {
            "title": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "modify"
        assert "subject" in result["tool_input"]
        assert "title" not in result["tool_input"]
        captured = capsys.readouterr()
        assert "title" in captured.err

    def test_no_change_when_subject_exists(self, base_data):
        """Should not modify when 'subject' already exists."""
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        # Should pass through to self-doc validation (None = allow)
        assert result is None

    def test_name_and_title_both_present_prefers_name(self, base_data, capsys):
        """When both 'name' and 'title' present, should correct 'name' first."""
        base_data["tool_input"] = {
            "name": "Correct subject",
            "title": "Wrong title",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "modify"
        assert result["tool_input"]["subject"] == "Correct subject"
        assert "title" in result["tool_input"]  # title not touched

    def test_preserves_other_params(self, base_data, capsys):
        """Should preserve other parameters like description and metadata."""
        base_data["tool_input"] = {
            "name": "Fix file not found error",
            "description": "When running pytest, it crashes with error at line 42. The error shows that test_file.txt is missing.",
            "metadata": {"priority": "high"},
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "modify"
        assert result["tool_input"]["subject"] == "Fix file not found error"
        assert result["tool_input"]["description"] == "When running pytest, it crashes with error at line 42. The error shows that test_file.txt is missing."
        assert result["tool_input"]["metadata"] == {"priority": "high"}

    def test_auto_corrects_task_id_for_task_update(self, base_data):
        """Should NOT auto-correct taskId (it's already correct camelCase)."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": "123",
            "name": "Updated task name",
        }
        result = gate_run(base_data)
        # taskId is already correct, no correction needed
        assert result is None

    def test_blocks_task_update_completion_without_description(self, base_data):
        """TaskUpdate with status=completed but no description is blocked."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "task_id": "123",
            "status": "completed",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "block"
        assert "TaskUpdate self-documentation incomplete" in result["reason"]

    def test_allows_task_update_completion_with_description(self, base_data):
        """TaskUpdate with status=completed and description is allowed."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "task_id": "123",
            "status": "completed",
            "description": "Fix that shows error when processing invalid input during overnight batch runs - it fails silently and outputs corrupted data.",
        }
        result = gate_run(base_data)
        # task_id gets auto-corrected to taskId (the correct param name)
        assert result is not None
        assert result["decision"] == "modify"
        assert "taskId" in result["tool_input"]
        assert "task_id" not in result["tool_input"]

    def test_allows_task_update_non_completion(self, base_data):
        """TaskUpdate with non-completion status requires no self-doc."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "task_id": "123",
            "status": "in_progress",
        }
        result = gate_run(base_data)
        # task_id gets auto-corrected to taskId (the correct param name)
        assert result is not None
        assert result["decision"] == "modify"
        assert "taskId" in result["tool_input"]
        assert "task_id" not in result["tool_input"]

    def test_task_update_task_id_auto_correct(self, base_data):
        """TaskUpdate corrects task_id (wrong) to taskId (correct)."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "task_id": "456",
            "status": "in_progress",
        }
        result = gate_run(base_data)
        # Corrects snake_case task_id to camelCase taskId
        assert result is not None
        assert result["decision"] == "modify"
        assert "taskId" in result["tool_input"]
        assert "task_id" not in result["tool_input"]


# --- TEST-GATE Coverage Tests -----------------------------------------------


class TestTaskDeleteBypass:
    """TEST-GATE-001: TaskDelete should bypass gate (not handled)."""

    def test_taskdelete_passes_through(self, base_data):
        """TaskDelete is not in eligibility check, should pass through."""
        base_data["tool_name"] = "TaskDelete"
        base_data["tool_input"] = {
            "task_id": "123",
        }
        result = gate_run(base_data)
        # TaskDelete is not in ("TaskCreate", "TaskUpdate"), so gate returns None
        assert result is None


class TestInvalidTaskIdTypes:
    """TEST-GATE-002: Invalid taskId types should be handled gracefully."""

    def test_taskupdate_integer_taskid_blocks(self, base_data):
        """TaskUpdate with integer taskId should trigger blocking."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": 123,  # Integer instead of string
            "status": "completed",
        }
        result = gate_run(base_data)
        # Integer taskId is not string, should not auto-correct properly
        assert result is not None

    def test_taskupdate_none_taskid_auto_corrects(self, base_data):
        """TaskUpdate with None taskId should NOT be auto-corrected (taskId is correct param name)."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": None,
            "status": "in_progress",
        }
        result = gate_run(base_data)
        # taskId is the correct param name, no correction needed
        assert result is None

    def test_taskupdate_empty_string_taskid_auto_corrects(self, base_data):
        """TaskUpdate with empty string taskId should NOT be auto-corrected (taskId is correct param)."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": "",
            "status": "in_progress",
        }
        result = gate_run(base_data)
        # taskId is the correct param name, no correction needed
        assert result is None


class TestEmptyToolInput:
    """TEST-GATE-003: Empty tool_input should not crash."""

    def test_taskcreate_empty_input_blocks(self, base_data):
        """TaskCreate with empty tool_input should block properly."""
        base_data["tool_name"] = "TaskCreate"
        base_data["tool_input"] = {}
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "block"


class TestBrittleDescription:
    """TEST-GATE-004: Description wording should be explicit."""

    def test_description_with_problem_situation_symptom_is_valid(self, base_data):
        """Description with Problem + Situation + Symptom should pass."""
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        # Full self-documentation: Problem (crashes), Situation (When running pytest),
        # Symptom (FileNotFoundError) - should pass
        assert result is None


class TestCharCountAssertions:
    """TEST-GATE-005: Block message should verify actual char counts."""

    def test_block_message_verifies_char_counts_1_of_10(self, base_data):
        """Block message should show 1/10 for subject."""
        base_data["tool_input"] = {
            "subject": "X",  # 1 char
            "description": "When running pytest it crashes with error",  # >10 chars, has Problem
        }
        result = gate_run(base_data)
        assert result is not None
        reason = result["reason"]
        # Should contain explicit count like "1/10" not just "chars"
        assert "/10" in reason, f"Expected '/10' in reason, got: {reason}"

    def test_block_message_verifies_char_counts_1_of_50(self, base_data):
        """Block message should show 1/50 for description."""
        base_data["tool_input"] = {
            "subject": "Fix file not found error when running test suite",  # >10 chars
            "description": "X",  # 1 char, should be 1/50
        }
        result = gate_run(base_data)
        assert result is not None
        reason = result["reason"]
        # Should contain explicit count like "1/50" not just "chars"
        assert "/50" in reason, f"Expected '/50' in reason, got: {reason}"


class TestTitleValuePreservation:
    """TEST-GATE-006: Title value should be preserved when both name and title present."""

    def test_name_and_title_both_present_preserves_title_value(self, base_data):
        """When both 'name' and 'title' present, title VALUE should be preserved, not just key existence."""
        base_data["tool_input"] = {
            "name": "Correct subject",
            "title": "MyCustomTitle",  # Different value to verify preservation
            "description": "When running pytest, it crashes with FileNotFoundError at line 42. The error shows test_file.txt doesn't exist.",
        }
        result = gate_run(base_data)
        assert result is not None
        assert result["decision"] == "modify"
        # Verify TITLE VALUE is preserved, not just key existence
        assert result["tool_input"].get("title") == "MyCustomTitle", \
            f"title value should be 'MyCustomTitle', got: {result['tool_input'].get('title')}"


class TestAutoCorrectBlockCombo:
    """TEST-GATE-008: Combined auto-correct + block scenario."""

    def test_taskupdate_taskid_wrong_and_completion_no_desc(self, base_data):
        """TaskUpdate with wrong taskId and status=completed without description should block."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": "wrong_id",  # Wrong param name
            "status": "completed",  # Completion without description
        }
        result = gate_run(base_data)
        # Should block because: 1) taskId wrong, 2) status=completed without description
        assert result is not None
        assert result["decision"] == "block"


class TestCollisionDetection:
    """TEST-GATE-009: Collision when both taskId and task_id present."""

    def test_taskupdate_both_taskid_and_task_id(self, base_data):
        """TaskUpdate with both taskId and task_id: keep taskId (correct), remove task_id (wrong)."""
        base_data["tool_name"] = "TaskUpdate"
        base_data["tool_input"] = {
            "taskId": "old_id",
            "task_id": "new_id",
            "description": "When running pytest, it crashes with error.",  # Valid description
        }
        result = gate_run(base_data)
        # Collision resolved: keep taskId (correct), remove task_id (wrong)
        assert result is not None
        assert result["decision"] == "modify"
        assert "taskId" in result["tool_input"]
        assert "task_id" not in result["tool_input"]
        assert result["tool_input"]["taskId"] == "old_id"


