#!/usr/bin/env python3
"""Per-backend test to verify each backend produces results."""

import asyncio
from search_research import AsyncSearchRouter

BACKENDS_UNDER_TEST = [
    "cds",
    "cks",
    "claude-history",
    "grep",
    "kg",
    "ast_code",
    "lsp",
    "notebooklm",
    "rlm",
    "skills",
    "yt_is",
    "qmd_wiki",
]


async def test_backend(router: AsyncSearchRouter, backend_name: str, query: str) -> dict:
    """Test a single backend with a broad query."""
    try:
        results = await router.search_async(query, limit=3, backends=[backend_name])
        return {
            "backend": backend_name,
            "count": len(results),
            "status": "PASS" if results else "ZERO_RESULTS",
            "first_result": results[0]["title"][:60] if results else None,
        }
    except Exception as e:
        return {
            "backend": backend_name,
            "count": 0,
            "status": f"ERROR: {type(e).__name__}: {e}",
            "first_result": None,
        }


async def main():
    print("=" * 80)
    print("PER-BACKEND TEST")
    print("=" * 80)

    router = AsyncSearchRouter(enable_jmri=True, enable_cache=False, mode="local-only")
    query = "class AsyncSearchRouter"  # Should match in router.py

    print(f"\nQuery: '{query}'")
    print(f"Mode: local-only\n")

    # First verify backends are registered
    results_all = await router.search_async("class", limit=1)
    print(f"Backends after first search: {list(router._backends.keys())}\n")

    print(f"{'Backend':<20} {'Status':<15} {'Count':<6} First Result")
    print("-" * 80)

    for backend_name in BACKENDS_UNDER_TEST:
        result = await test_backend(router, backend_name, query)
        status = result["status"]
        count = result["count"]
        first = result["first_result"] or ""
        print(f"{backend_name:<20} {status:<15} {count:<6} {first}")

    print("-" * 80)
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())