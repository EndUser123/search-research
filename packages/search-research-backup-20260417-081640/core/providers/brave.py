"""Brave search provider - Privacy-focused search with independent index.

Complete implementation using brave_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .brave_client import BraveClient as BraveClientImpl

logger = logging.getLogger(__name__)


class BraveBackend(BaseWebBackend):
    """Brave search provider using brave_client implementation.

    Features:
    - Privacy-focused search with independent index
    - Fast, lightweight search results
    - API key authentication
    - Safesearch and freshness options

    Usage:
        backend = BraveBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "brave"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "BRAVE_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize BraveBackend.

        Args:
            api_key: Brave API key. If not provided, reads from BRAVE_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = BraveClientImpl(
                api_key=self._api_key,
                max_results=self.max_results,
            )
        return self._client

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 5.0,
        **kwargs,
    ) -> list[dict]:
        """Execute search and return results.

        Args:
            query: Search query.
            max_results: Maximum number of results to return.
            timeout: Request timeout in seconds.
            **kwargs: Additional search parameters (safesearch, freshness, etc.).

        Returns:
            List of search result dictionaries with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet
                - score: Relevance score (0-1)
                - metadata: Provider-specific metadata

        Raises:
            ValueError: If API key is not configured.
        """
        try:
            client = self._get_client()
            response = await client.search(
                query,
                max_results=max_results or self.max_results,
                timeout=timeout,
                safesearch=kwargs.get("safesearch"),
                freshness=kwargs.get("freshness"),
                result_filter=kwargs.get("result_filter"),
            )

            results = []
            for item in response.results:
                results.append(
                    {
                        "title": item.title,
                        "url": item.url,
                        "content": item.content,
                        "score": item.score,
                        "metadata": {
                            "published_date": item.published_date,
                            "source": self.name,
                        },
                    }
                )

            return results

        except ValueError as e:
            # Only re-raise ValueError for missing API key
            if "API key" in str(e):
                raise
            # Other ValueErrors (like empty query) should return empty results
            logger.debug(f"Brave search returned ValueError: {e}")
            return []
        except Exception as e:
            logger.error(f"Brave search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
