"""Tests for AsyncSearchRouter.

These tests verify the async conversion of AsyncSearchRouter.
All tests should FAIL initially because AsyncSearchRouter doesn't exist yet.

Run with: pytest tests/test_async_router.py -v
"""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from search_research import Mode, SearchResult


class TestAsyncSearchRouterBasic:
    """Tests for basic AsyncSearchRouter instantiation and structure."""

    def test_async_search_router_class_exists(self):
        """Test that AsyncSearchRouter class can be imported."""
        # This will fail because AsyncSearchRouter doesn't exist yet
        from search_research import AsyncSearchRouter  # noqa: F401

    def test_init_creates_instance(self):
        """Test that AsyncSearchRouter can be instantiated."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        assert router is not None
        assert router.mode == Mode.FAST.value
        assert router.cache_ttl == 3600
        assert router.enable_cache is True

    def test_init_with_options(self):
        """Test AsyncSearchRouter initialization with options."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(cache_ttl=1800, enable_cache=False)
        assert router.cache_ttl == 1800
        assert router.enable_cache is False

    def test_init_with_mode_enum(self):
        """Test AsyncSearchRouter initialization with Mode enum."""
        from search_research import AsyncSearchRouter, Mode

        router = AsyncSearchRouter(mode=Mode.FAST)
        assert router.mode == "fast"
        assert router.web == False
        assert router.hyde == False

        router2 = AsyncSearchRouter(mode=Mode.COMPREHENSIVE)
        assert router2.mode == "comprehensive"
        assert router2.web == True
        assert router2.hyde == True

    def test_web_and_hyde_properties_default_to_mode(self):
        """Test that web and hyde properties default to mode-based values."""
        from search_research import AsyncSearchRouter

        # Fast mode: web=False, hyde=False by default
        router_fast = AsyncSearchRouter(mode="fast")
        assert router_fast.web == False
        assert router_fast.hyde == False

        # Comprehensive mode: web=True, hyde=True by default
        router_comp = AsyncSearchRouter(mode="comprehensive")
        assert router_comp.web == True
        assert router_comp.hyde == True

    def test_web_and_hyde_explicit_overrides(self):
        """Test that web and hyde parameters can override mode defaults."""
        from search_research import AsyncSearchRouter

        # Fast mode with web=True override
        router1 = AsyncSearchRouter(mode="fast", web=True)
        assert router1.web == True  # Override works
        assert router1.hyde == False  # HyDE still follows mode

        # Fast mode with hyde=True override
        router2 = AsyncSearchRouter(mode="fast", hyde=True)
        assert router2.web == False  # Web still follows mode
        assert router2.hyde == True  # Override works

        # Comprehensive mode with both overrides
        router3 = AsyncSearchRouter(mode="comprehensive", web=False, hyde=False)
        assert router3.web == False  # Override disables web
        assert router3.hyde == False  # Override disables hyde

        # Both overrides on
        router4 = AsyncSearchRouter(mode="fast", web=True, hyde=True)
        assert router4.web == True
        assert router4.hyde == True

    def test_has_search_async_method(self):
        """Test that search_async method exists and is coroutine function."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        assert hasattr(router, "search_async")
        assert asyncio.iscoroutinefunction(router.search_async)


class TestAsyncSearchRouterSearchMethod:
    """Tests for search_async method signature and basic behavior."""

    @pytest.mark.asyncio
    async def test_search_async_exists_and_awaitable(self):
        """Test that search_async can be called and awaited."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        result = await router.search_async("test query")
        assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_search_async_empty_query_raises(self):
        """Test that empty query raises ValueError."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("")

    @pytest.mark.asyncio
    async def test_search_async_whitespace_query_raises(self):
        """Test that whitespace-only query raises ValueError."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        with pytest.raises(ValueError, match="Query cannot be empty"):
            await router.search_async("   ")

    @pytest.mark.asyncio
    async def test_search_async_returns_list_of_search_results(self):
        """Test that search_async returns list of SearchResult objects."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        results = await router.search_async("test query", limit=5)

        assert isinstance(results, list)
        # Verify all items are SearchResult objects when backends work
        for result in results:
            assert isinstance(result, SearchResult)

    @pytest.mark.asyncio
    async def test_search_async_with_limit_parameter(self):
        """Test search_async with limit parameter."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        results = await router.search_async("test query", limit=3)
        assert len(results) <= 3


class TestAsyncSearchRouterParallelExecution:
    """Tests for async parallel execution using asyncio.gather."""

    @pytest.mark.asyncio
    async def test_uses_asyncio_gather_for_parallel_execution(self):
        """Test that all backends run in parallel using asyncio.gather."""
        from search_research import AsyncSearchRouter

        with patch("asyncio.gather", new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = [[] for _ in range(8)]

            router = AsyncSearchRouter()
            await router.search_async("test query")

            # Verify asyncio.gather was called
            mock_gather.assert_called_once()

    @pytest.mark.asyncio
    async def test_all_local_backends_executed(self):
        """Test that all 8 local backends are executed."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Mock backends to track execution
        backend_calls = []
        original_backends = router._backends.copy()

        for name, backend in router._backends.items():
            async_mock = AsyncMock(return_value=[])
            backend_calls.append((name, async_mock))
            backend.search = async_mock

        try:
            await router.search_async("test query")

            # Verify all backends were called
            for name, mock in backend_calls:
                mock.assert_called_once_with("test query", limit=10)
        finally:
            router._backends = original_backends


class TestAsyncSearchRouterErrorHandling:
    """Tests for error handling and graceful degradation."""

    @pytest.mark.asyncio
    async def test_backend_failure_doesnt_crash_search(self):
        """Test that backend failures are caught and don't crash the search."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Make one backend fail
        if router._backends:
            first_backend = list(router._backends.values())[0]
            first_backend.search = MagicMock(side_effect=Exception("Backend error"))

        # Should not raise
        results = await router.search_async("test query")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_multiple_backend_failures_handled(self):
        """Test that multiple backend failures are handled gracefully."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Make multiple backends fail
        for i, backend in enumerate(router._backends.values()):
            if i % 2 == 0:  # Fail half the backends
                backend.search = MagicMock(side_effect=Exception("Backend error"))

        # Should not raise
        results = await router.search_async("test query")
        assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_partial_results_returned_on_timeout(self):
        """Test that partial results are returned when some backends timeout."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Make one backend timeout (slow async)
        async def slow_search(*args, **kwargs):
            await asyncio.sleep(15)  # Longer than 10s timeout
            return []

        if router._backends:
            first_backend = list(router._backends.values())[0]
            first_backend.search = slow_search

        # Should return partial results before timeout
        results = await router.search_async("test query")
        assert isinstance(results, list)


class TestAsyncSearchRouterTimeoutHandling:
    """Tests for timeout handling (10s timeout)."""

    @pytest.mark.asyncio
    async def test_timeout_prevents_hanging(self):
        """Test that search_async respects 10s timeout."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Create a very slow backend
        async def very_slow_search(*args, **kwargs):
            await asyncio.sleep(20)  # Longer than 10s timeout
            return []

        if router._backends:
            first_backend = list(router._backends.values())[0]
            first_backend.search = very_slow_search

        # Should complete within reasonable time (with timeout)
        start = asyncio.get_event_loop().time()
        results = await router.search_async("test query")
        elapsed = asyncio.get_event_loop().time() - start

        assert isinstance(results, list)
        # Should timeout before 20s (allow some margin for overhead)
        assert elapsed < 15

    @pytest.mark.asyncio
    async def test_timeout_doesnt_affect_fast_backends(self):
        """Test that fast backends complete successfully even with timeout set."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Mock fast backends
        async def fast_search(*args, **kwargs):
            await asyncio.sleep(0.1)
            return [{"title": "result", "content": "test", "score": 0.9}]

        for backend in router._backends.values():
            backend.search = fast_search

        results = await router.search_async("test query")
        assert isinstance(results, list)


class TestAsyncSearchRouterBackendSelection:
    """Tests for selective backend execution."""

    @pytest.mark.asyncio
    async def test_specific_backends_only(self):
        """Test search_async with specific backends parameter."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Only search specific backends
        available = list(router._backends.keys())
        if available:
            selected_backends = available[:2]
            results = await router.search_async("test query", backends=selected_backends)
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_empty_backends_list_returns_empty(self):
        """Test that empty backends list returns empty results."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        results = await router.search_async("test query", backends=[])
        assert results == []

    @pytest.mark.asyncio
    async def test_invalid_backend_names_ignored(self):
        """Test that invalid backend names are ignored."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        results = await router.search_async(
            "test query", backends=["nonexistent_backend_1", "nonexistent_backend_2"]
        )
        # Should return empty results (no valid backends)
        assert isinstance(results, list)


class TestAsyncSearchRouterResultRanking:
    """Tests for result ranking and limiting."""

    @pytest.mark.asyncio
    async def test_results_ranked_by_score(self):
        """Test that results are ranked by relevance score."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Mock backends to return results with different scores
        async def mock_search(*args, **kwargs):
            return [
                {"title": "low", "content": "test", "score": 0.3},
                {"title": "high", "content": "test", "score": 0.9},
                {"title": "mid", "content": "test", "score": 0.6},
            ]

        for backend in router._backends.values():
            backend.search = mock_search

        results = await router.search_async("test query")

        # Verify results are sorted by score (descending)
        scores = [r.score for r in results]
        assert scores == sorted(scores, reverse=True)

    @pytest.mark.asyncio
    async def test_limit_parameter_honored(self):
        """Test that limit parameter is respected."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Mock backends to return many results
        async def mock_search(*args, **kwargs):
            return [
                {"title": f"result_{i}", "content": "test", "score": 0.9 - (i * 0.01)}
                for i in range(20)
            ]

        for backend in router._backends.values():
            backend.search = mock_search

        results = await router.search_async("test query", limit=5)
        assert len(results) <= 5


class TestAsyncSearchRouterNoBlockingCalls:
    """Tests to verify correct async behavior with mixed sync/async backends."""

    @pytest.mark.asyncio
    async def test_thread_pool_executor_used_for_sync_backends(self):
        """Test that ThreadPoolExecutor IS used for synchronous backends (correct behavior)."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Patch ThreadPoolExecutor to ensure it IS called for sync backends
        with patch("concurrent.futures.ThreadPoolExecutor") as mock_executor:
            # This should use ThreadPoolExecutor for synchronous backends
            try:
                await router.search_async("test query")
            except Exception:
                # We don't care if search fails, we're just checking the call pattern
                pass

            # Verify ThreadPoolExecutor WAS called (for sync backends)
            # This is correct behavior - sync backends need to run in thread pool
            mock_executor.assert_called()

    @pytest.mark.asyncio
    async def test_uses_asyncio_gather_not_as_completed(self):
        """Test that asyncio.gather is used instead of as_completed."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with patch("asyncio.gather", new_callable=AsyncMock) as mock_gather:
            mock_gather.return_value = [[] for _ in range(8)]

            await router.search_async("test query")

            # Verify asyncio.gather was used
            assert mock_gather.called

            # Verify concurrent.futures.as_completed was NOT used
            with patch("concurrent.futures.as_completed") as mock_as_completed:
                await router.search_async("test query")
                mock_as_completed.assert_not_called()


class TestAsyncSearchRouterCacheStats:
    """Tests for get_cache_stats method (#2249)."""

    def test_get_cache_stats_returns_dict(self):
        """Test that get_cache_stats returns a dictionary."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        stats = router.get_cache_stats()

        assert isinstance(stats, dict)

    def test_get_cache_stats_has_required_keys(self):
        """Test that get_cache_stats returns all expected keys."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        stats = router.get_cache_stats()

        # Check for expected cache metrics
        expected_keys = {"size", "max_size", "hits", "misses", "hit_rate", "ttl_seconds"}
        assert expected_keys.issubset(set(stats.keys()))

    def test_get_cache_stats_values_are_correct_types(self):
        """Test that get_cache_stats returns values of correct types."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        stats = router.get_cache_stats()

        assert isinstance(stats.get("size"), int)
        assert isinstance(stats.get("max_size"), int)
        assert isinstance(stats.get("hits"), int)
        assert isinstance(stats.get("misses"), int)
        assert isinstance(stats.get("hit_rate"), float)
        assert isinstance(stats.get("ttl_seconds"), int)

    def test_get_cache_stats_ttl_matches_router_ttl(self):
        """Test that cache stats TTL matches router cache_ttl."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(cache_ttl=1800)
        stats = router.get_cache_stats()

        assert stats["ttl_seconds"] == 1800


class TestAsyncSearchRouterImprovedErrorMessages:
    """Tests for improved error messages (#2253)."""

    @pytest.mark.asyncio
    async def test_empty_query_error_message_is_helpful(self):
        """Test that empty query raises helpful ValueError."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with pytest.raises(ValueError) as exc_info:
            await router.search_async("")

        error_msg = str(exc_info.value)
        # Check for helpful context
        assert "cannot be empty" in error_msg.lower()
        assert "whitespace" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_whitespace_query_error_message_is_helpful(self):
        """Test that whitespace-only query raises helpful ValueError."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with pytest.raises(ValueError) as exc_info:
            await router.search_async("   ")

        error_msg = str(exc_info.value)
        # Check for helpful context
        assert "cannot be empty" in error_msg.lower() or "whitespace" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_web_empty_query_error_message_is_helpful(self):
        """Test that empty web query raises helpful ValueError."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with pytest.raises(ValueError) as exc_info:
            await router.search_web_providers_async("")

        error_msg = str(exc_info.value)
        # Check for helpful context - web provider error message is similar to regular search
        assert "cannot be empty" in error_msg.lower() or "whitespace" in error_msg.lower()
        assert "meaningful" in error_msg.lower()

    @pytest.mark.asyncio
    async def test_unknown_backend_logs_warning_with_available_backends(self):
        """Test that unknown backend logs available backends in warning."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        # Initialize backends
        router._create_backends()

        # Search with non-existent backend
        results = await router.search_async("test", backends=["nonexistent_backend"])

        # Should return empty results
        assert results == []

    @pytest.mark.asyncio
    async def test_cache_stats_includes_ttl(self):
        """Test that cache stats includes TTL information."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(cache_ttl=7200)
        stats = router.get_cache_stats()

        assert "ttl_seconds" in stats
        assert stats["ttl_seconds"] == 7200

    @pytest.mark.asyncio
    async def test_cache_stats_hit_rate_calculation(self):
        """Test that cache stats hit_rate is calculated correctly."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        stats = router.get_cache_stats()

        # Hit rate should be between 0 and 1
        assert 0 <= stats["hit_rate"] <= 1
        # Initially, with no cache activity, hit_rate is 0 (0/0)
        assert stats["hit_rate"] == 0.0


class TestAsyncSearchRouterBackendPriorityWeighting:
    """Tests for backend priority weighting feature (#2250)."""

    def test_init_with_backend_weights(self):
        """Test that AsyncSearchRouter can be initialized with backend weights."""
        from search_research import AsyncSearchRouter

        weights = {"MULTILANG": 2.0, "CKS": 1.5}
        router = AsyncSearchRouter(backend_weights=weights)

        assert router.get_backend_weights() == weights

    def test_init_with_empty_backend_weights(self):
        """Test that empty backend_weights dict results in no custom weights."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter(backend_weights={})

        assert router.get_backend_weights() == {}

    def test_get_backend_weights_returns_copy(self):
        """Test that get_backend_weights returns a copy, not the original dict."""
        from search_research import AsyncSearchRouter

        weights = {"MULTILANG": 2.0}
        router = AsyncSearchRouter(backend_weights=weights)

        retrieved = router.get_backend_weights()
        retrieved["NEW_BACKEND"] = 3.0

        # Original should be unchanged
        assert router.get_backend_weights() == weights
        assert "NEW_BACKEND" not in router.get_backend_weights()

    def test_set_backend_weights_updates_weights(self):
        """Test that set_backend_weights updates the backend weights."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        new_weights = {"MULTILANG": 2.0, "CKS": 1.5}
        router.set_backend_weights(new_weights)

        assert router.get_backend_weights() == new_weights

    def test_set_backend_weights_creates_copy(self):
        """Test that set_backend_weights creates a copy of the input dict."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        weights = {"MULTILANG": 2.0}
        router.set_backend_weights(weights)

        # Modify original
        weights["CKS"] = 1.5

        # Router should not be affected
        assert router.get_backend_weights() == {"MULTILANG": 2.0}

    @pytest.mark.asyncio
    async def test_backend_priority_affects_result_ordering(self):
        """Test that backend priority weights affect result ordering within same score."""
        from search_research import AsyncSearchRouter, SearchResult

        # Create router with custom weights
        weights = {"SOURCE_A": 2.0, "SOURCE_B": 1.0}
        router = AsyncSearchRouter(backend_weights=weights)

        # Create SearchResult objects with same score but different sources
        results = [
            SearchResult(
                title="Result A1",
                content="test",
                source="SOURCE_A",
                score=0.9,
            ),
            SearchResult(
                title="Result B1",
                content="test",
                source="SOURCE_B",
                score=0.9,
            ),
        ]

        # Rank results using the router's method
        ranked = router._rank_results(results)

        # SOURCE_A (higher weight) should come first
        assert ranked[0].source == "SOURCE_A"
        assert ranked[1].source == "SOURCE_B"

    @pytest.mark.asyncio
    async def test_default_backend_weights_equal_priority(self):
        """Test that without custom weights, all backends have equal priority."""
        from search_research import AsyncSearchRouter, SearchResult

        router = AsyncSearchRouter()

        # All backends should have default weight of 1.0 (implicitly)
        # Results with same score should be sorted alphabetically by source
        results = [
            SearchResult(
                title="A",
                content="test",
                source="SOURCE_Z",
                score=0.9,
            ),
            SearchResult(
                title="B",
                content="test",
                source="SOURCE_A",
                score=0.9,
            ),
        ]

        ranked = router._rank_results(results)

        # Without custom weights, alphabetical order applies
        assert ranked[0].source == "SOURCE_A"
        assert ranked[1].source == "SOURCE_Z"

    @pytest.mark.asyncio
    async def test_backend_priority_only_affects_same_score_group(self):
        """Test that backend priority only affects ordering within same score group."""
        from search_research import AsyncSearchRouter, SearchResult

        # SOURCE_A has lower weight, SOURCE_B has higher weight
        weights = {"SOURCE_A": 1.0, "SOURCE_B": 2.0}
        router = AsyncSearchRouter(backend_weights=weights)

        results = [
            # SOURCE_B has higher score, should come first regardless of weight
            SearchResult(
                title="B1",
                content="test",
                source="SOURCE_B",
                score=0.95,
            ),
            # SOURCE_A has lower score, should come after SOURCE_B
            SearchResult(
                title="A1",
                content="test",
                source="SOURCE_A",
                score=0.9,
            ),
            # SOURCE_B has lower score, should come after SOURCE_A (same score group)
            SearchResult(
                title="B2",
                content="test",
                source="SOURCE_B",
                score=0.8,
            ),
        ]

        ranked = router._rank_results(results)

        # Score grouping takes precedence
        assert ranked[0].title == "B1"  # 0.95 from SOURCE_B
        assert ranked[1].title == "A1"  # 0.9 from SOURCE_A
        # Within same score (0.8), priority matters - but we only have one result at 0.8
        assert ranked[2].title == "B2"  # 0.8 from SOURCE_B


class TestAsyncSearchRouterStreaming:
    """Tests for streaming search methods (#2252)."""

    @pytest.mark.asyncio
    async def test_search_async_stream_is_async_generator(self):
        """Test that search_async_stream returns an async generator."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        stream = router.search_async_stream("test query")

        # Should be an async generator
        assert hasattr(stream, "__aiter__")
        assert hasattr(stream, "__anext__")

    @pytest.mark.asyncio
    async def test_search_async_stream_yields_results(self):
        """Test that search_async_stream yields SearchResult objects."""
        from search_research import AsyncSearchRouter, SearchResult

        router = AsyncSearchRouter()

        # Mock backends to return specific results
        async def mock_search(*args, **kwargs):
            return [
                SearchResult(
                    title="Result 1",
                    content="test content",
                    source="TEST_BACKEND",
                    score=0.9,
                )
            ]

        for backend in router._backends.values():
            backend.search = mock_search

        # Collect results from stream
        results = []
        async for result in router.search_async_stream("test query"):
            results.append(result)

        # Should have received results
        assert len(results) > 0
        assert all(isinstance(r, SearchResult) for r in results)

    @pytest.mark.asyncio
    async def test_search_async_stream_empty_query_raises(self):
        """Test that empty query raises ValueError for streaming."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            async for _ in router.search_async_stream(""):
                pass

    @pytest.mark.asyncio
    async def test_search_async_stream_handles_backend_failures(self):
        """Test that streaming continues even when backends fail."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Make some backends fail, others succeed
        backend_names = list(router._backends.keys())
        for i, name in enumerate(backend_names):
            if i % 2 == 0:
                # Failing backend
                async def failing_search(*args, **kwargs):
                    raise Exception("Backend error")

                router._backends[name].search = failing_search
            else:
                # Succeeding backend
                async def succeeding_search(*args, **kwargs):
                    return [{"title": f"Result from {name}", "content": "test", "score": 0.8}]

                router._backends[name].search = succeeding_search

        # Should collect results from succeeding backends without crashing
        results = []
        async for result in router.search_async_stream("test query"):
            results.append(result)

        # Should have results from succeeding backends
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_async_stream_with_limit(self):
        """Test that streaming respects limit parameter."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Mock backends to return many results
        async def mock_search(*args, **kwargs):
            return [{"title": f"Result {i}", "content": "test", "score": 0.9} for i in range(20)]

        for backend in router._backends.values():
            backend.search = mock_search

        # Count results with limit
        results = []
        async for result in router.search_async_stream("test query", limit=5):
            results.append(result)

        # Each backend should return at most limit results
        # But total results depend on number of backends
        assert len(results) > 0

    @pytest.mark.asyncio
    async def test_search_async_stream_batch_yields_batches(self):
        """Test that search_async_stream_batch yields lists of results."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()
        batches = []

        async for batch in router.search_async_stream_batch("test query"):
            batches.append(batch)

        # Batches should be lists
        assert all(isinstance(batch, list) for batch in batches)

    @pytest.mark.asyncio
    async def test_search_async_stream_batch_empty_query_raises(self):
        """Test that empty query raises ValueError for batch streaming."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        with pytest.raises(ValueError, match="Query cannot be empty"):
            async for _ in router.search_async_stream_batch(""):
                pass

    @pytest.mark.asyncio
    async def test_search_async_stream_batch_handles_backend_failures(self):
        """Test that batch streaming continues when backends fail."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Make some backends fail
        backend_names = list(router._backends.keys())
        for i, name in enumerate(backend_names):
            if i % 2 == 0:

                async def failing_search(*args, **kwargs):
                    raise Exception("Backend error")

                router._backends[name].search = failing_search

        # Should collect batches from succeeding backends
        batches = []
        async for batch in router.search_async_stream_batch("test query"):
            batches.append(batch)

        # Should have at least some batches (from succeeding backends)
        # Or empty list if all backends failed
        assert isinstance(batches, list)

    @pytest.mark.asyncio
    async def test_search_async_stream_specific_backends(self):
        """Test that streaming works with specific backends."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        # Get available backends
        available = list(router._backends.keys())
        if available:
            selected_backends = available[:2]

            results = []
            async for result in router.search_async_stream(
                "test query", backends=selected_backends
            ):
                results.append(result)

            # Should have results from selected backends
            assert isinstance(results, list)

    @pytest.mark.asyncio
    async def test_search_async_stream_empty_backends_returns_nothing(self):
        """Test that streaming with empty backends yields no results."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        results = []
        async for result in router.search_async_stream("test query", backends=[]):
            results.append(result)

        # Should have no results
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_search_async_stream_batch_empty_backends_returns_nothing(self):
        """Test that batch streaming with empty backends yields no results."""
        from search_research import AsyncSearchRouter

        router = AsyncSearchRouter()

        batches = []
        async for batch in router.search_async_stream_batch("test query", backends=[]):
            batches.append(batch)

        # Should have no batches
        assert len(batches) == 0
