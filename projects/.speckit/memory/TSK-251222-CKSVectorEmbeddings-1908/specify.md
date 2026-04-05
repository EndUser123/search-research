# CKS Vector Embeddings - Specification

**Date:** 2025-12-22
**TSK:** TSK-251222-CKSVectorEmbeddings-1908

---

## Problem Statement

CKS currently uses LIKE-based search which only matches keywords, not meaning.

**Current limitations:**
- Search "logging patterns" won't find "dual sink logging" unless exact word match
- Search "authentication" won't find "JWT" or "OAuth" content
- No semantic understanding of query intent

---

## Success Criteria

1. **Semantic Search:** Search by meaning, not just keywords
2. **Relevance Ranking:** Results ranked by semantic similarity
3. **Performance:** Search <200ms for 1000 entries
4. **Constitutional Compliance:**
   - Solo-dev appropriate (no enterprise overhead)
   - On-demand only (no background services)
   - Library-first (use existing libraries)

---

## Proposed Solution

### Architecture

```
CKS Entry Ingestion:
1. Text content → Sentence Transformer model
2. Generate 384-dim embedding (all-MiniLM-L6-v2)
3. Store in SQLite with content
4. Optional: Index with FAISS for faster search

Semantic Search:
1. Query text → embedding
2. Cosine similarity with stored embeddings
3. Rank by similarity score
4. Return top N results
```

### Technology Stack

| Component | Library | Size | Purpose |
|-----------|---------|------|---------|
| Embeddings | `sentence-transformers` | ~100MB | Generate text embeddings |
| Model | `all-MiniLM-L6-v2` | 120MB | Fast, good quality |
| Storage | SQLite (BLOB) | - | Store embeddings with entries |
| Similarity | NumPy/cosine | - | Calculate similarity |
| Optional: FAISS | `faiss-cpu` | ~10MB | Faster vector search |

---

## Implementation Scope

### Phase 1: Basic Vector Search (MVP)
- ✅ Add embedding generation to `ingest_memory()` and `ingest_pattern()`
- ✅ Store embeddings in `entries` table (BLOB column)
- ✅ Add `search_semantic()` method for similarity search
- ✅ Use NumPy for cosine similarity (no FAISS yet)

### Phase 2: Performance Optimization
- ✅ Add FAISS index for faster search (>1000 entries)
- ✅ Batch embedding generation for existing entries
- ✅ Embedding caching

### Out of Scope
- Training custom models (use pre-trained)
- Multi-modal embeddings (text only)
- Distributed vector search (single-machine only)

---

## Migration Strategy

### Existing Entries
```python
# Backfill embeddings for 370 existing entries
from src.cks.unified import CKS

cks = CKS()
cks.backfill_embeddings()  # New method
```

### New Entries
```python
# Automatic embedding generation
cks.ingest_memory("Question", "Answer")  # Generates embedding automatically
cks.ingest_pattern("Title", "Content")   # Generates embedding automatically
```

---

## Failure Conditions

- Search >500ms for 1000 entries
- Embedding generation >1s per entry
- Database size >3x (embeddings should be ~1.5x content size)
- Breaking existing LIKE search

---

## Time Estimate

- Phase 1 (MVP): 1-2 hours
- Phase 2 (Optimization): 1 hour
- Testing: 30 minutes
- **Total:** 2.5-3.5 hours
