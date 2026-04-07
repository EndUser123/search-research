#!/usr/bin/env python3
"""
test_task_tool_modify_integration.py - Integration test for Task tool modify protocol.

Tests the PreToolUse modify decision flow for the Task tool using the actual gate code:
1. Gate receives TaskUpdate with taskId (wrong param)
2. Gate returns modify with corrected task_id
3. Verify the corrected tool_input has the right shape for the PreToolUse harness

This tests the actual gate.run() function with real input — not a mock.
The harness (PreToolUse.py) applies the modification via:
    data["tool_input"] = res["tool_input"]
which is verified by the existing test_pretooluse_modify_integration.py tests.
"""

import sys
from pathlib import Path

import pytest

# Add hooks directory to path and import the actual gate
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from PreToolUse_task_self_doc_gate import run as gate_run


class TestTaskToolModifyIntegration:
    """Integration tests for Task tool modify decision in PreToolUse harness."""

    def test_taskupdate_auto_correct_modify_decision(self):
        """
        Verify TaskUpdate with taskId returns modify decision with task_id.

        The harness applies this via: data["tool_input"] = res["tool_input"]
        """
        test_input = {
            "tool_name": "TaskUpdate",
            "tool_input": {
                "taskId": "123",  # Wrong: camelCase
                "status": "in_progress",
                "subject": "Updated task subject",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        # Gate should return modify decision with corrected tool_input
        assert result is not None, "Expected modify decision, got None"
        assert result.get("decision") == "modify", f"Expected modify, got: {result}"
        assert "tool_input" in result, "modify decision must include tool_input"

        corrected = result["tool_input"]

        # taskId should be replaced with task_id
        assert "task_id" in corrected, f"task_id not in corrected: {corrected}"
        assert "taskId" not in corrected, f"taskId should not remain: {corrected}"

        # Value should be preserved
        assert corrected["task_id"] == "123", f"task_id value wrong: {corrected}"
        assert corrected["status"] == "in_progress", "status should be preserved"
        assert corrected["subject"] == "Updated task subject", "subject should be preserved"

    def test_taskcreate_name_to_subject_modify(self):
        """Verify TaskCreate with name returns modify decision with subject."""
        test_input = {
            "tool_name": "TaskCreate",
            "tool_input": {
                "name": "Fix file not found error",  # Wrong param name
                "description": "When running pytest, it crashes with FileNotFoundError at line 42. "
                              "The error shows test_file.txt doesn't exist.",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        assert result is not None, "Expected modify decision"
        assert result.get("decision") == "modify"
        corrected = result["tool_input"]

        assert "subject" in corrected, f"subject not in corrected: {corrected}"
        assert "name" not in corrected, f"name should not remain: {corrected}"
        assert corrected["subject"] == "Fix file not found error"

    def test_taskupdate_non_completion_allows(self):
        """Verify TaskUpdate with status!=completed and correct params returns None (allow)."""
        test_input = {
            "tool_name": "TaskUpdate",
            "tool_input": {
                "task_id": "456",  # Correct param name
                "status": "in_progress",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        # None = allow, no modification needed
        assert result is None, f"Expected None (allow), got: {result}"

    def test_taskcreate_well_documented_allows(self):
        """Verify TaskCreate with correct params and proper self-doc returns None (allow)."""
        test_input = {
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "Fix file not found error when running test suite",
                "description": "When running pytest, it crashes with FileNotFoundError at line 42. "
                              "The error shows test_file.txt doesn't exist.",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        # None = allow (well-documented, no corrections needed)
        assert result is None, f"Expected None (allow), got: {result}"

    def test_taskupdate_completion_blocks_without_description(self):
        """Verify TaskUpdate with status=completed but no description is blocked."""
        test_input = {
            "tool_name": "TaskUpdate",
            "tool_input": {
                "task_id": "789",
                "status": "completed",
                # No description - should be blocked
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        assert result is not None, "Expected block decision"
        assert result.get("decision") == "block", f"Expected block, got: {result}"
        assert "self-documentation incomplete" in result.get("reason", "")

    def test_taskupdate_with_both_taskid_and_name_no_conflict(self):
        """When both taskId and name are present, only the relevant one is corrected."""
        test_input = {
            "tool_name": "TaskUpdate",
            "tool_input": {
                "taskId": "999",  # Wrong param - should be corrected to task_id
                "status": "completed",
                "description": "Fix that shows error when processing invalid input during overnight "
                              "batch runs - it fails silently and outputs corrupted data.",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        result = gate_run(test_input)

        # Auto-correct applies (taskId -> task_id). Since description is valid self-doc,
        # gate returns modify (not block). The harness applies correction and allows.
        assert result is not None, "Expected modify decision"
        assert result.get("decision") == "modify", f"Expected modify, got: {result}"
        corrected = result["tool_input"]
        assert corrected.get("task_id") == "999", "taskId should be corrected to task_id"
        assert "taskId" not in corrected, "taskId should not remain"
        assert "description" in corrected, "description should be preserved"


class TestEnvVarOverride:
    """TEST-GATE-007: Integration tests for env var override of gate behavior."""

    def test_bypass_env_var_allows_without_self_doc(self):
        """TASK_SELF_DOC_BYPASS=1 should allow tasks without self-doc."""
        import os

        test_input = {
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "X",  # Vague - would normally block
                "description": "Y",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        # Set bypass env var
        old_val = os.environ.get("TASK_SELF_DOC_BYPASS", "")
        os.environ["TASK_SELF_DOC_BYPASS"] = "1"
        try:
            result = gate_run(test_input)
            # With bypass, gate returns None (allows)
            assert result is None, f"Expected None with bypass, got: {result}"
        finally:
            os.environ["TASK_SELF_DOC_BYPASS"] = old_val

    def test_bypass_disabled_requires_self_doc(self):
        """Without bypass, vague task should be blocked."""
        import os

        test_input = {
            "tool_name": "TaskCreate",
            "tool_input": {
                "subject": "X",  # Vague
                "description": "Y",
            },
            "session_id": "test-session",
            "terminal_id": "test-terminal",
        }

        # Ensure bypass is not set
        old_val = os.environ.get("TASK_SELF_DOC_BYPASS", "")
        os.environ.pop("TASK_SELF_DOC_BYPASS", None)
        try:
            result = gate_run(test_input)
            # Without bypass, gate blocks
            assert result is not None, "Expected block without bypass"
            assert result.get("decision") == "block", f"Expected block, got: {result}"
        finally:
            if old_val:
                os.environ["TASK_SELF_DOC_BYPASS"] = old_val


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
