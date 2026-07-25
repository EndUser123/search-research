---
title: "Inline conditional expansion over dispatch classes for skill design"
created: 2026-07-25
source: session-2026-07-25-why-skill-multi-model
tags: [skill-design, conditional-logic, dispatch, inline-expansion, closure-pressure, llm-skill-design]
summary: >
  When a skill's depth must adapt to the failure content (some failures
  need a deep protocol, others a fast path), prefer INLINE CONDITIONAL
  EXPANSION (the lens fires when the failure content matches a trigger)
  over DISPATCH CLASSES (Step-0 classification into --bug/--agent/--pattern
  etc., each with its own protocol). Rationale: dispatch presupposes
  reliable classification at Step 0, but misclassification is itself a
  closure-pressure failure mode — the model picks a class too fast under
  time pressure, then runs the wrong protocol. Inline triggers fire on
  EVIDENCE (the failure mentions hooks), not on a PRE-CLASSIFICATION GUESS.
  Produced by applying multi-producer synthesis to /why v3; codex + mimo
  recommended inline, glm + agy recommended dispatch; synthesizer chose
  inline on evidence-fit and reversibility grounds.
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - session-019f9a89 (5-model /why synthesis, 2026-07-25)
  - C:/Users/brsth/.grok/skills/why/SKILL.md (v3 implementation)
relations:
  - target: wiki/concepts/multi-producer-cross-model-synthesis.md
    type: produced-by — this decision came out of that methodology
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: applies — closure pressure is the failure mode dispatch amplifies
  - target: wiki/concepts/synchronous-review-direct-write-pattern.md
    type: sibling — produced by the same methodology run
---

# Inline conditional expansion over dispatch classes

## Decision context

**The problem behind this principle:** `/why` v2 (commit 774eb43) dispatched at Step 0 into four failure classes (`--bug`, `--agent`, `--pattern`, `--system`), each with its own protocol depth. The 5-model synthesis (Grok + glm + codex + agy + mimo) split on whether to keep the dispatch:

- **glm-5-2 + agy** argued for dispatch: "inline conditionals are skipped under closure pressure — the exact failure mode being prevented."
- **codex + mimo** argued for inline: "4 new modes is interface bloat; the protocols share 80% of steps; at 400 lines, inline is cleaner."

The synthesizer had to pick. The criterion was **evidence-fit and reversibility**.

## The principle

**For skills whose depth adapts to failure content, inline conditional expansion beats dispatch classes.**

| Property | Dispatch classes | Inline conditional |
|----------|------------------|--------------------|
| When does the conditional fire? | Step 0 — pre-classification | At the conditional step — when content matches the trigger |
| What fires it? | A guess about which class the failure belongs to | Evidence in the failure description or dimensions investigated |
| Failure mode if wrong | Wrong protocol runs end-to-end | One step is skipped or fires unnecessarily; recoverable |
| Reversibility | Adding/removing classes changes the dispatch table, the flags, and the variant routing — high touch-count | Adding/removing a trigger changes one step's "when this fires" line — low touch-count |
| Closure-pressure risk | **High** — model picks a class too fast under time pressure | **Low** — trigger fires based on content the model is already reading |

## Why inline wins (the synthesizer's argument)

### 1. Misclassification is itself a closure-pressure failure mode

The whole point of conditional depth is to skip ceremony on simple cases and guarantee rigor on complex ones. Dispatch makes "is this simple or complex?" a Step-0 decision — exactly the kind of premature closure the skill is trying to prevent. A model under closure pressure picks `--bug` (the fast path) because it feels efficient, then skips the agent-control lens on a real agent-control failure.

Inline triggers don't ask "what class is this?" They ask "does this failure's content match the trigger for the deep protocol?" — which is a content check the model is doing anyway when it reads the failure description.

### 2. The protocols share most of their steps

In /why, the `--bug` and `--agent` protocols shared ~80% of steps (evidence inventory, first-divergence, Ishikawa, classification, falsifier, fixes). The 20% that differed (agent-control lens, MAST, feedback loops, contract-map) is the conditional part. Dispatch pays the cost of separate protocols to gate 20% of the steps. Inline pays the cost of one `if` per conditional step. Inline is cheaper when overlap is high.

**When dispatch would win:** if the protocols genuinely diverged (different step orders, different outputs, different success criteria), dispatch would be cleaner. Inline conditionals in a divergent protocol produce spaghetti.

### 3. Reversibility favors inline

Adding a new conditional step inline: one `## Step X (fires when …)` block. Adding a new dispatch class: new flag, new row in the dispatch table, new column in the variant routing, new auto-detection heuristic, new documentation. The touch-count for evolution favors inline by ~5:1.

### 4. Operator override is preserved either way

If the auto-trigger is wrong, the operator can pass a flag. Dispatch needs `--agent` to force the deep protocol. Inline needs `--deep` (or equivalent). Neither loses override capability — but inline doesn't need it as often because the trigger fires on content, not on a guess.

## When dispatch DOES win (the steelman)

- **Genuinely distinct protocols** — if `--pattern` runs a longitudinal wiki-first analysis and `--bug` runs a single-file code review, the protocols share <30% of steps. Dispatch is cleaner.
- **Operator wants explicit control** — if the operator reliably knows the failure class upfront (e.g., they typed `--agent`), dispatch respects their intent. Inline second-guesses by auto-firing.
- **Skill is large (>600 lines)** — at that size, inline conditionals scattered through the skill become hard to track. A dispatch table at the top is more navigable.

These were not the case for /why v3 (~400 lines, ~80% step overlap), so inline won. The principle is "inline by default, dispatch when protocols actually diverge."

## Worked example — /why v3

**v2 dispatch (removed):**
```
Step 0: detect --bug / --agent / --pattern / --system
  --bug: run steps 0.5, 1, 2, 3, 8, 9, 11, 12, 14 (fast path)
  --agent: run full protocol + agent-control lens + MAST + loops
  --pattern: wiki-first, longitudinal
  --system: contract-map first
```

**v3 inline (kept):**
```
Step 6 (Agent-control lens): fires when failure content involves
  hooks/gates/receipts/verification/subagents/multi-repo/completion
  claims — detected from the failure description and the dimensions
  investigated in Step 5, not from a pre-classification at Step 0.
```

Same for Step 7 (MAST), Step 10 (feedback loops), Step 13 (contract-map). Each fires when its content trigger matches. No Step-0 classification.

## Falsifier

This principle is wrong if, within 6 months:
- **Inline triggers consistently fail to fire on real agent-control failures** — the content trigger is too narrow; dispatch would have been more reliable.
- **Inline triggers consistently fire on ordinary bugs** (false-positive dispatch) — the trigger is too broad; dispatch would have been more precise.
- **A skill designed with inline conditionals becomes spaghetti** (conditional steps scattered, hard to follow) — the protocol overlap was lower than estimated; dispatch would have been cleaner.
- **Operators consistently pass `--deep` or equivalent to force the full protocol** — they don't trust the inline trigger; dispatch would have respected their intent more cleanly.

## What this means for our workspace

- **Default to inline conditional expansion** for skills whose depth adapts to content.
- **Reserve dispatch for genuinely distinct protocols** — if step overlap <50%, dispatch is cleaner.
- **Apply the trigger-narrowness check during A/B testing** — does the lens fire on real failures it should fire on?
- **Apply the trigger-broadness check** — does it fire on failures it shouldn't?
- **Document the trigger explicitly** in the step body, not in a separate dispatch table. The trigger and the protocol live together.

## Methodology roots

- Produced by applying [[multi-producer-cross-model-synthesis]] to /why v3
- Codex + mimo recommended inline; glm + agy recommended dispatch
- Synthesizer chose inline on evidence-fit and reversibility grounds (see Decision context)
- Operator concurred
- Related to [[compound-skill-improvement-patterns]] — both address skill design; this one is the conditional-logic decision specifically
- Related to [[reactive-pattern-matching-and-closure-pressure]] — closure pressure is the failure mode dispatch amplifies

Sibling: [[synchronous-review-direct-write-pattern]] — the other design decision from the same synthesis run.
