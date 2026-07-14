"""Compatibility wrapper: delegate all research execution to /research."""

from __future__ import annotations

import argparse
import asyncio

from skills.research.orchestration import (
    format_standard_results,
    format_themed_results,
)
from skills.research.orchestration import execute_unified_search as _execute_unified_search


async def execute_unified_search(query: str, **kwargs) -> str:
    kwargs.setdefault("caller", "search-research:/all")
    return await _execute_unified_search(query, **kwargs)


def main(query: str, **kwargs) -> str:
    return asyncio.run(execute_unified_search(query, **kwargs))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Compatibility wrapper for /research (/all).")
    parser.add_argument("query")
    parser.add_argument("--mode", default="auto")
    parser.add_argument("--limit", type=int, default=30)
    parser.add_argument("--min-score", type=float, default=0.5)
    parser.add_argument("--context-threshold", type=int, default=20)
    parser.add_argument("--force-context-filter", action="store_true")
    parser.add_argument("--no-context-filter", action="store_true")
    args = parser.parse_args()
    print(main(args.query, mode=args.mode, limit=args.limit, min_score=args.min_score, context_threshold=args.context_threshold, force_context_filter=args.force_context_filter, no_context_filter=args.no_context_filter))
