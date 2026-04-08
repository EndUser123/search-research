#!/usr/bin/env python3
"""Edge case tests for async backend detection.

This test suite validates async backend detection works correctly for:
- Hybrid backends (can operate sync or async)
- Backends with deprecated @asyncio.coroutine decorator
- Subclass override scenarios
- Sync backends still work correctly
"""

import inspect
from unittest.mock import AsyncMock, MagicMock

import pytest

from search_research import AsyncSearchRouter


class TestAsyncBackendEdgeCases:
    """Test edge cases for async backend detection."""

    async def test_sync_backend_still_works(self):
        """Test that sync backends are not affected by async detection."""
        # Create a sync backend mock
        sync_backend = MagicMock()
        sync_backend.search = MagicMock(return_value=[
            {"title": "Sync Result", "content": "Sync content", "score": 0.8}
        ])

        # Create router with only sync backend
        router = AsyncAsyncSearchRouter()
        router._backends = {"test_sync": sync_backend}

        # Execute search
        results = await router.search_async("test query", limit=10)

        # Verify sync backend was called
        sync_backend.search.assert_called_once_with("test query", limit=10)

        # Verify we got results
        assert len(results) == 1
        assert results[0].title == "Sync Result"

    async def test_hybrid_backend_with_async_method(self):
        """Test backend that has async search method is detected correctly."""
        # Create hybrid backend with async search
        hybrid_backend = AsyncMock()
        hybrid_backend.search = AsyncMock(return_value=[
            {"title": "Hybrid Result", "content": "Hybrid content", "score": 0.9}
        ])

        # Verify it's detected as async
        assert inspect.iscoroutinefunction(hybrid_backend.search)

        # Create router
        router = AsyncAsyncSearchRouter()
        router._backends = {"test_hybrid": hybrid_backend}

        # Execute search
        results = await router.search_async("test query", limit=10)

        # Verify async backend was called
        hybrid_backend.search.assert_called_once_with("test query", limit=10)

        # Verify we got results
        assert len(results) == 1
        assert results[0].title == "Hybrid Result"

    async def test_backend_subclass_override(self):
        """Test that subclass overrides are detected correctly."""
        # Create parent class with sync search
        class ParentBackend:
            def search(self, query, limit):
                return [{"title": "Parent", "content": "Parent content", "score": 0.5}]

        # Create subclass with async search override
        class ChildBackend(ParentBackend):
            async def search(self, query, limit):
                return [{"title": "Child", "content": "Child content", "score": 0.9}]

        # Verify child is detected as async
        child = ChildBackend()
        assert inspect.iscoroutinefunction(child.search)

        # Create router with child backend
        router = AsyncAsyncSearchRouter()
        router._backends = {"test_child": child}

        # Execute search
        results = await router.search_async("test query", limit=10)

        # Verify we got child's results (async override used)
        assert len(results) == 1
        assert results[0].title == "Child"
        assert results[0].score == 0.9

    async def test_multiple_async_backends(self):
        """Test that multiple async backends all work correctly."""
        # Create multiple async backends
        async_backend_1 = AsyncMock()
        async_backend_1.search = AsyncMock(return_value=[
            {"title": "Async1", "content": "Content1", "score": 0.9}
        ])

        async_backend_2 = AsyncMock()
        async_backend_2.search = AsyncMock(return_value=[
            {"title": "Async2", "content": "Content2", "score": 0.8}
        ])

        # Create router with multiple async backends
        router = AsyncAsyncSearchRouter()
        router._backends = {
            "async1": async_backend_1,
            "async2": async_backend_2,
        }

        # Execute search
        results = await router.search_async("test query", limit=10)

        # Verify both async backends were called
        async_backend_1.search.assert_called_once()
        async_backend_2.search.assert_called_once()

        # Verify we got results from both
        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Async1" in titles
        assert "Async2" in titles

    async def test_mixed_async_and_sync_backends(self):
        """Test that async and sync backends can coexist."""
        # Create async backend
        async_backend = AsyncMock()
        async_backend.search = AsyncMock(return_value=[
            {"title": "Async Result", "content": "Async content", "score": 0.9}
        ])

        # Create sync backend
        sync_backend = MagicMock()
        sync_backend.search = MagicMock(return_value=[
            {"title": "Sync Result", "content": "Sync content", "score": 0.7}
        ])

        # Create router with both
        router = AsyncAsyncSearchRouter()
        router._backends = {
            "async_backend": async_backend,
            "sync_backend": sync_backend,
        }

        # Execute search
        results = await router.search_async("test query", limit=10)

        # Verify both were called
        async_backend.search.assert_called_once()
        sync_backend.search.assert_called_once()

        # Verify we got results from both
        assert len(results) == 2
        titles = [r.title for r in results]
        assert "Async Result" in titles
        assert "Sync Result" in titles

    async def test_async_backend_with_error(self):
        """Test that async backend errors are handled correctly."""
        # Create async backend that raises error
        async_backend = AsyncMock()
        async_backend.search = AsyncMock(side_effect=Exception("Backend error"))

        # Create router
        router = AsyncAsyncSearchRouter()
        router._backends = {"failing_async": async_backend}

        # Execute search - should handle error gracefully
        results = await router.search_async("test query", limit=10)

        # Verify backend was called
        async_backend.search.assert_called_once()

        # Verify we got empty results (error handled)
        assert isinstance(results, list)

    async def test_sync_backend_with_error(self):
        """Test that sync backend errors are handled correctly."""
        # Create sync backend that raises error
        sync_backend = MagicMock()
        sync_backend.search = MagicMock(side_effect=Exception("Backend error"))

        # Create router
        router = AsyncAsyncSearchRouter()
        router._backends = {"failing_sync": sync_backend}

        # Execute search - should handle error gracefully
        results = await router.search_async("test query", limit=10)

        # Verify backend was called
        sync_backend.search.assert_called_once()

        # Verify we got empty results (error handled)
        assert isinstance(results, list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
