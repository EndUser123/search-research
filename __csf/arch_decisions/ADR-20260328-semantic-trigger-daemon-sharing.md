# ADR-20260328: Semantic Trigger Resource Optimization via Daemon-Shared Embeddings

**Status:** Proposed
**Date:** 2026-03-28
**Driver:** Solo developer — multi-terminal RAM efficiency

---

## Context

The `sequential_thinking` hook uses `sentence-transformers/all-MiniLM-L6-v2` for semantic trigger detection. Each terminal loads its own model instance:

- **Per-terminal RAM:** ~90MB
- **10 terminals:** ~900MB total (duplicate model weights)

The daemon (`unified_semantic_daemon`) already provides shared model loading for CHS/CKS search. This ADR evaluates using that daemon for semantic trigger embeddings vs per-terminal loading.

## Decision

**Use daemon-based shared embeddings** via `DaemonClient` from `packages/search-research/contrib/semantic_daemon/`.

## Alternatives Considered

| Option | RAM (10 terminals) | Latency | Complexity |
|--------|-------------------|---------|------------|
| A: Per-terminal | ~900MB | ~50ms local | Simple |
| B: Daemon-shared | ~100MB total | ~50-100ms IPC | Moderate |

## Evidence

### Quantitative

| Metric | Per-Terminal | Daemon | Delta |
|--------|--------------|--------|-------|
| RAM | ~900MB | ~100MB | -800MB (-89%) |
| Embedding latency | ~50ms | ~50-100ms | +0-50ms |

**Source:** Derived from existing daemon benchmarks (`packages/search-research/contrib/semantic_daemon/CLAUDE.md:407`).

### Why Latency Overhead Is Acceptable

- Semantic trigger detection runs **once per prompt** (not per character/token)
- IPC overhead (~50ms) occurs at prompt submission time, before user sees response
- Soft floor zone prompts (15-30 chars) are the primary beneficiaries of semantic boost
- Strong match prompts (>30 chars) typically trigger via regex alone

## Consequences

### Positive

- 89% RAM reduction (~800MB saved across 10 terminals)
- Architecture aligns with existing daemon ecosystem
- Single model instance, easier updates/maintenance
- Multi-terminal safe (named pipe IPC with mutex synchronization)

### Negative 2nd Order Effects

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Daemon single point of failure | Medium | Auto-restart via SessionStart hook; regex-only fallback |
| IPC latency overhead | Low | Acceptable (~50ms, one-time per prompt) |
| Worker pool contention | Low | Increase ThreadPoolExecutor from 4 to 8 workers |
| Cold start (model loading) | Low | ~2-3s on first semantic request; non-blocking |

### Edge Cases

1. **Daemon dies mid-session:** Terminals fall back to regex-only triggers (not hard failure)
2. **10+ simultaneous terminals:** Worker queue grows but doesn't fail; latency degrades gracefully
3. **Daemon unavailable at startup:** Client auto-starts daemon; falls back to direct loading if auto-start fails

## Implementation Path

1. Create `UserPromptSubmit_modules/sequential_thinking_semantic_client.py`
   - Wraps `DaemonClient` from `packages/search-research/contrib/semantic_daemon/daemon_client.py`
   - Provides `compute_similarity(prompt)` function returning (score, matched_phrase)
   - Falls back to direct `SentenceTransformer` loading if daemon unavailable
2. Update `sequential_thinking.py` to use semantic client instead of direct model
3. Increase daemon worker pool from 4 to 8 in `unified_semantic_daemon.py`
4. Document fallback behavior in hook comments

## Multi-Terminal Safety

- Named pipe IPC: Windows `Global\CSF_NIP_SemanticDaemon_Startup` mutex prevents race conditions
- Dynamic pipe names: Prevents stale handle issues after daemon crash
- Discovery file: `P:/__csf/data/semantic_daemon_discovery.json` for pipe name lookup
- Pipe connectivity test: Client verifies pipe is accessible before trusting discovery file

**Source:** `packages/search-research/contrib/semantic_daemon/CLAUDE.md:491`

## Verification

After implementation:

1. Run existing 35 tests: `pytest P:/...
   - 2. Measure RAM with 10 terminals (target: <150MB total for semantic embeddings)
   - 3. Verify IPC latency <100ms per trigger detection
