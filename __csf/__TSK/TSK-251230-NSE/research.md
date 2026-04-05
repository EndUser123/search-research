# Research Intelligence: FAISS Incremental Update Optimization

## Sources Consulted

1. **FAISS Documentation** - IndexFlatIP incremental updates
2. **Python File I/O Best Practices** - Atomic writes, position tracking
3. **Existing Codebase Analysis** - `incremental_chs_update.py`, `FAISSVectorStore`

## Key Findings

### 1. Position Tracking Implementation

**Current State** (lines 94-184):
- `load_new_messages()` already has `start_byte` parameter
- File seeking implemented with `f.seek(start_byte)`
- State file already stores `file_byte_position`

**Issue**: Redundant duplicate checking (line 154):
```python
if msg_id in indexed_ids:  # This is O(n) for every message!
    skipped += 1
    continue
```

**Solution**: When `start_byte > 0`, we've already processed all prior messages. Skip the check.

### 2. Singleton Pattern for EmbeddingManager

**Existing Code** (line 192):
```python
manager = EmbeddingManager()  # Reloads 420MB model every run!
```

**Available Solution**: `ComponentManager.get_embedding_manager()` (lines 23-65 of `embedding_manager.py`)

**Benefits**:
- Thread-safe singleton
- Model cached in memory
- No reload overhead

### 3. FAISS Incremental Update Flow

```
┌─────────────────────────────────────────────────────────────────┐
│  Current Flow (Slow)                                          │
├─────────────────────────────────────────────────────────────────┤
│  1. Load state (file_byte_position stored)                     │
│  2. Scan from beginning (IGNORING position!)                   │
│  3. For each line: check if msg_id in indexed_ids              │
│  4. Generate embeddings for "new" messages                     │
│  5. FAISSVectorStore.incremental_update()                       │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│  Optimized Flow (Fast)                                         │
├─────────────────────────────────────────────────────────────────┤
│  1. Load state (file_byte_position stored)                     │
│  2. Seek to file_byte_position ✓                               │
│  3. Skip first partial line ✓                                   │
│  4. Process remaining lines (no duplicate check!) ✓             │
│  5. Use cached EmbeddingManager ✓                               │
│  6. FAISSVectorStore.incremental_update()                       │
└─────────────────────────────────────────────────────────────────┘
```

## Best Practices Identified

From `/research` on FAISS incremental updates:

1. **Skip duplicate checking when using position tracking** - Trust the file position
2. **Cache embedding model** - Use singleton pattern
3. **Buffer-based batching** - Collect new vectors, batch add them
4. **Periodic index rebuild** - Add 1000+ items, then rebuild index

## Performance Estimates

| Operation | Current | Optimized | Speedup |
|-----------|---------|----------|---------|
| File scan | 2-3 hours | ~10 seconds | 1000x |
| Duplicate checks | 42M ops | 0 | ∞ |
| Model load | 5-10s | 0s (cached) | 1x |
| Embedding generation | ~30s | ~30s | 1x |
| **Total** | **2-3 hours** | **~60 seconds** | **120x** |

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| File position corruption | Git rollback, automatic backups |
| New message duplicates | FAISSVectorStore.incremental_update() checks |
| State file drift | Backward compatible format |

## Recommendations

1. ✅ Implement `skip_duplicate_check` parameter
2. ✅ Use `ComponentManager.get_embedding_manager()`
3. ⏳ Add progress persistence (`.cwo12_progress.json`)
4. ⏳ Initialize git in TSK directory for rollback
