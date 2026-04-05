"""
Test channel name lookup in DownloadHandler.

Verifies that DownloadHandler queries the database for the actual
channel_name instead of using the raw channel_id for display.
"""

import sqlite3
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from rich.console import Console

from yt_fts.download.download_handler import DownloadHandler


@pytest.fixture
def temp_db_path():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False) as f:
        db_path = f.name
    yield db_path
    # Cleanup
    Path(db_path).unlink(missing_ok=True)


@pytest.fixture
def test_db_with_channel(temp_db_path):
    """Create a test database with a channel entry."""
    conn = sqlite3.connect(temp_db_path)
    cursor = conn.cursor()

    # Create Channels table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT,
            channel_url TEXT
        )
    """)

    # Create Videos table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Videos (
            video_id TEXT PRIMARY KEY,
            channel_id TEXT,
            title TEXT,
            publish_date TEXT,
            download_date TEXT
        )
    """)

    # Create Subtitles table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS Subtitles (
            subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            start_time TEXT,
            stop_time TEXT,
            text TEXT,
            language_code TEXT,
            is_generated INTEGER DEFAULT 0,
            source_type TEXT DEFAULT 'official'
        )
    """)

    # Insert a test channel with human-readable name
    test_channel_id = "UCXKeNggiHUHpdkIfUj7KEEg"
    test_channel_name = "3Blue1Brown"
    test_channel_url = "https://www.youtube.com/@3blue1brown"

    cursor.execute(
        "INSERT INTO Channels (channel_id, channel_name, channel_url) VALUES (?, ?, ?)",
        (test_channel_id, test_channel_name, test_channel_url)
    )

    conn.commit()
    conn.close()

    return {
        "db_path": temp_db_path,
        "channel_id": test_channel_id,
        "channel_name": test_channel_name,
        "channel_url": test_channel_url
    }


def test_channel_name_lookup_from_database(test_db_with_channel):
    """
    Test that DownloadHandler looks up channel_name from database.

    When a channel_id is used to initialize download, the handler should
    query the Channels table for the human-readable channel_name instead
    of displaying the raw channel_id.
    """

    test_data = test_db_with_channel
    channel_id = test_data["channel_id"]
    expected_name = test_data["channel_name"]

    # Mock get_db_connection to return our test database as a context manager
    class MockConnection:
        def __enter__(self):
            self._conn = sqlite3.connect(test_data["db_path"])
            return self._conn
        def __exit__(self, *args):
            self._conn.close()
    
    mock_get_db_connection = MockConnection

    # Mock get_channel_id_from_input to return our test channel_id
    def mock_get_channel_id_from_input(input_val):
        return channel_id

    # Mock the session initialization to avoid actual network calls
    def mock_init_session(self, url):
        return MagicMock()

    # Mock the download methods to avoid actual downloads
    def mock_download_vtts(self):
        self._videos_saved_during_download = []
        self.videos_saved_to_db = 0

    with patch("yt_fts.db.channels.get_db_connection", mock_get_db_connection):
        with patch("yt_fts.core.database.get_channel_id_from_input", mock_get_channel_id_from_input):
            with patch.object(DownloadHandler, "init_session", mock_init_session):
                with patch.object(DownloadHandler, "download_vtts", mock_download_vtts):
                    # Create DownloadHandler with suppress_status_messages=True to avoid print noise
                    console = Console(stderr=True)
                    handler = DownloadHandler(
                        console=console,
                        suppress_status_messages=True
                    )

                    # Mock video_ids to trigger the download path
                    handler.video_ids = ["video1", "video2"]
                    handler.tmp_dir = tempfile.mkdtemp()

                    # Call update_channel - this should trigger the channel_name lookup
                    handler.update_channel(channel_id)

                    # Verify that channel_name was looked up from database
                    assert handler.channel_name == expected_name, (
                        f"Expected channel_name to be '{expected_name}' from database, "
                        f"but got '{handler.channel_name}'"
                    )

                    # Verify it's NOT the raw channel_id
                    assert handler.channel_name != channel_id, (
                        f"channel_name should not be the raw channel_id '{channel_id}'"
                    )

    # Cleanup tmp_dir
    if hasattr(handler, "tmp_dir") and Path(handler.tmp_dir).exists():
        Path(handler.tmp_dir).rmdir()


def test_channel_name_fallback_when_not_in_database(test_db_with_channel):
    """
    Test that DownloadHandler falls back to channel_id when channel_name
    is not found in database.
    """

    test_data = test_db_with_channel
    # Use a channel_id that's NOT in the database
    unknown_channel_id = "UCUnknownChannelId123456"

    class MockConnection2:
        def __enter__(self):
            self._conn = sqlite3.connect(test_data["db_path"])
            return self._conn
        def __exit__(self, *args):
            self._conn.close()
    
    mock_get_db_connection2 = MockConnection2

    def mock_get_channel_id_from_input(input_val):
        return unknown_channel_id

    def mock_init_session(self, url):
        return MagicMock()

    def mock_download_vtts(self):
        self._videos_saved_during_download = []
        self.videos_saved_to_db = 0

    with patch("yt_fts.db.channels.get_db_connection", mock_get_db_connection2):
        with patch("yt_fts.core.database.get_channel_id_from_input", mock_get_channel_id_from_input):
            with patch.object(DownloadHandler, "init_session", mock_init_session):
                with patch.object(DownloadHandler, "download_vtts", mock_download_vtts):
                    console = Console(stderr=True)
                    handler = DownloadHandler(
                        console=console,
                        suppress_status_messages=True
                    )

                    handler.video_ids = ["video1"]
                    handler.tmp_dir = tempfile.mkdtemp()

                    handler.update_channel(unknown_channel_id)

                    # Should fall back to channel_id when not in database
                    assert handler.channel_name == unknown_channel_id, (
                        f"Expected channel_name to fallback to channel_id '{unknown_channel_id}'"
                    )

    if hasattr(handler, "tmp_dir") and Path(handler.tmp_dir).exists():
        Path(handler.tmp_dir).rmdir()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
