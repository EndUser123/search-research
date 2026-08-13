# Historical cache-overlap audit

Generated: 2026-08-09

## Decision

Supporting signal found for cache-first forward sync. This is a historical,
offline comparison, not a live NotebookLM measurement and not a quantified
production ROI result.

## Inputs

- Notebook/source manifest: `P:/.data/wiki/_state/nlm-sync-manifest.json`
- Exported transcript directory: `P:/.data/wiki/sources/transcripts/`
- Authoritative cache: `P:/.data/yt-is/transcripts.sqlite`
- The manifest's notebook `last_synced_at` values are from July 2026; no live
  notebook inventory or external request was used.

## Method

1. Read the 27 notebook entries and their source IDs from the local manifest.
2. Read only transcript frontmatter for matching source-ID markdown files.
3. Extract YouTube video IDs from frontmatter URLs, or URL-shaped titles when
   a URL field was unavailable.
4. Compare those IDs against `transcript_cache.video_id` in the authoritative
   cache using a read-only SQLite connection.

## Results

| Measure | Count |
|---|---:|
| Manifest source IDs | 5,581 |
| Matching transcript files present | 5,530 |
| Identifiable YouTube sources | 286 |
| YouTube IDs present in yt-is cache | 286 |
| YouTube IDs absent from yt-is cache | 0 |
| Non-YouTube or unresolved sources | 5,295 |

Observed historical cache overlap: **286/286 (100%)** for the identifiable
YouTube subset.

## Interpretation

Verified fact: every identifiable YouTube source in this historical manifest
had a matching row in the authoritative yt-is cache.

Inference: the cache-first provider is likely to avoid redundant NotebookLM
source-content calls for a similar already-exported corpus.

Not established: current notebook inventory overlap, future call reduction,
wall-clock savings, or behavior for sources whose title bridge cannot resolve a
video ID. The manifest is historical, and retrospective cache presence is not
the same as observing a prevented live call.

## Reproduction shape

The audit was performed with a read-only Python/SQLite scan of the three paths
above. It made no network requests, NotebookLM calls, database writes, or
transcript writes.

## Allowed next action

Keep cache-first enabled and measure `from_cache_count` on a fresh export receipt
when a live run is otherwise authorized. Do not use this packet alone to
authorize a live run, claim optimal VPH, or claim a production percentage
savings.
