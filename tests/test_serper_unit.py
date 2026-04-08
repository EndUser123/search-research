"""Unit tests for Serper search provider.

Tests use mocked HTTP responses to verify SerperBackend behavior.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import httpx

from core.providers.serper import SerperBackend
from core.providers.serper_client import SerperClient, SerperSearchResult


class TestSerperBackendInit:
    """Tests for SerperBackend initialization."""

    def test_backend_name(self):
        """Test that backend name is 'serper'."""
        backend = SerperBackend()
        assert backend.name == "serper"

    def test_requires_api_key(self):
        """Test that backend requires API key."""
        backend = SerperBackend()
        assert backend.requires_api_key is True

    def test_api_key_env_var(self):
        """Test that API key env var is 'SERPER_API_KEY'."""
        backend = SerperBackend()
        assert backend.api_key_env_var == "SERPER_API_KEY"

    def test_init_with_api_key(self):
        """Test initialization with explicit API key."""
        backend = SerperBackend(api_key="test_key_123")
        assert backend._api_key == "test_key_123"

    def test_init_from_env_var(self):
        """Test initialization from environment variable."""
        with patch.dict("os.environ", {"SERPER_API_KEY": "env_key_456"}):
            backend = SerperBackend()
            assert backend._api_key == "env_key_456"

    def test_init_with_default_max_results(self):
        """Test default max_results is 10."""
        backend = SerperBackend()
        assert backend.max_results == 10

    def test_init_with_custom_max_results(self):
        """Test custom max_results."""
        backend = SerperBackend(max_results=5)
        assert backend.max_results == 5

class TestSerperClient:
    """Tests for SerperClient HTTP interactions."""

    @pytest.fixture
    def mock_client(self):
        """Create a mock HTTP client."""
        client = SerperClient(api_key="test_key")
        return client

    def test_client_initialization(self):
        """Test client initializes with API key."""
        client = SerperClient(api_key="test_key")
        assert client._api_key == "test_key"

    def test_client_raises_without_api_key(self):
        """Test client raises ValueError when API key is missing."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                SerperClient(api_key=None)

    @pytest.mark.asyncio
    async def test_search_builds_correct_request(self, mock_client):
        """Test that search builds correct API request."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "Test Result",
                    "link": "https://example.com",
                    "snippet": "Test snippet",
                }
            ]
        }

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(mock_client, "_get_client", return_value=mock_http):
            await mock_client.search("test query")

            # Verify request was made correctly
            mock_http.post.assert_called_once()
            call_args = mock_http.post.call_args
            assert call_args[0][0] == "https://google.serper.dev/search"
            payload = call_args[1]["json"]
            assert payload["q"] == "test query"
            assert payload["apiKey"] == "test_key"

    @pytest.mark.asyncio
    async def test_search_parses_results(self, mock_client):
        """Test that search parses API response correctly."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "organic": [
                {
                    "title": "First Result",
                    "link": "https://example.com/1",
                    "snippet": "First snippet",
                },
                {
                    "title": "Second Result",
                    "link": "https://example.com/2",
                    "snippet": "Second snippet",
                }
            ]
        }

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(mock_client, "_get_client", return_value=mock_http):
            response = await mock_client.search("test query")

            assert len(response.results) == 2
            assert response.results[0].title == "First Result"
            assert response.results[0].url == "https://example.com/1"
            assert response.results[0].content == "First snippet"
            assert response.results[1].title == "Second Result"

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self, mock_client):
        """Test that search handles empty response gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"organic": []}

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(mock_client, "_get_client", return_value=mock_http):
            response = await mock_client.search("test query")

            assert len(response.results) == 0

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self, mock_client):
        """Test that search handles HTTP errors gracefully."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
            "Unauthorized", request=MagicMock(), response=mock_response
        )

        mock_http = AsyncMock()
        mock_http.post.return_value = mock_response

        with patch.object(mock_client, "_get_client", return_value=mock_http):
            with pytest.raises(httpx.HTTPStatusError):
                await mock_client.search("test query")

    @pytest.mark.asyncio
    async def test_search_handles_timeout(self, mock_client):
        """Test that search handles timeout gracefully."""
        mock_http = AsyncMock()
        mock_http.post.side_effect = httpx.TimeoutException("Request timeout")

        with patch.object(mock_client, "_get_client", return_value=mock_http):
            with pytest.raises(httpx.TimeoutException):
                await mock_client.search("test query")


class TestSerperBackendSearch:
    """Tests for SerperBackend.search() method."""

    @pytest.fixture
    def backend(self):
        """Create a backend instance with test API key."""
        return SerperBackend(api_key="test_key")

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_without_api_key(self):
        """Test that search returns empty list when API key is missing."""
        backend = SerperBackend(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            results = await backend.search("test query")
            assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_standard_format(self, backend):
        """Test that search returns results in standard format."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_result = MagicMock()
        mock_result.title = "Test Title"
        mock_result.url = "https://example.com"
        mock_result.content = "Test content"
        mock_result.score = 0.85
        mock_response.results = [mock_result]
        mock_client.search.return_value = mock_response

        backend._client = mock_client

        results = await backend.search("test query")

        assert len(results) == 1
        assert results[0]["title"] == "Test Title"
        assert results[0]["url"] == "https://example.com"
        assert results[0]["content"] == "Test content"
        assert results[0]["score"] == 0.85
        assert results[0]["metadata"]["source"] == "serper"

    @pytest.mark.asyncio
    async def test_search_passes_max_results(self, backend):
        """Test that search passes max_results to client."""
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.results = []
        mock_client.search.return_value = mock_response

        backend._client = mock_client

        await backend.search("test query", max_results=5)

        mock_client.search.assert_called_once()
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs["max_results"] == 5

    @pytest.mark.asyncio
    async def test_search_handles_client_errors_gracefully(self, backend):
        """Test that search handles client errors without raising."""
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("Client error")

        backend._client = mock_client

        results = await backend.search("test query")

        # Should return empty list on error
        assert results == []

    @pytest.mark.asyncio
    async def test_search_logs_errors(self, backend, caplog):
        """Test that search logs errors appropriately."""
        import logging

        mock_client = AsyncMock()
        mock_client.search.side_effect = RuntimeError("Search failed")

        backend._client = mock_client

        with caplog.at_level(logging.ERROR):
            results = await backend.search("test query")

        assert results == []
        # Should have logged an error
        assert any("Serper search failed" in record.message for record in caplog.records)


class TestSerperBackendClose:
    """Tests for SerperBackend.close() method."""

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test that close works when no client exists."""
        backend = SerperBackend(api_key="test_key")
        # Should not raise
        await backend.close()

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test that close closes the client."""
        backend = SerperBackend(api_key="test_key")
        mock_client = AsyncMock()
        backend._client = mock_client

        await backend.close()

        mock_client.close.assert_called_once()


class TestSerperSearchResult:
    """Tests for SerperSearchResult dataclass."""

    def test_search_result_creation(self):
        """Test creating a search result."""
        result = SerperSearchResult(
            title="Test",
            url="https://example.com",
            content="Content",
            score=0.9
        )
        assert result.title == "Test"
        assert result.url == "https://example.com"
        assert result.content == "Content"
        assert result.score == 0.9

    def test_search_result_defaults(self):
        """Test default values for optional fields."""
        result = SerperSearchResult(
            title="Test",
            url="https://example.com",
            content="Content"
        )
        assert result.score == 0.0


class TestSerperBackendValidation:
    """Tests for API key validation."""

    def test_validate_api_key_with_valid_key(self):
        """Test validate_api_key returns True when key is set."""
        backend = SerperBackend(api_key="test_key")
        assert backend.validate_api_key() is True

    def test_validate_api_key_without_key(self, caplog):
        """Test validate_api_key returns False and logs warning when key is missing."""
        import logging

        backend = SerperBackend(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            with caplog.at_level(logging.WARNING):
                result = backend.validate_api_key()

        assert result is False
        assert any("SERPER_API_KEY" in record.message for record in caplog.records)

    def test_is_available_with_api_key(self):
        """Test is_available returns True when API key is set."""
        backend = SerperBackend(api_key="test_key")
        assert backend.is_available() is True

    def test_is_available_without_api_key(self):
        """Test is_available returns False when API key is missing."""
        backend = SerperBackend(api_key=None)
        with patch.dict("os.environ", {}, clear=True):
            assert backend.is_available() is False
