---
title: "Shared-directory contamination: when accumulating artifacts from multiple runs break per-unit processing"
created: 2026-07-27
source: session-019fa276 (nlm-to-wiki bulk run cluster-filter bug)
tags: [bug-pattern, shared-directory, contamination, multi-unit-pipeline, filtering, provenance, isolation, cluster-transcripts]
summary: >
  Generalizable bug pattern: when a pipeline stores artifacts from multiple
  units (notebooks, repos, projects) in a shared directory, downstream
  stages that don't filter by unit identity will process ALL accumulated
  artifacts instead of just the current unit's. This produces silently wrong
  output (mixed-content clusters, cross-project references, contaminated
  metrics) that passes structural validation but is semantically wrong.
  Observed in nlm-to-wiki: cluster_transcripts.py read all 1,842 transcripts
  from 7 notebooks instead of filtering to the current notebook's 298,
  producing incoherent mega-clusters and 0 concept pages. The fix is
  per-unit filtering at every stage that reads from the shared directory.
  This pattern generalizes to any pipeline where unit A's output lands in
  the same directory as unit B's output.
agent: grok
host: grok
cognitive_load: 2
verification: observed
sources:
  - "P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py" (lines 195-213, the filter fix)
  - "P:/.agents/skills/nlm-to-wiki/scripts/report.py" (same pattern — list_sources needed ensure_auth + filtering)
  - "P:/docs/handoffs/nlm-to-wiki-v3-refactor-20260727/HANDOFF.md" (notebook 1's 0-pages root cause)
relations:
  - target: wiki/concepts/stateful-skills-need-maintenance-surface.md
    type: related
  - target: wiki/concepts/video-to-wiki-pipeline-report-metrics-and-framework.md
    type: related
  - target: wiki/concepts/nlm-to-wiki-optimization-opportunities.md
    type: related
---

# Shared-directory contamination: accumulating artifacts break per-unit processing

## Decision context

**Why this was needed:** during the nlm-to-wiki bulk run (40 notebooks),
notebook 1 produced 0 concept pages despite 298 transcripts being
exported successfully. Investigation showed cluster_transcripts.py was
reading ALL 1,842 transcript files from 7 notebooks in the shared
directory, not just the 298 belonging to the current notebook. The
mixed-content clusters were incoherent, and synthesis failed. Notebooks
2-5 succeeded only because they were processed when fewer cross-notebook
transcripts existed (their content was dominant). This is a generalizable
pattern, not a one-off bug.

## The pattern

```
SHARED DIRECTORY: wiki/sources/transcripts/
├── notebook_1_transcript_a.md    ← notebook_id: nb1
├── notebook_1_transcript_b.md    ← notebook_id: nb1
├── notebook_2_transcript_c.md    ← notebook_id: nb2  (CONTAMINANT for nb1 processing)
├── notebook_3_transcript_d.md    ← notebook_id: nb3  (CONTAMINANT)
└── ...

STAGE THAT READS THE DIRECTORY:
  files = glob("*.md")           ← reads ALL files, no filter
  process(files)                 ← processes mixed content → wrong output
```

**Why it's silent:** the pipeline doesn't crash. It produces output that
passes structural validation. The clusters have the right count, the
concept pages have the right frontmatter, the validator passes. The
problem is semantic: the clusters mix unrelated content, producing
incoherent synthesis or 0-page output (when synthesis can't extract a
coherent sub-topic from noise).

**Why it's time-dependent:** the first unit processed in a clean directory
works correctly (only its own files exist). The Nth unit processed after
N-1 prior units' files have accumulated gets progressively more
contaminated. This makes it hard to catch in testing — the pilot (unit 1)
always works because the directory is clean.

## Where this pattern applies beyond nlm-to-wiki

| Pipeline | Shared directory | Contamination risk |
|---|---|---|
| nlm-to-wiki | `wiki/sources/transcripts/` | Clustering mixes notebooks |
| nlm-to-wiki | `wiki/sources/keyframes/` | Vision enrichment on wrong notebook's frames |
| nlm-to-wiki | `wiki/concepts/` | Report.py counts ALL concept pages, not current notebook's |
| Bulk file processing | `/tmp/` or staging dir | Next run inherits previous run's output |
| Multi-repo CI | Shared artifact cache | Repo A's build artifacts leak into repo B's pipeline |
| Log analysis | Shared log directory | Analysis mixes events from different services |

## The fix: per-unit filtering at every read

Every stage that reads from a shared directory must filter by unit
identity:

```python
# WRONG (reads everything)
files = sorted(transcripts_dir.glob("*.md"))

# RIGHT (filters by notebook_id)
files = []
for f in transcripts_dir.glob("*.md"):
    head = f.read_text(encoding="utf-8")[:600]
    if f"notebook_id: {current_notebook_id}" in head:
        files.append(f)
```

**The filter must happen at EVERY read, not just the first.** In
nlm-to-wiki, three separate stages had the same bug:
1. `cluster_transcripts.py` — read all transcripts (fixed)
2. `report.py` `list_sources()` — read all sources without auth check (fixed)
3. `report.py` `collect_metrics()` — counted all concept pages (needs fix)

## How to detect this pattern in other pipelines

1. **Does the pipeline share a directory across units?** If yes, this
   pattern applies.
2. **Does every read from that directory filter by unit identity?** Check
   each `glob()`, `listdir()`, or `walk()` call.
3. **Does the first run in a clean directory always succeed?** That's the
   signature — time-dependent failures that only appear after accumulation.
4. **Does the output pass structural validation but seem semantically
   wrong?** Mixed content produces structurally valid but semantically
   incoherent output.

## Receipts

- **"cluster_transcripts.py read all 1,842 transcripts":** receipt —
  `P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py` line 195
  (pre-fix): `files = sorted(args.transcripts_dir.glob("*.md"))` — no
  notebook filter. Fixed in commit `4c93b94`.
- **"notebook 1 produced 0 pages":** receipt — manifest entry
  `concept_slugs: []` for notebook `af7b9263` in
  `P:/.data/wiki/_state/nlm-sync-manifest.json`.
- **"notebooks 2-5 succeeded despite contamination":** receipt — they
  each have 8-10 concept_slugs in the manifest, but may have lower quality
  due to cluster contamination from mixed content.
- **"report.py had the same pattern":** receipt — `list_sources()` in
  `report.py` returned `[]` when auth expired because there was no
  `ensure_auth()` call. Fixed by adding the auth check.

## Falsifier

This pattern doesn't generalize if:
- All pipelines use per-unit directories (no shared directory). But many
  don't — shared directories are common because they simplify file
  management.
- The filter is too expensive (reading every file's frontmatter). But
  frontmatter is at the top of the file — reading 600 bytes is ~0.1ms.
- The contamination never affects output quality (mixed content produces
  valid results). For clustering, it always affects quality — HDBSCAN
  on mixed content produces mega-clusters that are semantically wrong.

## Sources

- `P:/.agents/skills/nlm-to-wiki/scripts/cluster_transcripts.py` — the
  fix (lines 195-213): filter by notebook_id frontmatter before clustering
- `P:/.agents/skills/nlm-to-wiki/scripts/report.py` — the same pattern
  in `list_sources()` and `collect_metrics()` (auth fallback)
- `P:/docs/handoffs/nlm-to-wiki-v3-refactor-20260727/HANDOFF.md` — the
  0-pages root cause investigation

## Auto-related

- [[stateful-skills-need-maintenance-surface]] — the maintenance surface should detect cross-unit contamination
- [[video-to-wiki-pipeline-report-metrics-and-framework]] — the report metrics framework measures per-unit quality
- [[nlm-to-wiki-optimization-opportunities]] — parallel export across notebooks increases the shared-directory contention
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
