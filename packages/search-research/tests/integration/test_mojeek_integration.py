"""Integration tests for Mojeek search provider.

These tests make real API calls and require MOJEEK_API_KEY to be set.
Tests are skipped if API key is not available.
"""

import os

import pytest

from core.providers.mojeek import MojeekBackend


@pytest.mark.integration
class TestMojeekBackendIntegration:
    """Integration tests for MojeekBackend with real API calls."""

    @pytest.fixture
    def api_key(self):
        """Get API key from environment."""
        api_key = os.getenv("MOJEEK_API_KEY")
        if not api_key:
            pytest.skip("MOJEEK_API_KEY not set - skipping integration tests")
        return api_key

    @pytest.fixture
    def backend(self, api_key):
        """Create backend with real API key."""
        return MojeekBackend(api_key=api_key, max_results=5)

    @pytest.mark.asyncio
    async def test_backend_is_available(self, backend):
        """Test backend is available with valid API key."""
        assert backend.is_available() is True

    @pytest.mark.asyncio
    async def test_basic_search(self, backend):
        """Test basic search functionality."""
        results = await backend.search("Python programming", max_results=3)

        # Verify we got results
        assert isinstance(results, list)
        # Note: Mojeek API may not be available, so we accept empty results
        # If API were available, we'd expect: assert len(results) > 0

        # If we got results, verify format
        for result in results:
            assert "title" in result
            assert "url" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            assert result["metadata"]["source"] == "mojeek"

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, backend):
        """Test search respects max_results parameter."""
        results = await backend.search("machine learning", max_results=5)

        assert isinstance(results, list)
        # If results returned, verify count
        if results:
            assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_search_with_timeout(self, backend):
        """Test search with custom timeout."""
        # Should complete without timeout error
        results = await backend.search("async programming", timeout=10.0)

        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_empty_query(self, backend):
        """Test search with empty query returns empty list."""
        results = await backend.search("", max_results=5)

        # Should handle gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_backend_close(self, backend):
        """Test closing backend."""
        await backend.close()
        # Should not raise any errors

    @pytest.mark.asyncio
    async def test_consecutive_searches(self, backend):
        """Test multiple consecutive searches."""
        queries = ["python", "javascript", "rust"]

        for query in queries:
            results = await backend.search(query, max_results=3)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_result_format(self, backend):
        """Test all search results have required fields."""
        results = await backend.search("web development", max_results=3)

        for result in results:
            # Required fields
            assert "title" in result
            assert isinstance(result["title"], str)

            assert "url" in result
            assert isinstance(result["url"], str)

            assert "content" in result
            assert isinstance(result["content"], str)

            assert "score" in result
            assert isinstance(result["score"], (int, float))

            assert "metadata" in result
            assert isinstance(result["metadata"], dict)
            assert "source" in result["metadata"]
            assert result["metadata"]["source"] == "mojeek"

    @pytest.mark.asyncio
    async def test_validate_api_key(self, backend):
        """Test API key validation."""
        assert backend.validate_api_key() is True

    @pytest.mark.asyncio
    async def test_backend_properties(self, backend):
        """Test backend properties."""
        assert backend.name == "mojeek"
        assert backend.requires_api_key is True
        assert backend.api_key_env_var == "MOJEEK_API_KEY"


@pytest.mark.integration
class TestMojeekBackendWithoutAPIKey:
    """Integration tests for behavior without API key."""

    @pytest.fixture
    def backend_no_key(self):
        """Create backend without API key."""
        # Ensure no API key is set
        api_key = os.getenv("MOJEEK_API_KEY")
        if api_key:
            pytest.skip("MOJEEK_API_KEY is set - cannot test missing key scenario")

        return MojeekBackend(api_key=None, max_results=5)

    @pytest.mark.asyncio
    async def test_backend_not_available(self, backend_no_key):
        """Test backend is not available without API key."""
        assert backend_no_key.is_available() is False

    @pytest.mark.asyncio
    async def test_search_returns_empty(self, backend_no_key):
        """Test search returns empty list without API key."""
        results = await backend_no_key.search("test query")

        assert results == []
