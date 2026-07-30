---
title: "Self-reflection in LLMs fails without external evidence: what works for RCA and what doesn't"
created: 2026-07-30
source: session-019fb189
tags: [self-reflection, llm-failure-modes, rca, verification, epistemic-reflection, procedural-verification, intrinsic-self-correction, reflexion, toulmin, decision]
summary: >
  "Could I be wrong?" — pure intrinsic self-reflection in LLMs — does NOT
  improve reasoning quality and often degrades it (Huang et al. ICLR 2024).
  The gains reported by Reflexion and Self-Refine come from external feedback
  (test execution, tool results), not from the reflection step itself. For
  RCA specifically, the first direct empirical study (Riddell et al. FORGE
  2026, 48K scenarios) found the top failure predictors are exactly what
  reflection should fix but doesn't: anchoring bias, failure to update
  belief, stalled progress. The fix: replace "could I be wrong?" (epistemic
  reflection, internal) with "what evidence would prove me wrong?"
  (procedural verification, external). The distinction matters: procedural
  verification works (Chain-of-Verification, CRITIC); epistemic reflection
  doesn't.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://arxiv.org/abs/2310.01798 (Huang et al., ICLR 2024 — self-correction fails without external feedback)
  - https://arxiv.org/abs/2303.11366 (Shinn et al., NeurIPS 2023 — Reflexion ablation shows reflection alone hurts)
  - https://arxiv.org/abs/2303.17651 (Madaan et al., NeurIPS 2023 — Self-Refine gains were from bad initial prompts)
  - https://arxiv.org/html/2601.22208v1 (Riddell et al., FORGE 2026 — first LLM RCA study, 48K scenarios)
  - https://arxiv.org/abs/2309.11495 (Dhuliawala et al., Chain-of-Verification)
  - https://arxiv.org/abs/2305.11738 (Gou et al., CRITIC — tool-interactive critique)
  - https://arxiv.org/abs/2305.14975 (Tian et al., "Just Ask for Calibration")
  - https://arxiv.org/abs/2509.21545 (Ackerman, ICLR 2026 — limited metacognition)
relations:
  - target: wiki/concepts/convergence-gap-rca-symptom-restatement-toulmin-enforcement.md
    type: complements — the Toulmin COUNTEREXAMPLE field IS the procedural-verification replacement for epistemic reflection
  - target: wiki/concepts/premature-closure-narrative-sufficiency-external-approaches.md
    type: refines — adds the specific finding that reflection ≠ verification for LLMs
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related — closure pressure is why reflection fails (confirms rather than challenges)
  - target: wiki/concepts/research-applicability-checking-dont-cite-without-verifying-assumptions.md
    type: related — the Huang et al. result applies to our use case because RCA has no ground truth
---

# Self-reflection in LLMs fails without external evidence

## Decision context

**Why this was needed:** during session 019fb189's /why redesign research, the operator asked whether "could I be wrong?" reflection and other cognitive techniques would improve RCA quality. The workspace had prior findings on premature closure ([[premature-closure-narrative-sufficiency-external-approaches]]) but no specific evidence on whether self-reflection works for LLM-based diagnostic reasoning. The answer determines whether the /why redesign should include a reflection step — and the evidence says no, unless the reflection produces an external check.

## The evidence (high confidence, controlled ablations)

### Pure intrinsic self-correction fails

**Huang et al. (ICLR 2024):** "Large Language Models Cannot Self-Correct Reasoning Yet." Tested GPT-4 and Llama-2 on GSM8K, CommonSenseQA, HotpotQA. Without external feedback, self-correction *degrades* accuracy:
- GPT-4: 95.5% → 91.5% → 89.0% across two self-correction rounds
- Llama-2: 62.0% → 36.5% across two rounds
- When oracle labels are provided, self-correction appears to help — but the gain vanishes when the oracle is removed

**Key insight:** the model has no reliable internal signal that its reasoning has drifted. "Silent divergence" (arXiv:2603.15500) — trajectories drift from the correct answer yet remain locally coherent, so no error triggers reactive self-correction. The model doesn't know it's wrong. This is the same structural property documented in [[reactive-pattern-matching-and-closure-pressure]] — the pattern-completion pathway shortcuts the evidence-verification pathway.

### Reflexion's gains come from external execution, not reflection

**Shinn et al. (NeurIPS 2023):** Reflexion reports +11% on HumanEval. But the ablation (Table 3) tells the real story:
- Base model only: 0.60 pass@1
- Test generation + NO self-reflection: 0.60 (no improvement)
- NO test generation + self-reflection: 0.52 (**WORSE than baseline**)
- Reflexion (both): 0.68

The self-reflection step alone hurts. The gain requires *both* self-generated unit tests (external oracle) AND verbal self-reflection. Reflexion also fails outright on WebShop (tasks requiring diversity and exploration).

### Self-Refine's gains were from bad initial prompts

**Madaan et al. (NeurIPS 2023):** Self-Refine reports +20% across 7 tasks. But Huang et al. re-tested with an optimized initial prompt: baseline jumps to 81.8% and Self-Refine drops to 75.1%. The improvement was from fixing the initial prompt, not from the reflection step.

### Verbalized confidence is informative for flagging, not for self-revision

**Tian et al. (EMNLP 2023):** RLHF-tuned models give reasonably calibrated verbal confidence when asked. **Ackerman (ICLR 2026):** frontier LLMs show "increasingly strong evidence of certain metacognitive abilities" BUT they are "limited in resolution, emerge in context-dependent manners, and seem qualitatively different from humans." Using confidence to *change the answer* doesn't help; using it to *flag for human review* may help.

## The critical distinction: reflection vs. verification

| Type | Question | Works? | Why |
|---|---|---|---|
| **Epistemic reflection** (internal) | "Am I justified in believing this?" | ❌ No | Model has no reliable signal that reasoning drifted; confirms rather than challenges |
| **Procedural verification** (external) | "Does this match external evidence?" | ✅ Yes | Produces an external check — Chain-of-Verification, CRITIC, test execution |

**Chain-of-Verification (Dhuliawala et al., Meta 2024):** draft → plan verification questions → answer those questions *in isolation* (not biased by the original answer) → produce final response. Reduces hallucinations. The key move is *independence* — the verification questions are answered without seeing the draft.

**CRITIC (Gou et al., ICLR 2024):** LLMs validate and amend outputs via tool calls (search engines, code interpreters, calculators). Performance gains only materialize when external feedback is available.

## The Riddell et al. paper — the first direct RCA study

This is the single most relevant source. 48,000 simulated fault scenarios, 228 days of execution, 6 LLMs, 3 workflows. Key findings:

**Top 4 reasoning failures predicting incorrect RCA:**
1. Anchoring bias (RF-13) — premature fixation on first hypothesis
2. Repetition / stalled progress (RF-12) — going in circles
3. Arbitrary evidence selection (RF-07) — cherry-picking data
4. Failure to update belief (RF-09) — not revising when evidence contradicts

These are *exactly* what "could I be wrong?" should fix but doesn't — the model has no signal that it's anchored, stalled, or cherry-picking.

**Surprising finding:** trace data inclusion hurts accuracy (LLMs focus narrowly on call relationships). Agentic workflows (ReAct, Plan-and-Execute) often yield *negative returns* vs. straight-shot reasoning.

**Their recommendation:** "early hypothesis diversification (tree-of-thought), self-consistency or critique mechanisms, evidence sufficiency checks, and explicit domain guidance."

## What this means for our workspace

1. **Don't add a reflection step to /why.** Pure "could I be wrong?" prompting degrades reasoning. The workspace's existing external-verification mechanisms (evidence tiers, source-code citations, cross-model review, `--verify` subagent) are the correct pattern.

2. **Replace "could I be wrong?" with "what evidence would prove me wrong?"** — the Toulmin COUNTEREXAMPLE field already does this (see [[convergence-gap-rca-symptom-restatement-toulmin-enforcement]]). The difference: epistemic reflection (internal, fails) → procedural verification (external, works). This mirrors the distinction in [[premature-closure-narrative-sufficiency-external-approaches]] between internal narrative sufficiency and external evidence verification.

3. **Add hypothesis diversification** — force 3 ranked hypotheses before drilling into one. This is the Riddell paper's #1 recommendation for preventing anchoring bias.

4. **The workspace's cognitive techniques are mostly the RIGHT ones** — negative constraint preambles, required sequences, ACH, pre-mortems, fresh-lens critique, pattern-library query, evidence tiers. The one technique the evidence supports that we DON'T have: Self-Ask decomposition (forcing sub-question decomposition before investigation).

5. **Capability ≠ mechanism-finding.** Larger models produce *less* faithful reasoning on most tasks (Lanham et al.). SFT and RLHF *weaken* the ideal causal chain (Bao et al.). Don't use fluency or model size as a proxy for causal depth.

## Receipts

- Huang et al. ablation: GPT-4 drops 95.5%→89.0% with intrinsic self-correction (arXiv:2310.01798, verified full read)
- Reflexion ablation Table 3: self-reflection alone 0.52 < baseline 0.60 (arXiv:2303.11366, verified full read)
- Self-Refine rebuttal: baseline 81.8% > self-refine 75.1% with optimized prompt (Huang Table 8)
- Riddell et al.: anchoring bias RD ≤ –0.15, top predictor of incorrect RCA (arXiv:2601.22208, verified full read)
- Session 019fb189: operator asked "is it useful for the agent to reflect on 'could it be wrong'?" — answer is no, unless the reflection produces an external check

## Falsifier

If, after implementing the Toulmin COUNTEREXAMPLE + EVIDENCE fields (procedural verification), /why still produces symptom-restatements at the same rate as before, the procedural-verification approach doesn't work for RCA and an independent external critic (different model, different context) is required. Measure: run 3 real failures through /why with and without Toulmin fields; if COUNTEREXAMPLE content is non-trivial in ≥2 of 3, the approach helps.

## Sources

- [Large Language Models Cannot Self-Correct Reasoning Yet](https://arxiv.org/abs/2310.01798) (Huang et al., ICLR 2024) — definitive ablation: intrinsic self-correction degrades accuracy
- [Reflexion: Language Agents with Verbal Reinforcement Learning](https://arxiv.org/abs/2303.11366) (Shinn et al., NeurIPS 2023) — ablation shows reflection alone hurts; gain requires test execution
- [Self-Refine: Iterative Refinement with Self-Feedback](https://arxiv.org/abs/2303.17651) (Madaan et al., NeurIPS 2023) — gains were from bad initial prompts, not reflection
- [Stalled, Biased, and Confused: Uncovering Reasoning Failures in LLMs for Cloud-Based Root Cause Analysis](https://arxiv.org/html/2601.22208v1) (Riddell et al., FORGE 2026) — first direct LLM RCA study; anchoring bias is #1 failure predictor
- [Chain-of-Verification Reduces Hallucination in Large Language Models](https://arxiv.org/abs/2309.11495) (Dhuliawala et al., Meta 2024) — procedural verification works when answers are generated independently
- [CRITIC: Large Language Models Can Self-Correct with Tool-Interactive Critiquing](https://arxiv.org/abs/2305.11738) (Gou et al., ICLR 2024) — external tool feedback enables self-correction
- [Just Ask for Calibration](https://arxiv.org/abs/2305.14975) (Tian et al., EMNLP 2023) — verbal confidence can be calibrated for flagging, not for self-revision
- [Evidence for Limited Metacognition in LLMs](https://arxiv.org/abs/2509.21545) (Ackerman, ICLR 2026) — metacognitive abilities are limited, context-dependent, qualitatively different from humans
