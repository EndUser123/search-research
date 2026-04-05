"""
Performance Impact Test for TASK-F-006 Migration

This script tests the performance impact of the migration on common database operations
to ensure the <50ms requirement is met.
"""

import sqlite3
import statistics
import time
from datetime import datetime


def test_database_performance(db_path):
    """Test performance of common database operations."""

    print(f"Performance Test for: {db_path}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    print("-" * 60)

    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = OFF")

    # Test operations
    operations = [
        ("SELECT COUNT(*) FROM task", "count_tasks"),
        ("SELECT * FROM task LIMIT 10", "fetch_10_tasks"),
        ("SELECT id, title, status FROM task WHERE status = 'active'", "filter_active_tasks"),
        ("SELECT * FROM session_tracking", "fetch_all_sessions"),
        ("SELECT COUNT(*) FROM task WHERE session_id IS NOT NULL", "count_session_tasks"),
        ("SELECT task.*, session_tracking.status FROM task LEFT JOIN session_tracking ON task.session_id = session_tracking.session_id LIMIT 5", "join_session_task")
    ]

    results = {}

    for query, op_name in operations:
        times = []

        # Run each operation 10 times for statistical significance
        error_occurred = False
        for _ in range(10):
            start_time = time.time()
            try:
                result = conn.execute(query).fetchall()
                duration = (time.time() - start_time) * 1000
                times.append(duration)
            except sqlite3.Error as e:
                print(f"❌ {op_name}: FAILED - {e}")
                error_occurred = True
                continue

        if times:
            avg_time = statistics.mean(times)
            min_time = min(times)
            max_time = max(times)
            median_time = statistics.median(times)

            # Get row count for successful queries
            if not error_occurred:
                try:
                    row_count = len(conn.execute(query).fetchall())
                except:
                    row_count = 0
            else:
                row_count = 0

            results[op_name] = {
                'avg_ms': avg_time,
                'min_ms': min_time,
                'max_ms': max_time,
                'median_ms': median_time,
                'samples': len(times),
                'rows': row_count
            }

            print(f"✅ {op_name:25} | Avg: {avg_time:6.2f}ms | Min: {min_time:6.2f}ms | Max: {max_time:6.2f}ms | Median: {median_time:6.2f}ms | Rows: {results[op_name]['rows']:4}")

    conn.close()

    # Overall performance assessment
    print("-" * 60)

    if results:
        max_avg_time = max(r['avg_ms'] for r in results.values())
        overall_avg = statistics.mean([r['avg_ms'] for r in results.values()])

        print("Performance Summary:")
        print(f"  Max average operation time: {max_avg_time:.2f}ms")
        print(f"  Overall average operation time: {overall_avg:.2f}ms")
        print(f"  Total operations tested: {len(results)}")

        # Check if performance meets requirements
        performance_ok = max_avg_time < 50
        print(f"\n🎯 Performance Target (<50ms): {'✅ PASSED' if performance_ok else '❌ FAILED'}")

        if not performance_ok:
            slow_ops = [name for name, data in results.items() if data['avg_ms'] >= 50]
            print(f"   Slow operations: {', '.join(slow_ops)}")

    return results

def test_migration_comparison():
    """Test performance before and after migration using backup."""

    print("\n" + "=" * 80)
    print("MIGRATION PERFORMANCE COMPARISON")
    print("=" * 80)

    # Find the migration backup
    import glob

    backup_files = glob.glob("tasks.db.backup_TASK-F-006_*")
    if not backup_files:
        print("❌ No migration backup found for comparison")
        return

    backup_file = backup_files[0]  # Use the latest backup
    print(f"Using backup for comparison: {backup_file}")

    print("\n📊 PRE-MIGRATION PERFORMANCE (Backup)")
    pre_results = test_database_performance(backup_file)

    print("\n📊 POST-MIGRATION PERFORMANCE (Current)")
    post_results = test_database_performance("tasks.db")

    # Compare results
    print("\n" + "=" * 80)
    print("PERFORMANCE IMPACT ANALYSIS")
    print("=" * 80)

    if pre_results and post_results:
        common_ops = set(pre_results.keys()) & set(post_results.keys())

        for op in sorted(common_ops):
            pre_time = pre_results[op]['avg_ms']
            post_time = post_results[op]['avg_ms']
            impact = post_time - pre_time
            impact_percent = (impact / pre_time) * 100 if pre_time > 0 else 0

            status = "✅" if abs(impact) < 5 else "⚠️" if abs(impact) < 10 else "❌"

            print(f"{status} {op:25} | Pre: {pre_time:6.2f}ms | Post: {post_time:6.2f}ms | Impact: {impact:+6.2f}ms ({impact_percent:+5.1f}%)")

        # Overall assessment
        max_impact = max(abs(post_results[op]['avg_ms'] - pre_results[op]['avg_ms']) for op in common_ops)
        avg_impact = statistics.mean([post_results[op]['avg_ms'] - pre_results[op]['avg_ms'] for op in common_ops])

        print("\n🎯 Overall Performance Impact:")
        print(f"   Maximum impact: {max_impact:+.2f}ms")
        print(f"   Average impact: {avg_impact:+.2f}ms")
        print(f"   Performance requirement (<50ms): {'✅ PASSED' if max_impact < 50 else '❌ FAILED'}")

if __name__ == "__main__":
    import os
    import sys

    # Change to TaskMaster directory
    os.chdir("P:\\.speckit\\taskmaster")

    if len(sys.argv) > 1 and sys.argv[1] == "--compare":
        # Run comparison test
        test_migration_comparison()
    else:
        # Run single database test
        db_file = sys.argv[1] if len(sys.argv) > 1 else "tasks.db"
        test_database_performance(db_file)
