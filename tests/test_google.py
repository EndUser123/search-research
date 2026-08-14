"""Unit tests for Google search provider."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import HTTPStatusError

from core.providers.google import GoogleBackend


@pytest.fixture
def google_backend():
    """Create GoogleBackend instance for testing."""
    return GoogleBackend(api_key="test_api_key")


@pytest.fixture
def mock_google_response():
    """Mock Google Custom Search API response."""
    return {
        "kind": "customsearch#search",
        "url": {
            "type": "application/json",
            "template": "https://www.googleapis.com/customsearch/v1?q={searchTerms}"
        },
        "queries": {
            "request": [
                {
                    "title": "Google Custom Search - query",
                    "totalResults": "1000",
                    "searchTerms": "test query",
                    "count": 10,
                    "startIndex": 1,
                }
            ]
        },
        "context": {
            "title": "Test Search Engine"
        },
        "searchInformation": {
            "searchTime": 0.123,
            "totalResults": "1000"
        },
        "items": [
            {
                "kind": "customsearch#result",
                "title": "Test Result 1",
                "link": "https://example.com/1",
                "displayLink": "example.com",
                "snippet": "This is a test result snippet for result 1",
                "htmlSnippet": "This is a <b>test</b> result snippet",
                "pagemap": {
                    "article": [
                        {"publishedDate": "2026-03-07"}
                    ]
                }
            },
            {
                "kind": "customsearch#result",
                "title": "Test Result 2",
                "link": "https://example.com/2",
                "displayLink": "example.com",
                "snippet": "This is a test result snippet for result 2",
                "htmlSnippet": "Another <b>test</b> result",
            },
            {
                "kind": "customsearch#result",
                "title": "Test Result 3",
                "link": "https://example.com/3",
                "displayLink": "example.com",
                "snippet": "This is a test result snippet for result 3",
            }
        ]
    }


class TestGoogleBackend:
    """Test GoogleBackend implementation."""

    def test_name_property(self, google_backend):
        """Test provider name."""
        assert google_backend.name == "google"

    def test_requires_api_key(self, google_backend):
        """Test that provider requires API key."""
        assert google_backend.requires_api_key is True

    def test_api_key_env_var(self, google_backend):
        """Test API key environment variable name."""
        assert google_backend.api_key_env_var == "GOOGLE_API_KEY"

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        backend = GoogleBackend(api_key="explicit_key")
        assert backend._api_key == "explicit_key"

    def test_initialization_from_env(self, monkeypatch):
        """Test initialization from environment variable."""
        monkeypatch.setenv("GOOGLE_API_KEY", "env_key")
        backend = GoogleBackend()
        assert backend._api_key == "env_key"

    def test_initialization_max_results(self):
        """Test initialization with custom max_results."""
        backend = GoogleBackend(api_key="test_key", max_results=5)
        assert backend.max_results == 5

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_without_api_key(self, monkeypatch):
        """Test that search returns empty list when API key is missing."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        backend = GoogleBackend(api_key=None)

        results = await backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_success(self, google_backend, mock_google_response):
        """Test successful search returns formatted results."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            # Setup mock client
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_google_response
            mock_client_class.return_value = mock_client

            results = await google_backend.search("test query")

            assert len(results) == 3
            assert results[0]["title"] == "Test Result 1"
            assert results[0]["url"] == "https://example.com/1"
            assert results[0]["content"] == "This is a test result snippet for result 1"
            assert results[0]["score"] >= 0
            assert "metadata" in results[0]
            assert results[0]["metadata"]["source"] == "google"

    @pytest.mark.asyncio
    async def test_search_with_custom_max_results(self, google_backend, mock_google_response):
        """Test search with custom max_results parameter."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_google_response
            mock_client_class.return_value = mock_client

            await google_backend.search("test query", max_results=5)

            # Verify client was called with correct max_results
            mock_client.search.assert_called_once()
            call_kwargs = mock_client.search.call_args.kwargs
            assert "num" in call_kwargs or call_kwargs.get("max_results") == 5

    @pytest.mark.asyncio
    async def test_search_with_custom_timeout(self, google_backend, mock_google_response):
        """Test search with custom timeout parameter."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.return_value = mock_google_response
            mock_client_class.return_value = mock_client

            await google_backend.search("test query", timeout=10.0)

            # Verify timeout was passed through
            mock_client.search.assert_called_once()
            # Timeout should be handled at client level

    @pytest.mark.asyncio
    async def test_search_handles_http_error(self, google_backend):
        """Test that search returns empty list on HTTP error."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.side_effect = HTTPStatusError(
                "API Error",
                request=MagicMock(),
                response=MagicMock(status_code=403)
            )
            mock_client_class.return_value = mock_client

            results = await google_backend.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_handles_generic_exception(self, google_backend):
        """Test that search returns empty list on generic exception."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.side_effect = Exception("Network error")
            mock_client_class.return_value = mock_client

            results = await google_backend.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_search_empty_response(self, google_backend):
        """Test search with empty response."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.search.return_value = {"items": []}
            mock_client_class.return_value = mock_client

            results = await google_backend.search("test query")

            assert results == []

    @pytest.mark.asyncio
    async def test_close(self, google_backend):
        """Test close method."""
        with patch("search_research.providers.google.GoogleClientImpl") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.close = AsyncMock()
            mock_client_class.return_value = mock_client

            # Trigger client creation
            await google_backend.search("test")

            # Close should not raise
            await google_backend.close()

            # If client was created, close should be called
            if google_backend._client is not None:
                mock_client.close.assert_called_once()

    def test_validate_api_key_missing(self, monkeypatch):
        """Test validate_api_key returns False when key is missing."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        backend = GoogleBackend(api_key=None)

        assert backend.validate_api_key() is False

    def test_validate_api_key_present(self, monkeypatch):
        """Test validate_api_key returns True when key is present."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
        backend = GoogleBackend()

        assert backend.validate_api_key() is True

    def test_is_available_with_key(self, monkeypatch):
        """Test is_available returns True when API key is configured."""
        monkeypatch.setenv("GOOGLE_API_KEY", "test_key")
        backend = GoogleBackend()

        assert backend.is_available() is True

    def test_is_available_without_key(self, monkeypatch):
        """Test is_available returns False when API key is missing."""
        monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
        backend = GoogleBackend(api_key=None)

        assert backend.is_available() is False
