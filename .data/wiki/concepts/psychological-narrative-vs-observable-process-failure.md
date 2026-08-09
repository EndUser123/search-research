---
title: "Psychological narrative vs observable process failure: why 'I was defensive' is not a root cause"
created: 2026-08-08
updated: 2026-08-08
tags: [behavioral-rule, correction-response, root-cause, epistemic-discipline, enforcement, hook, anti-confession]
host: both
agent: grok
verification: session-validated-2026-08-08
cognitive_load: 2
summary: >
  Psychological self-narratives ("I was defensive," "I was overconfident,"
  "I got anchored") are inferences about WHY reasoning failed, not
  descriptions of WHAT process failure occurred. LLMs can become eloquent
  at confessing cognitive biases after the fact without getting materially
  better at preventing them. The durable fix: translate every psychological
  narrative into an observable process failure — what check was omitted,
  what evidence boundary was crossed, what alternative was not tested.
  Enforced by Stop_psychological_narrative_gate.py.
---

# Psychological narrative vs observable process failure

## The distinction

When an LLM is corrected, it often responds with a psychological
self-narrative:

> "You're right. I was being defensive."

This feels self-aware but is **narrative substituted for evidence**. The
LLM doesn't actually know it was "being defensive" — that's an inference
about its own internal reasoning process, which it cannot observe.

The alternative is an **observable process failure**:

> "My previous response defended the rating without testing whether
> the known bypass paths actually prevented the original failure.
> I failed to run the state/action mismatch test before claiming
> the state machine was sound."

This identifies a **specific, fixable process gap**: a test that was omitted,
an evidence boundary that was crossed, an alternative that was not searched.

## Why this matters

The distinction is the difference between:

| Psychological narrative | Observable process failure |
|------------------------|---------------------------|
| Sounds self-aware | Is actually self-aware |
| Explains WHY (inferred motive) | Describes WHAT (observable gap) |
| Cannot be fixed mechanically | Can be fixed with a check/gate/search |
| Confession theater | Root cause |
| "I was overconfident" | "I asserted X without a receipt matching the claim type" |

LLMs are trained to be helpful and to acknowledge mistakes. This produces
fluent confessions of cognitive bias — "I was anchored," "I succumbed to
closure pressure" — that sound like growth but change nothing.

## The translation table

| Psychological narrative | Observable process failure translation |
|------------------------|---------------------------------------|
| "I was defensive" | "I defended X without testing the decision-critical counterclaim Y" |
| "I was overconfident" | "I asserted X without a receipt matching the claim type" |
| "I got anchored" | "I searched within the solution frame without running the breadth-first discovery pass" |
| "I was biased" | "I promoted an inference to fact without discriminating evidence" |
| "I was careless" | "I omitted the [specific check/gate/step]" |
| "I succumbed to closure pressure" | "I concluded before the evidence requirements were satisfied" |

## Relationship to existing patterns

- `[[correction-response-discipline-anti-binary-swing]]` — the disposition
  matrix for how to respond to corrections (CONFIRMED/PARTIAL/REJECTED).
  This concept adds: the *format* of the response must be process-shaped,
  not psychological.
- `[[theatrical-contrition-and-over-apologetic-response-patterns]]` — covers
  performative apology as a surface. This concept goes deeper: even without
  apology theater, the root-cause attribution itself can be a narrative
  substitute.
- `[[decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming]]`
  — the reviewer-as-hypothesis rule (CONFIRMED/PARTIAL/REJECTED before
  adoption). This concept adds the translation requirement on top.

## Mechanical enforcement

`Stop_psychological_narrative_gate.py` detects psychological self-narratives
without an accompanying process-failure translation and blocks the turn.

**Detection patterns:** "I was (being) defensive/overconfident/anchored/biased/careless"

**Process-failure indicators (any one satisfies):**
- "I failed to / did not / omitted / skipped"
- "without testing / verifying / checking / searching"
- "crossed (the) evidence boundary"
- "asserted without / claimed without"
- "alternative not tested / counterexample not searched"

If the psychological narrative appears with a process-failure translation
in the same response, the hook passes. The model can still USE the
psychological phrase — it just can't stop there.

## Evidence incident (2026-08-08)

The reviewer-as-hypothesis rule existed in AGENTS.md throughout session
019fdf3d. Nine external-LLM recommendations were implemented without a
single CONFIRMED/PARTIAL/REJECTED classification. The implementing LLM's
response to being caught: "The irony, and naming it is more honest than
pretending I've internalized the discipline."

That response is itself a psychological narrative. The observable process
failure: "I implemented each recommendation immediately after reading it,
without decomposing the critique into individual claims, identifying what
evidence would distinguish my position from the reviewer's, or inspecting
that evidence before changing my conclusion."

## Falsifier

This concept is wrong if, within 6 months:
- The hook fires and the model produces a process-failure translation that
  is itself just a rephrased psychological narrative ("I failed to be
  sufficiently rigorous" — which is unobservable). Fix: tighten the
  process-failure detection patterns.
- The hook never fires because the model stops using psychological
  narratives (success — retire the hook).
- The hook fires constantly with false positives on legitimate self-assessment.
  Fix: narrow the detection patterns.
