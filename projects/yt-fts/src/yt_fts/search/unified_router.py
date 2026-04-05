"""
Unified Search Router - Example usage of MetaRouter.

This demonstrates how to subclass MetaRouter for search functionality.
"""
from __future__ import annotations

from typing import Any

from yt_fts.core_utils import (
    MetaRouter,
    ProviderConfig,
    ProviderResult,
    RoutingStrategy,
)


class UnifiedSearchRouter(MetaRouter):
    """Routes search queries to FTS, vector, and external backends."""

    def __init__(self, **kwargs):
        providers = [
            ProviderConfig(name="fts", priority=1, max_retries=2),
            ProviderConfig(name="vector", priority=2, max_retries=2),
        ]
        super().__init__(providers=providers, **kwargs)

    def search(self, query: str, limit: int = 10) -> ProviderResult:
        """Execute search using configured strategy."""
        return self.route({"query": query, "limit": limit})

    def _execute_provider(self, provider: ProviderConfig, data: Any) -> ProviderResult:
        """Execute search on a single provider - implement your logic here."""
        data.get("query", "")

        # Implement actual search logic for each provider
        if provider.name == "fts":
            # Call yt_fts.core.database.search_all(query)
            results = []  # Placeholder
        elif provider.name == "vector":
            # Call FAISS vector search
            results = []  # Placeholder
        else:
            return ProviderResult(provider.name, False, None, "Unknown provider")

        return ProviderResult(provider.name, True, results)

    def _merge_results(self, results: list[Any]) -> list[dict]:
        """Merge and deduplicate results from multiple providers."""
        # Deduplicate by video_id or other criteria
        merged = []
        seen = set()
        for result_list in results:
            for item in result_list:
                video_id = item.get("video_id")
                if video_id not in seen:
                    merged.append(item)
                    seen.add(video_id)
        return merged


# Example usage:
if __name__ == "__main__":
    router = UnifiedSearchRouter(strategy=RoutingStrategy.FIRST_SUCCESS)
    result = router.search("python tutorial", limit=5)
    print(f"Success: {result.success}")
    print(f"Provider: {result.provider_name}")
    print(f"Results: {len(result.data) if result.success else 0}")
    print(f"Metrics: {router.get_metrics()}")
