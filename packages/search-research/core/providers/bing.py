"""Bing search provider - Microsoft Bing Search API v7.

Complete implementation using bing_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .bing_client import BingClient as BingClientImpl

logger = logging.getLogger(__name__)


class BingBackend(BaseWebBackend):
    """Bing search provider using bing_client implementation.

    Features:
    - Web search with Microsoft Bing Search API v7
    - Async search support
    - API key authentication
    - Graceful error handling

    Usage:
        backend = BingBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "bing"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "BING_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize BingBackend.

        Args:
            api_key: Bing API key. If not provided, reads from BING_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = BingClientImpl(
                api_key=self._api_key,
                max_results=self.max_results,
            )
        return self._client

    def validate_api_key(self) -> bool:
        """Validate that API key is configured.

        Returns:
            True if API key is configured, False otherwise.
        """
        if not self._api_key:
            logger.warning(
                f"{self.name.upper()} provider requires {self.api_key_env_var} "
                f"environment variable or api_key parameter. Skipping {self.name} searches."
            )
            return False
        return True

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
            **kwargs: Additional search parameters.

        Returns:
            List of search result dictionaries with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet
                - score: Relevance score (0-1)
                - metadata: Provider-specific metadata

        Note: This method implements graceful degradation. It will return an
        empty list on any error rather than raising exceptions.
        """
        # Validate API key
        if not self.validate_api_key():
            return []

        try:
            client = self._get_client()
            response = await client.search(
                query,
                max_results=max_results or self.max_results,
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
                            "source": self.name,
                        },
                    }
                )

            return results

        except ValueError:
            # Re-raise ValueError for missing API key
            raise
        except Exception as e:
            logger.error(f"Bing search failed: {e}")
            # Graceful degradation: return empty list on any error
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
