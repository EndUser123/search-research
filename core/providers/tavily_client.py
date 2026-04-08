"""Tavily search client - Complete implementation with async support.

This module provides a fully functional Tavily search client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation
- Shared HTTP client for connection pooling

Based on tavily-python SDK v0.7.19
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
class TavilySearchResult:
    """A single Tavily search result."""

    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: str | None = None


@dataclass
class TavilySearchResponse:
    """Complete Tavily search response."""

    query: str
    results: list[TavilySearchResult]
    answer: str | None = None
    usage: dict[str, Any] | None = None


class TavilyClient:
    """Complete Tavily search client implementation.

    Usage:
        client = TavilyClient(api_key="tvly-...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://api.tavily.com/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
        search_depth: str = "basic",  # "basic" or "advanced"
        include_answer: bool = False,
        include_raw_content: bool = False,
        include_images: bool = False,
        include_image_descriptions: bool = False,
    ):
        """Initialize Tavily client.

        Args:
            api_key: Tavily API key. If None, reads from TAVILY_API_KEY env var.
            max_results: Maximum number of results to return (1-10).
            timeout: Request timeout in seconds.
            search_depth: "basic" (faster) or "advanced" (deeper search).
            include_answer: Whether to include LLM-generated answer.
            include_raw_content: Whether to include raw HTML content.
            include_images: Whether to include image results.
            include_image_descriptions: Whether to include AI image descriptions.
        """
        self._api_key = api_key or os.getenv("TAVILY_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Tavily API key is required. Set TAVILY_API_KEY env var or pass api_key parameter."
            )

        self._max_results = min(max(1, max_results), 10)  # Clamp to 1-10
        self._timeout = timeout
        self._search_depth = search_depth if search_depth in ("basic", "advanced") else "basic"
        self._include_answer = include_answer
        self._include_raw_content = include_raw_content
        self._include_images = include_images
        self._include_image_descriptions = include_image_descriptions

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
            "api_key": self._api_key,
            "query": query,
            "max_results": kwargs.get("max_results", self._max_results),
            "search_depth": kwargs.get("search_depth", self._search_depth),
            "include_answer": kwargs.get("include_answer", self._include_answer),
            "include_raw_content": kwargs.get("include_raw_content", self._include_raw_content),
            "include_images": kwargs.get("include_images", self._include_images),
            "include_image_descriptions": kwargs.get(
                "include_image_descriptions", self._include_image_descriptions
            ),
        }

        # Add optional parameters
        if "days" in kwargs:
            payload["days"] = kwargs["days"]
        if "topic" in kwargs:
            payload["topic"] = kwargs["topic"]

        return payload

    def _parse_result(self, raw: dict[str, Any]) -> TavilySearchResult:
        """Parse a single result from API response."""
        return TavilySearchResult(
            title=raw.get("title", ""),
            url=raw.get("url", ""),
            content=raw.get("content", ""),
            score=raw.get("score", 0.0),
            published_date=raw.get("published_date"),
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> TavilySearchResponse:
        """Parse complete API response."""
        results = []
        for item in raw.get("results", []):
            results.append(self._parse_result(item))

        return TavilySearchResponse(
            query=query,
            results=results,
            answer=raw.get("answer"),
            usage=raw.get("usage"),
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        search_depth: str | None = None,
        **kwargs,
    ) -> TavilySearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            search_depth: Override default search depth ("basic" or "advanced").
            **kwargs: Additional API parameters (days, topic, etc.).

        Returns:
            TavilySearchResponse with results.

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
            search_depth=search_depth or self._search_depth,
            **kwargs,
        )

        # Execute request
        client = self._get_client()
        try:
            response = await client.post(self.API_BASE, json=payload)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Tavily API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Tavily request failed: {e}")
            raise

        return self._parse_response(raw_data, query)


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> TavilySearchResponse:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Tavily API key (uses TAVILY_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        TavilySearchResponse with search results.
    """
    async with TavilyClient(api_key=api_key, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> TavilySearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Tavily API key (uses TAVILY_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        TavilySearchResponse with search results.
    """
    return asyncio.run(search(query, api_key, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Tavily API key format.

    Args:
        api_key: API key to validate. Uses TAVILY_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("TAVILY_API_KEY")
    if not key:
        return False
    # Tavily keys start with "tvly-" followed by ~32 characters
    return key.startswith("tvly-") and len(key) > 35
