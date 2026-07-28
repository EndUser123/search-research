---
title: "Missing decision frameworks: 9 categories our workspace lacks for systematic problem anticipation"
created: 2026-07-28
source: session-019fa276 (/go evaluation of cc-thinking-skills + problem-prediction research synthesis)
tags: [decision-frameworks, mental-models, FMEA, reference-class-forecasting, calibration, second-order-thinking, ACH, sensitivity-analysis, inversion, skills-gap, cc-thinking-skills]
summary: >
  Synthesis of three research streams (systematic problem anticipation,
  Proof-or-Stop evidence gating, cc-thinking-skills evaluation) identifying
  9 framework categories our workspace is missing, ranked by the failure
  class each catches. Top 4 (RCF, external-validity audit, probabilistic
  calibration, second-order thinking) are implementable as enhancements to
  existing skills (/tp, /www, /review) rather than new skills. Bottom 5
  (ACH, FMEA, sensitivity analysis, inversion-as-default, Hanlon/Chesterton)
  are medium-priority additions. The cc-thinking-skills repo (28 frameworks)
  was not directly readable but was cross-referenced against the wiki's own
  gap analysis. Formal methods (MCTS, LATS, model checking) are deferred —
  our decisions are low-frequency and reversible.
agent: grok
host: grok
cognitive_load: 3
verification: cross_referenced_to_workspace
sources:
  - "P:/.data/wiki/concepts/systematic-problem-anticipation-methods-and-existing-tools.md" (the FMEA/MCTS/LATS survey)
  - "P:/.data/wiki/concepts/skill-step-receipts-checked-by-hooks.md" (Proof-or-Stop evidence)
  - "P:/.data/wiki/concepts/blind-spot-detection-methods.md" (existing blind-spot coverage)
  - "P:/.data/wiki/concepts/assumption-auditing-and-unknown-unknown-discovery.md" (missing techniques)
  - "P:/.data/wiki/concepts/mental-models-for-tp-and-brainstorming.md" (second-order thinking design)
  - "P:/docs/handoffs/problem-prediction-skills-20260727/HANDOFF.md" (the 6 actionable items)
relations:
  - target: wiki/concepts/systematic-problem-anticipation-methods-and-existing-tools.md
    type: refines
  - target: wiki/concepts/mental-models-for-tp-and-brainstorming.md
    type: extends
  - target: wiki/concepts/blind-spot-detection-methods.md
    type: extends
  - target: wiki/concepts/skill-step-receipts-checked-by-hooks.md
    type: related
---

# Missing decision frameworks: what our workspace lacks

## Decision context

**Why this was needed:** the operator asked whether our problem-prediction
research produced actionable skill/repo/improvement ideas. Three research
streams converged: (1) the FMEA/MCTS/LATS survey, (2) the Proof-or-Stop
evidence-gating paper, and (3) an evaluation of the cc-thinking-skills
repo (28 mental-model frameworks). The synthesis identified 9 framework
categories our workspace is missing, each catching a documented failure
class that our existing skills (pre-mortem, steelman, disconfirmation)
miss.

## What we already have (strong)

| Framework | Where it lives | Receipt |
|---|---|---|
| Pre-mortem | `/red-team`, `/tp` domain 3a, `/wargame` | 3 skills implement it |
| Steelman + falsifier | `/tp`, `/design` Step 5.5 | Core `/tp` domain |
| Disconfirmation search | `/www` Round 3 (mandatory) | Structural enforcement |
| Adversarial review | `/red-team` (8 specialist lenses) | Full multi-agent pipeline |
| Devil's advocate | `/tp` two-lens (fresh subagent) | Costa & Kallick pattern |
| Double-loop learning | `/tp` problem framing, `/aar` Phase 4 | AAR captures meta-learning |

## The 9 missing categories (ranked by failure class caught)

### Tier 1: High-confidence gaps (would have caught documented failures)

**1. Reference-class forecasting (RCF) / Outside View.** Before committing
to a plan, grep the wiki for similar past decisions and surface their
resolved outcomes. Kahneman/Lovallo and Flyvbjerg credit this with curing
the planning fallacy. Our workspace's CooperBench overgeneralization and
the "6 workers" projection (this session) are both planning-fallacy
failures RCF would have caught. **Gap receipt:** `blind-spot-detection-
methods.md:130` explicitly flags this as the largest blind-spot gap.
**Implementation:** `/decide <proposal>` step that queries wiki + AAR
archive for similar decisions.

**2. External-validity audit on cited findings.** Before `/www` or
`/wiki` cites any study or benchmark, require a one-line check: "what
population was tested / what conditions held / which axes differ from my
context?" Peters & Chin-Yee (2025) found 26-73% overgeneralization rates
across 10 LLMs. **Gap receipt:** `assumption-auditing-and-unknown-unknown-
discovery.md:221` ranks this as highest-leverage missing technique.
**Implementation:** `/www` Phase 2 receipt must include
`external_validity_check: true`.

**3. Probabilistic calibration gate.** Before any confident claim, require
the model to state its evidence tier (FACT/INFERENCE/UNKNOWN) AND a
confidence 0-100 with base-rate anchor. Kadavath 2022 and Kaddour 2026
show calibration data materially reduces overconfidence; adversarial
framing reduces it by 15pp. **Gap receipt:** `assumption-auditing.md:159`.
**Implementation:** extend the existing evidence-tier labels in AGENTS.md
with a numeric confidence field.

**4. Second-order thinking in `/tp`.** For each recommendation, force
"first-order consequence → second-order → third-order → at which order
does it become negative?" Would have caught the exec-gate friction cascade
(block mutations → blocks all bash reads → user disables plugin).
**Gap receipt:** `mental-models-for-tp-and-brainstorming.md:128-138`
already designed the 4-question block but hasn't shipped it.
**Implementation:** add to `/tp` core domain 2 (~20 lines).

### Tier 2: Medium-confidence gaps (formal methods, proven elsewhere)

**5. Full ACH matrix (Analysis of Competing Hypotheses).** Force ≥3 design
alternatives AND evaluate each piece of evidence against each one, before
converging. Current `/why` Step 11a requires alternatives but not the
evidence × hypothesis matrix. **Gap receipt:** `blind-spot-detection-
methods.md:129`.

**6. FMEA (Failure Mode and Effects Analysis).** Systematic component-level
failure enumeration with severity × occurrence × detection scoring.
Handoff at `problem-prediction-skills-20260727/HANDOFF.md` covers the
full skill design. **Gap receipt:** `systematic-problem-anticipation.md:189`.

**7. Sensitivity analysis sweep.** For assumption-heavy recommendations,
require a one-page sweep naming which parameters the recommendation is
most sensitive to. Plan at `P:/tmp/sensitivity-sweep-plan.md`. **Gap
receipt:** `systematic-problem-anticipation.md:193`.

**8. Inversion as default `/plan` step.** "What would guarantee this
fails?" before any architectural commitment. Currently in `/skeptic`
references but not a default-fire step. **Gap receipt:**
`brainstorming-ideation-with-llms.md:70` says inversion is "highest-ROI
for LLMs" but doesn't fire by default.

**9. Hanlon's Razor + Chesterton's Fence in `/review`.** "Never attribute
to malice what a bug explains" + "before removing code, find out why it
was put there." In `/skeptic` references but not wired into `/review`'s
mechanical gates. **Gap receipt:** the deleted-then-broken-12-importers
incident in `cognitive-enforcement-patterns.md:236`.

## What we deliberately defer

**MCTS / LATS / ToT / formal verification (TLA+, Alloy, model checking).**
Research-grade; require reward functions, world models, or expert time.
Our decisions are low-frequency (a few per session) and reversible (git
history). MCTS shines in high-frequency, irreversible decisions.
**Defer receipt:** `systematic-problem-anticipation.md:198`.

## Receipts

- **"RCF is the largest blind-spot gap":** receipt —
  `blind-spot-detection-methods.md:130`: "The missing layer is reference
  class forecasting."
- **"external-validity audit is highest-leverage":** receipt —
  `assumption-auditing-and-unknown-unknown-discovery.md:221`.
- **"second-order thinking designed but not shipped":** receipt —
  `mental-models-for-tp-and-brainstorming.md:128-138`.
- **"MCTS deferred for our use case":** receipt —
  `systematic-problem-anticipation-methods-and-existing-tools.md:198`.
- **"cc-thinking-skills repo not directly readable":** receipt — the
  explore subagent (`019fa6da`) had no web fetch capability; analysis is
  cross-referenced from wiki concepts that cite the repo's URL.

## Falsifier

These 9 categories are unnecessary if:
- The existing 6 frameworks (pre-mortem, steelman, disconfirmation,
  adversarial, devil's advocate, double-loop) catch all relevant failure
  modes. **Testable:** track whether unresolved blind spots recur in AARs
  over the next 6 months. If they don't, the existing layer is sufficient.
- The Tier 2 formal methods (FMEA, ACH, sensitivity) are too heavyweight
  for our decision volume. **Testable:** implement one (FMEA is first),
  measure whether it catches failures the informal layer missed. If not,
  don't implement the rest.

## Sources

- `systematic-problem-anticipation-methods-and-existing-tools.md` — the
  FMEA/MCTS/LATS survey that identified the gaps
- `skill-step-receipts-checked-by-hooks.md` — Proof-or-Stop evidence that
  enforcement (not review) is the mechanism
- `blind-spot-detection-methods.md` — existing blind-spot coverage and
  the RCF gap
- `assumption-auditing-and-unknown-unknown-discovery.md` — the
  external-validity and calibration gaps
- `mental-models-for-tp-and-brainstorming.md` — the second-order thinking
  design (unshipped)
- `P:/docs/handoffs/problem-prediction-skills-20260727/HANDOFF.md` — the
  6 actionable items with implementation plans

## Auto-related

- [[systematic-problem-anticipation-methods-and-existing-tools]] — the survey this refines
- [[mental-models-for-tp-and-brainstorming]] — second-order thinking design lives here
- [[blind-spot-detection-methods]] — the RCF + ACH gaps are documented here
- [[skill-step-receipts-checked-by-hooks]] — enforcement is the mechanism (Proof-or-Stop)
- [[cognitive-enforcement-patterns-for-ai-coding-agents]] — pre-mortem protocol
