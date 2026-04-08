# ADR-20260407: Optimal Download Deduplication Strategy

**Status:** Proposed
**Date:** 2026-04-07
**Context:** Round-robin batch scheduler (ADR-20260404) has a dedup gap between `analysis_status` and `download_archive`. This ADR determines the canonical dedup source and closes the gap.

---

## Status Quo

Two parallel tracking systems exist:

| Table | Authority | States | Written by |
|-------|-----------|--------|------------|
| `analysis_status` | Transcript cache gate | `pending`, `complete`, `failed` | `mark_complete()` / `mark_failed()` |
| `download_archive` | Scheduler processing log | `success`, `failed`, `attempting` | `archive_finalize()` |

**Current `yield_next()` logic:**
1. Query `analysis_status WHERE status='pending'` → channels and videos
2. For each candidate, check `download_archive` — if `status IN (success, failed, attempting)` → skip

**The gap:** `archive_finalize()` is only called in the round-robin path (`analyze_videos_round_robin`). Videos processed by the old `analyze_videos_parallel` path call `mark_complete()` (updating `analysis_status`) but never `archive_finalize()`. These videos would be re-yielded on restart — except `yield_next()` first queries `analysis_status` for pending videos, and they are `status='complete'`, so they are excluded from the query result.

**Pre-mortem finding confirmed:** Videos processed pre-round-robin have `status='complete'` in `analysis_status` and no entry in `download_archive`. On restart, they are excluded by the pending query — correct behavior. No dedup gap at the yield level.

**Actual gap found during implementation:** `archive_finalize()` in the success path of `analyze_videos_round_robin` was MISSING — it was only called for failures. This means successful videos are not written to `download_archive` at all, breaking the yield_skip logic on restart.

---

## Decision: Canonical Source = `analysis_status` + `download_archive` (co-authority)

**Rationale:**

1. `analysis_status.status='complete'` is the canonical signal that a transcript exists on disk. `has_cached_transcript()` is checked inside `_analyze_one` before fetching — if a video somehow has `status='complete'` but no transcript, it re-fetches.

2. `download_archive` is the scheduler's own processing log — it prevents the same video from being yielded twice within a scheduler's own iteration pass (via `_record_attempting` EXCLUSIVE lock).

3. Keeping both allows `yield_next()` to skip videos that are:
   - Already complete in `analysis_status` (not in pending query at all)
   - Already in `download_archive` with success/failed/attempting (skipped even if still pending)

4. This is NOT redundant — they serve different dedup scopes. `analysis_status` is the master work-queue; `download_archive` is the intra-scheduler dedup log.

---

## Required Fixes

### FIX-1 [HIGH]: `archive_finalize('success')` missing in round-robin success path

**File:** `csf/batch.py`
**Location:** `analyze_videos_round_robin()`, success branch

Currently:
```python
if success and result is not None:
    successful_results[video_id] = result
    mark_complete(video_id)
    scheduler.archive_finalize(video_id, "success", source)  # ← MISSING
```

Must add `archive_finalize` on success. The failure path already has it.

**Evidence:** batch.py:264-267 (failure path has archive_finalize; success path does not)

### FIX-2 [MEDIUM]: `archive_finalize()` missing in `analyze_videos_parallel`

**File:** `csf/batch.py`
**Location:** `analyze_videos_parallel()`, both success and failure branches

The old path updates `analysis_status` but not `download_archive`. While `analysis_status.status='complete'` prevents re-yield on restart, `download_archive` should also be updated for completeness.

Both branches should call `scheduler.archive_finalize(video_id, "success/failed", source)`.

**Note:** `analyze_videos_parallel` does not receive a `scheduler` argument. It must be passed in or the function must be refactored to accept it.

### FIX-3 [LOW]: `yield_next()` does not check `analysis_status` for `complete`

Currently `yield_next()` relies entirely on `download_archive` to skip completed videos. If `archive_finalize` is ever missed (FIX-1, FIX-2), a video could be re-yielded even though `analysis_status.status='complete'`.

**Enhancement:** In `yield_next()`, after `_archive_status` check, also query `analysis_status` for `status='complete'` and skip if found.

---

## Contract Boundary Inventory

### Boundary 1: `yield_next()` → worker

| Field | Value |
|-------|-------|
| Producer | `yield_next()` generator |
| Consumer | `ThreadPoolExecutor` workers calling `_analyze_one()` |
| Input schema | `video_id`, `source` (channel URL) |
| Output schema | N/A (pull model) |
| Required fields | `video_id`, `source` |
| Freshness authority | `download_archive` (scheduler dedup) + `analysis_status` (transcript gate) |
| Invalidation trigger | `archive_finalize()` called for that `video_id`; or `analysis_status.status` changes to `complete` |
| Isolation boundary | Workspace-shared SQLite (WAL mode) |
| Failure behavior | Video stuck in `attempting` if worker crashes — stale recovery promotes to `failed` after 30min |

### Boundary 2: `archive_finalize()` → `download_archive`

| Field | Value |
|-------|-------|
| Producer | `batch.py` worker result handler |
| Consumer | `yield_next()` (reads to skip) |
| Input schema | `video_id`, `status` (success/failed), `source` |
| Output schema | `download_archive` row INSERT OR REPLACE |
| Required fields | `video_id`, `status` |
| Freshness authority | `archive_finalize()` call timestamp |
| Invalidation trigger | Subsequent `archive_finalize()` for same `video_id` |
| Isolation boundary | Workspace-shared SQLite (WAL + EXCLUSIVE transaction) |
| Failure behavior | SQLite error → best-effort (logged warning); video may be re-yielded |

---

## Optimal Flow (Target State)

```
analysis_status          download_archive           Transcript Cache
─────────────────        ─────────────────        ─────────────────
pending ──────────► yield_next()
                              │                        │
                              ▼                        │
                        worker.process()               │
                              │                        │
                   ┌──────────┴──────────┐            │
                   ▼                     ▼            │
              success                 failed           │
                   │                     │            │
          mark_complete()      mark_failed()           │
          archive_finalize()   archive_finalize()      │
               ("success")         ("failed")           │
                   │                     │            │
                   └─────────┬──────────┘            │
                             ▼                        │
                     download_archive                 │
                             │                        │
                      Next yield_next():              │
                      Skip if in archive              │
                      (status = success/failed)      │
                                              (also skip if analysis_status.complete)
```

---

## What "Invalid" Means

The user's question: "track invalid videos so we don't try to download them again."

There are two distinct cases:

1. **Permanently unavailable** (deleted, private, region-locked, no captions): `archive_finalize(video_id, 'failed')` — all methods exhausted, written to `download_archive`. On restart, `yield_next()` skips it. These are re-tried only if explicitly re-queued.

2. **Temporarily failed** (rate-limited, network error, 5xx): `channel_cooldown` entry with `cooldown_until`. The channel is skipped for the cooldown period. After cooldown expires, it becomes eligible again.

The system does NOT distinguish "transient failure from specific method" vs "video permanently unavailable" — both result in `archive_finalize('failed')`. This is acceptable because:
- The 30-day stale recovery means persistently failing videos are eventually promoted from `attempting` → `failed`
- A video marked `failed` can be manually re-queued by changing `analysis_status` back to `pending`

---

## Rate Limit Efficiency

The round-robin scheduler + per-channel cooldown is the primary 429-resilience mechanism:

- **Jitter** is applied per-worker after each job completion (moved from `yield_next()` in pre-mortem fix)
- **Channel cooldown** skips a channel for `_COOLDOWN_SECONDS` (default 60s) after a 429
- **Circuit breaker** in `transcript.py` opens after 3 consecutive 429s on a method token, independently of the channel cooldown
- **Stale recovery** promotes videos stuck in `attempting` (worker crashed) to `failed` after 30 minutes

This stack is sufficient to avoid unnecessary rate limit triggers. No additional backoff mechanism is needed.

---

## Alternatives Considered

**Alternative A: `download_archive` only as canonical source**
- Drop `analysis_status.status` as dedup signal
- `yield_next()` queries only `download_archive` for skip decisions
- **Rejected** — requires changing the pending-videos query to join both tables; adds complexity with no clear benefit since both signals are available

**Alternative B: `analysis_status` only as canonical source**
- Remove `download_archive` dedup check from `yield_next()`
- Rely solely on `status='complete'` to skip
- **Rejected** — `download_archive` also tracks `failed` and `attempting` states that need to skip re-yield; also `analysis_status` can be set to `failed` by `mark_failed()` which allows retry, while `download_archive.failed` means "all methods exhausted"

**Alternative C: Separate "permanent failure" status**
- Add a `permanently_unavailable` state to distinguish from retryable failures
- **Rejected** — premature optimization; the current `failed` state serves this purpose adequately; adding a new state requires schema migration and more states to manage

---

## Summary

The optimal flow is:
- **`analysis_status`** = transcript cache gate (`complete` = transcript exists)
- **`download_archive`** = scheduler processing log (`success/failed/attempting`)
- **`yield_next()`** skips videos in either table
- **Rate limits** handled by round-robin scheduling + channel cooldown + per-worker jitter
- **No new state** needed; current schema is sufficient

**FIX-1 is the critical gap** — `archive_finalize('success')` must be added to the round-robin success path.
