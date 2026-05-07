#!/usr/bin/env python3
"""
CKS Daemon Discovery - Simplified Direct Query Interface
========================================================

Provides query_cks_daemon() function for hooks to query CKS
without requiring a running daemon. Uses CKS unified interface directly.

This is a simplified replacement for the full daemon architecture,
designed for hook integration where daemon overhead isn't justified.
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add CSF src to path
_csf_src = Path("P:\\\\__csf/src")
if str(_csf_src) not in sys.path:
    sys.path.insert(0, str(_csf_src))


def query_cks_daemon(query: str, limit: int = 5) -> dict | None:
    """Query CKS for relevant entries.

    Args:
        query: Search query text
        limit: Maximum number of results to return

    Returns:
        Dict with "results" key containing list of CKS entries, or None on error
        Each entry is a dict with: title, content, entry_type, metadata

    Example:
        response = query_cks_daemon("git multi-terminal race condition", limit=1)
        if response:
            for entry in response["results"]:
                print(entry["title"])
                print(entry["content"][:100])
    """
    try:
        from cks.unified import CKS

        with CKS() as cks:
            # Search CKS
            results = cks.search(query, limit=limit)

            # Convert to expected format
            formatted_results = []
            for r in results:
                # Handle both dict and object results
                if isinstance(r, dict):
                    formatted_results.append(r)
                else:
                    # Convert object to dict
                    formatted_results.append(
                        {
                            "title": getattr(r, "title", "Unknown"),
                            "content": getattr(r, "content", ""),
                            "entry_type": getattr(r, "entry_type", "unknown"),
                            "metadata": getattr(r, "metadata", {}),
                        }
                    )

            return {"results": formatted_results}

    except Exception as e:
        # Fail silently - CKS is optional for hooks
        if __debug__:
            print(f"[CKS Discovery] Query failed: {e}", file=sys.stderr)
        return None


# Test function when run directly
if __name__ == "__main__":
    # Test query
    test_queries = [
        "git multi-terminal race condition",
        "questioning patterns",
        "working principles",
    ]

    print("CKS Discovery Test")
    print("=" * 70)

    for query in test_queries:
        print(f'\nQuery: "{query}"')
        response = query_cks_daemon(query, limit=2)

        if response:
            results = response.get("results", [])
            print(f"Found {len(results)} results")

            for i, r in enumerate(results[:1], 1):
                title = r.get("title", "No title")
                content = r.get("content", "")[:150]
                print(f"  {i}. {title}")
                print(f"     {content}...")
        else:
            print("  No results or error")
