# ADR-20260328: Intelligence Stream Source Enumeration and Unified Deduplication

**Status**: Accepted
**Date**: 2026-03-28
**Decision Maker**: bruce (solo developer)
**Source**: Architecture analysis — intelligence-stream pipeline gap analysis

## Context

The intelligence-stream pipeline has two separate entry points that are not composed:

| Entry Point | Deduplication Store | Calls |
|-------------|---------------------|-------|
| `csf-ingest` | `~/Downloads/intelligence-stream/.ingested_ids` (flat file) | `csf-analyze` sequentially via `subprocess.run()` |
| `csf-batch` | `P:/__csf/.data/intelligence-stream/batch_status/batch_status.sqlite` | `analyze_videos_parallel()` (ThreadPoolExecutor) |

Additionally, `transcript_cache.sqlite` provides a third deduplication layer for transcript text.

**Three separate stores, no unified view, and ingest bypasses batch processing entirely.**

The question driving this ADR: what is the optimal way to enumerate YouTube content sources (channels, playlists, user-provided lists), and how should deduplication across all three stores be unified?

## Problems

1. **Pipeline disconnect**: `csf-ingest --analyze` calls `csf-analyze` sequentially as a subprocess, not `analyze_videos_parallel()`. A video ingested via ingest can be re-analyzed via batch with no cross-notification.

2. **No source tracking**: `batch_status` only stores `(video_id, status, updated_at)`. It cannot answer "which channel did this video come from?" or "what new videos are available in channel X since last check?"

3. **Redundant work**: If a video has a cached transcript in `transcript_cache`, running `analyze_videos_parallel()` still calls Gemini for summarization without reusing the cached transcript.

## Decision Drivers

- **Correctness (deferred Phase 3)**: Never redownload, retranscribe, or re-analyze what has already been done — fully addressed in Phase 3 unified store
- **Performance**: YouTube Data API is ~10x faster than `yt-dlp` for enumeration; use API as primary, `yt-dlp` only as fallback for cookie-gated content
- **Cost**: YouTube Data API has quota limits (10,000 units/day); initial full import + daily checks should stay well within quota (1 unit per `playlistItems.list` call)
- **Multi-terminal safety**: All stores already use SQLite WAL mode — must preserve this
- **Idempotent restart**: Both pipelines already support `--force`; must preserve this

## Options

### Option A: Federated Stores with Registry (Status Quo + Light Unification)

Keep all three stores, add a `source_registry` SQLite table that maps `source_id → set of video_ids`, and add a new `csf-source` CLI for channel/playlist enumeration. Batch and ingest check all three stores before processing.

```
csf-source check <channel_url>
  → YouTube Data API or yt-dlp enumeration
  → for each video_id not in batch_status:
       batch_status.mark_pending(source_id=channel_url)
  → csf-batch picks up pending videos

csf-ingest --analyze
  → for each video_id not in .ingested_ids:
       download + csf-batch (NOT sequential csf-analyze subprocess)
```

**Favored quality**: Correctness (explicit source attribution), operational flexibility (per-source status)
**Degraded quality**: Complexity (4 stores instead of 3)
**Failure conditions**: Source registry gets stale if API enumeration fails mid-way
**ISO 25010**: +Maintainability (clear source lineage), +Reliability (per-source restart), -Portability (one more DB to manage)

### Option B: Unified Store — Collapse into `batch_status` as Source of Truth

Eliminate `.ingested_ids` and `transcript_cache` as separate deduplication surfaces. Extend `batch_status` to be the single store tracking: `video_id, status, source, updated_at, transcript_cached, analysis_result_id`.

Keep `transcript_cache.sqlite` for actual transcript storage (it already exists), but add a `transcript_available(video_id)` lookup on it before starting Gemini analysis.

**Favored quality**: Simplicity (one authoritative store for video-level deduplication), strong consistency
**Degraded quality**: Rigidity (single store handles both download tracking and analysis tracking — different write frequencies)
**Failure conditions**: If batch_status DB is corrupted, lose both download and analysis history
**ISO 25010**: +Maintainability (one store to reason about), +Reliability (single checkpoint), -Performance Efficiency (single DB under more write pressure)

### Option C: Pipeline Composition — Ingest Calls Batch Directly

Keep all stores, but fix `csf-ingest --analyze` to call `analyze_videos_parallel()` in-process instead of spawning `csf-analyze` sequentially. Add `source` column to `batch_status` for channel attribution. No separate source registry — rely on batch_status's existing `status='complete'` skip logic.

**Favored quality**: Correctness (ingest and batch unified through same status store), minimal new surface area
**Degraded quality**: Incomplete (no channel-level enumeration — still relies on user-provided lists or manual API calls)
**Failure conditions**: Without a source registry, "re-check this channel for new videos" requires re-enumerating the entire channel each time
**ISO 25010**: +Reliability (single status path), +Performance Efficiency (no new store), -Operational Excellence (no source-level monitoring)

## Decision

**Option C for immediate fix, Option B for Phase 3.**

**Phase 1 (now)**: Fix the pipeline composition — `csf-ingest --analyze` calls `analyze_videos_parallel()` in-process, not sequential subprocess. Add `source` column to `batch_status`. This eliminates the most costly problem (redundant Gemini calls on already-analyzed videos).

**Phase 2 (later)**: Build `csf-source` CLI with channel/playlist enumeration. Use YouTube Data API for all enumeration (faster than `yt-dlp`). RSS for daily incremental checks. API gap-resolution with `publishedAfter` cursor for detecting ceiling gaps.

**Phase 3 (deferred)**: Unified store — extend `batch_status` to be the single authoritative store for video-level deduplication. Collapse `.ingested_ids` and `transcript_cache` deduplication checks into `batch_status` as pre-flight. Add `channel_metadata` table for per-channel state. Transcript storage remains in `transcript_cache.sqlite` (separate from batch_status).

### Phase 2 Enumeration Strategy (Three-Tier)

**Tier 1 — RSS (daily monitoring, free, stateless)**
- URL: `https://www.youtube.com/feeds/videos.xml?channel_id=UC...`
- Returns ~15-20 most recent videos sorted by `published` descending
- Sufficient for daily "what's new since last check?"
- **Ceiling problem**: If channel has 500 videos and you haven't checked in a month, RSS only shows the 15 most recent — gap invisible from RSS alone

**Tier 2 — YouTube Data API with `publishedAfter` cursor (gap resolution, API-key-required)**
- `channels.list` with `contentDetails.relatedPlaylists.uploads` → `UU...` upload playlist ID
- `playlistItems.list` with `playlistId=<upload_playlist_id>`, `maxResults=50`, `publishedAfter=<timestamp>`, `order=date`
- Returns videos in reverse chronological order from the cursor point
- **Overlap detection is the gap boundary**: fetch 50 most recent → if zero overlap with `batch_status`, gap is ≥50 → fetch next 50 using oldest result's `publishedAt` as new cursor → repeat until overlap found
- Preferred over `yt-dlp` for initial import and gap resolution due to ~10x performance

**Tier 3 — `yt-dlp --flat-playlist` (full enumeration fallback, cookie-dependent)**
- Enumerates every video without downloading
- Required for age-restricted / members-only content that API cannot see (cookie-gated)
- Last resort when API returns fewer videos than expected

#### Gap Detection Trigger

```
IF RSS returns 15 non-overlapping video_ids
   AND channel's newest_downloaded_video.publishedAt > 7 days ago:
    → trigger API gap resolution
ELSE:
    → process RSS videos normally (no gap suspected)
```

**Why the 7-day guard?** If newest downloaded video is from 2 days ago and RSS shows 15 non-overlapping, that could just mean the channel uploaded 3 times in 2 days — normal processing suffices. If newest is 3 months old, the gap is structural and gap resolution is warranted.

#### API Gap Resolution Algorithm

```
INPUT: channel_upload_playlist_id, batch_status_videos (already downloaded)
OUTPUT: list of new video_ids not yet in batch_status

1. cursor = <publishedAt of newest video already in batch_status for this channel>
   (if no existing videos, cursor = epoch)

2. REPEAT (max 20 iterations to bound API quota usage):
     results = playlistItems.list(
         playlistId=channel_upload_playlist_id,
         maxResults=50,
         publishedAfter=cursor,
         order="date"
     )
     result_ids = {v.videoId for v in results.items}

     IF result_ids ∩ batch_status_videos ≠ ∅:
         # Overlap found — gap boundary reached
         RETURN new_ids (all previous result_ids not in batch_status)
     ELSE:
         # No overlap — keep fetching
         cursor = <oldest result's publishedAt>
         CONTINUE
     END
```

**Complexity**: Each iteration fetches 50 videos. Worst case for a channel with 500 videos and no overlap (gap = 500) = 10 API calls. At 1 quota unit per call, ~10 units total.

#### Initial Import (First Time Adding a Channel)

Full pagination via API with `nextPageToken`:
```
1. channels.list(part="contentDetails", id=<channel_id>)
   → extract contentDetails.relatedPlaylists.uploads (UU... playlist)

2. playlistItems.list with pagination (maxResults=50, repeat with nextPageToken)
   → collect ALL video_ids until nextPageToken is null

3. For each video_id:
     batch_status.set_status(video_id, "pending", source=channel_url)
```

No RSS, no gap detection — get the complete history in one pass.

## Consequences

**Positive:**
- Ingest pipeline reuses batch's idempotency (skip already-complete videos)
- Source attribution enables "sync channel X for new videos" without full re-enumeration
- Transcript cache reuse: `analyze_video()` checks `transcript_cache` before calling Gemini
- API-first enumeration is ~10x faster than `yt-dlp` for initial import
- `publishedAfter` cursor makes gap detection precise — no arbitrary pagination

**Negative:**
- Requires DB migration to add `source` column and `channel_metadata` table to `batch_status`
- `csf-source` Phase 2 requires YouTube Data API key — user has this in `.env`

**Mitigation for cookie-gated content:**
- `yt-dlp --cookies-from-browser` used as Tier 3 fallback only
- API gap resolution may still miss age-restricted videos — acceptable within quota budget

## Implementation Changes

### Phase 1 (Minimal)

1. **`csf/batch_status.py`**: Add `source` column to `analysis_status` table:
   ```sql
   ALTER TABLE analysis_status ADD COLUMN source TEXT;
   ```
   New public API: `mark_complete(video_id, source=...)`, `get_source(video_id)`.

2. **`bin/csf-ingest`**: Replace sequential `subprocess.run([python, csf-analyze, ...])` loop with in-process call to `analyze_videos_parallel()`. Remove the `--analyze` subprocess loop entirely.

3. **`csf/batch.py`**: Before calling Gemini for summarization, check `transcript_cache` via `has_cached_transcript(video_id)`. If True, call `analyze_video(..., mode="transcript")` to reuse the cached transcript directly, skipping the expensive Gemini API call. This avoids redundant Gemini calls on videos already in the transcript cache.

### Phase 2 (`csf-source` CLI — New)

4. **`bin/csf-source`** (new file):
   ```
   csf-source add <channel_url_or_playlist_url>   # initial import: full API pagination
   csf-source list
   csf-source check <source_id>                   # daily: RSS → gap detection → API if needed
   csf-source sync <source_id>                    # process all pending videos via batch
   ```

5. **`csf/source_enumerator.py`** (new module):
   - `get_upload_playlist_id(channel_url) -> playlist_id` via `channels.list` API
   - `enumerate_full(playlist_id) -> list[video_id]` via `playlistItems.list` with pagination (initial import)
   - `enumerate_recent(playlist_id, published_after: datetime) -> list[video_id]` via API with `publishedAfter` cursor (gap resolution)
   - `check_rss(channel_url) -> list[video_id]` via `https://www.youtube.com/feeds/videos.xml?channel_id=...`
   - `detect_gap(rss_ids, batch_status_ids) -> bool` — true if RSS has ≥15 non-overlapping IDs and newest batch_status video > 7 days old

   **`channel_metadata` table** (in `batch_status.sqlite`):
   ```sql
   CREATE TABLE channel_metadata (
       channel_url TEXT PRIMARY KEY,
       playlist_id TEXT,
       last_checked TEXT NOT NULL,          -- ISO timestamp of last RSS/API call
       last_full_enumeration TEXT,           -- ISO timestamp when initial import finished
       video_count_estimate INTEGER DEFAULT 0,
       next_page_token TEXT,                 -- for resuming interrupted API pagination
       quota_exhausted_at TEXT              -- ISO timestamp if quota hit mid-enumeration
   );
   ```

### Test Matrix

| Test | Coverage | How Run |
|------|----------|---------|
| `test_batch_source_attribution` | Phase 1: source column written/read correctly | `pytest tests/test_batch_status.py` |
| `test_ingest_calls_batch_not_subprocess` | Phase 1: verify in-process call path | `pytest tests/test_ingest.py` |
| `test_source_enumerator_api` | Phase 2: video enumeration via API | Mock API responses |
| `test_source_enumerator_yt_dlp` | Phase 2: `yt-dlp --flat-playlist` fallback | Mock subprocess |
| `test_rss_new_videos` | Phase 2: RSS returns only new videos | Mock HTTP responses |
| `test_batch_respects_transcript_cache` | Phase 1: skip Gemini if transcript cached | `pytest tests/test_batch.py` |

## Assumptions and Defaults

- **API key**: User has `YOUTUBE_API_KEY` in `.env` — used for Phase 2 API enumeration. `YOUTUBE_API_KEY` env var read at runtime.
- **API-first for enumeration**: YouTube Data API is the primary enumeration method (faster than `yt-dlp`). `yt-dlp` reserved for cookie-gated content that API cannot see.
- **RSS ceiling**: RSS returns at most ~15-20 recent videos. Gap trigger requires ≥15 non-overlapping AND `newest_batch_status_video.publishedAt > 7 days`.
- **`publishedAfter` cursor**: API gap resolution uses `publishedAfter` with the `publishedAt` of the newest already-downloaded video as lower bound — not arbitrary pagination. Each batch = 50 videos (API max).
- **Cookies**: `yt-dlp --cookies-from-browser` required for age-restricted/members-only content. Gracefully degrades — API gap resolution fills what cookies can enumerate.
- **Partial downloads**: If `csf-ingest` is interrupted mid-download, `.ingested_ids` is not updated (atomic write only on full success). Safe to re-run.
- **Quota exhaust mid-enumeration**: If YouTube Data API quota (10,000 units/day) is exhausted mid-enumeration, `csf-source` logs the last successful `nextPageToken` cursor and aborts. The next run resumes from the saved cursor. No videos are lost — the cursor persists in `channel_metadata.last_checked`. If no cursor was saved (quota hit on first call), the channel is flagged and must be retried tomorrow.
- **Idempotency**: `csf-batch --force` always works regardless of store state.

## Closed Questions

1. ~~Should `transcript_cache` be checked before calling `analyze_videos_parallel()`...~~ **Closed**: Check `transcript_cache` in `batch.py` before starting Gemini; if cached, skip Gemini call. The transcript is already fetched via `fetch_transcript_chain()` which checks cache first — the gap is that Gemini summarization still runs even when transcript is cached. Phase 1 adds a pre-flight check in `batch.py` that passes a flag to avoid redundant Gemini calls when transcript is already available.

2. ~~Should `.ingested_ids` be replaced entirely, or kept as a "download complete" marker?~~ **Closed**: Keep `.ingested_ids` as a separate "file downloaded" signal but stop checking it for deduplication — `batch_status` becomes the authoritative store. The `.ingested_ids` ledger persists for backward compatibility with existing workflows.

3. ~~For Phase 2, store last-checked timestamps per channel?~~ **Closed**: Add `channel_metadata(channel_url, last_checked, last_full_enumeration, video_count_estimate)` table to `batch_status` SQLite. `last_checked` is updated after every RSS/API call. `last_full_enumeration` is set only after initial import completes. `video_count_estimate` is updated after full reconciliation to enable gap detection heuristics.

## See Also

- `csf/batch.py` — parallel batch processing
- `csf/batch_status.py` — batch status tracking
- `csf/cache.py` — transcript cache with WAL mode
- `bin/csf-ingest` — current ingest CLI (bypasses batch)
- `bin/csf-batch` — current batch CLI
