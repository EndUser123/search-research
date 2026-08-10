"""Session tracer — lightweight local observability from events.jsonl.

Reads the structured event stream that Grok Build already captures and
produces a trace summary: tool calls by type, duration estimates, failure
rates, and a timeline view. No external service required.

Usage:
    python session_trace.py <session-id> [--timeline] [--by-tool] [--failures]

The trace data already exists in events.jsonl — this tool makes it queryable.
This is the local alternative to Langfuse; if you later adopt Langfuse, the
same data can be exported to its trace format.
"""
from __future__ import annotations

import json
import sys
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict, Counter


def parse_ts(ts_str: str) -> datetime:
    """Parse ISO 8601 timestamp."""
    return datetime.fromisoformat(ts_str.replace("Z", "+00:00"))


def load_events(session_id: str) -> list[dict]:
    """Load events from a session's events.jsonl."""
    # Try multiple encoded-cwd patterns
    candidates = [
        Path(f"C:/Users/brsth/.grok/sessions/P%3A%5C/{session_id}/events.jsonl"),
        Path(f"C:/Users/brsth/.grok/sessions/P%3A/{session_id}/events.jsonl"),
    ]
    for p in candidates:
        if p.exists():
            events = []
            with open(p, encoding="utf-8") as f:
                for line in f:
                    try:
                        events.append(json.loads(line))
                    except json.JSONDecodeError:
                        pass
            return events
    print(f"Error: events.jsonl not found for session {session_id}", file=sys.stderr)
    sys.exit(1)


def build_tool_traces(events: list[dict]) -> list[dict]:
    """Match tool_started and tool_completed events into traces."""
    started = {}  # tool_call_id -> event
    traces = []

    for evt in events:
        etype = evt.get("type", "")
        if etype == "tool_started":
            # Use timestamp as a rough ID (tools don't have explicit IDs in events)
            tool_name = evt.get("tool_name", "unknown")
            ts = evt.get("ts", "")
            key = f"{tool_name}@{ts}"
            started[key] = evt
        elif etype == "tool_completed":
            tool_name = evt.get("tool_name", "unknown")
            ts = evt.get("ts", "")
            exit_code = evt.get("exit_code", evt.get("result", {}).get("exit_code"))

            # Match to the most recent started event for this tool
            best_key = None
            best_ts = None
            for key, sevt in started.items():
                if key.startswith(tool_name + "@"):
                    sevt_ts = sevt.get("ts", "")
                    if sevt_ts <= ts:  # started before completed
                        if best_ts is None or sevt_ts > best_ts:
                            best_key = key
                            best_ts = sevt_ts

            if best_key:
                sevt = started.pop(best_key)
                try:
                    duration = (parse_ts(ts) - parse_ts(best_ts)).total_seconds()
                except (ValueError, TypeError):
                    duration = None

                traces.append({
                    "tool": tool_name,
                    "started_at": best_ts,
                    "completed_at": ts,
                    "duration_s": round(duration, 2) if duration else None,
                    "exit_code": exit_code,
                    "failed": exit_code is not None and exit_code != 0,
                })

    return traces


def summary_by_tool(traces: list[dict]) -> None:
    """Print tool usage summary."""
    by_tool = defaultdict(list)
    for t in traces:
        by_tool[t["tool"]].append(t)

    print(f"\n{'Tool':<35} {'Calls':>6} {'Failed':>7} {'Avg(s)':>8} {'Max(s)':>8}")
    print("-" * 70)

    for tool in sorted(by_tool, key=lambda t: len(by_tool[t]), reverse=True):
        calls = by_tool[tool]
        count = len(calls)
        failed = sum(1 for c in calls if c["failed"])
        durations = [c["duration_s"] for c in calls if c["duration_s"] is not None]
        avg = sum(durations) / len(durations) if durations else 0
        mx = max(durations) if durations else 0
        print(f"{tool:<35} {count:>6} {failed:>7} {avg:>8.1f} {mx:>8.1f}")


def show_failures(traces: list[dict]) -> None:
    """Print failed tool calls."""
    failures = [t for t in traces if t["failed"]]
    if not failures:
        print("\nNo failed tool calls.")
        return

    print(f"\n{'='*70}")
    print(f"FAILED TOOL CALLS ({len(failures)})")
    print(f"{'='*70}")
    for t in failures:
        print(f"  {t['tool']:<30} exit={t['exit_code']:<4} at {t['completed_at'][:19]}")


def show_timeline(events: list[dict]) -> None:
    """Print a condensed timeline of the session."""
    # Focus on meaningful events (not phase_changed noise)
    meaningful_types = {
        "turn_started", "turn_ended", "tool_started", "tool_completed",
        "mcp_tool_call_started", "mcp_tool_call_completed",
        "mcp_server_connected", "mcp_server_failed",
        "first_token", "loop_started",
    }
    meaningful = [e for e in events if e.get("type") in meaningful_types]

    print(f"\n{'='*70}")
    print(f"SESSION TIMELINE ({len(meaningful)} meaningful events of {len(events)} total)")
    print(f"{'='*70}")

    # Group by turn
    current_turn = None
    turn_tools = []

    for evt in meaningful:
        etype = evt.get("type", "")
        ts = evt.get("ts", "")[:19]

        if etype == "turn_started":
            if current_turn and turn_tools:
                print(f"  Turn {current_turn}: {len(turn_tools)} tool calls")
            current_turn = evt.get("turn", "?")
            turn_tools = []
            print(f"\n[Turn {current_turn}] {ts}")
        elif etype == "tool_started":
            tool = evt.get("tool_name", "?")
            turn_tools.append(tool)
        elif etype == "mcp_tool_call_started":
            tool = evt.get("tool_name", evt.get("server", "?"))
            turn_tools.append(f"mcp:{tool}")
        elif etype == "mcp_server_connected":
            name = evt.get("server", evt.get("name", "?"))
            print(f"  + MCP connected: {name}")
        elif etype == "mcp_server_failed":
            name = evt.get("server", evt.get("name", "?"))
            print(f"  ! MCP FAILED: {name}")

    if current_turn and turn_tools:
        tool_counts = Counter(turn_tools)
        print(f"  Tools used: {dict(tool_counts.most_common())}")


def main():
    parser = argparse.ArgumentParser(description="Session tracer — local observability from events.jsonl")
    parser.add_argument("session_id", help="Session UUID")
    parser.add_argument("--timeline", action="store_true", help="Show session timeline")
    parser.add_argument("--by-tool", action="store_true", help="Show tool usage summary")
    parser.add_argument("--failures", action="store_true", help="Show failed tool calls")
    args = parser.parse_args()

    events = load_events(args.session_id)
    print(f"Loaded {len(events)} events from session {args.session_id[:8]}...")

    # Always show summary stats
    types = Counter(e.get("type", "") for e in events)
    print(f"Event types: {dict(types.most_common(10))}")

    if args.timeline or not (args.by_tool or args.failures):
        show_timeline(events)

    traces = build_tool_traces(events)
    print(f"\nMatched {len(traces)} tool traces")

    if args.by_tool or not (args.timeline or args.failures):
        summary_by_tool(traces)

    if args.failures or not (args.timeline or args.by_tool):
        show_failures(traces)


if __name__ == "__main__":
    main()
