# TSK: Search System Optimizations - Phase 2

## Task: Implement 5 Search System Optimizations with Parallel Subagents

### Context
Previous optimizations (CDS cache, CKS cache, CHS streaming, CKS batch, CHS async) have been implemented and committed (811fc21df).

### Goal
Implement 5 additional optimizations for CKS/CHS/CDS and unified /search:

1. **Hybrid Search (semantic + keyword fusion)** - Combine semantic and keyword search using RRF
2. **Parallel Backend Search** - Make /search query all backends simultaneously (3-5x speedup)
3. **Result Diversification** - MMR algorithm to reduce duplicate/near-duplicate results
4. **Query Auto-Expansion** - Abbreviation mappings and synonym expansion
5. **HNSW Approximate Index** - 10-100x faster search in CHS at scale

### Files Read (RWV)
- `src/cks/unified.py` - Main CKS class with search_semantic, query cache, batch ingest
- `tests/cks/test_cks_query_cache.py` - CKS query cache tests
- `tests/cks/test_cks_batch_ingest.py` - CKS batch ingest tests
- `tests/chat_search/test_chs_streaming_embeddings.py` - CHS streaming tests
- `tests/chat_search/test_chs_async_incremental.py` - CHS async incremental tests

### Key Findings
- CKS already has Phase 1/2 features: query expansion, fusion methods (rrf/adaptive), MMR diversity
- The `search_semantic` method in `unified.py` already has fusion_method and diversity parameters
- There's a `reranking.py` module imported with RRF, MMR, adaptive fusion functions
- Query expansion exists in `query_expansion.py` module

### Status
Phase 0: Pre-Execution Checklist - In Progress
