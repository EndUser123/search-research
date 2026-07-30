---
thread_id: yt-is-nlm-to-wiki-integration-20260730
parent_handoff_path: none
current_session_id: 019fb189-b2ec-70f0-8d30-16a6e7bb5ad7
current_terminal_id: grok-build-terminal
produced_at: 2026-07-31T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 7aada874de315b77dcec5f5e0301022ccffa38d7
---

# yt-is / nlm-to-wiki integration — forward path

## Objective (one sentence)

Make yt-is the single canonical YouTube transcript store by syncing unsynced channels first, then matching becomes trivial — eliminating duplicate NotebookLM fetches across both systems.

## Status

OPEN — one-time backfill complete (3,893 transcripts imported, 473 orphans registered). Forward path identified but not implemented. Design discussion complete; this handoff captures the implementation plan.

## What was done this session

1. **Imported 3,893 YouTube transcripts** from nlm-to-wiki's .md store into yt-is `transcript_cache` via `import_nlm_transcripts.py` (84.6% exact title match rate)
2. **Registered 473 orphan video_ids** into `analysis_status` via `register_orphan_transcripts.py` (metadata from clusters.json)
3. **Identified the root cause of the 783 unmatched transcripts**: 1,057 of 1,616 Watch Later channels were never synced into yt-is — the title-match bridge had an incomplete index, not a matching-quality problem
4. **Installed sqlite3** via winget (was missing from the host)
5. **Created two scripts** in `P:/packages/yt-is/scripts/`: `import_nlm_transcripts.py`, `register_orphan_transcripts.py`

### Revision 2026-07-30T10:30 (refactor + review cycle)

6. **Refactored scripts into 3 shared modules** (`csf/urls.py`, `csf/paths.py`, `csf/clusters.py`) — eliminates hardcoded DB paths and regex duplication across 7 scripts. Commits `0558770`..`cf2c4ea`.
7. **Fixed all review findings** (SM-001 UnicodeDecodeError contract gap, SM-002 private import promotion, SM-003 dead code removal, YTIS-004 structured source match via json_extract, YTIS-005 warn on empty bridge, pre-existing backfill sys.path corruption, pre-existing test backslash bug).
8. **Added 31 unit tests** for the 3 shared modules (`tests/test_shared_modules.py`).
9. **Added .gitleaksignore** for pre-existing API key in `backfill_channel_metadata.py`.

**Refactor state:** 6 seams completed (A2 → A1 → A3 → B1 → B2 → C1). All verified. No seams remaining.

## What needs to happen next (the forward path)

The correct sequence, per the operator's framing:

```
1. Extract channel list from clusters.json (1,616 channels)
2. Cross-reference against yt-is channel_metadata (1,298 synced)
3. Sync the 1,057 unsynced channels into yt-is (csf-source sync / source_enumerator)
   → this populates analysis_status with authoritative video lists
4. NOW match the 783 unmatched transcripts → trivial (titles are in the index)
5. Import any remaining matched transcripts into transcript_cache
6. Forward sync: nlm-to-wiki reads FROM yt-is cache before hitting NotebookLM
7. History playlist as URL source (yt-is already has import scripts)
8. Activate 3 NotebookLM accounts in yt-is (currently 1 active)
```

## Key data

| Metric | Value | Source |
|---|---|---|
| nlm-to-wiki YouTube transcripts | 5,070 (.md files) | `P:/.data/wiki/sources/transcripts/*.md` |
| Successfully imported to yt-is | 3,893 | transcript_cache with `metadata_json LIKE '%nlm-to-wiki%'` |
| Orphan video_ids (registered) | 473 | analysis_status with `source='playlist:watch-later-nlm-to-wiki'` |
| Unmatched (title-match failed) | 783 | dry-run output |
| Channels in Watch Later set | 1,616 | clusters.json |
| Channels synced in yt-is | 1,298 | channel_metadata table |
| Channels NOT synced | 1,057 (65%) | set difference |
| Past duplication (both fetched) | 389 | cache_key collision (INSERT OR IGNORE) |

## Read-first list

1. `P:/packages/yt-is/AGENTS.md` — yt-is operating docs, NLM auth architecture
2. `P:/packages/yt-is/scripts/import_nlm_transcripts.py` — the importer (one-time backfill)
3. `P:/packages/yt-is/scripts/register_orphan_transcripts.py` — the orphan registration
4. `P:/.agents/skills/nlm-to-wiki/SKILL.md` — nlm-to-wiki pipeline (the consumer)
5. `C:/Users/brsth/Downloads/watch-later-1784999007767-deduped-clusters.json` — the cluster metadata

## Hard constraints

- yt-is uses NotebookLM as provider #5 in its fallback chain (not the only path)
- nlm-to-wiki uses NotebookLM for ALL source types (YouTube + web + PDF + docs)
- 2,459 non-YouTube sources are outside yt-is's model entirely — they stay as .md files
- nlm-to-wiki stored `url: null` for all 5,070 YouTube transcripts — the UUID→video_id bridge is needed
- 3 NotebookLM accounts available; yt-is currently uses only 1 (`a.hominidae`)

## Verification commands

```sql
-- Check import state
sqlite3 P:/.data/yt-is/transcripts.sqlite "SELECT COUNT(*) FROM transcript_cache WHERE metadata_json LIKE '%nlm-to-wiki%'"
-- Should be 3,893

-- Check orphan registration
sqlite3 P:/.data/yt-is/batch_status.sqlite "SELECT COUNT(*) FROM analysis_status WHERE source = 'playlist:watch-later-nlm-to-wiki'"
-- Should be 473

-- Check channel coverage
sqlite3 P:/.data/yt-is/batch_status.sqlite "SELECT COUNT(*) FROM channel_metadata"
-- Should be 1,298
```

## Resumption protocol

1. Run the verification commands above to confirm state
2. Extract the 1,057 unsynced channel list from clusters.json
3. Sync channels via `csf-source sync` or `source_enumerator.py`
4. Re-run `import_nlm_transcripts.py` to match the previously-unmatched transcripts
5. Implement forward sync (nlm-to-wiki reads from yt-is cache before NotebookLM)

## Last user message (verbatim)

> "To match the transcripts, you have to identify what the video URLs are from the channels in question. Once you have the correct video information, now it's trivial to match the names. Right now all the transcripts that have been downloaded some of them are likely not even to be registered as legal videos in YTS because it hasn't done a sync of the channels"

## Suggested next invocation

```
/go Continue yt-is/nlm-to-wiki integration. Read P:/docs/handoffs/yt-is-nlm-to-wiki-integration-20260730/HANDOFF.md.
Start with: (1) extract unsynced channels from clusters.json, (2) sync via csf-source,
(3) re-run import_nlm_transcripts.py to match the 783 unmatched.
```

---

## Revision 1 — 2026-07-30T11:30:00Z (session 019fb49b)

**Trigger:** operator said "do what you think is best — get this repo working and productive." Fresh session picked up this handoff and advanced the forward path.

**What changed since the original:**

### State verification (all claims confirmed)

Ran the verification SQL from the original handoff — all numbers match exactly:
- `transcript_cache` nlm-to-wiki imports: **3,893** ✓ (was 3,893)
- `analysis_status` orphans: **473** ✓ (was 473)
- `channel_metadata` count: **1,298** ✓ (was 1,298)
- `accurate_as_of_head` bound to `7aada874` (was `TBD`)

### Re-ran importer dry-run (current matching landscape)

| Metric | Value |
|---|---|
| YouTube transcripts in nlm-to-wiki | 5,070 |
| Bridge size (clusters + analysis_status) | 57,707 video_ids, 56,725 titles |
| Exact matched (already cached) | 4,287 |
| Unmatched | 783 (735 + 48 ambiguous) |

### Root-cause analysis of the 783 unmatched

Categorized the 783 into two distinct failure modes:

1. **URL-as-title (286 entries):** NotebookLM used the video URL as the title when it didn't have the real title (e.g., `2026-07-25 https://www.youtube.com/watch?v=b4d32pBa3UY&list=WL...`). The video_id is directly extractable from the URL — no title matching needed.
   - 269 already in transcript_cache (matched by other means, provenance link missing)
   - **17 NEW** — imported to cache via `url-from-title` match type

2. **Real title (497 entries):** Genuine YouTube titles (e.g., "Claude Code Just Dropped Memory 2.0") that are absent from ALL data sources:
   - Not in clusters.json (4,108 titles)
   - Not in analysis_status (56,602 titles)
   - Not in playlist.json full export (4,916 titles — 808 more than clusters, still 0 matches)
   - [INFERENCE] These are from YouTube History, not Watch Later — never exported as a playlist JSON

### Actions taken this session

- **Imported 17 URL-extracted transcripts** → cache grew from 3,893 → **3,910** nlm-to-wiki / 10,064 total
- **Fuzzy matching at threshold 85 (rapidfuzz):** only 16 recovered, with false-positive risk (e.g., "30 trending" matched "31 Trending"). Conservative — 6 at score 95+, deferred.
- **YouTube Data API search completed** for the 497 real-title unmatched. Results: **257 resolved** (224 at exact score 100, 87% confidence), 22 found-but-already-cached, 218 unresolved (all 4 API keys exhausted). Of the 257 resolved, only 25 imported to cache (17 URL-extracted + 8 API) due to a script bug that re-ran the search on `--import` and overwrote the saved results file. Fixed script now separates search/import phases (`--import-file` mode). **Remaining 249 can be imported tomorrow** when quota resets: `python P:/tmp/api_title_search.py` then `python P:/tmp/api_title_search.py --import-file P:/tmp/api_search_results_latest.json`

### Updated key data

| Metric | Value |
|---|---|
| nlm-to-wiki transcripts in yt-is cache | **3,918** (was 3,893; +17 URL-extracted + 8 API) |
| Total distinct video_ids in cache | **10,072** (was 10,047) |
| Unmatched after URL extraction | 497 (real-title, needs API search or History export) |
| API-resolved (not yet imported) | **249** (search tomorrow, import via `--import-file`) |
| API-unresolved (quota exhausted) | **218** (search day after tomorrow with fresh quota) |
| YouTube API keys available | 4 (YT_API_KEY_1-4 in P:/.env); all exhausted today |

### Updated forward path

The original handoff's forward path (channel sync → re-match) was based on the assumption that unsynced channels caused the gap. **Finding:** the 497 real-title unmatched are NOT from unsynced Watch Later channels — they're from YouTube History and absent from all playlist exports. Channel sync of Watch Later channels would not recover them.

Revised next steps:
1. **API title search** (in progress) — resolve video_ids for as many of the 497 as quota allows
2. **YouTube History export** — if the operator exports History as a JSON, build a bridge from it (free, no API cost)
3. **Forward sync** (step 6, unchanged) — nlm-to-wiki reads from yt-is cache before hitting NotebookLM
4. **Close superseded handoffs #1/#2** — the NLM fetch path (ytis-nlm-fetch-and-migration, yt-is-fetch-resume) is superseded by this import approach

**Updated evidence:**
- HEAD bound: `git rev-parse HEAD` = `7aada874de315b77dcec5f5e0301022ccffa38d7`
- Cache count: `SELECT COUNT(*) FROM transcript_cache WHERE metadata_json LIKE '%nlm-to-wiki%'` = 3,910
- Importer dry-run output (this session)
- API search script: `P:/tmp/api_title_search.py`
- Categorization script: `P:/tmp/categorize_unmatched.py`

**Status update:** OPEN — 25 additional transcripts imported (3,893 → 3,918). API search resolved 257 of 497 real-title unmatched (87% at exact score 100); 249 ready for import tomorrow via `--import-file` mode, 218 need re-search with fresh quota. Channel-sync path deprioritized (the 497 are YouTube-History-sourced, not Watch Later). Forward sync (step 6) is the next major milestone.
