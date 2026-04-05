"""Async/Sync Bridge for CLI applications.

Provides safe async/sync compatibility for CLI commands that need to call async functions
from synchronous context, particularly important for Windows IocpProactor event loop compatibility.
"""

import asyncio
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import Any, TypeVar

T = TypeVar("T")


class AsyncBridge:
    """Safe async/sync bridge for CLI applications on Windows IocpProactor."""

    @staticmethod
    def run_async(coro, timeout: int = 60) -> Any:
        """
        Run async coroutine from sync context safely.

        This method detects if we're already in an async context and handles appropriately:
        - If in async context with running loop: Use thread executor
        - If in sync context: Use asyncio.run()

        Args:
            coro: Async coroutine to run
            timeout: Timeout in seconds (default: 60)

        Returns:
            Result of the coroutine

        Raises:
            FutureTimeoutError: If operation times out
            Exception: Any exception from the coroutine
        """
        loop = None
        try:
            # Check if we're already in an async context
            loop = asyncio.get_running_loop()
            if loop.is_running():
                # We're in async context with running loop, use thread executor
                with ThreadPoolExecutor() as executor:
                    future = executor.submit(asyncio.run, coro)
                    return future.result(timeout=timeout)
            else:
                # Loop exists but not running, use it directly
                return asyncio.run(coro)
        except RuntimeError:
            # No running loop, safe to use asyncio.run
            return asyncio.run(coro)

    @staticmethod
    def is_async_context() -> bool:
        """Check if we're currently in an async context."""
        try:
            loop = asyncio.get_running_loop()
            return loop.is_running()
        except RuntimeError:
            return False

    @staticmethod
    def get_event_loop_info() -> dict:
        """Get information about current event loop for debugging."""
        try:
            loop = asyncio.get_running_loop()
            return {
                "is_running": loop.is_running(),
                "type": loop.__class__.__name__,
                "debug": loop.get_debug(),
                "closed": loop.is_closed(),
                "platform": sys.platform
            }
        except RuntimeError:
            return {
                "is_running": False,
                "type": None,
                "platform": sys.platform,
                "message": "No running event loop"
            }
