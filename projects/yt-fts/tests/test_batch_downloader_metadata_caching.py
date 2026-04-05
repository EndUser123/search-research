"""
Tests for _fetch_channel_metadata_yt_dlp behavior.
"""

from unittest.mock import MagicMock, patch
from yt_fts.download.batch_downloader import BatchDownloader


class TestFetchChannelMetadataCaching:
    """Test that _fetch_channel_metadata_yt_dlp uses subprocess correctly."""

    def test_fetched_name_returns_from_subprocess(self):
        """Should fetch the channel name from yt-dlp subprocess."""
        # Valid 24-char channel ID: UC + 22 alphanumeric
        channel_id = "UC" + "A" * 22
        mock_result = MagicMock()
        mock_result.stdout = f"Test Channel Name\nhttps://www.youtube.com/channel/{channel_id}"
        with patch("shutil.which", return_value="yt-dlp"), \
             patch("subprocess.run", return_value=mock_result) as mock_run:
            downloader = BatchDownloader(channels=[])
            name, url = downloader._fetch_channel_metadata_yt_dlp(channel_id)
        assert name == "Test Channel Name"
        assert url == f"https://www.youtube.com/channel/{channel_id}"
        mock_run.assert_called_once()


class TestFetchChannelMetadataInputValidation:
    """Test that _fetch_channel_metadata_yt_dlp validates input."""

    def test_rejects_malformed_channel_id_too_short(self):
        """Should reject channel IDs that are too short."""
        with patch("shutil.which", return_value="yt-dlp"), \
             patch("subprocess.run") as mock_run:
            downloader = BatchDownloader(channels=[])
            name, url = downloader._fetch_channel_metadata_yt_dlp("UCshort123")
        assert name is None
        assert url is None
        mock_run.assert_not_called()

    def test_rejects_channel_id_with_special_characters(self):
        """Should reject channel IDs with special characters."""
        with patch("shutil.which", return_value="yt-dlp"), \
             patch("subprocess.run") as mock_run:
            downloader = BatchDownloader(channels=[])
            name, url = downloader._fetch_channel_metadata_yt_dlp("UC123456; rm -rf /")
        assert name is None
        assert url is None
        mock_run.assert_not_called()

    def test_rejects_non_youtube_url(self):
        """Should reject URLs not pointing to youtube.com."""
        with patch("shutil.which", return_value="yt-dlp"), \
             patch("subprocess.run") as mock_run:
            downloader = BatchDownloader(channels=[])
            name, url = downloader._fetch_channel_metadata_yt_dlp("https://evil.com/malware")
        assert name is None
        assert url is None
        mock_run.assert_not_called()
