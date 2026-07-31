---
title: "Framing check pattern — 4 questions before any proposal ships"
created: 2026-07-31
source: session-019fb3a8 (/tp on /capture goal, then operator generalization)
tags: [prompting-pattern, framing-check, proposal-quality, design-gate, skill-design, anti-conflation, universal-pattern]
agent: grok
host: both
cognitive_load: 2
verification: workspace_verified
summary: >
  Four questions that catch design flaws before a proposal ships: (1) Output
  check — are output types conflated? (2) Routing check — does each output go
  to the right destination? (3) Overlap check — does this overlap with existing
  work? (4) Goal check — does the goal match the actual need? Generalized from
  skill design to ALL proposals (designs, plans, recommendations, artifacts).
  Embedded in H1 Think Pack as lens 6. Referenced by AGENTS.md as universal rule.
relations:
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: extends
  - target: wiki/concepts/proactive-improvement-opportunity-scanner
    type: derived-from
---

# Framing check pattern

## The 4 questions

Before committing any proposal — a skill design, a plan, a recommendation, a refactor approach, a research synthesis, any artifact that proposes a course of action — run these 4 questions:

1. **Output check**: does the proposal produce one type of output or multiple types? If multiple, are they conflated?
   - Example failure: `/capture` originally routed both knowledge ("we learned X") and improvements ("we should build X") to wiki concepts. Improvements buried in wiki concepts never get acted on.
   
2. **Routing check**: does every output type go to the right destination? Are any going to the wrong place?
   - Example failure: routing actionable improvements to a knowledge base instead of a task backlog.

3. **Overlap check**: does this overlap with existing work? If so, is the boundary clear?
   - Example failure: building `/capture` without checking whether `/aar`, `/friction`, `/harvest`, or `/debrief` already cover the same scope.

4. **Goal check**: does the proposal's goal match the operator's actual need, or is it the agent's interpretation of the need?
   - Example failure: interpreting "what should we capture" as "scan for findings" when the operator meant "what would make the system better" (broader, includes friction, UX, experience improvements).

## Why this works

The pattern catches the **conflation failure mode** — when a design looks correct from inside its own framing but has a structural flaw visible only from a different angle. The operator's challenge ("do we have the right goal?") forced a re-examination that surfaced the conflation. The framing check mechanizes that challenge so it doesn't depend on the operator catching it manually.

## Where it fires

| Location | When | Mechanism |
|---|---|---|
| H1 Think Pack (lens 6) | Before every /go implementation | Structural — fires mechanically |
| /create-skill | Before writing SKILL.md | Structural — embedded in skill creation workflow |
| /design | Before writing design doc | Referenced by design skill |
| /plan-writer | Before writing plan | Referenced by plan-writer skill |
| /refactor Step 4 | Before writing seams.json | Referenced by refactor skill |
| AGENTS.md | Universal — all proposals | Behavioral — "before proposing any solution, run framing check" |

## Generalization

The questions were originally skill-specific ("does the skill produce..."). The generalization to "does the proposal produce..." makes them universal. Every proposal — from a 1-line recommendation to a 200-line design doc — benefits from the same 4 questions.

## Falsifier

This pattern is wrong if:
- The questions consistently find nothing (proposals don't have conflation problems)
- The questions are too slow for routine proposals (over-firing on trivial changes)
- The questions find the same things the existing review/tp process already catches (redundant)
- Operators skip the check because it's ceremony (questions don't surface real problems)

## Source

Session 019fb3a8 (2026-07-31). The operator challenged `/capture`'s design ("do we have the right goal?"), which surfaced a conflation between knowledge routing and improvement routing. The operator then generalized: "this applies to all proposals, from big to small."
