---
title: "Review panels attack implementation, miss framing errors"
created: 2026-08-03
source: session-019fb177 (work-surface design)
tags: [review, framing, behavioral-pattern, adversarial-review, design-process]
summary: >
  When a design proposal is reviewed (red-team, /tp, adversarial specialists),
  the reviewers consistently optimize implementation details — scope reduction,
  architecture critique, technical risks — while missing fundamental framing
  errors. The operator catches framing in one question. This is a recurring
  failure pattern across multiple sessions.
agent: grok
host: grok
cognitive_load: 2
verification: observed
relations:
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: related
  - target: wiki/concepts/trust-over-believability.md
    type: related
---

# Review panels attack implementation, miss framing errors

## Decision context

During the work-surface design session (2026-08-02/03), a design proposal
went through **three review rounds**:

1. **Red-team** (3 specialists: architecture, scope, workflow) — produced 24 findings about scope, delegation mechanics, missing migrations
2. **/tp review** — integrated findings, reduced scope from 8→1 to 3→1, fixed delegation direction
3. **Operator** — asked one question: "is a sprint retro how people figure out what to do?"

The operator's question exposed that the entire design was built on a framing
error: `/tp session` (a retrospective) was positioned as the unified entry
point for figuring out what to do (a planning function). All three review
rounds optimized the *implementation* of this flawed framing without
questioning the framing itself.

## The pattern

Review panels — whether adversarial specialists, /tp critique, or structured
rubrics — consistently:

1. Attack **scope** ("8→1 is actually 3→1")
2. Attack **mechanics** ("delegation will fail for the same reason")
3. Attack **missing coverage** ("/harvest is infrastructure, not a scan step")
4. Attack **over-engineering** ("impact scoring needs a rubric")

But they do NOT ask: **"Is the thing being proposed the right thing?"** The
review assumes the framing is correct and optimizes within it. The operator,
free from the anchor of the proposed solution, asks the framing question
directly.

## Why this happens

Reviewers share the proposal's framing anchor. When given a design for
`/work`, they evaluate whether `/work` is well-designed — not whether `/work`
should exist. The review prompt says "review this proposal," not "question
whether the proposal addresses the right problem."

This is structurally the same as [[replacement-before-investigation-pattern]]:
the agent commits to a solution shape before verifying the problem shape.
Review panels inherit that commitment. It's also related to
[[trust-over-believability]] — the proposal's plausibility masks its framing
error, and reviewers trust the framing instead of verifying it.

## What this means for our workspace

1. **Reviews need a framing-check step.** Before architecture critique, the
   first review question should be: "What problem is this solving, and is
   that the actual problem?" This is a domain-mapping exercise, not an
   implementation critique.

2. **The operator's framing questions are the highest-signal feedback.** When
   the operator asks "is X how people do Y?", that's a framing challenge, not
   a factual question. Treat it as evidence the framing is wrong.

3. **/tp and red-team should include framing critique explicitly.** Add a
   "framing lens" that asks: "Does the proposed solution match the problem
   domain? Is the entry point the right ceremony type?"

4. **Design proposals should state the problem domain first.** "This solves
   the sprint-planning domain" is checkable. "This is a unified work surface"
   is not — it hides the domain assumption. See
   [[framing-check-pattern]] for the 4-question framing check that should
   precede any proposal.

## Instances observed

- **Work-surface design (2026-08-02)**: 3 review rounds optimized `/work`
  architecture. Operator caught: retro ≠ planning.
- **Session-review skill division (2026-08-01)**: `/tp session` positioned as
  unified entry point. Operator caught: `/todo` should be the front door.
- **Premature-recommendation pattern (2026-08-01)**: Agent recommended
  replacing agy before investigating workarounds. Same root cause: committed
  to solution shape before verifying problem shape.

## Falsifier

This pattern is wrong if review panels consistently catch framing errors
without explicit framing-check steps. If adding a "framing lens" to /tp or
red-team produces no additional findings, the pattern doesn't hold.

## Auto-related

- [[skill-catalog]]
- [[skill-graph]]
- [[synchronous-review-direct-write-pattern]]
- [[code-review-speed-comes-from-richer-context-not-more-agents]]
- [[coupling-inventory-as-mandatory-design-section]]

