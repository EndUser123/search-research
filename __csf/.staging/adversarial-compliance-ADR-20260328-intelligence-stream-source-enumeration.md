# Adversarial Compliance Review: ADR-20260328-intelligence-stream-source-enumeration

**Reviewed:** `P:/__csf/arch_decisions/ADR-20260328-intelligence-stream-source-enumeration.md`
**Date:** 2026-03-28
**Reviewer:** adversarial-compliance specialist

---

## 1. Spec Alignment (ADR claims vs actual code)

### [HIGH] Phase 1 transcript cache check cannot work as described

**ADR line 198** says: "Before calling Gemini for summarization, check `transcript_cache` via `list_cached_transcripts(video_id)`."

**Evidence against this claim:**
- `cache.py:283-325` -- `list_cached_transcripts(lang)` takes only a `lang` parameter, NOT `video_id`. There is no overload that accepts `video_id`.
- To query by `video_id`, one must use `get_cached_transcript(video_id, lang, source)` at line 219, but this requires knowing both `lang` and `source` -- which are not known before fetching the transcript.
- `analyze_video()` in `csf-analyze:481-561` has no integration with `cache.py` whatsoever. It calls `get_youtube_transcript(video_id)` directly at lines 342-363, which fetches fresh from `youtube_transcript_api` every time, completely bypassing the cache.
- The `cache.py` module is a standalone system that is never invoked during video analysis.

**Impact:** The Phase 1 fix description assumes `list_cached_transcripts(video_id)` exists and that `analyze_video()` checks it. Neither is true. The implementation task as written cannot be completed as described without first adding a video_id lookup to the cache module and integrating the cache into the analysis chain.

### [HIGH] `mark_complete(video_id, source=...)` API does not exist

**ADR line 194** says: "New public API: `mark_complete(video_id, source=...)`, `get_source(video_id)`"

**Evidence against this claim:**
- `batch_status.py:137-142` -- `mark_complete(video_id, db_path=None)` only takes `video_id`, no `source` parameter.
- `batch_status.py:117-124` -- No `get_source(video_id)` function exists.
- The table schema at lines 59-65 has no `source` column.

**Impact:** The Phase 1 implementation changes cannot be tested as described because the API it describes does not exist yet. This is expected for a Phase 1 design, but the ADR presents these as if they are modifications to existing APIs rather than new APIs to be created.

### [MEDIUM] Pipeline disconnect claim is accurate but description is incomplete

**ADR lines 24, 52-53** describe the `--analyze` subprocess loop and say "csf-batch (NOT sequential csf-analyze subprocess)" as the fix.

**Verification:** `csf-ingest:114-139` confirms the sequential subprocess loop. However, the ADR does not note that `csf-ingest` calls itself via `subprocess.run()` with `--url` and `--cks` flags, not `csf-analyze` directly. This is a subtle distinction -- the CLI being invoked is `csf-ingest`, not `csf-analyze`. The fix would need to call `analyze_videos_parallel()` in-process, but this requires importing `batch.py` into the `csf-ingest` module, creating a new coupling.

### [MEDIUM] YouTube Data API quota claim is unverifiable

**ADR line 34** says: "(1 unit per `playlistItems.list` call)"

**Verification:** This is a YouTube Data API general knowledge claim, not verifiable from the codebase. The ADR provides no source citation for this. The claim should be verified against actual YouTube API documentation before being used as a decision driver.

### [LOW] `batch_status` DB path is accurately described

**ADR Table (line 11)** says: `batch_status` uses `P:/__csf/.data/intelligence-stream/batch_status/batch_status.sqlite`

**Verification:** `batch_status.py:22-23` confirms this path.

### [LOW] `.ingested_ids` location is accurately described

**ADR Table (line 11)** says: `csf-ingest` uses `~/Downloads/intelligence-stream/.ingested_ids` (flat file)

**Verification:** `csf-ingest:40,67` confirms: `output_dir = Path("~/Downloads/intelligence-stream").expanduser()` and `ingested_ids_file = output_dir / ".ingested_ids"`.

---

## 2. Completeness (ADR template compliance)

### [MEDIUM] Missing "Decision Maker" field

The project ADR template includes a **Decision Maker** field (confirmed in prior adversarial-compliance review of ADR-20260328-search-quality-improvements). This ADR omits it.

### [MEDIUM] Missing Open Questions section numbering

The ADR has an "Open Questions" section but the questions are numbered with crossed-out numbers (1, 2, 3 with ~~strikethrough~~). This is confusing -- it is unclear if these are closed or deferred.

### [LOW] Status is "Draft" -- appropriate for proposed work

The status is correctly marked "Draft" since no implementation has started. This is appropriate.

---

## 3. Contract Accuracy

### [HIGH] `transcript_cache` integration approach is fundamentally flawed

**ADR line 198** proposes: "check `transcript_cache` via `list_cached_transcripts(video_id)`"

The actual `cache.py` API at line 283:

```python
def list_cached_transcripts(lang: str | None = None) -> list[TranscriptCache]:
```

Takes `lang`, not `video_id`. There is no way to ask "is this video already cached?" without knowing the language. The ADR's Phase 1 approach requires a new API function: `has_cached_transcript(video_id: str) -> bool` which does not exist.

### [MEDIUM] Phase 1 says "avoid redundant Gemini calls" but Gemini is called regardless of cache state

**ADR Problem 3 (line 28)**: "If a video has a cached transcript in `transcript_cache`, running `analyze_videos_parallel()` still calls Gemini for summarization without reusing the cached transcript."

The `analyze_video()` function in `csf-analyze` (lines 506-537) calls Gemini in three different modes. Even in "auto" mode where it first tries CLI, if CLI succeeds, it returns immediately without checking the cache. The transcript cache is never consulted during the analysis chain. The problem statement is correct but the root cause is more fundamental -- the cache is simply not in the code path at all.

### [MEDIUM] Gap detection trigger condition has a threshold precision issue

**ADR lines 114-119** describe the gap detection trigger:

```
IF RSS returns 15 non-overlapping video_ids
   AND channel's newest_downloaded_video.publishedAt > 7 days ago:
    → trigger API gap resolution
```

**Analysis:** This uses "> 7 days" threshold. The ADR provides no justification for "7 days" specifically. Per the reasoning flaws principle (arbitrary thresholds), this should be explained: why 7 and not 5 or 10? The threshold matters because it determines when API gap resolution (which costs API quota) is triggered.

---

## 4. Implementation Plan Feasibility

### [HIGH] Phase 1 Task 2 requires a non-existent cache API

**ADR Implementation Changes, Phase 1, item 3 (line 198)**:
> "Before calling Gemini for summarization, check `transcript_cache` via `list_cached_transcripts(video_id)`. If any cached transcript exists, pass it directly to the analysis result instead of re-fetching."

**Feasibility issues:**
1. `list_cached_transcripts(video_id)` does not exist (see Section 1 above)
2. `analyze_video()` does not accept a pre-existing transcript as input -- its fallback chain (CLI → transcript → SDK) always fetches fresh content
3. The "pass it directly to the analysis result" step is undefined -- there is no `analyze_video_with_transcript()` variant

This task requires: (a) adding `has_cached_transcript(video_id)` or `list_cached_transcripts(video_id=None)` to `cache.py`, (b) creating `analyze_video_with_transcript()`, and (c) modifying `analyze_videos_parallel()` to use the cached variant. The ADR does not mention items (b) or (c).

### [HIGH] Phase 2 `csf-source` CLI is new ground -- no existing scaffold

**ADR item 4 (line 202)**: "bin/csf-source (new file)"

The Phase 2 work requires building a completely new CLI with channel/playlist enumeration. This is non-trivial and requires:
- YouTube Data API integration
- RSS feed parsing
- Gap detection algorithm implementation
- A new `source_enumerator.py` module

The ADR does not estimate the scope of Phase 2 or provide detail on the `source_enumerator.py` API beyond the method signatures.

### [MEDIUM] Phase 1 Task 1 requires adding `source` column without migration plan

**ADR Implementation Changes, Phase 1, item 1 (line 190)**: "ALTER TABLE analysis_status ADD COLUMN source TEXT"

Adding a column to an existing SQLite table with existing data requires a migration strategy. The ADR does not discuss:
- How to handle existing rows (NULL source? default value?)
- Whether this needs a Alembic/migration system or just a one-time SQL migration script
- Whether `batch_status` is ever accessed by other tools that would need updating

---

## 5. Multi-Terminal Safety Assessment

### [MEDIUM] New `channel_metadata` table in Phase 2 is not discussed for multi-terminal safety

**ADR Open Question 3 (line 244)** mentions adding a `channel_metadata(channel_url, last_checked, last_full_enumeration, video_count_estimate)` table.

If multiple terminals run `csf-source check` simultaneously on the same channel, the `last_checked` timestamp would be subject to write contention. The ADR does not discuss WAL mode for this table or whether it needs its own locking strategy.

### [LOW] Existing stores are correctly identified as WAL mode

**ADR line 35**: "All stores already use SQLite WAL mode"

Verified: `batch_status.py:56` and `cache.py:68` both use `PRAGMA journal_mode=WAL`. This is accurate.

### [LOW] `_get_batch_status_storage()` singleton pattern is process-local, not terminal-local

**ADR line 7**: "Multi-terminal safe: all terminals share the same DB with WAL mode."

This is accurate at the SQLite level -- multiple processes can share the same WAL-mode DB. However, the singleton pattern at `batch_status.py:34-41` uses a module-level `_batch_status_storage` global that is per-process. This is fine because each terminal launches its own Python process. No issue here, but the ADR could be clearer about the process boundary.

---

## Summary of Findings

| Severity | Count | Key Issues |
|----------|-------|------------|
| HIGH | 3 | Phase 1 transcript cache check uses non-existent API, Phase 1 mark_complete API does not exist, Phase 1 transcript integration requires undefined analyze variant |
| MEDIUM | 5 | Gap detection 7-day threshold unexplained, source column migration plan missing, channel_metadata multi-terminal not discussed, YouTube API quota claim unsourced, ingest subprocess description slightly inaccurate |
| LOW | 3 | Decision Maker field missing, Open Questions numbering confusing, transcript_cache module exists but is disconnected from analyze_video |

**Overall Assessment:** The ADR correctly identifies three real problems (pipeline disconnect, no source tracking, redundant Gemini work) and the high-level decision (Option C for immediate fix, Option A for full solution) is sound. However, the Phase 1 implementation details have critical gaps: the transcript cache API used in the implementation does not exist as described, the `mark_complete` API needs to be created not modified, and the analysis function chain would need a new variant. The ADR should be revised to either (1) add the missing cache API design to Phase 1, or (2) narrow Phase 1 to only the pipeline composition fix (ingest calling `analyze_videos_parallel()`) and defer the transcript cache reuse to a separate phase with proper API design.

---

*Findings citation: `batch_status.py:59-65, 117-142`, `batch.py:66-67`, `csf-ingest:114-139`, `csf-analyze:481-561, 342-363`, `cache.py:219-243, 283-325`*
