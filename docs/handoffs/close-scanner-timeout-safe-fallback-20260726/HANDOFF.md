---
thread_id: close-scanner-timeout-safe-fallback-20260726
parent_handoff_path: none
current_session_id: 019f96f5-dc4a-79d0-9e17-396f2a582186
produced_at: 2026-07-26T01:00:00-06:00
status: open
handoff_type: implementation
implementation_status: RUNNER_IMPLEMENTED_AND_INTEGRATED
last_updated: 2026-07-27T01:10:00Z
---

# Cold-start implementation prompt: make `/close` timeout-safe

**STATUS UPDATE (2026-07-27):** The runner (`close_runner.py`) is fully
implemented, integrated into SKILL.md, tested (43 tests + 338 full suite),
and committed at HEAD. The controlled live test (disposable session
`0a4874b2-435c-4b93-bf27-141529bd3335`) passed with a Python-level git
mutation guard proving zero mutations reached real Git. The contract test
fixes (schema version 2.0, .md substantive-work) are also committed.

**Remaining:** (1) exercise the compact-success rendering path on a real
clean-close session; (2) the concurrent SKILL.md "What's at risk" hunk
remains uncommitted; (3) 2 local-ahead commits need pushing when ready.

You are a delegated implementation agent. You are not alone in the workspace;
do not revert, reset, overwrite, stage, commit, or push changes made by other
sessions. Preserve unrelated dirty work.

## Objective

Make `/close` fail closed and remain diagnostically useful when the
deterministic close scanner hangs, times out, or is killed. A scanner timeout
must never lead the agent to synthesize a close summary from memory, claim that
`/aar` ran when it did not, invoke a nonexistent `--quick` scanner mode, or
finish while a scanner child process is still running.

## Observed incident

The operator observed this `/close` trace:

- scanner started at 12:33 AM;
- agent reported `Scanner still running. Waiting.` at 12:36 AM;
- after eight minutes it diagnosed a hang and killed the scanner at 12:42 AM;
- it attributed the problem to a 14 MB `updates.jsonl` and a large dirty tree;
- it attempted a `--quick` variant, then started another standard scan;
- it considered emitting a close summary from session context because the scan
  timed out;
- the UI still reported `1 command still running`.

This is two separate concerns:

1. The scanner or its host task may have a performance/timeout defect.
2. The fallback behavior is unsafe regardless of the root performance cause.

## Verified source facts

Read these source files before changing anything:

- `C:\Users\brsth\.grok\skills\close\SKILL.md`
- `C:\Users\brsth\.grok\skills\close\__lib\close_accounting.py`
- `C:\Users\brsth\.grok\skills\close\__lib\validate_close_receipt.py`
- `C:\Users\brsth\.grok\skills\close\tests\`
- `P:\AGENTS.md`
- `C:\Users\brsth\.grok\AGENTS.md`
- `C:\Users\brsth\.grok\active-surface.last.md`

Current facts already verified:

- Public `/close` accepts no user arguments.
- `close_accounting.py` accepts only `standard` and `deep`; `--quick` is not a
  valid current scanner mode.
- The public skill path invokes the standard compact scanner.
- `_git()` uses a default 10-second subprocess timeout.
- Cross-repository `git_state_check.py` and `dirty_age.py` use 30-second
  subprocess timeouts.
- `/close` requires a valid scanner result before it can resolve gates.
- Substantive work without a valid AAR completion receipt must keep the
  retrospective gate unresolved.
- A valid AAR receipt requires the report-plus-packet validator, session
  identity, terminal `status: completed`, canonical report path, and matching
  report hash.
- The existing canonical renderer is bottom-up and ends with `## Final status`.

These facts do not prove which scanner phase caused the observed delay. Do not
promote the 14 MB transcript or 1000+ dirty files to root cause without a
measurement.

## Scope

Work directory:

- `C:\Users\brsth\.grok` for Grok-owned close code and tests
- `P:\` only for the durable handoff and workspace-owned test/diagnostic
  artifacts

Allowed reads:

- the files listed above;
- the active Grok invocation/orchestration source discovered by tracing the
  `/close` command;
- relevant tests, artifacts, logs, and session metadata needed to reproduce
  the timeout safely.

Allowed writes:

- `C:\Users\brsth\.grok\skills\close\__lib\`;
- `C:\Users\brsth\.grok\skills\close\tests\`;
- the active Grok-owned `/close` orchestration source, only after proving it is
  the loaded source of truth;
- this handoff directory for evidence updates.

Forbidden writes:

- generated/cache copies of skills;
- unrelated skills, hooks, plugins, or workspace packages;
- raw session evidence, `updates.jsonl`, `chat_history.jsonl`, or existing AAR
  packets;
- unrelated user dirty files.

Git:

- Do not stage, commit, push, reset, clean, stash, or discard changes.

## Required implementation

1. Trace the real `/close` invocation path. Confirm where the scanner process is
   launched, where task timeout/cancellation is handled, and where the agent
   receives the scanner result. Do not assume the skill prose is the runtime
   hook.

2. Add a bounded outer scanner execution contract. The exact timeout may be
   chosen after measuring the normal path, but it must be finite and explicit.
   On timeout, capture:

   - session ID;
   - scanner command and variant;
   - start time, deadline, and elapsed time;
   - last known scanner phase if available;
   - stdout/stderr tail;
   - process ID/tree cleanup result;
   - whether a valid evidence ledger was produced.

3. Ensure timeout cleanup terminates the scanner process tree, not only the
   parent process. Verify no scanner child remains before the caller proceeds.

4. Produce a machine-readable timeout/unavailable receipt in the existing
   close-evidence area or the active canonical state location. Reuse existing
   receipt conventions instead of inventing a parallel state system.

5. Make the close state machine fail closed when the scanner result is absent,
   malformed, timed out, or incomplete:

   - no clean-close disposition;
   - no summary synthesized from session memory;
   - no claim that `/aar` ran unless a valid AAR completion receipt exists;
   - final disposition explicitly says scanner unavailable/timeout;
   - preserve the timeout receipt for the next session or retry.

6. Remove or correct any active orchestration text that attempts
   `--quick`. Do not add a new quick mode as a workaround. If a degraded retry
   is useful, it must be an explicit, code-supported mode with its own receipt
   and must not bypass required gates.

7. Preserve the mandatory AAR contract. A scanner timeout must not silently
   turn `/aar` into an optional step. If the active orchestrator cannot safely
   continue to AAR after a scanner failure, it must say so explicitly and
   remain `CLOSE INCOMPLETE`; it must not claim AAR completion.

8. Add progress/phase observability only if it fits the existing architecture:
   phase start, phase completion, and last-progress timestamp are sufficient.
   Avoid noisy per-file logging or large transcript duplication.

9. Investigate the performance cause with bounded, read-only measurement. At
   minimum distinguish:

   - transcript parsing;
   - Git/status/history operations;
   - `git_state_check.py`;
   - `dirty_age.py`;
   - AAR/continuation packet scanning;
   - host task orchestration.

   Do not broaden the implementation into a general scanner rewrite unless a
   measured bottleneck requires it.

## Do not

- Do not emit a close report from memory after a failed scan.
- Do not treat the scanner's progress text as proof that the process is alive.
- Do not kill only the parent and leave child commands running.
- Do not invoke `--quick`; it is not part of the current scanner contract.
- Do not treat a timeout as a clean scan, a skipped gate, or an operator waiver.
- Do not claim `/aar` ran without a valid terminal AAR receipt.
- Do not delete or rewrite the 14 MB session transcript.
- Do not infer the root cause from file size or dirty-file count alone.
- Do not commit or push.

## Stop if

- the active `/close` invocation source cannot be identified;
- the scanner timeout is controlled by an external host API that cannot be
  changed from the allowed source tree;
- process-tree termination cannot be performed safely or verified;
- reproducing the timeout would require deleting, rewriting, or truncating
  session evidence;
- another session is editing the same target files and the change cannot be
  applied without overwriting it;
- a proposed fallback would permit a clean or complete disposition without a
  valid scanner result.

Report the blocker with the exact source path, command, and evidence.

## Acceptance criteria

### Safety

- A scanner timeout produces a durable timeout/unavailable receipt.
- The resulting close disposition is `CLOSE INCOMPLETE` or equivalent and
  explicitly names scanner unavailability.
- No memory-derived summary is emitted.
- No scanner child remains after timeout cleanup.
- A missing or invalid scanner result cannot satisfy the AAR or persistence
  gates.

### Compatibility

- Normal scanner execution still produces the canonical compact report.
- A valid AAR completion receipt still flows through `/close` normally.
- Existing close report validation still rejects hybrid/legacy narratives.
- The public `/close` interface remains argument-free.

### Tests

Add regression tests for:

1. a hanging scanner process and bounded timeout;
2. process-tree cleanup or a safe test double proving cleanup is attempted;
3. malformed/missing scanner output;
4. timeout receipt contents;
5. refusal to emit clean close from a timeout;
6. refusal to claim AAR completion without its receipt;
7. rejection of stale `--quick` orchestration;
8. unchanged normal-path rendering.

Run at minimum:

```powershell
python -m pytest -q
python -m py_compile __lib\close_accounting.py __lib\validate_close_receipt.py
git diff --check
```

If the active orchestrator has its own tests, run the smallest complete suite
covering its timeout/cancellation path as well.

## Final packet required from the cold-start agent

Return an evidence packet, not a narrative:

**Objective**
- State the exact timeout-safety outcome achieved.

**Preconditions**
- Active `/close` source path identified.
- Current scanner command and supported variants verified.
- Concurrent edits and relevant dirty state checked.

**Commands**
| Command | Exit | Notes |
| --- | ---: | --- |
| `...` | 0/1/... | exact result |

**Artifacts**
| Path | Type | Status |
| --- | --- | --- |
| `...` | source/test/receipt/log | found/written/missing |

**Changed files**
- Exact files changed, or `None`.

**Key observations**
- Measured slow phase, if identified.
- Timeout and cleanup behavior.
- Whether the normal path remained compatible.

**Gate verdict**
- `ready_for_parent_review`, `needs_fix`, `blocked`, or `partial`.
- Explain why; do not call it complete merely because tests pass.

**Uncertainty**
- Root cause still unknown, if applicable.
- Host-level behavior not directly verifiable, if applicable.

**Git status**
- Exact status summary; confirm no staging/commit/push occurred.

**Forbidden actions avoided**
- No deletion or rewriting of raw evidence.
- No stale quick-mode fallback.
- No memory-derived close summary.
- No commit or push.

## Parent integration rule

The parent session must inspect the active-source proof, diff, timeout receipt,
process-cleanup evidence, and fresh test output before accepting the change.
Passing unit tests alone does not prove the live Grok `/close` path invokes the
new timeout contract.
