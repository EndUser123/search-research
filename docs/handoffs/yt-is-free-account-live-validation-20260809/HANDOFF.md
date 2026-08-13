---
thread_id: yt-is-free-account-live-validation-20260809
parent_handoff_path: P:/packages/yt-is/HANDOFF.md
produced_at: 2026-08-09T20:05:00Z
status: partial_needs_source_add_investigation
handoff_type: bounded-live-validation
---

# yt-is bounded Free-account live validation

## Decision

The bounded coordinator run completed with a truthful `partial` result. The
exact-account token-only preflight passed for both Free identities, all 20
manifest IDs were present, and 14/20 rows reached `complete`. Six rows failed
at NotebookLM `ADD_SOURCE` with provider `rpc_code=9`. This is a source-add
failure, not an authentication failure.

No retry of the six failed IDs is authorized by this receipt. A new
source-add-specific decision packet must define the mechanism, falsifier,
early-abort gate, and promotion/repair rule first.

## Run receipt

- Run root: `P:/.logs/multi_account_fetch/20260809_free_accounts_live_run01/`
- Run ID: `20260809T195927Z-d9cee871`
- Authoritative DB: `P:/.data/yt-is/batch_status.sqlite`
- Scope: `--limit 20 --all-uncategorized`
- Accounts: `troup.hominidae`, `brsthomson`
- Partition: 10 manifest IDs per account
- Workers: 3 per account, serial account execution
- Coordinator status: `partial`
- Selected IDs: 20; missing IDs: 0
- Final DB status: 14 `complete`, 6 `failed`
- DB integrity after the run: `PRAGMA integrity_check=ok`

The exact preflight observed:

| Profile | Expected identity | Observed identity | Canonical storage | Result |
|---|---|---|---|---|
| `troup.hominidae` | `troup.hominidae@gmail.com` | `troup.hominidae@gmail.com` | `P:/.data/yt-is/nlm-auth/storage_state_troup_hominidae.json` | pass |
| `brsthomson` | `brsthomson@hotmail.com` | `brsthomson@hotmail.com` | `P:/.data/yt-is/nlm-auth/storage_state_brsthomson.json` | pass |

The coordinator invoked the existing `bin/csf-source fetch` route and did not
use a YouTube API fetch path. The child outputs show account-scoped worker
notebook creation/reuse and `0 deleted, 0 failed` cleanup failures. This does
not mean reusable worker notebooks were deleted; it means cleanup reported no
deletions or cleanup errors.

## Failed IDs

`troup.hominidae` failed at source-add:

- `gJtNWAlv0lA`
- `h01IK-c7Xng`
- `hW6FfYA6ios`
- `iwqbjwsN22k`
- `jCXwVGuFfXQ`

`brsthomson` failed at source-add:

- `keFH7JwVAvI`

The child logs record repeated `RPC ADD_SOURCE failed` events with
`rpc_code=9`. Successful sources in the same sub-batch were extracted, so the
result is not an all-account auth or notebook-creation failure. No transcript
fallback was used in this run.

## Claim ledger

| Claim | Type | Evidence | Confidence | Allowed action |
|---|---|---|---|---|
| Both exact Free identities were available immediately before launch | verified_fact | token-only preflight and coordinator summary | High | Reuse canonical auth path; do not request browser login from this result |
| The 20-ID scope was exact and fully represented in manifests | verified_fact | both manifests, selection receipts, summary | High | Reconcile by manifest IDs |
| 14 rows completed and 6 failed | measured_metric | coordinator summary and authoritative DB rows | High | Keep completed rows; investigate failed rows |
| The six failures were caused by authentication | contradicted | preflight passed; `ADD_SOURCE rpc_code=9` in child stderr | High | Do not reopen auth diagnosis |
| `rpc_code=9` has one deterministic local cause | unsupported | current logs expose code but not provider message | N/A | Perform offline/source-add mechanism investigation before retry |
| The coordinator can create/reuse account-scoped worker notebooks | verified_fact | child `worker_notebook_reset` and `notebook_prewarm` events | High | Keep coordinator as canonical live path |

## Next action

1. Preserve the six failed IDs and their current `analysis_status` rows.
2. Inspect the canonical source-add implementation and prior `rpc_code=9`
   packets; determine whether the failure is URL/source eligibility, provider
   capacity, account-tier behavior, or a local request construction defect.
3. Add only the smallest diagnostic or mechanism change justified by that
   evidence.
4. Run a new small canary only after its decision packet supplies abort and
   promotion rules.

