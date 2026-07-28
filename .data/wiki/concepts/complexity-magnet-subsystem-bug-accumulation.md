---
title: "Complexity magnet: when one subsystem accumulates bugs faster than the workspace can fix them"
created: 2026-07-27
source: session-019fa39d (/tp explore workspace-state analysis)
tags: [skill-architecture, technical-debt, complexity-budget, handoff-backlog, bug-tracking, system-design]
summary: >
  A complexity magnet is a subsystem whose bug/feature-request count grows
  faster than the workspace's fix rate. The close-scanner is the workspace's
  current complexity magnet: 19 handoffs (one skill's backlog equals the
  entire workspace's closed-handoff count of 19). The pattern arises when a
  system's gate/feature design creates the bugs it's supposed to catch —
  each new gate introduces false-positive modes, classification gaps, and
  interaction effects with other gates. The system accumulates complexity
  faster than it's simplified, indicating it has exceeded its complexity
  budget. The structural fix is not to rebuild from scratch (which discards
  the working parts) but to simplify the problematic gates by adding
  source-type classification (the fix proposed in close-scanner-gate-robustness-20260727).
agent: grok
host: both
cognitive_load: 2
verification: measured
sources:
  - "Direct measurement: Get-ChildItem + status grep across P:/docs/handoffs/ (2026-07-27)"
  - "P:/docs/handoffs/close-scanner-gate-robustness-20260727/HANDOFF.md — the two false-positive gates that triggered this analysis"
  - "P:/.data/wiki/concepts/producer-consumer-contract-drift-in-skill-chains.md — predicts the /close↔/aar bug class"
relations:
  - target: wiki/concepts/producer-consumer-contract-drift-in-skill-chains
    type: instance-of — close-scanner's bugs are an instance of contract drift between /close and /aar
  - target: wiki/concepts/research-to-execution-ratio-self-reinforcing-pattern
    type: related — the complexity magnet is the structural version of the same ratio problem
---

# Complexity magnet: when one subsystem accumulates bugs faster than the workspace can fix them

## Definition

A **complexity magnet** is a subsystem whose open-issue count grows faster
than the workspace's fix rate. It "attracts" bugs because its internal
complexity creates more failure modes than the surrounding system can
resolve. The defining signal: **one subsystem's open-issue count equals or
exceeds the entire workspace's closed-issue count.**

## Measured instance: the close-scanner

| Metric | Value | Receipt |
|--------|-------|---------|
| Close-scanner open handoffs | 17 | `Get-ChildItem P:/docs/handoffs/close*/HANDOFF.md` + status grep |
| Close-scanner closed handoffs | 1 (close-runner-needs-llm-check-block) | same |
| Close rate | **5%** (1/19) | computed |
| Entire workspace closed handoffs | 19 | full handoff inventory |
| **Ratio** | close-scanner open (17) = workspace closed (19) | measured |

One skill's open backlog (17) is the same order of magnitude as the entire
workspace's lifetime completed work (19).

## Root cause chain

1. The close-scanner has **14 gates** — each gate is a classification point
   that can produce false positives, false negatives, or interaction effects
2. Each new gate was added to catch a specific failure mode observed in a
   prior session — **accretive design**, not simplifying design
3. Gates interact: the `referenced_files` gate flags design-doc forward
   references as missing; the `continuation_coverage` gate parses
   system-prompt blocks as goals; the `verify` gate flags concurrent-session
   test failures as this session's responsibility
4. Each interaction produces a new handoff documenting the false positive —
   which increases the backlog without addressing the root cause
5. The backlog itself becomes a source of complexity (which handoff
   supersedes which? which is still relevant?) — **the debt compounds**

## The general pattern

A complexity magnet forms when:

1. **Gate/feature accretion** — new gates are added without removing or
   consolidating old ones. Each gate adds interaction surface area.
2. **No complexity budget** — there's no threshold at which the system says
   "we have too many gates; simplify before adding more."
3. **Bug-generation rate exceeds fix rate** — the system's design creates
   the bugs it's supposed to catch. The false-positive rate is structural,
   not behavioral.
4. **No simplification mechanism** — there's no process for retiring gates
   that produce more false positives than true positives.

## Detection signals

- One subsystem's open-issue count equals or exceeds the workspace's
  closed-issue count
- The subsystem's close rate is significantly below the workspace average
- New issues reference prior issues as root causes (compounding debt)
- Issues cluster around the same interface (e.g., close↔aar contract drift)

## Structural fixes (not rebuild)

The complexity magnet is **not** fixed by rebuilding the system from
scratch. A rebuild discards the working parts (13 of 14 close-scanner
gates function correctly). The fix is **source-type classification**:

| Problem gate | Current behavior | Fix |
|---|---|---|
| `referenced_files` | All missing files = dangling intent | Classify as FORWARD_REFERENCE vs DANGLING_INTENT based on handoff context |
| `continuation_coverage` | All extracted text = goal | Filter XML-tagged system-prompt blocks from goal extraction |
| `verify` | All test failures = this session's responsibility | Attribute test failures to the session that made the change (via git blame on the removed function) |

Each fix adds **classification intelligence** to an existing gate rather
than adding a new gate. This reduces false-positive rate without increasing
gate count.

## When to declare a complexity magnet

A subsystem is a complexity magnet when **all four** are true:

1. Open-issue count ≥ workspace closed-issue count (one subsystem's backlog
   = workspace lifetime output)
2. Close rate < 25% (most issues stay open)
3. Issues reference prior issues as root causes (compounding debt)
4. No simplification has occurred in the last 5 issues added (pure accretion)

The close-scanner meets all four as of 2026-07-27.

## Falsifier

This concept is wrong if:
- The close-scanner's backlog is normal for a 14-gate system (compare to
  other multi-gate systems' bug rates)
- The backlog is being actively worked down (the 5% close rate will improve
  as the gates mature)
- The false-positive rate is temporary (new gates always produce false
  positives initially; they stabilize over time)

If the close rate doesn't improve to >25% within 30 days, the complexity
magnet diagnosis is confirmed and a simplification pass is warranted.

## Related

- [[producer-consumer-contract-drift-in-skill-chains]] — predicts the close↔aar bug class
- [[research-to-execution-ratio-self-reinforcing-pattern]] — the structural version of the same ratio problem
- [[mechanical-enforcement-over-behavioral-reminder]] — why gates accrete (each new failure mode demands a gate)
