---
title: Embedded Claim Rule — prompt technique for assertion-vs-discussion distinction
created: 2026-08-07
session: 019fcdd2-e190-7323-9b77-57a1c73dada5
verified: OBSERVED
host: grok
---

# Embedded Claim Rule — prompt technique for assertion detection

## The technique

When building an LLM-as-judge that detects **assertions** (claims stated as fact) vs **discussion** (claims analyzed, quoted, or measured as meta-commentary), add an explicit **EMBEDDED CLAIM RULE** to the system prompt:

> When a state/prediction phrase appears inside a sentence that DISCUSSES it, the ENTIRE SENTENCE is DISCUSSION — do not extract the embedded phrase and evaluate it as a standalone assertion. Distancing verbs that make a sentence DISCUSSION: fabricated, claimed, stated, said, alleged, detects, measures, documents, identified, exhibits, shows, reported.

## Why it works

Without this rule, the LLM extracts embedded claims from discussion text and evaluates them as standalone assertions. Example: "The agent fabricated '50 handoffs are stale'" gets decomposed into the claim "50 handoffs are stale" which is then checked against evidence — producing a false positive.

The EMBEDDED CLAIM RULE prevents this decomposition by instructing the LLM to evaluate at the **sentence level**, not the phrase level. If a distancing verb introduces the claim, the sentence's primary purpose is analysis, not assertion.

## Evidence

- **Test corpus:** 8/8 (100%) accuracy with the rule vs 7/8 (88%) without it. The failing case was always the "Discussion: analyzing pattern" case where a quoted claim was extracted as an assertion.
- **DeepEval baseline:** 50% accuracy (catches contradictions but not unsupported inferences). The EMBEDDED CLAIM RULE plus "absent-from-evidence = unsupported" instruction brought it to 100%.
- **Session:** 019fcdd2, built 2026-08-07, tested via `P:/tmp/test_claim_judge.py`

## Transferability

This technique applies to any LLM-as-judge that must distinguish:
- **Asserting** a claim vs **quoting/referencing** one
- **Making** a statement vs **analyzing** one
- **Stating** a fact vs **measuring** how often it occurs

Use cases beyond ungrounded-claim detection:
- Hallucination detection (did the model assert X, or did it quote X from context?)
- Fact-checking (is the text claiming Y, or reporting that someone else claimed Y?)
- Sentiment analysis (is the text expressing anger, or describing an angry exchange?)

## Related

- [[ungrounded-state-prediction-claims-detection-architecture]] — the system this technique was built for
- [[prompting-patterns-for-ai-agent-control]] — broader prompt engineering patterns
