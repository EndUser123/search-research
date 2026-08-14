"""Unit tests for Brave search provider.

These tests use mocked responses to verify BraveBackend functionality.
"""

from unittest.mock import AsyncMock

import pytest

from core.providers.brave import BraveBackend
from core.providers.brave_client import BraveSearchResponse, BraveSearchResult


@pytest.fixture
def mock_brave_response():
    """Mock Brave Search API response."""
    return BraveSearchResponse(
        query="python programming",
        results=[
            BraveSearchResult(
                title="Python Programming Guide",
                url="https://example.com/python",
                content="Learn Python programming from basics to advanced.",
                score=0.95,
                published_date="2024-01-15",
            ),
            BraveSearchResult(
                title="Advanced Python Techniques",
                url="https://example.com/advanced-python",
                content="Master advanced Python concepts and patterns.",
                score=0.87,
                published_date="2024-02-20",
            ),
        ],
        usage=None,
    )


@pytest.fixture
def brave_backend():
    """Create BraveBackend instance for testing."""
    return BraveBackend(api_key="test_api_key")


class TestBraveBackend:
    """Test BraveBackend implementation."""

    def test_name_property(self, brave_backend):
        """Test provider name property."""
        assert brave_backend.name == "brave"

    def test_requires_api_key(self, brave_backend):
        """Test that provider requires API key."""
        assert brave_backend.requires_api_key is True

    def test_api_key_env_var(self, brave_backend):
        """Test API key environment variable name."""
        assert brave_backend.api_key_env_var == "BRAVE_API_KEY"

    def test_initialization_with_api_key(self):
        """Test initialization with explicit API key."""
        backend = BraveBackend(api_key="explicit_key")
        assert backend._api_key == "explicit_key"

    def test_initialization_without_api_key(self, monkeypatch):
        """Test initialization reads from environment variable."""
        monkeypatch.setenv("BRAVE_API_KEY", "env_key")
        backend = BraveBackend()
        assert backend._api_key == "env_key"

    @pytest.mark.asyncio
    async def test_search_success(self, brave_backend, mock_brave_response):
        """Test successful search returns formatted results."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_brave_response

        brave_backend._client = mock_client

        results = await brave_backend.search("python programming")

        assert len(results) == 2
        assert results[0]["title"] == "Python Programming Guide"
        assert results[0]["url"] == "https://example.com/python"
        assert results[0]["content"] == "Learn Python programming from basics to advanced."
        assert results[0]["score"] >= 0.0
        assert results[0]["metadata"]["source"] == "brave"
        assert "published_date" in results[0]["metadata"]

    @pytest.mark.asyncio
    async def test_search_max_results_parameter(self, brave_backend):
        """Test that max_results parameter is respected."""
        mock_client = AsyncMock()
        mock_response = BraveSearchResponse(
            query="test",
            results=[
                BraveSearchResult(
                    title=f"Result {i}",
                    url=f"https://example.com/{i}",
                    content=f"Content {i}",
                )
                for i in range(5)
            ],
        )
        mock_client.search.return_value = mock_response
        brave_backend._client = mock_client

        results = await brave_backend.search("test", max_results=5)

        assert len(results) == 5
        mock_client.search.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_timeout_parameter(self, brave_backend, mock_brave_response):
        """Test that timeout parameter is passed correctly."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_brave_response
        brave_backend._client = mock_client

        await brave_backend.search("test", timeout=10.0)

        # Verify timeout was passed to client
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs.get("timeout") == 10.0

    @pytest.mark.asyncio
    async def test_search_empty_response(self, brave_backend):
        """Test search with empty results."""
        mock_client = AsyncMock()
        mock_client.search.return_value = BraveSearchResponse(
            query="nonexistent query",
            results=[],
        )
        brave_backend._client = mock_client

        results = await brave_backend.search("nonexistent query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_api_error_graceful_degradation(self, brave_backend):
        """Test that API errors return empty list (graceful degradation)."""
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("API Error")
        brave_backend._client = mock_client

        results = await brave_backend.search("test query")

        assert results == []

    @pytest.mark.asyncio
    async def test_search_missing_api_key_raises_value_error(self, monkeypatch):
        """Test that missing API key raises ValueError."""
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        backend = BraveBackend(api_key=None)

        with pytest.raises(ValueError, match="API key is required"):
            await backend.search("test query")

    @pytest.mark.asyncio
    async def test_close(self, brave_backend):
        """Test closing the client connection."""
        mock_client = AsyncMock()
        mock_client.close = AsyncMock()
        brave_backend._client = mock_client

        await brave_backend.close()

        mock_client.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_without_client(self, brave_backend):
        """Test close when client is not initialized."""
        # Should not raise any error
        await brave_backend.close()

    def test_validate_api_key_with_valid_key(self, brave_backend, monkeypatch):
        """Test API key validation with valid key."""
        monkeypatch.setenv("BRAVE_API_KEY", "test_key")
        backend = BraveBackend(api_key="test_key")
        assert backend.validate_api_key() is True

    def test_validate_api_key_with_missing_key(self, monkeypatch):
        """Test API key validation with missing key."""
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        backend = BraveBackend(api_key=None)

        assert backend.validate_api_key() is False

    def test_is_available_with_api_key(self, brave_backend, monkeypatch):
        """Test is_available returns True when API key is configured."""
        monkeypatch.setenv("BRAVE_API_KEY", "test_api_key")
        backend = BraveBackend(api_key="test_api_key")
        assert backend.is_available() is True

    def test_is_available_without_api_key(self, monkeypatch):
        """Test is_available returns False when API key is missing."""
        monkeypatch.delenv("BRAVE_API_KEY", raising=False)
        backend = BraveBackend(api_key=None)

        assert backend.is_available() is False

    @pytest.mark.asyncio
    async def test_search_result_format(self, brave_backend, mock_brave_response):
        """Test that search results match standard format."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_brave_response
        brave_backend._client = mock_client

        results = await brave_backend.search("python")

        for result in results:
            assert "title" in result
            assert "url" in result
            assert "content" in result
            assert "score" in result
            assert "metadata" in result
            assert isinstance(result["score"], (int, float))
            assert isinstance(result["metadata"], dict)

    @pytest.mark.asyncio
    async def test_search_preserves_metadata(self, brave_backend, mock_brave_response):
        """Test that provider-specific metadata is preserved."""
        mock_client = AsyncMock()
        mock_client.search.return_value = mock_brave_response
        brave_backend._client = mock_client

        results = await brave_backend.search("python")

        assert results[0]["metadata"]["source"] == "brave"
        assert "published_date" in results[0]["metadata"]
