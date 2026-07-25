---
name: nlm-to-wiki
description: >
  Sync NotebookLM notebook content into the wiki vault as SCHEMA-compliant
  concept pages with full 4-hop provenance (concept → notebook → cluster →
  original source URL). Uses Report + Data-Table artifacts (not chat) for
  structured, citable extraction. Branches as `refines` on collision with
  existing concepts rather than overwriting. Composes with nlm-bulk-ingest
  via --from-clusters for full round-trip from raw URL list to wiki concepts.
host: both
---

# nlm-to-wiki

Pull concepts out of NotebookLM notebooks into the wiki, with provenance
that lets a reader click from any claim back to the exact source video or
URL the concept came from.

Built to round-trip with `[[nlm-bulk-ingest]]`:

```
URL list → nlm-bulk-ingest → 15 notebooks → nlm-to-wiki → ~50-150 wiki concept pages
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

## The pipeline (6 stages)

```
INPUT                     AUTH + SNAPSHOT
──notebook <id>           ────────────────
──all                     ensure auth (CDP silent re-auth)
──from-clusters <path>    snapshot current source_ids for re-sync gate
                                          │
                                          ▼
                          EXTRACT (Stage A)
                          ─────────────────
                          nlm report create --format "Create Your Own"
                            (concept extraction prompt, 5-15 min)
                          nlm data-table create
                            (tabular facts, 5-15 min)
                          poll studio status until both complete
                                          │
                                          ▼
                          PARSE (Stage B)
                          ───────────────
                          parse report markdown → concept records
                          parse data-table CSV → fact records
                          merge: each concept absorbs matching facts
                                          │
                                          ▼
                          RECONCILE (Stage C)
                          ────────────────
                          for each candidate concept:
                            qmd search vault for similar concepts
                            if similarity ≥ threshold:
                              mark as `refines <existing>`
                            else:
                              mark as new
                                          │
                                          ▼
                          EXPAND CITATIONS (Stage D)
                          ─────────────────────────
                          for each cited_text span:
                            SourceFulltext.find_citation_context()
                            expand to full surrounding paragraph
                                            │
                                            ▼
                          WRITE (Stage E)
                          ────────────────
                          emit SCHEMA-compliant frontmatter
                          (passes validate_wiki_entry.py)
                          atomic write per page
                                            │
                                            ▼
                          LINK + LOG (Stage F)
                          ────────────────────
                          wiki_after_write.py for [[wikilinks]]
                          append to wiki log
                          update sync manifest
```

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

# Dry run — parse + reconcile, no writes
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid> \
    --dry-run

# Re-sync (skips notebooks whose source_ids haven't changed)
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py \
    --notebook <uuid> \
    --resync
```

## Decision points

| Decision | Default | When to change |
|---|---|---|
| Extraction primitive | Report + Data-Table hybrid | `--quick` flag falls back to chat query for fast iteration |
| Similarity threshold for `refines` | 0.75 (cosine on embeddings) | `--threshold 0.85` for stricter matching; `--threshold 0.6` for more aggressive branching |
| Notebook profile | `codex` on this host | Matches `[[nlm-bulk-ingest]]` default |
| Vault target | `P:/.data/wiki/concepts/` | Override via `--vault <path>` for testing |
| Concepts per notebook | 5-20 (extraction prompt enforces) | Edit prompt in `references/extraction-prompts.md` |

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
- Studio generation has rate limits; retry with exponential backoff
- `cited_text` from query responses is a snippet, not a full passage — Stage D expands it

## Validation gate

Every page MUST pass `validate_wiki_entry.py` before the sync reports success.
The validator is the wiki skill's mandatory gate. Pages that fail are held in
a staging dir and reported at the end of sync; the operator decides whether to
fix or discard.

## Re-sync semantics

The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records
`source_ids` per notebook. On re-sync:

- Source IDs unchanged → skip extraction entirely, report "no new sources"
- Source IDs changed → re-extract, then dedup against existing pages (refines
  any that already exist from prior sync)

This makes `nlm-to-wiki sync` idempotent and safe to schedule.

## References

- `references/extraction-prompts.md` — Report + Data-Table prompt templates
- `references/frontmatter-mapping.md` — how nlm response → wiki SCHEMA frontmatter
- `references/provenance-model.md` — full 4-hop chain spec
- `references/dedup-policy.md` — the refines branching logic
- `[[nlm-bulk-ingest]]` — ingest direction (URL list → notebooks)
- `[[notebooklm-cli-operational-gotchas]]` — auth, bulk, cosmetic errors
- `[[notebooklm-source-limits-free-vs-paid]]` — capacity
