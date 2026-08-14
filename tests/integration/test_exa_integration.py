"""Integration tests for ExaBackend provider.

These tests require a valid EXA_API_KEY environment variable.
Tests are skipped if the API key is not set.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


@pytest.mark.skipif(
    not os.getenv("EXA_API_KEY"),
    reason="EXA_API_KEY environment variable not set",
)
class TestExaBackendIntegration:
    """Integration tests for ExaBackend with real API."""

    @pytest.mark.asyncio
    async def test_backend_is_available(self):
        """Test backend is available when API key is set."""
        from providers.exa import ExaBackend

        backend = ExaBackend()
        assert backend.is_available() is True

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Test search returns actual results from Exa API."""
        from providers.exa import ExaBackend

        backend = ExaBackend()
        results = await backend.search("Python programming", max_results=3)

        assert isinstance(results, list)
        assert len(results) > 0

        # Verify result structure
        result = results[0]
        assert "title" in result
        assert "url" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result
        assert result["metadata"]["source"] == "exa"

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self):
        """Test search handles empty query gracefully."""
        from providers.exa import ExaBackend

        backend = ExaBackend()
        results = await backend.search("", max_results=5)

        # Should return empty list or handle gracefully
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_with_max_results(self):
        """Test search respects max_results parameter."""
        from providers.exa import ExaBackend

        backend = ExaBackend()
        results = await backend.search("machine learning", max_results=5)

        assert len(results) <= 5

    @pytest.mark.asyncio
    async def test_close_connection(self):
        """Test closing backend connection."""
        from providers.exa import ExaBackend

        backend = ExaBackend()
        # Initialize client by calling search
        await backend.search("test query", max_results=1)

        # Close should not raise exception
        await backend.close()


class TestExaBackendMockedIntegration:
    """Mocked integration tests that don't require API key."""

    @pytest.mark.asyncio
    async def test_client_initialization(self):
        """Test Exa client is initialized correctly."""
        from providers.exa import ExaBackend

        backend = ExaBackend(api_key="test_key_123")

        # Get client should initialize Exa client
        client = backend._get_client()

        assert client is not None
        # Verify client has search method
        assert hasattr(client, "search")

    @pytest.mark.asyncio
    async def test_search_translates_response_format(self):
        """Test search translates Exa response to standard format."""
        from providers.exa import ExaBackend

        backend = ExaBackend(api_key="test_key")

        # Mock Exa response
        mock_result = MagicMock()
        mock_result.title = "Test Result"
        mock_result.url = "https://example.com/test"
        mock_result.score = 0.95
        mock_result.publishedDate = "2024-01-01"

        mock_response = MagicMock()
        mock_response.results = [mock_result]

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com/test"
        assert results[0]["score"] == 0.95
        assert results[0]["metadata"]["source"] == "exa"

    @pytest.mark.asyncio
    async def test_search_passes_domain_filters(self):
        """Test search passes domain filters to Exa client."""
        from providers.exa import ExaBackend

        backend = ExaBackend(api_key="test_key")

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search(
                "test query",
                include_domains=["github.com", "stackoverflow.com"],
                exclude_domains=["spam.com"],
            )

        # Verify domain filters were passed
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["include_domains"] == ["github.com", "stackoverflow.com"]
        assert call_kwargs["exclude_domains"] == ["spam.com"]

    @pytest.mark.asyncio
    async def test_search_timeout_parameter(self):
        """Test search handles timeout parameter (client-level, not passed to API)."""
        from providers.exa import ExaBackend

        backend = ExaBackend(api_key="test_key")

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search("test query", timeout=10.0)

        # Timeout is handled at HTTP level, not passed to search method
        mock_client.search.assert_called_once()
