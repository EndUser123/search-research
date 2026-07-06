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

from datetime import datetime
import time as time_module

from .backend_health import BackendHealthRegistry
from .cache import QueryCache
from .chs.utils import escape_fts5_query
from .config import config
from .domain_detector import detect_domain
from .hyde import apply_hyde
from .metrics import MetricsLogger, ComponentName  # TASK-3: Instrumented metrics
from .models import SearchResult  # CANONICAL import (Q-ARCH-001 fix)
from .modes import Mode
from .tracing import QueryTracer, QueryTrace  # TASK-3: Query tracing

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

        # TASK-3: Initialize metrics logger and query tracer
        self._metrics = MetricsLogger()
        self._tracer = QueryTracer()

        # Backend timeouts based on mode (PERF-007 baseline)
        # "fast" and "local-only" use fast timeout; "comprehensive" uses longer timeout
        if self.mode in ("fast", "local-only"):
            self.backend_timeout = 8.0  # 8s for local modes (was 2s, too aggressive for KG/LSP/AST backends)
        else:
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
            backends["vault"] = local.create_vault_backend()
        except Exception as e:
            logger.debug(f"Vault backend not available: {e}")

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

        try:
            backends["call_graph"] = local.CallGraphBackend()
        except Exception as e:
            logger.debug(f"Call graph backend not available: {e}")

        # QMD Wiki backend - searches Obsidian vault via QMD CLI
        try:
            backends["qmd_wiki"] = local.QMDWikiBackend()
        except Exception as e:
            if "backend unavailable" in str(e).lower():
                logger.warning(f"QMD_WIKI backend unavailable: {e}")
            else:
                logger.warning(f"QMD Wiki backend not available: {e}")

        # yt-is backend - searches YouTube transcript cache via FTS5
        try:
            backends["yt_is"] = local.YtIsBackend()
        except Exception as e:
            logger.debug(f"yt-is backend not available: {e}")

        # Domain constraint backend — proactive constraint surfacing
        try:
            backends["domain_constraint"] = local.create_domain_constraint_backend()
        except Exception as e:
            logger.debug(f"domain_constraint backend not available: {e}")

        self._backends = backends
        self._backends_initialized = True

        # Warm up sync backends to trigger build_index() before first search.
        # Without this, the first gather call causes all sync backends to call
        # build_index() simultaneously, flooding the thread pool and causing
        # premature timeouts on fast backends (PERF-001).
        self._warm_up_backends()

        return backends

    def _warm_up_backends(self) -> None:
        """Pre-warm sync backends by triggering build_index() with a no-op query.

        Calls search() on each backend to force lazy build_index() to run
        during router init rather than during the first concurrent gather.
        Backends that raise exceptions are skipped silently.
        """
        for name, backend in self._backends.items():
            try:
                # Skip backends that don't have a sync search method
                if not hasattr(backend, "search"):
                    continue
                # Skip async backends (they handle initialization differently)
                if hasattr(backend, "search_async") or (
                    hasattr(backend, "search") and inspect.iscoroutinefunction(backend.search)
                ):
                    continue
                # Trigger build_index() with a query that returns no results
                backend.search("", 1)
            except Exception:
                # Warm-up failures are non-fatal - backend may not have data yet
                pass

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

        # Escape FTS5 special characters before backend dispatch (PERF-001 fix: CAUSE-004)
        # qmd_wiki and yt_is backends use simple _sanitize_query that doesn't escape FTS5
        # operators like '.', ',', etc. Centralizing escaping here protects all backends.
        search_query = escape_fts5_query(search_query)

        # DOMAIN-CONSTRAINT: Detect domain tags and look up matching constraint entries.
        # Runs concurrently with normal backends. Results are injected as a separate
        # high-priority band (score >= 0.9) before result fusion.
        constraint_results: list[SearchResult] = []
        domain_class = detect_domain(search_query)

        if domain_class.has_constraints and domain_class.confidence >= 0.6:
            dc_backend = self._backends.get("domain_constraint")
            if dc_backend:
                try:
                    raw = dc_backend.search(domain_class.domains, limit=5)
                    for r in raw:
                        constraint_results.append(
                            SearchResult(
                                source=r["source"],
                                title=r["title"],
                                content=r["content"],
                                score=r["score"],
                                url="",
                                metadata=r.get("metadata", {}),
                            )
                        )
                except Exception:
                    pass  # Non-blocking — constraints are advisory only

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

        # TASK-3: Start query trace
        query_id = self._tracer.start_trace(query)

        # PERF-001: Concurrent backend execution using asyncio.gather()
        # This is the CRITICAL performance optimization - all backends run in parallel
        # Track backend hits for trace
        backend_hits: dict[str, int] = {}

        # Wrap each backend call with timing for metrics
        async def timed_search_backend(backend: str) -> tuple[str, list[SearchResult]]:
            start_time = time_module.perf_counter()
            results = await self._search_backend_async(backend, search_query, limit)
            elapsed_ms = (time_module.perf_counter() - start_time) * 1000
            # Log metric for this backend
            if results:
                avg_quality = sum(r.score for r in results) / len(results)
                backend_key = backend.replace("-", "_").upper()
                try:
                    component = ComponentName[backend_key]
                except KeyError:
                    component = ComponentName.SEARCH_PROVIDER
                self._metrics.log_component(
                    component=component,
                    latency_ms=elapsed_ms,
                    tokens_used=0,
                    quality=avg_quality,
                    cache_hit=False,
                )
            # Track backend hits
            backend_hits[backend] = len(results)
            return backend, results

        search_tasks = [timed_search_backend(backend) for backend in backends]

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
            if isinstance(result, tuple):
                backend, results = result
                all_results.extend(results)

        # DOMAIN-CONSTRAINT: Prepend constraint results as high-priority band.
        # Constraint results have fixed score 0.95; normal results are ranked.
        # This keeps constraints visible without polluting the ranked results.
        if constraint_results:
            all_results = constraint_results + all_results

        # Rank and limit results
        ranked_results = self._rank_results(all_results)[:limit]

        # Cache results (convert to dict for cache)
        if self.enable_cache:
            cache_results = [r.to_dict() for r in ranked_results]
            # Always use escaped search_query as cache key for consistency
            # Previously: HyDE-on used escaped, HyDE-off used raw -- causing unnecessary
            # cache misses since backends always receive escaped query.
            cache_key = search_query
            self._cache.set(cache_key, cache_results, limit=limit, backends=backends)

        # TASK-3: Log query trace after search completes
        final_quality = ranked_results[0].score if ranked_results else 0.0
        path_taken = "local_only" if not self.web else "web_search"
        trace = QueryTrace(
            query_id=query_id,
            timestamp=datetime.now().isoformat(),
            question=query,
            path_taken=path_taken,
            backend_hits=backend_hits,
            sources=[r.source for r in ranked_results],
            final_quality=final_quality,
            contradiction_detected=False,
            decision_audit_id=None,
        )
        self._tracer.log_trace(trace)

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

            # Per-backend timeout: router timeout is the ceiling for cancellation.
            # A backend's TIMEOUT is ignored so that slow backends (NotebookLM
            # at 60s) cannot override the router's cancellation budget and
            # block fast backends from returning. Backend internal timeouts
            # (e.g. subprocess timeouts) are unaffected by this.
            # Exception: backends with their own TIMEOUT (NotebookLM at 60s) need
            # enough time for LLM synthesis + API calls; use backend TIMEOUT when
            # it exceeds the router ceiling.
            backend_timeout = self.backend_timeout
            if hasattr(backend_instance, "TIMEOUT") and backend_instance.TIMEOUT > backend_timeout:
                backend_timeout = backend_instance.TIMEOUT

            if search_async_method is not _sentinel and callable(search_async_method):
                # Native async backend (has search_async method)
                raw_results = await asyncio.wait_for(
                    search_async_method(query, limit), timeout=backend_timeout
                )
            elif inspect.iscoroutinefunction(backend_instance.search):
                # Async search method (coroutine)
                raw_results = await asyncio.wait_for(
                    backend_instance.search(query, limit), timeout=backend_timeout
                )
            else:
                # Sync backend - use asyncio.to_thread() for non-blocking execution
                raw_results = await asyncio.wait_for(
                    asyncio.to_thread(backend_instance.search, query, limit),
                    timeout=backend_timeout,
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
        raw_result: dict[str, Any] | SearchResult,
        source: str,
    ) -> SearchResult:
        """Convert backend result to SearchResult format.

        Handles both dict-style raw results and SearchResult dataclass instances.

        Args:
            raw_result: Raw result from backend (dict or SearchResult dataclass)
            source: Backend name

        Returns:
            SearchResult instance
        """
        # If already a SearchResult dataclass, normalize source and return
        if isinstance(raw_result, SearchResult):
            return SearchResult(
                title=raw_result.title,
                content=raw_result.content,
                source=source.upper(),
                score=raw_result.score,
                url=getattr(raw_result, "url", None),
                file_path=raw_result.file_path,
                line_number=raw_result.line_number,
                metadata=raw_result.metadata,
                cached=raw_result.cached,
            )

        # Dict-style result (legacy backends)
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

        from collections import defaultdict

        # Normalize scores per-backend to [0, 1] using min-max scaling.
        # Different backends use incompatible scoring systems (e.g. raw BM25
        # scores of 5-10 vs normalized confidence of 0-1). Without
        # normalization, high-magnitude scores dominate ranking and
        # effectively silence backends with lower-magnitude scores.
        # Single-pass space optimization: track running (min, max) per source
        # instead of collecting all scores into lists.
        source_min_max: dict[str, tuple[float, float]] = defaultdict(lambda: (float("inf"), float("-inf")))
        for r in results:
            mn, mx = source_min_max[r.source]
            source_min_max[r.source] = (min(mn, r.score), max(mx, r.score))

        # Normalize each result's score for ranking purposes
        for r in results:
            mn, mx = source_min_max[r.source]
            if mx > mn:
                r.score = (r.score - mn) / (mx - mn)
            else:
                r.score = 1.0  # All scores equal within this source

        # Group by score (round to 3 decimals for grouping)
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
            source_groups: dict[str, list[SearchResult]] = defaultdict(list)
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
        from .providers import BraveBackend, DDGsBackend, ExaBackend, MMXBackend, SerperBackend, TavilyBackend

        # Map provider names to backend classes
        provider_map = {
            "tavily": TavilyBackend,
            "serper": SerperBackend,
            "exa": ExaBackend,
            "brave": BraveBackend,
            "duckduckgo": DDGsBackend,
            "minimax": MMXBackend,
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
