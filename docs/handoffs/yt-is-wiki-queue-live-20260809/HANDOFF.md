# yt-is / wiki-yt Terminal Queue Receipt

Date: 2026-08-09
Status: terminal_partial_needs_follow_up

## Current authoritative reconciliation (2026-08-12)

The sections below are chronological evidence unless explicitly superseded by
this header. The current queue at
`P:/.data/wiki/_state/nlm-sync/queue.json` reports:

- `pending=0`, `in_progress={}`
- `completed=47`, `failed=2`
- `poisoned=0`, `needs_resynthesis=0`
- `failure_history=9`, `poisoned_history=20`

The exact semantic-debt item was completed by bounded MMX checkpoint-resume
run16. Receipt:
`P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-run16-result_receipt.md`.
Its five pages passed normal validation with complete four-hop provenance, but
citation coverage remains `19/36` (`52.8%`), not complete-source coverage.

The two remaining `0 pages` failures are unclassified and not authorized for
automatic retry. The current exact-ID search found no worker receipt, account
profile, attempt record, source export, page output, or validation receipt for
either row. Reconciliation:
`P:/.logs/wiki-yt-queue/20260811/wiki_failed_residual_reconciliation_20260812.md`.

The current read-only manifest audit reports 13 gaps, 12 with output but no
exact worker/profile/attempt receipt and one with no local output; zero are
eligible for safe recovery:
`P:/.logs/wiki-yt-queue/20260812/manifest_gap_audit_current_after_run16.json`.
Do not fabricate manifest entries from page or transcript output alone.

## Later local reconciliation (authoritative current state)

The queue and local worker evidence were reconciled after this terminal receipt.
Current `P:/.data/wiki/_state/nlm-sync/queue.json` counts are:

- `pending=0`, `in_progress=0`
- `completed=43` records (`39` distinct notebook IDs)
- `failed=2`, `poisoned=0`
- `failure_history=6`, `poisoned_history=6`

The current manifest has `38` entries. The reproducible current audit is
`P:/.logs/wiki-yt-queue/20260809/historical_manifest_gap_audit_current.md`;
it reports `13` completed queue IDs absent from the manifest, `12` with local
output/provenance but no exact worker receipt, and `1` with no local output.
It found `0` safe manifest recoveries. The older queue and manifest-repair
sections below are retained as a chronological receipt and are not the current
source of truth.

The three records described below as poisoned were later reopened only through
the named retry packet, then recovered through the approved deterministic
degraded-fallback path. The standalone receipt is
`P:/.logs/wiki-yt-queue/20260809/poisoned_synthesis_retry_receipt_20260809.md`.
Semantic LLM re-synthesis remains deferred; degraded pages are explicitly
tagged and are not equivalent to ordinary high-quality synthesis.

### Current queue reconciliation (2026-08-11)

The queue file is now the current authority for this stream. It reports
`pending=0`, `in_progress=0`, `completed=45`, `failed=2`, `poisoned=1`,
`needs_resynthesis=1`, `failure_history=9`, and `poisoned_history=17`.
The active poisoned record is notebook
`4017aa6e-35fb-426d-bc53-34620bec405e` on `a.hominidae`; its latest bounded
`dgemma` attempt timed out after `1200s` and did not promote a page or manifest
entry. The two failed records remain unowned legacy records and are not safe
to retry.

The queue now supports an explicit per-notebook Stage-C checkpoint directory
for named poisoned retries. The worker passes `--synth-checkpoint` on first
use and `--synth-resume` only when the identity-validated checkpoint exists.
This preserves successful clusters across interruption without weakening the
quality gate or authorizing another retry by itself.

### Current superseding reconciliation (2026-08-11)

The canonical queue now reports `pending=0`, `in_progress=0`, `completed=46`,
`failed=2`, `poisoned=1`, and `needs_resynthesis=1`. The exact deferred item
`4017aa6e-35fb-426d-bc53-34620bec405e` received one named MMX retry with a
1,800-second bound. It timed out during Stage C after five clusters; the
canonical five degraded pages and manifest were unchanged, and the deferred
quality obligation remains. No further unchanged backend retry is justified.
Receipt:
`P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-run14-result_receipt.md`.

Two unrelated active failures remain as a separate residual: `56999a7a...`
(`WL: AI Coding & Tooling`) and `8138a528...` (`Mastering Claude Skills`), both
recorded only as `0 pages` after one attempt. Their decision packet is
`P:/.logs/wiki-yt-queue/20260809/wiki_failed_residual_decision_packet_20260809.md`.
They have no current raw worker receipt and are not authorized for automatic
retry or manifest fabrication.

## Decision

The bounded wiki-yt queue run is terminal and made real progress, but it is
not a clean all-success result. No queue work is active, no authentication
repair is indicated, and no failed item was retried in this continuation.

## Original terminal queue receipt (historical snapshot; superseded above)

Authoritative state: `P:/.data/wiki/_state/nlm-sync/queue.json`

- profiles: `a.hominidae`, `troup.hominidae`, `brsthomson`
- pending: `0`
- in progress: `0`
- completed records: `40`
- failed records: `8`
- poisoned records: `3`
- distinct completed notebook IDs: `36`
- queue lock: absent after workers exited
- worker processes: none of `queue_sync.py`, `sync.py`,
  `synthesize_subtopics.py`, or mmx children remain

The queue's `completed` array contains four duplicate notebook IDs from older
attempt history, so record count and distinct-ID count are intentionally both
reported.

## Original manifest repair receipt (historical snapshot; superseded above)

At the time of this original receipt, the manifest at
`P:/.data/wiki/_state/nlm-sync-manifest.json` contained `35` entries. Six
2026-08-09 successful receipts were verified from exact
worker logs and local transcript evidence, then written through the guarded
locked manifest writer:

| Notebook ID | Sources | Pages | Evidence |
|---|---:|---:|---|
| `16dac687-5ab6-4bf4-8330-632b0e92d852` | 32 | 4 | worker-02 stdout: `0 failed validation`, rename, `Synced: 1/1` |
| `afd2f1dd-ff64-44f7-9259-6f923b6c081a` | 28 | 2 | worker-02 stdout: `0 failed validation`, rename, `Synced: 1/1` |
| `f6e8ae52-82d6-4250-86a5-37ddc18fc30b` | 10 | 1 | worker-02 stdout: `0 failed validation`, rename, `Synced: 1/1` |
| `8df98abe-6541-4d68-8921-5d39149a838d` | 17 | 1 | worker-02 stdout: `0 failed validation`, rename, `Synced: 1/1` |
| `0fa07246-ba84-43fd-a9cd-f86999f24286` | 49 | 4 | worker-03 stdout: `0 failed validation`, rename, `Synced: 1/1` |
| `2530cb02-6981-4904-af2b-6a00a4ad1fa7` | 42 | 2 | worker-03 stdout: `0 failed validation`, rename, `Synced: 1/1` |

The six repairs are a state-reconciliation action, not a new NotebookLM
operation. No external fetch or source mutation was performed during repair.

The current audit supersedes the historical count above: `38` manifest entries
and `13` distinct completed queue IDs remain absent. They are older queue
records with missing profile/attempt provenance or no unique current successful
receipt. They are deliberately deferred; queue completion alone is not enough
to fabricate a manifest entry.

## Reliability fix

The run exposed a real concurrent-writer defect: multiple workers could load
the same manifest snapshot and atomically replace it, erasing sibling
successful entries. The durable fix is:

- `P:/.agents/skills/wiki-yt/scripts/sync.py`: lock, reload, merge the current
  per-notebook update, then atomic replace.
- `P:/.agents/skills/wiki-yt/scripts/maintenance.py`: use the same lock and
  reload before confirmed stale-slug repairs or notebook pruning.
- `P:/.agents/skills/wiki-yt/tests/test_sync_manifest.py`: two regression tests
  cover stale-worker merge and maintenance reload/repair.

Confirmed maintenance remains queue-exclusive because moving transcript or
concept files cannot be made safe by a manifest lock alone.

## Failures and non-findings

The three deferred semantic records are:

- `c8b07a4c-607c-4ddc-94be-688206daf737` — Claude Code x NotebookLM x Obsidian Research
- `f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2` — ext-The Renaissance of the Terminal
- `4017aa6e-35fb-426d-bc53-34620bec405e` — Claude Code Guide: Production Hooks and Agent Skills

Their logs show synthesis backend exhaustion (`Synced: 0/1`), not an auth
failure. The exact 2026-08-10 MMX retry for
`f5f8b2fa-c0ba-4d1a-acc2-02cb13a65ee2` also ended negative after reaching Stage
C; it did not mutate pages or the manifest. Do not repeat that packet. A new
retry must use the corrected large-prompt fallback path and a new decision
packet; this handoff does not authorize it.

Separately, the Free-account live validation receipt recorded six
`ADD_SOURCE` `rpc_code=9` failures. That is a source-add/provider result, not
an authentication result, and is documented at
`P:/docs/handoffs/yt-is-free-account-live-validation-20260809/HANDOFF.md`.

Successful queue logs also contain variable citation-quality ratios on some
historical notebooks. The sync validator passed the pages that were accepted,
but those ratios are a follow-up quality-audit signal, not evidence that every
historical page is equally strong.

## Claim ledger

| Claim | Type | Evidence | Confidence | Falsifier | Allowed action |
|---|---|---|---|---|---|
| Queue has no active work | verified_fact | current queue JSON, no worker processes, no queue lock | high | a live worker or pending item appears | schedule next bounded scope |
| Six current receipts are manifest-backed | verified_fact | exact worker logs, transcript evidence, manifest IDs | high | receipt/manifest/source IDs disagree | stop and repair audit |
| Manifest is safe for concurrent per-notebook sync writes | verified_fact | lock/reload/merge implementation and 2 regression tests | high | sibling update disappears in a concurrent test | fix before parallel queue |
| Thirteen older queue records should remain deferred | decision | no unique current successful receipt | high | an exact receipt is recovered | perform a guarded per-ID audit |
| Poisoned records are caused by auth | unsupported | no auth markers; logs show synthesis exhaustion | high confidence in non-auth classification | exact auth error in raw log | do not request login from this receipt |

## Verification

- `python -m pytest P:/.agents/skills/wiki-yt/tests/test_sync_manifest.py -q` -> `2 passed`
- `python -m pytest P:/.agents/skills/wiki-yt/tests -q` -> `44 passed`
- `python -m py_compile P:/.agents/skills/wiki-yt/scripts/maintenance.py P:/.agents/skills/wiki-yt/tests/test_sync_manifest.py` -> passed
- `git -C P:/.agents/skills/wiki-yt diff --check` -> clean

No stage, commit, push, queue retry, authentication request, or destructive
cleanup was performed for this receipt.

## Next actions

1. Treat the queue as complete for this bounded run; do not retry poisoned or
   source-add failures without separate packets and early-abort gates.
2. Keep the 13 historical manifest gaps as an explicit audit backlog; recover
   only from exact local evidence.
3. Run confirmed `maintenance.py` only while `queue_sync.py --status` reports
   no pending or in-progress work.
4. For the next live scope, perform exact-account token-only preflight and
   record a fresh scope/receipt before launching workers.
