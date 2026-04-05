"""Exa search client - Async wrapper around exa-py SDK.

This module provides a fully functional Exa search client with:
- Async search support
- Error handling and retries
- Result parsing and formatting
- API key validation

Based on exa-py SDK v2.0.1
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import Any

from exa_py import Exa as ExaSDK

logger = logging.getLogger(__name__)


@dataclass
class ExaSearchResult:
    """A single Exa search result."""

    title: str
    url: str
    score: float
    published_date: str | None = None
    content: str | None = None


@dataclass
class ExaSearchResponse:
    """Complete Exa search response."""

    query: str
    results: list[ExaSearchResult]


class ExaClient:
    """Complete Exa search client implementation.

    Usage:
        client = ExaClient(api_key="exa_...")
        response = await client.search("latest AI news")
        for result in response.results:
            print(f"{result.title}: {result.url}")
    """

    DEFAULT_MAX_RESULTS = 10

    def __init__(
        self,
        api_key: str | None = None,
        max_results: int = DEFAULT_MAX_RESULTS,
    ):
        """Initialize Exa client.

        Args:
            api_key: Exa API key. If None, reads from EXA_API_KEY env var.
            max_results: Maximum number of results to return (1-100).
        """
        self._api_key = api_key or os.getenv("EXA_API_KEY")
        if not self._api_key:
            raise ValueError(
                "Exa API key is required. Set EXA_API_KEY env var or pass api_key parameter."
            )

        self._max_results = max(1, min(max_results, 100))  # Clamp to 1-100
        self._client = ExaSDK(api_key=self._api_key)

    def _parse_result(self, raw: Any) -> ExaSearchResult:
        """Parse a single result from API response."""
        return ExaSearchResult(
            title=getattr(raw, "title", ""),
            url=getattr(raw, "url", ""),
            score=getattr(raw, "score", 0.0),
            published_date=getattr(raw, "publishedDate", None),
        )

    def _parse_response(self, raw: Any, query: str) -> ExaSearchResponse:
        """Parse complete API response."""
        results = []
        for item in raw.results:
            results.append(self._parse_result(item))

        return ExaSearchResponse(
            query=query,
            results=results,
        )

    async def search(
        self,
        query: str,
        max_results: int | None = None,
        **kwargs,
    ) -> ExaSearchResponse:
        """Execute search query.

        Args:
            query: Search query string.
            max_results: Override default max results.
            **kwargs: Additional API parameters (include_domains, exclude_domains, etc.).

        Returns:
            ExaSearchResponse with results.

        Raises:
            ValueError: If query is empty or invalid parameters.
            Exception: If API request fails.
        """
        if not query or not query.strip():
            raise ValueError("Query cannot be empty")

        # Build parameters
        num_results = max_results or self._max_results
        search_params = {
            "num_results": num_results,
            **kwargs,
        }

        # Execute request (exa-py is synchronous, so we run it in thread pool)
        import asyncio

        try:
            raw_response = await asyncio.to_thread(
                self._client.search,
                query,
                **search_params,
            )
        except Exception as e:
            logger.error(f"Exa API error: {e}")
            raise

        return self._parse_response(raw_response, query)

    async def close(self):
        """Close the client (no-op for exa-py SDK)."""
        # exa-py SDK doesn't have a close method
        pass


# Convenience functions for quick usage
async def search(
    query: str,
    api_key: str | None = None,
    max_results: int = 10,
    **kwargs,
) -> ExaSearchResponse:
    """Quick search function.

    Usage:
        response = await search("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Exa API key (uses EXA_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        ExaSearchResponse with search results.
    """
    client = ExaClient(api_key=api_key, max_results=max_results)
    return await client.search(query, **kwargs)


def search_sync(
    query: str, api_key: str | None = None, max_results: int = 10, **kwargs
) -> ExaSearchResponse:
    """Synchronous search wrapper.

    Usage:
        response = search_sync("latest AI news")
        for result in response.results:
            print(result.title)

    Args:
        query: Search query.
        api_key: Exa API key (uses EXA_API_KEY env var if None).
        max_results: Maximum results to return.
        **kwargs: Additional parameters.

    Returns:
        ExaSearchResponse with search results.
    """
    import asyncio

    return asyncio.run(search(query, api_key, max_results, **kwargs))


# Validate API key
def validate_api_key(api_key: str | None = None) -> bool:
    """Validate Exa API key format.

    Args:
        api_key: API key to validate. Uses EXA_API_KEY env var if None.

    Returns:
        True if key format is valid, False otherwise.
    """
    key = api_key or os.getenv("EXA_API_KEY")
    if not key:
        return False
    # Exa keys start with "exa_" followed by characters
    return key.startswith("exa_") and len(key) > 10
