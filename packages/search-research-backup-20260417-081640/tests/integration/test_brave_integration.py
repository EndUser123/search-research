"""Integration tests for Brave search provider.

These tests make actual API calls to Brave Search API.
Tests are skipped if BRAVE_API_KEY environment variable is not set.
"""

import os

import pytest

from core.providers.brave import BraveBackend


@pytest.fixture
def brave_backend():
    """Create BraveBackend instance for integration testing.

    Returns None if BRAVE_API_KEY is not set (test will be skipped).
    """
    api_key = os.getenv("BRAVE_API_KEY")
    if not api_key:
        return None
    return BraveBackend(api_key=api_key)


@pytest.mark.integration
class TestBraveBackendIntegration:
    """Integration tests for BraveBackend with real API calls."""

    def test_api_key_available(self, brave_backend):
        """Test that API key is configured for integration tests."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")
        assert brave_backend is not None
        assert brave_backend.is_available()

    @pytest.mark.asyncio
    async def test_real_search_query(self, brave_backend):
        """Test real search query against Brave Search API."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        results = await brave_backend.search(
            "Python programming language",
            max_results=5,
            timeout=10.0,
        )

        # Verify we got results
        assert isinstance(results, list)
        assert len(results) > 0

        # Verify result format
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            assert result["metadata"]["source"] == "brave"

            # Verify data types
            assert isinstance(result["title"], str)
            assert isinstance(result["url"], str)
            assert isinstance(result["content"], str)
            assert isinstance(result["score"], (int, float))
            assert isinstance(result["metadata"], dict)

            # Verify URL is valid
            assert result["url"].startswith("http")

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, brave_backend):
        """Test that max_results parameter limits results."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        results = await brave_backend.search(
            "machine learning",
            max_results=3,
            timeout=10.0,
        )

        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_timeout(self, brave_backend):
        """Test that timeout parameter works correctly."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        # Should complete within timeout
        results = await brave_backend.search(
            "artificial intelligence",
            timeout=5.0,
        )

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_close_connection(self, brave_backend):
        """Test closing the connection."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        # Perform a search
        await brave_backend.search("test query")

        # Close connection
        await brave_backend.close()

        # Should be able to create new client after close
        results = await brave_backend.search("another query")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_empty_query(self, brave_backend):
        """Test search with empty or whitespace query."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        # Empty query should return empty results or handle gracefully
        results = await brave_backend.search("   ")

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_special_characters(self, brave_backend):
        """Test search with special characters in query."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        results = await brave_backend.search("C++ programming language")

        assert isinstance(results, list)
        if len(results) > 0:
            assert all("title" in r for r in results)

    @pytest.mark.asyncio
    async def test_search_unicode(self, brave_backend):
        """Test search with Unicode characters."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        results = await brave_backend.search("日本語 - Japanese language")

        assert isinstance(results, list)
        if len(results) > 0:
            assert all("title" in r for r in results)

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_api_error(self, brave_backend):
        """Test that API errors are handled gracefully."""
        if brave_backend is None:
            pytest.skip("BRAVE_API_KEY not set - skipping integration test")

        # Use invalid API key to test error handling
        invalid_backend = BraveBackend(api_key="invalid_key_12345")

        results = await invalid_backend.search("test query")

        # Should return empty list on error, not raise
        assert isinstance(results, list)
        assert results == []

        await invalid_backend.close()
