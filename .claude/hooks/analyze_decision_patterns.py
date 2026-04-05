#!/usr/bin/env python3
"""Analyze decision pattern logs from production usage.

This script reads decision_patterns.jsonl and generates:
1. Distribution of decision types (validates 86%/10%/3%/2% assumptions)
2. Option extraction rates
3. Response length statistics
4. Recommendations for pattern tuning

Usage:
    python P:/claude/hooks/analyze_decision_patterns.py              # Last 1000 entries
    python P:/claude/hooks/analyze_decision_patterns.py --days 7    # Last 7 days
    python P:/claude/hooks/analyze_decision_patterns.py --full     # All entries
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path


def load_logs(log_file: Path, limit: int = 0) -> list[dict]:
    """Load decision pattern logs from JSONL file."""
    if not log_file.exists():
        print(f"❌ Log file not found: {log_file}")
        print("   Logs will appear after you use the next step system in production.")
        return []

    entries = []
    with open(log_file, encoding="utf-8") as f:
        for line_num, line in enumerate(f, 1):
            if limit and line_num > limit:
                break
            try:
                entry = json.loads(line.strip())
                entries.append(entry)
            except json.JSONDecodeError:
                continue

    return entries


def analyze_distribution(entries: list[dict]) -> dict[str, int]:
    """Analyze distribution of decision types."""
    counter = Counter(entry.get("decision_type", "unknown") for entry in entries)
    return dict(counter)


def analyze_option_rates(entries: list[dict]) -> dict[str, dict]:
    """Analyze option extraction rates by decision type."""
    by_type: dict[str, list[int]] = {}

    for entry in entries:
        dtype = entry.get("decision_type", "unknown")
        num_opts = entry.get("num_options", 0)

        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(num_opts)

    # Calculate statistics per type
    stats = {}
    for dtype, options_list in by_type.items():
        total = len(options_list)
        with_options = sum(1 for opts in options_list if opts > 0)
        avg_options = sum(options_list) / total if total > 0 else 0

        stats[dtype] = {
            "total": total,
            "with_options": with_options,
            "rate": with_options / total if total > 0 else 0,
            "avg_options": avg_options,
        }

    return stats


def analyze_response_lengths(entries: list[dict]) -> dict[str, dict]:
    """Analyze response length statistics by decision type."""
    by_type: dict[str, list[int]] = {}

    for entry in entries:
        dtype = entry.get("decision_type", "unknown")
        length = entry.get("response_length", 0)

        if dtype not in by_type:
            by_type[dtype] = []
        by_type[dtype].append(length)

    # Calculate statistics per type
    stats = {}
    for dtype, lengths in by_type.items():
        if lengths:
            stats[dtype] = {
                "min": min(lengths),
                "max": max(lengths),
                "avg": sum(lengths) / len(lengths),
                "median": sorted(lengths)[len(lengths) // 2],
            }

    return stats


def compare_to_expectations(distribution: dict[str, int], total: int) -> dict[str, dict]:
    """Compare actual distribution to expected from analysis.

    Expected (from 907 conversation analysis):
    - explicit_options: 86%
    - question_ending: 10%
    - next_steps_section: 3%
    - direction_request: 2%
    """
    expected = {
        "explicit_options": 0.86,
        "question_ending": 0.10,
        "next_steps_section": 0.03,
        "direction_request": 0.02,
    }

    comparison = {}
    for dtype, expected_pct in expected.items():
        actual_count = distribution.get(dtype, 0)
        actual_pct = actual_count / total if total > 0 else 0
        diff = actual_pct - expected_pct

        comparison[dtype] = {
            "expected_pct": expected_pct * 100,
            "actual_pct": actual_pct * 100,
            "diff_pct": diff * 100,
            "diff_count": int(diff * total),
        }

    return comparison


def print_report(entries: list[dict]) -> None:
    """Print comprehensive analysis report."""
    if not entries:
        return

    total = len(entries)
    print(f"\n{'='*80}")
    print("DECISION PATTERN ANALYSIS")
    print(f"{'='*80}")
    print(f"\n📊 Data Source: {total} log entries")

    # 1. Distribution Analysis
    print("\n🎯 DECISION TYPE DISTRIBUTION")
    distribution = analyze_distribution(entries)
    for dtype, count in sorted(distribution.items(), key=lambda x: x[1], reverse=True):
        pct = count / total * 100
        print(f"  {dtype}: {count} ({pct:.1f}%)")

    # 2. Comparison to Expected
    print("\n📈 ACTUAL vs EXPECTED (from 907 conversation analysis)")
    comparison = compare_to_expectations(distribution, total)
    for dtype, stats in comparison.items():
        expected = stats["expected_pct"]
        actual = stats["actual_pct"]
        diff = stats["diff_pct"]

        status = "✓" if abs(diff) < 5 else "⚠️"  # Within 5% = good
        print(f"  {status} {dtype}:")
        print(f"      Expected: {expected:.1f}%, Actual: {actual:.1f}%, Diff: {diff:+.1f}%")

    # 3. Option Extraction Rates
    print("\n🔧 OPTION EXTRACTION RATES")
    option_stats = analyze_option_rates(entries)
    for dtype, stats in sorted(option_stats.items(), key=lambda x: x[1]["rate"], reverse=True):
        rate = stats["rate"] * 100
        avg = stats["avg_options"]
        print(f"  {dtype}: {rate:.1f}% with options (avg {avg:.1f} options)")

    # 4. Response Length Analysis
    print("\n📏 RESPONSE LENGTH BY DECISION TYPE")
    length_stats = analyze_response_lengths(entries)
    for dtype, stats in sorted(length_stats.items(), key=lambda x: x[1]["avg"], reverse=True):
        print(f"  {dtype}:")
        print(f"      Min: {stats['min']}, Max: {stats['max']}, Avg: {stats['avg']:.0f}, Median: {stats['median']:.0f}")

    # 5. Recommendations
    print("\n💡 RECOMMENDATIONS")

    # Check if distributions match expectations
    significant_diffs = [
        dtype for dtype, stats in comparison.items()
        if abs(stats["diff_pct"]) > 10  # More than 10% difference
    ]

    if significant_diffs:
        print("  ⚠️  Decision types with significant deviation from expected:")
        for dtype in significant_diffs:
            stats = comparison[dtype]
            print(f"      • {dtype}: {stats['diff_pct']:+.1f}% (expected {stats['expected_pct']:.1f}%)")
        print("\n  Consider adjusting regex patterns for these types.")
    else:
        print("  ✓ All decision types within expected range.")

    # Check for low extraction rates
    low_extraction = [
        dtype for dtype, stats in option_stats.items()
        if stats["rate"] < 0.5 and stats["total"] >= 10  # Less than 50% and sufficient data
    ]

    if low_extraction:
        print("\n  ⚠️  Decision types with low option extraction rates:")
        for dtype in low_extraction:
            stats = option_stats[dtype]
            print(f"      • {dtype}: {stats['rate']*100:.1f}% (only {stats['with_options']}/{stats['total']} had options)")
        print("\n  Review extract_menu_options() logic for these types.")
    else:
        print("  ✓ Option extraction rates look good.")

    print(f"\n{'='*80}\n")


def filter_by_date(entries: list[dict], days: int) -> list[dict]:
    """Filter entries to last N days."""
    if days <= 0:
        return entries

    cutoff = datetime.utcnow() - timedelta(days=days)
    filtered = []

    for entry in entries:
        try:
            timestamp = datetime.fromisoformat(entry.get("timestamp", ""))
            if timestamp >= cutoff:
                filtered.append(entry)
        except (ValueError, TypeError):
            continue

    return filtered


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Analyze decision pattern logs")
    parser.add_argument(
        "--limit",
        type=int,
        default=1000,
        help="Limit to N most recent entries (default: 1000, 0 = all)",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=0,
        help="Only analyze entries from last N days (default: 0 = all time)",
    )
    parser.add_argument(
        "--full",
        action="store_true",
        help="Analyze all entries (same as --limit 0)",
    )

    args = parser.parse_args()

    log_file = Path(__file__).resolve().parent.parent / "state" / "logs" / "decision_patterns.jsonl"

    limit = 0 if args.full else args.limit
    entries = load_logs(log_file, limit)

    if args.days > 0:
        entries = filter_by_date(entries, args.days)
        print(f"Filtered to last {args.days} days: {len(entries)} entries")

    print_report(entries)
