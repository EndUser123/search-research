"""Unit tests for Kagi search provider.

These tests use mocked responses to verify KagiBackend implementation.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from core.providers.kagi_client import KagiClient, KagiSearchResponse, KagiSearchResult

from core.providers.kagi import KagiBackend


@pytest.fixture
def mock_kagi_response():
    """Mock Kagi API response."""
    return {
        "meta": {
            "id": "test-id",
            "query": "python async programming",
            "time": 0.5
        },
        "data": [
            {
                "t": "Python Async/Await Guide",
                "u": "https://example.com/async-guide",
                "d": "example.com",
                "sn": "Comprehensive guide to async/await in Python",
                "rank": 1
            },
            {
                "t": "Asyncio Best Practices",
                "u": "https://example.com/asyncio-best-practices",
                "d": "example.com",
                "sn": "Best practices for Python asyncio programming",
                "rank": 2
            }
        ]
    }


@pytest.fixture
def mock_empty_response():
    """Mock empty Kagi API response."""
    return {
        "meta": {
            "id": "test-id",
            "query": "test query",
            "time": 0.3
        },
        "data": []
    }


class TestKagiBackend:
    """Test KagiBackend implementation."""

    def test_name_property(self):
        """Test provider name."""
        backend = KagiBackend(api_key="test-key")
        assert backend.name == "kagi"

    def test_requires_api_key(self):
        """Test that provider requires API key."""
        backend = KagiBackend(api_key="test-key")
        assert backend.requires_api_key is True

    def test_api_key_env_var(self):
        """Test API key environment variable name."""
        backend = KagiBackend(api_key="test-key")
        assert backend.api_key_env_var == "KAGI_API_KEY"

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        backend = KagiBackend(api_key="test-key-123")
        assert backend._api_key == "test-key-123"

    def test_initialization_without_api_key(self, monkeypatch):
        """Test initialization reads from environment variable."""
        monkeypatch.setenv("KAGI_API_KEY", "env-key-456")
        backend = KagiBackend()
        assert backend._api_key == "env-key-456"

    @pytest.mark.asyncio
    async def test_search_with_valid_response(self, mock_kagi_response):
        """Test search with valid API response."""
        backend = KagiBackend(api_key="test-key")

        # Mock the client
        mock_client = AsyncMock()
        mock_response = KagiSearchResponse(
            query="python async programming",
            results=[
                KagiSearchResult(
                    title="Python Async/Await Guide",
                    url="https://example.com/async-guide",
                    content="Comprehensive guide to async/await in Python",
                    score=0.95
                ),
                KagiSearchResult(
                    title="Asyncio Best Practices",
                    url="https://example.com/asyncio-best-practices",
                    content="Best practices for Python asyncio programming",
                    score=0.87
                )
            ]
        )
        mock_client.search.return_value = mock_response

        with patch.object(backend, '_get_client', return_value=mock_client):
            results = await backend.search("python async programming")

            assert len(results) == 2
            assert results[0]["title"] == "Python Async/Await Guide"
            assert results[0]["url"] == "https://example.com/async-guide"
            assert results[0]["content"] == "Comprehensive guide to async/await in Python"
            assert results[0]["score"] == 0.95
            assert results[0]["metadata"]["source"] == "kagi"

    @pytest.mark.asyncio
    async def test_search_with_empty_response(self, mock_empty_response):
        """Test search with empty results."""
        backend = KagiBackend(api_key="test-key")

        mock_client = AsyncMock()
        mock_response = KagiSearchResponse(
            query="test query",
            results=[]
        )
        mock_client.search.return_value = mock_response

        with patch.object(backend, '_get_client', return_value=mock_client):
            results = await backend.search("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_without_api_key(self, monkeypatch):
        """Test search returns empty list when API key is missing."""
        monkeypatch.delenv("KAGI_API_KEY", raising=False)
        backend = KagiBackend(api_key=None)

        results = await backend.search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_api_error(self):
        """Test search handles API errors gracefully."""
        backend = KagiBackend(api_key="test-key")

        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("API Error")

        with patch.object(backend, '_get_client', return_value=mock_client):
            results = await backend.search("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_with_custom_max_results(self):
        """Test search with custom max_results parameter."""
        backend = KagiBackend(api_key="test-key", max_results=5)

        mock_client = AsyncMock()
        mock_response = KagiSearchResponse(
            query="test",
            results=[
                KagiSearchResult(
                    title=f"Result {i}",
                    url=f"https://example.com/{i}",
                    content=f"Content {i}",
                    score=0.9
                )
                for i in range(5)
            ]
        )
        mock_client.search.return_value = mock_response

        with patch.object(backend, '_get_client', return_value=mock_client):
            results = await backend.search("test", max_results=5)
            assert len(results) == 5

    @pytest.mark.asyncio
    async def test_search_with_custom_timeout(self):
        """Test search with custom timeout parameter."""
        backend = KagiBackend(api_key="test-key")

        mock_client = AsyncMock()
        mock_response = KagiSearchResponse(query="test", results=[])
        mock_client.search.return_value = mock_response

        with patch.object(backend, '_get_client', return_value=mock_client):
            await backend.search("test", timeout=10.0)
            # Verify client was called (timeout is handled internally)
            mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method cleans up resources."""
        backend = KagiBackend(api_key="test-key")

        mock_client = AsyncMock()
        backend._client = mock_client

        await backend.close()
        mock_client.close.assert_called_once()
        assert backend._client is None

    def test_validate_api_key_with_valid_key(self):
        """Test API key validation with valid key."""
        backend = KagiBackend(api_key="test-key")
        assert backend.validate_api_key() is True

    def test_validate_api_key_without_key(self, monkeypatch):
        """Test API key validation without key."""
        monkeypatch.delenv("KAGI_API_KEY", raising=False)
        backend = KagiBackend(api_key=None)
        assert backend.validate_api_key() is False

    def test_is_available_with_api_key(self):
        """Test is_available returns True when API key is set."""
        backend = KagiBackend(api_key="test-key")
        assert backend.is_available() is True

    def test_is_available_without_api_key(self, monkeypatch):
        """Test is_available returns False when API key is missing."""
        monkeypatch.delenv("KAGI_API_KEY", raising=False)
        backend = KagiBackend(api_key=None)
        assert backend.is_available() is False


class TestKagiClient:
    """Test KagiClient implementation."""

    def test_initialization_with_api_key(self):
        """Test client initialization with API key."""
        client = KagiClient(api_key="test-key")
        assert client._api_key == "test-key"

    def test_initialization_without_api_key(self, monkeypatch):
        """Test client initialization reads from environment."""
        monkeypatch.setenv("KAGI_API_KEY", "env-key")
        client = KagiClient()
        assert client._api_key == "env-key"

    def test_initialization_without_api_key_raises_error(self, monkeypatch):
        """Test client initialization fails without API key."""
        monkeypatch.delenv("KAGI_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Kagi API key is required"):
            KagiClient(api_key=None)

    def test_parse_result(self):
        """Test parsing single result from API response."""
        client = KagiClient(api_key="test-key")
        raw_result = {
            "t": "Test Title",
            "u": "https://example.com",
            "d": "example.com",
            "sn": "Test snippet",
            "rank": 1
        }

        result = client._parse_result(raw_result)
        assert result.title == "Test Title"
        assert result.url == "https://example.com"
        assert result.content == "Test snippet"

    def test_parse_response(self):
        """Test parsing complete API response."""
        client = KagiClient(api_key="test-key")
        raw_response = {
            "meta": {
                "id": "test-id",
                "query": "test query",
                "time": 0.5
            },
            "data": [
                {
                    "t": "Result 1",
                    "u": "https://example.com/1",
                    "d": "example.com",
                    "sn": "Snippet 1",
                    "rank": 1
                }
            ]
        }

        response = client._parse_response(raw_response, "test query")
        assert response.query == "test query"
        assert len(response.results) == 1
        assert response.results[0].title == "Result 1"

    @pytest.mark.asyncio
    async def test_search_success(self):
        """Test successful search."""
        client = KagiClient(api_key="test-key")

        # Mock HTTP client
        mock_http_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": {"id": "test-id", "query": "test", "time": 0.5},
            "data": [
                {
                    "t": "Test Result",
                    "u": "https://example.com",
                    "d": "example.com",
                    "sn": "Test snippet",
                    "rank": 1
                }
            ]
        }
        mock_http_client.post.return_value = mock_response

        with patch.object(client, '_get_client', return_value=mock_http_client):
            response = await client.search("test")

            assert response.query == "test"
            assert len(response.results) == 1
            assert response.results[0].title == "Test Result"

    @pytest.mark.asyncio
    async def test_search_with_empty_query_raises_error(self):
        """Test search with empty query raises ValueError."""
        client = KagiClient(api_key="test-key")
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await client.search("")

    @pytest.mark.asyncio
    async def test_close(self):
        """Test close method."""
        client = KagiClient(api_key="test-key")
        mock_http_client = AsyncMock()
        client._client = mock_http_client

        await client.close()
        mock_http_client.aclose.assert_called_once()
        assert client._client is None
