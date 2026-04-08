"""Unit tests for ExaBackend provider.

Tests use mocked responses to verify correct behavior without requiring API access.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from core.providers.exa import ExaBackend


class TestExaBackendInitialization:
    """Tests for ExaBackend initialization."""

    def test_backend_name(self):
        """Test backend name is 'exa'."""
        backend = ExaBackend(api_key="test_key")
        assert backend.name == "exa"

    def test_requires_api_key(self):
        """Test that backend requires API key."""
        backend = ExaBackend(api_key="test_key")
        assert backend.requires_api_key is True

    def test_api_key_env_var(self):
        """Test API key environment variable name."""
        backend = ExaBackend(api_key="test_key")
        assert backend.api_key_env_var == "EXA_API_KEY"

    def test_api_key_from_param(self):
        """Test API key from parameter."""
        backend = ExaBackend(api_key="test_key_123")
        assert backend._api_key == "test_key_123"

    def test_max_results_default(self):
        """Test default max_results value."""
        backend = ExaBackend(api_key="test_key")
        assert backend.max_results == 10

    def test_max_results_custom(self):
        """Test custom max_results value."""
        backend = ExaBackend(api_key="test_key", max_results=5)
        assert backend.max_results == 5


class TestExaBackendValidateApiKey:
    """Tests for API key validation."""

    def test_validate_api_key_missing(self, caplog):
        """Test validation fails when API key is missing."""
        backend = ExaBackend(api_key=None)
        assert backend.validate_api_key() is False

    def test_validate_api_key_present(self):
        """Test validation succeeds when API key is present."""
        with patch.dict("os.environ", {"EXA_API_KEY": "test_key"}):
            backend = ExaBackend(api_key="test_key")
            assert backend.validate_api_key() is True

    def test_validate_api_key_logs_warning(self, caplog):
        """Test that missing API key logs warning."""
        import logging

        backend = ExaBackend(api_key=None)
        with caplog.at_level(logging.WARNING):
            backend.validate_api_key()

        assert any("EXA_API_KEY" in record.message for record in caplog.records)


class TestExaBackendIsAvailable:
    """Tests for is_available method."""

    def test_is_available_with_api_key(self):
        """Test is_available returns True when API key is set."""
        backend = ExaBackend(api_key="test_key")
        assert backend.is_available() is True

    def test_is_available_without_api_key(self):
        """Test is_available returns False when API key is missing."""
        backend = ExaBackend(api_key=None)
        assert backend.is_available() is False


class TestExaBackendSearch:
    """Tests for search method."""

    @pytest.mark.asyncio
    async def test_search_returns_empty_list_when_no_api_key(self):
        """Test search returns empty list when API key is not configured."""
        backend = ExaBackend(api_key=None)
        results = await backend.search("test query")
        assert results == []

    @pytest.mark.asyncio
    async def test_search_returns_results(self):
        """Test search returns formatted results."""
        backend = ExaBackend(api_key="test_key")

        # Mock the client
        mock_response = MagicMock()
        mock_response.results = [
            MagicMock(title="Test Title 1", url="https://example.com/1", score=0.9),
            MagicMock(title="Test Title 2", url="https://example.com/2", score=0.8),
        ]

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            results = await backend.search("test query", max_results=5)

        assert len(results) == 2
        assert results[0]["title"] == "Test Title 1"
        assert results[0]["url"] == "https://example.com/1"
        assert results[0]["score"] == 0.9
        assert results[0]["metadata"]["source"] == "exa"

    @pytest.mark.asyncio
    async def test_search_handles_exception_gracefully(self, caplog):
        """Test search returns empty list on exception."""
        import logging

        backend = ExaBackend(api_key="test_key")

        # Mock client that raises exception
        mock_client = AsyncMock()
        mock_client.search.side_effect = Exception("API error")

        with patch.object(backend, "_get_client", return_value=mock_client):
            with caplog.at_level(logging.ERROR):
                results = await backend.search("test query")

        assert results == []
        assert any("Exa search failed" in record.message for record in caplog.records)

    @pytest.mark.asyncio
    async def test_search_passes_max_results(self):
        """Test search passes max_results to client."""
        backend = ExaBackend(api_key="test_key", max_results=10)

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search("test query", max_results=5)

        # Verify max_results was passed correctly
        mock_client.search.assert_called_once()
        call_args = mock_client.search.call_args
        # Positional arg 0 is query, keyword arg max_results should be 5
        assert call_args[1].get("max_results") == 5

    @pytest.mark.asyncio
    async def test_search_with_kwargs(self):
        """Test search passes additional kwargs to client."""
        backend = ExaBackend(api_key="test_key")

        mock_response = MagicMock()
        mock_response.results = []

        mock_client = AsyncMock()
        mock_client.search.return_value = mock_response

        with patch.object(backend, "_get_client", return_value=mock_client):
            await backend.search(
                "test query",
                include_domains=["example.com"],
                exclude_domains=["spam.com"],
            )

        # Verify kwargs were passed
        call_kwargs = mock_client.search.call_args[1]
        assert call_kwargs.get("include_domains") == ["example.com"]
        assert call_kwargs.get("exclude_domains") == ["spam.com"]


class TestExaBackendClose:
    """Tests for close method."""

    @pytest.mark.asyncio
    async def test_close_without_client(self):
        """Test close when client is not initialized."""
        backend = ExaBackend(api_key="test_key")
        # Should not raise exception
        await backend.close()

    @pytest.mark.asyncio
    async def test_close_with_client(self):
        """Test close closes the underlying client."""
        backend = ExaBackend(api_key="test_key")

        mock_client = AsyncMock()
        backend._client = mock_client

        await backend.close()

        mock_client.close.assert_called_once()
        assert backend._client is None
