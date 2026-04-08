# ADR-003: Staged Navigator with Multi-Terminal Safety

**Status:** Proposed | **Date:** 2026-04-05 | **Context:** search-research local backend layer enhancement

---

## Context

The `AsyncSearchRouter` in `core/router_async.py` fires all backends simultaneously via `asyncio.gather` with no layer ordering, no terminal isolation, and no git-history freshness checks. Three specific problems:

1. **No staged execution**: Layers 1-2 (exact match) and Layer 3 (semantic) compete equally, adding latency when cheap exact searches would suffice
2. **No terminal isolation**: `QueryCache` and `BackendHealthRegistry` are shared across all terminals — Terminal A's cache can serve stale results to Terminal B; Terminal A's backend failures can mark backends "down" for Terminal B
3. **No stale-data immunity**: CKS and CHS backends return cached results without checking if underlying files changed since the index was built

**Assumptions:**
- Single-workspace assumption: each terminal operates in one `cwd` — no cross-workspace health or cache interference expected
- Best-effort search: no result is critical enough to block on freshness; stale results with a flag are acceptable
- Windows 11 environment: `rg` (ripgrep) assumed available on PATH; ColGREP optional

**Value Assessment Principle** (from `P:\.claude\.evidence\value-assessment-principle.md`): Before adding each layer or component, verify it provides unique contribution beyond what existing patterns already cover. For any new abstraction, confirm existing code doesn't already provide ≥70% of the capability.

---

## Design

### Three-Layer Staged Navigator

| Layer | Engine | When It Runs | Latency Target |
|-------|--------|-------------|----------------|
| 1 | `GrepBackend` + `CDSBackend` | Always | <50ms |
| 2 | `RipgrepLayer` (extracted from `CDSBackend._ripgrep_importers` at `cds_backend.py:332`) | If Layer 1 underfills | <200ms |
| 3 | `ColGREPBackend` (or HyDE fallback) | If Layers 1-2 underfill AND intent is semantic | <2s |

**Staged vs Parallel dispatch**: Intent classifier detects semantic queries (contains intent-level language like "how does X work", "best approach for Y"). If semantic → staged. Otherwise → `asyncio.gather` parallel (existing behavior preserved for non-semantic queries).

### Multi-Terminal Isolation

**QueryCache** (`cache.py`): Add `terminal_id = hashlib.md5(str(Path.cwd()).encode()).hexdigest()[:8]` to cache key. Each terminal gets isolated cache namespace. `cache.py:42` — modify `_hash_query` to include `terminal_id` in key data.

**BackendHealthRegistry** (`backend_health.py`): Add `terminal_id` key to health state dict. `backend_health.py:59` — singleton pattern retained but state is per-terminal namespaced. Terminal A's consecutive failures don't affect Terminal B's view of backend health.

### Git-History Freshness

CKS and CHS backends run `git diff --name-only` on touched files before returning results. If diff is non-empty since index was built → return results with `metadata.stale = True`. Do not block. This directly addresses task #2638.

### Compact-Event Resilience

All `SearchResult` objects gain `metadata.staged_layer: int` (1, 2, or 3) indicating which layer produced the result. Enables interrupt-and-resume visibility: a compact event mid-stream can see which layer each result came from without re-running completed layers.

---

## Contract Boundaries

| Boundary | Producer | Consumer | Required Fields | Freshness Authority | Invalidation Trigger | Failure Behavior |
|----------|----------|----------|-----------------|--------------------|--------------------|----------------|
| `terminal-cache` | `QueryCache.set()` | `search_async()` | `query`, `results`, `terminal_id` | `terminal_id` key namespace | TTL expiry or `invalidate()` | Cache miss → query backends |
| `per-terminal-health` | `BackendHealthRegistry` | Backend selection | `terminal_id`, `backend_name`, `status` | `terminal_id` key namespace | Backend restart or `record_success()` | Unknown → assume ready |
| `staged-result` | `StagedBackendRouter` | `_rank_results()` | `SearchResult` schema + `staged_layer` | N/A | New query | Empty layer → next layer |
| `git-grounding` | `GitHistoryGrounding.check()` | CKSMetadataBackend / IncrementalIndexUpdater | `touched_files`, `is_stale` | `git diff` output | Any non-empty diff since index built | Warn + mark stale, don't block |

---

## Implementation Sequence

| Order | Component | Value Assessment | Risk |
|-------|-----------|-----------------|------|
| 1 | `terminal_id` in `QueryCache._hash_query` | Extends existing key; no new abstraction | LOW |
| 2 | `terminal_id` in `BackendHealthRegistry` state | Extends existing singleton; dict key change only | LOW |
| 3 | Extract `_ripgrep_importers` → `RipgrepLayer` class | Pattern already exists at `cds_backend.py:332`; this is extraction not creation | LOW |
| 4 | `StagedBackendRouter` with intent-classifier dispatch | NEW abstraction; no existing pattern covers this | MEDIUM |
| 5 | `staged_layer: int` metadata on `SearchResult` | Extends existing metadata dict; no schema change | LOW |
| 6 | Git-history grounding on CKS/CHS | Pattern from downloaded Perplexity doc; direct application | LOW |
| 7 | `ColGREPBackend` Layer 3 (progressive) | DEPENDS on #2473 (HyDE fix); only if ColGREP adds unique capability | MEDIUM |

**Value Assessment applied**: Steps 1, 2, 5, 6 extend existing patterns with minimal changes. Step 3 extracts existing code. Step 4 is the only greenfield addition — justified by the staged dispatch logic that doesn't exist anywhere. Step 7 is explicitly deferred until ColGREP's unique contribution vs HyDE is verified.

---

## Safety Policy

- Unknown freshness → fail-open on git-grounded backends; block only at CKS/CHS layer (Layers 1-2 always serve fresh data)
- Schema mismatch → reject at `StagedBackendRouter` dispatch
- ColGREP unavailable → degrade to HyDE Layer 3 transparently
- `rg` (ripgrep) unavailable → Layer 2 degrades to `GrepBackend` full-file scan (slower but functional)

**Bounded blast radius**: worst case is CKS/CHS returning `stale=True` results while Layers 1-2 serve fresh data. No data corruption possible. No cross-terminal state interference.

---

## Dependencies

| Task | Blocks |
|------|--------|
| #2473 (Fix HyDE layer) | Layer 3 ColGREP/HyDE progressive fallback |
| #2638 (CHS/CKS 0 results) | Git-grounding step; if root cause is not stale index, grounding approach changes |

---

## Consequences

**Positive:**
- Fast queries answered by Layer 1 in <50ms without waiting for semantic backends
- Terminal isolation prevents cross-terminal cache poisoning and health interference
- Git-grounding surfaces stale indexes rather than silently returning wrong results
- `staged_layer` metadata enables interrupt-and-resume debugging

**Negative:**
- Staged dispatch adds branching complexity to `search_async`
- Terminal ID derived from `Path.cwd()` — two terminals in same directory share cache (intentional: same workspace = same working set)
- ColGREP Layer 3 adds Rust dependency if used

**Rejected alternatives:**
- Inline layering into existing backends (violates single-responsibility; rejected per Value Assessment Principle)
- Replace existing backends with ColGREP-only (loses exact-match speed; ColGREP is slower for identifier search)
