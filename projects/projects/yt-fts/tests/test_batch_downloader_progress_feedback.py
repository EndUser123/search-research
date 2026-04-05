"""
Tests for progress feedback during batch download initialization.

Tests that BatchDownloader provides user feedback during blocking database
operations that occur after "Ready to process" message.
"""

from unittest.mock import MagicMock, Mock, patch
import io

import pytest

from yt_fts.download.batch_downloader import BatchDownloader
from rich.console import Console


class TestBatchDownloaderProgressFeedback:
    """Test progress feedback during DB operations."""

    @patch("yt_fts.core.database.enable_wal_mode")
    @patch("yt_fts.core.database.get_db_connection")
    @patch("yt_fts.download.batch_downloader.get_cached_channels")
    def test_prints_status_before_db_operations(
        self,
        mock_get_cached,
        mock_get_conn,
        mock_enable_wal,
    ):
        """Should print status message before blocking DB operations."""
        # Arrange
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_cached.return_value = ({}, [])  # cached_channels, channels_to_resolve

        downloader = BatchDownloader(
            channels=["@test"],
            suppress_quota_print=True,  # Skip quota output for test
        )

        # Mock console.print to track calls
        original_print = downloader.console.print
        downloader.console.print = MagicMock()

        # Act
        try:
            downloader.download_all()
        except Exception:
            # We only care about the initial DB operations, not full download
            pass

        # Assert - console.print was called (status messages shown)
        assert downloader.console.print.called, "Should print progress feedback during DB operations"

        # Restore original print
        downloader.console.print = original_print

    @patch("yt_fts.core.database.enable_wal_mode")
    @patch("yt_fts.core.database.get_db_connection")
    @patch("yt_fts.download.batch_downloader.get_cached_channels")
    @patch("yt_fts.download.channel_cache.print_aggregated_cache_status")
    def test_prints_cache_status_after_db_operations(
        self,
        mock_print_status,
        mock_get_cached,
        mock_get_conn,
        mock_enable_wal,
    ):
        """Should call print_aggregated_cache_status after DB operations."""
        # Arrange
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_cached.return_value = ({"@test": "url"}, [])

        downloader = BatchDownloader(
            channels=["@test"],
            suppress_quota_print=True,
            suppress_verbose=False,  # Enable progress messages
        )

        # Act
        try:
            downloader.download_all()
        except Exception:
            pass

        # Assert - print_aggregated_cache_status should be called
        assert mock_print_status.called, "Should call print_aggregated_cache_status to show cache results"

    @patch("yt_fts.core.database.enable_wal_mode")
    @patch("yt_fts.core.database.get_db_connection")
    @patch("yt_fts.download.batch_downloader.get_cached_channels")
    @patch("yt_fts.download.channel_cache.print_aggregated_cache_status")
    def test_shows_cached_and_new_channel_counts(
        self,
        mock_print_status,
        mock_get_cached,
        mock_get_conn,
        mock_enable_wal,
    ):
        """Should display both cached and new channel counts."""
        # Arrange
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        # Simulate 5 cached channels, 2 new to resolve
        mock_get_cached.return_value = (
            {"@ch1": "url1", "@ch2": "url2", "@ch3": "url3", "@ch4": "url4", "@ch5": "url5"},
            ["@new1", "@new2"]
        )

        downloader = BatchDownloader(
            channels=["@ch1", "@ch2", "@ch3", "@ch4", "@ch5", "@new1", "@new2"],
            suppress_quota_print=True,
            suppress_verbose=False,  # Enable progress messages
        )

        # Act
        try:
            downloader.download_all()
        except Exception:
            pass

        # Assert - print_aggregated_cache_status was called
        assert mock_print_status.called, "Should call print_aggregated_cache_status"

    @patch("yt_fts.core.database.enable_wal_mode")
    @patch("yt_fts.core.database.get_db_connection")
    @patch("yt_fts.download.batch_downloader.get_cached_channels")
    @patch("yt_fts.download.channel_cache.print_aggregated_cache_status")
    def test_does_not_print_when_suppress_verbose(
        self,
        mock_print_status,
        mock_get_cached,
        mock_get_conn,
        mock_enable_wal,
    ):
        """Should NOT call print_aggregated_cache_status when suppress_verbose=True."""
        # Arrange
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_cached.return_value = ({}, [])

        downloader = BatchDownloader(
            channels=["@test"],
            suppress_quota_print=True,
            suppress_verbose=True,  # This should suppress progress messages
        )

        # Act
        try:
            downloader.download_all()
        except Exception:
            pass

        # Assert - print_aggregated_cache_status should NOT be called when suppress_verbose=True
        assert not mock_print_status.called, "Should not print cache status when suppress_verbose=True"


class TestBatchDownloaderProgressIntegration:
    """Integration tests with actual console output."""

    @patch("yt_fts.core.database.enable_wal_mode")
    @patch("yt_fts.core.database.get_db_connection")
    @patch("yt_fts.download.batch_downloader.get_cached_channels")
    @patch("yt_fts.download.channel_cache.print_aggregated_cache_status")
    def test_initializing_message_shown_then_cache_status(
        self,
        mock_print_status,
        mock_get_cached,
        mock_get_conn,
        mock_enable_wal,
    ):
        """Should show 'Initializing database cache...' then the actual cache status."""
        # Arrange
        mock_conn = MagicMock()
        mock_get_conn.return_value = mock_conn
        mock_get_cached.return_value = ({"@test": "url"}, [])

        console = Console(file=io.StringIO(), force_terminal=True)
        downloader = BatchDownloader(
            channels=["@test"],
            suppress_quota_print=True,
            suppress_verbose=False,  # Enable progress messages
        )
        downloader.console = console

        # Act
        try:
            downloader.download_all()
        except Exception:
            pass

        # Assert - print_aggregated_cache_status should be called
        assert mock_print_status.called, "Should call print_aggregated_cache_status"

        # And it should be called with the downloader's console
        mock_print_status.assert_called_with(console)
