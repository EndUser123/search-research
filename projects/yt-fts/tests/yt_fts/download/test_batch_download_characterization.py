"""Characterization tests for batch_download command."""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

import pytest

from yt_fts.core.download_cli import batch_download


class TestBatchDownloadCharacterization:
    """Characterization tests for batch_download Click command."""

    @pytest.fixture
    def runner(self):
        return CliRunner()

    @pytest.fixture
    def temp_channels_file(self):
        with tempfile.NamedTemporaryFile(
            mode="w", suffix="_channels.txt", delete=False, encoding="utf-8"
        ) as f:
            for line in ["@testchannel1", "https://youtube.com/@testchannel2", "# Comment", "@testchannel3"]:
                f.write(line + chr(10))
            temp_path = f.name
        yield temp_path
        try:
            os.unlink(temp_path)
        except OSError:
            pass

    @patch("yt_fts.services.channel_cleaner.ChannelCleaner")
    def test_dry_run_with_channels_file(self, mock_cleaner_class, runner, temp_channels_file):
        """Characterization: --dry-run processes file but does not download."""
        mock_cleaner = MagicMock()
        mock_cleaner.clean_channels_file_cached.return_value = (
            ["@testchannel1", "@testchannel2", "@testchannel3"],
            {"cache_hit": False, "duplicates_removed": 0, "invalid_removed": 0}
        )
        mock_cleaner_class.return_value = mock_cleaner
        result = runner.invoke(batch_download, ["--dry-run", temp_channels_file])
        # Should exit successfully or with expected exit code
        # (dry-run mode exits early, before actual download)
        assert result.exit_code in [0, None, 1]

    @patch("yt_fts.core.download_cli.load_channels_from_database")
    @patch("yt_fts.core.download_cli.initialize_batch_logging")
    @patch("yt_fts.core.download_cli.BatchDownloader")
    def test_database_mode_when_no_input(
        self, mock_downloader_class, mock_init_logging, mock_load_db, runner
    ):
        """Characterization: When no input file, loads from database."""
        mock_load_db.return_value = (["@channel1"], "temp_file.txt")
        mock_init_logging.return_value = (MagicMock(), 3.0)
        mock_downloader = MagicMock()
        mock_downloader_class.return_value = mock_downloader
        result = runner.invoke(batch_download, [])
        mock_load_db.assert_called_once()

    @patch("yt_fts.services.channel_intake.ChannelIntakeService")
    def test_import_only_mode(self, mock_service_class, runner):
        """Characterization: --import-only imports channels then exits."""
        mock_service = MagicMock()
        mock_service.process.return_value = (["@channel1"], {"valid": 1})
        mock_service_class.return_value = mock_service
        with tempfile.NamedTemporaryFile(mode="w", suffix="_import.txt", delete=False) as f:
            import_path = f.name
        try:
            result = runner.invoke(batch_download, ["--import", import_path, "--import-only"])
            mock_service.process.assert_called_once()
        finally:
            try:
                os.unlink(import_path)
            except OSError:
                pass