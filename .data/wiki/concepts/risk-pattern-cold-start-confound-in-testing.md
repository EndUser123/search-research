---
title: "Risk pattern: cold-start confound in skill testing"
created: 2026-08-06
source: session-20260806
tags: [risk-pattern, testing, cold-start, confound, wiki-grounding]
summary: >
  Testing a wiki-grounded skill after seeding the wiki measures warm-state
  behavior, not cold-start. The wiki grounding step changes what the skill
  finds. Cold-start (empty wiki) is the condition every new user faces and
  must be tested first.
agent: grok
host: grok
cognitive_load: 1
verification: observed
relations:
  - target: wiki/concepts/risks-skill-improvement-research-2026.md
    type: extends
---

# Risk pattern: cold-start confound in skill testing

## Pattern

When a skill has a wiki-grounding step (query the wiki before executing), testing it after seeding the wiki measures warm-state behavior. But cold-start (empty wiki) is the default condition for any new skill — and it's the hardest condition. Seeding before testing makes the test results uninterpretable: you can't tell whether the skill works well on its own or only because the wiki gave it hints.

## Evidence

- **Session 2026-08-06:** `/tp` critique of the `/risk` improvement plan identified this confound. The original plan put wiki seeding (Rec 3) before test runs (Rec 1). The critique correctly noted: "if seeded, the scan has prior knowledge. If empty, it runs cold. These are different test conditions."
- **Fix:** test cold-start first, then seed, then re-test warm-state. This produces a controlled comparison.

## What this means for our workspace

1. For any skill with a wiki-grounding step (`/risk`, `/why`, `/www`), cold-start testing must come before warm-state testing.
2. The cold-start vs warm-state comparison IS the measurement of whether wiki grounding helps. Without it, you're just testing warm-state and assuming it generalizes.
3. This applies to any new wiki-grounded skill being developed.
4. The comparison also tells you whether the wiki seeding was worth the effort — if cold-start and warm-state produce the same results, the wiki grounding step adds no value and can be deferred.

## Falsifier

If the skill produces identical results cold-start and warm-state (wiki grounding has no effect), the confound doesn't matter — there's no behavioral difference to confuse. In practice, wiki grounding changes scan coverage, so the confound is real.

## Related concepts

- [[risks-skill-improvement-research-2026]] — the research where this confound was identified and fixed
- [[adaptive-expansion-evidence-triggered-conditional-steps]] — wiki grounding is an adaptive expansion step
- [[agent-failure-modes-2026]] — cold-start amnesia is the failure mode this confound exploits in testing

## Receipts

- Session 019fcdd2 `/tp` critique: F1 cold-start confound finding (VERIFIED, changes-recommendation)
- Wiki concept: `risks-skill-improvement-research-2026.md` § "Test run results" (cold-start data collected)
