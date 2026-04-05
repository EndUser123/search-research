"""
Tests for playlist export/import feature (TSK-003).

Tests data portability:
- `playlist export <name> [--output FILE]` - Exports to JSON
- `playlist import <file>` - Imports from JSON
- Validates JSON schema
- Handles duplicate playlist names

Edge cases tested:
- Exporting empty playlists
- Importing with duplicate names
- Invalid JSON files
- Missing required fields in JSON
- Large playlists
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from datetime import datetime, timezone, timedelta
from unittest.mock import patch, MagicMock
from io import StringIO

import pytest
from click.testing import CliRunner

# Add src directory to path for imports
_src_path = Path(__file__).parent.parent / "src"
if str(_src_path) not in sys.path:
    sys.path.insert(0, str(_src_path))

from sqlite_utils import Database
from yt_fts.core.cli import cli


class TestPlaylistExport:
    """Test suite for playlist export command."""

    @pytest.fixture
    def temp_db_with_playlist(self, tmp_path):
        """Create a temporary database with a populated playlist."""
        db_path = tmp_path / "test_export.db"
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
            {
                "video_id": "abc123",
                "video_title": "First Video",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "channel_id": "UC_test",
                "video_date": "2024-01-01",
            },
            {
                "video_id": "def456",
                "video_title": "Second Video",
                "video_url": "https://www.youtube.com/watch?v=def456",
                "channel_id": "UC_test",
                "video_date": "2024-01-02",
            },
            {
                "video_id": "ghi789",
                "video_title": "Third Video",
                "video_url": "https://www.youtube.com/watch?v=ghi789",
                "channel_id": "UC_test",
                "video_date": "2024-01-03",
            },
        ])

        now = datetime.now(timezone.utc).isoformat()
        playlist_id = 1
        db["playlists"].insert({
            "id": playlist_id,
            "name": "MyPlaylist",
            "description": "Test playlist for export",
            "created_at": now,
        })

        db["playlist_videos"].insert({
            "id": 1, "playlist_id": playlist_id, "video_id": "abc123", "position": 1, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 2, "playlist_id": playlist_id, "video_id": "def456", "position": 2, "added_at": now
        })
        db["playlist_videos"].insert({
            "id": 3, "playlist_id": playlist_id, "video_id": "ghi789", "position": 3, "added_at": now
        })

        yield str(db_path)
        db.close()

    def test_playlist_export_to_default_file(self, temp_db_with_playlist, tmp_path):
        """
        Test that `playlist export <name>` exports to default JSON file.

        Given: A database with a playlist named "MyPlaylist"
        When: Running `playlist export MyPlaylist`
        Then: A file "MyPlaylist.json" should be created with valid JSON
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlist}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act
            result = runner.invoke(cli, ["playlist", "export", "MyPlaylist"], env=env)

            # Assert
            assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

            # Check file was created
            export_file = output_dir / "MyPlaylist.json"
            assert export_file.exists(), "Export file should be created"

            # Verify JSON is valid and contains expected data
            with open(export_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["name"] == "MyPlaylist"
            assert "description" in data
            assert "created_at" in data
            assert "videos" in data
            assert len(data["videos"]) == 3
        finally:
            os.chdir(original_cwd)

    def test_playlist_export_to_custom_file(self, temp_db_with_playlist, tmp_path):
        """
        Test that `playlist export <name> --output FILE` exports to specified file.

        Given: A database with a playlist
        When: Running `playlist export MyPlaylist --output custom.json`
        Then: File "custom.json" should be created with valid JSON
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlist}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act
            result = runner.invoke(
                cli,
                ["playlist", "export", "MyPlaylist", "--output", "custom.json"],
                env=env
            )

            # Assert
            assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

            # Check custom file was created
            export_file = output_dir / "custom.json"
            assert export_file.exists(), "Custom export file should be created"

            # Verify JSON
            with open(export_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["name"] == "MyPlaylist"
        finally:
            os.chdir(original_cwd)

    def test_playlist_export_schema_validation(self, temp_db_with_playlist, tmp_path):
        """
        Test that exported JSON has correct schema.

        Given: A database with a playlist
        When: Running `playlist export MyPlaylist`
        Then: JSON should have required fields: name, description, created_at, videos array
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlist}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act
            result = runner.invoke(cli, ["playlist", "export", "MyPlaylist"], env=env)

            # Assert
            assert result.exit_code == 0

            export_file = output_dir / "MyPlaylist.json"
            with open(export_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Validate schema
            required_fields = ["name", "description", "created_at", "videos"]
            for field in required_fields:
                assert field in data, f"Missing required field: {field}"

            # Validate videos array structure
            assert isinstance(data["videos"], list)
            if len(data["videos"]) > 0:
                video = data["videos"][0]
                required_video_fields = ["video_id", "position"]
                for field in required_video_fields:
                    assert field in video, f"Missing video field: {field}"
        finally:
            os.chdir(original_cwd)

    def test_playlist_export_empty_playlist(self, tmp_path):
        """
        Test that exporting an empty playlist works.

        Given: A database with an empty playlist
        When: Running `playlist export EmptyPlaylist`
        Then: JSON should be created with empty videos array
        """
        # Arrange
        db_path = tmp_path / "test_export_empty.db"
        db = Database(str(db_path))

        # Create Videos table (export_playlist queries it)
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
            "name": "EmptyPlaylist",
            "description": "Empty playlist",
            "created_at": now,
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act
            result = runner.invoke(cli, ["playlist", "export", "EmptyPlaylist"], env=env)

            # Assert
            assert result.exit_code == 0, f"Export failed: {result.output or result.stderr}"

            export_file = output_dir / "EmptyPlaylist.json"
            assert export_file.exists()

            with open(export_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert data["name"] == "EmptyPlaylist"
            assert data["videos"] == []
        finally:
            os.chdir(original_cwd)

        db.close()

    def test_playlist_export_nonexistent_playlist(self, tmp_path):
        """
        Test that exporting a non-existent playlist returns an error.

        Given: A database
        When: Running `playlist export NonExistent`
        Then: Should return an error
        """
        # Arrange
        db_path = tmp_path / "test_export_nonexistent.db"
        db = Database(str(db_path))

        db["playlists"].create(
            {"id": int, "name": str, "description": str, "created_at": str},
            pk="id",
            if_not_exists=True,
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        with runner.isolated_filesystem(temp_dir=str(output_dir)):
            # Act
            result = runner.invoke(cli, ["playlist", "export", "NonExistent"], env=env)

            # Assert - should fail
            assert result.exit_code != 0 or "not found" in result.output.lower()

        db.close()

    def test_playlist_export_with_unicode_content(self, tmp_path):
        """
        Test that export handles unicode characters correctly.

        Given: A database with playlist containing unicode in name/description
        When: Running `playlist export`
        Then: JSON should be valid UTF-8 with unicode preserved
        """
        # Arrange
        db_path = tmp_path / "test_export_unicode.db"
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

        now = datetime.now(timezone.utc).isoformat()
        playlist_id = 1
        db["playlists"].insert({
            "id": playlist_id,
            "name": "Unicode Playlist 测试 🎵",
            "description": "Playlist with emojis 🔥 and Chinese 中文字符",
            "created_at": now,
        })

        db["Videos"].insert({
            "video_id": "vid1",
            "video_title": "Video with Arabic العربية",
            "video_url": "https://youtu.be/vid1",
            "channel_id": "UC_test",
            "video_date": "2024-01-01",
        })

        db["playlist_videos"].insert({
            "id": 1,
            "playlist_id": playlist_id,
            "video_id": "vid1",
            "position": 1,
            "added_at": now,
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": str(db_path)}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act
            result = runner.invoke(
                cli,
                ["playlist", "export", "Unicode Playlist 测试 🎵"],
                env=env
            )

            # Assert
            assert result.exit_code == 0

            # Verify file is valid UTF-8 JSON with unicode
            export_file = output_dir / "Unicode Playlist 测试 🎵.json"
            if not export_file.exists():
                # Fallback to encoded filename
                export_file = list(output_dir.glob("*.json"))[0]

            with open(export_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            assert "测试" in data["name"] or "test" in data["name"].lower()
            assert "🎵" in data["name"] or "music" in data["name"].lower()
        finally:
            os.chdir(original_cwd)

        db.close()


class TestPlaylistImport:
    """Test suite for playlist import command."""

    @pytest.fixture
    def temp_db(self, tmp_path):
        """Create a temporary empty database."""
        db_path = tmp_path / "test_import.db"
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

        # Add test videos that match the import
        db["Channels"].insert({
            "channel_id": "UC_test",
            "channel_name": "Test Channel",
            "channel_url": "https://www.youtube.com/@test",
        })
        db["Videos"].insert_all([
            {
                "video_id": "abc123",
                "video_title": "First Video",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "channel_id": "UC_test",
                "video_date": "2024-01-01",
            },
            {
                "video_id": "def456",
                "video_title": "Second Video",
                "video_url": "https://www.youtube.com/watch?v=def456",
                "channel_id": "UC_test",
                "video_date": "2024-01-02",
            },
        ])

        yield str(db_path)
        db.close()

    @pytest.fixture
    def valid_import_file(self, tmp_path):
        """Create a valid JSON import file."""
        import_file = tmp_path / "valid_import.json"
        data = {
            "name": "Imported Playlist",
            "description": "Imported from file",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "videos": [
                {"video_id": "abc123", "position": 1},
                {"video_id": "def456", "position": 2},
            ]
        }
        with open(import_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return str(import_file)

    def test_playlist_import_basic(self, temp_db, valid_import_file):
        """
        Test that `playlist import <file>` imports a playlist from JSON.

        Given: A database with existing videos and a valid JSON file
        When: Running `playlist import valid_import.json`
        Then: Playlist should be created with videos
        """
        # Arrange
        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", valid_import_file], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify playlist was created
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Imported Playlist"]
        )

        assert len(playlists) == 1
        assert playlists[0]["description"] == "Imported from file"

        # Verify videos were added
        playlist_id = playlists[0]["id"]
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
            [playlist_id]
        )

        assert len(videos) == 2
        assert videos[0]["video_id"] == "abc123"
        assert videos[1]["video_id"] == "def456"

    def test_playlist_import_with_duplicate_name(self, temp_db, valid_import_file, tmp_path):
        """
        Test that importing with a duplicate name is handled.

        Given: A database with an existing playlist named "Imported Playlist"
        When: Running `playlist import valid_import.json` (which has same name)
        Then: Should handle duplicate (rename, skip, or merge)
        """
        # Arrange - create existing playlist with same name
        db = Database(temp_db)
        now = datetime.now(timezone.utc).isoformat()
        db["playlists"].insert({
            "name": "Imported Playlist",
            "description": "Existing playlist",
            "created_at": now,
        })

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", valid_import_file], env=env)

        # Assert - should handle duplicate gracefully
        # Either rejects with error or creates with suffix like "Imported Playlist (2)"
        assert result.exit_code == 0 or "duplicate" in result.output.lower() or "exists" in result.output.lower()

    def test_playlist_import_invalid_json(self, temp_db, tmp_path):
        """
        Test that importing invalid JSON returns an error.

        Given: A database and an invalid JSON file
        When: Running `playlist import invalid.json`
        Then: Should return an error about invalid JSON
        """
        # Arrange
        invalid_file = tmp_path / "invalid.json"
        with open(invalid_file, "w") as f:
            f.write("{ not valid json }")

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", str(invalid_file)], env=env)

        # Assert - should fail
        assert result.exit_code != 0 or "invalid" in result.output.lower() or "json" in result.output.lower()

    def test_playlist_import_missing_required_fields(self, temp_db, tmp_path):
        """
        Test that importing JSON with missing required fields returns an error.

        Given: A database and a JSON file missing "name" field
        When: Running `playlist import incomplete.json`
        Then: Should return an error about missing fields
        """
        # Arrange
        incomplete_file = tmp_path / "incomplete.json"
        data = {
            "description": "Missing name field",
            "videos": []
        }
        with open(incomplete_file, "w") as f:
            json.dump(data, f)

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", str(incomplete_file)], env=env)

        # Assert - should fail
        assert result.exit_code != 0 or "required" in result.output.lower() or "missing" in result.output.lower()

    def test_playlist_import_nonexistent_video(self, temp_db, tmp_path):
        """
        Test that importing with non-existent video IDs is handled.

        Given: A database and a JSON file with non-existent video ID
        When: Running `playlist import with_bad_video.json`
        Then: Should skip or warn about non-existent videos
        """
        # Arrange
        import_file = tmp_path / "with_bad_video.json"
        data = {
            "name": "Playlist With Bad Video",
            "description": "Test",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "videos": [
                {"video_id": "abc123", "position": 1},  # exists
                {"video_id": "nonexistent123", "position": 2},  # doesn't exist
            ]
        }
        with open(import_file, "w") as f:
            json.dump(data, f)

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", str(import_file)], env=env)

        # Assert - should import but skip/warn about bad video
        assert result.exit_code == 0 or "not found" in result.output.lower()

        # Verify only valid video was imported
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Playlist With Bad Video"]
        )

        if len(playlists) > 0:
            playlist_id = playlists[0]["id"]
            videos = db.execute_returning_dicts(
                "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist_id]
            )
            # Should only have the valid video
            assert len(videos) <= 1

    def test_playlist_import_empty_videos_array(self, temp_db, tmp_path):
        """
        Test that importing with empty videos array creates an empty playlist.

        Given: A database and a JSON file with empty videos array
        When: Running `playlist import empty.json`
        Then: Should create an empty playlist
        """
        # Arrange
        empty_file = tmp_path / "empty.json"
        data = {
            "name": "Empty Playlist",
            "description": "Empty",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "videos": []
        }
        with open(empty_file, "w") as f:
            json.dump(data, f)

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", str(empty_file)], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify empty playlist was created
        db = Database(temp_db)
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Empty Playlist"]
        )

        assert len(playlists) == 1

        playlist_id = playlists[0]["id"]
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist_id]
        )
        assert len(videos) == 0

    def test_playlist_import_large_playlist(self, temp_db, tmp_path):
        """
        Test that importing a large playlist works.

        Given: A database and a JSON file with many videos
        When: Running `playlist import large.json`
        Then: Should create playlist with all videos
        """
        # Arrange
        large_file = tmp_path / "large.json"

        # Add many test videos
        db = Database(temp_db)
        for i in range(100):
            video_id = f"vid{i:03d}"
            try:
                db["Videos"].insert({
                    "video_id": video_id,
                    "video_title": f"Video {i}",
                    "video_url": f"https://youtu.be/{video_id}",
                    "channel_id": "UC_test",
                    "video_date": "2024-01-01",
                })
            except Exception:
                pass  # Ignore if already exists

        # Create import file with 100 videos
        data = {
            "name": "Large Playlist",
            "description": "Playlist with 100 videos",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "videos": [{"video_id": f"vid{i:03d}", "position": i + 1} for i in range(100)]
        }
        with open(large_file, "w") as f:
            json.dump(data, f)

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db}

        # Act
        result = runner.invoke(cli, ["playlist", "import", str(large_file)], env=env)

        # Assert
        assert result.exit_code == 0, f"Command failed: {result.output or result.stderr}"

        # Verify all videos were imported
        playlists = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["Large Playlist"]
        )

        assert len(playlists) == 1
        playlist_id = playlists[0]["id"]
        videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ?", [playlist_id]
        )
        assert len(videos) == 100


class TestExportImportRoundTrip:
    """Test suite for export/import round-trip."""

    @pytest.fixture
    def temp_db_with_playlist(self, tmp_path):
        """Create a temporary database with a playlist."""
        db_path = tmp_path / "test_roundtrip.db"
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
            {
                "video_id": "abc123",
                "video_title": "First Video",
                "video_url": "https://www.youtube.com/watch?v=abc123",
                "channel_id": "UC_test",
                "video_date": "2024-01-01",
            },
            {
                "video_id": "def456",
                "video_title": "Second Video",
                "video_url": "https://www.youtube.com/watch?v=def456",
                "channel_id": "UC_test",
                "video_date": "2024-01-02",
            },
        ])

        now = datetime.now(timezone.utc).isoformat()
        playlist_id = 1
        db["playlists"].insert({
            "id": playlist_id,
            "name": "RoundTripTest",
            "description": "Test round-trip export/import",
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

    def test_export_then_import_preserves_data(self, temp_db_with_playlist, tmp_path):
        """
        Test that exporting then importing preserves all data.

        Given: A database with a playlist
        When: Exporting to JSON, deleting the playlist, then importing
        Then: The imported playlist should match the original
        """
        # Arrange
        db = Database(temp_db_with_playlist)
        original_playlist = db.execute_returning_dicts(
            "SELECT * FROM playlists WHERE name = ?", ["RoundTripTest"]
        )[0]
        original_id = original_playlist["id"]

        original_videos = db.execute_returning_dicts(
            "SELECT * FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
            [original_id]
        )

        runner = CliRunner()
        env = {"YT_FTS_DB_PATH": temp_db_with_playlist}
        output_dir = tmp_path / "exports"
        output_dir.mkdir(exist_ok=True)

        # Change to output directory before running command
        import os
        original_cwd = os.getcwd()
        try:
            os.chdir(str(output_dir))

            # Act 1: Export
            result = runner.invoke(cli, ["playlist", "export", "RoundTripTest"], env=env)
            assert result.exit_code == 0

            # Act 2: Delete original playlist
            db.execute("DELETE FROM playlist_videos WHERE playlist_id = ?", [original_id])
            db.execute("DELETE FROM playlists WHERE id = ?", [original_id])

            # Verify deletion
            remaining = db.execute_returning_dicts(
                "SELECT * FROM playlists WHERE name = ?", ["RoundTripTest"]
            )
            assert len(remaining) == 0

            # Close database connection before import to avoid lock
            db.close()

            # Act 3: Import (use relative path since we changed to output_dir)
            import_file = "RoundTripTest.json"
            result = runner.invoke(cli, ["playlist", "import", import_file], env=env)
            assert result.exit_code == 0, f"Import failed: {result.output or result.stderr}"

            # Assert: Verify imported data matches original
            # Reopen database connection
            db = Database(temp_db_with_playlist)
            imported_playlists = db.execute_returning_dicts(
                "SELECT * FROM playlists WHERE name = ?", ["RoundTripTest"]
            )
            assert len(imported_playlists) == 1

            imported = imported_playlists[0]
            assert imported["name"] == original_playlist["name"]
            assert imported["description"] == original_playlist["description"]

            imported_videos = db.execute_returning_dicts(
                "SELECT * FROM playlist_videos WHERE playlist_id = ? ORDER BY position",
                [imported["id"]]
            )

            assert len(imported_videos) == len(original_videos)
            for i, (orig, imp) in enumerate(zip(original_videos, imported_videos)):
                assert imp["video_id"] == orig["video_id"]
                assert imp["position"] == orig["position"]
        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    pytest.main([__file__])
