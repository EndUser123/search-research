"""Characterization tests for cookie_extractor browser cleanup (P0-001)."""
import pytest
from unittest.mock import MagicMock, patch

from yt_fts.download.cookie_extractor import BrowserCookieExtractor


class TestBrowserCleanupCharacterization:
    """Characterization tests for browser resource cleanup.
    
    These tests capture current behavior to ensure browser cleanup
    happens even when exceptions occur during extraction.
    """

    def test_firefox_cleanup_on_success(self):
        """Characterize browser cleanup when extraction succeeds."""
        # This test captures current behavior: browser should close on success
        playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        playwright.firefox.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_context.cookies.return_value = [
            {"name": "test", "value": "value", "domain": ".youtube.com",
             "path": "/", "secure": True, "httpOnly": False}
        ]
        
        extractor = BrowserCookieExtractor(console=MagicMock())
        extractor._save_cookies_to_file = MagicMock(return_value="/path/to/cookies.txt")
        
        # Execute
        result = extractor._extract_from_firefox(playwright)
        
        # Verify: browser.close() should be called on success
        assert mock_browser.close.called, "Browser should be closed on successful extraction"
        assert result == "/path/to/cookies.txt"

    def test_firefox_cleanup_on_exception(self):
        """Characterize browser cleanup when exception occurs during extraction.
        
        This is the BUG: browser.close() is NOT called if exception occurs
        before line 131, leaving zombie browser processes.
        """
        playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        playwright.firefox.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        
        # Simulate exception during page.goto
        mock_page.goto.side_effect = Exception("Network error")
        
        extractor = BrowserCookieExtractor(console=MagicMock())
        
        # Execute
        result = extractor._extract_from_firefox(playwright)
        
        # FIXED: browser.close() IS now called on exception (via finally block)
        assert mock_browser.close.called, "FIXED: Browser should be closed on exception"
        assert result is None

    def test_chrome_cleanup_on_success(self):
        """Characterize browser cleanup when extraction succeeds."""
        # Test Chrome extraction on success path
        playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()
        
        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page
        mock_context.cookies.return_value = [
            {"name": "test", "value": "value", "domain": ".youtube.com",
             "path": "/", "secure": True, "httpOnly": False}
        ]
        
        extractor = BrowserCookieExtractor(console=MagicMock())
        extractor._save_cookies_to_file = MagicMock(return_value="/path/to/cookies.txt")
        
        # Execute
        result = extractor._extract_from_chrome(playwright)
        
        # Verify: browser.close() should be called on success
        assert mock_browser.close.called, "Browser should be closed on successful extraction"
        assert result == "/path/to/cookies.txt"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

    def test_chrome_cleanup_on_exception(self):
        """Characterize browser cleanup when exception occurs during Chrome extraction."""
        playwright = MagicMock()
        mock_browser = MagicMock()
        mock_context = MagicMock()
        mock_page = MagicMock()

        playwright.chromium.launch.return_value = mock_browser
        mock_browser.new_context.return_value = mock_context
        mock_context.new_page.return_value = mock_page

        # Simulate exception during page.goto
        mock_page.goto.side_effect = Exception("Network error")

        extractor = BrowserCookieExtractor(console=MagicMock())

        # Execute
        result = extractor._extract_from_chrome(playwright)

        # FIXED: browser.close() IS now called on exception (via finally block)
        assert mock_browser.close.called, "FIXED: Browser should be closed on exception"
