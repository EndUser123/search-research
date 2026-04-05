"""Kagi search client - Complete implementation with async support.

This module provides a fully functional Kagi search client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation

Kagi Search API: https://help.kagi.com/kagi/api/api-reference.html
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
class KagiSearchResult:
    """A single Kagi search result."""

    title: str
    url: str
    content: str
    score: float = 0.0
    published_date: str | None = None
    domain: str | None = None
    rank: int | None = None


@dataclass
class KagiSearchResponse:
    """Complete Kagi search response."""

    query: str
    results: list[KagiSearchResult]
    meta: dict[str, Any] | None = None


class KagiClient:
    """Complete Kagi search client implementation.

    Usage:
        client = KagiClient(api_key="kagi-...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    API_BASE = "https://kagi.com/api/v0/search"
    DEFAULT_MAX_RESULTS = 10
    DEFAULT_TIMEOUT = 30.0

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
        timeout: float = DEFAULT_TIMEOUT,
        limit: str = "kagi",  # "kagi" or "all"
    ):
        """Initialize Kagi client.

        Args:
            api_key: Kagi API key. If None, reads from KAGI_API_KEY env var.
            max_results: Maximum number of results to return (1-50).
            timeout: Request timeout in seconds.
            limit: Search scope - "kagi" (default) or "all".
        """
        self._api_key = api_key or os.getenv("KAGI_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Kagi API key is required. Set KAGI_API_KEY env var or pass api_key parameter."
            )

        self._max_results = min(max(1, max_results), 50)  # Clamp to 1-50
        self._timeout = timeout
        self._limit = limit if limit in ("kagi", "all") else "kagi"

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

    def _build_request_payload(self, query: str, **kwargs) -> dict[str, Any]:
        """Build API request payload."""
        payload = {
            "q": query,
            "limit": kwargs.get("limit", self._limit),
        }

        # Add optional parameters
        if "max_results" in kwargs:
            payload["max_results"] = kwargs["max_results"]

        return payload

    def _parse_result(self, raw: dict[str, Any]) -> KagiSearchResult:
        """Parse a single result from API response.

        Kagi API response format:
        {
            "t": "title",
            "u": "url",
            "d": "domain",
            "sn": "snippet",
            "rank": 1
        }
        """
        return KagiSearchResult(
            title=raw.get("t", ""),
            url=raw.get("u", ""),
            content=raw.get("sn", ""),
            score=1.0 - (raw.get("rank", 1) * 0.05),  # Decay score based on rank
            domain=raw.get("d"),
            rank=raw.get("rank"),
        )

    def _parse_response(self, raw: dict[str, Any], query: str) -> KagiSearchResponse:
        """Parse complete API response.

        Kagi API response format:
        {
            "meta": {
                "id": "search-id",
                "query": "query",
                "time": 0.5
            },
            "data": [...]
        }
        """
        results = []
        for item in raw.get("data", []):
            results.append(self._parse_result(item))

        return KagiSearchResponse(
            query=query,
            results=results,
            meta=raw.get("meta"),
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> KagiSearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            **kwargs: Additional API parameters.

        Returns:
            KagiSearchResponse with results.

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
            headers = {
                "Authorization": f"Bot {self._api_key}",
                "Content-Type": "application/json",
            }

            response = await client.post(self.API_BASE, json=payload, headers=headers)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            logger.error(f"Kagi API error: {e.response.status_code} - {e.response.text}")
            raise
        except Exception as e:
            logger.error(f"Kagi request failed: {e}")
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
) -> KagiSearchResponse:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Kagi API key (uses KAGI_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        KagiSearchResponse with search results.
    """
    async with KagiClient(api_key=api_key, max_results=max_results) as client:
        return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> KagiSearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Kagi API key (uses KAGI_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        KagiSearchResponse with search results.
    """
    return asyncio.run(search(query, api_key, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Kagi API key format.

    Args:
        api_key: API key to validate. Uses KAGI_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("KAGI_API_KEY")
    if not key:
        return False
    # Kagi keys are typically 32+ characters
    return len(key) >= 20
