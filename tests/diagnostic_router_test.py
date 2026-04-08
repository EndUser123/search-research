#!/usr/bin/env python3
"""
Diagnostic test to understand why UnifiedAsyncRouter returns 0 results.
"""

import asyncio
import logging
import sys
from pathlib import Path

# Add paths
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

# Enable debug logging
logging.basicConfig(level=logging.DEBUG, format='%(name)s - %(levelname)s - %(message)s')

from core.unified_router import UnifiedAsyncRouter
from search_research import AsyncSearchRouter


async def diagnose_local_router():
    """Test AsyncSearchRouter directly."""
    print("=" * 80)
    print("DIAGNOSIS 1: AsyncSearchRouter Direct Test")
    print("=" * 80)

    router = AsyncSearchRouter(enable_jmri=True, enable_cache=False)

    print("\n[DEBUG] Initialized AsyncSearchRouter")
    print(f"[DEBUG] Available backends: {list(router._backends.keys())}")

    # Test each backend individually
    for backend_name, backend in router._backends.items():
        print(f"\n[DEBUG] Testing backend: {backend_name}")
        try:
            results = backend.search("async", limit=5)
            print(f"[DEBUG]   Backend '{backend_name}' returned {len(results)} results")
            if results:
                print(f"[DEBUG]   First result: {results[0]}")
        except Exception as e:
            print(f"[DEBUG]   Backend '{backend_name}' failed: {e}")

    # Test full search
    print("\n[DEBUG] Running full search for 'async'...")
    results = await router.search_async("async", limit=10)
    print(f"[DEBUG] Full search returned {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"[DEBUG]   Result {i+1}: {r}")

    return results


async def diagnose_unified_router():
    """Test UnifiedAsyncRouter."""
    print("\n\n" + "=" * 80)
    print("DIAGNOSIS 2: UnifiedAsyncRouter Test")
    print("=" * 80)

    router = UnifiedAsyncRouter(
        mode="auto",
        enable_jmri=True,
        rrf_k=60,
    )

    print("\n[DEBUG] Initialized UnifiedAsyncRouter (mode=auto)")
    print("[DEBUG] Testing query: 'async await'")

    results = await router.search_async("async await", limit=10)
    print(f"[DEBUG] UnifiedAsyncRouter returned {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"[DEBUG]   Result {i+1}: {r}")

    return results


async def diagnose_local_only_mode():
    """Test UnifiedAsyncRouter in local-only mode."""
    print("\n\n" + "=" * 80)
    print("DIAGNOSIS 3: UnifiedAsyncRouter (local-only mode)")
    print("=" * 80)

    router = UnifiedAsyncRouter(
        mode="local-only",
        enable_jmri=True,
    )

    print("\n[DEBUG] Initialized UnifiedAsyncRouter (mode=local-only)")
    print("[DEBUG] Testing query: 'async'")

    results = await router.search_async("async", limit=10)
    print(f"[DEBUG] UnifiedAsyncRouter (local-only) returned {len(results)} results")
    for i, r in enumerate(results[:3]):
        print(f"[DEBUG]   Result {i+1}: {r}")

    return results


async def main():
    """Run all diagnostic tests."""
    print("\n" + "=" * 80)
    print("ROUTER DIAGNOSTIC TEST SUITE")
    print("=" * 80)

    try:
        # Test 1: Direct AsyncSearchRouter
        results1 = await diagnose_local_router()

        # Test 2: UnifiedAsyncRouter (auto mode)
        results2 = await diagnose_unified_router()

        # Test 3: UnifiedAsyncRouter (local-only mode)
        results3 = await diagnose_local_only_mode()

        # Summary
        print("\n\n" + "=" * 80)
        print("DIAGNOSTIC SUMMARY")
        print("=" * 80)
        print(f"Test 1 (AsyncSearchRouter direct): {len(results1)} results")
        print(f"Test 2 (UnifiedAsyncRouter auto): {len(results2)} results")
        print(f"Test 3 (UnifiedAsyncRouter local-only): {len(results3)} results")

        if len(results1) == 0:
            print("\n[DIAGNOSIS] Local backends are not returning results.")
            print("[DIAGNOSIS] Possible causes:")
            print("  1. Backends not properly initialized")
            print("  2. No indexed content available")
            print("  3. Search path/configuration issues")
        else:
            print("\n[DIAGNOSIS] Local backends ARE returning results.")
            print("[DIAGNOSIS] Issue may be in UnifiedAsyncRouter logic.")

    except Exception as e:
        print(f"\n[ERROR] Diagnostic test failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
