# Specification: Incremental FAISS Updates

## Project Overview

**Project ID:** TSK-251225-0043-FAISS-Incr
**Title:** Incremental FAISS Updates for CHS
**Created:** 2025-12-25 00:43
**Status:** Draft

## Problem Statement

### Current Situation

The Chat History Search (CHS) system uses a full FAISS index rebuild strategy:
- **Full sync time:** 73 seconds for 20,754 messages
- **Current workflow:**
  1. Auto-sync: Updates database only (0.3s)
  2. Full sync: Rebuilds entire FAISS index (73s)

### Problem

**Full FAISS rebuild is expensive:**
- Takes 73+ seconds for 20k messages
- Scales linearly with message count (will get worse)
- Blocks user from searching during rebuild
- Wastes computational resources re-encoding unchanged messages

### User Impact

**Current recommendation:**
- "Run full sync 1-2x per day"
- "Before important searches"

**Pain points:**
- New messages not searchable via semantic search until full sync
- Users must remember to run full sync manually
- 73-second wait time is disruptive during active work

## Solution Requirements

### Functional Requirements

**FR1: Incremental FAISS Updates**
- System MUST support adding new vectors to existing FAISS index
- Updates MUST complete in <5 seconds for up to 100 new messages
- Updates MUST NOT require full index rebuild

**FR2: Automatic Detection**
- System MUST automatically detect new messages in database
- Auto-sync trigger MUST also update FAISS incrementally
- Detection and update MUST complete transparently during search

**FR3: Index Integrity**
- Incremental updates MUST maintain index consistency
- Vector embeddings MUST use same model and normalization as full build
- Message metadata MUST stay synchronized with vector IDs

**FR4: Backward Compatibility**
- MUST support existing full rebuild as fallback
- MUST work with current FAISSHybridSearcher implementation
- MUST not break existing CHS search functionality

### Non-Functional Requirements

**NFR1: Performance**
- Incremental update: <5 seconds for 100 messages
- Update time: O(n) where n = new messages (not total messages)
- Search performance: No degradation after incremental updates

**NFR2: Reliability**
- Update failure MUST not corrupt existing index
- MUST support rollback to previous index if update fails
- MUST handle concurrent access (search during update)

**NFR3: Maintainability**
- Clear separation between incremental and full rebuild paths
- Comprehensive logging for debugging
- Metrics for tracking update performance

**NFR4: Data Integrity**
- Message deduplication (same message not added twice)
- Metadata synchronization (all vectors have valid message data)
- Index version tracking

## Technical Context

### Current Architecture

**FAISS Index Structure:**
```
chat_history_faiss_with_text/
├── faiss_index.bin          # FAISS IndexFlatIP (768 dimensions)
├── metadata.pkl             # Message metadata with full text
└── vector_dim: 768
    total_vectors: 20,754
```

**FAISS Configuration:**
- Index type: `IndexFlatIP` (inner product for cosine similarity)
- Embedding model: `all-mpnet-base-v2` (768 dimensions)
- Normalization: L2-normalized vectors for cosine similarity
- Metadata: Pickle file with message IDs and full text content

**Current Build Process:**
1. Load all 20,754 messages from SQLite database
2. Generate embeddings for all messages (batch processing)
3. L2-normalize all embeddings
4. Create new IndexFlatIP from scratch
5. Add all vectors to index
6. Save index + metadata to disk

### Why IndexFlatIP Matters

**IndexFlatIP characteristics:**
- Exact search (no approximation)
- Supports `add()` method for incremental updates
- No training required
- Memory-bound (all vectors in RAM)

**Implication for incremental updates:**
- CAN add vectors incrementally via `index.add(new_vectors)`
- No retraining needed
- Simple implementation

## Success Criteria

### Primary Success Metrics

1. **Performance**
   - ✅ 100 new messages added in <5 seconds
   - ✅ Search time unchanged (<100ms per query)

2. **Functionality**
   - ✅ New messages searchable via semantic search after update
   - ✅ No index corruption after 100+ incremental updates
   - ✅ Backward compatibility with existing full rebuild

3. **User Experience**
   - ✅ Transparent updates (no manual intervention)
   - ✅ Auto-sync now updates both database AND FAISS
   - ✅ No more "run full sync 1-2x per day" requirement

### Acceptance Tests

**Test 1: Basic Incremental Update**
```python
# Add 50 new messages
incremental_update(new_messages)
assert index.ntotal == 20804  # 20754 + 50
assert search("new message") returns results from new messages
```

**Test 2: No Performance Regression**
```python
# Measure search time before and after
time_before = measure_search_time(query)
incremental_update(new_messages)
time_after = measure_search_time(query)
assert time_after <= time_before * 1.1  # <10% slowdown
```

**Test 3: Index Integrity**
```python
# Verify all vectors have valid metadata
for vector_id in range(index.ntotal):
    assert metadata['messages'][vector_id] exists
    assert metadata['messages'][vector_id]['content'] not empty
```

## Assumptions & Constraints

### Assumptions

1. FAISS IndexFlatIP supports incremental `add()` operations
2. Embedding model produces consistent results over time
3. Message IDs are unique and stable
4. Disk space available for index backups

### Constraints

1. MUST use existing FAISS library (no migration to alternatives)
2. MUST maintain current metadata structure (pickle file with messages)
3. MUST work within current CHS architecture (FAISSHybridSearcher)
4. SHOULD minimize code changes to existing search logic

## Out of Scope

**Not in this release:**
- Alternative index structures (IndexIVF, HNSW)
- Distributed FAISS indexing
- Real-time streaming updates
- Automatic index compaction/optimization
- Alternative vector databases (Weaviate, Pinecone, etc.)

## Dependencies

### Internal Dependencies

- `src/lib/core_utils/faiss_vector_store.py` - FAISS wrapper
- `src/lib/core_utils/embedding_manager.py` - Embedding generation
- `src/modules/analysis/chat_search/src/faiss_hybrid_searcher.py` - Search interface
- `scripts/rebuild_faiss_with_text.py` - Full rebuild reference

### External Dependencies

- `faiss` - Vector similarity search library
- `sentence_transformers` - Embedding model (all-mpnet-base-v2)
- `numpy` - Vector operations
- `pickle` - Metadata serialization

## Risks & Mitigations

### Risk 1: FAISS Index Corruption

**Risk:** Incremental update corrupts index, breaking all searches

**Mitigation:**
- Backup existing index before update
- Validate index structure after update
- Fallback to previous index if validation fails

### Risk 2: Embedding Inconsistency

**Risk:** Embeddings generated at different times produce different vectors

**Mitigation:**
- Use same embedding model instance
- Verify L2 normalization applied consistently
- Add regression tests for embedding consistency

### Risk 3: Metadata Desynchronization

**Risk:** Vector IDs and metadata arrays get out of sync

**Mitigation:**
- Atomic update operation (both index and metadata together)
- Validation checks after update
- Version tracking in metadata

### Risk 4: Performance Degradation

**Risk:** Incremental updates slow down search over time

**Mitigation:**
- Benchmark search performance after each update
- Monitor index size and structure
- Document when full rebuild is recommended (e.g., after 1000 updates)

## Next Steps

**Immediate next steps:**
1. Research FAISS IndexFlatIP incremental `add()` behavior
2. Design incremental update API
3. Implement proof-of-concept for 100-message update
4. Integrate with existing auto-sync trigger

**Success definition:**
A developer can run `chs search "new conversation"` immediately after having a conversation, and it will find the new messages via semantic search without running a manual full sync.
