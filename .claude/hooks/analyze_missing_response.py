#!/usr/bin/env python3
"""
Analyze Stop_router diagnostic logs to detect missing response field.

Usage:
    python analyze_missing_response.py

Checks:
- How often response field is missing
- How often response field is empty
- What other data is present when response is missing
"""

import json
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
SESSION_DATA = HOOKS_DIR / "session_data"


def analyze_today():
    """Analyze today's decision log."""
    today = datetime.now().strftime("%Y-%m-%d")
    log_path = SESSION_DATA / f"hook_decisions_{today}.jsonl"

    if not log_path.exists():
        print(f"❌ No log file for today: {log_path}")
        return

    print(f"📊 Analyzing: {log_path}")
    print("=" * 80)

    diagnostic_entries = []
    router_starts = []
    hook_executions = []

    with open(log_path, encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            entry = json.loads(line)

            if entry.get("hook_name") == "Stop_router":
                if entry.get("decision") == "diagnostic":
                    diagnostic_entries.append(entry)
                elif entry.get("decision") == "start":
                    router_starts.append(entry)
            else:
                hook_executions.append(entry)

    print("\n📈 Summary:")
    print(f"  Router start entries: {len(router_starts)}")
    print(f"  Diagnostic entries (missing response): {len(diagnostic_entries)}")
    print(f"  Hook executions: {len(hook_executions)}")
    print(f"  Total Stop_router calls: {len(router_starts)}")

    if diagnostic_entries:
        print(f"\n⚠️  Missing response detected in {len(diagnostic_entries)} calls")
        print("\n🔍 Diagnostic Details:")

        reasons = Counter(e["reason"] for e in diagnostic_entries)
        for reason, count in reasons.most_common():
            print(f"  {reason}: {count}x")

        # Show available data keys when response is missing
        keys_seen = defaultdict(int)
        for entry in diagnostic_entries:
            claim_snippet = entry.get("claim_snippet", "")
            if claim_snippet.startswith("dict_keys"):
                # Parse the keys list
                print(f"\n  Available keys when response missing: {claim_snippet}")
                keys_seen[claim_snippet] += 1

        # Show recent examples
        print("\n📝 Recent diagnostic entries (last 5):")
        for entry in diagnostic_entries[-5:]:
            ts = entry.get("timestamp", "unknown")
            reason = entry.get("reason", "unknown")
            keys = entry.get("claim_snippet", "unknown")
            print(f"  {ts}: {reason}")
            print(f"    Keys present: {keys}")

    # Check response_length distribution
    response_lengths = [e.get("response_length", 0) for e in hook_executions]
    if response_lengths:
        print("\n📊 Response length distribution for hook executions:")
        zero_count = sum(1 for l in response_lengths if l == 0)
        nonzero_count = len(response_lengths) - zero_count
        print(f"  Zero-length responses: {zero_count}/{len(response_lengths)}")
        print(f"  Non-zero responses: {nonzero_count}/{len(response_lengths)}")

        if nonzero_count > 0:
            nonzero_lengths = [l for l in response_lengths if l > 0]
            print(f"  Min non-zero length: {min(nonzero_lengths)}")
            print(f"  Max non-zero length: {max(nonzero_lengths)}")
            print(f"  Avg non-zero length: {sum(nonzero_lengths) / len(nonzero_lengths):.0f}")

    print("\n" + "=" * 80)


def analyze_recent_days(days=7):
    """Analyze last N days of logs."""
    print(f"\n📅 Analyzing last {days} days:")
    print("=" * 80)

    total_diagnostics = 0
    total_router_calls = 0

    from datetime import timedelta
    today = datetime.now()

    for i in range(days):
        date = today - timedelta(days=i)
        date_str = date.strftime("%Y-%m-%d")
        log_path = SESSION_DATA / f"hook_decisions_{date_str}.jsonl"

        if not log_path.exists():
            continue

        diagnostics = 0
        router_calls = 0

        with open(log_path, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                entry = json.loads(line)

                if entry.get("hook_name") == "Stop_router":
                    if entry.get("decision") == "start":
                        router_calls += 1
                    elif entry.get("decision") == "diagnostic":
                        diagnostics += 1

        if router_calls > 0:
            print(f"  {date_str}: {diagnostics:3d} diagnostics / {router_calls:3d} calls ({diagnostics/router_calls*100:.1f}% missing)")
            total_diagnostics += diagnostics
            total_router_calls += router_calls

    if total_router_calls > 0:
        print(f"\n  TOTAL: {total_diagnostics} diagnostics / {total_router_calls} calls ({total_diagnostics/total_router_calls*100:.1f}% missing)")

    print("=" * 80)


if __name__ == "__main__":
    analyze_today()
    analyze_recent_days(7)
