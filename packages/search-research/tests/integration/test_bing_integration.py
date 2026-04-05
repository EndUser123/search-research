"""Integration tests for Bing search provider.

These tests require actual API credentials (BING_API_KEY environment variable).
Tests are skipped if credentials are not available.

Run with: pytest tests/integration/test_bing_integration.py -v
"""

import os

import pytest

from core.providers.bing import BingBackend


@pytest.mark.integration
class TestBingBackendIntegration:
    """Integration tests for BingBackend with real API calls."""

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Skip all tests if BING_API_KEY is not set."""
        if not os.getenv("BING_API_KEY"):
            pytest.skip("BING_API_KEY environment variable not set")

    @pytest.fixture
    def backend(self):
        """Create BingBackend instance for testing."""
        return BingBackend()

    @pytest.mark.asyncio
    async def test_basic_search(self, backend):
        """Test basic search functionality."""
        results = await backend.search("Python programming", max_results=5)

        # Should return results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check result structure
        result = results[0]
        assert "title" in result
        assert "url" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result
        assert result["metadata"]["source"] == "bing"

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, backend):
        """Test search with max_results parameter."""
        results = await backend.search("machine learning", max_results=3)

        assert isinstance(results, list)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_empty_query(self, backend):
        """Test search with empty query."""
        results = await backend.search("", max_results=5)

        # Should return empty list gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_timeout_handling(self, backend):
        """Test search with very short timeout."""
        # Use very short timeout to test timeout handling
        results = await backend.search("test query", timeout=0.001)

        # Should handle timeout gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_backend_availability(self, backend):
        """Test backend availability check."""
        assert backend.is_available()

    @pytest.mark.asyncio
    async def test_backend_close(self, backend):
        """Test closing backend."""
        # Perform a search to initialize client
        await backend.search("test")

        # Close should not raise
        await backend.close()

    @pytest.mark.asyncio
    async def test_consecutive_searches(self, backend):
        """Test multiple consecutive searches."""
        query1_results = await backend.search("Python", max_results=3)
        query2_results = await backend.search("JavaScript", max_results=3)

        assert isinstance(query1_results, list)
        assert isinstance(query2_results, list)

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self, backend):
        """Test search with special characters in query."""
        results = await backend.search("C++ programming", max_results=5)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_graceful_degradation_on_error(self, backend):
        """Test that backend degrades gracefully on API errors."""
        # Use invalid query that might cause errors
        # The backend should handle this gracefully
        results = await backend.search("a" * 10000, max_results=5)

        # Should return results or empty list, never crash
        assert isinstance(results, list)


@pytest.mark.integration
class TestBingBackendErrorHandling:
    """Test error handling in real API scenarios."""

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Skip all tests if BING_API_KEY is not set."""
        if not os.getenv("BING_API_KEY"):
            pytest.skip("BING_API_KEY environment variable not set")

    @pytest.mark.asyncio
    async def test_backend_without_api_key(self):
        """Test backend behavior when API key is missing."""
        # Temporarily unset API key
        original_key = os.getenv("BING_API_KEY")
        try:
            os.environ.pop("BING_API_KEY", None)
            backend = BingBackend()

            # Should not be available
            assert not backend.is_available()

            # Search should return empty list
            results = await backend.search("test query")
            assert results == []
        finally:
            # Restore original key
            if original_key:
                os.environ["BING_API_KEY"] = original_key


@pytest.mark.integration
class TestBingBackendResultsQuality:
    """Test quality of search results from real API."""

    @pytest.fixture(autouse=True)
    def skip_if_no_api_key(self):
        """Skip all tests if BING_API_KEY is not set."""
        if not os.getenv("BING_API_KEY"):
            pytest.skip("BING_API_KEY environment variable not set")

    @pytest.fixture
    def backend(self):
        """Create BingBackend instance for testing."""
        return BingBackend()

    @pytest.mark.asyncio
    async def test_results_have_required_fields(self, backend):
        """Test that all results have required fields."""
        results = await backend.search("artificial intelligence", max_results=5)

        for result in results:
            assert "title" in result
            assert isinstance(result["title"], str)
            assert len(result["title"]) > 0

            assert "url" in result
            assert isinstance(result["url"], str)
            assert len(result["url"]) > 0
            assert result["url"].startswith(("http://", "https://"))

            assert "content" in result
            assert isinstance(result["content"], str)

            assert "score" in result
            assert isinstance(result["score"], (int, float))

            assert "metadata" in result
            assert isinstance(result["metadata"], dict)
            assert result["metadata"]["source"] == "bing"

    @pytest.mark.asyncio
    async def test_results_relevance(self, backend):
        """Test that results are relevant to query."""
        query = "machine learning tutorials"
        results = await backend.search(query, max_results=5)

        # Results should be present
        assert len(results) > 0

        # At least some results should contain query terms in title or content
        # (This is a basic relevance check)
        relevant_count = 0
        for result in results:
            title_lower = result["title"].lower()
            content_lower = result["content"].lower()
            if "machine" in title_lower or "learning" in title_lower or \
               "machine" in content_lower or "learning" in content_lower:
                relevant_count += 1

        # At least 60% of results should be relevant
        assert relevant_count >= len(results) * 0.6

    @pytest.mark.asyncio
    async def test_unique_urls(self, backend):
        """Test that results have unique URLs."""
        results = await backend.search("Python programming", max_results=10)

        urls = [result["url"] for result in results]
        unique_urls = set(urls)

        # All URLs should be unique
        assert len(urls) == len(unique_urls)
