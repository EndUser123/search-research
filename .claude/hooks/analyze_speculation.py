#!/usr/bin/env python3
"""
analyze_speculation.py - Analyze speculation gate violations

Usage:
    python analyze_speculation.py [--days N] [--detail]
"""

import argparse
import json
import sqlite3
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
DB_FILE = HOOKS_DIR / "speculation_violations.sqlite"
LOGS_DIR = HOOKS_DIR / "logs"


# Terminal-scoped log files for multi-terminal isolation
def get_constructional_blocks_files() -> list[Path]:
    """Get all terminal-scoped constructional_blocks log files."""
    pattern = "constructional_blocks_*.jsonl"
    return sorted(LOGS_DIR.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)


def analyze_sqlite(days: int, show_detail: bool):
    """Analyze SQLite database."""
    if not DB_FILE.exists():
        print(f"  No SQLite data: {DB_FILE}")
        return

    conn = sqlite3.connect(str(DB_FILE))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    cursor = conn.execute(
        "SELECT timestamp, violation_types, snippet FROM violations WHERE timestamp > ? ORDER BY timestamp DESC",
        (cutoff,),
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print(f"  No violations in last {days} days")
        return

    print(f"  Total violations: {len(rows)}")

    # Count by type
    type_counts = Counter()
    for _, types_json, _ in rows:
        try:
            types = json.loads(types_json)
            for t in types:
                type_counts[t] += 1
        except:
            pass

    print("\n  By Type:")
    for vtype, count in type_counts.most_common():
        print(f"    {vtype}: {count}")

    if show_detail:
        print("\n  Recent Violations:")
        for ts, types_json, snippet in rows[:5]:
            types = json.loads(types_json) if types_json else []
            print(f"    [{ts[:19]}] {', '.join(types)}")
            print(f"      {snippet[:80]}...")
            print()


def analyze_jsonl(days: int, show_detail: bool):
    """Analyze JSONL log entries from constructional_blocks."""
    jsonl_files = get_constructional_blocks_files()
    if not jsonl_files:
        print(f"  No JSONL data: {LOGS_DIR / 'constructional_blocks_*.jsonl'}")
        return

    cutoff = datetime.now() - timedelta(days=days)
    entries = []

    for jsonl_file in jsonl_files:
        try:
            with open(jsonl_file) as f:
                for line in f:
                    try:
                        entry = json.loads(line)
                        if entry.get("hook") == "speculation_gate":
                            ts = datetime.fromisoformat(entry["timestamp"])
                            if ts > cutoff:
                                entries.append(entry)
                    except:
                        pass
        except OSError:
            pass  # Skip files that can't be read

    if not entries:
        print("  No speculation_gate entries in constructional_blocks.jsonl")
        return

    print(f"  Entries in constructional_blocks: {len(entries)}")

    # Count by reason prefix
    reason_counts = Counter()
    for e in entries:
        reason = e.get("reason", "")
        # Extract type from "TYPE: detail" format
        if ":" in reason:
            reason_type = reason.split(":")[0]
            reason_counts[reason_type] += 1

    print("\n  By Reason Type:")
    for rtype, count in reason_counts.most_common():
        print(f"    {rtype}: {count}")


def calculate_compliance_rate(days: int) -> tuple[int, int, float]:
    """Calculate compliance rate for escalation analysis."""
    if not DB_FILE.exists():
        return 0, 0, 1.0

    conn = sqlite3.connect(str(DB_FILE))
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    cursor = conn.execute("SELECT COUNT(*) FROM violations WHERE timestamp > ?", (cutoff,))
    violations = cursor.fetchone()[0]
    conn.close()

    # Estimate total diagnostic responses (rough heuristic)
    # In absence of true total, we use violations as signal
    # Low violations = high compliance
    if violations == 0:
        return 0, 100, 1.0  # Assume 100% compliance if no violations
    elif violations < 5:
        return violations, 50, 0.90  # Assume 90% compliance
    elif violations < 20:
        return violations, 100, 0.80  # Assume 80% compliance
    else:
        return violations, violations * 2, 0.50  # Assume 50% compliance


def main():
    parser = argparse.ArgumentParser(description="Analyze speculation gate violations")
    parser.add_argument("--days", type=int, default=7, help="Analysis period")
    parser.add_argument("--detail", action="store_true", help="Show detailed violations")
    args = parser.parse_args()

    print("=" * 50)
    print("SPECULATION GATE ANALYSIS")
    print(f"Period: Last {args.days} days")
    print("=" * 50)

    print("\n## SQLite Database")
    analyze_sqlite(args.days, args.detail)

    print("\n## JSONL Integration")
    analyze_jsonl(args.days, args.detail)

    print("\n## Compliance Estimate")
    violations, total_est, rate = calculate_compliance_rate(args.days)
    print(f"  Violations: {violations}")
    print(f"  Est. Compliance: {rate:.0%}")
    if rate < 0.70:
        print("  ⚠ BELOW THRESHOLD - Consider escalation")
    else:
        print("  ✓ Within acceptable range")

    print("\n## Violation Types Explanation")
    print("  SPECULATION_MARKER: Used 'likely', 'probably', etc. without evidence")
    print("  HIGH_CONFIDENCE_NO_TIER: Claimed >75% confidence without [Tier N] citation")
    print("  ROOT_CAUSE_NO_SOURCE: Claimed root cause without Read() or file:line")
    print("  PREMATURE_CONFIRMATION: Marked hypothesis ✅ without verification")


if __name__ == "__main__":
    main()
