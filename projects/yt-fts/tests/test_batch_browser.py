"""
Tests for batch_browser module.

Tests browser detection and browser suggestion functionality.
"""
from unittest.mock import patch

import pytest

from yt_fts.core.batch_browser import (
    BrowserInfo,
    detect_available_browsers,
    suggest_browser_cookies,
)


class TestBrowserInfo:
    """Test BrowserInfo dataclass."""

    def test_create_browser_info_empty(self):
        """Test creating BrowserInfo with default values."""
        info = BrowserInfo()
        assert info.firefox_available is False
        assert info.chrome_available is False
        assert info.edge_available is False
        assert info.brave_available is False
        assert info.opera_available is False
        assert info.vivaldi_available is False

    def test_create_browser_info_with_values(self):
        """Test creating BrowserInfo with specific values."""
        info = BrowserInfo(
            firefox_available=True,
            chrome_available=True,
            brave_available=True,
        )
        assert info.firefox_available is True
        assert info.chrome_available is True
        assert info.brave_available is True

    def test_get_optimal_browser_firefox_first(self):
        """Test Firefox is preferred when available."""
        info = BrowserInfo(firefox_available=True)
        assert info.get_optimal_browser() == "firefox"

    def test_get_optimal_browser_brave_second(self):
        """Test Brave is preferred when Firefox unavailable."""
        info = BrowserInfo(brave_available=True, firefox_available=False)
        assert info.get_optimal_browser() == "brave"

    def test_get_optimal_browser_chrome_third(self):
        """Test Chrome is preferred when Firefox/Brave unavailable."""
        info = BrowserInfo(
            chrome_available=True,
            firefox_available=False,
            brave_available=False,
        )
        assert info.get_optimal_browser() == "chrome"

    def test_get_optimal_browser_edge_fourth(self):
        """Test Edge is preferred when others unavailable."""
        info = BrowserInfo(
            edge_available=True,
            firefox_available=False,
            brave_available=False,
            chrome_available=False,
        )
        assert info.get_optimal_browser() == "edge"

    def test_get_optimal_browser_opera_fifth(self):
        """Test Opera is preferred when others unavailable."""
        info = BrowserInfo(
            opera_available=True,
            firefox_available=False,
            brave_available=False,
            chrome_available=False,
            edge_available=False,
        )
        assert info.get_optimal_browser() == "opera"

    def test_get_optimal_browser_vivaldi_last(self):
        """Test Vivaldi is last option."""
        info = BrowserInfo(
            vivaldi_available=True,
            firefox_available=False,
            brave_available=False,
            chrome_available=False,
            edge_available=False,
            opera_available=False,
        )
        assert info.get_optimal_browser() == "vivaldi"

    def test_get_optimal_browser_none(self):
        """Test get_optimal_browser returns None when no browsers available."""
        info = BrowserInfo()
        assert info.get_optimal_browser() is None

    def test_get_available_browsers_all(self):
        """Test get_available_browsers returns all available browsers."""
        info = BrowserInfo(
            firefox_available=True,
            chrome_available=True,
            brave_available=True,
            edge_available=False,
            opera_available=False,
            vivaldi_available=False,
        )
        browsers = info.get_available_browsers()
        assert browsers == ["firefox", "brave", "chrome"]

    def test_get_available_browsers_none(self):
        """Test get_available_browsers returns empty list when none available."""
        info = BrowserInfo()
        browsers = info.get_available_browsers()
        assert browsers == []


class TestDetectAvailableBrowsers:
    """Test detect_available_browsers function."""

    def test_detect_firefox_windows(self, monkeypatch, tmp_path):
        """Test Firefox detection on Windows."""
        # Mock Windows paths
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("yt_fts.core.batch_browser.os.path.exists") as mock_exists:
            # Firefox exists
            mock_exists.side_effect = lambda p: "Firefox" in str(p)

            monkeypatch.setenv("USERPROFILE", str(fake_home))
            monkeypatch.setenv("APPDATA", str(fake_home / "AppData" / "Roaming"))

            info = detect_available_browsers()

            assert info.firefox_available is True

    def test_detect_chrome_windows(self, monkeypatch, tmp_path):
        """Test Chrome detection on Windows."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("yt_fts.core.batch_browser.os.path.exists") as mock_exists:
            # Chrome exists
            mock_exists.side_effect = lambda p: "Chrome" in str(p)

            monkeypatch.setenv("USERPROFILE", str(fake_home))

            info = detect_available_browsers()

            assert info.chrome_available is True

    def test_detect_brave_windows(self, monkeypatch, tmp_path):
        """Test Brave detection on Windows."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("yt_fts.core.batch_browser.os.path.exists") as mock_exists:
            # Brave exists
            mock_exists.side_effect = lambda p: "Brave" in str(p)

            monkeypatch.setenv("USERPROFILE", str(fake_home))

            info = detect_available_browsers()

            assert info.brave_available is True

    def test_detect_no_browsers(self, monkeypatch, tmp_path):
        """Test detection when no browsers are installed."""
        fake_home = tmp_path / "home"
        fake_home.mkdir()

        with patch("yt_fts.core.batch_browser.os.path.exists") as mock_exists:
            # Nothing exists
            mock_exists.return_value = False

            monkeypatch.setenv("USERPROFILE", str(fake_home))

            info = detect_available_browsers()

            assert info.firefox_available is False
            assert info.chrome_available is False
            assert info.brave_available is False
            assert info.edge_available is False
            assert info.opera_available is False
            assert info.vivaldi_available is False


class TestSuggestBrowserCookies:
    """Test suggest_browser_cookies function."""

    @patch("yt_fts.core.batch_browser.detect_available_browsers")
    def test_suggest_returns_existing_setting(self, mock_detect):
        """Test suggest returns the already-set browser."""
        result = suggest_browser_cookies("chrome")
        assert result == "chrome"
        mock_detect.assert_not_called()

    @patch("yt_fts.core.batch_browser.detect_available_browsers")
    def test_suggest_detects_optimal_browser(self, mock_detect):
        """Test suggest detects optimal browser when none set."""
        mock_info = BrowserInfo(firefox_available=False, brave_available=True)
        mock_detect.return_value = mock_info

        result = suggest_browser_cookies("")

        assert result == "brave"

    @patch("yt_fts.core.batch_browser.detect_available_browsers")
    def test_suggest_falls_back_to_firefox(self, mock_detect):
        """Test suggest falls back to Firefox when no browsers detected."""
        mock_info = BrowserInfo()  # No browsers available
        mock_detect.return_value = mock_info

        result = suggest_browser_cookies("")

        assert result == "firefox"

    @patch("yt_fts.core.batch_browser.detect_available_browsers")
    def test_suggest_empty_string(self, mock_detect):
        """Test suggest treats empty string as unset."""
        mock_info = BrowserInfo(chrome_available=True)
        mock_detect.return_value = mock_info

        result = suggest_browser_cookies("")

        assert result == "chrome"
