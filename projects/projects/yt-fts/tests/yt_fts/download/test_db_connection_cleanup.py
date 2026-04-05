"""
Tests for database connection cleanup in download_handler.py.

TDD Phase: GREEN - Tests verify that database connections are properly closed even on errors.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from yt_fts.download.download_handler import DownloadHandler


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


class TestDatabaseConnectionCleanup:
    """Tests for proper database connection cleanup in vtt_to_db."""

    @patch("yt_fts.download.download_handler.get_db_connection")
    @patch("yt_fts.download.download_handler.parse_vtt")
    @patch("yt_fts.download.download_handler.check_interruption", return_value=False)
    def test_connection_closed_on_normal_completion(
        self, mock_check_interruption, mock_parse_vtt, mock_get_conn, temp_dir
    ):
        """Connection should be closed when vtt_to_db completes normally."""
        # Setup: Mock connection
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_conn.cursor.return_value = mock_cursor = MagicMock()
        # Configure mock as context manager that returns itself
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_get_conn.return_value = mock_conn

        # Create test VTT files with metadata
        vtt_file = temp_dir / "test_video.en.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest subtitle")

        json_file = temp_dir / "test_video.info.json"
        json_file.write_text('{"id": "test_video", "title": "Test", "upload_date": "20240101", "channel_id": "UC123", "duration": 60}')

        # Mock VTT parsing
        mock_parse_vtt.return_value = [
            {"start_time": 0.0, "stop_time": 1.0, "text": "Test subtitle"}
        ]

        # Create handler and set tmp_dir directly (use rich_mode=True to avoid clear_live issues)
        handler = DownloadHandler(rich_mode=True, suppress_status_messages=True)
        handler.tmp_dir = str(temp_dir)

        handler.vtt_to_db()

        # Verify connection context manager's __exit__ was called
        assert mock_conn.__exit__.called, "Connection __exit__ must be called after normal completion"

    @patch("yt_fts.download.download_handler.get_db_connection")
    @patch("yt_fts.download.download_handler.parse_vtt")
    @patch("yt_fts.download.download_handler.check_interruption", return_value=False)
    def test_connection_closed_on_commit_failure(
        self, mock_check_interruption, mock_parse_vtt, mock_get_conn, temp_dir
    ):
        """
        Connection should be closed even if commit() raises an exception.

        This is the critical bug fix: if con.commit() fails, the connection
        must still be closed to prevent leaks.
        """
        # Setup: Mock connection that raises error on commit
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_conn.commit.side_effect = sqlite3.OperationalError("database is locked")
        # Configure mock as context manager that returns itself
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_get_conn.return_value = mock_conn

        # Create test files
        vtt_file = temp_dir / "test_video.en.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest")

        json_file = temp_dir / "test_video.info.json"
        json_file.write_text('{"id": "test_video", "title": "Test", "upload_date": "20240101", "channel_id": "UC123", "duration": 60}')

        mock_parse_vtt.return_value = [{"start_time": 0.0, "stop_time": 1.0, "text": "Test"}]

        # Create handler and set tmp_dir directly (use rich_mode=True to avoid clear_live issues)
        handler = DownloadHandler(rich_mode=True, suppress_status_messages=True)
        handler.tmp_dir = str(temp_dir)

        # Call - commit error should propagate, but connection must still be closed
        with pytest.raises(sqlite3.OperationalError, match="database is locked"):
            handler.vtt_to_db()

        # CRITICAL ASSERTION: Connection context manager's __exit__ must be called even after commit error
        # This ensures proper cleanup via context manager
        assert mock_conn.__exit__.called, "Connection __exit__ must be called even when commit fails"

    @patch("yt_fts.download.download_handler.get_db_connection")
    @patch("yt_fts.download.download_handler.parse_vtt")
    @patch("yt_fts.download.download_handler.check_interruption", return_value=False)
    def test_connection_closed_on_database_error(
        self, mock_check_interruption, mock_parse_vtt, mock_get_conn, temp_dir
    ):
        """Connection should be closed even if cursor.execute raises an error."""
        # Setup: Mock connection where execute fails
        mock_conn = MagicMock(spec=sqlite3.Connection)
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.execute.side_effect = sqlite3.IntegrityError("UNIQUE constraint")
        # Configure mock as context manager that returns itself
        mock_conn.__enter__ = Mock(return_value=mock_conn)
        mock_conn.__exit__ = Mock(return_value=False)
        mock_get_conn.return_value = mock_conn

        # Create test files
        vtt_file = temp_dir / "test_video.en.vtt"
        vtt_file.write_text("WEBVTT\n\n00:00:00.000 --> 00:00:01.000\nTest")

        json_file = temp_dir / "test_video.info.json"
        json_file.write_text('{"id": "test_video", "title": "Test", "upload_date": "20240101", "channel_id": "UC123", "duration": 60}')

        mock_parse_vtt.return_value = [{"start_time": 0.0, "stop_time": 1.0, "text": "Test"}]

        # Create handler and set tmp_dir directly (use rich_mode=True to avoid clear_live issues)
        handler = DownloadHandler(rich_mode=True, suppress_status_messages=True)
        handler.tmp_dir = str(temp_dir)

        handler.vtt_to_db()

        # Connection must be closed even after database error
        assert mock_conn.__exit__.called, "Connection __exit__ must be called even when execute fails"
