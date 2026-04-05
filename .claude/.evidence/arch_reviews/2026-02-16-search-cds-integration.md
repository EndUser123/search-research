# Implementation Plan: Integrate Dead and Underutilized Search/CDS Tools

**Plan Created:** 2026-02-16
**Status:** DRAFT
**Objective:** Integrate dead and underutilized search/CDS tools into `EnhancedUnifiedSearchRouter`

---

## 1. Problem Statement

The `/search` and CDS (Code Documentation Search) systems have significant capability gaps. Existing powerful tools are either completely un-integrated or gated behind environment variables, leaving valuable functionality unused:

### Dead/Unintegrated Tools (Previously Discovered)
- **LSP Backend** (`lsp_backend.py`) - exists but is NOT imported into `unified_router.py`
- **Cross-Encoder Reranking** - exists but gated by `CROSS_ENCODER_ENABLED` env var (default: OFF)
- **Tree-sitter (MultiLang)** - exists but gated by `SEARCH_USE_MULTILANG=1` env var
- **Static Call Graph** (`static_call_graph.py`) - standalone, not integrated
- **Code Property Graph** (`code_property_graph.py`) - standalone, not integrated
- **Data Flow Analyzer** (`data_flow_analyzer.py`) - standalone, not integrated
- **Control Flow Analyzer** (`control_flow_analyzer.py`) - standalone, not integrated
- **HDMA Analyzer** (`hdma/analyzer.py`) - standalone, not integrated

### NEWLY DISCOVERED Tools (Dead/Underutilized)

#### Query Intent & Backend Selection
- **Query Intent Classifier** (`search/query_intent.py`) - Complete intent classification with `QueryIntentDetector`
  - `classify_query_intent()` - Returns IntentType (NAVIGATIONAL, INFORMATIONAL, TECHNICAL, EXPLORATORY)
  - `QueryIntentDetector.detect()` - Detects intent and maps to backends via `get_preferred_backends()`
  - Maps: CODE → ["CODE", "GREP", "LSP"], KNOWLEDGE → ["CKS", "DOCS", "CDS"]
  - Uses shared `classify_intent` from hooks (embedding-based semantic classification)

#### Vector/Embedding Tools
- **HNSW Index** (`search/hnsw_index.py`) - Complete HNSW index implementation (NOT a stub!)
  - Full HNSW class with add/search/save/load/set_ef methods
  - O(log N) search complexity, 90-99% recall
  - Incremental build support
- **HNSW Backend** (`search/backends/hnsw_backend.py`) - Complete HNSW vector backend, NOT integrated
- **FAISS Lock Wrapper** (`search/faiss_lock.py`) - `faiss_open_read()` with retry logic and exponential backoff
- **FAISS Vector Store** (`core/faiss_vector_store.py`) - FAISS-based vector storage
- **Vector Manager** - Multiple implementations across codebase

#### Reranking/Scoring Tools
- **MMR Diversity Ranking** (`search/diversity.py`) - Maximal Marginal Relevance for result diversity
  - `mmr_rerank()` - Balance relevance with diversity
  - `filter_redundant()` - Remove highly redundant results
  - `get_diverse_subset()` - Diverse subset with token efficiency
- **Hybrid Scorer** (`search/backends/hybrid_scorer.py`) - BM25 + cosine combination
  - `HybridScorer.combine_scores()` - Combine FTS5 and FAISS results
  - `normalize_scores_minmax()` - Min-max normalization utility
- **Confidence Calibration** (`search/confidence_calibration.py`) - Source trust scoring
  - `SourceTrustScorer` - Per-source trust weights (CKS: 0.95, CODE: 0.90, etc.)
  - `ConfidenceCalibrator` - Calibrate using trust + citation history
- **Faceted Search** (`search/faceted.py`) - Multi-dimensional filtering
  - `filter_results()` - By sources, types, dates, file_paths, categories, skill_sources
  - `get_facets()` - Extract facet counts from results
- **CKS Reranking** (`cks/reranking.py`) - Multi-signal fusion (RRF, temporal boosting, MMR)
- **Research Reranking** (`packages/research/src/research_skill/processors/reranking.py`) - Temporal boosting, usage scoring
- **Adaptive Ranking System** (`core/adaptive_ranking_system.py`) - Dynamic repository ranking

#### Tree-sitter Integration
- **Tree-sitter Wrapper** (`cli/nip/tree_sitter_wrapper.py`) - CLI wrapper for tree-sitter analysis
- **Tree-sitter Enhanced** (`modules/discover/hardware_accelerated/tree_sitter_enhanced.py`) - Hardware-accelerated CTAGS analyzer
- **Tree-sitter Integration** (`commands/rca/tree_sitter_integration.py`) - RCA system integration

#### Dependency Analysis
- **Dependency Graph** (`quality/core/dependency_graph.py`) - Full program dependency graph
  - `SymbolKind` enum (FUNCTION, ASYNC_FUNCTION, CLASS, METHOD, VARIABLE, IMPORT, PARAMETER)
  - `EdgeKind` enum (CALLS, DEFINES, IMPORTS, EXTENDS, USES, INSTANTIATES)
  - `Symbol` dataclass with qualified_name(), to_dict()
  - Cross-file reference resolution, call graph construction
- **Smart Dependency Manager** (`core/smart_dependency_manager.py`) - Dependency resolution
- **Import Dependency Checker** (`modules/verification/import_dependency_checker.py`) - Import analysis

#### Serena Integration Tools
- **Serena Symbols** (`modules/serena/core/symbols.py`) - LSP-spec symbol data models
- **Serena Knowledge Integration** (`modules/enhanced_development/serena_knowledge_integration.py`)
- **Serena AID Integration** (`modules/core_integration/serena_aid_integration.py`)

#### Indexing Infrastructure
- **Knowledge Indexing** (`knowledge/indexing.py`) - Knowledge base indexing
- **Chat Indexing Data Extractor** (`modules/analysis/chat_search/src/chat_indexing_data_extractor.py`)

#### Dead/Unused Implementations
- **Legacy Reranking** (`search/reranking.py`) - Superseded by `diversity.py`
- **Duplicate LSP Backend** (`knowledge/search/backends/lsp_backend.py`) - Duplicate of main LSP backend
- **Missing Module** - `cc_integration_lsp` referenced but doesn't exist (breaks `/lsp` CLI)

This results in:
- Slower searches (AST instead of tree-sitter, no HNSW acceleration)
- Less relevant results (no cross-encoder reranking, no temporal boosting)
- Missing query types (no symbol search via LSP, no call graph navigation, no dependency analysis)
- Duplicated code analysis (graph tools exist but aren't used by search)
- Wasted infrastructure (HNSW, FAISS backends exist but unused)

---

## 2. Context Analysis

### Existing Architecture

The `EnhancedUnifiedSearchRouter` (`__csf/src/search/unified_router.py`) orchestrates parallel search across multiple backends.

**Backend Integration Pattern:**
```python
# 1. Import with availability check
MULTILANG_BACKEND_AVAILABLE = False
try:
    from .backends.multilang_backend import MultiLangCodeBackend
    MULTILANG_BACKEND_AVAILABLE = True
except ImportError:
    pass

# 2. Initialize in __init__
if MULTILANG_BACKEND_AVAILABLE:
    self.multilang_backend = MultiLangCodeBackend(root_paths=[self._root_path])

# 3. Add to _get_backend_map()
all_backends[BACKEND_MULTILANG] = self.multilang_backend

# 4. Add normalization in _search_single()
if name == BACKEND_MULTILANG:
    # normalize result format
```

### Allowed APIs

| API | Source | Signature | Status |
|-----|--------|-----------|--------|
| **Core Backends** | | | |
| `MultiLangCodeBackend` | `multilang_backend.py:105` | `__init__(root_paths, use_tree_sitter, exclude_patterns)` | Gated |
| `LSPSymbolBackend` | `lsp_backend.py:162` | `__init__(root_paths)` | ✅ Complete, NOT integrated |
| `HNSWVectorBackend` | `hnsw_backend.py:18` | `__init__(dimension, M, ef_construction, ef_search)` | ✅ Complete, NOT integrated |
| `HNSWIndex` | `hnsw_index.py:24` | `__init__(dimension, M, ef_construction, ef_search)` | ✅ Complete |
| **Search Interface** | | | |
| `search()` | All backends | `def search(self, query: str, limit: int) -> list[SearchResult]` | Standard |
| **Reranking** | | | |
| `CrossEncoderReranker` | `reranking/cross_encoder.py:20` | `__init__(model_name: str)` | Gated |
| `CKSReranker` | `cks/reranking.py` | `rerank_cks(results, query)` | Standalone |
| **Graph Analysis** | | | |
| `StaticCallGraphBuilder` | `modules/discover/static_call_graph.py:198` | `__init__(language: str)` | Standalone |
| `CPGBuilder` | `modules/discover/code_property_graph.py:331` | `__init__(language: str)` | Standalone |
| `DependencyGraph` | `quality/core/dependency_graph.py` | `__init__()` | Standalone |

### Anti-Patterns to Avoid

| Invalid Pattern | Correct Pattern |
|----------------|-----------------|
| Assuming tree-sitter is available | Check `_TREE_SITTER_AVAILABLE` flag |
| `CrossEncoderReranker()` without feature flag | Check `CROSS_ENCODER_ENABLED` env var |
| Using duplicate LSP implementations | Use `search/backends/lsp_backend.py`, NOT `knowledge/search/backends/lsp_backend.py` |
| Direct HNSW without fallback | Check `HAS_HNSW` flag, provide FAISS fallback |
| Hardcoding hnswlib import | Use `hnsw_index.HAS_HNSW` availability check |

---

## 3. Existing Implementation Discovery

### Files Requiring Modification

| File | Current State | Required Change |
|------|---------------|-----------------|
| `search/unified_router.py` | Missing LSP/HNSW imports, gated features | Add imports, remove gates |
| `search/backends/lsp_backend.py` | Complete backend, not imported | Already conforms to interface ✅ |
| `search/backends/hnsw_backend.py` | Complete backend, not imported | Already conforms to interface ✅ |
| `search/reranking/cross_encoder.py` | Gated by env var (default OFF) | Remove gate, enable by default |
| `search/backends/multilang_backend.py` | Gated by env var | Remove gate, enable by default |

### Newly Discovered Available Files (Ready to Integrate)

| File | Purpose | Integration Status |
|------|---------|-------------------|
| `search/hnsw_index.py` | HNSW vector index implementation | ✅ Ready, wrap in backend |
| `search/backends/hnsw_backend.py` | HNSW vector search backend | ✅ Ready to add to router |
| `cks/reranking.py` | RRF + temporal boosting + MMR | ⚠️ Needs adapter |
| `packages/research/.../reranking.py` | Temporal boosting with half-life | ⚠️ Needs adapter |
| `core/faiss_vector_store.py` | FAISS vector storage | ⚠️ Needs adapter |
| `quality/core/dependency_graph.py` | Dependency analysis | ⚠️ Needs backend wrapper |
| `cli/nip/tree_sitter_wrapper.py` | Tree-sitter CLI wrapper | ⚠️ Needs backend adapter |

### Dead/Duplicate Files to Remove

| File | Status | Action |
|------|--------|--------|
| `knowledge/search/backends/lsp_backend.py` | Duplicate | Remove |
| `knowledge/search/backends/lsp_protocol.py` | Duplicate | Remove |
| `search/reranking.py` | Superseded by `diversity.py` | Remove |

### Missing Module (Blocker)

| Missing | Referenced By | Action |
|---------|--------------|--------|
| `cc_integration_lsp` | `cli/nip/lsp_query.py` | Implement or fix import |

### New Backend Wrappers to Create

| File | Purpose | Wraps |
|------|---------|-------|
| `search/backends/call_graph_backend.py` | Wrapper for `StaticCallGraphBuilder` | `modules/discover/static_call_graph.py` |
| `search/backends/cpg_backend.py` | Wrapper for `CPGBuilder` | `modules/discover/code_property_graph.py` |
| `search/backends/hdma_backend.py` | Wrapper for `HDMAAnalyzer` | `knowledge/analysis/hdma/analyzer.py` |
| `search/backends/dependency_backend.py` | Wrapper for `DependencyGraph` | `quality/core/dependency_graph.py` |

### Backend Name Constants to Add

```python
# Already exists but not integrated
BACKEND_LSP = "LSP"

# New backends to add
BACKEND_CALL_GRAPH = "CALL_GRAPH"
BACKEND_CPG = "CPG"
BACKEND_HDMA = "HDMA"
BACKEND_DEPENDENCY = "DEPENDENCY"
BACKEND_HNSW = "HNSW"  # Vector search
```

---

## 4. Test Discovery

### Existing Tests

| Test File | Coverage | Notes |
|-----------|----------|-------|
| `tests/lib/search/test_cross_encoder_reranking.py` | Cross-encoder | Shows usage pattern |
| `tests/lib/search/test_grep_backend.py` | 93% | Backend integration pattern |
| `tests/lib/search/test_cds_backend.py` | 84% | Backend integration pattern |
| `tests/lib/search/test_kg_backend.py` | ~90% | Backend integration pattern |

---

## 5. Proposed Solution

### Phase 0: Cleanup & Consolidation (NEW)

**Change 0.1: Remove Duplicate/Dead Code**
- File: `knowledge/search/backends/lsp_backend.py` (DELETE)
- File: `knowledge/search/backends/lsp_protocol.py` (DELETE)
- File: `search/reranking.py` (DELETE - superseded by `diversity.py`)

**Change 0.2: Fix Missing Module Dependency**
- File: `cli/nip/lsp_query.py`
- Either implement `cc_integration_lsp` module OR refactor to use existing `LSPSymbolBackend`

### Phase 1: Quick Wins (Remove Gates, Add Available Backends)

**Change 1.1: Enable Cross-Encoder by Default**
- File: `search/unified_router.py:328-332`
- Remove `enable_cross_encoder` parameter default
- Default to `True` instead of `False`
- Change `CROSS_ENCODER_ENABLED` env var default to "1"

**Change 1.2: Enable MultiLang by Default**
- File: `search/unified_router.py`
- Remove `SEARCH_USE_MULTILANG` environment variable check
- Use tree-sitter when available, fall back to AST

**Change 1.3: Add LSP Backend Import**
- File: `search/unified_router.py`
- Add import with availability check (follows existing pattern)
- Add `BACKEND_LSP = "LSP"` constant
- Initialize in `__init__`, add to `_get_backend_map()`

**Change 1.4: Add HNSW Backend Integration (NEW)**
- File: `search/unified_router.py`
- Add import: `from .backends.hnsw_backend import HNSWVectorBackend`
- Add `BACKEND_HNSW = "HNSW"` constant
- Initialize with availability check (`hnsw_index.HAS_HNSW`)
- Add to backend map, add result normalization

### Phase 2: Reranking Enhancements (NEW)

**Change 2.1: Integrate CKS Reranking**
- File: `search/reranking/cks_reranking_adapter.py` (NEW)
- Adapt `cks/reranking.py` for use in unified search
- Add RRF (Reciprocal Rank Fusion) for multi-source queries
- Add temporal boosting (recency weighting)

**Change 2.2: Integrate Research Temporal Boosting**
- File: `search/reranking/temporal_boosting.py` (NEW)
- Extract temporal boosting logic from `packages/research/.../reranking.py`
- Add half-life decay for freshness scoring

**Change 2.3: Unified Reranking Pipeline**
- File: `search/unified_router.py`
- Chain rerankers: Cross-Encoder → Temporal → MMR
- Make reranking configurable per backend

### Phase 3: Graph Backend Wrappers

**Change 3.1: Create CallGraphBackend**
- File: `search/backends/call_graph_backend.py`
- Wrap `StaticCallGraphBuilder` from `modules/discover/static_call_graph.py`
- Implements `search(query, limit)` interface
- Supports queries: "callers of X", "callees of X", "entry points"

**Change 3.2: Create CPGBackend**
- File: `search/backends/cpg_backend.py`
- Wrap `CPGBuilder` from `modules/discover/code_property_graph.py`
- Implements `search(query, limit)` interface
- Supports queries: "data flow for X", "control flow to X"

**Change 3.3: Create HDMABackend**
- File: `search/backends/hdma_backend.py`
- Wrap `HDMAAnalyzer` from `knowledge/analysis/hdma/analyzer.py`
- Implements `search(query, limit)` interface
- Supports queries: "architectural issues", "anti-patterns"

**Change 3.4: Create DependencyBackend (NEW)**
- File: `search/backends/dependency_backend.py`
- Wrap `DependencyGraph` from `quality/core/dependency_graph.py`
- Implements `search(query, limit)` interface
- Supports queries: "depends on X", "dependents of X", "circular deps"

### Phase 4: Router Integration

**Change 4.1: Add New Backends to Router**
- Import new backends with availability checks
- Add to `_get_backend_map()`
- Add result normalization in `_search_single()`

**Change 4.2: Add Backend Selection Logic**
- Map query patterns to appropriate backends
- Example: "callers of" → CALL_GRAPH, "symbol" → LSP, "depends on" → DEPENDENCY

**Change 4.3: Vector Backend Integration**
- Integrate HNSW backend for semantic vector search
- Add FAISS fallback when HNSW unavailable
- Support hybrid keyword+vector queries

### Phase 5: Advanced Features (NEW)

**Change 5.1: Integrate Query Intent Classifier**
- File: `search/unified_router.py`
- Import `QueryIntentDetector` from `search.query_intent`
- Use `get_preferred_backends()` for intelligent backend selection
- Map intents to backend priority order

**Change 5.2: Integrate MMR Diversity Ranking**
- File: `search/unified_router.py`
- Import `mmr_rerank` from `search.diversity`
- Add to reranking pipeline after cross-encoder
- Make lambda_param configurable

**Change 5.3: Integrate Confidence Calibration**
- File: `search/unified_router.py`
- Import `SourceTrustScorer`, `ConfidenceCalibrator`
- Apply to final results before returning
- Store trust scores for learning

**Change 5.4: Integrate Faceted Filtering**
- File: `search/unified_router.py`
- Import `filter_results`, `get_facets` from `search.faceted`
- Add optional filter parameters to search()
- Return facet counts with results

---

## 6. Implementation Plan

### Task Breakdown (Updated with New Discoveries)

| ID | Phase | Task | File | Effort | Dependencies |
|----|-------|------|------|--------|--------------|
| **Phase 0: Cleanup** | | | | | |
| T-000 | 0 | Remove duplicate/dead code files | Multiple (DELETE) | S | None |
| T-000-1 | 0 | Fix missing cc_integration_lsp | `cli/nip/lsp_query.py` | M | None |
| **Phase 1: Quick Wins** | | | | | |
| T-001 | 1 | Enable Cross-Encoder by default | `search/unified_router.py` | S | None |
| T-002 | 1 | Enable MultiLang by default | `search/unified_router.py` | S | None |
| T-003 | 1 | Add LSP backend import and integration | `search/unified_router.py` | M | None |
| T-004 | 1 | Add HNSW backend integration | `search/unified_router.py` | M | None |
| **Phase 2: Reranking** | | | | | |
| T-005 | 2 | Integrate CKS Reranking (RRF, temporal) | `search/reranking/cks_reranking_adapter.py` | M | None |
| T-006 | 2 | Extract Research temporal boosting | `search/reranking/temporal_boosting.py` | M | None |
| T-007 | 2 | Build unified reranking pipeline | `search/unified_router.py` | M | T-005, T-006 |
| **Phase 3: Graph Wrappers** | | | | | |
| T-008 | 3 | Create CallGraphBackend wrapper | `search/backends/call_graph_backend.py` | M | None |
| T-009 | 3 | Create CPGBackend wrapper | `search/backends/cpg_backend.py` | M | None |
| T-010 | 3 | Create HDMABackend wrapper | `search/backends/hdma_backend.py` | L | None |
| T-011 | 3 | Create DependencyBackend wrapper | `search/backends/dependency_backend.py` | M | None |
| **Phase 4: Integration** | | | | | |
| T-012 | 4 | Integrate all graph backends into router | `search/unified_router.py` | M | T-008-T-011 |
| T-013 | 4 | Add intelligent backend selection logic | `search/unified_router.py` | M | T-012 |
| T-014 | 4 | Integrate HNSW/FAISS vector search | `search/unified_router.py` | M | T-004 |
| **Phase 5: Advanced Features** | | | | | |
| T-015 | 5 | Integrate QueryIntentDetector | `search/unified_router.py` | M | T-013 |
| T-016 | 5 | Integrate MMR diversity ranking | `search/unified_router.py` | M | T-007 |
| T-017 | 5 | Integrate confidence calibration | `search/unified_router.py` | M | None |
| T-018 | 5 | Integrate faceted filtering | `search/unified_router.py` | M | None |
| **Testing** | | | | | |
| T-019 | TEST | Write tests for LSP backend | `tests/lib/search/test_lsp_backend.py` | M | T-003 |
| T-020 | TEST | Write tests for HNSW backend | `tests/lib/search/test_hnsw_backend.py` | M | T-004 |
| T-021 | TEST | Write tests for CallGraph backend | `tests/lib/search/test_call_graph_backend.py` | M | T-008 |
| T-022 | TEST | Write tests for CPG backend | `tests/lib/search/test_cpg_backend.py` | M | T-009 |
| T-023 | TEST | Write tests for Dependency backend | `tests/lib/search/test_dependency_backend.py` | M | T-011 |
| T-024 | TEST | Write tests for QueryIntentDetector | `tests/lib/search/test_query_intent.py` | M | T-015 |
| T-025 | TEST | Integration test for all backends | `tests/lib/search/test_unified_router_integrated.py` | L | T-001-T-018 |

### Rollback Strategy

Each phase can be independently reverted:
- **Phase 0 (Cleanup)**: Restore deleted files from git
- **Phase 1 (Quick Wins)**: Revert `unified_router.py` changes (4 commits)
- **Phase 2 (Reranking)**: Delete new adapter files, revert router changes (3 commits)
- **Phase 3 (Graph Wrappers)**: Delete new backend wrapper files (4 files)
- **Phase 4 (Integration)**: Revert router integration (3 commits)

Git branches will be used for each phase to enable atomic rollbacks.

---

## 7. Risks, Success Criteria, Dependencies

### Risks

| Risk | Impact | Mitigation |
|------|--------|------------|
| LSP server startup delay | Medium | Async initialization, timeout handling |
| Tree-sitter memory exhaustion | Medium | Keep AST fallback, exclude large patterns |
| Graph backends slow on large codebases | High | Lazy indexing, query timeout guards |
| Cross-Encoder model download | Low | Lazy loading, cached after first use |
| Breaking existing search behavior | Medium | Feature flags for gradual rollout |
| **HNSW memory usage** (NEW) | Medium | Dimension limit checks, FAISS fallback |
| **Duplicate reranking slowing queries** (NEW) | Low | Configurable pipeline, skip flags |
| **Dependency graph circularity** (NEW) | Medium | Cycle detection, depth limits |

### Success Criteria

1. **Functionality**: All new backends return valid `SearchResult` format
2. **Performance**: Backend timeout of 0.45s not exceeded for typical queries
3. **Compatibility**: Existing backends continue to work unchanged
4. **Test Coverage**: >80% coverage for new backends
5. **User Experience**: Query latency not increased by >20%

### Dependencies

| Dependency | Type | Status | Notes |
|------------|------|--------|-------|
| **External** | | | |
| `tree-sitter` Python bindings | External | Optional | AST fallback available |
| `sentence_transformers` | External | Required | For Cross-Encoder reranking |
| `hnswlib` | External | Optional | For HNSW backend (FAISS fallback) |
| `networkx` | External | Required | For graph backends |
| `faiss-cpu` | External | Optional | Fallback for HNSW |
| **Internal** | | | |
| `modules/discover/static_call_graph.py` | Internal | ✅ Exists | |
| `modules/discover/code_property_graph.py` | Internal | ✅ Exists | |
| `knowledge/analysis/hdma/analyzer.py` | Internal | ✅ Exists | |
| `code_intelligence/lsp/client.py` | Internal | ✅ Exists | |
| `search/backends/hnsw_backend.py` | Internal | ✅ Exists | Ready to integrate |
| `search/hnsw_index.py` | Internal | ✅ Exists | HNSW implementation |
| `cks/reranking.py` | Internal | ✅ Exists | Needs adapter |
| `quality/core/dependency_graph.py` | Internal | ✅ Exists | Needs wrapper |
| **Missing** | | | |
| `cc_integration_lsp` | Internal | ❌ Missing | Referenced by `lsp_query.py` |

---

## Next Actions

1. **Execute T-000**: Phase 0 - Remove duplicate/dead code files
2. **Execute T-001**: Enable Cross-Encoder by default
3. **Execute T-002**: Enable MultiLang by default
4. **Execute T-003**: Add LSP backend integration
5. **Execute T-004**: Add HNSW backend integration
6. **Verify Phase 1**: Run existing tests to ensure no regression
7. **Plan Phase 2**: Create detailed specs for reranking adapters
8. **Plan Phase 3**: Create detailed specs for graph backend wrappers

---

**Top Risks:**
- Graph backends may exceed 0.45s timeout on large codebases
- LSP availability varies by language/project
- Tree-sitter memory usage on very large codebases
- **HNSW memory usage** (NEW) - requires dimension checks and FAISS fallback
- **Dependency graph circularity** (NEW) - may need cycle detection

**Next Actions:**
1. Review and approve this updated plan
2. Start with Phase 0 (Cleanup) - remove dead/duplicate code
3. Continue with Phase 1 (Quick Wins) - enable gated features
4. Create feature branch: `feature/search-integration-phase0`

---

**Summary of New Discoveries:**

This plan now covers **26 integration tasks** (up from 21) across 5 phases:

- **Phase 0 (Cleanup)**: 2 tasks - remove dead code, fix missing module
- **Phase 1 (Quick Wins)**: 4 tasks - enable Cross-Encoder, MultiLang, LSP, HNSW
- **Phase 2 (Reranking)**: 3 tasks - CKS reranking, temporal boosting, unified pipeline
- **Phase 3 (Graph Wrappers)**: 4 tasks - CallGraph, CPG, HDMA, Dependency backends
- **Phase 4 (Integration)**: 3 tasks - router integration, backend selection, vector search
- **Phase 5 (Advanced Features)**: 4 tasks - Query Intent, MMR, Confidence Calibration, Faceted Filtering
- **Testing**: 7 tasks - comprehensive test coverage

**Key New Tools Discovered:**
- **Query Intent Classifier** (`search/query_intent.py`) - Complete intent classification with semantic embeddings
- **HNSW Index** (`search/hnsw_index.py`) - Full HNSW implementation (NOT a stub!)
- **FAISS Lock Wrapper** (`search/faiss_lock.py`) - Retry logic with exponential backoff
- **MMR Diversity** (`search/diversity.py`) - Maximal Marginal Relevance ranking
- **Hybrid Scorer** (`search/backends/hybrid_scorer.py`) - BM25 + cosine combination
- **Confidence Calibration** (`search/confidence_calibration.py`) - Source trust scoring
- **Faceted Search** (`search/faceted.py`) - Multi-dimensional filtering
- **Dependency Graph** (`quality/core/dependency_graph.py`) - Full program dependency graph with Symbol/EdgeKind enums
