"""Integration tests for You.com search provider.

These tests make actual API calls to You.com and require a valid API key.
Tests are skipped if YOU_API_KEY environment variable is not set.

Run integration tests:
    pytest tests/integration/test_you_integration.py -v
"""

import os

import pytest


class TestYouBackendIntegration:
    """Integration tests for YouBackend with real API calls."""

    @pytest.fixture(autouse=True)
    def skip_without_api_key(self):
        """Skip all tests if YOU_API_KEY is not set."""
        if not os.getenv("YOU_API_KEY"):
            pytest.skip(
                "YOU_API_KEY environment variable not set. "
                "Skipping You.com integration tests."
            )

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_returns_results(self):
        """Test that search returns actual results from You.com API."""
        from providers import YouBackend

        backend = YouBackend()

        results = await backend.search("Python programming", max_results=5)

        # Should return some results
        assert isinstance(results, list)
        assert len(results) > 0

        # Check result structure
        result = results[0]
        assert "title" in result
        assert "url" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result
        assert result["metadata"]["source"] == "you"

        # Cleanup
        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_with_max_results(self):
        """Test that max_results parameter is respected."""
        from providers import YouBackend

        backend = YouBackend()

        results = await backend.search("machine learning", max_results=3)

        assert len(results) <= 3

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_with_timeout(self):
        """Test that timeout parameter works correctly."""
        from providers import YouBackend

        backend = YouBackend()

        # Should complete successfully with timeout
        results = await backend.search("artificial intelligence", timeout=10.0)

        assert isinstance(results, list)

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_empty_query(self):
        """Test that empty query is handled gracefully."""
        from providers import YouBackend

        backend = YouBackend()

        results = await backend.search("", max_results=5)

        # Should return empty list for empty query
        assert results == []

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_whitespace_query(self):
        """Test that whitespace-only query is handled gracefully."""
        from providers import YouBackend

        backend = YouBackend()

        results = await backend.search("   ", max_results=5)

        # Should return empty list for whitespace query
        assert results == []

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_multiple_sequential_searches(self):
        """Test multiple sequential searches with the same backend instance."""
        from providers import YouBackend

        backend = YouBackend()

        # First search
        results1 = await backend.search("Python", max_results=3)
        assert isinstance(results1, list)

        # Second search
        results2 = await backend.search("JavaScript", max_results=3)
        assert isinstance(results2, list)

        # Third search
        results3 = await backend.search("TypeScript", max_results=3)
        assert isinstance(results3, list)

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_backend_availability(self):
        """Test that backend reports as available when API key is set."""
        from providers import YouBackend

        backend = YouBackend()

        # Should be available (we have API key)
        assert backend.is_available() is True

        await backend.close()

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_search_result_fields_are_valid(self):
        """Test that all result fields contain valid data."""
        from providers import YouBackend

        backend = YouBackend()

        results = await backend.search("web development", max_results=5)

        assert len(results) > 0

        for result in results:
            # Title should be non-empty string
            assert isinstance(result["title"], str)
            assert len(result["title"]) > 0

            # URL should be valid format
            assert isinstance(result["url"], str)
            assert result["url"].startswith("http")

            # Content should be non-empty string
            assert isinstance(result["content"], str)
            assert len(result["content"]) > 0

            # Score should be number between 0 and 1
            assert isinstance(result["score"], (int, float))
            assert 0 <= result["score"] <= 1

            # Metadata should contain source
            assert "metadata" in result
            assert isinstance(result["metadata"], dict)
            assert result["metadata"]["source"] == "you"

        await backend.close()
