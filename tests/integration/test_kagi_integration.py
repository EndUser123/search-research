"""Integration tests for Kagi search provider.

These tests require a valid KAGI_API_KEY environment variable.
Tests are skipped if the API key is not available.
"""

import os

import pytest

from core.providers.kagi import KagiBackend


@pytest.fixture
def real_kagi_backend():
    """Create a real KagiBackend instance for integration testing.

    Returns:
        KagiBackend: Configured backend instance, or None if API key missing.
    """
    api_key = os.getenv("KAGI_API_KEY")
    if not api_key:
        return None
    return KagiBackend(api_key=api_key)


@pytest.mark.skipif(
    not os.getenv("KAGI_API_KEY"),
    reason="KAGI_API_KEY environment variable not set"
)
class TestKagiIntegration:
    """Integration tests with real Kagi API."""

    @pytest.mark.asyncio
    async def test_real_search_query(self, real_kagi_backend):
        """Test real search query against Kagi API."""
        backend = real_kagi_backend
        assert backend is not None

        results = await backend.search("Python async programming", max_results=5)

        # Verify we got results
        assert isinstance(results, list)
        assert len(results) > 0

        # Verify result structure
        for result in results[:3]:  # Check first 3 results
            assert "title" in result
            assert "url" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            assert result["metadata"]["source"] == "kagi"

            # Verify data types
            assert isinstance(result["title"], str)
            assert isinstance(result["url"], str)
            assert isinstance(result["content"], str)
            assert isinstance(result["score"], float)
            assert 0 <= result["score"] <= 1

            # Verify URL is valid
            assert result["url"].startswith("http://") or result["url"].startswith("https://")

    @pytest.mark.asyncio
    async def test_real_search_with_max_results(self, real_kagi_backend):
        """Test real search with custom max_results parameter."""
        backend = real_kagi_backend

        results = await backend.search("machine learning", max_results=3)

        assert len(results) <= 3
        for result in results:
            assert "title" in result
            assert "url" in result

    @pytest.mark.asyncio
    async def test_real_search_timeout(self, real_kagi_backend):
        """Test that search respects timeout parameter."""
        backend = real_kagi_backend

        # This should complete quickly
        results = await backend.search("fast query", timeout=10.0)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_real_search_empty_query(self, real_kagi_backend):
        """Test real search with empty/whitespace query."""
        backend = real_kagi_backend

        # Empty query should return empty results (not raise)
        results = await backend.search("   ")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_backend_availability(self, real_kagi_backend):
        """Test backend availability check."""
        backend = real_kagi_backend

        assert backend.is_available() is True
        assert backend.validate_api_key() is True

    @pytest.mark.asyncio
    async def test_backend_properties(self, real_kagi_backend):
        """Test backend property values."""
        backend = real_kagi_backend

        assert backend.name == "kagi"
        assert backend.requires_api_key is True
        assert backend.api_key_env_var == "KAGI_API_KEY"

    @pytest.mark.asyncio
    async def test_close_backend(self, real_kagi_backend):
        """Test closing backend connection."""
        backend = real_kagi_backend

        # Should not raise
        await backend.close()


@pytest.mark.skipif(
    not os.getenv("KAGI_API_KEY"),
    reason="KAGI_API_KEY environment variable not set"
)
class TestKagiEdgeCases:
    """Integration tests for edge cases."""

    @pytest.mark.asyncio
    async def test_special_characters_in_query(self, real_kagi_backend):
        """Test search with special characters."""
        backend = real_kagi_backend

        results = await backend.search("C++ vs Python", max_results=3)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_unicode_query(self, real_kagi_backend):
        """Test search with Unicode characters."""
        backend = real_kagi_backend

        results = await backend.search("机器学习", max_results=3)
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_very_long_query(self, real_kagi_backend):
        """Test search with a very long query."""
        backend = real_kagi_backend

        long_query = "artificial intelligence " * 10
        results = await backend.search(long_query, max_results=2)
        assert isinstance(results, list)
