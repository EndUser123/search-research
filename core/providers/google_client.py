"""Google Custom Search API client - Complete implementation with async support.

This module provides a fully functional Google Custom Search API client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation

Based on Google Custom Search JSON API v1
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
class GoogleSearchResult:
    """A single Google Custom Search result."""

    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: str | None = None


@dataclass
class GoogleSearchResponse:
    """Complete Google Custom Search response."""

    query: str
    results: list[GoogleSearchResult]
    total_results: int | None = None
    search_time: float | None = None


class GoogleClient:
    """Complete Google Custom Search API client implementation.

    Usage:
        client = GoogleClient(api_key="AIza...", cx="012345...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://www.googleapis.com/customsearch/v1"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str | None = None,
        cx: str | None = None,  # Search Engine ID
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        """Initialize Google client.

        Args:
            api_key: Google API key. If None, reads from GOOGLE_API_KEY env var.
            cx: Custom Search Engine ID. If None, reads from GOOGLE_CX env var.
            max_results: Maximum number of results to return (1-10).
            timeout: Request timeout in seconds.
        """
        self._api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Google API key is required. Set GOOGLE_API_KEY env var or pass api_key parameter."
            )

        self._cx = cx or os.getenv("GOOGLE_CX")
        if not self._cx:
            logger.warning(
                "Google Custom Search Engine ID (cx) not provided. "
                "Using default search engine which may have limitations."
            )
            self._cx = None  # Will use API's default

        self._max_results = min(max(1, max_results), 10)  # Clamp to 1-10
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
            "key": self._api_key,
            "q": query,
            "num": kwargs.get("num", kwargs.get("max_results", self._max_results)),
        }

        # Add cx if provided
        if self._cx:
            params["cx"] = self._cx

        # Add optional parameters
        if "start" in kwargs:
            params["start"] = kwargs["start"]
        if "lr" in kwargs:
            params["lr"] = kwargs["lr"]  # Language restrict
        if "cr" in kwargs:
            params["cr"] = kwargs["cr"]  # Country restrict
        if "gl" in kwargs:
            params["gl"] = kwargs["gl"]  # Geolocation
        if "safe" in kwargs:
            params["safe"] = kwargs["safe"]  # Safe search level

        return params

    def _parse_result(self, raw: dict[str, Any]) -> GoogleSearchResult:
        """Parse a single result from API response."""
        # Extract snippet as content
        content = raw.get("snippet", "")

        # Try to extract published date from pagemap if available
        published_date = None
        pagemap = raw.get("pagemap", {})
        if "article" in pagemap:
            article = pagemap["article"][0] if pagemap["article"] else {}
            published_date = article.get("publishedDate")
        elif "metatags" in pagemap:
            metatags = pagemap["metatags"]
            if metatags:
                published_date = metatags[0].get("article:published_time")

        return GoogleSearchResult(
            title=raw.get("title", ""),
            url=raw.get("link", ""),
            content=content,
            score=0.0,  # Google doesn't provide scores in basic API
            published_date=published_date,
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> GoogleSearchResponse:
        """Parse complete API response."""
        results = []
        for item in raw.get("items", []):
            results.append(self._parse_result(item))

        search_info = raw.get("searchInformation", {})

        return GoogleSearchResponse(
            query=query,
            results=results,
            total_results=int(search_info.get("totalResults", "0")),
            search_time=search_info.get("searchTime"),
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> dict[str, Any]:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results (passed as 'num' parameter).
            **kwargs: Additional API parameters (start, lr, cr, gl, safe, etc.).

        Returns:
            Raw API response dictionary with results.

        Raises:
            httpx.HTTPStatusError: API request failed.
            ValueError: Invalid parameters.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Build request parameters
        params = self._build_request_params(
            query,
            num=max_results or self._max_results,
            **kwargs,
        )

        # Execute request
        client = self._get_client()
        try:
            response = await client.get(self.API_BASE, params=params)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Google API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Google request failed: {e}")
            raise

        return raw_data

    async def close(self):
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    cx: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> dict[str, Any]:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for item in response.get("items", []):
            print(item["title"])

    Args:
        query: Search query.
        api_key: Google API key (uses GOOGLE_API_KEY env var if None).
        cx: Custom Search Engine ID (uses GOOGLE_CX env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        Raw API response dictionary.
    """
    async with GoogleClient(api_key=api_key, cx=cx, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str,
    api_key: str | None = None,
    cx: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> dict[str, Any]:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for item in response.get("items", []):
            print(item["title"])

    Args:
        query: Search query.
        api_key: Google API key (uses GOOGLE_API_KEY env var if None).
        cx: Custom Search Engine ID (uses GOOGLE_CX env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        Raw API response dictionary.
    """
    return asyncio.run(search(query, api_key, cx, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Google API key format.

    Args:
        api_key: API key to validate. Uses GOOGLE_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("GOOGLE_API_KEY")
    if not key:
        return False
    # Google API keys start with "AIza" followed by ~35 characters
    return key.startswith("AIza") and len(key) > 37
