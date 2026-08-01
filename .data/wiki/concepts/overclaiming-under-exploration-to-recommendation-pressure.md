---
title: "Overclaiming under exploration-to-recommendation pressure: check disconfirming evidence before asserting"
created: 2026-07-31
source: session-2026-07-31 (/aar P1 — 5 recommendation reversals)
tags: [overclaiming, recommendation-reversal, exploration-to-recommendation, disconfirmation, verification-before-assertion, behavioral-pattern, failure-mode]
host: both
agent: grok
verification: single-source-verified
cognitive_load: 2
relations:
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write
    type: related
  - target: wiki/concepts/llm-defensiveness-pushback
    type: related
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation
    type: refines
summary: >
  When transitioning from exploration ("what did we find?") to recommendation
  ("what should we do?"), the agent asserts claims with confidence it hasn't
  earned — trading verification for assertiveness. The operator's predictable
  challenge questions ("how could you be wrong?", "did this actually work?",
  "what specific use cases?") expose the gap every time. Fix is procedural:
  answer the predictable challenge BEFORE asserting, not after being asked.
  5 instances in session 2026-07-31 — the pattern is stable, not occasional.
---

# Overclaiming under exploration-to-recommendation pressure

## Decision context

**Why this was needed:** Session 2026-07-31's AAR identified 5 recommendation
reversals — each from asserting a claim that a specific piece of evidence would
have disconfirmed if checked first. The pattern is not "the agent was wrong"
(random error); it's "the agent didn't check" (systematic pressure). The
exploration→recommendation transition creates confidence pressure that trades
verification for assertiveness.

## The pattern

| Phase | What happens | What should happen |
|-------|-------------|-------------------|
| Exploration | Research, investigate, gather evidence — high quality, honest | Same |
| Transition | Pressure to sound confident and decisive ("what should we do?") | **Pause** — check disconfirming evidence before asserting |
| Recommendation | Asserts claim as confident without checking what would deny it | Assert only after checking the specific falsifier |
| Operator challenge | "How could you be wrong?" / "did this actually work?" | — (the operator does this reliably) |
| Retraction | Claim collapses; retracted in next turn | — (prevented if falsifier was checked first) |

## The 5 instances (session 2026-07-31)

| # | Claim | Disconfirming evidence that existed | Operator's challenge |
|---|-------|-------------------------------------|---------------------|
| 1 | "Luna collapsed after one bad call" | Transcript boundary — turn-1 tools were a different model | "Luna never used one tool" |
| 2 | "Layer 2 worked positively for us" | In parallel dispatch, time value is minimal (same recovery cost as no gate) | "did this actually work positively for us?" |
| 3 | "First-available is exactly right for mechanical work" | Pool markdown carries failure-mode notes (minimax-m3 output budget) the picker drops | "how could you be wrong?" |
| 4 | "20% mechanical floor shows value" | Quota pools may be per-model not per-provider (unverified) | "what specific use cases show value?" |
| 5 | "Build the latency circuit breaker" | No data showed latency variance was a real problem | "do you have useful data somewhere else?" |

Each disconfirming evidence was **available before the assertion** — the agent
just didn't check it.

## Root cause analysis

```
OBSERVED_FAILURE: 5 recommendations asserted as confident, all retracted under scrutiny
IMMEDIATE_TRIGGER: exploration→recommendation transition created pressure to be decisive
PROXIMATE_CAUSE: agent asserted before checking disconfirming evidence
CONTRIBUTING_CONDITIONS: recommendation-dense session (research → improvements chain); each assertion felt like progress
SYSTEMIC_REUSABLE_CAUSE: the "could I be wrong?" check is optional (behavioral rule) rather than structural (pipeline step)
COMPETING_EXPLANATION: this session was unusually recommendation-dense, making the pattern more visible than typical
```

## The procedural fix

**Before any recommendation that will become an action item:**

1. **Name the falsifier:** what specific evidence would disconfirm this?
2. **Check it:** is that evidence available? If yes, read it.
3. **Answer the predictable challenge:** what will the operator ask? (Their questions are stable: "how could you be wrong?", "did this actually work?", "what specific use cases show value?")
4. **Then assert** — with the disconfirming evidence already integrated

This is the same principle as `/www`'s disconfirmation pass (Round 3), applied
to recommendations instead of research findings. The `/www` pipeline already
enforces it structurally for research. Recommendations need the same check
applied at the assertion point.

## Distinction from existing concepts

- **`causal-mechanism-claims-require-source-receipts`**: overclaiming about *how a system works* (mechanism) without reading the code. This concept is about overclaiming *what to do* (recommendation) without checking disconfirming evidence. Same root word, different failure class.
- **`evidence-first-default`**: the general principle of checking before asserting. This concept is the specific instance: the exploration→recommendation transition is where the pressure overcomes the principle.

## What this means for our workspace

1. **Recommendation-level disconfirmation check.** Before stating a recommendation as confident, name and check the falsifier. This is procedural, not architectural — it's a habit, not a system gap.
2. **The operator's challenge questions are predictable.** "How could you be wrong?", "did this actually work?", "what specific use cases?" — answer these BEFORE they're asked.
3. **Recommendation-dense sessions are higher-risk.** When the session chain is research → recommendations → actions, each assertion feels like progress. The pressure compounds. Extra vigilance needed in these session shapes.

## Falsifier

This pattern is wrong if:
- The 5 instances were session-specific (a particularly recommendation-dense session) rather than a stable behavioral pattern
- The operator's challenge questions are NOT predictable (they vary unpredictably, so pre-answering them doesn't help)
- Structural enforcement (a pipeline step that checks disconfirming evidence before allowing a recommendation) proves necessary because the procedural fix doesn't work

Re-verify across the next 5 sessions with recommendation content. If reversal count drops to ≤1 per session, the procedural fix works. If it stays at 3+, structural enforcement is needed.

## Receipts

| Claim | Evidence | Type |
|-------|----------|------|
| 5 recommendation reversals in session 2026-07-31 | AAR report P1: episodes E1-E5, recurring_patterns[0]; signals.json: recommendation_revision ×5 | [OBSERVED] |
| Each disconfirming evidence was available before assertion | E1: transcript boundary checkable; E2: parallel-vs-serial analysis checkable; E3: pool markdown readable; E4: quota cache checkable; E5: latency data checkable | [OBSERVED] |
| Operator's challenge questions are predictable | E1-E5 each matched a specific challenge pattern: "how could you be wrong?", "did this work?", "what use cases?", "do you have data?" | [OBSERVED] |
| Pattern is stable not occasional | 5/5 recommendations in this session reversed — rate, not count, is the signal | [INFERENCE] — needs cross-session verification |

## Auto-related

- [[scope-matching-verification-discipline]]
- [[close-scanner-verification-gap-stale-read]]
- [[premature-closure-narrative-sufficiency-external-approaches]]
- [[skill-graph]]
- [[sdlc-proactive-prevention-techniques-2026]]

