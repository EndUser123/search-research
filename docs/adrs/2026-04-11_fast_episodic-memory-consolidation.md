# ADR-20260411-fast-episodic-memory-consolidation: Absorb Episodic-Memory Semantic Chat Search into search-research

**Status:** Accepted
**Date:** 2026-04-11
**Context:** Want to eliminate the `episodic-memory` plugin while retaining its core value: semantic/conceptual chat search with AI-generated summaries across conversations.

### Decision

Add **two capabilities** to the existing CHS backend in `P:/packages/search-research`:
1. **Semantic search layer** using the already-installed `EmbedClient` (SentenceTransformer)
2. **Summary generation** — store AI-generated conversation summaries in CHS SQLite alongside raw messages

This replaces the plugin entirely. No new packages. No vector DB. No cross-project complexity initially.

### Rationale

| episodic-memory provides | search-research already has |
|-------------------------|---------------------------|
| Vector/semantic search | `EmbedClient` with SentenceTransformer (embeddings.py:34-53) |
| AI-generated summaries | No — needs addition |
| Cross-project search | No — scope for later |
| FTS5 keyword search | CHS with FTS5 already in `search.py` |

The `EmbedClient` is already wired up and working. Only missing piece is storing/use of summaries.

### What Changes

**1. CHS SQLite schema — add `summary` column**

File: `core/chs/db.py` or `core/chs/schema.py`

```sql
ALTER TABLE conversations ADD COLUMN summary TEXT;
```

**2. Summary generation on ingest — hook into existing provider pipeline**

File: `core/chs/providers/base.py` or new `core/chs/summarizer.py`

```python
# After conversation is appended to JSONL, generate summary
async def generate_summary(conversation_id: str, messages: list[dict]) -> str:
    """Generate 1-2 sentence summary via LLM."""
    prompt = f"Summarize this conversation in 1-2 sentences:\n{messages[-1]['content'][:500]}"
    # Use existing LLM integration
    return summary
```

**3. Semantic search in CHS — use EmbedClient**

File: `core/chs/search.py` — add `search_semantic(query, limit)` alongside existing FTS5 `search()`

```python
async def search_semantic(self, query: str, limit: int = 10) -> list[SearchResult]:
    """Search using vector embeddings + cosine similarity."""
    embedding = embed_client.embed_texts([query])[0]
    vector = bytes_to_vector(embedding, dim=384)
    # Query existing messages, rank by cosine similarity
    results = []
    for conv in self._get_all_conversations():
        score = cosine_similarity(vector, conv.embedding)
        if score > 0.7:
            results.append((score, conv))
    return sorted(results, key=lambda x: x[0], reverse=True)[:limit]
```

**4. Integrate into unified router — add `semantic` chat method**

File: `core/unified_router.py` — when `--chat-method semantic` or conceptual query detected, route to CHS semantic search.

### Alternatives Considered

| Option | Pros | Cons | Why Rejected |
|--------|------|------|--------------|
| **A: Keep plugin + integrate deeper** | Works today | Two systems to maintain, dependency on external plugin | Eliminating plugin is explicit goal |
| **B: Full cross-project index** | Single semantic index | Complex, privacy concerns, sync overhead | Scope creep — add later if needed |
| **C: SQLite vec extension** | Native vector ops | Adds compiled dep, more complexity | `EmbedClient` + Python cosine already sufficient |

### Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| Search recall | Semantic finds conceptual matches FTS5 misses | Slower (~200ms vs 10ms) |
| Memory | Reuses existing EmbedClient | Summary storage +20-100 bytes/conv |
| Complexity | Single system | CHS gets thicker |

### Multi-Terminal Safety
- **Safe** — summaries generated once on ingest, stored in SQLite (per-project DB)
- No shared mutable state introduced
- EmbedClient is already session-scoped

### Implementation

1. **Schema**: Add `summary TEXT` to `conversations` table in `db.py`
2. **Summarizer**: New `core/chs/summarizer.py` — LLM call to generate summary, called from provider `append()` pipeline
3. **Semantic search**: Add `search_semantic()` to `core/chs/search.py` using existing `EmbedClient`
4. **Router integration**: In `unified_router.py`, add `method='semantic'` option for chat search
5. **Skill updates**: `/chs`, `/search`, `/all` already auto-detect — semantic backend activates when query implies conceptual intent

**Rollback:** Feature flag `CHS_SEMANTIC_ENABLED=false` disables semantic search, falls back to FTS5.

### Consequences
- **Positive:** Eliminated plugin dependency; semantic chat search now in-house; existing EmbedClient leveraged
- **Negative:** Ingest slightly slower (summary generation); storage grows with summaries
- **Later:** Cross-project search via configurable transcript paths in `chs_config.json`
