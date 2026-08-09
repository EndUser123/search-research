---
title: "Operator-driven structural improvement: RCA to skill-graph propagation pattern"
created: 2026-08-09
source: session-019fe403 (/why RCA → design-choice audit → 6-skill propagation)
tags: [meta-pattern, rca, skill-graph, operator-driven, structural-fix, knowledge-capture, transferable]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/design-choice-audit-challenge-every-decision-against-first-principles.md
    type: instance-of — the design-choice audit is the first instance of this pattern
  - target: wiki/concepts/self-review-before-shipping-advice.md
    type: related — both are meta-patterns for improving agent behavior structurally
  - target: wiki/concepts/making-llm-agents-honestly-execute-skills-solution-stack.md
    type: complements — the solution stack makes agents execute skills honestly; this pattern improves the skills themselves
summary: >
  A recurring meta-pattern: the operator catches a recurring agent gap →
  /why traces the root cause → the fix becomes a wiki concept → the concept
  is propagated across the skill graph. The design-choice audit is the first
  documented instance. This pattern will recur whenever the operator identifies
  a class of agent behavior that should be structural, not behavioral.
---

# Operator-driven structural improvement: RCA to skill-graph propagation

## The pattern

```
Operator catches recurring agent gap (6 times in one session)
  ↓
Agent runs /why RCA → identifies root cause (skill checks outputs, not input assumptions)
  ↓
Fix becomes wiki concept (design-choice audit: 4 questions per design decision)
  ↓
Concept propagated to all skills that produce design decisions (6 skills)
  ↓
Future sessions benefit structurally — the questions fire without operator intervention
```

## Why this matters

The workspace has accumulated behavioral rules in AGENTS.md that fire
inconsistently under session pressure. The design-choice audit was a case
where the operator had to supply the same type of question 6 times before
the agent recognized the pattern. The structural fix (propagating the audit
to 6 skills) means future sessions get those questions automatically.

This is the same principle as [[mechanical-enforcement-over-behavioral-reminder]]:
behavioral rules don't fire under pressure; structural rules do. The
meta-pattern extends that principle to skill improvement: a behavioral gap
(noting a missing question) becomes a structural fix (adding the question
to the skill's procedure).

## When to apply this pattern

- The operator catches the same type of agent gap ≥3 times in one session
- The gap is a class of behavior, not a one-off instance
- A /why RCA can identify the root cause (not just the symptom)
- The fix can be encoded as a reusable step in a skill procedure

## Reference instance

Session 019fe403 (2026-08-09): the operator asked 6 design-discipline
questions ("is RPN the right concept?", "should this always run?", "does
this fit cmd_*?", etc.) that the agent should have asked itself. The /why
RCA traced the root cause: skills check whether proposed solutions are
correct but don't challenge whether design choices are optimal. The fix
became the design-choice audit (4 questions per design decision),
propagated to /tp, /go, /design, /refactor, /risk, and /plan-writer.

## Falsifier

This pattern is wrong if it produces ceremony without value — if the
propagated steps are mechanically answered ("considered X, rejected because
Y") without genuinely evaluating alternatives. The test: does the propagated
step ever change a proposed answer? If it never changes anything, it's
theatrical.
