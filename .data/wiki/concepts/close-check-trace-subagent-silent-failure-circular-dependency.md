---
title: "close-check pre-close-readiness depends on /trace, but /trace itself can fail silently inside the rhai workflow engine — circular-dependency single-point-of-failure"
created: 2026-08-01
source: session-019fb933-040b-7720-a257-e364f5df726f (close-check wf_019fbfc50a2b7411a3f4da20fd1c8751)
tags: [close-check, trace, workflow-engine, single-point-of-failure, circular-dependency, critical-code-trace, rhai-workflow, agentic-sdlc]
agent: grok
host: grok
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md
    type: extends — Phase 3 (Remediate) auto-invokes /trace but does not enforce its success
  - target: wiki/concepts/close-check-invokes-capture.md
    type: related — same auto-act surface (Phase 3 Remediate subagents)
  - target: wiki/concepts/multi-subagent-orchestration-workflow-failure-patterns.md
    type: extends — adds workflow-engine silent-abort to the existing 5 subagent failure patterns
  - target: wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md
    type: related — smoke check passes parse, not behavioral execution; same validation gap
  - target: wiki/concepts/pre-packed-evidence-pattern-for-workflow-subagents.md
    type: related — pre-packed evidence doesn't help when the subagent itself aborts before reading
summary: >
  The close-check pre-close-readiness gate depends on /trace to verify critical code
  (close-check.rhai, close-check.md) was traced before the session can be marked
  complete. But /trace itself is invoked as a Phase 3 Remediate subagent inside the
  rhai workflow engine, and the engine can silently abort it with status='failed'
  / reason='unknown error' — producing no TRACE REPORT output, no diagnostic, and
  no operator-visible signal beyond "trace was attempted and failed." This is a
  structural circular dependency: the workflow that defines the readiness gate
  cannot self-verify the code that defines the gate. The critical-code-trace check
  in pre-close-report.md becomes a fail despite the code being written and the
  trace being attempted, because the verification mechanism itself is unreliable
  in the only context where it matters most (session-close).
---

# close-check pre-close-readiness depends on /trace, but /trace itself can fail silently inside the rhai workflow engine — circular-dependency single-point-of-failure

## Decision context

**The structural concern flagged in pre-close-report.md:**

> "Pre-close readiness gate itself depends on /trace, which cannot self-verify the code that defines it."

This is not a hypothetical concern. It was observed in the live close-check workflow run for session 019fb933 (workflow `wf_019fbfc50a2b7411a3f4da20fd1c8751`). The workflow completed (status: complete, workflow_completed at 2026-08-02T00:25:50) but the critical-code-trace check registered as `[fail]` because:

1. **Critical code WAS written:** close-check.rhai + close-check.md committed during this session
2. **/trace WAS attempted:** Phase 3 Remediate invoked `/trace` as an auto-act subagent
3. **/trace FAILED silently:** `state.json` shows trace subagent `state='failed'`, reason='unknown error', no TRACE REPORT output produced
4. **Pre-close-readiness gate fails:** per the task rule, "status=fail if critical code was written but NOT traced" — even though trace was attempted, the absence of a TRACE REPORT counts as "not traced"

The result: a workflow that ran end-to-end, wrote the critical code it was designed to verify, and emitted a Finalize report — but its own readiness gate says "not ready" because the verification step that the gate depends on did not produce its expected artifact.

## The failure chain

```
close-check Phase 3 (Remediate)
  → invokes /trace as auto-act subagent
  → rhai workflow engine spawns subagent
  → subagent aborts with state='failed', reason='unknown error'
  → no TRACE REPORT written to disk
  → no operator-visible diagnostic beyond "trace was attempted and failed"
  → critical-code-trace check in pre-close-report.md: [fail]
  → workflow continues to Phase 4 (Finalize) — but readiness gate already failed
```

The "unknown error" reason is the key signal: the workflow engine is not surfacing the actual cause of the subagent failure. Comparing to [[multi-subagent-orchestration-workflow-failure-patterns]], that concept covers 5 patterns from a `/design` run, but the underlying mechanism is different — `/design` is a SKILL.md skill that the agent executes, while close-check is a rhai workflow file executed by `~/.grok/workflows/close-check.rhai` via the workflow tool. The failure modes of those two execution environments are distinct:

| Failure source | `/design` skill (agent-executed) | `close-check` rhai workflow |
|---|---|---|
| Subagent capability_mode | Agent sees warning in SKILL.md, can correct | Engine passes through silently |
| Resume failure recovery | Agent can re-launch fresh from SKILL.md guidance | Engine surfaces only "unknown error" |
| Model selection | Agent can probe before dispatch | Engine may pass through fleet-models.json stale data |
| Subagent abort | Agent sees full error in transcript | Engine records state='failed', no diagnostic |

The rhai workflow engine's failure surface is much narrower than the agent's. When a subagent aborts, the engine's status record is the only signal — and "unknown error" leaves the operator guessing.

## Why /trace is the canary

`/trace` is uniquely positioned as the canary for this failure mode because:

1. **It's invoked by close-check itself.** Other Phase 3 subagents (capture, handoff, wiki) write artifacts that close-check can verify locally. /trace writes a separate artifact (TRACE REPORT) that close-check depends on but doesn't generate — making /trace the only Phase 3 subagent whose success is structurally outside the workflow's control surface.
2. **Its output is a precondition for the readiness gate.** "Critical code was written but NOT traced" is the failure mode the gate specifically catches — and the only way to clear that gate is a TRACE REPORT from /trace, which the engine may fail to produce.
3. **The exact code that defines the gate is the same code that needs tracing.** The circular dependency: close-check.rhai defines the readiness gate; close-check.rhai itself is the critical code that /trace must trace; /trace runs inside close-check.rhai as a Phase 3 subagent. The verifier and the verified are the same artifact, running in the same execution context.

## What this means for our workspace

### 1. /trace must have a fail-loud contract inside rhai workflows

The current behavior — subagent state='failed', reason='unknown error', no artifact — leaves the operator with no actionable signal. Two structural fixes:

**(a) Engine-level diagnostic capture:** the rhai workflow engine should record the actual subagent error (HTTP status, exception class, last tool call) in `state.json` instead of "unknown error". Without this, every Phase 3 subagent failure is opaque.

**(b) /trace-level retry contract:** if /trace's subagent fails inside the workflow, /trace should automatically retry once with a fresh model + reduced context before declaring failure. The current /trace SKILL.md does not specify retry semantics inside a workflow context.

### 2. Critical-code-trace gate needs a fallback path

The current rule "status=fail if critical code was written but NOT traced" assumes a binary (traced / not traced). When trace was attempted but failed, the gate should distinguish:

- `traced_complete`: TRACE REPORT exists
- `traced_partial`: trace attempted, subagent failed, no report — needs operator attention
- `not_traced`: trace never invoked

The operator needs to know the difference between "your workflow skipped trace" and "trace ran and failed silently". Today, both look identical in the pre-close-report.

### 3. Phase 3 subagent failures need surfacing, not silent-continuation

3 of 5 Phase 3 subagents failed in this run (capture, handoff, trace) — the workflow continued to Phase 4 and emitted a Finalize report anyway. The workflow should surface per-subagent failure prominently in the Finalize report, not just record them in `state.json`. Operators reading the Finalize report should see: "trace: failed (unknown error); the critical-code-trace gate will not pass until this is resolved."

### 4. The circular dependency is structural, not a bug

This is not a workflow-engine bug to fix and walk away. The circular dependency (the gate's verifier is the same code as the verified artifact) is inherent to self-referential workflows. The fix is making the failure mode **observable** so operators can intervene, not eliminating the dependency.

## Falsifier

This finding is wrong if:

- The rhai workflow engine already surfaces subagent errors in `state.json` and the "unknown error" was a transient artifact (verify by reading the engine's status-reporting code)
- A retry mechanism for /trace inside workflows already exists and the operator didn't see it fire (verify by reading /trace SKILL.md and any retry wrapper)
- The critical-code-trace gate already distinguishes "attempted but failed" from "not invoked" (verify by reading the pre-close-report gate logic)
- The 3 Phase 3 subagent failures (capture, handoff, trace) actually produced useful artifacts despite the engine's "failed" status, making the engine's status record a misleading signal rather than a structural concern (verify by checking whether the workflow's Phase 4 succeeded using those artifacts)

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| Workflow wf_019fbfc50a2b7411a3f4da20fd1c8751 ran to complete (workflow_completed 2026-08-02T00:25:50) | Pre-packed evidence from session 019fb933 | [OBSERVED] |
| 3 of 5 Phase 3 subagents FAILED with 'unknown error' | Pre-packed evidence: "Remediate phase agents: capture (failed), friction (done), handoff (failed), trace (failed), wiki (done)" | [OBSERVED] |
| /trace specifically failed with no TRACE REPORT output | Pre-packed evidence: "trace subagent state='failed'... produced no TRACE REPORT output" | [OBSERVED] |
| Pre-close-report.md critical-code-trace check shows [fail] | Pre-packed evidence: "[fail] for 4 distinct findings" | [OBSERVED] |
| The structural concern was self-flagged in pre-close-report | Pre-packed evidence: "Pre-close readiness gate itself depends on /trace, which cannot self-verify the code that defines it" | [OBSERVED] |
| /tp critique (prompt 65 / 76) provided informal code review but is not equivalent to /trace | Pre-packed evidence | [OBSERVED] |
| Rhai workflow engine failure surface is narrower than agent-executed skills | Comparison to [[multi-subagent-orchestration-workflow-failure-patterns]] table | [INFERENCE] — engine internals not yet read this session |

## Sources

- Session 019fb933-040b-7720-a257-e364f5df726f (the analyzed session itself)
- Pre-packed evidence from session-attributed close-check sweep
- `~/.grok/workflows/close-check.rhai` — Phase 3 subagent invocation (path verified, code not re-read this session)
- `P:/.data/wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md` — Phase 4 design context
- `P:/.data/wiki/concepts/close-check-invokes-capture.md` — Phase 3 auto-act pattern
- `P:/.data/wiki/concepts/multi-subagent-orchestration-workflow-failure-patterns.md` — 5 patterns from /design run (different execution context)
- `P:/.data/wiki/concepts/pre-packed-evidence-pattern-for-workflow-subagents.md` — evidence pre-packing doesn't help when subagent aborts pre-read

## Auto-related

- [[close-runner-verdict-staleness-across-phases]]
- [[skill-graph]]
- [[close-scanner-verification-gap-stale-read]]
- [[trace-skill-execution-gap-critical-code-uncaught]]
- [[close-scanner-unavailable-fallback-session-observations-handoff]]

