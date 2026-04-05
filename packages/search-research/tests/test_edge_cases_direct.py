#!/usr/bin/env python3
"""Direct execution of edge case tests (bypassing pytest async issues)."""

import asyncio
import inspect
from unittest.mock import AsyncMock, MagicMock

from search_research import AsyncSearchRouter


async def test_sync_backend_still_works():
    """Test that sync backends are not affected by async detection."""
    print("Testing: Sync backends still work correctly...")

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

    print("  ✅ PASSED")


async def test_hybrid_backend_with_async_method():
    """Test backend that has async search method is detected correctly."""
    print("Testing: Hybrid backend with async method...")

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

    print("  ✅ PASSED")


async def test_backend_subclass_override():
    """Test that subclass overrides are detected correctly."""
    print("Testing: Backend subclass override...")

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

    print("  ✅ PASSED")


async def test_multiple_async_backends():
    """Test that multiple async backends all work correctly."""
    print("Testing: Multiple async backends...")

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

    print("  ✅ PASSED")


async def test_mixed_async_and_sync_backends():
    """Test that async and sync backends can coexist."""
    print("Testing: Mixed async and sync backends...")

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

    print("  ✅ PASSED")


async def main():
    """Run all edge case tests."""
    print("=" * 60)
    print("Edge Case Tests: Async Backend Detection")
    print("=" * 60)
    print()

    try:
        await test_sync_backend_still_works()
        await test_hybrid_backend_with_async_method()
        await test_backend_subclass_override()
        await test_multiple_async_backends()
        await test_mixed_async_and_sync_backends()

        print("\n" + "=" * 60)
        print("✅ ALL EDGE CASE TESTS PASSED")
        print("=" * 60)
        return 0
    except Exception as e:
        print(f"\n❌ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
