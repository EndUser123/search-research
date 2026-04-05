"""
Research Router - Example usage of AsyncMetaRouter for external APIs.

This demonstrates how to subclass AsyncMetaRouter for research queries
that call multiple external APIs in parallel.
"""

import asyncio
from typing import Any

from yt_fts.core_utils import (
    AsyncMetaRouter,
    ProviderConfig,
    ProviderResult,
    RoutingStrategy,
)


class ResearchRouter(AsyncMetaRouter):
    """Routes research queries to multiple external APIs.

    Supported providers:
    - wikipedia: Wikipedia API
    - arxiv: arXiv API
    - semantic_scholar: Semantic Scholar API
    """

    def __init__(self, **kwargs):
        providers = [
            ProviderConfig(name="wikipedia", priority=1, timeout_seconds=5.0),
            ProviderConfig(name="arxiv", priority=2, timeout_seconds=10.0),
            ProviderConfig(name="semantic_scholar", priority=3, timeout_seconds=10.0),
        ]
        super().__init__(providers=providers, **kwargs)

    async def research(self, query: str, max_results: int = 5) -> ProviderResult:
        """Execute research query using async parallel API calls."""
        return await self.route_async({"query": query, "max_results": max_results})

    async def _execute_provider_async(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        """Execute API call to a single research provider."""
        query = data.get("query", "")
        max_results = data.get("max_results", 5)

        if provider.name == "wikipedia":
            results = await self._fetch_wikipedia(query, max_results)
        elif provider.name == "arxiv":
            results = await self._fetch_arxiv(query, max_results)
        elif provider.name == "semantic_scholar":
            results = await self._fetch_semantic_scholar(query, max_results)
        else:
            return ProviderResult(provider.name, False, None, "Unknown provider")

        return ProviderResult(provider.name, True, results)

    async def _fetch_wikipedia(self, query: str, max_results: int) -> list[dict]:
        # Placeholder: Use aiohttp or httpx to call Wikipedia API
        return [{"title": f"Wiki: {query}", "url": "https://en.wikipedia.org/...", "source": "wikipedia"}]

    async def _fetch_arxiv(self, query: str, max_results: int) -> list[dict]:
        # Placeholder: Use aiohttp to call arXiv API
        return [{"title": f"arXiv: {query}", "url": "https://arxiv.org/...", "source": "arxiv"}]

    async def _fetch_semantic_scholar(self, query: str, max_results: int) -> list[dict]:
        # Placeholder: Use aiohttp to call Semantic Scholar API
        return [{"title": f"SS: {query}", "url": "https://semanticscholar.org/...", "source": "semantic_scholar"}]

    def _merge_results(self, results: list[Any]) -> dict[str, Any]:
        # Merge research results with source attribution
        merged = {"results": [], "by_source": {}}
        for source_results in results:
            for item in source_results:
                source = item.get("source", "unknown")
                if source not in merged["by_source"]:
                    merged["by_source"][source] = []
                merged["by_source"][source].append(item)
                merged["results"].append(item)
        return merged


async def main():
    router = ResearchRouter(strategy=RoutingStrategy.ALL_PARALLEL)
    result = await router.research("machine learning transformers")
    print(f"Success: {result.success}")
    print(f"Provider: {result.provider_name}")
    print(f"Results: {len(result.data['results']) if result.success else 0}")
    print(f"By source: {list(result.data['by_source'].keys()) if result.success else []}")
    print(f"Metrics: {router.get_metrics()}")


if __name__ == "__main__":
    asyncio.run(main())
