#!/usr/bin/env python3
"""Tests for UPS execution trace logging in registry.py.

Tests cover:
- stdout capture and logging
- stderr capture and logging
- Both stdout and stderr captured
- Empty capture (no logging)
- Log entry structure validation
- Integration with actual hook execution
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

# Add hooks to path
HOOKS_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(HOOKS_DIR))

from UserPromptSubmit_modules.base import HookContext, HookResult
from UserPromptSubmit_modules.registry import _log_execution_trace


@pytest.fixture
def temp_log_file(tmp_path: Path) -> Path:
    """Create a temporary log file for testing."""
    return tmp_path / "test_execution_trace.jsonl"


@pytest.fixture
def sample_context() -> HookContext:
    """Create a sample HookContext for testing."""
    return HookContext(
        prompt="test prompt",
        data={"test": "data"},
        session_id="test-session-123",
        terminal_id="test-terminal-abc",
    )


@pytest.fixture
def sample_result() -> HookResult:
    """Create a sample HookResult for testing."""
    return HookResult(context="test context", tokens=50)


class TestExecutionTraceStdoutCapture:
    """Test stdout capture and logging."""

    def test_stdout_only_is_logged(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that stdout capture is logged when non-empty."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="Test stdout output",
            stderr_captured="",
        )

        # Assert
        assert temp_log_file.exists()
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert log_entry["hook_name"] == "test_hook"
        assert log_entry["session_id"] == "test-session-123"
        assert log_entry["terminal_id"] == "test-terminal-abc"
        assert "stdout" in log_entry
        assert log_entry["stdout"] == "Test stdout output"

    def test_empty_stdout_not_logged(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that empty stdout is not logged."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="",
            stderr_captured="",
        )

        # Assert
        assert temp_log_file.exists()
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stdout" not in log_entry
        assert "stderr" not in log_entry

    def test_long_stdout_is_truncated(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that long stdout is truncated to 1000 characters."""
        # Create long stdout (2000 chars)
        long_stdout = "x" * 2000

        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured=long_stdout,
            stderr_captured="",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stdout" in log_entry
        assert len(log_entry["stdout"]) == 1000
        assert log_entry["stdout"].endswith("... (truncated)")


class TestExecutionTraceStderrCapture:
    """Test stderr capture and logging."""

    def test_stderr_only_is_logged(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that stderr capture is logged when non-empty."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="",
            stderr_captured="Test stderr output",
        )

        # Assert
        assert temp_log_file.exists()
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stderr" in log_entry
        assert log_entry["stderr"] == "Test stderr output"

    def test_empty_stderr_not_logged(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that empty stderr is not logged."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="",
            stderr_captured="",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stderr" not in log_entry

    def test_long_stderr_is_truncated(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that long stderr is truncated to 1000 characters."""
        # Create long stderr (2000 chars)
        long_stderr = "y" * 2000

        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="",
            stderr_captured=long_stderr,
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stderr" in log_entry
        assert len(log_entry["stderr"]) == 1000
        assert log_entry["stderr"].endswith("... (truncated)")


class TestExecutionTraceBothCapture:
    """Test both stdout and stderr captured together."""

    def test_both_stdout_and_stderr_logged(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that both stdout and stderr are logged when non-empty."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            stdout_captured="stdout message",
            stderr_captured="stderr message",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stdout" in log_entry
        assert "stderr" in log_entry
        assert log_entry["stdout"] == "stdout message"
        assert log_entry["stderr"] == "stderr message"


class TestExecutionTraceStructure:
    """Test log entry structure validation."""

    def test_log_entry_has_required_fields(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that log entry has all required fields."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="structure_test",
            context=sample_context,
            result=sample_result,
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        # Required fields
        assert "ts" in log_entry
        assert "session_id" in log_entry
        assert "terminal_id" in log_entry
        assert "hook_name" in log_entry
        assert "result" in log_entry

        # Result structure
        result = log_entry["result"]
        assert "is_empty" in result
        assert "has_context" in result
        assert "tokens_added" in result

    def test_log_entry_with_duration(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that duration_ms is logged when provided."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            duration_ms=15.5,
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "duration_ms" in log_entry
        assert log_entry["duration_ms"] == 15.5

    def test_log_entry_without_duration(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that duration_ms is omitted when not provided."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            duration_ms=None,
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "duration_ms" not in log_entry

    def test_log_entry_with_transcript(self, temp_log_file: Path, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that transcript_path is logged when provided."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=sample_context,
            result=sample_result,
            transcript_path="/path/to/transcript-claude-sonnet-4-6.jsonl",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "transcript_path" in log_entry
        assert log_entry["transcript_path"] == "/path/to/transcript-claude-sonnet-4-6.jsonl"
        assert "model_name" in log_entry
        assert log_entry["model_name"] == "claude-sonnet-4-6"


class TestExecutionTraceFailurePath:
    """Test execution trace logging for failed hooks."""

    def test_failed_hook_logs_none_result(self, temp_log_file: Path, sample_context: HookContext) -> None:
        """Test that failed hooks log result=None."""
        # Act
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="failed_hook",
            context=sample_context,
            result=None,  # Hook failed
            stdout_captured="error output",
            stderr_captured="error trace",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert log_entry["hook_name"] == "failed_hook"
        assert log_entry["result"]["is_empty"] is True
        assert log_entry["result"]["has_context"] is False
        assert log_entry["result"]["tokens_added"] == 0
        assert "stdout" in log_entry
        assert "stderr" in log_entry


class TestExecutionTraceGracefulDegradation:
    """Test graceful degradation when logging fails."""

    def test_logging_failure_does_not_raise(self, sample_context: HookContext, sample_result: HookResult) -> None:
        """Test that logging to invalid path does not raise exception."""
        # Use invalid path (e.g., root directory without write permission)
        # On Windows, CON: is invalid; on Unix, /dev/null is valid but /root/ might not be writable
        invalid_path = Path("CON:/invalid.jsonl") if sys.platform == "win32" else Path("/root/no-permission.jsonl")

        # Act & Assert - should not raise
        try:
            _log_execution_trace(
                log_file=invalid_path,
                hook_name="test_hook",
                context=sample_context,
                result=sample_result,
            )
            # If we get here, graceful degradation worked
            assert True
        except Exception:
            pytest.fail("Logging failure should be silently caught, not propagated")


class TestExecutionTraceIntegration:
    """Integration tests with actual hook execution."""

    def test_hook_with_stdout_write(self, temp_log_file: Path) -> None:
        """Test that actual hook stdout is captured and logged."""
        # Create a test hook that writes to stdout
        def test_hook(context: HookContext) -> HookResult:
            print("Hook stdout message")
            return HookResult.empty()

        # Simulate hook execution with capture
        import io

        context = HookContext(
            prompt="test",
            data={},
            session_id="integration-test",
            terminal_id="terminal-1",
        )

        stdout_capture = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = stdout_capture

        try:
            result = test_hook(context)
        finally:
            sys.stdout = old_stdout

        stdout_captured = stdout_capture.getvalue()

        # Log the execution
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
            stdout_captured=stdout_captured,
            stderr_captured="",
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert log_entry["hook_name"] == "test_hook"
        assert "stdout" in log_entry
        assert log_entry["stdout"] == "Hook stdout message\n"

    def test_hook_with_stderr_write(self, temp_log_file: Path) -> None:
        """Test that actual hook stderr is captured and logged."""
        # Create a test hook that writes to stderr
        def test_hook(context: HookContext) -> HookResult:
            import sys
            print("Hook stderr message", file=sys.stderr)
            return HookResult.empty()

        # Simulate hook execution with capture
        import io

        context = HookContext(
            prompt="test",
            data={},
            session_id="integration-test",
            terminal_id="terminal-1",
        )

        stderr_capture = io.StringIO()
        old_stderr = sys.stderr
        sys.stderr = stderr_capture

        try:
            result = test_hook(context)
        finally:
            sys.stderr = old_stderr

        stderr_captured = stderr_capture.getvalue()

        # Log the execution
        _log_execution_trace(
            log_file=temp_log_file,
            hook_name="test_hook",
            context=context,
            result=result,
            stdout_captured="",
            stderr_captured=stderr_captured,
        )

        # Assert
        with open(temp_log_file) as f:
            log_entry = json.loads(f.readline())

        assert "stderr" in log_entry
        assert log_entry["stderr"] == "Hook stderr message\n"
