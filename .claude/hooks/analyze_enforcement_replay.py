#!/usr/bin/env python3
from __future__ import annotations

"""
Replay analyzer for enforcement quality metrics.

Inputs:
- P:/.claude/hooks/session_data/enforcement_events.jsonl (or temp fallback)
- P:/.claude/hooks/session_data/hook_decisions_YYYY-MM-DD.jsonl
"""

import argparse
import json
import math
import tempfile
from collections import Counter, defaultdict
from datetime import UTC, datetime, timedelta
from pathlib import Path

WARNABLE_CATEGORIES = {"evidence_claims", "investigation_required"}


def _parse_ts(value: str) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=UTC)
        return dt
    except Exception:
        return None


def _event_log_candidates() -> list[Path]:
    return [
        Path("P:/.claude/hooks/session_data/enforcement_events.jsonl"),
        Path(tempfile.gettempdir()) / "claude_hooks" / "enforcement_events.jsonl",
    ]


def _load_events(days: int) -> list[dict[str, object]]:
    cutoff = datetime.now(UTC) - timedelta(days=days)
    for path in _event_log_candidates():
        if not path.exists():
            continue
        events: list[dict[str, object]] = []
        try:
            with open(path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    ts = _parse_ts(str(entry.get("timestamp", "")))
                    if ts is None or ts < cutoff:
                        continue
                    if isinstance(entry, dict):
                        events.append(entry)
            return events
        except Exception:
            continue
    return []


def _current_terminal_id() -> str | None:
    try:
        from __lib.terminal_detection import resolve_terminal_key

        return resolve_terminal_key({})
    except Exception:
        return None


def _filter_terminal(events: list[dict[str, object]], terminal_only: bool) -> list[dict[str, object]]:
    if not terminal_only:
        return events
    terminal_id = _current_terminal_id()
    if not terminal_id:
        return events
    filtered = []
    for e in events:
        term = str(e.get("terminal_key", ""))
        if term == terminal_id:
            filtered.append(e)
    return filtered


def _pct(n: int, d: int) -> float:
    if d <= 0:
        return 0.0
    return (n / d) * 100.0


def _load_router_latencies(days: int) -> dict[str, list[float]]:
    decisions_dir = Path("P:/.claude/hooks/session_data")
    if not decisions_dir.exists():
        return {"write_router": [], "stop_router": []}
    cutoff = datetime.now(UTC) - timedelta(days=days)
    buckets: dict[str, list[float]] = {"write_router": [], "stop_router": []}
    for file_path in sorted(decisions_dir.glob("hook_decisions_*.jsonl")):
        try:
            with open(file_path, encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except Exception:
                        continue
                    ts = _parse_ts(str(entry.get("timestamp", "")))
                    if ts is None or ts < cutoff:
                        continue
                    latency = entry.get("latency_ms")
                    if not isinstance(latency, (int, float)):
                        continue
                    hook_name = str(entry.get("hook_name", ""))
                    # Stop router emits hook-level execution latencies.
                    if hook_name:
                        buckets["stop_router"].append(float(latency))
        except Exception:
            continue
    return buckets


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    pos = (len(s) - 1) * q
    lo = int(math.floor(pos))
    hi = int(math.ceil(pos))
    if lo == hi:
        return round(s[lo], 2)
    frac = pos - lo
    return round(s[lo] * (1.0 - frac) + s[hi] * frac, 2)


def render(days: int, terminal_only: bool, show_all: bool) -> int:
    del show_all  # Reserved for future per-terminal breakout.
    events = _load_events(days)
    events = _filter_terminal(events, terminal_only)
    if not events:
        print("Enforcement Replay")
        print("-" * 40)
        print("No enforcement events found in selected window.")
        print("Collects from: P:/.claude/hooks/session_data/enforcement_events.jsonl")
        return 0

    violations = [e for e in events if e.get("event") == "violation"]
    autofix = [e for e in events if e.get("event") == "autofix"]
    warn_count = sum(1 for e in violations if str(e.get("mode")) == "warn")
    block_count = sum(1 for e in violations if str(e.get("mode")) == "block")
    total_violations = len(violations)

    # Counterfactual "without ladder" approximation:
    # every warn in a warnable category would have been an immediate block.
    warnable_warn = sum(
        1
        for e in violations
        if str(e.get("mode")) == "warn" and str(e.get("category")) in WARNABLE_CATEGORIES
    )
    baseline_blocks_without_ladder = block_count + warnable_warn

    by_category = Counter(str(e.get("category", "unknown")) for e in violations)
    by_hook = Counter(str(e.get("hook", "unknown")) for e in violations)
    scope_counts: dict[str, int] = defaultdict(int)
    for e in violations:
        scope_counts[str(e.get("scope", "unknown"))] += 1

    autofix_attempts = len(autofix)
    autofix_success = sum(1 for e in autofix if bool(e.get("success")))

    latencies = _load_router_latencies(days)
    stop_lat = latencies.get("stop_router", [])

    print("Enforcement Replay")
    print("-" * 40)
    print(f"Window: last {days} day(s)")
    print(f"Violations: {total_violations}")
    print(
        f"Before ladder (simulated immediate-block): {baseline_blocks_without_ladder} "
        f"({ _pct(baseline_blocks_without_ladder, total_violations):.1f}% of violations)"
    )
    print(
        f"After ladder (actual): blocks={block_count}, warns={warn_count} "
        f"(block rate {_pct(block_count, total_violations):.1f}%)"
    )
    print(f"Ladder deflected blocks: {warnable_warn}")
    print(
        f"Autofix success: {autofix_success}/{autofix_attempts} "
        f"({_pct(autofix_success, autofix_attempts):.1f}%)"
    )
    print(f"Scopes observed: {len(scope_counts)}")

    print("\nTop categories:")
    for cat, cnt in by_category.most_common(6):
        print(f"  - {cat}: {cnt}")

    print("\nTop hooks:")
    for hk, cnt in by_hook.most_common(6):
        print(f"  - {hk}: {cnt}")

    print("\nLatency (hook execution, from stop router decision logs):")
    print(f"  - samples: {len(stop_lat)}")
    print(f"  - p50: {_percentile(stop_lat, 0.50)} ms")
    print(f"  - p95: {_percentile(stop_lat, 0.95)} ms")

    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Replay enforcement metrics")
    parser.add_argument("--days", type=int, default=7, help="Lookback window in days")
    parser.add_argument("--terminal", action="store_true", help="Current terminal only")
    parser.add_argument("--all", dest="show_all", action="store_true", help="Reserved for future breakdown")
    args = parser.parse_args()
    return render(days=args.days, terminal_only=args.terminal, show_all=args.show_all)


if __name__ == "__main__":
    raise SystemExit(main())
