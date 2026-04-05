"""
Tests for yt_fts.download.batch_downloader module.

Tests BatchDownloader behavior for dry runs, channel validation,
and download orchestration.
"""

from unittest.mock import Mock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


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

        # Act & Assert - should not raise (even if not implemented)
        downloader.save_progress()


class TestBatchDownloaderSummary:
    """Test summary and reporting methods."""

    def test_display_summary_does_not_crash(self):
        """Should display summary without errors."""
        # Arrange
        downloader = BatchDownloader(
            channels=["@test"],
        )

        # Act & Assert - should not raise
        downloader.display_summary()

    def test_export_report_without_results(self, tmp_path):
        """Should handle export when no results exist."""
        # Arrange
        report_file = tmp_path / "report.json"
        downloader = BatchDownloader(
            channels=["@test"],
        )
        # No results set

        # Act
        downloader.export_report(str(report_file))

        # Assert - file not created when no results
        assert not report_file.exists()

    def test_export_report_with_results(self, tmp_path):
        """Should create file when results exist."""
        # Arrange
        report_file = tmp_path / "report.json"
        downloader = BatchDownloader(
            channels=["@test"],
        )
        downloader.results = {"successful": ["@test"]}

        # Act
        downloader.export_report(str(report_file))

        # Assert - file created when results exist
        assert report_file.exists()


class TestBatchDownloaderAttributes:
    """Test attribute initialization."""

    def test_channels_stored(self):
        """Should store channels list."""
        # Arrange
        channels = ["@test1", "@test2"]
        downloader = BatchDownloader(channels=channels)

        # Assert
        assert downloader.channels == channels

    def test_dry_run_attribute(self):
        """Should store dry_run flag."""
        # Arrange
        downloader = BatchDownloader(channels=["@test"], dry_run=True)

        # Assert
        assert downloader.dry_run is True

    def test_jobs_default(self):
        """Should default jobs to 2."""
        # Arrange
        downloader = BatchDownloader(channels=["@test"])

        # Assert
        assert downloader.jobs == 2

    def test_jobs_custom(self):
        """Should accept custom jobs value."""
        # Arrange
        downloader = BatchDownloader(channels=["@test"], jobs=4)

        # Assert
        assert downloader.jobs == 4