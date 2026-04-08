"""Unit tests for Bing search provider.

Tests use mocked responses to verify correct behavior without requiring
actual API calls or credentials.
"""

import os
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.providers.bing import BingBackend
from core.providers.bing_client import BingClient


class TestBingClient:
    """Test BingClient HTTP implementation."""

    @pytest.fixture
    def mock_response(self):
        """Mock successful Bing API response."""
        return {
            "webPages": {
                "value": [
                    {
                        "name": "Test Result 1",
                        "url": "https://example.com/1",
                        "snippet": "Snippet 1",
                    },
                    {
                        "name": "Test Result 2",
                        "url": "https://example.com/2",
                        "snippet": "Snippet 2",
                    },
                ]
            }
        }

    @pytest.fixture
    def client(self):
        """Create BingClient instance for testing."""
        return BingClient(api_key="test_key")

    def test_init_with_api_key(self):
        """Initialize client with explicit API key."""
        client = BingClient(api_key="my_key")
        assert client._api_key == "my_key"

    def test_init_from_env(self):
        """Initialize client from environment variable."""
        with patch.dict(os.environ, {"BING_API_KEY": "env_key"}):
            client = BingClient()
            assert client._api_key == "env_key"

    def test_init_missing_api_key(self):
        """Raise ValueError when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                BingClient()

    def test_parse_result(self, client):
        """Test parsing single result from API response."""
        raw = {
            "name": "Test Title",
            "url": "https://example.com",
            "snippet": "Test snippet",
        }
        result = client._parse_result(raw)

        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.content == "Test snippet"
        assert result.score == 0.0

    def test_parse_response(self, client, mock_response):
        """Test parsing complete API response."""
        response = client._parse_response(mock_response, "test query")

        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.results[0].title == "Test Result 1"
        assert response.results[1].url == "https://example.com/2"

    @pytest.mark.asyncio
    async def test_search_success(self, client, mock_response):
        """Test successful search with mocked HTTP response."""
        # Mock HTTP client
        mock_http_client = AsyncMock()
        mock_response_obj = MagicMock()
        mock_response_obj.json.return_value = mock_response
        mock_response_obj.raise_for_status.return_value = None
        mock_http_client.get.return_value = mock_response_obj

        with patch.object(client, "_get_client", return_value=mock_http_client):
            response = await client.search("test query")

        assert len(response.results) == 2
        assert response.results[0].title == "Test Result 1"
        assert response.query == "test query"

    @pytest.mark.asyncio
    async def test_search_http_error(self, client):
        """Test search handles HTTP errors gracefully."""
        mock_http_client = AsyncMock()
        mock_http_client.get.side_effect = httpx.HTTPStatusError(
            "API Error", request=MagicMock(), response=MagicMock()
        )

        with patch.object(client, "_get_client", return_value=mock_http_client):
            with pytest.raises(httpx.HTTPStatusError):
                await client.search("test query")

    @pytest.mark.asyncio
    async def test_search_empty_query(self, client):
        """Test search raises ValueError for empty query."""
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await client.search("")

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing HTTP client."""
        mock_http_client = AsyncMock()
        client._client = mock_http_client

        await client.close()

        mock_http_client.aclose.assert_called_once()
        assert client._client is None


class TestBingBackend:
    """Test BingBackend implementation."""

    @pytest.fixture
    def backend(self):
        """Create BingBackend instance for testing."""
        return BingBackend(api_key="test_key")

    def test_name_property(self, backend):
        """Test provider name."""
        assert backend.name == "bing"

    def test_requires_api_key(self, backend):
        """Test that provider requires API key."""
        assert backend.requires_api_key is True

    def test_api_key_env_var(self, backend):
        """Test API key environment variable name."""
        assert backend.api_key_env_var == "BING_API_KEY"

    def test_init_with_api_key(self):
        """Initialize backend with explicit API key."""
        backend = BingBackend(api_key="my_key")
        assert backend._api_key == "my_key"

    def test_init_from_env(self):
        """Initialize backend from environment variable."""
        with patch.dict(os.environ, {"BING_API_KEY": "env_key"}):
            backend = BingBackend()
            assert backend._api_key == "env_key"

    def test_validate_api_key_missing(self):
        """Test validation fails when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            backend = BingBackend(api_key=None)
            assert not backend.validate_api_key()

    def test_validate_api_key_present(self):
        """Test validation succeeds when API key is present."""
        backend = BingBackend(api_key="test_key")
        assert backend.validate_api_key()

    def test_is_available_with_key(self, backend):
        """Test backend is available when API key is set."""
        assert backend.is_available()

    def test_is_available_without_key(self):
        """Test backend is not available when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            backend = BingBackend(api_key=None)
            assert not backend.is_available()

    @pytest.mark.asyncio
    async def test_search_success(self, backend):
        """Test successful search returns formatted results."""
        # Mock the client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.title = "Test Result"
        mock_result.url = "https://example.com"
        mock_result.content = "Test content"
        mock_result.score = 0.8
        mock_response.results = [mock_result]
        mock_client.search.return_value = mock_response

        backend._client = mock_client

        results = await backend.search("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.8
        assert results[0]["metadata"]["source"] == "bing"

    @pytest.mark.asyncio
    async def test_search_missing_api_key(self):
        """Test search returns empty list when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            backend = BingBackend(api_key=None)
            results = await backend.search("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_graceful_degradation(self, backend):
        """Test search returns empty list on error (graceful degradation)."""
        # Mock client that raises exception
        mock_client = MagicMock()
        mock_client.search.side_effect = Exception("API Error")
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list, not raise exception
        assert results == []

    @pytest.mark.asyncio
    async def test_search_http_error(self, backend):
        """Test search handles HTTP errors gracefully."""
        mock_client = MagicMock()
        mock_client.search.side_effect = httpx.HTTPStatusError(
            "API Error", request=MagicMock(), response=MagicMock()
        )
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list
        assert results == []

    @pytest.mark.asyncio
    async def test_search_timeout(self, backend):
        """Test search handles timeout gracefully."""
        mock_client = MagicMock()
        mock_client.search.side_effect = TimeoutError("Request timeout")
        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list
        assert results == []

    @pytest.mark.asyncio
    async def test_close(self, backend):
        """Test closing backend."""
        mock_client = AsyncMock()
        backend._client = mock_client

        await backend.close()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_passes_max_results(self, backend):
        """Test that max_results parameter is passed to client."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.search.return_value = mock_response
        backend._client = mock_client

        await backend.search("test query", max_results=5)

        # Verify max_results was passed
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        assert call_args[1]["max_results"] == 5

    @pytest.mark.asyncio
    async def test_search_with_custom_timeout(self, backend):
        """Test search with custom timeout parameter."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.search.return_value = mock_response
        backend._client = mock_client

        await backend.search("test query", timeout=10.0)

        # Verify timeout was handled (backend doesn't directly pass timeout to client
        # since it's set at client initialization, but we verify the call works)
        mock_client.search.assert_called_once()


class TestBingBackendIntegration:
    """Integration-style tests for BingBackend."""

    def test_lazy_client_initialization(self):
        """Test that client is created lazily on first search."""
        backend = BingBackend(api_key="test_key")

        # Client should not exist initially
        assert backend._client is None

        # After search, client should be created
        # (We'll mock the actual search to avoid API call)
        with patch("search_research.providers.bing.BingClientImpl") as MockClient:
            mock_instance = MagicMock()
            mock_instance.search.return_value = MagicMock(results=[])
            MockClient.return_value = mock_instance

            import asyncio

            async def test():
                return await backend.search("test")

            asyncio.run(test())

            # Client should have been created
            assert MockClient.called

    def test_metadata_includes_source(self):
        """Test that metadata includes source provider name."""
        backend = BingBackend(api_key="test_key")

        # Mock client
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.title = "Test"
        mock_result.url = "https://example.com"
        mock_result.content = "Content"
        mock_result.score = 0.9
        mock_response.results = [mock_result]
        mock_client.search.return_value = mock_response
        backend._client = mock_client

        import asyncio

        async def test():
            results = await backend.search("test")
            assert results[0]["metadata"]["source"] == "bing"
            return results

        results = asyncio.run(test())
        assert results[0]["metadata"]["source"] == "bing"


class TestBingAPIKeyFormat:
    """Test Bing API key format validation."""

    def test_validate_api_key_format_valid(self):
        """Test validation of valid Bing API key format."""
        # Bing API keys are typically 32-character alphanumeric strings
        assert BingClient.validate_api_key_format("1234567890abcdefghijklmnop")

    def test_validate_api_key_format_invalid(self):
        """Test validation rejects invalid formats."""
        assert not BingClient.validate_api_key_format("short")
        assert not BingClient.validate_api_key_format("")
        assert not BingClient.validate_api_key_format(None)

    def test_validate_api_key_format_from_env(self):
        """Test validation using environment variable."""
        with patch.dict(os.environ, {"BING_API_KEY": "valid_key_32_characters_long!"}):
            assert BingClient.validate_api_key_format()
