---
title: "Run all lifecycle skills unconditionally — conditional detection is the gap"
created: 2026-08-01
source: session-019fb937 (close-check Phase 3 design)
sources:
  - internal: ~/.grok/workflows/close-check.rhai (Phase 3 Remediate)
  - internal: P:/.data/wiki/concepts/analysis-over-action-knowledge-capture-without-application.md
  - internal: P:/.data/wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
tags: [design-decision, close-check, lifecycle-skills, unconditional-execution, detection-gap]
agent: grok
host: both
cognitive_load: 2
verification: single-session-verified
summary: >
  Design decision: close-check Phase 3 runs all 5 lifecycle skills
  unconditionally — no conditional detection of which skills "should" run.
  The conditional detection approach (Phase 1 checks which skills ran, then
  Phase 3 runs only the missing ones) was the gap: the detector missed
  workflow-subagent invocations, produced false positives, and required
  the operator to manually curate which skills to invoke. Running all 5
  every time eliminates the detection problem entirely. The cost (running
  skills that might not be needed) is lower than the cost of missing one.
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: refines
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: related
  - target: wiki/concepts/analysis-over-action-knowledge-capture-without-application.md
    type: related
---

# Run all lifecycle skills unconditionally — conditional detection is the gap

## Decision context

**The problem:** close-check Phase 1 detected which lifecycle skills didn't run
("/capture didn't run", "/friction didn't run") and reported them as gaps.
Phase 3 was designed to run only the missing skills. But the detection
mechanism greps the transcript for slash-command invocations — it can't see
skills that ran as workflow subagents. This produced false positives
(every skill reported as "didn't run" even when Phase 3 ran them) and
required the operator to manually curate which to invoke.

**The operator's framing:** "Why don't we just simply run all the skills?
Why are we trying to get fancy and avoid work?"

**The insight:** conditional detection IS the gap. Every miss in detection
produces an uncaptured finding. The cost of running a skill that wasn't
needed (a few minutes of subagent time) is far lower than the cost of
missing a skill that was needed (a finding that slips through and recurs
in the next session). Eliminating detection eliminates the gap.

## The decision

Run all 5 lifecycle skills unconditionally in close-check Phase 3:
- `/capture` (auto-act) — always scans for uncaptured findings
- `/friction` (surface-only) — always reports friction patterns
- `/handoff` (auto-act) — always writes handoffs for open work
- `/trace` (surface-only) — always traces critical code
- `/wiki` (auto-act) — always captures durable knowledge

No conditions. No detection heuristics. No miss rate.

## Steelman (the rejected alternative)

**Conditional detection** (only run skills that Phase 1 identified as missing):
- **Pro:** faster (fewer skills to run), less redundant work
- **Con:** the detector is the single point of failure — if it misses, the
  finding is lost. On this host, the detector can't see workflow subagent
  invocations, so it always reports false positives. The "savings" from
  skipping skills that "already ran" are illusory when the detector is wrong.

**Why conditional lost:** the detector's accuracy is the bottleneck. A
detector with 100% accuracy would make conditional the right choice. But
LLM-based detection on a multi-agent host with workflow subagents, compaction,
and concurrent sessions will never reach 100%. The unconditional approach
trades a small constant cost (running 5 skills every time) for eliminating
an entire class of failure (detection misses).

## What this means for our workspace

New lifecycle skills added to close-check Phase 3 should also run
unconditionally. The `remediation_mode` tag (auto-act vs surface-only)
determines what happens with their output, not whether they run. The
unconditional model is simpler, more reliable, and eliminates the detection
gap that plagued this session.

**The performance trade-off:** running 5 skills unconditionally takes longer
than running 2-3 conditionally. The pre-packed evidence pattern (see
[[pre-packed-evidence-pattern-for-workflow-subagents]]) mitigates this by
eliminating transcript re-scans. Target: <5 min with optimization.

## Falsifier

This decision is wrong if:
- Running all 5 skills produces so much noise that the operator stops using
  close-check (over-firing)
- The unconditional skills write conflicting artifacts (two skills writing
  to the same wiki concept with different conclusions)
- The performance cost makes close-check impractical (>10 min even with
  pre-packed evidence)

The first is mitigated by the auto-act vs surface-only split. The second is
mitigated by serialized writes with safe-git. The third is the open risk —
addressed by TP-04 in the handoff.
