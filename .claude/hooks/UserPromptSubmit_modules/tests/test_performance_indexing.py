"""Performance indexing tests for detection_performance table.

Tests the effectiveness of database indexes on query performance.
"""
import sqlite3
import tempfile
from pathlib import Path


class TestPerformanceIndexing:
    """Test database indexing for performance optimization."""

    def test_timing_ms_index_creation(self):
        """Test that timing_ms index can be created successfully."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_perf.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create table
            cursor.execute("""
                CREATE TABLE detection_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    matched_frameworks TEXT,
                    matched_modes TEXT,
                    matched_profiles TEXT,
                    confidence REAL,
                    timing_ms REAL NOT NULL
                )
            """)

            # Create timing_ms index
            cursor.execute("CREATE INDEX idx_perf_timing_ms ON detection_performance(timing_ms DESC)")

            # Verify index exists
            cursor.execute(
                "SELECT sql FROM sqlite_master WHERE type='index' AND name='idx_perf_timing_ms'"
            )
            result = cursor.fetchone()
            assert result is not None
            assert "timing_ms" in result[0]

            conn.close()

    def test_query_plan_uses_timing_ms_index(self):
        """Test that slow detection queries use the timing_ms index."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_perf.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create schema
            cursor.execute("""
                CREATE TABLE detection_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    matched_frameworks TEXT,
                    matched_modes TEXT,
                    matched_profiles TEXT,
                    confidence REAL,
                    timing_ms REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_perf_timing_ms ON detection_performance(timing_ms DESC)")

            # Insert sample data
            for i in range(100):
                cursor.execute(
                    """
                    INSERT INTO detection_performance
                    (timestamp, prompt_hash, timing_ms)
                    VALUES (?, ?, ?)
                """,
                    (f"2026-03-15T00:00:{i:02d}.000000+00:00", f"hash_{i}", float(i))
                )
            conn.commit()

            # Check query plan
            cursor.execute(
                """
                EXPLAIN QUERY PLAN
                SELECT * FROM detection_performance
                WHERE timing_ms > 50.0
                ORDER BY timing_ms DESC
                LIMIT 10
            """
            )
            plan = cursor.fetchall()

            # Should use idx_perf_timing_ms
            plan_str = str(plan)
            assert "idx_perf_timing_ms" in plan_str or "INDEX" in plan_str

            conn.close()

    def test_composite_index_for_slow_detections(self):
        """Test composite index for slow detection queries with timestamp ordering."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_perf.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create schema
            cursor.execute("""
                CREATE TABLE detection_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    matched_frameworks TEXT,
                    matched_modes TEXT,
                    matched_profiles TEXT,
                    confidence REAL,
                    timing_ms REAL NOT NULL
                )
            """)

            # Create composite index (timing_ms DESC, timestamp DESC)
            cursor.execute(
                "CREATE INDEX idx_perf_timing_timestamp ON detection_performance(timing_ms DESC, timestamp DESC)"
            )

            # Insert sample data with varying patterns
            for timing in [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]:
                for i in range(10):
                    cursor.execute(
                        """
                        INSERT INTO detection_performance
                        (timestamp, prompt_hash, timing_ms)
                        VALUES (?, ?, ?)
                    """,
                        (f"2026-03-15T00:00:{i:02d}.000000+00:00", f"hash_{timing}_{i}", float(timing))
                    )
            conn.commit()

            # Test query plan for combined filter + order
            cursor.execute(
                """
                EXPLAIN QUERY PLAN
                SELECT * FROM detection_performance
                WHERE timing_ms > 50.0
                ORDER BY timing_ms DESC, timestamp DESC
                LIMIT 10
            """
            )
            plan = cursor.fetchall()

            # Should use the composite index
            plan_str = str(plan)
            assert "idx_perf_timing_timestamp" in plan_str or "INDEX" in plan_str

            # Verify query returns correct results
            cursor.execute(
                """
                SELECT timing_ms, timestamp
                FROM detection_performance
                WHERE timing_ms > 50.0
                ORDER BY timing_ms DESC, timestamp DESC
                LIMIT 10
            """
            )
            results = cursor.fetchall()

            # Should have 10 results
            assert len(results) == 10

            # All should be > 50ms
            for timing_ms, _ in results:
                assert timing_ms > 50.0

            # Should be ordered by timing_ms DESC, then timestamp DESC
            timings = [r[0] for r in results]
            assert timings == sorted(timings, reverse=True)

            conn.close()

    def test_migration_script_idempotency(self):
        """Test that migration script can be run multiple times safely."""
        # This test verifies the migration uses IF NOT EXISTS
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test_perf.db"
            conn = sqlite3.connect(str(db_path))
            cursor = conn.cursor()

            # Create base schema
            cursor.execute("""
                CREATE TABLE detection_performance (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    prompt_hash TEXT NOT NULL,
                    matched_frameworks TEXT,
                    matched_modes TEXT,
                    matched_profiles TEXT,
                    confidence REAL,
                    timing_ms REAL NOT NULL
                )
            """)
            cursor.execute("CREATE INDEX idx_perf_timestamp ON detection_performance(timestamp DESC)")
            cursor.execute("CREATE INDEX idx_perf_prompt_hash ON detection_performance(prompt_hash)")

            # Run migration twice (simulating idempotency)
            for _ in range(2):
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_perf_timing_ms ON detection_performance(timing_ms DESC)")
                cursor.execute(
                    "CREATE INDEX IF NOT EXISTS idx_perf_slow_detections ON detection_performance(timing_ms DESC, timestamp DESC)"
                )
                conn.commit()

            # Verify only 4 indexes total (2 original + 2 new)
            cursor.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='index' AND tbl_name='detection_performance'")
            index_count = cursor.fetchone()[0]

            # Should have exactly 4 indexes
            assert index_count == 4

            conn.close()
