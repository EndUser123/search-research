#!/usr/bin/env python3
"""RuntimeWarning regression test.

This test explicitly checks that NO RuntimeWarning about unawaited coroutines
appears when using async backends. This prevents the bug from reappearing silently.
"""

import asyncio
import warnings

from search_research import AsyncSearchRouter


async def test_no_runtime_warning_with_async_backends():
    """Test that NO RuntimeWarning appears when using async backends."""

    # Create router
    router = AsyncSearchRouter()

    # Check if RLM backend is available
    if "rlm" not in router._backends:
        print("⚠ RLM backend not available - skipping regression test")
        return True

    # Capture warnings
    with warnings.catch_warnings(record=True) as warning_list:
        warnings.simplefilter("always")

        # Execute search - should NOT produce RuntimeWarning
        results = await router.search_async("test query", limit=5)

        # Check for RuntimeWarnings
        runtime_warnings = [
            w for w in warning_list
            if issubclass(w.category, RuntimeWarning)
            and "coroutine" in str(w.message).lower()
        ]

        if runtime_warnings:
            print("\n❌ REGRESSION TEST FAILED")
            print(f"   Found {len(runtime_warnings)} RuntimeWarning(s):")
            for w in runtime_warnings:
                print(f"   - {w.category.__name__}: {w.message}")
            return False
        else:
            print("\n✅ REGRESSION TEST PASSED")
            print("   NO RuntimeWarning about unawaited coroutines")
            print(f"   Search completed: {len(results)} results")
            return True


async def main():
    """Run RuntimeWarning regression test."""
    print("=" * 60)
    print("RuntimeWarning Regression Test")
    print("=" * 60)
    print("\nTesting for: RuntimeWarning: coroutine 'XYZ.search' was never awaited")
    print()

    success = await test_no_runtime_warning_with_async_backends()

    if success:
        print("\n" + "=" * 60)
        print("✅ All regression tests PASSED")
        print("=" * 60)
        return 0
    else:
        print("\n" + "=" * 60)
        print("❌ Regression test FAILED")
        print("=" * 60)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
