"""Consolidated async router with concurrent backend execution (PERF-001).

This module is the PRIMARY router implementation for search-research with:
- Concurrent backend execution using asyncio.gather() (PERF-001)
- Per-backend timeout support (FAST: 2s, COMPREHENSIVE: 8s)
- Web provider concurrency with per-provider timeout (PERF-008)
- LRU query caching with 3600s TTL (PERF-002)
- Backend health tracking with exponential backoff
- Backend type detection (sync vs async) using inspect.iscoroutinefunction (T-007)

Consolidated from router.py and core/router.py - this is now the single source of truth.
"""

from __future__ import annotations

import asyncio
import inspect
import logging
from collections.abc import AsyncIterator
from typing import Any

from .backend_health import BackendHealthRegistry
from .cache import QueryCache
from .config import config
from .hyde import apply_hyde
from .models import SearchResult  # CANONICAL import (Q-ARCH-001 fix)
from .modes import Mode

logger = logging.getLogger(__name__)


# Type aliases for better readability
BackendList = list[str]


class AsyncSearchRouter:
    """Async router with concurrent backend execution.

    Implements PERF-001: Use asyncio.gather() for concurrent backend execution.
    Implements PERF-008: Web providers run concurrently with per-provider timeout.

    Example:
        router = AsyncSearchRouter(mode="fast")
        results = await router.search_async("FastAPI patterns", limit=10)
    """

    def __init__(
        self,
        mode: str | Mode = "fast",
        cache_ttl: int = 3600,  # PERF-002: Updated from 300 to 3600
        enable_cache: bool = True,
        enable_jmri: bool = True,
        web: bool | None = None,
        hyde: bool | None = None,
        backend_weights: dict[str, float] | None = None,
    ) -> None:
        """Initialize async search router.

        Args:
            mode: Search mode - "fast"/Mode.FAST (<2s) or "comprehensive"/Mode.COMPREHENSIVE (<8s)
            cache_ttl: Cache time-to-live in seconds (default: 3600)
            enable_cache: Enable query caching (default: True)
            enable_jmri: Enable jMRI token-efficient retrieval (default: True)
            web: Explicit override for web search (None=auto-detect from mode)
            hyde: Explicit override for HyDE query enhancement (None=auto-detect from mode)
            backend_weights: Priority weights for backends (default: all 1.0).
                Higher values = higher priority. Results from higher-priority backends
                appear first within the same score group.

        The web and hyde parameters allow explicit override of mode-based defaults:
        - If None (default): Use mode-based defaults (web=False for fast, web=True for comprehensive)
        - If True/False: Override mode defaults with explicit value
        """
        # Normalize mode to string for internal use
        if isinstance(mode, Mode):
            self.mode = mode.value
            self._mode_enum = mode
        else:
            self.mode = mode
            self._mode_enum = Mode(mode) if mode in ("fast", "comprehensive") else None

        self.cache_ttl = cache_ttl
        self.enable_cache = enable_cache
        self.enable_jmri = enable_jmri

        # Web and hyde overrides (None = use mode defaults)
        self._web_override = web
        self._hyde_override = hyde

        # Backend priority weights (default: all backends have equal weight 1.0)
        self._backend_weights = backend_weights or {}

        # Initialize cache with updated TTL
        self._cache = QueryCache(ttl_seconds=cache_ttl)

        # Initialize health registry
        self._health = BackendHealthRegistry()

        # Backend timeouts based on mode (PERF-007 baseline)
        if self.mode == "fast":
            self.backend_timeout = 2.0  # 2s for fast mode
        else:  # comprehensive
            self.backend_timeout = 8.0  # 8s for comprehensive mode

        # Web provider timeout (PERF-008)
        self.web_provider_timeout = 5.0  # 5s per web provider

        # Lazy backend initialization - backends are created on first use
        # to avoid blocking during router initialization
        self._backends: dict[str, Any] = {}
        self._backends_initialized = False

    @property
    def web(self) -> bool:
        """Get web search setting based on mode and override.

        Returns:
            True if web search is enabled (comprehensive mode or override=True)
            False if web search is disabled (fast mode or override=False)
        """
        if self._web_override is not None:
            return self._web_override
        # Mode-based defaults: comprehensive includes web, fast does not
        return self.mode == "comprehensive"

    @property
    def hyde(self) -> bool:
        """Get HyDE query enhancement setting based on mode and override.

        Returns:
            True if HyDE is enabled (comprehensive mode or override=True)
            False if HyDE is disabled (fast mode or override=False)
        """
        if self._hyde_override is not None:
            return self._hyde_override
        # Mode-based defaults: comprehensive uses HyDE, fast does not
        return self.mode == "comprehensive"

    def get_cache_stats(self) -> dict[str, Any]:
        """Get query cache statistics.

        Returns:
            Dictionary with cache metrics: size, max_size, hits, misses, hit_rate, ttl_seconds
        """
        return self._cache.get_stats()

    def get_backend_weights(self) -> dict[str, float]:
        """Get backend priority weights.

        Returns:
            Dictionary mapping backend names to their priority weights.
            Higher values = higher priority. Results from higher-priority backends
            appear first within the same score group.
        """
        return self._backend_weights.copy()

    def set_backend_weights(self, weights: dict[str, float]) -> None:
        """Set backend priority weights.

        Args:
            weights: Dictionary mapping backend names to priority weights.
                Higher values = higher priority. Only affects future searches.

        Example:
            router.set_backend_weights({"MULTILANG": 2.0, "CKS": 1.5})
        """
        self._backend_weights = weights.copy()

    def _create_backends(self) -> dict[str, Any]:
        """Create and initialize all local backends (lazy initialization).

        Returns:
            Dictionary mapping backend names to backend instances
        """
        if self._backends_initialized:
            return self._backends

        from .backends import local

        backends = {}

        # Core backends (always available)
        try:
            backends["cds"] = local.CDSBackend(enable_cache=self.enable_cache)
            backends["grep"] = local.GrepBackend()
            backends["skills"] = local.SkillsBackend(enable_cache=self.enable_cache)
        except Exception as e:
            logger.warning(f"Failed to initialize core backends: {e}")

        # Optional backends (may not be available)
        # Skip CHS to avoid blocking on FAISS index building
        # Uncomment when CHS initialization is optimized
        # try:
        #     backends["chs"] = local.IncrementalIndexUpdater()
        # except Exception as e:
        #     logger.debug(f"CHS backend not available: {e}")

        try:
            backends["cks"] = local.create_cks_metadata_backend()
        except Exception as e:
            logger.debug(f"CKS backend not available: {e}")

        try:
            backends["kg"] = local.KGBackend()
        except Exception as e:
            logger.debug(f"KG backend not available: {e}")

        try:
            if local.is_rlm_available():
                backends["rlm"] = local.create_rlm_backend()
        except Exception as e:
            logger.debug(f"RLM backend not available: {e}")

        try:
            backends["claude-history"] = local.create_claude_history_backend()
        except Exception as e:
            logger.debug(f"Claude History backend not available: {e}")

        try:
            backends["notebooklm"] = local.create_notebooklm_backend()
        except Exception as e:
            logger.debug(f"NotebookLM backend not available: {e}")

        # Extended backends (AST-aware, call graph, CPG, HDMA, LSP, dependency)
        # These use graceful degradation - they're optional but provide deep analysis
        try:
            backends["ast_code"] = local.create_ast_backend()
        except Exception as e:
            logger.debug(f"AST code backend not available: {e}")

        try:
            if local.CPG_AVAILABLE:
                backends["cpg"] = local.CPGBackend()
        except Exception as e:
            logger.debug(f"CPG backend not available: {e}")

        try:
            if local.HDMA_AVAILABLE:
                backends["hdma"] = local.HDMABackend()
        except Exception as e:
            logger.debug(f"HDMA backend not available: {e}")

        try:
            backends["lsp"] = local.create_lsp_backend()
        except Exception as e:
            logger.debug(f"LSP backend not available: {e}")

        try:
            if local.DEP_GRAPH_AVAILABLE:
                backends["dependency"] = local.DependencyBackend()
        except Exception as e:
            logger.debug(f"Dependency backend not available: {e}")

        # QMD Wiki backend - searches Obsidian vault via QMD CLI
        try:
            backends["qmd_wiki"] = local.QMDWikiBackend()
        except Exception as e:
            logger.debug(f"QMD Wiki backend not available: {e}")

        self._backends = backends
        self._backends_initialized = True

        return backends

    async def search_async(
        self,
        query: str,
        limit: int = 10,
        backends: BackendList | None = None,
        hyde_content: str | None = None,
    ) -> list[SearchResult]:
        """Search backends concurrently using asyncio.gather() (PERF-001).

        CRITICAL: This implementation uses asyncio.gather() to run all backends
        in parallel, NOT sequentially. This is the key performance optimization.

        Args:
            query: Search query
            limit: Maximum number of results
            backends: Optional list of backend names to use
            hyde_content: Optional pre-generated HyDE content for query enhancement

        Returns:
            List of SearchResult objects ranked by relevance

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty or contain only whitespace. "
                "Please provide a meaningful search query."
            )

        # Apply HyDE query enhancement if content provided (no LLM call needed — already generated)
        search_query = query
        hyde_applied = False
        if hyde_content:
            search_query, hyde_applied = apply_hyde(query, hyde_content=hyde_content)
            if hyde_applied:
                logger.debug(f"HyDE enhanced query: '{query[:50]}...' -> '{search_query[:50]}...'")

        # Check cache first
        if self.enable_cache:
            # If HyDE was applied, check cache with enhanced query first (more specific)
            if hyde_applied:
                cached = self._cache.get(search_query, limit=limit, backends=backends)
                if cached is not None:
                    logger.debug(f"Cache hit for HyDE-enhanced query: '{search_query[:50]}...'")
                    return [SearchResult.from_dict(r) for r in cached]
            # Fall back to original query cache
            cached = self._cache.get(query, limit=limit, backends=backends)
            if cached is not None:
                return [SearchResult.from_dict(r) for r in cached]

        # Determine which backends to use
        if backends is None:
            backends = self._get_backends_for_mode()

        # PERF-001: Concurrent backend execution using asyncio.gather()
        # This is the CRITICAL performance optimization - all backends run in parallel
        search_tasks = [
            self._search_backend_async(backend, search_query, limit) for backend in backends
        ]

        # Wait for all backends to complete (with individual timeouts)
        backend_results = await asyncio.gather(
            *search_tasks,
            return_exceptions=True,  # Don't fail on individual backend errors
        )

        # Process results and filter out exceptions
        all_results = []
        for result in backend_results:
            if isinstance(result, Exception):
                # Log error but continue with other results
                continue
            if isinstance(result, list):
                all_results.extend(result)

        # Rank and limit results
        ranked_results = self._rank_results(all_results)[:limit]

        # Cache results (convert to dict for cache)
        if self.enable_cache:
            cache_results = [r.to_dict() for r in ranked_results]
            # Use enhanced query as cache key if HyDE was applied
            cache_key = search_query if hyde_applied else query
            self._cache.set(cache_key, cache_results, limit=limit, backends=backends)

        return ranked_results

    async def search_async_stream(
        self,
        query: str,
        limit: int = 10,
        backends: BackendList | None = None,
        hyde_content: str | None = None,
    ) -> AsyncIterator[SearchResult]:
        """Stream search results as they become available from backends.

        Unlike search_async() which waits for ALL backends to complete,
        this method yields results immediately as each backend finishes.
        Results are NOT ranked or deduplicated - they arrive in backend completion order.

        PERF-008: Web providers run concurrently with per-provider timeout.

        Args:
            query: Search query
            limit: Maximum results per backend (NOT overall limit)
            backends: Optional list of backend names to use
            hyde_content: Optional pre-generated HyDE content for query enhancement

        Yields:
            SearchResult objects as they become available from each backend

        Raises:
            ValueError: If query is empty

        Example:
            >>> async for result in router.search_async_stream("FastAPI patterns"):
            ...     print(f"{result.source}: {result.title}")
        """
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty or contain only whitespace. "
                "Please provide a meaningful search query."
            )

        # Apply HyDE query enhancement if content provided (no LLM call needed — already generated)
        search_query = query
        if hyde_content:
            search_query, _ = apply_hyde(query, hyde_content=hyde_content)

        # Determine which backends to use
        if backends is None:
            backends = self._get_backends_for_mode()

        # Filter to available backends only
        available_backends = []
        for backend in backends:
            if isinstance(backend, str) and backend in self._backends:
                available_backends.append(backend)
            elif not isinstance(backend, str):
                available_backends.append(backend)  # Already an instance

        # Create tasks for all backends
        pending_tasks = set()
        task_to_backend = {}
        for backend in available_backends:
            backend_name = backend if isinstance(backend, str) else "unknown"
            task = asyncio.create_task(self._search_backend_async(backend, search_query, limit))
            pending_tasks.add(task)
            task_to_backend[task] = backend_name

        # Use asyncio.wait with FIRST_COMPLETED to yield results as backends finish
        completed_backends = set()
        while pending_tasks:
            done, pending_tasks = await asyncio.wait(
                pending_tasks, return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                backend_name = task_to_backend.get(task, "unknown")

                try:
                    results = await task
                    # Yield each result individually
                    for result in results:
                        yield result
                except TimeoutError:
                    logger.debug(f"Backend {backend_name} timed out during streaming search")
                except Exception as e:
                    logger.debug(f"Backend {backend_name} failed during streaming search: {e}")

                completed_backends.add(backend_name)

    async def search_async_stream_batch(
        self,
        query: str,
        limit: int = 10,
        batch_size: int = 5,
        backends: BackendList | None = None,
        hyde_content: str | None = None,
    ) -> AsyncIterator[list[SearchResult]]:
        """Stream search results in batches as backends complete.

        Similar to search_async_stream() but yields results in batches.
        Each batch contains all results from a single backend that just completed.

        PERF-008: Web providers run concurrently with per-provider timeout.

        Args:
            query: Search query
            limit: Maximum results per backend (NOT overall limit)
            batch_size: Minimum batch size before yielding (default: 5)
            backends: Optional list of backend names to use
            hyde_content: Optional pre-generated HyDE content for query enhancement

        Yields:
            Lists of SearchResult objects (batches) as backends complete

        Raises:
            ValueError: If query is empty

        Example:
            >>> async for batch in router.search_async_stream_batch("FastAPI patterns"):
            ...     print(f"Got {len(batch)} results from batch")
        """
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty or contain only whitespace. "
                "Please provide a meaningful search query."
            )

        # Apply HyDE query enhancement if content provided (no LLM call needed — already generated)
        search_query = query
        if hyde_content:
            search_query, _ = apply_hyde(query, hyde_content=hyde_content)

        # Determine which backends to use
        if backends is None:
            backends = self._get_backends_for_mode()

        # Filter to available backends only
        available_backends = []
        for backend in backends:
            if isinstance(backend, str) and backend in self._backends:
                available_backends.append(backend)
            elif not isinstance(backend, str):
                available_backends.append(backend)  # Already an instance

        # Create tasks for all backends
        pending_tasks = set()
        task_to_backend = {}
        for backend in available_backends:
            backend_name = backend if isinstance(backend, str) else "unknown"
            task = asyncio.create_task(self._search_backend_async(backend, search_query, limit))
            pending_tasks.add(task)
            task_to_backend[task] = backend_name

        # Use asyncio.wait with FIRST_COMPLETED to yield results as backends finish
        while pending_tasks:
            done, pending_tasks = await asyncio.wait(
                pending_tasks, return_when=asyncio.FIRST_COMPLETED
            )

            for task in done:
                backend_name = task_to_backend.get(task, "unknown")

                try:
                    results = await task
                    if results:  # Only yield non-empty batches
                        yield results
                except TimeoutError:
                    logger.debug(f"Backend {backend_name} timed out during batch streaming")
                except Exception as e:
                    logger.debug(f"Backend {backend_name} failed during batch streaming: {e}")

    async def _search_backend_async(
        self,
        backend: str,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        """Search a single backend with timeout.

        Handles both async backends (native) and sync backends (via asyncio.to_thread()).
        Converts raw backend results to SearchResult objects.

        Args:
            backend: Backend name or instance
            query: Search query
            limit: Maximum results

        Returns:
            List of SearchResult objects from this backend

        Raises:
            asyncio.TimeoutError: If backend exceeds timeout
        """
        try:
            # Ensure backends are initialized (lazy initialization)
            if not self._backends_initialized:
                self._create_backends()

            # Get backend instance if backend is a string
            backend_instance = self._backends.get(backend) if isinstance(backend, str) else backend

            if backend_instance is None:
                backend_name = backend if isinstance(backend, str) else "unknown"
                available = list(self._backends.keys()) if self._backends_initialized else []
                error_msg = (
                    f"Backend '{backend_name}' not found. "
                    f"Available backends: {available if available else '(not initialized)'}"
                )
                self._health.record_result(backend_name, success=False, error="Backend not found")
                logger.warning(error_msg)
                return []

            # Detect async vs sync backends
            # Use sentinel to avoid MagicMock creating attributes
            _sentinel = object()
            search_async_method = getattr(backend_instance, "search_async", _sentinel)

            if search_async_method is not _sentinel and callable(search_async_method):
                # Native async backend (has search_async method)
                raw_results = await asyncio.wait_for(
                    search_async_method(query, limit), timeout=self.backend_timeout
                )
            elif inspect.iscoroutinefunction(backend_instance.search):
                # Async search method (coroutine)
                raw_results = await asyncio.wait_for(
                    backend_instance.search(query, limit), timeout=self.backend_timeout
                )
            else:
                # Sync backend - use asyncio.to_thread() for non-blocking execution
                loop = asyncio.get_event_loop()
                raw_results = await asyncio.wait_for(
                    loop.run_in_executor(None, backend_instance.search, query, limit),
                    timeout=self.backend_timeout,
                )

            # Record success
            backend_name = backend if isinstance(backend, str) else "unknown"
            self._health.record_result(backend_name, success=True)

            # Convert raw results to SearchResult objects
            search_results = []
            for result in raw_results or []:
                search_results.append(self._convert_to_search_result(result, backend_name))

            return search_results

        except TimeoutError:
            # Record timeout as failure with helpful context
            timeout_msg = (
                f"Backend '{backend}' timed out after {self.backend_timeout}s. "
                f"Consider using 'comprehensive' mode for longer timeouts, "
                f"or check if the backend is responding."
            )
            self._health.record_result(backend, success=False, error="Timeout")
            logger.debug(timeout_msg)
            return []
        except Exception as e:
            # Record error
            self._health.record_result(backend, success=False, error=str(e))
            return []

    def _convert_to_search_result(
        self,
        raw_result: dict[str, Any],
        source: str,
    ) -> SearchResult:
        """Convert backend result to SearchResult format.

        Args:
            raw_result: Raw result from backend
            source: Backend name

        Returns:
            SearchResult instance
        """
        # Extract common fields
        title = raw_result.get("title") or raw_result.get("name", "")
        content = raw_result.get("content") or raw_result.get("description", "")
        score = raw_result.get("score", 0.5)

        # Extract metadata
        metadata = raw_result.get("metadata", {})
        if "file_path" in raw_result and "file_path" not in metadata:
            metadata["file_path"] = raw_result["file_path"]
        if "line" in raw_result and "line_number" not in metadata:
            metadata["line_number"] = raw_result["line"]

        return SearchResult(
            title=title,
            content=content,
            file_path=metadata.get("file_path"),
            line_number=metadata.get("line_number"),
            source=source.upper(),
            score=score,
            metadata=metadata,
            cached=raw_result.get("cached", False),
        )

    def _rank_results(self, results: list[SearchResult]) -> list[SearchResult]:
        """Rank results by relevance score with source diversity and backend priority.

        Ensures fair distribution across backends when scores are equal.
        Uses round-robin within score groups to prevent single-backend dominance.
        Results from higher-priority backends (via backend_weights) appear first.

        Args:
            results: List of search results

        Returns:
            Sorted results by score (descending) with source diversity and priority weighting
        """
        if not results:
            return []

        # Group by score (round to 3 decimals for grouping)
        from collections import defaultdict

        score_groups = defaultdict(list)
        for r in results:
            score_key = round(r.score, 3)
            score_groups[score_key].append(r)

        # Sort scores descending
        sorted_scores = sorted(score_groups.keys(), reverse=True)

        # Interleave results within each score group for diversity
        ranked = []
        for score in sorted_scores:
            group = score_groups[score]
            # Group by source within this score
            source_groups = defaultdict(list)
            for r in group:
                source_groups[r.source].append(r)

            # Get list of sources sorted by priority weight (descending), then by name
            # Sources with higher weights appear first
            def get_source_sort_key(source: str) -> tuple[float, str]:
                weight = self._backend_weights.get(source, 1.0)
                return (-weight, source)  # Negative for descending weight, then alphabetical

            sources = sorted(source_groups.keys(), key=get_source_sort_key)

            # Round-robin through sources (now priority-weighted)
            max_len = max(len(source_groups[s]) for s in sources)
            for i in range(max_len):
                for source in sources:
                    if i < len(source_groups[source]):
                        ranked.append(source_groups[source][i])

        return ranked

    async def search_web_providers_async(
        self,
        query: str,
        limit: int = 10,
        providers: list[str] | None = None,
    ) -> list[SearchResult]:
        """Search web providers concurrently with per-provider timeout (PERF-008).

        PERF-008: Web providers must run concurrently with per-provider timeout (5s).

        Args:
            query: Search query
            limit: Maximum results per provider
            providers: Optional list of provider names (default: all available)

        Returns:
            List of search results from all web providers

        Raises:
            ValueError: If query is empty
        """
        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty or contain only whitespace. "
                "Please provide a meaningful search query."
            )

        # Load web providers from config
        if providers is None:
            providers = config.WEB_PROVIDERS

        # PERF-008: Concurrent web provider execution with per-provider timeout
        provider_tasks = [
            self._search_web_provider_async(provider, query, limit) for provider in providers
        ]

        # Wait for all providers with individual timeouts
        provider_results = await asyncio.gather(*provider_tasks, return_exceptions=True)

        # Process results
        all_results = []
        for result in provider_results:
            if isinstance(result, Exception):
                continue
            if isinstance(result, list):
                all_results.extend(result)

        return all_results

    async def _search_web_provider_async(
        self,
        provider: str,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        """Search a single web provider with timeout (PERF-008).

        Args:
            provider: Provider name (e.g., "tavily", "serper")
            query: Search query
            limit: Maximum results

        Returns:
            List of results from this provider
        """
        try:
            # Web provider calls are implemented via _call_web_provider()
            # Use asyncio.wait_for() to enforce per-provider timeout
            result = await asyncio.wait_for(
                self._call_web_provider(provider, query, limit),
                timeout=self.web_provider_timeout,  # PERF-008: 5s per provider
            )

            # Record success
            self._health.record_result(f"web_{provider}", success=True)

            return result or []

        except TimeoutError:
            # Record timeout with helpful context
            timeout_msg = (
                f"Web provider '{provider}' timed out after {self.web_provider_timeout}s. "
                f"Check your internet connection and provider API status."
            )
            self._health.record_result(f"web_{provider}", success=False, error="Timeout")
            logger.warning(timeout_msg)
            return []
        except Exception as e:
            # Record error
            self._health.record_result(f"web_{provider}", success=False, error=str(e))
            return []

    async def _call_web_provider(
        self,
        provider: str,
        query: str,
        limit: int,
    ) -> list[SearchResult]:
        """Call a web provider API.

        Args:
            provider: Provider name (tavily, serper, exa, brave)
            query: Search query
            limit: Maximum results

        Returns:
            List of results from provider
        """
        from .providers import ExaBackend, SerperBackend, TavilyBackend

        # Map provider names to backend classes
        provider_map = {
            "tavily": TavilyBackend,
            "serper": SerperBackend,
            "exa": ExaBackend,
        }

        backend_class = provider_map.get(provider)
        if backend_class is None:
            available = list(provider_map.keys())
            logger.warning(
                f"Unknown web provider '{provider}'. "
                f"Available providers: {available}. "
                f"Check config.WEB_PROVIDERS setting."
            )
            return []

        # Create backend instance
        try:
            backend = backend_class(max_results=limit)

            # Check if provider is available (has API key)
            if not backend.is_available():
                logger.debug(
                    f"Web provider '{provider}' not available. "
                    f"Configure API key in environment variables or .env file. "
                    f"Required: {provider.upper()}_API_KEY"
                )
                return []

            # Call provider's search method
            results = await backend.search(
                query, max_results=limit, timeout=self.web_provider_timeout
            )

            # Convert provider results to SearchResult format
            search_results = []
            for result in results:
                search_results.append(
                    SearchResult(
                        title=result.get("title", "Untitled"),
                        content=result.get("content", result.get("snippet", "")),
                        url=result.get("url"),
                        source=provider.capitalize(),
                        score=result.get("score") if result.get("score") is not None else 0.5,
                        metadata={"provider": provider},
                    )
                )

            return search_results

        except Exception as e:
            logger.error(f"Error calling web provider {provider}: {e}")
            return []

    def _get_backends_for_mode(self) -> list[str]:
        """Get list of backends for current mode.

        Returns:
            List of backend names
        """
        # Ensure backends are initialized (lazy initialization)
        if not self._backends_initialized:
            self._create_backends()

        # Return all available backends
        # Mode-specific filtering is handled at search time, not registration time
        return list(self._backends.keys())


def create_async_router(
    mode: str | Mode = "fast",
    cache_ttl: int = 3600,
    enable_cache: bool = True,
    enable_jmri: bool = True,
    web: bool | None = None,
    hyde: bool | None = None,
    backend_weights: dict[str, float] | None = None,
) -> AsyncSearchRouter:
    """Factory function to create async router.

    Args:
        mode: Search mode - "fast"/Mode.FAST or "comprehensive"/Mode.COMPREHENSIVE
        cache_ttl: Cache time-to-live in seconds
        enable_cache: Enable query caching
        enable_jmri: Enable jMRI token-efficient retrieval
        web: Explicit override for web search (None=auto-detect from mode)
        hyde: Explicit override for HyDE query enhancement (None=auto-detect from mode)
        backend_weights: Priority weights for backends (default: all 1.0)

    Returns:
        Configured AsyncSearchRouter instance
    """
    return AsyncSearchRouter(
        mode=mode,
        cache_ttl=cache_ttl,
        enable_cache=enable_cache,
        enable_jmri=enable_jmri,
        web=web,
        hyde=hyde,
        backend_weights=backend_weights,
    )
