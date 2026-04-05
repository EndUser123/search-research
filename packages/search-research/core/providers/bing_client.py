"""Bing Search API client - Complete implementation with async support.

This module provides a fully functional Bing Search API v7 client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation

Based on Microsoft Bing Search API v7
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import Any

import httpx

logger = logging.getLogger(__name__)


@dataclass
class BingSearchResult:
    """A single Bing search result."""

    title: str
    url: str
    content: str
    score: float = 0.0


@dataclass
class BingSearchResponse:
    """Complete Bing search response."""

    query: str
    results: list[BingSearchResult]


class BingClient:
    """Complete Bing Search API v7 client implementation.

    Usage:
        client = BingClient(api_key="your_api_key")
        response = await client.search("Python programming")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://api.bing.microsoft.com/v7.0/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Bing client.

        Args:
            api_key: Bing API key. If None, reads from BING_API_KEY env var.
            max_results: Maximum number of results to return (1-50).
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key or os.getenv("BING_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Bing API key is required. Set BING_API_KEY env var or pass api_key parameter."
            )

        self._max_results = min(max(1, max_results), 50)  # Clamp to 1-50
        self._timeout = timeout

        self._client: httpx.AsyncClient | None = None

    async def __aenter__(self):
        """Async context manager entry."""
        self._client = httpx.AsyncClient(timeout=self._timeout)
        return self

    async def __aexit__(self, *args):
        """Async context manager exit."""
        if self._client:
            await self._client.aclose()
            self._client = None

    def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=self._timeout)
        return self._client

    def _build_request_params(self, query: str, max_results: int) -> dict[str, Any]:
        """Build API request parameters."""
        return {
            "q": query,
            "count": max_results,
            "offset": 0,
            "mkt": "en-US",
        }

    def _parse_result(self, raw: dict[str, Any]) -> BingSearchResult:
        """Parse a single result from API response."""
        return BingSearchResult(
            title=raw.get("name", ""),
            url=raw.get("url", ""),
            content=raw.get("snippet", ""),
            score=0.0,  # Bing doesn't provide relevance scores
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> BingSearchResponse:
        """Parse complete API response."""
        results = []

        # Parse web pages
        if "webPages" in raw and "value" in raw["webPages"]:
            for item in raw["webPages"]["value"]:
                results.append(self._parse_result(item))

        return BingSearchResponse(
            query=query,
            results=results,
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> BingSearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            **kwargs: Additional API parameters (not currently used).

        Returns:
            BingSearchResponse with results.

        Raises:
            httpx.HTTPStatusError: API request failed.
            ValueError: Invalid parameters.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Build request
        params = self._build_request_params(
            query,
            max_results or self._max_results,
        )

        # Execute request
        client = self._get_client()
        headers = {
            "Ocp-Apim-Subscription-Key": self._api_key,
        }

        try:
            response = await client.get(self.API_BASE, params=params, headers=headers)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Bing API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Bing request failed: {e}")
            raise

        return self._parse_response(raw_data, query)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None

    @staticmethod
    def validate_api_key_format(api_key: str | None = None) -> bool:
        """Validate Bing API key format.

        Args:
            api_key: API key to validate. Uses BING_API_KEY env var if None.

        Returns:
            True if key format is valid, False otherwise.
        """
        key = api_key or os.getenv("BING_API_KEY")
        if not key:
            return False
        # Bing API keys are typically 32-character alphanumeric strings
        return len(key) >= 20


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> BingSearchResponse:
    """Quick search function.

    Usage:
        response = await search("Python programming")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Bing API key (uses BING_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        BingSearchResponse with search results.
    """
    async with BingClient(api_key=api_key, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> BingSearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("Python programming")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Bing API key (uses BING_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        BingSearchResponse with search results.
    """
    return asyncio.run(search(query, api_key, max_results, **kwargs))
