# Implementation Plan: Search System Optimizations - Phase 2

## Discovery Summary

After reading existing code, I found:

### Already Implemented (from previous commit 811fc21df):
1. **CKS Query Cache** - LRU cache with TTL in `unified.py`
2. **CKS Batch Ingest** - `ingest_memories_batch()` and `ingest_patterns_batch()`
3. **CHS Streaming Embeddings** - `stream=True` parameter in `incremental_chs_update.py`
4. **CHS Async Incremental Update** - `incremental_update_async()` with background updates

### Already Implemented (Phase 1/2 features, possibly from earlier):
1. **Hybrid Search** - `hybrid_search_patch.py` with RRF fusion
2. **MMR Diversification** - `maximal_marginal_relevance()` in `reranking.py`
3. **Query Expansion** - Integrated in `search_semantic()` with `expand_query` parameter
4. **Parallel Backend Search** - `UnifiedSearchRouter` uses `ThreadPoolExecutor`

### What Needs to be Done:

Based on analysis, the optimizations 1-4 are already implemented in the codebase! The main missing piece is:

**Optimization 5: HNSW Approximate Index for CHS**
- Current CHS uses FAISS `IndexFlatIP` (exact search, O(N))
- Need to add `IndexHNSWFlat` (approximate search, O(log N))
- This provides 10-100x speedup at scale with minimal accuracy loss

### Revised Plan:

Since most features exist, the task becomes:
1. Add HNSW index support to CHS (new feature)
2. Add tests for existing features (RRF, MMR, parallel search, query expansion)
3. Document and verify all features work together

## Implementation Tasks (TDD)

### Task 1: HNSW Index for CHS
- **File**: `src/modules/analysis/chat_search/incremental_chs_update.py`
- **Changes**:
  - Add `use_hnsw: bool = False` parameter to `generate_embeddings()`
  - Add `create_hnsw_index()` function
  - Add `build_or_load_index()` function that chooses IndexFlatIP or IndexHNSWFlat
- **Test**: `tests/chat_search/test_chs_hnsw_index.py`

### Task 2: Tests for Hybrid Search RRF
- **File**: `tests/cks/test_cks_hybrid_search.py`
- **Tests**:
  - `test_hybrid_search_exists()` - Verify `search_hybrid()` method
  - `test_rrf_fusion_basic()` - Verify RRF combines results
  - `test_hybrid_search_weights()` - Verify fts_weight and semantic_weight

### Task 3: Tests for MMR Diversification
- **File**: `tests/cks/test_cks_mmr_diversification.py`
- **Tests**:
  - `test_mmr_function_exists()` - Verify MMR function exists
  - `test_mmr_reduces_duplicates()` - Verify MMR reduces similar results
  - `test_mmr_lambda_parameter()` - Verify diversity control

### Task 4: Tests for Parallel Backend Search
- **File**: `tests/lib/search/test_parallel_backend_search.py`
- **Tests**:
  - `test_parallel_search_router_exists()` - Verify UnifiedSearchRouter
  - `test_parallel_execution()` - Verify backends queried concurrently
  - `test_backend_failure_handling()` - Verify graceful degradation

### Task 5: Tests for Query Expansion
- **File**: `tests/cks/test_cks_query_expansion.py`
- **Tests**:
  - `test_query_expansion_parameter()` - Verify expand_query works
  - `test_abbreviation_expansion()` - Verify abbreviations are expanded
  - `test_expansion_boosts_recall()` - Verify more results with expansion

## Ralph Loop Configuration

**Enabled**: Yes - Implementation task requires iterative refinement
**Max Iterations**: 30
**Completion Promise**: All 5 optimizations have tests passing with >90% coverage
