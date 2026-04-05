"""Tests for vtt message fix - redundant message removed.

Issue: The "Downloading X vtt files" message was redundant because the worker
progress tracker already provides visual feedback.

Fix: Removed the redundant message from download_playlist method.

Run with: pytest tests/test_download_handler_vtt_message_fix.py -v
"""

import pytest
from unittest.mock import Mock, patch
import tempfile


class TestVttMessageFix:
    """Tests verifying the vtt message has been removed."""

    @pytest.fixture
    def handler(self):
        """Create a DownloadHandler instance for testing."""
        from yt_fts.download.download_handler import DownloadHandler
        console = Mock()
        console.stderr = True
        return DownloadHandler(
            console=console,
            rich_mode=False,
            suppress_status_messages=False,
        )

    @pytest.fixture
    def mock_playlist_data(self):
        """Mock playlist data for testing."""
        return [
            {"video_id": "abc123", "channel_name": "Test Channel", "channel_id": "UCtest123", "channel_url": "https://youtube.com/@testchannel"},
            {"video_id": "def456", "channel_name": "Test Channel", "channel_id": "UCtest123", "channel_url": "https://youtube.com/@testchannel"}
        ]

    def test_no_redundant_vtt_message_printed(self, handler, mock_playlist_data):
        """Verify the redundant 'Downloading X vtt files' message is NOT printed."""
        with patch.object(handler, "get_playlist_data", return_value=mock_playlist_data):
            with patch.object(handler, "_apply_max_videos_limit"):
                with patch.object(handler, "download_vtts"):
                    with patch.object(handler, "vtt_to_db"):
                        with patch("yt_fts.download.download_handler.check_if_channel_exists", return_value=False):
                            with patch("yt_fts.download.download_handler.add_channel_info"):
                                with tempfile.TemporaryDirectory() as tmp_dir:
                                    print_calls = []
                                    def track_print(*args, **kwargs):
                                        print_calls.append((args, kwargs))
                                        return handler._formatter.console.print(*args, **kwargs)
                                    handler._formatter.print_message = track_print
                                    
                                    handler.download_playlist(
                                        playlist_url="https://youtube.com/playlist?list=test",
                                        language="en",
                                        number_of_jobs=2
                                    )
                                    
                                    # Verify no vtt message was printed
                                    vtt_messages = [
                                        (args, kwargs) for args, kwargs in print_calls
                                        if args and "vtt" in str(args[0]).lower()
                                    ]
                                    
                                    assert len(vtt_messages) == 0,                                         f"Redundant vtt message should not be printed, found {len(vtt_messages)}"

    def test_download_playlist_flow_preserved(self, handler, mock_playlist_data):
        """Verify download_playlist flow is preserved after removing vtt message."""
        with patch.object(handler, "get_playlist_data", return_value=mock_playlist_data):
            with patch.object(handler, "_apply_max_videos_limit") as mock_limit:
                with patch.object(handler, "download_vtts") as mock_download:
                    with patch.object(handler, "vtt_to_db") as mock_vtt_to_db:
                        with patch("yt_fts.download.download_handler.check_if_channel_exists", return_value=False):
                            with patch("yt_fts.download.download_handler.add_channel_info") as mock_add_channel:
                                handler._videos_saved_during_download = False
                                
                                handler.download_playlist(
                                    playlist_url="https://youtube.com/playlist?list=test",
                                    language="en",
                                    number_of_jobs=2
                                )
                                
                                # Verify all expected methods were called
                                mock_limit.assert_called_once()
                                mock_download.assert_called_once()
                                mock_vtt_to_db.assert_called_once()
                                mock_add_channel.assert_called()
