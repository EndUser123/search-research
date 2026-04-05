"""
Tests for ChannelResolutionService
"""

from unittest.mock import MagicMock, patch

from yt_fts.download.channel_resolution_service import ChannelResolutionService


class TestChannelResolutionService:
    """Test cases for ChannelResolutionService."""

    def setup_method(self):
        """Set up test fixtures."""
        self.service = ChannelResolutionService()

    def test_resolve_channel_url_exact_match(self):
        """Test resolving URL with exact database match."""
        with (
            patch("yt_fts.db.channels.get_channel_id_by_url_exact") as mock_exact,
            patch(
                "yt_fts.db.channels.get_channel_id_by_handle_substring"
            ) as mock_handle,
        ):

            mock_exact.return_value = "UC1234567890"

            channel_id, resolved_url = self.service.resolve_channel_url(
                "https://youtube.com/@testchannel"
            )

            assert channel_id == "UC1234567890"
            assert resolved_url == "https://youtube.com/@testchannel"
            mock_exact.assert_called_once_with("https://youtube.com/@testchannel")
            mock_handle.assert_not_called()

    def test_resolve_channel_url_clean_suffix(self):
        """Test resolving URL with /videos suffix removed."""
        with (
            patch("yt_fts.db.channels.get_channel_id_by_url_exact") as mock_exact,
            patch(
                "yt_fts.db.channels.get_channel_id_by_handle_substring"
            ) as mock_handle,
        ):

            # First call (with /videos) returns None, second call (clean) returns ID
            mock_exact.side_effect = [None, "UC1234567890"]

            channel_id, resolved_url = self.service.resolve_channel_url(
                "https://youtube.com/@testchannel/videos"
            )

            assert channel_id == "UC1234567890"
            assert resolved_url == "https://youtube.com/@testchannel"
            assert mock_exact.call_count == 2

    def test_resolve_channel_url_handle_fallback(self):
        """Test falling back to handle resolution."""
        with (
            patch("yt_fts.db.channels.get_channel_id_by_url_exact") as mock_exact,
            patch(
                "yt_fts.db.channels.get_channel_id_by_handle_substring"
            ) as mock_handle,
        ):

            mock_exact.return_value = None
            mock_handle.return_value = "UC1234567890"

            channel_id, resolved_url = self.service.resolve_channel_url(
                "https://youtube.com/@testchannel"
            )

            assert channel_id == "UC1234567890"
            mock_handle.assert_called_once_with("testchannel")

    def test_resolve_channel_url_ytdlp_fallback(self):
        """Test falling back to yt-dlp resolution."""
        with (
            patch("yt_fts.db.channels.get_channel_id_by_url_exact") as mock_exact,
            patch(
                "yt_fts.db.channels.get_channel_id_by_handle_substring"
            ) as mock_handle,
            patch("yt_fts.db.channels.get_channel_id_from_input") as mock_from_input,
        ):

            mock_exact.return_value = None
            mock_handle.return_value = None
            mock_from_input.return_value = "UC1234567890"

            with patch("yt_dlp.YoutubeDL") as mock_ydl:
                mock_instance = MagicMock()
                mock_instance.extract_info.return_value = {"channel_id": "UC1234567890"}
                mock_ydl.return_value.__enter__.return_value = mock_instance

                channel_id, resolved_url = self.service.resolve_channel_url(
                    "https://youtube.com/channel/UC1234567890"
                )

                assert channel_id == "UC1234567890"
                mock_ydl.assert_called_once()

    def test_get_channel_display_name_with_cached_name(self):
        """Test getting display name when cached name exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = "Test Channel"

            result = self.service.get_channel_display_name("UC123", "fallback")

            assert result == "Test Channel"
            mock_get_name.assert_called_once_with("UC123")

    def test_get_channel_display_name_with_raw_id(self):
        """Test getting display name when only raw channel ID exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = "Channel UC1234567890abcdef"

            result = self.service.get_channel_display_name(
                "UC1234567890abcdef", "@test"
            )

            assert result == "⚠️ @test"
            mock_get_name.assert_called_once_with("UC1234567890abcdef")

    def test_get_channel_display_name_fallback_patterns(self):
        """Test progressive fallback for display names."""
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            # Test @handle pattern
            result = self.service.get_channel_display_name("UC123", "@testchannel")
            assert result == "⚠️ @testchannel"

            # Test youtube.com/@handle pattern
            result = self.service.get_channel_display_name(
                "UC123", "youtube.com/@testchannel/videos"
            )
            assert result == "⚠️ @testchannel"

            # Test channel/ pattern
            result = self.service.get_channel_display_name(
                "UC123", "channel/UC1234567890"
            )
            assert result == "⚠️ UC1234567890..."

            # Test raw UC pattern
            result = self.service.get_channel_display_name(
                "UC123", "UC1234567890abcdef"
            )
            assert result == "⚠️ UC1234567890..."

    def test_ensure_channel_name_in_db_with_existing_name(self):
        """Test ensuring channel name when name already exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = "Test Channel"

            result = self.service.ensure_channel_name_in_db("UC123")

            assert result == "UC123"
            mock_get_name.assert_called_once_with("UC123")

    def test_ensure_channel_name_in_db_no_cached_name(self):
        """Test ensuring channel name when no cached name exists."""
        with patch("yt_fts.db.channels.get_channel_name_from_db") as mock_get_name:
            mock_get_name.return_value = None

            result = self.service.ensure_channel_name_in_db("UC123")

            assert result == "UC123"
            mock_get_name.assert_called_once_with("UC123")

    def test_is_raw_channel_id(self):
        """Test identifying raw channel ID names."""
        assert self.service._is_raw_channel_id("Channel UC123") is True
        # YouTube channel IDs are 24 characters
        assert self.service._is_raw_channel_id("UC1234567890abcdefghij") is True
        assert self.service._is_raw_channel_id("__INVALID_CHANNEL__") is True
        assert self.service._is_raw_channel_id("Real Channel Name") is False
        assert self.service._is_raw_channel_id("UC123") is False  # Too short
