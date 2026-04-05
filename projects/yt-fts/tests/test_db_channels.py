"""Comprehensive tests for the channels database module.

Tests channel CRUD operations, validation, deduplication logic,
statistics calculations, and metadata updates.

Run with: pytest tests/test_db_channels.py -v
"""

import sqlite3
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from yt_fts.db.channels import (
    _is_valid_channel_identifier,
    add_channel_info,
    check_if_channel_exists,
    get_channel_id_from_input,
    get_channel_stats,
    get_batch_channel_stats,
    delete_channel,
    get_channel_name_from_db,
    update_channel_metadata,
    get_fresh_channels,
)


class TestIsValidChannelIdentifier:
    """Tests for _is_valid_channel_identifier validation function."""

    def test_accepts_uc_channel_id(self):
        """Test that valid UC channel IDs are accepted."""
        result = _is_valid_channel_identifier(
            "UC1234567890123456789012",
            "https://www.youtube.com/channel/UC1234567890123456789012"
        )
        assert result is True

    def test_accepts_handle(self):
        """Test that @handle format is accepted."""
        result = _is_valid_channel_identifier(
            "@testchannel",
            "https://www.youtube.com/@testchannel"
        )
        assert result is True

    def test_rejects_backslash_in_channel_id(self):
        """Test that backslashes in channel_id are rejected (Windows paths)."""
        backslash = chr(92)
        result = _is_valid_channel_identifier(
            f"C:{backslash}Users{backslash}Test",
            "https://www.youtube.com/channel/UC1234567890123456789012"
        )
        assert result is False

    def test_rejects_drive_letter(self):
        """Test that drive letters are rejected (e.g., 'C:')."""
        result = _is_valid_channel_identifier(
            "C:",
            "https://www.youtube.com/channel/UC1234567890123456789012"
        )
        assert result is False

    def test_rejects_channels_txt_filename(self):
        """Test that 'channels.txt' filename is rejected."""
        result = _is_valid_channel_identifier(
            "channels.txt",
            "https://www.youtube.com/channel/UC1234567890123456789012"
        )
        assert result is False


class TestCheckIfChannelExists:
    """Tests for check_if_channel_exists function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_channel_exists_returns_true(self, mock_get_conn):
        """Test that existing channel returns True."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["UC1234567890123456789012"]
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        result = check_if_channel_exists("UC1234567890123456789012")
        assert result is True


class TestAddChannelInfo:
    """Tests for add_channel_info function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_add_basic_channel_info(self, mock_get_conn):
        """Test adding basic channel information."""
        mock_conn = MagicMock()
        mock_get_conn.return_value.__enter__.return_value = mock_conn
        
        # Create a mock result that returns None for fetchone()
        mock_result = MagicMock()
        mock_result.fetchone.return_value = None
        mock_conn.execute.return_value = mock_result

        add_channel_info(
            "UC1234567890123456789012",
            "Test Channel",
            "https://www.youtube.com/channel/UC1234567890123456789012"
        )
        assert mock_conn.execute.called


class TestGetChannelIdFromInput:
    """Tests for get_channel_id_from_input function."""

    def test_raises_error_for_none_input(self):
        """Test that None input raises ValueError."""
        with pytest.raises(ValueError, match="Channel input cannot be None"):
            get_channel_id_from_input(None)

    def test_raises_error_for_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError, match="Channel input cannot be empty"):
            get_channel_id_from_input("")


class TestGetChannelStats:
    """Tests for get_channel_stats function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_basic_stats_calculation(self, mock_get_conn):
        """Test basic video statistics calculation."""
        mock_conn = MagicMock()
        
        def execute_side_effect(query, params=None):
            mock_result = MagicMock()
            if "COUNT(*) FROM Videos" in query and "LEFT JOIN" not in query:
                mock_result.fetchone.return_value = [100]
            elif "LEFT JOIN Subtitles" in query:
                mock_result.fetchone.return_value = [80]
            else:
                mock_result.fetchone.return_value = [0]
            return mock_result

        mock_conn.execute.side_effect = execute_side_effect
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        stats = get_channel_stats("UC1234567890123456789012")
        assert stats["total"] == 100



class TestGetChannelStatsIntegration:
    """Integration tests for get_channel_stats using real database execution.
    
    These tests use real SQLite databases to verify SQL queries return correct results.
    Mock-based tests cannot catch SQL bugs like COUNT vs COUNT DISTINCT.
    """

    @pytest.fixture
    def test_db_with_stats_data(self):
        """Create a real SQLite database with test data for stats calculation."""
        import tempfile
        import gc
        
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "test.db"
            conn = sqlite3.connect(str(db_path))
            cur = conn.cursor()

            # Create tables (minimal schema for stats calculation)
            cur.execute("""
                CREATE TABLE Channels (
                    channel_id TEXT PRIMARY KEY,
                    channel_name TEXT,
                    channel_url TEXT
                )
            """)

            cur.execute("""
                CREATE TABLE Videos (
                    video_id TEXT PRIMARY KEY,
                    channel_id TEXT,
                    video_title TEXT,
                    thumbnail_url TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    is_short INTEGER DEFAULT 0
                )
            """)

            cur.execute("""
                CREATE TABLE Subtitles (
                    subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT,
                    start_time TEXT,
                    stop_time TEXT,
                    text TEXT
                )
            """)

            # Insert test data
            test_channel_id = "UCstats123"
            cur.execute("INSERT INTO Channels VALUES (?, ?, ?)",
                       (test_channel_id, "Stats Test Channel", "https://youtube.com/@stats"))

            # 20 total videos
            for i in range(20):
                cur.execute("INSERT INTO Videos VALUES (?, ?, ?, ?, ?, ?, ?)",
                           (f"video_{i}", test_channel_id, f"Video {i}", "", 0, 0, 0))

            # 12 videos with subtitles (60% coverage)
            for i in range(12):
                cur.execute("INSERT INTO Subtitles (video_id, start_time, stop_time, text) VALUES (?, ?, ?, ?)",
                           (f"video_{i}", "0:00", "0:10", f"Subtitle text {i}"))

            conn.commit()
            # Important: close connection before yield to avoid Windows file lock on teardown
            conn.close()
            gc.collect()

            yield str(db_path), test_channel_id

    def test_stats_calculation_with_real_db(self, test_db_with_stats_data):
        """Test get_channel_stats returns correct counts from real database."""
        import gc
        from importlib import reload
        import yt_fts.utils.config as config_module
        import yt_fts.db.infra as infra_module
        import yt_fts.db.channels as channels_module

        db_path, test_channel_id = test_db_with_stats_data

        # Patch database path
        original_config = config_module.get_db_path
        original_infra = infra_module.get_db_path

        config_module.get_db_path = lambda: str(db_path)
        infra_module.get_db_path = lambda: str(db_path)

        try:
            reload(channels_module)
            from yt_fts.db.channels import get_channel_stats

            stats = get_channel_stats(test_channel_id)
        finally:
            config_module.get_db_path = original_config
            infra_module.get_db_path = original_infra
            gc.collect()

        # Verify: 20 unique videos, 12 with subtitles, 8 without
        assert stats["total"] == 20, f"Expected 20 total videos, got {stats['total']}"
        assert stats["with_transcripts"] == 12, f"Expected 12 with transcripts, got {stats['with_transcripts']}"
        assert stats["without_transcripts"] == 8, f"Expected 8 without transcripts, got {stats['without_transcripts']}"


class TestGetBatchChannelStats:
    """Tests for get_batch_channel_stats function."""

    def test_empty_list_returns_empty_dict(self):
        """Test that empty input list returns empty dictionary."""
        result = get_batch_channel_stats([])
        assert result == {}


class TestDeleteChannel:
    """Tests for delete_channel function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_delete_channel_cascades_to_videos(self, mock_get_conn):
        """Test that deleting channel also deletes associated videos."""
        mock_conn = MagicMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = [("vid1",), ("vid2",)]
        mock_conn.execute.return_value = mock_result
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        delete_channel("UC1234567890123456789012")
        assert mock_conn.commit.called


class TestGetChannelNameFromDb:
    """Tests for get_channel_name_from_db function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_get_existing_channel_name(self, mock_get_conn):
        """Test getting name for existing channel."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["Test Channel Name"]
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        result = get_channel_name_from_db("UC1234567890123456789012")
        assert result == "Test Channel Name"


class TestUpdateChannelMetadata:
    """Tests for update_channel_metadata function."""

    @patch("yt_fts.db.channels.get_db_connection")
    def test_update_subscriber_count(self, mock_get_conn):
        """Test updating subscriber count."""
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = ["Test Channel", "https://www.youtube.com/channel/UC1234567890123456789012"]
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        update_channel_metadata("UC1234567890123456789012", subscriber_count=50000)
        assert mock_conn.execute.called


class TestGetFreshChannels:
    """Tests for get_fresh_channels function."""

    def test_empty_list_returns_empty_set(self):
        """Test that empty input list returns empty set."""
        result = get_fresh_channels([])
        assert result == set()
