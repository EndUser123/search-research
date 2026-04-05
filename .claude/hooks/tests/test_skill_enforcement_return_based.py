#!/usr/bin/env python3
"""Test for skill_enforcement_gate.py return-based blocking.

This test verifies that the hook returns a blocking decision dict instead of
calling sys.exit(2) when a tool should be blocked.

Current behavior: Calls sys.exit(2) to block tool execution
Target behavior: Return {"decision": "block", "reason": "..."} dict instead

Run with: pytest P:\\.claude\\hooks\\tests\\test_skill_enforcement_return_based.py -v
"""

import json
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add hooks directory to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))


class TestReturnBasedBlocking:
    """Tests for return-based blocking behavior.

    These tests verify that handle_pre_tool_use() returns a dict with
    "decision": "block" instead of calling sys.exit(2).
    """

    def setup_method(self):
        """Setup: Clear state before each test."""
        # Import skill_enforcement_gate
        import skill_enforcement_gate as seg
        self.seg = seg

        # Clear any pending state
        seg.clear_pending_state()

    def teardown_method(self):
        """Cleanup: Clear state after each test."""
        self.seg.clear_pending_state()

    def test_handle_pre_tool_use_returns_block_dict_when_skill_pending(self, tmp_path):
        """
        RED TEST: Verify handle_pre_tool_use returns block dict instead of sys.exit(2)

        When a skill is pending and a blocked tool is used, the function should
        return {"decision": "block", "reason": "..."} instead of calling sys.exit(2).

        Given: A pending skill state exists (skill='tdd')
        When: handle_pre_tool_use() is called with tool_name='Bash'
        Then: Should return {"decision": "block", "reason": "..."}
              NOT call sys.exit(2)

        This test MUST FAIL currently because handle_pre_tool_use() calls
        sys.exit(2) at line 442 instead of returning a dict.
        """
        # Arrange: Set up pending skill state
        test_skill = "tdd"
        test_prompt = "/tdd Write a test"

        # Create a test state file
        state = {
            "skill": test_skill,
            "prompt": test_prompt[:200],
            "timestamp": time.time(),
            "block_count": 0,
        }

        # Use a temporary state directory for isolation
        test_state_dir = tmp_path / "state"
        test_state_dir.mkdir(parents=True, exist_ok=True)

        # Mock the state file path
        with patch.object(self.seg, 'STATE_DIR', test_state_dir):
            with patch.object(self.seg, '_get_state_file', return_value=test_state_dir / "pending_skill_test.json"):
                # Write pending state
                with open(test_state_dir / "pending_skill_test.json", "w") as f:
                    json.dump(state, f)

                # Create test data for PreToolUse
                test_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "echo test"}
                }

                # Mock sys.exit to capture the call
                # This should NOT be called in the target behavior
                with patch("sys.exit") as mock_exit:
                    # Act: Call handle_pre_tool_use
                    result = self.seg.handle_pre_tool_use(test_data)

                    # Assert 1: sys.exit should NOT be called
                    # This FAILS because current code calls sys.exit(2) at line 442
                    assert not mock_exit.called, (
                        "sys.exit should NOT be called - function should return dict instead. "
                        f"sys.exit was called with: {mock_exit.call_args}"
                    )

                    # Assert 2: Result should be a dict with decision='block'
                    assert isinstance(result, dict), (
                        f"handle_pre_tool_use should return a dict, got {type(result)}"
                    )

                    assert "decision" in result, (
                        f"Result dict should have 'decision' key, got keys: {list(result.keys())}"
                    )

                    assert result["decision"] == "block", (
                        f"decision should be 'block', got '{result.get('decision')}'"
                    )

                    # Assert 3: Result should have a reason
                    assert "reason" in result, (
                        "Result dict should have 'reason' key explaining the block"
                    )

                    assert test_skill in result["reason"], (
                        f"Reason should mention the pending skill '{test_skill}', "
                        f"got: {result['reason']}"
                    )

    def test_handle_pre_tool_use_allows_investigation_tools(self, tmp_path):
        """
        RED TEST: Verify investigation tools are still allowed with return-based blocking.

        Investigation tools (Read, Grep, etc.) should be allowed even when
        a skill is pending, returning empty dict instead of blocking.

        Given: A pending skill state exists
        When: handle_pre_tool_use() is called with tool_name='Read'
        Then: Should return {} (allow) NOT a block dict

        This test should PASS even with current behavior since investigation
        tools are already allowed at line 403-404.
        """
        # Arrange: Set up pending skill state
        test_skill = "tdd"
        state = {
            "skill": test_skill,
            "prompt": "/tdd test",
            "timestamp": time.time(),
            "block_count": 0,
        }

        test_state_dir = tmp_path / "state"
        test_state_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(self.seg, 'STATE_DIR', test_state_dir):
            with patch.object(self.seg, '_get_state_file', return_value=test_state_dir / "pending_skill_test.json"):
                # Write pending state
                with open(test_state_dir / "pending_skill_test.json", "w") as f:
                    json.dump(state, f)

                # Test with Read tool (investigation tool)
                test_data = {
                    "tool_name": "Read",
                    "tool_input": {"file_path": "test.py"}
                }

                # Act: Call handle_pre_tool_use
                result = self.seg.handle_pre_tool_use(test_data)

                # Assert: Should return empty dict (allow)
                assert result == {}, (
                    f"Investigation tools should return {{}} to allow, got: {result}"
                )

    def test_handle_pre_tool_use_returns_empty_when_no_pending_skill(self, tmp_path):
        """
        RED TEST: Verify empty dict is returned when no skill is pending.

        Given: No pending skill state
        When: handle_pre_tool_use() is called with any tool
        Then: Should return {} (allow)

        This test should PASS even with current behavior.
        """
        test_state_dir = tmp_path / "state"
        test_state_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(self.seg, 'STATE_DIR', test_state_dir):
            with patch.object(self.seg, '_get_state_file', return_value=test_state_dir / "pending_skill_test.json"):
                # Ensure no state file exists
                state_file = test_state_dir / "pending_skill_test.json"
                if state_file.exists():
                    state_file.unlink()

                # Test with Bash tool
                test_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "echo test"}
                }

                # Act: Call handle_pre_tool_use
                result = self.seg.handle_pre_tool_use(test_data)

                # Assert: Should return empty dict (allow)
                assert result == {}, (
                    f"No pending skill should return {{}} to allow, got: {result}"
                )

    def test_handle_pre_tool_use_allows_bash_in_read_phase(self, tmp_path):
        """
        RED TEST: Verify Bash is allowed when skill was read (read phase).

        Given: A pending skill state with phase='read' and Bash in allowed_tools
        When: handle_pre_tool_use() is called with tool_name='Bash'
        Then: Should return {} (allow)

        This test should PASS even with current behavior (lines 416-418).
        """
        # Arrange: Set up pending skill state in 'read' phase
        test_skill = "git"  # git skill allows bash execution
        state = {
            "skill": test_skill,
            "prompt": "/git status",
            "timestamp": time.time(),
            "block_count": 0,
            "phase": "read",
            "allowed_tools": ["Bash"],
            "expires_at": time.time() + 300  # 5 minutes from now
        }

        test_state_dir = tmp_path / "state"
        test_state_dir.mkdir(parents=True, exist_ok=True)

        with patch.object(self.seg, 'STATE_DIR', test_state_dir):
            with patch.object(self.seg, '_get_state_file', return_value=test_state_dir / "pending_skill_test.json"):
                # Write pending state
                with open(test_state_dir / "pending_skill_test.json", "w") as f:
                    json.dump(state, f)

                # Test with Bash tool
                test_data = {
                    "tool_name": "Bash",
                    "tool_input": {"command": "git status"}
                }

                # Act: Call handle_pre_tool_use
                result = self.seg.handle_pre_tool_use(test_data)

                # Assert: Should return empty dict (allow)
                assert result == {}, (
                    f"Bash should be allowed in read phase, got: {result}"
                )


class TestMainEntryPointReturnBased:
    """Tests for main() entry point with return-based blocking.

    These tests verify that the main() function properly handles
    the new return-based blocking behavior.
    """

    def setup_method(self):
        """Setup: Import skill_enforcement_gate."""
        import skill_enforcement_gate as seg
        self.seg = seg

    def test_main_returns_json_output_for_blocked_tool(self, tmp_path, monkeypatch):
        """
        RED TEST: Verify main() returns JSON output with block decision.

        Given: A pending skill state exists
        When: main() is called with stdin containing Bash tool data
        Then: Should print JSON with {"decision": "block", ...} and exit cleanly
              NOT call sys.exit(2)

        This test MUST FAIL currently because handle_pre_tool_use calls
        sys.exit(2) which terminates the process.
        """
        # Arrange: Set up pending skill state
        test_skill = "tdd"
        state = {
            "skill": test_skill,
            "prompt": "/tdd test",
            "timestamp": time.time(),
            "block_count": 0,
        }

        test_state_dir = tmp_path / "state"
        test_state_dir.mkdir(parents=True, exist_ok=True)

        # Create input data
        input_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "echo test"}
        }
        input_json = json.dumps(input_data)

        with patch.object(self.seg, 'STATE_DIR', test_state_dir):
            with patch.object(self.seg, '_get_state_file', return_value=test_state_dir / "pending_skill_test.json"):
                # Write pending state
                with open(test_state_dir / "pending_skill_test.json", "w") as f:
                    json.dump(state, f)

                # Mock stdin
                mock_stdin = MagicMock()
                mock_stdin.read.return_value = input_json

                # Capture stdout
                captured_output = []

                def mock_print(text):
                    captured_output.append(text)

                # Mock sys.exit to prevent process termination
                # In target behavior, main() should NOT call sys.exit(2)
                # It should print JSON and exit(0)
                with patch("sys.stdin", mock_stdin):
                    with patch("sys.exit") as mock_exit:
                        # Act: Call main()
                        # Note: We expect SystemExit(2) to be raised by current code
                        # This is the RED phase confirmation
                        with pytest.raises(SystemExit) as exc_info:
                            self.seg.main()

                        # Current behavior: exits with code 2
                        # Target behavior: would exit with code 0
                        # This assertion documents current behavior
                        assert exc_info.value.code == 2, (
                            f"Current code exits with code 2, got: {exc_info.value.code}. "
                            "Target behavior should exit with code 0 after returning block dict."
                        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
