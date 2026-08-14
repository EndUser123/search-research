---
title: "somewhere in our tabs or history, is my quota info for z.ai coding pro plan.  What's the quota / rate limits?"
date: "2025-12-10"
mode: "COPILOT"
uuid: "94671567-1657-48ad-9b4e-738d9772a0f6"
entry_count: 6
---

## Human

somewhere in our tabs or history, is my quota info for z.ai coding pro plan.  What's the quota / rate limits?

## Assistant

Your z.ai GLM Coding Pro plan gives you roughly 600 prompts every 5 hours in supported coding tools, plus an MCP/web-tools quota on top of that.[1][2][3]

## Prompt / rate limits

- Coding Pro: about 600 prompts per 5‑hour window, used when you call GLM‑4.6 from supported coding IDE tools like Claude Code, Cline, OpenCode, etc.[2][3]
- Quota refresh: once you hit the cap, you wait until the next 5‑hour cycle for it to fully reset; there is no separate weekly cap like Anthropic’s own Pro/Max plans.[1][2]
- Billing separation: these plan prompts only apply inside supported tools; direct API calls to GLM models are billed separately and do not consume your Coding Pro quota.[4][2][1]

## MCP / web search quota

- For MCP/web tools, the Pro plan includes around 1,000 web searches plus web-reader calls in total, again tied to the same 5‑hour maximum prompt pool for vision and related tools.[1]
- Lite and Max use the same structure with smaller or larger web/MCP quotas (Lite around 100, Max around 4,000), so Pro sits in the middle in terms of these non-chat limits.[5][1]

## Human

What's the difference between web reader and web search?

## Assistant

Web search is for finding relevant pages on the internet from a query, while web reader is for fetching and parsing the full content of a specific page by URL.[1][2]

## Web search

- Runs a search engine (like `search-prime`) over the open web given a natural-language query, and returns structured results (titles, URLs, summaries, etc.).[3][1]
- Used when the model does not yet know which site to read, and needs discovery, ranking, and freshness filters (time ranges, domain filters, result counts).[1][3]

## Web reader

- Given a specific URL, downloads and parses the page to return cleaned main content, title, metadata, and links, usually via the Web Reader MCP server.[2]
- Used after a page is already chosen (by you or via search) so the model can deeply read docs, blogs, GitHub READMEs, etc., and extract structured information.[2]

## Quota behavior in plans

- In the GLM Coding Lite/Pro/Max plans, “web search” and “web reader” share the same MCP bucket: each call to either tool consumes from a combined pool (e.g., 1,000 total for Pro in each 5‑hour window).[4][5][2]

## Human

3. Brave Search (--mode brave)
    - Engine: Brave Search API
    - API: Privacy-focused web search
    - Endpoint: [https://api.search.brave.com/res/v1/web/search](https://api.search.brave.com/res/v1/web/search)
    - Status: Available (needs BRAVE_SEARCH_API_KEY)
  4. Exa Neural Search (--mode exa)
    - Engine: Exa's neural search
    - Features: Semantic and conceptual search
    - Status: Available (needs EXA_API_KEY)
  5. GitHub/Octocode (--mode octocode)
    - Engine: GitHub API
    - Focus: Code repository search
    - Status: Available for code search

What are the quotas or rate limits?

I think Tavily is like the above.  What else is like the above?

## Assistant

Brave, Exa, Tavily, etc. are all “web search APIs for LLMs/agents,” but each has its own usage and rate limits; GitHub/Octocode is constrained by GitHub’s much stricter search/code-search caps.[1][2][3][4]

## Quotas / limits you asked about

- GitHub / Octocode: Uses the GitHub API, which has a general REST limit of around 5,000 core requests per hour per authenticated user, but a much lower search/code-search budget (roughly tens of search requests per minute, and a small separate bucket for code search, often around 10 code-search requests per minute). Octocode itself just sits on top of those limits and exposes rate-limit info via its own metadata tools.[2][5][6][7][8]
- Brave Search API: Commercial paid API; pricing is per 1,000 queries (around a few dollars per 1k), with plan-specific request caps and higher tiers for production, but public docs emphasize pricing more than a simple “N req/min” number, so you’ll typically be constrained by your paid quota rather than a hard low rate limit like GitHub’s.[9][4]
- Exa Neural Search: AI-native semantic search API priced by search count (for example around low single-digit dollars per 1,000 searches); rate limits are primarily quota/plan-based rather than a tiny per-minute cap, and Exa is explicitly positioned for high-volume agent/RAG workloads.[10][3]

(For each of these, the exact numbers depend on your paid plan, so the above is the structural picture; you’d check your account dashboard for your precise per-minute/per-day caps.)

## “Like Tavily” – similar APIs

Tavily is in the same family as Exa and Brave: AI‑oriented web search APIs designed to be called by LLM agents to get fresh web results with summaries/structured output. Other APIs in this “LLM-friendly web search” bucket include:[3][4][10]

- Firecrawl: Web search plus integrated content extraction; marketed specifically for RAG/agents, priced and limited similarly by credits/requests.[3]
- SerpAPI / Serper: General SERP wrappers for Google/Bing with JSON output; frequently used as drop‑in web search backends for LLM tools, limits are per‑request/credits per month rather than ultra‑tight minute caps.[4][3]
- Perplexity API, DuckDuckGo, Kagi, Google Custom Search, You.com API: All provide JSON search endpoints that can be wired into agents; practical limits are determined by your paid tier and credits, not tiny search-per-minute ceilings like GitHub’s code search.[10][4][3]

So conceptually: Brave, Exa, Tavily, Firecrawl, SerpAPI/Serper, Perplexity API, etc. form your “LLM web search stack,” while Octocode/GitHub is a separate “code corpus search” stack with much stricter search rate limits that you have to treat as a scarce resource.[1][2][10][3]

## Human

What are the free tier quotas / rate limits for the LLM web search stack?

## Assistant

For LLM-friendly web search APIs, typical free tiers today look like “low QPS plus a few thousand queries or credits per month,” with anything heavier needing a paid plan.[1][2][3][4]

## Brave Search API

- Free tier: About 1 query per second and roughly 2,000–5,000 queries per month, depending on whether you use the general Search API or the newer “AI Grounding” variant.[5][6][7][1]
- Above that, paid tiers jump to tens of QPS and tens of millions of queries per month, but those are no longer “free.”[8][1]

## Tavily

- Free tier: 1,000 API credits per month, no card required, with credits resetting on the first of each month.[2]
- Cost model: Basic searches consume 1 credit, advanced searches 2 credits; extraction operations consume credits per batch of successful URL extractions, so effective free volume depends on depth and extract usage.[9]

## Exa

- Free usage: Exa does not publish a fixed “X free calls/month” number; instead, it gives new accounts a one-time pool of about 10 USD worth of free credits to get started.[4]
- Rate limits: Default caps are around 5 QPS on core search/answer endpoints and 50 QPS on content fetch, with a concurrency cap on long-running research tasks, and higher limits available on request.[3]

## Others in the same stack

- Perplexity Search API: No standing, metered “free tier” for the API itself; some accounts receive a small recurring credit (around a few USD in usage) but this is not documented as a guaranteed free plan.[10][11]
- Bing Web Search (for comparison): Developer accounts commonly get around 1,000 free calls/month on a dev tier before needing a paid plan, which is why it’s often used alongside Brave/Tavily/Exa for prototyping.[10]

## Human

Workarounds to stay within 1 qps free tier limits in production

## Assistant

To stay within a 1 QPS free-tier limit in production, treat the external search API as a scarce, queued resource and aggressively batch, cache, and degrade usage before calling it.[1][2][3]

## Core patterns

- Centralized rate limiter: Put all calls to Brave/Tavily/Exa/etc. through a single gateway or service that enforces 1 request per second using a token-bucket or leaky-bucket algorithm, optionally allowing small bursts with a bounded bucket size.[4][5][3]
- Queue-based throttling: When more than 1 request/second arrives, enqueue jobs and drain them at 1 QPS, with a max wait timeout so you can drop or fall back instead of stampeding the provider.[6][2]

## Reduce actual call volume

- Caching layer: Cache search results by normalized query (and maybe key params like date range, region) with a TTL; most “same question” traffic should be served from cache without hitting the external API.[7][8]
- Semantic deduping: Before calling search, embed the incoming user query and deduplicate against recent queries; if it’s similar enough to a cached query, reuse or lightly post-process that result instead of calling search again.[1]
- Batch & precompute: For known workloads (e.g., scheduled reports, FAQ-style flows), pre-run searches off-peak and store structured results, so the real-time path performs fewer or no live web calls.[2][1]

## Degrade gracefully instead of erroring

- Fallback modes: When the queue is full or wait-time budget is exceeded, switch to cheaper data sources: local RAG index, previously crawled content, or slower background jobs that update answers asynchronously.[9][1]
- Priority + quotas per feature: Assign budgets per user/feature (e.g., “max 5 web calls per conversation”) and a priority queue so critical actions (security, billing, core UX) win over “nice-to-have” augmentation.[10][11]

## Implementation tips (for your stack)

- Per-process vs distributed: For a single service, in-memory counters or token bucket are fine; for multi-instance deployments, use a shared store (Redis) or your API gateway’s built-in throttling so the cluster collectively stays under 1 QPS.[8][12][13]
- Observability: Log external-call timestamps, queue depth, and provider 429s; set alerts when utilization approaches 80–90% of the free-tier budget so you can tighten caching or reduce call sites before hitting hard limits.[14][10]

## Human

Tavily Brave Exa Serper Perplexity GLM (both 4.6V and 4.6V flash), is there an optimal search strategy?  I'm going to use search expansion and verbal sampling (maybe) to explore the information space, then use more search on the information dense areas.

## Assistant

A good pattern is: use one semantic, LLM-friendly search API (Tavily/Perplexity/Exa) as your “frontline explorer,” then selectively fan out to Brave/Serper and only deepen with more calls where GLM judges the area as information-dense.[1][2][3]

## Roles for each search API

- Tavily: Strong default for RAG/agents since it bundles search, extraction, and summarization in one call; good as the primary “broad explorer” for your expansion/sampling loop.[4][5][3]
- Exa: Best when you already have a few good seeds and want “more like this” (semantic expansion on URLs, papers, repos); plug it in after GLM flags a cluster as promising.[6][2][7]
- Perplexity Search API: Higher-cost, high-quality deep research; reserve for narrow, high‑stakes questions where a single, strong, synthesized answer is worth multiple cheaper calls.[2][5]
- Brave: Large, independent index and good raw coverage; use as a complementary “ground truth SERP” when Tavily/Exa disagree, or when you need diversity beyond Bing-derived indexes.[8][9][10]
- Serper (or similar SERP APIs): Cheap, keyword-ish SERP snapshots; helpful for quick breadth sweeps and for feeding your own reader/crawler before doing semantic refinement.[11][4]

## Suggested query strategy with GLM 4.6V

- Phase 1 – Exploration: Let GLM generate 3–6 expanded queries via verbal sampling, then hit Tavily (or Exa/Perplexity for high‑value tasks) in parallel with shallow depth; cluster results by domain/topic and score them for density/novelty.[1][2]
- Phase 2 – Focus: For the top 1–2 clusters, use Exa’s “find similar” or Tavily with higher depth to pull more sources and full‑page content, driven by follow‑up queries that GLM refines based on gaps it detects.[3][6][2]
- Phase 3 – Cross-check & finalize: Where answers matter, cross-check one representative query via Brave or Serper and, if needed, a Perplexity deep call, then let GLM 4.6V synthesize using citations and internal consistency checks.[5][8][2]

## Efficiency and quota considerations

- Assign roles by cost: cheap/high‑volume (Tavily, Brave, Serper) for exploration; mid‑cost semantic (Exa) for targeted expansion; expensive synthesis (Perplexity) sparingly at the end.[12][10][4][5]
- Cache by semantic intent: store Tavily/Brave/Exa responses keyed by clustered query intent so repeated verbal samples often hit cache, and only trigger new calls when GLM detects a genuinely new angle.[13][4]
