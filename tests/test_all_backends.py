#!/usr/bin/env python3
"""Per-backend test to verify each backend produces results."""

import asyncio
from search_research import AsyncSearchRouter

BACKEND_QUERIES = {
    "cds": "async def",
    "cks": "router",
    "claude-history": "import asyncio",
    "grep": "class AsyncSearchRouter",
    "kg": "class",
    "ast_code": "class",
    "lsp": "class",
    "notebooklm": "class",
    "rlm": "class AsyncSearchRouter",
    "skills": "class",
    "yt_is": "class",
    "qmd_wiki": "import asyncio",
}


async def check_backend(router: AsyncSearchRouter, backend_name: str, query: str) -> dict:
    """Test a single backend with its specific query."""
    try:
        results = await router.search_async(query, limit=3, backends=[backend_name])
        return {
            "backend": backend_name,
            "count": len(results),
            "status": "PASS" if results else "ZERO_RESULTS",
            "first_result": results[0].title[:60] if results else None,
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

    print(f"\nMode: local-only\n")

    # First verify backends are registered
    results_all = await router.search_async("class", limit=1)
    print(f"Backends after first search: {list(router._backends.keys())}\n")

    print(f"{'Backend':<20} {'Status':<15} {'Count':<6} First Result")
    print("-" * 80)

    for backend_name, query in BACKEND_QUERIES.items():
        result = await check_backend(router, backend_name, query)
        status = result["status"]
        count = result["count"]
        first = result["first_result"] or ""
        print(f"{backend_name:<20} {status:<15} {count:<6} {first}")

    print("-" * 80)
    print("\nDone.")


if __name__ == "__main__":
    asyncio.run(main())