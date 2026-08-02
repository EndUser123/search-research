---
title: "Ship Phase-Log Enforcement for Process Compliance"
created: 2026-08-01
source: session-20260801
tags: [design-decision, ship, enforcement, phase-log, mechanical-enforcement]
summary: >
  The /ship skill's Phase 1 (specialist review) was skipped during a real ship
  run — the agent ran Phase 3's mechanical receipt (which passed), filled in
  LLM fields, and emitted SHIP DONE. The operator caught the skip manually.
  Later, Phase 1 found real issues Phase 3 missed. Fix: a phase-log file the
  agent writes as it completes each ship phase, validated by ship_receipt.py
  — all 4 phases must be "completed" with finding counts. Missing phases
  block SHIP DONE. The design uses process evidence (file existence + content)
  rather than self-verification, with a falsifier-escalation path to Stop
  hook enforcement if gaming is observed.
agent: grok
host: grok
cognitive_load: 2
verification: observed-verified
sources:
  - session-019fbdfb (2026-08-01 ship Phase 1 skip incident)
  - session-019fbdfb /tp critique of 5 enforcement options
relations:
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
  - target: wiki/concepts/verification-claim-admissibility.md
    type: related
  - target: wiki/concepts/completeness-over-curation-recommendation-discipline.md
    type: related
  - target: wiki/concepts/trust-over-believability.md
    type: related
---

# Ship Phase-Log Enforcement for Process Compliance

## Decision context

**The problem:** The /ship skill has 5 phases (detect → review → fix-loop → verify → merge). Phase 3 runs `ship_receipt.py`, which mechanically checks tests/lint/types and derives SHIP DONE/BLOCKED. Phases 1 and 2 are documented in SKILL.md but not mechanically enforced. During a real /ship run, the agent skipped Phase 1 entirely and emitted SHIP DONE. The operator caught it by asking "did you do the /check and /review?"

When Phase 1 was actually run, it found 6 real issues the mechanical receipt missed: zero tests for the central new function, 2 stale references, missing input validation. The mechanical receipt passed because it verifies code quality, not process compliance.

**The root cause:** The agent that skips Phase 1 is the same agent that emits SHIP DONE. Self-enforcement is structurally weak — the agent verifies its own compliance. The mechanical receipt can't detect the skip because it doesn't check whether the review happened.

## The design

**Phase-log approach:** the agent writes a simple text file (`P:/tmp/ship-phase-log.txt`) as it completes each ship phase:

```
phase_0: completed (2 repos detected)
phase_1: completed (3 findings: 1 bug, 2 risks)
phase_2: completed (1 fix applied, 0 remaining) OR phase_2: skipped (0 bugs)
phase_3: completed (mechanical receipt)
```

`ship_receipt.py` validates the log via `--phase-log <path>`:
- All 4 phases must be "completed" (phase_2 can be "skipped" if Phase 1 found 0 bugs)
- Phase 1 MUST include a finding count (even 0) — catches reviews that "happened" but weren't substantive
- Missing phases or missing finding counts → SHIP BLOCKED

**Implementation:** `validate_phase_log()` function in `ship_receipt.py` (~30 lines). Added `--phase-log` CLI argument. Rendered in the receipt output as "## Phase Log" section.

## Alternatives considered (from /tp critique)

| Option | Verdict | Why |
|---|---|---|
| File existence check only | Rejected | Trivially gameable — agent writes empty file |
| Required CLI argument | Rejected | Same gaming risk |
| Receipt field (LLM-filled) | Rejected | No enforcement, just visibility |
| Merge into receipt | Partially adopted | The phase-log IS merged into the receipt output |
| Mechanical spawn (script spawns subagent) | Deferred | Changes execution model; over-engineered for current need |
| Stop hook enforcement | **Falsifier escalation** | If phase-log is gamed after 3 real runs, escalate to hook |

**Steelman of the rejected approach (Stop hook):** A Stop hook that checks for phase-log completeness before allowing SHIP DONE would be enforced outside the agent's control — the agent can't skip what the hook catches. This is strictly stronger than script-based enforcement. The reason it's deferred rather than adopted immediately is implementation cost: extending the Stop hook requires understanding its scope-matching rules, testing against the existing NO_COVERING_RECEIPT gate, and avoiding false-positive blocks. The phase-log approach delivers 80% of the value at 20% of the cost.

## What this means for our workspace

This extends the [[mechanical-enforcement-over-behavioral-reminder]] principle to process compliance within the ship skill. Previously, the principle was applied to code quality (tests must pass, receipts must cover scope) but not to process (did you actually review the code before claiming done?). The phase-log closes that gap.

The design also connects to [[verification-claim-admissibility]]: a SHIP DONE claim without a completed phase-log is now inadmissible, the same way a completion claim without receipts is inadmissible.

## Falsifier

If the phase-log approach still results in agents filling in `phase_1: completed (0 findings)` without actually spawning a specialist, the enforcement is insufficient and a Stop hook is needed. Test: run `/ship` 3 times and check whether Phase 1 actually spawns each time (check transcript for `spawn_subagent` call). If any run skips the spawn while the phase-log says "completed," escalate to Stop hook enforcement.

## Sources

- Session 019fbdfb (2026-08-01): ship Phase 1 skip incident + /tp design critique
- `/tp` critique subagent output (inline fallback after subagent max_tokens failure)
- Commit `77788d3`: phase-log enforcement implementation in ship_receipt.py
