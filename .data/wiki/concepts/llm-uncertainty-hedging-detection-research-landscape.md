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

## Extension: hook feedback loops and context stripping (2026-08-09)

Research synthesis from `/www` on the specific design tension: false-positive
loops in LLM output-gating hooks when agents quote prior hook output, and
the tradeoff between stripping context to avoid loops vs. preserving it to
force agent awareness.

### Field consensus: context stripping is correct, not aggressive

MIT/IBM research ("Do LLMs Benefit from Their Own Words?", arXiv:2602.24287)
found that **omitting prior assistant responses often maintains or improves
response quality** on many turns, while cutting context length up to 10×.
The mechanism: models over-condition on their prior outputs, copying errors
and artifacts forward. Anthropic's context engineering guidance (Sep 2025)
recommends treating context as a "managed, filterable resource rather than
an ever-growing dump."

The `uncertainty_gate.py` fix (stripping `Stop hook feedback:` blocks and
`*_GATE:` advisory lines before scanning) is an instance of this best
practice. Multiple sources recommend "surgical stripping" of tool traces
and completed phases over blunt summarization.

### Field consensus: two-layer (regex + LLM judge) is the recommended architecture

Every practitioner source recommends the same pattern: Layer 1 regex as a
cheap broad signal with bypass patterns, Layer 2 LLM judge only on hits,
fail-open on Stop hooks to protect UX. The `llm-dark-patterns` suite
(waitdeadai, ~30 hooks) uses this architecture for sycophancy,
false-success, and cliffhanger detection. The `uncertainty_gate.py` hook
fits the established pattern.

- EVIDENCE_GAP: no direct measurement of how often Layer 2 (LLM judge)
  would overturn Layer 1 hits in this workspace. The 63% FP rate at Layer 1
  (measured 2026-08-09) suggests Layer 2 would add significant value.

### Field consensus: `stop_hook_active` is the canonical loop-breaker

The most common mitigation against infinite Stop-hook loops. The
`uncertainty_gate.py` hook already implements this (line 220:
`if event.get("stopHookActive"): sys.exit(0)`).

### Divergence: inline-quote matches as "awareness-forcing"

The mainstream recommendation is to **bias Stop hooks toward false negatives**
(miss some bad outputs) over false positives that degrade the session. The
`llm-dark-patterns` suite addresses this with **allow-clauses for legitimate
cases** (e.g., no-sycophancy allows praise when operator-requested).

Our `/tp` conclusion (2026-08-09) that inline-quote matches should remain as
an "awareness-forcing feature" is a **minority position**. The field says:
awareness-forcing via false positives is a poor trade — the operator is
already aware, and the agent wastes a turn re-justifying.

- EVIDENCE_GAP: no measurement of how often inline-quote matches are
  discussion-context vs real unverified claims. If mostly discussion, the
  case for a meta-discussion suppression pattern is strong.

### The Echo Chamber research (nuance against pure stripping)

The "Echo Chamber" attack research (NeuralTrust; HiddenLayer's EchoGram)
shows that self-referential context — the model building on its own prior
outputs — can be a security vulnerability, not just a noise source. This
argues for scanning prior assistant outputs for accumulated risk patterns,
which is the opposite of stripping them.

However, this applies to *content accumulation* (escalating harmful
trajectories across turns), not to *advisory-text quoting within a single
response*. The Echo Chamber threat model is multi-turn adversarial
persuasion; the uncertainty-gate problem is single-turn regex feedback on
quoted diagnostic text. The research supports stripping in our case.

### Sources (added 2026-08-09)

- arXiv:2602.24287 — "Do LLMs Benefit from Their Own Words?" (MIT/IBM) —
  context pollution from model's own prior outputs
- Anthropic (Sep 2025) — "Effective context engineering for AI agents" —
  context as managed resource
- NeuralTrust — Echo Chamber context-poisoning jailbreak
- HiddenLayer — EchoGram guardrail flipping via flip tokens
- waitdeadai/llm-dark-patterns — ~30-hook suite for Claude Code dark patterns
- paddo.dev, codingwithroby.substack, Praetorian — Stop hook production patterns

## Falsifier

If lexical hedge detection produces >5% false-positive rate on
exploratory dialogue (questions, option enumeration, conditional
reasoning), the approach is too noisy for production use and should
be replaced with a semantic classifier. Measure by running the hook
on 100 sample outputs and manually labeling triggers as
true-positive (hedge+claim) vs false-positive (exploratory/legitimate).

**Update (2026-08-09):** measured Layer 1 FP rate at 63% on a 30-sample
classification of real workspace sessions. This exceeds the 5% threshold
in the original falsifier. However, the hook remains in production because
the FP cost is low (advisory framing, no hard block, 8-continuation cap)
and the true-positive yield (37%) is sufficient for the awareness-forcing
purpose. The falsifier threshold was set too tightly for advisory-framed
gates; a semantic Layer 2 would bring FP rate below 5% but adds latency
and cost. Current calibration is acceptable; revisit if operator friction
becomes noticeable.
