"""Characterization tests for WebreaderMCPProvider HTTP status code handling.

These tests CAPTURE CURRENT BEHAVIOR of the _fetch_with_httpx method.
Run with: pytest tests/yt_fts/services/test_webreader_http_status_handling.py -v

TEST-009: Missing test for HTTP status code handling.
The _fetch_with_httpx method should:
- Return content on 200 status
- Return empty content on 404 (current behavior)
- Return empty content on 500 (current behavior)
- Follow redirects when follow_redirects=True

NOTE: Tests will FAIL until WebreaderMCPProvider is implemented.
This is the RED phase of TDD - tests document expected behavior.
"""

import pytest
from unittest.mock import Mock, patch


class TestWebreaderHttpStatusCodeHandling:
    """Tests for HTTP status code handling in _fetch_with_httpx method."""

    @pytest.fixture
    def mock_response(self):
        response = Mock()
        response.status_code = 200
        response.content = b"test content"
        return response

    def test_404_response_returns_empty_content(self, mock_response):
        """Characterization: 404 responses return empty content (current behavior)."""
        # Arrange
        mock_response.status_code = 404
        mock_response.content = b"Not Found"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=mock_response):
            result = provider._fetch_with_httpx("https://example.com/notfound")
            assert result == b"", f"Expected empty content on 404, got {result}"

    def test_500_error_returns_empty_content(self, mock_response):
        """Characterization: 500 errors return empty content (current behavior)."""
        # Arrange
        mock_response.status_code = 500
        mock_response.content = b"Internal Server Error"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=mock_response):
            result = provider._fetch_with_httpx("https://example.com/error")
            assert result == b"", f"Expected empty content on 500, got {result}"

    def test_503_service_unavailable_returns_empty_content(self, mock_response):
        """Characterization: 503 errors return empty content (current behavior)."""
        # Arrange
        mock_response.status_code = 503
        mock_response.content = b"Service Unavailable"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=mock_response):
            result = provider._fetch_with_httpx("https://example.com/unavailable")
            assert result == b"", f"Expected empty content on 503, got {result}"

    def test_200_returns_content(self, mock_response):
        """Characterization: 200 responses return content."""
        # Arrange
        mock_response.status_code = 200
        mock_response.content = b"Success content"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=mock_response):
            result = provider._fetch_with_httpx("https://example.com/success")
            assert result == b"Success content", f"Expected content on 200, got {result}"


class TestWebreaderRedirectHandling:
    """Tests for HTTP redirect following in _fetch_with_httpx method."""

    def test_redirect_301_followed_with_follow_redirects_true(self):
        """Characterization: 301 redirects are followed when follow_redirects=True."""
        # Arrange
        final_response = Mock()
        final_response.status_code = 200
        final_response.content = b"Redirected content"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get") as mock_get:
            mock_get.return_value = final_response
            result = provider._fetch_with_httpx("https://example.com/old", follow_redirects=True)
            assert result == b"Redirected content", f"Expected redirected content, got {result}"
            mock_get.assert_called_once()

    def test_redirect_302_followed_with_follow_redirects_true(self):
        """Characterization: 302 redirects are followed when follow_redirects=True."""
        # Arrange
        final_response = Mock()
        final_response.status_code = 200
        final_response.content = b"302 Redirected content"
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=final_response):
            result = provider._fetch_with_httpx("https://example.com/temp", follow_redirects=True)
            assert result == b"302 Redirected content", f"Expected redirected content, got {result}"


class TestWebreaderEdgeCases:
    """Tests for edge cases in _fetch_with_httpx method."""

    def test_empty_response_body(self):
        """Characterization: Empty response body is handled."""
        # Arrange
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.content = b""
        
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", return_value=mock_response):
            result = provider._fetch_with_httpx("https://example.com/empty")
            assert result == b"", f"Expected empty bytes, got {result}"

    def test_timeout_handling(self):
        """Characterization: Timeout errors are handled gracefully."""
        # Act & Assert
        from yt_fts.services.webreader_mcp import WebreaderMCPProvider
        import httpx
        
        provider = WebreaderMCPProvider()
        
        with patch("yt_fts.services.webreader_mcp.httpx.get", side_effect=httpx.TimeoutException("Request timed out")):
            result = provider._fetch_with_httpx("https://example.com/slow")
            assert result == b"", f"Expected empty content on timeout, got {result}"
