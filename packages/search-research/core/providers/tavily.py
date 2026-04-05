"""Tavily search provider - AI-powered search with answer generation.

Complete implementation using tavily_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .tavily_client import TavilyClient as TavilyClientImpl

logger = logging.getLogger(__name__)


class TavilyBackend(BaseWebBackend):
    """Tavily search provider using tavily_client implementation.

    Features:
    - AI-powered search with answer generation
    - Advanced search depth options
    - Image search support
    - API key authentication

    Usage:
        backend = TavilyBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "tavily"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "TAVILY_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize TavilyBackend.

        Args:
            api_key: Tavily API key. If not provided, reads from TAVILY_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = TavilyClientImpl(
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
            **kwargs: Additional search parameters (search_depth, days, topic, etc.).

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
                search_depth=kwargs.get("search_depth"),
                days=kwargs.get("days"),
                topic=kwargs.get("topic"),
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

        except ValueError:
            # Re-raise ValueError for missing API key
            raise
        except Exception as e:
            logger.error(f"Tavily search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
