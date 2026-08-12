---
title: "Feedback-loop test category for enforcement hooks"
created: 2026-08-12
tags: [testing, hooks, enforcement, feedback-loop, test-pattern]
host: both
agent: grok
verification: observed
---

# Feedback-loop test category for enforcement hooks

## Finding

Every enforcement hook that feeds back to the model needs test cases for the model's response to being caught. This is a distinct test category from "fresh assertion" (does the hook catch the violation?) and "standard suppression" (does the hook pass legitimate claims?).

## Root cause

The confabulation_gate had 7 tests covering forward direction (catching confabulation) and standard suppression (uncertainty labels, receipts, code context). Zero tests covered the feedback-loop direction — what happens when the gate fires, the model corrected itself, and the correction text contained the flagged phrase.

The feedback loop is unique to hooks whose feedback is consumed by the model (not the operator). The confabulation gate is the only hook with this property — but the pattern applies to any Stop hook that blocks with stderr feedback that the model reads and responds to.

## The test category

Three cases every enforcement hook with model-consumed feedback needs:

1. **Self-correction quoting the flagged phrase** — model corrects its own violation by quoting and analyzing it. The hook should NOT re-fire.
2. **Data/log output containing the flagged phrase** — model reads log data containing the phrase (e.g., JSON from hook_failures.jsonl). The hook should NOT fire.
3. **Uncertainty-labeled list containing the phrase** — model lists possible explanations including the phrase. The hook should NOT fire.

## Evidence

Session 019ff2ae (2026-08-12): confabulation_gate fired 3 times on message text that was analytical/corrective, not assertive. Two precision bugs fixed (analytical markers too narrow, JSON-escaped quotes not recognized). 9/9 tests pass post-fix.

## Falsifier

This finding is wrong if: the feedback-loop test cases catch zero bugs across all enforcement hooks. If every hook already handles feedback correctly without explicit tests, the category is unnecessary.

## Relations

- [[silently-dead-hooks-pgm-payload-bug-fleet-monitoring-gap]]
- [[mechanical-enforcement-of-llm-skill-steps-2026]]
