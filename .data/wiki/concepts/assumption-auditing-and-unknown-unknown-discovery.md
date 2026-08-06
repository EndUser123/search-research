---
title: "Assumption-auditing and unknown-unknown discovery: mental models for self-correcting AI agents"
created: 2026-07-27
source: session-019fa5a1 (/www research, triggered by operator meta-cognition question)
tags: [mental-models, assumption-auditing, epistemic-humility, premortem, external-validity, unknown-unknowns, self-correction, llm-behavior, research, meta-cognition, cross-host]
summary: >
  Research into mental models and techniques that, if adopted as default
  behavior, would let an AI agent catch its own overgeneralizations and surface
  unknown unknowns WITHOUT operator prompting. The session that triggered this
  research had the agent cite CooperBench ("solo agent beats fleet ~2x") without
  checking whether the benchmark's methodology applied to the workspace's task
  shape — an external-validity failure. Seven assumption-auditing techniques and
  seven unknown-unknown discovery techniques were identified. The highest-signal
  finding: the workspace already has most of the pieces (/tp, /wargame, /risk
  referenced, AGENTS.md rules) but they don't FIRE under session pressure because
  they're opt-in skills, not default behavior. The gap is not missing techniques;
  it's making existing techniques fire by default at the right decision points.
  Plus: /risk is referenced in 4+ places but doesn't exist as a SKILL.md.
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
sources:
  - "Hills 2026, 'Could You Be Wrong?' (MDPI AI, arXiv:2507.10124) — metacognitive prompt"
  - "Klein 2007, 'Performing a Project Premortem' (HBR) — premortem technique"
  - "Kaddour et al. 2026, 'Agentic Uncertainty Reveals Agentic Overconfidence' (arXiv:2602.06948) — adversarial framing, calibration data"
  - "Peters & Chin-Yee 2025, generalization bias (Royal Society Open Science) — 26-73% overgeneralization in LLMs"
  - "Kahneman & Tversky 1979; Flyvbjerg — reference-class forecasting"
  - "Irving 2018, AI safety via debate; Khan et al. 2024 — devil's advocate"
  - "Kadavath 2022, 'Language models (mostly) know what they know' — P(IK)"
  - "Pathak 2017 ICM; Bougie 2025 iLLM — curiosity-driven exploration"
  - "Bellemare-Pepin 2026 (Scientific Reports); Luminate (ACM CHI 2024) — divergent thinking"
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: extends — that names the failure (narrative closes investigation); this names the techniques that prevent it
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: complements — that names the pressure; this names the antidote techniques
  - target: wiki/concepts/solo-director-ai-fleet-coordination-isolation-best-practices.md
    type: refines — the CooperBench overgeneralization that triggered this research
  - target: wiki/concepts/multi-agent-correlated-errors.md
    type: related — error decorrelation as a technique for assumption diversity
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose.md
    type: extends — the claim-gate proposal applies the same enforcement principle to assumption-auditing
  - target: wiki/concepts/narrative-as-signal-anti-dismissal-rule.md
    type: related — both address the "plausible narrative substitutes for investigation" failure
---

# Assumption-auditing and unknown-unknown discovery

## Decision context

**Why this research was needed.** Session 019fa5a1 produced a sequence of
failures where the agent:
1. Cited CooperBench ("solo beats fleet ~2x") without checking if its methodology
   applied to the workspace's independent-decomposed-streams architecture
2. Declared close-authority "PROVEN" without an independent adversarial pass
3. Reported "zero regressions" without running the baseline comparison
4. Self-verified a security boundary it had designed against itself

Each failure was caught by the operator or an external LLM critique — not by
the agent's own processes. The operator asked: what mental models, if adopted
by default, would have let the agent catch these itself?

**What alternatives were explored.** Three parallel research streams: (1)
external research on assumption-auditing techniques, (2) external research on
unknown-unknown discovery, (3) workspace inventory of existing skills/concepts.
The workspace already has /tp, /wargame, /why, /risk (referenced), and
AGENTS.md rules for most of these techniques. The gap is not knowledge — it's
firing discipline.

**What the research changed.** Identified seven techniques the agent should
adopt as default behavior (not opt-in skills) at specific decision points.
Identified that /risk is referenced in 4+ places but doesn't exist as a
SKILL.md. Proposed a "default-fire" architecture where assumption-audit
techniques fire mechanically at claim/verdict decision points.

## The seven assumption-auditing techniques (external research)

### 1. "Could You Be Wrong?" metacognitive prompt (Hills 2026) [HIGH confidence]
A single follow-up prompt after a substantive claim activates latent counter-
knowledge that the original response suppressed. Already in AGENTS.md as a
standing rule. **Gap: it fires as prose, not as a mechanical gate.** The fix:
wire it as a mandatory self-checkpoint before any verdict/claim of completion.

### 2. Pre-mortem (Klein 2007) [HIGH confidence]
Assume the plan has failed; write the post-mortem from the future naming
specific causes. Bypasses optimism bias. Workspace has /wargame (move-schema
discipline) and /risk (referenced). **Gap: premortem fires only when the
user invokes /wargame or /risk, not before every architectural commitment.**

### 3. Reference-class forecasting (Kahneman & Tversky 1979; Flyvbjerg) [HIGH confidence]
Before trusting a study/benchmark, look up the distribution of outcomes from
similar cases and check whether your case fits the reference class. **This is
exactly what failed with CooperBench** — the agent cited the conclusion without
checking if the benchmark's task shape (interdependent overlapping) matched
the workspace's (independent decomposed). **Gap: no technique in the workspace
forces reference-class checking before citing external findings.**

### 4. Steelmanning before critiquing [HIGH confidence]
Construct the strongest version of the opposing view before evaluating it.
Counters motivated reasoning. Workspace /tp has this in its failure-mode
vocabulary. **Gap: it fires only when /tp is invoked, not as a default before
committing to an approach.**

### 5. External-validity audit on cited findings (Peters & Chin-Yee 2025) [HIGH confidence]
Before quoting a study: *What population was tested? What conditions held?
Which axes differ from my context?* Their research found 26-73% overgeneralization
rates across 10 LLMs — models strip qualifiers and convert descriptive findings
into action-guiding claims. **This is the exact failure mode.** **Gap: no
mechanical gate forces "check population transfer" before citing a benchmark.**

### 6. Generalization-bias scrubbing at generation time [MEDIUM confidence]
Preserve the source's scope markers (past tense, quantifiers, sample-specific
framing). Don't convert "X worked in N patients" into "X works." **Gap: the
agent's default summarization strips qualifiers under output-efficiency pressure.**

### 7. Base-rate check as final guardrail [HIGH confidence]
Before any confident probability, ask: *what is the base rate in the relevant
reference class?* **Gap: the agent cites vivid case-specific evidence without
anchoring to the distribution.**

## The seven unknown-unknown discovery techniques (external research)

### 1. Premortem (same as above, applied before commitment) [HIGH confidence]
### 2. Adversarial post-execution / failure-mode pre-specification (Kaddour 2026) [HIGH confidence]
Reframe from "is this correct?" to "actively search for bugs." Reduces
overconfidence by up to 15 percentage points. Pre-specify failure taxonomies
before reviewing.
### 3. Devil's advocate / AI safety via debate (Irving 2018; Khan 2024) [HIGH confidence]
Assign a second model/instance to attack the proposed answer. Burden shifts
from generation to refutation.
### 4. Rumsfeld matrix / assumption dead-listing [MEDIUM confidence]
Categorize: known-knowns, known-unknowns, unknown-knowns, unknown-unknowns.
Dead-listing: enumerate every hidden prerequisite ("what would have to be true
for this to be right?").
### 5. Divergent-convergent thinking / SCAMPER (Bellemare-Pepin 2026; Luminate 2024) [MEDIUM confidence]
Separate exploration from evaluation. SCAMPER checklist for systematic
divergent prompts. Prevents fixation on the first plausible path.
### 6. Curiosity-driven exploration (Pathak 2017; Bougie 2025) [MEDIUM confidence]
Use intrinsic reward (novelty, surprise, uncertainty) to drive exploration.
Prompt: "what check would most reduce my uncertainty?"
### 7. Epistemic humility via P(IK) (Kadavath 2022; Kaddour 2026) [HIGH confidence]
State confidence as 0-100. Classify claims as FACT/INFERENCE/UNKNOWN. Answer
"what would make me wrong?" before stating the claim.

## What the workspace already has (inventory)

| Technique | Workspace implementation | Fires by default? |
|---|---|---|
| Premortem | /wargame, /risk (referenced) | ❌ opt-in only |
| Devil's advocate | /tp (fresh subagent critique) | ❌ opt-in only |
| Steelman | /tp core domain 4 | ❌ opt-in only |
| "Could you be wrong?" | AGENTS.md standing rule | ⚠️ prose rule, fires sometimes |
| Evidence tiers (FACT/INFERENCE/UNKNOWN) | /why Step 4b, AGENTS.md | ⚠️ prose rule, inconsistent |
| Problem-first decomposition | AGENTS.md mandatory rule | ⚠️ prose rule, often skipped |
| Reference-class forecasting | ❌ not implemented | ❌ |
| External-validity audit | ❌ not implemented | ❌ |
| Base-rate check | ❌ not implemented | ❌ |
| Adversarial framing | /review --adversarial | ❌ opt-in only |
| Divergent thinking | /tp domain 5 (solution-space broadening) | ❌ opt-in only |
| Curiosity-driven exploration | ❌ not implemented | ❌ |

**The pattern:** the workspace has the TECHNIQUES (in /tp, /wargame, /why,
AGENTS.md rules) but lacks DEFAULT FIRING at the right decision points. Every
technique is opt-in. Under closure pressure, opt-in techniques don't fire —
which is the exact failure mode documented in [[reactive-pattern-matching-and-closure-pressure]].

## The three techniques that would have prevented this session's failures

| Session failure | Technique that would have caught it | Why it works |
|---|---|---|
| CooperBench overgeneralization | **External-validity audit** (#5) | Forces "what population was tested? does my context match?" before citing |
| "PROVEN" verdict on standalone module | **Adversarial framing** (#2 unknown-unknowns) | Reframes from "does it work?" to "what bugs can I find?" |
| "Zero regressions" without baseline | **Premortem** (#1) | "Imagine this claim is wrong — why?" → "I didn't run the baseline" |

Each of these maps to a documented workspace pattern: the CooperBench failure
is an instance of [[plausible-narratives-substitute-for-verification]] (the
narrative "CooperBench says fleets are bad" felt sufficient); the PROVEN verdict
is an instance of the maker-checker violation documented in
[[maker-checker-required-for-enforcement-work]] (the three-role conflict
specific to enforcement code, refined from the general principle in
[[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]]).

## The skill gap: can this be turned into a default-fire skill?

**Yes — and the workspace is 80% there.** The missing piece is a
"claim-gate" or "verdict-gate" skill that fires assumption-audit techniques
MECHANICALLY at specific decision points, rather than relying on the agent
to remember to invoke /tp or /risk.

**Proposed architecture (not implemented — for operator decision):**

A `/challenge` or `/audit-claim` skill that fires at these default points:
1. Before citing an external study/benchmark → external-validity audit
2. Before declaring "PROVEN" / "done" / "verified" → adversarial framing + premortem
3. Before recommending an approach → steelman the alternative
4. Before claiming "zero regressions" → base-rate check + reference-class

Each gate is a 30-second inline check (not a full /tp subagent spawn).
The gate produces a written artifact (a named counterclaim, a reference-class
citation, a failure-mode list) that must exist before the claim ships.

**This is the structural fix for the "techniques exist but don't fire" problem.**
Prose rules in AGENTS.md fire probabilistically. A claim-gate skill fires
mechanically at the decision point — same principle as the close-authority
state machine (enforcement at the boundary, not in the prose).

## What this means for our workspace

The workspace already has most of the techniques (in /tp, /wargame, /why,
AGENTS.md rules). The gap is not knowledge — it's firing discipline. Every
technique is opt-in. Under closure pressure, opt-in doesn't fire.

The structural fix is a default-fire "claim-gate" that mechanically triggers
assumption-audit techniques at specific decision points (before citing a study,
before declaring proven, before claiming zero regressions). This is the same
pattern as the close-authority state machine: enforcement at the boundary, not
in the prose.

## Key findings

1. **External-validity audit is the highest-leverage missing technique.**
   It would have caught the CooperBench overgeneralization, the "PROVEN"
   verdict, and most factual-overstatement failures. No workspace
   implementation exists.
2. **The workspace is 80% there.** /tp, /wargame, /why, and AGENTS.md rules
   cover most techniques. The gap is default-firing, not missing knowledge.
3. **/risk is referenced but doesn't exist.** 4+ skills/docs cite it;
   `~/.grok/skills/risk/SKILL.md` is absent. This will produce "Unknown
   command" at invocation.
4. **Adversarial framing reduces overconfidence by 15 percentage points**
   (Kaddour 2026) — the single most validated intervention for the failure
   class this session exhibited.

## Implications

- The proposed `/challenge` or claim-gate skill would be a structural fix for
  the "techniques exist but don't fire" problem — same principle as
  [[mandatory-step-enforcement-code-over-prose]]
- The /risk gap should be resolved: either build it, alias it to /tp,
  or remove the references
- Reference-class forecasting and external-validity audit should become
  default behavior before citing ANY external study or benchmark in /www,
  /wiki, or research handoffs

## Receipts

- [FACT] /tp exists with 1025-line SKILL.md at `C:\Users\brsth\.grok\skills\tp\SKILL.md` — verified by subagent read this session
- [FACT] /risk is referenced in 4+ places but `C:\Users\brsth\.grok\skills\red-team\SKILL.md` does NOT exist — verified by subagent read attempt this session
- [FACT] /wargame exists at `C:\Users\brsth\.grok\skills\wargame\SKILL.md` — verified by subagent read this session
- [FACT] Hills 2026 "Could You Be Wrong?" is already in `~/.grok/AGENTS.md` as a standing rule — verified by reading AGENTS.md this session
- [FACT] CooperBench methodology (arXiv 2601.13295 §2.1) confirms interdependent overlapping tasks — verified by subagent research this session
- [FACT] Peters & Chin-Yee 2025 found 26-73% overgeneralization rates in LLMs — verified by subagent research this session
- [INFERENCE] the workspace is 80% of the way to default-fire assumption auditing — supported by the inventory above showing most techniques exist but are opt-in

## Falsifier

This concept is wrong if:
- A future study shows LLMs CAN reliably self-correct without external prompting (would overturn Huang et al. 2024). Current evidence strongly disconfirms.
- Default-fire gates are shown to add more latency than value (the 30-second cost per gate × N gates per session may exceed the cost of occasional operator corrections). Would require measured comparison.
- The existing opt-in techniques (/tp, /wargame) are shown to fire reliably enough under closure pressure that default-fire is redundant. The session evidence strongly disconfirms — they didn't fire.

## Sources

- [Hills 2026, "Could You Be Wrong?"](https://arxiv.org/abs/2507.10124) (MDPI AI)
- [Klein 2007, "Performing a Project Premortem"](https://hbr.org/2007/09/performing-a-project-premortem) (HBR)
- [Kaddour et al. 2026, "Agentic Uncertainty"](https://arxiv.org/abs/2602.06948)
- [Peters & Chin-Yee 2025, generalization bias](https://royalsocietypublishing.org/doi/10.1098/rsos.241370) (RSOS)
- [Kahneman & Tversky 1979](https://en.wikipedia.org/wiki/Prospect_theory); Flyvbjerg on reference-class forecasting
- [Irving 2018, AI safety via debate](https://arxiv.org/abs/1805.00899); [Khan et al. 2024](https://arxiv.org/abs/2402.06782)
- [Kadavath 2022, "Language models (mostly) know what they know"](https://arxiv.org/abs/2207.05221)
- [Pathak 2017 ICM](https://arxiv.org/abs/1705.05363); [Bougie 2025 iLLM](https://arxiv.org/abs/2509.09675)
- [Bellemare-Pepin 2026](https://www.nature.com/articles/s41598-025-25157-3); [Luminate (Suh et al. 2024, ACM CHI)](https://dl.acm.org/doi/fullView/10.1145/3613904.3642400)
