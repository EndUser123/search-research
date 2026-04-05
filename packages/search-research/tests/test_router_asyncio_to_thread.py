"""Tests for T-007: asyncio.to_thread() wrapper for sync backends.

RED phase: Tests fail because router doesn't handle sync vs async backends correctly.
GREEN phase: Update router_async.py to detect and handle sync backends.
"""

import asyncio
import time
from unittest.mock import AsyncMock, MagicMock

import pytest


class TestAsyncioToThreadWrapper:
    """Test that router handles both sync and async backends correctly."""

    @pytest.mark.asyncio
    async def test_sync_backend_uses_run_in_executor(self):
        """Test that sync backends use asyncio.to_thread() (run_in_executor).

        Given: A sync backend (has search method but not search_async)
        When: _search_backend_async is called
        Then: Backend runs via run_in_executor (non-blocking)
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Create a real sync function (not MagicMock) for proper testing
        def sync_search(query, limit):
            return [{"title": "result1"}]

        # Create a simple object with the sync search method
        class SyncBackend:
            pass

        sync_backend = SyncBackend()
        sync_backend.search = sync_search

        router._backends = {"sync_backend": sync_backend}

        # Act
        results = await router._search_backend_async("sync_backend", "test query", 10)

        # Assert
        assert len(results) == 1, "Should return one result"
        assert results[0].title == "result1", "Should return results from sync backend"
        assert results[0].source == "SYNC_BACKEND", "Should have correct source"

    @pytest.mark.asyncio
    async def test_async_backend_uses_await_directly(self):
        """Test that async backends use await (not run_in_executor).

        Given: An async backend (has search_async method)
        When: _search_backend_async is called
        Then: Backend runs via await directly
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Create mock async backend
        async_backend = AsyncMock()
        async_backend.search_async = AsyncMock(return_value=[{"title": "result2"}])

        router._backends = {"async_backend": async_backend}

        # Act
        results = await router._search_backend_async("async_backend", "test query", 10)

        # Assert
        assert len(results) == 1, "Should return one result"
        assert results[0].title == "result2", "Should return results from async backend"
        assert results[0].source == "ASYNC_BACKEND", "Should have correct source"
        async_backend.search_async.assert_called_once_with("test query", 10)

    @pytest.mark.asyncio
    async def test_coroutine_search_method_detected(self):
        """Test that backends with async def search() are detected correctly.

        Given: A backend with async def search() coroutine
        When: _search_backend_async is called
        Then: Backend runs via await directly (not run_in_executor)
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Create a real async function (not MagicMock) for proper testing
        async def async_search(query, limit):
            return [{"title": "result3"}]

        # Create a simple object with the async search method
        class AsyncBackend:
            pass

        async_backend = AsyncBackend()
        async_backend.search = async_search

        router._backends = {"async_backend": async_backend}

        # Act
        results = await router._search_backend_async("async_backend", "test query", 10)

        # Assert
        assert len(results) == 1, "Should return one result"
        assert results[0].title == "result3", "Should return results from async search method"
        assert results[0].source == "ASYNC_BACKEND", "Should have correct source"

    @pytest.mark.asyncio
    async def test_multiple_backends_run_concurrently(self):
        """Test that sync and async backends run concurrently via asyncio.gather().

        Given: Multiple backends (mix of sync and async)
        When: search_async is called with multiple backends
        Then: All backends run concurrently (not sequentially)
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Track execution order
        execution_order = []

        # Create sync backend that tracks execution time
        def sync_search(query, limit):
            execution_order.append("sync_start")
            time.sleep(0.1)  # Simulate work
            execution_order.append("sync_end")
            return [{"title": "sync_result"}]

        # Create async backend that tracks execution time
        async def async_search(query, limit):
            execution_order.append("async_start")
            await asyncio.sleep(0.1)  # Simulate work
            execution_order.append("async_end")
            return [{"title": "async_result"}]

        # Create backend objects with methods
        class SyncBackend:
            pass

        class AsyncBackend:
            pass

        sync_backend = SyncBackend()
        sync_backend.search = sync_search

        async_backend = AsyncBackend()
        async_backend.search = async_search

        router._backends = {
            "sync_backend": sync_backend,
            "async_backend": async_backend,
        }

        # Act
        results = await router.search_async("test query", 10, backends=["sync_backend", "async_backend"])

        # Assert
        assert len(results) == 2, "Should have results from both backends"

        # Verify concurrency: both should start before either finishes
        assert "sync_start" in execution_order
        assert "async_start" in execution_order

        # In sequential execution, sync_start → sync_end → async_start → async_end
        # In concurrent execution, sync_start → async_start → (sync_end, async_end in any order)
        # Check that async_start happened before sync_end (concurrency indicator)
        sync_end_index = execution_order.index("sync_end")
        async_start_index = execution_order.index("async_start")

        # This assertion proves concurrency: async started before sync finished
        assert async_start_index < sync_end_index, "Async backend should start before sync backend finishes"

class TestBackendTimeoutHandling:
    """Test timeout handling for sync and async backends."""

    @pytest.mark.asyncio
    async def test_sync_backend_timeout(self):
        """Test that sync backend timeout is handled correctly.

        Given: A sync backend that takes longer than backend_timeout
        When: _search_backend_async is called
        Then: Returns empty list and records timeout in health registry
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter(mode="fast")  # 2s timeout
        router.backend_timeout = 0.1  # Set very short timeout for test

        sync_backend = MagicMock()
        # Make sync backend sleep longer than timeout
        sync_backend.search = MagicMock(
            side_effect=lambda q, l: asyncio.sleep(0.2) or [{"title": "slow_result"}]
        )

        router._backends = {"slow_sync_backend": sync_backend}

        # Act
        results = await router._search_backend_async("slow_sync_backend", "test query", 10)

        # Assert
        assert results == [], "Should return empty list on timeout"
        # Health registry should record failure
        assert not router._health.is_available("slow_sync_backend"), "Backend should be marked unavailable after timeout"

    @pytest.mark.asyncio
    async def test_async_backend_timeout(self):
        """Test that async backend timeout is handled correctly.

        Given: An async backend that takes longer than backend_timeout
        When: _search_backend_async is called
        Then: Returns empty list and records timeout in health registry
        """
        # Arrange
        from core.router_async import AsyncSearchRouter

        router = AsyncSearchRouter(mode="fast")  # 2s timeout
        router.backend_timeout = 0.1  # Set very short timeout for test

        async_backend = MagicMock()
        # Make async backend sleep longer than timeout
        async def slow_search(query, limit):
            await asyncio.sleep(0.2)
            return [{"title": "slow_async_result"}]

        async_backend.search_async = MagicMock(side_effect=slow_search)

        router._backends = {"slow_async_backend": async_backend}

        # Act
        results = await router._search_backend_async("slow_async_backend", "test query", 10)

        # Assert
        assert results == [], "Should return empty list on timeout"
        # Health registry should record failure
        assert not router._health.is_available("slow_async_backend"), "Backend should be marked unavailable after timeout"
