"""Tests for state-based discovery integration in batch_downloader.

This module tests the integration of the state-based discovery system
with the existing BatchDownloader class.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

from yt_fts.discovery.state_detection import (
    ChannelState,
    DiscoveryMethod,
)


class TestStateBasedDiscoveryIntegration:
    """Test state-based discovery integration with BatchDownloader."""

    @pytest.fixture
    def mock_batch_downloader(self):
        """Create a mock BatchDownloader for testing."""
        with patch("yt_fts.download.batch_downloader.BatchDownloader.__init__", return_value=None):
            from yt_fts.download.batch_downloader import BatchDownloader
            downloader = BatchDownloader.__new__(BatchDownloader)
            downloader.console = Mock()
            downloader.display_plugin = Mock()
            return downloader

    def test_detect_state_for_channel(self, mock_batch_downloader):
        """Test that state detection works for real channel data."""
        from yt_fts.discovery.state_detection import detect_channel_state

        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count, \
             patch("yt_fts.discovery.state_detection.get_channel_api_total") as mock_api_total, \
             patch("yt_fts.discovery.state_detection.get_api_total_last_checked") as mock_last_checked:

            # Test TRANSITION state
            mock_count.return_value = 0
            mock_api_total.return_value = None
            state = detect_channel_state("UCxxxxx")
            assert state == ChannelState.TRANSITION

    def test_discovery_method_selection(self, mock_batch_downloader):
        """Test that discovery method selection works correctly."""
        from yt_fts.discovery.state_detection import (
            transition_strategy,
            steady_state_strategy,
            recovery_strategy,
        )

        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:
            mock_count.return_value = 600

            method = transition_strategy("UCxxxxx", quota_pct=50)
            assert method == DiscoveryMethod.API

    def test_steady_state_uses_rss(self, mock_batch_downloader):
        """Test that STEADY_STATE always uses RSS."""
        from yt_fts.discovery.state_detection import steady_state_strategy

        method = steady_state_strategy("UCxxxxx")
        assert method == DiscoveryMethod.RSS


class TestStateBasedDiscoveryLogic:
    """Test the decision logic for state-based discovery."""

    def test_transition_state_logic(self):
        """TRANSITION: Empty DB should use API or yt-dlp."""
        # db_count < 10 = TRANSITION
        # db_count > 500 + quota > 20% = API
        # Otherwise = yt-dlp

        from yt_fts.discovery.state_detection import transition_strategy

        with patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:
            # Large channel, good quota -> API
            mock_count.return_value = 600
            assert transition_strategy("UCxxxxx", quota_pct=50) == DiscoveryMethod.API

            # Large channel, low quota -> yt-dlp
            assert transition_strategy("UCxxxxx", quota_pct=10) == DiscoveryMethod.YTDLP

            # Small channel -> yt-dlp
            mock_count.return_value = 50
            assert transition_strategy("UCxxxxx", quota_pct=50) == DiscoveryMethod.YTDLP

    def test_recovery_state_logic(self):
        """RECOVERY: Gap detected should use API or yt-dlp based on gap size."""
        from yt_fts.discovery.state_detection import recovery_strategy

        with patch("yt_fts.discovery.state_detection.get_channel_api_total") as mock_api_total, \
             patch("yt_fts.discovery.state_detection.get_db_video_count") as mock_count:

            # Large gap (>50) + good quota -> API
            mock_api_total.return_value = 500
            mock_count.return_value = 400  # Gap of 100
            assert recovery_strategy("UCxxxxx", quota_pct=50) == DiscoveryMethod.API

            # Small gap (<50) -> yt-dlp
            mock_count.return_value = 480  # Gap of 20
            assert recovery_strategy("UCxxxxx", quota_pct=50) == DiscoveryMethod.YTDLP

