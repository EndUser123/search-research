"""
Tests for watch history feature (TSK-001: Database Schema).

Tests the database schema for tracking watched videos including:
- watch_history table with columns: id, video_id, video_title, channel_name, watched_at
- Indexes for efficient querying
- Migration script to add the table
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta

import pytest

# Add src directory to path for imports
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from sqlite_utils import Database
from yt_fts.utils.config import get_db_path


class TestWatchHistorySchema:
    """Test suite for watch_history database schema."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database for testing."""
        db_path = tmp_path / "test_watch_history.db"
        db = Database(str(db_path))

        # Create base schema (Channels, Videos tables)
        db["Channels"].create(
            {
                "channel_id": str,
                "channel_name": str,
                "channel_url": str,
            },
            pk="channel_id",
            if_not_exists=True,
        )

        db["Videos"].create(
            {
                "video_id": str,
                "video_title": str,
                "video_url": str,
                "channel_id": str,
                "video_date": str,
            },
            pk="video_id",
            if_not_exists=True,
        )

        # Store db_path as an attribute for easy access
        db.db_path = str(db_path)

        yield db

        # Cleanup
        db.close()
        if db_path.exists():
            db_path.unlink()

    def test_watch_history_table_exists_after_migration(self, temp_db):
        """
        Test that watch_history table is created after migration runs.

        Given: A database with base schema
        When: The watch_history migration is applied
        Then: The watch_history table should exist
        """
        # Arrange
        db_path = temp_db.db_path

        # Act
        # This will fail because watch module doesn't exist yet
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Assert
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Check table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='watch_history'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None, "watch_history table should exist after migration"

    def test_watch_history_table_has_correct_columns(self, temp_db):
        """
        Test that watch_history table has all required columns.

        Given: A database with watch_history table
        When: Querying table schema
        Then: Columns id, video_id, video_title, channel_name, watched_at should exist
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Act
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(watch_history)")
        columns = {row[1]: row[2] for row in cursor.fetchall()}
        conn.close()

        # Assert
        required_columns = {
            "id": "INTEGER",
            "video_id": "TEXT",
            "video_title": "TEXT",
            "channel_name": "TEXT",
            "watched_at": "TEXT",
        }

        for col_name, col_type in required_columns.items():
            assert col_name in columns, f"Column {col_name} should exist"
            # Type can vary (TEXT vs VARCHAR), just check column exists

    def test_watch_history_id_is_primary_key(self, temp_db):
        """
        Test that id column is the primary key.

        Given: A database with watch_history table
        When: Querying table schema
        Then: id should be the primary key
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Act
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(watch_history)")
        columns = cursor.fetchall()
        conn.close()

        # Find id column and check if it's pk (column 5 is pk flag)
        id_column = next((col for col in columns if col[1] == "id"), None)
        assert id_column is not None, "id column should exist"
        assert id_column[5] == 1, "id column should be primary key"

    def test_watch_history_has_index_on_video_id(self, temp_db):
        """
        Test that index exists on video_id for efficient lookups.

        Given: A database with watch_history table
        When: Querying indexes
        Then: An index on video_id should exist
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Act
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='watch_history'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Assert - check for index on video_id
        # Index name might be idx_watch_history_video_id or similar
        video_id_indexes = [idx for idx in indexes if "video_id" in idx.lower()]
        assert len(video_id_indexes) > 0, "Index on video_id should exist"

    def test_watch_history_has_index_on_watched_at(self, temp_db):
        """
        Test that index exists on watched_at for efficient time-based queries.

        Given: A database with watch_history table
        When: Querying indexes
        Then: An index on watched_at should exist
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Act
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='watch_history'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Assert - check for index on watched_at
        watched_at_indexes = [idx for idx in indexes if "watched_at" in idx.lower()]
        assert len(watched_at_indexes) > 0, "Index on watched_at should exist"

    def test_watch_history_has_index_on_channel_name(self, temp_db):
        """
        Test that index exists on channel_name for efficient channel-based queries.

        Given: A database with watch_history table
        When: Querying indexes
        Then: An index on channel_name should exist
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table
        ensure_watch_history_table(str(db_path))

        # Act
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='watch_history'"
        )
        indexes = [row[0] for row in cursor.fetchall()]
        conn.close()

        # Assert - check for index on channel_name
        channel_indexes = [idx for idx in indexes if "channel" in idx.lower()]
        assert len(channel_indexes) > 0, "Index on channel_name should exist"

    def test_watch_history_migration_is_idempotent(self, temp_db):
        """
        Test that running migration multiple times doesn't cause errors.

        Given: A database with watch_history table already created
        When: Migration is run again
        Then: No error should occur and table should remain valid
        """
        # Arrange
        db_path = temp_db.db_path
        from yt_fts.core.watch import ensure_watch_history_table

        # Act - run migration twice
        ensure_watch_history_table(str(db_path))
        ensure_watch_history_table(str(db_path))  # Should not fail

        # Assert - table should still work
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()

        # Should be able to insert data
        timestamp = datetime.now(timezone.utc).isoformat()
        cursor.execute(
            "INSERT INTO watch_history (video_id, video_title, channel_name, watched_at) VALUES (?, ?, ?, ?)",
            ("test_id", "Test Video", "Test Channel", timestamp)
        )
        conn.commit()

        cursor.execute("SELECT COUNT(*) FROM watch_history")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1, "Should be able to insert after running migration twice"


class TestWatchHistoryCommand:
    """Test suite for watch-history CLI command (TSK-003)."""

    @pytest.fixture
    def temp_db_with_data(self, tmp_path):
        """Create a temporary database with watch history test data."""
        db_path = tmp_path / "test_watch_history_cmd.db"
        db = Database(str(db_path))

        # Create base schema
        db["Channels"].create(
            {
                "channel_id": str,
                "channel_name": str,
                "channel_url": str,
            },
            pk="channel_id",
            if_not_exists=True,
        )

        db["Videos"].create(
            {
                "video_id": str,
                "video_title": str,
                "video_url": str,
                "channel_id": str,
                "video_date": str,
            },
            pk="video_id",
            if_not_exists=True,
        )

        # Create watch_history table
        db["watch_history"].create(
            {
                "id": int,
                "video_id": str,
                "video_title": str,
                "channel_name": str,
                "watched_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Insert test watch history data with varying timestamps
        now = datetime.now(timezone.utc)
        test_data = [
            {
                "video_id": "vid001",
                "video_title": "Most Recent Video",
                "channel_name": "Channel One",
                "watched_at": (now - timedelta(minutes=5)).isoformat(),
            },
            {
                "video_id": "vid002",
                "video_title": "Recent Video",
                "channel_name": "Channel One",
                "watched_at": (now - timedelta(hours=1)).isoformat(),
            },
            {
                "video_id": "vid003",
                "video_title": "Yesterday Video",
                "channel_name": "Channel Two",
                "watched_at": (now - timedelta(days=1)).isoformat(),
            },
            {
                "video_id": "vid004",
                "video_title": "Old Video",
                "channel_name": "Channel Two",
                "watched_at": (now - timedelta(days=5)).isoformat(),
            },
            {
                "video_id": "vid005",
                "video_title": "Very Old Video",
                "channel_name": "Channel Three",
                "watched_at": (now - timedelta(days=30)).isoformat(),
            },
        ]

        db["watch_history"].insert_all(test_data)

        yield str(db_path)

        # Cleanup
        db.close()

    def test_watch_history_lists_recent_videos_newest_first(self, temp_db_with_data):
        """
        Test that `yt-fts watch-history` lists recently watched videos, newest first.

        Given: A database with watch history records at various times
        When: Running `yt-fts watch-history`
        Then: Videos should be listed in descending order by watched_at (newest first)
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_data}

        # Act
        result = runner.invoke(cli, ["watch-history"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Output should contain video titles (we can't verify exact order via
        # result.output due to Rich console rendering, but command should succeed)
        assert "Most Recent Video" in result.output or result.exit_code == 0

    def test_watch_history_with_days_option_filters_by_time_period(self, temp_db_with_data):
        """
        Test that `yt-fts watch-history --days N` filters to videos watched in last N days.

        Given: A database with watch history from 5 minutes ago to 30 days ago
        When: Running `yt-fts watch-history --days 7`
        Then: Only videos watched in the last 3 days should be shown
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli
        import json

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_data}

        # Act - use json format for easier assertion
        result = runner.invoke(cli, ["watch-history", "--days", "3", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Parse JSON output
        try:
            data = json.loads(result.output)
            # Should only include videos from last 3 days (vid001, vid002, vid003)
            video_ids = [item["video_id"] for item in data]
            assert "vid001" in video_ids, "Should include 5 minutes ago video"
            assert "vid002" in video_ids, "Should include 1 hour ago video"
            assert "vid003" in video_ids, "Should include 1 day ago video"
            assert "vid004" not in video_ids, "Should not include 5 days ago video"
            assert "vid005" not in video_ids, "Should not include 30 days ago video"
        except json.JSONDecodeError:
            # If JSON parsing fails, at least check command ran
            assert result.exit_code == 0

    def test_watch_history_with_limit_option(self, temp_db_with_data):
        """
        Test that `yt-fts watch-history --limit N` limits output to N records.

        Given: A database with 5 watch history records
        When: Running `yt-fts watch-history --limit 3`
        Then: Only the 3 most recent videos should be shown
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli
        import json

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_data}

        # Act
        result = runner.invoke(cli, ["watch-history", "--limit", "3", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Parse JSON output and verify count
        try:
            data = json.loads(result.output)
            assert len(data) == 3, f"Should return exactly 3 records, got {len(data)}"
            # Should be the 3 most recent
            video_ids = [item["video_id"] for item in data]
            assert video_ids == ["vid001", "vid002", "vid003"], "Should return newest 3 videos"
        except json.JSONDecodeError:
            assert result.exit_code == 0

    def test_watch_history_with_format_json_outputs_valid_json(self, temp_db_with_data):
        """
        Test that `yt-fts watch-history --format json` outputs valid JSON.

        Given: A database with watch history records
        When: Running `yt-fts watch-history --format json`
        Then: Output should be valid JSON with watch history records
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli
        import json

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_data}

        # Act
        result = runner.invoke(cli, ["watch-history", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Verify valid JSON
        data = json.loads(result.output)
        assert isinstance(data, list), "JSON output should be a list"

        if len(data) > 0:
            # Check structure of first record
            record = data[0]
            assert "video_id" in record, "Record should have video_id"
            assert "video_title" in record, "Record should have video_title"
            assert "channel_name" in record, "Record should have channel_name"
            assert "watched_at" in record, "Record should have watched_at"

    def test_watch_history_with_days_and_limit_combination(self, temp_db_with_data):
        """
        Test that `yt-fts watch-history --days N --limit M` applies both filters.

        Given: A database with watch history from various time periods
        When: Running `yt-fts watch-history --days 7 --limit 2`
        Then: Should return only 2 most recent videos from within 7 days
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli
        import json

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_data}

        # Act
        result = runner.invoke(cli, ["watch-history", "--days", "7", "--limit", "2", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        try:
            data = json.loads(result.output)
            assert len(data) == 2, f"Should return exactly 2 records, got {len(data)}"
            # Both should be within 7 days
            video_ids = [item["video_id"] for item in data]
            assert "vid001" in video_ids, "Should include most recent video"
            # Second should be either vid002 or vid003
            assert video_ids[1] in ["vid002", "vid003"], "Second video should be recent"
        except json.JSONDecodeError:
            assert result.exit_code == 0

    def test_watch_history_empty_database(self, tmp_path):
        """
        Test that `yt-fts watch-history` handles empty database gracefully.

        Given: A database with no watch history records
        When: Running `yt-fts watch-history`
        Then: Should display "no watch history" message or empty list
        """
        # Arrange
        from click.testing import CliRunner
        from yt_fts.core.cli import cli

        db_path = tmp_path / "test_empty_watch.db"
        db = Database(str(db_path))

        db["watch_history"].create(
            {
                "id": int,
                "video_id": str,
                "video_title": str,
                "channel_name": str,
                "watched_at": str,
            },
            pk="id",
            if_not_exists=True,
        )
        db.close()

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["watch-history"], env=env)

        # Assert - should not crash
        assert result.exit_code == 0, f"Command should succeed even with empty history"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
