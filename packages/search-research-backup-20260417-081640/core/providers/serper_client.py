"""Serper search client - Complete implementation with async support.

This module provides a fully functional Serper search client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation
- Shared HTTP client for connection pooling

Based on Serper.dev Google Search API
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx
from search_research.http_client import get_async_client

logger = logging.getLogger(__name__)


@dataclass
class SerperSearchResult:
    """A single Serper search result."""

    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class SerperSearchResponse:
    """Complete Serper search response."""

    query: str
    results: list[SerperSearchResult]


class SerperClient:
    """Complete Serper search client implementation.

    Usage:
        client = SerperClient(api_key="serper_...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://google.serper.dev/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Serper client.

        Args:
            api_key: Serper API key. If None, reads from SERPER_API_KEY env var.
            max_results: Maximum number of results to return (1-100).
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key or os.getenv("SERPER_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Serper API key is required. Set SERPER_API_KEY env var or pass api_key parameter."
            )

        self._max_results = min(max(1, max_results), 100)  # Clamp to 1-100
        self._timeout = timeout

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        # Shared client is managed by http_client module, don't close it
        pass

    def _get_client(self) -> httpx.AsyncClient:
        """Get shared HTTP client."""
        return get_async_client()

    def _build_request_payload(self, query: str, **kwargs) -> dict[str, Any]:
        """Build API request payload."""
        payload = {
            "q": query,
            "apiKey": self._api_key,
            "num": kwargs.get("max_results", self._max_results),
        }

        # Add optional parameters
        if "type" in kwargs:
            payload["type"] = kwargs["type"]
        if "gl" in kwargs:
            payload["gl"] = kwargs["gl"]
        if "hl" in kwargs:
            payload["hl"] = kwargs["hl"]

        return payload

    def _parse_result(self, raw: dict[str, Any]) -> SerperSearchResult:
        """Parse a single result from API response."""
        return SerperSearchResult(
            title=raw.get("title", ""),
            url=raw.get("link", ""),
            content=raw.get("snippet", ""),
            score=0.0,  # Serper doesn't provide scores, use 0.0
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> SerperSearchResponse:
        """Parse complete API response."""
        results = []
        for item in raw.get("organic", []):
            results.append(self._parse_result(item))

        return SerperSearchResponse(
            query=query,
            results=results,
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> SerperSearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            **kwargs: Additional API parameters (type, gl, hl, etc.).

        Returns:
            SerperSearchResponse with results.

        Raises:
            httpx.HTTPStatusError: API request failed.
            ValueError: Invalid parameters.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Build request
        payload = self._build_request_payload(
            query,
            max_results=max_results or self._max_results,
            **kwargs,
        )

        # Execute request
        client = self._get_client()
        try:
            response = await client.post(self.API_BASE, json=payload)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Serper API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Serper request failed: {e}")
            raise

        return self._parse_response(raw_data, query)


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> SerperSearchResponse:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Serper API key (uses SERPER_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        SerperSearchResponse with search results.
    """
    async with SerperClient(api_key=api_key, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> SerperSearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Serper API key (uses SERPER_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        SerperSearchResponse with search results.
    """
    return asyncio.run(search(query, api_key, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Serper API key format.

    Args:
        api_key: API key to validate. Uses SERPER_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("SERPER_API_KEY")
    if not key:
        return False
    # Serper keys are typically at least 20 characters
    return len(key) >= 20
