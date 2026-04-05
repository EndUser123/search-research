# ADR-20260329: FAP Layer 2 Semantic Embedding via Semantic Daemon

**Date:** 2026-03-29
**Status:** Proposed
**Decider:** Solo dev (brsth)
**Supersedes:** None

---

## Context

FAP (Failure Analysis Protocol) Layer 2 in `analysis_protocol_gate.py` uses exact-token keyword overlap (`_concept_cluster_match`) to detect FAP intent. This fails on paraphrases:

```
Trigger: "what actually triggered this failure"
Concept cluster: root_cause (keywords: root, cause, trigger, ...)
Token overlap: 0 hits → no match → FAP not injected
```

But the intent is identical. The problem is paraphrase brittleness, not keyword quality.

### Constraints

1. **Hook subprocess timeout**: 60s max, must complete within Claude Code hook lifecycle
2. **Multi-terminal isolation**: State must not bleed between terminals
3. **Compaction immune**: Model state must survive Claude Code serialization/deserialization
4. **No external API calls**: Hooks cannot call external APIs (per constitutional policy)
5. **Local GPU available**: NVIDIA RTX 5070, `torch 2.11.0.dev20251215+cu128`, `sentence-transformers 5.2.3`

### Options considered

**Option A: Extend semantic daemon with `embed_texts` action** (CHOSEN)
- Add raw embedding endpoint to existing `UnifiedSemanticDaemon`
- FAP hook calls `SemanticClient.query("embed", {"texts": [prompt]})` via existing named pipe IPC
- Daemon is already: long-running, system-level, multi-terminal safe, compaction-immune
- Single model instance shared across all hook calls and terminals
- **Remaining risk**: daemon mid-request interrupted by compaction → needs explicit test

**Option B: Local MiniLM in hook subprocess**
- `all-MiniLM-L6-v2` (~90MB, ~2s cold start on GPU)
- Fresh subprocess per hook call → 2s cold start every invocation
- NOT compaction-immune: model state lost on compaction
- Multi-terminal: each terminal subprocess loads own copy → VRAM duplication
- **Rejected**: fails compaction immunity and multi-terminal sharing

**Option C: Persistent hook runner cache**
- Maintain warm model in hook runner process
- Hook runner is thin spawner not designed for stateful caching
- Compaction could kill/reset runner, losing cached model
- **Rejected**: architectural change too large, compaction risk unresolved

---

## Decision

Add `embed_texts` action to `SemanticClient` and `UnifiedSemanticDaemon`. FAP Layer 2 calls the daemon via named pipe IPC, gets back float32 embedding vectors, computes cosine similarity against pre-computed cluster centroids.

### Semantic layer (replaces keyword overlap)

For each FAP prompt:
1. Embed the prompt via `SemanticClient.query("embed", {"texts": [prompt]})`
2. Compute cosine similarity against 6 pre-defined cluster centroid vectors
3. If max similarity > threshold → semantic match → FAP triggers
4. Fall back to keyword overlap if daemon unavailable

### Cluster centroids

Pre-compute centroid vectors for 6 FAP concept clusters using known-positive examples:
- `wrong_abstraction`
- `root_cause`
- `missing_principle`
- `fix_inadequacy`
- `bug_class`
- `frustration_signal`

Centroids stored as module-level constants in `analysis_protocol_gate.py` (computed once at import time via sample embedding average).

### Similarity threshold

Configurable via `cognitive_enhancers_config.json`:
```json
{
  "fap_semantic_threshold": 0.75
}
```

### Daemon embedding model

Use the same model already loaded by the daemon for search — `sentence-transformers/all-MiniLM-L6-v2`. No new model needed.

---

## Consequences

### Positive
- Paraphrase blindness resolved: "what actually triggered this" and "root cause of" both embed to similar vectors → same cluster match
- Single model instance: GPU memory efficient, daemon-warm across all terminals
- Compaction immune: daemon is a separate OS process, survives Claude Code compaction
- Multi-terminal safe: named pipe IPC with mutex already implemented in daemon startup
- Existing infrastructure reused: SemanticClient, daemon lifecycle, auto-start already wired

### Negative
- Adds embedding round-trip via IPC (~5-20ms) to every semantic Layer 2 check
- If daemon is down, falls back to keyword overlap (acceptable degradation)
- Compaction mid-request: potential brief timeout — needs test coverage

### Risks
| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Daemon crash during compaction | Low | Daemon has overlapped I/O with timeout + health monitoring |
| Pipe busy / connection refused | Low | SemanticClient has retry logic (MAX_RETRIES=2, 0.5s delay) |
| Embedding model different from search model | None | Same `sentence-transformers/all-MiniLM-L6-v2` used |

---

## Implementation Plan

### Phase 1: Add `embed` action to daemon

**Files:**
- `packages/search-research/contrib/semantic_daemon/unified_semantic_daemon.py`
- `packages/search-research/contrib/semantic_daemon/daemon_client.py`

**Changes:**
1. `SemanticClient.query("embed", {"texts": list[str]})` → returns `{"embeddings": [[float, ...], ...], "status": "success"}`
2. `UnifiedSemanticDaemon._handle_embed()` → routes to model call
3. Uses same embedding model as `_get_embedding_model()` already in daemon

**Daemon IPC protocol** (existing):
```
[4 bytes: length][JSON: {"action": "embed", "texts": [...]}]
Response:
[4 bytes: length][JSON: {"embeddings": [...], "status": "success"}]
```

### Phase 2: Update FAP Layer 2 in `analysis_protocol_gate.py`

**File:**
- `P:\.claude\hooks\UserPromptSubmit_modules\analysis_protocol_gate.py`

**Changes:**
1. Add `_SEMANTIC_THRESHOLD` config
2. Add `_compute_cluster_centroids()` — pre-compute at import time from sample phrases
3. Replace `_concept_cluster_match()` with semantic similarity against centroids
4. Keep `_concept_cluster_match` as fast-path fallback when daemon unavailable
5. Add `_get_embedding(prompt)` → calls SemanticClient with retry/fallback

**Fallback chain:**
```
_semantic_match(prompt)
  → try: SemanticClient.query("embed", {"texts": [prompt]})
  → except (ConnectionError, TimeoutError):
      → _concept_cluster_match(prompt)  # keyword fallback
```

### Phase 3: Test + verify

1. Unit test: paraphrase "what actually triggered this failure" matches `root_cause` cluster
2. Unit test: keyword fallback fires when daemon is down
3. Integration test: compaction mid-embedding-request → daemon recovers
4. End-to-end: verify FAP injection fires on paraphrase inputs

---

## Files

| File | Change |
|------|--------|
| `packages/search-research/contrib/semantic_daemon/unified_semantic_daemon.py` | Add `_handle_embed()` action |
| `packages/search-research/contrib/semantic_daemon/daemon_client.py` | Add `query("embed", ...)` method |
| `P:\.claude\hooks\UserPromptSubmit_modules\analysis_protocol_gate.py` | Semantic Layer 2 + fallback |
| `P:\.claude\hooks\logs\fap_layer_stats.json` | Track semantic vs keyword hit rates |

---

## References

- Semantic daemon docs: `packages/search-research/contrib/semantic_daemon/CLAUDE.md`
- FAP hook: `P:\.claude\hooks\UserPromptSubmit_modules\analysis_protocol_gate.py`
- Hook external dependency policy: `P:\.claude\hooks\CLAUDE.md` → "Hook External Dependency Policy"
- Multi-terminal safety: daemon uses `Global\CSF_NIP_SemanticDaemon_Startup` mutex (daemon_client.py)
