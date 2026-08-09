---
title: "Design-choice audit: challenge every design decision against first principles"
created: 2026-08-09
source: session-019fe403 (/why RCA on why /tp didn't ask the operator's questions)
tags: [design-discipline, first-principles, skill-graph-pattern, design-choice, alternatives, host-invariants, structural-fix]
host: grok
agent: grok
verification: directly-verified
relations:
  - target: wiki/concepts/optimal-long-term-solution-not-minimal-fix.md
    type: extends — applies the optimal-long-term principle at design-choice granularity
  - target: wiki/concepts/problem-first-systems-decomposition.md
    type: complements — decomposition identifies the problem; this audits the solution choices
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — accepting the first plausible design choice is a closure-pressure failure
  - target: wiki/concepts/invariants-beat-environment-comfort.md
    type: applies — "does this fit host invariants" is one of the 4 questions
summary: >
  A reusable design-discipline step for any skill that produces design decisions.
  After generating a proposal, for each design decision (gate mechanism, execution
  model, phase placement, integration approach), state: the choice made, the
  alternatives considered, why this one is optimal, and which host invariant it
  respects. Prevents the pattern where the agent proposes the first plausible
  mechanism without questioning whether it's the right concept, whether it should
  always run, or whether it fits the architecture.
---

# Design-choice audit: challenge every design decision against first principles

## The problem this solves

The operator repeatedly had to supply design-discipline questions that the
skill should have asked structurally:

- "Is RPN the right concept to gate on?" → I proposed a numeric threshold without questioning whether a number was the right gate
- "Should this be adaptive?" → I proposed a static config flag without considering adaptive logic
- "Should it run always?" → I proposed conditional execution without questioning the condition
- "Why wire review-relay?" → I carried it forward from a prior session without re-examining fit
- "All solutions must be multi-terminal isolated" → I was building without checking the core invariant
- "You should follow the cmd_* pattern" → I proposed external composition without checking the orchestration pattern

Each is a question the agent should have asked BEFORE proposing. The pattern:
the agent produces a design proposal that is *correct* (will work) but whose
foundational choices are *unexamined* (first plausible option accepted without
challenge).

## Root cause

This is a **closure-pressure** failure at the design-choice level. The
`[[optimal-long-term-solution-not-minimal-fix]]` rule fires at the solution
level ("is approach A or B better?") but not at the design-choice level ("is
a numeric threshold the right gate mechanism, or should it be category-based?
should it always run, or be conditional?"). The agent accepts the first
plausible design choice because closure pressure rewards having *an* answer,
not the *optimal* answer at each decision point.

## The audit (4 questions per design decision)

For each design decision in a proposal (gate mechanism, execution model,
phase placement, integration approach, threshold type, run condition):

### 1. CONCEPT — is this the right mechanism?

Not "will it work" but "is it the optimal concept?" Challenge the mechanism
itself. If you proposed a numeric threshold, ask: is a number the right way
to gate, or should it be category-based? If you proposed a config flag, ask:
should it be adaptive instead?

### 2. SCOPE — should this always apply, or be conditional?

Challenge the default execution model. If you proposed conditional execution
("only runs when X"), ask: should it always run? What's the cost of the
condition vs. unconditional execution? If you proposed always-run, ask: is
there a case where it shouldn't?

### 3. FIT — does this respect the host invariants?

Check against known constraints: multi-terminal isolation, stale-data
immunity, cmd_* pattern (Python orchestrates where practical), session
scoping, atomic writes. This is [[invariants-beat-environment-comfort]]
applied at the design-choice level.

### 4. ALTERNATIVES — what was rejected and why?

State ≥1 alternative for each load-bearing design choice. The existing
"rejected alternatives visible" rule, but at design-choice granularity, not
solution granularity.

## Where it applies (skill graph)

| Skill | Where in the skill | What it catches |
|---|---|---|
| `/tp` exploration | After domain 5 (solution-space), before recommendations | Unexamined design choices in proposed solutions |
| `/go` | Step 4 (alternatives block) — extend from solution-level to design-choice-level | Implementation plans with unchallenged design decisions |
| `/design` | Between draft and reviewer | Design docs with foundational choices not audited |
| `/refactor` | In the dry-run output, before ranking | Seam placements accepted without challenge |
| `/plan` / `/plan-writer` | In step-definition format | Plans with load-bearing design choices not stated |
| `/risk` | Add "design-choice" scan category | Proposals where the mechanism itself is the risk |

## How it differs from existing rules

| Existing rule | What it covers | What this adds |
|---|---|---|
| [[optimal-long-term-solution-not-minimal-fix]] | Solution-level: "is approach A or B better?" | Design-choice-level: "is a threshold the right gate? should it always run?" |
| "Rejected alternatives visible" (AGENTS.md) | Solution-level alternatives | Per-decision alternatives at design-choice granularity |
| "Alternatives before architectural implementation" (AGENTS.md) | Fires before implementation waves | Fires during design generation, before the proposal is complete |
| [[invariants-beat-environment-comfort]] | Host invariants as a principle | Applied as a checklist question per design choice |

## Falsifier

This pattern is wrong if it adds ceremony without changing outcomes — if the
agent states alternatives mechanically ("considered X, rejected because Y")
without genuinely evaluating them. The test: does the audit ever change the
proposed design choice? If it never changes anything, it's theater.

## Reference session

Session 019fe403 (2026-08-09): the operator asked 6 design-discipline
questions across 5 turns that the agent should have asked itself. Each
question materially changed the design (RPN→category, conditional→always-run,
review-relay→cmd_review improvement, etc.). The audit would have caught all 6
structurally.
