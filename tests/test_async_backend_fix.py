#!/usr/bin/env python3
"""Test that async backends are properly awaited.

This test verifies the fix for the unawaited coroutine bug where
RLMBackend.search() (async method) was being wrapped with asyncio.to_thread()
instead of being awaited directly.
"""

import asyncio
import unittest
from unittest.mock import AsyncMock, MagicMock

from search_research import AsyncSearchRouter


class TestAsyncBackendFix(unittest.TestCase):
    """Test async backend detection and proper awaiting."""

    def test_async_backend_search_is_awaited_directly(self):
        """Test that async backends are awaited directly, not wrapped in to_thread."""
        # Create an async backend mock
        async_backend = AsyncMock()
        async_backend.search = AsyncMock(return_value=[
            {"title": "Test Result", "content": "Test content", "score": 0.9}
        ])

        # Create router with only the async backend
        router = AsyncAsyncSearchRouter()
        router._backends = {"test_async": async_backend}

        # Execute search - should call async backend directly
        async def run_search():
            results = await router.search_async("test query", limit=10)
            return results

        results = asyncio.run(run_search())

        # Verify the async backend was called
        async_backend.search.assert_called_once_with("test query", limit=10)

        # Verify we got results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Test Result")

    def test_sync_backend_uses_to_thread(self):
        """Test that sync backends still use asyncio.to_thread."""
        # Create a sync backend mock
        sync_backend = MagicMock()
        sync_backend.search = MagicMock(return_value=[
            {"title": "Sync Result", "content": "Sync content", "score": 0.8}
        ])

        # Create router with only the sync backend
        router = AsyncAsyncSearchRouter()
        router._backends = {"test_sync": sync_backend}

        # Execute search
        async def run_search():
            results = await router.search_async("test query", limit=10)
            return results

        results = asyncio.run(run_search())

        # Verify the sync backend was called
        sync_backend.search.assert_called_once()

        # Verify we got results
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "Sync Result")

    def test_mixed_async_and_sync_backends(self):
        """Test that both async and sync backends work together."""
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

        # Create router with both backends
        router = AsyncAsyncSearchRouter()
        router._backends = {
            "async_backend": async_backend,
            "sync_backend": sync_backend,
        }

        # Execute search
        async def run_search():
            results = await router.search_async("test query", limit=10)
            return results

        results = asyncio.run(run_search())

        # Verify both backends were called
        async_backend.search.assert_called_once()
        sync_backend.search.assert_called_once()

        # Verify we got results from both
        self.assertEqual(len(results), 2)
        titles = [r.title for r in results]
        self.assertIn("Async Result", titles)
        self.assertIn("Sync Result", titles)


if __name__ == "__main__":
    unittest.main()
