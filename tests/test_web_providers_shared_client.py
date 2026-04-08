"""Tests for T-005: Verify web providers use shared HTTP client.

RED phase: Tests fail because providers still create new clients.
GREEN phase: Update providers to use get_async_client().
"""

from unittest.mock import MagicMock, patch

import pytest


class TestTavilyClientUsesSharedClient:
    """Test that TavilyClient uses shared HTTP client."""

    @pytest.mark.asyncio
    async def test_get_client_uses_shared_client(self):
        """Test that _get_client returns shared httpx.AsyncClient.

        Given: TavilyClient is initialized
        When: _get_client() is called
        Then: Returns the shared client from get_async_client()
        """
        # Arrange
        from http_client import get_async_client
        from providers.tavily_client import TavilyClient

        client = TavilyClient(api_key="test_key")

        # Act
        result = client._get_client()

        # Assert
        shared_client = get_async_client()
        assert result is shared_client, (
            "TavilyClient should use shared client, but got different instance"
        )

    @pytest.mark.asyncio
    async def test_context_manager_uses_shared_client(self):
        """Test that async context manager uses shared client.

        Given: TavilyClient is used as async context manager
        When: Entering context via __aenter__
        Then: Uses shared client from get_async_client()
        """
        # Arrange
        from http_client import get_async_client
        from providers.tavily_client import TavilyClient

        client = TavilyClient(api_key="test_key")

        # Act
        async with client as ctx:
            # Assert
            shared_client = get_async_client()
            assert ctx._client is shared_client, (
                "Context manager should use shared client"
            )

    @pytest.mark.asyncio
    async def test_does_not_create_new_client(self):
        """Test that TavilyClient does NOT create new httpx.AsyncClient.

        Given: TavilyClient is initialized
        When: Client is used
        Then: Should NOT call httpx.AsyncClient() constructor
        """
        # Arrange
        from providers.tavily_client import TavilyClient

        client = TavilyClient(api_key="test_key")

        # Act & Assert
        with patch("httpx.AsyncClient") as mock_async_client:
            mock_async_client.return_value = MagicMock()

            # This should NOT create a new client
            result = client._get_client()

            # Verify httpx.AsyncClient constructor was NOT called
            assert not mock_async_client.called, (
                "Should not create new httpx.AsyncClient instance"
            )


class TestSerperClientUsesSharedClient:
    """Test that SerperClient uses shared HTTP client."""

    @pytest.mark.asyncio
    async def test_get_client_uses_shared_client(self):
        """Test that _get_client returns shared httpx.AsyncClient.

        Given: SerperClient is initialized
        When: _get_client() is called
        Then: Returns the shared client from get_async_client()
        """
        # Arrange
        from http_client import get_async_client
        from providers.serper_client import SerperClient

        client = SerperClient(api_key="test_key")

        # Act
        result = client._get_client()

        # Assert
        shared_client = get_async_client()
        assert result is shared_client, (
            "SerperClient should use shared client"
        )


class TestProviderIntegration:
    """Integration tests for shared client usage across providers."""

    @pytest.mark.asyncio
    async def test_all_providers_use_same_shared_client(self):
        """Test that all web providers use the same shared client instance.

        Note: ExaClient is excluded because it uses the exa_py SDK which
        has its own internal HTTP client (likely with connection pooling).

        Given: Multiple provider clients are created
        When: Each provider gets its HTTP client
        Then: All providers return the same shared client instance
        """
        # Arrange
        from http_client import get_async_client
        from providers.serper_client import SerperClient
        from providers.tavily_client import TavilyClient

        tavily = TavilyClient(api_key="test_key")
        serper = SerperClient(api_key="test_key")

        # Act
        tavily_client = tavily._get_client()
        serper_client = serper._get_client()
        shared_client = get_async_client()

        # Assert
        assert tavily_client is shared_client, "Tavily should use shared client"
        assert serper_client is shared_client, "Serper should use shared client"
        assert tavily_client is serper_client, (
            "All providers should use the same shared client instance"
        )
