"""Exa search provider - Semantic search for research.

Complete implementation using exa_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .exa_client import ExaClient as ExaClientImpl

logger = logging.getLogger(__name__)


class ExaBackend(BaseWebBackend):
    """Exa search provider using exa_client implementation.

    Features:
    - Semantic search with AI-powered understanding
    - Advanced filtering options (domains, dates, etc.)
    - API key authentication
    - Graceful degradation on errors

    Usage:
        backend = ExaBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "exa"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "EXA_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize ExaBackend.

        Args:
            api_key: Exa API key. If not provided, reads from EXA_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = ExaClientImpl(
                api_key=self._api_key,
                max_results=self.max_results,
            )
        return self._client

    def validate_api_key(self) -> bool:
        """Validate that API key is configured.

        Checks both the instance variable and environment variable.

        Returns:
            True if API key is configured, False otherwise
        """
        if self._api_key:
            return True
        return super().validate_api_key()

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
            timeout: Request timeout in seconds (not used directly, handled by SDK).
            **kwargs: Additional search parameters (include_domains, exclude_domains, etc.).

        Returns:
            List of search result dictionaries with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet (empty for Exa)
                - score: Relevance score (0-1)
                - metadata: Provider-specific metadata

        Note: Returns empty list on failure (graceful degradation).
        """
        try:
            if not self.validate_api_key():
                return []

            client = self._get_client()
            response = await client.search(
                query,
                max_results=max_results or self.max_results,
                **kwargs,
            )

            results = []
            for item in response.results:
                results.append(
                    {
                        "title": item.title,
                        "url": item.url,
                        "content": item.content or "",
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
            logger.debug(f"Exa search returned ValueError: {e}")
            return []
        except Exception as e:
            logger.error(f"Exa search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
