#!/usr/bin/env python3
"""
Test UnifiedAsyncRouter with fixed backends (auto-detected paths).
"""

import asyncio
import sys
from pathlib import Path

import pytest

# Add paths
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from search_research import UnifiedAsyncRouter  # noqa: E402
from quality_checker import QualityConfig  # noqa: E402


@pytest.mark.asyncio
async def test_unified_router():
    """Test UnifiedAsyncRouter with auto-detected paths."""

    print("=" * 80)
    print("UNIFIED ROUTER TEST with Fixed Backends")
    print("=" * 80)

    print(f"\n[INFO] Current working directory: {Path.cwd()}")

    # Test 1: Simple query
    print("\n" + "-" * 80)
    print("Test 1: Simple query 'AsyncSearchRouter'")
    print("-" * 80)

    router = UnifiedAsyncRouter(
        mode="local-only",  # Only local search for testing
        enable_jmri=True,
        rrf_k=60,
        quality_config=QualityConfig(
            confidence_threshold=0.5,
            freshness_hours=24,
            min_backends=1
        )
    )

    results = await router.search_async("AsyncSearchRouter", limit=10)
    print(f"\n[RESULT] Search returned {len(results)} results")

    for i, r in enumerate(results[:5]):
        print(f"\n  [{i+1}] Score: {r.score:.2f}")
        if hasattr(r, 'backend'):
            print(f"      Backend: {r.backend}")
            print(f"      Title: {r.title[:80]}")
        elif hasattr(r, 'source'):
            print(f"      Source: {r.source}")
            print(f"      Title: {r.title[:80]}")

    # Test 2: Broader query
    print("\n" + "-" * 80)
    print("Test 2: Broader query 'async'")
    print("-" * 80)

    results2 = await router.search_async("async", limit=20)
    print(f"\n[RESULT] Search returned {len(results2)} results")

    for i, r in enumerate(results2[:5]):
        print(f"\n  [{i+1}] Score: {r.score:.2f}")
        if hasattr(r, 'backend'):
            print(f"      Backend: {r.backend}")
            print(f"      Title: {r.title[:80]}")
        elif hasattr(r, 'source'):
            print(f"      Source: {r.source}")
            print(f"      Title: {r.title[:80]}")

    print("\n" + "=" * 80)
    print("CONCLUSION:")
    if len(results) > 0 and len(results2) > 0:
        print("✅ SUCCESS: UnifiedAsyncRouter is working with fixed backends")
        print(f"   Test 1: {len(results)} results")
        print(f"   Test 2: {len(results2)} results")
    else:
        print("❌ FAILURE: Still getting no results")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(test_unified_router())
