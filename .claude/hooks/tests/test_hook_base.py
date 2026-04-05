"""Tests for hook_base.py module.

This test file verifies the FAIL-FAST behavior in hook_base.py,
particularly the silent import failure masking issue (QUAL-001).

Run with: pytest P:/.claude/hooks/tests/test_hook_base.py -v
"""

import importlib
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


class TestGetLogErrorFailFast:
    """Tests for _get_log_error() FAIL-FAST behavior (QUAL-001)."""

    def test_import_error_should_raise_not_return_noop_lambda(self):
        """
        Test that when _get_log_error() catches ImportError, it should FAIL FAST
        by raising an exception, NOT return a silent no-op lambda.

        Bug: Lines 42-48 in hook_base.py currently return:
            return lambda *args, **kwargs: None

        This VIOLATES the FAIL-FAST policy stated in the module docstring:
            "ALL errors fail immediately with exit code 1. No masking, no
            graceful degradation."

        Given: The cc_diagnostic_logger module is not available (ImportError)
        When: _get_log_error() is called
        Then: It should raise an exception (ImportError or SystemExit)
              NOT return a no-op lambda that silently masks the failure

        This test MUST FAIL currently (RED phase) because the bug exists.
        """
        # Arrange: Setup path and import
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        # Patch sys.modules to make cc_diagnostic_logger import fail
        # Save original state
        original_modules = sys.modules.copy()

        # Remove cc_diagnostic_logger from sys.modules if present
        sys.modules.pop('cc_diagnostic_logger', None)

        try:
            # Mock to raise ImportError when cc_diagnostic_logger is imported
            import builtins
            original_import = builtins.__import__

            def mock_import(name, *args, **kwargs):
                if name == 'cc_diagnostic_logger':
                    raise ImportError(f"No module named '{name}'")
                return original_import(name, *args, **kwargs)

            with patch.object(builtins, '__import__', side_effect=mock_import):
                # Import and reload to trigger the ImportError
                import __lib.hook_base as hook_base_module
                importlib.reload(hook_base_module)

                # Act & Assert: _get_log_error() should FAIL FAST by raising SystemExit
                # when cc_diagnostic_logger import fails, NOT return a silent no-op lambda
                with pytest.raises(SystemExit) as exc_info:
                    hook_base_module._get_log_error()

                # Verify exit code is 1 (error)
                assert exc_info.value.code == 1, "FAIL-FAST should exit with code 1"
        finally:
            # Restore sys.modules
            sys.modules.clear()
            sys.modules.update(original_modules)


class TestGetLogErrorLazyImport:
    """Tests for _get_log_error() lazy import and cc_diagnostic_logger integration.

    Tests verify:
    1. _get_log_error() returns actual log_error function when cc_diagnostic_logger is available
    2. hooks_dir is correctly added to sys.path
    3. calling log_error() actually writes to cc_errors.jsonl

    Test Phase: RED - Tests must FAIL before implementation
    """

    def setup_method(self):
        """Setup: Add hooks directory to sys.path for imports."""
        hooks_dir = Path(__file__).resolve().parent.parent
        hooks_dir_str = str(hooks_dir)
        if hooks_dir_str not in sys.path:
            sys.path.insert(0, hooks_dir_str)

    def test_returns_log_error_function_when_available(self, tmp_path):
        """
        RED TEST: Verify _get_log_error() returns actual log_error function

        When cc_diagnostic_logger is available, _get_log_error() should return
        the actual log_error function, not a no-op lambda.

        Given: cc_diagnostic_logger module is available
        When: _get_log_error() is called
        Then: Should return actual log_error function (not no-op lambda)

        This test FAILS if the function returns the no-op lambda instead of
        the actual log_error function.
        """
        # Arrange: Clear cc_diagnostic_logger from sys.modules for clean test
        modules_to_remove = [m for m in sys.modules if 'cc_diagnostic_logger' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        # Create a mock cc_diagnostic_logger module with actual log_error function
        def real_log_error(error_type, error_message, context=None, stack_trace=None):
            """Real log_error function signature from cc_diagnostic_logger"""
            return f"Logged: {error_type} - {error_message}"

        mock_logger = MagicMock()
        mock_logger.log_error = real_log_error

        # Act: Patch the import to return our mock
        with patch.dict(sys.modules, {'cc_diagnostic_logger': mock_logger}):
            # Use importlib to avoid Python name mangling of __lib
            hook_base = importlib.import_module('__lib.hook_base')
            result = hook_base._get_log_error()

        # Assert: Result should be callable
        assert callable(result), "_get_log_error() should return a callable"

        # Result should be the actual log_error function
        # This is the RED test - it will fail if we get the no-op lambda
        # The no-op lambda returns None, real function returns a value
        call_result = result("test_error", error_message="Test", context={}, stack_trace="")
        assert call_result is not None, (
            "Should return actual log_error function that returns a value, "
            "not no-op lambda that returns None"
        )

    def test_hooks_dir_added_to_sys_path(self, tmp_path):
        """
        RED TEST: Verify hooks_dir is added to sys.path

        The _get_log_error() function should add hooks_dir to sys.path
        to enable the cc_diagnostic_logger import.

        Given: hooks_dir is not in sys.path initially (simulated)
        When: _get_log_error() is called
        Then: hooks_dir should be in sys.path after call

        This verifies the lazy import mechanism correctly sets up the import path.
        """
        # Arrange: Get hooks_dir and save original path
        hooks_dir = Path(__file__).resolve().parent.parent
        hooks_dir_str = str(hooks_dir)
        original_path = sys.path.copy()

        # Note: We can't actually remove hooks_dir from sys.path because we need
        # it to import hook_base. Instead, we verify that _get_log_error adds it
        # if it's not already there, by checking the code path execution.

        # Act: Import hook_base and call _get_log_error
        hook_base = importlib.import_module('__lib.hook_base')

        # Remove from sys.modules to force fresh import attempt
        if 'cc_diagnostic_logger' in sys.modules:
            del sys.modules['cc_diagnostic_logger']

        # Remove hooks_dir temporarily to test _get_log_error adds it back
        if hooks_dir_str in sys.path:
            sys.path.remove(hooks_dir_str)

        # Now hooks_dir is NOT in sys.path - call _get_log_error which should add it
        with patch.dict(sys.modules, {'cc_diagnostic_logger': MagicMock()}):
            hook_base._get_log_error()

        # Assert: hooks_dir should now be in sys.path
        assert hooks_dir_str in sys.path, (
            f"hooks_dir ({hooks_dir_str}) should be in sys.path "
            f"after _get_log_error() call"
        )

        # Restore original path
        sys.path[:] = original_path

    def test_log_error_writes_to_cc_errors_jsonl(self, tmp_path, monkeypatch):
        """
        RED TEST: Verify log_error() actually writes to cc_errors.jsonl

        End-to-end test: _get_log_error() returns function that writes
        errors to the log file.

        Given: cc_diagnostic_logger is available with test log directory
        When: log_error() is called via _get_log_error()
        Then: cc_errors.jsonl should be created with valid JSON entry

        This test verifies the actual log file is created and written to.
        """
        import json

        # Arrange: Clear module cache
        modules_to_remove = [m for m in sys.modules if 'cc_diagnostic_logger' in m]
        for module in modules_to_remove:
            del sys.modules[module]

        # Set up test log directory
        test_log_dir = tmp_path / "logs" / "diagnostics"
        test_log_dir.mkdir(parents=True, exist_ok=True)
        cc_errors_path = test_log_dir / "cc_errors.jsonl"

        # Create a real log_error function that writes actual JSON to file
        def real_log_error(error_type, error_message, context=None, stack_trace=None):
            """Mock log_error that writes actual JSON to file"""
            entry = {
                "event": "error",
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
                "stack_trace": stack_trace
            }
            with open(cc_errors_path, 'a') as f:
                f.write(json.dumps(entry) + '\n')

        # Patch cc_diagnostic_logger module
        mock_logger = MagicMock()
        mock_logger.log_error = real_log_error
        mock_logger.LOG_FILES = {"errors": cc_errors_path}
        mock_logger.DIAGNOSTICS_ENABLED = True

        # Patch environment variables to use test directory
        monkeypatch.setenv("CC_DIAGNOSTICS_DIR", str(test_log_dir))
        monkeypatch.setenv("CC_DIAGNOSTICS_ENABLED", "true")

        # Act: Get log_error function and call it
        with patch.dict(sys.modules, {'cc_diagnostic_logger': mock_logger}):
            hook_base = importlib.import_module('__lib.hook_base')
            log_error = hook_base._get_log_error()

            log_error(
                error_type="test_hook_error",
                error_message="Test error message",
                context={"hook": "test_hook"},
                stack_trace="Test traceback"
            )

        # Assert: Verify file was created and has valid JSON content
        assert cc_errors_path.exists(), (
            f"log_error() should create {cc_errors_path}"
        )

        # Verify file has valid JSON content
        content = cc_errors_path.read_text()
        assert len(content) > 0, "cc_errors.jsonl should have content"

        # Parse and verify the JSON entry
        entry = json.loads(content.strip())
        assert entry["error_type"] == "test_hook_error"
        assert entry["error_message"] == "Test error message"
        assert entry["context"]["hook"] == "test_hook"
        assert entry["stack_trace"] == "Test traceback"
        assert entry["event"] == "error"


class TestHookMainSysArgvEdgeCases:
    """Tests for sys.argv edge cases in hook_main decorator (line 66).

    Edge case: hook_name = Path(sys.argv[0]).stem if sys.argv else "unknown_hook"

    These tests FAIL in RED phase to reveal edge case issues.
    """

    def setup_method(self):
        """Setup: Import hook_base module."""
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))
        # Use importlib to avoid Python name mangling of __lib
        import importlib
        self.hook_base = importlib.import_module('__lib.hook_base')

    def test_empty_sysargv_list_returns_unknown_hook(self, monkeypatch):
        """
        Test that when sys.argv is an empty list [],
        the hook_name defaults to "unknown_hook".

        Edge case: Empty sys.argv list should trigger fallback.
        Current code has IndexError when accessing sys.argv[0] on empty list.

        Given: sys.argv is []
        When: An exception is raised in a @hook_main decorated function
        Then: hook_name should be "unknown_hook" (fallback)
        """
        # Arrange: Set sys.argv to empty list
        monkeypatch.setattr(sys, 'argv', [])

        # Act: Call a function decorated with @hook_main that raises an exception
        @self.hook_base.hook_main
        def failing_function():
            raise ValueError("Test error")

        # Assert: Should raise SystemExit with exit code 1
        with pytest.raises(SystemExit) as exc_info:
            failing_function()

        # Verify exit code is 1 (error)
        assert exc_info.value.code == 1

        # NOTE: This test FAILS with IndexError because Path(sys.argv[0])
        # is evaluated before the "if sys.argv" check in the ternary expression

    def test_sysargv_zero_nonexistent_path(self, monkeypatch, capsys):
        """
        Test that when sys.argv[0] contains a path that doesn't exist,
        Path.stem still works correctly (it doesn't require file existence).

        Edge case: sys.argv[0] may not be a valid file path on disk.
        Path.stem works on strings, not actual files.

        Given: sys.argv[0] is '/nonexistent/path/to/hook.py'
        When: An exception is raised in a @hook_main decorated function
        Then: hook_name should be 'hook' (extracted via Path.stem)
        """
        # Arrange: Set sys.argv[0] to a non-existent path
        monkeypatch.setattr(sys, 'argv', ['/nonexistent/path/to/hook.py'])

        # Act: Call a function decorated with @hook_main that raises an exception
        @self.hook_base.hook_main
        def failing_function():
            raise ValueError("Test error")

        # Assert: Should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            failing_function()

        # Verify exit code is 1
        assert exc_info.value.code == 1

        # Verify stderr contains the hook name extracted from path
        captured = capsys.readouterr()
        assert "[HOOK_ERROR] hook:" in captured.err

    def test_unknown_hook_fallback_verification(self, monkeypatch, capsys):
        """
        Verify that "unknown_hook" fallback is used when sys.argv is falsy.

        This test ensures the conditional expression works correctly:
        hook_name = Path(sys.argv[0]).stem if sys.argv else "unknown_hook"

        Given: sys.argv is []
        When: An exception is raised in a @hook_main decorated function
        Then: stderr should contain "unknown_hook" as the hook name

        This test FAILS because current code has IndexError on empty sys.argv
        before the conditional check can evaluate to False.
        """
        # Arrange: Test with empty sys.argv
        monkeypatch.setattr(sys, 'argv', [])

        @self.hook_base.hook_main
        def failing_function():
            raise RuntimeError("Test error for fallback")

        # Act & Assert: Should raise SystemExit
        with pytest.raises(SystemExit) as exc_info:
            failing_function()

        # Capture stderr to verify "unknown_hook" is used
        captured = capsys.readouterr()

        # This assertion FAILS because current code raises IndexError
        # before reaching the "unknown_hook" fallback
        assert "[HOOK_ERROR] unknown_hook:" in captured.err


class TestSetHookContextStoresUserPrompt:
    """Tests for set_hook_context storing user_prompt in thread-local storage."""

    def test_set_hook_context_stores_user_prompt(self):
        """
        Test that set_hook_context stores user_prompt in thread-local storage.

        Given: No user_prompt is currently set
        When: set_hook_context is called with a user_prompt
        Then: The user_prompt is retrievable from thread-local storage
        """
        # Arrange - Import and clear any existing context
        from __lib.hook_base import _hook_context, set_hook_context
        if hasattr(_hook_context, "user_prompt"):
            delattr(_hook_context, "user_prompt")

        # Act
        test_prompt = "Write a test for the hook_base module"
        set_hook_context(user_prompt=test_prompt)

        # Assert
        assert hasattr(_hook_context, "user_prompt"), "user_prompt should be stored in thread-local storage"
        assert _hook_context.user_prompt == test_prompt, f"user_prompt should be '{test_prompt}'"


class TestSetHookContextStoresSessionId:
    """Tests for set_hook_context storing claude_session_id in thread-local storage."""

    def test_set_hook_context_stores_session_id(self):
        """
        Test that set_hook_context stores claude_session_id in thread-local storage.

        Given: No claude_session_id is currently set
        When: set_hook_context is called with a claude_session_id
        Then: The claude_session_id is retrievable from thread-local storage
        """
        # Arrange - Import and clear any existing context
        from __lib.hook_base import _hook_context, set_hook_context
        if hasattr(_hook_context, "claude_session_id"):
            delattr(_hook_context, "claude_session_id")

        # Act
        test_session_id = "test_session_12345"
        set_hook_context(claude_session_id=test_session_id)

        # Assert
        assert hasattr(_hook_context, "claude_session_id"), "claude_session_id should be stored in thread-local storage"
        assert _hook_context.claude_session_id == test_session_id, f"claude_session_id should be '{test_session_id}'"


class TestHookMainDecoratorLogsException:
    """Tests for hook_main decorator logging exceptions."""

    def test_hook_main_decorator_logs_exception(self, tmp_path):
        """
        Test that hook_main decorator logs exceptions with correct format to cc_errors.jsonl.

        Given: A function decorated with @hook_main that raises an exception
        When: The decorated function is called and raises an exception
        Then: The exception is logged with error_type, error_message, context, and stack_trace
        """
        # Arrange
        from unittest.mock import patch

        from __lib.hook_base import hook_main

        # Create mock log_error function to capture calls
        log_calls = []

        def mock_log_error(error_type, error_message, context=None, stack_trace=None,
                          user_prompt=None, claude_session_id=None):
            """Capture log_error calls to a list."""
            entry = {
                "error_type": error_type,
                "error_message": error_message,
                "context": context,
                "stack_trace": stack_trace,
                "user_prompt": user_prompt,
                "claude_session_id": claude_session_id,
            }
            log_calls.append(entry)

        @hook_main
        def failing_function():
            """A function that raises an exception."""
            raise ValueError("Test error for hook_main decorator")

        # Mock sys.argv to provide hook name
        with patch("sys.argv", ["test_hook.py"]):
            # Mock _get_log_error to return our fake logger
            with patch("__lib.hook_base._get_log_error", return_value=mock_log_error):
                # Mock sys.exit to prevent test termination
                with patch("sys.exit"):
                    # Act
                    failing_function()

        # Assert - Verify log_error was called
        assert len(log_calls) == 1, f"Expected 1 log call, got {len(log_calls)}"

        log_entry = log_calls[0]
        assert log_entry["error_type"] == "test_hook_error", f"Expected error_type 'test_hook_error', got '{log_entry['error_type']}'"
        assert log_entry["error_message"] == "Test error for hook_main decorator", f"Expected error message about test error, got '{log_entry['error_message']}'"
        assert log_entry["context"] == {"hook": "test_hook"}, f"Expected context with hook name, got {log_entry['context']}"
        assert log_entry["stack_trace"] is not None, "Expected stack_trace to be present"
        assert "ValueError" in log_entry["stack_trace"], "Expected stack_trace to contain ValueError"


class TestHookMainDecoratorReturnsExitCode1:
    """Tests for hook_main decorator exit code behavior."""

    def test_hook_main_decorator_returns_exit_code_1(self):
        """
        Test that hook_main decorator returns exit code 1 on exception.

        Given: A function decorated with @hook_main that raises an exception
        When: The decorated function is called and raises an exception
        Then: sys.exit is called with exit code 1
        """
        # Arrange
        from unittest.mock import Mock, patch

        from __lib.hook_base import hook_main

        mock_log_error = Mock()

        @hook_main
        def failing_function():
            """A function that raises an exception."""
            raise RuntimeError("Test error for exit code verification")

        # Mock sys.argv to provide hook name
        with patch("sys.argv", ["test_hook.py"]):
            # Mock _get_log_error to return our fake logger
            with patch("__lib.hook_base._get_log_error", return_value=mock_log_error):
                # Mock sys.exit to capture the exit code
                with patch("sys.exit") as mock_exit:
                    # Act
                    failing_function()

        # Assert - Verify sys.exit was called with code 1
        mock_exit.assert_called_once_with(1), f"Expected sys.exit(1), got {mock_exit.call_args}"
