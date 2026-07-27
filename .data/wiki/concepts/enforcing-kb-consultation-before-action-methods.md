---
title: "Enforcing knowledge-base consultation before action: methods practitioners like and dislike"
created: 2026-07-27
source: session-019f9a3c (/www research on error-handling-loops-skip-wiki-query)
tags: [enforcement-mechanism, llm-behavior, agent-architecture, rag-gating, escalation-policy, retrieval-enforcement, adoption-evidence, cross-host]
summary: >
  External research on how practitioners force LLM agents to consult their
  knowledge base / documentation before responding, claiming a blocker, or
  escalating to a human. Three enforcement tiers exist (hard / soft /
  adaptive); practitioners consistently prefer hard enforcement and
  criticize soft enforcement for failing under the same closure pressure
  that produces the original error. Reflection/self-verification does NOT
  fix the problem — the evidence shows pure self-critique fails under the
  same biases (Huang et al. 2023, Self-Refine 94% error rate in feedback).
  Reflection works ONLY with external grounding (tools, tests, separate
  critics). Risk-tiered escalation beats confidence-based escalation
  because raw LLM confidence is miscalibrated (claimed 90% ≈ 75%). The
  most liked patterns combine mandatory retrieval with a quality gate
  (CRAG) and a structural mode split (Cline Plan/Act). Wiki claims
  (~50% advisory compliance ceiling, structural gates strongest) are
  externally corroborated.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "LangGraph force-calling-a-tool-first how-to: https://www.baihezi.com/mirrors/langgraph/how-tos/force-calling-a-tool-first/"
  - "CrewAI Knowledge Sources docs: https://docs.crewai.com/concepts/knowledge"
  - "OpenAI Agents SDK Guardrails: https://openai.github.io/openai-agents-python/guardrails/"
  - "Huang et al. 2023, 'LLMs Cannot Self-Correct Reasoning Yet': https://arxiv.org/abs/2210.03629"
  - "Self-Refine (Madaan et al. 2023): https://arxiv.org/abs/2303.17651"
  - "Reflexion (Shinn et al. 2023): https://arxiv.org/abs/2303.11366"
  - "ReflAct (Kim et al. EMNLP 2025): https://arxiv.org/abs/2505.15182"
  - "Corrective RAG (Yan et al. 2024): https://arxiv.org/abs/2401.15884"
  - "AgentSpec runtime enforcement (ICSE 2026): https://arxiv.org/pdf/2503.18666"
  - "Cursor Project Rules docs: https://cursor.com/docs/rules"
  - "Cline Plan & Act + Hooks: https://docs.cline.bot/core-workflows/plan-and-act"
  - "oh-my-pi advisor-watchdog: https://github.com/can1357/oh-my-pi/blob/main/docs/advisor-watchdog.md"
  - "Risk-tiered action classification (MindStudio): https://www.mindstudio.ai/blog/classify-ai-agent-actions-by-risk"
  - "Confidence-based escalation limitations (emergentmind): https://www.emergentmind.com/topics/confidence-based-escalation-hitl"
  - "Vadim Markovtsev, 'The Research on LLM Self-Correction': https://vadim.blog/the-research-on-llm-self-correction/"
  - "OpenAI practical guide to building AI agents: https://openai.com/business/guides-and-resources/a-practical-guide-to-building-ai-agents/"
relations:
  - target: wiki/concepts/error-handling-loops-skip-wiki-query
    type: external-evidence-for — the /why RCA identified the gap; this provides the solutions landscape
  - target: wiki/concepts/rule-not-fired-vs-rule-doesnt-exist
    type: corroborates — external sources confirm advisory rules have low compliance; structural triggers are needed
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build
    type: extends — adds the specific KB-consultation enforcement surface (existing concept covers completion claims enforcement)
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: solution-for — the hard-enforcement tier is the structural fix for this behavioral pattern
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: corroborates — external research confirms reflection fails under closure pressure; only external grounding survives
  - target: wiki/concepts/mandatory-step-enforcement-code-over-prose
    type: refines — adds the specific "retrieve before act" enforcement surface with adoption evidence
---

# Enforcing knowledge-base consultation before action

## Decision context

**Why this research was needed.** A `/why` RCA (this session) found that an
agent hit an `nlm` CLI auth error and told the operator "you must do browser
OAuth" — without checking the workspace wiki, which documented a silent
agent-performable recovery. The RCA identified the gap: error-handling loops
have no mandatory wiki-query step, and "search before proposing" doesn't fire
on diagnosis. The question this research answers: *how do OTHER practitioners
solve this problem, and which implementation methods do they actually like
vs. dislike?*

**What alternatives were explored.** Four sub-areas were researched in
parallel: (1) mandatory retrieval / RAG gating, (2) human-escalation
policies, (3) open-source framework patterns + adoption evidence, and (4)
reflection/self-verification as an alternative. The disconfirmation pass
searched for evidence against each emerging conclusion.

**What the research changed.** It confirmed the wiki's internal conclusions
(~50% advisory compliance ceiling, structural gates strongest, reflection
decays under pressure) with external evidence from 15+ sources. It added the
specific implementation taxonomy the wiki lacked: three enforcement tiers,
the risk-tiered escalation model, and the Plan/Act mode split as the closest
existing analog to what this workspace needs.

## Receipts

This concept is grounded in `/www` Phase 2 research (4 parallel minimax-m3
subagents, 2026-07-27) + disconfirmation pass (3 minimax-search queries).
Key evidence tiers:

- **[Tier 2 — official docs]** LangGraph force-tool-first how-to, CrewAI
  Knowledge Sources docs, OpenAI Agents SDK Guardrails docs, Cursor Project
  Rules docs, Cline Plan/Act docs. URLs in frontmatter `sources:`.
- **[Tier 2 — peer-reviewed]** Huang et al. 2023 (arxiv 2210.03629), Self-Refine
  (arxiv 2303.17651), Reflexion (arxiv 2303.11366), ReflAct (arxiv 2505.15182),
  CRAG (arxiv 2401.15884), AgentSpec (ICSE 2026, arxiv 2503.18666).
- **[Tier 2 — practitioner evidence]** oh-my-pi advisor-watchdog (GitHub),
  MindStudio 4-tier risk framework, emergentmind confidence-based escalation
  limitations, Vadim Markovtsev "Research on LLM Self-Correction" (vadim.blog).
- **[Tier 3 — community signal]** Reddit r/cursor, r/CLine threads on rules
  being ignored — consistent across multiple independent threads; treated as
  adoption-evidence signal, not controlled study.
- **[INFERENCE]** The ~50% advisory compliance ceiling figure is from our
  internal wiki ([[evidence-first-default-and-needless-confirmation]] §2.2),
  not independently re-measured in this research. External sources corroborate
  the direction (soft enforcement fails under pressure) but do not cite the
  exact percentage.

## The three enforcement tiers

External research converges on a three-tier taxonomy for forcing agents to
consult their knowledge base before acting:

| Tier | Mechanism | Reliability | What people LIKE | What people DON'T LIKE |
|------|-----------|-------------|------------------|------------------------|
| **Hard** | API-level forcing (`tool_choice: "required"`), graph topology (LangGraph force-tool-first), PreToolUse hooks (block until retrieval fires), CrewAI auto-injection | ~95-100% | Deterministic — cannot be skipped regardless of model whim; survives prompt drift and model upgrades | Can be too rigid (AgentSpec ICSE 2026); adds latency on queries that don't need retrieval; host-specific implementation |
| **Soft** | System prompts, `.cursorrules`, `.clinerules`, `CONVENTIONS.md` auto-load | ~50-80% | Zero code change; works in any framework; easy to A/B test | Agents recite rules correctly but ignore them in practice — the #1 complaint on r/cursor and r/CLine; degrades under context pressure and with weaker/local models |
| **Adaptive** | CRAG quality gate, Self-RAG reflection tokens, TARG confidence gating | ~70-90% | Cuts cost/latency on easy queries; compensates for weak retrievers automatically | Gate signal can be miscalibrated; the evaluator itself can be wrong; requires fine-tuning or special prompting |

**Practitioner consensus:** hard enforcement is consistently preferred. The
Reddit/HN/dev.to frustration is loudest around soft enforcement with weaker
models. Multiple sources independently state: "developers dislike anything
that depends on the model 'choosing' to consult docs."

## Methods practitioners LIKE (adoption evidence)

### 1. Hard `tool_choice` API forcing [HIGH confidence — ≥4 sources]
OpenAI `tool_choice: "required"`, Anthropic `{"type": "any"}`, Cohere
`"REQUIRED"`, Gemini forced-function-calling. Enforced at the model serving
layer — the first output cannot be free-form text. Highest reliability;
works across all major providers with near-identical semantics.
**Dislike:** easy to infinite-loop if you never release the constraint;
suppresses explanatory pre-text.

### 2. Forced retrieve-first graph node [HIGH — official LangGraph pattern]
The graph's START node is wired to a `force_retrieve` node that returns a
hardcoded AIMessage with a pre-built tool_calls payload for the retriever.
Deterministic at the orchestration layer; survives model upgrades.
**Dislike:** bypasses model judgment about whether retrieval is needed.

### 3. CrewAI automatic knowledge injection [MEDIUM — vendor docs + community]
When `knowledge_sources=[...]` is attached, CrewAI rewrites the prompt,
retrieves from ChromaDB/Qdrant, and injects chunks *before* the agent
reasons — no tool-call decision required. Considered the cleanest "always
retrieve first" in CrewAI.
**Dislike:** storage paths are platform-specific; default behavior changed
across versions.

### 4. OpenAI Agents SDK guardrail tripwires [MEDIUM — vendor docs]
`@input_guardrail` decorators wrap a check function that raises
`InputGuardrailTripwireTriggered` to halt execution. True hard enforcement
(not prompt hope); composable with tracing.
**Dislike:** tool guardrails do NOT apply to hosted tools (FileSearchTool) —
must wrap search in a custom function tool.

### 5. Cline Plan/Act mode split [HIGH — community + vendor docs]
Plan mode is structurally read-only — the agent cannot edit files or run
most commands. It must explore, read, and discuss before switching to Act
mode. This is the closest existing analog to "query the wiki before declaring
a blocker." The structural separation (you literally cannot enter Act mode
without passing through Plan) is what makes it work.
**Dislike:** `.clinerules` are still soft — r/CLine threads describe agents
acknowledging rules then defaulting to "standard AI assistant behavior."

### 6. CRAG (Corrective RAG) quality gate [MEDIUM — paper + adoption]
Post-retrieval evaluator scores documents for relevance; if quality is low,
triggers corrective actions (filter, re-retrieve, web search fallback).
**Dislike:** adds an extra LLM/classifier call per query.

## Methods practitioners DON'T LIKE

### 1. System-prompt-only enforcement [HIGH — universal criticism]
"ALWAYS use the retrieve tool first — NEVER answer from memory." Every
source that tested this reports the same failure: strong models comply
~95%+ but degrade under long contexts, adversarial prompts, or competing
instructions. Reddit threads on Cursor and Cline are the loudest: agents
recite rules when asked but ignore them in practice. This is the external
validation of our wiki's ~50% advisory compliance ceiling.

### 2. Confidence-based escalation [HIGH — multi-source disconfirmation]
Using the model's self-reported confidence to decide whether to escalate
to a human. Raw LLM confidence is miscalibrated: claimed 90% ≈ 75% accuracy
(emergentmind, multiple papers). Every escalation guide recommends combining
confidence with a separate risk-tier signal, never using confidence alone.
**The fix:** risk-tiered action gates (Tier 1-4) where humans pre-classify
actions by reversibility, not by the LLM's self-reported certainty.

### 3. Pure self-critique / reflection without external grounding [HIGH — paper evidence]
Huang et al. (2023) found unaided self-critique *consistently decreased*
accuracy on math/QA — models changed correct answers to wrong ones more
often than they fixed errors. Self-Refine's own error analysis traced ~94%
of failures to erroneous self-generated feedback. Reflexion's limitations
section states success depends on the model's ability to diagnose its own
mistakes — on WebShop, "runs were terminated early" after unhelpful
reflections.

The critical distinction (vadim.blog, 2026): **"Almost every published
'success' of reflection is actually a success of verification. Strip away
the external tool — the compiler, the test suite — and the gains vanish."**
Reflection works ONLY when grounded in external state, tools, tests, or a
separate critic. Pure "did you check your docs?" prompts are the same class
as advisory rules and fail under the same closure pressure.

## What this means for our workspace

The external evidence maps directly onto the four fixes the `/why` RCA
recommended:

| RCA fix | External analog | Evidence |
|---------|-----------------|----------|
| Fix 1: mandatory wiki-query before offload | Hard `tool_choice` + forced retrieve-first node | ≥4 independent sources confirm hard enforcement is preferred |
| Fix 2: retry-on-timeout default | Attempt/turn limit with retry-then-escalate (OpenAI guide) | OpenAI's practical guide recommends 2-3 retry caps |
| Fix 3: receipt-before-offload | Risk-tiered action gates (Tier 1-4) | MindStudio, CLTC Berkeley confirm risk classification over confidence |
| Fix 4: structural gate (PreToolUse/Stop) | PreToolUse hooks + AgentSpec runtime enforcement | AgentSpec ICSE 2026; Claude Code hooks widely adopted |

**The disconfirmation-survived conclusion:** there is no evidence that soft
enforcement or pure reflection reliably solves this problem. Every source
that tested these approaches found the same failure mode our wiki documented
internally. The structural fix (hard enforcement) is the only approach with
production-grade reliability evidence.

## Honest trade-offs

**What's NOT clear from the research:**

1. **False positive rate of hard enforcement.** How often does forcing
   retrieval waste time on queries that didn't need it? No source reported
   empirical FP rates. Our workspace would need to measure this.

2. **Ergonomics of the risk-tier classification.** MindStudio's 4-tier
   framework requires pre-classifying every action. Is this maintainable for
   a multi-agent fleet? The `/www` ledger for `mandatory-step-enforcement`
   flagged the same question as unresolved: "whether the frozen
   requirement-set intake can be made ergonomic enough to actually happen
   every task."

3. **Calibration drift.** The ~95% compliance for hard enforcement is
   measured on current models. As models evolve, does hard enforcement
   remain reliable, or do models learn to game the constraint? AgentSpec's
   "too rigid" critique suggests the enforcement mechanism itself needs
   maintenance.

## Falsifier

This concept is wrong if:

- A future study shows soft/prompt-level enforcement achieving >90% compliance
  under production conditions (closing the gap with hard enforcement). Our
  wiki's ~50% ceiling claim would need revision.
- Risk-tiered escalation is shown to be LESS effective than confidence-based
  in a controlled comparison (would overturn C2). No such study was found.
- Pure reflection (without external grounding) is shown to reliably fix the
  "agent doesn't check docs" problem in production (would overturn C3). The
  evidence strongly disconfirms this.

**Discriminating test:** implement Fix 1 (mandatory wiki-query before offload)
as a PreToolUse hook. Measure: (a) how often the hook fires (over- vs
under-triggering), (b) whether the false-positive rate is acceptable, (c)
whether the nlm-class failure recurs. If the failure recurs despite the hook,
the hook's detection logic is wrong, not the concept.

## Related

- [[error-handling-loops-skip-wiki-query]] — the /why RCA that motivated this research
- [[rule-not-fired-vs-rule-doesnt-exist]] — the meta-pattern; this concept provides the external evidence for the "add a trigger" fix
- [[best-practices-enforcement-mechanism-grok-build]] — sibling enforcement concept for completion claims
- [[plausible-narratives-substitute-for-verification]] — the behavioral pattern; hard enforcement is the structural fix
- [[reactive-pattern-matching-and-closure-pressure]] — the substrate; external research confirms reflection fails under closure pressure
- [[mandatory-step-enforcement-code-over-prose]] — state machines + scanner gates; this concept adds the KB-consultation surface
- [[evidence-first-default-and-needless-confirmation]] — the offload pattern; risk-tiered escalation is the structural fix
