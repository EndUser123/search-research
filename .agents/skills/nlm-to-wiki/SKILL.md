---
name: nlm-to-wiki
description: >
  Sync NotebookLM notebook content into the wiki vault as SCHEMA-compliant
  concept pages with full 4-hop provenance (concept → notebook → cluster →
  original source URL). v3 exports raw source transcripts via `nlm source
  content` (not NotebookLM synthesis), clusters them into sub-topics within
  each notebook, and synthesizes a concept page per sub-topic with per-claim
  citations. Optional vision enrichment for high-scene-change videos via crv.
  Branches as `refines` on collision with existing concepts rather than
  overwriting. Composes with nlm-bulk-ingest via --from-clusters for full
  round-trip from raw URL list to wiki concepts.
host: both
---

# nlm-to-wiki

Pull concepts out of NotebookLM notebooks into the wiki, with provenance
that lets a reader click from any claim back to the exact source video or
URL the concept came from.

Built to round-trip with `[[nlm-bulk-ingest]]`:

```
URL list → nlm-bulk-ingest → 15 notebooks → nlm-to-wiki → ~5-15 sub-topic
                                          (v3: transcript export) wiki concept pages
                                                                with provenance back to original URLs
```

## When to use

- You have a NotebookLM notebook whose content you want in the searchable wiki
- You want structured concept pages (not chat dumps) with verified citations
- You want a future reader to trace any claim back to its source

## When NOT to use

| Situation | Use instead |
|---|---|
| "Summarize this notebook for me" | `nlm notebook query <id> "..."` directly |
| Add URLs to a notebook | `[[nlm-bulk-ingest]]` (ingest direction) |
| Update an existing wiki concept | `/wiki update <slug>` |
| One-off Q&A against sources | `nlm notebook query` (no persistence needed) |

## The pipeline (v3)

```
INPUT                     AUTH + SNAPSHOT
──notebook <id>           ────────────────
──all                     ensure auth (CDP silent re-auth)
──from-clusters <path>    snapshot current source_ids for re-sync gate
                                          │
                                          ▼
                          EXPORT TRANSCRIPTS (Stage A)
                          ─────────────────────────────
                          for each source: nlm source content <id>
                            → raw transcript (NOT NotebookLM synthesis)
                          → wiki/sources/transcripts/<source_id>.md
                            (provenance frontmatter; crash-resumable)
                                          │
                          [optional] ──enrich-vision ──▶ crv keyframes
                            for high-scene-change videos only (threshold)
                                          │
                                          ▼
                          CLUSTER (Stage B)
                          ────────────────
                          embed transcript text (all-MiniLM-L6-v2)
                          HDBSCAN two-pass + greedy merge
                            → 5-15 sub-topics per notebook (--max-subtopics)
                                          │
                                          ▼
                          SYNTHESIZE (Stage C)
                          ─────────────────────────
                          for each sub-topic cluster:
                            LLM (MiniMax via mmx CLI) synthesizes a concept
                            page from the contributing transcripts
                            each claim cites source_id + title + excerpt
                                          │
                                          ▼
                          RECONCILE (Stage D)
                          ────────────────
                          for each candidate concept:
                            qmd search vault for similar concepts
                            if similarity ≥ threshold:
                              mark as `refines <existing>`
                            else:
                              mark as new
                                          │
                                          ▼
                          WRITE (Stage E)
                          ────────────────
                          emit SCHEMA-compliant frontmatter
                          (4-hop provenance: concept → notebook → cluster → URL)
                          passes validate_wiki_entry.py
                          atomic write per page
                                          │
                                          ▼
                          LINK + LOG (Stage F)
                          ────────────────────
                          wiki_after_write.py for [[wikilinks]]
                          append to wiki log
                          update sync manifest
```

**Why transcripts, not synthesis:** NotebookLM's Report + Data-Table
artifacts *synthesize* a narrative essay from the sources, losing transcript
fidelity. v3 exports the primary content (raw transcripts) and clusters +
synthesizes locally, so every claim traces to a verbatim source excerpt. See
[[video-to-wiki-pipeline-transcript-extraction-multimodal]].

## Usage

```bash
# Sync one notebook (the canonical case)
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid> \
    --profile codex

# Sync all notebooks (sequential; ~10-30 min each)
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --all \
    --profile codex \
    --state sync-state.json

# Round-trip from nlm-bulk-ingest output
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --from-clusters clusters.json \
    --profile codex \
    --state sync-state.json

# Dry run — export + cluster + synthesize + reconcile, no page writes
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid> \
    --dry-run

# Re-sync (skips notebooks whose source_ids haven't changed)
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid>

# v3: with optional vision enrichment + custom sub-topic count
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid> \
    --enrich-vision --max-subtopics 12 --synth-backend mmx
```

## Decision points

| Decision | Default | When to change |
|---|---|---|
| Extraction primitive | Raw transcript export (`nlm source content`) | — (v2 Report+Data-Table was wrong; superseded) |
| Sub-topic cluster count | 10 (`--max-subtopics`) | 5-15 range; raise for broader themes, lower for granular concepts |
| HDBSCAN min_cluster_size | 5 (transcript-tuned) | Higher (8-15) for notebooks with many sources; see `cluster_transcripts.py --min-cluster-size` |
| Synthesis LLM backend | mmx (MiniMax-M2.7) | `--synth-backend dgemma` for the free fallback; switch if pages are thin |
| Vision enrichment | Off (opt-in `--enrich-vision`) | Enable for notebooks with visual content (tutorials, demos); talking-head videos auto-skip |
| Scene-change threshold | 10 keyframes | `enrich_vision.py --threshold`; lower to enrich more videos |
| Similarity threshold for `refines` | 0.75 (cosine on embeddings) | `--threshold 0.85` for stricter matching |
| Notebook profile | `codex` on this host | Matches `[[nlm-bulk-ingest]]` default |

## Provenance model (4-hop chain)

Every emitted wiki page carries provenance back to the original source URL:

```yaml
provenance:
  chain:
    - level: concept
      id: <wiki-slug>
    - level: notebook
      id: <notebook-uuid>
      title: <notebook-title>
      url: https://notebooklm.google.com/notebook/<uuid>
    - level: cluster         # only when --from-clusters used
      id: <cluster-id>
      name: <cluster-name>
      source_path: clusters.json
    - level: source_url      # only when --from-clusters used
      url: https://www.youtube.com/watch?v=...
      title: <video title>
      channel: <channel>
  cited_text:
    - claim: "<specific claim text>"
      source_id: "<nlm source uuid>"
      expanded_context: "<full paragraph from source fulltext>"
      source_urls:           # which original URLs contributed this source
        - https://...
```

A reader can click from any wiki concept → notebook → cluster → exact YouTube video.

## Operational gotchas (inherited)

All the [[notebooklm-cli-operational-gotchas]] apply:
- `nlm login --check` lies about auth; `nlm login --profile <name>` recovers silently
- `nlm source content` is rate-limited; export_transcripts paces at 1.5s spacing by default (`--spacing`)
- `nlm source content` returns the raw indexed text — no AI processing; this is the correct v3 primitive
- Large notebooks (191+ sources) take ~5-10 min to export; crash-resumable (re-run skips completed sources)

## Validation gate

Every page MUST pass `validate_wiki_entry.py` before the sync reports success.
The validator is the wiki skill's mandatory gate. Pages that fail are held in
a staging dir and reported at the end of sync; the operator decides whether to
fix or discard.

## Re-sync semantics

The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records
`source_ids` per notebook. On re-sync:

- Source IDs unchanged → skip export entirely, report "no new sources"
- Source IDs changed → re-export + re-cluster + re-synthesize, then dedup
  against existing pages (refines any that already exist from prior sync)

This makes `nlm-to-wiki sync` idempotent and safe to schedule.

## References

- `references/extraction-prompts.md` — Report + Data-Table prompt templates
- `references/frontmatter-mapping.md` — how nlm response → wiki SCHEMA frontmatter
- `references/provenance-model.md` — full 4-hop chain spec
- `references/dedup-policy.md` — the refines branching logic
- `[[nlm-bulk-ingest]]` — ingest direction (URL list → notebooks)
- `[[notebooklm-cli-operational-gotchas]]` — auth, bulk, cosmetic errors
- `[[notebooklm-source-limits-free-vs-paid]]` — capacity
