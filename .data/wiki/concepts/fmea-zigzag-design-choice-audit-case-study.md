---
title: "FMEA zigzag: a design-choice-audit case study"
created: 2026-08-09
source: session-019fe403 (FMEA phase proposal → dismissal → reversal → overcorrection → correct answer)
tags: [case-study, design-choice-audit, fmea, zigzag-pattern, premature-dismissal, overcorrection, behavioral-pattern]
host: grok
agent: grok
verification: observed
relations:
  - target: wiki/concepts/design-choice-audit-challenge-every-decision-against-first-principles.md
    type: case-study-of — the FMEA zigzag is the reference incident for why the audit exists
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: related — the initial dismissal was premature closure
summary: >
  A documented case of the design-choice audit's reference incident: proposing
  FMEA as a phase → dismissing it → reversing under operator pressure →
  over-engineering (delta-FMEA with baseline) → simplifying to the correct
  answer (session-scoped, category-gated). The zigzag pattern (dismissal →
  reversal → overcorrection → correct) is what the audit catches structurally.
---

# FMEA zigzag: a design-choice-audit case study

## The sequence

| Turn | Position | Driver |
|---|---|---|
| 1. Initial /tp (35-item list) | FMEA listed as one-time action, not a phase | Didn't consider it as a pipeline step |
| 2. Operator: "why not make FMEA a step?" | **Dismissed** — argued FMEA is "pipeline design review, not change verification" | Defensive reasoning. Reframed the question into a different one and argued against the reframe. |
| 3. Operator pushback | **Reversed** — "you're right, ship-py should check the pipeline works" | Correct correction, but overshot into enthusiasm |
| 4. Second /tp explore | Proposed delta-FMEA with baseline cache (M effort) | Carried enthusiasm forward without simplifying |
| 5. /todo | "Build delta-FMEA now" as NOW #1 | Same enthusiasm |
| 6. Operator: "should this be adaptive? is RPN the right concept? should it always run?" | **Simplified** — session-scoped, category-gated, no baseline (S effort) | The design-choice audit questions forced re-examination |

## The zigzag pattern

```
Dismissal → Reversal → Overcorrection → Correct answer
     ↑                                      |
     └──────── operator catches ────────────┘
```

The pattern: the agent's first instinct is to dismiss (closure pressure).
When forced to reconsider, it overcorrects (compensation for the dismissal).
Only when the operator asks first-principles questions does it reach the
correct answer.

## What the design-choice audit would have caught

If the audit had existed at turn 1, it would have asked:

- **CONCEPT:** is a one-time FMEA action the right mechanism, or should it
  be a pipeline phase? (The answer: a phase, because ship-py ships pipelines.)
- **SCOPE:** should FMEA always run, or be conditional? (The answer: always
  on .py files, same as every other phase.)
- **FIT:** does it fit the cmd_* pattern? (Yes — scan_file is already stable.)

These questions would have produced the correct answer at turn 1 instead of
turn 6.

## Why this matters as a case study

The FMEA zigzag is the reference incident for the design-choice audit. It
demonstrates:

1. **The dismissal is wrong** — the operator's suggestion was correct
2. **The reversal overcorrects** — enthusiasm without simplification produces
   over-engineered solutions (delta-FMEA with baseline)
3. **The correct answer is simpler** — session-scoped + category-gated + no
   baseline is S effort, not M
4. **The audit catches it structurally** — asking "is this the right mechanism?"
   before accepting the first framing prevents the entire zigzag

## Falsifier

This case study is wrong if the design-choice audit doesn't actually prevent
future zigzags — if the agent mechanically answers the 4 questions without
genuinely re-examining its initial proposal. The test: future sessions
should reach the correct answer in fewer turns than this session's 6.
