"""Google search provider - Google Custom Search API.

Complete implementation using google_client with async support.
"""

import logging
import os

from .base_web import BaseWebBackend
from .google_client import GoogleClient as GoogleClientImpl

logger = logging.getLogger(__name__)


class GoogleBackend(BaseWebBackend):
    """Google search provider using google_client implementation.

    Features:
    - Google Custom Search JSON API integration
    - Async search support
    - Custom Search Engine ID support
    - API key authentication

    Usage:
        backend = GoogleBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        """Provider identifier."""
        return "google"

    @property
    def requires_api_key(self) -> bool:
        """Whether provider requires API key."""
        return True

    @property
    def api_key_env_var(self) -> str:
        """Environment variable name for API key."""
        return "GOOGLE_API_KEY"

    def __init__(self, api_key: str | None = None, max_results: int = 10):
        """Initialize GoogleBackend.

        Args:
            api_key: Google API key. If not provided, reads from GOOGLE_API_KEY env var.
            max_results: Maximum number of results to return.
        """
        self._api_key = api_key if api_key is not None else os.getenv(self.api_key_env_var)
        self.max_results = max_results
        self._client = None  # Lazy initialization

    def _get_client(self):
        """Get or create the client (lazy initialization)."""
        if self._client is None:
            self._client = GoogleClientImpl(
                api_key=self._api_key,
                max_results=self.max_results,
            )
        return self._client

    def validate_api_key(self) -> bool:
        """Validate that API key is configured.

        Overrides base class to check instance's _api_key attribute.

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
            **kwargs: Additional search parameters (cx, lr, cr, gl, safe, etc.).

        Returns:
            List of search result dictionaries with keys:
                - title: Result title
                - url: Result URL
                - content: Result content/snippet
                - score: Relevance score (0-1, always 0 for Google API)
                - metadata: Provider-specific metadata

        Note:
            Returns empty list on failure (never raises exceptions).
        """
        if not self.validate_api_key():
            return []

        try:
            client = self._get_client()
            response = await client.search(
                query,
                max_results=max_results or self.max_results,
                **kwargs,
            )

            # Parse raw API response
            results = []
            for item in response.get("items", []):
                # Extract published date from pagemap if available
                published_date = None
                pagemap = item.get("pagemap", {})
                if "article" in pagemap:
                    article = pagemap["article"][0] if pagemap["article"] else {}
                    published_date = article.get("publishedDate")
                elif "metatags" in pagemap:
                    metatags = pagemap["metatags"]
                    if metatags:
                        published_date = metatags[0].get("article:published_time")

                result_dict = {
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("snippet", ""),
                    "score": 0.0,  # Google API doesn't provide scores
                    "metadata": {
                        "published_date": published_date,
                        "source": self.name,
                    },
                }
                results.append(result_dict)

            return results

        except ValueError:
            # Re-raise ValueError for missing API key
            raise
        except Exception as e:
            logger.error(f"Google search failed: {e}")
            return []

    async def close(self):
        """Close the underlying client connection."""
        if self._client is not None:
            await self._client.close()
