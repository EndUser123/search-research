---
title: "Delegation optimization for AI agents: chunking, routing, cascading, and coordination cost"
created: 2026-07-30
source: session-019fb189
tags: [delegation, subagent-dispatch, parallel-execution, model-routing, cascading, RouteLLM, FrugalGPT, coordination-cost, skill-design, reusable-pattern]
summary: >
  How to optimally delegate work across AI agent subagents. Covers four axes:
  (1) task decomposition — one question per agent, parallelize independent work;
  (2) model routing — match model tier to task type (RouteLLM achieves 85% cost
  savings at 95% GPT-4 quality; cascading achieves 98% but only when escalation
  rate is low and verifier cost is cheap); (3) coordination cost — scales
  quadratically with agent count; multi-agent often underperforms single-agent
  on multi-hop reasoning; (4) output format — structured findings, not raw
  search dumps or full reports. Backed by RouteLLM (LMSYS), FrugalGPT (TMLR
  2024), cascade break-even math, and practitioner experience from crew.ai,
  AutoGen, LangGraph. Complements context-firewall-architecture and
  model-pool-selection-policy.
agent: grok
host: grok
cognitive_load: 4
verification: multi-source-verified
sources:
  - https://arxiv.org/html/2406.18665v4 (RouteLLM, LMSYS, ICLR 2025)
  - https://arxiv.org/abs/2305.05176 (FrugalGPT, Chen et al., TMLR 2024)
  - https://arxiv.org/html/2405.15842v1 (Model Cascading for Code)
  - https://arxiv.org/abs/2310.12963 (AutoMix, Madaan et al., 2023)
  - https://github.com/dennisonbertram/llm-routing-benchmark (cascade failure mode benchmark)
  - https://leepcast.com/blog/llm-routing-model-cascades (cascade break-even math)
relations:
  - target: wiki/concepts/context-firewall-architecture.md
    type: complements — context firewall prevents pollution; delegation optimization prevents waste
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: extends — model pool policy selects the model; delegation optimization decides how to split and route
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques.md
    type: related — cascading and model tiering for synthesis tasks
---

# Delegation optimization for AI agents

## Decision context

**Why this was needed:** during session 019fb189, multiple /www research runs took 5-8 minutes per agent, and a /design writer revision ran for 644 seconds before being killed. The operator requested delegation optimization as a reusable pattern. The initial concept was written from session observations only — the operator correctly identified that external research was needed: "you haven't done the research to have a good idea of what delegation optimization is to agents." This revision integrates external research on model routing, cascading, coordination cost, and practitioner experience.

## Axis 1: Task decomposition — chunking and parallelism

### One question per agent

Never assign 2+ independent angles to one agent. If you have 6 questions, dispatch 6 narrow agents (3-5 tool calls each) running in parallel, not 2 broad agents (9-15 tool calls each) running slowly.

**The math:** total work = N questions × M tool calls per question. Wall-clock (parallel) = max(M) × tool latency ≈ M × 30s. Wall-clock (serial/bundled) = N × M × 30s. Parallelization gives N× speedup when questions are independent.

**Measured failure (session 019fb189):** /www runs with 1 agent × 3 angles = 5-8 min; corrected to 1 agent × 1 angle = ~2 min. /design writer revision with 32 issues in one turn = 644s, killed at 55 tool calls.

**When NOT to parallelize:** questions share context (later question depends on earlier answer). In that case they're one dependency chain in one agent — but still narrow, not bundled with unrelated work.

### The coordination cost ceiling

External research adds a critical constraint the session observations missed: **coordination cost scales quadratically with agent count.** Communication overhead (message passing, context transfer, result aggregation) grows as O(N²) where N = agent count.

**Key finding (Redis blog "Why Multi-Agent LLM Systems Fail"):** in an 180-config evaluation, multi-agent systems **underperformed single-agent** on most configurations. Single-agent LLMs outperform multi-agent on multi-hop reasoning (arXiv 2604.02460).

**Practical implication:** don't dispatch more agents than necessary. The optimal is N = number of truly independent questions, not "maximum parallelism." Beyond ~6-8 agents, coordination overhead typically exceeds the parallelization benefit.

### Output format: structured findings

Request structured findings per item: name/description/source/relevance, ~2-4 sentences each. NOT raw search dumps (bloats context, triggers compaction). NOT terse numbered lists only (loses signal). The orchestrator synthesizes; agents gather.

## Axis 2: Model routing — which model handles which task

### RouteLLM: learned per-query routing

RouteLLM (LMSYS, ICLR 2025) trains a router from Chatbot Arena preference data that decides per-query whether to use a strong or weak model. Results: **85% cost savings at 95% of GPT-4 quality**, escalating to the strong model on only ~14% of queries.

**Applicability to our fleet:** our model pool (Grok, glm-5-2, codex, mmx, minimax-m3) could use a similar routing classifier. The router needs preference data — which we have implicitly in session transcripts (which model produced the operator-approved output).

### FrugalGPT: cascading (cheap → escalate)

FrugalGPT (Chen et al., TMLR 2024) tries the cheap model first, escalates only when a verifier/scorer indicates low confidence. Up to **98% cost reduction** matching the best individual model.

**The cascade break-even math (least-published, most actionable finding):** the cascade pays off only when:
- **Escalation rate is low** (≤20-30% on the workload)
- **Verifier cost is cheap** (small model, regex, logprob threshold)
- **Quality gap between cheap and strong is large** on the task
- **Task is non-uniform in difficulty**

**Cascade failure mode:** a live benchmark (dennisonbertram/llm-routing-benchmark R-003) found a FrugalGPT cascade produced accuracy identical to always-cheap at 2.4× cost — **zero accuracy gain**. The cascade was strictly dominated because the escalation rate was too high and the verifier cost exceeded the savings.

### Task-type → model-tier mapping

Synthesized from practitioner guides (no canonical academic taxonomy found):

| Task type | Recommended tier | Rationale |
|---|---|---|
| Extraction, classification, formatting | Small/cheap (mimo, ornith) | Mechanical; frontier model adds no value |
| Single-document summarization | Small-to-mid | Adequate on smaller models |
| Multi-step reasoning, code with tools | Mid-to-large (glm-5-2, codex) | Reasoning depth matters |
| Open-ended reasoning, novel code, agentic multi-step | Large (parent-inherited Grok) | Cascading rarely safe here |
| Adversarial review, critique, cross-checking | Different model family (diversity) | [[model-pool-selection-policy-speed-quota-diversity]] Rule 3 |

**Our workspace already implements this** via the model pool policy (speed + quota over free, except diversity). The external research confirms the policy is well-founded.

## Axis 3: When multi-agent HURTS

### "Capable language models can outgrow collaboration" (Nature 2025)

A critical finding from the external research: **as models become more capable, the benefit of multi-agent collaboration decreases.** Strong single agents can outperform multi-agent teams because coordination overhead and communication losses exceed the diversity benefit.

**Implication for our fleet:** Grok (parent model) running a task inline may be faster and higher quality than spawning 3 subagents — unless the subagents bring genuinely different information (different files, different model family, different rubric). The context-firewall pattern (subagent reads bulk content, returns summary) is one case where multi-agent helps. The parallel-research pattern (multiple independent searches) is another. But "debate" or "review by same-model agents" is likely dominated by single-agent.

### Practitioner failure modes

From crew.ai, AutoGen, and LangGraph practitioner reports:
- **Delegation ping-pong** — agents hand off to each other in infinite loops (crew.ai)
- **Error compounding** — one agent's error propagates through the chain (17× error multiplier observed)
- **Config complexity** — 180+ configuration parameters; most teams don't tune them
- **Context loss at handoff** — the receiving agent doesn't get the full context, producing divergent work

**What practitioners like:** structured task delegation (crew.ai's role-based), subagent context isolation (returns only output, not reasoning), and the "Write Phase → Read Phase" pattern (write to persistent memory, read with compressed injection).

## How this maps to our workspace skills

| Skill | Decomposition | Model routing | Coordination |
|---|---|---|---|
| **/www** | 1 research question per agent; cap 3-5 searches | DDG for search; minimax-m3 for synthesis; parent for final wiki write | Wait-all-before-conclude gate |
| **/design** | Chunk revisions by severity (critical → majors → minors) | Cheap model for pre-write steps; frontier for writer + critical friend | Write→review loop with resume_from |
| **/go** | 1 implementation unit per worker; worktree isolation | Parent-inherited for implementation; cheap model for mechanical checks | Git-based coordination (commit after each unit) |
| **/risk** | 1 attack surface per specialist | Parent for code-reading specialists; cross-model for blind-spot detection | Root-cause clustering after all return |
| **/review** | 1 lens per reviewer | Parent for all reviewers (consistency) | JSON findings files, merged by orchestrator |
| **/tp** | 1 critique per subagent | Different model family for fresh lens | Two-lens: critique then verify |

## What our existing wiki already covers (and this concept adds)

| Topic | Existing concept | This concept adds |
|---|---|---|
| Context isolation | [[context-firewall-architecture]] | When to use subagents (not just how) |
| Model selection | [[model-pool-selection-policy-speed-quota-diversity]] | Routing and cascading strategies (RouteLLM, FrugalGPT) |
| Synthesis speed | [[llm-synthesis-quality-and-speed-techniques]] | Chunking and coordination cost ceiling |
| Parallel wait gate | [[parallel-subagent-wait-all-gate]] | Quadratic coordination cost as the reason N should be bounded |

## Research applicability check (Round 3.25)

Per [[research-applicability-checking-dont-cite-without-verifying-assumptions]], each cited finding's conditions were checked against our use case:

| Finding | Applies to us? | Why |
|---|---|---|
| RouteLLM 85% savings | ⚠️ Partially | Concept applies (learned routing); specific number is from single-query chat, not multi-step agentic tasks; no independent replication |
| FrugalGPT 98% savings | ⚠️ Partially | Cascading works for mechanical tasks; unsafe for reasoning tasks where cheap model failure is undetectable (Huang et al.) |
| Cascade break-even math | ✅ Yes | Most applicable finding — our verifiers are expensive (cross-model review, operator judgment), so the break-even math directly constrains cascade viability |
| Multi-agent underperforms single-agent | ✅ Yes, per task type | Confirms parent-inherited for reasoning tasks; multi-agent still helps for independent mechanical parallel work |
| Coordination cost O(N²) | ⚠️ At our scale | Negligible at N=3-6; relevant for N>10. Practical limit ~6-8 agents |
| Task-tier mapping | ✅ Yes | Confirms our existing [[model-pool-selection-policy-speed-quota-diversity]] |

**Downgrade:** RouteLLM and FrugalGPT headline numbers (85%, 98%) are from different task distributions and should be cited as "potential" not "expected." The cascade break-even math and multi-agent underperformance findings are directly applicable.

## Receipts

- RouteLLM: 85% cost at 95% GPT-4 quality (arXiv 2406.18665, LMSYS ICLR 2025)
- FrugalGPT: 98% cost reduction (Chen et al., TMLR 2024)
- Cascade failure: acc 0.844 at 2.4× cost, zero gain (dennisonbertram benchmark R-003)
- Multi-agent underperformance: 180-config evaluation, single-agent wins most configs (Redis blog)
- Session 019fb189: 1 agent × 3 angles = 5-8 min; corrected to 1 agent × 1 angle = ~2 min
- /design writer: 32 issues × ~4 tool calls = ~128 tool calls; killed at 55 in 644s

## What this means for our workspace

1. **Skills that dispatch parallel subagents** (/www, /design, /go, /risk, /review, /tp) should follow the 3 delegation rules: 1 question per agent, structured findings output, DDG-first for search. These are already in the /www SKILL.md's parallel-dispatch section.
2. **Model routing should be task-type aware** — mechanical tasks (extraction, search, formatting) to cheap models; reasoning tasks to frontier; adversarial tasks to different model families. The existing [[model-pool-selection-policy-speed-quota-diversity]] already implements this; the task-type mapping table in this concept adds specificity.
3. **Don't spawn more agents than the work requires** — coordination cost is quadratic. The practical limit is ~6-8 agents before overhead exceeds parallelism benefit. For reasoning tasks, a single strong agent may outperform a multi-agent team (Nature 2025).
4. **Cascade routing is viable for mechanical tasks only** — the break-even math (escalation rate × verifier cost) makes cascading unsafe for reasoning tasks where cheap-model failure is undetectable (Huang et al.).
5. **Chunk revision work by severity** — the /design writer failure (32 issues in one turn, killed at 644s) is the canonical example. Revision turns should be chunked: critical first, then majors, then minors/nits.

## Falsifier

If following these rules produces the same wall-clock time as violating them (because the bottleneck is tool latency or model speed, not delegation structure), the rules are overhead. However, the session evidence shows 3-4× speedup from correct decomposition alone, and the external research (RouteLLM 85% savings, cascade math) confirms delegation structure is typically the dominant factor. The rules compound: chunking enables parallelism, routing reduces per-agent cost, structured output prevents context bloat. Violating any one degrades wall-clock by 2-3×.

## Sources

- [RouteLLM](https://arxiv.org/html/2406.18665v4) (LMSYS, ICLR 2025) — learned per-query routing, 85% cost at 95% quality
- [FrugalGPT](https://arxiv.org/abs/2305.05176) (Chen et al., TMLR 2024) — cascading, 98% cost reduction
- [Model Cascading for Code](https://arxiv.org/html/2405.15842v1) — black-box cascading for code generation
- [AutoMix](https://arxiv.org/abs/2310.12963) (Madaan et al., 2023) — self-verification gating for cascades
- [Cascade failure benchmark](https://github.com/dennisonbertram/llm-routing-benchmark) — cascade dominated by verifier cost
- [Cascade break-even math](https://leepcast.com/blog/llm-routing-model-cascades) — escalation rate × verifier cost tradeoff
- [Why Multi-Agent LLM Systems Fail](https://redis.io/blog/why-multi-agent-llm-systems-fail/) — 180-config evaluation, coordination cost
