"""
Unit tests for ChannelResolutionService.
"""

from unittest.mock import patch

import pytest

from yt_fts.download.channel_resolution_service import ChannelResolutionService


@pytest.fixture
def resolution_service():
    return ChannelResolutionService(cookies_from_browser=None)


class TestChannelResolutionServiceInitialization:
    def test_initialization_with_none_cookies(self, resolution_service):
        service = ChannelResolutionService(cookies_from_browser=None)
        assert service.cookies_from_browser is None


class TestResolveChannelUrl:
    def test_exact_url_match_in_database(self, resolution_service):
        url = "https://www.youtube.com/@testchannel"
        expected = "UCXKeNggiHUHpdkIfUj7KEEg"
        with patch("yt_fts.db.channels.get_channel_id_by_url_exact", return_value=expected):
            channel_id, _resolved_url = resolution_service.resolve_channel_url(url)
            assert channel_id == expected


class TestGetChannelDisplayName:
    def test_none_channel_id_returns_fallback_name(self, resolution_service):
        result = resolution_service.get_channel_display_name(None, "Fallback")
        assert result == "Fallback"


class TestEnsureChannelNameInDb:
    def test_none_input_returns_none(self, resolution_service):
        result = resolution_service.ensure_channel_name_in_db(None)
        assert result is None


class TestIsRawChannelId:
    def test_channel_uc_prefix_returns_true(self, resolution_service):
        assert resolution_service._is_raw_channel_id("Channel UC123456789012345678901") is True
    def test_uc_shorter_than_20_returns_false(self, resolution_service):
        assert resolution_service._is_raw_channel_id("UC1234567890") is False
    def test_invalid_channel_marker_returns_true(self, resolution_service):
        assert resolution_service._is_raw_channel_id("__INVALID_CHANNEL__") is True
    def test_human_readable_name_returns_false(self, resolution_service):
        assert resolution_service._is_raw_channel_id("3Blue1Brown") is False


class TestGetProgressiveDisplayName:
    def test_handle_input_returns_formatted(self, resolution_service):
        result = resolution_service._get_progressive_display_name("UC123", "@test")
        assert "@" in result
    def test_channel_uc_input_truncated(self, resolution_service):
        result = resolution_service._get_progressive_display_name("UC123", "channel/UC12345678")
        assert "..." in result


class TestEdgeCases:
    def test_empty_string_url(self, resolution_service):
        with patch("yt_fts.db.channels.get_channel_id_by_url_exact", return_value=None):
            with patch("yt_fts.db.channels.get_channel_id_by_handle_substring", return_value=None):
                with patch.object(resolution_service, "_resolve_via_ytdlp", return_value=None):
                    channel_id, _ = resolution_service.resolve_channel_url("")
                    assert channel_id is None
