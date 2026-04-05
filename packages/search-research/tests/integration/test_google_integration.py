"""Integration tests for Google search provider.

These tests require a valid GOOGLE_API_KEY environment variable.
Tests are skipped if the API key is not configured.
"""

import os

import pytest

from core.providers.google import GoogleBackend


@pytest.fixture
def google_backend_integration():
    """Create GoogleBackend with real API key for integration testing."""
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        pytest.skip("GOOGLE_API_KEY environment variable not set")
    return GoogleBackend(api_key=api_key)


class TestGoogleBackendIntegration:
    """Integration tests for GoogleBackend with real API calls."""

    @pytest.mark.asyncio
    async def test_real_search_basic(self, google_backend_integration):
        """Test real search with basic query."""
        results = await google_backend_integration.search(
            "Python programming",
            max_results=5,
            timeout=10.0
        )

        # Should return results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check first result structure
        result = results[0]
        assert "title" in result
        assert "url" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result

        # Validate data types
        assert isinstance(result["title"], str)
        assert isinstance(result["url"], str)
        assert isinstance(result["content"], str)
        assert isinstance(result["score"], (int, float))
        assert isinstance(result["metadata"], dict)

        # Validate metadata
        assert result["metadata"]["source"] == "google"

    @pytest.mark.asyncio
    async def test_real_search_empty_query(self, google_backend_integration):
        """Test search with empty query."""
        results = await google_backend_integration.search("")

        # Should handle gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_real_search_max_results(self, google_backend_integration):
        """Test search with custom max_results."""
        results = await google_backend_integration.search(
            "FastAPI framework",
            max_results=3,
            timeout=10.0
        )

        # Should return at most max_results
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_real_search_with_special_characters(self, google_backend_integration):
        """Test search with special characters."""
        results = await google_backend_integration.search(
            "machine learning & AI",
            max_results=5,
            timeout=10.0
        )

        # Should handle special characters
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_backend_availability(self, google_backend_integration):
        """Test backend availability check."""
        assert google_backend_integration.is_available() is True
        assert google_backend_integration.validate_api_key() is True

    @pytest.mark.asyncio
    async def test_close_connection(self, google_backend_integration):
        """Test closing connection."""
        # Should not raise
        await google_backend_integration.close()

    @pytest.mark.asyncio
    async def test_real_search_timeout_handling(self, google_backend_integration):
        """Test search with very short timeout."""
        results = await google_backend_integration.search(
            "test query",
            timeout=0.001  # Extremely short timeout
        )

        # Should handle timeout gracefully (may return empty or partial results)
        assert isinstance(results, list)
