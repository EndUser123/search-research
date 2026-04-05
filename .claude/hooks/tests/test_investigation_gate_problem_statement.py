#!/usr/bin/env python3
"""Unit tests for problem statement verification in investigation gate.

Tests the gate that prevents diagnosing why something is broken without
first verifying it IS broken in the form assumed.

Source: plan-20260325-problem-statement-verification.md
"""

import os
import sys
from pathlib import Path

# Set block mode for testing
os.environ["PROBLEM_STMT_VERIFICATION_ENABLED"] = "true"

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


# Mock shared_utils before import
class MockSharedUtils:
    @staticmethod
    def log_hook_event(**kwargs):
        """Mock log_hook_event for testing."""
        pass


sys.modules["shared_utils"] = MockSharedUtils()

import PreToolUse_investigation_gate as gate


def run_hook_input(
    tool_name: str,
    tool_input: dict,
    user_message: str = "",
    reset_state: bool = True,
    preloaded_state: dict = None,
) -> tuple[bool, str]:
    """Helper to run hook with synthetic input."""
    original_enabled = gate.ENABLED
    gate.ENABLED = True

    try:
        input_data = {
            "tool_name": tool_name,
            "tool_input": tool_input,
        }

        if user_message:
            input_data["conversation"] = [{"role": "user", "content": user_message}]

        if reset_state:
            gate.save_state(gate.fresh_state())

        if preloaded_state:
            original_load = gate.load_state
            gate.load_state = lambda: preloaded_state
            try:
                allowed, message = gate.process_hook(tool_name, tool_input, user_message)
            finally:
                gate.load_state = original_load
        else:
            allowed, message = gate.process_hook(tool_name, tool_input, user_message)

        return allowed, message
    finally:
        gate.ENABLED = original_enabled


class TestProblemStatementPattern:
    """Test problem statement pattern detection."""

    def test_01_block_hook_is_broken(self):
        """Block when claiming a hook is broken without verification."""
        allowed, msg = run_hook_input(
            "Bash",
            {"command": "ls"},
            user_message="SessionStart_tldr.py is broken - it's not firing",
        )
        assert not allowed, "Should block unverified problem statement"
        assert "PROBLEM STATEMENT UNVERIFIED" in msg

    def test_02_block_file_not_working(self):
        """Block when claiming a file/script is not working."""
        allowed, msg = run_hook_input(
            "Read",
            {"file_path": "P:/test.py"},
            user_message="The script is not working as expected",
        )
        assert not allowed, "Should block unverified problem statement"
        assert "PROBLEM STATEMENT UNVERIFIED" in msg

    def test_03_block_hook_not_registered(self):
        """Block when claiming hook is not registered."""
        allowed, msg = run_hook_input(
            "Grep", {"pattern": "test"}, user_message="Why is the hook not registered?"
        )
        assert not allowed, "Should block unverified problem statement"
        assert "PROBLEM STATEMENT UNVERIFIED" in msg

    def test_04_allow_after_settings_read(self):
        """Allow after reading settings.json to verify registration."""
        state = gate.fresh_state()
        state["files_read"].append("P:/.claude/settings.json")

        allowed, msg = run_hook_input(
            "Bash",
            {"command": "ls"},
            user_message="SessionStart_tldr.py is not registered",
            preloaded_state=state,
        )
        assert allowed, f"Should allow after settings.json read: {msg}"

    def test_05_allow_after_hook_file_read(self):
        """Allow after reading the hook file itself."""
        state = gate.fresh_state()
        state["files_read"].append("P:/.claude/hooks/SessionStart_tldr.py")

        allowed, msg = run_hook_input(
            "Bash",
            {"command": "ls"},
            user_message="SessionStart_tldr.py is broken",
            preloaded_state=state,
        )
        assert allowed, f"Should allow after hook file read: {msg}"

    def test_06_allow_after_git_status(self):
        """Allow after git status check."""
        state = gate.fresh_state()
        state["files_read"].append("git status")

        allowed, msg = run_hook_input(
            "Bash",
            {"command": "ls"},
            user_message="The hook file is not in git",
            preloaded_state=state,
        )
        assert allowed, f"Should allow after git status: {msg}"

    def test_07_no_problem_statement_allows(self):
        """Allow normal messages without problem statements."""
        allowed, msg = run_hook_input(
            "Read", {"file_path": "P:/test.py"}, user_message="Read this file for me"
        )
        assert allowed, f"Should allow non-problem statements: {msg}"

    def test_08_disabled_gate_allows(self):
        """Allow when gate is disabled via env var."""
        original_env = os.environ.get("PROBLEM_STMT_VERIFICATION_ENABLED")
        try:
            os.environ["PROBLEM_STMT_VERIFICATION_ENABLED"] = "false"
            # Re-import to pick up new env
            import importlib

            importlib.reload(gate)

            allowed, msg = run_hook_input(
                "Bash", {"command": "ls"}, user_message="This hook is broken"
            )
            assert allowed, f"Should allow when disabled: {msg}"
        finally:
            os.environ["PROBLEM_STMT_VERIFICATION_ENABLED"] = original_env or "true"
            importlib.reload(gate)


class TestPatternEdgeCases:
    """Edge cases for problem statement pattern detection."""

    def test_01_false_positive_regular_question(self):
        """Don't block regular questions about hooks."""
        allowed, msg = run_hook_input(
            "Read", {"file_path": "P:/test.py"}, user_message="How does the hook system work?"
        )
        assert allowed, f"Should not block regular questions: {msg}"

    def test_02_false_positive_investigation(self):
        """Don't block when actually investigating."""
        state = gate.fresh_state()
        state["files_read"].append("P:/.claude/settings.json")
        state["files_read"].append("P:/.claude/hooks/SessionStart_tldr.py")

        allowed, msg = run_hook_input(
            "Grep",
            {"pattern": "SessionStart"},
            user_message="Is SessionStart_tldr.py registered? Let me check.",
            preloaded_state=state,
        )
        assert allowed, f"Should allow investigation with verification: {msg}"

    def test_03_mixed_case_insensitive(self):
        """Problem statement detection is case insensitive."""
        state = gate.fresh_state()
        state["files_read"].append("P:/.claude/settings.json")

        allowed, msg = run_hook_input(
            "Bash", {"command": "ls"}, user_message="THE HOOK IS BROKEN", preloaded_state=state
        )
        assert allowed, f"Should be case insensitive: {msg}"


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
