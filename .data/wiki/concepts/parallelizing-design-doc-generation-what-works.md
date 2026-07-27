---
title: "Parallelizing design-doc generation: what actually works (map-reduce, multi-agent, multi-candidate)"
created: 2026-07-27
source: session-019f9a3c (/www research on speeding up /design)
tags: [skill-design, parallel-agents, map-reduce, multi-agent, multi-candidate, fan-out, fan-in, synthesis, llm-behavior, design-documents, adoption-evidence, cross-host]
summary: >
  External research on whether parallel multi-agent orchestration can speed
  up design-doc generation. The operator's proposed pattern (parallel
  drafters each with their own scope → critic-friend merge) is the LEAST
  effective option. The evidence converges on three findings: (1) parallel
  section drafting rarely beats serial for a single coherent document —
  the reconciliation/merge step costs as much as the parallelism saved,
  and no major AI coding tool (Cursor, Devin, Copilot Workspace, Codex,
  Jules) parallelizes design-doc authoring; (2) multi-candidate generation
  (N writers in parallel) IS worth it when paired with FUSION (synthesis
  of complementary fragments), not SELECTION (picking the best whole) —
  FusioN beats BoN by up to +55% win-rate and can exceed the oracle best
  single sample; (3) parallelism pays off at the pre-write layer
  (parallel research/preflight/premise-verification, already designed
  into /www and /design Steps 0.5-0.8) and the post-write layer (parallel
  review dimensions), not the authoring layer. The optimal speedup for
  /design is: parallel pre-write + parallel review + a --fast mode that
  skips the review-revise loop for well-scoped designs. Diminishing
  returns on N-candidate generation plateau by N≈3-5; adaptive routing
  (easy prompts → N=1, hard → N=3+ synthesis) captures ~4× more
  efficiency than fixed N.
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
sources:
  - "LangGraph Orchestrator-Worker (Send API + reducer): https://docs.langchain.com/oss/python/langgraph/workflows-agents"
  - "LLMxMapReduce V2 (arxiv 2504.05732): https://arxiv.org/abs/2504.05732"
  - "Tree-Oriented MapReduce / DocTree (arxiv 2511.00489): https://arxiv.org/abs/2511.00489"
  - "STORM (arxiv 2402.14207, NAACL 2024): https://arxiv.org/abs/2402.14207"
  - "Chain-of-Agents (arxiv 2406.02818, NeurIPS 2024): https://arxiv.org/abs/2406.02818"
  - "MAST taxonomy (arxiv 2503.13657, NeurIPS 2025): https://arxiv.org/html/2503.13657v1"
  - "Snell et al. scaling test-time compute (arxiv 2408.03314): https://arxiv.org/abs/2408.03314"
  - "FusioN / Making Not Taking Best-of-N (arxiv 2510.00931): https://arxiv.org/abs/2510.00931"
  - "Self-Consistency (Wang et al. 2022, arxiv 2203.11171): https://arxiv.org/abs/2203.11171"
  - "Tree-of-Thoughts (Yao et al. 2023, arxiv 2305.10601): https://arxiv.org/abs/2305.10601"
  - "Cognition 'Don't Build Multi-Agents': https://cognition.com/blog/dont-build-multi-agents"
  - "Aider Architect mode: https://aider.chat/2024/09/26/architect.html"
  - "Cowork Forge (parallel design + codegen): https://dev.to/sopaco/from-idea-to-code-how-an-ai-multi-agent-system-works-like-a-team-to-write-software-568h"
  - "Anthropic contextual retrieval (long-context vs map-reduce): https://www.anthropic.com/engineering/contextual-retrieval"
  - "Wisdom and Delusion of LLM Ensembles: https://www.researchgate.net/publication/396923787"
relations:
  - target: wiki/concepts/adaptive-expansion-evidence-triggered-conditional-steps
    type: corroborates — conditional expansion fires on independence; design-doc sections are NOT independent
  - target: wiki/concepts/advanced-prompting-patterns-for-ai-agents
    type: extends — adds the document-generation-specific findings to the sub-agent context firewall pattern
  - target: wiki/concepts/brainstorming-ideation-with-llms
    type: refines — brainwriting (parallel fan-out) works for ideation, NOT for coherent long-form synthesis
  - target: wiki/concepts/adhd-parallel-frame-divergent-ideation-integration
    type: corroborates — N-frame fan-out for generation, but convergence requires a strong editor
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: informs — /design skill enhancement direction (parallel pre-write + parallel review + --fast mode)
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques
    type: extended-by — follow-up research adds synthesis/speed/constraint/iteration layers
---

# Parallelizing design-doc generation: what actually works

## Decision context

**Why this research was needed.** The operator asked whether `/design`
could be sped up by dispatching multiple subagents in parallel (each with
their own scope) before a critic-friend reviews and merges. The `/design`
loop currently takes 10-30 minutes per run, dominated by serial
write→review→revise→re-review cycles. The question: does parallel
multi-agent orchestration help?

**What alternatives were explored.** Four sub-areas researched in parallel:
(1) map-reduce/fan-out fan-in for long documents, (2) multi-agent
collaborative writing patterns, (3) how AI coding tools actually generate
design docs, (4) multi-candidate generation with critic/selector. The
disconfirmation pass searched for evidence against each emerging
conclusion.

**What the research changed.** It refuted the operator's initial framing
(parallel drafters → merge) as the optimal approach and pointed to three
higher-ROI interventions: parallel pre-write, parallel review, and a
`--fast` mode. It also identified FusioN (synthesis of N candidates) as a
genuine quality multiplier for open-ended generation — distinct from
Best-of-N selection.

## The three findings (disconfirmation-survived)

## Receipts

This concept is grounded in `/www` Phase 2 research (4 parallel minimax-m3
subagents, 2026-07-27) + disconfirmation pass (2 minimax-search queries).
Key evidence tiers:

- **[Tier 2 — peer-reviewed]** FusioN (arxiv 2510.00931), Chain-of-Agents
  (arxiv 2406.02818, NeurIPS 2024), MAST taxonomy (arxiv 2503.13657,
  NeurIPS 2025), Snell et al. scaling test-time compute (arxiv 2408.03314),
  Self-Consistency (arxiv 2203.11171), Tree-of-Thoughts (arxiv 2305.10601),
  LLMxMapReduce V2 (arxiv 2504.05732), Tree-Oriented MapReduce (arxiv
  2511.00489), STORM (arxiv 2402.14207, NAACL 2024).
- **[Tier 2 — vendor docs]** LangGraph orchestrator-worker + Send API
  (docs.langchain.com), Aider Architect mode (aider.chat), Cowork Forge
  (dev.to), Cognition "Don't Build Multi-Agents" (cognition.com).
- **[Tier 2 — practitioner evidence]** Cursor Plan Mode, Devin DAG,
  Copilot Workspace, OpenAI Codex PLANS.md, Google Jules, BMAD Method —
  all surveyed via vendor docs; all generate design docs serially.
- **[Tier 3 — internal measurement]** /www skill provenance: "4 parallel
  M3 subagents completed in ~90-140s" — measured 2026-07-24. Used to
  estimate parallel pre-write time savings for /design.
- **[INFERENCE]** The "~3-5 min saved" for parallel pre-write is derived
  from the /www measurement, scaled to /design's 4 pre-write steps. Actual
  savings unmeasured.
- **[INFERENCE]** The `--fast` mode quality cost is unmeasured — whether
  critical-friend-only review catches the same issues as the full loop
  needs A/B testing.
- **[UNKNOWN]** FusioN for design docs specifically is unvalidated — the
  FusioN evidence is from translation/Arena tasks, not design docs with
  strict cross-section consistency requirements.

### Finding 1: Parallel section drafting rarely beats serial for a single coherent document [HIGH confidence]

**Evidence:** Every major AI coding tool generates design docs **serially**:
Cursor Plan Mode (single agent), Devin DAG (serial planning, parallel
execution), GitHub Copilot Workspace (fully serial stages), OpenAI Codex
PLANS.md (single-agent living doc), Google Jules (serial plan per task),
BMAD (sequential persona handoffs). The one exception — Cowork Forge —
parallelizes *independent artifacts* (PRD + architecture + UX spec from a
shared brief), not sections of one document.

**Why:** LangGraph's orchestrator-worker pattern (the canonical fan-out
fan-in for documents) explicitly acknowledges that the default merge is
string concatenation, and coherence problems appear unless an LLM
synthesizer pass is added. That synthesizer pass "often costs as much as
the parallel writers combined." The MAST taxonomy (Cemri et al., NeurIPS
2025) found 41-87% failure rates in multi-agent systems, with the top
failure modes being information loss at handoffs and ignored peer feedback.

**The Anthropic counterpoint:** for documents that fit in a long-context
window with caching, plain long-context stuffing outperforms fan-out
patterns on coherence — because there is no merge problem. Fan-out wins
only when the document exceeds the window or when generation is from many
source documents.

**Cognition (Devin's makers) said it directly:** "Don't Build Multi-Agents."
Multi-agent shines when subproblems are truly independent; a single design
doc is not that.

### Finding 2: Multi-candidate generation IS worth it — but only with FUSION, not SELECTION [HIGH confidence]

**Evidence:** The FusioN paper (Khairi et al. 2025, arxiv 2510.00931) shows
that synthesizing complementary fragments from N candidates beats
Best-of-N selection by up to +55% win-rate on long-form tasks. Critically,
FusioN can **exceed the oracle best single sample** by mix-and-matching
complementary fragments — one candidate's strong thesis + another's
evidence + a third's prose beats any single whole draft. Sample efficiency:
FusioN gains ~+6% with N=2 that BoN needs ~2× the samples to match.

**Diminishing returns:** Quality gains scale roughly log(N) and plateau by
N≈16 (Snell et al. 2024). The jump from N=1 → N=3 captures a
disproportionate share of the lift. Adaptive routing (easy prompts → N=1,
hard → N=3+ synthesis) captures ~4× more efficiency than fixed N.

**Where it fails:** The "Wisdom and Delusion of LLM Ensembles" paper notes
the theoretical upper bound (83% above best single model) is rarely reached
in practice. FusioN requires a capable fusor LLM — weak models fail to
integrate well. Less helpful on tightly constrained tasks where diversity
adds little value.

**For the /design case:** generating 3 full design-doc candidates in
parallel and fusing them is token-expensive (3× generation + 1× fusion
pass) but produces a result no single candidate can match. The wall-clock
is same as one candidate (parallel), but the token cost is ~4×. This is
the quality-maximizing option, not the speed-maximizing option.

### Finding 3: Parallelism pays at the pre-write and post-write layers, not the authoring layer [HIGH confidence]

**Evidence:** The `/www` skill's own provenance validates parallel
pre-write: "4 parallel M3 subagents completed in ~90-140s, produced 35
techniques across 7 categories." The four pre-write steps in `/design`
(0.5 context firewall, 0.6 domain research, 0.7 preflight, 0.8 premise
verification) are largely independent and can all run in parallel.

**Post-write parallelism:** the reviewer's 11 check dimensions
(implementability, completeness, consistency, alternatives quality,
implementation plan, risk table, traceability, acceptance criteria,
premise labeling, file inventory, coupling inventory) are independent
and can be split across 3-4 parallel reviewers, then deduplicated.

**The authoring layer is serial by nature:** a coherent design requires
shared voice, consistent terminology, and a single decision-log thread.
Parallel authors produce contradictions that synthesis agents must
reconcile, and the reconciliation costs more than the parallelism saved.

## What this means for /design speedup

Ranked by ROI:

| Intervention | Time saved | Risk | Confidence |
|---|---|---|---|
| **Parallel pre-write** (Steps 0.5-0.8 in parallel) | ~3-5 min | Low — steps are independent by design | H |
| **Parallel review dimensions** (3-4 reviewers → deduplicate) | ~2-3 min | Medium — dedup needed | H |
| **`--fast` mode** (critical friend only, skip review-revise loop) | ~8-10 min | Medium — quality gate weaker | M |
| **Multi-candidate FusioN** (3 writers → fuse) | 0 min wall-clock, ~4× tokens | Low — but token-expensive | M |
| **Parallel section drafting** (operator's original idea) | NEGATIVE — merge costs more than parallelism saves | — | H (don't do it) |

**The operator's proposed pattern (parallel drafters → critic-friend merge)
is the LEAST effective option.** The evidence is unambiguous: the merge
step eats the gain for a single coherent document. The optimal speedup
combines the top 3 interventions: parallel pre-write + parallel review +
`--fast` mode for well-scoped designs.

## Method comparison (what people like and dislike)

### Map-reduce / fan-out fan-in for documents

| Method | Liked | Disliked |
|---|---|---|
| Skeleton-then-Expand | Outline editable before prose; scales to books | Mid-document drift without running context |
| LangChain Map-Reduce | Production-grade; cheap map + strong reduce | Loses cross-chunk dependencies; degrades for generative coherence |
| LLMxMapReduce V2 | +32.9% reference utilization on SurveyEval | Brittle schema; expensive recursive refinement |
| Tree-Oriented MapReduce | Captures long-range dependencies | Slow for deep trees; validated on QA not generation |
| LangGraph Orchestrator-Worker | First-class Send API + reducer | Merge is concatenation; needs costly synthesizer pass |
| STORM | +25% organization on FreshWiki | Source bias; still needs human editing |
| Multi-Agent Section Drafting | Specialization improves per-section quality | Coordination overhead; residual inconsistencies |

### Multi-agent collaborative writing

| Pattern | Quality evidence | Failure mode |
|---|---|---|
| Chain-of-Agents | +10% on long-doc QA | Information loss at handoffs |
| Critic-Revise | Reduces self-bias | Critics share blind spots; local optima |
| Debate-to-Write | Higher diversity on essays | 3-5× cost; shallow persona diversity |
| Mixture-of-Agents | SOTA on AlpacaEval | Flattens distinctive voice; optimizes for judges |
| Role-Based (CrewAI) | More consistent structured docs | Quality fully a function of upfront design |
| Sequential Co-Authoring | Maintains narrative across handoffs | Style drift; worse than single-agent for long outputs |

### Multi-candidate generation

| Pattern | Gain | Cost | Where it fails |
|---|---|---|---|
| Best-of-N (selection) | log(N), plateaus at N≈16 | N× tokens | Picks a monolith; can't combine fragments |
| FusioN (synthesis) | Up to +55% vs BoN; exceeds oracle | (N+1)× tokens | Needs capable fusor; domain-dependent |
| Self-Consistency | +17.9% GSM8K | N× tokens | Only works for discrete/comparable answers |
| Tree-of-Thoughts | 74% on Game of 24 vs 9% CoT-SC | ~same tokens | Requires problem-specific decomposition |
| Adaptive routing | ~4× efficiency vs fixed N | Needs difficulty estimator | Frontier shifts as models improve |

## Falsifier

This concept is wrong if:

- A future study shows parallel section drafting beats serial for single
  coherent documents (would overturn Finding 1). No such study found.
- FusioN is shown to underperform BoN on long-form tasks in a controlled
  comparison (would overturn Finding 2). Current evidence strongly favors
  FusioN.
- The /design pre-write steps are shown to have hidden dependencies that
  break parallel dispatch (would overturn Finding 3's pre-write claim).
  The steps are designed to be independent; no dependencies found.

**Discriminating test for /design:** implement parallel pre-write + parallel
review. Measure wall-clock reduction and quality change (review-findings
count, critical-friend verdict). If quality degrades, the parallelism
introduced inconsistencies the serial loop would have caught.

## Honest trade-offs

**What the research does NOT prove:**

1. **The absolute time savings are estimated, not measured.** The
   "~3-5 min saved" for parallel pre-write is derived from the /www skill's
   measured 90-140s for 4 parallel M3 subagents, scaled to /design's 4
   pre-write steps. Actual savings depend on model selection and step
   independence.

2. **The `--fast` mode quality cost is unmeasured.** Skipping the
   review-revise loop saves ~8-10 min but weakens the quality gate. Whether
   critical-friend-only review catches the same issues as the full loop is
   unknown — it needs A/B testing on real designs.

3. **FusioN for design docs specifically is unvalidated.** The FusioN
   evidence is from translation/Arena tasks. Design docs have stricter
   internal-consistency requirements (the Traceability Matrix, File Change
   Inventory, and Coupling Inventory must all agree). FusioN's fragment
   combination may produce cross-section contradictions that the existing
   consistency sweep would need to catch.

## Related

- [[adaptive-expansion-evidence-triggered-conditional-steps]] — conditional expansion fires on independence; design-doc sections are NOT independent
- [[advanced-prompting-patterns-for-ai-agents]] — sub-agent context firewall pattern (validated for research, not synthesis)
- [[brainstorming-ideation-with-llms]] — brainwriting works for ideation, not for coherent long-form
- [[adhd-parallel-frame-divergent-ideation-integration]] — N-frame fan-out for generation, convergence requires strong editor
- [[agentic-sdlc-skill-lifecycle-architecture]] — /design skill enhancement direction informed by this research
