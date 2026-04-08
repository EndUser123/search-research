#!/usr/bin/env python3
"""
Simplified test to verify router works with a guaranteed match.
"""

import asyncio
import sys
from pathlib import Path

# Add paths
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from search_research import AsyncSearchRouter


async def test_guaranteed_match():
    """Test with a query that MUST match in the current directory."""
    print("=" * 80)
    print("SIMPLE ROUTER TEST: Guaranteed Match Query")
    print("=" * 80)

    router = AsyncAsyncSearchRouter(enable_jmri=True, enable_cache=False)

    print("\n[INFO] Initialized AsyncAsyncSearchRouter")
    print(f"[INFO] Available backends: {list(router._backends.keys())}")

    # Use a query that MUST find something in the current codebase
    # "class AsyncAsyncSearchRouter" will definitely match in router.py
    query = "class AsyncAsyncSearchRouter"
    print(f"\n[INFO] Testing query: '{query}'")
    print("[INFO] This query MUST match in P:/packages/search-research/src/search_research/router.py")

    results = await router.search_async(query, limit=10)
    print(f"\n[RESULT] Search returned {len(results)} results")

    if results:
        print("\n[SUCCESS] Router is working! Found results:")
        for i, r in enumerate(results[:5]):
            print(f"\n  Result {i+1}:")
            print(f"    Source: {r.source}")
            print(f"    Score: {r.score:.3f}")
            print(f"    Title: {r.title[:80]}")
            print(f"    Content: {r.content[:100]}...")
        return True
    else:
        print("\n[FAILURE] Router returned 0 results even for guaranteed match!")
        print("[DEBUG] This indicates a fundamental router configuration issue")
        return False


async def main():
    success = await test_guaranteed_match()
    if success:
        print("\n" + "=" * 80)
        print("CONCLUSION: Router works with guaranteed matches")
        print("The previous 'async' query failed because there's no content to match")
        print("=" * 80)
    else:
        print("\n" + "=" * 80)
        print("CONCLUSION: Router is broken even for guaranteed matches")
        print("This is a critical configuration issue")
        print("=" * 80)
    return success


if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)
