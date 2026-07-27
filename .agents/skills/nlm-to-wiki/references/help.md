# nlm-to-wiki — Help resource

Quick reference, common questions, and troubleshooting for the nlm-to-wiki
skill. Loaded on demand; SKILL.md carries the entry-point summary.

All commands run from `P:/.agents/skills/nlm-to-wiki/scripts/`. The default
profile is `codex` (= `a.hominidae@gmail.com` on this host).

## Quick reference

| Task | Command |
|---|---|
| List notebooks + sync status (the default) | `python sync.py` or `python sync.py --status` |
| Sync one notebook | `python sync.py --notebook <uuid>` |
| Dry run (no page writes) | `python sync.py --notebook <uuid> --dry-run` |
| Sync with vision enrichment | `python sync.py --notebook <uuid> --enrich-vision` |
| Re-sync (skips unchanged) | `python sync.py --notebook <uuid>` |
| Round-trip from bulk-ingest clusters | `python sync.py --from-clusters clusters.json` |
| Audit state (read-only) | `python maintenance.py --audit` |
| Disk usage per notebook | `python maintenance.py --disk-report` |
| Fix stale manifest slugs | `python maintenance.py --fix-stale-slugs --confirm` |
| Prune a deleted notebook's state | `python maintenance.py --prune-notebook <uuid> --confirm` |
| Recover from auth expiry | `nlm login --profile codex` (silent CDP, ~10s, no browser interaction) |

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
| `✗ Authentication Error: Authentication expired` | nlm cookie session expired | `nlm login --profile codex` — silent CDP re-auth, ~10s, **no browser interaction needed**. Do NOT escalate to the operator; this is agent-performable. ([[notebooklm-cli-operational-gotchas]] Gotcha 1) |
| `nlm login --check` returns `network_error` | The probe lies; auth is probably fine | Ignore the probe. Run `nlm login --profile codex` to silently refresh, or just retry the operation. |
| Status table shows 0 notebooks | Auth expired before list call | `nlm login --profile codex`, then re-run `--status` |
| Export produces 0 transcripts but source list works | (rare) all sources already exported and `--force` not set | `python export_transcripts.py --notebook <id> --force` to re-export |
| Clustering produces 1 giant cluster | Too few transcripts or `--min-cluster-size` too high for the input | Normal for tiny notebooks; real notebooks (50+ sources) produce 5-15 clusters. Lower `--min-cluster-size` for small test runs. |
| Synthesis returns no JSON (parse fail) | LLM wrapped output in prose or hit `stop_reason: length` | Re-run; if persistent, switch `--synth-backend dgemma` or narrow input via `--max-members` |
| Pages fail `validate_wiki_entry.py` (too thin) | Synthesis produced <40 lines or <3 wikilinks | Inspect staging dir; re-run synthesis with a different backend or raise `--max-members` for richer input |
| Manifest has stale `concept_slugs` after manual page deletion | Pages were removed but manifest wasn't updated | `python maintenance.py --fix-stale-slugs --confirm` |
| Transcripts exist for a notebook that's gone from NotebookLM | Notebook was deleted in the UI | `python maintenance.py --remove-orphaned-transcripts --confirm` (or `--prune-notebook <id> --confirm` to also clear manifest + concept pages) |
| `qmd` not found / reconcile warns | qmd CLI missing or not on PATH | Non-fatal — reconcile continues without dedup; pages may duplicate existing concepts. Install qmd to restore the `refines` branching. |

**The auth-recovery recipe is agent-performable.** The single most common
failure mode (expired session) has a ~10s silent recovery that does NOT
require operator intervention. If you hit "Authentication expired," run
`nlm login --profile codex` and retry — do not report it as a blocker. See
[[notebooklm-cli-operational-gotchas]] Gotcha 1 for the full receipt.
