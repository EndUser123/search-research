---
title: "Ship discipline: complete and public-ready, not fast"
created: 2026-07-31
source: session-019fb3a8 (operator correction)
tags: [ship, quality-gate, operator-correction, discipline, public-ready]
agent: grok
host: both
cognitive_load: 1
verification: operator_corrected
summary: >
  Ship gates must prioritize completeness and public-readiness over speed.
  The agent incorrectly framed ship gates as needing to be "fast" — the
  operator corrected: "this is not true, ship needs to be complete and the
  target needs to be shippable to the public." Every gate that prevents a
  bug from reaching users is worth the time. Speed is never a constraint on
  shipping quality.
relations:
  - target: wiki/concepts/framing-check-pattern
    type: derived-from
---

# Ship discipline: complete and public-ready, not fast

## What was learned

The agent said "ship gates need to be fast" as a reason to defer mutation testing. The operator corrected: ship needs to be **complete** and **public-ready**. Speed is never a constraint on quality.

This is the same class as the "minimal-fix-and-root-cause" anti-pattern — the agent imposed a constraint (speed/minimalism) that the operator doesn't have. The framing check's goal-check question ("does the goal match the operator's actual need?") catches this.

## What this means

- Ship verify gates should be thorough, not optimized for speed
- If a gate takes 5 minutes but catches a bug that would reach production, it's worth it
- Mutation testing is correctly deferred to `/check --deep` not because ship should be fast, but because mutation testing is too slow for ANY interactive gate (minutes-hours per file)
- The distinction is: "too slow for interactive use" (valid reason to defer) vs "we should optimize for speed" (wrong framing)

## Falsifier

This is wrong if the operator ever says "ship is taking too long, skip some gates." That would mean speed IS a constraint.
