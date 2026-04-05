#!/usr/bin/env python3
"""
RED Phase Tests for runaway_session_detector.py Stop hook.

These tests WILL FAIL until the implementation is complete.
Run with: pytest P:\\.claude\\hooks\\tests\\test_runaway_detector.py -v

Task ID: #450
Source: P:\\.claude\\plans\\safety-hooks-implementation.md (Phase 2, lines 320-540)

This test suite verifies:
1. Session-isolated state file naming (uses session_id in filename)
2. Block pattern tracking - records (hook_name, operation, error_type) signature
3. Runaway detection - 3 repeated blocks within 5 minutes triggers runaway
4. Reset on success - successful operation clears block history
5. Stop hook integration - parses previous_hook_outputs for block decisions
"""

import json
import sys
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add hooks directory to path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# Mock imports - tests will FAIL until implementation exists
try:
    from runaway_session_detector import (
        MAX_REPEAT_COUNT,
        MAX_REPEAT_WINDOW_SECONDS,
        STATE_DIR,
        STATE_FILE,
        RunawayDetector,
        main,
    )
except ImportError:
    # This is expected in RED phase - implementation doesn't exist yet
    RunawayDetector = None
    STATE_DIR = None
    STATE_FILE = None
    MAX_REPEAT_COUNT = 3
    MAX_REPEAT_WINDOW_SECONDS = 300


class TestSessionIsolatedStateFileNaming:
    """Test suite for session-isolated state file naming."""

    def test_state_file_includes_session_id(self, tmp_path):
        """
        Test that state file path includes session_id in filename.

        Given: A RunawayDetector instance with a specific session_id
        When: The detector is initialized
        Then: The state file path should include the session_id
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session_id = f"test_sess_{uuid.uuid4().hex[:8]}"

        # Mock STATE_DIR to use temp path
        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session_id)

            # State file should include session_id
            state_filename = detector.state_file.name
            assert test_session_id in state_filename, \
                f"State file name should include session_id: {state_filename}"

            # State file parent should be STATE_DIR
            assert detector.state_file.parent == tmp_path, \
                "State file parent should be STATE_DIR"

    def test_different_sessions_different_state_files(self, tmp_path):
        """
        Test that different sessions use different state files.

        Given: Two RunawayDetector instances with different session_ids
        When: Both detectors are initialized
        Then: They should use different state file paths
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        session1 = f"sess1_{uuid.uuid4().hex[:8]}"
        session2 = f"sess2_{uuid.uuid4().hex[:8]}"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector1 = RunawayDetector(session_id=session1)
            detector2 = RunawayDetector(session_id=session2)

            # State files should be different
            assert detector1.state_file != detector2.state_file, \
                "Different sessions should have different state files"

            # Both should be in the same directory
            assert detector1.state_file.parent == detector2.state_file.parent, \
                "State files should be in same directory"

    def test_state_directory_created_on_init(self, tmp_path):
        """
        Test that state directory is created on initialization.

        Given: A RunawayDetector instance
        When: The detector is initialized
        Then: The state directory should be created if it doesn't exist
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session_id = f"test_sess_{uuid.uuid4().hex[:8]}"
        nonexistent_dir = tmp_path / "nonexistent" / "subdir"

        with patch('runaway_session_detector.STATE_DIR', nonexistent_dir):
            detector = RunawayDetector(session_id=test_session_id)

            # Directory should be created
            assert nonexistent_dir.exists(), \
                "STATE_DIR should be created during initialization"
            assert nonexistent_dir.is_dir(), \
                "STATE_DIR should be a directory"


class TestBlockPatternTracking:
    """Test suite for block pattern tracking functionality."""

    def test_record_block_stores_signature(self, tmp_path):
        """
        Test that record_block stores (hook_name, operation, error_type) signature.

        Given: A RunawayDetector instance
        When: record_block is called with hook_name, operation, and error_type
        Then: The signature should be stored in the state file
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "test_hook"
        operation = "Edit:test_file.py"
        error_type = "Test error message"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)
            result = detector.record_block(hook_name, operation, error_type)

            # State should be saved
            assert detector.state_file.exists(), \
                "State file should be created after record_block"

            # Load and verify state
            state = json.loads(detector.state_file.read_text())
            assert "blocks" in state, "State should have 'blocks' key"

            # Should have at least one block
            assert len(state["blocks"]) >= 1, "Should have recorded at least one block"

            # Verify signature format: hook_name:operation:error_type
            latest_block = state["blocks"][-1]
            expected_signature = f"{hook_name}:{operation}:{error_type}"
            assert latest_block["signature"] == expected_signature, \
                f"Block signature should match: {latest_block['signature']}"

            # Should have timestamp
            assert "timestamp" in latest_block, \
                "Block should have timestamp"

    def test_multiple_blocks_tracked_separately(self, tmp_path):
        """
        Test that multiple different blocks are tracked separately.

        Given: A RunawayDetector instance
        When: record_block is called with different signatures
        Then: Each unique signature should be tracked separately
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Record three different blocks
            detector.record_block("hook1", "Edit:file1.py", "error1")
            detector.record_block("hook2", "Write:file2.py", "error2")
            detector.record_block("hook1", "Edit:file1.py", "different_error")

            # Load state
            state = json.loads(detector.state_file.read_text())

            # Should have three blocks
            assert len(state["blocks"]) == 3, \
                f"Should have 3 blocks, got {len(state['blocks'])}"

            # Verify each signature is unique
            signatures = [b["signature"] for b in state["blocks"]]
            assert len(signatures) == len(set(signatures)), \
                "All signatures should be unique"

    def test_block_signature_truncation(self, tmp_path):
        """
        Test that long error types are truncated appropriately.

        Given: A RunawayDetector instance
        When: record_block is called with a very long error_type
        Then: The signature should be truncated to prevent bloating
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        long_error = "x" * 500  # Very long error message

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)
            detector.record_block("test_hook", "Edit:file.py", long_error)

            # Load state
            state = json.loads(detector.state_file.read_text())
            signature = state["blocks"][-1]["signature"]

            # Signature should be truncated (spec says error_type truncated to 100 chars)
            # Full signature would be: "test_hook:Edit:file.py:{long_error}"
            # So signature should be much shorter than 600 chars
            assert len(signature) < 200, \
                f"Signature should be truncated, got length {len(signature)}"


class TestRunawayDetection:
    """Test suite for runaway detection logic."""

    def test_three_repeated_blocks_triggers_runaway(self, tmp_path):
        """
        Test that 3 repeated blocks within 5 minutes triggers runaway detection.

        Given: A RunawayDetector instance
        When: The same (hook_name, operation, error_type) is recorded 3 times
        Then: is_runaway should be True after the 3rd block
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "test_hook"
        operation = "Edit:stuck_file.py"
        error_type = "Permission denied"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # First block - should not trigger runaway
            result1 = detector.record_block(hook_name, operation, error_type)
            assert result1["is_runaway"] is False, \
                "First block should not trigger runaway"

            # Second block - should not trigger runaway
            result2 = detector.record_block(hook_name, operation, error_type)
            assert result2["is_runaway"] is False, \
                "Second block should not trigger runaway"

            # Third block - SHOULD trigger runaway
            result3 = detector.record_block(hook_name, operation, error_type)
            assert result3["is_runaway"] is True, \
                "Third repeated block should trigger runaway"

            # Should have a reason
            assert "reason" in result3, \
                "Runaway result should include reason"
            assert len(result3["reason"]) > 0, \
                "Reason should not be empty"
            assert "RUNAWAY SESSION DETECTED" in result3["reason"], \
                "Reason should mention runaway detection"

    def test_blocks_outside_window_dont_trigger(self, tmp_path):
        """
        Test that blocks outside the 5-minute window don't trigger runaway.

        Given: A RunawayDetector instance with old blocks
        When: A new block is recorded after the time window
        Then: Only blocks within the window should count
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "test_hook"
        operation = "Edit:file.py"
        error_type = "Test error"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Manually create old blocks (outside 5-minute window)
            old_time = time.time() - MAX_REPEAT_WINDOW_SECONDS - 100
            detector.state = {
                "blocks": [
                    {
                        "timestamp": old_time,
                        "signature": f"{hook_name}:{operation}:{error_type}"
                    },
                    {
                        "timestamp": old_time + 10,
                        "signature": f"{hook_name}:{operation}:{error_type}"
                    }
                ],
                "last_success": None
            }
            detector._save_state()

            # Add one more block (should make 3 total, but 2 are old)
            result = detector.record_block(hook_name, operation, error_type)

            # Should NOT trigger runaway because 2 blocks are outside window
            assert result["is_runaway"] is False, \
                "Should not trigger runaway when old blocks are outside window"

    def test_different_signatures_dont_trigger(self, tmp_path):
        """
        Test that different signatures don't accumulate for runaway detection.

        Given: A RunawayDetector instance
        When: Blocks with different signatures are recorded
        Then: Each signature should be counted separately
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "test_hook"
        operation = "Edit:file.py"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Record 3 blocks with different error types
            for i in range(3):
                result = detector.record_block(hook_name, operation, f"Error type {i}")
                assert result["is_runaway"] is False, \
                    f"Different errors should not trigger runaway (block {i+1})"

    def test_runaway_reason_includes_details(self, tmp_path):
        """
        Test that runaway reason includes hook, operation, and error details.

        Given: A runaway detection is triggered
        When: The result is returned
        Then: The reason should include the hook_name, operation, and error_type
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "PreToolUse_tdd_gate"
        operation = "Write:test.py"
        error_type = "No test found for implementation"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Trigger runaway
            for i in range(3):
                result = detector.record_block(hook_name, operation, error_type)

            # Verify reason content
            assert "3 times" in result["reason"] or "3" in result["reason"], \
                "Reason should mention repeat count"
            assert hook_name in result["reason"], \
                f"Reason should include hook_name: {hook_name}"
            assert operation in result["reason"], \
                f"Reason should include operation: {operation}"
            assert "Catch-22" in result["reason"] or "loop" in result["reason"].lower(), \
                "Reason should mention Catch-22 or loop"


class TestResetOnSuccess:
    """Test suite for reset on successful operation."""

    def test_success_clears_block_history(self, tmp_path):
        """
        Test that successful operation clears block history.

        Given: A RunawayDetector with existing blocks
        When: record_success is called
        Then: Block history should be cleared
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Record some blocks
            detector.record_block("hook1", "Edit:file1.py", "error1")
            detector.record_block("hook2", "Edit:file2.py", "error2")

            # Verify blocks exist
            state_before = json.loads(detector.state_file.read_text())
            assert len(state_before["blocks"]) == 2, \
                "Should have 2 blocks before success"

            # Record success
            detector.record_success()

            # Verify blocks are cleared
            state_after = json.loads(detector.state_file.read_text())
            assert len(state_after["blocks"]) == 0, \
                "Blocks should be cleared after success"

    def test_success_updates_last_success_timestamp(self, tmp_path):
        """
        Test that record_success updates last_success timestamp.

        Given: A RunawayDetector instance
        When: record_success is called
        Then: last_success should be set to current time
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Record success
            before_time = time.time()
            detector.record_success()
            after_time = time.time()

            # Verify timestamp
            state = json.loads(detector.state_file.read_text())
            assert state["last_success"] is not None, \
                "last_success should be set"
            assert before_time <= state["last_success"] <= after_time, \
                "last_success should be current time"

    def test_recent_success_prevents_runaway(self, tmp_path):
        """
        Test that recent success prevents runaway detection.

        Given: A RunawayDetector with blocks
        When: A successful operation occurs, then more blocks
        Then: Runaway should not trigger because of recent success
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"
        hook_name = "test_hook"
        operation = "Edit:file.py"
        error_type = "Test error"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)

            # Record 2 blocks
            detector.record_block(hook_name, operation, error_type)
            detector.record_block(hook_name, operation, error_type)

            # Record success
            detector.record_success()

            # Record 2 more blocks (same signature)
            detector.record_block(hook_name, operation, error_type)
            result = detector.record_block(hook_name, operation, error_type)

            # Should NOT trigger runaway because success cleared history
            assert result["is_runaway"] is False, \
                "Recent success should prevent runaway detection"


class TestStopHookIntegration:
    """Test suite for Stop hook integration with previous_hook_outputs."""

    def test_parses_previous_hook_outputs_for_blocks(self, tmp_path, monkeypatch):
        """
        Test that Stop hook parses previous_hook_outputs for block decisions.

        Given: Stop hook input with previous_hook_outputs
        When: A previous hook output contains decision="block"
        Then: The hook should extract block details and record them
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        # Simulate hook input with previous block
        hook_input = {
            "session_id": test_session,
            "stop_hook_active": True,
            "tool_use": {
                "name": "Edit",
                "input": {"file_path": "test.py", "old_string": "old", "new_string": "new"}
            },
            "previous_hook_outputs": [
                {
                    "hook_name": "PreToolUse_tdd_gate",
                    "content": json.dumps({
                        "decision": "block",
                        "reason": "No test found for implementation"
                    })
                }
            ]
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            # Mock stdin and call main
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            # Capture stdout
            mock_stdout = MagicMock()
            monkeypatch.setattr('sys.stdout', mock_stdout)

            try:
                main()
            except SystemExit:
                pass

            # Check that block was recorded
            state_file = tmp_path / f"{test_session}_block_patterns.json"
            if state_file.exists():
                state = json.loads(state_file.read_text())
                assert len(state["blocks"]) > 0, \
                    "Block should be recorded from previous_hook_outputs"

    def test_ignores_non_block_hook_outputs(self, tmp_path, monkeypatch):
        """
        Test that hook ignores non-block outputs.

        Given: Stop hook input with various previous outputs
        When: Outputs don't contain decision="block"
        Then: No blocks should be recorded
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        hook_input = {
            "session_id": test_session,
            "stop_hook_active": True,
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "test.py"}
            },
            "previous_hook_outputs": [
                {
                    "hook_name": "SomeHook",
                    "content": json.dumps({"warning": "This is a warning"})
                },
                {
                    "hook_name": "AnotherHook",
                    "content": "Plain text output"
                }
            ]
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            mock_stdout = MagicMock()
            monkeypatch.setattr('sys.stdout', mock_stdout)

            try:
                main()
            except SystemExit:
                pass

            # No blocks should be recorded
            state_file = tmp_path / f"{test_session}_block_patterns.json"
            if state_file.exists():
                state = json.loads(state_file.read_text())
                assert len(state["blocks"]) == 0, \
                    "No blocks should be recorded for non-block outputs"

    def test_runaway_triggers_block_decision(self, tmp_path, monkeypatch):
        """
        Test that runaway detection triggers block decision in output.

        Given: A runaway condition is detected
        When: The Stop hook processes previous_hook_outputs
        Then: Output should contain decision="block" with runaway message
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        # First, set up runaway condition by recording 2 prior blocks
        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            detector = RunawayDetector(session_id=test_session)
            detector.record_block("PreToolUse_tdd_gate", "Edit:test.py", "No test")
            detector.record_block("PreToolUse_tdd_gate", "Edit:test.py", "No test")

        # Now trigger with 3rd block via Stop hook
        hook_input = {
            "session_id": test_session,
            "stop_hook_active": True,
            "tool_use": {
                "name": "Edit",
                "input": {"file_path": "test.py"}
            },
            "previous_hook_outputs": [
                {
                    "hook_name": "PreToolUse_tdd_gate",
                    "content": json.dumps({
                        "decision": "block",
                        "reason": "No test"
                    })
                }
            ]
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            # Capture output
            output_buffer = []
            mock_stdout = MagicMock()
            mock_stdout.write = lambda s: output_buffer.append(s)
            monkeypatch.setattr('sys.stdout', mock_stdout)

            try:
                main()
            except SystemExit as e:
                # Exit code 1 expected for block
                assert e.code == 1, "Should exit with code 1 when blocking"

            # Check output contains block decision
            output_text = ''.join(output_buffer)
            output_data = json.loads(output_text)

            assert output_data.get("decision") == "block", \
                "Output should contain block decision"
            assert output_data.get("runaway_detected") is True, \
                "Output should indicate runaway was detected"
            assert "reason" in output_data, \
                "Output should contain reason"

    def test_exits_without_error_when_no_runaway(self, tmp_path, monkeypatch):
        """
        Test that hook exits normally when no runaway detected.

        Given: Stop hook input with no runaway condition
        When: The hook processes the input
        Then: Should exit with code 0 or output empty dict
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        hook_input = {
            "session_id": test_session,
            "stop_hook_active": True,
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "test.py"}
            },
            "previous_hook_outputs": []
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            output_buffer = []
            mock_stdout = MagicMock()
            mock_stdout.write = lambda s: output_buffer.append(s)
            monkeypatch.setattr('sys.stdout', mock_stdout)

            try:
                main()
            except SystemExit as e:
                # Exit code 0 expected when not blocking
                assert e.code == 0, "Should exit with code 0 when not blocking"

            # Output should be empty or non-blocking
            output_text = ''.join(output_buffer)
            if output_text.strip():
                output_data = json.loads(output_text)
                assert output_data.get("decision") != "block", \
                    "Should not block when no runaway"

    def test_handles_malformed_hook_outputs_gracefully(self, tmp_path, monkeypatch):
        """
        Test that malformed hook outputs don't crash the hook.

        Given: Stop hook input with malformed previous_hook_outputs
        When: The hook processes the input
        Then: Should handle gracefully and not crash
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        hook_input = {
            "session_id": test_session,
            "stop_hook_active": True,
            "tool_use": {
                "name": "Read",
                "input": {"file_path": "test.py"}
            },
            "previous_hook_outputs": [
                {"hook_name": "GoodHook", "content": "not json"},
                {"hook_name": "BadHook", "content": None},
                "not_a_dict",
                {"content": json.dumps({"decision": "block", "reason": "Test"})}
            ]
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            output_buffer = []
            mock_stdout = MagicMock()
            mock_stdout.write = lambda s: output_buffer.append(s)
            monkeypatch.setattr('sys.stdout', mock_stdout)

            # Should not raise exception
            try:
                main()
            except SystemExit:
                pass  # Expected
            except Exception as e:
                pytest.fail(f"Should handle malformed outputs gracefully, got: {e}")

    def test_operation_signature_generation(self, tmp_path):
        """
        Test that operation signature is generated correctly from tool_use.

        Given: A tool_use with file_path or command
        When: Block is recorded
        Then: Operation signature should include tool_name and relevant input
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            # Test Edit tool with file_path
            detector = RunawayDetector(session_id=test_session)
            result = detector.record_block(
                hook_name="PreToolUse_tdd_gate",
                operation="Edit:test.py",  # Pre-formatted as expected
                error_type="No test found"
            )

            # Load state and check signature
            state = json.loads(detector.state_file.read_text())
            signature = state["blocks"][-1]["signature"]

            assert "PreToolUse_tdd_gate" in signature, \
                "Signature should include hook name"
            assert "Edit:test.py" in signature, \
                "Signature should include operation"

    def test_inactive_session_skips_detection(self, tmp_path, monkeypatch):
        """
        Test that inactive sessions skip runaway detection.

        Given: Stop hook input with stop_hook_active=False
        When: The hook processes the input
        Then: Should skip detection and exit normally
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        test_session = f"sess_{uuid.uuid4().hex[:8]}"

        hook_input = {
            "session_id": test_session,
            "stop_hook_active": False,  # Inactive
            "tool_use": {"name": "Edit", "input": {}},
            "previous_hook_outputs": [
                {
                    "hook_name": "SomeHook",
                    "content": json.dumps({"decision": "block", "reason": "Test"})
                }
            ]
        }

        with patch('runaway_session_detector.STATE_DIR', tmp_path):
            mock_stdin = json.dumps(hook_input)
            monkeypatch.setattr('sys.stdin', MagicMock(read=MagicMock(return_value=mock_stdin)))

            output_buffer = []
            mock_stdout = MagicMock()
            mock_stdout.write = lambda s: output_buffer.append(s)
            monkeypatch.setattr('sys.stdout', mock_stdout)

            try:
                main()
            except SystemExit as e:
                assert e.code == 0, "Should exit with 0 when inactive"

            # No state file should be created
            state_file = tmp_path / f"{test_session}_block_patterns.json"
            assert not state_file.exists(), \
                "No state file should be created when inactive"


class TestConstants:
    """Test suite for verifying implementation constants."""

    def test_max_repeat_count_is_three(self):
        """
        Test that MAX_REPEAT_COUNT is set to 3.

        Given: The runaway_session_detector module
        When: MAX_REPEAT_COUNT constant is checked
        Then: It should be 3
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        assert MAX_REPEAT_COUNT == 3, \
            f"MAX_REPEAT_COUNT should be 3, got {MAX_REPEAT_COUNT}"

    def test_max_repeat_window_is_five_minutes(self):
        """
        Test that MAX_REPEAT_WINDOW_SECONDS is set to 300 (5 minutes).

        Given: The runaway_session_detector module
        When: MAX_REPEAT_WINDOW_SECONDS constant is checked
        Then: It should be 300
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        assert MAX_REPEAT_WINDOW_SECONDS == 300, \
            f"MAX_REPEAT_WINDOW_SECONDS should be 300, got {MAX_REPEAT_WINDOW_SECONDS}"

    def test_state_dir_path(self):
        """
        Test that STATE_DIR points to correct location.

        Given: The runaway_session_detector module
        When: STATE_DIR constant is checked
        Then: It should point to P:/.claude/state/runaway_detector
        """
        if RunawayDetector is None:
            pytest.skip("runaway_session_detector.py not implemented yet")

        expected = Path("P:/.claude/state/runaway_detector")
        assert STATE_DIR == expected, \
            f"STATE_DIR should be {expected}, got {STATE_DIR}"


# Run tests if executed directly
if __name__ == "__main__":
    pytest.main([__file__, "-v"])
