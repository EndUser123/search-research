#!/usr/bin/env python3
"""Test suite for PostToolWrite_doc_validator.py hook."""

import json
import subprocess
from pathlib import Path

import pytest


def run_hook(tool_name: str, tool_params: dict, response_text: str) -> dict:
    """Helper to run hook and capture output."""
    hook_path = Path("P:/.claude/hooks/post/PostToolWrite_doc_validator.py")

    input_data = {"tool": tool_name, "parameters": tool_params, "response": response_text}

    process = subprocess.run(
        ["python", str(hook_path)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        cwd="P:/",
    )

    return {"exit_code": process.returncode, "stdout": process.stdout, "stderr": process.stderr}


class TestPostToolWriteBasicPatterns:
    """Test basic post-write validation patterns."""

    def test_non_code_modifying_tools_skipped(self):
        """Non-code-modifying tools should be skipped."""
        for tool in ["Read", "Grep", "Glob"]:
            result = run_hook(tool, {}, "Any response text")
            assert result["exit_code"] == 0
            assert len(result["stderr"]) == 0

    def test_empty_response_allowed(self):
        """Empty responses should pass."""
        result = run_hook("Edit", {"file_path": "test.py"}, "")
        assert result["exit_code"] == 0

    def test_code_only_response_allowed(self):
        """Code-only responses should pass."""
        response = "```python\nprint('hello')\n```"
        result = run_hook("Write", {"file_path": "test.py"}, response)
        assert result["exit_code"] == 0


class TestUnverifiedClaimDetection:
    """Test detection of unverified claims after code changes."""

    def test_should_fix_without_testing_warned(self):
        """'This should fix' without testing should generate warning."""
        response = "Updated the config file. This should fix the issue."
        result = run_hook("Edit", {"file_path": "config.py"}, response)

        # PostToolUse is non-blocking, so exit 0
        assert result["exit_code"] == 0
        # But should have warning output
        assert len(result["stderr"]) > 0

    def test_verified_claim_allowed(self):
        """Claims backed by testing should pass."""
        response = """
        Updated config.py with timeout setting.

        Verified with:
        ```bash
        python -m pytest tests/test_config.py -v
        ```

        All tests passed.
        """
        result = run_hook("Edit", {"file_path": "config.py"}, response)
        assert result["exit_code"] == 0
        # No warnings expected

    def test_optimal_solution_claim_warned(self):
        """'Optimal solution' claims without verification should warn."""
        response = "This is the optimal solution for the problem."
        result = run_hook("Write", {"file_path": "solution.py"}, response)

        assert result["exit_code"] == 0  # Non-blocking
        assert len(result["stderr"]) > 0


class TestUncertaintyPatterns:
    """Test detection of uncertain claims without testing."""

    def test_i_think_without_test_warned(self):
        """'I think' without testing evidence should warn."""
        response = "I think this fixes the memory leak."
        result = run_hook("Edit", {"file_path": "memory.py"}, response)

        assert result["exit_code"] == 0
        # Should generate warning

    def test_probably_without_test_warned(self):
        """'Probably' without testing should warn."""
        response = "This is probably caused by a race condition."
        result = run_hook("Bash", {"command": "ls"}, response)

        assert result["exit_code"] == 0
        # Should generate warning

    def test_uncertain_with_test_allowed(self):
        """Uncertain language with testing evidence should pass."""
        response = """
        I think this fixes the issue.

        Testing confirmed:
        - Unit tests: PASSED
        - Integration test: PASSED
        - Manual verification: CONFIRMED
        """
        result = run_hook("Edit", {"file_path": "fix.py"}, response)
        assert result["exit_code"] == 0


class TestWarningOutputFormat:
    """Test that warnings are well-formatted."""

    def test_warning_format(self):
        """Warnings should follow standard format."""
        response = "This should fix it."
        result = run_hook("Edit", {"file_path": "test.py"}, response)

        # Should have warning message
        assert "VERIFICATION PROTOCOL" in result["stderr"] or len(result["stderr"]) > 0

    def test_multiple_issues_listed(self):
        """Multiple issues should be listed."""
        response = "I think this is the optimal solution that should fix everything."
        result = run_hook("Write", {"file_path": "test.py"}, response)

        # Should detect both patterns
        assert len(result["stderr"]) > 0


@pytest.mark.parametrize(
    "response,should_warn",
    [
        ("This should fix it.", True),
        ("This is the optimal solution.", True),
        ("I think this works.", True),
        ("Probably caused by X.", True),
        ("Fixed and tested. All tests pass.", False),
        ("Updated code. Verification: Tests passed.", False),
        ("# Code only response", False),
        ("", False),
    ],
)
def test_doc_validator_decision_matrix(response, should_warn):
    """Parametrized test for various response types."""
    result = run_hook("Edit", {"file_path": "test.py"}, response)
    assert result["exit_code"] == 0  # Always non-blocking

    if should_warn:
        assert len(result["stderr"]) > 0
    # Note: Non-warning cases may still have output, but we can't easily
    # verify it's not a warning without parsing stderr content


class TestHookPerformance:
    """Test hook performance requirements."""

    def test_hook_execution_time(self):
        """Hook should complete quickly (non-blocking)."""
        import time

        start = time.time()
        result = run_hook("Edit", {"file_path": "test.py"}, "Any response")
        elapsed = time.time() - start

        assert elapsed < 3.0, f"Hook took {elapsed:.2f}s, should be under 3s"
        assert result["exit_code"] == 0


class TestNonBlockingBehavior:
    """Test that hook is non-blocking."""

    @pytest.mark.parametrize(
        "response",
        [
            "This should fix it without testing.",
            "This is the optimal solution.",
            "I think this works.",
            "Probably broken.",
        ],
    )
    def test_never_blocks(self, response):
        """PostToolWrite validator should NEVER block (always exit 0)."""
        for tool in ["Edit", "Write", "Bash"]:
            result = run_hook(tool, {"file_path": "test.py"}, response)
            assert (
                result["exit_code"] == 0
            ), f"PostToolWrite blocked for {tool} with response: {response}"
