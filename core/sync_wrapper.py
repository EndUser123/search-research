"""SyncSearchWrapper: Backward compatibility wrapper for AsyncSearchRouter.

This module provides a synchronous API wrapper around AsyncSearchRouter for backward
compatibility with existing code that uses SearchRouter.

DEPRECATED: This wrapper is deprecated and will be removed in a future version.
Migrate to AsyncSearchRouter for better performance. See docs/unified_search_migration.md.

Example:
    from core.sync_wrapper import SyncSearchWrapper

    wrapper = SyncSearchWrapper()
    results = wrapper.search("FastAPI patterns", limit=10)
"""

from __future__ import annotations

import asyncio
import warnings

from .router_async import AsyncSearchRouter, SearchResult


class SyncSearchWrapper:
    """Backward compatibility wrapper for AsyncSearchRouter.

    This class provides a synchronous API that wraps AsyncSearchRouter.search_async()
    using asyncio.run(). It exists solely for backward compatibility with code that
    was written before the async router was introduced.

    .. deprecated::
        This class is deprecated and will be removed in a future version.
        Migrate to AsyncSearchRouter for better performance and native async support.
        See docs/unified_search_migration.md for a detailed migration guide.

    Example:
        Before (deprecated):
            wrapper = SyncSearchWrapper()
            results = wrapper.search("FastAPI patterns", limit=10)

        After (recommended):
            router = AsyncSearchRouter()
            results = await router.search_async("FastAPI patterns", limit=10)
            # Or in sync context:
            results = asyncio.run(router.search_async("FastAPI patterns", limit=10))
    """

    def __init__(
        self,
        cache_ttl: int = 3600,
        enable_cache: bool = True,
        enable_jmri: bool = True,
    ) -> None:
        """Initialize the synchronous wrapper.

        Emits a DeprecationWarning to encourage migration to AsyncSearchRouter.

        Args:
            cache_ttl: Cache time-to-live in seconds. Default is 3600 (1 hour).
            enable_cache: Whether to enable query caching. Default is True.
            enable_jmri: Whether to enable jMRI token-efficient retrieval. Default is True.

        Warning:
            This class is deprecated. Use AsyncSearchRouter directly for better performance.
            See docs/unified_search_migration.md for migration guide.
        """
        warnings.warn(
            "SyncSearchWrapper is deprecated and will be removed in a future version. "
            "Migrate to AsyncSearchRouter for better performance. "
            "See docs/unified_search_migration.md for migration guide.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Store configuration for backward compatibility
        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        self.enable_jmri = enable_jmri

        # Create internal AsyncSearchRouter instance
        self._async_router = AsyncSearchRouter(
            cache_ttl=cache_ttl,
            enable_cache=enable_cache,
            enable_jmri=enable_jmri,
        )

    def search(
        self,
        query: str,
        limit: int = 10,
        backends: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search local backends synchronously.

        This is a synchronous wrapper around AsyncSearchRouter.search_async()
        that uses asyncio.run() to execute the async method. A fresh event loop
        is created for each call.

        Args:
            query: The search query string.
            limit: Maximum number of results to return. Default is 10.
            backends: Optional list of backend names to use. If None, all available
                backends are queried.

        Returns:
            A list of SearchResult objects ranked by relevance score.

        Raises:
            ValueError: If query is empty or contains only whitespace.
            RuntimeError: If called from an existing async context (asyncio.run
                cannot be nested).

        Note:
            This method creates a new event loop on each call. For better
            performance in async contexts, use AsyncSearchRouter directly.
        """
        return asyncio.run(
            self._async_router.search_async(
                query=query,
                limit=limit,
                backends=backends,
            )
        )
