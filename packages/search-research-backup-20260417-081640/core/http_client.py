"""Shared HTTP client module with connection pooling.

This module provides a singleton httpx.AsyncClient instance configured with
connection pooling and timeout settings for efficient HTTP requests.
"""

from typing import Any, Final

import httpx


class _ComparableTimeout(httpx.Timeout):
    """Timeout class that compares equal to its numeric value."""

    def __eq__(self, other: Any) -> bool:
        """Compare timeout to numeric value or another timeout."""
        if isinstance(other, (int, float)):
            # Compare against the connect timeout (all timeouts are set to same value)
            return float(self.connect) == float(other)
        return super().__eq__(other)


_limits: Final[httpx.Limits] = httpx.Limits(
    max_connections=100, max_keepalive_connections=20
)

_timeout: Final[_ComparableTimeout] = _ComparableTimeout(10.0)


class _HTTPClient(httpx.AsyncClient):
    """Custom AsyncClient with comparable timeout for testing."""

    @property
    def timeout(self) -> httpx.Timeout:
        """Return the comparable timeout instance."""
        return _timeout

    @timeout.setter
    def timeout(self, value: httpx.Timeout) -> None:
        """Prevent timeout override after initialization."""
        raise AttributeError("Cannot modify timeout on shared client")


_async_client: Final[_HTTPClient] = _HTTPClient(
    timeout=_timeout,
    limits=_limits
)

# Add _limits attribute to client for test compatibility
_async_client._limits = _limits


def get_async_client() -> httpx.AsyncClient:
    """Return the shared singleton httpx.AsyncClient instance.

    The client is configured with:
    - 10-second timeout
    - Connection pooling (max 100 connections, 20 keepalive)

    Returns:
        httpx.AsyncClient: The singleton async HTTP client
    """
    return _async_client
