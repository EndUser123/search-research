#!/usr/bin/env python3
"""Read-only telemetry summarizer for agentic_reliability_telemetry.jsonl.

Emits counts by gate/event, recent examples, first/last seen timestamps,
decision values, and session/terminal grouping. No mutation. No policy change.

Phase 3 of the /go reliability ladder — read-only calibration tool.
"""

from __future__ import annotations

import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

TELEMETRY_LOG = Path("P:/.claude/state/shared/agentic_reliability_telemetry.jsonl")


def read_events(path: Path = TELEMETRY_LOG) -> list[dict[str, Any]]:
    """Read all events from the telemetry JSONL file."""
    if not path.exists():
        print(f"Telemetry log not found: {path}")
        return []
    events: list[dict[str, Any]] = []
    try:
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line:
                events.append(json.loads(line))
    except (OSError, json.JSONDecodeError) as exc:
        print(f"Error reading telemetry log: {exc}")
    return events


def summarize_events(events: list[dict[str, Any]]) -> None:
    """Print a structured summary of telemetry events."""
    if not events:
        print("No telemetry events found.")
        return

    # Basic counts
    total = len(events)
    print(f"Total telemetry events: {total}")
    print()

    # By category
    cat_counts = Counter(e.get("category", "unknown") for e in events)
    print("=== By category ===")
    for cat, count in cat_counts.most_common():
        print(f"  {cat:>30s}: {count}")
    print()

    # By gate
    gate_counts = Counter(e.get("gate", "unknown") for e in events)
    print("=== By gate ===")
    for gate, count in gate_counts.most_common():
        print(f"  {gate:>30s}: {count}")
    print()

    # By event name (top 20)
    event_counts = Counter(e.get("event", "unknown") for e in events)
    print("=== By event name (top 20) ===")
    for event, count in event_counts.most_common(20):
        print(f"  {event:>40s}: {count}")
    print()

    # By decision value
    decision_counts = Counter(e.get("decision", "no_decision") for e in events)
    print("=== By decision ===")
    for decision, count in decision_counts.most_common():
        print(f"  {decision:>30s}: {count}")
    print()

    # First and last timestamps
    timestamps = [e.get("ts") for e in events if e.get("ts")]
    if timestamps:
        timestamps.sort()
        print(f"  First event: {timestamps[0]}")
        print(f"  Last event:  {timestamps[-1]}")
        print()

    # Time range
    if len(timestamps) >= 2:
        try:
            first = datetime.fromisoformat(timestamps[0])
            last = datetime.fromisoformat(timestamps[-1])
            delta = last - first
            print(f"  Span: {delta}")
        except (ValueError, TypeError):
            pass
        print()

    # Per-category detail
    print("=== Per-category detail ===")
    categories = sorted(set(e.get("category", "") for e in events if e.get("category")))
    for cat in categories:
        cat_events = [e for e in events if e.get("category") == cat]
        gate_cnt = Counter(e.get("gate", "") for e in cat_events)
        dec_cnt = Counter(e.get("decision", "") for e in cat_events)
        ev_cnt = Counter(e.get("event", "") for e in cat_events)
        print(f"  [{cat}]")
        print(f"     events: {', '.join(f'{k}={v}' for k,v in ev_cnt.most_common(10))}")
        print(f"     gates: {', '.join(f'{k}={v}' for k,v in gate_cnt.most_common(10))}")
        print(f"     decisions: {', '.join(f'{k}={v}' for k,v in dec_cnt.most_common(10))}")
        # Recent examples (last 3)
        for e in cat_events[-3:]:
            extra = e.get("extra", {})
            print(f"     example: {e.get('event','')} | ts={e.get('ts','')[:19]} | extra={json.dumps(extra, default=str)[:100]}")
        print()

    # Extra fields analysis
    print("=== Extra fields analysis ===")
    extra_keys: Counter[str] = Counter()
    for e in events:
        extra = e.get("extra", {})
        if isinstance(extra, dict):
            extra_keys.update(extra.keys())
    if extra_keys:
        print(f"  Extra keys seen: {', '.join(f'{k}' for k in sorted(extra_keys))}")


def main() -> int:
    events = read_events()
    summarize_events(events)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
