---
title: "Mechanical-as-input not mechanical-as-frame: preserving model adaptivity while grounding in scanner output"
created: 2026-08-05
source: session-019fcd47 (operator insight during /tp do? vs /todo comparison)
tags: [skill-design, mechanical-grounding, model-adaptivity, scanner-as-input, code-orchestrates-model-judges, anti-anchoring, transferable-pattern]
agent: grok
host: both
cognitive_load: 2
verification: session-verified
summary: >
  When a skill with model-driven evaluation (like /tp do?) adopts mechanical
  scanner output (like /todo's scan_functions.py), the scanner must be ONE
  INPUT among several — not the frame that anchors the evaluation. If the
  scanner output becomes the universe of findings, the model loses its
  adaptive ability to see patterns, friction, and cross-domain connections
  that no scanner can detect. The pattern: scanner as Step 0e (one more
  evidence stream), not scanner as the backbone. This is distinct from
  [[code-orchestrates-model-judges-skill-scale]], which covers code as gate
  enforcer. This concept covers code as evidence feeder while the model
  retains framing control.
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: complements
  - target: wiki/concepts/analyst-exhibits-pattern-being-analyzed
    type: related
---

# Mechanical-as-input not mechanical-as-frame

## The pattern

When combining a mechanical scanner (deterministic, pattern-matching) with a
model-driven evaluation (adaptive, pattern-connecting), the scanner output
should enter as **one input stream among several**, not as the frame.

**Scanner as input (correct):** the model reads scanner output alongside
transcript evidence, session arc, git history, and conversation context. All
inputs are candidates for findings. The model decides what matters based on
the full picture.

**Scanner as frame (incorrect):** the model reads scanner output, treats the
filtered items as the universe of possible findings, then evaluates only those
items. Findings the scanner can't see (friction patterns, unactioned
recommendations, cross-domain connections) are missed because they're outside
the frame.

## How to tell which one you have

| Signal | Scanner-as-input | Scanner-as-frame |
|--------|-----------------|-----------------|
| Model starts with scanner, then adds its own findings | ✅ | |
| Model starts with scanner, then only evaluates scanner items | | ❌ |
| Scanner output gets the same validity check as other inputs | ✅ | |
| Scanner output is treated as ground truth (not checked for false positives) | | ❌ |
| Findings from conversation/transcript appear alongside scanner findings | ✅ | |
| All findings trace back to scanner sources | | ❌ |

## When it matters

This distinction matters whenever a skill has both:
1. A mechanical data source (scanner, script output, API response)
2. A model-driven evaluation layer that is supposed to see things the mechanical source cannot

Examples on this host:
- `/tp do?` + `/todo` scanner — the session review needs conversation patterns the scanner can't see
- `/check` + diff output — the verifier needs runtime claims that diff alone can't validate
- `/review` + static analysis — the reviewer needs architectural judgment that linters can't provide
- `/close` + close_accounting.py — the close orchestrator needs session context that accounting can't capture

## When it doesn't matter

If the skill is purely mechanical (scanner produces the complete output, model
just passes it through), this pattern doesn't apply — see
[[code-output-passthrough-narration-over-script-output]] instead.

If the skill has no mechanical input, this pattern doesn't apply — there's
nothing to accidentally over-weight.

## The guardrail

**The mechanical input must receive the same validity filter as every other
input.** If the scanner says "11 unresolved reviews," the model still asks:
are these already addressed? false positives? from abandoned work? The scanner
is a candidate generator, not an oracle.

This is the same principle as the `/todo` 8-point evaluation checklist: every
item, regardless of source, gets checked for "is this already done? false
positive? duplicate? actionable?"

## Reference implementation

`/tp do?` Step 0 has multiple mechanical inputs:
- Step 0a: compaction segment analysis
- Step 0b: transcript evidence scan (friction patterns)
- Step 0c: session arc (user messages with topics)
- Step 0d: git commit scan
- Step 0e (new): `/todo` scanner output

All five enter as evidence streams. The model reads all five, then does its
evaluation passes (NOW/NEXT/LATER, CROSS-DOMAIN NOTICES, COMPLETENESS SCAN).
The scanner doesn't replace the evaluation; it feeds it one more evidence
stream that the model might have otherwise missed (git status, uncommitted
handoffs, stale reviews).

## Relationship to code-orchestrates-model-judges

[[code-orchestrates-model-judges-skill-scale]] covers code as **gate
enforcer** — deterministic code decides whether the model can advance.

This concept covers code as **evidence feeder** — deterministic code provides
input the model uses for judgment, but the model retains framing control.

Both apply the same principle (deterministic does coordination, model does
judgment) at different layers:

| Concept | Layer | Code role | Model role |
|---------|-------|-----------|------------|
| code-orchestrates-model-judges | Gate enforcement | Decides whether to advance | Fills judgment fields |
| mechanical-as-input-not-frame | Evidence gathering | Provides filtered data streams | Decides what matters from all streams |

## Falsifier

This pattern is wrong if:
- The scanner output is so comprehensive that the model never needs to look
  beyond it (in which case, use [[code-output-passthrough-narration-over-script-output]]
  instead)
- The scanner's false-positive rate is high enough that the validity filter
  rejects most items (in which case, fix the scanner before feeding it as
  input)
- The model's evaluation adds no value on top of the scanner (in which case,
  the skill doesn't need a model-driven layer)

## Cross-references

- [[code-orchestrates-model-judges-skill-scale]] — the gate-enforcement complement
- [[analyst-exhibits-pattern-being-analyzed]] — why the session that authors a
  change shouldn't be the one that validates it
- [[code-output-passthrough-narration-over-script-output]] — when to bypass the
  model entirely
- [[optimal-vs-blanket-rule-application]] — don't apply this pattern blindly;
  check whether the specific skill needs mechanical grounding
