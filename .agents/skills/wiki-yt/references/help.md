# wiki-yt — Help resource

Quick reference, common questions, and troubleshooting for the wiki-yt
skill. Loaded on demand; SKILL.md carries the entry-point summary.

All commands run from `P:/.agents/skills/wiki-yt/scripts/`. The default
account identity is `a.hominidae` (= `a.hominidae@gmail.com` on this host).

## Quick reference

| Task | Command |
|---|---|
| List notebooks + sync status (the default) | `python sync.py` or `python sync.py --status` |
| Sync one notebook | `python sync.py --notebook <uuid>` |
| Dry run (no page writes) | `python sync.py --notebook <uuid> --dry-run` |
| Force semantic rebuild | `python sync.py --notebook <uuid> --force-resynthesis --synth-backend mmx` |
| Sync with vision enrichment | `python sync.py --notebook <uuid> --enrich-vision` |
| Re-sync (skips unchanged) | `python sync.py --notebook <uuid>` |
| Round-trip from bulk-ingest clusters | `python sync.py --from-clusters clusters.json` |
| Audit state (read-only) | `python maintenance.py --audit` |
| Disk usage per notebook | `python maintenance.py --disk-report` |
| Fix stale manifest slugs | `python maintenance.py --fix-stale-slugs --confirm` |
| Prune a deleted notebook's state | `python maintenance.py --prune-notebook <uuid> --confirm` |
| Check canonical auth | `python -c "from ytis_nlm import probe_account_session; print(probe_account_session('a.hominidae'))"` |
| Repair canonical auth | `python -c "from ytis_nlm import ensure_account_session; print(ensure_account_session('a.hominidae'))"` (non-interactive durable repair) |
| Repair all exact YTIS accounts | `python P:/packages/yt-is/bin/csf-nlm-auth --all` (credential-free JSON; exit 2 if any account remains unavailable) |
| Bulk ingestion (queue worker) | `python scripts/bin/queue_sync.py --worker --worker-id w1` |
| Enqueue from both accounts | `python scripts/bin/queue_sync.py --enqueue --all-profiles` |
| Check bulk queue status | `python scripts/bin/queue_sync.py --status` |
| Retry failed queue items | `python scripts/bin/queue_sync.py --retry-failed` (fails closed if any failed record lacks an exact canonical account profile) |
| Retry deferred degraded pages | `python scripts/bin/queue_sync.py --retry-deferred --notebook-id <uuid> --synth-backend mmx --timeout-s 1200 --max-attempts 1` (keeps the deferred obligation until true semantic success and bounds this retry to one worker attempt) |
| Retry one poisoned item | `python scripts/bin/queue_sync.py --retry-poisoned --notebook-id <uuid> --synth-backend dgemma --timeout-s 1200` (force-resynthesis is on by default; timeout kills the owned child tree) |
| Recover a dead queue worker | `python scripts/bin/queue_sync.py --recover-worker --worker-id <worker-id>` (refuses live PIDs; records an orphaned claim as failed unless `--requeue-orphan` is explicitly authorized) |

## Common questions

**How do I know what to sync?** Run `python sync.py --status`. It lists every
notebook with ≥10 sources (skips test junk), sorted by size, with columns
showing whether it's synced, how many transcripts exist, and how many concept
pages have been written. Pick the one you want, then run `--notebook <id>`.

**How do I know if a sync will do what I expect before committing?** Run with
`--dry-run` first. It exports transcripts, clusters, synthesizes, and
reconciles, but does NOT write any wiki pages. The log shows cluster count,
synthesized titles, and new-vs-refines split.

**What gets skipped on re-sync?** Two layers: (1) if the notebook's
`source_ids` hash is unchanged, the *entire notebook* is skipped; (2) at the
transcript level, individual sources already exported are skipped (file-exists
check). Adding 1 video to a 188-source notebook re-exports only that 1 new
transcript.

**Why are YouTube source URLs `null` in the transcript frontmatter?**
NotebookLM doesn't expose the original URL for YouTube sources — only the
title. The 4-hop chain closes via `match_uuids_to_urls.py` (title → URL
matching against `clusters.json`, 97.9% match rate). The `url:` field is
populated only when `--from-clusters` provides the mapping.

**What model synthesizes the concept pages?** MiniMax-M2.7 via the `mmx` CLI
(default). The handoff spec said "M3" but M3 isn't deployed; M2.7 is the
available MiniMax model. Switch to the free fallback with
`--synth-backend dgemma` if pages run thin or quota is a concern.

**How many parallel workers should I use?** Maximum **3 concurrent workers
per account**. This host has three NotebookLM accounts (`a.hominidae` = paid,
`troup.hominidae` = free, `brsthomson` = free), so you can run
up to 9 workers total (3 per account). The NotebookLM API degrades above 3
sessions per account (yt-is benchmark: 3+3 workers hit 4,123 VPH; 4+4
regressed to 1,150 VPH). Pass `--workers` when enqueueing to set the global
queue capacity; per-account limits are enforced independently.

**How do I use the free accounts?** Use `--all-profiles` on enqueue to
discover notebooks from all three accounts. Each notebook is tagged with its
exact account identity; workers automatically use the correct canonical
storage file. The free accounts (`troup.hominidae`, `brsthomson`) each have a
50-source-per-notebook limit. If a probe fails, the bridge attempts the
matching durable master-token repair and, when needed, the established
account-specific headless CDP bootstrap. Do not sign in through a shared
browser or run the legacy CLI from a queue worker.

**Can I run `sync.py --all` alongside queue workers?** The old CDP login
contention no longer applies because the runtime uses direct clients and
canonical account files. Still respect the measured per-account concurrency
limit and do not run two jobs against the same notebook state concurrently.

**Where does the data live?**

| Artifact | Path |
|---|---|
| Raw transcripts | `P:/.data/wiki/sources/transcripts/<source_id>.md` |
| Vision keyframes | `P:/.data/wiki/sources/keyframes/<notebook_id>/` |
| Concept pages | `P:/.data/wiki/concepts/<slug>.md` |
| Sync manifest | `P:/.data/wiki/_state/nlm-sync-manifest.json` |
| Pruned pages (recoverable) | `P:/.data/wiki/_state/nlm-trash/<notebook_id>/` |

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `Authentication expired` or canonical probe failure | Stored account session is expired, mismatched, or unusable | The bridge attempts the exact account's durable master-token/CDP repair. If it remains unavailable, inspect the account-specific reason; no interactive login or cross-account fallback is attempted. |
| Status table shows 0 notebooks | Canonical probe/list failed or no notebooks meet the filter | Check the probe result and account identity; do not infer auth recovery from an empty list. |
| Export produces 0 transcripts but source list works | (rare) all sources already exported and `--force` not set | `python export_transcripts.py --notebook <id> --force` to re-export |
| Clustering produces 1 giant cluster | Too few transcripts or `--min-cluster-size` too high for the input | Normal for tiny notebooks; real notebooks (50+ sources) produce 5-15 clusters. Lower `--min-cluster-size` for small test runs. |
| Synthesis returns no JSON (parse fail) | LLM wrapped output in prose or hit `stop_reason: length` | Re-run; if persistent, switch `--synth-backend dgemma` or narrow input via `--max-members` |
| Pages fail `validate_wiki_entry.py` (too thin) | Synthesis produced <40 lines or <3 wikilinks | Inspect staging dir; re-run synthesis with a different backend or raise `--max-members` for richer input |
| A poisoned retry times out | Backend or child process exceeded the bounded retry window | Treat it as blocked; verify no child processes or staging output remain, preserve the receipt, and do not mark the notebook synced or repeat without a new backend/timeout decision |
| Manifest has stale `concept_slugs` after manual page deletion | Pages were removed but manifest wasn't updated | `python maintenance.py --fix-stale-slugs --confirm` |
| Transcripts exist for a notebook that's gone from NotebookLM | Notebook was deleted in the UI | `python maintenance.py --remove-orphaned-transcripts --confirm` (or `--prune-notebook <id> --confirm` to also clear manifest + concept pages) |
| `qmd` not found / reconcile fails | qmd CLI missing or not on PATH | Sync fails closed before writing a completion manifest; install qmd or fix the reconcile stage, then retry. |
| Queue worker produces 0 pages for every notebook | Canonical auth failure, direct-client error, or stale queue state | Inspect the worker's canonical probe/error, verify the queue item's exact account identity, and retry only after the account probe passes. Profileless legacy failures are not retried until ownership is recovered from exact evidence. |
| Export returns rc=5 for some sources | Individual source fetch failure (status=3, video unavailable) | **Partial, not success** — transcripts are preserved, but sync does not write a manifest or rename the notebook; queue retry is required. |
| Worker log shows `synced_0_pages` | The sync returned zero valid pages | The worker records a retryable failure; it never records completion for zero pages. |
| Legacy CLI/CDP login error | A retired auth path was invoked | Do not repair it inside wiki-yt. Use `ensure_account_session()` and inspect the durable YTIS auth result instead. |

**Authentication is an account-scoped durable boundary.** A static storage file
is not proof of a live session. The runtime performs a probe and attempts only
the matching non-interactive repair path; it fails closed when that path cannot
prove the account is usable.
