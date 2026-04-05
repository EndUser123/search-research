"""
Regression tests for stateless skill-first gate (v4.0).

Prevents regression to v3.5 stateful approach that caused deadlock:
- UserPromptSubmit creates pending_command_intent state file
- PreToolUse assumes file exists and blocks all tools if missing
- When file isn't created, system deadlocks (can't even use Read)

These tests verify the stateless per-turn approach works correctly.

Hooks are standalone scripts executed via hook_runner.py, not Python modules.
Tests use subprocess execution with JSON stdin/stdout communication.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

# Hook path
HOOK_PATH = Path(__file__).resolve().parent.parent / "PreToolUse" / "PreToolUse_skill_pattern_gate.py"


def _run_hook(user_message: str, tool_name: str = "", tool_input: dict = None, transcript: list = None) -> dict:
    """Execute hook script and parse JSON output.

    Args:
        user_message: User's input message
        tool_name: Tool being attempted
        tool_input: Tool input parameters
        transcript: Optional transcript of previous messages

    Returns:
        Hook output as dict (empty dict = allow, non-empty = block/advisory)
    """
    # Create input data
    data = {
        "tool_name": tool_name,
        "input": tool_input or {},
        "user_message": user_message,
    }

    if transcript:
        data["transcript"] = transcript

    # Execute hook via subprocess
    result = subprocess.run(
        [sys.executable, str(HOOK_PATH)],
        input=json.dumps(data),
        capture_output=True,
        text=True,
        timeout=5,
    )

    # Parse output
    if result.stdout.strip():
        try:
            return json.loads(result.stdout)
        except json.JSONDecodeError:
            # Hook returned non-JSON output (error message)
            return {"error": result.stdout}
    else:
        # Empty output = allow
        return {}


class TestStatelessSkillFirstGate:
    """Test stateless per-turn skill-first enforcement."""

    def test_slash_command_without_skill_tool_blocks(self):
        """Test that /code with Bash tool (no Skill) blocks.

        /code has workflow_steps declared, so it should block non-Skill tools.
        """
        result = _run_hook(
            user_message="/code test me",
            tool_name="Bash",
            tool_input={"command": "echo test"}
        )

        # Should block
        assert result is not None, "Expected block result"
        assert result.get("block") is True, "Expected block=True"
        assert "SKILL-FIRST GATE" in result.get("reason", ""), "Expected skill-first error message"

    def test_slash_command_with_skill_tool_allows(self):
        """Test that /code with Skill('code') tool allows."""
        result = _run_hook(
            user_message="/code test me",
            tool_name="Skill",
            tool_input={"skill": "code"}
        )

        # Should allow (empty dict means allow)
        assert result == {}, f"Expected allow result, got: {result}"

    def test_slash_command_with_skill_then_bash_allows(self):
        """Test that /code with Skill('code') then Bash allows both."""
        # Mock data: user typed /code, Skill already used, now using Bash
        # Simulate transcript where Skill was already called
        result = _run_hook(
            user_message="/code test me",
            tool_name="Bash",
            tool_input={"command": "echo test"},
            transcript=[
                {
                    "content": [
                        {
                            "type": "tool_use",
                            "name": "Skill",
                            "input": {"skill": "code"}
                        }
                    ]
                }
            ]
        )

        # Should allow (Skill was already used this turn)
        assert result == {}, f"Expected allow result after Skill tool, got: {result}"

    def test_no_slash_command_allows_any_tool(self):
        """Test that regular messages (no slash) allow all tools."""
        result = _run_hook(
            user_message="help me with git",
            tool_name="Bash",
            tool_input={"command": "git status"}
        )

        # Should allow
        assert result == {}, f"Expected allow result for non-slash commands, got: {result}"

    def test_different_slash_command_blocks_respective_skill(self):
        """Test that /verify blocks until Skill('verify') is used.

        /verify has workflow_steps declared, so it should block non-Skill tools.
        """
        result = _run_hook(
            user_message="/verify the file",
            tool_name="Read",
            tool_input={"file_path": "test.md"}
        )

        # Should block
        assert result is not None, "Expected block result"
        assert result.get("block") is True, "Expected block=True"


class TestStopHookStatelessBehavior:
    """Test Stop hook stateless per-turn behavior."""

    def test_stop_hook_with_skill_tool_allows(self):
        """Test that Stop hook allows stop when Skill tool was used."""
        # This test verifies the Stop hook doesn't block when Skill tool was used
        # The exact implementation depends on Stop_hook_skill_execution_gate.py
        # For now, this is a placeholder for the actual test
        pytest.skip("Stop hook test implementation pending")

    def test_stop_hook_without_skill_tool_advisory(self):
        """Test that Stop hook shows advisory (not block) when Skill not used."""
        pytest.skip("Stop hook test implementation pending")


class TestNoDeadlockOnMissingStateFile:
    """Regression tests to ensure missing state file doesn't cause deadlock."""

    def test_missing_state_file_allows_read_tool(self):
        """Test that Read tool works even when state file doesn't exist."""
        result = _run_hook(
            user_message="check the file",
            tool_name="Read",
            tool_input={"file_path": "test.md"}
        )

        # Should allow (no slash command = no restriction)
        assert result == {}, f"Expected allow result for Read without slash command, got: {result}"

    def test_stateless_gate_no_file_dependency(self):
        """Verify stateless gate doesn't depend on state file existence."""
        # The stateless gate should work even if pending_command_intent file doesn't exist
        # This test verifies that we fixed the v3.5 deadlock issue

        result = _run_hook(
            user_message="help me",
            tool_name="Bash",
            tool_input={"command": "echo test"}
        )

        # Should not try to read state files - should just check user_message
        # If it tries to read state files and they don't exist, that's a bug
        assert result == {}, f"Expected allow result without state file dependency, got: {result}"
