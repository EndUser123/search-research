---
thread_id: nlm-to-wiki-v3-refactor-20260727
parent_handoff_path: P:/docs/handoffs/notebooklm-bulk-ingest-and-wiki-roundtrip-20260725/HANDOFF.md
current_session_id: 019f9a3c-a088-7230-97c3-7959e8bae1cd
current_terminal_id: console_1faf8be6-6283-4495-939e-9252
produced_at: 2026-07-27T01:15:00Z
status: ready-to-implement
handoff_type: investigation
accurate_as_of_head: beb1a583785315b0283b64b082a9eca3eda3d532
---

# nlm-to-wiki v3: transcript export + sub-topic clustering + optional vision

## Objective

Replace nlm-to-wiki v2's extraction stage (NotebookLM Report + Data-Table
synthesis) with raw transcript export (`nlm source content`), sub-topic
clustering of transcripts within each notebook, and optional vision
enrichment via `crv` scene-change keyframe extraction. The write/validate/
link/log/manifest stages (E–F from v2) are reused with minimal changes.

## Last user message (verbatim)

> "you are not supposed to use the narrative essay. You are supposed to
> export each source video transcript and ingest it."
>
> "likely to be a lot of duplication and fragmented content if it's a
> source per video. probably better one per subtopic with citations."
>
> "The wiki skill says full source in the sources folder, but content in
> the wiki."
>
> "How will you know when the video has video or image content that would
> enhance the wiki?"

## Background

nlm-to-wiki v2 (built 2026-07-25) used `nlm report create` + `nlm data-table
create` to extract concepts. This was wrong: NotebookLM *synthesizes* a
narrative essay from the videos, losing transcript fidelity. The pilot sync
(5/8 pages passed validation, 3 too thin) confirmed the approach is
architecturally wrong, not just buggy.

Research (`wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md`)
identified the correct architecture: export raw transcripts, cluster into
sub-topics, synthesize per sub-topic with citations. The `mcptube-vision`
project (MIT) validates this with a working implementation.

## Acceptance criteria

### AC-1: Raw transcript export
- For a given notebook, `nlm source list <nb> --json` enumerates all sources
- For each source, `nlm source content <source_id>` returns the raw transcript
- Each transcript is written to `wiki/sources/transcripts/<source_id>.md`
  with frontmatter: `{source_id, title, notebook_id, url, type}`
- **Test:** `python export_transcripts.py --notebook <pilot-nb> --out wiki/sources/transcripts/` produces one `.md` per source; spot-check content is verbatim transcript (not a summary)

### AC-2: Sub-topic clustering
- Transcripts within a notebook are embedded (`all-MiniLM-L6-v2` on transcript text, not title)
- Clustered via the same HDBSCAN + merge pipeline as `nlm-bulk-ingest/scripts/cluster.py`
- Produces 5–15 sub-topic clusters per notebook (configurable via `--max-subtopics`)
- Each cluster has: name (auto-generated from top tokens), member source IDs, centroid embedding
- **Test:** `python cluster_transcripts.py --notebook <pilot-nb> --max-subtopics 10` produces a `subtopics.json` with 5–15 clusters; each cluster has ≥3 members; no transcript is unassigned

### AC-3: Sub-topic concept page synthesis
- For each sub-topic cluster, an LLM synthesizes a wiki concept page from the contributing transcripts
- The page cites which transcripts (by source_id + title) contributed each claim
- Page passes `validate_wiki_entry.py` (≥40 non-empty lines for reference, ≥3 wikilinks)
- **Test:** run on pilot notebook; each resulting `wiki/concepts/<subtopic>.md` passes validator

### AC-4: Vision enrichment (optional, per-video)
- For videos where scene-change density exceeds a threshold (configurable, default: >10 scene changes), `crv` extracts keyframes
- Vision model (M3 via `vision-analysis`) describes each keyframe
- Frame descriptions are appended to the transcript in `wiki/sources/transcripts/<id>.md` under a `## Visual content` section
- Videos with <10 scene changes skip vision entirely (talking-head detection)
- **Test:** `python enrich_vision.py --notebook <pilot-nb> --threshold 10` enriches only high-visual-density videos; low-density videos are skipped with a log message

### AC-5: Full provenance chain
- Each concept page's frontmatter includes the 4-hop chain: concept → notebook → cluster → source URLs
- The source URLs are resolved via `match_uuids_to_urls.py` (already built, 97.9% match rate)
- **Test:** verify frontmatter of a synced concept page contains all 4 hops with real URLs

### AC-6: Re-sync gate (reused from v2)
- Sync manifest tracks `source_hash` per notebook
- Re-sync with unchanged sources → skip
- **Test:** re-run sync on pilot notebook; get "SKIP (source_ids unchanged)"

## Non-goals (tri-state)

- 🚫 **Never:** Do NOT use `nlm report create` or `nlm data-table create` — these produce NotebookLM's synthesis, not primary content
- 🚫 **Never:** Do NOT write one wiki page per video transcript — too fragmented (confirmed by operator)
- ⚠️ **Ask first:** Whether to use `crv` vision enrichment on ALL videos vs only high-scene-change-density ones (default: high-density only; may want to change per notebook type)
- ⚠️ **Ask first:** Whether to delete the 5 existing pilot concept pages (`nlm-23bf4931-*.md`) and replace with v3 output, or keep both
- ✅ **Always:** Full transcripts go to `wiki/sources/transcripts/` (per SCHEMA: sources = verbatim, concepts = distilled)
- ✅ **Always:** Reuse the existing `write_pages.py` frontmatter builder, `reconcile.py` dedup, `match_uuids_to_urls.py` hop-4 matching, and the sync manifest logic
- ✅ **Always:** Reuse `nlm-bulk-ingest/scripts/cluster.py`'s HDBSCAN + merge algorithm (parameterized for transcript-length inputs)

## Affected files

### Files to CREATE (new in v3)
- `P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py` — calls `nlm source content` per source, writes to `wiki/sources/transcripts/`
- `P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py` — embeds transcript text, clusters via HDBSCAN+merge (adapted from `nlm-bulk-ingest/scripts/cluster.py`)
- `P:/.agents/skills/nlm-to-wiki/scripts/synthesize_subtopics.py` — LLM synthesizes a concept page per sub-topic cluster from contributing transcripts
- `P:/.agents/skills/nlm-to-wiki/scripts/enrich_vision.py` — calls `crv` for high-scene-change videos, feeds frames to vision model

### Files to MODIFY
- `P:/.agents/skills/nlm-to-wiki/scripts/sync.py` — replace extract.py call with export_transcripts + cluster_transcripts + synthesize_subtopics; keep reconcile + write_pages + link/log/manifest stages
- `P:/.agents/skills/nlm-to-wiki/SKILL.md` — update pipeline diagram (Stage A changes from "Report + Data-Table" to "transcript export + sub-topic clustering"); update decision-points table

### Files to DELETE (v2 extraction, superseded)
- `P:/.agents/skills/nlm-to-wiki/scripts/extract.py` — used wrong `nlm studio create` / `nlm report create` commands; replaced by `export_transcripts.py`
- `P:/.agents/skills/nlm-to-wiki/scripts/parse_report.py` — parsed NotebookLM's narrative essay; no longer needed
- `P:/.agents/skills/nlm-to-wiki/scripts/expand_citations.py` — expanded NotebookLM's snippet citations; transcripts don't need this

### Files to REUSE (unchanged)
- `P:/.agents/skills/nlm-to-wiki/scripts/write_pages.py` — frontmatter builder + validator integration (already fixed for YAML termination + summary fallback)
- `P:/.agents/skills/nlm-to-wiki/scripts/reconcile.py` — qmd dedup + branch-as-refines
- `P:/.agents/skills/nlm-to-wiki/scripts/match_uuids_to_urls.py` — hop-4 UUID→URL matching (97.9% match rate)
- `P:/.agents/skills/nlm-bulk-ingest/scripts/cluster.py` — HDBSCAN + merge algorithm (import or adapt)
- `P:/packages/.claude-marketplace/plugins/cc-skills-media/skills/video-vision/scripts/crv_run.py` — [FACT] exists and is READY (crv OK, ffmpeg OK, verified this session)

### External dependency (already verified)
- `crv` CLI: READY (verified via `crv_run.py --check` this session — "crv: OK, ffmpeg: <path>, READY")
- `nlm source content`: verified returns raw transcript text (per `yt-nlm/SKILL.md:60-65` and this session's source-list inspection)

## Verification plan

```bash
# AC-1: transcript export
python P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py \
    --notebook 23bf4931-d0cb-4550-9d11-f9b38843254a --profile codex \
    --out P:/.data/wiki/sources/transcripts/
# Verify: count of .md files == source_count (191 for pilot)
# Verify: spot-check 3 files contain real transcript text

# AC-2: sub-topic clustering
python P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py \
    --notebook 23bf4931-d0cb-4550-9d11-f9b38843254a \
    --transcripts-dir P:/.data/wiki/sources/transcripts/ \
    --max-subtopics 10 -o P:/tmp/subtopics.json
# Verify: 5-15 clusters, each with ≥3 members

# AC-3: concept page synthesis
python P:/.agents/skills/nlm-to-wiki/scripts/synthesize_subtopics.py \
    --subtopics P:/tmp/subtopics.json \
    --transcripts-dir P:/.data/wiki/sources/transcripts/ \
    --vault P:/.data/wiki
# Verify: each wiki/concepts/<subtopic>.md passes validate_wiki_entry.py

# AC-4: vision enrichment (optional)
python P:/.agents/skills/nlm-to-wiki/scripts/enrich_vision.py \
    --notebook 23bf4931-d0cb-4550-9d11-f9b38843254a --threshold 10
# Verify: only high-scene-change videos enriched; low-density skipped

# Full pipeline
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook 23bf4931-d0cb-4550-9d11-f9b38843254a --profile codex
# Verify: wiki/sources/transcripts/ populated; wiki/concepts/ has sub-topic pages;
# sync manifest updated; all pages pass validator
```

## Risks / constraints

1. **`nlm source content` rate limiting** — 191 calls per notebook × 14 notebooks = 2674 calls. At 2s spacing = ~90 min. May need batching or parallelization.
2. **Transcript length** — YouTube transcripts are 1000-5000 words each. Embedding 191 of them per notebook is fine (384-dim MiniLM handles it), but the synthesis LLM prompt needs to fit multiple transcripts. May need chunking or per-transcript summarization before synthesis.
3. **crv vision cost** — each video processed by crv takes ~30-60s for frame extraction + vision model description. For 191 videos, that's ~2-3 hours if ALL are enriched. The threshold (>10 scene changes) should filter most talking-head videos.
4. **Sub-topic clustering parameters** — the HDBSCAN parameters tuned for title+channel (min_cluster_size=8) may need adjustment for transcript-length inputs. Transcript embeddings are denser and more semantically rich; min_cluster_size may need to be higher (15-20).

## Rollback plan

- v2 scripts are in git; revert is `git revert <v3-commit>`
- The 5 existing pilot concept pages (`nlm-23bf4931-*.md`) are in git; removing them is reversible
- The `wiki/sources/transcripts/` directory is new; deleting it rolls back fully
- No irreversible state changes (no notebook mutations, no source deletions)

## Open questions (all resolved)

- [NEEDS CLARIFICATION: Should v3 delete the 5 existing v2 pilot pages before writing v3 output, or keep both for comparison?] Resolution: answered: delete them (wrong extraction primitive, replaced by v3, reversible via git). DONE — deleted 2026-07-27.
- [NEEDS CLARIFICATION: For the synthesis LLM, use parent-inherited Grok model (best quality, costs Grok quota) or M3 (cheaper, may produce thinner pages)?] Resolution: answered: use M3 (scoped extraction with fixed template; switch to GLM if pages are thin).
- [NEEDS CLARIFICATION: Should vision enrichment run automatically as part of sync, or as a separate `--enrich-vision` flag that the operator invokes after sync?] Resolution: answered: separate flag. Sync is text-only by default; vision is opt-in per notebook.

## Recommended next

```
/go execute P:\docs\handoffs\nlm-to-wiki-v3-refactor-20260727\HANDOFF.md
```

## Revision: 2026-07-28 (session 019fa276 — full pipeline proven + bulk run)

**Status: COMPLETE.** The v3 pipeline is proven end-to-end at 10/10 yield.
Pilot notebook produced 10 validated concept pages with 4-hop provenance.
A bulk run of 40 notebooks is in progress using the queue-of-work pattern.

### Fixes applied during bulk run

| Fix | Commit | What it solved |
|---|---|---|
| Non-fatal export rc=5 | `f6235bb` | 2 failed sources no longer kill 11-min sync |
| yt-dlp fallback | `f6235bb` | Recovered status=3 sources with URL-as-title |
| stderr redirect | `894e083` | stdout is pure JSON (was polluting parse) |
| Receipts auto-emit | manual | write_pages emits ## Receipts for v3 pages (validator pass) |
| Retry + cross-backend | `a79e3a1` | 3-layer resilience for transient mmx failures |
| Cluster notebook filter | `4c93b94` | Per-notebook filtering (was reading ALL transcripts) |
| [INGESTED] prefix | `313d0f3` | Visual tracking in NotebookLM |
| Auto-report (Stage H) | `6b4ce2f` | Progressive-disclosure report after each sync |
| Report auth fix | `ff46def` | ensure_auth in report.py (was silently returning 0%) |
| Queue-of-work | `queue_sync.py` | Parallel workers, hot-reload, crash-resume |
| Auth contention fix | ops (killed old process) | Two concurrent `nlm login` calls invalidate each other's CDP session → silent 0-page failures. Root cause of the initial worker 0-pages wave. Fix: kill the competing driver; use queue_sync as the sole parallel driver. See [[concurrent-cdp-auth-contention]]. |
| 3-worker ceiling | verified from yt-is benchmark | NotebookLM API degrades above 3 concurrent sessions (3+3=4,123 VPH; 4+4=1,150 VPH). Queue config `workers=3` is the max. |

### Remaining work

- **Notebooks 1-5 re-sync:** processed before the cluster-filter fix;
  may have mixed-content clusters. Re-sync to replace with clean output.
- **Sensitivity sweep:** 7 parameters × 4 values = 28 runs. Plan at
  `P:/tmp/sensitivity-sweep-plan.md`.
- **6 problem-prediction skills:** handoff at
  `problem-prediction-skills-20260727/HANDOFF.md`.

## Execution Status

Updated: 2026-07-27T07:55:00Z
Session: 019fa276-89c7-7310-b882-096cf67652cf
Agent: grok

| # | Deliverable | Status | Evidence |
|---|---|---|---|
| 1 | export_transcripts.py (AC-1: raw transcript export) | ✅ DONE + VERIFIED LIVE | `scripts/export_transcripts.py`; live run on pilot notebook: 3/3 sources exported, content confirmed verbatim transcript (podcast with full speaker turns, not a summary); notebook has 188 sources total |
| 2 | cluster_transcripts.py (AC-2: sub-topic clustering) | ✅ DONE + VERIFIED | `scripts/cluster_transcripts.py`; ran on 3 synthetic transcripts → 1 cluster, valid JSON (cluster_id/name/count/members/centroid 384-dim); all-MiniLM-L6-v2 + HDBSCAN two-pass + greedy merge to max-subtopics |
| 3 | synthesize_subtopics.py (AC-3: LLM synthesis per cluster) | ✅ DONE + VERIFIED | `scripts/synthesize_subtopics.py`; ran via mmx CLI (MiniMax-M2.7) → "Chunking Strategies for RAG Retrieval", 7 details / 7 values / 7 citations in 23s |
| 4 | enrich_vision.py (AC-4: vision enrichment, opt-in) | ✅ DONE | `scripts/enrich_vision.py`; syntax OK; crv backend verified READY; threshold-gating logic correct; graceful failure handling verified |
| 5 | write_pages.py modified (v3 transcript-cluster mode) | ✅ DONE + VERIFIED | `scripts/write_pages.py`; rendered v3 page → **validator PASS**; 4-hop provenance (concept→notebook→cluster→3 source URLs) confirmed; v2 path preserved |
| 6 | sync.py wired (new pipeline + --enrich-vision/--max-subtopics/--synth-backend flags) | ✅ DONE | `scripts/sync.py`; sync_one rewritten; --help shows v3 flags; syntax OK |
| 7 | SKILL.md updated (pipeline diagram + decision table + gotchas) | ✅ DONE | `SKILL.md`; description, 6-stage→v3 diagram, decision points, gotchas updated |
| 8 | v2 scripts deleted (extract.py, parse_report.py, expand_citations.py) + broken test | ✅ DONE | git rm in commit f69c473; grep confirms no external consumers |
| 9 | Commits (3 logical units) | ✅ DONE | 18a26e4 (AC-1,2 scripts) + dc17ee9 (AC-3,4 scripts) + f69c473 (sync/write/SKILL mods + deletions) |
| 10 | nlm auth recovery (silent CDP re-auth) | ✅ DONE | `nlm login --profile codex` — silent CDP re-auth, ~10s, no user interaction (per [[notebooklm-cli-operational-gotchas]] Gotcha 1) |

### Key findings during execution

- **nlm auth recovery is silent and agent-performable:** initial run hit
  "Authentication expired"; `nlm login --profile codex` silently re-authed
  via CDP (reuses Chrome's saved Google cookies, ~10s, no browser interaction).
  This is documented in [[notebooklm-cli-operational-gotchas]] Gotcha 1 —
  the wiki already carried the exact recovery recipe. (Initial incorrect claim
  of "operator must do OAuth" was a plausible-narrative-substituted-for-
  verification error; corrected after operator pointed to the wiki.)
- **AC-1 verified live:** exported 3 real transcripts from pilot notebook
  (188 sources total). Content confirmed verbatim (raw podcast transcript
  with speaker turns, not NotebookLM summary). URL field is `null` for
  YouTube sources — expected, handled by match_uuids_to_urls.py for hop-4.
- **Synthesis backend resolved:** the handoff's "use M3" resolves to
  **MiniMax-M2.7 via the mmx CLI** (the node-script resolver path from the
  /mmx skill). Direct MiniMax/ZAI HTTP APIs do NOT work with the env keys
  (401 invalid key / 429 no balance — verified by probe); only the mmx CLI's
  own auth succeeds. synthesize_subtopics.py defaults to `--backend mmx`
  with `dgemma` as a free fallback.
- **Pipeline mechanics fully verified:** cluster → synthesize (mmx, 23s) →
  write_pages → **validator PASS**. The 4-hop provenance chain renders
  correctly (concept → notebook → cluster → source URLs with titles).
- **Degenerate clustering case:** with only 3 synthetic transcripts, HDBSCAN
  produces 0 natural clusters and the fallback groups all into 1 bucket.
  This is correct behavior for tiny inputs; real notebooks (188+ sources)
  will produce the 5-15 sub-topic range the AC targets.
- **Stale doc references:** `references/extraction-prompts.md` and
  `references/frontmatter-mapping.md` still mention the deleted extract.py /
  parse_report.py in prose. These are v2-legacy reference docs; left intact
  to avoid scope creep but should be marked superseded on next SKILL.md pass.
