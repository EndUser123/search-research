"""
Simplified test suite for database migration.
Tests core functionality without complex performance assertions.
"""

import shutil
import sqlite3
from pathlib import Path

import pytest


class TestDatabaseMigration:
    """Core tests for database indexing."""

    @pytest.fixture
    def production_db(self):
        return Path("P:/.claude/hooks/events.db")

    @pytest.fixture
    def test_db(self, production_db, tmp_path):
        """Create test database copy."""
        test_db_path = tmp_path / "test_events.db"
        shutil.copy2(production_db, test_db_path)
        return test_db_path

    @pytest.fixture
    def small_test_db(self, tmp_path):
        """Create small test database with 1000 rows."""
        db_path = tmp_path / "small_test.db"
        conn = sqlite3.connect(db_path)
        conn.execute("""
            CREATE TABLE constitutional_events (
                id INTEGER PRIMARY KEY,
                sessionid TEXT NOT NULL,
                event_type TEXT NOT NULL,
                timestamp INTEGER NOT NULL,
                evidence_tier TEXT NOT NULL,
                payload TEXT
            )
        """)
        for i in range(1000):
            conn.execute(
                "INSERT INTO constitutional_events "
                "(sessionid, event_type, timestamp, evidence_tier, payload) "
                "VALUES (?, ?, ?, ?, ?)",
                (f"session-{i % 100}", f"event-{i % 10}", 1700000000 + i, "T3", f"{{\"data\": {i}}}")
            )
        conn.commit()
        conn.close()
        return db_path

    def test_backup_creation(self, test_db, tmp_path):
        """Test backup file creation."""
        from add_indexes import create_backup

        backup_path = tmp_path / "backup.db"
        result = create_backup(test_db, backup_path)

        assert result["success"] is True
        assert backup_path.exists()
        assert backup_path.stat().st_size == test_db.stat().st_size

    def test_backup_data_integrity(self, test_db, tmp_path):
        """Test backup contains identical data."""
        from add_indexes import create_backup

        backup_path = tmp_path / "backup.db"
        create_backup(test_db, backup_path)

        conn_orig = sqlite3.connect(test_db)
        conn_backup = sqlite3.connect(backup_path)

        count_orig = conn_orig.execute("SELECT COUNT(*) FROM constitutional_events").fetchone()[0]
        count_backup = conn_backup.execute("SELECT COUNT(*) FROM constitutional_events").fetchone()[0]

        assert count_orig == count_backup

        conn_orig.close()
        conn_backup.close()

    def test_index_creation(self, small_test_db):
        """Test index creation."""
        from add_indexes import create_indexes

        result = create_indexes(str(small_test_db))

        assert result["success"] is True
        assert len(result["indexes_created"]) >= 5  # At least 5 indexes

    def test_index_verification(self, small_test_db):
        """Test indexes are created correctly."""
        from add_indexes import create_indexes, verify_indexes

        create_indexes(str(small_test_db))
        result = verify_indexes(str(small_test_db))

        assert result["success"] is True
        assert len(result["indexes_found"]) >= 5
        assert "idx_sessionid" in result["indexes_found"]
        assert "idx_event_type" in result["indexes_found"]
        assert "idx_timestamp" in result["indexes_found"]

    def test_query_uses_index(self, small_test_db):
        """Test that queries use indexes."""
        from add_indexes import create_indexes

        create_indexes(str(small_test_db))
        conn = sqlite3.connect(small_test_db)

        # Check query plan uses index
        cursor = conn.execute(
            "EXPLAIN QUERY PLAN "
            "SELECT * FROM constitutional_events WHERE sessionid = ?",
            ("session-1",)
        )
        plan = cursor.fetchone()
        plan_text = " ".join(str(p) for p in plan)

        assert "SEARCH" in plan_text or "USING INDEX" in plan_text
        conn.close()

    def test_data_integrity_preserved(self, small_test_db):
        """Test that data is unchanged after indexing."""
        from add_indexes import create_indexes

        conn = sqlite3.connect(small_test_db)

        # Get data before
        data_before = conn.execute("SELECT * FROM constitutional_events").fetchall()
        count_before = len(data_before)

        # Create indexes
        create_indexes(str(small_test_db))

        # Get data after
        data_after = conn.execute("SELECT * FROM constitutional_events").fetchall()
        count_after = len(data_after)

        assert count_before == count_after
        assert data_before == data_after

        conn.close()

    def test_rollback_indexes(self, small_test_db):
        """Test index rollback."""
        from add_indexes import create_indexes, drop_indexes

        # Create indexes
        create_indexes(str(small_test_db))
        conn = sqlite3.connect(small_test_db)

        cursor = conn.execute("PRAGMA index_list(constitutional_events)")
        indexes_with = len(cursor.fetchall())
        conn.close()

        assert indexes_with >= 5

        # Rollback
        drop_indexes(str(small_test_db))

        # Verify removed
        conn = sqlite3.connect(small_test_db)
        cursor = conn.execute("PRAGMA index_list(constitutional_events)")
        indexes_without = len(cursor.fetchall())
        conn.close()

        assert indexes_without < indexes_with

    def test_performance_measurement(self, small_test_db):
        """Test performance measurement works."""
        from add_indexes import create_indexes, measure_query_performance

        # Measure without index
        metrics_before = measure_query_performance(
            str(small_test_db),
            "SELECT * FROM constitutional_events WHERE sessionid = ?",
            ("session-1",)
        )

        assert "avg_time_ms" in metrics_before
        assert "min_time_ms" in metrics_before
        assert "max_time_ms" in metrics_before

        # Create indexes
        create_indexes(str(small_test_db))

        # Measure with index
        metrics_after = measure_query_performance(
            str(small_test_db),
            "SELECT * FROM constitutional_events WHERE sessionid = ?",
            ("session-1",)
        )

        assert "avg_time_ms" in metrics_after

        # Print results for documentation
        speedup = metrics_before["avg_time_ms"] / metrics_after["avg_time_ms"]
        print(f"\nQuery speedup: {speedup:.1f}x")
        print(f"  Before: {metrics_before['avg_time_ms']:.2f}ms")
        print(f"  After: {metrics_after['avg_time_ms']:.2f}ms")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
