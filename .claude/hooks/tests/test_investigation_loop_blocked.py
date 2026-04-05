#!/usr/bin/env python3
"""
Test suite for investigation loop detection feature in recursive_failure_detector.py.

These tests verify that the hook detects and blocks investigation loops where
the agent performs read-only operations (Read, Grep, Search) without any
write operations (Write, Bash, Edit) across multiple consecutive tool calls.

Feature Requirements:
- Add READ_ONLY_CYCLE_LIMIT = 3 (lower than FAILURE_THRESHOLD)
- Detect sequences of Read/Grep/Search without Write/Bash/Edit
- Add prescriptive directive for investigation loops
- Lower threshold for read-only cycles (vs. actual failures)

Test Categories:
1. Positive cases (should trigger detection/blocking)
2. Negative cases (should NOT trigger)
3. Edge cases
"""

import json
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import recursive_failure_detector as rfd


class TestInvestigationLoopDetection:
    """
    Test suite for investigation loop detection.

    Tests verify that sequences of read-only operations (Read, Grep, Glob)
    trigger blocking after READ_ONLY_CYCLE_LIMIT consecutive operations,
    while sequences that include Write, Bash, or Edit operations do not.
    """

    def setup_method(self):
        """Create temporary session directory for each test."""
        import os

        # Store original bypass setting and disable for testing
        self.original_bypass = os.environ.get("CONSTITUTIONAL_HOOKS_BYPASS")
        if "CONSTITUTIONAL_HOOKS_BYPASS" in os.environ:
            del os.environ["CONSTITUTIONAL_HOOKS_BYPASS"]

        # Create temporary session directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_session_dir = rfd.SESSION_DIR
        rfd.SESSION_DIR = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary session directory."""
        import os

        # Restore original bypass setting
        rfd.SESSION_DIR = self.original_session_dir
        if self.original_bypass is not None:
            os.environ["CONSTITUTIONAL_HOOKS_BYPASS"] = self.original_bypass
        elif "CONSTITUTIONAL_HOOKS_BYPASS" in os.environ:
            del os.environ["CONSTITUTIONAL_HOOKS_BYPASS"]

        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    # =========================================================================
    # POSITIVE CASES - Should trigger blocking
    # =========================================================================

    def test_four_consecutive_read_operations_should_block(self):
        """
        Test: 4 consecutive Read operations → BLOCK

        Given: Tool history with 4 Read operations
        When: A 5th Read operation is attempted
        Then: The operation should be blocked
        """
        # Arrange: Create 4 consecutive Read failures
        for i in range(4):
            rfd.save_failure(
                tool="Read",
                cmd_hash="abc12345",
                error_snippet=f"Read attempt {i+1}"
            )

        # Act: Attempt another Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read some file",
            file_path="test.py"
        )

        # Assert: Should be blocked
        assert result.get("block") is True, "Should block after 4 consecutive Read operations"
        assert "investigation loop" in result.get("message", "").lower(), \
            "Block message should mention investigation loop"

    def test_three_consecutive_grep_operations_should_block(self):
        """
        Test: 3 Grep operations in sequence → BLOCK

        Given: Tool history with 3 Grep operations
        When: A 4th Grep operation is attempted
        Then: The operation should be blocked
        """
        # Arrange: Create 3 consecutive Grep failures
        for i in range(3):
            rfd.save_failure(
                tool="Grep",
                cmd_hash="grep123",
                error_snippet=f"Grep attempt {i+1}"
            )

        # Act: Attempt another Grep operation
        result = rfd.check_for_catch22(
            tool="Grep",
            command="grep pattern file.py",
            file_path=""
        )

        # Assert: Should be blocked
        assert result.get("block") is True, "Should block after 3 consecutive Grep operations"
        assert "investigation loop" in result.get("message", "").lower(), \
            "Block message should mention investigation loop"

    def test_mixed_read_only_tools_should_block(self):
        """
        Test: Mix of Read/Grep/Search (3 total) → BLOCK

        Given: Tool history with Read → Grep → Read sequence
        When: Another read-only tool is attempted
        Then: The operation should be blocked
        """
        # Arrange: Create mixed read-only sequence
        rfd.save_failure("Read", "read123", "Read file")
        rfd.save_failure("Grep", "grep456", "Search pattern")
        rfd.save_failure("Glob", "glob789", "Find files")

        # Act: Attempt another read-only operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read another file",
            file_path="test.py"
        )

        # Assert: Should be blocked
        assert result.get("block") is True, \
            "Should block after 3 mixed read-only operations"

    def test_read_only_cycle_across_time_window(self):
        """
        Test: Read-only cycle across 10-minute window → BLOCK

        Given: Tool history with 3 read-only operations within 10 minutes
        When: Another read-only operation is attempted
        Then: The operation should be blocked
        """
        # Arrange: Create read-only operations within time window
        now = datetime.now()
        failures = []

        # Create 3 failures spaced within 10 minutes
        for i in range(3):
            timestamp = now + timedelta(minutes=i*3)  # 0, 3, 6 minutes
            failures.append({
                "timestamp": timestamp.isoformat(),
                "tool": "Read",
                "command_hash": "read123",
                "error_snippet": f"Read attempt {i+1}"
            })

        # Manually save failures
        session_file = rfd.get_session_file()
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_file, "w") as f:
            json.dump(failures, f)

        # Act: Attempt another read-only operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read another file",
            file_path="test.py"
        )

        # Assert: Should be blocked
        assert result.get("block") is True, \
            "Should block read-only cycle within time window"

    def test_exactly_three_read_only_operations_should_block(self):
        """
        Test: Exactly 3 read-only operations → BLOCK

        Given: Tool history with exactly 3 read-only operations
        When: Another read-only operation is attempted
        Then: The operation should be blocked (threshold is 3)
        """
        # Arrange: Create exactly 3 read-only failures
        for i in range(3):
            rfd.save_failure("Read", "read123", f"Read {i+1}")

        # Act: Attempt 4th read-only operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be blocked
        assert result.get("block") is True, \
            "Should block at exactly 3 read-only operations (threshold)"

    # =========================================================================
    # NEGATIVE CASES - Should NOT trigger blocking
    # =========================================================================

    def test_two_read_operations_should_allow(self):
        """
        Test: 2 Read operations → ALLOW

        Given: Tool history with only 2 Read operations
        When: A 3rd Read operation is attempted
        Then: The operation should be allowed (below threshold)
        """
        # Arrange: Create only 2 Read failures
        for i in range(2):
            rfd.save_failure("Read", "read123", f"Read {i+1}")

        # Act: Attempt 3rd Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed
        assert result.get("allow") is True, \
            "Should allow with only 2 read-only operations (below threshold)"

    def test_read_write_read_sequence_should_allow(self):
        """
        Test: Read → Write → Read sequence → ALLOW

        Given: Tool history with mixed read/write operations
        When: Any operation is attempted
        Then: The operation should be allowed (has Write in sequence)
        """
        # Arrange: Create mixed sequence with Write
        rfd.save_failure("Read", "read123", "Read file")
        rfd.save_failure("Write", "write456", "Write file")
        rfd.save_failure("Read", "read789", "Read another file")

        # Act: Attempt another Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed (Write breaks the cycle)
        assert result.get("allow") is True, \
            "Should allow when Write operation breaks read-only cycle"

    def test_bash_operations_should_allow(self):
        """
        Test: Bash operations included → ALLOW

        Given: Tool history with Bash operations
        When: Any operation is attempted
        Then: The operation should be allowed (Bash is not read-only)
        """
        # Arrange: Create sequence with Bash
        rfd.save_failure("Read", "read123", "Read file")
        rfd.save_failure("Bash", "bash456", "Run command")
        rfd.save_failure("Read", "read789", "Read another file")

        # Act: Attempt another Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed (Bash breaks the cycle)
        assert result.get("allow") is True, \
            "Should allow when Bash operation breaks read-only cycle"

    def test_edit_operations_should_allow(self):
        """
        Test: Edit operations included → ALLOW

        Given: Tool history with Edit operations
        When: Any operation is attempted
        Then: The operation should be allowed (Edit is not read-only)
        """
        # Arrange: Create sequence with Edit
        rfd.save_failure("Read", "read123", "Read file")
        rfd.save_failure("Edit", "edit456", "Edit file")
        rfd.save_failure("Read", "read789", "Read another file")

        # Act: Attempt another Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed (Edit breaks the cycle)
        assert result.get("allow") is True, \
            "Should allow when Edit operation breaks read-only cycle"

    # =========================================================================
    # EDGE CASES
    # =========================================================================

    def test_empty_tool_history_should_allow(self):
        """
        Test: Empty tool history → ALLOW

        Given: No previous tool operations
        When: Any operation is attempted
        Then: The operation should be allowed
        """
        # Arrange: No failures saved (empty history)

        # Act: Attempt Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed
        assert result.get("allow") is True, \
            "Should allow with empty tool history"

    def test_tools_outside_time_window_should_allow(self):
        """
        Test: Tools outside time window → ALLOW

        Given: Tool history with read-only operations older than 10 minutes
        When: A new operation is attempted
        Then: The operation should be allowed (old ops don't count)
        """
        # Arrange: Create old failures (outside time window)
        old_time = datetime.now() - timedelta(minutes=15)
        failures = []
        for i in range(3):
            failures.append({
                "timestamp": (old_time + timedelta(minutes=i)).isoformat(),
                "tool": "Read",
                "command_hash": "read123",
                "error_snippet": f"Old read {i+1}"
            })

        # Save old failures
        session_file = rfd.get_session_file()
        session_file.parent.mkdir(parents=True, exist_ok=True)
        with open(session_file, "w") as f:
            json.dump(failures, f)

        # Act: Attempt Read operation
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Should be allowed (old ops outside window)
        assert result.get("allow") is True, \
            "Should allow when previous operations are outside time window"

    def test_test_file_operations_should_bypass(self):
        """
        Test: Test file operations → BYPASS investigation loop check

        Given: Attempting to write a test file
        When: Even with many read-only operations in history
        Then: The operation should be allowed (test files exempt)
        """
        # Arrange: Create many read-only failures
        for i in range(5):
            rfd.save_failure("Read", "read123", f"Read {i+1}")

        # Act: Attempt to write test file
        result = rfd.check_for_catch22(
            tool="Write",
            command="Write test file",
            file_path="tests/test_feature.py"  # Test file path
        )

        # Assert: Should be allowed (test file exemption)
        assert result.get("allow") is True, \
            "Should bypass investigation loop check for test files"

    def test_investigation_loop_prescriptive_directive(self):
        """
        Test: Investigation loop includes prescriptive directive

        Given: An investigation loop is detected
        When: The block message is generated
        Then: The message should include prescriptive directive
        """
        # Arrange: Create investigation loop
        for i in range(4):
            rfd.save_failure("Read", "read123", f"Read {i+1}")

        # Act: Trigger block
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file",
            file_path="test.py"
        )

        # Assert: Message should include directive
        assert result.get("block") is True
        message = result.get("message", "")
        assert len(message) > 0, "Block message should not be empty"
        # Check for directive indicators (specific wording may vary)
        assert "loop" in message.lower() or "investigat" in message.lower(), \
            "Block message should mention loop or investigation"

    def test_read_only_limit_constant_exists(self):
        """
        Test: READ_ONLY_CYCLE_LIMIT constant exists

        Given: The recursive_failure_detector module
        When: Checking for READ_ONLY_CYCLE_LIMIT constant
        Then: The constant should exist and be different from FAILURE_THRESHOLD
        """
        # Act & Assert: Check constant exists
        assert hasattr(rfd, 'READ_ONLY_CYCLE_LIMIT'), \
            "Module should define READ_ONLY_CYCLE_LIMIT constant"

        # Assert: Should be different from FAILURE_THRESHOLD
        # (investigation loop uses broader pattern, so can have different threshold)
        if hasattr(rfd, 'READ_ONLY_CYCLE_LIMIT'):
            assert rfd.READ_ONLY_CYCLE_LIMIT != rfd.FAILURE_THRESHOLD, \
                f"READ_ONLY_CYCLE_LIMIT ({rfd.READ_ONLY_CYCLE_LIMIT}) should differ from FAILURE_THRESHOLD ({rfd.FAILURE_THRESHOLD})"


class TestInvestigationLoopIntegration:
    """
    Integration tests for investigation loop detection.

    These tests verify the complete flow including state management,
    time window filtering, and interaction with existing Catch-22 logic.
    """

    def setup_method(self):
        """Create temporary session directory for each test."""
        import os

        # Store original bypass setting and disable for testing
        self.original_bypass = os.environ.get("CONSTITUTIONAL_HOOKS_BYPASS")
        if "CONSTITUTIONAL_HOOKS_BYPASS" in os.environ:
            del os.environ["CONSTITUTIONAL_HOOKS_BYPASS"]

        # Create temporary session directory
        self.temp_dir = tempfile.mkdtemp()
        self.original_session_dir = rfd.SESSION_DIR
        rfd.SESSION_DIR = Path(self.temp_dir)

    def teardown_method(self):
        """Clean up temporary session directory."""
        import os

        # Restore original bypass setting
        rfd.SESSION_DIR = self.original_session_dir
        if self.original_bypass is not None:
            os.environ["CONSTITUTIONAL_HOOKS_BYPASS"] = self.original_bypass
        elif "CONSTITUTIONAL_HOOKS_BYPASS" in os.environ:
            del os.environ["CONSTITUTIONAL_HOOKS_BYPASS"]

        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_investigation_loop_with_different_command_hashes(self):
        """
        Test: Investigation loop detected across different command hashes

        Given: Multiple read-only operations with different command patterns
        When: The threshold is reached
        Then: Should block (counting all read-only operations, not just identical)
        """
        # Arrange: Create read-only ops with different hashes
        rfd.save_failure("Read", "hash1", "Read file1.py")
        rfd.save_failure("Read", "hash2", "Read file2.py")
        rfd.save_failure("Grep", "hash3", "Grep pattern")

        # Act: Attempt another read-only op
        result = rfd.check_for_catch22(
            tool="Read",
            command="Read file3.py",
            file_path="file3.py"
        )

        # Assert: Should block (counts all read-only, not same-command)
        assert result.get("block") is True, \
            "Should block investigation loop across different command patterns"

    def test_regular_catch22_not_confused_with_investigation_loop(self):
        """
        Test: Regular Catch-22 (same command) vs investigation loop

        Given: Multiple failures of the same command (regular Catch-22)
        When: The FAILURE_THRESHOLD is reached
        Then: Should use regular Catch-22 message, not investigation loop
        """
        # Arrange: Compute hash for test command
        test_command = "python script.py"
        cmd_hash = rfd.compute_command_hash(test_command)

        # Create same-command failures (regular Catch-22)
        for i in range(rfd.FAILURE_THRESHOLD):
            rfd.save_failure(
                tool="Bash",
                cmd_hash=cmd_hash,  # Use actual computed hash
                error_snippet=f"Command failed {i+1}"
            )

        # Act: Attempt same command again
        result = rfd.check_for_catch22(
            tool="Bash",
            command=test_command,  # Same command
            file_path=""
        )

        # Assert: Should block with Catch-22 message
        assert result.get("block") is True
        message = result.get("message", "")
        # Regular Catch-22 mentions "operation pattern failed"
        # Investigation loop mentions "read-only" or "investigation"
        # This test ensures we're not mixing them up
        assert "catch-22" in message.lower(), \
            "Should show Catch-22 message for repeated same-command failures"


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v"])
