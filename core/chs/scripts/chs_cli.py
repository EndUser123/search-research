"""CHS v2 Search CLI.

Command-line interface for searching chat history with support for
--global, --project, --limit, and --json flags.

Usage:
    python -m knowledge.systems.chs.v2.scripts.chs_cli "search query"
    python -m knowledge.systems.chs.v2.scripts.chs_cli --global "query"
    python -m knowledge.systems.chs.v2.scripts.chs_cli --project 123 --limit 5 --json "query"
"""

from __future__ import annotations

import argparse
import json
import sys


def format_result_human(result: dict) -> str:
    """Format a search result for human-readable output.

    Args:
        result: Search result dict

    Returns:
        Formatted string
    """
    lines = []
    lines.append(f"  [{result.get('id', 'N/A')}]")
    if "user_content" in result:
        user = result["user_content"][:100]
        lines.append(f"    User: {user}...")
    elif "content" in result:
        content = result["content"][:100]
        lines.append(f"    Content: {content}...")
    if "assistant_content" in result:
        assistant = result["assistant_content"][:100]
        lines.append(f"    Assistant: {assistant}...")
    if "score" in result:
        score = result["score"]
        lines.append(f"    Score: {score:.3f}")
    return "\n".join(lines)


def main() -> int:
    """CHS v2 search CLI main entry point.

    Returns:
        Exit code (0 for success, 1 for error)
    """
    parser = argparse.ArgumentParser(
        description="Search chat history using CHS v2",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='\nExamples:\n  %(prog)s "python error handling"\n  %(prog)s --global "asyncio tutorial"\n  %(prog)s --project 123 --limit 5 "database schema"\n  %(prog)s --json "machine learning"\n        ',
    )
    parser.add_argument("query", nargs="+", help="Search query (one or more words)")
    parser.add_argument(
        "--global",
        dest="global_scope",
        action="store_true",
        help="Search all projects (no project filter)",
    )
    parser.add_argument("--project", type=int, default=None, help="Filter by specific project ID")
    parser.add_argument(
        "--limit", type=int, default=20, help="Maximum number of results (default: 20)"
    )
    parser.add_argument("--json", action="store_true", help="Output results as JSON")
    args = parser.parse_args()
    query = " ".join(args.query)
    if not query.strip():
        print("ERROR: Query cannot be empty", file=sys.stderr)
        return 1
    try:
        from search_research.core.chs.config import Config
        from search_research.core.chs.db import get_connection
        from search_research.core.chs.search import search_turns

        config = Config()
        conn = get_connection(config.db_path)
        results = search_turns(db=conn, query=query, limit=args.limit, query_embedding=None)
        conn.close()
        if not results:
            if args.json:
                print(json.dumps([]))
            else:
                print(f"No results found for: {query}")
            return 0
        if args.json:
            output = []
            for r in results:
                output.append(
                    {
                        "id": r.get("id"),
                        "content": r.get("user_content", r.get("content", "")),
                        "score": r.get("score", 0.0),
                    }
                )
            print(json.dumps(output, ensure_ascii=False, indent=2))
        else:
            print(f"Searching: {query}")
            print(f"Found {len(results)} result(s)\n")
            for i, result in enumerate(results, 1):
                print(f"{i}.")
                print(format_result_human(result))
                print()
        return 0
    except ImportError as e:
        print(f"ERROR: Required module not available: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"ERROR: Search failed: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
