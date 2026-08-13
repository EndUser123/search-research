# yt-is Unattended Full-Backlog Readiness Handoff

Date: 2026-08-12
Status: `not_ready_for_unattended_full_backlog`

## Authority

Read these first, in order:

1. `P:/packages/yt-is/AGENTS.md`
2. `P:/packages/yt-is/CLAUDE.md`
3. `P:/packages/yt-is/HANDOFF.md`
4. `P:/packages/yt-is/docs/operations/unattended-backlog-operation.md`
5. `P:/.logs/multi_account_fetch/20260810_unattended_readiness_gate_audit_20260810.md`

The package-local handoff and the gate audit are current authority. Older
handoffs under `P:/docs/handoffs/` are historical unless explicitly linked by
those documents.

## Continuation supersession (2026-08-12)

The package-local handoff and active goal audit supersede the counts and
readiness details later in this document. The current authoritative database
snapshot is `integrity_check=ok`, `complete=9,982`, `failed=197`, and
`pending=332,940`, recorded in
`P:/.logs/multi_account_fetch/20260812_ytis_goal_completion_audit_after_run10.md`.
The read-only checker remains `health_status=planned` with `issues=[]`, but
`full_authorization=false` and `scheduler_unverified=true`.

The adaptive scheduler also received an offline safety correction: completed
health results from worker slots above the current `target_workers` no longer
authorize scale-up. This preserves completion-boundary health semantics and
does not constitute live adaptive or VPH evidence. See the package handoff's
`Adaptive health-window capacity boundary` section and
`tests/test_adaptive_worker_scheduler.py` for the verified regression.

The consolidated current gate ledger is
`P:/.logs/multi_account_fetch/20260811_unattended_readiness_reconciliation.md`.
It remains `not_ready_for_unattended_full_backlog`; it does not authorize
execution. The adversarial review is
`P:/.logs/multi_account_fetch/20260811_unattended_readiness_adversarial_review.md`.
The current residual audit is
`P:/.logs/multi_account_fetch/20260812_residual_audit_after_run10.json`.
The current residual packet set is
`P:/.logs/multi_account_fetch/20260812_residual_retry_packet_set_after_run10/`.
The pending-only residual-policy gate receipt is
`P:/.logs/multi_account_fetch/20260812_residual_policy_gate_pending_only_after_run10/`.
It permits only a pending-row drain policy while leaving failed rows deferred;
it is not a recovery or full-backlog authorization.
The installed Windows task remains interactive-token and plan-only. A fresh
S4U registration-only recheck was blocked by `Register-ScheduledTask: Access is
denied` before task creation; no fresh task, state, output, supervisor, or
canonical mutation resulted. This is an OS permission boundary, not a
NotebookLM auth failure. Receipt:
`P:/.logs/multi_account_fetch/20260812_scheduler_s4u_registration_recheck_run01/result_receipt.md`.
The next step requires an operator/elevated registration context for the exact
user or an explicitly approved password-backed principal. Do not request
another NotebookLM login or substitute `SYSTEM`, shared cookies, legacy
login, or `--no-sandbox`.
The cross-run residual-attempt ledger is
`P:/.data/yt-is/unattended-backlog/residual-attempt-ledger.json`.
Future requeues must use the ledger-backed command with a unique mechanism,
hypothesis, account scope, and exact decision packet; same-mechanism overlap
is rejected.

## Wiki semantic debt reconciliation (2026-08-11)

The exact poisoned/deferred notebook
`4017aa6e-35fb-426d-bc53-34620bec405e` was completed by bounded MMX
checkpoint-resume run16. The run reopened only that item, completed in
`1168.5s` within the `1200s` bound, and left the wiki queue at
`completed=47`, `failed=2`, `poisoned=0`, `needs_resynthesis=0`, with no
pending/in-progress work. Receipt:
`P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-run16-result_receipt.md`.

Five pages passed normal validation with complete four-hop provenance from 36
local transcripts. Citation coverage is `19/36` (`52.8%`), so this closes the
poisoned queue state but does not establish complete source coverage. The
read-only manifest audit still reports 13 historical gaps and zero exact
receipt repairs:
`P:/.logs/wiki-yt-queue/20260812/manifest_gap_audit_current_after_run16.json`.

## Throughput gate closure (2026-08-11)

The latest unknown-caption pair at
`P:/.logs/multi_account_fetch/throughput_pair_20260811_unknown_30_live_gate_run02/`
is `control_invalid_adaptive_not_launched`. Its fixed controls reconciled
`86/90` and `79/90` after fresh source-add RPC9 and post-add
`SourceNotFoundError` failures. Immediate token-only auth passed for all three
canonical identities, so this is not an auth failure. Adaptive was withheld;
the observed rates are not valid VPH comparison or optimality evidence. Staged
integrity and cleanup passed, while selected-cache completeness correctly
failed for incomplete controls. Receipt:
`P:/.logs/multi_account_fetch/throughput_pair_20260811_unknown_30_live_gate_run02/result_receipt.md`.

Do not direct-replay the RPC9 rows or request login from this result. Reopen
only with an exact isolated recovery packet and require a fresh clean control
before adaptive or full-backlog execution.

## Superseding throughput attempts (2026-08-11)

The throughput-pair planner was corrected before the next current-contract
attempt. It now selects authoritative `analysis_status.status='pending'`
rows even when their IDs are present in the reference transcript cache; the
selected IDs are removed from the isolated staging cache before execution.
The regression test covers a pending cohort whose IDs are all in that cache.
Focused planner/coordinator tests passed (`25 passed`), compilation and diff
hygiene passed. This fixes cohort preparation; it does not make a live result
valid by itself.

The fresh captioned smoke at
`P:/.logs/multi_account_fetch/throughput_pair_20260811_objective_current_captioned_smoke_run02/`
passed both fixed controls (`6/6` each) and preserved canonical DB/cache
hashes and SQLite integrity. Its adaptive arms were deliberately not
exercised: with only `2` IDs per account and outer `batch_size=50`, the
observed scheduler correctly stayed at the initial three workers and scaled
down. Its diagnostic rates are not an adaptive comparison or optimality
claim. Receipt:
`P:/.logs/multi_account_fetch/throughput_pair_20260811_objective_current_captioned_smoke_run02/result_receipt.md`.

The follow-up captioned batch-1 attempt at
`P:/.logs/multi_account_fetch/throughput_pair_20260811_objective_current_captioned_batch1_run03/`
used `10` IDs per account and `batch_size=1`, which was intended to make
scale-up observable but was below the runtime's conservative planner floor.
Both fixed controls were invalid before adaptive launch:
pair-01 reconciled `27/30` and pair-02 `29/30`. Failures were typed
`nlm_content_below_threshold` for `Tz4RkJQUrwE`, `V6UJ3jfwt9s`, and
`TM-JPf07iM4`; `ZHYqjD099Aw` produced the known source-add recovery followed
by `SourceNotFoundError`. Immediate token-only auth passed for
`a.hominidae`, `troup.hominidae`, and `brsthomson`; this was not an auth
failure. Adaptive was withheld, so no VPH comparison or optimality claim is
valid. Canonical hashes and integrity remained unchanged. Receipt:
`P:/.logs/multi_account_fetch/throughput_pair_20260811_objective_current_captioned_batch1_run03/result_receipt.md`.
The exact residual classification and next-action boundary are recorded at
`P:/.logs/multi_account_fetch/throughput_pair_20260811_objective_current_captioned_batch1_run03/batch1_residual_decision_packet.md`.

Do not ask the operator to authenticate again from either result. Do not
replay the exact residual IDs or launch another adaptive arm from this
handoff. The next throughput action requires an exact residual decision or a
narrow new mechanism, then a fresh clean control. Full-backlog operation,
logged-out scheduler proof, and maximum/optimal sustained VPH remain open.

The throughput-pair planner now fails closed before staging when an adaptive
packet is below that floor. It records the required logical-batch count from
the configured health window, scale-up backlog, and four-batches-per-worker
dispatch contract. This is a feasibility guard, not live scale-up or VPH
evidence; focused planner/coordinator verification is `27 passed`.

The current scheduler audit is
`P:/.logs/multi_account_fetch/scheduler_canary_audit_20260811.md`. It verifies
that `YtisUnattendedBacklog` is registered with the interactive-token,
plan-only canary arguments. It does not prove logged-out execution or
authorize `--execute --until-empty`. Older statements in this historical
handoff that the task was unregistered are superseded by the audit above.

## Current bounded-canary reconciliation (2026-08-11)

The later run10 source-add fallback-only canary is the current bounded
recovery result. It passed immediate token-only preflight for all three exact
identities, used `--fallback-only` with zero NotebookLM mutation actions, and
promoted only `DV4EYDLeqBg` after a 645-character quality check. The other two
exact results were excluded. Receipt:
`P:/.logs/multi_account_fetch/20260812_source_add_fallback_canary_run10/result_receipt.md`.
Canonical counts are now `complete=9,682`, `failed=197`, `pending=333,240`.
The stale pre-promotion plan was archived at
`P:/.data/yt-is/unattended-backlog/state-stale-after-run10.json`; a fresh plan
was installed at `P:/.data/yt-is/unattended-backlog/state.json` and health is
`planned` with `issues=[]`. This is not default fallback, RPC9 repair,
throughput, or full-backlog authorization. The older dated canary prose below
is retained as historical evidence.

Three source-add fallback outputs passed the exact `500`-character promotion
gate and were reconciled into canonical state with the locked exact-result
promoter. The apply receipts are
`P:/.logs/multi_account_fetch/20260811_fallback_promotion_source_add_successes_20260811/run01_apply_receipt.json`
and
`P:/.logs/multi_account_fetch/20260811_fallback_promotion_source_add_successes_20260811/run02_apply_receipt.json`.
The current canonical status is `complete=9,681`, `failed=197`, and
`pending=333,241`; two source-add rows remain failed and packet-required.
Current residual authority:
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run03_after_source_add_run03/post_quality_reconciliation_residual_audit.json`.

The source-addressability fallback-only canary run02 is recorded at
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run02/result_receipt.md`.
One exact row recovered through Whisper with `13,928` characters and was
promoted by the exact quality-gated promoter; the other exact row was later
classified terminal `unavailable` from four-stage raw evidence. The
source-addressability class is now closed by the exact-ID reconciliation
receipt; the separate weak-quality case is classified as `fallback_quality`
below. This does not authorize default fallback routing or full-backlog
execution.

The subsequent exact run03 canary tested the three remaining untested IDs and
found all three unavailable across Selenium, Whisper/audio, yt-dlp, and
cookie-backed yt-dlp. The guarded classification reconciliation moved those
three plus `FUaqMRqbYvY` to terminal `unavailable` without requeueing or
completion. Receipt:
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run03_after_source_add_run03/unavailable_reconciliation_receipt.md`.

The separate 33-character `QvxHBtYsDig` result was classified as
`fallback_quality`, closing the source-addressability class; it was not
promoted and not requeued. Receipt:
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run03_after_source_add_run03/fallback_quality_reconciliation_receipt.md`.

The latest content-threshold fallback-only canary is recorded at
`P:/.logs/multi_account_fetch/20260811_content_threshold_fallback_canary_run01/result_receipt.md`.
Three exact current residuals recovered through `ytdlp` with `22`, `46`, and
`8,815` characters, passed the existing 21-character quality gate, and were
promoted through separate exact receipts. Immediate token-only auth passed for
all three identities; staging integrity, exact reconciliation, cleanup, and
the no-NotebookLM-mutation scan passed. The class is now 12 rows. This is
positive bounded sample evidence only; do not blanket-requeue the remaining
rows or infer full-backlog readiness.

The latest exact source-add fallback-only canary is recorded at
`P:/.logs/multi_account_fetch/20260811_source_add_fallback_canary_run03_after_content_run01/result_receipt.md`.
It re-tested the two remaining exact source-add rows after immediate token-only
auth passed for all three identities. `w9cxJdazkEs` ended `no_transcript`;
`yLSnkG9yLbA` exhausted the bounded Whisper fallback and ended
deadline-exhausted/unknown. No row met the `500`-character promotion gate, no
promotion occurred, and raw events contained no NotebookLM mutation. This is
negative exact-canary evidence only; it does not authorize direct RPC9 replay,
default fallback routing, or full-backlog execution.

The latest bounded coordinator canary is
`P:/.logs/multi_account_fetch/quality-observability-canary-run01/`. It selected
400 pending IDs and reconciled 389 complete plus 11 failed. Immediate token-only
auth passed for `a.hominidae`, `troup.hominidae`, and `brsthomson`. Pro adaptive
settings were forwarded and emitted scale-down transitions only; the run did
not prove scale-up. Free profiles remained at fixed three workers. The normal
cache/NotebookLM path also did not populate the fallback-only quality fields,
so no semantic-quality result is claimed. Receipt:
`P:/.logs/multi_account_fetch/quality-observability-canary-run01/result_receipt.md`.

The subsequent exact command-residual fallback canary run04 processed
`QOhOFjRLjWA`, `YUazGIwPwfI`, and `yJUq-obHXzw` in isolated staging. It
reconciled `3/3` to `complete/whisper`, produced non-empty cache output,
passed both SQLite integrity checks, matched all three token-only auth
identities, found no NotebookLM source/add/materialization/content action, and
left the canonical DB/cache unchanged. This is a positive bounded fallback
sample only; it does not authorize blanket routing, semantic-quality
promotion, or full-backlog operation. Receipt:
`P:/.logs/multi_account_fetch/20260811_command_residual_current_canary_run04/result_receipt.md`.

The disjoint six-ID command-residual follow-up at
`P:/.logs/multi_account_fetch/20260811_command_residual_current_canary_run05/`
reconciled `4/6` staged rows to `complete/whisper` and `2/6` to explicit
fallback-deadline failure. All three immediate token-only auth identities
passed; exact manifests, staging integrity, process cleanup, and canonical
hash preservation passed. No mutating source-add, materialization,
source-content, or content-fetch action occurred; generic `nlm_client_*`
initialization/auth-probe events were present and are not mutation evidence.
This is partial bounded class evidence with an expensive tail, not default
fallback promotion, throughput evidence, or full-backlog authorization.
Receipt:
`P:/.logs/multi_account_fetch/20260811_command_residual_current_canary_run05/result_receipt.md`.

The current five-row `source_add` residual class was then tested through two
disjoint exact fallback-only packets in isolated staging. Run01 recovered one
row; run02 recovered two and terminalized two (`no_transcript` and fallback
deadline exhausted). All three immediate token-only auth probes passed, raw
events showed no source-add/materialization/content action, staging integrity
and cleanup passed, and canonical DB/cache hashes were preserved. This is
`3/5` partial bounded recovery evidence with a costly tail, not default
fallback promotion, throughput evidence, or full-backlog authorization.
Receipts:
`P:/.logs/multi_account_fetch/20260811_source_add_fallback_canary_run01/result_receipt.md`
and
`P:/.logs/multi_account_fetch/20260811_source_add_fallback_canary_run02/result_receipt.md`.

The first exact row from the current six-row `source_addressability` class was
then tested through a fresh isolated fallback-only packet at
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run01/`.
It recovered `QvxHBtYsDig` in `19.598s` with a non-empty `33`-character /
`5`-word Selenium cache result. All three immediate token-only auth probes
passed; raw events showed no source-add/materialization/content action; staged
integrity and cleanup passed; and canonical DB/cache hashes were preserved.
Because the output barely clears the existing minimum, this is a bounded route
success with a semantic-quality caveat, not default promotion or evidence of
acceptable final transcript quality. Receipt:
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run01/result_receipt.md`.

The current database is `integrity_check=ok` with `complete=9,681`,
`failed=197`, and `pending=333,241`. The fresh residual audit is
`P:/.logs/multi_account_fetch/20260811_source_addressability_fallback_canary_run03_after_source_add_run03/post_quality_reconciliation_residual_audit.json`;
51 rows still require a separate decision packet. A fresh plan-only canonical
state was installed at `P:/.data/yt-is/unattended-backlog/state.json`, while
the prior stale plan remains preserved at
`P:/.data/yt-is/unattended-backlog/state-pre-quality-observability-canary-run01.json`.
The health check returned `planned` with `issues=[]`. Full-backlog authorization,
logged-out scheduler proof, fallback promotion, and throughput optimality remain
open.

## Current superseding reconciliation (2026-08-11)

Use `P:/packages/yt-is/HANDOFF.md` and
`P:/packages/yt-is/docs/operations/unattended-backlog-operation.md` for the
current counts. The active database is `integrity_check=ok` with
`complete=9,681`, `failed=197`, and `pending=333,241`; the current residual
audit classifies all 197 failures and leaves 51 rows requiring a separate
decision packet. The read-only health check is `planned` with `issues=[]`, but
`full_authorization=false`, `scheduler_unverified=true`, and residuals remain.

The downstream wiki queue now reports `completed=47`, `failed=2`,
`poisoned=0`, `needs_resynthesis=0`, with no pending/in-progress work. The
exact notebook `4017aa6e-35fb-426d-bc53-34620bec405e` was closed by the
bounded MMX checkpoint-resume run16; citation coverage remains only `19/36`
(`52.8%`). Receipt:
`P:/.logs/wiki-yt-queue/20260811/semantic-resynthesis-4017-mmx-run16-result_receipt.md`.

The interactive-token Task Scheduler canary is verified only in plan-only
mode; Windows denied S4U registration. The application supervisor's separate
bounded execute/restart/resume canary passed on six isolated staged IDs; its
receipt is
`P:/.logs/multi_account_fetch/20260810_scheduler_restart_resume_canary_run04/result_receipt.md`.
The current task audit is
`P:/.logs/multi_account_fetch/scheduler_canary_audit_20260811.md`. No
full-backlog authorization receipt exists. Do not register an executing task
or run `--until-empty` from this handoff.

## Latest throughput/source-add reconciliation (2026-08-11)

The distinct-settings no-caption pair at
`P:/.logs/multi_account_fetch/throughput_pair_20260811_no_caption_30_distinct_settings_plan_run01/`
is closed as `negative_control_invalid_adaptive_not_launched`. Immediate
token-only auth passed for `a.hominidae`, `troup.hominidae`, and `brsthomson`,
but the two fixed controls reconciled only `85/90` and `88/90` because seven
typed RPC9 source-add/content residuals occurred. Adaptive arms were withheld;
neither control result is valid VPH evidence.

The four exact RPC9 rows were processed once through isolated staged
`--fallback-only` recovery: `3/4` reached non-empty Whisper cache completion
and `1/4` exhausted its bounded deadline. Staging integrity passed and no
NotebookLM action occurred in fallback mode. This does not prove RPC9 is fixed,
promote fallback by default, authorize a same-shape pair, or authorize the
full backlog. Use the package-local handoff and these receipts as authority:

- `P:/.logs/multi_account_fetch/throughput_pair_20260811_no_caption_30_distinct_settings_plan_run01/result_receipt.md`
- `P:/.logs/multi_account_fetch/throughput_pair_20260811_no_caption_30_distinct_settings_plan_run01/rpc9_recovery/source_add_pair01/result_receipt.md`

The fallback path now persists transcript length/word-count bands in cache and
`analysis_status.quality_metrics` for every fresh fallback completion. This is
observability only: the coordinator still treats non-empty output as
operationally complete, so a short band remains a quality-review obligation
and does not authorize retries or default fallback routing.

## Historical reconciliation (2026-08-11; superseded)

The package-local current authority supersedes the counts below:
`P:/packages/yt-is/HANDOFF.md` and
`P:/packages/yt-is/docs/operations/unattended-backlog-operation.md` now report
canonical `complete=9,282`, `failed=196`, `pending=333,641`, and the current
residual audit. The six exact RPC9 rows from the 2026-08-11 unknown-cohort
throughput control were processed once through isolated `--fallback-only`
staging: `2` recovered transcripts, `4` terminal unavailable outcomes, `0`
pending, and `0` direct NotebookLM source-action events. Receipt:
`P:/.logs/multi_account_fetch/throughput_pair_20260811_unknown_plan_run03/source_add_recovery_run01/result_receipt.md`.
This closes only that recovery branch; it does not prove RPC9 is fixed or make
the invalid throughput pair usable as VPH evidence.

The throughput harness was then repaired offline to record explicit Pro/Free
policy, keep adaptive settings Pro-only, and fail closed on packet/path/settings
provenance drift. Focused harness tests pass; no new live pair is authorized
until the corrected child-settings contract is verified and a fresh packet is
prepared.

The fresh executable pair control canary was then attempted from the corrected
packet. Immediate token-only auth passed for all three accounts. The control
reconciled `29/30` selected IDs and stopped before adaptive: `brsthomson` had
one typed `ADD_SOURCE` `RPCError rpc_code=9` for `A1NrAlw1lHw`; the other nine
items on that account completed. This is not an auth failure and no VPH from
the arm is valid comparison evidence. Receipt:
`P:/.logs/multi_account_fetch/throughput_pair_20260811_unknown_plan_run07/pair-01/control_result_receipt.md`.
The coordinator now persists partial/runner-failed arm receipts atomically
instead of discarding a nonzero partial summary.

The wiki queue checkpoint path is also now wired through
`queue_sync.py -> sync.py -> synthesize_subtopics.py` for explicitly named
poisoned retries. It remains fail-closed on checkpoint identity and citation
quality. Current queue state is `completed=45`, `failed=2`, `poisoned=1`, and
`needs_resynthesis=1`; the active poison item is `4017...` after a bounded
1,200-second DGemma timeout. No new semantic retry is authorized by this
handoff alone.

## Historical state snapshot (superseded)

- Canonical DB: `complete=9184`, `failed=294`, `pending=333641`,
  `PRAGMA integrity_check=ok`.
- Exact token-only identities are mapped as `a.hominidae` Pro,
  `troup.hominidae` Free, and `brsthomson` Free. Do not reopen browser login
  from old source-add failures; run the exact auth preflight immediately before
  any authorized live arm.
- The current source-add fallback route is bounded and opt-in. It is not
  default-promoted or authorized for full backlog.
- Wiki obligations remain explicitly preserved: three `needs_resynthesis`
  items have no verified semantic promotion, and thirteen historical manifest
  gaps have no safe repair. Do not fabricate manifest entries or blind-retry
  semantic synthesis.
- The supervisor restart/resume and cache-isolation contract now has a bounded
  pass: run06 killed the active supervisor tree, passed an immediate exact
  token-only preflight, recovered the chunk once, archived partial artifacts,
  completed `6/6` staged IDs, passed both staged SQLite integrity checks, and
  left no matching process. This does not prove OS Task Scheduler or logged-out
  execution. Evidence:
  `P:/.logs/multi_account_fetch/20260810_scheduler_restart_resume_canary_run06/`.
- The installer now defaults to `S4U` and verifies the exported task principal,
  logon type, run level, action, working directory, and execution limit. The
  task is still unregistered; `-WhatIf` is the only installer validation so
  far, so the logged-out boundary remains unproven.
- The supervisor now carries an auditable `--caption-state` / `--uncached-only`
  selection contract. Uncached selection requires an explicit read-only
  reference cache, and the child receipt must match the supervisor state. This
  enables clean bounded throughput cohorts but is not throughput evidence.

## Historical throughput evidence (superseded)

The isolated run at
`P:/.logs/multi_account_fetch/20260810_uncached_control_adaptive_pair_run03/`
ran the fixed control only over a frozen 1,200-ID cohort. All three exact auth
probes passed immediately before launch. Results were `1137 complete`, `63
failed`, `0 pending`; every completed ID had a non-empty isolated cache row,
both staging SQLite databases passed integrity, and process cleanup passed.

The measured combined completed VPH was `1534.50`, using the maximum parallel
account elapsed (`1137 / 2667.454s * 3600`). This is partial control/reliability
evidence, not a clean throughput baseline: 231 fallback attempts ran, 48
`transcript_chain_failed` events were present, and failures included two
deadline-exhausted fallbacks plus two cookie-rotation failures. The packet
therefore classified the control as
`control_invalid_adaptive_not_launched`; the adaptive arm was correctly not
started. Do not claim optimal throughput or compare this run as a clean VPH
winner.

## Offline validation

The current account policy plans 400 rows as `a.hominidae=134`,
`brsthomson=133`, `troup.hominidae=133`; Pro adaptive settings are forwarded,
Free remains fixed at three workers, and explicit source-add fallback carries a
900-second deadline. The read-only health result is `planned` with no issues:
`P:/.logs/multi_account_fetch/20260810_offline_plan_validation/`.

Reusing an older supervisor state after configuration changed was rejected
fail-closed. The focused supervisor tests now pass (`47 passed`), compilation
and diff hygiene pass, and installer `-WhatIf` completes with the S4U default
without registering a task. The `YtisUnattendedBacklog` Task Scheduler task is
not registered. No full-backlog authorization receipt exists.

## Next work, in order

1. Close or packet the source-add residual policy, three semantic resynthesis
   items, and thirteen historical manifest gaps.
2. Register the chosen S4U/password task only after operator approval, then run
   a logged-out bounded scheduler canary with exact receipts and health checks.
3. Use the explicit uncached/caption-state selection contract to run a clean
   fixed-control versus adaptive throughput pair; run03 and run04 cannot serve
   as clean comparison members.
4. Re-audit the exact canonical pending-ID set and independently pass all five
   authorization gates.
5. Only then build a version-2 full-backlog authorization receipt with an
   expiry and run bounded chunks with health/reconciliation checks.

Do not stage, commit, push, register the unattended task, run `--until-empty`,
or launch another adaptive arm from this handoff alone.
