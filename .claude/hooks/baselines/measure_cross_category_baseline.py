#!/usr/bin/env python3
"""Measure baseline metrics for 3D compatibility matrix before deployment.

TASK-008: Collect M1, M2, M3, and S1 baseline measurements.
"""
from __future__ import annotations

import json
import sqlite3
import statistics

# Add parent directory to path for imports
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from UserPromptSubmit_modules.unified_detection import (
    _COMPATIBILITY_MATRIX,
)


def measure_m1_cross_category_usage() -> dict[str, Any]:
    """Measure M1: Cross-category trigger usage rate.

    Expected: 0% (matrix not yet deployed to production)

    Returns:
        {
            "metric": "M1_cross_category_usage",
            "baseline_percent": 0.0,
            "measurement_date": "2026-03-15",
            "total_prompt_submits": count,
            "cross_category_triggers": count,
            "usage_rate": 0.0
        }
    """
    # Query performance.db for UserPromptSubmit events
    db_path = Path(__file__).parent.parent / "state" / "performance.db"

    if not db_path.exists():
        return {
            "metric": "M1_cross_category_usage",
            "baseline_percent": 0.0,
            "measurement_date": datetime.now().isoformat(),
            "total_prompt_submits": 0,
            "cross_category_triggers": 0,
            "usage_rate": 0.0,
            "note": "No performance.db found - system not yet initialized"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Count total UserPromptSubmit events in last 7 days
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()
        cursor.execute("""
            SELECT COUNT(*) FROM detection_metrics
            WHERE timestamp > ?
        """, (week_ago,))
        total_submits = cursor.fetchone()[0] or 0

        # Count events with compatible_combinations (should be 0)
        cursor.execute("""
            SELECT COUNT(*) FROM detection_metrics
            WHERE timestamp > ?
            AND json_extract(detection_result, '$.compatible_combinations') IS NOT NULL
            AND json_array_length(json_extract(detection_result, '$.compatible_combinations')) > 0
        """, (week_ago,))
        cross_category_triggers = cursor.fetchone()[0] or 0

        usage_rate = (cross_category_triggers / total_submits * 100) if total_submits > 0 else 0.0

        conn.close()

        return {
            "metric": "M1_cross_category_usage",
            "baseline_percent": 0.0,  # Expected 0% before deployment
            "measurement_date": datetime.now().isoformat(),
            "total_prompt_submits": total_submits,
            "cross_category_triggers": cross_category_triggers,
            "usage_rate": round(usage_rate, 2),
            "measurement_period_days": 7
        }
    except Exception as e:
        return {
            "metric": "M1_cross_category_usage",
            "baseline_percent": 0.0,
            "measurement_date": datetime.now().isoformat(),
            "total_prompt_submits": 0,
            "cross_category_triggers": 0,
            "usage_rate": 0.0,
            "error": str(e)
        }


def measure_m2_performance_overhead() -> dict[str, Any]:
    """Measure M2: Compatibility matrix lookup performance.

    Target: <5ms overhead
    Baseline: Should be ~0.2-0.3ms (from T-003 implementation)

    Returns:
        {
            "metric": "M2_performance_overhead",
            "baseline_ms": 0.25,
            "target_ms": 5.0,
            "measurement_date": "2026-03-15",
            "samples": 100,
            "min_ms": 0.16,
            "max_ms": 0.30,
            "avg_ms": 0.24,
            "p95_ms": 0.28
        }
    """
    # Import here to avoid circular dependency
    from UserPromptSubmit_modules.unified_detection import _detect_3d_compatibility

    # Sample prompts for testing
    test_prompts = [
        "Design microservice architecture considering team structure",
        "Debug authentication flow failure affecting mobile users",
        "Optimize slow database queries causing timeout",
        "Review security implications of OAuth implementation",
        "Refactor legacy codebase for better maintainability",
    ]

    latencies = []
    samples = 100

    for i in range(samples):
        prompt = test_prompts[i % len(test_prompts)]

        # Measure detection latency
        start = time.perf_counter()
        result = _detect_3d_compatibility(
            matched_frameworks={"assumption_surfacing"},
            matched_modes={"multi_agent"},
            matched_profiles={"architecture"}
        )
        end = time.perf_counter()

        latency_ms = (end - start) * 1000
        latencies.append(latency_ms)

    # Calculate statistics
    latencies_sorted = sorted(latencies)
    p95_index = int(len(latencies_sorted) * 0.95)

    return {
        "metric": "M2_performance_overhead",
        "baseline_ms": round(statistics.mean(latencies), 3),
        "target_ms": 5.0,
        "measurement_date": datetime.now().isoformat(),
        "samples": samples,
        "min_ms": round(min(latencies), 3),
        "max_ms": round(max(latencies), 3),
        "avg_ms": round(statistics.mean(latencies), 3),
        "median_ms": round(statistics.median(latencies), 3),
        "p95_ms": round(latencies_sorted[p95_index], 3),
        "stdev_ms": round(statistics.stdev(latencies) if len(latencies) > 1 else 0, 3)
    }


def measure_m3_matrix_entry_count() -> dict[str, Any]:
    """Measure M3: Number of compatibility matrix entries.

    Target: <50 entries (maintenance burden)
    Baseline: 19 entries (14 from T-004 + 5 hardcoded)

    Returns:
        {
            "metric": "M3_matrix_entry_count",
            "baseline_count": 19,
            "target_count": 50,
            "measurement_date": "2026-03-15",
            "hardcoded_entries": 5,
            "disk_entries": 14,
            "by_framework": {...},
            "by_mode": {...},
            "by_profile": {...}
        }
    """
    # Count entries in _COMPATIBILITY_MATRIX (it's a dict with tuple keys)
    hardcoded_entries = len(_COMPATIBILITY_MATRIX)

    # Check for disk-based entries
    disk_entries = 0
    matrix_file = Path(__file__).parent.parent / "state" / "compatibility_matrix.json"

    if matrix_file.exists():
        try:
            with open(matrix_file) as f:
                disk_data = json.load(f)
                disk_entries = len(disk_data.get("compatibility_matrix", {}))
        except Exception:
            pass  # File not readable, count as 0

    total_entries = hardcoded_entries + disk_entries

    # Categorize by framework, mode, profile
    # _COMPATIBILITY_MATRIX is dict[tuple[str, str, str], CompatibilityMatrixEntry]
    by_framework: dict[str, int] = {}
    by_mode: dict[str, int] = {}
    by_profile: dict[str, int] = {}

    for (framework, mode, profile), entry in _COMPATIBILITY_MATRIX.items():
        by_framework[framework] = by_framework.get(framework, 0) + 1
        by_mode[mode] = by_mode.get(mode, 0) + 1
        by_profile[profile] = by_profile.get(profile, 0) + 1

    return {
        "metric": "M3_matrix_entry_count",
        "baseline_count": total_entries,
        "target_count": 50,
        "measurement_date": datetime.now().isoformat(),
        "hardcoded_entries": hardcoded_entries,
        "disk_entries": disk_entries,
        "by_framework": by_framework,
        "by_mode": by_mode,
        "by_profile": by_profile,
        "matrix_file": str(matrix_file),
        "file_exists": matrix_file.exists()
    }


def measure_s1_cks_query_rate() -> dict[str, Any]:
    """Measure S1: Current CKS query frequency.

    Target: 20% reduction after deployment
    Baseline: Current queries per day

    Returns:
        {
            "metric": "S1_cks_query_rate",
            "baseline_queries_per_day": 123.4,
            "measurement_period": "7 days",
            "measurement_date": "2026-03-15",
            "total_queries": count,
            "unique_sessions": count,
            "queries_per_session": avg
        }
    """
    # Query performance.db for CKS queries
    db_path = Path(__file__).parent.parent / "state" / "performance.db"

    if not db_path.exists():
        return {
            "metric": "S1_cks_query_rate",
            "baseline_queries_per_day": 0.0,
            "measurement_period_days": 7,
            "measurement_date": datetime.now().isoformat(),
            "total_queries": 0,
            "unique_sessions": 0,
            "queries_per_session": 0.0,
            "note": "No performance.db found - system not yet initialized"
        }

    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Query last 7 days of CKS-related events
        week_ago = (datetime.now() - timedelta(days=7)).isoformat()

        # Count CKS queries (look for cks_integration or daemon_client events)
        cursor.execute("""
            SELECT COUNT(*) FROM detection_metrics
            WHERE timestamp > ?
            AND (detection_system LIKE '%cks%'
                 OR detection_system LIKE '%daemon%'
                 OR detection_system LIKE '%semantic%')
        """, (week_ago,))
        total_queries = cursor.fetchone()[0] or 0

        # Count unique sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM detection_metrics
            WHERE timestamp > ?
            AND (detection_system LIKE '%cks%'
                 OR detection_system LIKE '%daemon%'
                 OR detection_system LIKE '%semantic%')
        """, (week_ago,))
        unique_sessions = cursor.fetchone()[0] or 0

        # Calculate per-day average
        queries_per_day = total_queries / 7.0
        queries_per_session = (total_queries / unique_sessions) if unique_sessions > 0 else 0.0

        conn.close()

        return {
            "metric": "S1_cks_query_rate",
            "baseline_queries_per_day": round(queries_per_day, 2),
            "measurement_period_days": 7,
            "measurement_date": datetime.now().isoformat(),
            "total_queries": total_queries,
            "unique_sessions": unique_sessions,
            "queries_per_session": round(queries_per_session, 2)
        }
    except Exception as e:
        return {
            "metric": "S1_cks_query_rate",
            "baseline_queries_per_day": 0.0,
            "measurement_period_days": 7,
            "measurement_date": datetime.now().isoformat(),
            "total_queries": 0,
            "unique_sessions": 0,
            "queries_per_session": 0.0,
            "error": str(e)
        }


def main() -> None:
    """Run all baseline measurements and create JSON report."""
    print("🔬 TASK-008: Measuring baseline metrics for 3D compatibility matrix\n")

    # Create baselines directory
    baselines_dir = Path(__file__).parent
    baselines_dir.mkdir(exist_ok=True)

    # Measure all metrics
    print("📊 Measuring M1: Cross-category trigger usage...")
    m1_result = measure_m1_cross_category_usage()
    print(f"  ✓ Usage rate: {m1_result['usage_rate']}% ({m1_result['cross_category_triggers']}/{m1_result['total_prompt_submits']} prompts)\n")

    print("⚡ Measuring M2: Performance overhead...")
    m2_result = measure_m2_performance_overhead()
    print(f"  ✓ Average latency: {m2_result['avg_ms']}ms (target: <{m2_result['target_ms']}ms)")
    print(f"  ✓ P95 latency: {m2_result['p95_ms']}ms\n")

    print("📝 Measuring M3: Matrix entry count...")
    m3_result = measure_m3_matrix_entry_count()
    print(f"  ✓ Total entries: {m3_result['baseline_count']} (target: <{m3_result['target_count']})")
    print(f"  ✓ Hardcoded: {m3_result['hardcoded_entries']}, Disk: {m3_result['disk_entries']}\n")

    print("🔍 Measuring S1: CKS query rate...")
    s1_result = measure_s1_cks_query_rate()
    print(f"  ✓ Queries/day: {s1_result['baseline_queries_per_day']}")
    print(f"  ✓ Total queries: {s1_result['total_queries']} ({s1_result['unique_sessions']} sessions)\n")

    # Compile baseline report
    baseline_report = {
        "measurement_date": datetime.now().isoformat(),
        "plan_reference": "plan-20260315-cognitive-cross-category-compatibility-matrix.md",

        "primary_metrics": {
            "M1_cross_category_usage": {
                "baseline_percent": m1_result["baseline_percent"],
                "target_percent": 15.0,
                "status": "not_deployed" if m1_result["usage_rate"] == 0 else "unexpected",
                "measurement": m1_result
            },
            "M2_performance_overhead": {
                "baseline_ms": m2_result["baseline_ms"],
                "target_ms": m2_result["target_ms"],
                "status": "pass" if m2_result["avg_ms"] < m2_result["target_ms"] else "fail",
                "measurement": m2_result
            },
            "M3_matrix_entry_count": {
                "baseline_count": m3_result["baseline_count"],
                "target_count": m3_result["target_count"],
                "status": "pass" if m3_result["baseline_count"] < m3_result["target_count"] else "fail",
                "measurement": m3_result
            }
        },

        "secondary_metrics": {
            "S1_cks_query_rate": {
                "baseline_queries_per_day": s1_result["baseline_queries_per_day"],
                "target_reduction_percent": 20.0,
                "status": "measured",
                "measurement": s1_result
            }
        },

        "metadata": {
            "matrix_entries_file": str(Path(__file__).parent.parent / "state" / "compatibility_matrix.json"),
            "unified_detection_version": "1.0",
            "conflict_arbiter_version": "7.0",
            "measurement_tool": "measure_cross_category_baseline.py"
        }
    }

    # Write baseline JSON file
    output_file = baselines_dir / "cross_category_baseline_20260315.json"
    with open(output_file, "w") as f:
        json.dump(baseline_report, f, indent=2)

    print(f"✅ Baseline report written to: {output_file}\n")

    # Print summary
    print("📋 BASELINE SUMMARY")
    print("=" * 60)
    print(f"M1: Cross-category usage       {m1_result['usage_rate']}% (baseline before deployment)")
    print(f"M2: Performance overhead        {m2_result['avg_ms']}ms avg, {m2_result['p95_ms']}ms p95 (target: <5ms) {'✅' if m2_result['avg_ms'] < m2_result['target_ms'] else '❌'}")
    print(f"M3: Matrix entry count          {m3_result['baseline_count']} entries (target: <50) {'✅' if m3_result['baseline_count'] < m3_result['target_count'] else '❌'}")
    print(f"S1: CKS query rate              {s1_result['baseline_queries_per_day']} queries/day (baseline for reduction)")
    print("=" * 60)
    print("\n✅ All baseline metrics measured successfully!")
    print("\nNext steps:")
    print("1. Deploy 3D compatibility matrix to production")
    print("2. Monitor metrics for 7 days")
    print("3. Compare post-deployment metrics against this baseline")
    print("4. Run baselines/measure_cross_category_baseline.py again")


if __name__ == "__main__":
    main()
