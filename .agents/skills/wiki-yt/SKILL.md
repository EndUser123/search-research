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

Built to round-trip with `/nlm-bulk-ingest`:

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
| Add URLs to a notebook | `/nlm-bulk-ingest` (ingest direction) |
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

### yt-is cache-first forward sync

When exporting source transcripts, `scripts/export_transcripts.py` builds the
yt-is title bridge once and checks
`scripts/yt_is_forward_sync.py` before calling NotebookLM. A hit reads the
canonical yt-is transcript cache; a miss or provider error fails through to
the existing NotebookLM path. The behavior is intentionally best-effort and
must never turn a cache problem into a pipeline-wide failure.

The export result also carries a deterministic `export_receipt` with
`cache_hit_count`, `cache_miss_count`, `cache_unresolved_count`,
`feed_forward_success_count`, and `feed_forward_failure_count` (while
preserving `from_cache_count`). After page validation succeeds, `sync.py`
copies that receipt into both the returned sync result and the per-notebook
manifest entry. Do not treat these counters as live ROI or source-coverage
proof; they are operational provenance for a specific export.

Offline regression coverage is in
`P:/.agents/skills/wiki-yt/tests/test_forward_sync.py`; run it with
`python -m pytest P:/.agents/skills/wiki-yt/tests/test_forward_sync.py P:/.agents/skills/wiki-yt/tests/test_ytis_nlm.py -q`.
This test boundary does not prove live overlap or ROI; do not quote savings
without a fresh source-inventory comparison.

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

# Local maintenance audit without a live NotebookLM inventory query
python P:/.agents/skills/wiki-yt/scripts/maintenance.py --audit --offline

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

# Explicitly rebuild semantic pages even when source_ids are unchanged
python P:/.agents/skills/wiki-yt/scripts/sync.py \
    --notebook <uuid> --force-resynthesis --synth-backend mmx
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

# Retry failed items (moves them back to pending only when every record has an
# exact canonical account profile; profileless legacy records fail closed)
python scripts/bin/queue_sync.py --retry-failed

# Retry a named degraded page through a semantic backend; the deferred record
# remains until a true semantic sync succeeds.
python scripts/bin/queue_sync.py --retry-deferred \
    --notebook-id <uuid> --synth-backend mmx --timeout-s 1200 \
    --max-attempts 1
```

For a bounded deferred retry, `--max-attempts 1` is the default and should be
left explicit in the packet. It prevents a failed semantic item from being
silently re-run by the queue's broader retry policy. If a worker process dies
after claiming an item, first verify the recorded PID is gone, then release
the claim with the dead-worker recovery command; it refuses to touch a live
PID and records the recovery in queue history:

```powershell
python P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py `
  --recover-worker --worker-id <worker-id>
```

Add `--requeue-orphan` only when a fresh packet explicitly authorizes retrying
the recovered item. The default records the orphaned claim as failed and
preserves any separate `needs_resynthesis` obligation. Do not delete or edit
queue claims by hand.

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

## Synthesis quality gate

The synthesis stage is fail-closed for provenance quality. A concept is not
accepted when its JSON has no citations, an empty claim or excerpt, or a
citation that cannot resolve to one of the cluster's source IDs/titles. The
synthesizer emits `FAILURE_CLASS=citation_invalid` for that case. If map-reduce
pre-summarization falls back to transcript heads, it emits
`FAILURE_CLASS=synthesis_degraded` instead of presenting the degraded context
as a successful synthesis. `queue_sync.py` preserves those stable classes in
the retry record. Backend exhaustion is recorded as
`synthesis_backend_exhausted` rather than generic `rc=1`. These failures remain
retryable; they never authorize page writes, manifest advancement, or
`[INGESTED]` renaming.

There is one explicit, lower-quality recovery path for a named poisoned item:
`--synth-backend deterministic --allow-degraded-fallback`. It emits only
bounded, whitespace-normalized excerpts selected from the exact local
transcripts, with source-ID citations, no invented values, a
`degraded-fallback` page tag, `provenance_status`, and manifest quality counts.
The queue records `synced_degraded_fallback`, never ordinary `synced`, and adds
the item to `needs_resynthesis`. That quality-debt record survives queue
reloads and is not silently treated as semantic completion. The
path is opt-in per exact retry packet; it is not the default backlog policy.
It may advance only after every page passes the normal citation and wiki
validator gates and the child emits `DEGRADED_FALLBACK_PROMOTED=1`. Missing
transcripts, invalid citations, or an unapproved fallback remain poisoned.

Poisoned items are not included in `--retry-failed` automatically. A bounded
alternate-backend retry must name the exact notebook IDs:

```powershell
python P:/.agents/skills/wiki-yt/scripts/bin/queue_sync.py `
  --retry-poisoned --notebook-id <UUID> --synth-backend dgemma `
  --timeout-s 1200 --synth-checkpoint-dir P:/.logs/wiki-yt-queue/checkpoints
```

When `--synth-checkpoint-dir` is supplied, the queue writes one durable
checkpoint path per exact notebook. The worker passes `--synth-checkpoint` on
the first attempt and `--synth-resume` on later attempts when that file exists.
Checkpoint records are identity-validated against the regenerated subtopics
and notebook; a mismatch fails closed rather than reusing stale synthesis.
This is progress protection, not permission to retry a poisoned item more than
once or to weaken citation validation.

For an explicitly approved excerpt-only recovery, use the same exact-ID form
with `--synth-backend deterministic --allow-degraded-fallback` and record why
semantic LLM synthesis is not required for that item.

The reopen operation is queue-lock protected, moves the prior poison record to
`poisoned_history`, and carries the selected backend to the child `sync.py`
command. It is a diagnostic recovery operation, not permission to reopen the
whole poison set repeatedly. Reconcile queue, manifest, page validation, and
raw worker logs after the run; a nonzero result remains poisoned.

`--retry-poisoned` enables `--force-resynthesis` by default. This bypasses only
the source-ID hash skip; it does not bypass transcript, citation, page
validation, account-auth, or queue-lock gates. Use it for an exact named
poisoned notebook after selecting a backend and recording a bounded retry
packet. `--timeout-s` records an explicit per-item deadline on the reopened
queue record; the worker launches the sync in an owned process group and kills
the entire descendant tree when the deadline expires, preserving stdout/stderr
and recording a timeout failure. A timeout, missing output, or child
termination is a blocked retry, not a successful fallback and must not be
converted to a queue completion.

`--retry-deferred` is the corresponding bounded path for a page that was
already promoted through explicit degraded fallback. It requires an exact
canonical profile and an LLM backend (`mmx` or `dgemma`), carries
`--force-resynthesis` and the selected timeout into every automatic retry, and
keeps the deferred record until the child reports a true `synced` result. It
does not re-add the item to the ordinary discovery queue or reopen an active
poisoned item; reconcile a bounded failure through the explicit poisoned path.

Each queue completion or failure stores the stdout/stderr receipt paths in the
durable queue record. This is the authoritative bridge for future
manifest-reconciliation audits; it does not repair historical gaps whose exact
worker/profile/attempt receipt is absent.

Stage E is transactional at the validation boundary. Candidate pages are
written under the run-scoped same-volume directory
`P:/.data/wiki/_state/nlm-sync-staging/<notebook-prefix>-<run-id>/`; canonical
concept pages are not promoted until every candidate passes the normal wiki
validator. On validation failure, leave the candidates for diagnosis and keep
the canonical pages and manifest unchanged. A promotion failure is also a
failed sync and requires reconciliation before retrying.

## Reconciled historical synthesis state (2026-08-12)

The following supersedes the older retry notes above. The authoritative queue
now reports `pending=0`, `in_progress=0`, `poisoned=0`,
`needs_resynthesis=0`, `completed=47`, and `failed=2`. The two remaining
failures are profileless legacy records with `0 pages`; they remain
`deferred_missing_failure_evidence` and must not be retried without an exact
worker/profile/attempt receipt.

The three previously poisoned notebooks now have final semantic `synced`
records, and their current manifests and pages reconcile:

- `c8b07a4c-607c-4ddc-94be-688206daf737`: 38/38 transcripts and 4 current
  `llm_validated` pages; see the run11 worker receipt under
  `P:/.logs/wiki-yt-queue/20260810/`.
- `f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2`: 27/27 transcripts and 2 current
  `llm_validated` pages; see the run06 worker receipt under
  `P:/.logs/wiki-yt-queue/20260810/`.
- `4017aa6e-35fb-426d-bc53-34620bec405e`: 36/36 transcripts and 5
  `llm_validated` pages after the MMX checkpoint-resume run16; see
  `P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-final-resume-run16-4017aa6e-35fb-426d-bc53-34620bec405e-1786459045419236800.stdout.log`.

The run16 receipt reports `citation_rate=52.8%`; do not describe that notebook
as having complete citation coverage merely because all five pages passed
validation. Eight older degraded-fallback pages remain on disk but are not in
the current manifests; the manifest auditor now reports them explicitly as
`degraded_page_slug_missing_from_manifest`. Preserve them for a separately
reviewed cleanup packet.

The read-only historical audit still reports 13 manifest gaps and zero safe
repairs. Twelve have output/provenance without an exact receipt, and one has
no local output evidence. Never reconstruct a manifest entry from output alone.
The governing audit is
`P:/.logs/wiki-yt-queue/20260812/manifest_gap_audit_current_after_goal_continuation.md`.

## Concurrent manifest writes

`sync.py` writes `P:/.data/wiki/_state/nlm-sync-manifest.json` through a
per-file `fasteners.InterProcessLock`, reloads the latest manifest while holding
that lock, and merges the completed notebook update before the atomic replace.
This is required because multiple account workers may finish at the same time;
an atomic replace without the locked reload can still lose a sibling worker's
successful entry. `maintenance.py` uses the same lock for confirmed repairs and
prunes, and reloads before applying its mutation.

The manifest is a state receipt, not the sole proof of a completed queue item.
After a concurrent run, reconcile queue completion records, exact worker logs,
transcript frontmatter, and manifest entries. Do not fabricate missing entries
from a queue title alone. Historical queue records without an unambiguous
successful receipt remain an explicit audit gap.

For historical gaps, use the read-only auditor before considering any repair:

```powershell
python P:/.agents/skills/wiki-yt/scripts/audit_manifest_gaps.py `
  --output P:/.logs/wiki-yt-queue/<date>/historical_manifest_gap_audit.json
```

The auditor parses exact transcript frontmatter and exact concept provenance;
it does not treat arbitrary ID mentions or its own markdown packets as output
evidence. `output_provenance_found_receipt_missing` means local transcript and
concept output exists but the worker/profile receipt is absent. That status is
not eligible for manifest recovery. Only a separately reviewed packet with an
exact worker receipt, profile, attempt, successful output, and source identity
may authorize a guarded manifest repair. The normal result for incomplete
historical evidence is an explicit audit gap, not a synthesized manifest row.

The current historical audit found 13 gaps: 12 have local output/provenance but
no exact worker/profile/attempt receipt, and one has no local output. None is
eligible for automatic manifest repair. Preserve those gaps as quarantine
records until an exact receipt is recovered; never infer ownership or
completion from a title, page, or queue row alone.

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

# Offline audit (local state only; never classifies live orphans)
python P:/.agents/skills/wiki-yt/scripts/maintenance.py --audit --offline

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
`--offline` skips the live NotebookLM inventory query and is valid for local
audits and stale-slug repairs only; it cannot be combined with
`--remove-orphaned-transcripts` or `--all-fixes` because those operations need a
verified live notebook set.

Confirmed maintenance that moves transcripts or concept pages is queue-exclusive:
wait for `queue_sync.py --status` to show no pending or in-progress work before
running it. The manifest lock prevents writer races, but it cannot make a
concurrent file move and sync safe.

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
- `/nlm-bulk-ingest` — ingest direction (URL list → notebooks)
- `[[notebooklm-cli-operational-gotchas]]` — auth, bulk, cosmetic errors
- `[[video-to-wiki-pipeline-transcript-extraction-multimodal]]` — v3 architecture rationale
- `[[notebooklm-source-limits-free-vs-paid]]` — capacity
