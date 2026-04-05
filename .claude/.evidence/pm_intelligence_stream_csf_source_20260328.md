# Pre-Mortem: intelligence-stream `csf-source` CLI Restructuring

**Analyzed**: `set_status_batch` O(1) bulk insert, N+1 loop elimination, `InterProcessLock` on `cmd_sync`
**Date**: 2026-03-28
**Analysis**: CLAUDE.md constraints + code review + empirical test results (109/110 pass)

---

## Step 0: Constraints from CLAUDE.md

- **Solo-dev**: No CI/CD, no PR reviews, pragmatic solutions over enterprise patterns
- **Multi-terminal safety**: State changes must propagate; shared state needs locking
- **Evidence tiers**: Claims must cite evidence (Tier 1 = execution artifacts)
- **Fasteners not in package**: Added to requirements.txt and installed separately

---

## Step 0.7: Kill Criteria

- If `set_status_batch` silently drops entries (partial commit) → rollback and revert
- If `InterProcessLock` causes `cmd_sync` to hang indefinitely → remove lock
- If N+1 replacement causes data loss → rollback per-entry approach

---

## Step 1: Failure Scenario

**"It's 6 months later. The `csf-source` CLI broke our YouTube ingestion pipeline and we lost tracking for several channels."**

---

## Step 1.5: Fix Side Effects

| Fix | NEW Risks Introduced |
|-----|---------------------|
| `set_status_batch` with `BEGIN IMMEDIATE` | Long-held exclusive lock blocks readers; WAL reader timeout |
| `fasteners.InterProcessLock` on `cmd_sync` | Lock files orphaned on crash; `P:/__csf/` not always writable |
| N+1 → batch | If batch fails mid-way, all entries roll back (atomicity is now ALL-or-NOTHING) |
| `is_complete(video["video_id"])` pre-filter | If video_id is missing from returned dict, silently skipped |

---

## Step 2: Brainstorm Failure Causes (10+)

### Tech/Process
1. **Batch atomicity trap**: `set_status_batch` uses `INSERT OR REPLACE` — if one video's data is malformed, entire batch rolls back under `BEGIN IMMEDIATE`
2. **Orphaned lock files**: `fasteners.InterProcessLock` on `P:/__csf/.data/intelligence-stream/locks/` — if process killed mid-lock, lock file stays, causing permanent blocking
3. **Hardcoded path fragility**: `P:/__csf/` on Windows may not exist; `mkdir(parents=True, exist_ok=True)` at import time could fail silently if parent is read-only
4. **`is_complete` pre-filter data loss**: In `cmd_add`, `is_complete(video["video_id"])` skips entries not yet complete — but if the video WAS processed but marked failed, it gets silently re-queued
5. **Duplicate source in gap_videos**: `gap_videos` from `enumerate_recent` may contain videos already in DB — `is_complete` only checks "complete", not "pending"
6. **WAL reader starvation**: `BEGIN IMMEDIATE` blocks all readers; on a large batch (10K videos), readers timeout
7. **`cmd_check` concurrent with `cmd_sync`**: Both write to `analysis_status`; no lock on `cmd_check` — potential TOCTOU on `pending_ids` set

### External
8. **YouTube API quota exhaustion**: `enumerate_full` hits quota mid-enumeration — partial batch of pending videos, user doesn't know which were added
9. **RSS feed disabled**: `check_rss` returns empty; gap detection never fires; new videos silently missed
10. **API key rotation mid-operation**: `publishedAfter` filter uses RFC 3339 — if API key rotated, timestamps may shift, causing duplicate re-ingestion

### People/Process
11. **No idempotency on `add`**: Re-running `add` for same channel re-enumerates all videos, creating duplicates in batch_status
12. **No rollback on `cmd_check` partial failure**: If `set_status_batch` fails after some inserts, `last_checked` is still updated — user thinks check succeeded
13. **`fasteners` import failure on fresh install**: Module not in pyproject.toml (only requirements.txt) — Docker builds without requirements.txt may fail

---

## Step 2.5: Cascade Traces (risks ≥6)

### Risk 2 (Orphaned Lock) → Risk 6 (WAL starvation)
1. Process A starts `cmd_sync`, acquires lock
2. Process A is kill -9'd while holding lock
3. Lock file `channel__youtube.com_channel_UCxxx.lock` persists
4. Process B starts `cmd_sync`, waits indefinitely for lock
5. **Deny of service** — terminal must be manually cleaned

### Risk 1 (Batch atomicity) → Risk 7 (No rollback)
1. `set_status_batch([...1000 entries...])` starts
2. Entry 501 has constraint violation (NULL video_id from malformed API response)
3. `INSERT OR REPLACE` throws exception
4. `rollback()` fires — 0 entries written
5. `upsert_channel(last_checked)` still fires in `cmd_check` caller
6. User believes 1000 videos were checked, but 0 were added
7. Next `check` sees no new videos, doesn't retry

### Risk 7 (`cmd_check` concurrent with `cmd_sync`)
1. Terminal A runs `cmd_check` — reads `pending_ids` = {vid1, vid2, vid3}
2. Terminal B runs `cmd_sync vid1` — marks vid1 complete
3. Terminal A's `gap_detected` calc uses stale `pending_ids` set
4. Gap detection decision is wrong (false positive or false negative)

---

## Step 2.6: AI/LLM Failure Modes

- Context window overflow during large channel import (>10K videos) could cause `enumerate_full` to silently truncate
- LLM-generated `publishedAfter` filter value might not be RFC 3339 compliant, causing API to reject it
- In `detect_gap`, the `newest_batch_published` datetime could drift if server timezone changes

---

## Step 2.7: Temporal Failure Modes

- **`_GAP_TRIGGER_DAYS_OLD = 7`** — This constant was set during initial design. If channel has very low upload frequency (1 video/month), 7 days is too aggressive — gap detection fires on every `check`
- **`cmd_add` re-enumeration**: If `add` is run twice, no idempotency — `enumerate_full` re-fetches all videos and creates new pending entries alongside old ones
- **Lock file TTL**: No TTL on `fasteners` lock files — if lock holder crashes, no auto-cleanup

---

## Step 3: Categorization

| ID | Category |
|----|----------|
| 1, 6, 7 | Tech |
| 2, 3, 4, 5 | Tech/External |
| 8, 9, 10 | External |
| 11, 12, 13 | Process |

---

## Step 4: Risk Ratings (L × I = Score)

| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| 2 | Orphaned lock → permanent DoS | 2 | 3 | **6** |
| 1 | Batch atomicity trap → 0 rows written | 3 | 3 | **9** |
| 7 | cmd_check/concurrent TOCTOU → wrong gap decision | 2 | 3 | **6** |
| 3 | Hardcoded `P:/__csf/` path fails | 2 | 2 | **4** |
| 4 | `is_complete` skips failed videos → re-queue | 2 | 2 | **4** |
| 5 | Gap videos re-added despite being pending | 2 | 2 | **4** |
| 6 | WAL reader starvation | 1 | 3 | **3** |
| 8 | API quota exhaustion mid-enum | 2 | 2 | **4** |
| 9 | RSS disabled → silent miss | 1 | 2 | **2** |
| 10 | API key rotation → re-ingestion | 1 | 2 | **2** |
| 11 | No idempotency on `add` | 2 | 2 | **4** |
| 12 | No rollback on partial failure | 3 | 3 | **9** |
| 13 | `fasteners` not in pyproject.toml | 2 | 2 | **4** |

---

## Step 4.5: Dependency Cascades

- **RISK-1** (atomicity trap) `[causes: RISK-12]` (no rollback) — they are the same root cause (batch atomicity + no compensation)
- **RISK-2** (orphaned lock) `[causes: RISK-6]` (WAL reader starvation in worst case)

---

## Step 5: Top 3 Risks → Actions

**RISK-1/12 (L3×I3=9): Batch atomicity + no rollback**
- Fix: Wrap each entry in TRY-EXCEPT inside the transaction; commit per-entry (fire-and-forget with best-effort)
- OR: Add a `set_status_batch_best_effort` that catches per-entry errors and continues

**RISK-2 (L2×I3=6): Orphaned lock**
- Fix: Use `fasteners.InterProcessLock` with `lockfile_timeout` parameter (pass to constructor); if can't acquire in N seconds, raise instead of block forever

**RISK-7 (L2×I3=6): cmd_check/concurrent TOCTOU**
- Fix: Add `BEGIN IMMEDIATE` transaction around the `gap_detected` decision block in `cmd_check` — serialize read of `pending_ids` + decision + write

---

## Step 6: Warning Signs

- Lock files accumulating in `P:/__csf/.data/intelligence-stream/locks/` after crashes
- `cmd_check` reports 0 new videos but RSS shows 15+
- `cmd_sync` hangs with no output for >5 minutes
- `add` run twice → pending count doubles

---

## Step 7: Adversarial Validation

*Dispatched 8 agents in parallel — see evidence files*
