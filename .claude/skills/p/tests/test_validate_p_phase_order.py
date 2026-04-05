#!/usr/bin/env python3
"""
Tests for validate_p_phase_order.py hook script.

Tests phase order enforcement logic, including:
- Phase marker prerequisite validation
- Multi-terminal safety
- Error output format (stdout, not stderr)
"""

import json
import sys
import tempfile
import threading
import time
from io import StringIO
from pathlib import Path

import pytest

# Add lib directory to path
LIB_DIR = Path(__file__).parent.parent / "hooks"
sys.path.insert(0, str(LIB_DIR))

from validate_p_phase_order import main, marker_exists


class TestMarkerExists:
    """Test marker_exists helper function."""

    def test_marker_exists_true(self):
        """Returns True when marker file exists with correct content."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            assert marker_exists(marker, expected_phase=1) is True

    def test_marker_exists_false(self):
        """Returns False when marker file does not exist."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            assert marker_exists(marker, expected_phase=1) is False

    def test_marker_corrupted_wrong_phase(self):
        """Returns False when marker has wrong phase prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"
            # Write marker with wrong phase (should be Phase 1, not Phase 2)
            marker.write_text("Phase 2 completed at 2026-03-09T12:00:00\n")

            assert marker_exists(marker, expected_phase=1) is False

    def test_marker_empty_rejected(self):
        """Returns False when marker file is empty."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"
            marker.write_text("")

            assert marker_exists(marker, expected_phase=1) is False

    def test_marker_with_invalid_content_rejected(self):
        """Returns False when marker has no phase prefix."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"
            marker.write_text("Some random text without phase prefix\n")

            assert marker_exists(marker, expected_phase=1) is False


class TestPhaseOrderValidation:
    """Test phase order enforcement logic."""

    def _run_hook(self, phase: str, tool_name: str = "Skill", skill_name: str = "p") -> dict:
        """Helper to run hook with given input and return parsed output."""
        input_data = {
            "tool_name": tool_name,
            "tool_input": {
                "name": skill_name,
                "args": [f"--phase={phase}"]
            }
        }

        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run hook
            import unittest.mock as mock
            with mock.patch('sys.stdin', StringIO(json.dumps(input_data))):
                try:
                    main()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        # Parse output
        if output.strip():
            return json.loads(output), exit_code
        return {}, exit_code

    def test_p0_always_allowed(self):
        """P0 (Scaffold) should always be allowed without markers."""
        result, exit_code = self._run_hook("0")
        assert exit_code == 0
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_p1_always_allowed(self):
        """P1 (Build) should always be allowed without markers."""
        result, exit_code = self._run_hook("1")
        assert exit_code == 0
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_p2_requires_p1_marker(self):
        """P2 should require P1 marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                result, exit_code = self._run_hook("2")
                assert exit_code == 0  # Hooks always exit with 0
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P1 (Build)" in result["hookSpecificOutput"]["permissionDecisionReason"]
            finally:
                os.chdir(old_cwd)

    def test_p3_requires_p2_marker(self):
        """P3 should require P2 marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                result, exit_code = self._run_hook("3")
                assert exit_code == 0  # Hooks always exit with 0
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P2 (Review)" in result["hookSpecificOutput"]["permissionDecisionReason"]
            finally:
                os.chdir(old_cwd)

    def test_p4_requires_p3_marker(self):
        """P4 should require P3 marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                result, exit_code = self._run_hook("4")
                assert exit_code == 0  # Hooks always exit with 0
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P3 (Validate)" in result["hookSpecificOutput"]["permissionDecisionReason"]
            finally:
                os.chdir(old_cwd)

    def test_p5_requires_p4_marker(self):
        """P5 should require P4 marker."""
        with tempfile.TemporaryDirectory() as tmpdir:
            import os
            old_cwd = os.getcwd()
            os.chdir(tmpdir)

            try:
                result, exit_code = self._run_hook("5")
                assert exit_code == 0  # Hooks always exit with 0
                assert result["hookSpecificOutput"]["permissionDecision"] == "deny"
                assert "P4 (Publish)" in result["hookSpecificOutput"]["permissionDecisionReason"]
            finally:
                os.chdir(old_cwd)

    def test_auto_mode_always_allowed(self):
        """Auto mode should always be allowed."""
        result, exit_code = self._run_hook("auto")
        assert exit_code == 0
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_non_skill_tool_allowed(self):
        """Non-Skill tools should always be allowed."""
        result, exit_code = self._run_hook("2", tool_name="Read")
        assert exit_code == 0
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"

    def test_different_skill_allowed(self):
        """Different skill should be allowed."""
        result, exit_code = self._run_hook("2", skill_name="other-skill")
        assert exit_code == 0
        assert result["hookSpecificOutput"]["permissionDecision"] == "allow"


class TestJSONErrorHandling:
    """Test JSON error handling in hook input parsing."""

    def _run_hook_with_raw_input(self, raw_input: str) -> tuple[dict, int]:
        """Helper to run hook with raw stdin input (not pre-validated JSON)."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = StringIO()

        try:
            # Run hook with raw input
            import unittest.mock as mock
            with mock.patch('sys.stdin', StringIO(raw_input)):
                try:
                    main()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code
        finally:
            output = sys.stdout.getvalue()
            sys.stdout = old_stdout

        # Parse output
        if output.strip():
            try:
                return json.loads(output), exit_code
            except json.JSONDecodeError:
                # If output is also invalid JSON, return empty dict
                return {}, exit_code
        return {}, exit_code

    def test_malformed_json_returns_deny(self):
        """Malformed JSON input should return deny with error message."""
        # Test various malformed inputs
        malformed_inputs = [
            "",  # Empty input
            "{",  # Incomplete JSON
            "not json",  # Plain text
            '{"tool_name": "Skill", "tool_input": {"name": "p"}',  # Missing closing braces
            '{"tool_name": "Skill", broken json}',  # Invalid syntax
        ]

        for malformed_input in malformed_inputs:
            result, exit_code = self._run_hook_with_raw_input(malformed_input)

            # Should deny the request
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny", f"Expected deny for input: {malformed_input[:50]}"
            assert exit_code == 0, f"Expected exit code 0 for input: {malformed_input[:50]}"
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert "invalid" in reason.lower() or "json" in reason.lower(), \
                f"Expected JSON error message for input: {malformed_input[:50]}"


class TestStderrSanitization:
    """
    Test P0-002: Hook must not leak exception details to stderr.

    Regression test for P0-002 bug: Hook stderr leakage on exceptions.
    This test ensures that hooks sanitize error messages and never write
    exception tracebacks to stderr, which could leak sensitive information
    or break JSON parsing in calling processes.
    """

    @pytest.mark.regression
    def test_malformed_json_no_stderr_leak(self, capsys):
        """
        Test P0-002: Hook sanitizes errors - no exception traceback to stderr.

        Given: Malformed JSON input that triggers json.JSONDecodeError
        When: Hook processes the input
        Then:
            - stdout contains JSON error response with permissionDecision
            - stderr is EMPTY (no exception traceback leaked)
        """
        import unittest.mock as mock

        # Test various malformed inputs that trigger exceptions
        malformed_inputs = [
            "",  # Empty input
            "{",  # Incomplete JSON
            "not json",  # Plain text
            '{"tool_name": "Skill", "tool_input": {"name": "p"}',  # Missing closing braces
            '{"tool_name": "Skill", broken json}',  # Invalid syntax
        ]

        for malformed_input in malformed_inputs:
            # Clear any previous captures
            capsys.readouterr()

            # Run hook with malformed input
            with mock.patch('sys.stdin', StringIO(malformed_input)):
                try:
                    main()
                    exit_code = 0
                except SystemExit as e:
                    exit_code = e.code

            # Capture stdout and stderr
            captured = capsys.readouterr()
            stdout_output = captured.out
            stderr_output = captured.err

            # Verify stdout contains valid JSON error response
            assert stdout_output.strip(), f"Expected stdout output for input: {malformed_input[:50]}"
            result = json.loads(stdout_output)
            assert result["hookSpecificOutput"]["permissionDecision"] == "deny", \
                f"Expected deny decision for input: {malformed_input[:50]}"
            reason = result["hookSpecificOutput"]["permissionDecisionReason"]
            assert "invalid" in reason.lower() or "json" in reason.lower(), \
                f"Expected JSON error message for input: {malformed_input[:50]}"

            # CRITICAL: Verify stderr is EMPTY (no exception traceback leaked)
            assert stderr_output == "", \
                f"P0-002 VIOLATION: stderr must be empty but got: {stderr_output[:200]} for input: {malformed_input[:50]}"

    def test_unexpected_exception_no_stderr_leak(self, capsys):
        """
        Test P0-002: Unexpected exceptions don't leak to stderr.

        Given: Input that could trigger unexpected exceptions (e.g., None, missing keys)
        When: Hook processes the input
        Then:
            - stdout contains JSON error response with permissionDecision
            - stderr is EMPTY (no exception traceback leaked)

        This test ensures the hook catches ALL exceptions, not just JSONDecodeError.
        """
        import traceback
        import unittest.mock as mock

        # Test inputs that might trigger different exceptions
        edge_case_inputs = [
            "null",  # JSON null - could cause NoneType errors
            "[]",  # Empty array - missing expected keys
            "{}",  # Empty object - missing tool_name, tool_input
            '{"tool_name": null}',  # Null tool_name
            '{"tool_name": "Skill"}',  # Missing tool_input
        ]

        for edge_input in edge_case_inputs:
            # Clear any previous captures
            capsys.readouterr()

            # Run hook with edge case input - catch ANY exception
            with mock.patch('sys.stdin', StringIO(edge_input)):
                exception_caught = False
                try:
                    main()
                except SystemExit:
                    # Normal exit - hook handled it
                    pass
                except Exception:
                    # Unexpected exception - hook didn't catch it!
                    # This is the P0-002 bug - exception details could leak to stderr
                    exception_caught = True
                    # Get the traceback that would have gone to stderr
                    tb_str = traceback.format_exc()

            # Capture stdout and stderr
            captured = capsys.readouterr()
            stdout_output = captured.out
            stderr_output = captured.err

            # If an exception was raised (not caught by hook), that's a failure
            # The hook MUST catch all exceptions and return JSON responses
            assert not exception_caught, \
                f"P0-002 VIOLATION: Hook raised uncaught exception for input: {edge_input[:50]}\n" + \
                f"Exception details that leaked: {tb_str}"

            # Verify hook doesn't crash - should always produce output
            assert stdout_output.strip(), f"Expected stdout output for edge case: {edge_input[:50]}"

            # Parse output safely
            try:
                result = json.loads(stdout_output)
                # Should have a permission decision (allow or deny)
                assert "permissionDecision" in result.get("hookSpecificOutput", {}), \
                    f"Expected permissionDecision for edge case: {edge_input[:50]}"
            except json.JSONDecodeError:
                # If output isn't valid JSON, that's also a problem
                assert False, f"Hook produced non-JSON output for edge case: {edge_input[:50]}"

            # CRITICAL: Verify stderr is EMPTY (no exception traceback leaked)
            assert stderr_output == "", \
                f"P0-002 VIOLATION: stderr must be empty but got: {stderr_output[:200]} for edge case: {edge_input[:50]}"


class TestMultiTerminalSafety:
    """Test multi-terminal safety of marker operations."""

    def test_concurrent_marker_checks(self):
        """Multiple terminals can check markers safely."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            # Multiple checks should succeed
            assert marker_exists(marker, expected_phase=1) is True
            assert marker_exists(marker, expected_phase=1) is True
            assert marker_exists(marker, expected_phase=1) is True

    def test_marker_creation_is_idempotent(self):
        """Creating marker multiple times is safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create marker multiple times
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            # Should still exist and be valid
            assert marker_exists(marker, expected_phase=1) is True
            assert "Phase 1 completed" in marker.read_text()


    def test_concurrent_marker_write_read(self):
        """One terminal can write while another reads - should be safe."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            read_results = []
            write_complete = threading.Event()

            def read_marker():
                """Thread that reads the marker multiple times."""
                for _ in range(10):
                    result = marker_exists(marker, expected_phase=1)
                    read_results.append(result)
                    time.sleep(0.001)  # Small delay to interleave operations

            def write_marker():
                """Thread that writes to the marker."""
                # Wait a bit to let reads start
                time.sleep(0.005)
                marker.write_text("Phase 1 completed at 2026-03-09T12:00:01\n")
                write_complete.set()

            # Start both threads
            reader = threading.Thread(target=read_marker)
            writer = threading.Thread(target=write_marker)
            reader.start()
            writer.start()

            # Wait for completion
            reader.join()
            writer.join()

            # All reads should have succeeded (either old or new content)
            assert len(read_results) == 10
            assert all(read_results), "All reads should return True"

            # Final marker should be valid
            assert marker_exists(marker, expected_phase=1) is True

    def test_concurrent_marker_write_write(self):
        """Two terminals writing simultaneously - last write wins (file system atomicity)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            write_count = [0]
            errors = []

            def write_marker(thread_id: int):
                """Thread that writes to the marker."""
                try:
                    for i in range(5):
                        timestamp = f"2026-03-09T12:00:{thread_id}{i}"
                        marker.write_text(f"Phase 1 completed at {timestamp}\n")
                        write_count[0] += 1
                        time.sleep(0.001)
                except Exception as e:
                    errors.append(e)

            # Start multiple writer threads
            threads = []
            for i in range(3):
                t = threading.Thread(target=write_marker, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All writes should have completed
            assert write_count[0] == 15  # 3 threads * 5 writes

            # Final marker should be valid (one of the writes won)
            assert marker_exists(marker, expected_phase=1) is True
            content = marker.read_text()
            assert "Phase 1 completed at" in content
            assert "Phase 1" in content

    def test_marker_state_after_concurrent_access(self):
        """Run 10 threads doing concurrent checks, verify state consistency."""
        with tempfile.TemporaryDirectory() as tmpdir:
            state_dir = Path(tmpdir) / "state"
            state_dir.mkdir(parents=True)
            marker = state_dir / "p1-complete.marker"

            # Create initial marker
            marker.write_text("Phase 1 completed at 2026-03-09T12:00:00\n")

            results = []
            errors = []

            def access_marker(thread_id: int):
                """Thread that reads and validates the marker."""
                try:
                    for _ in range(10):
                        # Check if marker exists
                        exists = marker.exists()
                        if exists:
                            # Validate content
                            valid = marker_exists(marker, expected_phase=1)
                            results.append((thread_id, exists, valid))
                        time.sleep(0.001)
                except Exception as e:
                    errors.append((thread_id, e))

            # Start multiple threads
            threads = []
            for i in range(10):
                t = threading.Thread(target=access_marker, args=(i,))
                threads.append(t)
                t.start()

            # Wait for all threads
            for t in threads:
                t.join()

            # No errors should have occurred
            assert len(errors) == 0, f"Errors occurred: {errors}"

            # All checks should have found the marker valid
            assert len(results) == 100  # 10 threads * 10 reads
            for thread_id, exists, valid in results:
                assert exists, f"Thread {thread_id}: Marker should exist"
                assert valid, f"Thread {thread_id}: Marker should be valid"

            # Final marker state should still be valid
            assert marker_exists(marker, expected_phase=1) is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
