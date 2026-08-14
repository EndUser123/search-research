"""DuckDuckGo search provider via ddgs library.

Free, no API key required. Aggregates results from DuckDuckGo.
"""

import asyncio
import logging

from .base_web import BaseWebBackend

logger = logging.getLogger(__name__)


class DDGsBackend(BaseWebBackend):
    """DuckDuckGo search provider using the ddgs library.

    Features:
    - Free, no API key required
    - Text, news, images, videos search
    - Privacy-respecting (DuckDuckGo)
    - 1-3s response time

    Usage:
        backend = DDGsBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        return "duckduckgo"

    @property
    def requires_api_key(self) -> bool:
        return False

    @property
    def api_key_env_var(self) -> str:
        return ""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self._available: bool | None = None

    def is_available(self) -> bool:
        if self._available is not None:
            return self._available
        try:
            from ddgs import DDGS  # noqa: F401
            self._available = True
        except ImportError:
            logger.debug("ddgs library not installed. pip install ddgs")
            self._available = False
        return self._available

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 8.0,
        **kwargs,
    ) -> list[dict]:
        if not self.is_available():
            return []

        try:
            from ddgs import DDGS

            def _sync_search():
                return DDGS().text(query, max_results=max_results or self.max_results)

            raw_results = await asyncio.wait_for(
                asyncio.to_thread(_sync_search),
                timeout=timeout,
            )

            results = []
            for item in raw_results or []:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("href", ""),
                    "content": item.get("body", ""),
                    "score": 0.5,
                    "metadata": {"source": self.name},
                })

            return results

        except asyncio.TimeoutError:
            logger.debug(f"DDGs search timed out after {timeout}s")
            return []
        except Exception as e:
            logger.error(f"DDGs search failed: {e}")
            return []

    async def close(self):
        pass
