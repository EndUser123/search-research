---
title: "LLM councils and model fusion (MoA, OpenRouter, Karpathy)"
created: 2026-07-21
source: session-2026-07-21
tags: [council, fusion, moa, multi-agent, openrouter, ensemble, design, red-team, latency]
summary: >
  Three related patterns: (1) Mixture-of-Agents layered proposer/aggregator
  (Together 2024 paper), (2) OpenRouter Fusion panel+judge product (2026), (3)
  Karpathy-style LLM Council peer-review + chairman. All trade latency/cost for
  quality on hard async work. Weak diversity (same family, same brief) underperforms;
  fusion is not a default coding path.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/multi-agent-correlated-errors
    type: refines
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: related
  - target: wiki/concepts/gemini-google-api-models-2026-07
    type: related
---

# LLM councils and model fusion

## One-line stance

**Panel of models → structured synthesis (judge/chairman)** beats a single call on
deep research / hard reasoning **when** members are diverse and latency is acceptable.
It is a **tool for hard questions**, not a replacement for a fast coding model.

## Pattern family (three names, same skeleton)

| Name | Origin | Structure | Distinctive claim |
|------|--------|-----------|-------------------|
| **Mixture-of-Agents (MoA)** | Wang et al., Together AI, arXiv:2406.04692 (2024) | Layers of agents; each layer sees prior layer outputs; proposers + aggregators | Open-source MoA beat GPT-4o on AlpacaEval 2.0 (65.1% vs 57.5% LC win); aggregator ≠ pure ranker |
| **OpenRouter Fusion** | OpenRouter product, 2026-04+; blog 2026-06-12 | Parallel panel + judge analysis (consensus, contradictions, blind spots) + final synthesis | On DRACO deep-research: budget panel (Gemini 3 Flash + Kimi K2.6 + DeepSeek V4 Pro) ≈ Fable 5 at ~50% cost; frontier fusion can exceed solo Fable |
| **LLM Council** | Karpathy-inspired community pattern | Multiple models answer → anonymized peer critique/rank → chairman synthesizes | Governance / deliberative framing; voting variants report accuracy lifts in some repos |

All three are **ensembles at inference time** (no weight merge). Do not confuse with
**model merging** (SLERP/TIES of checkpoints) — some 2026 blogs blur “fusion” with merge.

## MoA (research core) — what actually matters

From arXiv:2406.04692 and secondary surveys:

1. **Collaborativeness:** models improve when they see others’ answers, even if those answers are weaker than self-solo.
2. **Proposer vs aggregator specialization:** not every model is good at both. WizardLM-class proposers; Qwen/GPT-class aggregators in the paper’s setups.
3. **Width helps more than pure ranking:** multi-proposer diversity > same model best-of-N at fixed temperature; aggregator synthesizes rather than only picks.
4. **Cost knobs:** fewer layers (MoA-Lite) trades quality for spend; first aggregation often captures most gain.
5. **Latency is structural:** wait for slowest panel member × layers, then aggregate.

**Do:** use cross-family proposers + a strong aggregator.  
**Don't:** assume N persona prompts on one model equals MoA.

## OpenRouter Fusion (productized MoA)

Authority: [Surpassing Frontier Performance with Fusion](https://openrouter.ai/blog/announcements/fusion-beats-frontier/) (2026-06-12).

### Pipeline

1. Dispatch prompt to **panel** in parallel (often with web_search / web_fetch / bash server tools).
2. **Judge** produces structured analysis: consensus, contradictions, partial coverage, unique insights, blind spots.
3. **Calling / synthesizer model** writes final answer grounded in that analysis.

### Reported DRACO results (OpenRouter’s run; relative ranking more reliable than absolute)

| Config | Score (their run) |
|--------|-------------------|
| Fable 5 + GPT-5.5 → Opus 4.8 judge | **69.0%** |
| Opus + GPT-5.5 + Gemini 3.1 Pro → Opus | 68.3% |
| Solo Fable 5 | 65.3%* |
| Budget: Gemini 3 Flash + Kimi K2.6 + DeepSeek V4 Pro → Opus | **64.7%** (~50% cost of Fable-class) |
| Solo DeepSeek V4 Pro / GPT-5.5 / Opus 4.8 | ~59–60% |
| Solo Gemini 3 Flash | 43.1% |

\* Fable completed 93/100 tasks (content filter); comparison uneven.

### Operational claims that transfer

- **Self-fusion helps:** Opus+Opus with Opus synthesizer beat solo Opus (~+6.7 pts) → synthesis + second sampling path matters, not only architecture diversity.
- **Not a Fable drop-in:** DRACO ≠ long-horizon agent work where single frontier models still win.
- **Coding:** use Fusion as a **server tool** the coding model invokes for architecture/research questions — not as the default token path for every edit.
- **Latency:** Fusion path often **2–3×** a normal call when invoked.
- **Eval hygiene:** panel with search can contaminate benchmarks; exclude rubric domains.

API shapes (docs-linked from blog): model slug `openrouter/fusion`, plugin `id: fusion` with `analysis_models`, or tool type `openrouter:fusion`.

## LLM Council (Karpathy lineage)

Community pattern (github/andybhall/llm-council-governance, writeups 2025–2026):

1. Query N models independently.  
2. Anonymized peer review / ranking of each other’s answers.  
3. **Chairman** model synthesizes.

Variants add **voting** for classification/judge tasks (reported +pp accuracy in some governance experiments — treat as domain-specific until replicated on your tasks).

**Relation to this fleet:** `cc-council` is the in-repo council: multi-model stage + synthesizer; personas exist but architecture doc emphasizes **cross-model** not persona theater. See [[multi-agent-correlated-errors]].

## Do's and don'ts (fleet-facing)

### Do

- Use panel+judge when the artifact is **expensive to reverse** (design, ADR, red-team verdict, deep research).
- Prefer **cross-family** panel members (e.g. Gemini Flash + DeepSeek + Kimi + local code model) over three clones of the same API.
- Give the **judge an explicit rubric**: consensus / contradiction / blind spot / unique insight (Fusion’s structure).
- Cap width: 2–3 proposers + 1 judge is usually enough; MoA paper’s first aggregation captures most lift.
- Keep **single-model path** for latency-sensitive code/test/discover.

### Don't

- Default `/go` implement waves to Fusion (latency tax without quality need).
- Confuse **persona diversity** with **error decorrelation** ([[multi-agent-correlated-errors]]).
- Trust LLM-as-judge **tiny margins** (~3 pts) as signal.
- Equate Fusion with **weight merging** or with “always better than the best panel member.”
- Put Fusion on the interactive streaming UX path without UX for multi-minute waits.

## Where it maps on this host

| Skill / system | Fit | How |
|----------------|-----|-----|
| `/design` | **High** | Optional panel+judge before sealing design doc |
| `/red-team` | **High** | Already specialists → critic; add cross-family panel for B-class |
| `/review --second-opinion` | **High** | External critics already; formalize Fusion judge fields |
| `/debrief --deep` | **Medium** | Multi-lens + critic is thin MoA |
| `/wargame`, `/plan` (hard reverse) | **Medium** | Opt-in |
| `/tp` full | **Medium** | Two-lens is mini-council |
| `/go` default waves | **Low** | Lane escalate only; no Fusion |
| OpenRouter `openrouter/fusion` | **Product option** | If OR key present; not required for local MoA via `spawn_subagent` |

DIY MoA without OpenRouter: parallel `spawn_subagent(model=…)` × N diverse slugs → parent or dedicated judge slug synthesizes with Fusion-style sections. Failures still go through [[model-picker-as-failover-not-router]].

## Conflicts / caveats

- **⚠️ Absolute DRACO scores** depend on judge model (paper notes 10–25 pt shifts). Use **relative** ranking within one eval setup.
- **⚠️ Marketing blogs** (MindStudio, Tecadrise, etc.) restate OpenRouter claims; cite OpenRouter primary + arXiv for load-bearing numbers.
- **⚠️ Solo Gemini Flash ~43% on their DRACO** while budget **panel** including Flash reaches ~65% — diversity + synthesis, not “Flash alone is frontier.”

## Relationship to existing concepts

- **Refines** [[multi-agent-correlated-errors]]: names MoA/Fusion/Council as productized instances of uncorrelated-error ensembles; reiterates frame diversity + falsifiers.
- **Related** [[model-picker-as-failover-not-router]]: Fusion is recommendation + product path, not a second silent router inside every skill.
- **Related** [[gemini-google-api-models-2026-07]]: Gemini 3 Flash is a common **budget panel** member in OpenRouter’s published configs.

## Sources

- https://arxiv.org/abs/2406.04692 — Mixture-of-Agents (Wang et al., 2024)
- https://github.com/togethercomputer/moa — reference MoA code
- https://openrouter.ai/blog/announcements/fusion-beats-frontier/ (2026-06-12)
- https://openrouter.ai/docs/guides/features/server-tools/fusion (linked from blog)
- https://arxiv.org/abs/2602.11685 — DRACO (Perplexity; cited by OpenRouter)
- Karpathy LLM Council lineage: https://github.com/andybhall/llm-council-governance ; https://starlog.is/articles/llm-engineering/karpathy-llm-council/
- Survey mention MoA: arXiv HTML “LLMs Working in Harmony” (2504.01963)

## Staleness

Product Fusion benchmarks and Gemini IDs churn. Re-check OpenRouter blog + Gemini models page if >6 months old. MoA *architecture* paper is evergreen as a method reference.

## Auto-related

- [[plan-then-execute-pattern]]
- [[exemption-logic-as-conflict-signal]]
- [[multi-agent-correlated-errors]]
- [[pi-agent-harness]]
- [[llm-handoff-best-practices]]

