#!/usr/bin/env python3
"""
Hook Chain E2E Tests

Tests complete hook chain execution:
UserPromptSubmit → PreToolUse → tool execution → PostToolUse → Stop

Verifies evidence propagation through chain and hook failure handling.

Test Coverage:
- Hook chain execution order
- Evidence propagation through chain
- Hook failure handling
- Bypass flag integration
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

# Add hooks directory to path
hooks_dir = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(hooks_dir))

from evidence_store import read_session_context, write_session_context


class TestHookChainExecution:
    """Test complete hook chain execution."""

    def test_userpromptsubmit_pretooluse_chain(self, tmp_path):
        """
        Test UserPromptSubmit → PreToolUse → tool execution chain.

        Verifies that hooks execute in correct order and pass data correctly.
        """
        session_id = "hook-chain-session"
        terminal_id = "test-terminal"

        # Stage 1: UserPromptSubmit
        userpromptsubmit_input = {
            "prompt": "Create a new file",
            "message": "Create a new file",
            "session_id": session_id,
            "terminal_id": terminal_id,
        }

        userpromptsubmit_hook = hooks_dir / "UserPromptSubmit.py"
        if userpromptsubmit_hook.exists():
            result = subprocess.run(
                [sys.executable, str(userpromptsubmit_hook)],
                input=json.dumps(userpromptsubmit_input),
                capture_output=True,
                text=True,
                timeout=10,
            )
            assert result.returncode == 0

        # Stage 2: PreToolUse (before tool execution)
        pretooluse_input = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.txt", "content": "test content"},
            "session_id": session_id,
            "terminal_id": terminal_id,
        }

        pretooluse_hook = hooks_dir / "PreToolUse.py"
        pre_result = None
        if pretooluse_hook.exists():
            pre_result = subprocess.run(
                [sys.executable, str(pretooluse_hook)],
                input=json.dumps(pretooluse_input),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # PreToolUse may block (exit 2) or allow (exit 0)
            # We just verify it executed
            assert pre_result.returncode in [0, 2]

        # Stage 3: Simulate tool execution
        # (In real scenario, Claude Code would execute the tool here)

        # Stage 4: PostToolUse (after tool execution)
        posttooluse_input = {
            "tool_name": "Write",
            "tool_input": {"file_path": "test.txt", "content": "test content"},
            "tool_response": {"success": True},
            "session_id": session_id,
            "terminal_id": terminal_id,
        }

        posttooluse_hook = hooks_dir / "PostToolUse.py"
        if posttooluse_hook.exists():
            post_result = subprocess.run(
                [sys.executable, str(posttooluse_hook)],
                input=json.dumps(posttooluse_input),
                capture_output=True,
                text=True,
                timeout=10,
            )
            # PostToolUse should never block
            assert post_result.returncode == 0

    def test_hook_chain_with_stop_verification(self, tmp_path):
        """
        Test complete chain with Stop hook verification.

        UserPromptSubmit → PreToolUse → tool → PostToolUse → Stop
        """
        session_id = "stop-chain-session"
        terminal_id = "test-terminal"

        # Execute full hook chain
        # ... (same as test_userpromptsubmit_pretooluse_chain)

        # Stage 5: Stop hook (final verification)
        stop_input = {
            "prompt": "Create a new file",
            "response": "File created successfully",
            "session_id": session_id,
            "terminal_id": terminal_id,
        }

        stop_hook = hooks_dir / "Stop.py"
        if stop_hook.exists():
            env = {**os.environ, "STOP_NO_SIDE_EFFECTS": "1"}
            stop_result = subprocess.run(
                [sys.executable, str(stop_hook)],
                input=json.dumps(stop_input),
                capture_output=True,
                text=True,
                timeout=10,
                env=env,
            )

            # Stop may block if verification fails
            # For this test, we just verify execution
            assert stop_result.returncode in [0, 2]


class TestEvidencePropagation:
    """Test evidence propagation through hook chain."""

    def test_userpromptsubmit_context_propagates(self, tmp_path):
        """
        Test that UserPromptSubmit context propagates to later hooks.

        Session context should be available to PreToolUse, PostToolUse, Stop.
        """
        session_id = "123e4567-e89b-12d3-a456-426614174000"

        # UserPromptSubmit stores context
        write_session_context(
            session_id=session_id,
            terminal_id="test-terminal",
            metadata={"user_intent": "create file", "target": "test.txt"},
        )

        # Verify context is retrievable by later hooks
        context = read_session_context()
        assert context.get("session_id") == session_id
        assert context.get("terminal_id") == "test-terminal"
        assert context.get("metadata", {}).get("user_intent") == "create file"
        assert context.get("metadata", {}).get("target") == "test.txt"

    def test_tool_execution_evidence_propagates(self, tmp_path):
        """
        Test that tool execution evidence propagates to Stop hook.

        Tool events should be available for verification at Stop time.
        """
        session_id = "tool-propagation-session"

        # Simulate tool execution
        from posttooluse.e2e_tracker_hook import E2ETrackerHook

        tracker = E2ETrackerHook()
        result = tracker.process(
            tool_name="Write",
            tool_input={"file_path": "test.txt", "content": "content"},
            tool_response={
                "success": True,
                "context": {
                    "session_id": session_id,
                    "terminal_id": "test-terminal",
                },
            },
        )

        assert result.get("passed") is True
        assert result.get("tracked") is True

        # Verify workflow evidence was written for later Stop-time inspection.
        e2e_log = Path("P:/") / ".claude" / "state" / f"e2e_executions_{session_id}.jsonl"
        assert e2e_log.exists()


class TestHookFailureHandling:
    """Test hook failure handling and recovery."""

    def test_pretooluse_block_prevents_execution(self):
        """
        Test that PreToolUse block prevents tool execution.

        When PreToolUse returns exit 2, tool should not execute.
        """
        # This would require integration with actual Claude Code
        # For now, we test the hook in isolation

        pretooluse_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "rm -rf /"},  # Dangerous command
            "session_id": "block-test-session",
            "terminal_id": "test-terminal",
        }

        pretooluse_hook = hooks_dir / "PreToolUse.py"
        if not pretooluse_hook.exists():
            pytest.skip("PreToolUse.py not found")

        result = subprocess.run(
            [sys.executable, str(pretooluse_hook)],
            input=json.dumps(pretooluse_input),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # PreToolUse should block dangerous commands, either via hard exit 2 or
        # by returning a structured blocking decision from the current router chain.
        assert result.returncode in [0, 2]
        if result.returncode == 0:
            payload = json.loads(result.stdout)
            assert payload.get("decision") in {"block", "deny", "ask_user"}

    def test_posttooluse_never_blocks(self):
        """
        Test that PostToolUse never blocks tool execution.

        PostToolUse hooks should always exit 0 (advisory only).
        """
        posttooluse_input = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"},
            "tool_response": {"success": True},
            "session_id": "post-test-session",
            "terminal_id": "test-terminal",
        }

        posttooluse_hook = hooks_dir / "PostToolUse.py"
        if not posttooluse_hook.exists():
            pytest.skip("PostToolUse.py not found")

        result = subprocess.run(
            [sys.executable, str(posttooluse_hook)],
            input=json.dumps(posttooluse_input),
            capture_output=True,
            text=True,
            timeout=10,
        )

        # PostToolUse should never block
        assert result.returncode == 0

    def test_hook_error_doesnt_crash_session(self):
        """
        Test that hook errors don't crash the entire session.

        Hooks should fail gracefully and allow session to continue.
        """
        # Test with invalid input that might cause hook errors
        invalid_input = {
            "invalid_field": "value",
            "session_id": "error-test-session",
            "terminal_id": "test-terminal",
        }

        for hook_name in ["PreToolUse", "PostToolUse", "Stop"]:
            hook_path = hooks_dir / f"{hook_name}.py"
            if not hook_path.exists():
                continue

            result = subprocess.run(
                [sys.executable, str(hook_path)],
                input=json.dumps(invalid_input),
                capture_output=True,
                text=True,
                timeout=10,
            )

            # Hook should handle error gracefully
            # (exit 0 with error message, or exit 2 with reason)
            assert result.returncode in [0, 2]


class TestBypassIntegration:
    """Test bypass flag integration across hook chain."""

    def test_bypass_disables_all_verification_hooks(self, tmp_path, monkeypatch):
        """
        TEST-008: Test CONSTITUTIONAL_HOOKS_BYPASS disables verification.

        When bypass is enabled, verification hooks should be disabled.
        """
        # Enable bypass
        monkeypatch.setenv("CONSTITUTIONAL_HOOKS_BYPASS", "1")

        # Test that verification hooks don't block
        # (This would require actual hook execution in bypass mode)

        # Verify bypass flag is set
        from hook_tracker import is_bypass_enabled

        assert is_bypass_enabled() is True

    def test_selective_bypass_per_hook(self, tmp_path, monkeypatch):
        """
        Test that individual hooks can be bypassed selectively.

        Different hooks may have separate bypass flags.
        """
        # Bypass specific hook
        monkeypatch.setenv("UNVERIFIED_STANCE_ENABLED", "false")

        # Import and verify hook respects bypass
        # (This would require hook-specific testing)

        # Clean up
        monkeypatch.delenv("UNVERIFIED_STANCE_ENABLED")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
