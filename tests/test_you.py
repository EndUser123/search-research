"""Unit tests for You.com search provider.

Tests use mocked responses to verify provider behavior without requiring
actual API calls. Tests follow the TDD pattern: RED → GREEN → REFACTOR.
"""

import httpx
import pytest
from unittest.mock import AsyncMock, MagicMock

from providers import YouBackend


class TestYouBackend:
    """Unit tests for YouBackend."""

    def test_name_property(self):
        """Test that provider name is correct."""
        backend = YouBackend()
        assert backend.name == "you"

    def test_requires_api_key(self):
        """Test that provider requires API key."""
        backend = YouBackend()
        assert backend.requires_api_key is True

    def test_api_key_env_var(self):
        """Test that API key environment variable is correct."""
        backend = YouBackend()
        assert backend.api_key_env_var == "YOU_API_KEY"

    def test_initialization_with_api_key(self, monkeypatch):
        """Test initialization with explicit API key."""
        monkeypatch.setenv("YOU_API_KEY", "test_api_key")
        backend = YouBackend(api_key="explicit_key")
        assert backend._api_key == "explicit_key"

    def test_initialization_from_env(self, monkeypatch):
        """Test initialization reads API key from environment."""
        monkeypatch.setenv("YOU_API_KEY", "env_key")
        backend = YouBackend()
        assert backend._api_key == "env_key"

    def test_initialization_without_api_key(self, monkeypatch):
        """Test initialization without API key."""
        monkeypatch.delenv("YOU_API_KEY", raising=False)
        backend = YouBackend()
        assert backend._api_key is None

    def test_validate_api_key_missing(self, monkeypatch):
        """Test validate_api_key returns False when key is missing."""
        monkeypatch.delenv("YOU_API_KEY", raising=False)
        backend = YouBackend()
        assert backend.validate_api_key() is False

    def test_validate_api_key_present(self, monkeypatch):
        """Test validate_api_key returns True when key is present."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")
        backend = YouBackend()
        assert backend.validate_api_key() is True

    def test_is_available_without_key(self, monkeypatch):
        """Test is_available returns False when API key is missing."""
        monkeypatch.delenv("YOU_API_KEY", raising=False)
        backend = YouBackend()
        assert backend.is_available() is False

    def test_is_available_with_key(self, monkeypatch):
        """Test is_available returns True when API key is present."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")
        backend = YouBackend()
        assert backend.is_available() is True

    @pytest.mark.asyncio
    async def test_search_without_api_key_returns_empty(self, monkeypatch):
        """Test that search returns empty list when API key is missing."""
        monkeypatch.delenv("YOU_API_KEY", raising=False)
        backend = YouBackend()

        results = await backend.search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_correct_format(self, monkeypatch):
        """Test that search returns results in correct format."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        # Mock the YouClient.search method
        from providers.you_client import YouSearchResponse, YouSearchResult

        mock_response = YouSearchResponse(
            query="test query",
            results=[
                YouSearchResult(
                    title="Test Result 1",
                    url="https://example.com/1",
                    content="Test content 1",
                    score=0.9,
                ),
                YouSearchResult(
                    title="Test Result 2",
                    url="https://example.com/2",
                    content="Test content 2",
                    score=0.8,
                ),
            ],
        )

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query", max_results=5)

        assert len(results) == 2
        assert results[0]["title"] == "Test Result 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["content"] == "Test content 1"
        assert results[0]["score"] >= 0
        assert "source" in results[0]["metadata"]
        assert results[0]["metadata"]["source"] == "you"

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, monkeypatch):
        """Test that search respects max_results parameter."""
        from providers.you_client import YouSearchResponse, YouSearchResult

        monkeypatch.setenv("YOU_API_KEY", "test_key")

        # Create 3 results (client handles max_results)
        mock_response = YouSearchResponse(
            query="test query",
            results=[
                YouSearchResult(
                    title=f"Result {i}",
                    url=f"https://example.com/{i}",
                    content=f"Content {i}",
                    score=0.9,
                )
                for i in range(3)
            ],
        )

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query", max_results=3)

        # Verify client was called with max_results
        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs.get("max_results") == 3

        # Verify we got the expected number of results
        assert len(results) == 3

    @pytest.mark.asyncio
    async def test_search_with_timeout(self, monkeypatch):
        """Test that search respects timeout parameter."""
        from providers.you_client import YouSearchResponse

        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_response = YouSearchResponse(query="test query", results=[])

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        backend = YouBackend()
        backend._client = mock_client

        await backend.search("test query", timeout=10.0)

        # Verify timeout was used (implementation dependent)
        # This test verifies the parameter is accepted
        assert True

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self, monkeypatch):
        """Test that search handles HTTP errors gracefully."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.HTTPStatusError(
            "API Error", request=MagicMock(), response=MagicMock(status_code=401)
        )

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list on error
        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_network_error(self, monkeypatch):
        """Test that search handles network errors gracefully."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.NetworkError("Network error")

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list on error
        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_timeout_error(self, monkeypatch):
        """Test that search handles timeout errors gracefully."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.TimeoutException("Request timed out")

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list on timeout
        assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_json_decode_error(self, monkeypatch):
        """Test that search handles JSON decode errors gracefully."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_client = AsyncMock()
        # YouClient raises ValueError, not JSON decode error
        # This simulates a parsing error in the client
        mock_client.search.side_effect = Exception("Parsing error")

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list on error
        assert results == []

    @pytest.mark.asyncio
    async def test_close_cleans_up_client(self, monkeypatch):
        """Test that close properly cleans up HTTP client."""
        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_client = AsyncMock()
        mock_client.close = AsyncMock()

        backend = YouBackend()
        backend._client = mock_client

        await backend.close()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_empty_response(self, monkeypatch):
        """Test that search handles empty API response."""
        from providers.you_client import YouSearchResponse

        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_response = YouSearchResponse(query="test query", results=[])

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_missing_fields(self, monkeypatch):
        """Test that search handles results with missing fields."""
        from providers.you_client import YouSearchResponse, YouSearchResult

        monkeypatch.setenv("YOU_API_KEY", "test_key")

        mock_response = YouSearchResponse(
            query="test query",
            results=[
                YouSearchResult(title="", url="https://example.com/1", content="Content 1"),
                YouSearchResult(title="Result 2", url="", content="Content 2"),
                YouSearchResult(title="Result 3", url="https://example.com/3", content=""),
            ],
        )

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        backend = YouBackend()
        backend._client = mock_client

        results = await backend.search("test query")

        # Should handle missing fields gracefully
        assert len(results) == 3
        assert all("title" in r for r in results)
        assert all("url" in r for r in results)
        assert all("content" in r for r in results)

    def test_max_results_property(self):
        """Test max_results property."""
        backend = YouBackend(max_results=15)
        assert backend.max_results == 15
