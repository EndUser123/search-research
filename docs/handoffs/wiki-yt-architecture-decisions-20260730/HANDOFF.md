---
thread_id: wiki-yt-architecture-decisions-20260730
parent_handoff_path: P:/docs/handoffs/yt-is-nlm-to-wiki-fixes-20260730/HANDOFF.md
current_session_id: 019fb49b-e6b2-7bf1-a14b-b706c7c91b66
current_terminal_id: grok-build-terminal
produced_at: 2026-07-31T04:00:00Z
status: open
handoff_type: investigation
accurate_as_of_head: 02758e1
---

# wiki-yt architecture: yt-is as universal transcript cache

## Objective

Document the architecture decisions made this session for how wiki-yt and
yt-is relate, so a future session can pick up the design without re-deriving
the analysis.

## Key decisions

### Decision 1: NotebookLM (Gemini Notebooks) stays as primary transcript fetcher

**Rationale:** Shadow-ban immune (server-side Google-to-Google). YouTube
returns HTTP 429 for automated-access throttling, which the yt-is circuit
breaker handles. But yt-dlp/direct methods hit YouTube's servers directly
and get throttled at batch scale. NotebookLM processes server-side without
exposing the host IP.

**Alternatives rejected:** Bypass NotebookLM entirely (Stage 0 design) —
loses the notebook's organizational roles (clustering scope, provenance
anchor, re-sync identity) and doesn't solve the real problem (duplicate
fetches, which cache-first already addresses).

### Decision 2: Cache-first + feed-forward (the virtuous cycle)

**Cache-first:** Before `nlm source content`, check yt-is `transcript_cache`.
If the transcript is there, skip the NLM fetch.

**Feed-forward:** After exporting a transcript from any source, write it to
yt-is `transcript_cache` via `set_cached_transcript`.

**Combined effect:** First sync of a notebook feeds the cache; subsequent
syncs (or cross-notebook overlap) skip NLM for cached videos. Over time,
yt-is accumulates everything.

**Limitation:** Cache is 96.5% NLM-derived (9,725/10,072). F2 is a
re-fetch-skip optimization, not an alternative-source play. ROI depends on
notebook↔cache overlap (unmeasured).

### Decision 3: yt-is is NOT the pipeline entry point (Stage 0 rejected)

**Why:** A `/tp` critique found that bypassing notebooks would break 4
roles the notebook plays: (1) clustering scope, (2) provenance anchor,
(3) re-sync identity key, (4) source UUID namespace. Building Stage 0
would require redesigning all four — high cost, low marginal benefit over
cache-first which already eliminates duplicate fetches.

### Decision 4: nlm-to-wiki renamed to wiki-yt

**Why:** "nlm-to-wiki" was stale (NotebookLM → Gemini Notebooks). The
skill handles YouTube, web pages, PDFs, and docs — not just NotebookLM.
Renamed to wiki-yt as a first step toward a cleaner identity. Full
restructure (making it a `/wiki` subcommand) deferred.

### Decision 5: Non-lossy metadata pipeline

**Why:** Every importer was dropping 6+ metadata fields available in the
source data. Channel sync via RSS returned bare video_ids. This caused
"orphans" (videos with no metadata) and forced fuzzy title matching.

**Fix:** `enrich_videos_by_id` (videos.list API, 1 unit/50 videos) +
`check_rss_rich` (free RSS XML parsing) + importer enrichment (description,
thumbnail extraction) + cross-source COALESCE merge.

## Status

- Cache-first + feed-forward: SHIPPED and smoke-tested
- Metadata pipeline (Units 1-3): SHIPPED with 15 tests
- wiki-yt rename: SHIPPED
- Stage 0 bypass: REJECTED per /tp critique
- NotebookLM auth: BROKEN (stale port-map PID from --force run; profiles
  renamed; "codex" profile corrupted)

## Next steps

1. Measure cache-first hit rate on a real wiki-yt sync (`from_cache_count`)
2. Run yt-is sync to completion (740 channels unchecked from partial run)
3. Fix NLM auth (clear port-map, try `a.hominidae` profile with Chrome closed)
4. Build the capability-claim Stop hook (see kill-unverified-claims handoff)

## Last user message (verbatim)

> "0" (accepting all /tp recommendations)
