---
title: "Data-driven detector prioritization: scan historical transcripts to decide which hook to build next"
created: 2026-08-08
source: session-019fe25d
tags: [hooks, detector, prioritization, measurement, correction-scanning, historical-transcripts, data-driven, transferable-technique]
host: grok
agent: grok
cognitive_load: 2
verification: directly-verified
relations:
  - target: wiki/concepts/measurement-before-addition-principle.md
    type: implements
  - target: wiki/concepts/scan-historical-transcripts-before-deferring-data-already-exists.md
    type: extends
  - target: wiki/concepts/llm-judgment-hooks.md
    type: complements
summary: >
  Before building a new enforcement detector, scan the 2,539+ historical session
  transcripts for operator corrections, classify them by failure type, and build
  the detector for the highest-frequency uncovered class. This replaces guessing
  ("which failure class matters most?") with data ("which class caused the most
  operator corrections?"). In the first run, this method identified equivalence_bypass
  (43 corrections, no detector) as the highest-priority build target — not the
  class the agent would have guessed.
---

# Data-driven detector prioritization

## Decision context

The workspace had 6+ narrow enforcement detectors (confabulation, false-choice,
minimal-bias, lazy-closure, empirical-claims, recommendation-gate), each built
ad-hoc when a specific failure class caused operator corrections. The question
was: **which detector should we build next?** Without data, the answer is
whichever failure class the agent happens to remember or finds architecturally
interesting — a known bias (session 019fde37: the agent deferred a narrow
mechanical fix twice in favor of "higher-ROI" architectural captures).

The [[measurement-before-addition-principle]] says: measure the current defect
rate before adding detection. This method operationalizes that principle for
hook prioritization specifically.

## The method

```
1. SCAN: run correction_classifier.py across all historical session transcripts
   (~2,539 files, ~4,350 user messages, ~62 seconds)

2. CLASSIFY: each correction is matched against failure-type patterns:
   - confabulation, false_choice, ungrounded_recommendation, lazy_closure
   - equivalence_bypass, transition_effort_bias, narrative_sufficiency
   - scope_drift, replacement_before_investigation, general_correction

3. COMPARE: cross-reference frequency against existing detector coverage:
   - Classes WITH a detector: how many corrections still occur? (detector may need tuning)
   - Classes WITHOUT a detector: how many corrections? (build priority)

4. PRIORITIZE: highest-frequency uncovered class = next detector to build
```

## First-run results (2026-08-08)

| Failure type | Corrections | Has detector? | Action |
|---|---|---|---|
| general_correction | 495 | Various (uncategorized) | Tighten classifier |
| lazy_closure | 69 | ✅ `Stop_lazy_closure_debt.py` | Monitor |
| **equivalence_bypass** | **43** | **❌** | **BUILD (highest priority)** |
| transition_effort_bias | 36 | ✅ `minimal_bias_gate.py` | Monitor |
| confabulation | 26 | ✅ `confabulation_gate.py` | Monitor |
| ungrounded_recommendation | 16 | ✅ `minimal_bias_gate.py` | Monitor |
| **narrative_sufficiency** | **12** | **❌** | **BUILD** |
| **scope_drift** | **10** | **❌** | **BUILD** |
| false_choice | 9 | ✅ `Stop_false_choice_validator.py` | Monitor |
| replacement_before_investigation | 1 | ❌ | Defer (low frequency) |

The data said: equivalence_bypass (43) > narrative_sufficiency (12) > scope_drift (10).
All three were built in one session using the data as the prioritization driver.

## What this catches that guessing misses

Without data, the agent's instinct is to build the detector for the failure
class that:
- Caused the most recent visible correction (recency bias)
- Is architecturally interesting (interesting-bias)
- The agent remembers from this session (availability bias)

The data revealed **equivalence_bypass** (43 corrections) as the top priority —
a class that hadn't been discussed this session and wouldn't have been the
agent's guess. The /scan-historical-transcripts-before-deferring principle
applies: the data already exists; the question is whether to use it.

## Data-quality caveats

**The regex classifier has noise.** Many "general_correction" hits are false
positives from subagent dispatch prompts (system-injected messages that contain
correction keywords like "didn't", "shouldn't" as part of task instructions,
not operator pushback). The directional findings (equivalence_bypass is clearly
higher than scope_drift) are valid even with noise in the denominator, but
absolute counts are inflated.

**The classifier should be refined iteratively.** Each run produces samples
that can be eyeballed for false positives. Tightening the regex for
general_correction would improve future runs. The scanner is at
`~/.grok/scripts/correction_classifier.py`.

## The block-logging gap (structural finding discovered during this method)

While building the dashboard to measure detector effectiveness, we discovered
that `log_fail` was only called on **error paths**, never on **successful
blocks**. This meant 6/8 detectors showed as "silent" in the dashboard despite
working in production — `confabulation_gate` blocked live during the session
but produced zero log entries. The detectors were functioning but invisible.

**The pattern:** observability code that only logs failures, not successes,
creates a false picture of system activity. The fix: call `log_block()` on
every successful block, not just `log_fail()` on errors. This applies to any
monitoring infrastructure where "is it working?" is a question — if you only
log when things break, you can't tell whether the system is active or dead.

## What this means for our workspace

1. **Run the scanner before building any new detector.** The data tells you
   which class to prioritize. Without it, you're guessing.

2. **The dashboard (`detector_health.py`) runs on SessionStart** — every
   session sees detector activity state. Silent detectors (zero fires) are
   surfaced immediately, not discovered months later.

3. **Regression tests (`test_detectors.py`) run on modification** — 16 tests
   (block + suppress for each detector) catch pattern regressions when regex
   patterns are tuned.

4. **The block-logging gap applies to all hooks, not just detectors.** Any
   hook that can block should log both blocks and errors. The `log_fail` /
   `log_block` split should be the standard pattern.

## Falsifier

This method is wrong if:
- The regex classifier produces so much noise that the prioritization is
  random (test: tighten the classifier and check if the ranking changes
  materially)
- The correction frequency doesn't correlate with actual harm (test: compare
  high-frequency classes against AAR findings — do the most-corrected classes
  also cause the most damage?)
- The historical transcripts don't represent current failure patterns (test:
  re-run on recent-only transcripts and compare rankings)

## Receipts

- Scanner: `~/.grok/scripts/correction_classifier.py` (2,539 files, 717 corrections, 62s)
- Dashboard: `~/.grok/scripts/detector_health.py` (revealed 6/8 silent detectors)
- Block-logging fix: commit `c94531e` (4 detectors patched to call `log_block`)
- 3 new detectors built from data: commit `12df7ee` (equivalence_bypass, narrative_sufficiency, scope_drift)
- Regression tests: `~/.grok/hooks/tests/test_detectors.py` (16/16 passing)
- SessionStart injection: `~/.grok/hooks/detector-health-session-start.json`

## Auto-related

- [[skill-catalog]]
- [[youtube-transcript-extraction-techniques]]
- [[close-scanner-unavailable-fallback-session-observations-handoff]]
- [[scan-historical-transcripts-before-deferring-data-already-exists]]
- [[adhd-friendly-unified-todo-workspace-email-scanning]]

