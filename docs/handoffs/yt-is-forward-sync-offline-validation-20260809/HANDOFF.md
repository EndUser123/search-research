---
thread_id: yt-is-forward-sync-offline-validation-20260809
parent_handoff_path: P:/packages/yt-is/HANDOFF.md
produced_at: 2026-08-09T19:05:00Z
status: ready_for_parent_review
handoff_type: offline-validation
---

# yt-is offline operational validation

## Decision

Offline validation passed. The dry-run path showed no external work was
observed: no live NotebookLM run, browser action, or YouTube/API request was
reported. No database write, staging, commit, or push was performed.

This handoff does **not** authorize a live fetch or establish a throughput
result. The next live action, if authorized, must use a fresh decision packet
with an explicit source/cohort hypothesis and early-abort gate. The 2026-08-09
source-add `rpc_code=9` retry remains closed under the package handoff.

## Authoritative database and scope

- Active batch database: `P:/.data/yt-is/batch_status.sqlite`
- Package-local `P:/packages/yt-is/.data/yt-is/batch_status.sqlite` is stale and
  must not be used for operational counts.
- At validation time the active DB contained `337,053` pending rows and
  `7,468` pending rows with `has_captions IS NULL`.
- The default six-day uncategorized coordinator scope contained `0` rows.
  An explicit scope is therefore required for a bounded run.

The coordinator dry-run used the current local pending scope with
`--all-uncategorized --limit 20`, deterministic `updated_at ASC, video_id ASC`
ordering, and the three canonical identities:

- `a.hominidae` (Pro)
- `troup.hominidae` (Free)
- `brsthomson` (Free2)

Receipt root:
`P:/packages/yt-is/.logs/multi_account_fetch/20260809_offline_scope_dry_run_20_v2/`

## Coordinator validation

The dry-run command completed with `status=planned` and `selected_count=20`.
It generated fresh account manifests and selection receipts with exact
fingerprints. Partitioning was `a.hominidae=7`, `troup.hominidae=7`, and
`brsthomson=6`; each child used `--workers 3` and `--dry-run`.

Reconciliation against the active DB showed:

- all `20` IDs exist;
- all `20` remain `status=pending`;
- all IDs are unique across manifests;
- coordinator and child status counts agree at `pending=20`;
- `PRAGMA integrity_check` returned `ok`;
- child stderr files are empty and stdout explicitly reports `Mode: DRY RUN`.

The receipt's `manifest_fingerprint` is a SHA-256 of the raw manifest JSON.
The manifest's `input_database_fingerprint` is a canonical JSON hash of the
rows selected by the coordinator, not a file hash. The receipt's
`database_snapshot_fingerprint` (also retained as legacy
`database_fingerprint`) is a canonical JSON hash of the current
`analysis_status` rows for the manifest IDs in manifest order. It is not the
513 MB SQLite file hash; the receipt now names its schema and scope explicitly.

The default fixed-worker mode was exercised. Adaptive worker flags remain an
opt-in, offline-validated integration and are not represented as live
performance evidence.

## Cache-first forward-sync validation

The existing `wiki-yt` forward-sync implementation was inspected at:

- `P:/.agents/skills/wiki-yt/scripts/yt_is_forward_sync.py`
- `P:/.agents/skills/wiki-yt/scripts/export_transcripts.py`

Added tests at:
`P:/.agents/skills/wiki-yt/tests/test_forward_sync.py`

The tests prove, without external calls or DB mutation:

1. A cache hit returns the cached transcript and video ID.
2. A cache miss returns empty and preserves fail-through behavior.
3. Cache errors do not block the NotebookLM fallback path, including through
   the export loop.
4. The export loop does not call NotebookLM or yt-dlp after a cache hit.
5. The export loop calls the existing NotebookLM path after a cache miss.
6. Video-ID resolution remains title-bridge based.

The current receipt contract extends the export result with deterministic
`cache_hit_count`, `cache_miss_count`, `cache_unresolved_count`,
`feed_forward_success_count`, and `feed_forward_failure_count` counters while
preserving `from_cache_count`. After the page-validation gate, `sync.py`
propagates this `export_receipt` into the returned sync result and the
per-notebook manifest entry. This is operational provenance only; it does not
prove live cache ROI or source coverage.

Verification: `20 passed` for `test_forward_sync.py` and the existing
`test_ytis_nlm.py` boundary.

Historical overlap audit:
`P:/docs/handoffs/yt-is-forward-sync-offline-validation-20260809/cache-overlap-audit.md`.
It found `286/286` identifiable YouTube sources in the July local manifest in
the authoritative yt-is cache. This supports the mechanism but is not current
inventory evidence or a production ROI measurement.

## Claim ledger

| Claim | Type | Evidence | Confidence | Allowed action |
|---|---|---|---|---|
| The coordinator can create a bounded exact three-account plan without external work | verified_fact | Dry-run receipt and child stdout | High | Reuse the command shape after fresh preflight |
| The active six-day uncategorized scope is empty | measured_metric | Read-only query of `P:/.data/yt-is/batch_status.sqlite` | High | Use an explicit scope or report `no_work` |
| Cache hits bypass NotebookLM in the export loop | verified_fact | Discriminating integration test | High | Keep cache-first path enabled |
| Cache-first saves a quantified fraction of future NotebookLM calls | unsupported | No current notebook/cache overlap measurement | N/A | Measure from a fresh, non-tainted source inventory before quoting ROI |
| Authentication is the cause of the prior source-add failures | contradicted | Canonical probes passed; source-add `rpc_code=9` was recorded | High | Do not reopen login from that evidence |
| A live source-add retry is currently authorized | unsupported | No new mechanism-specific packet or gate | N/A | Do not launch from this handoff |

## Next action

Parent review should choose between:

1. a fresh source-add mechanism packet and a small gate-authorized live canary;
2. offline measurement of notebook/source overlap for cache-first ROI; or
3. implementation of the separately tracked progressive visual-analysis
   handoff.

Do not use the stale package-local DB or the historical channel-sync-first
instructions to select live work.
