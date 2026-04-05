"""Tests for FR-17: API Total Tracking for quota-free completeness checks."""

import gc
import pytest
from pathlib import Path
import tempfile
import sqlite3

from yt_fts.core.database import get_channel_api_total, set_channel_api_total
from yt_fts.utils.migrations import (
    check_migration_status,
    migrate_to_api_total_tracking,
)


@pytest.fixture(autouse=True)
def cleanup_sqlite_connections():
    """Force garbage collection after each test to close SQLite connections.

    Windows keeps file locks on SQLite databases even after conn.close().
    This fixture ensures all connections are properly closed before temp
    directory cleanup runs.
    """
    yield
    gc.collect()


@pytest.fixture
def temp_db_with_api_total():
    """Create a temporary database with api_total columns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"

        # Override get_db_path for this test
        import yt_fts.core.database as db_module
        import yt_fts.utils.migrations as migrations_module
        from yt_fts.utils.config import get_db_path

        original_get_db_path_db = db_module.get_db_path
        original_get_db_path_migrations = migrations_module.get_db_path

        db_module.get_db_path = lambda: str(db_path)
        migrations_module.get_db_path = lambda: str(db_path)

        # Create test database schema
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()

        # Create Channels table (without api_total columns initially)
        cur.execute("""
            CREATE TABLE Channels (
                channel_id TEXT PRIMARY KEY,
                channel_name TEXT,
                channel_url TEXT
            )
        """)

        # Create Videos table
        cur.execute("""
            CREATE TABLE Videos (
                video_id TEXT PRIMARY KEY,
                channel_id TEXT,
                video_title TEXT,
                video_url TEXT,
                video_date TEXT
            )
        """)

        # Insert test channel
        test_channel_id = "UCtest123"
        cur.execute("INSERT INTO Channels VALUES (?, ?, ?)",
                   (test_channel_id, "Test Channel", "https://youtube.com/@test"))

        # Insert some videos
        for i in range(5):
            cur.execute("INSERT INTO Videos VALUES (?, ?, ?, ?, ?)",
                       (f"video_{i}", test_channel_id, f"Video {i}", f"https://youtube.com/watch?v=video_{i}", "2024-01-01"))

        conn.commit()
        conn.close()

        yield test_channel_id, db_path

        # Cleanup: restore original functions and force GC to close connections
        db_module.get_db_path = original_get_db_path_db
        migrations_module.get_db_path = original_get_db_path_migrations
        gc.collect()


class TestMigrationApiTotalTracking:
    """Tests for api_total tracking migration."""

    def test_migration_adds_columns(self, temp_db_with_api_total):
        """Test that migration adds api_total columns to Channels table."""
        channel_id, db_path = temp_db_with_api_total

        # Run migration
        migrate_to_api_total_tracking()

        # Verify columns exist
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(Channels)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()

        assert "api_total_video_count" in columns, "api_total_video_count column not added"
        assert "api_total_last_checked" in columns, "api_total_last_checked column not added"

    def test_migration_handles_duplicate_columns(self, temp_db_with_api_total):
        """Test that migration handles existing columns gracefully."""
        channel_id, db_path = temp_db_with_api_total

        # Run migration twice
        migrate_to_api_total_tracking()
        migrate_to_api_total_tracking()  # Should not error

        # Verify still works
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(Channels)")
        columns = {row[1] for row in cur.fetchall()}
        conn.close()

        assert "api_total_video_count" in columns

    def test_migration_status_detection(self, temp_db_with_api_total):
        """Test that migration status is detected correctly."""
        # Before migration
        status = check_migration_status()
        assert status.get("api_total_tracking") == False, "Should not show as migrated before migration"

        # Run migration
        migrate_to_api_total_tracking()

        # After migration
        status = check_migration_status()
        assert status.get("api_total_tracking") == True, "Should show as migrated after migration"


class TestApiTotalDatabaseFunctions:
    """Tests for get/set_channel_api_total functions."""

    def test_get_api_total_returns_none_when_not_set(self, temp_db_with_api_total):
        """Test that get_channel_api_total returns None when no value is stored."""
        channel_id, _ = temp_db_with_api_total

        # Run migration first
        migrate_to_api_total_tracking()

        # Should return None when not set
        result = get_channel_api_total(channel_id)
        assert result is None, f"Expected None, got {result}"

    def test_set_and_get_api_total(self, temp_db_with_api_total):
        """Test that set_channel_api_total stores and get_channel_api_total retrieves."""
        channel_id, _ = temp_db_with_api_total

        # Run migration first
        migrate_to_api_total_tracking()

        # Set api_total
        test_value = 100
        set_channel_api_total(channel_id, test_value)

        # Get api_total
        result = get_channel_api_total(channel_id)
        assert result == test_value, f"Expected {test_value}, got {result}"

    def test_set_api_total_updates_timestamp(self, temp_db_with_api_total):
        """Test that set_channel_api_total updates the timestamp."""
        channel_id, db_path = temp_db_with_api_total

        # Run migration first
        migrate_to_api_total_tracking()

        # Set api_total
        set_channel_api_total(channel_id, 100)

        # Verify timestamp was set
        conn = sqlite3.connect(str(db_path))
        cur = conn.cursor()
        cur.execute("SELECT api_total_last_checked FROM Channels WHERE channel_id = ?", (channel_id,))
        result = cur.fetchone()
        conn.close()

        assert result is not None, "Timestamp should be set"
        assert result[0] is not None, "Timestamp should not be NULL"

    def test_set_api_total_handles_nonexistent_channel(self, temp_db_with_api_total):
        """Test that set_channel_api_total handles non-existent channel gracefully."""
        _, db_path = temp_db_with_api_total

        # Run migration first
        migrate_to_api_total_tracking()

        # Should not error for non-existent channel
        set_channel_api_total("UCnonexistent", 100)  # Should pass without exception

    def test_get_api_total_handles_nonexistent_channel(self, temp_db_with_api_total):
        """Test that get_channel_api_total returns None for non-existent channel."""
        _, _ = temp_db_with_api_total

        # Run migration first
        migrate_to_api_total_tracking()

        # Should return None for non-existent channel
        result = get_channel_api_total("UCnonexistent")
        assert result is None, f"Expected None for non-existent channel, got {result}"

    def test_get_api_total_handles_missing_columns(self, temp_db_with_api_total):
        """Test that get_channel_api_total returns None when columns don't exist."""
        channel_id, _ = temp_db_with_api_total

        # Don't run migration - columns don't exist
        # Should return None gracefully instead of crashing
        result = get_channel_api_total(channel_id)
        assert result is None, f"Expected None when columns missing, got {result}"


class TestApiTotalScenarios:
    """Tests for common api_total usage scenarios."""

    def test_complete_channel_detection(self, temp_db_with_api_total):
        """Test scenario: DB has all videos, api_total matches."""
        channel_id, _ = temp_db_with_api_total

        # Run migration
        migrate_to_api_total_tracking()

        # DB has 5 videos
        db_count = 5

        # API says 5 videos total
        api_total = 5
        set_channel_api_total(channel_id, api_total)

        # Stored value should match
        stored_total = get_channel_api_total(channel_id)
        assert stored_total == api_total

        # Channel is complete: db_count >= api_total
        assert db_count >= stored_total, "Channel should be detected as complete"

    def test_incomplete_channel_detection(self, temp_db_with_api_total):
        """Test scenario: DB has fewer videos than api_total (incomplete)."""
        channel_id, _ = temp_db_with_api_total

        # Run migration
        migrate_to_api_total_tracking()

        # DB has 5 videos
        db_count = 5

        # API says 10 videos total (5 missing)
        api_total = 10
        set_channel_api_total(channel_id, api_total)

        # Stored value should reflect gap
        stored_total = get_channel_api_total(channel_id)
        assert stored_total == api_total

        # Channel is incomplete: db_count < api_total
        missing_count = stored_total - db_count
        assert missing_count == 5, f"Should detect 5 missing videos, got {missing_count}"

    def test_quota_saving_scenario(self, temp_db_with_api_total):
        """Test scenario: Stored api_total avoids API call (quota saved)."""
        channel_id, _ = temp_db_with_api_total

        # Run migration
        migrate_to_api_total_tracking()

        # First run: No stored value - would need API call
        stored_total = get_channel_api_total(channel_id)
        assert stored_total is None, "First run: no stored value"

        # After API call, store the value
        api_total_from_api = 100  # Simulated API result
        set_channel_api_total(channel_id, api_total_from_api)

        # Subsequent runs: Get stored value (no API call needed)
        stored_total = get_channel_api_total(channel_id)
        assert stored_total == api_total_from_api, "Subsequent runs: value retrieved without API call"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
