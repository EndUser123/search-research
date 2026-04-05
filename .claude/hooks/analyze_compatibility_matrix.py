#!/usr/bin/env python3
"""
Analyze 3D Compatibility Matrix Usage
======================================

Understand how cross-category cognitive combinations are being used.

Key metrics:
- M1: Cross-category trigger usage rate (target: >15%)
- M2: Performance overhead (target: <5ms)
- M3: Matrix entry count (target: <50 entries)
- Most-used 3D combinations
- Detection latency distribution
- False positive indicators

Usage:
  python analyze_compatibility_matrix.py [days] [--terminal] [--all]

Options:
  days        Days to analyze (default: 7)
  --terminal  Filter to current terminal only
  --all       Show all terminals separately
"""

import argparse
import sqlite3
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add hooks directory for imports
HOOKS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(HOOKS_DIR))

DB_PATH = HOOKS_DIR / "state" / "performance.db"


def get_current_terminal_id() -> str:
    """Get current terminal ID for filtering."""
    try:
        from __lib.terminal_detection import detect_terminal_id
        return detect_terminal_id()
    except ImportError:
        return None


def analyze_compatibility_usage(days: int = 7, terminal_filter: str = None, show_all: bool = False):
    """Analyze 3D compatibility matrix usage patterns."""

    if not DB_PATH.exists():
        print("  [!] Performance database not found")
        return

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Calculate cutoff date
    cutoff = (datetime.now() - timedelta(days=days)).isoformat()

    # Build terminal filter
    terminal_clause = ""
    terminal_params = []
    if terminal_filter:
        terminal_clause = "AND terminal_id = ?"
        terminal_params = [terminal_filter]
    elif not show_all:
        # No filter, aggregate all terminals
        terminal_clause = ""

    print(f"\n{'='*60}")
    print("3D COMPATIBILITY MATRIX ANALYSIS")
    print(f"Period: Last {days} days")
    if terminal_filter:
        print(f"Terminal: {terminal_filter[:20]}...")
    elif show_all:
        print("View: Per-terminal breakdown")
    print(f"{'='*60}\n")

    # M1: Cross-category trigger usage rate
    print(f"{'─'*60}")
    print("M1: CROSS-CATEGORY TRIGGER USAGE")
    print(f"{'─'*60}")

    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT session_id) as total_sessions,
            COUNT(DISTINCT CASE
                WHEN framework IS NOT NULL THEN session_id
            END) as sessions_with_3d,
            COUNT(*) as total_detections,
            AVG(detection_latency_ms) as avg_latency_ms
        FROM compatibility_usage_log
        WHERE timestamp >= ? {terminal_clause}
    """, [cutoff] + terminal_params)

    result = cursor.fetchone()
    if result and result[0]:
        total_sessions = result[0]
        sessions_with_3d = result[1] or 0
        total_detections = result[2] or 0
        avg_latency = result[3] or 0

        usage_rate = (sessions_with_3d / total_sessions * 100) if total_sessions > 0 else 0

        print(f"  Total sessions: {total_sessions}")
        print(f"  Sessions with 3D triggers: {sessions_with_3d}")
        print(f"  Usage rate: {usage_rate:.1f}%")
        print("  Target: >15%")

        if usage_rate >= 15:
            print("  Status: ✅ PASS")
        else:
            print(f"  Status: ⚠️  BELOW TARGET (need {(15 - usage_rate):.1f}% more)")

        print(f"\n  Total 3D detections: {total_detections}")
    else:
        print("  No 3D compatibility detections recorded")

    # M2: Performance overhead
    print(f"\n{'─'*60}")
    print("M2: PERFORMANCE OVERHEAD")
    print(f"{'─'*60}")

    cursor.execute(f"""
        SELECT
            MIN(detection_latency_ms) as min_latency,
            AVG(detection_latency_ms) as avg_latency,
            MAX(detection_latency_ms) as max_latency
        FROM compatibility_usage_log
        WHERE timestamp >= ? {terminal_clause}
    """, [cutoff] + terminal_params)

    result = cursor.fetchone()
    if result and result[0]:
        min_lat = result[0] or 0
        avg_lat = result[1] or 0
        max_lat = result[2] or 0

        print(f"  Min latency: {min_lat:.3f} ms")
        print(f"  Avg latency: {avg_lat:.3f} ms")
        print(f"  Max latency: {max_lat:.3f} ms")
        print("  Target: <5ms")

        if avg_lat < 5:
            print(f"  Status: ✅ PASS ({avg_lat:.3f}x better than target)")
        else:
            print(f"  Status: ❌ FAIL ({avg_lat:.3f}x over target)")

    # M3: Matrix entry count
    print(f"\n{'─'*60}")
    print("M3: MATRIX ENTRY COUNT")
    print(f"{'─'*60}")

    cursor.execute("""
        SELECT COUNT(DISTINCT framework || ':' || mode || ':' || profile)
        FROM compatibility_usage_log
    """)

    result = cursor.fetchone()
    if result:
        entry_count = result[0] or 0
        print(f"  Active entries: {entry_count}")
        print("  Target: <50 entries")

        if entry_count < 50:
            print(f"  Status: ✅ PASS ({entry_count}/50 entries used)")
        else:
            print(f"  Status: ⚠️  APPROACHING LIMIT ({entry_count}/50 entries)")

    # Most-used 3D combinations
    print(f"\n{'─'*60}")
    print("MOST-USED 3D COMBINATIONS")
    print(f"{'─'*60}")

    group_by = "terminal_id, " if show_all else ""
    cursor.execute(f"""
        SELECT
            framework,
            mode,
            profile,
            COUNT(*) as usage_count,
            AVG(detection_latency_ms) as avg_latency
        FROM compatibility_usage_log
        WHERE timestamp >= ? {terminal_clause}
        GROUP BY {group_by}framework, mode, profile
        ORDER BY usage_count DESC
        LIMIT 10
    """, [cutoff] + terminal_params)

    results = cursor.fetchall()
    if results:
        print(f"  {'Rank':<6} {'Framework':<25} {'Mode':<12} {'Profile':<20} {'Count':<7} {'Latency'}")
        print(f"  {'-'*6}-{'-'*25}-{'-'*12}-{'-'*20}-{'-'*7}-{'-'*10}")

        for i, (framework, mode, profile, count, latency) in enumerate(results, 1):
            latency_str = f"{latency:.3f}ms" if latency else "N/A"
            combo = f"{framework} + {mode} + {profile}"
            print(f"  {i:<6} {combo[:60]:<60} {count:<7} {latency_str}")
    else:
        print("  No 3D combinations recorded yet")

    # Detection quality indicators
    print(f"\n{'─'*60}")
    print("DETECTION QUALITY")
    print(f"{'─'*60}")

    # Check for high-frequency combinations (potential false positives)
    cursor.execute(f"""
        SELECT
            framework,
            mode,
            profile,
            COUNT(*) as usage_count,
            COUNT(DISTINCT session_id) as unique_sessions
        FROM compatibility_usage_log
        WHERE timestamp >= ? {terminal_clause}
        GROUP BY {group_by}framework, mode, profile
        HAVING usage_count > 100
        ORDER BY usage_count DESC
    """, [cutoff] + terminal_params)

    high_freq = cursor.fetchall()
    if high_freq:
        print("  High-frequency combinations (>100 detections):")
        for framework, mode, profile, count, sessions in high_freq:
            avg_per_session = count / sessions if sessions > 0 else 0
            print(f"    • {framework} + {mode} + {profile}")
            print(f"      {count} detections across {sessions} sessions ({avg_per_session:.1f}/session)")

            if avg_per_session > 20:
                print(f"      ⚠️  POSSIBLE FALSE POSITIVE (>{avg_per_session:.1f}/session)")
    else:
        print("  No high-frequency combinations detected")

    # Recommendations
    print(f"\n{'─'*60}")
    print("RECOMMENDATIONS")
    print(f"{'─'*60}")

    recommendations = []

    # Check usage rate
    if usage_rate < 15:
        recommendations.append("• Increase cross-category detection sensitivity to reach >15% usage rate")

    # Check matrix size
    if entry_count > 40:
        recommendations.append("• Matrix approaching 50-entry limit - consider pruning low-value entries")

    # Check for potential over-detection
    cursor.execute(f"""
        SELECT
            COUNT(DISTINCT framework || ':' || mode || ':' || profile) as entry_count,
            SUM(detection_count) as total_detections
        FROM (
            SELECT framework, mode, profile, COUNT(*) as detection_count
            FROM compatibility_usage_log
            WHERE timestamp >= ? {terminal_clause}
            GROUP BY {group_by}framework, mode, profile
            HAVING detection_count > 100
        )
    """, [cutoff] + terminal_params)

    result = cursor.fetchone()
    if result and result[0] > 5:
        recommendations.append("• Review high-frequency combinations for potential false positives")

    # Performance optimization
    if avg_lat > 2:
        recommendations.append("• Consider matrix lookup optimization to reduce latency")

    if recommendations:
        for rec in recommendations:
            print(f"  {rec}")
    else:
        print("  ✅ No immediate recommendations - system performing well")

    conn.close()


def main():
    parser = argparse.ArgumentParser(
        description="Analyze 3D Compatibility Matrix Usage"
    )
    parser.add_argument(
        "days",
        nargs="?",
        type=int,
        default=7,
        help="Days to analyze (default: 7)"
    )
    parser.add_argument(
        "--terminal",
        action="store_true",
        help="Filter to current terminal only"
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Show per-terminal breakdown"
    )

    args = parser.parse_args()

    terminal_filter = None
    if args.terminal:
        terminal_filter = get_current_terminal_id()
        if not terminal_filter:
            print("[!] Could not detect terminal ID")
            return

    analyze_compatibility_usage(
        days=args.days,
        terminal_filter=terminal_filter,
        show_all=args.all
    )


if __name__ == "__main__":
    main()
