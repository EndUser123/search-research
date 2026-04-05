#!/usr/bin/env python3
from __future__ import annotations

"""
Performance Tracker - Hook Performance Decorator
=================================================

Decorator for tracking hook execution performance.

Features:
- Execution time tracking using time.perf_counter()
- Output size measurement (stdout bytes)
- Configurable timeouts per hook type
- Integration with cc_diagnostic_logger.log_hook_invocation
- Exception-safe: logs performance even when hook raises

Usage:
    from performance_tracker import track_hook_performance

    @track_hook_performance(hook_type="UserPromptSubmit")
    def main():
        return {"result": "success"}

Author: CSF
Version: 1.0.0
"""

import functools
import sys
import time
from collections.abc import Callable
from io import StringIO
from typing import Any

from cc_diagnostic_logger import log_hook_invocation

# =============================================================================
# DEFAULT TIMEOUTS PER HOOK TYPE
# =============================================================================

HOOK_TYPE_TIMEOUTS = {
    "UserPromptSubmit": 3000,  # 3 seconds
    "PreToolUse": 2000,        # 2 seconds
    "PostToolUse": 6000,       # 6 seconds
    "Stop": 1000,              # 1 second
}


# =============================================================================
# DECORATOR
# =============================================================================

def track_hook_performance(
    hook_type: str,
    timeout_ms: int | None = None,
    hook_name: str | None = None,
) -> Callable:
    """
    Decorator to track hook execution performance.

    Args:
        hook_type: Type of hook (UserPromptSubmit, PreToolUse, PostToolUse, Stop)
        timeout_ms: Optional custom timeout in milliseconds. If not provided,
                    uses the default for the hook_type.
        hook_name: Optional hook name for logging. If not provided, uses the
                   wrapped function's __name__.

    Returns:
        Decorated function with performance tracking

    Example:
        @track_hook_performance(hook_type="UserPromptSubmit")
        def main():
            print("Hello")
            return {"result": "success"}
    """
    def decorator(func: Callable) -> Callable:
        # Determine timeout: use explicit override, or default for hook_type
        effective_timeout = timeout_ms
        if effective_timeout is None:
            effective_timeout = HOOK_TYPE_TIMEOUTS.get(hook_type, 3000)

        # Use provided hook_name or fall back to function name
        effective_hook_name = hook_name or func.__name__

        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            # Capture original stdout
            original_stdout = sys.stdout

            # Track execution time
            start_time = time.perf_counter()

            # Capture stdout to measure output size
            string_buffer = StringIO()
            sys.stdout = string_buffer

            exception_raised = None
            result = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                exception_raised = e
                raise
            finally:
                # Calculate execution time
                end_time = time.perf_counter()
                execution_time_ms = (end_time - start_time) * 1000

                # Restore stdout
                sys.stdout = original_stdout

                # Measure output size (bytes written to stdout)
                output_size_bytes = len(string_buffer.getvalue().encode("utf-8"))

                # Output any captured stdout to the real stdout
                captured_output = string_buffer.getvalue()
                if captured_output:
                    original_stdout.write(captured_output)

                # Log performance via log_hook_invocation
                log_hook_invocation(
                    hook_name=effective_hook_name,
                    event_type=hook_type,
                    action="pass" if exception_raised is None else "error",
                    execution_time_ms=execution_time_ms,
                    timeout_ms=effective_timeout,
                    output_size_bytes=output_size_bytes,
                )

        return wrapper

    return decorator


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def get_default_timeout(hook_type: str) -> int:
    """
    Get the default timeout for a given hook type.

    Args:
        hook_type: Type of hook

    Returns:
        Default timeout in milliseconds
    """
    return HOOK_TYPE_TIMEOUTS.get(hook_type, 3000)


def set_default_timeout(hook_type: str, timeout_ms: int) -> None:
    """
    Set a custom default timeout for a hook type.

    Args:
        hook_type: Type of hook
        timeout_ms: Timeout in milliseconds
    """
    HOOK_TYPE_TIMEOUTS[hook_type] = timeout_ms
