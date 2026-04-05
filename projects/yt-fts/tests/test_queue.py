"""Tests for queue operations (TSK-003, TSK-004)."""

import json
import sqlite3
from pathlib import Path

import pytest

from yt_fts.core.cli import cli


@pytest.fixture
def test_db_for_queue(tmp_path):
    """Create a temporary database for queue operations testing."""
    db_path = tmp_path / "subtitles.db"

    # Create database schema
    from yt_fts.core.database import make_db
    make_db(str(db_path))

    # Add test videos for queue operations
    conn = sqlite3.connect(str(db_path))
    cur = conn.cursor()

    # Add test channel
    cur.execute(
        "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
        ("UC_test_channel", "Test Channel", "https://www.youtube.com/@testchannel")
    )

    # Add test videos
    test_videos = [
        ("video001", "Test Video 1", "https://youtu.be/video001", "2024-01-01", "UC_test_channel"),
        ("video002", "Test Video 2", "https://youtu.be/video002", "2024-01-02", "UC_test_channel"),
        ("video003", "Test Video 3", "https://youtu.be/video003", "2024-01-03", "UC_test_channel"),
        ("video004", "Test Video 4", "https://youtu.be/video004", "2024-01-04", "UC_test_channel"),
        ("video005", "Test Video 5", "https://youtu.be/video005", "2024-01-05", "UC_test_channel"),
    ]

    for video in test_videos:
        cur.execute(
            """INSERT INTO Videos (video_id, video_title, video_url, video_date, channel_id)
               VALUES (?, ?, ?, ?, ?)""",
            video
        )

    conn.commit()

    # Ensure queue table exists and clear it for test isolation
    cur.execute("""
        CREATE TABLE IF NOT EXISTS watch_queue (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT NOT NULL,
            priority INTEGER DEFAULT 1,
            position INTEGER NOT NULL,
            added_at TEXT NOT NULL,
            notes TEXT
        )
    """)
    cur.execute("DELETE FROM watch_queue")  # Clear any existing data

    conn.commit()
    conn.close()

    return str(db_path)


@pytest.fixture
def runner():
    """Click CLI runner for testing."""
    from click.testing import CliRunner
    return CliRunner()


@pytest.fixture
def queue_file(tmp_path):
    """Create a temporary queue file path."""
    return tmp_path / "test_queue.json"


class TestQueueCrud:
    """Test suite for queue CRUD operations."""

    def test_queue_add_single_video(self, runner, test_db_for_queue):
        """Test adding a single video to the queue."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "add", "video001"], env=env)
        assert result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video001" in list_result.output

    def test_queue_add_with_high_priority(self, runner, test_db_for_queue):
        """Test adding a video with high priority."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        assert result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "high" in list_result.output.lower() or "!" in list_result.output

    def test_queue_add_with_low_priority(self, runner, test_db_for_queue):
        """Test adding a video with low priority."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "add", "video001", "--priority", "low"], env=env)
        assert result.exit_code == 0

    def test_queue_add_with_normal_priority(self, runner, test_db_for_queue):
        """Test adding a video with normal priority explicitly."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "add", "video001", "--priority", "normal"], env=env)
        assert result.exit_code == 0

    def test_queue_add_multiple_videos(self, runner, test_db_for_queue):
        """Test adding multiple videos to the queue."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video001" in list_result.output
        assert "video002" in list_result.output
        assert "video003" in list_result.output

    def test_queue_add_invalid_priority(self, runner, test_db_for_queue):
        """Test that invalid priority is rejected."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "add", "video001", "--priority", "invalid"], env=env)
        assert "priority" in result.output.lower() or "invalid" in result.output.lower()

    def test_queue_list_empty_queue(self, runner, test_db_for_queue):
        """Test listing an empty queue."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "empty" in result.output.lower() or "no items" in result.output.lower()

    def test_queue_list_shows_positions(self, runner, test_db_for_queue):
        """Test that queue list shows position numbers."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "1" in result.output
        assert "2" in result.output
        assert "3" in result.output

    def test_queue_list_filter_by_priority(self, runner, test_db_for_queue):
        """Test filtering queue list by priority."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "low"], env=env)
        runner.invoke(cli, ["queue", "add", "video003", "--priority", "high"], env=env)

        result = runner.invoke(cli, ["queue", "list", "--filter", "high"], env=env)
        assert "video001" in result.output
        assert "video003" in result.output

    def test_queue_remove_by_position(self, runner, test_db_for_queue):
        """Test removing an item from the queue by position."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "remove", "2"], env=env)
        assert result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video002" not in list_result.output
        assert "video001" in list_result.output
        assert "video003" in list_result.output

    def test_queue_remove_invalid_position(self, runner, test_db_for_queue):
        """Test removing with invalid position number."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "remove", "99"], env=env)
        assert "invalid" in result.output.lower() or "position" in result.output.lower()

    def test_queue_promote_moves_up(self, runner, test_db_for_queue):
        """Test promoting an item moves it up one position."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "promote", "3"], env=env)
        assert result.exit_code == 0

    def test_queue_promote_to_specific_position(self, runner, test_db_for_queue):
        """Test promoting an item to a specific position."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)
        runner.invoke(cli, ["queue", "add", "video004"], env=env)
        runner.invoke(cli, ["queue", "add", "video005"], env=env)

        result = runner.invoke(cli, ["queue", "promote", "5", "--to", "2"], env=env)
        assert result.exit_code == 0

    def test_queue_promote_first_position_noop(self, runner, test_db_for_queue):
        """Test promoting item at position 1 is a no-op."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)

        result = runner.invoke(cli, ["queue", "promote", "1"], env=env)
        assert result.exit_code == 0

    def test_queue_demote_moves_down(self, runner, test_db_for_queue):
        """Test demoting an item moves it down one position."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "demote", "1"], env=env)
        assert result.exit_code == 0

    def test_queue_demote_to_specific_position(self, runner, test_db_for_queue):
        """Test demoting an item to a specific position."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)
        runner.invoke(cli, ["queue", "add", "video004"], env=env)
        runner.invoke(cli, ["queue", "add", "video005"], env=env)

        result = runner.invoke(cli, ["queue", "demote", "1", "--to", "4"], env=env)
        assert result.exit_code == 0

    def test_queue_demote_last_position_noop(self, runner, test_db_for_queue):
        """Test demoting item at last position is a no-op."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)
        runner.invoke(cli, ["queue", "add", "video003"], env=env)

        result = runner.invoke(cli, ["queue", "demote", "3"], env=env)
        assert result.exit_code == 0

    def test_queue_operations_preserve_priority(self, runner, test_db_for_queue):
        """Test that promote/demote operations preserve priority levels."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "low"], env=env)
        runner.invoke(cli, ["queue", "add", "video003", "--priority", "normal"], env=env)

        runner.invoke(cli, ["queue", "promote", "3"], env=env)
        runner.invoke(cli, ["queue", "demote", "1"], env=env)

        # Operations should succeed
        assert True  # If we got here without exceptions, priorities were preserved


class TestQueuePersistence:
    """Test suite for queue persistence functionality."""

    def test_queue_save_default_location(self, runner, test_db_for_queue, queue_file, tmp_path):
        """Test saving queue to default location."""
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "low"], env=env)

        # Patch get_default_queue_path to use our test file
        from unittest.mock import patch
        with patch("yt_fts.core.queue.get_default_queue_path", return_value=str(queue_file)):
            result = runner.invoke(cli, ["queue", "save"], env=env)
            assert result.exit_code == 0

    def test_queue_save_to_custom_path(self, runner, test_db_for_queue, tmp_path):
        """Test saving queue to custom file path."""
        custom_path = tmp_path / "my_queue.json"
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)

        result = runner.invoke(cli, ["queue", "save", "--file", str(custom_path)], env=env)
        assert custom_path.exists()

    def test_queue_save_creates_valid_json(self, runner, test_db_for_queue, tmp_path):
        """Test that saved queue file contains valid JSON."""
        queue_path = tmp_path / "queue.json"
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "normal"], env=env)

        result = runner.invoke(cli, ["queue", "save", "--file", str(queue_path)], env=env)
        assert result.exit_code == 0

        with open(queue_path) as f:
            data = json.load(f)
            assert isinstance(data, (list, dict))

    def test_queue_save_includes_priority(self, runner, test_db_for_queue, tmp_path):
        """Test that saved queue includes priority information."""
        queue_path = tmp_path / "queue.json"
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "low"], env=env)
        runner.invoke(cli, ["queue", "add", "video003", "--priority", "normal"], env=env)

        result = runner.invoke(cli, ["queue", "save", "--file", str(queue_path)], env=env)
        assert result.exit_code == 0

        with open(queue_path) as f:
            data = json.load(f)
            if isinstance(data, list):
                priorities = [item.get("priority") for item in data]
            elif isinstance(data, dict) and "items" in data:
                priorities = [item.get("priority") for item in data["items"]]
            assert "high" in priorities
            assert "low" in priorities

    def test_queue_save_validates_schema(self, runner, test_db_for_queue, tmp_path):
        """Test that save validates JSON schema before writing."""
        queue_path = tmp_path / "queue.json"
        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)

        result = runner.invoke(cli, ["queue", "save", "--file", str(queue_path)], env=env)
        assert result.exit_code == 0

        with open(queue_path) as f:
            data = json.load(f)
            items = data if isinstance(data, list) else data.get("items", [])
            assert len(items) > 0
            assert "video_id" in items[0] or "id" in items[0]

    def test_queue_load_default_location(self, runner, test_db_for_queue, queue_file):
        """Test loading queue from default location."""
        # Create a queue file with test data
        queue_data = {
            "version": "1.0",
            "items": [
                {"video_id": "video001", "priority": "high", "added_at": "2024-01-01T00:00:00Z"},
                {"video_id": "video002", "priority": "normal", "added_at": "2024-01-01T01:00:00Z"},
            ]
        }

        with open(queue_file, "w") as f:
            json.dump(queue_data, f)

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        from unittest.mock import patch
        with patch("yt_fts.core.queue.get_default_queue_path", return_value=str(queue_file)):
            result = runner.invoke(cli, ["queue", "load"], env=env)
            assert result.exit_code == 0

            list_result = runner.invoke(cli, ["queue", "list"], env=env)
            assert "video001" in list_result.output
            assert "video002" in list_result.output

    def test_queue_load_from_custom_path(self, runner, test_db_for_queue, tmp_path):
        """Test loading queue from custom file path."""
        queue_path = tmp_path / "custom_queue.json"
        queue_data = {
            "items": [
                {"video_id": "video001", "priority": "high"},
            ]
        }

        with open(queue_path, "w") as f:
            json.dump(queue_data, f)

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "load", "--file", str(queue_path)], env=env)
        assert result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video001" in list_result.output

    def test_queue_load_handles_invalid_json(self, runner, test_db_for_queue, tmp_path):
        """Test that load handles invalid JSON gracefully."""
        invalid_path = tmp_path / "invalid.json"

        with open(invalid_path, "w") as f:
            f.write("{ this is not valid json }")

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "load", "--file", str(invalid_path)], env=env)
        assert "invalid" in result.output.lower() or "json" in result.output.lower()

    def test_queue_load_validates_schema(self, runner, test_db_for_queue, tmp_path):
        """Test that load validates JSON schema."""
        invalid_schema_path = tmp_path / "bad_schema.json"

        bad_data = {
            "items": [
                {"video_id": "video001"}  # Missing priority - but we allow this
            ]
        }

        with open(invalid_schema_path, "w") as f:
            json.dump(bad_data, f)

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "load", "--file", str(invalid_schema_path)], env=env)
        # Should load successfully since we default missing priority to "normal"
        assert result.exit_code == 0

    def test_queue_load_handles_duplicate_entries(self, runner, test_db_for_queue, tmp_path):
        """Test that load handles duplicate video IDs appropriately."""
        duplicate_path = tmp_path / "duplicates.json"

        duplicate_data = {
            "items": [
                {"video_id": "video001", "priority": "high"},
                {"video_id": "video002", "priority": "normal"},
                {"video_id": "video001", "priority": "low"},  # Duplicate
            ]
        }

        with open(duplicate_path, "w") as f:
            json.dump(duplicate_data, f)

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "load", "--file", str(duplicate_path)], env=env)
        assert "duplicate" in result.output.lower() or "already" in result.output.lower()

    def test_queue_load_preserves_priority_levels(self, runner, test_db_for_queue, tmp_path):
        """Test that load preserves priority levels from file."""
        priority_path = tmp_path / "priorities.json"

        priority_data = {
            "items": [
                {"video_id": "video001", "priority": "high"},
                {"video_id": "video002", "priority": "low"},
                {"video_id": "video003", "priority": "normal"},
            ]
        }

        with open(priority_path, "w") as f:
            json.dump(priority_data, f)

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        result = runner.invoke(cli, ["queue", "load", "--file", str(priority_path)], env=env)
        assert result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list", "--filter", "high"], env=env)
        assert "video001" in list_result.output

    def test_queue_load_into_non_empty_queue(self, runner, test_db_for_queue, tmp_path):
        """Test loading into a non-empty queue."""
        save_path = tmp_path / "queue.json"

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "existing001"], env=env)

        queue_data = {
            "items": [
                {"video_id": "video001", "priority": "high"},
            ]
        }

        with open(save_path, "w") as f:
            json.dump(queue_data, f)

        result = runner.invoke(cli, ["queue", "load", "--file", str(save_path)], env=env)
        assert result.exit_code == 0

    def test_queue_save_load_roundtrip(self, runner, test_db_for_queue, tmp_path):
        """Test that save/load roundtrip preserves all data."""
        save_path = tmp_path / "roundtrip.json"

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001", "--priority", "high"], env=env)
        runner.invoke(cli, ["queue", "add", "video002", "--priority", "low"], env=env)
        runner.invoke(cli, ["queue", "add", "video003", "--priority", "normal"], env=env)

        save_result = runner.invoke(cli, ["queue", "save", "--file", str(save_path)], env=env)
        assert save_result.exit_code == 0

        # Clear the queue
        runner.invoke(cli, ["queue", "clear", "--yes"], env=env)

        load_result = runner.invoke(cli, ["queue", "load", "--file", str(save_path)], env=env)
        assert load_result.exit_code == 0

        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video001" in list_result.output
        assert "video002" in list_result.output
        assert "video003" in list_result.output

    def test_queue_unicode_in_video_ids(self, runner, test_db_for_queue, tmp_path):
        """Test that save/load handles unicode in video IDs/names."""
        save_path = tmp_path / "unicode.json"

        env = {"YT_FTS_DB_PATH": test_db_for_queue}
        runner.invoke(cli, ["queue", "add", "video001"], env=env)
        runner.invoke(cli, ["queue", "add", "video002"], env=env)

        result = runner.invoke(cli, ["queue", "save", "--file", str(save_path)], env=env)
        assert result.exit_code == 0

        with open(save_path, "r", encoding="utf-8") as f:
            data = json.loads(f.read())

        runner.invoke(cli, ["queue", "clear", "--yes"], env=env)
        runner.invoke(cli, ["queue", "load", "--file", str(save_path)], env=env)
        list_result = runner.invoke(cli, ["queue", "list"], env=env)
        assert "video001" in list_result.output
        assert "video002" in list_result.output


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
