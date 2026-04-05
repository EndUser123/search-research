"""
Failing tests for yt-dlp logging display issue.

These tests FAIL because the current code sets yt_dlp to WARNING level,
which causes visual corruption when WARNING messages appear inline with
Rich progress bars.

Run with: pytest tests/test_batch_downloader_logging_fix.py -v

Expected: All tests should FAIL initially
After Fix: All tests should PASS when yt_dlp is set to ERROR level
"""

import logging
from unittest.mock import MagicMock, patch

import pytest

from yt_fts.download.batch_downloader import BatchDownloader


class TestYtDlpLoggerLevel:
    """Tests for yt_dlp logger level configuration."""

    @pytest.fixture
    def downloader(self):
        """Create BatchDownloader instance for testing."""
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
        )

    def test_yt_dlp_logger_set_to_error_level(self, downloader):
        """
        Test that yt_dlp logger is set to ERROR level (not WARNING).

        Given: A BatchDownloader instance
        When: _initialize_batch_download is called
        Then: yt_dlp logger should be set to ERROR level
        """
        # Act
        with patch("yt_fts.download.batch_downloader.log_user_message"),              patch("yt_fts.download.batch_downloader.log_operation"):
            downloader._initialize_batch_download()

        # Assert - Get the actual logger level
        yt_dlp_logger = logging.getLogger("yt_dlp")
        actual_level = yt_dlp_logger.level

        # This FAILS because current code sets WARNING (30)
        # Should PASS after fix sets ERROR (40)
        assert actual_level == logging.ERROR,             f"Expected yt_dlp logger level to be ERROR (40), but got {actual_level}"

    def test_yt_dlp_logger_not_set_to_warning(self, downloader):
        """
        Test that yt_dlp logger is NOT set to WARNING level.

        Given: A BatchDownloader instance
        When: _initialize_batch_download is called
        Then: yt_dlp logger should NOT be set to WARNING level
        """
        # Act
        with patch("yt_fts.download.batch_downloader.log_user_message"),              patch("yt_fts.download.batch_downloader.log_operation"):
            downloader._initialize_batch_download()

        # Assert - Verify it's not WARNING
        yt_dlp_logger = logging.getLogger("yt_dlp")
        actual_level = yt_dlp_logger.level

        # This FAILS because current code sets WARNING (30)
        # Should PASS after fix sets ERROR (40)
        assert actual_level != logging.WARNING,             f"yt_dlp logger should NOT be set to WARNING level, but got {actual_level}"


class TestTechnicalLoggerLevel:
    """Tests for technical logger level configuration."""

    @pytest.fixture
    def downloader(self):
        """Create BatchDownloader instance for testing."""
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
        )

    def test_technical_logger_set_to_critical_level(self, downloader):
        """
        Test that technical logger is set to CRITICAL level.

        Given: A BatchDownloader instance
        When: _initialize_batch_download is called
        Then: technical logger should be set to CRITICAL level
        """
        # Act
        with patch("yt_fts.download.batch_downloader.log_user_message"),              patch("yt_fts.download.batch_downloader.log_operation"):
            downloader._initialize_batch_download()

        # Assert
        technical_logger = logging.getLogger("technical")
        actual_level = technical_logger.level

        # This should PASS (technical logger is already set to CRITICAL)
        assert actual_level == logging.CRITICAL,             f"Expected technical logger level to be CRITICAL (50), but got {actual_level}"


class TestRootLoggerConfiguration:
    """Tests for root logger configuration in Rich mode."""

    @pytest.fixture
    def downloader(self):
        """Create BatchDownloader instance for testing."""
        return BatchDownloader(
            channels=["@testchannel"],
            suppress_quota_print=True,
            suppress_verbose=True,
        )

    def test_root_logger_level_appropriate_for_rich(self, downloader):
        """
        Test that root logger level is appropriate for Rich mode.

        Given: A BatchDownloader instance
        When: _initialize_batch_download is called
        Then: Root logger should be at INFO or higher level for Rich display
        """
        # Act
        with patch("yt_fts.download.batch_downloader.log_user_message"),              patch("yt_fts.download.batch_downloader.log_operation"):
            downloader._initialize_batch_download()

        # Assert - Root logger should be at INFO or higher (INFO=20, WARNING=30, ERROR=40)
        root_logger = logging.getLogger()
        actual_level = root_logger.level

        # Root logger should be INFO or higher (lower numeric value)
        # This test verifies the root logger configuration
        assert actual_level <= logging.WARNING,             f"Root logger level ({actual_level}) should be INFO or higher for Rich mode"
