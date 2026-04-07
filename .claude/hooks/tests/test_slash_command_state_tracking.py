#!/usr/bin/env python3
"""Test slash command state tracking fix (v3.5).

Tests that Stop hook correctly reads state file to determine if slash command
was satisfied, instead of relying on flaky tools_used field.
"""

import json

# Add hooks directory to path
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PreToolUse_workflow_steps_gate import _update_command_intent_state
from StopHook_skill_execution_gate import run
from UserPromptSubmit_modules.skill_enforcer import _store_command_intent


def test_state_file_created_with_satisfied_flags():
    """Test that _store_command_intent creates state file with v3.5 fields."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create mock HookContext
        class MockContext:
            def __init__(self):
                self.data = {"session": {"id": "test-session-123"}}
                self.prompt = "/git"
                self.session_id = "test-session-123"
                self.terminal_id = "test-terminal-abc"

        # Mock the state directory to temp directory
        with patch("UserPromptSubmit_modules.skill_enforcer.INTENT_STATE_DIR", tmp_path):
            context = MockContext()
            _store_command_intent(context, "git")

            # Check that state file was created
            state_file = tmp_path / "pending_command_intent_test-terminal-abc.json"
            assert state_file.exists(), "State file should be created"

            # Verify v3.5 fields are present
            data = json.loads(state_file.read_text())
            assert data["skill"] == "git"
            assert data["skill_loaded"] is False
            assert data["execution_tools_used"] is False
            assert data["satisfied"] is False
            print("✅ State file created with v3.5 satisfaction tracking fields")


def test_state_updates_when_skill_loaded():
    """Test that state is updated when Skill tool is called."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create initial state file
        state_file = tmp_path / "pending_command_intent_test-terminal.json"
        initial_state = {
            "skill": "git",
            "skill_loaded": False,
            "execution_tools_used": False,
            "satisfied": False,
            "terminal_id": "test-terminal",
        }
        state_file.write_text(json.dumps(initial_state))

        # Mock _get_intent_file to return our test file
        with patch("PreToolUse_workflow_steps_gate._get_intent_file", return_value=state_file):
            # Update state for skill_loaded
            updated = _update_command_intent_state(skill_loaded=True)
            assert updated is True, "State should be updated"

            # Verify skill_loaded flag is set
            data = json.loads(state_file.read_text())
            assert data["skill_loaded"] is True
            assert data["satisfied"] is False  # Not satisfied until execution tool used
            print("✅ State updated when Skill tool is loaded")


def test_state_updates_when_execution_tool_used():
    """Test that state is updated and satisfied flag is set."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create initial state file with skill_loaded=True
        state_file = tmp_path / "pending_command_intent_test-terminal.json"
        initial_state = {
            "skill": "git",
            "skill_loaded": True,
            "execution_tools_used": False,
            "satisfied": False,
            "terminal_id": "test-terminal",
        }
        state_file.write_text(json.dumps(initial_state))

        # Mock _get_intent_file to return our test file
        with patch("PreToolUse_workflow_steps_gate._get_intent_file", return_value=state_file):
            # Update state for execution_tools_used
            updated = _update_command_intent_state(execution_tools_used=True)
            assert updated is True, "State should be updated"

            # Verify both flags are set and satisfied=True
            data = json.loads(state_file.read_text())
            assert data["skill_loaded"] is True
            assert data["execution_tools_used"] is True
            assert data["satisfied"] is True  # Both conditions met!
            print("✅ State marked as satisfied when execution tool is used")


def test_stop_hook_respects_satisfied_state():
    """Test that Stop hook allows stop when satisfied=True in state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create state directory structure
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create state file with satisfied=True
        state_file = state_dir / "pending_command_intent_test-terminal.json"
        satisfied_state = {
            "skill": "git",
            "skill_loaded": True,
            "execution_tools_used": True,
            "satisfied": True,
            "terminal_id": "test-terminal",
        }
        state_file.write_text(json.dumps(satisfied_state))

        # Mock state directory and terminal detection
        with patch("StopHook_skill_execution_gate.HOOKS_DIR", tmp_path):
            with patch(
                "skill_guard.utils.terminal_detection.detect_terminal_id",
                return_value="test-terminal",
            ):
                # Create Stop hook input with empty tools_used (platform bug condition)
                input_data = {
                    "user_prompt": "/git",
                    "tools_used": [],  # Empty despite successful execution!
                    "transcript_path": str(tmp_path / "transcript.jsonl"),
                }

                # Call Stop hook
                result = run(input_data)

                # Should allow stop (returns None) because satisfied=True in state
                assert result is None, "Stop hook should allow stop when satisfied=True"
                print("✅ Stop hook respects satisfied state, ignores empty tools_used")


def test_stop_hook_blocks_when_not_satisfied():
    """Test that Stop hook hard-blocks when satisfied=False in state."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create state directory structure
        state_dir = tmp_path / "state"
        state_dir.mkdir(parents=True, exist_ok=True)

        # Create state file with satisfied=False (only skill_loaded, no execution)
        state_file = state_dir / "pending_command_intent_test-terminal.json"
        unsatisfied_state = {
            "skill": "git",
            "skill_loaded": True,
            "execution_tools_used": False,
            "satisfied": False,
            "terminal_id": "test-terminal",
        }
        state_file.write_text(json.dumps(unsatisfied_state))

        # Mock state directory and terminal detection
        with patch("StopHook_skill_execution_gate.HOOKS_DIR", tmp_path):
            with patch(
                "skill_guard.utils.terminal_detection.detect_terminal_id",
                return_value="test-terminal",
            ):
                # Create Stop hook input with empty tools_used
                input_data = {
                    "user_prompt": "/git",
                    "tools_used": [],
                    "transcript_path": str(tmp_path / "transcript.jsonl"),
                }

                # Call Stop hook
                result = run(input_data)

                # Should return a workflow block when satisfied=False
                assert result is not None, "Stop hook should return block when satisfied=False"
                assert result.get("block") is True
                assert "WORKFLOW_BLOCK_NOT_HOOK_CRASH" in result.get("reason", "")
                assert "SLASH COMMAND NOT EXECUTED" in result.get("reason", "")
                print("✅ Stop hook blocks when slash command not satisfied")


if __name__ == "__main__":
    test_state_file_created_with_satisfied_flags()
    test_state_updates_when_skill_loaded()
    test_state_updates_when_execution_tool_used()
    test_stop_hook_respects_satisfied_state()
    test_stop_hook_blocks_when_not_satisfied()
    print("\n✅ All tests passed!")
