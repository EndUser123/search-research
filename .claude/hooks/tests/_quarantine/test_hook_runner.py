#!/usr/bin/env python3
"""Tests for hook_runner.py - TDD RED Phase.

These tests verify the hook runner's error handling and logging behavior.
All tests should FAIL initially (RED phase) until implementation is complete.

Run with: pytest P:/.claude/hooks/tests/test_hook_runner.py -v
"""

import io
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add hooks directory to path for imports
hooks_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(hooks_dir))

from __lib.hook_runner import _log_error, _timeout_monitor, safe_run


class TestSafeRunImportErrors:
    """Test that ModuleNotFoundError is logged correctly."""

    def test_safe_run_logs_import_errors(self, tmp_path):
        """
        Test that ModuleNotFoundError is logged correctly.

        Given: A hook file that imports a non-existent module
        When: The hook is executed via safe_run
        Then: The error should be logged to cc_errors.jsonl with correct error type
        """
        # Arrange - Create a hook file with import error
        hook_file = tmp_path / "import_error_hook.py"
        hook_file.write_text("""
# This hook imports a non-existent module
import nonexistent_module_xyz

def main():
    print("This should never execute")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                exit_code = safe_run(hook_file)

        # Assert - Verify error was logged
        assert exit_code == 1, "safe_run should return 1 on import error"

        # Verify log file was created and contains error entry
        assert error_log.exists(), "Error log file should be created"

        # Read and verify log entry
        log_entries = []
        with open(error_log, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        assert len(log_entries) > 0, "Should have at least one log entry"

        # Find the import error entry
        import_error = None
        for entry in log_entries:
            if 'import_error_hook' in entry.get('error_type', ''):
                import_error = entry
                break

        assert import_error is not None, "Should find import_error in log entries"
        assert 'import_error' in import_error['error_type'], "Error type should indicate import error"
        assert 'Import error' in import_error['error_message'] or 'ModuleNotFoundError' in import_error['error_message'], \
            "Error message should mention import error"


class TestSafeRunSyntaxErrors:
    """Test that SyntaxError is logged correctly."""

    def test_safe_run_logs_syntax_errors(self, tmp_path):
        """
        Test that SyntaxError is logged correctly.

        Given: A hook file with invalid Python syntax
        When: The hook is executed via safe_run
        Then: The error should be logged to cc_errors.jsonl with syntax error type
        """
        # Arrange - Create a hook file with syntax error
        hook_file = tmp_path / "syntax_error_hook.py"
        hook_file.write_text("""
# This hook has a syntax error
def main(
    # Missing closing parenthesis - invalid syntax
    print("This should never execute")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                exit_code = safe_run(hook_file)

        # Assert - Verify error was logged
        assert exit_code == 1, "safe_run should return 1 on syntax error"

        # Verify log file was created and contains error entry
        assert error_log.exists(), "Error log file should be created"

        # Read and verify log entry
        log_entries = []
        with open(error_log, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        assert len(log_entries) > 0, "Should have at least one log entry"

        # Find the syntax error entry
        syntax_error = None
        for entry in log_entries:
            if 'syntax_error_hook' in entry.get('error_type', ''):
                syntax_error = entry
                break

        assert syntax_error is not None, "Should find syntax_error in log entries"
        assert 'syntax_error' in syntax_error['error_type'], "Error type should indicate syntax error"
        assert 'Syntax error' in syntax_error['error_message'], \
            "Error message should mention syntax error"


class TestSafeRunRuntimeErrors:
    """Test that generic Exception is logged correctly."""

    def test_safe_run_logs_runtime_errors(self, tmp_path):
        """
        Test that generic Exception is logged correctly.

        Given: A hook file that raises a runtime exception
        When: The hook is executed via safe_run
        Then: The error should be logged to cc_errors.jsonl with runtime error type
        """
        # Arrange - Create a hook file with runtime error
        hook_file = tmp_path / "runtime_error_hook.py"
        hook_file.write_text("""
# This hook raises a runtime exception
def main():
    raise ValueError("This is a test runtime error")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                exit_code = safe_run(hook_file)

        # Assert - Verify error was logged
        assert exit_code == 1, "safe_run should return 1 on runtime error"

        # Verify log file was created and contains error entry
        assert error_log.exists(), "Error log file should be created"

        # Read and verify log entry
        log_entries = []
        with open(error_log, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        assert len(log_entries) > 0, "Should have at least one log entry"

        # Find the runtime error entry
        runtime_error = None
        for entry in log_entries:
            if 'runtime_error_hook' in entry.get('error_type', ''):
                runtime_error = entry
                break

        assert runtime_error is not None, "Should find runtime_error in log entries"
        assert 'runtime_error' in runtime_error['error_type'], "Error type should indicate runtime error"
        assert 'Runtime error' in runtime_error['error_message'], \
            "Error message should mention runtime error"
        assert 'ValueError' in runtime_error['error_message'], \
            "Error message should include the exception type"


class TestSafeRunObservability:
    """Test structured stderr diagnostics include hook scope metadata."""

    def test_safe_run_logs_stderr_with_session_scope(self, tmp_path):
        hook_file = tmp_path / "stderr_hook.py"
        hook_file.write_text(
            """
import sys
sys.stderr.write("blocked for test\\n")
"""
        )

        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)

        payload = {
            "session_id": "session-123",
            "terminal_id": "console-abc",
            "prompt_id": "prompt-xyz",
            "tool_name": "Read",
            "cwd": "P:\\\\workspace",
            "tool_input": {"file_path": "P:\\\\file.txt"},
        }

        with patch("__lib.hook_runner.HOOKS_DIR", tmp_path):
            with patch.object(sys, "stdin", io.StringIO(json.dumps(payload))):
                exit_code = safe_run(hook_file)

        assert exit_code == 0

        stderr_log = log_dir / "hook_runner_stderr.jsonl"
        assert stderr_log.exists()

        entries = [
            json.loads(line)
            for line in stderr_log.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        assert entries
        entry = entries[-1]
        assert entry["hook"] == "stderr_hook"
        assert entry["session_id"] == "session-123"
        assert entry["terminal_id"] == "console-abc"
        assert entry["prompt_id"] == "prompt-xyz"
        assert entry["tool_name"] == "Read"
        assert entry["file_path"].replace("\\\\", "\\") == "P:\\file.txt"
        assert entry["event_kind"] == "stderr"


class TestSafeRunExitCodes:
    """Test exit code behavior."""

    def test_safe_run_returns_exit_code_1_on_error(self, tmp_path):
        """
        Test that safe_run returns 1 when hook fails.

        Given: A hook file that raises an exception
        When: The hook is executed via safe_run
        Then: safe_run should return exit code 1
        """
        # Arrange - Create a hook file that fails
        hook_file = tmp_path / "failing_hook.py"
        hook_file.write_text("""
def main():
    raise RuntimeError("Hook failed")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                exit_code = safe_run(hook_file)

        # Assert - Verify exit code
        assert exit_code == 1, f"Expected exit code 1, got {exit_code}"

    def test_safe_run_returns_exit_code_0_on_success(self, tmp_path):
        """
        Test that safe_run returns 0 when hook succeeds.

        Given: A hook file that executes successfully
        When: The hook is executed via safe_run
        Then: safe_run should return exit code 0
        """
        # Arrange - Create a successful hook file
        hook_file = tmp_path / "success_hook.py"
        hook_file.write_text("""
def main():
    print("Hook executed successfully")
    return 0

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                exit_code = safe_run(hook_file)

        # Assert - Verify exit code
        assert exit_code == 0, f"Expected exit code 0, got {exit_code}"


class TestTimeoutMonitor:
    """Test timeout monitoring behavior."""

    def test_timeout_monitor_logs_without_stderr_noise(self, tmp_path, capsys):
        """
        Test that timeout warning fires after specified duration.

        Given: A timeout duration of 0.6 seconds
        When: _timeout_monitor is called with a duration
        Then: It should log the warning without emitting stderr noise
        """
        # Arrange - Setup log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        hook_name = "test_hook"
        duration = 0.6  # 0.6 seconds

        # Act - Call timeout monitor
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                _timeout_monitor(hook_name, duration)

        captured = capsys.readouterr()
        assert captured.err == "", "Timeout monitor should not emit stderr noise"

        # Assert - Check that error was logged
        assert error_log.exists(), "Error log file should be created"

        # Read and verify log entry
        log_entries = []
        with open(error_log, encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    log_entries.append(json.loads(line))

        assert len(log_entries) > 0, "Should have at least one log entry"

        # Find the timeout warning entry
        timeout_warning = None
        for entry in log_entries:
            if 'timeout_imminent' in entry.get('error_type', ''):
                timeout_warning = entry
                break

        assert timeout_warning is not None, "Should find timeout_imminent in log entries"
        assert 'test_hook' in timeout_warning['error_type'], \
            "Error type should include hook name"
        assert 'timeout' in timeout_warning['error_message'].lower(), \
            "Error message should mention timeout"


class TestSafeRunWithTimeout:
    """Test safe_run with timeout parameter."""

    def test_safe_run_with_timeout_starts_monitor(self, tmp_path):
        """
        Test that safe_run with timeout parameter starts timeout monitor.

        Given: A timeout value of 1.5 seconds
        When: safe_run is called with timeout parameter
        Then: A timer should be started for timeout monitoring
        """
        # Arrange - Create a hook that completes quickly
        hook_file = tmp_path / "quick_hook.py"
        hook_file.write_text("""
def main():
    print("Quick execution")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook with timeout
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                # Mock threading.Timer to verify it's called
                with patch('threading.Timer') as mock_timer:
                    mock_timer_instance = MagicMock()
                    mock_timer.return_value = mock_timer_instance

                    exit_code = safe_run(hook_file, timeout=1.5)

        # Assert - Verify timer was created and started
        assert mock_timer.called, "Threading.Timer should be called"
        assert mock_timer_instance.start.called, "Timer should be started"
        assert mock_timer_instance.cancel.called, "Timer should be cancelled after completion"

        # Verify the timer was created with correct duration (timeout - 0.5)
        call_args = mock_timer.call_args
        timer_duration = call_args[0][0]  # First positional argument
        expected_duration = 1.5 - 0.5  # timeout - 0.5 as per implementation
        assert abs(timer_duration - expected_duration) < 0.01, \
            f"Timer duration should be {expected_duration}, got {timer_duration}"

    def test_safe_run_without_timeout_no_monitor(self, tmp_path):
        """
        Test that safe_run without timeout doesn't start monitor.

        Given: No timeout parameter
        When: safe_run is called without timeout
        Then: No timer should be started
        """
        # Arrange - Create a hook
        hook_file = tmp_path / "no_timeout_hook.py"
        hook_file.write_text("""
def main():
    print("No timeout")

if __name__ == "__main__":
    main()
""")

        # Create temp log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        # Act - Run the hook without timeout
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                with patch('threading.Timer') as mock_timer:
                    exit_code = safe_run(hook_file)

        # Assert - Verify timer was NOT created
        assert not mock_timer.called, "Threading.Timer should not be called when no timeout specified"


class TestLogError:
    """Test _log_error function."""

    def test_log_error_creates_log_entry(self, tmp_path):
        """
        Test that _log_error creates a proper log entry.

        Given: Error information (hook name, error type, message, traceback)
        When: _log_error is called
        Then: A proper JSON log entry should be created
        """
        # Arrange - Setup log directory
        log_dir = tmp_path / "logs" / "diagnostics"
        log_dir.mkdir(parents=True)
        error_log = log_dir / "cc_errors.jsonl"

        hook_name = "test_hook"
        error_type = "test_error"
        error_msg = "Test error message"
        tb = "Test traceback"

        # Act - Log the error
        with patch('__lib.hook_runner.LOGS_DIR', log_dir):
            with patch('__lib.hook_runner.ERRORS_LOG', error_log):
                _log_error(hook_name, error_type, error_msg, tb)

        # Assert - Verify log file was created
        assert error_log.exists(), "Error log file should be created"

        # Read and verify log entry
        with open(error_log, encoding='utf-8') as f:
            log_content = f.read()

        assert len(log_content) > 0, "Log file should have content"

        # Parse JSON log entry
        log_entry = json.loads(log_content.strip())

        # Verify required fields
        assert 'timestamp' in log_entry, "Log entry should have timestamp"
        assert 'event' in log_entry, "Log entry should have event"
        assert log_entry['event'] == 'error', "Event should be 'error'"
        assert 'error_type' in log_entry, "Log entry should have error_type"
        assert hook_name in log_entry['error_type'], "Error type should include hook name"
        assert 'error_message' in log_entry, "Log entry should have error_message"
        assert log_entry['error_message'] == error_msg, "Error message should match"
        assert 'stack_trace' in log_entry, "Log entry should have stack_trace"
        assert log_entry['stack_trace'] == tb, "Stack trace should match"
        assert 'context' in log_entry, "Log entry should have context"
        assert log_entry['context']['hook'] == hook_name, "Context should include hook name"
        assert log_entry['context']['error_category'] == error_type, "Context should include error category"
        assert log_entry['context']['runner'] == 'hook_runner', "Context should include runner name"
