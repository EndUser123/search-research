---
title: "Token optimization patterns for LLM agent fleets"
created: 2026-08-05
source: session-2026-08-05 (/www research on self-improving agent patterns we don't have)
sources:
  - external: https://arxiv.org/abs/2510.00615 (ACON, Microsoft, ICML 2026)
  - external: https://arxiv.org/abs/2510.26585 (SupervisorAgent, ICLR 2026)
  - external: https://boliv.substack.com/p/lazy-skills-a-token-efficient-approach (Lazy Skills, 2025)
  - external: https://arxiv.org/abs/2601.06007 (LOOP Skill Engine, 2026)
  - external: https://github.com/microsoft/LLMLingua (LLMLingua-2, Microsoft)
  - external: https://github.com/lm-sys/RouteLLM (RouteLLM, LMSYS)
  - external: https://vllm.ai/blog/2026-06-02-session-aware-agentic-routing (vLLM SAAR, 2026)
  - external: https://dev.to/kiran_kumar_366b5f9805948/agentic-ais-token-debt (Tool-call output distillation, 2026)
  - external: https://github.com/atlassian-labs/mcp-compressor (MCP compressor, Atlassian)
  - external: https://www.glean.com/perspectives/how-to-optimize-token-efficiency-in-agentic-systems (Glean, 2026)
  - external: https://github.com/pleasedodisturb/awesome-llm-token-optimization (curated list, 2026)
tags: [token-optimization, context-engineering, prompt-caching, model-routing, context-compression, fleet-management, cost-optimization, token-budget, semantic-cache, tool-distillation]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Twelve token optimization techniques for LLM agent fleets, spanning five
  layers: caching (prompt cache, semantic cache), context management
  (compaction, distillation, lazy loading), output minimization (structured
  outputs, tool-call distillation), routing (cost-aware model selection, token
  budget governance), and reuse (execution plan compilation). The workspace
  already has context firewall architecture, skill-based progressive disclosure,
  and model routing. The highest-ROI additions are: (1) tool-call output
  distillation to flatten O(N^2) context growth, (2) fleet-level token budget
  governance with per-agent quotas, (3) reusable execution plans (LOOP-style)
  for repeated workflows, and (4) bounded multi-agent loops with improvement
  thresholds. Novel 2025-2026 techniques (ACON failure-triggered compression,
  SupervisorAgent runtime governance, LOOP plan compilation) represent the
  frontier the workspace hasn't adopted yet.
relations:
  - target: wiki/concepts/self-improving-agent-systems-techniques-and-workspace-gaps.md
    type: extends
  - target: wiki/concepts/context-firewall-architecture.md
    type: related
  - target: wiki/concepts/context-management-trade-offs.md
    type: related
  - target: wiki/concepts/enforcement-hierarchy-and-compaction-strategy.md
    type: related
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale.md
    type: related
  - target: wiki/concepts/semantic-caching-for-llm-agents.md
    type: complement
  - target: wiki/concepts/deterministic-output-engineering.md
    type: related
---

# Token optimization patterns for LLM agent fleets

## Decision context

**Why this research was needed:** the operator asked what self-improving agent patterns the workspace is missing, specifically naming token optimization. The workspace runs a fleet of coding agents whose primary cost driver is token consumption — both input (context loading) and output (generation). No dedicated concept existed on token optimization techniques for agent fleets.

**Scope:** agent-specific optimization (not general LLM serving). Focus on patterns a coding-agent CLI workspace with a multi-agent fleet can implement.

## Key Findings

### Five-layer token optimization taxonomy

| Layer | Techniques | What the workspace has | What's missing |
|-------|-----------|----------------------|---------------|
| **Caching** | Prompt cache (KV reuse), semantic cache (embedding-based) | Provider-level prompt caching (implicit) | Semantic cache; shared fleet cache |
| **Context management** | Compaction, distillation, lazy loading, output distillation | Session-level compaction; skill progressive disclosure | Tool-call output distillation (O(N^2) flattening); ACON failure-triggered compression |
| **Output minimization** | Structured outputs, constrained decoding, schema enforcement | Deterministic output engineering concept | Systematic structured output across all agent calls |
| **Routing** | Cost-aware model selection, token budget governance | Model routing (coding pool, reasoning pool) | Fleet-level token budget with per-agent quotas; cascading (cache→cheap→expensive) |
| **Reuse** | Execution plan compilation, skill library | Skill catalog (700+ skills) | LOOP-style compiled plans for repeated workflows |

### Top techniques by impact × effort

| Technique | Effort | Impact | Source | Novel? |
|-----------|--------|--------|--------|--------|
| **Tool-call output distillation** (O(N^2)→O(N)) | High | Very High | DEV.to 2026, Atlassian mcp-compressor | Yes (2026) |
| **Fleet token budget governance** | Medium | Very High | Zylos 2026, llm-budget GitHub | Emerging |
| **Reusable execution plans (LOOP)** | High | Very High | arXiv 2601.06007, 93-99% savings | Yes (2026) |
| **Lazy Skills 3-tier progressive disclosure** | Medium | High | boliv.substack 2025 | Partially (workspace has 2-tier) |
| **Bounded multi-agent loops** | Low-Med | High | SupervisorAgent, Glean 2026 | Emerging |
| **Cost-aware cascading routing** | Medium | High | RouteLLM, vLLM SAAR 2026 | Partially (workspace has static routing) |
| **Prompt compression (LLMLingua-2)** | Medium | Medium-High | Microsoft 2024 | Known |
| **ACON failure-triggered compression** | Medium | High | arXiv 2510.00615, ICML 2026 | Yes (2026) |
| **Structured output / constrained decoding** | Low-Med | Medium-High | JSONSchemaBench 2025 | Known |
| **Context economization (evidence ranking)** | Medium | High | Glean 2026, Anthropic docs | Known principles |
| **Shared fleet prompt cache** | Low | High | TokTier 2026 | Known |
| **Semantic caching (application-level)** | Medium | High | GPTCache, GPT Semantic Cache paper | Known (see [[semantic-caching-for-llm-agents]]) |

### The O(N^2) tool-call growth problem

The most novel finding: multi-step agent tool chains produce **quadratic context growth**. Each tool call's output is appended to context, and the agent reads all accumulated context on the next call. By step 20, context can reach 500K tokens even when the actual task needs ~50K [INFERENCE — illustrative magnitudes; the O(N^2) framing is sourced to DEV.to 2026, specific numbers are approximate].

**Solution: tool-call output distillation.** Intercept tool return values before appending to context and apply: schema hoisting (extract shared keys once), delta-encoding (replace sequential values with diffs), entity reference dedup (replace repeated entities with anchors). This flattens O(N^2) to O(N). The Atlassian mcp-compressor implements this for MCP tool surfaces.

**Workspace relevance:** the fleet's `/go` orchestrator spawns subagents whose tool calls (read_file, grep, run_terminal_command) produce large outputs. These accumulate in the parent context. Distillation rules (e.g., "replace full file reads with file:line citations after the first read") would prevent context exhaustion.

### LOOP Skill Engine: compiled plans

The LOOP Skill Engine (arXiv 2601.06007, 2026) compiles successful agent traces into branch-free executable recipes. On subsequent runs, the agent loads the stored plan instead of re-deriving it. Reported savings: **93.3% on daily repeated tasks, 99.98% on high-frequency operations**.

**Workspace relevance:** the fleet repeats common workflows (code review, refactoring, testing, wiki sync). Currently each invocation re-derives the plan from scratch. Compiled plans would eliminate redundant planning cost. This is a natural extension of the existing skill catalog — skills are already "plans" but they're written by humans, not compiled from successful traces.

### SupervisorAgent: runtime loop governance

SupervisorAgent (ICLR 2026) uses an LLM-free adaptive filter to monitor multi-agent loops at runtime. It detects when a loop is not converging (improvement delta below threshold) and intervenes to halt it. Reported: **29.68% token reduction** by preventing runaway reflection loops.

**Workspace relevance:** the `/go` orchestrator has parallel waves and review-fix loops but no runtime convergence detection. A lightweight supervisor (even a deterministic script checking improvement delta) would prevent wasting tokens on non-converging loops.

### ACON: failure-triggered context compression

ACON (Microsoft, ICML 2026) doesn't compress context on a schedule — it compresses **when the agent fails**. The trigger is: the agent's last action failed (test failure, error, incorrect output). At that point, ACON compresses the context around the failure point, preserving the relevant context while discarding noise.

**Workspace relevance:** the workspace's compaction is time-based (when approaching context limit). Failure-triggered compression would be more surgical — compress only when needed, and only the relevant context window.

## Honest trade-offs

**Like:** token optimization directly reduces cost and latency for every agent operation; techniques compound across the fleet; the workspace's existing substrates (skills, routing, compaction) provide a strong foundation.

**Dislike:** tool-call output distillation requires intercepting every tool return — it's architectural, not incremental. LOOP compiled plans require trace compilation infrastructure that doesn't exist. Budget governance adds enforcement overhead that could block legitimate work. Semantic caching risks serving stale answers (see [[semantic-caching-for-llm-agents]]).

## Falsifier

This concept is wrong if, within 6 months:
- The techniques are implemented but fleet token consumption doesn't decrease measurably
- A vendor ships built-in tool-call distillation that makes manual implementation obsolete
- The O(N^2) growth problem is solved at the model level (infinite context windows with O(1) read cost)
- LOOP-style plan compilation produces brittle plans that break when the codebase changes

## What this means for our workspace

**Highest-ROI additions (ordered):**

1. **Tool-call output distillation** — add a post-processing layer to subagent return values that replaces full file content with citations, deduplicates entity references, and delta-encodes sequential values. This addresses the most expensive growth pattern in the fleet's multi-step workflows.

2. **Bounded loop governance** — add max-turn and improvement-threshold guards to `/go`'s parallel waves and review-fix loops. Low effort, immediate token savings. A deterministic script checking "did the fix actually change anything?" prevents burning tokens on non-converging loops.

3. **Fleet token budget** — implement per-agent token quotas within a fleet-wide budget. Prevents one runaway agent from consuming the fleet's quota. The existing `fleet_quota.py` tracks quota at the provider level; per-agent budgeting is the natural extension.

4. **Reusable execution plans** — extend the skill catalog to include "compiled plans" generated from successful agent traces. Start with the highest-frequency workflows (/review, /check, /go discovery phase). The skill catalog already supports this structurally — the gap is the compilation pipeline.

5. **ACON-style failure-triggered compaction** — enhance the existing compaction to trigger on failure events (test failures, error states) rather than only on context-size thresholds.

## Related

- [[self-improving-agent-systems-techniques-and-workspace-gaps]]@extends — this concept extends the self-improving agent survey with token optimization as a specific dimension
- [[context-firewall-architecture]]@related — context isolation is the foundation that makes per-agent optimization possible
- [[context-management-trade-offs]]@related — sliding windows vs compaction trade-offs
- [[enforcement-hierarchy-and-compaction-strategy]]@related — where compaction lives in the enforcement hierarchy
- [[code-orchestrates-model-judges-skill-scale]]@related — code orchestration as a token optimization (zero tokens on coordination)
- [[semantic-caching-for-llm-agents]]@complement — semantic caching as a token optimization technique
- [[deterministic-output-engineering]]@related — structured outputs as output token minimization

## Sources

**Context compression:**
- ACON: Optimizing Context Compression for Long-horizon LLM Agents — https://arxiv.org/abs/2510.00615
- LLMLingua-2 (Microsoft) — https://github.com/microsoft/LLMLingua
- Agent Context Window Compression Guide (2026) — https://agentmarketcap.ai/blog/2026/04/10/agent-context-window-compression-techniques-2026

**Routing and budget:**
- RouteLLM (LMSYS) — https://github.com/lm-sys/RouteLLM
- vLLM Session-Aware Agentic Routing (SAAR) — https://vllm.ai/blog/2026-06-02-session-aware-agentic-routing
- llm-budget — https://github.com/Mattbusel/llm-budget
- Zylos Agent Cost Optimization — https://zylos.ai/research/2026-04-12-ai-agent-cost-optimization-token-budget-model-routing/

**Tool-call distillation:**
- Agentic AI's Token Debt (DEV Community) — https://dev.to/kiran_kumar_366b5f9805948/agentic-ais-token-debt-why-multi-step-tool-chains-blow-up-your-context-window-and-how-semantic-4f2k
- mcp-compressor (Atlassian Labs) — https://github.com/atlassian-labs/mcp-compressor

**Progressive disclosure and plan reuse:**
- Lazy Skills — https://boliv.substack.com/p/lazy-skills-a-token-efficient-approach
- LOOP Skill Engine — https://arxiv.org/abs/2601.06007
- SkillsInjector — https://arxiv.org/abs/2605.29794

**Runtime governance:**
- SupervisorAgent (ICLR 2026) — https://arxiv.org/abs/2510.26585
- Glean Token Efficiency — https://www.glean.com/perspectives/how-to-optimize-token-efficiency-in-agentic-systems

**Survey:**
- Awesome LLM Token Optimization — https://github.com/pleasedodisturb/awesome-llm-token-optimization

**Research method:** /www pipeline, 5 parallel or-ling-3-flash-free subagents + parent DDG/firecrawl practitioner signal, 50+ sourced findings synthesized.
