#!/usr/bin/env python3
"""
Error Search Utility - Find hook errors quickly.

Usage:
    python find_errors.py                    # Show last 10 errors
    python find_errors.py --tool TaskCreate  # Filter by tool name
    python find_errors.py --type PostToolUse # Filter by hook type
    python find_errors.py --last 20          # Show last N errors
    python find_errors.py --since 1h         # Errors from last hour
    python find_errors.py --all              # Search all log sources
"""

import argparse
import json
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

# Log file locations
LOG_DIR = Path(r"P:\.claude\hooks\logs\diagnostics")
ERROR_LOG = LOG_DIR / "cc_errors.jsonl"
INVOCATION_LOG = LOG_DIR / "hook_invocations.jsonl"


def parse_duration(s: str) -> timedelta:
    """Parse duration string like '1h', '30m', '2d'."""
    match = re.match(r"(\d+)([hmds])", s.lower())
    if not match:
        return timedelta(hours=1)
    value, unit = int(match.group(1)), match.group(2)
    if unit == "h":
        return timedelta(hours=value)
    elif unit == "m":
        return timedelta(minutes=value)
    elif unit == "d":
        return timedelta(days=value)
    elif unit == "s":
        return timedelta(seconds=value)
    return timedelta(hours=1)


def load_jsonl(path: Path) -> list[dict]:
    """Load JSONL file into list of dicts."""
    if not path.exists():
        return []
    entries = []
    for line in path.read_text(encoding="utf-8").strip().split("\n"):
        if line:
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return entries


def search_errors(
    tool_filter: str | None = None,
    type_filter: str | None = None,
    since: timedelta | None = None,
    last_n: int = 10,
    include_invocations: bool = False,
) -> list[dict]:
    """Search error logs with filters."""
    results = []
    cutoff = None
    if since:
        cutoff = datetime.now(UTC) - since

    # Search cc_errors.jsonl
    for entry in load_jsonl(ERROR_LOG):
        # Time filter
        if cutoff:
            ts_str = entry.get("timestamp", "")
            if ts_str:
                try:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    if ts < cutoff:
                        continue
                except ValueError:
                    pass

        # Type filter
        if type_filter:
            error_type = entry.get("error_type", "")
            if type_filter.lower() not in error_type.lower():
                continue

        # Tool filter (check context)
        if tool_filter:
            ctx = entry.get("context", {})
            tool = ctx.get("tool", "") or ctx.get("hook", "")
            if tool_filter.lower() not in tool.lower():
                continue

        entry["_source"] = "cc_errors"
        results.append(entry)

    # Also search hook_invocations for errors
    if include_invocations:
        for entry in load_jsonl(INVOCATION_LOG):
            # Only include entries with errors
            if not entry.get("error") and not entry.get("hook_errors"):
                # Also flag entries with hooks_executed=[] which may indicate crashes
                if entry.get("hooks_executed") != []:
                    continue

            # Time filter
            if cutoff:
                ts_str = entry.get("ts", "")
                if ts_str:
                    try:
                        ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                        if ts < cutoff:
                            continue
                    except ValueError:
                        pass

            # Type filter
            if type_filter:
                hook_type = entry.get("type", "")
                if type_filter.lower() not in hook_type.lower():
                    continue

            # Tool filter
            if tool_filter:
                tool = entry.get("tool", "")
                if tool_filter.lower() not in tool.lower():
                    continue

            entry["_source"] = "hook_invocations"
            results.append(entry)

    # Sort by timestamp (newest first) and limit
    def get_ts(e):
        return e.get("timestamp") or e.get("ts") or ""

    results.sort(key=get_ts, reverse=True)
    return results[:last_n]


def format_error(entry: dict) -> str:
    """Format error entry for display."""
    source = entry.get("_source", "unknown")
    ts = entry.get("timestamp") or entry.get("ts", "???")
    # Truncate timestamp for display
    if len(ts) > 19:
        ts = ts[:19]

    lines = [f"{'=' * 60}"]
    lines.append(f"[{source}] {ts}")

    if source == "cc_errors":
        lines.append(f"  Error Type: {entry.get('error_type', 'N/A')}")
        lines.append(f"  Message: {entry.get('error_message', 'N/A')[:100]}")
        lines.append(f"  Terminal: {entry.get('terminal_id', 'MISSING')}")
        lines.append(f"  Session: {entry.get('claude_session_id', 'MISSING')}")
        if entry.get("user_prompt_preview"):
            lines.append(f"  Prompt: {entry['user_prompt_preview'][:60]}...")
        ctx = entry.get("context", {})
        if ctx:
            lines.append(f"  Context: {ctx}")
    else:
        lines.append(f"  Router: {entry.get('router', 'N/A')}")
        lines.append(f"  Tool: {entry.get('tool', 'N/A')}")
        lines.append(f"  Hooks Executed: {entry.get('hooks_executed', [])}")
        lines.append(f"  Terminal: {entry.get('terminal_id', 'MISSING')}")
        if entry.get("error"):
            lines.append(f"  Error: {entry['error']}")
        if entry.get("hook_errors"):
            lines.append(f"  Hook Errors: {entry['hook_errors']}")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Search hook errors")
    parser.add_argument("--tool", help="Filter by tool name (e.g., TaskCreate)")
    parser.add_argument("--type", help="Filter by hook type (e.g., PostToolUse)")
    parser.add_argument("--last", type=int, default=10, help="Show last N errors")
    parser.add_argument("--since", help="Errors since duration (1h, 30m, 2d)")
    parser.add_argument("--all", action="store_true", help="Search all log sources")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    since = parse_duration(args.since) if args.since else None

    results = search_errors(
        tool_filter=args.tool,
        type_filter=args.type,
        since=since,
        last_n=args.last,
        include_invocations=args.all,
    )

    if args.json:
        print(json.dumps(results, indent=2, default=str))
    else:
        print(f"\nFound {len(results)} errors:\n")
        for entry in results:
            print(format_error(entry))
            print()


if __name__ == "__main__":
    main()
