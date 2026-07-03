#!/usr/bin/env python3
"""Test suite for PreToolUse_tool_check.py hook."""

import json
import subprocess
from pathlib import Path

import pytest


def run_hook(tool_name: str, tool_params: dict, response_text: str = "") -> dict:
    """Helper to run hook and capture output."""
    hook_path = Path("P:/.claude/hooks/pre/PreToolUse_tool_check.py")

    input_data = {
        "tool": tool_name,
        "parameters": tool_params,
        "response": response_text
    }

    process = subprocess.run(
        ["python", str(hook_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd="P:/"
    )

    return {
        "exit_code": process.returncode,
        "stdout": process.stdout,
        "stderr": process.stderr
    }


class TestEditToolValidation:
    """Test Edit tool parameter validation."""

    def test_edit_replace_all_string_blocked(self):
        """Edit with replace_all as string should be blocked."""
        result = run_hook("Edit", {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new",
            "replace_all": "false"  # Wrong type
        })
        assert result["exit_code"] == 1
        assert "TOOL VALIDATION FAILED" in result["stderr"]

    def test_edit_replace_all_boolean_allowed(self):
        """Edit with replace_all as boolean should pass."""
        result = run_hook("Edit", {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new",
            "replace_all": False  # Correct type
        })
        assert result["exit_code"] == 0

    def test_edit_without_replace_all_allowed(self):
        """Edit without replace_all parameter should pass."""
        result = run_hook("Edit", {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new"
        })
        assert result["exit_code"] == 0


class TestAgentToolValidation:
    """Test Agent tool parameter validation."""

    def test_agent_without_subagent_type_blocked(self):
        """Agent without subagent_type should be blocked."""
        result = run_hook("Agent", {
            "description": "Test task"
        })
        assert result["exit_code"] == 1
        assert "Missing required parameter" in result["stderr"]

    def test_agent_with_subagent_type_allowed(self):
        """Agent with subagent_type should pass."""
        result = run_hook("Agent", {
            "subagent_type": "general-purpose",
            "description": "Test task"
        })
        assert result["exit_code"] == 0

    def test_agent_model_validation(self):
        """Agent with invalid model should be blocked."""
        result = run_hook("Agent", {
            "subagent_type": "general-purpose",
            "model": "invalid_model"
        })
        assert result["exit_code"] == 1
        assert "model" in result["stderr"].lower()

    def test_agent_valid_model_allowed(self):
        """Agent with valid model should pass."""
        for model in ["sonnet", "opus", "haiku"]:
            result = run_hook("Agent", {
                "subagent_type": "general-purpose",
                "model": model
            })
            assert result["exit_code"] == 0


class TestBashToolValidation:
    """Test Bash tool parameter validation."""

    def test_bash_windows_path_blocked(self):
        """Bash with Windows backslash paths should be blocked."""
        result = run_hook("Bash", {
            "command": "cd C:\\Users\\test && ls"
        })
        assert result["exit_code"] == 1
        assert "forward slashes" in result["stderr"].lower()

    def test_bash_forward_slashes_allowed(self):
        """Bash with forward slashes should pass."""
        result = run_hook("Bash", {
            "command": "cd /c/Users/test && ls"
        })
        assert result["exit_code"] == 0

    def test_bash_invasive_operation_warning(self):
        """Bash with invasive operations should generate warnings."""
        result = run_hook("Bash", {
            "command": "rm -rf temp_dir"
        })
        assert result["exit_code"] == 0
        # Should generate advisory (exit 0 but with output)
        # This is a non-blocking warning


class TestWriteToolValidation:
    """Test Write tool parameter validation."""

    def test_write_existing_file_warning(self):
        """Write to existing file should generate warning."""
        # Note: This test requires the file to actually exist
        # For now, we'll just test that the hook runs
        result = run_hook("Write", {
            "file_path": "P:/README.md",
            "content": "test"
        })
        # Should pass but may have warnings (non-blocking)
        assert result["exit_code"] == 0


class TestHookOutputFormat:
    """Test that hook produces helpful output."""

    def test_validation_error_format(self):
        """Validation errors should be well-formatted."""
        result = run_hook("Edit", {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new",
            "replace_all": "false"
        })

        assert "TOOL VALIDATION FAILED" in result["stderr"]
        assert "Errors Found:" in result["stderr"]
        assert "Suggested Fixes:" in result["stderr"]

    def test_warning_format(self):
        """Warnings should be clearly marked."""
        result = run_hook("Bash", {
            "command": "cd C:\\test"
        })

        # Should have warning output
        assert len(result["stderr"]) > 0 or len(result["stdout"]) > 0


@pytest.mark.parametrize("tool,params,should_pass", [
    ("Edit", {"file_path": "test.py", "old_string": "x", "new_string": "y", "replace_all": False}, True),
    ("Edit", {"file_path": "test.py", "old_string": "x", "new_string": "y", "replace_all": "false"}, False),
    ("Agent", {"subagent_type": "general-purpose", "description": "test"}, True),
    ("Agent", {"description": "test"}, False),
    ("Bash", {"command": "ls -la"}, True),
    ("Bash", {"command": "cd C:\\test"}, False),
])
def test_tool_check_decision_matrix(tool, params, should_pass):
    """Parametrized test for various tool validations."""
    result = run_hook(tool, params)
    if should_pass:
        assert result["exit_code"] == 0
    else:
        assert result["exit_code"] == 1


class TestHookPerformance:
    """Test hook performance requirements."""

    def test_hook_execution_time(self):
        """Hook should complete in under 5 seconds."""
        import time

        start = time.time()
        result = run_hook("Edit", {
            "file_path": "test.py",
            "old_string": "old",
            "new_string": "new"
        })
        elapsed = time.time() - start

        assert elapsed < 5.0, f"Hook took {elapsed:.2f}s, should be under 5s"
        assert result["exit_code"] == 0
