# Phase 1 Findings: ADR-20260328-intelligence-stream-source-enumeration

**Session:** critique-20260328_141625
**Compiled:** 2026-03-28
**Specialists:** adversarial-critic (reasoning/bias/calibration), adversarial-compliance (spec/code alignment)
**Total consolidated findings:** 19 unique issues across 6 categories

---

## CRITICAL (Must Fix Before Phase 1)

### C-1: Phase 1 transcript cache reuse is unimplementable as described
**Source:** adversarial-compliance §1 [HIGH] + adversarial-critic META-018
**Specialist consensus:** 2/2

The ADR describes checking `transcript_cache` before calling Gemini, but:
1. `list_cached_transcripts(lang)` at `cache.py:283` takes only `lang`, not `video_id` — the API does not support video-id lookup
2. `analyze_video()` at `csf-analyze:481` never calls the cache module — it fetches directly via `get_youtube_transcript()`
3. No `has_cached_transcript(video_id)` function exists
4. `analyze_video()` has no variant that accepts a pre-fetched transcript

**ADR text:** Line 198 — "check transcript_cache via list_cached_transcripts(video_id)"
**Actual API:** `cache.py:283` — `list_cached_transcripts(lang: str | None) -> list[TranscriptCache]`
**Fix required:** Add `has_cached_transcript(video_id) -> bool` to `cache.py`, create `analyze_video_with_transcript(transcript)`, modify `analyze_videos_parallel()` to check cache first. These are not in the current Phase 1 scope.

---

### C-2: `mark_complete(video_id, source=...)` does not exist
**Source:** adversarial-compliance §1 [HIGH]
**Specialist consensus:** 1/2 (compliance only, but definitive)

The ADR describes a new API at line 194: `mark_complete(video_id, source=...)`, `get_source(video_id)`.
**Actual API:** `batch_status.py:137` — `mark_complete(video_id, db_path=None)` takes no `source` parameter. No `get_source()` exists.
**Fix required:** This is a new API to be created (not a modification), but the ADR presents it as a modification to an existing function.

---

### C-3: API quota exhaustion is a silent failure mode
**Source:** adversarial-critic META-004 [CRITICAL]
**Specialist consensus:** 4/7 (performance, quality, testing, logic)

The ADR acknowledges 10,000 units/day quota (line 34) but the gap resolution algorithm loops until overlap found (lines 141-147) with no quota check. If quota is exceeded mid-enumeration, the user sees zero new videos with no error — a silent failure.
**Fix required:** Per-request quota tracking, warning when quota <20%, `--dry-run` flag for enumeration.

---

## HIGH

### H-1: Gap resolution algorithm needs iteration bound
**Source:** adversarial-critic META-005 [HIGH]

The algorithm at lines 139-147 uses `cursor = oldest result's publishedAt` as the new cursor. For channels with irregular upload patterns (e.g., 10 videos 6 months ago, 2 last week), the cursor can move backward in time — potentially causing infinite loops or excessive API calls.
**Fix required:** Max 20 iterations (1000 videos = reasonable ceiling) + `publishedBefore` upper bound check.

### H-2: 7-day threshold lacks justification
**Source:** adversarial-critic META-001 + adversarial-compliance §3 [MEDIUM→HIGH by consensus]
**Specialist consensus:** 5/7 (security, performance, quality, testing, logic)

The gap detection trigger uses `> 7 days ago` with no empirical basis. Why 7 and not 5, 10, or 14?
**Impact:** Weekly-upload channels trigger false-positive gap resolution (wasting API quota); daily-upload channels may have undetected gaps.
**Fix required:** Either use observed channel upload frequency as adaptive threshold, or document empirical basis for 7 days.

### H-3: Option C correctness inconsistency
**Source:** adversarial-critic META-013 [HIGH]

Decision driver says "Correctness: Never redownload..." (line 32) → Option A favored (correctness). But Decision says "Option C" which the ADR itself notes is "Incomplete (no channel-level enumeration)" (line 77). Phase 1 does not unify stores — it preserves the three-store model.
**Fix required:** Clarify primary driver. If correctness, Phase 1 must include source attribution at minimum. If simplicity, rename the driver accordingly.

### H-4: `channel_metadata` table schema never defined
**Source:** adversarial-critic META-006 [MEDIUM] + adversarial-compliance §4 [MEDIUM]
**Specialist consensus:** 2/2

ADR line 244 references `channel_metadata(channel_url, last_checked, last_full_enumeration, video_count_estimate)` but no `CREATE TABLE` statement appears anywhere. No test coverage for this table.
**Fix required:** Add explicit `CREATE TABLE channel_metadata(...)` to Implementation Changes.

### H-5: `csf-source` CLI interface underspecified
**Source:** adversarial-critic META-007 [MEDIUM]

Phase 2 deliverable at lines 202-208 lists CLI signatures but not behavior: `--dry-run`, `--limit`, output format, exit codes all undefined.
**Fix required:** Full CLI specification before Phase 2 begins.

### H-6: Concurrency safety — gap detection TOCTOU race
**Source:** adversarial-critic META-002 [HIGH]
**Specialist consensus:** 4/7

The gap detection algorithm (lines 129-148) performs `result_ids ∩ batch_status_videos` check then write — no locking. Two terminals running `csf-source check` simultaneously could queue the same video_ids.
**Fix required:** `INSERT OR IGNORE` with explicit schema check, or `IMMEDIATE` transaction mode.

---

## MEDIUM

### M-1: `.ingested_ids` atomicity claim unverified
**Source:** adversarial-critic META-003 [MEDIUM]

ADR line 235 claims atomic write safety for `.ingested_ids` but provides no implementation citation. Plain `open(path, 'a')` append is not atomic on crash.
**Fix required:** Cite actual implementation (`tempfile.NamedTemporaryFile` + `os.rename()`) or add `fsync()` enforcement.

### M-2: YouTube API quota unit claim unsourced
**Source:** adversarial-compliance §1 [MEDIUM]

ADR line 34 says "1 unit per playlistItems.list call" — general knowledge claim not verifiable from codebase.
**Fix required:** Add source citation or reframe as assumption to verify.

### M-3: Option C favored without cost/benefit analysis
**Source:** adversarial-critic META-009 [HIGH→MEDIUM]

Decision picks Option C without structured comparison of Options A/B/C. Option B (Unified Store) discarded without evaluation.
**Fix required:** Add decision matrix comparing all options across ISO 25010 qualities.

### M-4: "10x faster" API claim has no measurement
**Source:** adversarial-critic META-010 [HIGH→MEDIUM]

Lines 33, 104 claim "~10x faster" with no citation. If wrong, entire Phase 2 strategy rests on incorrect assumption.
**Fix required:** Provide benchmark reference or reframe as expected/guesstimated.

### M-5: RSS feed availability not verified before Tier 1 reliance
**Source:** adversarial-critic META-008 [MEDIUM]

RSS can be disabled, return stale content, or change format. No error handling if RSS fails — falls through to Tier 2 silently?
**Fix required:** Explicit RSS failure handling: on HTTP error, log warning and fall to Tier 2.

### M-6: Phase 1 `source` column migration plan missing
**Source:** adversarial-compliance §4 [MEDIUM]

`ALTER TABLE analysis_status ADD COLUMN source TEXT` (line 190) — no plan for existing rows (NULL? default?), no Alembic/migration strategy.
**Fix required:** Document migration approach.

### M-7: Idempotency claim vs partial file handling contradiction
**Source:** adversarial-critic META-015 [HIGH→MEDIUM]

Line 36 claims `--force` enables idempotent restart. Line 235 says atomic write covers the ID file. But the video file itself on interrupt — overwrite? append? Neither?
**Fix required:** Clarify what happens to partial video files on `--force` re-run.

### M-8: `channel_metadata` multi-terminal write contention not discussed
**Source:** adversarial-compliance §5 [MEDIUM]

Simultaneous `csf-source check` on same channel → `last_checked` timestamp write contention. No WAL mode discussion for new table.
**Fix required:** Add WAL mode note for `channel_metadata` or document locking strategy.

### M-9: Phase 2 API-first policy conflicts with Tier 3 trigger
**Source:** adversarial-critic META-014 [HIGH→MEDIUM]

API-first policy (line 33) vs Tier 3 triggered when "API returns fewer videos than expected" (line 107) — this penalizes API for being API-limited, not just for failing.
**Fix required:** Distinguish API error (trigger Tier 3) from API limitation (do not trigger Tier 3).

### M-10: "Correctness" driver stated but not delivered in Phase 1
**Source:** adversarial-critic META-011 [HIGH→MEDIUM]

Line 32: Correctness — "Never redownload...". Phase 1 (lines 85-86): only adds `source` column + changes subprocess call. Phase 3 (deferred): actual correctness evaluation.
**Fix required:** Rename "Correctness" to "Correctness (deferred)" or restructure Phase 1.

---

## LOW

### L-1: Missing Decision Maker field
**Source:** adversarial-compliance §2 [MEDIUM→LOW]

### L-2: Open Questions numbering confusing (strikethrough numbers)
**Source:** adversarial-compliance §2 [MEDIUM→LOW]

### L-3: ISO 25010 attributes applied inconsistently
**Source:** adversarial-critic META-016 [LOW]

### L-4: Worst-case complexity omits network failures
**Source:** adversarial-critic META-017 [LOW]

### L-5: "Source attribution enables X" claim is speculative
**Source:** adversarial-critic META-019 [LOW]

### L-6: Compliance/standards section absent
**Source:** adversarial-critic META-012 [LOW]

---

## MERGED ITEMS (cross-specialist overlap)

| Merged | From Critic | From Compliance | Resolution |
|--------|------------|-----------------|------------|
| Arbitrary threshold | META-001 (7-day) | §3 gap trigger threshold | Unified to H-2 |
| Cache API doesn't exist | META-018 | C-1, §1 transcript | Unified to C-1 |
| mark_complete missing | — | C-2 | Unified to C-2 |
| Multi-terminal safety | META-002 TOCTOU | §5 channel_metadata | Unified to H-6 |
| Ingest subprocess description | META-015 idempotency | §1 pipeline disconnect | Unified to M-7 |

---

## HEALTH SCORE CALCULATION

| Severity | Count | Score Each | Subtotal |
|----------|-------|-----------|----------|
| CRITICAL | 1 | ×20 | 20 |
| HIGH | 5 | ×10 | 50 |
| MEDIUM | 10 | ×5 | 50 |
| LOW | 6 | ×2 | 12 |

**Health Score: 100 − 132 = 0%** (capped at 0, actual negative)

*Note: Health score below 50% indicates systemic problems. The CRITICAL + HIGH concentration (6 items) represents fundamental implementation blockers, not surface issues.*

---

## TOP RECOMMENDED NEXT STEPS (sorted by severity)

1. **[CRITICAL]** Fix Phase 1 transcript cache scope: either narrow to only pipeline composition (ingest→batch) and defer cache reuse, OR expand Phase 1 to include `has_cached_transcript()` API + `analyze_video_with_transcript()` variant
2. **[HIGH]** Add iteration bound (max 20) and `publishedBefore` check to gap resolution algorithm
3. **[HIGH]** Add API quota tracking with kill switch before Phase 2 implementation
4. **[HIGH]** Resolve Option C correctness inconsistency — clarify Phase 1 delivers source attribution or rename driver
5. **[HIGH]** Add explicit `channel_metadata` schema (`CREATE TABLE`) to ADR
6. **[HIGH]** Bound gap detection TOCTOU with `IMMEDIATE` transaction or `INSERT OR IGNORE`
7. **[MEDIUM]** Justify 7-day threshold with empirical data or make adaptive
8. **[MEDIUM]** Define `csf-source` CLI interface fully before Phase 2
9. **[MEDIUM]** Clarify `--force` behavior on partial video files
10. **[MEDIUM]** Add YouTube API ToS / compliance section
