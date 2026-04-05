# Product Requirements Document (PRD)
# search-research Package

**Version:** 1.0
**Status:** Draft
**Author:** AI Assistant
**Date:** 2026-03-05
**Stakeholders:** CSF development team, research-skill maintainers

---

## 1. Executive Summary

### 1.1 Problem Statement

Current search infrastructure is split across two packages:
- **unified-search**: Local code/knowledge search (<1s)
- **research-skill**: Web research with HyDE (5-10s)

This separation creates:
- Duplicate backend implementations
- Inconsistent result formats
- Difficulty sharing improvements
- No unified interface for mixed local+web queries

### 1.2 Solution

Create a unified `search-research` package that provides:
- **Fast local search** for code/knowledge (<1s)
- **Comprehensive web search** with external providers (5-10s)
- **Intelligent routing** based on query intent
- **Unified API** for both `/search` and `/research` commands

### 1.3 Success Metrics

- **Performance**: FAST mode <1s, COMPREHENSIVE mode 5-10s
- **Functionality**: All existing backends work in new package
- **Integration**: Both `/search` and `/research` use new package
- **Testing**: >90% code coverage, integration tests pass
- **Adoption**: Migration completed within 4 weeks

---

## 2. Goals and Objectives

### 2.1 Primary Goals

1. **Unify search infrastructure** - Single package for local and web search
2. **Improve developer experience** - Consistent API across commands
3. **Enable intelligent routing** - Auto-detect query intent
4. **Maintain performance** - No regressions in existing workflows
5. **Support extensibility** - Easy to add new backends

### 2.2 Secondary Goals

1. **Reduce code duplication** - Share backends, cache, intent detection
2. **Improve testability** - Comprehensive test suite
3. **Enhance observability** - Clear logging, metrics
4. **Graceful degradation** - Work without API keys
5. **Documentation** - Complete API docs and migration guide

---

## 3. Functional Requirements

### 3.1 Core Functionality

#### FR-1: Unified Router

The package SHALL provide a unified router that supports:
- **FAST mode**: Local backends only (<1s)
- **COMPREHENSIVE mode**: All backends with HyDE (5-10s)
- **CUSTOM mode**: User-specified backends and options

```python
from search_research import SearchRouter, ResearchRouter, UnifiedRouter

# Fast local search
router = SearchRouter()
results = router.search("FastAPI patterns")  # <1s

# Comprehensive web search
router = ResearchRouter()
results = router.search("FastAPI best practices")  # 5-10s

# Full control
router = UnifiedRouter(mode=Mode.FAST)
results = router.search("FastAPI patterns", web=True)
```

#### FR-2: Local Backends

The package SHALL support the following local backends:
- **CDS**: Code Documentation Search (AST-based docstring search)
- **Grep**: Code Pattern Search (AST-based function/class search)
- **CHS**: Chat History Search (semantic search on conversations)
- **CKS**: Constitutional Knowledge System (knowledge base)
- **RLM**: Recursive Language Model (code generation search)
- **Persona**: Persona Memory Search (context-aware search)
- **MultiLang**: Tree-sitter multi-language code search
- **NotebookLM**: NotebookLM MCP integration

#### FR-3: Web Backends

The package SHALL support the following web backends:
- **Tavily**: AI-powered search with synthesis
- **Serper**: Google search with knowledge graph
- **Exa**: Neural/semantic search

All web backends SHALL:
- Gracefully degrade when API keys are missing
- Timeout after 5 seconds
- Return results in unified format
- Support retry with exponential backoff

#### FR-4: Query Intent Detection

The package SHALL provide automatic query intent detection:
- **LOCAL_ONLY**: Code patterns, function names, file paths
- **WEB_ENHANCED**: Best practices, tutorials, "latest"
- **MIXED**: Ambiguous queries

Intent detection SHALL be:
- >90% accurate on test corpus
- Overridable via explicit flags
- Logged for observability

#### FR-5: Query Caching

The package SHALL provide query caching:
- **LRU cache** with configurable size (default: 1000 queries)
- **TTL** with configurable expiration (default: 3600s)
- **Cache key** based on query + backend list
- **Cache stats** exposed via metrics

#### FR-6: Result Aggregation

The package SHALL aggregate results from multiple backends:
- **Merge** results from all backends
- **Deduplicate** across backends (URL, file_path)
- **Rank** by hybrid score (BM25 + cosine similarity)
- **Limit** to requested number of results

#### FR-7: HyDE Enhancement

The package SHALL support HyDE (Hypothetical Document Embeddings):
- **Generate** hypothetical document for web queries
- **Enhance** query with key phrases from document
- **Apply** only to web backends (not local)
- **Be optional** (can be disabled)

### 3.2 API Requirements

#### FR-8: Public API

The package SHALL export the following public API:

```python
# Router classes
SearchRouter
ResearchRouter
UnifiedRouter

# Mode enums
Mode.FAST
Mode.COMPREHENSIVE
Mode.CUSTOM

# Base classes
BaseSearchBackend
BaseWebBackend

# Intent detection
QueryIntent
IntentType

# Result schema
SearchResult
```

#### FR-9: Result Schema

All search results SHALL follow this schema:

```python
@dataclass
class SearchResult:
    # Content
    title: str
    content: str
    url: str | None
    file_path: str | None
    line_number: int | None

    # Metadata
    source: str
    score: float
    metadata: dict[str, Any]

    # Timestamps
    created_at: datetime
    cached: bool = False
```

### 3.3 CLI Integration

#### FR-10: /search Command

The `/search` command SHALL:
- Use `SearchRouter` by default (FAST mode)
- Support `--web` flag to include web providers
- Support `--auto` flag for intelligent routing
- Maintain backward compatibility with existing flags

#### FR-11: /research Command

The `/research` command SHALL:
- Use `ResearchRouter` (COMPREHENSIVE mode)
- Support all existing providers and modes
- Maintain backward compatibility with existing CLI

---

## 4. Non-Functional Requirements

### 4.1 Performance

#### NFR-1: Response Time

| Mode | Target | Maximum |
|------|--------|----------|
| FAST | <1s | 1.5s |
| COMPREHENSIVE | 5-10s | 15s |

#### NFR-2: Backend Timeout

| Backend Type | Timeout |
|--------------|----------|
| Local | 0.5s |
| Web | 5s |

#### NFR-3: Cache Performance

- Cache hit rate: >50% for repeated queries
- Cache lookup: <10ms
- Cache size: <100MB for 1000 queries

### 4.2 Reliability

#### NFR-4: Graceful Degradation

- Web backends MUST work without API keys (skip with warning)
- Local backends MUST always work (no external dependencies)
- Cache failures MUST NOT crash search (log and continue)

#### NFR-5: Error Handling

- All exceptions MUST be caught and logged
- Partial results MUST be returned on backend failures
- Error messages MUST be actionable (suggest fixes)

### 4.3 Maintainability

#### NFR-6: Code Quality

- >90% test coverage
- Type hints on all public APIs
- Docstrings on all public functions
- PEP 8 compliant

#### NFR-7: Extensibility

- New backends MUST be addable without modifying core
- Backend registration MUST be declarative
- Configuration MUST be external (not hardcoded)

### 4.4 Compatibility

#### NFR-8: Python Version

- Support Python 3.10+
- Test on Python 3.10, 3.11, 3.12

#### NFR-9: Backward Compatibility

- Existing `/search` workflows MUST continue working
- Existing `/research` workflows MUST continue working
- Result format MUST be backward compatible

---

## 5. Implementation Plan

### 5.1 Phase 1: Package Foundation (Week 1)

**Deliverables:**
- Package structure created
- Core infrastructure implemented
- Test infrastructure setup
- Basic router API works

**Tasks:**
1. Create package structure (`search-research/`)
2. Implement `base.py` (BaseSearchBackend ABC)
3. Implement `cache.py` (QueryCache)
4. Implement `intent_detector.py` (QueryIntentDetector)
5. Implement `router.py` (UnifiedRouter skeleton)
6. Setup pytest, conftest.py
7. Write initial tests

**Acceptance Criteria:**
- ✅ Package installs successfully
- ✅ `pip install search-research` works
- ✅ `from search_research import SearchRouter` works
- ✅ Tests pass for core infrastructure

### 5.2 Phase 2: Local Backends (Week 1-2)

**Deliverables:**
- All local backends migrated
- `SearchRouter` fully functional
- Integration tests passing

**Tasks:**
1. Copy local backends from `unified-search`:
   - CDS, Grep, CHS, CKS, RLM, Persona, MultiLang, NotebookLM
2. Update imports (namespace changes)
3. Write tests for each backend
4. Implement `SearchRouter` (FAST mode)
5. Write integration tests
6. Performance testing (<1s target)

**Acceptance Criteria:**
- ✅ All local backends work in new package
- ✅ `SearchRouter.search()` returns results
- ✅ Integration tests pass
- ✅ Performance: <1s for local queries
- ✅ Test coverage: >90%

### 5.3 Phase 3: Web Backends (Week 2)

**Deliverables:**
- All web backends implemented
- `ResearchRouter` fully functional
- Graceful degradation working

**Tasks:**
1. Implement `base_web.py` (BaseWebBackend ABC)
2. Implement web providers:
   - Tavily backend
   - Serper backend
   - Exa backend
3. Add API key management
4. Implement graceful degradation
5. Implement `ResearchRouter` (COMPREHENSIVE mode)
6. Write integration tests
7. Performance testing (5-10s target)

**Acceptance Criteria:**
- ✅ All web backends work with API keys
- ✅ Graceful degradation without keys (skip with warning)
- ✅ `ResearchRouter.search()` returns results
- ✅ Integration tests pass
- ✅ Performance: 5-10s for web queries
- ✅ Test coverage: >90%

### 5.4 Phase 4: HyDE Enhancement (Week 2-3)

**Deliverables:**
- HyDE query enhancement implemented
- Integrated into `ResearchRouter`
- Tests show measurable improvement

**Tasks:**
1. Implement HyDE query enhancement
2. Integrate into `ResearchRouter`
3. Add tests for HyDE effectiveness
4. Measure improvement (relevance scores)
5. Document HyDE behavior

**Acceptance Criteria:**
- ✅ HyDE improves web search relevance (>10% improvement)
- ✅ HyDE is optional (can be disabled)
- ✅ Tests demonstrate improvement
- ✅ Documentation complete

### 5.5 Phase 5: Consumer Integration (Week 3)

**Deliverables:**
- `/search` updated to use new package
- `/research` updated to use new package
- Backward compatibility maintained

**Tasks:**
1. Update `__csf` to use `SearchRouter`
2. Update `research-skill` to use `ResearchRouter`
3. Add deprecation warnings to `unified-search`
4. Update documentation
5. Test backward compatibility
6. Migration testing

**Acceptance Criteria:**
- ✅ `/search` works with new package
- ✅ `/research` works with new package
- ✅ Existing workflows unaffected
- ✅ No performance regressions
- ✅ Documentation updated

### 5.6 Phase 6: Deprecation & Migration (Week 4)

**Deliverables:**
- `unified-search` deprecated
- Migration guide published
- Support plan in place

**Tasks:**
1. Add deprecation warnings to `unified-search`
2. Publish migration guide
3. Update README with migration instructions
4. Announce deprecation timeline
5. Create support plan
6. Update package metadata

**Acceptance Criteria:**
- ✅ Clear migration path documented
- ✅ Deprecation timeline communicated
- ✅ Support plan published
- ✅ Package metadata updated

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Coverage Goal:** >90%

**Test Categories:**
- Backend tests (each backend tested independently)
- Cache tests (hit/miss, TTL, size limits)
- Intent detection tests (accuracy, edge cases)
- Result aggregation tests (merge, dedup, ranking)

### 6.2 Integration Tests

**Test Scenarios:**
- FAST mode with local backends only
- COMPREHENSIVE mode with all backends
- CUSTOM mode with specific backends
- Web backends with/without API keys
- Cache hit/miss scenarios

### 6.3 Performance Tests

**Benchmarks:**
- FAST mode: <1s for 10 queries
- COMPREHENSIVE mode: 5-10s for 10 queries
- Cache lookup: <10ms
- Backend timeout: 0.5s local, 5s web

### 6.4 End-to-End Tests

**Test Flows:**
1. User searches code patterns (`/search "FastAPI patterns"`)
2. User researches best practices (`/research "FastAPI best practices"`)
3. User enables web search (`/search "FastAPI" --web`)
4. User with no API keys (graceful degradation)

---

## 7. Dependencies

### 7.1 External Dependencies

**Required:**
- Python 3.10+
- pytest (testing)
- pydantic (result schema)

**Optional:**
- Tavily API key
- Serper API key
- Exa API key
- NotebookLM MCP server

### 7.2 Internal Dependencies

**Consumers:**
- `__csf` (CSF framework)
- `research-skill` (research command)

**Replaces:**
- `unified-search` (local search package)

---

## 8. Risks and Mitigation

### 8.1 Technical Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Performance regression in FAST mode | HIGH | MEDIUM | Comprehensive performance testing, benchmarking |
| Intent detection accuracy | MEDIUM | MEDIUM | Large test corpus, explicit flags override |
| Web backend API failures | MEDIUM | HIGH | Graceful degradation, retry logic |
| Cache memory leaks | LOW | LOW | Cache size limits, monitoring |
| HyDE effectiveness | LOW | MEDIUM | A/B testing, optional flag |

### 8.2 Project Risks

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Migration complexity | HIGH | MEDIUM | Phased rollout, backward compatibility |
| Breaking existing workflows | HIGH | LOW | Comprehensive testing, deprecation warnings |
| API key management burden | MEDIUM | MEDIUM | Clear documentation, graceful degradation |
| Timeline overruns | MEDIUM | LOW | Realistic estimates, phased delivery |

---

## 9. Open Questions

### 9.1 Package Name

**Question:** Is `search-research` the best name?

**Options:**
- `search-research` (current proposal)
- `unified-search-research`
- `omniscient`
- `search-engine`
- `knowledge-search`

**Decision needed:** 2026-03-06

### 9.2 API Key Storage

**Question:** How should users configure API keys?

**Options:**
- Environment variables (`TAVILY_API_KEY`)
- Config file (`~/.search-research/config.toml`)
- CLI flags (`--tavily-api-key`)
- Hybrid (env vars + config file)

**Decision needed:** 2026-03-06

### 9.3 HyDE Implementation

**Question:** Should HyDE be LLM-generated or template-based?

**Options:**
- LLM-generated (current research-skill approach, slower)
- Template-based (faster, less accurate)
- Optional (user can enable/disable)

**Decision needed:** 2026-03-06

---

## 10. Success Criteria

### 10.1 Must Have (P0)

- ✅ Package installs successfully
- ✅ FAST mode <1s performance
- ✅ COMPREHENSIVE mode 5-10s performance
- ✅ All local backends work
- ✅ Web backends work with API keys
- ✅ Graceful degradation without keys
- ✅ >90% test coverage
- ✅ Integration with `/search` and `/research`

### 10.2 Should Have (P1)

- ✅ Intent detection >90% accuracy
- ✅ HyDE improves relevance >10%
- ✅ Cache hit rate >50%
- ✅ Complete documentation
- ✅ Migration guide
- ✅ Backward compatibility

### 10.3 Nice to Have (P2)

- ✅ Performance monitoring/metrics
- ✅ Advanced caching strategies
- ✅ Custom backend registration
- ✅ Result filtering/sorting options

---

## 11. Timeline

### Week 1 (Mar 6-12)
- Phase 1: Package Foundation
- Phase 2: Local Backends (start)

### Week 2 (Mar 13-19)
- Phase 2: Local Backends (complete)
- Phase 3: Web Backends

### Week 3 (Mar 20-26)
- Phase 4: HyDE Enhancement
- Phase 5: Consumer Integration (start)

### Week 4 (Mar 27-Apr 2)
- Phase 5: Consumer Integration (complete)
- Phase 6: Deprecation & Migration

**Target Release:** 2026-04-02

---

## 12. Appendices

### Appendix A: API Reference

[Detailed API documentation to be created during implementation]

### Appendix B: Migration Guide

[Step-by-step migration guide to be created during Phase 6]

### Appendix C: Performance Benchmarks

[Benchmark results to be collected during Phase 2-4]

### Appendix D: Test Coverage Report

[Coverage report to be generated after each phase]

---

## 13. Approval

**Stakeholders:**
- [ ] CSF development team
- [ ] research-skill maintainers
- [ ] Architecture review
- [ ] Security review

**Approval Date:** _______________

---

## Changelog

| Version | Date | Changes | Author |
|---------|------|---------|--------|
| 1.0 | 2026-03-05 | Initial PRD creation | AI Assistant |
