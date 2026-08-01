---
title: "Knowledge capture: can't afford to leave future-useful info uncaptured"
created: 2026-07-31
source: session-019fb3a8 (operator correction)
tags: [knowledge-capture, wiki, operator-correction, capture-discipline]
agent: grok
host: both
cognitive_load: 1
verification: operator_corrected
summary: >
  The agent said "the session produced 3 wiki concepts, which is enough.
  More would be thin." The operator corrected: "completely false. If there
  are more future useful concepts, we can't afford not to capture them.
  We should be scared if we leave future useful info to disappear." The
  cost of losing durable knowledge always exceeds the cost of capturing it.
relations:
  - target: wiki/concepts/proactive-improvement-opportunity-scanner
    type: derived-from
  - target: wiki/concepts/framing-check-pattern
    type: derived-from
---

# Knowledge capture: can't afford to leave future-useful info uncaptured

## What was learned

The agent applied a false economy: "3 wiki concepts is enough, more would be thin." The operator corrected: if there are future-useful concepts, they must be captured. The loss cost always exceeds the capture cost.

This is the same anti-pattern as "ship gates need to be fast" — the agent imposed a constraint (minimize wiki entries) that the operator doesn't have. The workspace accumulates knowledge monotonically; thin entries are filtered by the wiki validator, not by the agent deciding "enough."

## What this means

- Never decide "enough wiki concepts" — the validator enforces quality, not the agent
- If a finding is future-useful, capture it — even if the session already has 10 concepts
- The cost of a false negative (lost knowledge) is always higher than a false positive (thin entry that gets pruned later)
- This applies to /capture's knowledge stream: persist all uncaptured knowledge, don't apply a count limit

## Falsifier

This is wrong if the wiki becomes so cluttered with thin entries that future sessions can't find useful knowledge. The /skill-prune skill exists to prevent this — if it can't keep up, revisit.
