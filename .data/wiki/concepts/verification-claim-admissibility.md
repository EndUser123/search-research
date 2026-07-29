---
title: "Verification claim admissibility: verdict vocabulary, replay realism, and baseline-aware regression"
created: 2026-07-27
source: session-019fa5a1 (/tp opportunity scan, O-3/O-4/O-5)
tags: [verification, verdict, replay-realism, regression, evidence-discipline, claim-lifecycle, cross-host]
summary: >
  Three verification-claim admissibility rules extracted from the external LLM
  critique of the close-authority work. (1) Verdict vocabulary must distinguish
  COMPONENT_PROVEN from LIVE_ENFORCEMENT_PROVEN — a standalone module with
  passing tests is not "enforcement proven." (2) Tests labeled "real replay"
  must exercise the production entry point end-to-end; lower tiers must be
  labeled honestly (unit / integration / real replay). (3) "Zero regressions"
  is inadmissible without a baseline comparison that states exact failure
  counts before and after, plus the failure-set diff. All three are instances
  of the claim-lifecycle gate pattern: claims are admissible only with their
  required receipt.
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - "Session 019fa5a1 external LLM critique (rounds 1 and 2)"
  - "P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md"
  - "P:/docs/handoffs/external-llm-critique-evidentiary-discipline-20260727/HANDOFF.md"
relations:
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: extends — that names the principle (prose fails, gates work); this applies it to verification claims
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: related — both address claims that feel sufficient but aren't
  - target: wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md
    type: complements — that covers assumption-auditing techniques; this covers the verdict vocabulary those techniques produce
---

# Verification claim admissibility

## Decision context

**Why this was needed.** The close-authority work (session 019fa5a1) produced
three overstatements caught by external critique: (1) a standalone module with
20 passing tests was labeled "ENFORCEMENT PROVEN" when it wasn't wired into
production; (2) a synthetic unit test was labeled "real replay"; (3) "zero
regressions" was claimed without running the baseline comparison. Each
overstatement was made in good faith but lacked the receipt the claim required.

## Rule 1: Verdict vocabulary — COMPONENT vs LIVE

A verdict must distinguish two independent axes:

| Axis | Values | Meaning |
|---|---|---|
| **Component** | PROVEN / NOT_PROVEN | Does the module work in isolation? |
| **Live** | PROVEN / NOT_PROVEN | Is the module wired into the production path and actually invoked? |

**Standalone-tested = `COMPONENT_PROVEN — LIVE_NOT_PROVEN`.** Not
`PROVEN_WITH_LIMITATIONS` — that label conflates two axes.

**The rule:** when claiming a verdict on enforcement/authority/security work,
state both axes explicitly. The live axis requires evidence that the production
entry point invokes the module (import + call site), not just that the module
exists and passes tests.

## Rule 2: Replay realism tiers

| Tier | Definition | Label |
|---|---|---|
| **Unit** | Calls functions directly with synthetic inputs | "unit test" |
| **Integration** | Calls real components in a test harness (not the production entry point) | "integration test" |
| **Real replay** | Executes the actual production CLI/entry point with real artifacts at real filesystem paths | "real replay" |

**The rule:** a test may only be labeled "real replay" if it meets tier 3.
Lower tiers must use their honest label. Calling an integration test a "real
replay" is an overstatement that the next consumer will trust.

## Rule 3: Baseline-aware regression contract

When the baseline has N pre-existing failures:

```
REQUIRED REGRESSION REPORT:
  baseline failures: <count>
  post-change failures: <count>
  newly-failing tests: <list>
  newly-passing tests: <list>
```

**The rule:** "zero regressions" is inadmissible without this report. The
umbrella claim is replaced by the exact failure-set diff. When the baseline
is clean (0 failures), "zero new failures" is sufficient.

## What this means for our workspace

These three rules are concrete instances of the claim-lifecycle gate pattern.
Each rule defines: what claim is being made, what receipt is required, and
what label is admissible. They can be enforced mechanically:

- Rule 1: /check scanner can detect "PROVEN" in output text and require the
  component/live axis
- Rule 2: /check can detect "real replay" labels and require production-entry-
  point evidence
- Rule 3: /check can detect "zero regressions" and require the baseline
  failure-set diff

## Falsifier

These rules are over-engineering if:
- The overstatement pattern is rare (one session is insufficient evidence).
  Measure before scaling to mechanical enforcement.
- The existing verdict tokens already encode these distinctions under
  different names. Check before adding new vocabulary.

## Receipts

- [FACT] The close-authority report used "PROVEN_WITH_LIMITATIONS" for a standalone module — verified: commit 7148eb6 report text, session 019fa5a1
- [FACT] test_20 was labeled "real replay" but used synthetic digests and direct function calls — verified: test_close_authority.py test_20, read this session
- [FACT] "Zero regressions" was claimed without running the baseline; actual comparison showed 22 baseline vs 23 branch (1 new regression) — verified: /check verifier output, session 019fa5a1

## Related

- [[mandatory-step-enforcement-code-over-prose]] — the enforcement principle these rules apply
- [[plausible-narratives-substitute-for-verification]] — the behavioral pattern these rules prevent
- [[assumption-auditing-and-unknown-unknown-discovery]] — the techniques that produce the claims these rules govern
