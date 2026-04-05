"""
Tests for cookie authentication validation.

Functional tests that verify cookies work with YouTube authentication.
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from dataclasses import dataclass

from yt_fts.download.cookie_auth_tester import (
    test_cookie_authentication,
    CookieTestResult,
    CookieTestStatus,
)


class TestCookieTestResult:
    """Test CookieTestResult dataclass."""

    def test_create_success_result(self) -> None:
        """Test creating a successful test result."""
        result = CookieTestResult(
            status=CookieTestStatus.VALID,
            message="Cookies are working",
            video_id="test123",
            availability="public",
        )
        assert result.status == CookieTestStatus.VALID
        assert result.video_id == "test123"

    def test_is_valid_true(self) -> None:
        """Test is_valid returns True for VALID status."""
        result = CookieTestResult(
            status=CookieTestStatus.VALID,
            message="Valid",
            video_id="test",
        )
        assert result.is_valid() is True

    def test_is_valid_false(self) -> None:
        """Test is_valid returns False for non-VALID statuses."""
        for status in [
            CookieTestStatus.INVALID,
            CookieTestStatus.ERROR,
            CookieTestStatus.NO_TEST_VIDEO,
        ]:
            result = CookieTestResult(
                status=status,
                message="Test",
                video_id="test",
            )
            assert result.is_valid() is False


class TestTestCookieAuthentication:
    """Test cookie authentication function."""

    @pytest.fixture
    def mock_ydl(self) -> Mock:
        """Create mock YoutubeDL instance."""
        with patch("yt_fts.download.cookie_auth_tester.yt_dlp") as mock:
            yield mock

    def test_valid_cookies_members_only_becomes_accessible(
        self, mock_ydl: Mock
    ) -> None:
        """Test that valid cookies make members-only videos accessible."""
        # Mock yt-dlp to return public availability (cookies worked)
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "id": "test123",
            "availability": "public",  # Cookies worked - video is accessible
            "title": "Test Video",
        }
        mock_ydl.YoutubeDL.return_value.__enter__.return_value = mock_instance

        result = test_cookie_authentication(
            video_id="test123",
            cookies_from_browser="firefox",
        )

        assert result.status == CookieTestStatus.VALID
        assert "working" in result.message.lower()
        assert result.availability == "public"

    def test_invalid_cookies_still_members_only(self, mock_ydl: Mock) -> None:
        """Test that invalid cookies leave videos as members-only."""
        # Mock yt-dlp to return members_only availability (cookies didn't work)
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "id": "test123",
            "availability": "members_only",
            "title": "Members Only",
        }
        mock_ydl.YoutubeDL.return_value.__enter__.return_value = mock_instance

        result = test_cookie_authentication(
            video_id="test123",
            cookies_from_browser="firefox",
        )

        assert result.status == CookieTestStatus.INVALID
        assert "expired" in result.message.lower() or "invalid" in result.message.lower()
        assert result.availability == "members_only"

    def test_no_cookies_no_test(self) -> None:
        """Test that no cookies returns NO_TEST_VIDEO status."""
        result = test_cookie_authentication(
            video_id="test123",
            cookies_from_browser=None,
        )

        assert result.status == CookieTestStatus.NO_TEST_VIDEO
        assert "no cookies" in result.message.lower()

    def test_ytdlp_error(self, mock_ydl: Mock) -> None:
        """Test that yt-dlp errors return ERROR status."""
        mock_instance = MagicMock()
        mock_instance.extract_info.side_effect = Exception("Network error")
        mock_ydl.YoutubeDL.return_value.__enter__.return_value = mock_instance

        result = test_cookie_authentication(
            video_id="test123",
            cookies_from_browser="firefox",
        )

        assert result.status == CookieTestStatus.ERROR
        assert "error" in result.message.lower()

    def test_ydl_opts_contains_cookies(self, mock_ydl: Mock) -> None:
        """Test that cookies are passed to yt-dlp options."""
        mock_instance = MagicMock()
        mock_instance.extract_info.return_value = {
            "id": "test123",
            "availability": "public",
        }
        mock_ydl.YoutubeDL.return_value.__enter__.return_value = mock_instance

        test_cookie_authentication(
            video_id="test123",
            cookies_from_browser="chrome",
        )

        # Verify YoutubeDL was called with cookiesfrombrowser
        call_args = mock_ydl.YoutubeDL.call_args
        ydl_opts = call_args[0][0] if call_args[0] else call_args[1].get("ydl_opts", {})
        assert "cookiesfrombrowser" in ydl_opts
        assert ydl_opts["cookiesfrombrowser"] == ("chrome",)
