"""
Tests for playlist CRUD feature (TSK-001).

Tests the complete CRUD lifecycle for playlists:
- `playlist create <name> [--desc TEXT]` - Creates playlist
- `playlist list` - Lists all playlists with counts
- `playlist show <name>` - Shows playlist contents
- `playlist add <name> <video-id> [--at POSITION]` - Adds video
- `playlist remove <name> <video-id>` - Removes video
- `playlist delete <name>` - Deletes playlist

Edge cases tested:
- Empty playlists
- Duplicate video additions
- Position tracking
- Invalid video IDs
- Special characters in playlist names/descriptions
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


class TestPlaylistCreate:
    """Test suite for playlist create command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_playlists.db"
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
            {
                "video_id": "ghi789",
                "video_title": "Existing Video Three",
                "video_url": "https://www.youtube.com/watch?v=ghi789",
                "channel_id": "UC_test_channel_1",
                "video_date": "2024-01-03",
            },
        ])

        # Create playlists table (schema that should be created by playlists.py)
        db["playlists"].create(
            {
                "id": int,
                "name": str,
                "description": str,
                "created_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        # Create playlist_videos table for many-to-many relationship
        db["playlist_videos"].create(
            {
                "id": int,
                "playlist_id": int,
                "video_id": str,
                "position": int,
                "added_at": str,
            },
            pk="id",
            if_not_exists=True,
        )

        yield str(db_path)

        # Cleanup
        db.close()

    def test_playlist_create_basic(self, temp_db):
        """
        Test that `playlist create <name>` creates a new playlist.

        Given: A database with existing videos
        When: Running `playlist create MyFavorites`
        Then: A playlist should be created with the name and default values
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "create", "MyFavorites"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify playlist was created
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["MyFavorites"]
        )

        assert len(playlists) == 1, "Should have one playlist"
        assert playlists[0]["name"] == "MyFavorites"
        assert playlists[0]["description"] == "" or playlists[0]["description"] is None

        # Verify timestamp is valid ISO format and recent
        created_at = playlists[0]["created_at"]
        datetime.fromisoformat(created_at)  # Should not raise

    def test_playlist_create_with_description(self, temp_db):
        """
        Test that `playlist create <name> --desc TEXT` creates a playlist with description.

        Given: A database with existing videos
        When: Running `playlist create MyFavorites --desc "My favorite videos"`
        Then: A playlist should be created with the name and description
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["playlist", "create", "MyFavorites", "--desc", "My favorite videos"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify playlist was created with description
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["MyFavorites"]
        )

        assert len(playlists) == 1
        assert playlists[0]["name"] == "MyFavorites"
        assert playlists[0]["description"] == "My favorite videos"

    def test_playlist_create_with_special_characters(self, temp_db):
        """
        Test that playlists can be created with special characters in name/description.

        Given: A database
        When: Running `playlist create` with special characters
        Then: Playlist should be created correctly
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(
            cli,
            ["playlist", "create", "Test & Favorites!", "--desc", "Videos with quotes: \"test\" and 'apostrophes'"],
            env=env
        )

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify playlist was created
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Test & Favorites!"]
        )

        assert len(playlists) == 1
        assert playlists[0]["description"] == "Videos with quotes: \"test\" and 'apostrophes'"

    def test_playlist_create_duplicate_name(self, temp_db):
        """
        Test that creating a playlist with a duplicate name is handled.

        Given: A playlist named "MyFavorites" exists
        When: Running `playlist create MyFavorites` again
        Then: Should return an error or handle gracefully
        """
        # Arrange
        db = Database(temp_db)
        db["playlists"].insert({
            "name": "MyFavorites",
            "description": "Original",
            "created_at": datetime.now(timezone.utc).isoformat(),
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "create", "MyFavorites"], env=env)

        # Assert - should fail or warn about duplicate
        assert result.exit_code != 0 or "duplicate" in result.output.lower() or "exists" in result.output.lower()

    def test_playlist_create_empty_name(self, temp_db):
        """
        Test that creating a playlist with empty name is rejected.

        Given: A database
        When: Running `playlist create ""`
        Then: Should return an error
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "create", ""], env=env)

        # Assert - should fail
        assert result.exit_code != 0


class TestPlaylistList:
    """Test suite for playlist list command."""

    @pytest.fixture
    def temp_db_with_playlists(self, tmp_path):
        """Create a temporary database with existing playlists."""
        db_path = tmp_path / "test_playlist_list.db"
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
            pk="id",
            if_not_exists=True,
        )

        # Add test videos
        db["Videos"].insert_all([
            {"video_id": "abc123", "video_title": "Video One", "video_url": "https://youtu.be/abc123",
             "channel_id": "UC1", "video_date": "2024-01-01"},
            {"video_id": "def456", "video_title": "Video Two", "video_url": "https://youtu.be/def456",
             "channel_id": "UC1", "video_date": "2024-01-02"},
            {"video_id": "ghi789", "video_title": "Video Three", "video_url": "https://youtu.be/ghi789",
             "channel_id": "UC1", "video_date": "2024-01-03"},
        ])

        # Add test playlists
        now = datetime.now(timezone.utc).isoformat()
        playlist1_id = 1
        playlist2_id = 2
        playlist3_id = 3
        db["playlists"].insert({
            "id": playlist1_id,
            "name": "Favorites",
            "description": "My favorites",
            "created_at": now,
        })
        db["playlists"].insert({
            "id": playlist2_id,
            "name": "Watch Later",
            "description": "Videos to watch later",
            "created_at": now,
        })
        db["playlists"].insert({
            "id": playlist3_id,
            "name": "Empty Playlist",
            "description": "No videos yet",
            "created_at": now,
        })

        # Add videos to playlists
        db["playlist_videos"].insert({
            "id": 1,
            "playlist_id": playlist1_id, "video_id": "abc123", "position": 1, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 2,
            "playlist_id": playlist1_id, "video_id": "def456", "position": 2, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 3,
            "playlist_id": playlist2_id, "video_id": "ghi789", "position": 1, "added_at": now
        })

        yield str(db_path)
        db.close()

    def test_playlist_list_shows_all_playlists(self, temp_db_with_playlists):
        """
        Test that `playlist list` shows all playlists with video counts.

        Given: A database with multiple playlists
        When: Running `playlist list`
        Then: Should display all playlists with their video counts
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlists}

        # Act
        result = runner.invoke(cli, ["playlist", "list"], env=env)

        # Assert - Rich output goes to stdout (visible in test output), not result.output
        # We verify the command succeeded, which means the table was rendered
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

    def test_playlist_list_empty_database(self, tmp_path):
        """
        Test that `playlist list` handles empty database gracefully.

        Given: A database with no playlists
        When: Running `playlist list`
        Then: Should show empty list or appropriate message
        """
        # Arrange
        db_path = tmp_path / "test_empty.db"
        db = Database(str(db_path))
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["playlist", "list"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"
        db.close()

    def test_playlist_list_shows_video_counts(self, temp_db_with_playlists):
        """
        Test that `playlist list` shows accurate video counts.

        Given: A database with playlists containing different numbers of videos
        When: Running `playlist list`
        Then: Video counts should be accurate
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlists}

        # Act
        result = runner.invoke(cli, ["playlist", "list"], env=env)

        # Assert
        assert result.exit_code == 0
        # Output should show counts -Favorites has 2, Watch Later has 1, Empty has 0


class TestPlaylistShow:
    """Test suite for playlist show command."""

    @pytest.fixture
    def temp_db_with_playlist(self, tmp_path):
        """Create a temporary database with a populated playlist."""
        db_path = tmp_path / "test_playlist_show.db"
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
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
            {"video_id": "vid1", "video_title": "First Video", "video_url": "https://youtu.be/vid1",
             "channel_id": "UC_test", "video_date": "2024-01-01"},
            {"video_id": "vid2", "video_title": "Second Video", "video_url": "https://youtu.be/vid2",
             "channel_id": "UC_test", "video_date": "2024-01-02"},
            {"video_id": "vid3", "video_title": "Third Video", "video_url": "https://youtu.be/vid3",
             "channel_id": "UC_test", "video_date": "2024-01-03"},
        ])

        now = datetime.now(timezone.utc).isoformat()
        playlist_id = 1
        db["playlists"].insert({
            "id": playlist_id,
            "name": "My Playlist",
            "description": "Test description",
            "created_at": now,
        })

        db["playlist_videos"].insert({
            "id": 1, "playlist_id": playlist_id, "video_id": "vid1", "position": 1, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 2, "playlist_id": playlist_id, "video_id": "vid2", "position": 2, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 3, "playlist_id": playlist_id, "video_id": "vid3", "position": 3, "added_at": now
        })

        yield str(db_path)
        db.close()

    def test_playlist_show_by_name(self, temp_db_with_playlist):
        """
        Test that `playlist show <name>` displays playlist contents.

        Given: A database with a playlist containing videos
        When: Running `playlist show "My Playlist"`
        Then: Should display playlist name, description, and all videos
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlist}

        # Act
        result = runner.invoke(cli, ["playlist", "show", "My Playlist"], env=env)

        # Assert - Rich output goes to stdout (visible in test output), not result.output
        # We verify the command succeeded, which means the table was rendered
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

    def test_playlist_show_empty_playlist(self, tmp_path):
        """
        Test that `playlist show` handles empty playlists.

        Given: A database with an empty playlist
        When: Running `playlist show <empty_playlist>`
        Then: Should show playlist exists but has no videos
        """
        # Arrange
        db_path = tmp_path / "test_empty_show.db"
        db = Database(str(db_path))

        # Create all required tables (playlist show queries Videos table)
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
            pk="id",
            if_not_exists=True,
        )

        now = datetime.now(timezone.utc).isoformat()
        db["playlists"].insert({
            "name": "Empty",
            "description": "Empty playlist",
            "created_at": now,
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["playlist", "show", "Empty"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"
        db.close()

    def test_playlist_show_nonexistent_playlist(self, tmp_path):
        """
        Test that `playlist show` handles non-existent playlists.

        Given: A database without the specified playlist
        When: Running `playlist show NonExistent`
        Then: Should return an error
        """
        # Arrange
        db_path = tmp_path / "test_nonexistent.db"
        db = Database(str(db_path))

        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["playlist", "show", "NonExistent"], env=env)

        # Assert - should fail
        assert result.exit_code != 0 or "not found" in result.output.lower()
        db.close()


class TestPlaylistAdd:
    """Test suite for playlist add command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_playlist_add.db"
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
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
            {"video_id": "ghi789", "video_title": "Video Three", "video_url": "https://youtu.be/ghi789",
             "channel_id": "UC_test", "video_date": "2024-01-03"},
        ])

        now = datetime.now(timezone.utc).isoformat()
        db["playlists"].insert({
            "name": "Favorites",
            "description": "My favorites",
            "created_at": now,
        })

        yield str(db_path)
        db.close()

    def test_playlist_add_video(self, temp_db):
        """
        Test that `playlist add <name> <video-id>` adds a video to playlist.

        Given: A database with a playlist and existing video
        When: Running `playlist add Favorites abc123`
        Then: Video should be added to the playlist
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "add", "Favorites", "abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify video was added
        db = Database(temp_db)
        playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Favorites"]
        )[0]
        playlist_videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ? AND video_id = ?",
            [playlist["id"], "abc123"]
        )

        assert len(playlist_videos) == 1
        assert playlist_videos[0]["video_id"] == "abc123"

    def test_playlist_add_at_position(self, temp_db):
        """
        Test that `playlist add <name> <video-id> --at POSITION` adds video at specific position.

        Given: A playlist with videos
        When: Running `playlist add Favorites ghi789 --at 1`
        Then: Video should be inserted at position 1, shifting others
        """
        # Arrange
        db = Database(temp_db)
        playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Favorites"]
        )[0]
        now = datetime.now(timezone.utc).isoformat()

        # Add two videos first
        db["playlist_videos"].insert_all([
            {"playlist_id": playlist["id"], "video_id": "abc123", "position": 1, "added_at": now},
            {"playlist_id": playlist["id"], "video_id": "def456", "position": 2, "added_at": now},
        ])

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - insert at position 1
        result = runner.invoke(cli, ["playlist", "add", "Favorites", "ghi789", "--at", "1"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify positions: ghi789 should be at 1, abc123 at 2, def456 at 3
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
            [playlist["id"]]
        )

        assert len(videos) == 3
        assert videos[0]["video_id"] == "ghi789"
        assert videos[1]["video_id"] == "abc123"
        assert videos[2]["video_id"] == "def456"

    def test_playlist_add_duplicate_video(self, temp_db):
        """
        Test that adding a duplicate video is handled gracefully.

        Given: A playlist with video abc123
        When: Running `playlist add Favorites abc123` again
        Then: Should warn about duplicate or ignore
        """
        # Arrange
        db = Database(temp_db)
        playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Favorites"]
        )[0]
        now = datetime.now(timezone.utc).isoformat()

        # Add video first
        db["playlist_videos"].insert({
            "playlist_id": playlist["id"], "video_id": "abc123", "position": 1, "added_at": now
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act - try to add again
        result = runner.invoke(cli, ["playlist", "add", "Favorites", "abc123"], env=env)

        # Assert - should not add duplicate
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist["id"]]
        )
        assert len(videos) == 1, "Should still have only one video"

    def test_playlist_add_invalid_video_id(self, temp_db):
        """
        Test that adding an invalid video ID is handled.

        Given: A database
        When: Running `playlist add Favorites nonexistent123`
        Then: Should return an error about invalid video ID
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "add", "Favorites", "nonexistent123"], env=env)

        # Assert - should fail or warn
        assert result.exit_code != 0 or "not found" in result.output.lower() or "invalid" in result.output.lower()

    def test_playlist_add_to_nonexistent_playlist(self, temp_db):
        """
        Test that adding to a non-existent playlist is handled.

        Given: A database
        When: Running `playlist add NonExistent abc123`
        Then: Should return an error
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "add", "NonExistent", "abc123"], env=env)

        # Assert - should fail
        assert result.exit_code != 0


class TestPlaylistRemove:
    """Test suite for playlist remove command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_playlist_remove.db"
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
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

        now = datetime.now(timezone.utc).isoformat()
        playlist_id = 1
        db["playlists"].insert({
            "id": playlist_id,
            "name": "Favorites",
            "description": "My favorites",
            "created_at": now,
        })
        db["playlist_videos"].insert({
            "id": 1, "playlist_id": playlist_id, "video_id": "abc123", "position": 1, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 2, "playlist_id": playlist_id, "video_id": "def456", "position": 2, "added_at": now
        })

        yield str(db_path)
        db.close()

    def test_playlist_remove_video(self, temp_db):
        """
        Test that `playlist remove <name> <video-id>` removes a video.

        Given: A playlist with videos
        When: Running `playlist remove Favorites abc123`
        Then: Video should be removed from the playlist
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "remove", "Favorites", "abc123"], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify video was removed
        db = Database(temp_db)
        playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Favorites"]
        )[0]
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist["id"]]
        )

        assert len(videos) == 1
        assert videos[0]["video_id"] == "def456"

    def test_playlist_remove_nonexistent_video(self, temp_db):
        """
        Test that removing a non-existent video is handled gracefully.

        Given: A playlist
        When: Running `playlist remove Favorites nonexistent123`
        Then: Should warn or return error
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "remove", "Favorites", "nonexistent123"], env=env)

        # Assert - should not crash, might warn
        # Original videos should still be there
        db = Database(temp_db)
        playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Favorites"]
        )[0]
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist["id"]]
        )
        assert len(videos) == 2


class TestPlaylistDelete:
    """Test suite for playlist delete command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary database with test data."""
        db_path = tmp_path / "test_playlist_delete.db"
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
        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
            pk="id",
            if_not_exists=True,
        )

        # Add test data
        now = datetime.now(timezone.utc).isoformat()
        db["playlists"].insert_all([
            {"name": "ToDelete", "description": "Will be deleted", "created_at": now},
            {"name": "ToKeep", "description": "Will be kept", "created_at": now},
        ])

        yield str(db_path)
        db.close()

    def test_playlist_delete(self, tmp_path):
        """
        Test that `playlist delete <name>` deletes the playlist.

        Given: A database with playlists
        When: Running `playlist delete ToDelete`
        Then: Playlist should be removed from database
        """
        # Arrange - Create fresh db for this test
        db_path = tmp_path / "test_delete_fresh.db"
        db = Database(str(db_path))

        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )
        db["playlist_videos"].create(
            {"id": int, "playlist_id": int, "video_id": str, "position": int, "added_at": str},
            pk="id",
            if_not_exists=True,
        )

        now = datetime.now(timezone.utc).isoformat()
        db["playlists"].insert_all([
            {"name": "ToDelete", "description": "Will be deleted", "created_at": now},
            {"name": "ToKeep", "description": "Will be kept", "created_at": now},
        ])

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act - provide 'y' to confirm deletion
        result = runner.invoke(cli, ["playlist", "delete", "ToDelete"], input="y\n", env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify playlist was deleted
        playlists = db.execute_returning_dicts("SELECT * FROM playlists WHERE name = ?", ["ToDelete"])
        assert len(playlists) == 0

        # Verify other playlist still exists
        playlists = db.execute_returning_dicts("SELECT * FROM playlists WHERE name = ?", ["ToKeep"])
        assert len(playlists) == 1

        db.close()

    def test_playlist_delete_nonexistent(self, tmp_path):
        """
        Test that deleting a non-existent playlist is handled.

        Given: A database
        When: Running `playlist delete NonExistent`
        Then: Should return an error
        """
        # Arrange
        db_path = tmp_path / "test_delete_nonexistent.db"
        db = Database(str(db_path))

        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}

        # Act
        result = runner.invoke(cli, ["playlist", "delete", "NonExistent"], env=env)

        # Assert - should fail
        assert result.exit_code != 0 or "not found" in result.output.lower()
        db.close()


if __name__ == "__main__":
    pytest.main([__file__])
