"""
Unit tests for status_display.py timeout decorator.

These tests verify the _execute_with_timeout function handles edge cases correctly.

BUG: The current implementation uses `if exception[0]:` which is a truthy check.
This should be `if exception[0] is not None:` to be explicit and handle all cases correctly.
"""
import pytest
import threading
import time
from unittest.mock import patch
from yt_fts.core.status_display import _execute_with_timeout


class TestExecuteWithTimeout:
    """Tests for _execute_with_timeout decorator behavior."""

    def test_timeout_decorator_returns_result_on_success(self):
        """
        Test that _execute_with_timeout returns function result when no exception occurs.
        
        Given: A function that returns a value
        When: Executed with _execute_with_timeout
        Then: The returned value should match the function's result
        """
        def successful_func():
            return "success"
        
        result = _execute_with_timeout(successful_func, timeout_seconds=1.0)
        assert result == "success"

    def test_timeout_decorator_raises_exception_when_function_raises(self):
        """
        Test that _execute_with_timeout propagates exceptions from wrapped function.
        
        Given: A function that raises a ValueError
        When: Executed with _execute_with_timeout
        Then: ValueError should be raised
        """
        def failing_func():
            raise ValueError("test error")
        
        with pytest.raises(ValueError, match="test error"):
            _execute_with_timeout(failing_func, timeout_seconds=1.0)

    def test_timeout_decorator_returns_none_on_timeout(self):
        """
        Test that _execute_with_timeout returns None when function times out.
        
        Given: A function that sleeps longer than timeout
        When: Executed with _execute_with_timeout with short timeout
        Then: None should be returned
        """
        def slow_func():
            time.sleep(2.0)
            return "should not see this"
        
        result = _execute_with_timeout(slow_func, timeout_seconds=0.1)
        assert result is None

    def test_timeout_decorator_with_none_exception_does_not_crash(self):
        """
        Test that _execute_with_timeout handles None exception correctly.
        
        Given: A function that completes successfully (exception stays None)
        When: Executed with _execute_with_timeout
        Then: Should return result without attempting to raise None
        """
        def func_returning_none():
            return None
        
        # This should not crash - exception[0] should remain None
        result = _execute_with_timeout(func_returning_none, timeout_seconds=1.0)
        assert result is None

    def test_timeout_decorator_should_use_explicit_none_check(self):
        """
        CHARACTERIZATION TEST: Documents current behavior before fix.
        
        This test demonstrates that the current implementation uses a truthy check
        (`if exception[0]:`) instead of an explicit None check
        (`if exception[0] is not None:`).
        
        The bug is on line 45-46 of status_display.py:
            if exception[0]:        # Truthy check - BUG
                raise exception[0]
        
        Should be:
            if exception[0] is not None:  # Explicit check - CORRECT
                raise exception[0]
        
        This test will FAIL until the code is fixed to use explicit None check.
        
        Given: The _execute_with_timeout function
        When: Examining the source code
        Then: It should use `if exception[0] is not None:` not `if exception[0]:`
        """
        import inspect
        source = inspect.getsource(_execute_with_timeout)
        
        # This assertion will FAIL with current code because it uses `if exception[0]:`
        # After fixing to use `if exception[0] is not None:`, this test will PASS
        assert "if exception[0] is not None:" in source, \
            "BUG: Code uses truthy check 'if exception[0]:' instead of explicit 'if exception[0] is not None:'"

    def test_timeout_decorator_with_zero_timeout(self):
        """
        Test that _execute_with_timeout handles zero timeout correctly.
        
        Given: A function that takes time to complete
        When: Executed with _execute_with_timeout with zero timeout
        Then: Should return None due to immediate timeout
        """
        def slow_func():
            time.sleep(0.5)
            return "result"
        
        result = _execute_with_timeout(slow_func, timeout_seconds=0.0)
        # With zero timeout, thread may not even start, should return None
        assert result is None
