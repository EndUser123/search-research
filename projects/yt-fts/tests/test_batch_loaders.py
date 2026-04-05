"""
Tests for batch_loaders module.

Tests channel loading functionality including file input, database loading,
and channel cleaning.
"""
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.core.batch_loaders import (
    ChannelLoadResult,
    load_channels_from_input,
    load_channels_from_database,
    load_channels_for_batch,
    log_msg,
)


class TestChannelLoadResult:
    """Test ChannelLoadResult dataclass."""

    def test_create_result(self):
        """Test creating a ChannelLoadResult."""
        result = ChannelLoadResult(
            channels=["https://youtube.com/channel1"],
            source="file",
            raw_count=10,
            filtered_count=5,
            duplicates_removed=2,
        )
        assert result.channels == ["https://youtube.com/channel1"]
        assert result.source == "file"
        assert result.raw_count == 10
        assert result.filtered_count == 5
        assert result.duplicates_removed == 2

    def test_create_result_minimal(self):
        """Test creating a ChannelLoadResult with minimal args."""
        result = ChannelLoadResult(
            channels=["https://youtube.com/channel1"],
            source="direct",
        )
        assert result.raw_count == 0  # default
        assert result.filtered_count == 0  # default
        assert result.duplicates_removed == 0  # default


class TestLogMsg:
    """Test log_msg function."""

    def test_log_msg_writes_to_stderr(self, capsys):
        """Test log_msg writes formatted message to stderr."""
        log_msg("TEST", "Test message")
        captured = capsys.readouterr()
        assert "[TEST]" in captured.err
        assert "Test message" in captured.err


class TestLoadChannelsFromDatabase:
    """Test load_channels_from_database function."""

    @patch("yt_fts.core.batch_loaders.tempfile.NamedTemporaryFile")
    def test_load_channels_from_db_success(self, mock_temp):
        """Test loading channels from database successfully."""
        # Patch at the actual import location
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchall.return_value = [
                    ("https://youtube.com/channel1",),
                    ("https://youtube.com/channel2",),
                ]
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                mock_temp_file = MagicMock()
                mock_temp_file.name = "/tmp/test_channels.txt"
                mock_temp.return_value.__enter__.return_value = mock_temp_file

                result = load_channels_from_database()

                assert result is not None
                assert result == "/tmp/test_channels.txt"

    def test_load_channels_from_db_empty(self):
        """Test loading channels from empty database returns None."""
        with patch("sqlite_utils.Database") as mock_db_class:
            with patch("yt_fts.core.database.get_db_path") as mock_get_db_path:
                mock_db = MagicMock()
                mock_db.execute.return_value.fetchall.return_value = []
                mock_db_class.return_value = mock_db
                mock_get_db_path.return_value = "/path/to/db"

                result = load_channels_from_database()

                assert result is None


class TestLoadChannelsFromInput:
    """Test load_channels_from_input function."""

    @patch("yt_fts.core.batch_loaders.console")
    def test_load_channels_from_file(self, mock_console, tmp_path):
        """Test loading channels from a file."""
        # Mock the cleaner at actual import location
        with patch("yt_fts.services.channel_cleaner.ChannelCleaner", create=True) as mock_cleaner_class:
            mock_cleaner = MagicMock()
            mock_cleaner.clean_channels.return_value = (["https://youtube.com/channel1", "https://youtube.com/channel2", "https://youtube.com/channel3"], {"duplicates_removed": 0})
            mock_cleaner_class.return_value = mock_cleaner

            # Create test input file
            input_file = tmp_path / "channels.txt"
            input_file.write_text(
                "https://youtube.com/channel1\n"
                "# This is a comment\n"
                ":\n"
                "https://youtube.com/channel2\n"
                "\n"
                "https://youtube.com/channel3\n"
            )

            result = load_channels_from_input(str(input_file), quiet_mode=True)

            assert len(result.channels) == 3
            assert "https://youtube.com/channel1" in result.channels
            assert "https://youtube.com/channel2" in result.channels
            assert "https://youtube.com/channel3" in result.channels
            assert result.source == "file"

    @patch("yt_fts.core.batch_loaders.console")
    def test_load_channels_with_limit(self, mock_console, tmp_path):
        """Test loading channels with a limit."""
        with patch("yt_fts.services.channel_cleaner.ChannelCleaner", create=True) as mock_cleaner_class:
            mock_cleaner = MagicMock()
            mock_cleaner.clean_channels.return_value = (["https://youtube.com/channel1", "https://youtube.com/channel2"], {"duplicates_removed": 0})
            mock_cleaner_class.return_value = mock_cleaner

            input_file = tmp_path / "channels.txt"
            input_file.write_text(
                "https://youtube.com/channel1\n"
                "https://youtube.com/channel2\n"
                "https://youtube.com/channel3\n"
                "https://youtube.com/channel4\n"
            )

            result = load_channels_from_input(str(input_file), limit=2, quiet_mode=True)

            assert len(result.channels) == 2

    @patch("yt_fts.core.batch_loaders.console")
    def test_load_channels_direct_input(self, mock_console, tmp_path):
        """Test loading channels from direct input (not a file)."""
        result = load_channels_from_input("https://youtube.com/channel1", quiet_mode=True)

        assert len(result.channels) == 1
        assert result.channels == ["https://youtube.com/channel1"]
        assert result.source == "direct"

    @patch("yt_fts.core.batch_loaders.console")
    def test_load_channels_filters_comments_and_empty(self, mock_console, tmp_path):
        """Test that comments and empty lines are filtered."""
        with patch("yt_fts.services.channel_cleaner.ChannelCleaner", create=True) as mock_cleaner_class:
            mock_cleaner = MagicMock()
            mock_cleaner.clean_channels.return_value = (["https://youtube.com/channel1", "https://youtube.com/channel2"], {"duplicates_removed": 0})
            mock_cleaner_class.return_value = mock_cleaner

            input_file = tmp_path / "channels.txt"
            input_file.write_text(
                "# Comment line\n"
                "https://youtube.com/channel1\n"
                "\n"
                ":\n"
                "https://youtube.com/channel2\n"
            )

            result = load_channels_from_input(str(input_file), quiet_mode=True)

            assert len(result.channels) == 2

    @patch("yt_fts.core.batch_loaders.console")
    def test_load_channels_finds_in_data_dir(self, mock_console, tmp_path):
        """Test loading channels finds file in data subdirectory."""
        with patch("yt_fts.services.channel_cleaner.ChannelCleaner", create=True) as mock_cleaner_class:
            mock_cleaner = MagicMock()
            mock_cleaner.clean_channels.return_value = (["https://youtube.com/channel1"], {"duplicates_removed": 0})
            mock_cleaner_class.return_value = mock_cleaner

            # Create script directory structure
            script_dir = tmp_path / "src" / "yt_fts" / "core"
            script_dir.mkdir(parents=True)

            # Create input file in data subdirectory
            data_dir = tmp_path / "data"
            data_dir.mkdir(parents=True)
            input_file = data_dir / "channels.txt"
            input_file.write_text("https://youtube.com/channel1\n")

            # Patch the script directory detection - return a value that will make Path(file).parent
            # resolve to the correct location
            with patch("yt_fts.core.batch_loaders.os.path.dirname") as mock_dirname:
                with patch("yt_fts.core.batch_loaders.os.path.abspath") as mock_abspath:
                    # Return the data directory as the "script" location
                    mock_abspath.return_value = str(data_dir)
                    mock_dirname.return_value = str(data_dir)

                    result = load_channels_from_input("channels.txt", quiet_mode=True)

                    assert len(result.channels) == 1


class TestLoadChannelsForBatch:
    """Test load_channels_for_batch function."""

    @patch("yt_fts.core.batch_loaders.load_channels_from_input")
    def test_load_from_input_file(self, mock_load_input):
        """Test load_channels_for_batch uses input file when provided."""
        mock_load_input.return_value = ChannelLoadResult(
            channels=["https://youtube.com/channel1"],
            source="file",
        )

        channels, source = load_channels_for_batch(
            input_file="channels.txt", limit=5
        )

        assert len(channels) == 1
        assert source == "file"
        mock_load_input.assert_called_once_with("channels.txt", 5, False)

    @patch("yt_fts.core.batch_loaders.load_channels_from_database")
    @patch("yt_fts.core.batch_loaders.load_channels_from_input")
    def test_load_from_database_when_no_input_file(
        self, mock_load_input, mock_load_db
    ):
        """Test load_channels_for_batch loads from DB when input_file is None."""
        mock_load_db.return_value = "/tmp/channels.txt"
        mock_load_input.return_value = ChannelLoadResult(
            channels=["https://youtube.com/channel1"],
            source="database",
        )

        channels, source = load_channels_for_batch(input_file=None)

        assert len(channels) == 1
        assert source == "database"
        mock_load_db.assert_called_once()

    @patch("yt_fts.core.batch_loaders.load_channels_from_database")
    def test_load_from_database_returns_empty_on_none(self, mock_load_db):
        """Test load_channels_for_batch returns empty list when DB has no channels."""
        mock_load_db.return_value = None

        channels, source = load_channels_for_batch(input_file=None)

        assert channels == []
        assert source == "none"
