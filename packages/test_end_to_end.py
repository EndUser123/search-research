#!/usr/bin/env python3
"""
End-to-end test for search-research → search-backends → user results
Tests the full pipeline from query to results.
"""

import asyncio
import sys
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent / "search-research"))
sys.path.insert(0, str(Path(__file__).parent / "search-backends"))

from search_backends import CKSMetadataBackend

from core import SearchRouter


def test_search_backends_direct():
    """Test search-backends directly."""
    print("\n" + "=" * 80)
    print("TEST 1: search-backends Direct Import")
    print("=" * 80)

    try:
        backend = CKSMetadataBackend()
        print("✓ CKSMetadataBackend imported and created")

        results = backend.search("test", limit=1)
        print(f"✓ CKSMetadataBackend.search() returned {len(results)} results")

        if results:
            r = results[0]
            print(f"  - Title: {r.title[:50]}...")
            print(f"  - Content: {r.content[:100]}...")
            print(f"  - Score: {r.score}")
        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_search_research_router():
    """Test search-research router with backends."""
    print("\n" + "=" * 80)
    print("TEST 2: search-research Router (uses search-backends internally)")
    print("=" * 80)

    try:
        router = SearchRouter()
        print("✓ SearchRouter created")

        results = await router.search_async("async patterns", limit=5)
        print(f"✓ Search executed, returned {len(results)} results")

        if results:
            print("\nTop 3 results:")
            for i, r in enumerate(results[:3]):
                print(f"\n  {i + 1}. [{r.source}] (score: {r.score:.2f})")
                print(f"     Title: {r.title[:60]}...")
                print(f"     Content: {r.content[:80]}...")

        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def test_full_pipeline():
    """Test the full pipeline from query to formatted results."""
    print("\n" + "=" * 80)
    print("TEST 3: Full Pipeline with Result Formatting")
    print("=" * 80)

    try:
        from core.results.synthesis import SynthesisProcessor

        router = SearchRouter()
        synthesizer = SynthesisProcessor()

        # Execute search
        results = await router.search_async("working principles", limit=5)
        print(f"✓ Found {len(results)} results")

        # Synthesize results
        if results:
            synthesis = synthesizer.synthesize(results, query="working principles")
            print(f"✓ Synthesis created: {synthesis['summary'][:100]}...")

            # Show sources
            print(f"\n✓ Sources: {synthesis['sources']}")

        return True
    except Exception as e:
        print(f"✗ Failed: {e}")
        import traceback

        traceback.print_exc()
        return False


async def main():
    """Run all tests."""
    print("\n" + "=" * 80)
    print("END-TO-END TEST SUITE")
    print("Testing: search-research → search-backends → user results")
    print("=" * 80)

    results = []

    # Test 1: Direct search-backends
    results.append(("search-backends direct", test_search_backends_direct()))

    # Test 2: search-research router
    results.append(("search-research router", await test_search_research_router()))

    # Test 3: Full pipeline
    results.append(("full pipeline", await test_full_pipeline()))

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)

    passed = sum(1 for _, r in results if r)
    total = len(results)

    for name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {name}")

    print(f"\nTotal: {passed}/{total} tests passed")

    if passed == total:
        print("\n✓ All tests passed! The full pipeline is working.")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
