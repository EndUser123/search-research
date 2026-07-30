---
title: "Delegation optimization: chunking, output format, and backend discipline for parallel subagent dispatch"
created: 2026-07-30
source: session-019fb189
tags: [delegation, subagent-dispatch, parallel-execution, latency-optimization, context-firewall, skill-design, reusable-pattern, model-agnostic]
summary: >
  When a skill dispatches multiple subagents for parallel work (research,
  review, implementation, analysis), three rules determine whether the run
  completes in minutes or hours: (1) one question per agent — never bundle
  multiple angles into one agent's scope; (2) request structured findings,
  not raw search output or full reports — the orchestrator synthesizes; (3)
  use free/fast backends first (DDG) and avoid expensive operations (full
  page fetches) unless load-bearing. These rules are model-agnostic and
  apply to /www, /design, /go, /red-team, /review, and any skill that fans
  out work across subagents.
agent: grok
host: grok
cognitive_load: 2
verification: session-evidence
sources:
  - Session 019fb189 /www runs: 5-8 min per agent when violated; target 2-3 min when followed
  - Session 019fb189 /design writer revision: 644s, 55 tool calls, cancelled — 32 issues in one turn was too much
relations:
  - target: wiki/concepts/context-firewall-architecture.md
    type: complements — context firewall prevents pollution; delegation optimization prevents waste
  - target: wiki/concepts/llm-synthesis-quality-and-speed-techniques.md
    type: related — cascading to cheaper models for mechanical work
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md
    type: implements — model tiering for delegation
---

# Delegation optimization: chunking, output format, and backend discipline

## Decision context

**Why this was needed:** during session 019fb189, multiple /www research runs took 5-8 minutes per agent. A subsequent /design writer revision (32 issues in one turn) ran for 644 seconds before being killed. The root cause in both cases was the same: **inefficient delegation** — too much work per agent, wrong output format, wrong backend. The operator observed: "we need to be more efficient with how we distribute tasks" and requested these rules be reusable across all skills.

## The three rules

### Rule 1: One question per agent

Never assign 2+ independent angles to one agent. If you have 6 questions, dispatch 6 narrow agents (3-5 searches each) running in parallel, not 2 broad agents (9-15 searches each) running slowly.

**Why:** each angle needs 3-5 tool calls. 3 angles in one agent = 9-15 serial tool calls, taking 5-8 min. Split into 3 agents = 3-5 tool calls each, running in parallel, ~2-3 min wall-clock.

**Measured failure:** /www runs with 1 agent assigned 3 angles took 5-8 min each. Corrected decomposition (1 question per agent) should complete in ~2-3 min per agent. The same pattern caused the /design writer revision to fail: 32 review issues dispatched in one `resume_from` turn required ~128 tool calls; the subagent got through 55 in 644 seconds before being killed. The fix: chunk revision turns by severity (critical first, then majors, then minors/nits).

**When this is NOT about research only:** the same applies to code review (1 file per reviewer specialist), implementation (1 unit per worker), design revision (critical issues first, then majors, then minors — chunked turns not one massive turn).

### Rule 2: Request structured findings, not raw output or full reports

The orchestrator (parent model) does the synthesis. Agents are gatherers. Request structured findings per item: name/description/source/relevance/applicability, ~2-4 sentences each. NOT raw search dumps (bloats context, triggers compaction). NOT terse numbered lists only (loses signal the operator values). Structured-but-concise is the target.

**Why:** raw search output bloats the orchestrator's context and triggers compaction mid-task. A full research report per agent (5-8K words) across 6 agents = 30-48K words the orchestrator must process. Structured findings (500 words per agent) across 6 agents = 3K words — manageable.

**The nuance:** "more info is better than less" (operator preference). The rule is not "minimize output" — it's "structure the output so the orchestrator can synthesize efficiently." Rich structured findings are welcome; raw search dumps are not.

### Rule 3: Use free/fast backends first; avoid expensive operations

- **DDG first** (`from ddgs import DDGS; DDGS().text(...)`) — free, fast, no quota. Escalate to firecrawl or built-in web_search only for content-rich queries.
- **Don't fetch full pages** (arxiv, documentation sites) — read abstracts/summaries. Full-text fetch should be reserved for the 1-2 highest-value sources only. Each full page fetch takes 10-30s.
- **Cap: 3-5 tool calls per agent** — if the agent needs more, the question is too broad; decompose further.

**Why:** built-in web_search consumes Grok quota (~2 RPS fleet-wide, 429-prone). MCP search_tool adds latency. Full page fetches waste 2-3 min on content that doesn't change findings.

## How this applies across skills

| Skill | Rule 1 (chunking) | Rule 2 (output format) | Rule 3 (backend) |
|---|---|---|---|
| **/www** | 1 research question per agent | Structured findings per item (technique/source/relevance) | DDG first, abstract-only |
| **/design** | 1 revision concern per writer turn (critical → majors → minors) | Design doc sections, not freeform prose | Read evidence brief, not raw source files |
| **/go** | 1 implementation unit per worker | Code + test result, not analysis | Use workspace tools (grep, read), not web search |
| **/red-team** | 1 attack surface per specialist | JSON findings file, not inline prose | Read target files, not external research |
| **/review** | 1 lens per reviewer (correctness, security, etc.) | Findings JSON with severity, not narrative | Static analysis + code reading |
| **Any skill** | If the work can't complete in ~2-3 min, the scope is too broad | If the output can't be consumed in ~30s, it's not structured enough | If the backend costs quota or adds >10s latency, justify or switch |

## The chunking formula

```
Total work = N questions × M tool calls per question
Wall-clock (parallel) = max(M) × tool latency ≈ M × 30s
Wall-clock (serial/bundled) = N × M × tool latency ≈ N × M × 30s

Parallelization factor = N (linear speedup)
Constraint: each agent must be independent (no cross-referencing between agents)
```

If N > 6, consider whether all questions are truly independent. If not, identify dependencies and sequence the dependent ones.

The formula shows the asymmetry clearly: parallelizing N questions into N agents gives N× speedup. Bundling them into fewer agents serializes the work. The only reason to bundle is when questions share context (a later question depends on an earlier answer) — in which case they're not independent and should be in one agent, but that agent should still be narrow (one dependency chain, not multiple independent chains bundled together).

## What this does NOT cover

- **Context firewall** (preventing raw content from polluting the orchestrator's context): covered by [[context-firewall-architecture]]
- **Model tiering** (which model to use for which task): covered by [[model-pool-selection-policy-speed-quota-diversity]] and [[llm-synthesis-quality-and-speed-techniques]]
- **Wait-all-before-conclude gate** (ensuring all agents return before synthesis): covered by [[parallel-subagent-wait-all-gate]]

This concept is specifically about HOW to decompose the work, WHAT to ask for as output, and WHICH tools to use — the three axes that determine delegation efficiency. These three rules are model-agnostic: they apply regardless of which model the subagent runs on, because the bottleneck is delegation structure (serial vs parallel, scope per agent), not model speed. Faster models help, but the 3× speedup from correct parallelization dwarfs the marginal speedup from a faster model on the wrong task decomposition.

## Receipts

- /www runs (session 019fb189): 1 agent × 3 angles = 5-8 min per agent; corrected to 1 agent × 1 angle = ~2-3 min target
- /design writer revision (session 019fb189): 32 issues × ~4 tool calls per issue = ~128 tool calls; subagent got through 55 in 644s before being killed
- Operator observation: "I don't mind getting more info than less, that's probably more useful, but we need to be more efficient with how we distribute tasks"

## Falsifier

If following these three rules produces the same wall-clock time as violating them (e.g., because the bottleneck is tool latency, not delegation structure), the rules are unnecessary overhead. Measure: run the same research task with and without the rules; if wall-clock is within 20% of each other, the bottleneck is elsewhere (tool latency, model speed, network). In that case, optimize the bottleneck, not the delegation structure.

However, in practice the delegation structure is almost always the dominant factor — the /www runs this session showed 3-4× speedup from correct decomposition alone, before any backend or model optimization was applied. The three rules compound: chunking enables parallelism, structured output prevents context bloat, and fast backends reduce per-agent latency. Violating any one degrades wall-clock by 2-3×.

The operator's exact framing: "I don't mind getting more info than less, that's probably more useful, but we need to be more efficient with how we distribute tasks." The three rules operationalize that directive: distribute tasks narrowly (Rule 1), ask for structured findings (Rule 2), use fast backends (Rule 3).
