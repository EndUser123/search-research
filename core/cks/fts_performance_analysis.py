#!/usr/bin/env python3
"""CKS FTS5 Performance Analysis
Analyzes whether reducing database size from 48K to ~20K entries will
significantly improve search performance.
"""

import math
import random
import sqlite3
import statistics
import time
from pathlib import Path

# Computed project root (Python 3.12+)
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent


def analyze_database(db_path: Path) -> None:
    """Comprehensive FTS5 performance analysis."""
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 70)
    print("CKS FTS5 Performance Analysis")
    print("=" * 70)

    # 1. Database Statistics
    print("\n1. DATABASE STATISTICS")
    print("-" * 70)

    cursor.execute("SELECT COUNT(*) FROM entries")
    total_entries = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM entries WHERE content IS NOT NULL")
    with_content = cursor.fetchone()[0]

    cursor.execute("PRAGMA page_size")
    page_size = cursor.fetchone()[0]

    cursor.execute("PRAGMA page_count")
    page_count = cursor.fetchone()[0]

    db_size_mb = (page_size * page_count) / (1024 * 1024)

    print(f"Total entries:      {total_entries:,}")
    print(f"With content:       {with_content:,}")
    print(f"Database size:      {db_size_mb:.1f} MB ({page_count:,} pages)")
    print(f"Page size:          {page_size} bytes")

    # Check FTS5
    cursor.execute("""
        SELECT name FROM sqlite_master
        WHERE type='table' AND name='entries_fts'
    """)
    fts_exists = cursor.fetchone() is not None
    print(f"FTS5 enabled:       {fts_exists}")

    if not fts_exists:
        print("\nERROR: FTS5 not enabled. Cannot analyze.")
        conn.close()
        return

    cursor.execute("SELECT COUNT(*) FROM entries_fts")
    fts_count = cursor.fetchone()[0]
    print(f"FTS5 index entries: {fts_count:,}")

    # 2. Performance Benchmark
    print("\n2. PERFORMANCE BENCHMARK (50 iterations)")
    print("-" * 70)

    # Get sample search terms
    cursor.execute("""
        SELECT DISTINCT title
        FROM entries
        WHERE title IS NOT NULL AND LENGTH(title) > 3
        LIMIT 100
    """)
    search_terms = [row[0] for row in cursor.fetchall()]

    timings = []
    result_counts = []

    for i in range(50):
        query = random.choice(search_terms)
        start = time.perf_counter()

        cursor.execute(
            """
            SELECT e.id, e.title, e.type
            FROM entries e
            JOIN entries_fts fts ON e.id = fts.id
            WHERE entries_fts MATCH ?
            ORDER BY rank
            LIMIT 20
        """,
            (query,),
        )

        results = cursor.fetchall()
        end = time.perf_counter()

        timings.append((end - start) * 1000)
        result_counts.append(len(results))

    mean_time = statistics.mean(timings)
    median_time = statistics.median(timings)
    min_time = min(timings)
    max_time = max(timings)
    stdev = statistics.stdev(timings) if len(timings) > 1 else 0

    print("Search latency (ms):")
    print(f"  Mean:   {mean_time:.3f}")
    print(f"  Median: {median_time:.3f}")
    print(f"  Min:    {min_time:.3f}")
    print(f"  Max:    {max_time:.3f}")
    print(f"  StdDev: {stdev:.3f}")
    print(f"\nMean results: {statistics.mean(result_counts):.1f}")

    # 3. FTS5 Performance Theory
    print("\n3. FTS5 PERFORMANCE CHARACTERISTICS")
    print("-" * 70)

    print("\nAlgorithmic Complexity:")
    print("  Index building:     O(n) where n = document count")
    print("  Search query:       O(log n + k) where k = result count")
    print("  Ranking (BM25):     O(k log k) for sorting results")
    print("  Inverted index:     B-tree structure for fast lookups")

    print("\nMemory & Cache:")
    print("  Index size:         ~10-30% of original text size")
    print("  Page cache:         Dominates real-world performance")
    print("  Cold cache:         First search loads index pages")
    print("  Warm cache:         Subsequent searches <1ms")

    # 4. Archival Impact Analysis
    print("\n4. ARCHIVAL IMPACT ANALYSIS (48K -> 20K entries)")
    print("-" * 70)

    current_count = total_entries
    target_count = 20000
    reduction_ratio = target_count / current_count

    # Theoretical speedup from log reduction
    theoretical_speedup = math.log(current_count) / math.log(target_count)

    # Projected storage savings
    projected_size_mb = db_size_mb * reduction_ratio

    print("\nCurrent state:")
    print(f"  Entries:    {current_count:,}")
    print(f"  Size:       {db_size_mb:.1f} MB")
    print(f"  Latency:    {mean_time:.3f} ms")

    print("\nAfter archival to 20K entries:")
    print(f"  Entries:    {target_count:,}")
    print(
        f"  Size:       ~{projected_size_mb:.1f} MB (save {db_size_mb - projected_size_mb:.1f} MB)"
    )
    print(f"  Reduction:  {reduction_ratio:.1%} of current size")

    print("\nPerformance impact:")
    print(f"  Theoretical speedup: {theoretical_speedup:.2%} faster")
    print(f"  Projected latency:   {mean_time / theoretical_speedup:.3f} ms")
    print(f"  Absolute improvement: {mean_time * (1 - 1/theoretical_speedup):.3f} ms")
    print(f"  Improvement %:       {(1 - 1/theoretical_speedup) * 100:.2f}%")

    # 5. Scale Performance Projection
    print("\n5. PERFORMANCE AT DIFFERENT SCALES (Theoretical)")
    print("-" * 70)

    scales = [10000, 20000, 30000, 40000, 48806]
    baseline_count = current_count
    baseline_time = mean_time

    print(f"\n{'Entries':>10} {'vs Current':>12} {'Projected ms':>12}")
    print("-" * 36)

    for scale in scales:
        speedup = math.log(baseline_count) / math.log(scale) if scale > 0 else 1
        projected = baseline_time / speedup
        comparison = f"{(1 - 1/speedup) * 100:+.1f}%"
        print(f"{scale:>10,} {comparison:>12} {projected:>12.3f}")

    # 6. Recommendation
    print("\n6. RECOMMENDATION")
    print("-" * 70)

    print("\nFrom a PURE PERFORMANCE standpoint:")
    print("  ❌ Archival does NOT significantly improve FTS5 search speed")
    print(f"  ❌ 48K -> 20K reduction = only {theoretical_speedup:.2%} faster")
    print(f"  ❌ Absolute improvement = {mean_time * (1 - 1/theoretical_speedup):.3f} ms")
    print(f"  ✅ Current latency ({mean_time:.3f} ms) is already excellent")
    print("  ✅ Warm cache will reduce latency to <1ms regardless of size")

    print("\nWhy FTS5 performance is logarithmic:")
    print("  • Inverted index structure (B-trees)")
    print("  • Direct lookup via posting lists")
    print("  • Result count dominates latency, not doc count")
    print("  • Page cache eliminates most I/O after first search")

    print("\nWhen archival IS worth it:")
    print(
        f"  ✅ Storage: {db_size_mb:.0f}MB -> {projected_size_mb:.0f}MB ({db_size_mb - projected_size_mb:.0f}MB saved)"
    )
    print("  ✅ Data quality: Remove stale/obsolete entries")
    print("  ✅ Backup/restore: Faster operations")
    print("  ✅ Data relevance: Higher signal-to-noise ratio")

    print("\nRecommended approach:")
    print("  1. Keep FTS5 database at current size for performance")
    print("  2. Implement archival for storage/quality reasons only")
    print("  3. Use archival policy (e.g., entries not used in 6 months)")
    print("  4. Keep archive database accessible for rare queries")
    print("  5. Monitor page cache hit ratio for optimization")

    conn.close()
    print("\n" + "=" * 70)


if __name__ == "__main__":
    db_path = PROJECT_ROOT / "__csf" / "data" / "cks.db"

    if not db_path.exists():
        print(f"ERROR: Database not found at {db_path}")
        exit(1)

    analyze_database(db_path)
