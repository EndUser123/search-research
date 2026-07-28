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
# DEFAULT (no args): list notebooks with sync status, then pick one
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py
# → prints a status table (notebook × synced/transcripts/pages)
# → run again with --notebook <id> to sync the one you want

# Status only (no sync)
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py --status
python P:/.agents/skills/nlm-to-wiki/scripts/sync.py --status --min-sources 50

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

## Agent invocation pattern (when invoked as `/nlm-to-wiki`)

**Step 0 — help short-circuit.** If the argument is `-h`, `-help`, `--help`,
or `help` (case-insensitive), read `references/help.md` and present its
contents (Quick reference table, Common questions, Troubleshooting). Do NOT
run the sync pipeline, call `nlm`, or ask which notebook to sync. Stop after
presenting the help resource. This makes `/nlm-to-wiki -h` the fast path for
"how do I use this?" without side effects.

**Step 1 — no args: status picker.** When invoked without a target notebook
(and not a help request), the agent should:

1. Run `python sync.py --status` to produce the notebook status table.
2. Use `ask_user_question` to let the operator pick. Offer common choices:
   - The notebook with the most unsynced sources
   - Any notebook already partially synced (transcripts > 0, pages = 0)
   - "All qualifying notebooks" (`--all` with `--min-sources` filter)
   - Other (operator types a notebook ID)
3. On selection, run `python sync.py --notebook <id> --dry-run` first, then
   the full sync if the dry-run output looks right.

Do not auto-run `--all` without explicit operator confirmation — 87
notebooks at ~15-25 min each is multi-hour work.

For the full cheat-sheet, FAQ, and troubleshooting table, see
`references/help.md` (or run `/nlm-to-wiki -h`). Key pointer: auth expiry
recovers silently via `nlm login --profile codex` (~10s, no operator
intervention).

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

## Bulk ingestion (queue-of-work pattern)

For syncing many notebooks in parallel, use the queue-of-work worker at
`scripts/bin/queue_sync.py`. It decouples work distribution from execution:
a JSON queue file holds the pending notebooks, and independent worker
processes claim items, sync them, and report results.

```bash
# Populate the queue from NotebookLM (notebooks with ≥50 sources)
python scripts/bin/queue_sync.py --enqueue --profile codex

# Populate from BOTH accounts (paid + free) in one call
python scripts/bin/queue_sync.py --enqueue --all-profiles

# Start a worker (run 2-3 of these in separate terminals)
python scripts/bin/queue_sync.py --worker --worker-id w1 --profile codex
python scripts/bin/queue_sync.py --worker --worker-id w2 --profile codex

# Check progress
python scripts/bin/queue_sync.py --status

# Retry failed items (moves them back to pending)
python scripts/bin/queue_sync.py --retry-failed
```

**Multi-profile support (two NotebookLM accounts):**

This host has two NotebookLM accounts configured as named profiles:

| Profile | Email | Tier | Max sources/notebook |
|---------|-------|------|---------------------|
| `codex` | a.hominidae@gmail.com | Paid | 300 |
| `troup.hominidae` | troup.hominidae@gmail.com | Free | 50 |
| `brsthomson` | brsthomson@hotmail.com | Free | 50 |

Each profile is an independent CDP session — they do NOT contend for auth.
Workers can freely process notebooks from either account. Use `--all-profiles`
on enqueue to discover notebooks from all three accounts. Each notebook in the
queue is tagged with its source profile; workers automatically pass the
correct profile to `sync.py`.

**Worker ceiling: 3 concurrent workers per account.** The NotebookLM API
degrades above 3 concurrent sessions per account. With 3 accounts (1 paid + 2
free), you can run up to 9 workers total (3 per account). The yt-is benchmark
measured 4,123 VPH at 3+3 workers on one account; 4+4 regressed to 1,150 VPH.
Set `config.workers` in the queue file to the total number of worker
processes you launch. See [[nlm-to-wiki-optimization-opportunities]].

**One-time setup for free profiles:** the profiles were created by copying
credentials from yt-is worker profiles. If auth expires and silent CDP
re-auth fails (Chrome doesn't have the session), run for each:
```bash
nlm login --profile troup.hominidae
nlm login --profile brsthomson
```
Each opens a browser window — sign in as the respective account.
After the one-time login, subsequent re-auth is silent via CDP.

**⚠ Auth contention (critical):** never run two different sync drivers
concurrently (e.g., `sync.py --all` alongside queue workers). Each
`nlm login --profile codex` call invalidates the previous CDP session.
Two drivers both calling `nlm login` will silently invalidate each other's
auth, producing 0-page failures with no error. The queue worker is the
single approved parallel driver — do not mix it with `--all` or manual
`sync.py` runs. See [[concurrent-cdp-auth-contention]].

**Durable locations:** the queue file lives at
`P:/.data/wiki/_state/nlm-sync/queue.json` (not `P:/tmp/` — other agents
clean tmp). The worker script lives at
`P:/.agents/skills/nlm-to-wiki/scripts/bin/queue_sync.py`.

## Operational gotchas (inherited)

All the [[notebooklm-cli-operational-gotchas]] apply:
- `nlm login --check` lies about auth; `nlm login --profile <name>` recovers silently
- `nlm source content` is rate-limited; export_transcripts paces at 1.5s spacing by default (`--spacing`)
- `nlm source content` returns the raw indexed text — no AI processing; this is the correct v3 primitive
- **rc=5 from export is non-fatal:** individual source failures (rc=5) are logged and skipped; the sync continues. Only rc=2 (no sources / auth failure) aborts.
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

## Maintenance and cleanup

The skill accumulates state: the manifest (`_state/nlm-sync-manifest.json`),
transcript files (`sources/transcripts/`), concept pages (`concepts/`), and
keyframes (`sources/keyframes/`). Notebooks get deleted, sources get removed,
v2→v3 migrations leave stale slugs. `maintenance.py` audits and repairs.

```bash
# Audit (read-only, safe) — report all mismatches
python P:/.agents/skills/nlm-to-wiki/scripts/maintenance.py --audit

# Status + audit in one pass (the routine health check)
python P:/.agents/skills/nlm-to-wiki/scripts/maintenance.py --audit --disk-report

# Fix stale manifest concept_slugs (pages deleted but slugs remain)
python maintenance.py --fix-stale-slugs --confirm

# Remove transcripts whose notebook was deleted from NotebookLM
python maintenance.py --remove-orphaned-transcripts --confirm

# Prune ALL state for a deleted notebook (manifest + transcripts + concept pages)
# Concept pages are moved to _state/nlm-trash/<uuid>/, not deleted outright.
python maintenance.py --prune-notebook <uuid> --confirm

# Apply all safe fixes in one pass
python maintenance.py --all-fixes --confirm
```

**Safety model:** every destructive command requires `--confirm`. Without it,
the command runs as a dry-run and reports what it *would* change. `--prune-notebook`
is the most destructive (removes concept pages too) — concept pages are moved
to `_state/nlm-trash/<uuid>/` for recovery, never outright deleted.

**When to run maintenance:**

| Trigger | Command |
|---|---|
| After deleting wiki concept pages manually | `--fix-stale-slugs` clears dangling manifest refs |
| After a notebook is deleted from NotebookLM | `--remove-orphaned-transcripts` + `--prune-notebook <id>` |
| Monthly health check | `--audit --disk-report` (read-only) |
| Before a large re-sync | `--all-fixes` to start from clean state |
| Disk pressure on `sources/` | `--disk-report` shows per-notebook transcript size |

## References

- `references/help.md` — quick reference, FAQ, troubleshooting (start here for "how do I…" questions)
- `references/provenance-model.md` — full 4-hop chain spec
- `references/dedup-policy.md` — the refines branching logic
- `references/extraction-prompts.md` — ⚠ STALE (v2 Report+Data-Table prompts; superseded by transcript export)
- `references/frontmatter-mapping.md` — ⚠ STALE (v2 Report→frontmatter mapping; superseded by write_pages.py transcript-cluster mode)
- `[[nlm-bulk-ingest]]` — ingest direction (URL list → notebooks)
- `[[notebooklm-cli-operational-gotchas]]` — auth, bulk, cosmetic errors
- `[[video-to-wiki-pipeline-transcript-extraction-multimodal]]` — v3 architecture rationale
- `[[notebooklm-source-limits-free-vs-paid]]` — capacity
