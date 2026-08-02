---
title: "Examples over rules — escape hatch for tacit knowledge that resists encoding"
created: 2026-07-19
source: session-2026-07-19
last_verified: 2026-08-02
tags: [context-engineering, few-shot, prompting, llm, technique]
summary: >
  Rules encode explicit knowledge; examples encode tacit knowledge. When you
  find yourself rewriting the same rule repeatedly and outputs still feel
  "off," stop trying to encode the rule and instead drop a small number of
  curated past outputs (2-8, not 10-30) into the prompt as a style/pattern
  corpus. This is a tool to reach for when rules fail, not a default
  architecture — and it transfers to format-matching tasks (structured output,
  code security) better than to reasoning tasks (code synthesis, multi-step
  logic), where examples can actively hurt performance.
agent: grok
cognitive_load: 2
verification: multi-source-verified
evidence_gaps: []
host: both
---

## Summary

Rules and examples are two different encoding strategies for getting an LLM to
match your intent. **Rules encode explicit knowledge** (verifiable, testable,
hook-enforceable). **Examples encode tacit knowledge** (cadence, emphasis,
taste — patterns too complex to articulate). When rules work, rules win. When
the thing you're trying to convey resists articulation, stop rewriting the
rule and use examples instead.

**Key update (2026-08-02 re-verification):** the original "10-30 examples"
recommendation was **wrong**. Multiple empirical studies show saturation at
2-8 examples for most tasks; beyond that, performance crashes sharply. The
domain split is also more nuanced than "prose vs code" — it is
**format-matching vs reasoning**.

## Key Findings

### The technique (when it earns its keep)

- Provide **2-8 curated past outputs** labeled with *why each is good*. Raw
  dumps force the model to infer your taste; labeled examples tell it.
  (Updated from 10-30 — see "Few-shot saturation" below.)
- The corpus must be context-bounded (fits the window) or have a retrieval
  path. Hand-waving "index and reference" is the implementation gap most
  treatments skip.
- The corpus must rotate, or it slowly teaches the model a style you've
  outgrown. Style drifts; oldest examples must carry a date.

### Where it works (high confidence, multi-source verified)

- **Prose-style transfer:** newsletters, brand voice, content of any kind.
  (Original claim — confirmed by AppliedAIHub Bayesian analysis: examples
  constrain all output dimensions simultaneously while descriptions address
  only named ones.)
- **Structured output formats:** JSON schemas, report layouts, reasoning
  traces — implicit structural conventions that examples demonstrate but
  descriptions struggle to capture. (New finding 2026-08-02.)
- **Code security:** few-shot examples significantly reduce vulnerabilities
  like improper input handling. (Source: Medium/dnagasuresh1992, 2025.)

### Where it transfers poorly (verified — was inference, now multi-source)

The original concept claimed examples "transfer poorly to verifiable-output
domains (code, infra, policy)." Research refines this: **the split is not
prose-vs-code, it is format-matching-vs-reasoning.**

- **Code synthesis / reasoning:** arXiv 2412.02906 ("Does Few-Shot Learning
  Help LLM Performance in Code Synthesis?") directly tests this and finds
  few-shot examples do NOT reliably improve code synthesis. The model mimics
  example structure rather than solving the actual problem.
- **Reasoning tasks generally:** OpenAI's own GPT-5 guidance states "clear
  instructions and well-defined constraints often work better than adding
  examples," and warns that few-shot prompts can reduce performance when the
  task requires heavy reasoning. (Source: OpenAI Prompt Optimization Cookbook,
  cited via tianpan.co.)
- **Tasks where the model already has strong pre-trained capabilities:**
  few-shot can hurt by pushing the model into overthinking or format-matching
  behavior. (Source: Medium/rinkukalsi300, 2025.)

### Few-shot collapse: when more examples make performance WORSE

This is the most important finding from the 2026-08-02 re-verification. The
original concept's "10-30 examples" recommendation is actively dangerous.

**The few-shot saturation curve** (tianpan.co, Apr 2026): adding examples
improves accuracy up to a model-specific sweet spot, then causes sharp
degradation. Specific measurements:
- **Gemini 3 Flash:** 93% → 30% at 8 examples
- **Qwen 3.5:** 56% → 0% on a code-fixing task

**The Few-Shot Dilemma** (arXiv 2509.13196, "Over-prompting"): formal
academic study confirming the over-prompting effect across GPT-4o,
DeepSeek-V3, Gemma-3, LLaMA, and Mistral. The optimal example count is
per-model and per-task — there is no universal number. One author's
classifier peaked at 3 examples; the 8-example version was the worst
performer.

**AdaptGauge** (open-source tool, Feb 2026, tested 12 models across 5 tasks):
detects "few-shot collapse" cases where adding examples degrades performance.
The tool exists because the problem is common enough to warrant dedicated
detection.

### Few-shot rot: model upgrades invalidate old examples

When migrating to a newer model version without re-evaluating few-shot
examples, demonstrations that previously improved accuracy begin dragging it
down. The new model has different failure modes, formatting priors, and
instruction-following behavior. (Source: tianpan.co, "Few-Shot Example Rot,"
Apr 2026.)

### Example selection matters more than example count

Libretto testing (13 pts on HN): 19 percentage point difference between worst
and best set of few-shot examples on the same task. Selection-induced
collapse: retrieval-based (dynamic) example selection caused a 58% relative
performance drop compared to curated fixed examples. (Source:
tianpan.co/getlibretto, 2026.)

## Signal that this is the right tool (the trigger to remember)

> You keep rewriting the same rule / instruction / system prompt for a workflow
> and the output still feels wrong in a way you can't articulate. "I know it
> when I see it, but I can't write the rule for it."

That's the firing condition. Stop trying to write a better rule. Collect 2-8
of your best past outputs, paste them in, and ask the model to match them.

**But first check:** is the task format-matching (examples help) or reasoning
(examples may hurt)? If reasoning, try zero-shot with clear instructions first.

## Decision context

**Why this re-verification was needed:** the concept was the #1 highest-debt
item in the wiki (epistemic_debt.py score 0.72, `verification: inferred-only`,
5 incoming links). Two evidence gaps were explicitly documented: (1) no
evidence that examples transfer poorly to code domains, (2) no local corpus
existed to test. The 2026-08-02 /www run researched both gaps with 3 parallel
subagents + HN/DDG practitioner signals.

**What changed:** the "10-30 examples" corpus size was refuted (saturation
crashes at 2-8 for most tasks). The domain-transfer claim was refined from
"prose vs code" to "format-matching vs reasoning" — a more precise and
actionable distinction. Three new failure modes were documented (few-shot
collapse, few-shot rot, selection-induced collapse). Verification upgraded
from `inferred-only` to `multi-source-verified`.

**What the research changed operationally:** this concept now provides
specific guardrails (cap at 2-8, re-evaluate after model upgrades, avoid for
reasoning tasks) that the original lacked. The operator's observation that
"there is no visible practice of curating few-shot examples" (from
`operator-collaboration-style-and-leverage.md`) is now contextualized: the
practice is correct to avoid for reasoning-heavy skills, but could help for
format-matching skills (structured output, report templates).

## What this means for our workspace

1. **Audit skills for format-matching vs reasoning.** Skills that produce
   structured output (wiki entries, handoff templates, reports) could benefit
   from 2-8 curated examples. Skills that require reasoning (/why, /tp,
   /review) should NOT use few-shot examples — zero-shot with clear
   instructions is better per OpenAI's own guidance.

2. **Re-evaluate any existing few-shot blocks after model upgrades.** The
   fleet uses multiple models (Grok, Codex, Agy, MiniMax). Example blocks
   tuned for one model may hurt another. The few-shot rot finding means every
   model-pool update should trigger a re-evaluation of example-based prompts.

3. **No local corpus needed for prose-style transfer.** The original concept's
   evidence gap about "no local corpus exists" is less urgent than it seemed.
   The technique is most useful for format-matching, where 2-8 examples from
   recent good outputs suffice. A persistent corpus is only needed for
   recurring brand-voice or style tasks, which this workspace doesn't have.

4. **The operator's rules-based prompting style is correct for this fleet.**
   `operator-collaboration-style-and-leverage.md` noted the operator never
   curates few-shot examples. Given that the fleet's skills are predominantly
   reasoning-heavy (/why, /tp, /review, /go, /check), this is the right
   default. Examples would hurt more than help.

## Falsifier

This concept is wrong if:
- Future research shows few-shot examples reliably improve reasoning tasks at
  any corpus size (the current evidence shows they hurt).
- The saturation curve is shown to be an artifact of poor example selection,
  not an intrinsic limit (if curated examples at 10-30 consistently beat
  curated examples at 2-8, the corpus-size claim is wrong).
- The format-matching vs reasoning distinction is shown to be a false
  dichotomy (e.g., if examples help code reasoning when structured as
  chain-of-thought demonstrations).

The few-shot collapse finding (AdaptGauge, arXiv 2509.13196) is the strongest
evidence against the original "more examples = better" intuition. If
replication studies fail to reproduce the collapse effect, this concept's
corpus-size guidance should be re-evaluated.

## Evidence

All claims in this concept are externally sourced from published research and
practitioner testing (see Sources below). No local code inspection was
performed — this is a research-synthesis concept, not a mechanism claim about
local infrastructure. The workspace-implications recommendations in "What this
means for our workspace" are [INFERENCE] derived from applying external
research to this fleet's skill composition (predominantly reasoning-heavy skills).

## Sources

- [AppliedAIHub: Zero-shot vs few-shot prompting](https://appliedaihub.org/blog/zero-shot-vs-few-shot-prompting/) (2025) — Bayesian explanation of why examples constrain output dimensions
- [arXiv 2412.02906: Does Few-Shot Learning Help LLM Performance in Code Synthesis?](https://arxiv.org/html/2412.02906v1) (Dec 2024) — directly tests code synthesis, finds examples don't reliably help
- [arXiv 2509.13196: The Few-Shot Dilemma (Over-prompting)](https://arxiv.org/html/2509.13196v1) (2025) — formal study of over-prompting across 5 LLMs
- [AdaptGauge (github)](https://github.com/ShuntaroOkuma/adapt-gauge-core) (Feb 2026) — open-source tool detecting few-shot collapse, 12 models tested
- [Libretto: Does example choice matter?](https://www.getlibretto.com/blog/does-it-matter-which-examples-you-choose-for-few-shot-prompting) (2026) — 19pp difference between worst and best example sets
- [tianpan.co: Few-Shot Saturation Curve](https://tianpan.co/blog/2026-04-16-few-shot-saturation-curve) (Apr 2026) — Gemini 93%→30%, Qwen 56%→0% data
- [tianpan.co: Few-Shot Example Rot](https://tianpan.co/blog/2026-04-27-few-shot-example-rot-model-upgrades) (Apr 2026) — model-upgrade regression
- [OpenAI Prompt Optimization Cookbook](https://cookbook.openai.com/examples/gpt-5/prompt-optimization-cookbook) (2025) — GPT-5 guidance against examples for reasoning
- [NAACL 2025: Nafar et al.](https://aclanthology.org/2025.naacl-long.417/) (2025) — ICL competitive with fine-tuning for simple tasks
- [Medium/rinkukalsi300: Zero-shot, few-shot or no-shot?](https://medium.com/@rinkukalsi300/zero-shot-few-shot-or-no-shot-4d8c5b16a87b) (Jul 2025) — failure modes: overfitting, format-mimicry, order sensitivity
- Session 2026-07-19 (original concept creation)
- Session 2026-08-02 /www re-verification (3 parallel subagents + HN/DDG practitioner signals)

## Related

- [[skill-enforcement-layers]] @related — rules-based enforcement is the
  complement; this page is the escape hatch when rules fail
- [[solo-operator-adr-best-practices]] @related — ADRs are rules-as-decisions;
  the corpus method applies to prose-shaped outputs ADRs don't cover
- [[claude-code-skill-failure-patterns]] @related — skills are the strongest
  rules encoding; this is the fallback for what skills can't capture
- [[operator-collaboration-style-and-leverage]] @related — documents the
  operator's rules-based prompting style, now contextualized as correct
- [[deliberation-waste-re-deriving-same-answer]] @related
- [[external-state-cross-check-as-structural-fix]] @related
- [[rule-not-fired-vs-rule-doesnt-exist]] @related

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[skill-catalog]]
- [[antigravity-codes-platform]]
- [[open-knowledge-format-okf]]
- [[llm-wiki-knowledge-pattern]]

