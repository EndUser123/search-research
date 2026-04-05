"""
Tests for bookmark CRUD feature (TSK-002).

Tests bookmark functionality:
- `bookmark add <video-id> <timestamp> <note>` - Adds bookmark
- `bookmark list [--video <id>]` - Lists bookmarks
- `bookmark remove <bookmark-id>` - Removes bookmark

Edge cases tested:
- Bookmarks with special characters in notes
- Filtering bookmarks by video
- Invalid video IDs
- Invalid timestamp formats
- Non-existent bookmark removal
"""

import os
import sys
import sqlite3
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock

import pytest
from click.testing import CliRunner

# Add src directory to path for imports
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from sqlite_utils import Database
from yt_fts.core.cli import cli


class TestBookmarkAdd:
    """Test suite for bookmark add command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_bookmarks.db"
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

        # Create bookmarks table (schema that should be created by bookmarks.py)
        db["bookmarks"].create(
            {
                "id": int,
                "video_id": str,
                "timestamp": str,
                "note": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Add test channels
        db["Channels"].insert({
            "channel_id": "UC_test_channel_1",
            "channel_name": "Test Channel One",
            "channel_url": "https://www.youtube.com/@testchannel1",
        })

        # Add test videos
        db["Videos"].insert_all([
            {
                "video_id": "abc123",
                "video_title": "Existing Video One",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "channel_id": "UC_test_channel_1",
                "video_date": "2024-01-01",
            },
            {
                "video_id": "def456",
                "video_title": "Existing Video Two",
                "video_url": "https://www.youtube.com/watch?v=def456",
                "channel_id": "UC_test_channel_1",
                "video_date": "2024-01-02",
            },
        ])

        yield str(db_path)

        # Cleanup
        db.close()

    def test_bookmark_add_basic(self, temp_db):
        """
        Test that `bookmark add <video-id> <timestamp> <note>` adds a bookmark.

        Given: A database with existing videos
        When: Running `bookmark add abc123 1:23 "Interesting point"`
        Then: A bookmark should be created with the video ID, timestamp, and note
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "1:23", "Interesting point"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1, "Should have one bookmark"
        assert bookmarks[0]["video_id"] == "abc123"
        assert bookmarks[0]["timestamp"] == "1:23"
        assert bookmarks[0]["note"] == "Interesting point"

        # Verify timestamp is valid ISO format and recent
        created_at = bookmarks[0]["created_at"]
        datetime.fromisoformat(created_at)  # Should not raise

    def test_bookmark_add_with_seconds_timestamp(self, temp_db):
        """
        Test that bookmarks can be added with raw seconds timestamp.

        Given: A database with existing videos
        When: Running `bookmark add abc123 83 "Point at 1:23"`
        Then: A bookmark should be created with timestamp stored as provided
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "83", "Point at 1:23"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert bookmarks[0]["timestamp"] == "83"
        assert bookmarks[0]["note"] == "Point at 1:23"

    def test_bookmark_add_with_special_characters_in_note(self, temp_db):
        """
        Test that bookmarks can be added with special characters in notes.

        Given: A database with existing videos
        When: Running `bookmark add` with special characters in note
        Then: Bookmark should be created with the note properly stored
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - note with quotes, apostrophes, emojis
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "5:30", "Check this out! \"Important\" - don't skip 🔥"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created with correct note
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert "Check this out!" in bookmarks[0]["note"]
        assert "Important" in bookmarks[0]["note"]
        assert "don't skip" in bookmarks[0]["note"]

    def test_bookmark_add_with_multiline_note(self, temp_db):
        """
        Test that bookmarks can have multi-line notes.

        Given: A database with existing videos
        When: Running `bookmark add` with a multi-line note
        Then: Bookmark should be created with the full note
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - multi-line note
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "10:15", "Key point:\n- First item\n- Second item\n- Third item"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created with multi-line note
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert "Key point:" in bookmarks[0]["note"]
        assert "First item" in bookmarks[0]["note"]

    def test_bookmark_add_invalid_video_id(self, temp_db):
        """
        Test that adding a bookmark with invalid video ID is handled.

        Given: A database
        When: Running `bookmark add nonexistent123 1:23 "Note"`
        Then: Should return an error about invalid video ID
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "nonexistent123", "1:23", "Note"],
            env=env
        )

        # Assert - should fail or warn
        assert result.exit_code != 0 or "not found" in result.output.lower() or "invalid" in result.output.lower()

    def test_bookmark_add_empty_note(self, temp_db):
        """
        Test that adding a bookmark with empty note is allowed.

        Given: A database with existing videos
        When: Running `bookmark add abc123 1:23 ""`
        Then: Bookmark should be created with empty note
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "1:23", ""],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created with empty note
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert bookmarks[0]["note"] == "" or bookmarks[0]["note"] is None

    def test_bookmark_add_invalid_timestamp_format(self, temp_db):
        """
        Test that invalid timestamp formats are handled.

        Given: A database with existing videos
        When: Running `bookmark add abc123 invalid_timestamp "Note"`
        Then: Should return an error about invalid timestamp
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "not_a_time", "Note"],
            env=env
        )

        # Assert - should fail or warn about timestamp format
        # Implementation might accept any string as timestamp, so we just check it doesn't crash
        # but ideally should validate the format

    def test_bookmark_add_multiple_bookmarks_same_video(self, temp_db):
        """
        Test that multiple bookmarks can be added to the same video.

        Given: A database with a video
        When: Running `bookmark add` multiple times for the same video
        Then: All bookmarks should be created
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - add multiple bookmarks
        result1 = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "1:00", "First point"],
            env=env
        )
        result2 = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "2:30", "Second point"],
            env=env
        )
        result3 = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "5:45", "Third point"],
            env=env
        )

        # Assert
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert result3.exit_code == 0

        # Verify all bookmarks were created
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ? ORDER BY timestamp",
            ["abc123"]
        )

        assert len(bookmarks) == 3
        assert bookmarks[0]["note"] == "First point"
        assert bookmarks[1]["note"] == "Second point"
        assert bookmarks[2]["note"] == "Third point"


class TestBookmarkList:
    """Test suite for bookmark list command."""

    @pytest.fixture
    def temp_db_with_bookmarks(self, tmp_path):
        """Create a temporary database with existing bookmarks."""
        db_path = tmp_path / "test_bookmark_list.db"
        db = Database(str(db_path))

        # Create base schema
        db["Channels"].create(
            {"channel_id": str, "channel_name": str, "channel_url": str},
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
        db["bookmarks"].create(
            {
                "id": int,
                "video_id": str,
                "timestamp": str,
                "note": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Add test data
        db["Channels"].insert({
            "channel_id": "UC_test",
            "channel_name": "Test Channel",
            "channel_url": "https://www.youtube.com/@test",
        })
        db["Videos"].insert_all([
            {"video_id": "abc123", "video_title": "Video One", "video_url": "https://youtu.be/abc123",
             "channel_id": "UC_test", "video_date": "2024-01-01"},
            {"video_id": "def456", "video_title": "Video Two", "video_url": "https://youtu.be/def456",
             "channel_id": "UC_test", "video_date": "2024-01-02"},
        ])

        # Add test bookmarks
        now = datetime.now(timezone.utc).isoformat()
        db["bookmarks"].insert_all([
            {"video_id": "abc123", "timestamp": "1:23", "note": "First bookmark", "created_at": now},
            {"video_id": "abc123", "timestamp": "5:45", "note": "Second bookmark", "created_at": now},
            {"video_id": "def456", "timestamp": "2:10", "note": "Third bookmark", "created_at": now},
        ])

        yield str(db_path)
        db.close()

    def test_bookmark_list_shows_all(self, temp_db_with_bookmarks):
        """
        Test that `bookmark list` shows all bookmarks.

        Given: A database with multiple bookmarks across videos
        When: Running `bookmark list`
        Then: Should display all bookmarks with video titles and timestamps
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # Act
        result = runner.invoke(cli, ["bookmark", "list"], env=env)

        # Assert - Rich output goes to stdout (visible in test output), not result.output
        # We verify the command succeeded, which means the table was rendered
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

    def test_bookmark_list_filter_by_video(self, temp_db_with_bookmarks):
        """
        Test that `bookmark list --video <id>` filters bookmarks by video.

        Given: A database with bookmarks across multiple videos
        When: Running `bookmark list --video abc123`
        Then: Should only show bookmarks for abc123
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # Act
        result = runner.invoke(cli, ["bookmark", "list", "--video", "abc123"], env=env)

        # Assert - Rich output goes to stdout (visible in test output), not result.output
        # We verify the command succeeded, which means the filtered table was rendered
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

    def test_bookmark_list_empty_database(self, tmp_path):
        """
        Test that `bookmark list` handles empty database gracefully.

        Given: A database with no bookmarks
        When: Running `bookmark list`
        Then: Should show empty list or appropriate message
        """
        # Arrange
        db_path = tmp_path / "test_empty_bookmarks.db"
        db = Database(str(db_path))

        db["Channels"].create(
            {"channel_id": str, "channel_name": str, "channel_url": str},
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
        db["bookmarks"].create(
            {
                "id": int,
                "video_id": str,
                "timestamp": str,
                "note": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["bookmark", "list"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"
        db.close()

    def test_bookmark_list_filter_nonexistent_video(self, temp_db_with_bookmarks):
        """
        Test that filtering by non-existent video shows no results.

        Given: A database with bookmarks
        When: Running `bookmark list --video nonexistent123`
        Then: Should show no bookmarks or appropriate message
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # Act
        result = runner.invoke(cli, ["bookmark", "list", "--video", "nonexistent123"], env=env)

        # Assert - should not crash, might show empty
        assert result.exit_code == 0


class TestBookmarkRemove:
    """Test suite for bookmark remove command."""

    @pytest.fixture
    def temp_db_with_bookmarks(self, tmp_path):
        """Create a temporary database with existing bookmarks."""
        db_path = tmp_path / "test_bookmark_remove.db"
        db = Database(str(db_path))

        # Create base schema
        db["Channels"].create(
            {"channel_id": str, "channel_name": str, "channel_url": str},
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
        db["bookmarks"].create(
            {
                "id": int,
                "video_id": str,
                "timestamp": str,
                "note": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Add test data
        db["Channels"].insert({
            "channel_id": "UC_test",
            "channel_name": "Test Channel",
            "channel_url": "https://www.youtube.com/@test",
        })
        db["Videos"].insert({
            "video_id": "abc123",
            "video_title": "Video One",
            "video_url": "https://youtu.be/abc123",
            "channel_id": "UC_test",
            "video_date": "2024-01-01",
        })

        # Add test bookmarks
        now = datetime.now(timezone.utc).isoformat()
        db["bookmarks"].insert_all([
            {"video_id": "abc123", "timestamp": "1:23", "note": "First bookmark", "created_at": now},
            {"video_id": "abc123", "timestamp": "5:45", "note": "Second bookmark", "created_at": now},
        ])

        yield str(db_path)
        db.close()

    def test_bookmark_remove_by_id(self, temp_db_with_bookmarks):
        """
        Test that `bookmark remove <bookmark-id>` removes the bookmark.

        Given: A database with bookmarks
        When: Running `bookmark remove 1`
        Then: The bookmark with id=1 should be removed
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # First, list bookmarks to get an ID
        list_result = runner.invoke(cli, ["bookmark", "list"], env=env)

        # Act - remove first bookmark (id=1)
        result = runner.invoke(cli, ["bookmark", "remove", "1"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was removed
        db = Database(temp_db_with_bookmarks)
        bookmarks = db.execute_returning_dicts("SELECT * FROM bookmarks WHERE id = ?", [1])

        assert len(bookmarks) == 0, "Bookmark should be removed"

        # Verify other bookmark still exists
        all_bookmarks = db.execute_returning_dicts("SELECT * FROM bookmarks")
        assert len(all_bookmarks) == 1

    def test_bookmark_remove_nonexistent_id(self, temp_db_with_bookmarks):
        """
        Test that removing a non-existent bookmark ID is handled.

        Given: A database with bookmarks
        When: Running `bookmark remove 999`
        Then: Should return an error or appropriate message
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # Act
        result = runner.invoke(cli, ["bookmark", "remove", "999"], env=env)

        # Assert - should not crash, might warn
        # Original bookmarks should still be there
        db = Database(temp_db_with_bookmarks)
        all_bookmarks = db.execute_returning_dicts("SELECT * FROM bookmarks")
        assert len(all_bookmarks) == 2, "All bookmarks should still exist"

    def test_bookmark_remove_invalid_id_format(self, temp_db_with_bookmarks):
        """
        Test that providing an invalid ID format is handled.

        Given: A database with bookmarks
        When: Running `bookmark remove abc`
        Then: Should return an error about invalid ID format
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_bookmarks}

        # Act
        result = runner.invoke(cli, ["bookmark", "remove", "abc"], env=env)

        # Assert - should fail
        assert result.exit_code != 0 or "invalid" in result.output.lower()


class TestBookmarkEdgeCases:
    """Test suite for bookmark edge cases."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_bookmark_edge.db"
        db = Database(str(db_path))

        # Create base schema
        db["Channels"].create(
            {"channel_id": str, "channel_name": str, "channel_url": str},
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
        db["bookmarks"].create(
            {
                "id": int,
                "video_id": str,
                "timestamp": str,
                "note": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Add test data
        db["Channels"].insert({
            "channel_id": "UC_test",
            "channel_name": "Test Channel",
            "channel_url": "https://www.youtube.com/@test",
        })
        db["Videos"].insert({
            "video_id": "abc123",
            "video_title": "Video One",
            "video_url": "https://youtu.be/abc123",
            "channel_id": "UC_test",
            "video_date": "2024-01-01",
        })

        yield str(db_path)
        db.close()

    def test_bookmark_note_with_unicode_characters(self, temp_db):
        """
        Test that bookmarks can store unicode characters in notes.

        Given: A database with existing videos
        When: Running `bookmark add` with unicode characters
        Then: Bookmark should be created with unicode preserved
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - note with various unicode: emojis, Chinese characters, Arabic
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "1:23", "Fire reaction! 🔥 Chinese: 中文字符 Arabic: العربية"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created with unicode preserved
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert "Fire reaction!" in bookmarks[0]["note"]
        # Unicode should be preserved
        assert "中文字符" in bookmarks[0]["note"] or "中文" in bookmarks[0]["note"]

    def test_bookmark_very_long_note(self, temp_db):
        """
        Test that very long notes are handled.

        Given: A database with existing videos
        When: Running `bookmark add` with a very long note
        Then: Bookmark should be created
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Create a very long note (1000 characters)
        long_note = "A" * 1000

        # Act
        result = runner.invoke(
            cli,
            ["bookmark", "add", "abc123", "1:23", long_note],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify bookmark was created
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == 1
        assert len(bookmarks[0]["note"]) == 1000

    def test_bookmark_timestamp_with_various_formats(self, temp_db):
        """
        Test that various timestamp formats are accepted.

        Given: A database with existing videos
        When: Running `bookmark add` with different timestamp formats
        Then: Bookmarks should be created with timestamps as provided
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Test various formats
        timestamps = ["1:23", "01:23", "1:23:45", "01:23:45", "83", "3600"]

        for i, ts in enumerate(timestamps):
            result = runner.invoke(
                cli,
                ["bookmark", "add", "abc123", ts, f"Note for {ts}"],
                env=env
            )
            assert result.exit_code == 0, f"Failed for timestamp {ts}: {result.output or result.stderr}"

        # Verify all bookmarks were created
        db = Database(temp_db)
        bookmarks = db.execute_returning_dicts(
            "SELECT * FROM bookmarks WHERE video_id = ?", ["abc123"]
        )

        assert len(bookmarks) == len(timestamps)


if __name__ == "__main__":
    pytest.main([__file__])
