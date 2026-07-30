#!/usr/bin/env python3
"""
DDG search wrapper for subagents on Windows PowerShell.

Solves the Class C quoting hazard: inline `python -c "from ddgs import DDGS;
list(DDGS().text('query'))"` fails when nested quotes collide with PowerShell's
string handling. This script eliminates the problem by moving the Python code
into a file — subagents pass the query as a plain argument.

Usage:
    python P:/.agents/scripts/ddgs_search.py "search query" [--max 10] [--json]
    python P:/.agents/scripts/ddgs_search.py "search query" --site reddit.com
    echo "query via stdin" | python P:/.agents/scripts/ddgs_search.py --stdin --max 5

Output (JSON to stdout):
    [{"title": "...", "href": "...", "body": "..."}, ...]

Exit codes:
    0 = results returned (possibly empty list)
    1 = error (ddgs not installed, network failure, etc.)

Design principles:
    - Single query per invocation (subagents loop for batch)
    - JSON output only (easy to parse, no formatting ambiguity)
    - No workspace module imports (standalone — just stdlib + ddgs)
    - Query is a positional arg (PowerShell-safe: one double-quoted string)
"""
import argparse
import json
import sys


def run_search(query: str, max_results: int = 10, site: str | None = None) -> list[dict]:
    """Run a DDG text search and return structured results."""
    try:
        from ddgs import DDGS
    except ImportError:
        print(json.dumps({"error": "ddgs package not installed. Run: pip install ddgs"}), file=sys.stderr)
        sys.exit(1)

    full_query = f"site:{site} {query}" if site else query

    try:
        results = list(DDGS().text(full_query, max_results=max_results))
    except Exception as e:
        print(json.dumps({"error": f"DDG search failed: {e}"}), file=sys.stderr)
        sys.exit(1)

    # Normalize keys (ddgs sometimes returns 'href', sometimes 'link')
    normalized = []
    for r in results:
        normalized.append({
            "title": r.get("title", ""),
            "href": r.get("href", r.get("link", "")),
            "body": r.get("body", ""),
        })
    return normalized


def main():
    parser = argparse.ArgumentParser(
        description="DDG search wrapper for PowerShell-safe subagent use",
    )
    parser.add_argument(
        "query",
        nargs="?",
        help="Search query (use --stdin for piped input)",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read query from stdin instead of positional arg",
    )
    parser.add_argument(
        "--max",
        type=int,
        default=10,
        help="Max results (default: 10)",
    )
    parser.add_argument(
        "--site",
        type=str,
        default=None,
        help="Restrict to site (e.g., reddit.com, news.ycombinator.com)",
    )
    parser.add_argument(
        "--text",
        action="store_true",
        help="Output as plain text instead of JSON (one result per line)",
    )

    args = parser.parse_args()

    if args.stdin:
        query = sys.stdin.read().strip()
    elif args.query:
        query = args.query
    else:
        parser.error("Provide a query as positional arg or use --stdin")

    results = run_search(query, max_results=args.max, site=args.site)

    if args.text:
        for r in results:
            print(f"TITLE: {r['title']}")
            print(f"URL:   {r['href']}")
            print(f"BODY:  {r['body'][:200]}")
            print()
    else:
        print(json.dumps(results, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
