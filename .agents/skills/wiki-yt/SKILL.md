---
name: wiki-yt
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
domain: knowledge
---

# wiki-yt

Pull concepts out of NotebookLM notebooks into the wiki, with provenance
that lets a reader click from any claim back to the exact source video or
URL the concept came from.

Built to round-trip with `[[nlm-bulk-ingest]]`:

```
URL list → nlm-bulk-ingest → 15 notebooks → wiki-yt → ~5-15 sub-topic
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
──all                     read-only canonical account/session probe
──from-clusters <path>    snapshot current source_ids for re-sync gate
                                          │
                                          ▼
                          EXPORT TRANSCRIPTS (Stage A)
                          ─────────────────────────────
                          for each source: YTIS direct source fulltext API
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
                            CONTEXT STRATEGY (auto-selected):
                              total < 300K chars → FULL transcripts
                              total > 300K chars → map-reduce:
                                pre-summarize each transcript, then synthesize
                              single transcript > 200K chars → overlapping chunks
                                (200K chunks, 20K = 10% overlap)
                            each claim cites source_id + title + excerpt
                                          │
                                          ▼
                          RECONCILE (Stage D)
                          ────────────────
                          for each candidate concept:
                            grep vault for similar concepts (keyword match)
                            if title/tags overlap ≥ threshold:
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
python P:/.agents/skills/wiki-yt/scripts/sync.py
# → prints a status table (notebook × synced/transcripts/pages)
# → run again with --notebook <id> to sync the one you want

# Status only (no sync)
python P:/.agents/skills/wiki-yt/scripts/sync.py --status
python P:/.agents/skills/wiki-yt/scripts/sync.py --status --min-sources 50

# Sync one notebook (the canonical case)
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --notebook <uuid> \
    --account-profile a.hominidae

# Sync all notebooks (sequential; ~10-30 min each)
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --all \
    --account-profile a.hominidae \
    --state sync-state.json

# Round-trip from nlm-bulk-ingest output
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --from-clusters clusters.json \
    --account-profile a.hominidae \
    --state sync-state.json

# Dry run — export + cluster + synthesize + reconcile, no page writes
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --notebook <uuid> \
    --dry-run

# Re-sync (skips notebooks whose source_ids haven't changed)
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --notebook <uuid>

# v3: with optional vision enrichment + custom sub-topic count
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --notebook <uuid> \
    --enrich-vision --max-subtopics 12 --synth-backend mmx
```

## Agent invocation pattern (when invoked as `/wiki-yt`)

**Step 0 — help short-circuit.** If the argument is `-h`, `-help`, `--help`,
or `help` (case-insensitive), read `references/help.md` and present its
contents (Quick reference table, Common questions, Troubleshooting). Do NOT
run the sync pipeline, call `nlm`, or ask which notebook to sync. Stop after
presenting the help resource. This makes `/wiki-yt -h` the fast path for
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
`references/help.md` (or run `/wiki-yt -h`). Authentication is fail-closed and
durably non-interactive: the bridge probes the exact canonical account, then
refreshes it from the account's master token or uses the established dedicated
headless CDP bootstrap path. It never invokes a shared/default-profile login or
asks the operator to sign in during a pipeline run.

## Decision points

| Decision | Default | When to change |
|---|---|---|
| Extraction primitive | YTIS direct source fulltext API (raw indexed transcript) | — (v2 Report+Data-Table was wrong; superseded) |
| Sub-topic cluster count | 10 (`--max-subtopics`) | 5-15 range; raise for broader themes, lower for granular concepts |
| HDBSCAN min_cluster_size | 5 (transcript-tuned) | Higher (8-15) for notebooks with many sources; see `cluster_transcripts.py --min-cluster-size` |
| Synthesis LLM backend | mmx (MiniMax-M2.7) | `--synth-backend dgemma` for the free fallback; switch if pages are thin |
| Context per transcript | 0 = full text (default since 2026-08-01) | `--per-member-chars 1200` for legacy truncation; 0 uses map-reduce when over budget |
| Context budget | 300,000 chars | `--context-budget N` to adjust the map-reduce trigger threshold |
| Overlap for large transcripts | 200K chunk + 20K overlap (10%) | Automatic — fires for single transcripts > 200K chars |
| Vision enrichment | Off (opt-in `--enrich-vision`) | Enable for notebooks with visual content (tutorials, demos); talking-head videos auto-skip |
| Scene-change threshold | 10 keyframes | `enrich_vision.py --threshold`; lower to enrich more videos |
| Similarity threshold for `refines` | 0.75 (cosine on embeddings) | `--threshold 0.85` for stricter matching |
| Notebook account | `a.hominidae` on this host | Exact identity; `--profile` is a compatibility alias for `--account-profile` |

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
python scripts/bin/queue_sync.py --enqueue --account-profile a.hominidae

# Populate from BOTH accounts (paid + free) in one call
python scripts/bin/queue_sync.py --enqueue --all-profiles --workers 9

# Start a worker (run 2-3 of these in separate terminals)
python scripts/bin/queue_sync.py --worker --worker-id w1 --account-profile a.hominidae
python scripts/bin/queue_sync.py --worker --worker-id w2 --account-profile a.hominidae

# Check progress
python scripts/bin/queue_sync.py --status

# Retry failed items (moves them back to pending)
python scripts/bin/queue_sync.py --retry-failed
```

**Account identities and canonical auth:**

This host has three NotebookLM accounts. They are exact external identities,
not worker labels or CLI profile stores:

| Profile | Email | Tier | Max sources/notebook |
|---------|-------|------|---------------------|
| `a.hominidae` | a.hominidae@gmail.com | Paid | 300 |
| `troup.hominidae` | troup.hominidae@gmail.com | Free | 50 |
| `brsthomson` | brsthomson@hotmail.com | Free | 50 |

The active bridge resolves these identities to the YTIS-owned storage files:

| Account | Canonical storage |
|---|---|
| `a.hominidae` | `P:/.data/yt-is/nlm-auth/storage_state.json` |
| `troup.hominidae` | `P:/.data/yt-is/nlm-auth/storage_state_troup_hominidae.json` |
| `brsthomson` | `P:/.data/yt-is/nlm-auth/storage_state_brsthomson.json` |

`scripts/ytis_nlm.py` is the only wiki-yt auth bridge. It imports the
package-owned YTIS resolver, validates the embedded account email, repairs the
exact account through `ensure_account_session()`, and opens the direct
`notebooklm-py` client. A worker label can be used for telemetry only; it never
selects auth state. The durable master-token files live under
`P:/.data/yt-is/nlm-auth/master-tokens/` and are never shared between accounts.

Use `--all-profiles` to discover notebooks from all three accounts. Each queue
item retains its exact account identity and workers pass it to `sync.py` as
`--account-profile`.

**Worker ceiling: 3 concurrent workers per account.** The NotebookLM API
degrades above 3 concurrent sessions per account. With 3 accounts (1 paid + 2
free), you can run up to 9 workers total (3 per account). The yt-is benchmark
measured 4,123 VPH at 3+3 workers on one account; 4+4 regressed to 1,150 VPH.
Set the total queue capacity with `--workers` when enqueueing (or edit
`config.workers` deliberately before launching workers). The queue enforces
both this global ceiling and each account's `max_workers` limit under its lock;
starting extra worker processes does not bypass either limit. See
[[nlm-to-wiki-optimization-opportunities]].

**Durable authentication:** an expired or unusable canonical session triggers
the account-specific non-interactive repair path. It first uses the matching
master token and then, only when no token exists, the established dedicated
headless CDP family. If both fail, the pipeline stops with the exact account
and reason; it does not open a login window, invoke the legacy `nlm` CLI, copy a
different account's storage, or infer success from a static file check.

Multiple workers may use separate canonical account files, subject to the
account's measured concurrency limits. The direct client removes the old CDP
login-contention mechanism, but it does not authorize unlimited concurrency.

**Durable locations:** the queue file lives at
`P:/.data/wiki/_state/nlm-sync/queue.json` (not `P:/tmp/` — other agents
clean tmp). Claims contain the exact account, lease ID, worker ID, UTC start
time, epoch start time, and PID. A worker reclaims only expired ISO/epoch
leases; legacy time-only claims are retained rather than guessed. The worker
script lives at
`P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py`.

## Operational gotchas (inherited)

The direct-client operational rules apply:
- `ensure_account_session()` is the auth gate; it attempts account-scoped
  master-token repair and exceptional dedicated-CDP bootstrap, then fails
  closed if the exact account remains unavailable.
- Source fulltext calls are rate-limited; `export_transcripts` paces at 1.5s spacing by default (`--spacing`).
- Source fulltext returns raw indexed text — no AI processing; this is the correct v3 primitive.
- **rc=5 from export is partial, not success:** completed transcripts are
  preserved for resume, but sync does not cluster, write a manifest, rename
  the notebook, or mark it complete. The queue records a retryable failure.
- Large notebooks (191+ sources) take ~5-10 min to export; crash-resumable (re-run skips completed sources)

## Validation gate

Every page MUST pass `validate_wiki_entry.py` before the sync reports success.
The validator is the wiki skill's mandatory gate. Pages that fail are held in
a staging dir, the sync returns nonzero, and no manifest or `[INGESTED]` rename
is written. Already-written valid pages remain durable and the queue retries
the notebook without treating the partial result as complete.

## Re-sync semantics

The sync manifest at `P:/.data/wiki/_state/nlm-sync-manifest.json` records
`source_ids` per notebook. On re-sync:

- Source IDs unchanged → skip export entirely, report "no new sources"
- Source IDs changed → re-export + re-cluster + re-synthesize, then dedup
- A source-list failure is distinct from an empty source list and fails closed;
  it never creates an empty hash that can accidentally authorize a skip.
  against existing pages (refines any that already exist from prior sync)

This makes `wiki-yt sync` idempotent and safe to schedule.

## Maintenance and cleanup

The skill accumulates state: the manifest (`_state/nlm-sync-manifest.json`),
transcript files (`sources/transcripts/`), concept pages (`concepts/`), and
keyframes (`sources/keyframes/`). Notebooks get deleted, sources get removed,
v2→v3 migrations leave stale slugs. `maintenance.py` audits and repairs.

```bash
# Audit (read-only, safe) — report all mismatches
python P:/.agents/skills/wiki-yt/scripts/maintenance.py --audit

# Status + audit in one pass (the routine health check)
python P:/.agents/skills/wiki-yt/scripts/maintenance.py --audit --disk-report

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
