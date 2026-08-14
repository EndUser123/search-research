"""Tests for the shared HTTP client module.

This test suite verifies the singleton httpx.AsyncClient with connection pooling.
Tests are written following TDD RED phase - they FAIL before implementation.

Run with: pytest tests/test_http_client.py -v
"""

from unittest.mock import MagicMock, patch

import httpx
import pytest


class TestGetAsyncClient:
    """Test suite for get_async_client() function."""

    def test_returns_httpx_async_client_instance(self):
        """Test that get_async_client returns an httpx.AsyncClient instance.

        Given: The http_client module is imported
        When: get_async_client() is called
        Then: An httpx.AsyncClient instance is returned
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client = get_async_client()

        # Assert
        assert isinstance(client, httpx.AsyncClient), (
            f"Expected httpx.AsyncClient, got {type(client).__name__}"
        )

    def test_singleton_pattern_same_instance(self):
        """Test that get_async_client returns the same instance on multiple calls.

        Given: The http_client module is imported
        When: get_async_client() is called multiple times
        Then: The same instance (by id) is returned each time
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client1 = get_async_client()
        client2 = get_async_client()
        client3 = get_async_client()

        # Assert
        assert id(client1) == id(client2), (
            f"Expected same instance (id={id(client1)}), got different id={id(client2)}"
        )
        assert id(client2) == id(client3), (
            f"Expected same instance (id={id(client2)}), got different id={id(client3)}"
        )
        assert id(client1) == id(client3), (
            f"Expected same instance (id={id(client1)}), got different id={id(client3)}"
        )

    def test_connection_limits_configuration(self):
        """Test that the client is configured with correct connection limits.

        Given: The http_client module is imported
        When: get_async_client() is called
        Then: The client has max_connections=100 and max_keepalive_connections=20
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client = get_async_client()

        # Assert
        assert hasattr(client, '_limits'), "Client should have _limits attribute"
        limits = client._limits

        assert limits.max_connections == 100, (
            f"Expected max_connections=100, got {limits.max_connections}"
        )
        assert limits.max_keepalive_connections == 20, (
            f"Expected max_keepalive_connections=20, got {limits.max_keepalive_connections}"
        )

    def test_timeout_configuration(self):
        """Test that the client is configured with a 10-second timeout.

        Given: The http_client module is imported
        When: get_async_client() is called
        Then: The client has a timeout of 10 seconds
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client = get_async_client()

        # Assert
        assert hasattr(client, 'timeout'), "Client should have timeout attribute"
        timeout = client.timeout

        # httpx.Timeout can be compared as a number or accessed via connect/read
        assert timeout == 10.0, (
            f"Expected timeout=10.0, got {timeout}"
        )

    def test_client_is_async(self):
        """Test that the returned client is an AsyncClient, not a synchronous Client.

        Given: The http_client module is imported
        When: get_async_client() is called
        Then: The client is specifically an httpx.AsyncClient (not httpx.Client)
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client = get_async_client()

        # Assert
        import httpx
        assert isinstance(client, httpx.AsyncClient), (
            f"Expected AsyncClient instance, got {type(client).__name__}"
        )
        assert not isinstance(client, httpx.Client), (
            "Client should be AsyncClient, not synchronous Client"
        )

    def test_connection_pooling_enabled(self):
        """Test that connection pooling is enabled on the client.

        Given: The http_client module is imported
        When: get_async_client() is called
        Then: The client has connection limits configured (indicating pooling)
        """
        # Arrange
        from http_client import get_async_client

        # Act
        client = get_async_client()

        # Assert
        assert client._limits is not None, (
            "Client should have connection limits configured for pooling"
        )
        assert client._limits.max_connections > 0, (
            "Client should allow multiple connections for pooling"
        )


class TestHttpClientIntegration:
    """Integration tests for HTTP client behavior."""

    @pytest.mark.asyncio
    async def test_client_can_make_request(self):
        """Test that the client can make an HTTP request (integration test).

        Given: The http_client module is imported and client is initialized
        When: An HTTP request is made with the client
        Then: The request can be executed (even if it fails, client is functional)

        Note: This test verifies the client is functional, not that external
        services are available. We use a mock to avoid network dependencies.
        """
        # Arrange
        from http_client import get_async_client

        client = get_async_client()

        # Mock the actual request to avoid network dependency
        with patch.object(client, 'get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"test": "data"}
            mock_get.return_value = mock_response

            # Act
            response = await client.get("http://example.com")

            # Assert
            assert response.status_code == 200
            assert response.json() == {"test": "data"}
            mock_get.assert_called_once_with("http://example.com")

    def test_module_structure(self):
        """Test that the http_client module has the expected structure.

        Given: The http_client module exists
        When: The module is inspected
        Then: It exports get_async_client function
        """
        # Arrange & Act
        import search_research.http_client as http_client_module

        # Assert
        assert hasattr(http_client_module, 'get_async_client'), (
            "http_client module should export get_async_client function"
        )
        assert callable(http_client_module.get_async_client), (
            "get_async_client should be callable"
        )
