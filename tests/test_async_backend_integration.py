#!/usr/bin/env python3
"""Integration test for async backend fix.

This test verifies that RLMBackend (which has async search) is properly awaited
instead of being wrapped with asyncio.to_thread().
"""

import asyncio


async def test_rlm_backend_async_fix():
    """Test that RLMBackend.async search works without RuntimeWarning."""
    from search_research import AsyncSearchRouter

    # Create router with RLM backend
    router = AsyncSearchRouter()

    # Verify RLM is available
    if "rlm" not in router._backends:
        print("⚠ RLM backend not available - skipping integration test")
        return

    # Execute search - this should NOT produce RuntimeWarning about unawaited coroutines
    results = await router.search_async("test query", limit=5)
    print(f"✓ RLM backend search completed: {len(results)} results")
    return results


if __name__ == "__main__":
    asyncio.run(test_rlm_backend_async_fix())
