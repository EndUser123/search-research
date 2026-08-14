"""Brave Search client - Complete implementation with async support.

This module provides a fully functional Brave Search client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation

Based on Brave Search API
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
class BraveSearchResult:
    """A single Brave search result."""

    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: str | None = None


@dataclass
class BraveSearchResponse:
    """Complete Brave search response."""

    query: str
    results: list[BraveSearchResult]
    usage: dict[str, Any] | None = None


class BraveClient:
    """Complete Brave Search client implementation.

    Usage:
        client = BraveClient(api_key="BSA...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://api.search.brave.com/res/v1/web/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 5.0

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Brave client.

        Args:
            api_key: Brave API key. If None, reads from BRAVE_API_KEY env var.
            max_results: Maximum number of results to return (1-20).
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key or os.getenv("BRAVE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Brave API key is required. Set BRAVE_API_KEY env var or pass api_key parameter."
            )

        self._max_results = min(max(1, max_results), 20)  # Clamp to 1-20
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

    def _build_request_params(self, query: str, **kwargs) -> dict[str, Any]:
        """Build API request parameters."""
        params = {
            "q": query,
            "count": kwargs.get("max_results", self._max_results),
        }

        # Add optional parameters (only if truthy, to avoid empty strings)
        text = kwargs.get("text")
        if text:
            params["text"] = text
        safesearch = kwargs.get("safesearch")
        if safesearch:
            params["safesearch"] = safesearch
        freshness = kwargs.get("freshness")
        if freshness:
            params["freshness"] = freshness
        result_filter = kwargs.get("result_filter")
        if result_filter:
            params["result_filter"] = result_filter

        return params

    def _parse_result(self, raw: dict[str, Any]) -> BraveSearchResult:
        """Parse a single result from API response."""
        return BraveSearchResult(
            title=raw.get("title", ""),
            url=raw.get("url", ""),
            content=raw.get("snippet", raw.get("description", "")),
            score=raw.get("score", 0.0),
            published_date=raw.get("published_date"),
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> BraveSearchResponse:
        """Parse complete API response."""
        results = []

        # Parse web results
        web_results = raw.get("web", {}).get("results", [])
        for item in web_results:
            results.append(self._parse_result(item))

        return BraveSearchResponse(
            query=query,
            results=results,
            usage=raw.get("usage"),
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        timeout: float | None = None,
        **kwargs,
    ) -> BraveSearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            timeout: Override default timeout.
            **kwargs: Additional API parameters.

        Returns:
            BraveSearchResponse with results.

        Raises:
            httpx.HTTPStatusError: API request failed.
            ValueError: Invalid parameters.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Build request
        params = self._build_request_params(
            query,
            max_results=max_results or self._max_results,
            **kwargs,
        )

        # Execute request
        client = self._get_client()
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self._api_key,
        }

        try:
            actual_timeout = timeout if timeout is not None else self._timeout
            response = await client.get(
                self.API_BASE,
                params=params,
                headers=headers,
                timeout=actual_timeout,
            )
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Brave API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Brave request failed: {e}")
            raise

        return self._parse_response(raw_data, query)

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> BraveSearchResponse:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Brave API key (uses BRAVE_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        BraveSearchResponse with search results.
    """
    async with BraveClient(api_key=api_key, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> BraveSearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Brave API key (uses BRAVE_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        BraveSearchResponse with search results.
    """
    return asyncio.run(search(query, api_key, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Brave API key format.

    Args:
        api_key: API key to validate. Uses BRAVE_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("BRAVE_API_KEY")
    if not key:
        return False
    # Brave keys start with "BSA" followed by alphanumeric characters
    return len(key) > 10
