# Requirements Analysis: Incremental FAISS Updates

## Functional Requirements Breakdown

### FR1: Incremental FAISS Updates

**Requirement:** System MUST support adding new vectors to existing FAISS index

**Detailed Breakdown:**
1. **Input:** List of new message objects (with id, content, timestamp, metadata)
2. **Process:**
   - Generate embeddings for new messages only
   - L2-normalize embeddings (for cosine similarity)
   - Add vectors to existing FAISS index using `index.add()`
   - Update metadata pickle file with new message data
3. **Output:** Updated index file + metadata
4. **Constraints:**
   - Update time: O(n) where n = new messages
   - MUST NOT require re-encoding existing messages
   - MUST maintain index structure (IndexFlatIP, 768 dimensions)

**Acceptance Criteria:**
- Adding 100 messages takes <5 seconds
- Index total count increases by exact number of new messages
- Search returns results from newly added messages

### FR2: Automatic Detection

**Requirement:** System MUST automatically detect new messages and update FAISS

**Detailed Breakdown:**
1. **Detection:**
   - Query database for messages with ID > last indexed ID
   - OR: Check timestamp against last indexed timestamp
2. **Trigger:**
   - Current auto-sync trigger (on every `chs search`)
   - Update chs_sync.py to support incremental mode
3. **Flow:**
   ```
   User runs: chs search "query"
     ↓
   auto_sync_if_needed() called
     ↓
   Check for new messages in database
     ├─ No new messages → Search existing index
     └─ New messages found →
       ├─ Generate embeddings for new messages
       ├─ Add vectors to FAISS index
       ├─ Update metadata
       ├─ Save updated index
       └─ Search (now includes new messages)
   ```

**Acceptance Criteria:**
- Auto-sync updates both database AND FAISS
- No manual intervention required
- Search includes latest messages automatically

### FR3: Index Integrity

**Requirement:** Incremental updates MUST maintain index consistency

**Detailed Breakdown:**
1. **Vector-Metadata Alignment:**
   - Vector position in FAISS index MUST match position in metadata['messages'] array
   - Message ID in metadata MUST be unique
   - No gaps in sequence (contiguous array)

2. **Deduplication:**
   - Check if message ID already exists in index before adding
   - Skip duplicate messages with warning
   - Log duplicate detection

3. **Validation:**
   - After update, verify `index.ntotal == len(metadata['messages'])`
   - Verify all message IDs are unique
   - Verify all message content is non-empty

**Acceptance Criteria:**
- No duplicate message IDs in index
- Vector count matches metadata message count
- All searches return valid message data

### FR4: Backward Compatibility

**Requirement:** MUST support existing full rebuild as fallback

**Detailed Breakdown:**
1. **Fallback Triggers:**
   - User explicitly requests `--full` flag
   - Incremental update fails
   - Index corruption detected
   - After N incremental updates (configurable threshold)

2. **Interface:**
   - `chs_sync.py --incremental` (new flag)
   - `chs_sync.py --full` (existing behavior)
   - `chs_sync.py --auto` (smart choice based on new message count)

3. **Migration Path:**
   - Existing indexes work without modification
   - Incremental updates add version field to metadata
   - Version tracking for future compatibility

**Acceptance Criteria:**
- Full rebuild still works with existing script
- Can switch between incremental and full rebuild
- No breaking changes to existing code

## Non-Functional Requirements Analysis

### NFR1: Performance

**Target Metrics:**

| Operation | Target | Current (Full Rebuild) |
|-----------|--------|----------------------|
| Add 10 messages | <1s | 73s |
| Add 100 messages | <5s | 73s |
| Add 1000 messages | <30s | 73s (would scale to ~350s) |
| Search query | <100ms | <100ms (unchanged) |

**Performance Profile:**
- **Embedding generation:** ~100ms per message (GPU) or ~500ms per message (CPU)
- **FAISS add operation:** ~1ms per vector
- **Metadata update:** ~100ms (pickle serialization)
- **File I/O:** ~500ms (write index + metadata)

**Bottleneck:** Embedding generation dominates

**Optimization Strategies:**
1. Batch embedding generation (already done)
2. GPU acceleration (already implemented)
3. Parallel processing for >100 messages

### NFR2: Reliability

**Failure Scenarios:**

1. **Update Failure Mid-Operation:**
   - **Risk:** Index partially updated, metadata out of sync
   - **Mitigation:** Update in temporary directory, atomic rename
   - **Rollback:** Keep previous index until new index validated

2. **Index Corruption:**
   - **Risk:** FAISS index file corrupted during write
   - **Mitigation:** Backup before update
   - **Detection:** Verify index can be loaded after update

3. **Concurrent Access:**
   - **Risk:** Search during update causes stale results or crash
   - **Mitigation:** File lock during update OR copy-on-write
   - **Detection:** Check if index file locked before search

**Reliability Requirements:**
- 99.9% success rate for incremental updates
- Automatic rollback on failure
- No data loss (all messages recoverable)

### NFR3: Maintainability

**Code Organization:**

```
src/lib/core_utils/
├── faiss_vector_store.py          # ADD: incremental_update() method
├── embedding_manager.py           # NO CHANGE: already supports batch

src/modules/analysis/chat_search/
├── chs_sync.py                     # MODIFY: add --incremental flag
├── src/faiss_hybrid_searcher.py   # NO CHANGE: uses FAISSVectorStore

scripts/
├── rebuild_faiss_with_text.py     # NO CHANGE: full rebuild fallback
└── incremental_faiss_update.py    # NEW: standalone incremental script
```

**Logging Requirements:**
```python
logger.info(f"Incremental FAISS update: {new_count} messages")
logger.debug(f"Embedding generation: {embed_time:.2f}s")
logger.debug(f"FAISS add: {add_time:.2f}s")
logger.debug(f"Metadata update: {meta_time:.2f}s")
logger.info(f"Total update time: {total_time:.2f}s")
logger.info(f"Index size: {index.ntotal} vectors")
```

**Metrics to Track:**
- Update frequency (how often incremental updates run)
- Update size (number of messages per update)
- Update duration (performance over time)
- Failure rate (rollback events)

### NFR4: Data Integrity

**Data Validation:**

1. **Pre-Update Checks:**
   - Verify input messages have required fields (id, content)
   - Check for duplicate message IDs
   - Verify embedding model compatibility

2. **Post-Update Checks:**
   - Verify index loadable
   - Verify vector count matches metadata count
   - Verify message IDs are unique
   - Spot-check: search for a newly added message

3. **Recovery:**
   - Backup created before every update
   - Backup naming: `faiss_index_backup_{timestamp}.bin`
   - Automatic cleanup of old backups (keep last 5)

**Integrity Rules:**
```
IF index.ntotal != len(metadata['messages']):
    RAISE IntegrityError

IF any(msg_id in metadata['messages'] is None):
    RAISE IntegrityError

IF any(len(msg['content']) == 0 for msg in metadata['messages']):
    RAISE IntegrityError
```

## User Stories

### Story 1: Seamless Semantic Search

**As a** developer using CHS
**I want** my new conversations to be searchable via semantic search immediately
**So that** I can find recent conversations without manual full sync

**Acceptance:**
- New messages appear in semantic search within 5 seconds of conversation
- No manual intervention required
- Search quality unchanged (new messages ranked appropriately)

### Story 2: Fast Updates

**As a** developer using CHS
**I want** FAISS updates to complete quickly
**So that** my workflow is not interrupted

**Acceptance:**
- Updates complete in <5 seconds for typical usage (≤100 messages)
- No noticeable delay before search results
- Can search while update is happening (or wait is minimal)

### Story 3: Reliable Updates

**As a** developer using CHS
**I want** updates to never corrupt my index
**So that** I can trust the search functionality

**Acceptance:**
- Failed updates automatically rollback
- No manual recovery needed
- Clear logging of what happened

### Story 4: Optional Full Rebuild

**As a** developer using CHS
**I want** to run full rebuild if needed
**So that** I can optimize or recover from issues

**Acceptance:**
- `chs_sync.py --full` still works
- Can rebuild from scratch anytime
- No data loss

## Technical Requirements

### TR1: FAISS API Usage

**Required FAISS Operations:**

```python
# Load existing index
index = faiss.read_index("faiss_index.bin")

# Add new vectors
index.add(new_embeddings)  # new_embeddings: numpy array (n, 768)

# Verify addition
assert index.ntotal == previous_total + n

# Save updated index
faiss.write_index(index, "faiss_index.bin")
```

**Constraints:**
- MUST use same index type (IndexFlatIP)
- MUST maintain same dimensionality (768)
- MUST preserve existing vectors

### TR2: Embedding Generation

**Required Operations:**

```python
# Generate embeddings for new messages
new_texts = [msg['content'] for msg in new_messages]
new_embeddings = embedding_manager.encode(new_texts, show_progress=False)

# L2-normalize for cosine similarity
norms = np.linalg.norm(new_embeddings, axis=1, keepdims=True)
new_embeddings = new_embeddings / norms

# Convert to float32
new_embeddings = new_embeddings.astype(np.float32)
```

**Constraints:**
- MUST use same embedding model (all-mpnet-base-v2)
- MUST apply L2-normalization
- MUST output float32 dtype

### TR3: Metadata Management

**Required Operations:**

```python
# Load metadata
with open("metadata.pkl", "rb") as f:
    metadata = pickle.load(f)

# Append new messages
for msg in new_messages:
    metadata['messages'].append({
        'id': msg['id'],
        'session_id': msg['session_id'],
        'role': msg['role'],
        'content': msg['content'],
        'timestamp': msg['timestamp'],
        'token_count': msg['token_count'],
        'metadata': msg.get('metadata', {})
    })

# Update total count
metadata['total_vectors'] = index.ntotal

# Save metadata
with open("metadata.pkl", "wb") as f:
    pickle.dump(metadata, f)
```

**Constraints:**
- MUST maintain array structure
- MUST update total_vectors count
- MUST preserve existing message data

### TR4: Atomic Update

**Required Operations:**

```python
# Create temporary directory
temp_dir = Path("faiss_update_temp")
temp_dir.mkdir(exist_ok=True)

# Build updated index in temp
temp_index_path = temp_dir / "faiss_index.bin"
temp_metadata_path = temp_dir / "metadata.pkl"

# Write updates to temp
faiss.write_index(updated_index, str(temp_index_path))
with open(temp_metadata_path, "wb") as f:
    pickle.dump(updated_metadata, f)

# Validate temp files
validated_index = faiss.read_index(str(temp_index_path))
assert validated_index.ntotal == expected_count

# Atomic rename (replaces existing files)
shutil.move(str(temp_index_path), "faiss_index.bin")
shutil.move(str(temp_metadata_path), "metadata.pkl")

# Cleanup temp dir
shutil.rmtree(temp_dir)
```

**Constraints:**
- MUST validate before replacing existing files
- MUST use atomic rename operation
- MUST cleanup temporary files

## Priority Matrix

| Requirement | Priority | Complexity | Risk |
|-------------|----------|------------|------|
| FR1: Incremental Updates | P0 (Critical) | Medium | Low |
| FR2: Automatic Detection | P0 (Critical) | Low | Low |
| FR3: Index Integrity | P0 (Critical) | Medium | Medium |
| FR4: Backward Compatibility | P1 (High) | Low | Low |
| NFR1: Performance | P0 (Critical) | Medium | Medium |
| NFR2: Reliability | P0 (Critical) | High | High |
| NFR3: Maintainability | P1 (High) | Low | Low |
| NFR4: Data Integrity | P0 (Critical) | Medium | Medium |

**Implementation Order:**
1. FR1 + NFR4: Core incremental update with validation
2. FR3: Integrity checks and rollback
3. NFR2: Reliability features (backup, atomic update)
4. FR2: Integration with auto-sync
5. FR4: Backward compatibility verification

## Dependencies

### External Dependencies

- `faiss>=1.7.0` - IndexFlatIP.add() method available
- `numpy>=1.20.0` - Vector operations
- `sentence-transformers>=2.0.0` - Embedding model

### Internal Dependencies

- `FAISSVectorStore` class - Add incremental_update() method
- `EmbeddingManager` class - Use existing encode() method
- `FAISSHybridSearcher` class - Reload index after update
- `chs_sync.py` - Add --incremental flag

## Success Metrics

### Quantitative Metrics

1. **Performance:**
   - ✅ Incremental update: <5s for 100 messages
   - ✅ Search time: ≤100ms (no degradation)
   - ✅ Embedding time: <3s for 100 messages (GPU)

2. **Reliability:**
   - ✅ Success rate: >99.5%
   - ✅ Corruption rate: 0%
   - ✅ Rollback success: 100%

3. **Functionality:**
   - ✅ All new messages searchable after update
   - ✅ No duplicate message IDs
   - ✅ Vector-metadata alignment: 100%

### Qualitative Metrics

1. **User Experience:**
   - ✅ No manual intervention required
   - ✅ Transparent updates (user unaware of update happening)
   - ✅ Confidence in system (no fear of corruption)

2. **Maintainability:**
   - ✅ Clear logging of update operations
   - ✅ Easy to debug issues
   - ✅ Well-documented code

## Open Questions

1. **Q:** Should we support incremental updates for other index types (IVF, HNSW)?
   **A:** No, out of scope. IndexFlatIP is current production index.

2. **Q:** How often should we recommend full rebuild?
   **A:** After ~1000 incremental updates OR if search degrades. Document in guide.

3. **Q:** Should we implement automatic periodic full rebuild?
   **A:** No, manual control only. Users decide when to rebuild.

4. **Q:** What happens if embedding model changes?
   **A:** Full rebuild required. Detect model version mismatch and warn.

5. **Q:** Should we support deletion of messages?
   **A:** No, FAISS IndexFlatIP doesn't support removal. Append-only.
