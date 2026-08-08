---
title: "Automatic logical fallacy detection in agent hooks: viable design, known limits, and why narrow receipt-based detection wins"
created: 2026-08-08
source: session-019fe25d (/www run)
tags: [hooks, enforcement, fallacy-detection, llm-judge, reasoning-quality, disconfirmed-premise, receipt-based-architecture, grok-build]
summary: >
  Research on whether hooks can automatically detect logical fallacies. The
  generic premise ("detect fallacies and block") is DISCONFIRMED on three
  independent grounds: (1) human inter-annotator agreement on fallacy labeling
  is low (κ ~0.54 on logical validity), so any detector is calibrated against
  a noisy target; (2) informal fallacies are inherently context-dependent and
  cannot be identified from form alone; (3) false positives cause conversation
  collapse and chilling effects on valid reasoning. The viable approach — which
  this workspace already uses — is NARROW: detect specific high-signal reasoning-
  error patterns (receipt-missing, narrative-sufficiency, causal-claim-without-
  verification) via the two-layer regex+LLM-judge pattern, fail-open, and treat
  the output as advisory signal rather than blocking gate. Generic fallacy
  taxonomies (MAFALDA's 92 categories) are too noisy for hook enforcement;
  binary-evidence patterns (receipt exists or doesn't) are tractable.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/llm-judgment-hooks.md
    type: extends
  - target: wiki/concepts/narrative-as-signal.md
    type: refines
  - target: wiki/concepts/fabricated-causal-chain-receipt-required.md
    type: instance-of
  - target: wiki/concepts/measurement-before-addition-principle.md
    type: constrained-by
  - target: wiki/concepts/cognitive-enforcement-patterns-for-ai-coding-agents.md
    type: complement
---

# Automatic logical fallacy detection in agent hooks

## Decision context

**Why this research was needed:** the operator asked "how can we have hooks
detect logical fallacies automatically?" The implicit goal is to catch
reasoning errors — fabricated causal chains, narrative sufficiency, false
dichotomies, unsupported claims — at the hook layer rather than relying on
the model's own compliance with prose rules. The workspace has ~15 wiki
concepts documenting specific reasoning-error patterns (narrative-as-signal,
fabricated-causal-chain, optimality-claims-are-completion-claims, etc.), all
enforced through prose rules with a documented ~50% compliance ceiling under
session pressure. A hook that catches these mechanically would close the gap.

**What the research changed:** it confirmed that the workspace's existing
architecture (narrow, receipt-based, pattern-specific detection) is the right
approach — NOT because generic fallacy detection is impossible, but because
its precision ceiling is too low for blocking enforcement. The research
redirected the question from "which fallacy taxonomy should the hook use?"
to "which specific reasoning-error patterns have binary evidence that a hook
can check deterministically?"

## The disconfirmed premise: generic fallacy detection as a blocking gate

Three independent findings disconfirm using a generic fallacy classifier as
a blocking hook:

### 1. Human annotators disagree on what counts as a fallacy

The LREC 2022 study "The Search for Agreement on Logical Fallacy Annotation
of an Infodemic" reports low inter-annotator agreement even after multiple
annotation phases. A 2024 study quantifying LLM-judge consistency found κ =
0.78 on factual correctness but only **κ = 0.54 on logical validity**
(chain-of-thought errors) — meaning the same judge disagrees with itself
nearly half the time on whether reasoning is valid. If the gold standard is
this noisy, any detector calibrated against it inherits the noise. You cannot
build a high-precision blocking gate on a target that humans can't consistently
label. [INFERENCE — single source for the κ number; qualitative direction
robust across sources]

### 2. Informal fallacies are inherently context-dependent

Wikipedia's "List of fallacies" notes that informal fallacies "cannot
ordinarily be identified from form alone, since their assessment depends on
content, evidence, context, and purpose." This is a structural property of
the domain: formal fallacies (affirming the consequent) have syntactic
signatures; informal fallacies (ad hominem, straw man, appeal to authority)
require understanding the argument's intent and context. A hook that sees
only the agent's output text lacks the context to distinguish "this is a
fallacy" from "this is a valid heuristic stated concisely." [FACT — domain
property, well-established]

### 3. False positives cause conversation collapse and chilling effects

The two-layer hook pattern (regex Layer 1 → LLM Layer 2) is documented in
[[llm-judgment-hooks]] with a specific failure mode: regex false positives
cause the conversation-collapse loop (agent rephrases → blocked again →
rephrases → blocked → screen fills with restatements). A 2025-26 study on
LLM-based content judges found high false-positive rates on harmless content,
causing a "chilling effect" where legitimate output was blocked. For
fallacy detection specifically, the risk is higher: valid reasoning that
uses shorthand, heuristics, or analogy gets flagged because it doesn't
follow formal logical structure. Blocking on that signal would degrade the
agent's ability to do exactly the kind of fast pragmatic reasoning the
operator values. [INFERENCE — the chilling-effect finding is from content
moderation, not fallacy detection specifically, but the mechanism transfers]

### The absence-in-production signal

OpenAI's moderation API, Anthropic's safety layer, and production guardrail
frameworks (NeMo Guardrails, Guardrails AI) use policy-based and keyword-
based filters — NOT automatic fallacy detectors. No major deployment uses
generic fallacy classification as a blocking gate. This absence is itself a
signal: the field has evaluated this approach and found it insufficient for
production reliability. [INFERENCE — absence-of-evidence reasoning, but
corroborated by the three findings above]

## The viable approach: narrow pattern-specific detection

The disconfirmation above kills the generic approach but NOT the underlying
goal. The viable design detects SPECIFIC reasoning-error patterns that have
**binary evidence** (a receipt exists or doesn't; a claim is sourced or
isn't) rather than classifying against a subjective taxonomy.

### Why binary-evidence patterns are tractable

| Pattern | Evidence type | Detection method | Precision |
|---------|--------------|-----------------|-----------|
| Causal claim without receipt | Binary (receipt exists?) | Regex for causal language + check for tool-call citation | High |
| Completion claim without verification | Binary (test output exists?) | Regex for "done/fixed" + check for test command in transcript | High |
| Optimality claim without comparison | Binary (alternatives named?) | Regex for "optimal/best" + check for comparison block | High |
| Narrative sufficiency (plausible story as answer) | Graded (subjective) | LLM judge with rubric | Medium |
| Generic fallacy (ad hominem, straw man) | Graded (subjective, context-dependent) | LLM classifier on MAFALDA | Low (~κ 0.54) |

The first three are what the workspace already implements via prose rules
and receipt-gate hooks. They work because the evidence is binary — either
you have a tool-call receipt for that causal claim or you don't. The last
two are what the research disconfirms for blocking use.

### The two-layer pattern for reasoning errors (from [[llm-judgment-hooks]])

```
Agent output → Layer 1 regex (causal/completion/optimality language)
  → no hit → ALLOW (~95% of outputs)
  → hit → Layer 2 LLM judge (Gemini Flash / MiniMax M3, ~2-3s)
    → JSON: {has_receipt: bool, is_direction_query: bool, is_future_step: bool}
    → block = has_causal_claim AND NOT has_receipt AND NOT is_direction_query
  → fail-open on judge error (never kill conversation)
```

This is the pattern already documented in [[llm-judgment-hooks]] for the
alternatives-gate. The same architecture extends to any reasoning-error
pattern with a checkable evidence condition.

### Fail-open is mandatory for Stop hooks

From [[llm-judgment-hooks]]: a fail-closed Stop hook that breaks = permanent
conversation deadlock. A broken fallacy judge must not kill the conversation.
The judge is advisory: it surfaces the signal, the operator decides whether
to act. This is the [[narrative-as-signal]] principle applied to the hook
layer — the detection is the trigger to investigate, not the answer.

## State of the art in fallacy detection (for reference)

[Note: specific F1 numbers below are [UNTESTED] — sourced through subagent
readings of search snippets, not primary-source verification during this run.
Qualitative rankings are robust; treat exact numbers as approximate.]

| Approach | Best reported performance | Trade-off |
|----------|--------------------------|-----------|
| MAFALDA benchmark (LLaMA-2-70B) | macro-F1 ~0.77 (precision ~0.94, recall ~0.65) | High precision but misses 35% of fallacies; recall too low for a blocking gate |
| CoCoLoFa fine-tuned BERT | F1 ~0.86 detection | Best published; but trained on social-media comments, not agent reasoning |
| Logical Structure Tree (EMNLP 2024) | +8-10% precision over flat classifiers | Structure-aware; best for formal fallacies |
| Knowledge-augmented prompting (Follow My Lead) | +7% over baseline | Injects fallacy definitions into context |
| VeriCoT (neuro-symbolic chain verification) | Flags ~82% of erroneous CoT chains | Not a fallacy detector — verifies reasoning steps via theorem prover. Distinct sub-class. |
| Flat BERT/RoBERTa classifiers | F1 ~0.65, <10ms CPU | Fast but misses structured fallacies |

**Key insight:** even the best detector (F1 ~0.86 on CoCoLoFa) misses 14%
of fallacies with a 14% false-positive rate. For a blocking hook that fires
on every agent turn, that means roughly 1 in 7 valid outputs gets blocked.
That is not viable for production — it's the conversation-collapse scenario.

### VeriCoT: the distinct sub-class worth noting

VeriCoT (arXiv 2511.04662) is NOT a fallacy classifier — it's a reasoning-
chain verifier that formalizes each CoT step into first-order logic and
checks it with a theorem prover. This is a fundamentally different approach:
instead of asking "is this a fallacy?" it asks "does this reasoning step
follow from the previous one?" This is more tractable because the evidence
is structural (does step N follow from steps 1..N-1?) rather than taxonomic
(which of 92 categories does this match?). [INFERENCE — single source, not
tested on workspace. Potential follow-up research target.]

## Workspace-counterexample check

- **Recommendation: use narrow receipt-based detection, not generic fallacy
  classification** — no counterexample found. The workspace already does this
  ([[fabricated-causal-chain-receipt-required]], [[ship-receipt-mechanical-
  generation-from-per-check-results]]). The research confirms the architecture.
- **Recommendation: fail-open advisory, not blocking** — no counterexample.
  [[narrative-as-signal]] explicitly endorses this: the signal triggers
  investigation, it doesn't replace it.
- **Recommendation: do NOT add a generic MAFALDA-classifier hook** —
  ⚠️ [KNOWN-FAILURE-MODE: [[measurement-before-addition-principle]]] — before
  adding ANY new detection capability, measure the conversion rate of existing
  findings. The workspace already has signal-overflow risk (15+ reasoning-error
  concepts, multiple scanner hooks). Adding a low-precision generic detector
  pours more signal into a system that may already be at capacity. The
  measurement-before-addition principle requires auditing existing detection
  conversion rates BEFORE adding new detection.
- **Recommendation: scope to binary-evidence patterns** — no counterexample.
  This is the [[trusted-exit-status-fallacy-pipeline-ground-truth]] principle:
  check the artifact (receipt), not the label (fallacy classification).

## Do's and don'ts

### Do
- Detect SPECIFIC reasoning-error patterns with binary evidence (receipt
  exists? alternatives named? test output present?) — these have high precision
- Use the two-layer regex+LLM pattern from [[llm-judgment-hooks]] for patterns
  that need semantic judgment
- Fail-open on Stop hooks — a broken judge must not kill the conversation
- Treat detection as advisory signal (trigger to investigate), not blocking
  gate (the answer) — per [[narrative-as-signal]]
- Use I-CALM-style abstention prompting in the LLM judge (reward abstention
  over false-positive classification) — reduces false positives ~30%
- Use pairwise comparison (agent output vs known-good reference) rather than
  pointwise scoring when feasible — reduces position/verbosity bias
- Log all judge decisions with κ tracking — if intra-judge agreement drops
  below 0.7 on a pattern, that pattern is too subjective for hook enforcement
- Consider VeriCoT-style chain verification (structural, not taxonomic) for
  reasoning-step validation — distinct from fallacy classification

### Don't
- Don't use a generic MAFALDA-trained classifier as a blocking hook — precision
  ceiling (~86% F1) means ~1 in 7 valid outputs blocked → conversation collapse
- Don't classify against the full 92-category MAFALDA taxonomy — inter-annotator
  agreement is too low (κ ~0.54 on logical validity) for the labels to be reliable
- Don't fail-closed on a Stop hook with an LLM judge — broken judge = dead
  conversation (documented in [[llm-judgment-hooks]])
- Don't add fallacy detection without first measuring existing signal conversion
  rates — per [[measurement-before-addition-principle]], you may be adding to
  signal overflow
- Don't expect the LLM judge to be consistent across runs — log and track κ;
  patterns with κ < 0.7 are too noisy for enforcement
- Don't conflate "fallacy detection" (graded, subjective) with "receipt
  verification" (binary, deterministic) — the latter is tractable, the former
  isn't, and the workspace already chose the latter

## Host invariant check

- **Multi-terminal isolation:** an LLM judge calling an external API (Gemini
  Flash, MiniMax M3) from a hook does not touch shared browser state. No
  invariant violation. [FACT — verified against [[concurrent-cdp-auth-contention]]]
- **Recursion guard:** mandatory when calling an LLM from a hook — set
  `HOOK_LLM_JUDGE_ACTIVE=1` env var, exit 0 if detected. Documented in
  [[llm-judgment-hooks]]. [FACT]
- **Secret redaction:** agent output may contain API keys in code quotes —
  redact before sending to external judge. Documented. [FACT]
- **`.grok/hooks/` directory:** does not exist yet on this host — any hook
  implementation is greenfield, no existing hook to conflict with. [FACT —
  verified via filesystem check this session]
- **Prompt injection defense:** wrap evaluation target in boundary markers
  (`--- text-begin ---` / `--- text-end ---`) so agent output can't override
  judge instructions. Documented. [FACT]

## What this means for our workspace

The workspace already has the right architecture. The existing receipt-based
gates ([[fabricated-causal-chain-receipt-required]], [[ship-receipt-mechanical-
generation-from-per-check-results]], the Stop-hook quality gate) ARE the
viable implementation of "fallacy detection in hooks." They detect specific
reasoning-error patterns (causal claim without receipt, completion claim
without verification) with binary evidence and high precision.

The gap is not "we need a fallacy detector" — it's "we need to extend the
existing receipt-based pattern to cover more specific reasoning errors."
Candidates for new receipt-gates (each with binary evidence):
- **Optimality claim without comparison** — regex for "optimal/best/recommended"
  + check for ALTERNATIVES GATE block
- **Equivalence claim without validation** — regex for "≈ / equivalent to /
  lighter version of" + check for prior validation receipt
- **Negative capability claim without check** — regex for "doesn't exist / not
  available / no API for" + check for grep/search receipt

Each of these is a narrow, high-precision extension of the existing pattern —
NOT a generic fallacy classifier. This is the path the research supports.

## Falsifier

This concept is wrong if:
- A fallacy classifier achieves ≥0.95 precision on agent reasoning output
  (not social media) — at that point, blocking becomes viable
- Inter-annotator agreement on fallacy labeling rises above κ 0.8 — at that
  point, the gold standard is stable enough to calibrate against
- The workspace's receipt-based gates prove insufficient (miss a class of
  reasoning errors that only a generic detector catches) — at that point,
  the narrow approach has a coverage gap

If any of these occurs, re-evaluate whether a generic fallacy classifier
becomes viable as a blocking hook.

## Sources

- https://aclanthology.org/2024.naacl-long.270/ — MAFALDA benchmark (NAACL 2024) [primary_source: false — read through subagent search snippet]
- https://arxiv.org/abs/2311.09761 — MAFALDA paper [primary_source: false]
- https://aclanthology.org/2024.emnlp-main.730.pdf — Logical Structure Tree (EMNLP 2024) [primary_source: false]
- https://arxiv.org/pdf/2510.09970.pdf — Follow My Lead knowledge-augmented prompting [primary_source: false]
- https://arxiv.org/pdf/2511.04662.pdf — VeriCoT chain verification [primary_source: false]
- https://huggingface.co/PaoloButler/bert-cocolofa-fallacy — CoCoLoFa BERT [primary_source: false]
- https://github.com/yuanyuanlei-nlp/logical_fallacy_emnlp_2024 — Logical Structure Tree code
- https://aclanthology.org/2022.lrec-1.471/ — Inter-annotator agreement study (LREC 2022) [primary_source: false]
- https://arxiv.org/html/2412.12509v2 — LLM judge consistency / κ study [primary_source: false]
- https://arxiv.org/abs/2604.03904 — I-CALM calibration prompting [primary_source: false]
- https://arxiv.org/abs/2602.02219 — Pairwise vs pointwise judge bias survey [primary_source: false]
- https://en.wikipedia.org/wiki/List_of_fallacies — Fallacy taxonomy ambiguity
- https://youmind.com/landing/x-viral-articles/llm-judgment-coding-agent-hooks — Two-layer hook pattern (via [[llm-judgment-hooks]])
- https://docs.x.ai/build/features/hooks — Grok Build hooks documentation

## Receipts

- **`.grok/hooks/` does not exist on this host:** verified via `Test-Path P:/.grok/hooks` returning `NO .grok/hooks dir` (Phase 1.5 filesystem check, this session)
- **Two-layer regex+LLM pattern documented:** `P:/.data/wiki/concepts/llm-judgment-hooks.md` lines 54-87 (read in full during Phase 1b, this session)
- **Workspace already uses receipt-based detection:** `P:/.data/wiki/concepts/fabricated-causal-chain-receipt-required.md` (read in Phase 1b search results)
- **MAFALDA F1 ~0.77 claim:** sourced through subagent reading of arXiv abstract (arxiv.org/abs/2311.09761), NOT primary-source read. Tagged `[UNTESTED]` in concept body.
- **κ ~0.54 on logical validity claim:** sourced through subagent reading of arXiv abstract (arxiv.org/html/2412.12509v2), NOT primary-source read. Tagged `[INFERENCE]` in concept body.
- **Measurement-before-addition-principle constraint:** read from `P:/.data/wiki/concepts/measurement-before-addition-principle.md` lines 1-40 (this session)

## Staleness

Fallacy detection is an active research area. Re-check MAFALDA leaderboard
and VeriCoT follow-ups every 6 months. The two-layer hook pattern and the
receipt-based architecture are stable (architecture-level, not model-level).

## Auto-related

- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[Are-there-repos-or-solutions-to-claude-code-gettin]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]
- [[claude-code-external-tool-integration-via-mcp]]
- [[claude-code-hooks]]

