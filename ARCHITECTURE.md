# search-research Architecture

**Version:** 1.0 | **Status:** Draft | **Date:** 2026-03-05

## Overview

search-research provides a unified search and research system consolidating:
- **unified-search**: Local code/knowledge search (<1s)
- **research-skill**: Web research with HyDE (5-10s)
- **__csf search components**: Chat history, knowledge base, code search

**Key Architecture:** Async-first unified router with 18 backends (8 local + 10 web), mode-based routing, and intelligent result aggregation.

---

## Architecture Diagram

```
┌──────────────────────────────────────────────────────────────┐
│                     Consumer Layer                            │
│  - /search command (SearchRouter - FAST mode)                 │
│  - /research command (ResearchRouter - COMPREHENSIVE mode)   │
│  - Python API (UnifiedRouter - CUSTOM mode)                  │
└─────────────────────────────┬────────────────────────────────┘
                              │
                    ┌─────────▼──────────┐
                    │  UnifiedRouter    │
                    │  (async core)     │
                    │                   │
                    │  - Mode routing   │
                    │  - Intent detect  │
                    │  - LRU cache      │
                    │  - Result agg.    │
                    └─────────┬──────────┘
                              │
              ┌───────────────┴───────────────┐
              │                               │
      ┌───────▼────────┐           ┌─────────▼────────┐
      │  Local Backends│           │  Web Backends    │
      │  (8 backends)  │           │  (10 providers)  │
      ├────────────────┤           ├──────────────────┤
      │ • CHS          │           │ • Tavily         │
      │ • CKS          │           │ • Serper         │
      │ • CDS          │           │ • Exa            │
      │ • Grep         │           │ • Perplexity     │
      │ • Skills       │           │ • Brave          │
      │ • RLM          │           │ • Bing           │
      │ • Persona      │           │ • Google         │
      │ • MultiLang    │           │ • DuckDuckGo     │
      │ • NotebookLM   │           │ • Kagi           │
      │                │           │ • You.com        │
      │ Timeout: 0.5s  │           │ • Mojeek        │
      └────────────────┘           │ Timeout: 5s      │
                                   │ Graceful deg.    │
                                   └──────────────────┘
              └──────────────────────────┬───────────────┘
                                         │
                               ┌─────────▼──────────┐
                               │ Result Processing  │
                               ├────────────────────┤
                               │ • Deduplication    │
                               │ • Hybrid scoring   │
                               │ • Ranking          │
                               │ • Limiting         │
                               └────────────────────┘
```

---

## Core Components

### 1. UnifiedRouter (Async)

**Purpose:** Central orchestrator for all search operations

**Responsibilities:**
- Mode-based routing (FAST/COMPREHENSIVE/CUSTOM)
- Query intent detection (LOCAL_ONLY/WEB_ENHANCED/MIXED)
- Parallel backend execution via `asyncio.gather()`
- Result aggregation and ranking
- LRU caching with TTL

**Key Methods:**
```python
class UnifiedRouter:
    async def search_async(
        self,
        query: str,
        mode: Mode = Mode.FAST,
        backend: list[str] | None = None,
        limit: int = 20,
        **kwargs
    ) -> SearchResults

    def search(
        self,
        query: str,
        mode: Mode = Mode.FAST,
        **kwargs
    ) -> SearchResults:
        """Sync wrapper for backward compatibility."""
        return asyncio.run(self.search_async(query, mode, **kwargs))
```

**Performance:**
- FAST mode: <1s (local backends only)
- COMPREHENSIVE mode: 5-10s (all backends with HyDE)
- Concurrent execution: 10k+ operations possible

### 2. Mode-Based Routing

**Modes:**

| Mode | Description | Backends | Timeout |
|------|-------------|----------|---------|
| **FAST** | Local code/knowledge search only | 8 local backends | 0.5s each |
| **COMPREHENSIVE** | All backends with HyDE enhancement | 18 backends | 0.5s local, 5s web |
| **CUSTOM** | User-specified backends only | User-defined | Per-backend |

**Mode Selection:**
```python
from search_research import Mode, UnifiedRouter

router = UnifiedRouter(mode=Mode.FAST)
results = router.search("async patterns")  # <1s

router = UnifiedRouter(mode=Mode.COMPREHENSIVE)
results = router.search("async best practices")  # 5-10s

router = UnifiedRouter(mode=Mode.CUSTOM)
results = router.search("async", backend=["cds", "grep"])  # <1s
```

### 3. Query Intent Detection

**Intent Types:**

| Intent | Description | Example |
|--------|-------------|---------|
| **LOCAL_ONLY** | Code patterns, function names, file paths | `"def async_"`, `"src/router.py"` |
| **WEB_ENHANCED** | Best practices, tutorials, "latest" | `"async best practices"`, `"latest FastAPI"` |
| **MIXED** | Ambiguous queries | `"async patterns"` |

**Detection Approach:**
- Keyword matching (fast, deterministic)
- Heuristic rules (path detection, code patterns)
- Fallback to MIXED on uncertainty

**Override Options:**
```bash
# Explicit flags
search-research "async patterns" --auto          # Use intent detection
search-research "async patterns" --web           # Force web search
search-research "async patterns" --backend cds grep  # Custom backends
```

**Accuracy Target:** >90% (measured on validation corpus)

### 4. Local Backends (8)

**Backend Overview:**

| Backend | Purpose | Technology | Timeout |
|---------|---------|------------|---------|
| **CHS** | Chat History Search | FTS5 + semantic embeddings | 0.5s |
| **CKS** | Constitutional Knowledge System | Multi-graph engine (FAISS) | 0.5s |
| **CDS** | Code Documentation Search | AST-based docstring extraction | 0.5s |
| **Grep** | Code Pattern Search | AST-based function/class search | 0.5s |
| **Skills** | Skills & Commands | Progressive disclosure search | 0.5s |
| **RLM** | Recursive Language Model | Code generation search | 0.5s |
| **Persona** | Persona Memory | Context-aware cognitive search | 0.5s |
| **MultiLang** | Multi-language Code | Tree-sitter parser (optional) | 0.5s |
| **NotebookLM** | NotebookLM Integration | MCP server (optional) | 0.5s |

**Protocol Interface:**
```python
class BaseSearchBackend(Protocol):
    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs
    ) -> list[SearchResult]

    @property
    def available(self) -> bool:
        """Check if backend is ready (deps installed, DB exists)."""
```

**Graceful Degradation:**
- Backends skip if dependencies unavailable (e.g., MultiLang without tree-sitter)
- Warning logged, search continues with available backends
- No hard failures for optional backends

### 5. Web Backends (10+)

**Provider Overview:**

| Provider | Type | API Key Required | Timeout |
|----------|------|------------------|---------|
| **Tavily** | AI-powered search with synthesis | Yes | 5s |
| **Serper** | Google search with knowledge graph | Yes | 5s |
| **Exa** | Neural/semantic search | Yes | 5s |
| **Perplexity** | AI search with citations | Yes | 5s |
| **Brave** | Privacy-focused search | Yes | 5s |
| **Bing** | Microsoft Search | Yes | 5s |
| **Google** | Google Custom Search | Yes | 5s |
| **DuckDuckGo** | Privacy search (free tier) | No | 5s |
| **Kagi** | Premium search | Yes | 5s |
| **You.com** | AI search | Yes | 5s |
| **Mojeek** | Independent search | No | 5s |

**Protocol Interface:**
```python
class BaseWebBackend(Protocol):
    async def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> list[SearchResult]

    @property
    def available(self) -> bool:
        """Check if API key configured."""
```

**Graceful Degradation:**
- Providers skip without API keys (warning logged)
- Partial results returned from available providers
- Circuit breaker after 5 consecutive failures
- Exponential backoff for retries

**API Key Configuration:**
```bash
# Environment variables
export TAVILY_API_KEY=tvly-xxx
export SERPER_API_KEY=xxx
export EXA_API_KEY=exa_xxx

# Config file (optional)
~/.search-research/config.toml:
[providers]
tavily_api_key = "tvly-xxx"
serper_api_key = "xxx"
```

### 6. HyDE Enhancement

**Purpose:** Improve web search relevance using hypothetical document embeddings

**How It Works:**
1. **Generate** hypothetical document answering user's query (LLM)
2. **Extract** 3-5 key phrases from hypothetical document
3. **Enhance** original query with key phrases
4. **Search** web providers with enhanced query
5. **Filter** noise through embedding encoder's "dense bottleneck"

**Effectiveness:**
- **74% improvement**: 41.8 MAP vs 24.0 baseline (BM25)
- **Performs on par** with fine-tuned models without labeled data
- **Zero-shot approach**: No training data required

**Implementation:**
```python
class HyDEEnhancer:
    async def enhance_query(
        self,
        query: str,
        backend: list[str] | None = None
    ) -> str:
        """Generate hypothetical document and extract key phrases."""
        # 1. Generate hypothetical document (LLM)
        # 2. Extract 3-5 key phrases
        # 3. Combine with original query
        # 4. Return enhanced query
```

**Configuration:**
```python
# Enable HyDE (default for COMPREHENSIVE mode)
router = UnifiedRouter(mode=Mode.COMPREHENSIVE, hyde=True)

# Disable HyDE (faster, less accurate)
router = UnifiedRouter(mode=Mode.COMPREHENSIVE, hyde=False)
```

**Trade-offs:**
- **Pro:** 10-15% relevance improvement (measured)
- **Con:** Additional LLM call overhead (~1-2s)
- **Decision:** Optional flag, default enabled for COMPREHENSIVE mode

### 7. Query Caching

**Strategy:** LRU + TTL dual eviction

**Cache Configuration:**
```python
QueryCache(
    max_size=1000,        # Maximum entries
    ttl=3600,             # Time-to-live (seconds)
    enable_stats=True     # Track hit/miss rates
)
```

**Cache Key:** Based on query + backend list
```python
cache_key = f"{query}:{','.join(sorted(backends))}"
```

**Eviction Logic:**
1. **TTL expiration** (time-based): Entry expires after 3600s regardless of access
2. **LRU eviction** (space-based): Evict least recently used when cache full
3. **Combined:** Whichever happens first

**Tiered TTL Strategy:**
- **Hot queries**: 24h TTL (frequently repeated)
- **Regular queries**: 1h TTL (default)
- **Rare queries**: 10min TTL (space-limited)

**Performance Targets:**
- **Hit rate**: >50% for repeated queries
- **Lookup time**: <10ms
- **Memory**: <100MB for 1000 queries

**Monitoring:**
```python
cache_stats = router.get_cache_stats()
print(f"Hit rate: {cache_stats.hit_rate:.2%}")
print(f"Size: {cache_stats.size}/{cache_stats.max_size}")
```

### 8. Result Aggregation

**Pipeline:**

```
Raw Results (from all backends)
         ↓
    Merge (combine lists)
         ↓
 Deduplicate (by URL, file_path)
         ↓
Hybrid Scoring (BM25 + cosine)
         ↓
    Rank (by score DESC)
         ↓
    Limit (top N)
         ↓
Final Results
```

**Deduplication:**
```python
class ResultDeduplicator:
    def deduplicate(
        self,
        results: list[SearchResult]
    ) -> list[SearchResult]:
        """Remove duplicates by URL or file_path."""
        seen = set()
        unique = []
        for result in results:
            key = result.url or result.file_path
            if key not in seen:
                seen.add(key)
                unique.append(result)
        return unique
```

**Hybrid Scoring:**
```python
class HybridScorer:
    def score(
        self,
        result: SearchResult,
        query: str
    ) -> float:
        """Combine BM25 and cosine similarity scores."""
        bm25_score = self._bm25_score(result, query)
        cosine_score = self._cosine_score(result, query)
        return 0.7 * bm25_score + 0.3 * cosine_score
```

**Ranking:**
- Primary: Hybrid score (DESC)
- Secondary: Backend priority (configurable)
- Tertiary: Timestamp (DESC)

---

## Data Models

### SearchResult Schema

```python
@dataclass
class SearchResult:
    """Unified search result from any backend."""

    # Content
    title: str
    content: str
    url: str | None = None          # Web results
    file_path: str | None = None    # Local results
    line_number: int | None = None  # Code results

    # Metadata
    source: str                     # Backend name
    score: float                    # Relevance (0-1)
    metadata: dict[str, Any]        # Backend-specific

    # Timestamps
    created_at: datetime
    cached: bool = False
```

### SearchResults Schema

```python
@dataclass
class SearchResults:
    """Container for search results with metadata."""

    query: str
    hits: list[SearchResult]
    total: int                      # Total results found
    returned: int                   # Results returned (after limit)
    metadata: dict[str, Any]        # Response metadata
```

### Mode Enum

```python
class Mode(Enum):
    """Search mode."""
    FAST = "fast"                    # Local backends only
    COMPREHENSIVE = "comprehensive"  # All backends with HyDE
    CUSTOM = "custom"                # User-specified backends
```

### IntentType Enum

```python
class IntentType(Enum):
    """Query intent classification."""
    LOCAL_ONLY = "local_only"        # Code patterns, file paths
    WEB_ENHANCED = "web_enhanced"    # Best practices, tutorials
    MIXED = "mixed"                  # Ambiguous
```

---

## Concurrency Model

### Asyncio vs Threading (Decision)

**Choice:** Asyncio for I/O-bound concurrent operations

**Evidence:**

| Aspect | Threading | Asyncio |
|--------|-----------|---------|
| **Concurrency** | Hundreds | 10,000+ |
| **Memory** | ~1-8MB per thread | ~KB per coroutine |
| **Context Switch** | Microseconds | Nanoseconds |
| **Programming** | Shared memory + locks | Event loop + await |
| **Use Case** | CPU-bound, blocking SDKs | I/O-bound, async libs |

**Why Asyncio for search-research:**
- **I/O-bound workload**: File reads, network requests (10+ web providers)
- **High concurrency**: Need 10+ concurrent backend searches
- **Scalability**: 10k+ concurrent operations possible
- **Memory efficiency**: KB-level overhead vs MB per thread
- **Library ecosystem**: Async versions available (aiohttp, asyncpg, etc.)

**Hybrid Approach:**
- **Async core**: `UnifiedRouter.search_async()`
- **Sync wrapper**: `UnifiedRouter.search()` for backward compatibility
- **Blocking calls**: Use `asyncio.to_thread()` for legacy SDKs

### Execution Flow

```python
async def search_async(
    self,
    query: str,
    mode: Mode,
    backend: list[str] | None,
    limit: int
) -> SearchResults:
    """Concurrent search across all backends."""

    # 1. Check cache
    cached = await self.cache.get(query, backend)
    if cached:
        return cached

    # 2. Detect intent (if needed)
    if mode == Mode.FAST and backend is None:
        intent = await self.intent_detector.detect(query)
        backends = self._select_backends(intent)
    else:
        backends = self._resolve_backends(backend)

    # 3. Parallel search (concurrent)
    tasks = [
        backend.search(query, limit)
        for backend in backends
        if backend.available
    ]
    results = await asyncio.gather(
        *tasks,
        return_exceptions=True  # Don't fail on single backend error
    )

    # 4. Aggregate results
    aggregated = self._aggregate_results(results)

    # 5. Cache results
    await self.cache.set(query, backend, aggregated)

    return aggregated
```

### Backend Timeout Handling

```python
async def _search_with_timeout(
    self,
    backend: BaseSearchBackend,
    query: str,
    limit: int,
    timeout: float
) -> list[SearchResult]:
    """Execute backend search with timeout."""
    try:
        return await asyncio.wait_for(
            backend.search(query, limit),
            timeout=timeout
        )
    except asyncio.TimeoutError:
        logger.warning(f"{backend.name} timed out after {timeout}s")
        return []  # Return empty, don't fail entire search
    except Exception as e:
        logger.error(f"{backend.name} failed: {e}")
        return []  # Return empty, don't fail entire search
```

---

## Error Handling

### Exception Hierarchy

```python
class SearchResearchError(Exception):
    """Base exception for search-research package."""

class BackendError(SearchResearchError):
    """Backend-related errors."""
    class BackendUnavailableError(BackendError):
        """Backend not available (missing deps, no API key)."""
    class BackendTimeoutError(BackendError):
        """Backend exceeded timeout."""

class InvalidQueryError(SearchResearchError):
    """Query validation errors."""

class CacheError(SearchResearchError):
    """Cache-related errors."""
```

### Error Handling Strategy

**Backends:**
- Catch all exceptions during search
- Return empty results on failure
- Log error with backend name
- Don't fail entire search for single backend error

**Router:**
- Validate query before execution
- Catch backend exceptions during `gather()`
- Return partial results on failures
- Raise `InvalidQueryError` for malformed queries

**Cache:**
- Graceful degradation on cache failures
- Log warning, continue without cache
- Don't fail search for cache errors

**User-Facing Messages:**
```python
# Good: Actionable
"Backend 'tavily' skipped: TAVILY_API_KEY not set. Set via environment variable or config file."

# Bad: Cryptic
"BackendError: unavailable"
```

---

## Performance Targets

### Response Time

| Mode | Target | Maximum | Measurement |
|------|--------|---------|-------------|
| FAST | <1s | 1.5s | 10 local queries |
| COMPREHENSIVE | 5-10s | 15s | 10 web queries |
| Cache hit | <10ms | 50ms | 100 repeated queries |

### Backend Timeout

| Backend Type | Timeout | Rationale |
|--------------|---------|-----------|
| Local | 0.5s | File I/O, SQLite queries |
| Web | 5s | Network latency, API rate limits |

### Cache Performance

| Metric | Target | Measurement |
|--------|--------|-------------|
| Hit rate | >50% | Repeated query patterns |
| Lookup | <10ms | In-memory LRU |
| Size | <100MB | 1000 queries × 100KB avg |

### Intent Detection

| Metric | Target | Measurement |
|--------|--------|-------------|
| Accuracy | >90% | Validation corpus |
| Latency | <10ms | Keyword + heuristics |

---

## Migration Strategy

### From unified-search

**Before:**
```python
from unified_search import EnhancedUnifiedSearchRouter

router = EnhancedUnifiedSearchRouter()
results = router.search("async patterns")
```

**After:**
```python
from search_research import UnifiedRouter

router = UnifiedRouter(mode=Mode.FAST)
results = router.search("async patterns")
```

**Breaking Changes:**
- `EnhancedUnifiedSearchRouter` → `UnifiedRouter`
- `mode` parameter required (was implicit)
- Async API preferred (`search_async()`)

### From research-skill

**Before:**
```python
from research_skill import research

results = research("async best practices", providers=["tavily"])
```

**After:**
```python
from search_research import UnifiedRouter

router = UnifiedRouter(mode=Mode.COMPREHENSIVE)
results = router.search("async best practices", backend=["tavily"])
```

**Breaking Changes:**
- `research()` function → `UnifiedRouter.search()`
- `providers` → `backend`
- Unified API for local and web search

### Deprecation Timeline

**Phase 1 (Week 1-3):** Initial release
- search-research package available
- unified-search and research-skill still work
- Deprecation warnings added

**Phase 2 (Week 4-8):** Migration period
- Documentation and migration guides
- Bug fixes and improvements
- unified-search/research-skill in maintenance mode

**Phase 3 (Week 8+):** Deprecation
- unified-search deprecated
- research-skill deprecated
- Users must migrate to search-research

---

## Configuration

### Environment Variables

```bash
# API Keys (optional)
export TAVILY_API_KEY=tvly-xxx
export SERPER_API_KEY=xxx
export EXA_API_KEY=exa_xxx

# Cache Configuration
export SEARCH_CACHE_SIZE=1000
export SEARCH_CACHE_TTL=3600

# Backend Paths
export SEARCH_CHS_DB=~/.search-research/chat_history.db
export SEARCH_CKS_DB=~/.search-research/cks.db

# Debug
export SEARCH_DEBUG=true
export SEARCH_LOG_LEVEL=DEBUG
```

### Config File (Optional)

```toml
# ~/.search-research/config.toml

[cache]
max_size = 1000
ttl = 3600

[backends.chs]
database_path = "~/.search-research/chat_history.db"

[backends.cks]
database_path = "~/.search-research/cks.db"

[providers.tavily]
api_key = "tvly-xxx"
timeout = 5

[providers.serper]
api_key = "xxx"
timeout = 5
```

---

## Testing Strategy

### Unit Tests

**Coverage Targets:**
- Core router: >95%
- Intent detection: >90%
- Cache: >90%
- Overall: >90%

**Test Categories:**
- Backend tests (each backend tested independently)
- Cache tests (hit/miss, TTL, size limits)
- Intent detection tests (accuracy, edge cases)
- Result aggregation tests (merge, dedup, ranking)

### Integration Tests

**Test Scenarios:**
- FAST mode with local backends only
- COMPREHENSIVE mode with all backends
- CUSTOM mode with specific backends
- Web backends with/without API keys
- Cache hit/miss scenarios

### Performance Tests

**Benchmarks:**
- FAST mode: <1s for 10 queries
- COMPREHENSIVE mode: 5-10s for 10 queries
- Cache lookup: <10ms
- Backend timeout: 0.5s local, 5s web

### End-to-End Tests

**Test Flows:**
1. User searches code patterns (`/search "FastAPI patterns"`)
2. User researches best practices (`/research "FastAPI best practices"`)
3. User enables web search (`/search "FastAPI" --web`)
4. User with no API keys (graceful degradation)

---

## Observability

### Logging

**Levels:**
- `DEBUG`: Detailed execution flow
- `INFO`: Normal operations (cache hits, backend selections)
- `WARNING`: Graceful degradation (backend skipped, API key missing)
- `ERROR`: Backend failures, timeouts

**Example:**
```python
logger.info(f"Cache hit: {query}")
logger.warning(f"Backend 'tavily' skipped: API key not set")
logger.error(f"Backend 'chs' failed: {e}")
```

### Metrics

**Track:**
- Query latency (p50, p95, p99)
- Backend success rate
- Cache hit rate
- Intent detection accuracy

**Example:**
```python
metrics = {
    "query_latency": 0.85,  # seconds
    "backend_success_rate": 0.95,
    "cache_hit_rate": 0.65,
    "intent_accuracy": 0.92
}
```

---

## Security

### API Key Management

**Principles:**
- Environment variables only (never hardcode)
- Redact API keys in logs/error messages
- `.env` files in `.gitignore`
- Validation at startup (fail fast)

**Example:**
```python
def validate_api_keys():
    """Validate API keys at startup."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key and not tavily_key.startswith("tvly-"):
        raise ValueError(f"Invalid TAVILY_API_KEY format")
```

### Query Sanitization

**Principles:**
- Sanitize user input before execution
- Prevent injection attacks
- Validate query length and content

**Example:**
```python
def sanitize_query(query: str) -> str:
    """Sanitize user query."""
    if len(query) > 1000:
        raise InvalidQueryError("Query too long (max 1000 chars)")
    # Remove null bytes, control characters
    return query.encode("utf-8").decode("utf-8", errors="ignore")
```

### Rate Limiting

**Principles:**
- Respect provider rate limits
- Exponential backoff for retries
- Circuit breaker after consecutive failures

**Example:**
```python
@with_resilience(
    profile="aggressive",
    idempotent=True,
    max_retries=3,
    backoff_base=2
)
async def search_with_retry(query: str):
    """Search with automatic retry and backoff."""
    return await provider.search(query)
```

---

## Future Enhancements

### Short Term (3 months)

- [ ] Complete all backend implementations
- [ ] Achieve >90% test coverage
- [ ] Optimize cache hit rate >50%
- [ ] Measure HyDE effectiveness >10% improvement

### Medium Term (3-6 months)

- [ ] ML-based intent detection (if heuristic <90% accuracy)
- [ ] Query suggestions and autocomplete
- [ ] Performance optimization (profiling, hot paths)
- [ ] Advanced caching strategies (multi-level, write-through)

### Long Term (6-12 months)

- [ ] Distributed caching (Redis, Memcached)
- [ ] Federated search (cross-instance)
- [ ] Multi-modal search (image, video, audio)
- [ ] Custom ML models for ranking

---

## References

### Internal Documentation
- **PRD.md**: Product requirements document
- **SDD.md**: Solution design document
- **ADR-001**: Architecture decision record (async-first approach)
- **MIGRATION.md**: Migration guide (to be created)
- **TESTING.md**: Testing strategy (to be created)

### External Research
- [Python asyncio vs threading analysis 2024](https://medium.com/@george.seif042/async-vs-multi-threading-in-python-whats-the-difference-and-which-one-should-you-use-940b9d94c2e8)
- [HyDE: Precise Zero-Shot Dense Retrieval](https://arxiv.org/abs/2212.10496)
- [Unified Search Architecture Best Practices](https://www.mongodb.com/basics/unified-search)
- [Redis LRU+TTL Caching Strategies](https://redis.io/docs/manual/eviction/)

---

## Appendix A: Backend Integration Guide

### Adding a New Local Backend

**1. Implement Protocol:**
```python
class MyBackend:
    async def search(
        self,
        query: str,
        limit: int = 20,
        **kwargs
    ) -> list[SearchResult]:
        """Search implementation."""
        results = []
        # ... search logic ...
        return results

    @property
    def available(self) -> bool:
        """Check if backend is ready."""
        return True  # or check dependencies
```

**2. Register Backend:**
```python
# src/search_research/backends/__init__.py
from .my_backend import MyBackend

BACKENDS = {
    "my_backend": MyBackend(),
    # ... other backends ...
}
```

**3. Add Tests:**
```python
# tests/test_backends/test_my_backend.py
@pytest.mark.asyncio
async def test_my_backend_search():
    backend = MyBackend()
    results = await backend.search("test query", limit=5)
    assert len(results) >= 0
```

### Adding a New Web Provider

**1. Implement Protocol:**
```python
class MyProvider:
    def __init__(self, api_key: str):
        self.api_key = api_key

    async def search(
        self,
        query: str,
        limit: int = 10,
        **kwargs
    ) -> list[SearchResult]:
        """Search implementation."""
        # ... API call ...
        return results

    @property
    def available(self) -> bool:
        """Check if API key configured."""
        return bool(self.api_key)
```

**2. Register Provider:**
```python
# src/search_research/providers/__init__.py
from .my_provider import MyProvider

PROVIDERS = {
    "my_provider": MyProvider(
        api_key=os.getenv("MY_PROVIDER_API_KEY")
    ),
    # ... other providers ...
}
```

**3. Add Graceful Degradation:**
```python
# Provider skips automatically if unavailable
if not my_provider.available:
    logger.warning("MyProvider skipped: API key not set")
```

---

**Document Control**

- **Version:** 1.0
- **Date:** 2026-03-05
- **Status:** Draft
- **Author:** AI Assistant
- **Next Review:** 2026-03-12 (after Phase 1 completion)

**Related Documents:**
- PRD.md (Product Requirements)
- SDD.md (Solution Design)
- ADR-001 (Architecture Decision Record)
- MIGRATION.md (Migration Guide - to be created)
- TESTING.md (Testing Strategy - to be created)
