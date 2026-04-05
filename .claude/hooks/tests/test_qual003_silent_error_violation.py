#!/usr/bin/env python3
"""QUAL-003: Silent failure - no error logging.

Violation: CLAUDE.md "Fail fast ALWAYS. NO graceful degradation, NO error masking"

Target violations in PostToolUse_task_tracker.py:
- Line 156: mark_as_tracked() - except OSError: pass
- Line 198: save_session_state() - except OSError: pass
- Line 182-188: load_session_state() - except (OSError, ValueError): return default
- Line 328-329: get_all_sessions_tasks() - except (OSError, ValueError): continue

This test file ENFORCES the constitutional requirement that errors MUST be logged.
These tests are EXPECTED TO FAIL until the violations are fixed.

Test strategy:
1. Simulate OSError during state save/load operations
2. Verify error is logged (not silently ignored)
3. Verify logging captures error details
"""

from __future__ import annotations

import io
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add hooks dir to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))


class TestQual003MarkAsTrackedErrorLogging:
    """QUAL-003: mark_as_tracked must log OSError (line 156 violation)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_mark_as_tracked_must_log_oserror(self):
        """FAILING TEST: mark_as_tracked MUST log OSError, not silent pass.

        Given: OSError occurs when creating marker file (e.g., permission denied)
        When: mark_as_tracked() is called
        Then: Error MUST be logged to stderr with error details

        This test ENFORCES: CLAUDE.md "Fail fast ALWAYS"
        Current violation (line 156): except OSError: pass
        """
        from PostToolUse_task_tracker import get_marker_path, mark_as_tracked

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Create a marker path
            marker_path = get_marker_path("test_terminal", "task_123")

            # Mock Path.touch() to raise OSError
            with patch.object(Path, "touch", side_effect=OSError("[Errno 13] Permission denied")):
                # Capture stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()

                try:
                    # Execute
                    mark_as_tracked(marker_path)

                    # Verify error was logged (not silently ignored)
                    stderr_output = sys.stderr.getvalue()

                    # THIS ASSERTION WILL FAIL until line 156 is fixed
                    assert len(stderr_output) > 0, (
                        "QUAL-003 VIOLATION: OSError was silently ignored (line 156: except OSError: pass). "
                        "Constitutional requirement: 'Fail fast ALWAYS. NO graceful degradation, NO error masking'. "
                        "Error MUST be logged to stderr for debugging."
                    )

                    # Verify error details are captured
                    assert any(term in stderr_output for term in ["Permission denied", "OSError", "13", "mark_as_tracked"]), (
                        "QUAL-003 VIOLATION: Error logging must capture error details. "
                        "stderr should contain error message, error type, or error code."
                    )
                finally:
                    sys.stderr = old_stderr


class TestQual003SaveSessionStateErrorLogging:
    """QUAL-003: save_session_state must log OSError (line 198 violation)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_save_session_state_must_log_oserror(self):
        """FAILING TEST: save_session_state MUST log OSError, not silent pass.

        Given: OSError occurs when writing state file (e.g., disk full, permission denied)
        When: save_session_state() is called
        Then: Error MUST be logged to stderr with error details

        This test ENFORCES: CLAUDE.md "Fail fast ALWAYS"
        Current violation (line 198): except OSError: pass
        """
        from PostToolUse_task_tracker import save_session_state

        test_state = {
            "session_id": "test_session",
            "tasks": {},
            "last_update": None,
            "recent_files": [],
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Mock Path.write_text() to raise OSError
            with patch.object(Path, "write_text", side_effect=OSError("[Errno 28] No space left on device")):
                # Capture stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()

                try:
                    # Execute
                    save_session_state("test_session", test_state)

                    # Verify error was logged (not silently ignored)
                    stderr_output = sys.stderr.getvalue()

                    # THIS ASSERTION WILL FAIL until line 198 is fixed
                    assert len(stderr_output) > 0, (
                        "QUAL-003 VIOLATION: OSError was silently ignored (line 198: except OSError: pass). "
                        "Constitutional requirement: 'Fail fast ALWAYS. NO graceful degradation, NO error masking'. "
                        "Error MUST be logged to stderr for debugging."
                    )

                    # Verify error details are captured
                    assert any(term in stderr_output for term in ["No space left", "OSError", "28", "save_session_state"]), (
                        "QUAL-003 VIOLATION: Error logging must capture error details. "
                        "stderr should contain error message, error type, or error code."
                    )
                finally:
                    sys.stderr = old_stderr


class TestQual003LoadSessionStateErrorLogging:
    """QUAL-003: load_session_state must log OSError (line 182-188 violation)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_load_session_state_must_log_oserror(self):
        """FAILING TEST: load_session_state MUST log OSError on read failure.

        Given: OSError occurs when reading state file (e.g., file locked, corrupted)
        When: load_session_state() is called on existing file
        Then: Error MUST be logged to stderr with error details

        This test ENFORCES: CLAUDE.md "Fail fast ALWAYS"
        Current violation (line 182-188): except (OSError, ValueError): return default
        """
        from PostToolUse_task_tracker import load_session_state

        # Create a state file first
        state_path = self.state_dir / "test_session_tasks.json"
        state_path.write_text('{"session_id": "test"}')

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Mock Path.read_text() to raise OSError
            with patch.object(Path, "read_text", side_effect=OSError("[Errno 11] Resource temporarily unavailable")):
                # Capture stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()

                try:
                    # Execute
                    result = load_session_state("test_session")

                    # Should return default state on error (this is acceptable behavior)
                    assert result["session_id"] == "test_session"

                    # Verify error was logged (not silently ignored)
                    stderr_output = sys.stderr.getvalue()

                    # THIS ASSERTION WILL FAIL until line 182-188 is fixed
                    assert len(stderr_output) > 0, (
                        "QUAL-003 VIOLATION: OSError was silently ignored (line 182-188: except (OSError, ValueError): return default). "
                        "Constitutional requirement: 'Fail fast ALWAYS. NO graceful degradation, NO error masking'. "
                        "Error MUST be logged to stderr for debugging."
                    )

                    # Verify error details are captured
                    assert any(term in stderr_output for term in ["Resource temporarily unavailable", "OSError", "11", "load_session_state"]), (
                        "QUAL-003 VIOLATION: Error logging must capture error details. "
                        "stderr should contain error message, error type, or error code."
                    )
                finally:
                    sys.stderr = old_stderr


class TestQual003GetAllSessionsTasksErrorLogging:
    """QUAL-003: get_all_sessions_tasks must log OSError (line 328-329 violation)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_get_all_sessions_tasks_must_log_oserror(self):
        """FAILING TEST: get_all_sessions_tasks MUST log OSError on file processing.

        Given: OSError occurs when reading a session state file
        When: get_all_sessions_tasks() processes state files
        Then: Error MUST be logged to stderr, not silently continued

        This test ENFORCES: CLAUDE.md "Fail fast ALWAYS"
        Current violation (line 328-329): except (OSError, ValueError): continue
        """
        from PostToolUse_task_tracker import get_all_sessions_tasks

        # Create a state file
        state_path = self.state_dir / "session1_tasks.json"
        state_path.write_text('{"session_id": "session1", "tasks": {}}')

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Mock read_text to raise OSError
            original_read_text = Path.read_text
            def mock_read_error(self, *args, **kwargs):
                if "session1_tasks.json" in str(self):
                    raise OSError("[Errno 5] Input/output error")
                return original_read_text(self, *args, **kwargs)

            with patch.object(Path, "read_text", mock_read_error):
                # Capture stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()

                try:
                    # Execute
                    result = get_all_sessions_tasks()

                    # Verify error was logged (not silently continued)
                    stderr_output = sys.stderr.getvalue()

                    # THIS ASSERTION WILL FAIL until line 328-329 is fixed
                    assert len(stderr_output) > 0, (
                        "QUAL-003 VIOLATION: OSError was silently ignored (line 328-329: except (OSError, ValueError): continue). "
                        "Constitutional requirement: 'Fail fast ALWAYS. NO graceful degradation, NO error masking'. "
                        "Error MUST be logged to stderr for debugging."
                    )

                    # Verify error details are captured
                    assert any(term in stderr_output for term in ["Input/output error", "OSError", "5", "get_all_sessions_tasks"]), (
                        "QUAL-003 VIOLATION: Error logging must capture error details. "
                        "stderr should contain error message, error type, or error code."
                    )
                finally:
                    sys.stderr = old_stderr


class TestQual003IntegrationTests:
    """Integration tests for QUAL-003 error logging."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.TemporaryDirectory()
        self.state_dir = Path(self.temp_dir.name) / "state"
        self.state_dir.mkdir()

    def teardown_method(self):
        """Clean up test fixtures."""
        self.temp_dir.cleanup()

    def test_task_create_propagates_save_errors(self):
        """FAILING TEST: track_task_create should surface save errors.

        Given: OSError occurs during save_session_state within track_task_create
        When: track_task_create() is called
        Then: Error MUST be logged for debugging

        This is an integration test that verifies the error propagates through the call stack.
        """
        from PostToolUse_task_tracker import track_task_create

        tool_input = {
            "taskId": "test_1",
            "subject": "Test task",
            "description": "Test description",
            "status": "pending",
        }

        with patch.dict(os.environ, {"TASK_STATE_DIR": str(self.state_dir)}):
            # Mock write_text to fail
            with patch.object(Path, "write_text", side_effect=OSError("[Errno 30] Read-only file system")):
                # Capture stderr output
                old_stderr = sys.stderr
                sys.stderr = io.StringIO()

                try:
                    # Execute
                    result = track_task_create(tool_input, "test_session", "term_1")

                    # Verify error was logged through the call stack
                    stderr_output = sys.stderr.getvalue()

                    # THIS ASSERTION WILL FAIL until error logging is added
                    assert len(stderr_output) > 0, (
                        "QUAL-003 VIOLATION: OSError in track_task_create was silently ignored. "
                        "Error from save_session_state (line 198) must propagate and be logged."
                    )

                    # Verify error details are captured
                    assert "Read-only file system" in stderr_output or "OSError" in stderr_output or "30" in stderr_output, (
                        "QUAL-003 VIOLATION: Error logging must capture error details."
                    )
                finally:
                    sys.stderr = old_stderr
