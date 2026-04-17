"""Mojeek search provider - Independent search engine.

Complete implementation using mojeek_client with async support.

Note: Mojeek does not currently offer a public API. This implementation
follows the standard search provider pattern and can be adapted when/if
Mojeek releases an API, or used as a template for web scraping integration.
"""

import logging
import os

from .base_web import BaseWebBackend
from .mojeek_client import MojeekClient as MojeekClientImpl

logger = logging.getLogger(__name__)


class MojeekBackend(BaseWebBackend):
    """Mojeek search provider using mojeek_client implementation.

    Note: Mojeek does not currently offer a public API. This provider
    follows the standard search provider pattern for future compatibility.

    Features:
    - Independent search engine
    - Privacy-focused search
    - API key authentication (when available)

    Usage:
        backend = MojeekBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "mojeek"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "MOJEEK_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize MojeekBackend.

        Args:
            api_key: Mojeek API key. If not provided, reads from MOJEEK_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = MojeekClientImpl(
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
            **kwargs: Additional search parameters.

        Returns:
            List of search result dictionaries with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet
                - score: Relevance score (0-1)
                - metadata: Provider-specific metadata

        Note: Returns empty list on error (graceful degradation).
        """
        if not self.validate_api_key():
            return []

        try:
            client = self._get_client()
            response = await client.search(
                query,
                max_results=max_results or self.max_results,
                timeout=timeout,
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
            logger.error(f"Mojeek search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
            self._client = None
