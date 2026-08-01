---
title: "Optimal multi-backend search strategy (what research says)"
created: 2026-07-21
source: session-2026-07-21
tags: [web-search, ensemble, RRF, reciprocal-rank-fusion, hybrid-search, deep-search, research, strategy, routing, parallel, quality]
summary: >
  Research consensus (2025-2026) on maximizing search quality with multiple backends:
  (1) Hybrid search via Reciprocal Rank Fusion (RRF) merges ranked result lists without
  score calibration — documents near the top of multiple lists win. (2) Iterative retrieval
  (search → reason → search) dramatically beats single-shot on multi-hop tasks. (3) LLM
  Ensemble taxonomy (IJCAI 2026 survey): ensemble-before (routing), during (token/span/
  process), after (non-cascade/cascade). (4) For agents, parallel decomposition + sequential
  reflection (hybrid tree search) is the frontier. The local search-research package already
  implements several of these patterns (async concurrent execution, HyDE, auto mode).
agent: grok
host: both
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/web-search-tool-routing
    type: refines
  - target: wiki/concepts/web-research-state-2026
    type: related
  - target: wiki/concepts/llm-council-and-model-fusion
    type: related
  - target: wiki/concepts/multi-agent-correlated-errors
    type: related
---

# Optimal multi-backend search strategy (what research says)

## Why this page exists

`web-search-tool-routing.md` answers "which backend for which query." This page answers
the harder question: **given N backends, how do we combine their outputs to maximize
quality?** That is a researched problem with named algorithms, not a matter of preference.

## The five research-backed patterns

### 1. Reciprocal Rank Fusion (RRF) — merge ranked lists without score calibration

**The single most important technique for multi-backend search.** Different backends
return different score scales (Firecrawl relevance, Brave snippets, Exa neural scores,
Tavily answer scores). You cannot directly compare scores across backends. RRF solves
this by using **rank position only**.

**Formula:**
```
RRF(d) = Σ [ 1 / (k + rank_i(d)) ]   for i = 1 to n
```
where `rank_i(d)` is the document's rank in backend `i`'s result list, and `k` is a
smoothing constant (typically 60; Cormack et al. 2009).

**Why it works:** documents appearing near the top of multiple backend result lists get
the highest combined scores. A doc at rank 1 in one backend and rank 3 in another beats
a doc at rank 1 in one and absent elsewhere. This is exactly the "source diversity"
principle — independent backends agreeing on a source is stronger signal than any one
backend's score.

**Authority:**
- Cormack, Clarke & Buett-Schuur (SIGIR 2009): original paper, k=60 validated
- Azure AI Search, Elasticsearch, LangChain4j, Spice.ai all ship RRF as the default
  hybrid aggregation (Microsoft, Elastic, glaforge.dev, spice.ai — all scraped 2026-07-21)
- RAG-Fusion: multi-query generation + RRF aggregation pattern (glaforge.dev 2026-02)

**Application here:** when running `minimax-search` + `web-search-prime` + `firecrawl_search`
+ `search-research --mode serper` in parallel, apply RRF to their ranked result lists
before scraping. The local `search-research` package has a `ResearchRouter` designed for
this — worth verifying whether it already does RRF or naive concatenation.

### 2. Iterative retrieval beats single-shot on multi-hop (search-reason-search loop)

FutureSearch (LessWrong, June 2025) and Perplexity research (Advancing Search-Augmented
Language Models, April 2026) independently confirm: **standard LLMs with keyword search
score below 10% on complex multi-hop benchmarks; systems built around iterative retrieval
score dramatically higher.** The tool matters less than whether it supports a loop.

**Pattern:**
1. Search
2. Reason over results ("do I have what I need?")
3. Search again with refined query based on gaps
4. Repeat until sufficient or budget exhausted

**Implication:** `/www` Phase 2 should not be "fire searches, scrape, synthesize" as a
single pass. It should be "fire searches → assess gaps → fire targeted follow-ups →
synthesize." The current `/www` skill is closer to single-pass with its 2.6 context
firewall. A loop-aware mode would materially improve quality on complex topics.

**Authority:** arXiv:2508.05668 (Xi et al., "A Survey of LLM-based Deep Search Agents,"
SJTU + CSU, Aug 2025) — the canonical survey. Perplexity's Sonar Pro implements this
as "Pro Search: multi-step mode where the model runs multiple web searches and fetches
URL content automatically before answering."

### 3. Hybrid search structure: parallel + sequential + tree/graph

From arXiv:2508.05668 §3:

| Structure | When | Example |
|-----------|------|---------|
| **Parallel** (decomposition-based) | Query has multiple independent facets | "Gemini API vs agy" + "search routing" fired simultaneously |
| **Parallel** (diversification-based) | One intent, multiple plausible phrasings | HyDE multi-perspective: technical, ethical, societal framings |
| **Sequential** (reflection-driven) | Each search depends on prior results | Find URL → scrape → find cited source → scrape that |
| **Sequential** (proactivity-driven) | Agent decides when/what to search based on context | ReAct loop, Pro Search |
| **Hybrid tree** | Explore multiple paths, expand promising ones | MCTS over search paths; vote on final answer |
| **Hybrid graph (DAG)** | Queries have dependencies; backtrack on dead ends | Deep Research agents (OpenAI, Gemini, Perplexity) |

**For this fleet:** most `/www` runs are parallel-decomposition (good). Adding
sequential-reflection loops would close the gap to Pro Search-class quality without
needing a dedicated deep research subscription.

### 4. LLM Ensemble taxonomy (before / during / after inference)

From the IJCAI 2026 survey "Harnessing Multiple Large Language Models" (Chen et al.,
arXiv:2502.18036, Awesome-LLM-Ensemble repo maintained July 2026):

| Phase | Method | Application to search |
|-------|--------|----------------------|
| **(a) Before** — routing | Pre-trained or rule-based router picks one model/backend | Our intent-based routing (`/web` skill) |
| **(b) During** — token/span/process | Ensemble at decoding (token voting, span selection, process selection) | Not directly applicable to search backends (applies to LLM fusion) |
| **(c) After** — non-cascade | All candidates fully generated, then fused | RRF over search results; MoA over LLM responses |
| **(c) After** — cascade | Try cheap model first, escalate if confidence low | Our lane escalate (Ornith → DiffusionGemma → MiniMax); also "cascade LLM" pattern |

**Key insight for this fleet:** the local search-research package implements (a)
routing + (c) non-cascade aggregation. It does not implement the during-inference
patterns, which require decoder-level access we don't have. That's fine — during-inference
is for LLM fusion (covered in `llm-council-and-model-fusion`), not search backend fusion.

### 5. Context engineering is ~80% of agentic search

From Weaviate / Leonie Monigatti at AI Engineer Europe 2026 (cited in Vellum):
**"context engineering — deciding what actually goes into an agent's context window —
is about 80% agentic search."** Stale context produces confident wrong answers.

**Implication:** the bottleneck is not which backend to call. It is **what to scrape,
how to compress, and what to put in the synthesis prompt.** Firecrawl's 94% token
reduction (2,788 vs 38,381 tokens/page) is the highest-leverage tool here. The `/www`
context firewall (Step 2.6) and `/design` Step 0.5 firewall are the right patterns;
they should be used more aggressively.

## Local implementation status (search-research)

**Location:** `P:/packages/.claude-marketplace/plugins/search-research/`  
**Status doc:** `IMPLEMENTATION_COMPLETE.md` (2026-03-06, marked ✅ COMPLETE)  
**Codex work:** the package was built across 6 phases ( Weeks 1-4) — likely via Codex
based on the git log style ("chore: update settings" dominant) and the IMPLEMENTATION_*
docs. The package replaces the deprecated `unified-search` module.

**What's implemented (per IMPLEMENTATION_COMPLETE.md):**

| Feature | Status | Notes |
|---------|--------|-------|
| Async concurrent execution | ✅ | `asyncio.gather()` across providers (PERF-001, PERF-008) |
| 11 web providers | ✅ | Tavily full + 10 stubs at time of writing; backends dir has 13 modules now |
| HyDE enhancement | ✅ | `hyde.py` (255 lines), key phrase extraction, multi-perspective |
| Per-provider timeout (5s) + graceful degradation | ✅ | If one backend fails, others continue |
| LRU+TTL cache (3600s) | ✅ | `cache.py` |
| RuleBasedIntentDetector (40+ patterns, >70% accuracy) | ✅ | `query_intent.py` (270 lines) |
| ResearchRouter COMPREHENSIVE mode | ✅ | Multi-backend aggregation |
| SearchRouter FAST mode (<1s) | ✅ | Local backends only |
| 90 integration tests | ✅ | Mode routing, fallback, degradation |

**What's NOT explicitly confirmed (gaps to verify):**

| Gap | Why it matters |
|-----|---------------|
| Whether aggregation uses **RRF** or naive concatenation | RRF is the research-backed method; naive concat wastes the diversity signal |
| Whether sequential reflection loop is implemented | Survey says this is the biggest quality lever for multi-hop |
| Saturation detection (`--saturation-threshold`) | Listed in CLI_USAGE — stops when new results stop adding signal |
| Current test status (last run date) | Package may have drifted since March |

**Recommendation:** probe `search_research/router.py` and `providers/` to verify
whether RRF is implemented. If not, that's the single highest-value improvement —
it's ~50 lines of Python and turns parallel-search from "many lists" into "one ranked
list with diversity signal."

## Synthesis: what optimal looks like for this fleet

Combining all five patterns with the local inventory:

### Tier 1 — what we should do every time (low effort, high return)

1. **Parallelize independent queries** across ≥2 backends (minimax-search + web-search-prime minimum)
2. **Apply RRF** (or at least deduplicate + cross-rank) before scraping
3. **Scrape via Firecrawl** with `onlyMainContent: true` (94% token reduction)
4. **Submit `firecrawl_search_feedback`** (refunds 1 credit)
5. **Score sources CREDIBLE-lite** before citing

### Tier 2 — for complex / multi-hop topics

6. **Decompose** the question into sub-queries (parallel structure)
7. **Run HyDE** via `search-research --hyde` or `--multi-hyde --hyde-perspectives technical,ethical,societal`
8. **Sequential reflection loop:** after first pass, assess gaps, fire targeted follow-ups
9. **Context firewall** the scraped content into a brief before synthesis
10. **Cross-family synthesis** via different LLM than the one that searched

### Tier 3 — for hard-to-reverse / high-stakes decisions

11. **Cross-family critic** on the synthesis (Gemini via API, or `/agy` as second opinion)
12. **Fusion panel** if the decision warrants it (see `llm-council-and-model-fusion`)
13. **DAG/graph search** with backtracking if the topic has dependency chains

### What NOT to do

- **Don't** run one backend and trust it (no diversity signal)
- **Don't** scrape raw HTML (38K tokens/page vs 2.8K via Firecrawl)
- **Don't** concatenate result lists without RRF or dedup (wastes the multi-backend signal)
- **Don't** single-pass synthesize on multi-hop topics (iterative retrieval is the frontier)
- **Don't** use `agy` as a search backend (it's a second-opinion harness — see `gemini-api-vs-agy-cli`)
- **Don't** use Perplexity MCP (disabled — expensive); `pwm` CLI only for genuine deep research
- **Don't** default to built-in `web_search` (2 RPS, 429-prone)

## Authority sources (scored)

| Source | Score | Key contribution |
|--------|-------|------------------|
| [arXiv:2508.05668 — Survey of LLM-based Deep Search Agents](https://arxiv.org/html/2508.05668v3) (Xi et al., SJTU+CSU, Aug 2025) | 12 | Canonical taxonomy: parallel/sequential/hybrid structures; decomposition vs diversification; reflection-driven loops |
| [arXiv:2502.18036 — Harnessing Multiple LLMs: LLM Ensemble Survey](https://github.com/junchenzhi/Awesome-LLM-Ensemble) (Chen et al., IJCAI 2026) | 12 | Before/during/after inference taxonomy; routing vs cascade vs non-cascade |
| [Cormack et al. SIGIR 2009 — Reciprocal Rank Fusion](https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf) | 12 | Original RRF paper; k=60 validated; the standard merging algorithm |
| [Azure AI Search — Hybrid search ranking with RRF](https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking) | 11 | Production implementation reference |
| [Elasticsearch — Reciprocal Rank Fusion](https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion) | 11 | Production implementation; multi-retriever RRF |
| [glaforge.dev — RAG-Fusion with RRF](https://glaforge.dev/posts/2026/02/10/advanced-rag-understanding-reciprocal-rank-fusion-in-hybrid-search/) (2026-02) | 10 | RAG-Fusion pattern: multi-query + RRF; LangChain4j example |
| [Perplexity Research — Advancing Search-Augmented LMs](https://research.perplexity.ai/articles/advancing-search-augmented-language-models) (2026-04) | 11 | Post-training pipeline for search agents; iterative retrieval |
| [FutureSearch / LessWrong — Guide for LLM-Assisted Web Research](https://www.lesswrong.com/posts/uAEhvX6scvcZANWwg/) (2025-06) | 12 | Independent benchmark; regular+search beats deep research; scaffolding matters |
| [Vellum — Best Web Search APIs & MCPs 2026](https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents) (2026-06-30) | 11 | Firecrawl 94% token reduction; provider comparison; "context engineering is 80%" |
| Host `IMPLEMENTATION_COMPLETE.md` | 11 | Local package status (2026-03-06) |
| Host `CLI_USAGE.md` | 11 | search-research modes, HyDE, saturation detection |

## Conflicts / caveats

- **⚠️ RRF k value:** original paper uses k=60; Elasticsearch default is 20; Azure lets you tune. No universal optimum — tune on your corpus if quality matters at the margin.
- **⚠️ FutureSearch "regular beats deep research"** is from June 2025; deep research tools (OpenAI, Gemini, Perplexity) have improved. Re-test before treating as load-bearing.
- **⚠️ "Saturation detection"** in search-research is listed in CLI_USAGE but not verified working. Probe before relying.
- **⚠️ Local package may have drifted** since March 2026. Re-run tests (`pytest` in package dir) before relying on it for production work.

## Codex conversation / implementation location

The search-research package at `P:/packages/.claude-marketplace/plugins/search-research/`
was built over 4 weeks (Phases 1-6) and marked COMPLETE on 2026-03-06. Key docs:

| Doc | Path | Purpose |
|-----|------|---------|
| `IMPLEMENTATION_COMPLETE.md` | package root | Phase-by-phase status; all 6 ✅ |
| `MIGRATION.md` | package root | How to migrate from `unified-search` (17KB, detailed) |
| `CLI_USAGE.md` | package root | All modes, HyDE options, examples |
| `BASELINE.md` | package root | Performance metrics for regression detection |
| `ROLLBACK_TRIGGERS.md` | package root | When/how to roll back |
| `DEPRECATION.md` | package root | `unified-search` deprecation announcement |
| `HYDE_IMPLEMENTATION_SUMMARY.md` | package root | HyDE design (14KB) |

**Codex session transcripts:** `~/.codex/sessions/2026/` (year-organized; specific session not located in this probe — would need grep for "search-research" or "unified-search" across session JSONLs to find the exact conversation).

**Git log signature:** commits are dominated by "chore: update settings" and "chore: update python module" — this is the Codex CLI's commit style (auto-generated), confirming the package was built via Codex, not hand-written.

**Is it finished?** Per `IMPLEMENTATION_COMPLETE.md`: yes, all 6 phases done. Per
`MIGRATION.md` (2026-07-09, 4 months later): still being maintained. The package is
usable but may have drifted from its March baseline — re-run tests before production use.

## Relationship to existing concepts

- **Refines** [[web-search-tool-routing]] — adds the "how to combine backends" layer that routing alone doesn't address.
- **Related** [[web-research-state-2026]] — the social/scraping state page covers platform-specific tools; this covers the algorithmic combination.
- **Related** [[llm-council-and-model-fusion]] — MoA/Fusion is the LLM-ensemble counterpart; RRF is the search-results-ensemble counterpart. Same principle (uncorrelated errors), different layer.
- **Related** [[multi-agent-correlated-errors]] — diversity + falsifier-gating applies to search backends too: different indices decorrelate, RRF is the aggregation that captures the benefit.

## Sources

- https://arxiv.org/html/2508.05668v3 — Survey of LLM-based Deep Search Agents (Aug 2025)
- https://arxiv.org/abs/2502.18036 + https://github.com/junchenzhi/Awesome-LLM-Ensemble — LLM Ensemble survey (IJCAI 2026)
- https://plg.uwaterloo.ca/~gvcormac/cormacksigir09-rrf.pdf — Original RRF paper (Cormack et al., SIGIR 2009)
- https://learn.microsoft.com/en-us/azure/search/hybrid-search-ranking
- https://www.elastic.co/docs/reference/elasticsearch/rest-apis/reciprocal-rank-fusion
- https://glaforge.dev/posts/2026/02/10/advanced-rag-understanding-reciprocal-rank-fusion-in-hybrid-search/
- https://spice.ai/learn/reciprocal-rank-fusion
- https://research.perplexity.ai/articles/advancing-search-augmented-language-models (2026-04)
- https://www.lesswrong.com/posts/uAEhvX6scvcZANWwg/a-guide-for-llm-assisted-web-research (2025-06)
- https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents (2026-06-30)
- `P:/packages/.claude-marketplace/plugins/search-research/IMPLEMENTATION_COMPLETE.md`
- `P:/packages/.claude-marketplace/plugins/search-research/CLI_USAGE.md`

## Staleness

Research survey papers are evergreen as method references. Provider capabilities
(Firecrawl, Vellum, Perplexity benchmarks) change quarterly — re-check if >6 months old.
Local package status should be re-verified by running tests before production reliance.
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
