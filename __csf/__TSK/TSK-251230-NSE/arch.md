# Architecture Analysis: FAISS Incremental Update Optimization

## System Overview

The CHS (Chat History Search) system uses FAISS for vector similarity search over chat messages. The incremental update feature allows adding new messages without rebuilding the entire index.

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      CHS Search Flow                             │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  ┌──────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ history.json │───▶│ incremental_chs_ │───▶│  FAISS       │  │
│  │    (424k     │    │    update.py     │    │  Index       │  │
│  │    lines)    │    │                  │    │  (97k vecs)  │  │
│  └──────────────┘    └──────────────────┘    └──────────────┘  │
│                             │                                   │
│                             ▼                                   │
│                    ┌──────────────────┐                        │
│                    │ EmbeddingManager │                        │
│                    │  (all-mpnet-     │                        │
│                    │   base-v2)       │                        │
│                    └──────────────────┘                        │
│                             │                                   │
│                             ▼                                   │
│                    ┌──────────────────┐                        │
│                    │ FAISSVectorStore │                        │
│                    │ .incremental_    │                        │
│                    │    update()      │                        │
│                    └──────────────────┘                        │
└─────────────────────────────────────────────────────────────────┘
```

## Performance Bottlenecks

### 1. Full File Scan (Primary Bottleneck)
**Location**: `incremental_chs_update.py:load_new_messages()`

```python
# Current: Scans all 424k lines every time
for line in f:  # O(n) where n=424,688
    msg_id = data.get("uuid") or data.get("leafUuid") or data.get("id")
    if msg_id in indexed_ids:  # O(m) where m=97k
        continue
```

**Impact**: 2-3+ hours to process 424k lines

### 2. Duplicate Checking (Secondary Bottleneck)
**Location**: `incremental_chs_update.py:154`

```python
if msg_id in indexed_ids:  # O(m) lookup in Python set
    skipped += 1
    continue
```

**Impact**: ~42 million set membership checks per run

### 3. Model Reloading
**Location**: `incremental_chs_update.py:192`

```python
manager = EmbeddingManager()  # Loads 420MB model every run
```

**Impact**: ~5-10 seconds startup time per run

## Optimization Strategy

### Position Tracking (Already Implemented)
```python
# State file tracks file byte position
state = {
    "file_byte_position": 123456789,  # Resume from here
    "last_indexed_count": 97830,
    "last_update": "2024-12-30T21:16:16"
}
```

### Redundant Duplicate Elimination
When using position tracking:
- All messages BEFORE position X are already indexed
- No need to check `msg_id in indexed_ids`
- Only check for duplicates within NEW messages

### Singleton Pattern
```python
# Use ComponentManager instead of direct instantiation
manager = ComponentManager.get_embedding_manager("all-mpnet-base-v2")
# Model cached in memory, no reload needed
```

## Target Performance

| Metric | Current | Target |
|--------|---------|--------|
| Time to scan | 2-3 hours | <10 seconds |
| Messages processed | 424,688 | ~100 new only |
| Duplicate checks | 42M | ~100 |
| Model reload time | 5-10s | 0s (cached) |

## Architecture Decision Records

### ADR-001: File Position Tracking
**Decision**: Track file byte position in state file instead of rescanning entire history.jsonl

**Rationale**: history.jsonl is append-only; seeking to last position is O(1) vs O(n) scan

**Consequences**:
- + 99.9% reduction in scan time
- - Requires state file management
- - Must handle file truncation/rotation

### ADR-002: Remove Redundant Duplicate Check
**Decision**: Skip `msg_id in indexed_ids` check when using position tracking

**Rationale**: Position tracking guarantees all prior messages are indexed; duplicate check is redundant

**Consequences**:
- + Eliminates 42M set lookups
- - New messages could contain duplicates (mitigated by incremental_update() dedup)

### ADR-003: Singleton EmbeddingManager
**Decision**: Use ComponentManager.get_embedding_manager() instead of direct instantiation

**Rationale**: Model loading is expensive; caching in memory eliminates 5-10s overhead

**Consequences**:
- + Faster incremental updates
- + Model reused across operations
- - Memory footprint increased (~500MB)

## Implementation Files

| File | Purpose |
|------|---------|
| `incremental_chs_update.py` | Incremental update script with position tracking |
| `chat_history_search.py` | CHS command with auto-update integration |
| `faiss_vector_store.py` | FAISS index operations |
| `embedding_manager.py` | Embedding generation with singleton support |
