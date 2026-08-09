---
thread_id: grok-enforcement-receipt-authority-20260808
parent_handoff_path: P:/docs/handoffs/grok-enforcement-cold-start-20260807/HANDOFF.md
produced_at: 2026-08-08
status: ready_for_parent_review
handoff_type: validation
base_head: e75437a78d9ba5889a276f9dc8bb1859fb6dcbe9
test_commit: 34b21d9
worktree_path: P:/.worktrees/grok-receipt-authority-20260807
latest_replay_head: 5edc33aeed494ad3d48d07873571b38e7f179a9d
latest_replay_commit: 6be8aa3
shared_source_and_configuration_untouched: true
---

# Receipt-authority rollout validation

## Decision

**Ready for parent review, not ready for activation.** The existing receipt
gate implementation was validated in an isolated worktree. No shared Grok
source, hook registration, global configuration, authentication, external
service, or quota state was changed.

The current source already defines three opt-in modes in
`hooks/scripts/quality_gate.py:46-70`:

- `shadow`: keep the old gate authoritative;
- `receipt_authoritative_with_old_fail_safe`: use receipt authority when
  receipt state exists, otherwise use the old decision;
- `receipt_authoritative`: use the receipt decision.

The mode is selected by `GROK_RECEIPT_GATE_MODE` in the hook process. I did
not verify a host-level mechanism that scopes that environment variable to
`/ship-py` only. Do not enable it globally based on this handoff.

The scoped-injection inspection covered the active `quality-gate.json` and
`verification-receipts.json` registrations, `config.toml`, and
`ship-py/__lib/ship_orchestrator.py`. The registrations invoke the hook
scripts directly, the orchestrator does not pass an `env=` override to its
subprocess calls, and the config has no receipt-mode setting. This is evidence
against a currently documented workflow-scoped injection path, not proof that
no lower-level host facility can provide one.

## Base and worktree

- Shared repository: `C:/Users/brsth/.grok`
- Shared base observed: `e75437a78d9ba5889a276f9dc8bb1859fb6dcbe9`
- Isolated worktree: `P:/.worktrees/grok-receipt-authority-20260807`
- Test commit: `34b21d9` (`test: validate receipt gate rollout modes`)
- Shared Grok source, hook registration, and global configuration were not
  edited, staged, committed, reset, or cleaned by this work.
- Verification commands may write caches or temporary state; do not infer a
  clean shared checkout from this handoff.
- The shared checkout is concurrently owned and must be revalidated before
  any integration decision.

After the shared checkout advanced to `5edc33a`, the test commit was replayed
as `6be8aa3` in `P:/.worktrees/grok-receipt-authority-current-20260808`.
The same focused suite passed there (`83 passed`), with Ruff, compilation,
and diff checks clean. This replay confirms the test remains compatible with
the latest observed head; it does not authorize integrating into the shared
checkout.

## What was added

`hooks/scripts/tests/test_receipt_gate_modes.py` exercises:

1. The complete rollout decision matrix for the three modes.
2. Invalid environment values falling back to `shadow`.
3. The real `quality_gate.main()` path with controlled missing receipt state.
4. The real `quality_gate.main()` path with an invalid verification receipt.

The first test fixture incorrectly used `P:/tmp`, which production code
intentionally excludes from code-modification tracking. That produced three
false test failures. The fixture was corrected to `P:/packages/...`, and the
tests then passed. This correction is part of the reviewed test commit.

## Verification

Passed in the isolated worktree:

```text
python -m pytest hooks/scripts/tests/test_ship_phase_gate.py \
  skills/ship-rhai/tests/test_ship_receipt.py \
  skills/ship-py/tests/test_ship_orchestrator.py \
  hooks/scripts/tests/test_receipt_gate_modes.py -q
83 passed

python hooks/scripts/test_authoritative_receipts.py
44 passed, 0 failed

python hooks/scripts/test_metric_semantics.py
18 passed, 0 failed

python -m py_compile hooks/scripts/quality_gate.py \
  hooks/scripts/tests/test_receipt_gate_modes.py
ruff check hooks/scripts/tests/test_receipt_gate_modes.py
git diff --check
```

The pre-existing `test_worktree_identity.py` was also run twice. Its
functional checks passed (`16/17`), but its existing latency assertion failed
both times: Git identity resolution averaged `814.3 ms` and `1022.3 ms`,
against a `<200 ms` threshold. No worktree-identity source was changed. This
is a real environment/performance finding and must not be hidden by changing
the threshold without a separate investigation.

## Controlled behavior observed

With a transcript in which code was modified and a verification command ran:

| Mode | Receipt state | Result |
|---|---|---|
| `shadow` | missing | old gate allows |
| `receipt_authoritative_with_old_fail_safe` | missing | old gate allows |
| `receipt_authoritative` | missing | receipt gate blocks |
| `shadow` | invalid receipt present | old gate allows |
| `receipt_authoritative_with_old_fail_safe` | invalid receipt present | receipt gate blocks |
| `receipt_authoritative` | invalid receipt present | receipt gate blocks |

This validates the intended decision function and the hook's selected-mode
path. It does not prove that the active Grok host will pass a workflow-scoped
environment variable into every hook invocation.

## Claim ledger

| Claim | Type | Evidence | Confidence | Falsifier | Action allowed |
|---|---|---|---|---|---|
| The three mode functions exist in the current source | verified_fact | `quality_gate.py:46-70` | high | source differs at integration head | inspect before merge |
| Missing and invalid receipt state produce the expected mode-specific decisions | measured_metric | 14 new tests, including `quality_gate.main()` | high for tested path | controlled test fails at integration head | parent may review test commit |
| The receipt mode can be scoped to `/ship-py` with the current env knob | unsupported | inspected registrations/config/orchestrator expose no scoped injection path | low | a lower-level host launcher facility is found and verified | do not activate |
| Git identity resolution is below 200 ms | unsupported | existing test threshold only | none | two observed runs were 814-1022 ms | investigate separately |
| Global authoritative activation is safe | unsupported | no live deny/re-entry run or rollback test | none | any missing receipt or hook error is allowed unexpectedly | do not activate |

## Adversarial review

- Tested production exclusion behavior rather than assuming any `.py` path is
  tracked; the initial `P:/tmp` fixture was rejected and corrected.
- Tested missing versus present-invalid receipt state separately; these are
  different branches in the fail-safe mode.
- Used valid session IDs after identifying that malformed IDs exit before the
  gate decision.
- Did not treat unit tests as proof of active hook registration.
- Did not treat the existing latency assertion as a passing performance fact.
- No tautological metric, retry duplication, stale artifact, or cohort issue
  applies to this decision test.

## Parent decision required

Before activation, choose one:

1. Keep `shadow` while a host-scoped opt-in path is designed and tested.
2. Authorize a deliberately global `receipt_authoritative_with_old_fail_safe`
   pilot with an explicit rollback condition and live deny/re-entry receipt.
3. Authorize full `receipt_authoritative` only after the fail-safe pilot and
   the identity-resolution latency issue are resolved or accepted.

The recommended next technical action is to verify how Grok constructs hook
process environments and implement a scoped opt-in only if that path is
real. Otherwise keep the default unchanged and record the global activation
decision explicitly.

## Handoff state

- Validation: complete for the isolated test scope.
- Production activation: not performed.
- Shared checkout: preserve and revalidate before integration.
- Remaining risk: hook-environment scoping and Git identity latency.
- Next executable action: inspect the Grok hook launcher environment path,
  then run a controlled live deny/re-entry test under the selected mode.
