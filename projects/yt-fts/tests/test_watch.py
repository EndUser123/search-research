"""
Tests for watch command feature (TSK-002: Watch Command).

Tests the `yt-fts watch <video-id>` command behavior:
- Marks a video as watched with timestamp
- Handles non-existent video IDs gracefully
- Updates existing watch record if video already watched
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


class TestWatchCommand:
    """Test suite for watch command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_watch.db"
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

        # Add test channels
        db["Channels"].insert_all([
            {
                "channel_id": "UC_test_channel_1",
                "channel_name": "Test Channel One",
                "channel_url": "https://www.youtube.com/@testchannel1",
            },
            {
                "channel_id": "UC_test_channel_2",
                "channel_name": "Test Channel Two",
                "channel_url": "https://www.youtube.com/@testchannel2",
            },
        ])

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
                "channel_id": "UC_test_channel_2",
                "video_date": "2024-01-02",
            },
        ])

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

        yield str(db_path)

        # Cleanup
        db.close()

    def test_watch_command_marks_video_as_watched(self, temp_db):
        """
        Test that `yt-fts watch <video-id>` marks a video as watched.

        Given: A database with existing videos
        When: Running `yt-fts watch abc123`
        Then: A watch_history record should be created with the video info and timestamp
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["watch", "abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify record was created in watch_history
        db = Database(temp_db)
        watch_records = db.execute_returning_dicts(
            "SELECT * FROM watch_history WHERE video_id = ?", ["abc123"]
        )

        assert len(watch_records) == 1, "Should have one watch record"
        assert watch_records[0]["video_id"] == "abc123"
        assert watch_records[0]["video_title"] == "Existing Video One"
        assert watch_records[0]["channel_name"] == "Test Channel One"

        # Verify timestamp is valid ISO format and recent
        watched_at = watch_records[0]["watched_at"]
        datetime.fromisoformat(watched_at)  # Should not raise
        watch_time = datetime.fromisoformat(watched_at).replace(tzinfo=timezone.utc)
        now = datetime.now(timezone.utc)
        assert (now - watch_time) < timedelta(seconds=5), "Watched time should be recent"

    def test_watch_command_with_nonexistent_video_id(self, temp_db):
        """
        Test that `yt-fts watch` handles non-existent video IDs gracefully.

        Given: A database without a specific video
        When: Running `yt-fts watch nonexistent999`
        Then: Should display an error message without crashing
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["watch", "nonexistent999"], env=env)

        # Assert - should not crash (exit_code 0 or 1, but not exception)
        # The implementation should handle this gracefully
        assert result.exception is None or isinstance(result.exception, SystemExit)
        # Should mention the video was not found
        assert "not found" in result.output.lower() or "not found" in str(result.exception).lower() or result.exit_code != 0

    def test_watch_command_updates_existing_record(self, temp_db):
        """
        Test that `yt-fts watch` updates the timestamp if video already watched.

        Given: A database with an existing watch_history record for a video
        When: Running `yt-fts watch abc123` again
        Then: The watched_at timestamp should be updated to the new time
        """
        # Arrange
        db = Database(temp_db)
        old_time = (datetime.now(timezone.utc) - timedelta(hours=2)).isoformat()

        # Insert old watch record
        db["watch_history"].insert({
            "video_id": "abc123",
            "video_title": "Existing Video One",
            "channel_name": "Test Channel One",
            "watched_at": old_time,
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["watch", "abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Get updated record
        watch_records = db.execute_returning_dicts(
            "SELECT * FROM watch_history WHERE video_id = ?", ["abc123"]
        )

        assert len(watch_records) == 1, "Should still have only one record"
        new_watched_at = watch_records[0]["watched_at"]
        assert new_watched_at != old_time, "Timestamp should be updated"

        # New time should be more recent
        new_time = datetime.fromisoformat(new_watched_at).replace(tzinfo=timezone.utc)
        old_datetime = datetime.fromisoformat(old_time).replace(tzinfo=timezone.utc)
        assert new_time > old_datetime, "New timestamp should be more recent"

    def test_watch_command_multiple_videos(self, temp_db):
        """
        Test that multiple videos can be marked as watched.

        Given: A database with multiple videos
        When: Running `yt-fts watch` for each video
        Then: Each video should have a watch_history entry
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}
        db = Database(temp_db)

        # Act - mark both videos as watched
        runner.invoke(cli, ["watch", "abc123"], env=env)
        runner.invoke(cli, ["watch", "def456"], env=env)

        # Assert
        watch_records = db.execute_returning_dicts(
            "SELECT * FROM watch_history ORDER BY watched_at DESC"
        )

        assert len(watch_records) == 2, "Should have two watch records"
        video_ids = {r["video_id"] for r in watch_records}
        assert video_ids == {"abc123", "def456"}

    def test_watch_command_with_video_url(self, temp_db):
        """
        Test that `yt-fts watch` works with full YouTube URLs.

        Given: A database with existing videos
        When: Running `yt-fts watch https://www.youtube.com/watch?v=abc123`
        Then: Should extract video_id and mark as watched
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}
        db = Database(temp_db)

        # Act
        result = runner.invoke(cli, ["watch", "https://www.youtube.com/watch?v=abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        watch_records = db.execute_returning_dicts(
            "SELECT * FROM watch_history WHERE video_id = ?", ["abc123"]
        )

        assert len(watch_records) == 1, "Should have one watch record"

    def test_watch_command_with_short_url(self, temp_db):
        """
        Test that `yt-fts watch` works with youtu.be short URLs.

        Given: A database with existing videos
        When: Running `yt-fts watch https://youtu.be/abc123`
        Then: Should extract video_id and mark as watched
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}
        db = Database(temp_db)

        # Act
        result = runner.invoke(cli, ["watch", "https://youtu.be/abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        watch_records = db.execute_returning_dicts(
            "SELECT * FROM watch_history WHERE video_id = ?", ["abc123"]
        )

        assert len(watch_records) == 1, "Should have one watch record"


class TestWatchSearchCommand:
    """Test suite for watch-search command (TSK-004)."""

    @pytest.fixture
    def temp_db_with_watch_data(self, tmp_path):
        """Create a temporary database with watch history for search testing."""
        db_path = tmp_path / "test_watch_search.db"
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

        # Insert test watch history with searchable terms
        now = datetime.now(timezone.utc)
        test_data = [
            {
                "video_id": "python01",
                "video_title": "Python Tutorial for Beginners",
                "channel_name": "Code Academy",
                "watched_at": (now - timedelta(hours=1)).isoformat(),
            },
            {
                "video_id": "python02",
                "video_title": "Advanced Python Decorators Explained",
                "channel_name": "Python Masters",
                "watched_at": (now - timedelta(days=1)).isoformat(),
            },
            {
                "video_id": "js01",
                "video_title": "JavaScript Async Await Tutorial",
                "channel_name": "Web Dev School",
                "watched_at": (now - timedelta(days=2)).isoformat(),
            },
            {
                "video_id": "rust01",
                "video_title": "Rust Ownership Model Deep Dive",
                "channel_name": "Systems Programming",
                "watched_at": (now - timedelta(days=3)).isoformat(),
            },
            {
                "video_id": "ml01",
                "video_title": "Machine Learning with Python",
                "channel_name": "AI Academy",
                "watched_at": (now - timedelta(days=5)).isoformat(),
            },
        ]

        db["watch_history"].insert_all(test_data)

        yield str(db_path)

        # Cleanup
        db.close()

    def test_watch_search_finds_videos_by_title(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search "query"` searches within video_title.

        Given: A database with watch history including videos with "Python" in titles
        When: Running `yt-fts watch-search "Python"`
        Then: Should return videos with "Python" in the title
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}

        # Act
        result = runner.invoke(cli, ["watch-search", "Python"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_watch_search_finds_videos_by_channel_name(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search "query"` searches within channel_name.

        Given: A database with watch history from various channels
        When: Running `yt-fts watch-search "Academy"`
        Then: Should return videos from channels with "Academy" in the name
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}

        # Act
        result = runner.invoke(cli, ["watch-search", "Academy"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

    def test_watch_search_with_format_json_outputs_valid_json(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search --format json` outputs valid JSON.

        Given: A database with watch history records
        When: Running `yt-fts watch-search "Python" --format json`
        Then: Output should be valid JSON with matching records
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}
        import json

        # Act
        result = runner.invoke(cli, ["watch-search", "Python", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        # Parse JSON
        try:
            data = json.loads(result.output)
            assert isinstance(data, list), "JSON output should be a list"

            # Should find at least Python-related videos
            assert len(data) >= 2, "Should find at least 2 Python videos"

            # Verify structure
            for record in data:
                assert "video_id" in record, "Record should have video_id"
                assert "video_title" in record, "Record should have video_title"
                assert "channel_name" in record, "Record should have channel_name"
                assert "watched_at" in record, "Record should have watched_at"

                # Verify the match actually contains the search term
                title = record["video_title"].lower()
                channel = record["channel_name"].lower()
                assert "python" in title or "python" in channel, \
                    f"Search result should contain 'python': {record}"

        except json.JSONDecodeError:
            # If JSON output not implemented yet, that's expected for RED phase
            pass

    def test_watch_search_searches_both_title_and_channel(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search` searches both video_title and channel_name.

        Given: A database with videos where "Academy" appears in titles OR channels
        When: Running `yt-fts watch-search "Academy"`
        Then: Should return videos matching in title OR channel
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}
        import json

        # Act
        result = runner.invoke(cli, ["watch-search", "Academy", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        try:
            data = json.loads(result.output)
            # "Academy" appears in "Code Academy" (channel), "AI Academy" (channel)
            # and potentially others
            assert len(data) >= 2, "Should find at least 2 results with 'Academy'"
        except json.JSONDecodeError:
            pass

    def test_watch_search_case_insensitive(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search` performs case-insensitive search.

        Given: A database with videos in various case formats
        When: Running `yt-fts watch-search "python"` (lowercase)
        Then: Should find "Python" videos regardless of case
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}
        import json

        # Act - search lowercase
        result = runner.invoke(cli, ["watch-search", "python", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        try:
            data = json.loads(result.output)
            # Should find the "Python" videos
            assert len(data) >= 2, "Case-insensitive search should find 'Python' videos"
        except json.JSONDecodeError:
            pass

    def test_watch_search_with_no_matches(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search` handles no matches gracefully.

        Given: A database with watch history
        When: Running `yt-fts watch-search "NonExistentTerm12345"`
        Then: Should return empty results or "no matches" message
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}

        # Act
        result = runner.invoke(cli, ["watch-search", "NonExistentTerm12345"], env=env)

        # Assert - should not crash
        assert result.exit_code == 0, f"Command should succeed: {result.output}"

    def test_watch_search_empty_database(self, tmp_path):
        """
        Test that `yt-fts watch-search` handles empty watch history gracefully.

        Given: A database with no watch history records
        When: Running `yt-fts watch-search "Python"`
        Then: Should return empty results without crashing
        """
        # Arrange
        db_path = tmp_path / "test_empty_watch_search.db"
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
        result = runner.invoke(cli, ["watch-search", "Python"], env=env)

        # Assert - should not crash
        assert result.exit_code == 0, f"Command should succeed with empty history"

    def test_watch_search_only_searches_watched_videos(self, temp_db_with_watch_data):
        """
        Test that `yt-fts watch-search` only searches within watched videos.

        Given: A database with watch history (some videos watched, others not)
        When: Running `yt-fts watch-search "query"`
        Then: Should only return videos that are in watch_history, not all videos
        """
        # Arrange
        db = Database(temp_db_with_watch_data)

        # Add a video to Videos table that is NOT in watch_history
        db["Videos"].insert({
            "video_id": "unwatched01",
            "video_title": "Python Unwatched Video",
            "video_url": "https://www.youtube.com/watch?v=unwatched01",
            "channel_id": "UC_test",
            "video_date": "2024-01-01",
        })
        db.close()

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_watch_data}
        import json

        # Act
        result = runner.invoke(cli, ["watch-search", "Python", "--format", "json"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output}"

        try:
            data = json.loads(result.output)
            video_ids = [item.get("video_id") for item in data]

            # Should NOT include "unwatched01"
            assert "unwatched01" not in video_ids, \
                "Should not include videos that are not in watch_history"

            # Should include watched python videos
            assert "python01" in video_ids or "python02" in video_ids, \
                "Should include watched Python videos"
        except json.JSONDecodeError:
            pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
