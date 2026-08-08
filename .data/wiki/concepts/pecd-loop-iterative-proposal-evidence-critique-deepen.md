---
title: "PECD loop: iterative proposal-evidence-critique-deepen refinement"
created: 2026-08-08
source: session-019fdf3d
tags: [meta-pattern, iterative-refinement, workflow, tp, www, proposal, evidence, critique, convergence, decision-quality]
summary: >
  The operator identified a recurring meta-pattern: proposals are generated
  (/tp), grounded against external evidence (/www), critiqued (/tp review),
  and deepened (/www focused). Each pass through the loop produces strictly
  better proposals. The pattern is codified as the PECD loop — Proposal,
  Evidence, Critique, Deepen — with a convergence check that exits when no
  items remain labeled "refine."
agent: grok
host: grok
cognitive_load: 3
verification: single-source-verified
relations:
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/evidence-driven-experiment-loop
    type: related
  - target: wiki/concepts/research-quality-principle-efficiency-not-censorship
    type: related
  - target: wiki/concepts/adaptive-research-depth-preventing-incomplete-www-coverage
    type: related
---

# PECD loop: iterative proposal-evidence-critique-deepen refinement

## The pattern

When evaluating proposals for system improvements, a single-pass approach
(generate → evaluate) produces plausible but unverified ideas. The PECD loop
adds evidence grounding and adversarial critique between generation and
decision, producing dramatically better output:

```
Propose → Ground → Critique → [convergence check] → Deepen → Critique → Decide
```

Each pass through the loop produces strictly better proposals because:

1. **Grounding catches ideas that don't survive external evidence.** A
   proposal that sounds right but conflicts with industry practice gets
   labeled REFUTED and removed.
2. **Critique catches over-engineering and wrong assumptions.** An
   enhancement that adds complexity without proportional value gets labeled
   defer with reasoning.
3. **Deepening resolves specific decision questions on uncertain items.**
   "Should we flip the gate ordering?" becomes a targeted research question
   with a concrete answer, not a gut feeling.
4. **The convergence check prevents infinite loops.** When critique produces
   zero "refine" items, the loop exits.

## The five phases

| Phase | Cognitive mode | Skill | What it produces | Output labels |
|-------|---------------|-------|-----------------|---------------|
| **P — Propose** | Divergent | /tp or /insight | N candidate improvements | (unlabeled) |
| **E — Evidence** | Convergent | /www | Each candidate validated/refuted | CONFIRMED, EXTENDED, NOVEL, REFUTED |
| **C — Critique** | Adversarial | /tp review | Each candidate triaged | ship, refine, defer |
| **D — Deepen** | Targeted | /www (focused) | Specific decision questions answered | UPGRADE, CONFIRM CURRENT, CONFIRM DEFER |
| **Decide** | Convergent | (operator) | Final ship/refine/defer list | (terminal) |

## Worked example (session 019fdf3d)

```
/tp "what should we do to improve?"
  → 4 improvements proposed

/tp "what's the optimal forward path?"
  → 3 architectures with priority ordering

/www "Five improvements grounded in this session's evidence"
  → 1 NOVEL, 3 EXTENDED, 1 CONFIRMED+EXTENDED, 10 enhancements

/tp review "the 10 actionable enhancements"
  → 3 ship, 3 refine, 3 defer

/www "do additional research on the review items"
  → 2 upgraded to ship, 1 partially upgraded, 2 confirmed, 1 deferred with evidence

Final: 6 ship, 1 confirm current, 2 deferred
```

The first pass produced 10 plausible enhancements. After one PECD iteration,
6 were validated for shipping with external evidence, 1 was confirmed as
already-optimal (avoiding unnecessary work), and 2 were deferred with
concrete evidence for why. **The loop converted uncertainty into evidence.**

## What can be automated

The mechanical structure is a workflow:

```
propose (subagent)
  → ground (subagent, /www)
  → critique (subagent, /tp review)
  → [convergence: any "refine" items?]
    → yes: deepen (subagent, /www focused) → back to critique
    → no: emit final decisions
```

Automatable:
- Phase chaining (output of one feeds input of next)
- Convergence detection (zero "refine" items → exit)
- Targeted deepening (each "refine" item gets a focused /www query)
- Output synthesis (final list from accumulated evidence)

Not automatable:
- Initial proposal quality (depends on session context)
- "When to stop" operator judgment (remaining "refine" items may not be worth another iteration)
- Priority ordering (requires workspace understanding)
- Operator redirects mid-loop ("can we codify that?", "do additional research")

## Semi-automated design

The right design is semi-automated: the workflow pauses at the critique
phase for operator review before deciding whether to deepen. This preserves
the operator's ability to redirect while automating the expensive mechanical
work (research dispatch, evidence aggregation, convergence checking).

```
/workflow pecd "improve our SDLC skills"
  → Phase 1: propose (automated)
  → Phase 2: ground (automated)
  → Phase 3: critique (automated)
  → PAUSE: operator reviews ship/refine/defer list
    → operator says "deepen R1, R2, R3" or "ship the 3, defer the rest"
  → Phase 4: deepen (if operator requests)
  → Phase 5: re-critique deepened items (automated)
  → Phase 6: emit final decisions
```

## Falsifier

This concept is wrong if:
- Single-pass proposal generation produces the same quality as PECD (the
  loop adds no value). Observed: this session's first pass produced 10
  enhancements; after PECD, 4 were upgraded/refined/deferred — material
  quality improvement.
- The operator stops using the workflow because the pause-breaks are too
  slow. Mitigation: the workflow runs all automated phases without pausing;
  the pause is only at the critique checkpoint.
- The loop never converges (items keep getting labeled "refine" forever).
  Mitigation: max 2 iterations. After iteration 2, all remaining "refine"
  items are auto-deferred with rationale.

## Relationship to existing patterns

- [[compound-skill-improvement-patterns]] — documents skill-pair
  compositions (/tp + /review, /www + /wiki). PECD is the meta-composition
  that chains these pairs into a refinement loop.
- [[evidence-driven-experiment-loop]] — handles evidence-gated decisions
  for experiments/benchmarks. PECD handles evidence-gated decisions for
  proposals/improvements. Same structure, different domain.
- [[adaptive-research-depth-preventing-incomplete-www-coverage]] —
  documents the "search-reason-search" reflection loop inside /www.
  PECD applies the same reflection principle at the inter-skill level:
  critique feeds back into research.
- [[research-quality-principle-efficiency-not-censorship]] — PECD respects
  this principle: the loop optimizes evidence quality (more passes = better
  decisions), not depth reduction (fewer passes = less work).
