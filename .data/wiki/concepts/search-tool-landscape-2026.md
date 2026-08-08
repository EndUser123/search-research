---
title: "Search tool landscape 2026: community verdicts, benchmarks, and optimal mix for /web and /www"
created: 2026-07-22
source: session-2026-07-22 (/www compound research)
sources:
  - https://aimultiple.com/agentic-search
  - https://webscraft.org/blog/search-api-dlya-ai-agentiv-scho-obirayut-rozrobniki-i-de-pomilyayutsya?lang=en
  - https://www.reddit.com/r/Rag/comments/1gr8jnr/which_search_api_should_i_use_between_tavilycom/
  - https://brave.com/learn/best-search-api-2026/
  - https://www.firecrawl.dev/blog/best-web-search-apis
  - P:/.data/wiki/concepts/web-search-tool-routing.md
  - P:/.data/wiki/concepts/web-research-state-2026.md
tags: [search-api, tavily, exa, brave, firecrawl, serper, duckduckgo, perplexity, social-search, benchmarks, comparisons, ai-agents]
host: both
agent: grok
verification: web_sources_cited
cognitive_load: 4
summary: "Community verdicts, benchmark data, and optimal backend mix for AI agent search. Covers: what practitioners like/dislike about Tavily, Exa, Brave, Serper, DDG, Perplexity; the AIMultiple 8-API benchmark (100 queries, LLM-judge); social media search strategies; and recommended tool sets for /web, /www, and deep research."
---

# Search tool landscape 2026: community verdicts, benchmarks, and optimal mix

Synthesized from the AIMultiple agentic search benchmark (100 queries, 8 APIs, LLM-judge), practitioner experience blogs, Reddit discussions, and our existing wiki inventory (`web-search-tool-routing`, `web-research-state-2026`, `optimal-multi-backend-search-strategy`).

## The benchmark: AIMultiple 8-API comparison (May 2026)

Source: [aimultiple.com/agentic-search](https://aimultiple.com/agentic-search) — 100 AI/LLM-domain queries, 4,000 results evaluated, GPT-5.2 LLM-judge, bootstrap statistics.

| Rank | API | Agent Score (95% CI) | Latency | Key finding |
|------|-----|---------------------|---------|-------------|
| 1 | **Brave** | 14.89 (13.80-15.93) | **669ms** | Only API to statistically outperform Tavily |
| 2 | **Firecrawl** | 14.58 (13.12-15.98) | 1,335ms | Top tier; best on deep content retrieval |
| 3 | **Exa** | 14.39 (13.25-15.50) | ~1,200ms | Top tier; best on technical docs |
| 4 | **Parallel Pro** | 14.21 (13.07-15.47) | **13,600ms** | Top tier quality but 20x slower |
| 5 | **Tavily** | 13.67 (12.62-14.76) | 998ms | Slightly below top tier; good latency |
| 6 | **Parallel Base** | 13.50 (12.38-14.66) | 2,900ms | Mid-tier |
| 7 | **Perplexity** | 12.96 (11.77-14.22) | **11,000ms** | Decent quality, terrible latency |
| 8 | **SerpAPI** | 12.28 (11.19-13.41) | 2,400ms | High quality per result but low relevance |

**Critical finding:** The top 4 APIs (Brave, Firecrawl, Exa, Parallel Pro) are **statistically indistinguishable** — overlapping confidence intervals mean the quality differences could be random variation. Only Brave vs. Tavily showed a statistically meaningful gap (~1 point).

**When quality is tied, latency decides:** Brave at 669ms vs Parallel Pro at 13,600ms means a 5-search agent loop takes 3 seconds vs 68 seconds.

## What practitioners like and dislike

Source: [webscraft.org practitioner comparison](https://webscraft.org/blog/search-api-dlya-ai-agentiv-scho-obirayut-rozrobniki-i-de-pomilyayutsya?lang=en), [Reddit r/Rag discussion](https://www.reddit.com/r/Rag/comments/1gr8jnr/).

### Tavily — the default for new AI agents

| Like | Dislike |
|------|---------|
| AI-optimized output (clean snippets, no HTML junk) | $0.008/query gets expensive at scale (~$300/mo at 45k queries) |
| Native integration with LangChain, Spring AI, CrewAI, AutoGen | Quality slightly below Brave (benchmark confirmed) |
| Separate extract endpoint for full-page RAG | Free tier (1,000/mo) is small |
| **Practitioner quote:** "tavily is good overall" (r/Rag) | |

### Brave — best quality + speed, but pricing risk

| Like | Dislike |
|------|---------|
| **Highest Agent Score** (14.89) + **lowest latency** (669ms) | Free tier removed Feb 2026 without warning |
| Independent index (not Google, not Bing) | Credit card required immediately; no spending cap |
| $5/1k queries with $5 free monthly credits (~1k free) | Results less "AI-optimized" than Tavily |
| Good for production where price matters | Requires attribution in product |
| **Practitioner quote:** "switched to Brave and added our own filtering and it works" (r/Rag) | |

### Exa — semantic search king for research

| Like | Dislike |
|------|---------|
| **Only neural search** — understands semantics, not just keywords | Weaker coverage of forums, social media, low-text pages |
| Best on technical documentation queries (benchmark) | 1,000 free/mo; Starter $49/mo for 5k |
| March 2026: first 10 results with full text are free per search | Higher cost at scale (~$135/mo at 45k) |
| **Practitioner quote:** "exa best for speed" (r/Rag) | Not a general-purpose replacement |

### Serper — cheapest Google SERP

| Like | Dislike |
|------|---------|
| **$0.30-1/1k queries** — cheapest option | Raw Google SERP, not AI-optimized (more token waste) |
| 2,500 free queries/month (most generous free tier) | Google v. SerpAPI lawsuit (Dec 2025) — legal risk for all Google-scraping providers |
| Fast (1-2 seconds) | Model receives "junk" with relevant content |

### DuckDuckGo — the free anonymous fallback

| Like | Dislike |
|------|---------|
| **Completely free, no API key required** | JSON endpoint broken from some hosts (DNS issues) |
| Independent index, different bias from Google | Not AI-optimized |
| No tracking | Lower quality than paid alternatives |
| **Practitioner quote:** "DuckDuckGo web search is nearly 7x faster than Google web search" (apiserpent) | Coverage gaps on specialized topics |

### Perplexity — synthesis quality, latency problem

| Like | Dislike |
|------|---------|
| Best for synthesized answers with citations out of the box | **11+ second average latency** — unusable for interactive agents |
| Good for factual verification queries | Expensive (operator disabled on our host for cost reasons) |
| Sonar Deep Research: searches hundreds of sources autonomously | Quality inconsistent across query types |

### Firecrawl — best scraping pipeline

| Like | Dislike |
|------|---------|
| **94% token reduction** vs raw HTML (2,788 vs 38,381 tokens/page) | Not primarily a search engine — it's a scraping/crawling pipeline |
| Full-page content extraction, JS-rendered pages | 1,000 credits/month free; paid plans start at €14/mo |
| Autonomous agent mode (1-5 min deep research) | Search API is secondary to scraping |
| **Our fleet already uses Firecrawl** as primary scraper + search backend | |

## The optimal mix for our fleet

Based on the benchmark, practitioner experience, and our existing inventory:

### Constraint-based grouping (free = use it unless something blocks you)

| Backend | Cost | Binding constraint | Verdict |
|---------|------|-------------------|---------|
| **mmx search** (CLI) | $0 (unlimited) | Subprocess overhead; Windows .cmd shim (use node-script resolver) | **Always use** — replaced minimax-search MCP (removed 2026-07-28) |
| **web-search-prime** | $0 (unlimited) | Shared GLM coding plan quota with glm-5-2 model | **Always use** — native config.toml MCP (migrated 2026-07-28) |
| **DDG** | $0, no key, no rate limit | JSON endpoint broken from this host (use ddgs lib or lite HTML) | **Always use** |
| **firecrawl** | 1k credits/mo free | Metered — refundable via feedback (1 credit per search feedback) | **Use for scraping; search costs 2 credits** |
| **Brave** | $5/mo free (~1k queries) | Metered beyond free; removed unlimited free tier Feb 2026 | **Use up to free quota** |
| **Exa** | 1k/mo free | Metered; first 10 results with full text free per search (Mar 2026) | **Use up to free quota; best for semantic/research** |
| **Serper** | 2.5k/mo free | Metered beyond; Google lawsuit risk (Dec 2025) | **Use up to free quota** |
| **HN Algolia** | $0, no key | None | **Always use for tech topics** |
| **Stack Exchange** | $0, no key | None (generous rate limits) | **Always use for technical Q&A** |
| **Reddit PRAW** | $0, 100 QPM | Rate limited above 100 QPM (generous) | **Always use for community signal** |
| **yt-dlp** | $0 | IP-level rate limiting; age-restricted needs cookies | **Use for YouTube transcripts** |
| **Mojeek** | $0, no key | Independent small index — lower coverage | **Use for additional diversity** |
| **Perplexity (pwm)** | $5/1k | Expensive; 11s latency | **Reserve for deep research only** |
| **Tavily** | Requires key | `TAVILY_API_KEY` is **SET** — MCP connected, CLI + SDK available | **Works** |

**Rule:** free + no binding constraint = use it. The only reason to exclude a free tool is if it adds **tool-selection confusion** (the degradation effect at 15-20 tools). The solution to that is the routing layer (search-research CLI `--mode auto`, or our `/web` routing) — not excluding the tool from the fleet.

### The "great results" mix

For a standard `/www` or `/web` run on a research topic:

```
Free + no constraint → fire them all in parallel:
1. web-search-prime (unlimited, recency/domain filters)
2. mmx search query (unlimited, MiniMax index)
3. DDG (free, no key, different ranking bias)
4. Mojeek (free, no key, independent small index)
5. HN Algolia (if tech topic)
6. Stack Exchange (if technical Q&A)
7. Reddit PRAW (if community signal needed)
→ RRF merge via search__fuse across all backends used
→ firecrawl_scrape top 3-5 results from the fused list
→ Brave/Exa/Serper as bonus queries within their free monthly quotas
```

For deep research:
```
1-5 above + 
6. firecrawl_agent (autonomous 1-5 min deep crawl)
7. Exa --hyde (semantic multi-perspective)
→ iterative refinement loop (search → assess gaps → search again)
```

## Social media search — the missing layer

Our wiki (`web-research-state-2026`) covers this well. Summary of what works:

| Platform | Free path | Quality | Key tool |
|----------|-----------|---------|----------|
| **Reddit** | OAuth via PRAW (100 QPM free) | Excellent — structured, API-accessible | `praw-dev/praw` |
| **YouTube** | yt-dlp + youtube-transcript-api | Good — transcripts are gold for tutorials | `yt-dlp/yt-dlp` |
| **X/Twitter** | Effectively dead for free API | Poor — 1 req/15min on free tier | `site:x.com` via web-search-prime |
| **LinkedIn** | No good free API | Workable via site: search + firecrawl | `site:linkedin.com` via web-search-prime |
| **Hacker News** | Algolia HN Search API (free) | Excellent — full-text, no auth | `hn.algolia.com/api` |
| **Stack Overflow** | Stack Exchange API (free) | Excellent — structured Q&A | `api.stackexchange.com` |

### How to integrate social into search

| Social source | When to search it | Backend to use |
|---------------|-------------------|----------------|
| Reddit | Community opinions, troubleshooting, unfiltered signal | `web-search-prime` with `site:reddit.com` or PRAW directly |
| YouTube | Tutorials, demos, conference talks | `web-search-prime` with `site:youtube.com`, then yt-dlp for transcripts |
| Hacker News | Practitioner signal on tech/AI topics | `hn.algolia.com/api` directly (free, no key) |
| Stack Overflow | Technical errors, implementation details | `api.stackexchange.com` directly (free, no key) |
| X/Twitter | Real-time signal, developer chatter | `web-search-prime` with `site:x.com` (limited but free) |
| LinkedIn | Professional/business signal | `web-search-prime` with `site:linkedin.com` |

## Tool selection degradation: the hidden problem

Source: [webscraft.org](https://webscraft.org/blog/search-api-dlya-ai-agentiv-scho-obirayut-rozrobniki-i-de-pomilyayutsya?lang=en).

A documented effect: **as tool count increases, selection accuracy decreases.**

| Tool count | Selection behavior |
|------------|-------------------|
| 3-5 | LLM chooses correct tool ~95% of the time |
| 10-15 | Systematic errors begin (calls Wikipedia instead of news search) |
| 20+ | Regular mis-selections (tool descriptions semantically overlap) |

**Solution: consolidate search into 1-2 universal tools** + use Tool RAG (vector search on a tool registry) for the rest. Our `/web` skill already consolidates via routing — the search-research CLI's `--mode auto` is exactly this pattern.

**Our risk:** our fleet has 20+ search surfaces (per `web-search-tool-routing`). The consolidation into minimax-search (default) + web-search-prime (scoped) + firecrawl (content) + search-research CLI (diversity) is the right architecture — 4 logical entry points, not 20.

## Pricing reality check at scale

Source: [webscraft.org cost analysis](https://webscraft.org/blog/search-api-dlya-ai-agentiv-scho-obirayut-rozrobniki-i-de-pomilyayutsya?lang=en).

At 45k queries/month (~500 users × 3 calls/session × 30 days):

| API | Monthly cost | AI-optimized? |
|-----|-------------|---------------|
| Tavily | ~$300 | Yes |
| Brave | ~$225 | Partial |
| Exa | ~$135 | Yes (neural) |
| SerpAPI | ~$450 | No (raw SERP) |
| Serper | ~$45 | No (raw SERP) |
| DDG | **$0** | No |
| Firecrawl | ~€71 (100k pages) | Yes (markdown) |
| **Our fleet** | **$0** (minimax + web-search-prime unlimited) | Yes (minimax) |

**Our advantage:** web-search-prime and mmx search are unlimited for this operator. This is a significant cost advantage — we pay $0 for the equivalent of ~$225-300/month in API costs.

## What we should also consider

1. **Wire the unused APIs.** Brave (`BRAVE_API_KEY` set) and Exa (`EXA_API_KEY` set) are ready in our env but not wired as MCPs. Wiring them would add benchmark-tier quality + index diversity.

2. **Exa --hyde for semantic research.** The search-research CLI supports `--mode exa --hyde`. For `/www` shape=research or shape=facts, this is the highest-quality path (neural search + multi-perspective HyDE).

3. **Social API integration.** Hacker News (Algolia) and Stack Exchange APIs are free with no key. Adding them as named backends in search-research would cover practitioner signal that general-web search misses.

4. **Tavily key is still empty.** If we want Tavily (the de facto AI agent standard), we need to set `TAVILY_API_KEY`. It's the only major API we're missing.

5. **Brave free tier was removed** (Feb 2026). New users only get $5 in credits. Our `BRAVE_API_KEY` predates this — verify it still works.

6. **Google v. SerpAPI lawsuit** (Dec 2025) creates legal risk for all Google-scraping providers (Serper, SerpAPI). Brave and Exa (independent indexes) are immune. DDG is immune.

## Conflicts

⚠️ **Benchmark vs. practitioner experience:** AIMultiple ranks Brave #1, but practitioners on Reddit say "tavily is good overall" and use it as default. Resolution: the quality difference is statistically insignificant for top 4 APIs — choice should be driven by **latency, cost, and ecosystem fit**, not raw quality scores.

⚠️ **Brave pricing stability:** Brave removed its free tier without warning in Feb 2026. Practitioners warn: "pricing may change again without notice." Don't build critical dependency on Brave's pricing model.

⚠️ **DDG speed claim:** "7x faster than Google" (apiserpent) — likely measures DDG's simple HTML response vs Google's complex SERP. For AI agents, the relevant comparison is API-to-API, where DDG is competitive but not 7x faster.

## Auto-related

- [[web-search-tool-routing]] — our full inventory + routing; this concept adds community verdicts and benchmark data
- [[optimal-multi-backend-search-strategy]] — RRF + iterative retrieval; this concept adds which backends to fuse
- [[web-research-state-2026]] — social media research state; this concept adds search-specific social strategies
- [[deep-research-systems-and-web-upgrade]] — deep research upgrade path; this concept informs which backends to use for --deep mode
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
