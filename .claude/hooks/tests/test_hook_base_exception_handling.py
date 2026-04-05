"""Tests for hook_main decorator exception handling behavior.

These tests verify the exception handling behavior of the hook_main decorator
in hook_base.py (lines 51-84).

Run with: pytest P:/.claude/hooks/tests/test_hook_base_exception_handling.py -v
"""

import sys
from pathlib import Path

import pytest


class TestHookMainExceptionHandling:
    """Tests for hook_main decorator exception handling behavior."""

    def test_hook_main_raises_system_exit_on_exception(self, capsys):
        """
        Test that decorated function raises SystemExit with code 1 when exception occurs.

        Given: A function decorated with @hook_main that raises an exception
        When: The decorated function is called
        Then: SystemExit with code 1 should be raised
        """
        # Arrange: Import hook_main decorator
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from __lib.hook_base import hook_main

        # Create a test function that raises an exception
        @hook_main
        def failing_function():
            raise ValueError("Test error message")

        # Act & Assert: Should raise SystemExit with code 1
        with pytest.raises(SystemExit) as exc_info:
            failing_function()

        assert exc_info.value.code == 1, (
            "hook_main decorator should exit with code 1 when exception occurs"
        )

    def test_hook_main_prints_error_to_stderr(self, capsys):
        """
        Test that error message is printed to stderr.

        Given: A function decorated with @hook_main that raises an exception
        When: The decorated function is called (and caught)
        Then: Error message should be printed to stderr
        """
        # Arrange: Import hook_main decorator
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from __lib.hook_base import hook_main

        # Create a test function that raises an exception
        @hook_main
        def failing_function():
            raise RuntimeError("Specific error for stderr test")

        # Act: Call the function (it will exit, but we capture output first)
        with pytest.raises(SystemExit):
            failing_function()

        # Assert: Check stderr contains error message
        captured = capsys.readouterr()
        assert "HOOK_ERROR" in captured.err, (
            "stderr should contain HOOK_ERROR prefix"
        )
        assert "RuntimeError" in captured.err, (
            "stderr should contain exception type"
        )
        assert "Specific error for stderr test" in captured.err, (
            "stderr should contain the error message"
        )

    def test_hook_main_prints_json_error_to_stdout(self, capsys):
        """
        Test that JSON output {"ok": False, "error": "..."} is printed to stdout.

        Given: A function decorated with @hook_main that raises an exception
        When: The decorated function is called (and caught)
        Then: JSON with ok=False and error message should be printed to stdout
        """
        # Arrange: Import hook_main decorator
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        import json

        from __lib.hook_base import hook_main

        # Create a test function that raises an exception
        test_error_msg = "JSON output test error"
        @hook_main
        def failing_function():
            raise Exception(test_error_msg)

        # Act: Call the function
        with pytest.raises(SystemExit):
            failing_function()

        # Assert: Check stdout contains valid JSON with expected structure
        captured = capsys.readouterr()
        stdout_content = captured.out.strip()

        # Parse the JSON from stdout
        try:
            error_json = json.loads(stdout_content)
        except json.JSONDecodeError:
            assert False, (
                f"stdout should contain valid JSON, got: {stdout_content}"
            )

        assert error_json.get("ok") is False, (
            f"JSON should have 'ok': False, got: {error_json}"
        )
        assert test_error_msg in error_json.get("error", ""), (
            f"JSON error field should contain the error message, got: {error_json}"
        )

    def test_hook_main_preserves_function_metadata_with_functools_wraps(self):
        """
        Test that functools.wraps preserves original function metadata.

        Given: A function with custom name, docstring, and module
        When: The function is decorated with @hook_main
        Then: The decorated function should preserve original metadata
        """
        # Arrange: Import hook_main decorator
        hooks_dir = Path(__file__).resolve().parent.parent
        if str(hooks_dir) not in sys.path:
            sys.path.insert(0, str(hooks_dir))

        from __lib.hook_base import hook_main

        # Create a test function with specific metadata
        @hook_main
        def my_custom_function_name():
            """This is a custom docstring for testing."""
            return "success"

        # Assert: Metadata should be preserved
        assert my_custom_function_name.__name__ == "my_custom_function_name", (
            f"Function name should be preserved, got: {my_custom_function_name.__name__}"
        )
        assert "custom docstring for testing" in my_custom_function_name.__doc__, (
            f"Function docstring should be preserved, got: {my_custom_function_name.__doc__}"
        )

        # Verify it still works correctly
        result = my_custom_function_name()
        assert result == "success", (
            "Function should still execute normally when no exception occurs"
        )
