# Requirements Analysis: FAISS Incremental Update Optimization

## Functional Requirements

### FR-1: Position Tracking
The system MUST track and resume from the last byte position in `history.jsonl`.

**Acceptance Criteria**:
- State file stores `file_byte_position`
- On restart, file seek to saved position
- Skip first partial line after seek
- Handle file rotation (start from 0 if file shrinks)

### FR-2: Eliminate Redundant Duplicate Checking
When resuming from file position, skip `msg_id in indexed_ids` check.

**Acceptance Criteria**:
- Add `skip_duplicate_check` parameter to `load_new_messages()`
- When `start_byte > 0`, duplicate check is skipped
- FAISSVectorStore.incremental_update() still deduplicates new messages

### FR-3: Singleton EmbeddingManager
Use ComponentManager singleton to cache model between runs.

**Acceptance Criteria**:
- Replace `EmbeddingManager()` with `ComponentManager.get_embedding_manager()`
- Model cached in memory
- Second run is faster (no model load overhead)

### FR-4: Performance Targets
Incremental update MUST complete in under 60 seconds for ~100 new messages.

**Acceptance Criteria**:
- Wall clock time <60s
- Only new messages processed
- GPU utilized efficiently (RTX 5070)

## Non-Functional Requirements

### NFR-1: Backward Compatibility
- Existing state files must be readable
- Existing FAISS index must remain valid
- No breaking changes to API

### NFR-2: Reliability
- Automatic backups before update
- Rollback on failure
- Git-based recovery option

### NFR-3: Observability
- Progress logging during scan
- Performance metrics on completion
- Clear error messages

## Technical Requirements

### TR-1: Files to Modify
| File | Lines | Changes |
|------|-------|---------|
| `incremental_chs_update.py` | 94-184 | Add skip_duplicate_check parameter |
| `incremental_chs_update.py` | 154-156 | Conditional duplicate check logic |
| `incremental_chs_update.py` | 294-300 | Pass skip_duplicate_check=True |
| `incremental_chs_update.py` | 192-194 | Use ComponentManager |
| `chat_history_search.py` | 1560-1752 | Update run_incremental_faiss_update() |

### TR-2: Dependencies
- `ComponentManager` from `lib.core_utils.embedding_manager`
- `FAISSVectorStore` (existing)
- `numpy` (existing)

## Risk Assessment

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| File position corruption | Low | High | Git rollback, backups |
| New message duplicates | Medium | Low | FAISSVectorStore deduplicates |
| Model cache growth | Low | Low | ComponentManager handles |
| State file format change | Low | Medium | Backward compatible |

## Definition of Done

- [x] Requirements documented
- [ ] Code changes implemented
- [ ] Performance verified (<60s for 100 messages)
- [ ] No duplicates in index
- [ ] Tests pass
- [ ] Documentation updated
