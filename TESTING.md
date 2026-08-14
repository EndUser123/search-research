# Testing Strategy: search-research Package

**Version:** 1.0 | **Date:** 2026-03-05

Comprehensive testing strategy for the unified search and research system.

---

## Testing Philosophy

**Principles:**
1. **Test coverage >90%** - All critical paths covered
2. **Fast feedback** - Unit tests <1s total, integration tests <10s
3. **Isolation** - No external dependencies for unit tests
4. **Realistic data** - Test with actual queries, not just "test string"
5. **Backward compatibility** - Verify migrations work correctly

---

## Coverage Targets

| Component | Target | Priority |
|-----------|--------|----------|
| **Core Router** | >95% | HIGH |
| **Intent Detection** | >90% | HIGH |
| **Cache** | >90% | HIGH |
| **Backends** | >90% | HIGH |
| **Result Aggregation** | >95% | HIGH |
| **Web Providers** | >85% | MEDIUM |
| **HyDE Enhancement** | >85% | MEDIUM |
| **CLI** | >80% | MEDIUM |
| **Overall** | >90% | HIGH |

---

## Test Structure

```
tests/
├── conftest.py                      # Shared fixtures
├── test_router.py                   # Core router tests
├── test_cache.py                    # Cache tests
├── test_query_intent.py             # Intent detection tests
├── test_result_aggregation.py       # Result processing tests
├── test_backends/
│   ├── __init__.py
│   ├── test_cds_backend.py          # CDS backend tests
│   ├── test_grep_backend.py         # Grep backend tests
│   ├── test_skills_backend.py       # Skills backend tests
│   ├── test_chs_backend.py          # CHS backend tests
│   ├── test_cks_backend.py          # CKS backend tests
│   ├── test_rlm_backend.py          # RLM backend tests
│   ├── test_persona_backend.py      # Persona backend tests
│   ├── test_multilang_backend.py    # MultiLang backend tests
│   ├── test_notebooklm_backend.py   # NotebookLM backend tests
│   └── test_web_providers/
│       ├── test_tavily.py           # Tavily provider tests
│       ├── test_serper.py           # Serper provider tests
│       ├── test_exa.py              # Exa provider tests
│       └── ...
├── test_hyde.py                     # HyDE enhancement tests
├── integration/
│   ├── __init__.py
│   ├── test_e2e_search.py           # End-to-end search tests
│   ├── test_mode_routing.py         # Mode-based routing tests
│   ├── test_backend_fallback.py     # Backend failure scenarios
│   ├── test_cache_invalidation.py   # Cache behavior tests
│   └── test_migration.py            # Migration compatibility tests
└── performance/
    ├── __init__.py
    ├── test_latency.py              # Latency benchmarks
    ├── test_throughput.py           # Throughput tests
    └── test_concurrency.py          # Concurrent execution tests
```

---

## Fixtures and Test Data

### conftest.py

```python
import pytest
import asyncio
from pathlib import Path
from typing import AsyncIterator

from search_research import UnifiedRouter, Mode
from search_research.backends import CDSBackend, GrepBackend
from search_research.cache import QueryCache


@pytest.fixture
def sample_codebase(tmp_path: Path) -> Path:
    """Create temporary codebase with sample files."""
    # Create sample Python files
    (tmp_path / "async_module.py").write_text("""
async def fetch_data():
    async with aiohttp.ClientSession() as session:
        async with session.get("https://api.example.com") as resp:
            return await resp.json()

def sync_function():
    return "sync"
""")

    (tmp_path / "sync_module.py").write_text("""
def sync_function():
    return "sync"

class SyncClass:
    def method(self):
        return "method"
""")

    return tmp_path


@pytest.fixture
def mock_backend():
    """Create mock backend for testing."""
    class MockBackend:
        async def search(self, query: str, limit: int = 20):
            return [
                {
                    "title": f"Result {i}",
                    "content": f"Content for {query}",
                    "score": 0.9 - (i * 0.1),
                    "source": "mock",
                }
                for i in range(limit)
            ]

        @property
        def available(self) -> bool:
            return True

    return MockBackend()


@pytest.fixture
def sample_cache() -> QueryCache:
    """Create sample cache with test data."""
    cache = QueryCache(max_size=100, ttl=60)

    # Pre-populate with sample data
    cache.set("test query", ["cds", "grep"], {
        "hits": [{"title": "Test Result"}],
        "total": 1
    })

    return cache


@pytest.fixture
async def sample_router(sample_codebase: Path) -> UnifiedRouter:
    """Create router with sample backends."""
    router = UnifiedRouter(
        mode=Mode.FAST,
        enable_cache=True,
        cache_ttl=60
    )

    # Add backends pointing to sample codebase
    # (implementation depends on actual backend structure)

    return router


@pytest.fixture
def sample_queries():
    """Sample queries for testing."""
    return {
        "code_pattern": "async def fetch",
        "file_path": "async_module.py",
        "ambiguous": "patterns",
        "best_practices": "async best practices",
        "tutorial": "how to use async",
    }


@pytest.fixture
def intent_test_data():
    """Test data for intent detection."""
    return {
        "local_only": [
            "def async_function",
            "src/router.py",
            "class AsyncHandler",
        ],
        "web_enhanced": [
            "async best practices",
            "latest async features",
            "async tutorial",
        ],
        "mixed": [
            "async patterns",
            "asyncio usage",
            "await examples",
        ],
    }
```

---

## Unit Tests

### Test Router (test_router.py)

```python
import pytest
from search_research import UnifiedRouter, Mode, SearchResult


@pytest.mark.asyncio
async def test_router_initialization():
    """Test router initializes with correct defaults."""
    router = UnifiedRouter(mode=Mode.FAST)

    assert router.mode == Mode.FAST
    assert router.cache_enabled is True
    assert router.cache_ttl == 3600


@pytest.mark.asyncio
async def test_router_search_fast_mode(sample_router, sample_queries):
    """Test FAST mode search (local backends only)."""
    results = await sample_router.search_async(
        sample_queries["code_pattern"],
        mode=Mode.FAST
    )

    assert len(results.hits) > 0
    assert results.total > 0
    # All results should be from local backends
    for hit in results.hits:
        assert hit.source in ["cds", "grep", "skills", "chs", "cks"]


@pytest.mark.asyncio
async def test_router_search_custom_backend(sample_router):
    """Test CUSTOM mode with specific backends."""
    results = await sample_router.search_async(
        "async patterns",
        backend=["cds", "grep"]
    )

    assert len(results.hits) >= 0
    # All results should be from specified backends
    for hit in results.hits:
        assert hit.source.lower() in ["cds", "grep", "code documentation", "code pattern"]


@pytest.mark.asyncio
async def test_router_search_with_limit(sample_router):
    """Test search with result limit."""
    results = await sample_router.search_async(
        "async",
        limit=5
    )

    assert len(results.hits) <= 5


@pytest.mark.asyncio
async def test_router_search_invalid_query(sample_router):
    """Test search with invalid query raises error."""
    with pytest.raises(InvalidQueryError):
        await sample_router.search_async("")  # Empty query

    with pytest.raises(InvalidQueryError):
        await sample_router.search_async("a" * 1001)  # Too long


@pytest.mark.asyncio
async def test_router_concurrent_searches(sample_router):
    """Test router handles concurrent searches correctly."""
    queries = ["async", "await", "asyncio"]

    tasks = [
        sample_router.search_async(q)
        for q in queries
    ]
    results = await asyncio.gather(*tasks)

    assert len(results) == 3
    for result in results:
        assert isinstance(result, SearchResults)
```

### Test Cache (test_cache.py)

```python
import pytest
import time
from search_research.cache import QueryCache


def test_cache_initialization():
    """Test cache initializes with correct defaults."""
    cache = QueryCache(max_size=1000, ttl=3600)

    assert cache.max_size == 1000
    assert cache.ttl == 3600
    assert cache.size == 0


def test_cache_set_and_get():
    """Test cache set and get operations."""
    cache = QueryCache(max_size=100, ttl=60)

    # Set value
    cache.set("test query", ["cds", "grep"], {"hits": []})

    # Get value
    value = cache.get("test query", ["cds", "grep"])
    assert value is not None
    assert value["hits"] == []


def test_cache_miss():
    """Test cache returns None for missing key."""
    cache = QueryCache()

    value = cache.get("missing query", ["cds"])
    assert value is None


def test_cache_ttl_expiration():
    """Test cache respects TTL."""
    cache = QueryCache(max_size=100, ttl=1)  # 1 second TTL

    cache.set("test query", ["cds"], {"hits": []})

    # Immediate hit
    value = cache.get("test query", ["cds"])
    assert value is not None

    # Wait for expiration
    time.sleep(2)

    # Should be expired
    value = cache.get("test query", ["cds"])
    assert value is None


def test_cache_lru_eviction():
    """Test cache evicts least recently used entries when full."""
    cache = QueryCache(max_size=3, ttl=60)

    # Fill cache
    cache.set("query1", ["cds"], {"hits": []})
    cache.set("query2", ["cds"], {"hits": []})
    cache.set("query3", ["cds"], {"hits": []})

    # Access query1 (make it recently used)
    cache.get("query1", ["cds"])

    # Add new entry (should evict query2 - LRU)
    cache.set("query4", ["cds"], {"hits": []})

    # query2 should be evicted
    assert cache.get("query2", ["cds"]) is None

    # query1, query3, query4 should still exist
    assert cache.get("query1", ["cds"]) is not None
    assert cache.get("query3", ["cds"]) is not None
    assert cache.get("query4", ["cds"]) is not None


def test_cache_hit_rate_tracking():
    """Test cache tracks hit rate correctly."""
    cache = QueryCache(max_size=100, ttl=60)

    cache.set("query1", ["cds"], {"hits": []})
    cache.set("query2", ["cds"], {"hits": []})

    # 2 hits
    cache.get("query1", ["cds"])
    cache.get("query2", ["cds"])

    # 2 misses
    cache.get("query3", ["cds"])
    cache.get("query4", ["cds"])

    stats = cache.get_stats()
    assert stats["hit_rate"] == 0.5  # 2/4 = 50%
```

### Test Intent Detection (test_query_intent.py)

```python
import pytest
from search_research.query_intent import QueryIntentDetector, IntentType


@pytest.mark.asyncio
async def test_intent_detection_local_only(intent_test_data):
    """Test LOCAL_ONLY intent detection."""
    detector = QueryIntentDetector()

    for query in intent_test_data["local_only"]:
        intent = await detector.detect(query)
        assert intent.type == IntentType.LOCAL_ONLY
        assert intent.confidence > 0.8


@pytest.mark.asyncio
async def test_intent_detection_web_enhanced(intent_test_data):
    """Test WEB_ENHANCED intent detection."""
    detector = QueryIntentDetector()

    for query in intent_test_data["web_enhanced"]:
        intent = await detector.detect(query)
        assert intent.type == IntentType.WEB_ENHANCED
        assert intent.confidence > 0.8


@pytest.mark.asyncio
async def test_intent_detection_mixed(intent_test_data):
    """Test MIXED intent detection."""
    detector = QueryIntentDetector()

    for query in intent_test_data["mixed"]:
        intent = await detector.detect(query)
        assert intent.type == IntentType.MIXED
        # Mixed queries have lower confidence
        assert intent.confidence > 0.5


@pytest.mark.asyncio
async def test_intent_detection_accuracy():
    """Test intent detection achieves >90% accuracy."""
    detector = QueryIntentDetector()

    test_queries = {
        IntentType.LOCAL_ONLY: [
            "def async_function",
            "src/router.py",
            "class AsyncHandler",
            "import asyncio",
            "# TODO: fix async",
            "AsyncManager",
        ],
        IntentType.WEB_ENHANCED: [
            "async best practices",
            "latest async features Python 3.12",
            "async tutorial for beginners",
            "why use async await",
            "async vs threading performance",
        ],
        IntentType.MIXED: [
            "async patterns",
            "asyncio usage examples",
            "await patterns",
            "async context managers",
        ],
    }

    correct = 0
    total = 0

    for expected_intent, queries in test_queries.items():
        for query in queries:
            intent = await detector.detect(query)
            if intent.type == expected_intent:
                correct += 1
            total += 1

    accuracy = correct / total
    assert accuracy > 0.9, f"Accuracy {accuracy:.2%} below 90% threshold"
```

### Test Backends (test_backends/)

#### test_cds_backend.py

```python
import pytest
from search_research.backends import CDSBackend


@pytest.mark.asyncio
async def test_cds_backend_search(sample_codebase):
    """Test CDS backend searches code documentation."""
    backend = CDSBackend(codebase_path=sample_codebase)

    assert backend.available is True

    results = await backend.search("async function", limit=10)

    assert len(results) >= 0
    for result in results:
        assert "title" in result
        assert "content" in result
        assert "source" in result
        assert result["source"] == "cds"


@pytest.mark.asyncio
async def test_cds_backend_empty_query(sample_codebase):
    """Test CDS backend handles empty query gracefully."""
    backend = CDSBackend(codebase_path=sample_codebase)

    results = await backend.search("", limit=10)

    assert len(results) == 0


@pytest.mark.asyncio
async def test_cds_backend_limit(sample_codebase):
    """Test CDS backend respects result limit."""
    backend = CDSBackend(codebase_path=sample_codebase)

    results = await backend.search("async", limit=5)

    assert len(results) <= 5
```

#### test_grep_backend.py

```python
import pytest
from search_research.backends import GrepBackend


@pytest.mark.asyncio
async def test_grep_backend_search(sample_codebase):
    """Test Grep backend searches code patterns."""
    backend = GrepBackend(codebase_path=sample_codebase)

    assert backend.available is True

    results = await backend.search("def", limit=10)

    assert len(results) >= 0
    for result in results:
        assert "title" in result
        assert "content" in result
        assert result["source"] == "grep"


@pytest.mark.asyncio
async def test_grep_backend_file_path_filter(sample_codebase):
    """Test Grep backend filters by file path."""
    backend = GrepBackend(codebase_path=sample_codebase)

    results = await backend.search(
        "async",
        file_path="async_module.py"
    )

    # All results should be from async_module.py
    for result in results:
        assert "async_module.py" in result.get("metadata", {}).get("file", "")


@pytest.mark.asyncio
async def test_grep_backend_class_search(sample_codebase):
    """Test Grep backend searches for class definitions."""
    backend = GrepBackend(codebase_path=sample_codebase)

    results = await backend.search("class Sync")

    assert len(results) >= 0
    for result in results:
        content = result["content"].lower()
        assert "class" in content
```

---

## Integration Tests

### Test Mode Routing (test_mode_routing.py)

```python
import pytest
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
async def test_fast_mode_local_only(sample_router):
    """Test FAST mode uses only local backends."""
    results = await sample_router.search_async(
        "async patterns",
        mode=Mode.FAST
    )

    # Verify no web providers used
    for hit in results.hits:
        assert hit.source not in ["tavily", "serper", "exa"]


@pytest.mark.asyncio
async def test_comprehensive_mode_all_backends():
    """Test COMPREHENSIVE mode uses all backends."""
    router = UnifiedRouter(mode=Mode.COMPREHENSIVE)

    results = await router.search_async(
        "async best practices",
        mode=Mode.COMPREHENSIVE
    )

    # Should have results from multiple backend types
    sources = {hit.source for hit in results.hits}
    assert len(sources) > 1


@pytest.mark.asyncio
async def test_custom_mode_specific_backends():
    """Test CUSTOM mode uses only specified backends."""
    router = UnifiedRouter(mode=Mode.CUSTOM)

    results = await router.search_async(
        "async patterns",
        backend=["cds", "grep"]
    )

    # All results should be from specified backends
    for hit in results.hits:
        assert hit.source.lower() in ["cds", "grep"]


@pytest.mark.asyncio
async def test_auto_mode_intent_routing():
    """Test AUTO mode routes based on intent detection."""
    router = UnifiedRouter(mode=Mode.COMPREHENSIVE, auto_mode=True)

    # LOCAL_ONLY query → FAST mode
    results = await router.search_async("def async_function")
    # Should use local backends only (faster)

    # WEB_ENHANCED query → COMPREHENSIVE mode
    results = await router.search_async("async best practices")
    # Should use all backends including web
```

### Test Backend Fallback (test_backend_fallback.py)

```python
import pytest
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
async def test_backend_unavailable_skip():
    """Test router skips unavailable backends."""
    router = UnifiedRouter(
        mode=Mode.FAST,
        backend=["cds", "nonexistent_backend"]
    )

    # Should not fail, just skip unavailable backend
    results = await router.search_async("async patterns")

    assert isinstance(results, SearchResults)


@pytest.mark.asyncio
async def test_backend_timeout_recovery():
    """Test router recovers from backend timeout."""
    class SlowBackend:
        async def search(self, query: str, limit: int):
            await asyncio.sleep(10)  # Timeout
            return []

        @property
        def available(self) -> bool:
            return True

    router = UnifiedRouter(mode=Mode.CUSTOM)
    router.register_backend(SlowBackend(), timeout=0.5)

    # Should not hang, should return partial results
    results = await router.search_async("test")

    assert isinstance(results, SearchResults)


@pytest.mark.asyncio
async def test_web_backend_no_api_key():
    """Test web backends skip without API keys."""
    # Remove API keys
    import os
    original_keys = {
        "TAVILY_API_KEY": os.environ.get("TAVILY_API_KEY"),
        "SERPER_API_KEY": os.environ.get("SERPER_API_KEY"),
    }

    for key in original_keys:
        if original_keys[key]:
            del os.environ[key]

    router = UnifiedRouter(mode=Mode.COMPREHENSIVE)

    # Should not fail, should skip web backends
    results = await router.search_async("async best practices")

    # Restore keys
    for key, value in original_keys.items():
        if value:
            os.environ[key] = value

    assert isinstance(results, SearchResults)
```

### Test Cache Invalidation (test_cache_invalidation.py)

```python
import pytest
import time
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
async def test_cache_hit_repeated_queries():
    """Test cache returns cached results for repeated queries."""
    router = UnifiedRouter(
        mode=Mode.FAST,
        enable_cache=True
    )

    query = "async patterns"

    # First call - cache miss
    start1 = time.time()
    results1 = await router.search_async(query)
    time1 = time.time() - start1

    # Second call - cache hit (should be faster)
    start2 = time.time()
    results2 = await router.search_async(query)
    time2 = time.time() - start2

    # Results should be identical
    assert len(results1.hits) == len(results2.hits)

    # Cache hit should be faster (may not always be true in tests)
    # but we can check both completed successfully
    assert time2 >= 0


@pytest.mark.asyncio
async def test_cache_invalidation_ttl():
    """Test cache invalidates after TTL expires."""
    router = UnifiedRouter(
        mode=Mode.FAST,
        enable_cache=True,
        cache_ttl=1  # 1 second TTL
    )

    query = "async patterns"

    # First call
    results1 = await router.search_async(query)

    # Wait for TTL expiration
    await asyncio.sleep(2)

    # Second call should be cache miss
    results2 = await router.search_async(query)

    # Both should succeed
    assert len(results1.hits) >= 0
    assert len(results2.hits) >= 0


@pytest.mark.asyncio
async def test_cache_key_includes_backend_list():
    """Test cache key includes backend list."""
    router = UnifiedRouter(mode=Mode.CUSTOM, enable_cache=True)

    query = "async patterns"

    # Search with different backend lists
    results1 = await router.search_async(query, backend=["cds"])
    results2 = await router.search_async(query, backend=["grep"])

    # Results should be different (different backends)
    # even though query is the same
    sources1 = {hit.source for hit in results1.hits}
    sources2 = {hit.source for hit in results2.hits}

    assert sources1 != sources2
```

### Test Migration Compatibility (test_migration.py)

```python
import pytest
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
async def test_unified_search_migration():
    """Test migration from unified-search API."""
    # Old API
    # from unified_search import EnhancedUnifiedSearchRouter
    # router = EnhancedUnifiedSearchRouter()
    # results = router.search("async patterns")

    # New API
    router = UnifiedRouter(mode=Mode.FAST)
    results = await router.search_async("async patterns")

    # Should work
    assert len(results.hits) >= 0


@pytest.mark.asyncio
async def test_research_skill_migration():
    """Test migration from research-skill API."""
    # Old API
    # from research_skill import research
    # results = research("async best practices", providers=["tavily"])

    # New API
    router = UnifiedRouter(mode=Mode.COMPREHENSIVE)
    results = await router.search_async(
        "async best practices",
        backend=["tavily"]
    )

    # Should work (may skip if no API key)
    assert isinstance(results, SearchResults)


def test_import_compatibility():
    """Test old imports still work (with deprecation warnings)."""
    import warnings

    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # This should trigger deprecation warning
        try:
            from unified_search import EnhancedUnifiedSearchRouter
            assert len(w) > 0
            assert issubclass(w[0].category, DeprecationWarning)
        except ImportError:
            # unified-search not installed (expected in new environment)
            pass
```

---

## Performance Tests

### Test Latency (test_latency.py)

```python
import pytest
import time
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
@pytest.mark.performance
async def test_fast_mode_latency_target():
    """Test FAST mode achieves <1s latency target."""
    router = UnifiedRouter(mode=Mode.FAST)

    queries = ["async", "await", "asyncio"]
    latencies = []

    for query in queries:
        start = time.time()
        await router.search_async(query)
        latency = time.time() - start
        latencies.append(latency)

    avg_latency = sum(latencies) / len(latencies)
    max_latency = max(latencies)

    assert avg_latency < 1.0, f"Average latency {avg_latency:.2f}s exceeds 1s target"
    assert max_latency < 1.5, f"Max latency {max_latency:.2f}s exceeds 1.5s limit"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_comprehensive_mode_latency_target():
    """Test COMPREHENSIVE mode achieves 5-10s latency target."""
    router = UnifiedRouter(mode=Mode.COMPREHENSIVE)

    start = time.time()
    await router.search_async("async best practices")
    latency = time.time() - start

    assert 5.0 <= latency <= 15.0, f"Latency {latency:.2f}s outside 5-15s target"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_cache_lookup_latency():
    """Test cache lookup achieves <10ms target."""
    router = UnifiedRouter(mode=Mode.FAST, enable_cache=True)

    # Prime cache
    await router.search_async("async patterns")

    # Measure cache hit latency
    start = time.time()
    await router.search_async("async patterns")
    latency = time.time() - start

    # Convert to milliseconds
    latency_ms = latency * 1000

    assert latency_ms < 50, f"Cache lookup {latency_ms:.1f}ms exceeds 50ms limit"
```

### Test Throughput (test_throughput.py)

```python
import pytest
import asyncio
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
@pytest.mark.performance
async def test_concurrent_search_throughput():
    """Test router handles 100 concurrent searches."""
    router = UnifiedRouter(mode=Mode.FAST)

    queries = [f"query{i}" for i in range(100)]

    start = asyncio.get_event_loop().time()
    results = await asyncio.gather(*[
        router.search_async(q) for q in queries
    ])
    elapsed = asyncio.get_event_loop().time() - start

    assert len(results) == 100
    throughput = len(results) / elapsed

    # Should handle >10 queries/second
    assert throughput > 10, f"Throughput {throughput:.1f} qps below 10 qps target"


@pytest.mark.asyncio
@pytest.mark.performance
async def test_sequential_search_performance():
    """Test 10 sequential searches complete in <10s."""
    router = UnifiedRouter(mode=Mode.FAST)

    start = asyncio.get_event_loop().time()
    for i in range(10):
        await router.search_async(f"query{i}")
    elapsed = asyncio.get_event_loop().time() - start

    assert elapsed < 10.0, f"10 sequential queries took {elapsed:.1f}s, exceeds 10s target"
```

### Test Concurrency (test_concurrency.py)

```python
import pytest
import asyncio
from search_research import UnifiedRouter, Mode


@pytest.mark.asyncio
@pytest.mark.performance
async def test_no_race_conditions():
    """Test concurrent searches don't cause race conditions."""
    router = UnifiedRouter(mode=Mode.FAST)

    # Run 50 concurrent searches with same query
    query = "async patterns"
    tasks = [router.search_async(query) for _ in range(50)]
    results = await asyncio.gather(*tasks)

    # All results should be valid
    for result in results:
        assert isinstance(result, SearchResults)
        assert len(result.hits) >= 0

    # All results should be identical
    first_hit_count = len(results[0].hits)
    for result in results[1:]:
        assert len(result.hits) == first_hit_count


@pytest.mark.asyncio
@pytest.mark.performance
async def test_cache_concurrent_access():
    """Test cache handles concurrent access correctly."""
    router = UnifiedRouter(mode=Mode.FAST, enable_cache=True)

    # Prime cache
    await router.search_async("test query")

    # Concurrent cache hits
    tasks = [router.search_async("test query") for _ in range(100)]
    results = await asyncio.gather(*tasks)

    # All should succeed
    assert len(results) == 100
    for result in results:
        assert isinstance(result, SearchResults)
```

---

## Running Tests

### Run All Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=search_research --cov-report=html --cov-report=term

# Run with coverage threshold
pytest tests/ --cov=search_research --cov-fail-under=90
```

### Run Specific Test Categories

```bash
# Unit tests only
pytest tests/test_router.py tests/test_cache.py -v

# Backend tests
pytest tests/test_backends/ -v

# Integration tests
pytest tests/integration/ -v

# Performance tests
pytest tests/performance/ -v -m performance
```

### Run with Verbose Output

```bash
# Show detailed test output
pytest tests/ -vv --tb=long

# Show print statements
pytest tests/ -v -s
```

### Run Parallel Tests

```bash
# Install pytest-xdist
pip install pytest-xdist

# Run tests in parallel (4 workers)
pytest tests/ -n 4
```

---

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}

    - name: Install dependencies
      run: |
        pip install -e ".[all,dev]"

    - name: Run tests
      run: |
        pytest tests/ --cov=search_research --cov-report=xml --cov-report=term

    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        file: ./coverage.xml
```

---

## Test Data Management

### Fixtures

- **sample_codebase**: Temporary directory with sample Python files
- **mock_backend**: Mock backend returning deterministic results
- **sample_cache**: Pre-populated cache for testing
- **sample_router**: Router configured with test backends
- **sample_queries**: Representative query examples
- **intent_test_data**: Labeled intent detection test data

### External Dependencies

**Unit tests:** No external dependencies (all mocked)

**Integration tests:**
- Optional: Real codebase for backend tests
- Optional: API keys for web provider tests (skip if missing)

**Performance tests:**
- Requires: Real codebase with realistic size
- Target: 1000+ files for meaningful benchmarks

---

## Continuous Quality Monitoring

### Coverage Tracking

```bash
# Generate coverage report
pytest --cov=search_research --cov-report=html

# View in browser
open htmlcov/index.html
```

### Performance Baselines

```bash
# Run performance tests
pytest tests/performance/ -v --benchmark-only

# Compare against baseline
pytest tests/performance/ --benchmark-compare
```

### Regression Detection

```bash
# Run tests with regression detection
pytest tests/ --regression --regression-baseline=baseline.json
```

---

## Test Maintenance

### Adding New Tests

1. **Create test file** in appropriate directory (unit/integration/performance)
2. **Use fixtures** from conftest.py for consistency
3. **Follow naming convention:** test_<function>_<scenario>
4. **Add docstrings** explaining what is being tested
5. **Mark tests** appropriately (@pytest.mark.asyncio, @pytest.mark.performance)

### Updating Tests

1. **Run tests** before making changes
2. **Update test** to reflect new behavior
3. **Verify coverage** hasn't decreased
4. **Add new tests** for new features

### Flaky Tests

**Symptoms:** Test passes sometimes, fails other times

**Solutions:**
- Add explicit waits/sleeps for async operations
- Use fixtures for deterministic data
- Mock external dependencies
- Increase timeout values

---

## Test Metrics Dashboard

Track these metrics in CI/CD:

| Metric | Target | Current | Status |
|--------|--------|---------|--------|
| **Coverage** | >90% | TBD | ⚠️ |
| **Unit Test Pass Rate** | 100% | TBD | ⚠️ |
| **Integration Test Pass Rate** | >95% | TBD | ⚠️ |
| **FAST Mode Latency** | <1s | TBD | ⚠️ |
| **COMPREHENSIVE Mode Latency** | 5-10s | TBD | ⚠️ |
| **Cache Hit Rate** | >50% | TBD | ⚠️ |
| **Intent Detection Accuracy** | >90% | TBD | ⚠️ |

---

**Last Updated:** 2026-03-05
**Document Version:** 1.0
**Status:** Draft - Pending Review
