---
title: "Detecting LLM uncertainty and hedging: research landscape for hook design"
created: 2026-08-05
source: session-20260805-www
tags: [uncertainty, hedging, calibration, hook-design, llm-output-validation, research-synthesis]
summary: >
  Comprehensive research synthesis on detecting when an LLM is uncertain, hedging,
  or guessing in its output. Covers confidence calibration research, hedge word
  taxonomies from NLP, production guardrail tools, self-monitoring approaches,
  failure modes, and uncertainty-triggered research (Self-RAG, CRAG, FLARE).
  Designed to inform a hook that detects hedging adjacent to factual claims and
  surfaces /www as a verification suggestion.
agent: grok
host: grok
cognitive_load: 4
verification: researched
relations:
  - target: wiki/concepts/claims-require-receipts.md
    type: extends
  - target: wiki/concepts/self-reflection-in-llms-fails-without-external-evidence.md
    type: extends
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation.md
    type: refines
  - target: wiki/concepts/llm-sycophancy-calibration-failure-research-2026.md
    type: refines
---

# Detecting LLM uncertainty and hedging: research landscape

## Decision context

We want to build a hook that detects when an LLM's output contains hedging
language adjacent to factual claims ("maybe 5 RPM," "probably because X"),
and surfaces `/www` as a verification suggestion. This concept captures the
full research landscape to inform that design decision.

## Finding 1: Hedge word detection is a mature NLP task with established taxonomies

**The Prince et al. (1982) taxonomy** is the foundational framework, still
used in CoNLL-2010 and BioScope corpora:

- **Approximators** (modify propositional content): "about," "approximately,"
  "roughly," "somewhat," "sort of"
- **Plausibility shields** (speaker's own uncertainty): "I think," "probably,"
  "maybe," "perhaps," "seem," "appear," "I guess"
- **Attribution shields** (deflect to others): "according to X," "reportedly,"
  "it is said that"

**CoNLL-2010 Shared Task** benchmarked hedge detection on Wikipedia and
biomedical text. Best systems achieved >85 F1 on biomedical data, ~67 F1 on
Wikipedia (harder due to informal text). Detection approaches evolved from
lexicon+rules → CRF/SVM → BERT/SciBERT fine-tuning.

**For our use case:** a regex-based approach using the Prince taxonomy is
feasible for a first version. The key insight from the research: hedge
words alone are insufficient — **context matters**. "Maybe we should try X"
(exploratory) vs "X is maybe 5 RPM" (unstated inference) requires
disambiguation. The literature uses syntactic patterns and POS tags for
this; we'd use adjacency to factual claims.

## Finding 2: Verbalized confidence is overconfident and prompt-sensitive

**Core finding across 2024-2025 research:**

- LLMs that verbalize confidence ("I'm 80% sure") show **positive but
  imperfect correlation with accuracy** — typically overconfident,
  especially in the 70-100% range
- Models frequently report near-100% confidence on **wrong** answers
- Calibration depends heavily on **how** you ask (prompt method matters
  more than model size)
- RLHF amplifies overconfidence (models learn that decisive answers are preferred)

**Key papers:**
- Yang et al. (2024, arXiv:2412.14737): "On Verbalized Confidence Scores" —
  reliability depends on prompt design, not just model capability
- Pawitan & Holmes (2025, HDSR): confidence only partially explained by
  token probabilities; LLMs lack coherent internal uncertainty sense
- ConfTuner (Li et al., NeurIPS 2025): fine-tuning with tokenized Brier
  score improves calibration up to 55%
- DiNCo (Wang & Stengel-Eskin, 2025): self-distractor normalization reduces
  overconfidence saturation

**Implication for our hook:** we cannot rely on the model's own confidence
labels (`[INFERENCE]` vs `[FACT]`) alone — the model doesn't know when it's
inferring. External lexical detection catches what self-labeling misses.
This validates our approach: pattern-matching on hedging language is a
**complementary** signal to self-applied epistemic labels.

## Finding 3: Self-monitoring/self-evaluation works for some tasks, fails for subtle errors

**What works:**
- **Semantic entropy / self-consistency**: sample multiple responses, cluster
  by meaning, measure disagreement. High disagreement = low confidence.
  Works well for black-box (API-only) settings.
- **P(True)** (Kadavath et al., 2022): generate answer, then ask "Is this
  true?" — works better when showing multiple samples first. Larger models
  improve at this.
- **Training for explicit uncertainty**: fine-tuning models to emit
  `<uncertain>` markers or calibrated confidence scores reduces
  overconfident errors and can trigger RAG/abstention.

**What fails:**
- **Subtle/complex errors**: self-evaluation struggles with instruction-following
  nuances, multi-claim generations, professional knowledge
- **Consistent wrongness**: if the model consistently produces the same wrong
  answer, self-consistency shows high agreement (false confidence)
- **Self-preference bias**: models prefer their own outputs
- **Cost**: multi-sample methods are 5-10x more expensive

**Implication:** self-monitoring is insufficient alone. The research
consensus is to layer: lexical detection (cheap, fast) → semantic entropy
(expensive, accurate) → human review (final fallback). Our hook is the
first layer.

## Finding 4: Uncertainty-triggered research is well-established prior art

Three foundational systems implement exactly the pattern we're considering:

- **Self-RAG** (Asai et al., 2023): model trained to self-assess whether
  retrieval is needed, then retrieves and critiques retrieved passages.
  Uses "reflection tokens" to decide retrieve/no-retrieve/verify.
- **FLARE** (Jiang et al., 2023): actively retrieves during generation when
  low-confidence tokens appear. Predicts upcoming content; if confidence
  drops, triggers retrieval.
- **CRAG** (Yan et al., 2024): retrieval evaluator scores document quality
  as Correct/Incorrect/Ambiguous. Low confidence triggers web search and
  decompose-then-recompose filtering.

**Cleanlab TLM** provides trustworthiness scores (0-1) combining
self-reflection, consistency, and probabilistic measures. Their "Reliable
Agentic RAG" adjusts retrieval strategies until trustworthiness exceeds
threshold.

**Implication:** our `/www` trigger pattern is an instance of the
FLARE/CRAG family — detect uncertainty in output, trigger research.
The difference: we detect uncertainty **lexically** (hedge words) rather
than **probabilistically** (token entropy). This is appropriate for a
black-box agent (Grok Build) where we don't have token logits.

## Finding 5: Production guardrail tools exist but focus on hallucination, not hedging

**Tools that detect uncertainty/hallucination in LLM output:**

| Tool | Approach | Hedging detection? |
|---|---|---|
| Cleanlab TLM | Trustworthiness scores (consistency + self-reflection) | No — probabilistic, not lexical |
| Galileo Luna-2 | Fine-tuned evaluators, sub-200ms inline blocking | Partial — faithfulness/groundedness |
| NeMo Guardrails | Programmable rails (Colang), self-check, fact-checking | No built-in hedge detection |
| UQLM (CVS Health) | Black-box consistency/semantic entropy package | No — probabilistic |
| Patronus AI Lynx | Fine-tuned hallucination detector (8B/70B) | No — factuality-focused |
| Openlayer | Groundedness/faithfulness scoring + guardrails | Partial — deterministic layer |

**None of these tools specifically detect hedge words adjacent to factual
claims.** The gap is real: existing tools focus on hallucination (output
contradicts sources) or consistency (output varies across samples). They
don't detect the case where the model is hedging because it doesn't know
the answer — which is exactly our target pattern.

This is a genuine contribution opportunity: lexical hedge detection as a
complementary layer to probabilistic UQ methods.

## Finding 6: Failure modes — what goes wrong with uncertainty detection

**From production guardrail research:**

- **False positives are the #1 production issue**: high FPR degrades UX,
  erodes trust, trains users to route around the system. Target FPR <1-2%.
- **Multiple stacked guards compound**: 5 guards at 90% accuracy each → ~40%
  overall false-positive rate if any failure triggers regeneration.
- **Gaming/avoidance**: users learn to avoid trigger words instead of
  actually being more certain. This is the "teaching to the test" failure.
- **Latency**: LLM-based guards add 5-10x overhead. Deterministic guards
  are preferred for inline use.
- **Inconsistency**: guards that flip verdicts on identical inputs erode trust.

**Specific to hedging detection:**
- RLHF already causes hedging as a side effect of safety training. A hook
  that penalizes hedging might push models toward overconfidence (worse).
- The intervention matters: advisory surfacing ("consider verifying X") is
  less disruptive than blocking ("you hedged, try again").
- Context disambiguation is critical: "maybe we should consider X" is
  exploratory and should not trigger.

**Mitigation:** our hook should be **advisory, non-blocking** (like the
existing `Maybe:` surfacing pattern in AGENTS.md), focused on hedge+claim
adjacency (not bare hedge words), with explicit context filters for
exploratory dialogue.

## Design implications for our hook

Based on this research, the optimal design is:

1. **Lexical detection** (regex on Prince taxonomy hedge words) as primary signal
2. **Context filter**: fire only when hedge is adjacent to a factual claim or
   specific number, not when it's exploratory ("maybe we should...")
3. **Advisory, non-blocking**: surface as `⚠ UNCERTAINTY: "maybe 5 RPM" —
   consider /www to verify` rather than blocking the response
4. **Route to /www**: the hook suggests research, doesn't auto-fire it
5. **Complement, not replace**: the hook works alongside existing
   `[INFERENCE]`/`[FACT]` labels, not instead of them. The model's own
   epistemic labels catch some cases; lexical detection catches others.

**What NOT to do (from the research):**
- Don't block on hedge words alone (too many false positives)
- Don't penalize hedging without offering a verification path (creates
  avoidance behavior, not actual certainty)
- Don't rely on the model's self-assessment alone (overconfidence is the
  documented failure mode)

## Sources

- Prince, Frader, & Bosk (1982) — hedge taxonomy (foundational)
- CoNLL-2010 Shared Task (Farkas et al.) — hedge detection benchmark
- BioScope corpus (Vincze et al.) — biomedical hedge annotation
- Yang et al. (2024, arXiv:2412.14737) — verbalized confidence reliability
- Pawitan & Holmes (2025, HDSR) — confidence in LLM reasoning
- ConfTuner (Li et al., NeurIPS 2025, arXiv:2508.18847) — calibration training
- DiNCo (Wang & Stengel-Eskin, 2025, arXiv:2509.25532) — distractor normalization
- Kadavath et al. (2022, arXiv:2207.05221) — "Language Models (Mostly) Know What They Know"
- Kuhn et al. (2023, arXiv:2302.09664) — semantic entropy
- Self-RAG (Asai et al., 2023, arXiv:2310.11511) — self-reflective retrieval
- FLARE (Jiang et al., 2023, arXiv:2305.06983) — active retrieval on low confidence
- CRAG (Yan et al., 2024, arXiv:2401.15884) — corrective retrieval
- Shorinwa et al. (2024/2025, arXiv:2412.05563) — UQ survey for LLMs
- Cleanlab TLM — trustworthiness scoring for agentic RAG
- UQLM (CVS Health, github.com/cvs-health/uqlm) — UQ Python package
- merge.dev, digitalapplied.com — production guardrail best practices

## Falsifier

If lexical hedge detection produces >5% false-positive rate on
exploratory dialogue (questions, option enumeration, conditional
reasoning), the approach is too noisy for production use and should
be replaced with a semantic classifier. Measure by running the hook
on 100 sample outputs and manually labeling triggers as
true-positive (hedge+claim) vs false-positive (exploratory/legitimate).
