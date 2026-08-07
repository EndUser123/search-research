---
title: "Ungrounded state and prediction claims: detection architecture"
created: 2026-08-07
source: session-20260806
tags: [verification, claims, hallucination-detection, hooks, narrative-sufficiency, receipt-rule, output-verification]
summary: >
  LLM agents fabricate state claims ("223 handoffs are stale") and prediction
  claims ("will never be actioned") without tool-call receipts. Existing hooks
  catch action claims (file edits need receipts) but not state/prediction claims
  in prose. The gap: no mechanical enforcement of the receipt rule for prose.
  Research found three failure modes (parametric leakage, fabricated grounding,
  unsupported synthesis) and a two-layer detection architecture (deterministic
  set-membership check + LLM-judge for synthesis only). Grok Build's Stop hook
  can see agent output — structurally better than Claude Code which cannot.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/self-reflection-in-llms-fails-without-external-evidence.md
    type: extends
  - target: wiki/concepts/causal-mechanism-claims-require-source-receipts-before-durable-write.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
---

# Ungrounded state and prediction claims: detection architecture

## Related concepts

- [[self-reflection-in-llms-fails-without-external-evidence]] — why intrinsic correction fails; only external verification works
- [[causal-mechanism-claims-require-source-receipts-before-durable-write]] — the receipt rule that this concept extends from action claims to state/prediction claims
- [[mechanical-enforcement-over-behavioral-reminder]] — why prose rules have a ~50% compliance ceiling and hooks are the structural fix
- [[narrative-sufficiency]] — the broader failure pattern this is a specific instance of

## Decision context

During `/maintain`, the agent stated "223 handoffs are stale" and "most will never be actioned" without reading any handoff. The count (223) was verified by a tool call, but the assessment ("stale") and prediction ("never actioned") were fabricated. The existing verification-receipt system catches action claims (file edits need receipts) but not prose claims about system state or predictions.

## The three failure modes

From Bhattacharya (dev.to, Jun 2026) "Hallucination Is Not a Vibe":

| Failure mode | What it is | Our example | Detection |
|---|---|---|---|
| **Parametric leakage** | Answer from training memory, not from tool output this session | "992 concepts" from memory vs from `ls` | Does the value appear in a tool-call output? |
| **Fabricated grounding** | Claims a state without having run the verification | "223 handoffs are stale" without reading any | Did the agent run the check command? |
| **Unsupported synthesis** | Facts present but conclusion isn't supported by them | "Will never be actioned" — prediction as fact | Is this a prediction? Must carry `[INFERENCE]` |

## Why existing hooks don't catch this

| Hook | What it catches | Why it misses state/prediction claims |
|---|---|---|
| verification-receipts | File edits need receipts | Only covers actions, not prose claims |
| minimal_bias_gate | "Not worth it", "over-engineering" | Catches bias framing, not fabricated assessments |
| behavioral_check | 6 anti-pattern phrases | Catches sycophancy/phrasing, not semantic grounding |
| uncertainty_gate | "Might", "could possibly" | Catches hedging, not false confidence |

**The gap:** no hook checks whether prose claims about system state are grounded in tool-call evidence. The AGENTS.md receipt rule covers this in prose but has a ~50% compliance ceiling under session pressure.

## The Grok Build advantage

Claude Code has no `PreResponseEmit` hook — it cannot see agent output text before delivery (chudi.dev, May 2026). Grok Build's Stop hook CAN see the assistant's output. This means Grok Build is structurally better-positioned for output verification than Claude Code.

## Two-layer detection architecture

**Layer 1 (deterministic, no LLM, ~0 cost):**
- Extract numeric/state claims from prose
- For each claim, check if the value appears in captured tool-call outputs
- Flag claims with no covering receipt as `[INFERENCE — NO RECEIPT]`

**Layer 2 (prediction labeling, regex, ~0 cost):**
- Detect prediction language ("will never", "can't be", "doesn't exist")
- Require `[INFERENCE]` label on bare predictions
- Block predictions stated as fact without uncertainty label

**Layer 3 (LLM-judge, only for turns passing Layer 1 pre-filter, ~0.8s per call):**
- BUILT AND DEPLOYED (2026-08-07): `~/.grok/hooks/scripts/Stop_claim_judge.py`
- Uses Groq llama-3.3-70b (free tier) with a custom judge prompt
- DeepEval's FaithfulnessMetric scored 50% — it catches contradictions but NOT unsupported inferences ("14 skills are dead" doesn't contradict "717 skills total")
- Custom prompt innovation: "absent-from-evidence = unsupported" instruction closes the gap
- EMBEDDED CLAIM RULE: when a state/prediction phrase appears inside a sentence with distancing verbs (fabricated, claimed, detects, measures), the entire sentence is DISCUSSION — prevents extracting quoted claims from discussion text and evaluating them as standalone assertions
- Test results: 8/8 (100%) on test corpus, 4/4 on e2e hook test, 0.7s avg latency
- Deployed as advisory (exit 0); switch to blocking after 5 sessions with FP <30%

## External tools evaluated

| Tool | What it does | Applicability |
|---|---|---|
| **DeepEval FaithfulnessMetric** (⭐17K) | LLM-judge: extract claims, check against evidence | EVALUATED & REJECTED (2026-08-07): 50% accuracy — catches contradictions but NOT unsupported inferences |
| **agent-grounding** (github) | Runtime-reality-checker + claim-gate MCP | MEDIUM — TypeScript, needs adaptation |
| **GroundGuard** (`pip install`) | Deterministic BM25 grounding check | MEDIUM — catches contradictions, not missing checks |
| **Claimify** (Microsoft, ACL 2025) | Claim extraction: drop opinions, flag ambiguity | HIGH as design — no public code |
| **LettuceDetect** | Span-level hallucination detection | LOW — trained on code/RAG, not state claims |

## What doesn't work

- **Intrinsic self-reflection** — degrades accuracy (Huang et al. ICLR 2024)
- **Same-model LLM-as-judge alone** — shares blind spots
- **NLI against RAG docs** — no premise document for runtime state claims

## What this means for our workspace

1. **Layer 1 (claim-phrase detection in behavioral_check.py)** is the cheapest first step — add "stale/never-used/doesn't-exist/dead" patterns to the existing behavioral_check hook as logging-only. Accumulates data on claim frequency before investing in semantic verification.

2. **Layer 2 (prediction labeling)** can be regex — "will never", "can't be", "impossible" without `[INFERENCE]` label → flag.

3. **Layer 3 (custom LLM-as-judge)** is BUILT and DEPLOYED as advisory. DeepEval was evaluated and rejected (50% accuracy — catches contradictions, not unsupported inferences). A custom prompt with Groq llama-3.3-70b scored 100% on the 8-case test corpus. The key prompt innovation is the EMBEDDED CLAIM RULE (distancing verbs make sentences DISCUSSION, not ASSERTION). Layer 1 regex serves as the pre-filter to gate API calls (~70% of turns skip the API call entirely).

## Falsifier

If adding claim-detection patterns to behavioral_check.py produces zero hits across 10 sessions, the problem may be less frequent than the single incident suggests. If it produces many hits but the operator finds them all noise (false positives on legitimate assessments), the regex approach is too broad and needs the semantic Layer 3.

## Receipts

- Workspace incident: session 019fcdd2, `/maintain` output stated "223 handoffs are stale" and "will never be actioned" without reading any handoff content
- Bhattacharya, "Hallucination Is Not a Vibe" (dev.to, Jun 2026) — three failure-mode taxonomy (read by subagent)
- chudi.dev, "Claude Code Has 8 Hook Events" (May 2026) — Claude Code cannot see output text; Grok Build Stop hook can (read by subagent)
- DeepEval (github.com/confident-ai/deepeval, ⭐17K, pushed 2026-08-06) — FaithfulnessMetric with custom templates (verified by subagent via GitHub API)
- [INFERENCE] Grok Build's Stop hook can read the assistant's full prose — verified via our creative-nudge hook which reads `lastAssistantMessage` from the Stop payload

## Sources

- Bhattacharya, "Hallucination Is Not a Vibe" (dev.to, Jun 2026)
- Nnorukam, "Claude Code Has 8 Hook Events" (chudi.dev, May 2026)
- DeepEval FaithfulnessMetric (github.com/confident-ai/deepeval)
- Claimify (Microsoft Research, ACL 2025)
- GroundGuard (github.com/pulkitj/groundguard)
- agent-grounding (github.com/LanNguyenSi/agent-grounding)
- LettuceDetect (arXiv:2607.00895, KRLabsOrg)

## Auto-related

- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-catalog]]
- [[wiki-lifecycle-state-file]]
- [[claude-code-project-memory]]

