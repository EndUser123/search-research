---
title: "Mechanical tool output is a hypothesis, not a measurement: the method-vs-evidence receipt distinction"
created: 2026-08-09
source: session-2026-08-09
tags: [evidence, receipts, method, scanners, measurement, epistemics, root-cause, closure-pressure]
summary: >
  The AGENTS.md "Claims require receipts" rule covers evidence-handling
  failures (quoting a source). It does not cover method failures: treating
  mechanical scanner output (grep counts, regex matches, automated tool
  results) as if it has the same epistemic status as direct observation.
  Scanner output is a hypothesis generator — it needs sampling or validation
  before it becomes a fact. This session produced a concrete demonstration:
  a regex scanner reported "23.3% of sessions have evidence-accuracy
  corrections," which sampled down to 2-6% after false-positive analysis.
  The receipt rule must be applied at the moment of first stating, not the
  moment of being challenged — and the receipt type must match the claim type.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
tier: warm
confidence: 0.9
last_verified: 2026-08-09
half_life_days: 180
relations:
  - target: wiki/concepts/denylist-drift-in-workspace-scanners
    type: related
  - target: wiki/concepts/inference-chains-bare-numbers-destructive-write
    type: related
---

## Summary

Two distinct root causes produce the same surface symptom — the agent
states something as fact that turns out to be wrong. Conflating them under
one banner ("the agent doesn't verify enough") produces fixes too vague to
fire. They have different receipts and different fixes:

1. **Evidence-handling failure:** the agent reads a source, forms a
   summary, states the summary, and the summary is wrong because it wasn't
   anchored to the exact words. Fix: quote the verbatim source before
   stating the claim.
2. **Method failure:** the agent runs a mechanical tool (scanner, grep,
   regex matcher), gets a count or rate, and states it as fact without
   checking the tool's false-positive rate. Fix: sample before you state
   a rate.

Both share an underlying driver — **closure pressure**, the pull toward
a decisive answer rather than sitting with "let me verify that." But
closure pressure is not directly fixable; the two mechanical fixes above
are what make it actionable.

## Key Findings

### The two failure modes have different receipt types

| Failure type | What the agent did wrong | Required receipt | Existing rule coverage |
|---|---|---|---|
| Evidence-handling | Stated a claim about evidence already in context without quoting it | Verbatim quote of the source field/line | "Claims require receipts" — covered |
| Method | Treated scanner output as measurement without checking FP rate | Sample of hits classified as real vs noise | "Evidence scope: receipt type must match claim type" — covered, but easily missed |

### The 23.3% → 2-6% demonstration (this session)

A regex scanner matched evidence-correction patterns ("verify", "fabrication",
"re-check", "wrong/incorrect") in 615 of 2635 historical session transcripts
(23.3%). Reported as CHRONIC. After sampling ~80 hits across 6 categories
and classifying them manually:

- `re-check` (659 hits): 95% false positive — matched "verify" in skill descriptions and subagent task prompts
- `fabrication` (324 hits): 90% false positive — matched workspace vocabulary about anti-fabrication architecture
- `wrong-claim` (39 hits): 95% false positive — all samples were bare `/check` invocations
- `did-you-check` (21 hits): 40% real — "did you actually read the documentation?"
- `thats-wrong` (5 hits): 60% real — "That's not true", "No, that's not correct"

Overall message-level FP rate: **92%**. Estimated true sessions with ≥1 real
evidence-accuracy correction: 61-153 (2.3%-5.8%). Classification shifted from
CHRONIC to **ACUTE**.

This is the canonical example: the scanner output (23.3%) was a hypothesis.
The sampling pass (2-6%) was the measurement. Stating the hypothesis as
measurement was the method failure.

### The verification reflex works — but fires too late

The meta-pattern across this session's three failures (list_handoffs.py
"bug", misread JSON classification, 23.3% rate): **each was caught within
1-2 turns by the agent's own re-run**. The problem is not that the agent
doesn't verify; it's that verification happens *after* stating, not *before*.
The cost is wasted operator turns (a `/go proceed` on a non-bug, a Stop hook
catching a hedge, a `/tp` to diagnose the pattern).

The fix is a **sequencing change**, not a new constraint: move the
verification step earlier. Before stating "X is broken," run X. Before
stating "rate is Y%," check the FP rate.

### Why "be more careful" doesn't work

Prose rules for response patterns have a documented ~50% compliance ceiling
under session pressure (per the workspace's own wiki citations). The
receipt rule exists and covers both failure modes — but it fires at the
*moment of being challenged*, not the *moment of first stating*. The
sequencing change (verify-then-state instead of state-then-verify-on-
challenge) is the actionable refinement.

## The durable rule

**Scanner output is a hypothesis, not a measurement.** Any claim derived
from mechanical tool output (grep count, regex match rate, automated
classification) requires a validation pass before it can be stated as fact.

Specifically:
- **Rate claims** ("X% of sessions have Y") require sampling the matches
  and estimating the false-positive rate. The rate without the FP analysis
  is a hypothesis.
- **Count claims** ("N files match pattern Z") are facts about the scanner,
  not about the world. "N files match" is true; "N files ARE pattern Z" is
  a hypothesis requiring validation.
- **Classification claims** ("this file is a candidate_source") are
  hypotheses about the classifier's accuracy, not facts about the file.

The receipt for a scanner-derived claim is a **validation sample**, not
the scanner output itself.

## When to apply

- Before stating any rate, percentage, or frequency derived from automated
  tooling
- Before stating a classification result as fact (file type, authority
  status, severity level)
- Before reporting a count as evidence of a pattern ("N matches means the
  problem is widespread")

## When NOT to apply

- Direct observations (exit code, quoted file field, command stdout) —
  these are evidence, not scanner output
- Counts of items you've personally enumerated and inspected each one
- Rates computed from a fully-classified population (no sampling needed
  when N=population)

## Falsifier

This concept is wrong if mechanical tool output is as reliable as direct
observation for the claim type being made. In workspaces where scanner
patterns are precise (exact-match filename filters, schema-validated JSON
parsing), the FP rate is near zero and sampling adds overhead without
value. The rule is calibrated for **fuzzy pattern matchers** (regex on
natural language, substring matching on paths) where FP rates of 50-95%
are empirically observed.

## Related

[[denylist-drift-in-workspace-scanners]] — same session, different bug
class: denylist classification of workspace files drifts. The preflight
fix demonstrates the principle (the denylist was a hypothesis about which
dirs were derived; the actual workspace had 25+ unlisted derived dirs).

[[inference-chains-bare-numbers-destructive-write]] — the broader pattern
of unverified numbers causing silent failures.

## Sources

- Session 2026-08-09: three evidence/method failures caught by re-run verification
- Scanner files: `P:\tmp\scan_evidence_corrections.py`, `P:\tmp\scan_evidence_refined.py`, `P:\tmp\classify_fp_rate.py`
- AGENTS.md: "Claims require receipts; narrative sufficiency is not verification" and "Evidence scope: receipt type must match claim type"
- Sample size: 80 hits classified manually across 6 pattern categories
