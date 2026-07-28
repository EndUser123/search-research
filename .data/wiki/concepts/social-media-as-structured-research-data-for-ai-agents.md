---
title: "Social Media as Structured Research Data for AI Agents"
slug: social-media-as-structured-research-data-for-ai-agents
created: 2026-07-28
category: reference
tags: [social-media, reddit, linkedin, twitter, hacker-news, research, data-sources, api, scraping]
summary: >
  How to use Reddit, LinkedIn, X/Twitter, Hacker News, YouTube, and Discord
  as structured data sources for AI research pipelines. Covers free-tier
  API limits, authentication requirements, recommended libraries, and how
  production deep-research tools (Perplexity, OpenAI, Gemini, Anthropic)
  integrate community signals. Reddit at 100 QPM via PRAW and HN via
  Firebase+Algolia are the viable free backbone. X and LinkedIn are
  effectively paywalled. Perplexity's 20-24% Reddit citation share proves
  community data is now a research primitive, not an optional extra.
cognitive_load: 2
verification: multi-source-verified
agent: grok
host: both
sources:
  - "Profound AI citation study (~700K ChatGPT citations, Oct-Dec 2025)"
  - "Evertune 200M-prompt analysis (Perplexity citation share)"
  - "Reddit Data API Wiki (May 2026, free tier specs)"
  - "X Developer Community (API pricing, Academic Research tier)"
  - "HN Firebase API docs + Algolia HN Search docs"
  - "Apify, Bright Data, Oxylabs pricing pages"
  - "PullPush.io (Pushshift replacement)"
  - "arXiv:2502.00627 (Discord Unveiled dataset)"
  - "arXiv:2512.14720 (SoMe benchmark for LLM social agents)"
  - "Open-source: langchain-ai/open_deep_research, assafelovic/gpt-researcher, Alibaba-NLP/DeepResearch"
relations:
  - target: wiki/concepts/web-research-state-2026.md
    type: refines
  - target: wiki/concepts/search-tool-landscape-2026.md
    type: related
  - target: wiki/concepts/youtube-watch-later-and-history-playlist-url-extraction.md
    type: related
---

# Social Media as Structured Research Data for AI Agents

## Decision context

**The problem:** `/www` research subagents consistently hit a wall with social
media sources — they can *find* Reddit threads via `site:reddit.com` search,
but can't *read* the full discussion content. This limits research quality
when community sentiment is the primary signal (e.g., "what tools do people
actually like?"). The question: how should our research pipeline integrate
social platforms as structured data sources, and what's the current state of
free-tier access?

**What the research changed:** confirmed Reddit PRAW + HN APIs as the viable
free backbone. Surfaced PullPush.io as a Pushshift replacement for historical
Reddit data. Discovered that Perplexity's 20-24% Reddit citation share proves
community data has crossed the threshold from "optional enrichment" to
"research primitive." Identified the licensing moat pattern (Google paid
Reddit $60M/yr; Perplexity sued, then paid $42.5M) that shapes who can
access what.

## Platform-by-platform state (2026)

### Reddit — viable free backbone (with setup)

| Aspect | Value |
|--------|-------|
| Free tier | 100 QPM with OAuth (144K requests/day) |
| Without OAuth | 10 QPM — but `.json` endpoints now 403 blocked from this host |
| Paid tier | $0.24 per 1,000 calls |
| Commercial use | Forbidden on free tier |
| Auth | OAuth 2 (script app type for read-only research) |
| Library | PRAW (`praw-dev/praw`), well-maintained |
| Setup | 5 min at reddit.com/prefs/apps → create script app → env vars |

**Key insight from research:** Reddit is the #1 most-cited source by major AI
platforms. Perplexity cites Reddit in 20-24% of all responses (Evertune
200M-prompt analysis). ChatGPT cites Reddit 2.4% of the time. The gap
reflects Perplexity's deliberate "Social" mode + three-layer ML reranker
that structurally favors community content.

**Historical data:** Pushshift is gone, but **PullPush.io** is the drop-in
replacement — free, supports cross-subreddit full-text search. Monthly dumps
available for top 40k subreddits through end of 2024.

### Hacker News — best free data available

| Aspect | Value |
|--------|-------|
| Firebase API | 1,000 requests/hour per IP, no auth |
| Algolia Search | 10,000 requests/hour per IP, no auth |
| Cost | Free, no key |
| Data | Stories, comments, votes, user profiles, job postings |

**Verified working from this host** (2026-07-28): HN Algolia returned
relevant results for "yt-dlp watch later" immediately. Stack Exchange API
also works (free, no key). These two are the zero-setup social data sources.

### X/Twitter — effectively paywalled

| Aspect | Value |
|--------|-------|
| Free tier | 100 post reads/month, 17 posts/24hrs (unusable for research) |
| Academic Research | $0 for verified university researchers, up to 10M tweets |
| Basic | $200/mo (closed to new signups) |
| Discovery workaround | `web-search-prime` with `site:x.com` + oEmbed for individual tweets |

**Reality:** the free ecosystem collapsed in 2023-2024 and hasn't recovered.
For `/www` research, `site:x.com` discovery via web-search-prime is the
ceiling without spending money or having academic credentials.

### LinkedIn — most restricted

| Aspect | Value |
|--------|-------|
| Official API | Requires partnership approval, very narrow |
| Apollo.io free | 50-100 credits/month, 50 calls/min |
| Bright Data | 5,000 free records/month on new accounts |
| Scraping risk | LinkedIn actively sues scrapers (hiQ v. LinkedIn) |

**For `/www`:** `site:linkedin.com` + firecrawl_scrape for specific profiles
is the workable path. No bulk research is feasible without paid services.

### YouTube — fully working

| Aspect | Value |
|--------|-------|
| yt-dlp | Free, transcript extraction, playlist export |
| youtube-transcript-api | Free, PyPI |
| Data API v3 | Free tier with 10K units/day quota |
| Firecrawl | Has `/transcript` endpoint (available on this host) |

Already integrated into our pipeline. See
[[youtube-watch-later-and-history-playlist-url-extraction]].

### Discord — conditional

Bot API is free but requires server membership. No historical backfill
(must be in server at time of message). Not relevant for `/www` research
unless targeting specific communities.

## How production deep-research tools integrate social data

| Tool | Reddit integration | Social weighting | Open-source equivalent |
|------|-------------------|-----------------|----------------------|
| **Perplexity** | #1 source (20-24% of citations); dedicated "Social" mode | Three-layer ML reranker favors community content | `gpt-researcher` (closest) |
| **Google Gemini** | Licensed via $60M/yr Reddit deal | Native Reddit Data API access | `gemini-fullstack-langgraph-quickstart` |
| **OpenAI Deep Research** | 2.4% Reddit citations; no special social mode | Standard retrieval, no social weighting | `open_deep_research` (LangChain) |
| **Anthropic Claude** | No explicit social special-casing | Source-quality heuristics (prefer authority over SEO farms) | Multi-agent orchestrator pattern |
| **LangChain Open Deep Research** | BYO MCP/retriever | Operator-configured | This is the pattern we should follow |

**The key architectural pattern for us:** open-source deep research has
converged on **pluggable retrievers / MCP servers** as the integration
primitive. The operator brings the social-source connection (Reddit PRAW,
HN API, etc.) via MCP or direct Python calls. No built-in social weighting
unless the operator configures it.

## What this means for `/www` and our research pipeline

### The gap we need to close

Current state (verified 2026-07-28):

| Source | Discovery | Full content extraction | Gap |
|--------|-----------|------------------------|-----|
| HN | ✅ Algolia API | ✅ Same API | **None — working** |
| Stack Exchange | ✅ API | ✅ API | **None — working** |
| Reddit | ✅ `site:reddit.com` | ❌ `.json` 403, PRAW not installed | **Setup needed** |
| YouTube | ✅ search + yt-dlp | ✅ yt-dlp + transcript-api | **None — working** |
| X/Twitter | ✅ `site:x.com` | ⚠️ oEmbed only | **Paywall — accept limit** |
| LinkedIn | ✅ `site:linkedin.com` | ⚠️ firecrawl per-URL | **Accept limit** |

### Recommended integration (not a `/www` skill change)

The fix is infrastructure, not skill edits:

1. **Install PRAW + set up Reddit OAuth** (5 min one-time setup):
   ```
   pip install praw
   # Create script app at reddit.com/prefs/apps
   # Set REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET, REDDIT_USER_AGENT
   ```
   This unlocks 100 QPM — enough for any research run.

2. **Add HN + Stack Exchange to `/www` Round 1 default queries** (one
   directive in the skill, not a new section): "For community signal, add
   HN Algolia and Stack Exchange API queries alongside the default backends.
   Both are free, no-key, and provide high-quality practitioner signal."

3. **Accept X and LinkedIn limits.** `site:` discovery + per-URL scrape is
   the ceiling. Don't invest engineering time in paywalled platforms.

4. **PullPush.io for historical Reddit research.** When a topic needs
   longitudinal data (how sentiment changed over time), PullPush provides
   free cross-subreddit full-text search without API limits.

### Why not add a "social mode" to `/www`

The 2026-07-26 self-assessment found `/www` is already bloated (516 lines).
Adding social-source routing as a skill feature would be more ceremony.
The fix is pluggable infrastructure (PRAW + HN API), not skill complexity.
`/web`'s routing logic already handles `site:reddit.com` → PRAW dispatch —
the gap is just that PRAW isn't installed.

## Falsifier

This concept is wrong if:
- Reddit further restricts the free API (possible — the trend is toward
  paywalled access; the $60M Google deal signals Reddit values its data)
- HN Algolia or Firebase changes their free tiers (unlikely — YC has kept
  HN free since 2007)
- A new social platform emerges with genuinely free API access for AI
  agents (possible — Bluesky's AT Protocol is a candidate)
- MCP-based social data servers become standard (would change the
  integration pattern from direct API calls to MCP plug-ins)

## Sources

- [Reddit Data API Wiki](https://github.com/reddit-archive/reddit/wiki/API) — free tier specs (100 QPM OAuth, 10 QPM unauthenticated)
- [PRAW — praw-dev/praw](https://github.com/praw-dev/praw) — canonical Python Reddit API wrapper (BSD-2-Clause)
- [PullPush.io](https://pullpush.io) — Pushshift replacement for historical Reddit data
- [HN Firebase API](https://github.com/HackerNews/API) — official HN API docs (1,000 req/hr)
- [HN Algolia Search API](https://hn.algolia.com/api) — full-text search (10,000 req/hr)
- [X API pricing](https://developers.x.com) — pay-per-use model, Academic Research tier
- [Evertune 200M-prompt analysis](https://evertune.ai) — Perplexity Reddit citation share (20-24%)
- [Profound AI citation study](https://profound.ai) — ChatGPT citation distribution (~700K citations)
- [langchain-ai/open_deep_research](https://github.com/langchain-ai/open_deep_research) — open-source deep research pattern
- [assafelovic/gpt-researcher](https://github.com/assafelovic/gpt-researcher) — pluggable retriever architecture
- [Alibaba-NLP/DeepResearch](https://github.com/Alibaba-NLP/DeepResearch) — fully open-source deep research model
- [arXiv:2512.14720](https://arxiv.org/abs/2512.14720) — SoMe benchmark for LLM social media agents
- [arXiv:2502.00627](https://arxiv.org/abs/2502.00627) — Discord Unveiled dataset (2B messages)

## Related

- [[web-research-state-2026]] — the existing reference (this concept refines
  it with 2026-07-28 verification + deep-research tool comparison)
- [[search-tool-landscape-2026]] — backend benchmarks
- [[youtube-watch-later-and-history-playlist-url-extraction]] — YouTube
  extraction already integrated
