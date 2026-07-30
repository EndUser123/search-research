# Design Summary: `/behave` — Grok-Native Behavioral Decision-Integrity Skill

## What was produced

A design document for a new Grok-native skill (`/behave`) that performs **post-hoc diagnostic auditing** of LLM decision-integrity failures, filling four gaps no existing Grok skill covers: decision-transition auditing, load-bearing finding identification, self-protection pattern detection, and user-dependence classification.

## Key design choices

- **Skill name:** `/behave` — reuses the name from the original Claude-only skill (not loaded on Grok, no collision); matches the operator's existing BE-01 handoff reference and the short-name convention.
- **Diagnostic, not runtime enforcement.** Runtime enforcement is architecturally impossible in Grok Build (no cognitive-transition hook). The skill outputs a diagnostic report; the operator decides.
- **Separate skill, not a merge.** Handoff explicit non-goal: no merge into `/tp` or `/debrief`. The skill reuses `/why` infrastructure (pattern library, evidence tiers, cross-model review, feedback-to-wiki) rather than reinventing it.
- **v1 scope: 3 patterns** (BP-001 inference over execution, BP-007 selective reporting, BP-008 authority assumption). The other 5 McCormick patterns are v2.
- **7-dimension analysis contract preserved** from the requirements spec: decision timeline, finding classification, load-bearing finding map, claim-to-evidence verification, authority-path analysis, user-dependence check, self-protection detection.
- **Replay fixture as acceptance oracle.** A structured test case representing a known incident pattern — deterministic, testable, the gold standard for the skill's diagnostic output.

## What gets built

15 implementation units across 4 new files and 1 auto-updated catalog entry:

1. **`C:/Users/brsth/.grok/skills/behave/SKILL.md`** (~450 LOC) — the skill itself with frontmatter, input/output contracts, 10-step methodology.
2. **`C:/Users/brsth/.grok/skills/behave/fixtures/review-decision-integrity-v1.md`** (~80 LOC) — replay fixture.
3. **`C:/Users/brsth/.grok/skills/behave/README.md`** (~40 LOC) — acceptance test documentation.
4. **`P:/.data/wiki/concepts/governance-pattern-library.md`** (~60 LOC) — cumulative pattern library (initial seed: 3 v1 patterns).

No existing skill is modified. No hooks added. No settings.json change.

## Why this is the optimal long-term solution

- **Reuses infrastructure.** `/why` already has pattern-library query, evidence-tier calibration, cross-model review, and feedback-to-wiki. Building parallel infrastructure would be duplication.
- **Testable.** The replay fixture gives a deterministic acceptance oracle — the v1 design can be verified against a known incident pattern. This is the strongest possible acceptance criterion for a diagnostic skill.
- **Cumulative.** Step 9 feedback-to-wiki means every new governance pattern found becomes reusable on the next incident. The skill gets better over time.
- **Composes with VI-01.** VI-01 (behavioral rules in `/tp` and `/design`) is the runtime-side counterpart; `/behave` is the diagnostic-side counterpart. Together they cover detection + repair.

## Open questions

Three [INFERENCE] premises and three [UNKNOWN] premises are listed in § 16 of the design doc. The most important:

- **Analyst-exhibits-pattern-being-analyzed risk** — the skill may itself exhibit self-protection patterns when diagnosing them. Mitigation: cross-model review (Step 8) for high-stakes findings.
- **Whether the 5 v2 patterns should be added to v1 anyway** — handoff constrains v1 to 3; broader coverage is operator-callable.
- **Whether runtime enforcement becomes feasible in v2** — depends on whether Grok Build adds a cognitive-transition hook.

## Disposition

The design itself is **HANDOFF** (operator review). The 15 implementation units are **COMMIT_THIS_SESSION** conditional on operator approval.

## Files

- Design: `C:\Users\brsth\AppData\Local\Temp\grok-design-81539877\grok-design-doc-81539877.md`
- This summary: `C:\Users\brsth\AppData\Local\Temp\grok-design-81539877\grok-design-summary-81539877.md`
