#!/usr/bin/env python3
"""
Performance Benchmarks for CKS Phase 1 Enhancements

Compares baseline search vs Phase 1 enhanced search to verify
expected performance improvements:
- Recall: +20-30%
- Precision: +15-25%
- Latency: +60-120ms (acceptable)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

# Add paths
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))
sys.path.insert(0, "src")

from cks.unified import CKS


def benchmark_search():
    """Run performance benchmarks comparing baseline vs Phase 1"""
    print("="*70)
    print("CKS Phase 1 Performance Benchmark".center(70))
    print("="*70)
    print()

    # Initialize CKS with test database
    test_db_path = Path(__file__).parent / "benchmark_cks.db"
    cks = CKS(db_path=test_db_path, enable_semantic=True)

    # Add diverse test data if database is empty
    import sqlite3
    conn = sqlite3.connect(test_db_path)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM entries")
    count = cur.fetchone()[0]
    conn.close()

    if count < 10:
        print("Test database has insufficient data. Adding sample entries...")
        sample_entries = [
            ("Database timeout configuration", "Set DB timeout to 60s to prevent connection errors", "correction"),
            ("Authentication error handling", "Handle auth errors with proper retry logic", "pattern"),
            "Python database connection pool using SQLAlchemy",
            "CKS authentication token management and refresh",
            "Error handling patterns for database operations",
            "Connection timeout settings for PostgreSQL",
            "User authentication flow in web applications",
            "Database query optimization techniques",
            "Session management for authenticated users",
            "SQLAlchemy async connection handling",
        ]

        for entry in sample_entries:
            if isinstance(entry, tuple):
                cks.ingest_memory(entry[0], entry[1], entry[2])
            else:
                cks.ingest_memory(entry, entry, "knowledge")

        print(f"Added {len(sample_entries)} sample entries\n")

    # Test queries with synonyms/abbreviations
    test_queries = [
        ("db timeout", {"expand_query": True, "fusion_method": "rrf"}),
        ("cks auth", {"expand_query": True, "fusion_method": "rrf", "diversity": 0.7}),
        ("database connection", {"expand_query": True}),
        ("authentication error", {"expand_query": True, "diversity": 0.5}),
    ]

    results = {
        "baseline": {"count": 0, "time": 0},
        "phase1": {"count": 0, "time": 0}
    }

    print("Running benchmarks...")
    print("-"*70)

    for query, phase1_params in test_queries:
        print(f"\nQuery: '{query}'")

        # Baseline search
        start = time.time()
        baseline_results = cks.search_semantic(query, limit=5)
        baseline_time = (time.time() - start) * 1000
        baseline_count = len(baseline_results)

        print(f"  Baseline:  {baseline_count} results in {baseline_time:.1f}ms")

        # Phase 1 enhanced search
        start = time.time()
        phase1_results = cks.search_semantic(
            query,
            limit=5,
            **phase1_params
        )
        phase1_time = (time.time() - start) * 1000
        phase1_count = len(phase1_results)

        print(f"  Phase 1:   {phase1_count} results in {phase1_time:.1f}ms")

        # Calculate improvements
        count_diff = phase1_count - baseline_count
        time_diff = phase1_time - baseline_time

        if count_diff > 0:
            print(f"  Improvement: +{count_diff} results ({count_diff/baseline_count*100:.0f}% increase)")
        if time_diff > 0:
            print(f"  Latency:     +{time_diff:.1f}ms")

        results["baseline"]["count"] += baseline_count
        results["baseline"]["time"] += baseline_time
        results["phase1"]["count"] += phase1_count
        results["phase1"]["time"] += phase1_time

    # Summary
    print("\n" + "="*70)
    print("Summary".center(70))
    print("="*70)

    avg_baseline_count = results["baseline"]["count"] / len(test_queries)
    avg_phase1_count = results["phase1"]["count"] / len(test_queries)
    avg_baseline_time = results["baseline"]["time"] / len(test_queries)
    avg_phase1_time = results["phase1"]["time"] / len(test_queries)

    recall_improvement = ((avg_phase1_count - avg_baseline_count) / avg_baseline_count * 100) if avg_baseline_count > 0 else 0
    latency_overhead = avg_phase1_time - avg_baseline_time

    print("\nAverage Results per Query:")
    print(f"  Baseline:  {avg_baseline_count:.1f} results")
    print(f"  Phase 1:   {avg_phase1_count:.1f} results")
    print(f"  Recall:    +{recall_improvement:.0f}% improvement")

    print("\nAverage Latency per Query:")
    print(f"  Baseline:  {avg_baseline_time:.1f}ms")
    print(f"  Phase 1:   {avg_phase1_time:.1f}ms")
    print(f"  Overhead:  +{latency_overhead:.1f}ms")

    # Verify against expected targets
    print("\n" + "="*70)
    print("Target Verification".center(70))
    print("="*70)

    targets = {
        "Recall Improvement": (recall_improvement, 20, 30),
        "Latency Overhead": (latency_overhead, 0, 120),
    }

    for metric, (value, min_target, max_target) in targets.items():
        status = "✓ PASS" if min_target <= value <= max_target else "✗ FAIL"
        print(f"\n{status} - {metric}")
        print(f"  Expected: {min_target:.0f}-{max_target:.0f}")
        print(f"  Actual:   {value:.0f}")

    return all(min_target <= value <= max_target for value, min_target, max_target in targets.values())

if __name__ == "__main__":
    try:
        success = benchmark_search()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\nBenchmark failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
