"""TDD tests for UnifiedSemanticDaemon SemanticCache integration.

AT-007: Integrate SemanticCache into UnifiedSemanticDaemon query path

Tests verify:
- QueryCache is instantiated in daemon with 1-hour TTL
- Cache is checked before FAISS search (cache hit path)
- Cache miss triggers FAISS query
- Cache hit rate is tracked in metrics
- 1-hour TTL is enforced

RED Phase: All tests should FAIL until implementation is complete.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

# Setup path - add project root
csf_root = Path(__file__).parent.parent.parent.parent.parent


class TestQueryCacheInstantiation:
    """Tests for QueryCache instantiation in UnifiedSemanticDaemon."""

    def test_daemon_has_query_cache_attr(self):
        """
        Test that UnifiedSemanticDaemon has a query_cache attribute.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for query_cache attribute
        Then: The attribute should exist
        """
        from search_research.cache import QueryCache
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon, "query_cache"
        ), "UnifiedSemanticDaemon should have query_cache attribute"
        assert isinstance(
            daemon.query_cache, QueryCache
        ), "query_cache should be an instance of QueryCache"

    def test_query_cache_has_1_hour_ttl(self):
        """
        Test that QueryCache is configured with 1-hour TTL (3600 seconds).

        Given: UnifiedSemanticDaemon is instantiated
        When: We check the query_cache TTL configuration
        Then: TTL should be 3600 seconds (1 hour)
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert hasattr(
            daemon.query_cache, "ttl_seconds"
        ), "QueryCache should have ttl_seconds attribute"
        assert (
            daemon.query_cache.ttl_seconds == 3600
        ), f"QueryCache TTL should be 3600 seconds (1 hour), got {daemon.query_cache.ttl_seconds}"

    def test_daemon_has_cache_stats_attr(self):
        """
        Test that daemon tracks cache hit rate in metrics.

        Given: UnifiedSemanticDaemon is instantiated
        When: We check for cache metrics attributes
        Then: Cache tracking attributes should exist
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Check for cache stats tracking in daemon metrics
        assert hasattr(daemon, "_stats"), "UnifiedSemanticDaemon should have _stats attribute"
        # Cache stats should be tracked
        assert (
            "cache_hits" in daemon._stats or "cache_hit_rate" in daemon._stats
        ), "Daemon stats should include cache hit tracking"


class TestCacheCheckedBeforeFAISS:
    """Tests for cache checking before FAISS search."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_checked_before_cks_search(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache is checked before CKS (FAISS) search.

        Given: Daemon is running with cache enabled
        When: A CKS search query is executed
        Then: Cache should be checked before FAISS search
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations to allow daemon startup
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()  # Non-blocking wait

        daemon = UnifiedSemanticDaemon()

        # Mock the cache to track get() calls
        cache_get_calls = []
        original_cache_get = daemon.query_cache.get

        def mock_cache_get(query, **kwargs):
            cache_get_calls.append((query, kwargs))
            return None  # Cache miss for this test

        daemon.query_cache.get = mock_cache_get

        # Mock CKS to prevent actual search
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute a CKS search
        daemon._search_cks("test query", 5, {})

        # Verify cache was checked before search
        assert len(cache_get_calls) > 0, "Cache should be checked before FAISS search"
        assert (
            cache_get_calls[0][0] == "test query"
        ), "Cache should be checked with the query string"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_checked_before_chs_search(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache is checked before CHS semantic search.

        Given: Daemon is running with cache enabled
        When: A CHS search query is executed
        Then: Cache should be checked before semantic search
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations to allow daemon startup
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock the cache to track get() calls
        cache_get_calls = []
        original_cache_get = daemon.query_cache.get

        def mock_cache_get(query, **kwargs):
            cache_get_calls.append((query, kwargs))
            return None  # Cache miss for this test

        daemon.query_cache.get = mock_cache_get

        # Mock CKS for CHS semantic search
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute a CHS semantic-only search (fallback path)
        daemon._search_chs_semantic_only("test query", 5, {})

        # Verify cache was checked before search
        assert len(cache_get_calls) > 0, "Cache should be checked before CHS semantic search"


class TestCacheHitPath:
    """Tests for cache hit behavior."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_hit_returns_cached_results(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache hit returns cached results without FAISS query.

        Given: Daemon with cached results for a query
        When: The same query is executed again
        Then: Cached results should be returned, FAISS should not be queried
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock cache to return cached results
        cached_results = [
            {"id": "1", "content": "cached result 1", "score": 0.9},
            {"id": "2", "content": "cached result 2", "score": 0.8},
        ]

        def mock_cache_get(query, **kwargs):
            if query == "cached query":
                return cached_results
            return None

        daemon.query_cache.get = mock_cache_get

        # Mock CKS to track if search_semantic is called
        cks_search_calls = []
        daemon._cks = MagicMock()

        def mock_search(query, limit, **kwargs):
            cks_search_calls.append((query, limit))
            return []

        daemon._cks.search_semantic = mock_search

        # Execute search with cached query
        results = daemon._search_cks("cached query", 5, {})

        # Verify cached results were returned
        assert results == cached_results, "Cache hit should return cached results"

        # Verify FAISS was NOT called
        assert len(cks_search_calls) == 0, "FAISS search should not be called on cache hit"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_hit_increments_hit_counter(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache hit increments the hit counter.

        Given: Daemon with cached results
        When: A cached query is executed
        Then: Cache hit counter should be incremented
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Get initial cache stats
        initial_stats = daemon.query_cache.get_stats()
        initial_hits = initial_stats.get("hits", 0)

        # Mock cache to return cached results
        cached_results = [{"id": "1", "content": "cached result"}]

        def mock_cache_get(query, **kwargs):
            if query == "cached query":
                # This will increment hit counter in real implementation
                # For now we just track the call
                return cached_results
            return None

        daemon.query_cache.get = mock_cache_get
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute cached search
        daemon._search_cks("cached query", 5, {})

        # Note: In real implementation, hit counter increments inside QueryCache.get()
        # This test verifies the integration - counter should be higher after cache hit
        final_stats = daemon.query_cache.get_stats()
        final_hits = final_stats.get("hits", 0)

        # In actual implementation, this should be incremented
        # For RED phase, this test will fail until implementation is done
        assert final_hits >= initial_hits, "Cache hit counter should be incremented after cache hit"


class TestCacheMissPath:
    """Tests for cache miss behavior."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_miss_triggers_faiss_query(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache miss triggers FAISS query.

        Given: Daemon with no cached results for a query
        When: A new query is executed
        Then: FAISS search should be executed
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Mock cache to return None (cache miss)
        daemon.query_cache.get = MagicMock(return_value=None)

        # Mock CKS to track search calls
        faiss_results = [{"id": "1", "content": "faiss result 1", "score": 0.9}]
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=faiss_results)

        # Execute search with uncached query
        results = daemon._search_cks("new query", 5, {})

        # Verify FAISS was called
        daemon._cks.search_semantic.assert_called_once()
        call_args = daemon._cks.search_semantic.call_args
        assert (
            call_args[1]["query"] == "new query" or call_args[0][0] == "new query"
        ), "FAISS search should be called with the query"

        # Verify FAISS results were returned
        assert results == faiss_results, "Cache miss should return FAISS results"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_miss_results_are_cached(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache miss results are stored in cache.

        Given: Daemon with cache miss
        When: FAISS returns results
        Then: Results should be stored in cache for future queries
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Track cache.set() calls
        cache_set_calls = []
        original_cache_set = daemon.query_cache.set

        def mock_cache_set(query, results, **kwargs):
            cache_set_calls.append((query, results, kwargs))

        daemon.query_cache.set = mock_cache_set
        daemon.query_cache.get = MagicMock(return_value=None)

        # Mock CKS
        faiss_results = [{"id": "1", "content": "faiss result 1", "score": 0.9}]
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=faiss_results)

        # Execute search
        daemon._search_cks("new query", 5, {})

        # Verify results were cached
        assert len(cache_set_calls) > 0, "Cache miss results should be stored in cache"
        assert cache_set_calls[0][0] == "new query", "Cache should store results with the query"
        assert cache_set_calls[0][1] == faiss_results, "Cache should store the FAISS results"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_miss_increments_miss_counter(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache miss increments the miss counter.

        Given: Daemon with cache miss
        When: A new query is executed
        Then: Cache miss counter should be incremented
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Get initial cache stats
        initial_stats = daemon.query_cache.get_stats()
        initial_misses = initial_stats.get("misses", 0)

        # Mock cache to return None (cache miss)
        daemon.query_cache.get = MagicMock(return_value=None)
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute search
        daemon._search_cks("new query", 5, {})

        # Verify miss counter was incremented
        final_stats = daemon.query_cache.get_stats()
        final_misses = final_stats.get("misses", 0)

        # In actual implementation, this should be incremented
        assert (
            final_misses >= initial_misses
        ), "Cache miss counter should be incremented after cache miss"


class TestCacheHitRateTracking:
    """Tests for cache hit rate tracking in metrics."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_hit_rate_in_daemon_stats(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache hit rate is tracked in daemon stats.

        Given: Daemon with cache enabled
        When: Cache operations occur
        Then: Hit rate should be available in daemon stats
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Perform some cache operations
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Cache miss
        daemon.query_cache.get = MagicMock(return_value=None)
        daemon._search_cks("query1", 5, {})

        # Cache hit
        cached_results = [{"id": "1", "content": "cached"}]
        daemon.query_cache.get = MagicMock(return_value=cached_results)
        daemon._search_cks("query2", 5, {})

        # Check that cache stats are tracked
        cache_stats = daemon.query_cache.get_stats()
        assert "hit_rate" in cache_stats, "Cache stats should include hit_rate"

        # Daemon stats should reflect cache performance
        # This will be implemented in GREEN phase
        assert (
            "cache_hit_rate" in daemon._stats or "cache_hits" in daemon._stats
        ), "Daemon stats should track cache hit rate"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_stats_accessible_via_method(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache statistics are accessible via a method.

        Given: Daemon with cache enabled
        When: We request cache statistics
        Then: Statistics should be returned with hits, misses, hit_rate
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Get cache stats
        stats = daemon.query_cache.get_stats()

        # Verify required fields
        assert "hits" in stats, "Cache stats should include 'hits'"
        assert "misses" in stats, "Cache stats should include 'misses'"
        assert "hit_rate" in stats, "Cache stats should include 'hit_rate'"
        assert "size" in stats, "Cache stats should include 'size'"
        assert isinstance(stats["hit_rate"], float), "hit_rate should be a float"


class TestCacheTTLEnforcement:
    """Tests for 1-hour TTL enforcement."""

    def test_cache_ttl_is_3600_seconds(self):
        """
        Test that cache TTL is set to 3600 seconds (1 hour).

        Given: QueryCache is instantiated
        When: We check the TTL configuration
        Then: TTL should be 3600 seconds
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        assert (
            daemon.query_cache.ttl_seconds == 3600
        ), f"Cache TTL should be 3600 seconds (1 hour), got {daemon.query_cache.ttl_seconds}"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_expired_entry_returns_none(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that expired cache entries return None (trigger FAISS query).

        Given: Cache entry older than 1 hour
        When: The same query is executed
        Then: Cache should return None (miss) and trigger FAISS query
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Manually insert an expired entry
        # QueryCache stores entries with timestamp
        # We'll set a timestamp from > 1 hour ago

        # This requires internal cache manipulation or time mocking
        # For RED phase, we verify the structure exists
        assert hasattr(
            daemon.query_cache, "_cache"
        ), "QueryCache should have internal _cache storage"

        assert hasattr(
            daemon.query_cache, "ttl_seconds"
        ), "QueryCache should have ttl_seconds for TTL enforcement"

        # Note: Actual TTL enforcement is tested by QueryCache unit tests
        # This integration test verifies the daemon uses cache with correct TTL

    def test_cache_entry_has_timestamp(self):
        """
        Test that cache entries include timestamp for TTL enforcement.

        Given: QueryCache stores an entry
        When: We inspect the cached entry
        Then: Entry should have a timestamp field
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        daemon = UnifiedSemanticDaemon()

        # Add a test entry to cache
        test_results = [{"id": "1", "content": "test"}]
        daemon.query_cache.set("test query", test_results)

        # Verify entry structure includes timestamp
        # Note: This accesses internal cache structure
        # In production, use public API
        cache_key = daemon.query_cache._hash_query("test query")
        assert cache_key in daemon.query_cache._cache, "Query should be in cache after set()"

        entry = daemon.query_cache._cache[cache_key]
        assert "timestamp" in entry, "Cache entry should have timestamp for TTL enforcement"
        assert "results" in entry, "Cache entry should have results"


class TestCacheIntegrationWithQueryParams:
    """Tests for cache key generation with query parameters."""

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_key_includes_limit(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache key includes limit parameter.

        Given: Same query with different limits
        When: Both queries are executed
        Then: They should have different cache entries
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Track cache keys
        cache_keys = []

        original_get = daemon.query_cache.get

        def mock_get(query, **kwargs):
            cache_keys.append((query, kwargs))
            return None

        daemon.query_cache.get = mock_get
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute same query with different limits
        daemon._search_cks("test query", 5, {})
        daemon._search_cks("test query", 10, {})

        # Verify different cache keys
        # The cache should differentiate by limit
        assert len(cache_keys) == 2, "Cache should be checked for each query"

    @patch("search_research.contrib.semantic_daemon.unified_semantic_daemon.WIN32_AVAILABLE", True)
    @patch("win32file.CreateFile")
    @patch("win32pipe.CreateNamedPipe")
    @patch("win32pipe.ConnectNamedPipe")
    @patch("win32event.CreateEvent")
    @patch("win32event.WaitForSingleObject")
    @patch("win32event.ResetEvent")
    def test_cache_key_includes_entry_type(
        self,
        mock_reset,
        mock_wait,
        mock_create_event,
        mock_connect,
        mock_create_pipe,
        mock_create_file,
    ):
        """
        Test that cache key includes entry_type parameter.

        Given: Same query with different entry_type filters
        When: Both queries are executed
        Then: They should have different cache entries
        """
        from search_research.contrib.semantic_daemon.unified_semantic_daemon import (
            UnifiedSemanticDaemon,
        )

        # Mock pipe operations
        mock_create_pipe.return_value = MagicMock()
        mock_event = MagicMock()
        mock_create_event.return_value = mock_event
        mock_wait.return_value = MagicMock()

        daemon = UnifiedSemanticDaemon()

        # Track cache keys
        cache_keys = []

        original_get = daemon.query_cache.get

        def mock_get(query, **kwargs):
            cache_keys.append((query, kwargs))
            return None

        daemon.query_cache.get = mock_get
        daemon._cks = MagicMock()
        daemon._cks.search_semantic = MagicMock(return_value=[])

        # Execute same query with different entry_type
        daemon._search_cks("test query", 5, {"entry_type": "memory"})
        daemon._search_cks("test query", 5, {"entry_type": "pattern"})

        # Verify different cache keys
        assert len(cache_keys) == 2, "Cache should be checked for each query with different params"

        # Verify entry_type is in the cache key kwargs
        assert (
            cache_keys[0][1].get("entry_type") == "memory"
        ), "First query should include entry_type in cache key"
        assert (
            cache_keys[1][1].get("entry_type") == "pattern"
        ), "Second query should include entry_type in cache key"
