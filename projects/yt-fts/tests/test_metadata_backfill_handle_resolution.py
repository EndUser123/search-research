"""
Test for handle to UC channel_id resolution in metadata backfill.

This tests the fix for the issue where handles like @1veritasium
are passed to YouTube API which requires UC channel_id format.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill


class TestHandleResolution:
    """Test handle resolution in metadata backfill API."""

    def test_get_upload_playlist_id_rejects_handle(self):
        """Test that _get_upload_playlist_id rejects handles starting with @."""
        # Provide mock API key to avoid ValueError
        backfill = YouTubeAPIBackfill(api_keys=["test-key"])
        
        # Handle should be rejected
        result = backfill._get_upload_playlist_id("@1veritasium")
        assert result is None, "Handles starting with @ should be rejected"

    def test_get_upload_playlist_id_rejects_non_uc_format(self):
        """Test that _get_upload_playlist_id rejects non-UC formats."""
        backfill = YouTubeAPIBackfill(api_keys=["test-key"])
        
        # Non-UC format should be rejected
        result = backfill._get_upload_playlist_id("not_a_uc_id")
        assert result is None, "Non-UC channel IDs should be rejected"

    def test_get_upload_playlist_id_accepts_uc_format(self):
        """Test that _get_upload_playlist_id accepts UC format."""
        backfill = YouTubeAPIBackfill(api_keys=["test-key"])
        
        # Mock the API response
        with patch('yt_fts.services.metadata_backfill_api.requests.get') as mock_get:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "items": [{
                    "contentDetails": {
                        "relatedPlaylists": {
                            "uploads": "UUtest123"
                        }
                    }
                }]
            }
            mock_get.return_value = mock_response
            
            result = backfill._get_upload_playlist_id("UC123456789012345678901")
            # Should return the upload playlist ID
            assert result is not None, "UC format channel IDs should be accepted"


class TestHandleResolutionTimeoutAndValidation:
    """Test suite for timeout and UC validation in handle resolution."""

    @pytest.fixture
    def mock_batch_downloader(self):
        """Create a BatchDownloader fixture for testing."""
        # Mock the BatchDownloader with necessary attributes
        downloader = Mock()
        downloader.cookie_file = None  # No cookies for testing
        downloader.suppress_quota_print = True
        downloader.console = None
        downloader.batch_manager = MagicMock()
        
        # Import the actual method
        from yt_fts.download.batch_downloader import BatchDownloader
        downloader._backfill_new_channel_metadata = BatchDownloader._backfill_new_channel_metadata.__get__(downloader, BatchDownloader)
        
        return downloader

    def test_socket_timeout_required_in_ydl_opts(self, mock_batch_downloader):
        """yt-dlp options must include socket_timeout to prevent hangs."""
        import yt_dlp
        from unittest.mock import patch, Mock
        
        # Mock yt-dlp to capture the ydl_opts
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = Mock()
            mock_ydl_cls.return_value.__enter__ = Mock(return_value=mock_ydl)
            mock_ydl.extract_info = Mock(return_value={"channel_id": "UC123456"})
            
            # Call with a handle
            mock_batch_downloader._backfill_new_channel_metadata(
                channel_id="@testhandle",
                channel_display_name="Test",
                db_state={}
            )
            
            # Verify yt-dlp was called
            assert mock_ydl.extract_info.called, "yt-dlp should be called"
            
            # Get the ydl_opts that were passed to YoutubeDL constructor
            # YoutubeDL(ydl_opts) means ydl_opts is the first positional arg (index 0)
            call_args = mock_ydl_cls.call_args
            assert call_args is not None, "YoutubeDL should have been called"
            # call_args[0] is positional args tuple, call_args[0][0] is the ydl_opts dict
            ydl_opts = call_args[0][0] if call_args[0] else {}
            
            assert "socket_timeout" in ydl_opts, "socket_timeout must be set to prevent hangs"
            assert ydl_opts["socket_timeout"] == 10, "socket_timeout should be 10 seconds"

    def test_uc_format_validated_after_resolution(self, mock_batch_downloader):
        """Resolved channel_id must start with 'UC' before being used."""
        from unittest.mock import patch, Mock
        
        # Mock yt-dlp to return invalid format
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = Mock()
            mock_ydl_cls.return_value.__enter__ = Mock(return_value=mock_ydl)
            # Simulate yt-dlp returning invalid format
            mock_ydl.extract_info = Mock(return_value={"channel_id": "INVALID_FORMAT"})
            
            # Call with a handle - should return skip_reason
            api_mismatch, should_skip, skip_reason = mock_batch_downloader._backfill_new_channel_metadata(
                channel_id="@testhandle",
                channel_display_name="Test",
                db_state={}
            )
            
            # This will FAIL because we don't validate UC format currently
            assert skip_reason in ("unresolvable_handle", "resolution_failed"),                 "Should return skip_reason when resolved_id is not UC format"

    def test_none_channel_id_handled_gracefully(self, mock_batch_downloader):
        """When yt-dlp returns None, should handle gracefully."""
        from unittest.mock import patch, Mock
        
        with patch("yt_dlp.YoutubeDL") as mock_ydl_cls:
            mock_ydl = Mock()
            mock_ydl_cls.return_value.__enter__ = Mock(return_value=mock_ydl)
            # Simulate yt-dlp returning None for channel_id
            mock_ydl.extract_info = Mock(return_value={"uploader_id": None})
            
            api_mismatch, should_skip, skip_reason = mock_batch_downloader._backfill_new_channel_metadata(
                channel_id="@testhandle",
                channel_display_name="Test",
                db_state={}
            )
            
            # Should return skip_reason for unresolvable
            assert skip_reason in ("unresolvable_handle", "resolution_failed"),                 "Should return skip_reason when resolution returns None"
