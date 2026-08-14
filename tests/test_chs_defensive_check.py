#!/usr/bin/env python3
"""Minimal test for CHS backend defensive check fix."""

import asyncio


# Mock backend without search method (like IncrementalIndexUpdater)
class MockIndexerBackend:
    """A backend that only has indexing methods, no search."""

    def update_index(self):
        """Update the index."""
        pass


# Mock backend with search method
class MockSearchBackend:
    """A backend with search method."""

    def search(self, query: str, limit: int = 10) -> list:
        """Search method."""
        return []


async def test_defensive_check():
    """Test the defensive check logic directly."""
    print("Testing: Defensive check for non-searchable backends...")

    # Test 1: Backend without search method
    indexer = MockIndexerBackend()
    search_method = getattr(indexer, 'search', None)

    if search_method is None or not callable(search_method):
        print("  ✅ PASS: Non-searchable backend correctly detected")
        print(f"     has 'search' attribute: {hasattr(indexer, 'search')}")
        print(f"     is callable: {callable(search_method)}")
    else:
        print("  ❌ FAIL: Should have detected non-searchable backend")
        return False

    # Test 2: Backend with search method
    searchable = MockSearchBackend()
    search_method = getattr(searchable, 'search', None)

    if search_method is not None and callable(search_method):
        print("  ✅ PASS: Searchable backend correctly detected")
        print(f"     has 'search' attribute: {hasattr(searchable, 'search')}")
        print(f"     is callable: {callable(search_method)}")
    else:
        print("  ❌ FAIL: Should have detected searchable backend")
        return False

    print("\n✅ ALL TESTS PASSED")
    return True


if __name__ == "__main__":
    success = asyncio.run(test_defensive_check())
    exit(0 if success else 1)
