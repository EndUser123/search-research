"""Z.ai web search provider via web_search_prime MCP endpoint.

Uses the Z.ai Coding Plan's remote MCP web_search_prime tool.
Requires ZAI_API_KEY (Coding Plan subscription).
"""

import asyncio
import json
import logging
import os

from .base_web import BaseWebBackend

logger = logging.getLogger(__name__)

# Z.ai returns double-JSON-encoded results: a JSON string whose value
# is a bare JSON array of {title, link, content, refer}.
_ZAI_URL = "https://api.z.ai/api/mcp/web_search_prime/mcp"
_ZAI_TOOL = "web_search_prime"


def _extract_results(content_text: str) -> list[dict]:
    """Parse z.ai double-JSON response into result dicts."""
    data = None
    try:
        data = json.loads(content_text)
        while isinstance(data, str):
            data = json.loads(data)
    except (ValueError, TypeError):
        return []

    items = []
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        for k in ("organic", "results", "web_results", "data"):
            v = data.get(k)
            if isinstance(v, list):
                items = v
                break

    return items


class ZAIBackend(BaseWebBackend):
    """Z.ai search provider using web_search_prime MCP endpoint.

    Features:
    - Uses Z.ai's own grounded web search
    - Returns structured results with content
    - Requires Coding Plan subscription (ZAI_API_KEY)
    - 2-5s response time

    Usage:
        backend = ZAIBackend()
        results = await backend.search("Python async programming", max_results=10)
    """

    @property
    def name(self) -> str:
        return "zai"

    @property
    def requires_api_key(self) -> bool:
        return True

    @property
    def api_key_env_var(self) -> str:
        return "ZAI_API_KEY"

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self._api_key: str | None = (
            os.getenv("ZAI_API_KEY")
            or os.getenv("ZHIPU_API_KEY")
            or os.getenv("GLM_API_KEY")
        )

    def is_available(self) -> bool:
        if not self._api_key:
            logger.debug("ZAI_API_KEY not set (z.ai Coding Plan required)")
            return False
        try:
            from mcp.client.streamable_http import streamablehttp_client  # noqa: F401
            return True
        except ImportError:
            logger.debug("mcp SDK not installed — z.ai backend unavailable")
            return False

    async def search(
        self,
        query: str,
        max_results: int = 10,
        timeout: float = 10.0,
        **kwargs,
    ) -> list[dict]:
        if not self.is_available():
            return []

        try:
            from mcp import ClientSession
            from mcp.client.streamable_http import streamablehttp_client

            headers = {"Authorization": f"Bearer {self._api_key}"}

            async with streamablehttp_client(_ZAI_URL, headers=headers) as (read, write, _):
                async with ClientSession(read, write) as session:
                    await session.initialize()
                    res = await session.call_tool(
                        _ZAI_TOOL,
                        {"search_query": query, "content_size": "high"},
                    )

            txt = getattr(res.content[0], "text", "") if res.content else ""
            raw_items = _extract_results(txt)

            results = []
            for item in raw_items[:max_results]:
                results.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "content": item.get("content", ""),
                    "score": 0.5,
                    "metadata": {"source": self.name},
                })

            return results

        except asyncio.TimeoutError:
            logger.debug(f"z.ai search timed out after {timeout}s")
            return []
        except Exception as e:
            logger.error(f"z.ai search failed: {e}")
            return []

    async def close(self):
        pass
