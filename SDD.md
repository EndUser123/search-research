# Solution Design Document (SDD)
# search-research Package

**Version:** 1.0 | **Status:** Draft | **Date:** 2026-03-05

## Executive Summary

Technical architecture for unified search and research system with fast local code/knowledge search (<1s) and comprehensive web research (5-10s).

## Key Design Decisions

1. **Asyncio for I/O-bound concurrency** - Multiple backends run concurrently
2. **Protocol-based interfaces** - Backends implement protocols, not inheritance
3. **Mode-based routing** - FAST (local), COMPREHENSIVE (all), CUSTOM (user-specified)
4. **Graceful degradation** - Web backends skip cleanly when API keys missing
5. **Unified result schema** - SearchResult dataclass with strict typing

## Architecture

```
Consumer Layer (commands, skills)
         ↓
UnifiedRouter (mode-based routing)
         ↓
    Intent Detection → Backend Selection
         ↓
    ┌──────────┬───────────┬──────────────┐
    ▼          ▼           ▼              ▼
Local    Web    NotebookLM    Result
Backends  Backends   Backend    Aggregation
(I/O)    (I/O)      (I/O)      & Ranking
```

## Core Components

### UnifiedRouter (Async)
- Concurrent backend execution via asyncio.gather()
- Mode selection (FAST/COMPREHENSIVE/CUSTOM)
- Intent detection for automatic routing
- Result aggregation and ranking
- LRU caching with TTL

### Backend Protocols
```python
class BaseSearchBackend(Protocol):
    async def search(query: str, limit: int) -> list[SearchResult]
    @property
    def available(self) -> bool
```

### Query Intent Detection
- LOCAL_ONLY: Code patterns, function names, file paths
- WEB_ENHANCED: Best practices, tutorials
- MIXED: Ambiguous queries
- Target: >90% accuracy

### Result Aggregation
- Merge results from all backends
- Deduplicate by URL/file_path
- Rank by hybrid score (BM25 + cosine)
- Limit to top N results

### Query Caching
- LRU cache (default: 1000 queries)
- TTL (default: 3600s)
- Target hit rate: >50%

### HyDE Enhancement
- Generate hypothetical document
- Extract 3-5 key phrases
- Enhance query before web search
- Improvement: ~10-15% relevance

## Async Architecture

**Decision:** Asyncio over threading/multiprocessing

**Rationale:**
- I/O-bound workload (file reads, network requests)
- No GIL contention
- Clean async/await syntax
- Concurrent execution without overhead

**Implementation:**
```python
async def search_async(self, query: str, limit: int):
    tasks = [backend.search(query, limit) for backend in backends]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return self._aggregate_results(results)
```

## Type System

**Decision:** Domain models with TypeVars

**Components:**
- SearchResult dataclass (immutable)
- Mode enum
- Backend protocols (BaseSearchBackend, BaseWebBackend)
- Generic type parameters for reusability

**Target:** 100% type coverage on public API

## GIL & Multiprocessing

**Decision:** No multiprocessing needed

**Rationale:**
- I/O-bound workload
- Asyncio provides concurrency without process overhead
- Lower memory footprint
- No GIL contention with I/O operations

## Error Handling

**Exception Hierarchy:**
- SearchResearchError (base)
  - BackendError
    - BackendUnavailableError
    - BackendTimeoutError
  - InvalidQueryError
  - CacheError

**Strategy:**
- Backends: Catch exceptions, return empty results
- Router: Validate query, catch backend exceptions during gather
- Cache: Graceful degradation

## Performance

### Targets

| Metric | Target | Max |
|--------|--------|-----|
| FAST mode | <1s | 1.5s |
| COMPREHENSIVE | 5-10s | 15s |
| Local timeout | 0.5s | - |
| Web timeout | 5s | - |
| Cache hit rate | >50% | - |
| Intent accuracy | >90% | - |

### Optimizations

1. Concurrent backend execution
2. Query caching (LRU + TTL)
3. Lazy backend initialization
4. Result streaming

## Testing

**Coverage Targets:**
- Core router: >95%
- Intent detection: >90%
- Cache: >90%
- Overall: >90%

**Test Categories:**
- Unit tests (router, cache, intent)
- Integration tests (modes)
- Performance tests (latency)
- Async tests (concurrency)

## Deployment

**Python:** 3.10+ (tested on 3.14)
**Platforms:** Windows 11 (primary), macOS, Linux
**Dependencies:** pydantic>=2.0.0, typing-extensions

## Observability

**Logging:** DEBUG/INFO/WARNING/ERROR levels
**Metrics:** Query latency, backend success rate, cache hit rate, intent accuracy

## Security

**API Keys:** Environment variables only, never hardcode
**Validation:** Query sanitization, result cleaning, URL validation
**Rate Limiting:** Respect provider limits, exponential backoff

## Migration

**From unified-search:**
- Update imports: `unified_search` → `search_research`
- Update router: `EnhancedUnifiedSearchRouter` → `UnifiedRouter`

**From research-skill:**
- Import ResearchRouter
- Remove duplicate implementations

## Future Enhancements

**Short term (3mo):** Implement all backends, complete cache, integration tests
**Medium term (3-6mo):** ML-based scoring, query suggestions, performance optimization
**Long term (6-12mo):** Distributed caching, federated search, multi-modal search

## Risk Mitigation

| Risk | Mitigation |
|------|------------|
| Intent detection accuracy | Explicit flags override |
| Backend timeouts | Per-backend timeouts |
| API key management | Environment variables only |
| Web provider API changes | Graceful degradation |

---

**Document Control**

Version: 1.0
Date: 2026-03-05
Status: Draft - Pending Review
