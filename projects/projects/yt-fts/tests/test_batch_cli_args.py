"""Test batch-download CLI argument changes.

Tests for current CLI arguments:
- --channels-scan-per-batch: Maximum total channels to scan from file
- --channels-download-per-batch: Stop after N channels have videos downloaded

Note: These tests check CLI argument parsing only. They don't validate
actual download behavior since that would require network calls to YouTube.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner

from yt_fts.core.cli import cli


def test_max_scan_option_accepts_value():
    """Test that --channels-scan-per-batch option is accepted."""
    runner = CliRunner()

    # Create a temporary channels file with 5 channels
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n@channel2\n@channel3\n@channel4\n@channel5\n")
        channels_file = f.name

    try:
        # Mock the download to avoid actual network calls
        with patch("yt_fts.core.download_cli.BatchDownloader") as mock_downloader:
            mock_instance = mock_downloader.return_value
            mock_instance.download_all.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--channels-scan-per-batch",
                    "3",
                    "--delay",
                    "0",
                ],
            )
            # The command should parse correctly without "no such option" error
            assert "no such option" not in result.output.lower()
            assert "unrecognized arguments" not in result.output.lower()
    finally:
        Path(channels_file).unlink(missing_ok=True)


def test_max_downloads_option_accepts_value():
    """Test that --channels-download-per-batch option is accepted."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n@channel2\n@channel3\n")
        channels_file = f.name

    try:
        # Mock the download to avoid actual network calls
        with patch("yt_fts.core.download_cli.BatchDownloader") as mock_downloader:
            mock_instance = mock_downloader.return_value
            mock_instance.download_all.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--channels-download-per-batch",
                    "2",
                    "--delay",
                    "0",
                ],
            )
            # The command should parse correctly
            assert "no such option" not in result.output.lower()
            assert "unrecognized arguments" not in result.output.lower()
    finally:
        Path(channels_file).unlink(missing_ok=True)


def test_both_options_work_together():
    """Test that --channels-scan-per-batch and --channels-download-per-batch can be used together."""
    runner = CliRunner()

    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
        f.write("@channel1\n@channel2\n@channel3\n@channel4\n@channel5\n")
        channels_file = f.name

    try:
        # Mock the download to avoid actual network calls
        with patch("yt_fts.core.download_cli.BatchDownloader") as mock_downloader:
            mock_instance = mock_downloader.return_value
            mock_instance.download_all.return_value = {
                "successful": [],
                "failed": [],
                "skipped": [],
            }

            result = runner.invoke(
                cli,
                [
                    "batch-download",
                    channels_file,
                    "--channels-scan-per-batch",
                    "10",
                    "--channels-download-per-batch",
                    "3",
                    "--delay",
                    "0",
                ],
            )
            # Both options should be accepted
            assert "no such option" not in result.output.lower()
            assert "unrecognized arguments" not in result.output.lower()
    finally:
        Path(channels_file).unlink(missing_ok=True)


if __name__ == "__main__":
    import pytest

    pytest.main([__file__, "-v"])
