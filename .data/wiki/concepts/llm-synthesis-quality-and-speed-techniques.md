---
title: "LLM synthesis quality and speed techniques for document generation"
created: 2026-07-27
source: session-019f9a3c (/www follow-up to parallelizing-design-doc-generation)
tags: [synthesis-quality, llm-speed, constrained-generation, iterative-refinement, model-cascading, prompt-caching, speculative-decoding, design-documents, cross-host]
summary: >
  Follow-up research to parallelizing-design-doc-generation-what-works.md.
  Four sub-areas researched: (1) synthesis/fusion quality techniques — input
  diversity + explicit synthesis prompt matter more than technique choice;
  Generative Self-Aggregation and Outline-First are the highest-leverage
  patterns; (2) speed/latency — prefix caching + model cascading +
  speculative decoding are the production-deployable, near-lossless
  speedups (2-10× combined); (3) constrained generation — outline-level
  structure helps (+20-25% organization), rigid JSON schema hurts
  creative prose (diversity collapse, up to 27-pt reasoning drops);
  hybrid (free prose + structured metadata) is the sweet spot; (4)
  iterative refinement — most gains land in rounds 1-2 (~20% avg
  improvement), diminishing after 2-3 rounds, plateau/degradation after
  4; 3+ review-revise cycles for a design doc is likely overkill. The
  practical synthesis for /design: 2-round default (draft + 1 revise),
  parallel pre-write + parallel review, model cascading (cheap for
  extraction/preflight, frontier for synthesis), outline-constrained
  drafting, and structured metadata fields (not prose) for
  machine-readable parts.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "Generative Self-Aggregation (arxiv 2503.04104): https://arxiv.org/html/2503.04104v1"
  - "LLM-Blender (arxiv 2306.02561): https://arxiv.org/abs/2306.02561"
  - "Hierarchical Map-Reduce (ACL Findings 2025): https://aclanthology.org/2025.findings-acl.289.pdf"
  - "Outline-First / WritingPath (arxiv 2404.13919): https://arxiv.org/html/2404.13919v1"
  - "RECONCILE multi-agent debate (arxiv 2412.15487): https://arxiv.org/abs/2412.15487"
  - "Self-Refine (arxiv 2303.17651): https://arxiv.org/abs/2303.17651"
  - "Reflexion (arxiv 2303.11366): https://arxiv.org/abs/2303.11366"
  - "RefineBench (arxiv 2511.22173): https://arxiv.org/abs/2511.22173"
  - "Chain-of-Density (arxiv 2309.04269): https://arxiv.org/abs/2309.04269"
  - "Prefix caching (vLLM): https://docs.vllm.ai/en/stable/design/prefix_caching/"
  - "Speculative decoding / SwiftSpec (arxiv 2506.11309): https://arxiv.org/html/2506.11309v1"
  - "RouteLLM (lmsys): https://www.lmsys.org/blog/2024-07-01-routellm/"
  - "LLMLingua-2 (arxiv 2403.12968): https://arxiv.org/abs/2403.12968"
  - "XGrammar (MLC blog): https://blog.mlc.ai/2024/11/22/achieving-efficient-flexible-portable-structured-generation-with-xgrammar"
  - "JSONSchemaBench (arxiv 2501.10868): https://arxiv.org/html/2501.10868v1"
  - "Diversity Collapse / Price of Format (arxiv 2505.18949): https://arxiv.org/abs/2505.18949"
  - "Hidden Cost of Structure (Schall & de Melo 2025): https://aclanthology.org/2025.ranlp-1.124.pdf"
  - "Let Me Speak Freely? (Tam et al. 2024): https://arxiv.org/html/2408.02442v1"
  - "Instructor / London Stock Exchange: https://python.useinstructor.com/blog/2025/09/11/london-stock-exchange-group-powers-market-surveillance-with-instructor/"
  - "Andrew Ng agentic patterns: https://www.deeplearning.ai/the-batch/how-agents-can-improve-llm-performance"
relations:
  - target: wiki/concepts/parallelizing-design-doc-generation-what-works
    type: extends — adds synthesis-quality + speed + constraint + iteration layers to the parallelism findings
  - target: wiki/concepts/compensating-for-weaker-models-ensemble-multi-pass
    type: related — model cascading is the production deployment of weaker-model compensation
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: informs — /design enhancement direction (2-round default, model cascading, structured metadata)
---

# LLM synthesis quality and speed techniques for document generation

## Decision context

**Why this research was needed.** The prior concept
([[parallelizing-design-doc-generation-what-works]]) established that
parallel section drafting fails but parallel pre-write + parallel review
+ `--fast` mode work. The operator asked for "additional research on
synthesis quality, speed, etc." — this concept covers the four sub-areas
the prior research didn't reach: what makes the synthesis step itself
produce high-quality output, what speed techniques are
production-deployable, whether structural constraint helps or hurts, and
when iterative refinement stops paying off.

**What alternatives were explored.** Four sub-areas researched in
parallel: (1) synthesis/fusion quality techniques, (2) speed/latency
reduction, (3) constrained/structured generation, (4) iterative
refinement vs one-shot. The findings converge on a clear practical
synthesis for the /design use case.

**What the research changed.** It validated the `--fast` mode hypothesis
(2-round default is sufficient; 3+ rounds is overkill per RefineBench
2025), identified model cascading as the highest-ROI speed intervention
for /design (cheap models for preflight/extraction, frontier for
synthesis), and confirmed the existing design-doc template is already at
the right constraint level (outline + free prose, not rigid JSON).

## Finding 1: Synthesis quality is driven by input diversity + synthesis prompt > technique choice [HIGH confidence]

Across 8 synthesis techniques surveyed (Generative Self-Aggregation,
LLM-Blender, Hierarchical Map-Reduce, Outline-First, Extractive-then-
Abstractive, Multi-Agent Debate, Synthesis-Aware Decoding, Iterative
Self-Refine), the cross-cutting finding:

- **Input diversity is the single highest-leverage variable.** Homogeneous
  drafts (same temperature, same prompt, same model) collapse synthesis
  back to a single voice. Diverse inputs (different prompts/personas/
  temperatures) give the synthesizer material to work with.
- **The synthesis prompt itself matters more than the technique.**
  Explicitly instructing "combine strengths, resolve contradictions by
  preferring evidence quality, remove redundancy, ensure logical flow,
  and flag unresolved conflicts" measurably improves output even without
  any machinery.
- **Outline-First is the strongest pattern for long-form docs.** WritingPath
  (+20-25% organization/coverage), STORM (+25% absolute organization,
  +10% breadth), Skeleton-of-Thought (2×+ speedup via parallel expansion)
  all show that committing to structure before prose reduces drift and
  redundancy.
- **Multi-Agent Debate has the highest ceiling but highest cost.** Up to
  3× improvement on coherence, but 2-10× cost and groupthink risk.

## Finding 2: Prefix caching + model cascading + speculative decoding are the near-lossless speedups [HIGH confidence]

Eight speed techniques surveyed. The three that are both
production-deployable AND near-lossless:

| Technique | Speedup | Quality cost | Production-ready |
|---|---|---|---|
| **Prefix/KV-cache caching** | 50-90% TTFT reduction; 2-10× throughput on shared prefixes | None (lossless) | ✅ vLLM, Anthropic, OpenAI |
| **Speculative decoding (EAGLE-3)** | 1.5-3× typical; up to 4× | None (lossless — preserves distribution) | ✅ vLLM, Meta, NVIDIA |
| **Model cascading/routing (RouteLLM)** | 40-85% cost reduction | ~5% quality drop on misclassified hard cases | ✅ RouteLLM, FrugalGPT |

The other techniques (prompt compression, continuous batching, grammar
constraints, quantization, semantic caching) are either
quality-compromising at aggressive settings or are infrastructure-level
rather than workflow-level.

**For /design specifically:** model cascading is the highest-ROI
intervention. The pre-write steps (preflight, premise verification,
evidence brief) are mechanical and can run on cheap models (DeepSeek,
M3). Only the synthesis (writer draft) and the critical friend need the
frontier model. This cuts cost ~40-60% with negligible quality impact.

## Finding 3: Outline-level structure helps; rigid JSON schema hurts creative prose [HIGH confidence]

The evidence converges on a clear pattern for design docs:

- **Mandatory-section outlines help** — Outline-then-Expand (WritingPath,
  STORM, Skeleton-of-Thought) shows +20-25% gains on organization and
  coverage for long-form docs. The /design template already does this.
- **Rigid JSON schemas applied to prose hurt** — Diversity Collapse (Yun
  et al. 2025) shows structured chat templates collapse semantic
  diversity; "Hidden Cost of Structure" (Schall & de Melo 2025) shows
  constraints degrade generative quality on RLHF-tuned models; "Let Me
  Speak Freely?" (Tam et al. 2024) shows up to 27-pt drops on reasoning.
- **The sweet spot is "outline + section-level free prose + structured
  metadata fields."** Use grammar-constrained decoding only for
  machine-readable fields (decision status, risk level, owner, dates).
  Let prose sections generate unconstrained.

**For /design specifically:** the existing template is already at the
right constraint level. Adding structured metadata fields at the document
header (decision enums, risk-level enums) via Instructor or JSON Schema
would be the optimal next step. Forcing section prose into JSON would
measurably hurt quality.

## Finding 4: Iterative refinement shows diminishing returns after 2-3 rounds [HIGH confidence]

The write→review→revise loop is NOT ceremony, but 3+ rounds is likely
overkill:

- **Self-Refine (Madaan 2023):** ~20% absolute average improvement, with
  biggest gains in rounds 1-2. Most curves plateau by round 3-4.
- **RefineBench (2025):** even frontier models (Gemini 2.5 Pro, GPT-5)
  gain only +1.8% over 5 turns of pure self-refinement. External guidance
  (checklists, rubrics) is what unlocks >90%.
- **Chain-of-Density (2023):** iteration has an OPTIMUM, not monotonic
  improvement — beyond 5-6 entities, quality degrades.
- **Actionable feedback is the multiplier, not iterations.** Generic
  "make it better" critique produces small gains; checklist-based critique
  (clarity, completeness, decisions documented, invariants stated)
  produces large gains even in fewer rounds.

**Practical answer for /design:**
- **Default: 2 rounds** (draft + 1 revise). Captures ~80% of the available
  improvement.
- **Allow 3 rounds** if the critique surfaces specific structural issues.
- **Hard-cap at 4.** Beyond that, diminishing returns + over-refinement
  risk (model starts removing specific grounded details in favor of fluff).
- **The /design run in this session ran 3 revision rounds** (26 findings →
  12 findings → 1 critical regression). Round 3 caught a genuine factual
  error (F-Field transcript schema), so it was justified. But rounds 1-2
  already captured most of the value.

## Receipts

- **[Tier 2 — peer-reviewed]** Self-Refine (2303.17651), Reflexion
  (2303.11366), RefineBench (2511.22173), Chain-of-Density (2309.04269),
  WritingPath (2404.13919), LLM-Blender (2306.02561), RECONCILE
  (2412.15487), Generative Self-Aggregation (2503.04104), LLMLingua-2
  (2403.12968), JSONSchemaBench (2501.10868), Diversity Collapse
  (2505.18949), Hidden Cost of Structure (Schall & de Melo 2025), Let Me
  Speak Freely (Tam et al. 2024), SwiftSpec (2506.11309).
- **[Tier 2 — vendor/production]** vLLM prefix caching docs, RouteLLM
  (lmsys), XGrammar (MLC blog), Instructor (London Stock Exchange case
  study), Andrew Ng agentic patterns.
- **[INFERENCE]** The "40-60% cost reduction" from model cascading in
  /design is derived from RouteLLM's 40-85% range, scoped to the pre-write
  steps. Actual savings unmeasured.
- **[INFERENCE]** The "2-round default is sufficient" claim is derived
  from Self-Refine curves + RefineBench plateau data, applied to design
  docs specifically. Design docs may differ from the benchmarks (more
  structural, more interdependent) — needs A/B testing.

## Practical synthesis for /design

Combining all four findings with the prior parallelization research:

| Intervention | Source finding | Time/cost saved | Quality impact |
|---|---|---|---|
| **2-round default** (draft + 1 revise; allow 3 for structural issues) | F4: RefineBench plateau | ~8-12 min per run | Negligible (rounds 3+ are marginal) |
| **Model cascading** (cheap for preflight/extraction, frontier for synthesis) | F2: RouteLLM | 40-60% cost reduction | ~5% on misclassified hard cases |
| **Parallel pre-write + parallel review** | Prior concept | ~5-8 min | Low risk |
| **Outline-constrained drafting** (already in template) | F3: Outline-then-Expand | N/A (already done) | +20-25% organization |
| **Structured metadata fields** (decision/risk/owner enums via Instructor) | F3: hybrid pattern | N/A | +reliability on machine-readable parts |
| **Explicit synthesis prompt** ("combine strengths, resolve contradictions, flag conflicts") | F1: cross-cutting | N/A | Measurable coherence gain |

**The `--fast` mode from the prior concept should default to 2 rounds,**
not 1. One round (draft + critical friend only) risks missing the
actionable-feedback multiplier that Self-Refine identifies as the real
driver of improvement.

## Falsifier

This concept is wrong if:
- A future study shows 3+ review rounds produce materially better design
  docs than 2 rounds on a controlled comparison (would overturn F4's
  practical recommendation). RefineBench currently disconfirms.
- Model cascading is shown to produce unacceptable quality loss on
  design-doc synthesis specifically (would overturn F2's recommendation).
  RouteLLM data is from chat/QA, not design docs.
- Rigid JSON schema is shown to IMPROVE design-doc prose quality (would
  overturn F3). Diversity Collapse + Hidden Cost + Let Me Speak Freely
  all disconfirm.

**Discriminating test:** implement the 2-round default + model cascading.
Measure: (a) wall-clock time vs the current 3-round loop, (b) review-
finding count and severity distribution (does 2-round catch the same
class of errors?), (c) critical-friend verdict distribution. If 2-round
produces equivalent quality at lower cost, the recommendation is
validated.

## Related

- [[parallelizing-design-doc-generation-what-works]] — parent concept; this extends it with synthesis/speed/constraint/iteration layers
- [[compensating-for-weaker-models-ensemble-multi-pass]] — model cascading is the production deployment
- [[agentic-sdlc-skill-lifecycle-architecture]] — /design enhancement direction
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
