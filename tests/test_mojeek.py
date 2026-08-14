"""Unit tests for Mojeek search provider.

Tests use mocked HTTP responses to verify:
- API key validation
- Search request formatting
- Response parsing
- Error handling and graceful degradation
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from core.providers.mojeek import MojeekBackend
from core.providers.mojeek_client import (
    MojeekSearchResponse,
    MojeekSearchResult,
)


class TestMojeekClient:
    """Test MojeekClient implementation."""

    @pytest.fixture
    def mock_response(self):
        """Mock successful API response."""
        return {
            "query": "python async programming",
            "results": [
                {
                    "title": "Async IO in Python",
                    "url": "https://docs.python.org/3/library/asyncio.html",
                    "snippet": "Python's asyncio module provides infrastructure for writing single-threaded concurrent code.",
                    "score": 0.95,
                },
                {
                    "title": "Real Python: Async IO",
                    "url": "https://realpython.com/async-io-python/",
                    "snippet": "Learn how to use Python's async/await syntax to write concurrent code.",
                    "score": 0.88,
                },
            ],
        }

    @pytest.fixture
    def client(self, monkeypatch):
        """Create client with test API key."""
        monkeypatch.setenv("MOJEEK_API_KEY", "test_key_123")
        from providers.mojeek_client import MojeekClient

        return MojeekClient(api_key="test_key_123")

    def test_init_with_api_key(self, monkeypatch):
        """Test client initialization with API key."""
        from providers.mojeek_client import MojeekClient

        monkeypatch.setenv("MOJEEK_API_KEY", "env_key_456")
        client = MojeekClient(api_key="explicit_key_789")
        assert client._api_key == "explicit_key_789"

    def test_init_from_env(self, monkeypatch):
        """Test client initialization reads from environment."""
        from providers.mojeek_client import MojeekClient

        monkeypatch.setenv("MOJEEK_API_KEY", "env_key_456")
        client = MojeekClient()
        assert client._api_key == "env_key_456"

    def test_init_missing_api_key(self, monkeypatch):
        """Test client initialization fails without API key."""
        from providers.mojeek_client import MojeekClient

        monkeypatch.delenv("MOJEEK_API_KEY", raising=False)
        with pytest.raises(ValueError, match="Mojeek API key is required"):
            MojeekClient()

    def test_parse_result(self):
        """Test parsing single result from API response."""
        from providers.mojeek_client import MojeekClient

        client = MojeekClient(api_key="test_key")
        raw = {
            "title": "Test Result",
            "url": "https://example.com",
            "snippet": "Test content",
            "score": 0.85,
        }

        result = client._parse_result(raw)
        assert isinstance(result, MojeekSearchResult)
        assert result.title == "Test Result"
        assert result.url == "https://example.com"
        assert result.content == "Test content"
        assert result.score == 0.85

    def test_parse_response(self, mock_response):
        """Test parsing complete API response."""
        from providers.mojeek_client import MojeekClient

        client = MojeekClient(api_key="test_key")
        response = client._parse_response(mock_response, "test query")

        assert isinstance(response, MojeekSearchResponse)
        assert response.query == "test query"
        assert len(response.results) == 2
        assert response.results[0].title == "Async IO in Python"
        assert response.results[1].title == "Real Python: Async IO"

    def test_build_request_payload(self, client):
        """Test building API request payload."""
        payload = client._build_request_payload(
            "test query", max_results=5, timeout=10.0
        )

        assert payload["q"] == "test query"
        assert payload["key"] == "test_key_123"
        assert payload["count"] == 5

    @pytest.mark.asyncio
    async def test_search_success(self, client, mock_response):
        """Test successful search execution."""
        # Mock HTTP client
        mock_http_response = MagicMock()
        mock_http_response.status_code = 200
        mock_http_response.json.return_value = mock_response
        mock_http_response.raise_for_status = MagicMock()

        mock_http_client = MagicMock()
        mock_http_client.get = AsyncMock(return_value=mock_http_response)
        client._client = mock_http_client

        response = await client.search("python async")

        assert response.query == "python async"
        assert len(response.results) == 2
        assert response.results[0].url == "https://docs.python.org/3/library/asyncio.html"

    @pytest.mark.asyncio
    async def test_search_http_error(self, client):
        """Test search handles HTTP errors gracefully."""
        mock_http_client = MagicMock()
        mock_http_client.get = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "401 Unauthorized", request=MagicMock(), response=MagicMock()
            )
        )
        client._client = mock_http_client

        with pytest.raises(httpx.HTTPStatusError):
            await client.search("test query")

    @pytest.mark.asyncio
    async def test_close(self, client):
        """Test closing HTTP client."""
        mock_http_client = AsyncMock()
        mock_http_client.aclose = AsyncMock()
        client._client = mock_http_client

        await client.close()

        mock_http_client.aclose.assert_called_once()
        assert client._client is None


class TestMojeekBackend:
    """Test MojeekBackend provider implementation."""

    @pytest.fixture
    def backend(self, monkeypatch):
        """Create backend with test API key."""
        monkeypatch.setenv("MOJEEK_API_KEY", "test_key_123")
        return MojeekBackend(api_key="test_key_123", max_results=10)

    @pytest.fixture
    def mock_search_response(self):
        """Mock client search response."""
        from providers.mojeek_client import MojeekSearchResponse

        return MojeekSearchResponse(
            query="test query",
            results=[
                MojeekSearchResult(
                    title="Test Result",
                    url="https://example.com",
                    content="Test content",
                    score=0.9,
                )
            ],
        )

    def test_name(self, backend):
        """Test provider name."""
        assert backend.name == "mojeek"

    def test_requires_api_key(self, backend):
        """Test that provider requires API key."""
        assert backend.requires_api_key is True

    def test_api_key_env_var(self, backend):
        """Test API key environment variable name."""
        assert backend.api_key_env_var == "MOJEEK_API_KEY"

    def test_init_with_api_key(self, monkeypatch):
        """Test initialization with explicit API key."""
        backend = MojeekBackend(api_key="explicit_key")
        assert backend._api_key == "explicit_key"

    def test_init_from_env(self, monkeypatch):
        """Test initialization reads API key from environment."""
        monkeypatch.setenv("MOJEEK_API_KEY", "env_key")
        backend = MojeekBackend()
        assert backend._api_key == "env_key"

    def test_validate_api_key_success(self, backend):
        """Test API key validation succeeds when key is set."""
        assert backend.validate_api_key() is True

    def test_validate_api_key_missing(self, monkeypatch):
        """Test API key validation fails when key is missing."""
        monkeypatch.delenv("MOJEEK_API_KEY", raising=False)
        backend = MojeekBackend(api_key=None)
        assert backend.validate_api_key() is False

    def test_is_available_with_key(self, backend):
        """Test provider is available when API key is set."""
        assert backend.is_available() is True

    def test_is_available_without_key(self, monkeypatch):
        """Test provider is not available when API key is missing."""
        monkeypatch.delenv("MOJEEK_API_KEY", raising=False)
        backend = MojeekBackend(api_key=None)
        assert backend.is_available() is False

    @pytest.mark.asyncio
    async def test_search_success(
        self, backend, mock_search_response, monkeypatch
    ):
        """Test successful search returns formatted results."""
        # Mock client
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_search_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Test Result"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.9
        assert results[0]["metadata"]["source"] == "mojeek"

    @pytest.mark.asyncio
    async def test_search_missing_api_key(self, monkeypatch):
        """Test search returns empty list when API key is missing."""
        monkeypatch.delenv("MOJEEK_API_KEY", raising=False)
        backend = MojeekBackend(api_key=None)

        results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_error_handling(self, backend, monkeypatch):
        """Test search handles errors gracefully and returns empty list."""
        # Mock client that raises exception
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("API error")

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_with_max_results(self, backend, mock_search_response):
        """Test search respects max_results parameter."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_search_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search("test query", max_results=5)

        # Verify client was called with max_results
        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["max_results"] == 5

    @pytest.mark.asyncio
    async def test_search_with_timeout(self, backend, mock_search_response):
        """Test search passes timeout parameter."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_search_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search("test query", timeout=10.0)

        # Verify timeout was passed to client
        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["timeout"] == 10.0

    @pytest.mark.asyncio
    async def test_close(self, backend):
        """Test closing backend closes client."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        backend._client = mock_client

        await backend.close()

        mock_client.close.assert_called_once()
        assert backend._client is None

    def test_lazy_client_initialization(self, backend):
        """Test client is lazily initialized."""
        assert backend._client is None

        client = backend._get_client()

        assert client is not None
        assert backend._client is client

    @pytest.mark.asyncio
    async def test_search_standard_format(self, backend, mock_search_response):
        """Test search returns results in standard format."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_search_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        # Verify standard format keys
        result = results[0]
        assert "title" in result
        assert "url" in result
        assert "content" in result
        assert "score" in result
        assert "metadata" in result
        assert result["metadata"]["source"] == "mojeek"


class TestMojeekBackendGracefulDegradation:
    """Test graceful degradation behavior."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_http_error(self, monkeypatch):
        """Test search returns empty list on HTTP errors (never raises)."""
        monkeypatch.setenv("MOJEEK_API_KEY", "test_key")
        backend = MojeekBackend()

        # Mock client that raises HTTP error
        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.HTTPStatusError(
            "500 Server Error", request=MagicMock(), response=MagicMock()
        )

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_timeout(self, monkeypatch):
        """Test search returns empty list on timeout (never raises)."""
        monkeypatch.setenv("MOJEEK_API_KEY", "test_key")
        backend = MojeekBackend()

        # Mock client that raises timeout
        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.TimeoutException(
            "Request timed out", request=MagicMock()
        )

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_empty_on_network_error(self, monkeypatch):
        """Test search returns empty list on network errors (never raises)."""
        monkeypatch.setenv("MOJEEK_API_KEY", "test_key")
        backend = MojeekBackend()

        # Mock client that raises network error
        mock_client = AsyncMock()
        mock_client.search.side_effect = httpx.NetworkError("Network unreachable")

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_logs_errors(self, monkeypatch, caplog):
        """Test search logs errors before returning empty list."""
        import logging

        monkeypatch.setenv("MOJEEK_API_KEY", "test_key")
        backend = MojeekBackend()

        # Mock client that raises exception
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("Test error")

        with patch.object(backend, "_get_client", return_value=mock_client):
            with caplog.at_level(logging.ERROR):
                results = await backend.search("test query")

        assert results == []
        assert any("Mojeek search failed" in record.message for record in caplog.records)
