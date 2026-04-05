'''
Test for YouTube API progress display format.

The progress display should show "yt-api:" instead of "→" to clearly indicate
which API is being used for fetching channel objects.
'''

from unittest.mock import patch, MagicMock
import sys
import pytest

class TestYouTubeAPIProgressDisplay:
    """Test that YouTube API progress display shows "yt-api:" prefix."""

    @patch('yt_fts.services.metadata_backfill_api._flush_quota_to_db')
    def test_progress_shows_yt_api_prefix_not_arrow(self, mock_flush, capsys):
        """Progress display should use "yt-api:" instead of "→"""
        from yt_fts.services.metadata_backfill_api import YouTubeAPIBackfill

        # Mock console
        mock_console = MagicMock()
        mock_console.supports_hyperlinks = False

        # Create API backfill instance with progress enabled and fake API key
        api = YouTubeAPIBackfill(
            api_keys=['fake_key_for_testing'],
            console=mock_console,
            show_progress=True
        )

        # Mock the HTTP requests to return fake data
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = [
            # First call: get playlist items (with pagination)
            {
                'items': [
                    {'contentDetails': {'videoId': 'vid1'}},
                    {'contentDetails': {'videoId': 'vid2'}},
                ],
                'nextPageToken': 'next_token',
            },
            # Second call: get playlist items (last page)
            {
                'items': [
                    {'contentDetails': {'videoId': 'vid3'}},
                ],
                # No nextPageToken - end of pagination
            },
        ]

        mock_video_response = MagicMock()
        mock_video_response.status_code = 200
        mock_video_response.json.return_value = {
            'items': [
                {'id': 'vid1', 'contentDetails': {'duration': 'PT10M'}},
                {'id': 'vid2', 'contentDetails': {'duration': 'PT10M'}},
                {'id': 'vid3', 'contentDetails': {'duration': 'PT10M'}},
            ]
        }

        with patch('requests.get', side_effect=[mock_response, mock_response, mock_video_response]):
            videos = api.fetch_all_videos_from_channel('UC_test_channel_id')

        # Verify console.print was called with "yt-api:" prefix
        # The output now goes to console.print instead of stderr
        print_calls = [str(call) for call in mock_console.print.call_args_list]
        combined_output = ' '.join(print_calls)
        
        assert 'yt-api:' in combined_output, f'Expected "yt-api:" in console.print calls, got: ' + repr(print_calls)
        
        # The arrow should NOT be in the output
        assert '→' not in combined_output, 'Arrow "→" should not be in output (use "yt-api:" instead). Got: ' + repr(combined_output)

        # Verify we got some videos
        assert len(videos) > 0
