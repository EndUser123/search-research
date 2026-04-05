# Architecture Decision: Async vs. Thread-based for search-research

**Date:** 2026-03-05
**Query:** Which architecture is better for search-research refactoring - PRD async-first or actual thread-based?
**Decision:** Adopt PRD async-first architecture with hybrid migration approach

## Decision

**PRD architecture (async-first) is better** for the search-research refactoring, with pragmatic migration: adopt PRD's async/streaming design but preserve backward compatibility via sync wrapper.

## Rationale

1. **I/O-bound workload optimized for async** - 10+ web providers, 8 local backends, file I/O, database queries all benefit from asyncio concurrent execution
2. **Superior scalability** - Async handles 50+ concurrent backend calls with lower memory overhead than thread pools  
3. **Future-proof ecosystem** - Python 3.12+ async patterns align with modern libraries (httpx, FastAPI, asyncio.Runner)
4. **Streaming results enable better UX** - Progressive feedback prevents 10-second waits for aggregation
5. **Type system improvements** - ResultFilter, Pagination, and progress callbacks enable programmatic integration

## Alternatives Considered

### 1. Keep thread-based architecture (actual)
- **Pros:** No migration work, proven stability, test coverage exists
- **Cons:** Poorer scalability for web providers (10+ concurrent threads inefficient), higher memory overhead, no streaming support
- **Trade-off:** Short-term simplicity vs. long-term scalability

### 2. Full async rewrite (PRD pure)
- **Pros:** Modern async patterns, streaming API, optimal performance  
- **Cons:** 2-3 week migration, all backends must support async, breaking change for consumers
- **Trade-off:** Performance vs. migration cost

### 3. Hybrid approach (recommended)
- **Pros:** Async for new code, sync wrapper for backward compatibility, incremental migration
- **Cons:** Maintaining two code paths temporarily, slightly more complex
- **Trade-off:** Balance modernization with stability

## Risk

- **Async migration breaking existing consumers** - unified-search and __csf currently import router
  - **Mitigation:** Provide sync wrapper (`def search()`) that calls `asyncio.run(search_async())`
- **MCP provider compatibility** - research-skill providers are MCP protocol, not async Python
  - **Mitigation:** Create async MCP client wrapper using `aiohttp` or async MCP SDK
- **Test suite refactoring** - All tests use sync router
  - **Mitigation:** Add `pytest-asyncio` fixtures, parameterize tests for sync/async
- **Intent classifier dependency** - __csf LLM-based intent_classifier not portable
  - **Mitigation:** Copy + create simplified rule-based fallback

## Migration Strategy

### Phase 1 (Week 1-2): Async Core + Sync Wrapper
- Implement `UnifiedRouterAsync` with async backend execution
- Create sync wrapper `UnifiedRouter` that calls `asyncio.run()`
- Add streaming API (`AsyncIterator[SearchResult]`)
- Copy and update 3 core backends (CDS, Grep, Skills) to async

### Phase 2 (Week 2-3): Full Backend Migration
- Migrate remaining local backends (CHS, CKS, RLM, Persona, MultiLang) to async
- Create async MCP client wrappers for web providers
- Add progress callback support
- Update 50% of test suite to `pytest-asyncio`

### Phase 3 (Week 3-4): Advanced Features
- Implement ResultFilter, Pagination
- Add configuration hierarchy (TOML)
- Provider health monitoring with failover
- Complete test suite migration

### Phase 4 (Week 4+): Cleanup
- Deprecate sync wrapper (keep for 2 releases)
- Remove thread-based code paths
- Performance optimization (async benchmarks)

## Type System Design

```python
from typing import Protocol, TypeVar, Generic, AsyncIterator, Callable, overload

T = TypeVar('T')

class SearchBackend(Protocol[T]):
    """Protocol for search backends."""
    async def search_async(self, query: str, **kwargs) -> list[T]: ...
    async def search_streaming(self, query: str, **kwargs) -> AsyncIterator[T]: ...

@dataclass
class ResultFilter:
    """Filter search results after retrieval."""
    backend: list[str] | None = None
    min_score: float | None = None
    time_range: str | None = None
    source_type: list[str] | None = None

class UnifiedRouter:
    @overload
    async def search(self, query: str) -> SearchResults: ...
    
    @overload
    async def search(self, query: str, streaming: Literal[True]) -> AsyncIterator[SearchResult]: ...
    
    @overload  
    async def search(self, query: str, progress_callback: Callable[[str, float], None]) -> SearchResults: ...
    
    async def search(self, query: str, **kwargs) -> SearchResults | AsyncIterator[SearchResult]:
        ...
```

## Confidence

**85%** - Async is correct direction for I/O-bound workload with 10+ concurrent providers.

**Evidence basis:**
- Python async best practices (https://docs.python.org/3/library/asyncio.html)
- RealPython asyncio guide (https://realpython.com/async-io-python/)
- FastAPI async patterns (proven production deployment)
- Codebase analysis: 3 packages reviewed (unified-search, research-skill, __csf search)

## Key Assumptions

1. Async migration can be completed in 2-3 weeks (high complexity)
2. MCP providers have async-compatible clients or can be wrapped
3. Test suite migration with `pytest-asyncio` is straightforward
4. Intent classifier can be extracted from __csf or replaced with rule-based fallback

## Adversarial Self-Review

**Weakest assumption:** "Async migration can be completed in 2-3 weeks" - Underestimates complexity of converting 9 local backends + 10 web providers + test suite. If timeline is constrained (4 weeks total), hybrid approach (async core + sync wrapper) is more realistic than full async rewrite.
