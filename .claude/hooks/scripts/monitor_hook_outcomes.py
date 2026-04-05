#!/usr/bin/env python3
"""
monitor_hook_outcomes.py - Outcome-based hook effectiveness metrics

Measures whether hooks are actually changing behavior by tracking
principle violation trends over time from principle-events.jsonl.

Replaces the phantom CKS field metrics (work_type, cks_context_injection)
which measured unimplemented features and always reported 0%.
"""

import argparse
import json
import sys
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path

PRINCIPLE_LOG = Path("P:/.claude/logs/principle-events.jsonl")
TREND_DAYS = 14  # How many days to show in trend chart
BAR_WIDTH = 40  # Max bar width in chars


def load_violations(days: int) -> dict[str, dict[str, int]]:
    """Load violations grouped by date and principle."""
    if not PRINCIPLE_LOG.exists():
        return {}

    cutoff = datetime.now() - timedelta(days=days)
    by_date: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

    for line in PRINCIPLE_LOG.read_text(errors="ignore").splitlines():
        try:
            d = json.loads(line)
            ts_str = d.get("ts", "")
            if not ts_str:
                continue
            ts = datetime.fromisoformat(ts_str[:19])
            if ts < cutoff:
                continue
            date = ts_str[:10]
            principle = d.get("principle", "unknown")
            by_date[date][principle] += 1
        except (json.JSONDecodeError, ValueError):
            continue

    return by_date


def compute_trend(by_date: dict, principle: str) -> str:
    """Compare last 7 days vs prior 7 days to determine trend direction."""
    today = datetime.now().date()
    recent_7 = sum(
        by_date.get(str(today - timedelta(days=i)), {}).get(principle, 0) for i in range(7)
    )
    prior_7 = sum(
        by_date.get(str(today - timedelta(days=i)), {}).get(principle, 0) for i in range(7, 14)
    )
    if prior_7 == 0:
        return "INSUFFICIENT DATA"
    change = (recent_7 - prior_7) / prior_7
    if change < -0.1:
        return f"IMPROVING ({change:+.0%})"
    elif change > 0.1:
        return f"WORSENING ({change:+.0%})"
    else:
        return f"STABLE ({change:+.0%})"


def print_report(days: int) -> int:
    """Print the outcome metrics report. Returns exit code."""
    by_date = load_violations(days * 2)  # Load extra for trend comparison

    if not by_date:
        print("⚠️  No principle-events.jsonl data found")
        print(f"   Expected: {PRINCIPLE_LOG}")
        return 1

    # All dates in trend window
    today = datetime.now().date()
    trend_dates = [str(today - timedelta(days=i)) for i in range(TREND_DAYS - 1, -1, -1)]
    trend_dates_set = set(trend_dates)
    recent_by_date = {d: v for d, v in by_date.items() if d in trend_dates_set}

    # Total counts per principle (in trend window)
    totals: dict[str, int] = defaultdict(int)
    for date_data in recent_by_date.values():
        for p, c in date_data.items():
            totals[p] += c

    print("📊 Hook Outcome Metrics")
    print("=" * 60)
    print(f"Period: Last {TREND_DAYS} days\n")

    if not totals:
        print("✅ No principle violations recorded in this period.")
        return 0

    # Primary trend: context_reuse (most important)
    primary = "context_reuse"
    if primary in totals:
        daily_max = (
            max((recent_by_date.get(d, {}).get(primary, 0) for d in trend_dates), default=1) or 1
        )

        print(f"context_reuse violations ({TREND_DAYS}-day trend):")
        for date in trend_dates:
            count = recent_by_date.get(date, {}).get(primary, 0)
            bar_len = int((count / daily_max) * BAR_WIDTH)
            bar = "█" * bar_len
            print(f"  {date}: {bar:<{BAR_WIDTH}} {count}")

        trend = compute_trend(by_date, primary)
        recent_avg = (
            sum(
                recent_by_date.get(str(today - timedelta(days=i)), {}).get(primary, 0)
                for i in range(7)
            )
            / 7
        )
        prior_avg = (
            sum(
                by_date.get(str(today - timedelta(days=i)), {}).get(primary, 0)
                for i in range(7, 14)
            )
            / 7
        )
        print(f"\n  Trend: {trend}")
        print(f"  7-day avg: {recent_avg:.1f}/day | prior 7-day avg: {prior_avg:.1f}/day")
        print()

    # All principle totals
    print("All principles (last 14 days):")
    for principle, count in sorted(totals.items(), key=lambda x: -x[1]):
        bar_len = int((count / max(totals.values())) * 20)
        bar = "█" * bar_len
        print(f"  {count:4d}  {bar:<20}  {principle}")

    # Health assessment
    print()
    cr_total = totals.get("context_reuse", 0)
    trend_str = compute_trend(by_date, "context_reuse")
    if "IMPROVING" in trend_str:
        print("✅ context_reuse violations are declining — context_summary is working")
        return 0
    elif "WORSENING" in trend_str:
        print("❌ context_reuse violations are increasing — check context_summary hook")
        return 1
    else:
        if cr_total > 200:
            print(f"⚠️  context_reuse stable but high ({cr_total} in 14 days) — consider tuning")
            return 1
        print(f"✅ Violation rates stable ({cr_total} context_reuse in 14 days)")
        return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Hook outcome metrics from principle violations")
    parser.add_argument("--days", type=int, default=7, help="Days to analyze (default: 7)")
    args = parser.parse_args()
    return print_report(args.days)


if __name__ == "__main__":
    sys.exit(main())
