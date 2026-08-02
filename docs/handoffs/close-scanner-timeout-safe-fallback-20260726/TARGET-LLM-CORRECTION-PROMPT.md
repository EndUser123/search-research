# Target LLM correction prompt: repair `close_runner.py` before integration

You are continuing your own `/close` timeout-safety implementation. Your first
packet correctly reported `partial`, but parent adversarial review found
load-bearing defects in the two new files. Fix this prototype now. Do not wire
it into `/close` or the active Stop hook until the corrected code passes parent
review.

You are not alone in the workspace. Preserve all concurrent work. Do not
revert, overwrite, stage, commit, push, reset, clean, stash, or discard changes
made by other sessions.

## Objective

Make the standalone runner and its tests truthfully enforce this invariant:

> A clean-close claim is allowed only when the current session has a fresh,
> strictly validated successful attempt, a matching newly generated evidence
> ledger, all required close gates are resolved, and every tracked scanner
> descendant is confirmed terminated.

This correction phase owns only the standalone runner and its tests. It does
not authorize production wiring.

## Current authority and state

- Preflight packet produced by parent review:
  `P:\tmp\close-runner-review-source-discovery-20260726.json`
- Reviewed `C:\Users\brsth\.grok` revision:
  `d96a2df2f1d547bf8183a10fcd0ee591d185cc0f`
- Preflight scopes:
  - `C:\Users\brsth\.grok\skills\close`
  - `C:\Users\brsth\.grok\hooks\scripts`
  - `P:\docs\handoffs\close-scanner-timeout-safe-fallback-20260726`
- Preflight decision: `proceed_with_discovery`
- No active `close_runner` or `validate_close_claim` wiring was found.
- Your files are currently untracked:
  - `C:\Users\brsth\.grok\skills\close\__lib\close_runner.py`
  - `C:\Users\brsth\.grok\skills\close\tests\test_close_runner.py`
- These existing files are modified by another session and are forbidden in
  this phase:
  - `C:\Users\brsth\.grok\skills\close\SKILL.md`
  - `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
  - `C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py`
  - `C:\Users\brsth\.grok\skills\close\tests\test_new_features.py`
  - `C:\Users\brsth\.grok\skills\close\tests\test_scanner.py`

Recheck the current diff before editing. If either allowed file changed after
your packet, reconcile ownership before proceeding.

## Parent-confirmed failures

The existing 24 tests pass, but the following probes also pass and disprove the
claimed invariant:

```text
incomplete_as_success= True
wrong_top_level_session_as_success= True
missing_ledger_claim= (True, 'validated')
fallback_validator= (
  False,
  ['Close summary is missing the canonical human-readable sections: ...']
)
```

The causes are verified in current source:

1. `_validate_scanner_output()` accepts arbitrary non-JSON text containing
   `CLOSE`, including `CLOSE INCOMPLETE`.
2. JSON session binding looks in the wrong location and accepts a mismatched
   top-level `session_id`.
3. `validate_close_claim()` reads `ledger_path` and then returns `True` without
   validating ledger existence, hash, session, freshness, schema, or gates.
4. A successful scanner process is treated as equivalent to a clean-close
   disposition. A scanner may run successfully while reporting unresolved
   gates.
5. `_ProcessTreeKiller.kill_all()` tracks and checks only the parent PID. It
   cannot report a surviving grandchild.
6. If `_ProcessTreeKiller` construction fails, the fallback kills only the
   direct child and records `cleanup_ok=True`.
7. Execution exceptions other than `KeyboardInterrupt` can escape without a
   terminal attempt result.
8. Concurrent attempts unconditionally replace `latest-attempt.json`; an older
   attempt finishing later can supersede a newer attempt.
9. The fallback `CLOSE INCOMPLETE` output is rejected by the existing canonical
   receipt validator.
10. `ledger_generated_at` is set to the runner's current time rather than read
    from the ledger and proven to belong to this attempt.

Do not argue from the passing suite. Add tests that fail on current code, record
the RED results, then repair the implementation.

## Scope

Work directory:

- `C:\Users\brsth\.grok\skills\close`

Allowed reads:

- all close skill source and tests;
- the parent preflight packet;
- the original handoff and both target prompts;
- `C:\Users\brsth\.grok\hooks\scripts\EVIDENCE_CONTRACT.md`;
- Grok user-guide documentation needed for process/runtime behavior.

Allowed writes:

- `C:\Users\brsth\.grok\skills\close\__lib\close_runner.py`
- `C:\Users\brsth\.grok\skills\close\tests\test_close_runner.py`
- this handoff directory for a correction evidence packet only.

Forbidden writes:

- every other source, test, hook, skill, config, cache, generated file, or raw
  session artifact.

Git actions:

- do not stage, commit, push, reset, clean, stash, amend, or discard.

## Required corrections

### 1. Replace permissive output validation

Do not infer scanner validity from human text markers.

- Invoke the scanner in a strict machine-readable mode internally.
- Parse the complete JSON object.
- Require the exact expected schema and top-level `session_id`.
- Require `variant == "standard"` for the public close path.
- Reject missing, extra/ambiguous, malformed, or wrong-session identity.
- Reject output whose scanner disposition/gates do not support a clean close.
- Use the existing canonical renderer for operator output after validating the
  structured result; do not create a competing renderer.

If using the existing renderer from `close_accounting.py` would require editing
the concurrently owned file, stop and report the precise integration boundary.
Do not copy the renderer into the runner.

### 2. Distinguish scanner execution success from clean-close eligibility

Keep two facts separate:

- the scanner process completed successfully;
- the evidence says the session may close cleanly.

A successful scan with open handoffs, `needs_attention`, `needs_llm_check`,
manual-review requirements, blocked work, missing AAR, unverified persistence,
or any equivalent unresolved state must not authorize a clean-close claim.

Inventory the actual gate-state enum from current source. Define allowed terminal
gate states from that inventory, not from guesswork. Test every disallowed state.

### 3. Validate the evidence ledger completely

A succeeded attempt receipt must link to the exact ledger created by that
attempt. Validate at minimum:

- canonical resolved path under `P:\.artifacts\close-evidence`;
- file exists and is a regular file;
- supported ledger schema;
- exact session ID;
- exact variant;
- ledger `generated_at` is parsed from the ledger, is not before attempt start,
  and is not unreasonably after attempt end;
- ledger file timestamp/fingerprint is fresh for this attempt;
- SHA-256 matches the receipt;
- ledger gates match the structured scanner output;
- every required gate is eligible for a clean close;
- persistence evidence and AAR receipt requirements are satisfied.

Never manufacture `ledger_generated_at` with `_utc_now()`. Read it from the
ledger and validate it.

`validate_close_claim()` must fail closed on `None`, missing file, wrong hash,
wrong session, stale time, unsupported schema, mismatched gates, unresolved
gates, invalid cleanup, or malformed data.

### 4. Make attempt ordering concurrency-safe

Prevent an older attempt from overwriting a newer attempt as authoritative.
Use one of:

- a per-session single-flight lock with explicit stale-lock handling; or
- an atomic compare-and-swap/ordering protocol whose correctness is tested.

Define whether ordering is by monotonic sequence, start time, or another stable
value. Wall-clock timestamps alone are insufficient if equal or skewed.

Tests must include:

- older attempt finishes after newer failure;
- concurrent start is rejected or serialized;
- stale lock recovery, if locks are used;
- failed pointer update cannot silently authorize the prior success.

### 5. Verify the actual process tree

Before termination, enumerate and retain the complete descendant PID set for
the scanner. After termination:

- verify the parent and every recorded descendant;
- use an exact PID liveness method, not substring matching;
- include every survivor in the receipt;
- set `cleanup_ok=True` only when all tracked PIDs are confirmed inactive.

The direct-child-only fallback must never report successful cleanup. If verified
tree control is unavailable, use `cleanup_failed` and keep close incomplete.

The real Windows test must assert both:

- child and grandchild are dead;
- `kill_all()` itself returned `cleanup_ok=True` with no survivors.

Also add a test where the parent dies but a simulated descendant survives and
ensure cleanup reports failure.

### 6. Cover every execution failure

Convert process launch errors, communicate errors, decoding/validation errors,
hash/ledger errors, cancellation, and cleanup errors into explicit non-success
terminal results.

The runner must:

- attempt to write a receipt for every reached attempt;
- emit canonical incomplete output and nonzero exit on every non-success path;
- never convert receipt-write failure into success;
- report `ENFORCEMENT_UNAVAILABLE` when authoritative state cannot be written or
  read.

Do not catch errors merely to continue with reduced safety.

### 7. Use the existing canonical output contract

The failure output must pass the current
`validate_close_receipt.validate_close_receipt()` contract and remain visibly
`CLOSE INCOMPLETE`.

Do not weaken the existing validator to accept the current ad hoc template.
Change only the runner-owned output construction in this phase, using existing
renderer/contract helpers where safely reusable.

## Mandatory RED tests

Before implementation, add tests that reproduce these exact failures and show
they fail against the current code:

1. `CLOSE INCOMPLETE` text is rejected as successful scanner output.
2. Wrong top-level session ID is rejected.
3. Succeeded receipt with `ledger_path=None` rejects clean-close claim.
4. Missing ledger file rejects.
5. Ledger hash mismatch rejects.
6. Ledger generated before attempt start rejects.
7. Ledger session mismatch rejects.
8. Unresolved gate in a valid ledger rejects.
9. Scanner success with unresolved gates does not authorize clean close.
10. Parent dead plus grandchild alive reports cleanup failure.
11. Tree-killer unavailable never records `cleanup_ok=True`.
12. Process-launch exception produces incomplete disposition.
13. Older attempt finishing later cannot supersede newer failure.
14. Runner-generated incomplete output passes the existing receipt validator.

Record the initial failing command, exit code, and failing test names. A test
that passes before the implementation change is not a valid RED test.

## Verification

Run:

```powershell
cd C:\Users\brsth\.grok\skills\close
python -m pytest -q tests\test_close_runner.py --timeout=30
python -m pytest -q --timeout=60
python -m py_compile __lib\close_runner.py
git -C C:\Users\brsth\.grok diff --check
git -C C:\Users\brsth\.grok status --short -- skills\close
git -C C:\Users\brsth\.grok diff --cached --name-only
```

Re-run the four parent probes and require:

```text
incomplete_as_success= False
wrong_top_level_session_as_success= False
missing_ledger_claim= (False, <reason>)
fallback_validator= (True, [])
```

If the full suite exceeds its bound, use a background process with redirected
output, bounded polling, and verified process cleanup. Do not leave a test
process running and do not describe a timeout as pass or fail.

## Do not

- Do not wire `close_runner.py` into `SKILL.md`.
- Do not edit `quality_gate.py` or `EVIDENCE_CONTRACT.md`.
- Do not claim the production `/close` path is fixed.
- Do not add lexical enforcement in place of receipt validation.
- Do not weaken existing validators or gates.
- Do not add `--quick` or another degraded bypass.
- Do not infer the scanner performance root cause.
- Do not delete or rewrite raw incident evidence.
- Do not touch concurrent modifications.
- Do not report `ready_for_parent_review` from the old 24 tests alone.

## Stop if

- either allowed file has an ownership conflict you cannot reconcile;
- strict validation requires changing a concurrently owned file;
- the canonical renderer cannot be reused without duplicating it;
- the actual gate-state contract cannot be determined;
- safe Windows descendant enumeration/liveness verification is unavailable;
- concurrency ordering cannot be made atomic;
- any correction would require production wiring in this phase.

Return `blocked` with exact source lines, commands, and the next executable
integration step. Do not work around the stop condition.

## Gate verdict

Return:

- `ready_for_parent_review` only when every mandatory RED test first failed,
  then passes; all four parent probes have the required corrected results; the
  full suite passes; real Windows descendant cleanup passes; and only the two
  allowed code/test files changed;
- `needs_fix` if any unsupported success or false cleanup remains;
- `blocked` if a stop condition fires;
- `partial` only for a sound, fail-closed prototype whose remaining work is
  explicitly outside the two-file correction scope.

This verdict covers the standalone prototype only. It does not authorize
production integration.

## Final evidence packet

Return exactly:

**Objective**
- Corrected standalone invariant.

**Preconditions**
- Preflight packet, revision, initial hashes/status, ownership check.

**RED evidence**

| Test | Initial command | Exit | Confirmed failure |
| --- | --- | ---: | --- |
| `...` | `...` | 1 | exact assertion |

**Commands**

| Command | Exit | Duration | Result |
| --- | ---: | ---: | --- |
| `...` | 0/1/... | ... | ... |

**Artifacts**

| Path | Type | Status/hash |
| --- | --- | --- |
| `...` | source/test/receipt/log | ... |

**Changed files**
- Exact files and purpose; confirm no other file changed by this session.

**Corrected invariants**
- Output identity validation.
- Ledger binding and gate eligibility.
- Attempt ordering.
- Descendant cleanup.
- Exception/receipt behavior.
- Canonical incomplete rendering.

**Parent probes**

```text
incomplete_as_success= ...
wrong_top_level_session_as_success= ...
missing_ledger_claim= ...
fallback_validator= ...
```

**Verification**
- Focused suite.
- Full suite.
- Real Windows process-tree test.
- Compile and diff checks.
- Production wiring: `NOT PERFORMED`.

**Gate verdict**
- `ready_for_parent_review`, `needs_fix`, `blocked`, or `partial`.

**Uncertainty**
- Remaining prototype or host-boundary limitations.

**Git status**
- Exact status; distinguish pre-existing concurrent changes from your two
  files.

**Forbidden actions avoided**
- No production wiring.
- No concurrent-file edits.
- No staging, commit, push, reset, clean, stash, or discard.
- No raw-evidence mutation.
- No unsupported completion claim.

The parent will independently rerun the adversarial probes and inspect the diff.
