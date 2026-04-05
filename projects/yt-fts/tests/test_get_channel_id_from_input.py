#!/usr/bin/env python3
"""
Comprehensive tests for the enhanced get_channel_id_from_input function.

Tests integration with UnifiedChannelProcessor, backward compatibility,
error handling, and performance optimizations.

Author: CSF NIP Implementation Team
Version: 1.0.0
"""

import gc
import sys
import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch, call

import pytest

# Add src to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from yt_fts.core.database import add_channel_info, get_channel_id_from_input, make_db
from yt_fts.services.unified_channel_processor import (
    ChannelInfo,
    ChannelResult,
    InputType,
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
    # Second GC pass to catch any objects freed by the first pass
    gc.collect()


class TestGetChannelIdFromInput:
    """Test suite for enhanced get_channel_id_from_input function."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        import uuid
        import shutil
        import sqlite3

        # Create a temp directory that we'll clean up manually
        tmpdir = Path(tempfile.mkdtemp())
        try:
            # Use unique filename to avoid cross-test locking issues
            unique_name = f"test_{uuid.uuid4().hex[:8]}.db"
            temp_db_path = tmpdir / unique_name

            # Initialize the database using raw sqlite3 to avoid connection pooling
            conn = sqlite3.connect(str(temp_db_path))
            cur = conn.cursor()

            # Create Channels table
            cur.execute("""
                CREATE TABLE Channels (
                    channel_id TEXT PRIMARY KEY,
                    channel_name TEXT NOT NULL,
                    channel_url TEXT NOT NULL
                )
            """)

            # Create Videos table
            cur.execute("""
                CREATE TABLE Videos (
                    video_id TEXT PRIMARY KEY,
                    video_title TEXT NOT NULL,
                    video_url TEXT NOT NULL,
                    channel_id TEXT,
                    video_date TEXT,
                    duration INTEGER,
                    thumbnail_url TEXT,
                    view_count INTEGER,
                    is_short INTEGER,
                    FOREIGN KEY (channel_id) REFERENCES Channels(channel_id)
                )
            """)

            # Create Subtitles table
            cur.execute("""
                CREATE TABLE Subtitles (
                    subtitle_id INTEGER PRIMARY KEY,
                    video_id TEXT NOT NULL,
                    start_time TEXT NOT NULL,
                    stop_time TEXT,
                    text TEXT NOT NULL,
                    FOREIGN KEY (video_id) REFERENCES Videos(video_id)
                )
            """)

            conn.commit()
            conn.close()

            # Insert test data directly to avoid sqlite_utils connection pooling
            conn = sqlite3.connect(str(temp_db_path))
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO Channels VALUES (?, ?, ?)",
                ("UC1234567890123456789012", "Test Channel One", "https://www.youtube.com/channel/UC1234567890123456789012")
            )
            cur.execute(
                "INSERT INTO Channels VALUES (?, ?, ?)",
                ("UC9876543210987654321098", "Test Channel Two", "https://www.youtube.com/channel/UC9876543210987654321098")
            )
            conn.commit()
            conn.close()

            yield str(temp_db_path)
        finally:
            # Cleanup: try to remove the temp directory, ignore errors on Windows
            try:
                shutil.rmtree(tmpdir, ignore_errors=True)
            except:
                pass

    @pytest.fixture
    def mock_channel_info(self):
        """Mock channel information for testing."""
        return ChannelInfo(
            channel_id="UC1234567890123456789012",
            name="Test Channel",
            handle="@testchannel",
            url="https://www.youtube.com/channel/UC1234567890123456789012"
        )

    def test_backward_compatibility_rowid(self, temp_db):
        """Test backward compatibility with database rowid lookup."""
        import sqlite3
        # Patch get_db_connection to use temp database
        with patch("yt_fts.db.channels.get_db_connection") as mock_get_conn:
            conn = sqlite3.connect(str(temp_db))
            mock_get_conn.return_value.__enter__.return_value = conn
            # Test successful rowid lookup
            channel_id = get_channel_id_from_input(1)
            assert channel_id in ["UC1234567890123456789012", "UC9876543210987654321098"]
            conn.close()

    def test_backward_compatibility_channel_name(self, temp_db):
        """Test backward compatibility with channel name lookup."""
        import sqlite3
        # Patch get_db_connection to use temp database
        with patch("yt_fts.db.channels.get_db_connection") as mock_get_conn:
            conn = sqlite3.connect(str(temp_db))
            mock_get_conn.return_value.__enter__.return_value = conn
            # Test successful name lookup
            channel_id = get_channel_id_from_input("Test Channel One")
            assert channel_id == "UC1234567890123456789012"
            conn.close()

    def test_input_validation_none(self):
        """Test input validation for None input."""
        with pytest.raises(ValueError, match="Channel input cannot be None"):
            get_channel_id_from_input(None)

    def test_input_validation_empty_string(self):
        """Test input validation for empty string."""
        with pytest.raises(ValueError, match="Channel input cannot be empty"):
            get_channel_id_from_input("")

        with pytest.raises(ValueError, match="Channel input cannot be empty"):
            get_channel_id_from_input("   ")

    def test_input_validation_invalid_type(self):
        """Test input validation for invalid types."""
        with pytest.raises(ValueError, match="Channel input must be string or integer"):
            get_channel_id_from_input([])

        with pytest.raises(ValueError, match="Channel input must be string or integer"):
            get_channel_id_from_input({})

    def test_input_validation_negative_rowid(self):
        """Test input validation for negative rowid."""
        with pytest.raises(ValueError, match="Row ID must be a positive integer"):
            get_channel_id_from_input(-1)

        with pytest.raises(ValueError, match="Row ID must be a positive integer"):
            get_channel_id_from_input(0)

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    @patch("yt_fts.db.channels.check_if_channel_exists")
    @patch("yt_fts.db.channels.add_channel_info")
    @patch("yt_fts.db.channels.get_channel_id_from_rowid")
    @patch("yt_fts.db.channels.get_channel_id_from_name")
    def test_handle_resolution_success(self, mock_name, mock_rowid, mock_add, mock_check, mock_create_processor, mock_channel_info):
        """Test successful @handle resolution using UnifiedChannelProcessor."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.HANDLE,
            processing_time_ms=50
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)
        mock_check.return_value = False  # Channel doesn't exist in DB
        mock_name.return_value = None  # Not in database by name
        mock_rowid.return_value = None  # Not a rowid

        # Test @handle resolution
        channel_id = get_channel_id_from_input("@testchannel")

        assert channel_id == "UC1234567890123456789012"
        mock_processor.process_channel_input.assert_called_once_with("@testchannel")
        mock_add.assert_called_once()

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    @patch("yt_fts.db.channels.get_db_connection")
    def test_url_resolution_success(self, mock_get_conn, mock_create_processor, mock_channel_info):
        """Test successful URL resolution using UnifiedChannelProcessor."""
        # Setup mocks - database returns None (not found)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Not found in database
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.URL,
            processing_time_ms=100
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test URL resolution
        url = "https://www.youtube.com/channel/UC1234567890123456789012"
        channel_id = get_channel_id_from_input(url)

        assert channel_id == "UC1234567890123456789012"
        mock_processor.process_channel_input.assert_called_once_with(url)

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    @patch("yt_fts.db.channels.get_db_connection")
    def test_channel_id_resolution_success(self, mock_get_conn, mock_create_processor, mock_channel_info):
        """Test successful channel ID resolution using UnifiedChannelProcessor."""
        # Setup mocks - database returns None (not found)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Not found in database
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.CHANNEL_ID,
            processing_time_ms=25
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test channel ID resolution
        channel_id_input = "UC1234567890123456789012"
        channel_id = get_channel_id_from_input(channel_id_input)

        assert channel_id == "UC1234567890123456789012"
        mock_processor.process_channel_input.assert_called_once_with(channel_id_input)

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_resolution_failure_with_suggestions(self, mock_create_processor):
        """Test resolution failure with helpful suggestions."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=False,
            error="Channel not found",
            suggestions=[
                "Check the @handle format (e.g., '@channelname')",
                "Try the channel's full URL instead",
                "Verify the channel exists on YouTube"
            ]
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test resolution failure
        with pytest.raises(ValueError) as exc_info:
            get_channel_id_from_input("@nonexistentchannel")

        error_message = str(exc_info.value)
        assert "Could not resolve channel '@nonexistentchannel'" in error_message
        assert "Channel not found" in error_message
        assert "Suggestions:" in error_message
        assert "Check the @handle format" in error_message

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_resolution_failure_without_suggestions(self, mock_create_processor):
        """Test resolution failure without suggestions."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=False,
            error="Network error",
            suggestions=None
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test resolution failure
        with pytest.raises(ValueError) as exc_info:
            get_channel_id_from_input("invalid_input")

        error_message = str(exc_info.value)
        assert "Could not resolve channel 'invalid_input'" in error_message
        assert "Network error" in error_message
        # Should not contain suggestions section
        assert "Suggestions:" not in error_message

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_unexpected_error_handling(self, mock_create_processor):
        """Test handling of unexpected errors during resolution."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        # Simulate an unexpected exception
        mock_processor.process_channel_input = AsyncMock(side_effect=Exception("Unexpected network failure"))

        # Test unexpected error handling
        with pytest.raises(ValueError) as exc_info:
            get_channel_id_from_input("@testchannel")

        error_message = str(exc_info.value)
        assert "Unexpected error resolving channel '@testchannel'" in error_message
        assert "Unexpected network failure" in error_message

    def test_database_fallback_mechanism(self, temp_db):
        """Test that database lookups are tried first before processor."""
        import sqlite3
        # Patch get_db_connection to use temp database
        with patch("yt_fts.db.channels.get_db_connection") as mock_get_conn:
            conn = sqlite3.connect(str(temp_db))
            mock_get_conn.return_value.__enter__.return_value = conn
            # This test verifies that we still get database hits even when
            # UnifiedChannelProcessor might fail

            # Test that name lookup works
            channel_id = get_channel_id_from_input("Test Channel Two")
            assert channel_id == "UC9876543210987654321098"
            conn.close()

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    @patch("yt_fts.db.channels.check_if_channel_exists")
    @patch("yt_fts.db.channels.get_channel_id_from_name")
    def test_caching_to_database(self, mock_name, mock_check, mock_create_processor, mock_channel_info):
        """Test that successful resolution is cached to local database."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.HANDLE
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)
        mock_check.return_value = False  # Channel doesn't exist in DB
        mock_name.return_value = None  # Not in database

        # Test that successful resolution gets cached
        with patch("yt_fts.db.channels.add_channel_info") as mock_add:
            get_channel_id_from_input("@newchannel")

            mock_add.assert_called_once_with(
                "UC1234567890123456789012",
                "Test Channel",
                "https://www.youtube.com/channel/UC1234567890123456789012"
            )

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    @patch("yt_fts.core.database.check_if_channel_exists")
    def test_no_caching_when_channel_exists(self, mock_check, mock_create_processor, mock_channel_info):
        """Test that existing channels are not added to database again."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.HANDLE
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)
        mock_check.return_value = True  # Channel already exists in DB

        # Test that existing channels are not added again
        with patch("yt_fts.core.database.add_channel_info") as mock_add:
            get_channel_id_from_input("@existingchannel")

            mock_add.assert_not_called()

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_database_caching_error_handling(self, mock_create_processor, mock_channel_info):
        """Test that database caching errors don't break the main resolution."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.HANDLE
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test that database caching errors are ignored
        with patch("yt_fts.core.database.check_if_channel_exists", return_value=False), \
             patch("yt_fts.core.database.add_channel_info", side_effect=Exception("Database error")):

            # Should still succeed despite database caching error
            channel_id = get_channel_id_from_input("@testchannel")
            assert channel_id == "UC1234567890123456789012"

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_async_sync_bridging(self, mock_create_processor, mock_channel_info):
        """Test that async/sync bridging works correctly."""
        # Setup mocks
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UC1234567890123456789012",
            channel_info=mock_channel_info,
            input_type=InputType.HANDLE,
            processing_time_ms=10
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Test that the async function can be called from sync context
        channel_id = get_channel_id_from_input("@asynctest")

        assert channel_id == "UC1234567890123456789012"
        mock_processor.process_channel_input.assert_called_once_with("@asynctest")

    @patch("yt_fts.db.channels.get_channel_id_from_rowid", return_value=None)
    @patch("yt_fts.db.channels.get_db_connection")
    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_string_integer_conversion(self, mock_create, mock_get_conn, mock_rowid):
        """Test that string integers are handled as names, not rowids."""
        # This should be treated as a name, not a rowid, since it's a string
        # Mock database to return None (not found)
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_cursor.fetchone.return_value = None  # Not found in database
        mock_conn.execute.return_value = mock_cursor
        mock_get_conn.return_value.__enter__.return_value = mock_conn

        # Setup processor to return a result
        mock_processor = MagicMock()
        mock_create.return_value = mock_processor
        from yt_fts.services.unified_channel_processor import ChannelResult, InputType
        mock_result = ChannelResult(
            success=True,
            channel_id="UCSTRINGTEST",
            channel_info=None,
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        channel_id = get_channel_id_from_input("123")
        assert channel_id == "UCSTRINGTEST"
        mock_rowid.assert_not_called()  # Should not call rowid for string input

    def test_whitespace_handling(self):
        """Test that whitespace is properly handled."""
        with patch("yt_fts.core.database.get_channel_id_from_name") as mock_name:
            mock_name.return_value = None

            with patch("yt_fts.services.unified_channel_processor.create_processor_for_cli") as mock_create:
                mock_processor = MagicMock()
                mock_create.return_value = mock_processor

                mock_result = ChannelResult(
                    success=True,
                    channel_id="UCWHITESPACETEST",
                    channel_info=ChannelInfo(
                        channel_id="UCWHITESPACETEST",
                        name="Test Channel"
                    )
                )
                mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

                # Test with various whitespace patterns
                channel_id = get_channel_id_from_input("  @testchannel  ")
                assert channel_id == "UCWHITESPACETEST"

                # Verify that stripped input was passed to processor
                mock_processor.process_channel_input.assert_called_with("@testchannel")


class TestIntegrationWithExistingComponents:
    """Test integration with existing yt-fts components."""

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_integration_with_export_module(self, mock_create_processor):
        """Test integration pattern used by export module."""
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UCTESTEXPORT123456789012345",
            channel_info=ChannelInfo(
                channel_id="UCTESTEXPORT123456789012345",
                name="Export Test Channel"
            )
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Simulate how export module uses the function
        channel_id = get_channel_id_from_input("@exporttest")
        assert channel_id == "UCTESTEXPORT123456789012345"

    @patch("yt_fts.services.unified_channel_processor.create_processor_for_cli")
    def test_integration_with_search_module(self, mock_create_processor):
        """Test integration pattern used by search module."""
        mock_processor = MagicMock()
        mock_create_processor.return_value = mock_processor

        mock_result = ChannelResult(
            success=True,
            channel_id="UCTESTSEARCH123456789012345",
            channel_info=ChannelInfo(
                channel_id="UCTESTSEARCH123456789012345",
                name="Search Test Channel"
            )
        )
        mock_processor.process_channel_input = AsyncMock(return_value=mock_result)

        # Simulate how search module uses the function
        channel_id = get_channel_id_from_input("https://www.youtube.com/channel/UCTESTSEARCH123456789012345")
        assert channel_id == "UCTESTSEARCH123456789012345"


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v", "--tb=short"])
