"""Tests for PostToolUse logging behavior.

RED PHASE: Tests will FAIL because current implementation writes to stderr.
After fix: Tests will pass when logger.debug() with NullHandler is used.
"""

import json
import sys
from io import StringIO
from pathlib import Path

# Add hooks directory to path for imports (E402 exemption - must be before import)
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

import PostToolUse  # noqa: E402


class TestPostToolUseLoggingFix:
    """Test suite for PostToolUse logging fix - replacing stderr with logger.debug()."""

    def test_happy_path_no_exception_no_stderr(self, tmp_path):
        """
        Test that successful operations (no exception) produce no stderr output.

        Given: A successful tool event (no exception in logging/signal)
        When: PostToolUse processes the event
        Then: No stderr output should be produced
        """
        # Arrange: Create minimal successful event data
        event_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.txt"},
            "tool_result": "file content",
            "session_id": "test-session-123",
            "terminal_id": "test-terminal",
        }

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            # Act: Process the event
            input_json = json.dumps(event_data)

            # Simulate stdin
            old_stdin = sys.stdin
            sys.stdin = StringIO(input_json)

            # Execute main
            PostToolUse.main()

        except SystemExit:
            # main() calls sys.exit(0), catch and continue
            pass
        finally:
            sys.stdin = old_stdin
            stderr_output = sys.stderr.getvalue()
            sys.stderr = old_stderr

        # Assert: No stderr output should be produced
        assert "PostToolUse Logging Error" not in stderr_output
        assert stderr_output == "" or stderr_output.strip() == "{}"

    def test_exception_path_logging_failure_silent(self, tmp_path, monkeypatch):
        """
        Test that evidence logging failures are silent (no stderr).

        Given: append_tool_event raises an exception
        When: PostToolUse processes the event
        Then: Exception should be caught silently with no stderr output
        """
        # Arrange: Mock append_tool_event to raise exception
        def mock_append_event(*_args, **_kwargs):
            raise RuntimeError("Evidence store failure")

        monkeypatch.setattr(PostToolUse, "append_tool_event", mock_append_event)

        event_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.txt"},
            "tool_result": "file content",
            "session_id": "test-session-123",
            "terminal_id": "test-terminal",
        }

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            # Act: Process the event with failing evidence logging
            input_json = json.dumps(event_data)
            old_stdin = sys.stdin
            sys.stdin = StringIO(input_json)

            # Execute main
            PostToolUse.main()

        except SystemExit:
            pass
        finally:
            sys.stdin = old_stdin
            stderr_output = sys.stderr.getvalue()
            sys.stderr = old_stderr

        # Assert: Should NOT write to stderr (after fix)
        # Current implementation WILL write to stderr (expected failure before fix)
        assert "PostToolUse Logging Error" not in stderr_output

    def test_exception_path_signal_file_failure_silent(self, tmp_path, monkeypatch):
        """
        Test that signal file creation failures are silent (no stderr).

        Given: Signal file creation raises an OSError
        When: PostToolUse processes an error event
        Then: Exception should be caught silently with no stderr output
        """
        # Arrange: Create event that will trigger signal file creation
        event_data = {
            "tool_name": "Bash",
            "tool_input": {"command": "false"},
            "tool_result": "exit code 1",  # Error, triggers signal file
            "session_id": "test-session-123",
            "terminal_id": "test-terminal",
        }

        # Capture stderr
        old_stderr = sys.stderr
        sys.stderr = StringIO()

        try:
            # Act: Process the event
            input_json = json.dumps(event_data)
            old_stdin = sys.stdin
            sys.stdin = StringIO(input_json)

            # Execute main
            PostToolUse.main()

        except SystemExit:
            pass
        finally:
            sys.stdin = old_stdin
            stderr_output = sys.stderr.getvalue()
            sys.stderr = old_stderr

        # Assert: Should NOT write to stderr (after fix)
        assert "PostToolUse Logging Error" not in stderr_output

    def test_regression_evidence_logging_works(self, tmp_path, monkeypatch):
        """
        Regression test: Evidence logging still works when no exception.

        Given: A successful tool event
        When: PostToolUse processes the event
        Then: append_tool_event should be called with correct parameters
        """
        # Arrange: Track calls to append_tool_event
        calls = []

        def mock_append_event(*_args, **kwargs):
            calls.append(kwargs)

        monkeypatch.setattr(PostToolUse, "append_tool_event", mock_append_event)

        event_data = {
            "tool_name": "Read",
            "tool_input": {"file_path": "test.txt"},
            "tool_result": "file content",
            "session_id": "test-session-123",
            "terminal_id": "test-terminal",
        }

        # Act: Process the event
        input_json = json.dumps(event_data)
        old_stdin = sys.stdin
        sys.stdin = StringIO(input_json)

        try:
            PostToolUse.main()
        except SystemExit:
            pass
        finally:
            sys.stdin = old_stdin

        # Assert: append_tool_event was called
        assert len(calls) == 1
        assert calls[0]["session_id"] == "test-session-123"
        assert calls[0]["tool_name"] == "Read"
        assert calls[0]["success"] is True
