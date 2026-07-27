---
title: "nlm-to-wiki optimization opportunities: parallel export, parallel synthesis, embedding cache"
created: 2026-07-27
source: session-019fa276 (/wiki analysis of nlm-to-wiki performance)
tags: [nlm-to-wiki, performance, optimization, parallelism, bottleneck-analysis, embedding-cache, transcript-export]
summary: >
  Five ranked optimization opportunities for the nlm-to-wiki v3 pipeline,
  grounded in live timing data from the pilot notebook (188 sources).
  Export is the dominant bottleneck at 3.2s per transcript × 188 = ~10 min
  serial; parallelizing with 6 workers cuts it to ~1.7 min (6x speedup).
  Parallel cluster synthesis cuts the LLM stage from ~3.5 min to ~40s (5x).
  Embedding cache eliminates re-embedding cost on re-syncs. Total projected
  speedup: first sync ~10 min → ~3 min; re-sync ~10 min → ~30s when only a
  few sources changed. Refines the existing architecture concept which
  noted "transcript export is mechanical and parallelizable" without
  implementation detail.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - "P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py" (serial loop, lines 149-167)
  - "P:/.agents/skills/nlm-to-wiki/scripts/synthesize_subtopics.py" (serial mmx calls, line 245)
  - "P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py" (full re-embed every run)
  - "Live sync run 019fa3ca" (45 transcripts / 145.5s = 3.2s each, observed 2026-07-27)
  - "P:/.data/wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md" (architecture concept, optimization #4)
relations:
  - target: wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md
    type: refines
  - target: wiki/concepts/stateful-skills-need-maintenance-surface.md
    type: related
  - target: wiki/concepts/notebooklm-cli-operational-gotchas.md
    type: related
---

# nlm-to-wiki optimization opportunities

## Decision context

**Why this analysis was needed:** the first full v3 sync of the pilot
notebook (188 sources) revealed that the pipeline's wall-clock time is
dominated by a single serial stage: transcript export. The export loop
fetches one transcript at a time with 1.5s spacing between calls, producing
a ~10 min floor for any notebook of this size. With 15 large notebooks
(278-299 sources each) queued for sync, the serial export alone would
consume 2.5+ hours. The operator asked `/wiki` to analyze optimization
opportunities before committing to the bulk run.

**The real question:** which optimizations have the highest ROI, and which
are safe to implement without risking nlm rate-limiting or mmx quota
exhaustion? The analysis below ranks five opportunities by impact and
implementation cost, grounded in live timing data from the in-flight sync.

## Live timing baseline (the receipt)

Measured during sync `019fa3ca` on pilot notebook `23bf4931` (188 sources):

| Stage | Observed time | Rate | Bottleneck |
|---|---|---|---|
| Export (Stage A) | 45 transcripts / 145.5s | 3.2s per transcript | Serial loop + 1.5s spacing |
| Projected full export | ~10.1 min for 188 | — | Dominates wall-clock |
| Clustering (Stage B) | [INFERENCE] ~30s for 188 | MiniLM batch encode | Tolerable; one-time |
| Synthesis (Stage C) | [INFERENCE] ~3.5 min for 10 clusters | ~20s per mmx call, serial | Second bottleneck |
| Total projected | ~14 min | — | — |

The export rate (3.2s each) decomposes as: 1.5s `time.sleep(spacing)` +
~1.7s per `nlm source content` API call. The spacing is a conservative
default; the actual nlm rate limit tolerance is unknown (the wiki's
[[notebooklm-cli-operational-gotchas]] doesn't quantify it).

## Ranked optimization opportunities

### Opt 1: Parallel transcript export — HIGH impact, LOW risk

**Current:** `export_transcripts.py` lines 149-167 — strictly serial:
`fetch_content → atomic_write → time.sleep(spacing)`.

**Fix:** `concurrent.futures.ThreadPoolExecutor(max_workers=6)` wrapping
`fetch_content`. Each worker handles one source ID; atomic writes are
already thread-safe (tmp + os.replace). Reduce spacing to 0.25s per worker
(effective ~1.5s aggregate with 6 workers).

**Projected speedup:** 188 sources at 3.2s serial = 10.1 min → with 6
workers ≈ 1.7 min (**6x faster**).

**Risk:** nlm may rate-limit aggressive parallelism. Mitigation: probe with
6 parallel calls first; if any return 429, fall back to 3 workers. The
crash-resume (file-exists check) already handles partial failures, so a
rate-limit midpoint isn't destructive — re-run continues from where it
stopped.

**Evidence the rate limit tolerates moderate parallelism:** the
[[notebooklm-cli-operational-gotchas]] documents `nlm source add --youtube`
as bulk-repeatable (hundreds of URLs in one call), suggesting the backend
handles concurrent source operations, not just serial ones. [INFERENCE] —
read operations (`source content`) likely have equal or higher limits than
write operations (`source add`).

### Opt 2: Parallel cluster synthesis — MEDIUM impact, LOW risk

**Current:** `synthesize_subtopics.py` processes clusters serially with
`time.sleep(1.0)` between mmx calls (line 245). 10 clusters × ~20s = ~3.5 min.

**Fix:** `ThreadPoolExecutor(max_workers=5)` for cluster synthesis. mmx CLI
calls are independent processes with no shared state; the only shared
resource is the output JSON file (each cluster writes to a separate record
in the list, assembled after all threads join).

**Projected speedup:** 10 clusters × 20s serial = 3.5 min → with 5 workers
≈ 40s (**5x faster**).

**Risk:** mmx (MiniMax) quota exhaustion under parallel load. Mitigation:
start with 3 workers; if any call returns quota error, the existing
dgemma fallback handles it per-cluster. The skill's `--synth-backend` flag
already allows mixing backends per run.

### Opt 3: Embedding cache — MEDIUM impact on re-runs, zero on first run

**Current:** `cluster_transcripts.py` re-embeds ALL transcripts every run
via `embed_text()`, even if only 1 source was added. For 188 transcripts,
MiniLM encoding takes ~30s.

**Fix:** cache embeddings to disk as
`_state/embeddings/<source_id>.json` (384-dim vector). On re-run, load
cached vectors for unchanged transcripts; only embed new/changed ones.
Invalidate by comparing transcript file mtime against cache mtime.

**Projected speedup:** first run unchanged (~30s); re-run with 1 new source
≈ 0.5s (embed 1 + load 187 cached) instead of ~30s (**60x faster on
re-sync**).

**Implementation cost:** ~30 lines — a `load_or_embed()` function that
checks the cache before calling `model.encode()`. No architectural change.

### Opt 4: Incremental clustering — MEDIUM impact, HIGHER complexity

**Current:** adding 1 video to a 188-source notebook triggers full
re-clustering of all 189 transcripts, which may re-assign existing members
to different clusters, which invalidates all prior synthesis.

**Fix:** assign new transcripts to the nearest existing cluster centroid
(computed from the cached embeddings). Only re-cluster if the centroid drift
exceeds a threshold (e.g., a new transcript shifts a centroid by >0.15
cosine distance). Cache synthesis per cluster; only re-synthesize clusters
whose membership changed.

**Projected speedup:** 1 new source → assign to nearest cluster (~0.01s) +
re-synthesize 1 cluster (~20s) instead of re-cluster all (~30s) +
re-synthesize all (~3.5 min).

**Why this is lower priority:** it's an architectural change to the
clustering model (from "rebuild every time" to "incremental assignment +
drift-triggered rebuild"). The payoff only materializes on frequent small
re-syncs, not on the initial bulk run. Defer until the bulk run is done and
incremental syncs become the common case.

### Opt 5: Single-mode export probe — LOW impact, trivial

**Current:** `fetch_content()` tries `--json` first, then falls back to
plain text. For sources where `--json` fails, this makes 2 API calls.

**Fix:** probe `--json` on the first source; cache the result; use the
working mode for all subsequent sources.

**Projected speedup:** saves ~1.7s per non-JSON source. For a notebook
where all sources are JSON-compatible (common), zero savings. For a notebook
where none are, saves ~30% of export time.

## Combined projection

| Scenario | Current | After Opt 1+2 | After Opt 1+2+3 |
|---|---|---|---|
| First sync (188 sources) | ~14 min | ~3 min | ~3 min |
| Re-sync, 1 source added | ~14 min | ~3 min | ~25s |
| Bulk run (15 notebooks × 288 avg) | ~5 hours | ~75 min | ~75 min |

Opt 1 and Opt 2 together cut the first-sync time by ~5x and the bulk run
from multi-hour to ~75 min. Opt 3 makes incremental re-syncs nearly free.
Opt 4 and Opt 5 are refinements that pay off later.

## What this means for our workspace

- **Implement Opt 1 + Opt 2 before the bulk run.** They're low-risk,
  high-impact, and the implementation is ~50 lines total
  (ThreadPoolExecutor in two scripts). The bulk run of 15 notebooks is the
  immediate consumer.
- **Opt 3 (embedding cache) is the re-sync multiplier.** Once the bulk run
  is done, subsequent syncs will be incremental (operator adds videos to
  existing notebooks). The cache makes those near-instant.
- **Opt 4 (incremental clustering) should wait.** It's architecturally
  more complex and the payoff is deferred. Re-evaluate after 3 months of
  incremental syncs show whether full re-clustering is actually wasteful
  in practice.
- **Probe the nlm rate limit before committing to worker count.** Start
  with 4 workers on the first parallel export; if no 429s in the first 20
  sources, raise to 6. The crash-resume handles any midpoint failures.

## Falsifier

These projections are wrong if:
- nlm rate-limits parallel `source content` calls aggressively (429s at 4
  workers). Then Opt 1's speedup is capped at 2-3x, not 6x. Testable: run
  10 parallel calls and observe.
- mmx quota is too small for 5 parallel synthesis calls. Then Opt 2 degrades
  to 2-3 workers with dgemma fallback. Testable: fire 5 parallel mmx calls.
- The embedding cache hits invalidation churn (transcripts re-exported
  frequently with `--force`). Then Opt 3 provides no benefit. Mitigated by
  only caching when the transcript file mtime is stable.

## Sources

- `P:/.agents/skills/nlm-to-wiki/scripts/export_transcripts.py:149-167` —
  the serial export loop with `time.sleep(spacing)`. Source of the 3.2s
  per-transcript rate.
- `P:/.agents/skills/nlm-to-wiki/scripts/synthesize_subtopics.py:245` —
  the serial synthesis loop with `time.sleep(1.0)` between mmx calls.
- `P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py` —
  `embed_text()` re-embeds all transcripts every run; no disk cache.
- Live sync `019fa3ca` — 45 new transcripts in 145.5s = 3.2s each,
  observed 2026-07-27 during this analysis.
- `P:/.data/wiki/concepts/video-to-wiki-pipeline-transcript-extraction-multimodal.md`
  § "Optimizations" #4 — "transcript export is mechanical and parallelizable."
  This concept refines that bullet with implementation detail and timing data.

## Auto-related

- [[video-to-wiki-pipeline-transcript-extraction-multimodal]] — the v3 architecture rationale; this concept refines its optimization #4 with implementation detail
- [[stateful-skills-need-maintenance-surface]] — the maintenance surface pattern; optimization is the performance complement to maintenance's correctness role
- [[notebooklm-cli-operational-gotchas]] — nlm rate limits and auth behavior; the parallel export must respect these
- [[semantic-clustering-bounded-size]] — the HDBSCAN + merge algorithm; Opt 3 and Opt 4 modify how it's invoked, not the algorithm itself
