# Target LLM prompt: fix the `/close` fail-open control path

You are the implementation owner for the Grok Build `/close` control path. Work
in this session and fix the verified control-system defect described below.
You are not alone in the workspace. Preserve concurrent work; do not revert,
reset, overwrite, stash, stage, commit, push, or discard changes made by other
sessions.

## Objective

Make it mechanically impossible for `/close` to emit `SESSION CLOSED`,
successful persistence, completed AAR, or an equivalent clean-close claim when
the current scanner attempt is absent, stale, malformed, timed out, killed, or
still has live descendants.

Do not treat the scanner's performance cause as established. The verified root
cause is that scanner execution, result freshness, failure disposition, and
terminal claims are not joined by one code-owned state transition. When the
scanner became unavailable, model judgment substituted for evidence.

## Required reading

Read these before editing:

- `P:\AGENTS.md`
- `C:\Users\brsth\.grok\AGENTS.md`
- `C:\Users\brsth\.grok\active-surface.last.md`
- `C:\Users\brsth\.grok\docs\user-guide\08-skills.md`
- `C:\Users\brsth\.grok\docs\user-guide\20-background-tasks.md`
- `C:\Users\brsth\.grok\docs\user-guide\10-hooks.md`
- `C:\Users\brsth\.grok\skills\close\SKILL.md`
- `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
- `C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py`
- `C:\Users\brsth\.grok\skills\close\tests\`
- `C:\Users\brsth\.grok\hooks\scripts\EVIDENCE_CONTRACT.md`
- `C:\Users\brsth\.grok\hooks\scripts\quality_gate.py`
- `P:\docs\handoffs\close-scanner-timeout-safe-fallback-20260726\HANDOFF.md`
- `P:\docs\handoffs\close-scanner-timeout-safe-fallback-20260726\TARGET-LLM-PROMPT.md`
- `C:\Users\brsth\.codex\attachments\2dfa08a1-b002-44a0-886b-a0136075569b\pasted-text.txt`

Read the current source, not only committed `HEAD`. The close files already
have substantial uncommitted changes.

## Current verified facts

- `/close` is a hot-reloaded user skill. Its `SKILL.md` currently directs the
  model to launch `close_accounting.py` directly.
- `close_accounting.py` accepts only `standard` and `deep`; `quick` is invalid.
- The scanner writes one normal evidence ledger at
  `P:\.artifacts\close-evidence\<session-id>.json`, replacing the prior file.
- The incident's last available ledger was generated before the failed final
  scan. It cannot prove the later close claims.
- The target output explicitly emitted a summary from session context and
  judgment after killing timed-out scanner attempts.
- A timed-out diagnostic in the parent review left its Python child alive after
  the parent tool timed out. The child had to be terminated explicitly. Parent
  cancellation therefore must not be treated as proof of descendant cleanup.
- These files are currently modified and must not be overwritten:
  - `skills/close/SKILL.md`
  - `skills/close/__lib/close_accounting.py`
  - `skills/close/__lib/validate_close_receipt.py`
  - `skills/close/tests/test_new_features.py`
  - `skills/close/tests/test_scanner.py`
- The current uncommitted changes already remove `quick`, validate AAR
  completion receipts, and render unresolved attention as `CLOSE INCOMPLETE`.
  Extend those changes; do not duplicate or revert them.

## Preconditions and authority gate

1. Run the workspace `preflight` discovery audit against:
   - `C:\Users\brsth\.grok\skills\close`
   - `C:\Users\brsth\.grok\hooks`
   - relevant handoffs under `P:\docs\handoffs`
2. Record current branch, `HEAD`, worktrees, and exact dirty diff for every
   proposed target file.
3. Determine the owner of the current close-file modifications from available
   receipts/session evidence. If ownership cannot be established, do not
   overwrite them. Report the collision and stop.
4. Re-run the active-surface snapshot if runtime configuration changed since
   the recorded snapshot:

   ```powershell
   python C:\Users\brsth\.grok\hooks\scripts\active_surface_snapshot.py
   ```

5. Prove the loaded `/close` source and active Stop consumer before changing
   either. A filename match or passing unit test is not runtime authority.

## Required design

Implement one code-owned close-attempt state machine with these terminal states:

- `succeeded`
- `failed`
- `timed_out`
- `cancelled`
- `malformed`
- `cleanup_failed`

There must be no implicit success state and no transition from an unavailable
scanner result to a model-authored close summary.

### 1. Code-owned scanner runner

Add or extend a Grok-owned runner under the canonical close skill `__lib`
directory. Update the active `/close` skill to invoke this runner, not the raw
scanner.

The runner must:

- launch the exact supported scanner command using `--variant standard` and
  the canonical operator-facing format;
- have a finite, explicit outer deadline;
- assign a unique attempt ID;
- capture session ID, command, variant, PID, start/deadline/end timestamps,
  elapsed time, exit code, stdout/stderr tails, last phase/progress timestamp,
  and produced-ledger metadata;
- reject exit-zero output unless it is structurally valid, session-bound, and
  fresh for this attempt;
- never reuse a previous session ledger as the current result;
- on every non-success terminal state, return a minimal canonical
  `CLOSE INCOMPLETE` result that names scanner unavailability and contains no
  memory-derived accounting or persistence claims.

Do not add a `quick` or gate-skipping fallback.

### 2. Attempt-scoped evidence and freshness

Extend the existing close-evidence contract rather than creating an unrelated
state system.

The receipt design must:

- preserve every attempt rather than overwriting the only failure evidence;
- identify attempt ID, session ID, schema version, terminal state, and command;
- link a successful attempt to the exact normal ledger by hash and generation
  time;
- record cleanup outcome and any live descendant PIDs;
- atomically update the authoritative latest-attempt state;
- define how a later retry supersedes an earlier timeout without deleting it;
- make stale successful ledgers ineligible after a newer failed attempt;
- fail closed on missing, malformed, unknown-version, or partially written
  receipts.

Document the producer, consumer, freshness, and supersession rules in the
existing evidence contract.

### 3. Verified Windows process-tree cleanup

On timeout or cancellation, terminate the scanner and all descendants. Use a
Windows mechanism whose tree semantics can be tested on this host, such as a
Job Object or another explicitly verified descendant-controller design.

Do not claim cleanup from:

- killing only the shell or direct child;
- a tool response saying the parent task was killed;
- sending a signal without checking liveness;
- a mocked assertion that cleanup was attempted.

After cleanup, enumerate/check the tracked descendant PIDs and record whether
each is gone. `cleanup_failed` must keep close incomplete.

### 4. Claim consumer

Trace the active Stop/claim-enforcement path. Add the narrowest code-owned
consumer necessary so that text containing `SESSION CLOSED`, successful
persistence, completed AAR, or equivalent clean-close language is rejected
unless the latest attempt receipt:

- belongs to the current session;
- is `succeeded`;
- is fresh;
- links to the current valid evidence ledger;
- shows all required close gates resolved;
- shows successful process cleanup/no live descendants.

Do not treat a crashing, timed-out, or malformed enforcement hook as pass
evidence. Report it as `ENFORCEMENT_UNAVAILABLE`. If Grok's documented
fail-open hook protocol prevents a full invariant, state the residual host
boundary precisely and retain the runner-level fail-closed behavior.

Avoid broad lexical matching. Use parsed receipt/state evidence and
claim-specific tests.

### 5. Phase measurement, after safety

Only after the fail-closed path is working, perform bounded read-only
measurement to distinguish:

- transcript parsing;
- Git/status/history operations;
- `git_state_check.py`;
- `dirty_age.py`;
- AAR and continuation scanning;
- host/background-task orchestration.

Label the observed bottleneck only if timing evidence identifies it. Otherwise
report the performance root cause as unknown. Performance attribution does not
block acceptance of the safety correction.

## Allowed writes

After authority and collision checks pass:

- `C:\Users\brsth\.grok\skills\close\__lib\`
- `C:\Users\brsth\.grok\skills\close\tests\`
- `C:\Users\brsth\.grok\skills\close\SKILL.md`
- `C:\Users\brsth\.grok\hooks\scripts\EVIDENCE_CONTRACT.md`
- the proven active close-claim consumer and its focused tests
- `P:\docs\handoffs\close-scanner-timeout-safe-fallback-20260726\` for evidence
  and handoff updates

Use patch/edit-then-verify. Never full-overwrite an existing file.

## Forbidden actions

- Do not synthesize accounting, persistence, AAR, or closure from conversation
  memory.
- Do not invoke or implement `--quick`.
- Do not delete, truncate, rewrite, or compress session logs or raw evidence.
- Do not kill unrelated Python, PowerShell, Git, Grok, or agent processes.
- Do not stage, commit, push, reset, clean, stash, or discard.
- Do not edit generated/cache skill copies.
- Do not broaden into a general `/close` rewrite or unrelated hook hardening.
- Do not call the performance cause proven without phase timing.
- Do not report completion from unit tests alone.

## Stop if

- ownership of the existing dirty close files cannot be established;
- the active `/close` source or claim consumer cannot be proven;
- the required invariant depends on a host API outside editable authority;
- safe descendant tracking/termination cannot be implemented and verified;
- receipt freshness/supersession cannot prevent stale-success reuse;
- another session modifies a target after your preflight and the edits cannot
  be reconciled safely;
- a proposed path still permits clean-close claims without a fresh successful
  attempt receipt.

Report the exact path, PID/command where applicable, conflicting diff, and next
executable step.

## Required tests

Add tests for at least:

1. normal scanner success with a fresh matching ledger;
2. hanging scanner bounded by the outer deadline;
3. child and grandchild termination with post-cleanup liveness checks;
4. cleanup failure producing `cleanup_failed`;
5. nonzero exit;
6. missing output;
7. malformed output;
8. stale successful ledger from an earlier attempt;
9. newer timeout superseding an older success;
10. attempt-receipt atomicity and schema rejection;
11. refusal to emit clean close from every non-success state;
12. refusal to claim AAR completion without a valid AAR receipt;
13. refusal to claim persistence without current persistence evidence;
14. rejection of `quick`;
15. claim-consumer allow/block behavior using real receipt shapes;
16. unchanged canonical normal-path rendering.

The process-tree test must create a real child/grandchild on Windows and prove
they are gone. A test double may supplement but not replace it.

Run at minimum:

```powershell
cd C:\Users\brsth\.grok\skills\close
python -m pytest -q
python -m py_compile __lib\close_accounting.py __lib\validate_close_receipt.py
git -C C:\Users\brsth\.grok diff --check
```

Also run the focused test suite for the proven active claim consumer. If a full
suite exceeds the execution window, run it through a background process with
redirected output, bounded polling, and explicit cleanup; do not leave its
children running.

## Live acceptance

Unit tests prove only script behavior. Before `ready_for_parent_review`, run a
controlled live negative-path test in a disposable session:

1. invoke the actual `/close` path with a deliberately hanging scanner test
   double or supported injection;
2. observe a bounded timeout;
3. verify an attempt-scoped timeout receipt;
4. verify the operator output is canonical `CLOSE INCOMPLETE`;
5. verify no scanner descendant remains;
6. attempt a clean-close claim and verify the active claim consumer rejects it;
7. run a normal scanner attempt and verify unchanged successful rendering.

Do not use the operator's raw incident session as the destructive test target.

## Gate verdict

Return:

- `ready_for_parent_review` only if source authority, current-diff ownership,
  unit tests, real Windows process cleanup, receipt freshness, active claim
  consumption, and controlled live negative/normal paths are all evidenced;
- `partial` if the runner is fixed but active claim consumption or live runtime
  behavior is not proven;
- `needs_fix` if any non-success state can still produce clean-close claims or
  stale-success reuse;
- `blocked` for an authority, collision, or host-boundary stop condition.

## Final evidence packet

Return exactly these sections:

**Objective**
- Exact invariant achieved.

**Source authority**
- Preflight packet path, revision, scopes, canonical source/caller/consumer,
  conflicts, and unresolved areas.

**Concurrent work**
- Initial and final dirty status for every target file; ownership conclusion.

**Commands**

| Command | Exit | Duration | Result |
| --- | ---: | ---: | --- |
| `...` | 0/1/... | ... | ... |

**Artifacts**

| Path | Type | Attempt/session | Status/hash |
| --- | --- | --- | --- |
| `...` | source/test/receipt/log | ... | ... |

**Changed files**
- Exact paths and purpose.

**State-machine evidence**
- Every terminal state and its permitted final disposition.

**Process cleanup evidence**
- Parent/child/grandchild PIDs, cleanup method, and post-cleanup liveness result.

**Claim-consumer evidence**
- Exact active consumer, allow case, reject case, and live invocation receipt.

**Performance observations**
- Phase timings, or `root cause unknown`.

**Verification**
- Unit, integration, live negative-path, and live normal-path results kept
  separate.

**Gate verdict**
- `ready_for_parent_review`, `partial`, `needs_fix`, or `blocked`, with reason.

**Uncertainty**
- Residual host fail-open boundary or unverified behavior.

**Git status**
- Exact status; confirm no staging, commit, push, reset, clean, or stash.

**Forbidden actions avoided**
- Explicit confirmation for each prohibited action class.

The parent will inspect the source-authority packet, current diff, attempt
receipts, process liveness evidence, claim-consumer evidence, and fresh test
output. Do not call the work complete merely because a focused test passes.
