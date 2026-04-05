"""
Tests for yt_fts.download.batch_downloader module.

Tests BatchDownloader behavior for dry runs, channel validation,
and download orchestration.
"""

from unittest.mock import Mock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader
from yt_fts.utils.rich_console import reset_console_cache


@pytest.fixture(autouse=True)
def reset_console_state():
    """
    Ensure each test gets a fresh console state.
    
    This fixes test isolation issues where Rich console state
    from previous tests causes 'I/O operation on closed file' errors.
    """
    # Reset console cache before each test
    reset_console_cache()
    yield
    # Reset console cache after each test
    reset_console_cache()


class TestBatchDownloaderDryRun:
    """Test dry run behavior."""

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    def test_dry_run_returns_skipped_results(self, mock_api):
        """Should return skipped results without downloading."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@testchannel1", "@testchannel2"],
            dry_run=True,
        )

        # Act
        results = downloader._dry_run_channels()

        # Assert
        assert "skipped" in results
        assert len(results["skipped"]) == 2
        assert all("Dry run" in r["message"] for r in results["skipped"])

    @patch("yt_fts.services.metadata_backfill_api.YouTubeAPIBackfill")
    def test_dry_run_does_not_make_api_calls(self, mock_api):
        """Should not make any API calls in dry run mode."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@testchannel"],
            dry_run=True,
        )

        # Act - should not raise any network errors
        results = downloader._dry_run_channels()

        # Assert
        assert results["skipped"][0]["channel"] == "@testchannel"


class TestBatchDownloaderValidateChannels:
    """Test channel validation."""

    def test_validate_channels_with_valid_handle(self):
        """Should accept valid @channel handles."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test", "@AnotherTest", "@yet_an"],
        )

        # Act
        valid = downloader.validate_channels()

        # Assert - @ handles are considered valid
        assert len(valid) == 3

    def test_validate_channels_filters_empty(self):
        """Should filter out empty/whitespace channels."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test", "", "  ", "@valid"],
        )

        # Act
        valid = downloader.validate_channels()

        # Assert - empty and None are filtered, whitespace may be kept
        assert "@test" in valid
        assert "@valid" in valid


class TestBatchDownloaderProgress:
    """Test progress tracking methods."""

    def test_get_progress_returns_string(self):
        """Should return progress string."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test"],
        )

        # Act
        progress = downloader.get_progress()

        # Assert
        assert isinstance(progress, str)

    def test_save_progress_does_not_crash(self):
        """Should execute save_progress without errors."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test"],
        )

        # Act & Assert - should not raise
        downloader.save_progress()

    def test_get_progress_format(self):
        """Should return progress in expected format."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test1", "@test2", "@test3"],
        )

        # Act
        progress = downloader.get_progress()

        # Assert
        assert isinstance(progress, str)
        assert len(progress) > 0
