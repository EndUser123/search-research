"""Serper search provider - Google Search API wrapper.

Complete implementation using serper_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .serper_client import SerperClient as SerperClientImpl

logger = logging.getLogger(__name__)


class SerperBackend(BaseWebBackend):
    """Serper search provider using serper_client implementation.

    Features:
    - Google Search API integration
    - Fast, accurate search results
    - API key authentication

    Usage:
        backend = SerperBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "serper"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "SERPER_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize SerperBackend.

        Args:
            api_key: Serper API key. If not provided, reads from SERPER_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def validate_api_key(self) -> bool:
        """Validate that API key is configured if required.

        Logs warning if API key is missing.

        Returns:
            True if API key is configured or not required, False otherwise
        """
        if not self.requires_api_key:
            return True

        # Check both instance _api_key and environment variable
        api_key = self._api_key or os.getenv(self.api_key_env_var)
        if not api_key:
            logger.warning(
                f"{self.name.upper()} provider requires {self.api_key_env_var} "
                f"environment variable. Skipping {self.name} searches."
            )
            return False

        return True

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = SerperClientImpl(
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
            **kwargs: Additional search parameters (type, gl, hl, etc.).

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
            logger.error(f"Serper search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
