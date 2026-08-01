---
title: "Missing decision frameworks: cc-thinking-skills 28-framework classification + 9 gap categories"
created: 2026-07-28
source: session-019fa276 (/go evaluation of cc-thinking-skills + problem-prediction research synthesis)
tags: [decision-frameworks, mental-models, FMEA, reference-class-forecasting, calibration, second-order-thinking, ACH, sensitivity-analysis, inversion, skills-gap, cc-thinking-skills, second-order, probabilistic, opportunity-cost, theory-of-constraints, ooda, triz, via-negativa, lindy-effect]
summary: >
  Verified classification of all 28 frameworks from the cc-thinking-skills
  repo (github.com/tjboudreaux/cc-thinking-skills) against our workspace.
  14 already have equivalents. 8 are missing and worth porting (second-order
  thinking, probabilistic calibration, opportunity cost, theory of
  constraints, OODA, TRIZ, via negativa, Lindy effect). 4 are present but
  differently shaped. 2 are deferred. Plus 9 gap categories from the
  broader problem-prediction research (RCF, external-validity, FMEA, ACH,
  sensitivity analysis, inversion-as-default, Hanlon/Chesterton). Each
  missing framework has an implementation target skill and estimated lines.
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

## Verified classification: all 28 cc-thinking-skills frameworks

Source repo: [github.com/tjboudreaux/cc-thinking-skills](https://github.com/tjboudreaux/cc-thinking-skills)
(MIT license, 28 skills, replication-gated eval pipeline, zero skills hold
robust replicated ELEVATE verdict — treat as scaffolds, not proven accuracy
boosts).

### Already have (14)

| Framework | Our equivalent |
|---|---|
| `thinking-pre-mortem` | ✅ `/red-team`, `/tp` domain 3a, `/wargame` |
| `thinking-steel-manning` | ✅ `/tp` steelman + falsifier |
| `thinking-red-team` | ✅ `/red-team` (8 specialist lenses) |
| `thinking-first-principles` | ✅ `/design` Phase 0, brainstorming-ideation |
| `thinking-scientific-method` | ✅ `/why` hypothesis-differential (Step 6-7) |
| `thinking-five-whys-plus` | ✅ `/why` Ishikawa + 5-whys |
| `thinking-cynefin` | ✅ `/skeptic` references |
| `thinking-systems` | ✅ `/why` systems lens (dimension 3) |
| `thinking-socratic` | ✅ `/tp` questioning, `/refine` |
| `thinking-map-territory` | ✅ `/skeptic` references |
| `thinking-circle-of-competence` | ✅ AGENTS.md "operator already knows..." |
| `thinking-bounded-rationality` | ✅ `/wargame` (bounded info decisions) |
| `thinking-reversibility` | ✅ AGENTS.md reversibility scale (1.0-2.0) |
| `thinking-model-router` | ✅ `/go` profile auto-routing |

### Missing — worth porting (8)

| Framework | What it does | Why we need it | Implementation target |
|---|---|---|---|
| **`thinking-second-order`** | Think beyond immediate consequences: 1st → 2nd → 3rd order → when does it go negative? | Would have caught exec-gate cascade. Wiki designed the block but hasn't shipped it. | `/tp` core domain 2 (~20 lines) |
| **`thinking-probabilistic`** | Calibrated probability estimation with priors + Bayes | Evidence tiers lack numeric confidence. Kadavath 2022 shows calibration reduces overconfidence. | Evidence tier field (~15 lines) |
| **`thinking-opportunity-cost`** | Evaluate choices by what you give up | We don't systematically ask "what else could we do with this time/compute?" | `/tp` domain 5 (~10 lines) |
| **`thinking-theory-of-constraints`** | Find the ONE bottleneck limiting throughput | Export is the constraint, not clustering/synthesis. Would structure sensitivity sweep. | `/go` H1 Think or `/design` Phase 0 (~30 lines) |
| **`thinking-ooda`** | Observe-Orient-Decide-Act for dynamic situations | Applies to incident response, live-run decisions, auth-expiry handling. | `/why` or `/debugging-and-error-recovery` (~20 lines) |
| **`thinking-triz`** | Resolve technical contradictions (40 inventive principles) | Unique — "how to invent around a hard constraint." Applies to skill design (hook timeout vs evidence coverage). | Evaluate first; may be too specialized (~40 lines) |
| **`thinking-via-negativa`** | Improve by removing, not adding | Directly applicable to ceremony-tax problem. "What can we remove?" is structurally different from "what should we add?" | `/close` or `/skill-prune` (~15 lines) |
| **`thinking-lindy-effect`** | Older things likely to last longer | "Has this pattern persisted across 3+ sessions?" is a Lindy signal for skill retention. | `/skill-prune` or `/skill-dev` (~10 lines) |

### Present but differently shaped (4)

| Framework | Our version | Difference |
|---|---|---|
| `thinking-kepner-tregoe` | `/why` Step 6-11 | K-T is more structured (situation appraisal → problem analysis → decision analysis → potential problem analysis). Our `/why` is Ishikawa-first. |
| `thinking-thought-experiment` | `/wargame` | Wargame is plan-focused; thought-experiment is broader (architecture, edge cases, philosophy). |
| `thinking-margin-of-safety` | AGENTS.md reversibility scale + verification gates | Embedded in the verification system, not a standalone framework. |
| `thinking-jobs-to-be-done` | `/tp` domain 5 (solution-space broadening) | Close but not JTBD-framed. We don't systematically ask "what job is this skill hired to do?" |

### Evaluate but probably don't need (2)

| Framework | Why defer |
|---|---|
| `thinking-effectuation` | Startup/innovation focused ("start with means, not goals"). Our workspace is infrastructure, not product. |
| `thinking-model-combination` | Our `/red-team` already combines multiple lenses. A standalone meta-skill would compete. |

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
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
