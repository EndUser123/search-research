"""Migration script to add performance indexes to detection_performance table.

This migration adds indexes to optimize common queries:
- idx_perf_timing_ms: Optimizes slow detection queries (WHERE timing_ms > ?)
- idx_perf_slow_detections: Composite index for slow detections with time ordering

Migration version: 001
Date: 2026-03-15
"""
from __future__ import annotations

import sqlite3
from pathlib import Path


def migrate(db_path: Path) -> dict[str, str]:
    """Apply migration to add performance indexes.

    Args:
        db_path: Path to performance.db database

    Returns:
        Dict with migration results
    """
    if not db_path.exists():
        return {
            "status": "skipped",
            "reason": f"Database not found at {db_path}",
        }

    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check if indexes already exist
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='detection_performance' AND name IN ('idx_perf_timing_ms', 'idx_perf_slow_detections')"
        )
        existing_indexes = {row[0] for row in cursor.fetchall()}

        results = {}

        # Add timing_ms index for slow detection queries
        if "idx_perf_timing_ms" not in existing_indexes:
            cursor.execute("CREATE INDEX idx_perf_timing_ms ON detection_performance(timing_ms DESC)")
            results["idx_perf_timing_ms"] = "created"
        else:
            results["idx_perf_timing_ms"] = "already_exists"

        # Add composite index for slow detections with timestamp ordering
        if "idx_perf_slow_detections" not in existing_indexes:
            cursor.execute(
                "CREATE INDEX idx_perf_slow_detections ON detection_performance(timing_ms DESC, timestamp DESC)"
            )
            results["idx_perf_slow_detections"] = "created"
        else:
            results["idx_perf_slow_detections"] = "already_exists"

        conn.commit()
        conn.close()

        return {
            "status": "success",
            "indexes": results,
            "database": str(db_path),
        }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
            "database": str(db_path),
        }


def verify_indexes(db_path: Path) -> dict[str, list[str]]:
    """Verify that indexes exist and are being used by query planner.

    Args:
        db_path: Path to performance.db database

    Returns:
        Dict with index information and query plans
    """
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Get all indexes on detection_performance
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='index' AND tbl_name='detection_performance'")
        indexes = {row[0]: row[1] for row in cursor.fetchall()}

        # Test query plans
        query_plans = {}

        # Query 1: Slow detections (WHERE timing_ms > ?)
        cursor.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM detection_performance
            WHERE timing_ms > 50.0
            ORDER BY timing_ms DESC
            LIMIT 10
        """
        )
        query_plans["slow_detections"] = [row[3] for row in cursor.fetchall()]

        # Query 2: Performance summary (ORDER BY timestamp DESC)
        cursor.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT timing_ms FROM detection_performance
            ORDER BY timestamp DESC
            LIMIT 100
        """
        )
        query_plans["performance_summary"] = [row[3] for row in cursor.fetchall()]

        # Query 3: Combined slow detections with timestamp ordering
        cursor.execute(
            """
            EXPLAIN QUERY PLAN
            SELECT * FROM detection_performance
            WHERE timing_ms > 50.0
            ORDER BY timing_ms DESC, timestamp DESC
            LIMIT 10
        """
        )
        query_plans["slow_detections_with_timestamp"] = [row[3] for row in cursor.fetchall()]

        conn.close()

        return {
            "indexes": indexes,
            "query_plans": query_plans,
        }

    except Exception as e:
        return {
            "error": str(e),
        }


if __name__ == "__main__":
    # Run migration on default database
    default_db = Path(__file__).resolve().parent.parent.parent / "logs/diagnostics/performance.db"

    print(f"Running migration on: {default_db}")
    result = migrate(default_db)
    print(f"Migration result: {result}")

    if result["status"] == "success":
        print("\nVerifying indexes...")
        verification = verify_indexes(default_db)

        if "error" in verification:
            print(f"Verification error: {verification['error']}")
        else:
            print("\nIndexes found:")
            for name, sql in verification["indexes"].items():
                print(f"  - {name}")

            print("\nQuery execution plans:")
            for query_name, plans in verification["query_plans"].items():
                print(f"  {query_name}:")
                for plan in plans:
                    print(f"    {plan}")
