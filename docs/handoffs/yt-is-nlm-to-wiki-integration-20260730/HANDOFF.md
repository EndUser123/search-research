---
thread_id: yt-is-nlm-to-wiki-integration-20260730
parent_handoff_path: none
current_session_id: 019fb189-b2ec-70f0-8d30-16a6e7bb5ad7
current_terminal_id: grok-build-terminal
produced_at: 2026-07-31T00:30:00Z
status: open
handoff_type: investigation
accurate_as_of_head: TBD
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
