---
title: "Deep research systems: vendor architectures, open-source repos, and /web upgrade path"
created: 2026-07-22
source: session-2026-07-22 (/www compound research)
sources:
  - https://www.anthropic.com/engineering/multi-agent-research-system
  - https://blog.promptlayer.com/how-deep-research-works/
  - https://github.com/assafelovic/gpt-researcher
  - https://github.com/langchain-ai/open_deep_research
  - https://www.perplexity.ai/hub/blog/introducing-perplexity-deep-research
  - https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research
  - https://github.com/DavidZWZ/Awesome-Deep-Research
  - https://openai.com/index/introducing-deep-research/
tags: [deep-research, agentic-research, multi-agent, web-search, architecture, comparisons, open-source, /web-upgrade]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "How vendor deep research systems work (Anthropic, OpenAI, Perplexity), popular open-source repos, and how to apply these patterns to upgrade /web into a deep research mode."
---

# Deep research systems: vendor architectures, open-source repos, and /web upgrade path

Synthesized from 5 scraped sources + our existing `optimal-multi-backend-search-strategy` concept. Addresses: how vendor deep research works, what repos are popular, and how these patterns apply to our `/web` skill.

## The common architecture: all deep research is multi-agent search-reason-search

Despite vendor differences, every production deep research system follows the same core pattern:

```
User query → Plan → [Search → Reason → Search → Reason → ...] → Synthesize → Cited report
```

The differences are in how planning, search, and synthesis are distributed across agents.

## Vendor comparison

| Dimension | **Anthropic Claude Research** | **OpenAI Deep Research** | **Perplexity Sonar Deep Research** |
|-----------|-------------------------------|--------------------------|-------------------------------------|
| **Architecture** | Orchestrator-worker (lead agent + parallel subagents) | Single agent with ReAct loop + extended CoT | Multi-step retrieval model (Sonar DR API) |
| **Foundation model** | Claude Opus 4 (lead) + Claude Sonnet 4 (subagents) | o3 reasoning model, RL-trained for browsing | Sonar (proprietary, built on frontier models) |
| **Parallelism** | 3-5 subagents in parallel, each with 3+ parallel tool calls | Sequential ReAct loop (one search at a time) | Hundreds of sources searched autonomously |
| **Key innovation** | Context compression via subagent context windows | Extended chain-of-thought reasoning through 200+ steps | Pro Search multi-step mode with automatic URL fetching |
| **Stopping mechanism** | Lead agent decides when sufficient | Budget-driven (20-30 min, 30-60 searches, 120-150 pages) | Coverage threshold + source count |
| **Token usage** | 15x chat; token count explains 80% of performance variance | Similar magnitude (o3 reasoning is expensive) | Autonomous — searches until it judges coverage sufficient |
| **Citation** | Dedicated CitationAgent processes documents for inline citations | Every claim has clickable inline citation | Inline citations with source links |
| **Key stat** | +90.2% over single-agent Opus 4 on research eval | "Better than intern work" in blind professional tests | Searches "hundreds of sources" per query |
| **Source** | [Anthropic engineering blog](https://www.anthropic.com/engineering/multi-agent-research-system) | [PromptLayer analysis](https://blog.promptlayer.com/how-deep-research-works/) | [Perplexity docs](https://docs.perplexity.ai/docs/sonar/models/sonar-deep-research) |

### Anthropic's multi-agent architecture (most relevant to us)

Source: [How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (Jun 2025).

This is the most detailed vendor architecture disclosure. Key points:

1. **Lead agent decomposes the query** into subtasks, describes them to subagents with objectives, output formats, tools, and boundaries.
2. **Subagents search independently** with their own context windows — this is context compression via parallelism. Each subagent returns condensed findings.
3. **Lead agent synthesizes** and decides if more research is needed (re-enters loop).
4. **CitationAgent** processes final documents to add inline citations.

**Critical finding:** token usage explains 80% of performance variance on BrowseComp. The multi-agent architecture's value is primarily **scaling token usage** by distributing work across separate context windows.

**Key prompt engineering lessons:**
- Teach the orchestrator to delegate (detailed task descriptions prevent duplication)
- Scale effort to query complexity (1 agent for simple, 10+ for complex)
- Start wide, then narrow (short broad queries first, then specific)
- Parallel tool calling cut research time by 90%

### OpenAI's five-phase process

Source: [PromptLayer analysis](https://blog.promptlayer.com/how-deep-research-works/) + [OpenAI announcement](https://openai.com/index/introducing-deep-research/).

1. **Clarify** — ask follow-up questions to understand intent
2. **Plan** — decompose into sub-questions, prioritize broad context first
3. **Iterative search** — search → read → refine query → search again (ReAct loop)
4. **Read & analyze** — handle HTML, PDFs, images, code execution
5. **Synthesize** — structured report with inline citations

**Budget-driven hard stops:** 20-30 min max, 30-60 web searches, 120-150 pages, 150-200 reasoning iterations. When budget hits, produces partial report with clear marking.

## Open-source repos

| Repo | Stars | Architecture | Key feature | Relevance to us |
|------|-------|-------------|-------------|-----------------|
| **[gpt-researcher](https://github.com/assafelovic/gpt-researcher)** | 28.6k | Planner + execution agents (Plan-and-Solve paper) | Claude Skill available; MCP support; deep research mode (tree exploration) | **Highest relevance** — can install as Claude Skill, has MCP server |
| **[open_deep_research](https://github.com/langchain-ai/open_deep_research)** | 12.4k | LangGraph workflow; configurable multi-model | Deep Research Bench #6 (RACE 0.4344); supports any LLM + search tool + MCP | Good reference for architecture; configurable per-task model routing |
| **[Awesome-Deep-Research](https://github.com/DavidZWZ/Awesome-Deep-Research)** | — | Curated list | Papers, tools, benchmarks | Reference catalog |
| **STORM (Stanford)** | — | Multi-agent (inspired GPT-Researcher's multi_agents) | Wikipedia-quality article generation | Academic foundation |
| **Deep Research Bench** | — | Benchmark (100 PhD-level tasks, 22 fields) | RACE score (LLM-as-judge with Gemini) | Evaluation framework |

### GPT-Researcher architecture (most applicable)

```
Query → Planner agent generates research questions
      → Execution agents gather info per question (parallel)
      → Summarize + source-track each resource
      → Filter + aggregate summaries
      → Publisher generates final report
```

Deep Research mode adds **tree-like exploration** with configurable depth and breadth, ~5 min per research, ~$0.4 cost with o3-mini. Has both a pip package (`pip install gpt-researcher`) and an MCP server (`gptr-mcp`).

## How to upgrade /web into a deep research mode

Our `/web` skill currently does single-pass research: route queries → search backends → scrape → synthesize. The existing `optimal-multi-backend-search-strategy` concept identified the key gap: **sequential reflection loops** (search-reason-search). Here's how vendor patterns map to our architecture:

### Level 1: Iterative refinement (highest ROI, lowest effort)

**What to add:** after first search pass, assess gaps, fire targeted follow-ups.

This is what `/www` Phase 2.8 already describes but rarely executes in practice. The upgrade: make it the default for `depth=deep`, not an optional step.

```python
# After first synthesis pass
gaps = assess_gaps(findings, original_gaps)
if gaps:
    refined_queries = reformulate(gaps, prior_results)
    results = search(refined_queries)
    findings = merge(findings, results)
```

### Level 2: Parallel subagent decomposition (Anthropic pattern)

**What to add:** decompose complex queries into sub-queries, dispatch each to a subagent with its own context window, merge results.

This is the Anthropic orchestrator-worker pattern. Our `/go` skill already supports parallel subagent spawning. The upgrade:

```
User query → /web lead agent decomposes into N sub-queries
           → spawn N subagents, each searches + scrapes + summarizes independently
           → lead agent merges subagent findings
           → synthesize final report with citations
```

**Token cost:** Anthropic reports 15x chat tokens for multi-agent. For our fleet, this means using the free pool (DGemma, Gemma 4 31B) for subagent work and the parent model only for synthesis.

### Level 3: MCP server integration (GPT-Researcher pattern)

**What to add:** run GPT-Researcher as an MCP server for genuine deep research tasks.

GPT-Researcher has a dedicated MCP server ([gptr-mcp](https://github.com/assafelovic/gptr-mcp)). We could wire it into our config.toml as an MCP backend:

```toml
[mcp_servers.gpt-researcher]
command = "node"
args = ["gptr-mcp/index.js"]
```

Then `/web --deep` could delegate to the GPT-Researcher MCP server for multi-step research, getting the benefit of its tree-exploration + Plan-and-Solve architecture without building it ourselves.

### What NOT to build

- **Don't** build a full multi-agent research framework from scratch — GPT-Researcher and open_deep_research already exist and are battle-tested
- **Don't** try to replicate OpenAI's o3-trained browsing model — we don't have the training infrastructure
- **Don't** replace `/web` — add a `--deep` mode that activates the iterative/parallel pattern
- **Don't** ignore our existing multi-backend search advantage — RRF across minimax-search + web-search-prime + firecrawl is already better than single-backend

### Recommended upgrade path

| Priority | Change | Effort | Impact |
|----------|--------|--------|--------|
| 1 | Make `/www` Phase 2.8 iterative refinement actually execute on `depth=deep` | Low | Closes the single-pass gap; biggest quality lever |
| 2 | Add `/web --deep` mode that spawns parallel subagents for sub-query decomposition | Medium | Anthropic pattern; 90% improvement on breadth-first queries |
| 3 | Wire GPT-Researcher MCP server for genuine deep research tasks | Low (install) | Gets tree-exploration + Plan-and-Solve for free |
| 4 | Add citation tracking (source URL + excerpt per claim) to /web output | Medium | Makes output verifiable, like vendor products |
| 5 | Add budget-driven stopping (max searches, max pages, max time) | Low | Prevents runaway research; OpenAI pattern |

## Key insights from the research

1. **Token usage is the dominant factor** (80% of variance) — multi-agent systems work primarily because they spend more tokens via parallel context windows. [HIGH — Anthropic's own BrowseComp data]

2. **All vendors converge on the same pattern**: plan → iterative search-reason → synthesize with citations. The differences are in model training, not architecture. [HIGH — consistent across all sources]

3. **Parallel subagents with separate context windows** is the Anthropic innovation — it solves context limits by distributing work, not by building bigger context windows. [HIGH — Anthropic engineering blog]

4. **Budget-driven stopping** is universal — every system has hard limits on time, searches, pages. Without them, agents spiral. [HIGH — OpenAI and Anthropic both report this]

5. **GPT-Researcher is the most mature open-source option** — 28.6k stars, MCP server, Claude Skill, pip package, tree-based deep research mode. [HIGH — GitHub verified]

6. **The Deep Research Bench** provides a standardized evaluation framework (RACE score with Gemini-as-judge) — useful if we want to benchmark our own /web --deep against open-source tools. [MEDIUM — benchmark exists but we haven't run it]

## Conflict

⚠️ **Anthropic vs. OpenAI on parallelism**: Anthropic claims parallel subagents are the key innovation (+90.2%). OpenAI uses a sequential ReAct loop. Both achieve high quality. The resolution: parallelism helps with **breadth** (independent facets of a question); sequential reasoning helps with **depth** (dependent chains of evidence). Our `/web --deep` should support both modes.

## Auto-related

- [[optimal-multi-backend-search-strategy]] — covers RRF, iterative retrieval, hybrid search structures; this concept adds vendor architectures and the /web upgrade path
- [[compound-skill-improvement-patterns]] — references emergentmind deep-research agents; this concept provides concrete vendor architectures
- [[llm-council-and-model-fusion]] — MoA/Fusion is the LLM-ensemble counterpart; deep research uses similar multi-agent patterns
- [[web-search-tool-routing]] — which backend for which query; deep research mode would use all backends in parallel
- [[skill-performance-and-reliability]] — SkillAxe finding that skills improve execution reliability (coverage) not answer quality; deep research mode is the same pattern at the search level
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
