---
title: "does z.ai with their coding plan have a working mcp server for internet searches?"
date: "2026-06-30"
mode: "COPILOT"
uuid: "c09118f1-a6a2-4ae0-841a-9fb941bdde95"
entry_count: 5
---

## Human

does z.ai with their coding plan have a working mcp server for internet searches?

## Assistant

Yes, **z.ai's coding plan includes a working Web Search MCP server specifically for internet searches**, and it is **exclusive to the Coding Plan**.[1][2]

### Key details about the Web Search MCP Server:

| Attribute | Description |
|-----------|-------------|
| **Name** | Web Search MCP Server (Coding Plan Exclusive) [1] |
| **Type** | Remote MCP Server (HTTP-based, no local installation required) [1][2] |
| **Primary Tool** | `webSearchPrime` — searches web information, returning page titles, URLs, summaries, site names [2] |
| **Capabilities** | Search latest technical documentation, API changes, open-source project info, best practices [1] |
| **Compatible Clients** | Claude Code, Cline, and any MCP-compatible client [1][2] |
| **API Key Required** | Yes, from Z.AI Console [1][2] |

### Important distinction:
- **All coding plans support MCP**, but the **Lite plan does NOT include the MCP search feature** (only Pro/Max tiers get it).[3]
- The Web Search MCP is a **z.ai-exclusive remote server**, separate from third-party options like Brave Search or Firecrawl.[3]

You'll configure it by adding a user service with your `Z_AI_API_KEY` and using the endpoint `https://api.z.ai/api/mcp/web_search_prime/mcp`.[3]

Do you have a specific coding plan tier (Lite, Pro, or Max), since this affects whether you get the MCP search feature?

## Human

does it actually work?

## Assistant

**No, it doesn't reliably work** — there are significant, well-documented issues with the z.ai Web Search MCP server for Coding Plan users.

### Key problems reported:

| Issue | Details |
|-------|---------|
| **429 "insufficient balance"** | Official endpoint (`web_search/sse`) returns 429 even with active quota on Pro plans [1] |
| **Empty results** | Alternative endpoint (`web_search_prime/sse`) authenticates but returns `[]` for every query [1] |
| **Backend disconnected** | Web search backend appears not properly connected for Coding Plan API keys [1] |
| **Out of order for months** | User reports it stopped working around January 2026 and hasn't been fixed [1] |
| **Connection failures** | z.ai MCP servers show connection errors in `/status` after OpenCode v1.0.137 update [2] |

### What users say:

> *"I've been trying to get the Z.AI Web Search MCP working with Claude Code on my GLM Coding Pro (Yearly) plan and spent hours debugging this. It's been out of order for months, and I doubt they'll ever repair it."*[1]

> *"At the moment the z.ai search isn't working—it simply returns [] on every request and only uses API tokens when it does respond."*[1]

### Recommendations:

Instead of relying on z.ai's broken Web Search MCP, use **third-party alternatives** that work:

- **Brave Search MCP** (free tier available)[3]
- **Firecrawl MCP** (for web content extraction)[3]
- **Custom MCP server** for search (users suggest adding a new MCP server for searching)[1]

The **documentation claims it works**, but **real-world user experience shows it's broken** — this is a common pattern where promised features don't match deployment reality.[4][5]

Would you like help setting up a working Brave Search or Firecrawl MCP instead?

## Human

what about minimax and opencode-zen or opencode-go?

## Assistant

## Summary: MiniMax vs z.ai for Web Search MCP

### **MiniMax Coding Plan MCP: WORKS** ✅

| Attribute | Status |
|-----------|--------|
| **Web Search** | Official `web_search` tool returns structured results with titles, URLs, snippets, related queries [1][2][3] |
| **Functional Status** | "Already part of what you pay for" — users report it works reliably [4] |
| **Setup** | Configure via `minimax-coding-plan-mcp` with `uvx` [1][5] |
| **Auth Requirements** | May need real-name verification for some regions; auth errors if API setup incomplete [6] |
| **Official Docs** | Platform docs confirm web_search MCP provides web search + browsing [7][5] |

**MiniMax setup command:**
```json
{
  "mcp": {
    "MiniMax": {
      "type": "local",
      "command": ["uvx", "minimax-coding-plan-mcp", "-y"],
      "environment": {
        "MINIMAX_API_KEY": "YOUR_KEY",
        "MINIMAX_API_HOST": "https://api.minimax.io"
      }
    }
  }
}
```


***

### **OpenCode Zen / OpenCode Go: NOT MCP PROVIDERS** ❌

| Platform | What it actually is |
|----------|---------------------|
| **OpenCode Zen** | AI **gateway** for coding models (GLM-5.2, Kimi, MiniMax M3, Qwen3.7, DeepSeek V4) [8][9] |
| **OpenCode Go** | Low-cost **subscription** ($5 first month, $10/month) for model access [8][10] |
| **Web Search** | Built-in **websearch tool** (not external MCP) — use `websearch` vs `webfetch` for discovery vs retrieval [11] |

Key difference: OpenCode Zen/Go are **model providers**, not MCP server providers. They give you access to models via API endpoints, but you still need to configure separate MCP servers for tools like web search.

***

### Recommendation Table

| If you need... | Use... |
|----------------|--------|
| **Working web search MCP** | MiniMax Coding Plan MCP (confirmed functional) [4][5] |
| **Free search option** | Brave Search MCP (free tier) or TinyFish web search (no API key) [12][13] |
| **Model access gateway** | OpenCode Zen/Go for models, but add separate MCP for tools [8][10] |

**Bottom line:** MiniMax is the working alternative to broken z.ai for web search MCP. OpenCode Zen/Go don't provide MCP servers — they're model gateways.

Do you want help setting up MiniMax's web search MCP, or would you prefer a free option like TinyFish or Brave?

## Human

what are some best mcp servers for web searching?

## Assistant

Here are the **best MCP servers for web searching**, categorized by use case:

## Top MCP Servers for Web Search

### **1. Featured Best Options**

| MCP Server | Best For | API Key Required | Cost | Key Features |
|------------|----------|------------------|------|--------------|
| **Firecrawl MCP** | Most capable web data (search + scrape + crawl + browser automation) | Yes | Free tier + paid | Search, scraping, crawling, browser automation, structured extraction [1][2][3] |
| **Brave Search MCP** | #1 most-used for LLMs, scale + quality balance | Yes | Free tier (5k queries/mo) + paid | 30B pages, 5 snippets per result, web/local/images/videos/news search [4][5][6] |
| **Perplexity MCP** | Real-time web-wide research with reasoning | Yes | Free credits + paid | Sonar API for conversational AI, ranked results with metadata [7][8][9] |
| **Kindly Web Search MCP** | Real-time page parsing + intelligent fallback | Yes (Serper/Tavily) | Paid | Parses any page with headless browser, instant content to LLM, no 2nd scrape call needed [10][11][12] |

***

### **2. Free / No-API-Key Options**

| MCP Server | Search Engines | Best For | Setup Complexity |
|------------|----------------|----------|------------------|
| **OpenWebSearch MCP** | Bing, Baidu, DuckDuckGo, Brave, Exa, CSDN, Github | Free multi-engine, no API keys, structured data | Low [13][14][15] |
| **DuckDuckGo MCP** | DuckDuckGo | Privacy-focused, no auth required (2,400+ views) | Very low [16] |
| **Google Search MCP** | Google (Playwright-based) | Bypasses anti-scraping, free Google results | Medium [17][18] |
| **Web Search MCP (mrkrsl)** | Direct connections | Local LLMs, no API keys | Low [19] |

***

### **3. Quick Setup Comparison**

| Server | Setup Command | Auth |
|--------|---------------|------|
| **Brave Search** | `npx -y brave-search-mcp --http --ui` | `BRAVE_API_KEY` [20] |
| **Firecrawl** | `npx -y firecrawl-mcp` | `FIRECRAWL_API_KEY` [3] |
| **Perplexity** | `npx -y @perplexity-ai/mcp-server` | `PERPLEXITY_API_KEY` [8] |
| **OpenWebSearch** | `https://open-websearch--aas-ee.run.tools/mcp` | None [15] |
| **Kindly** | `docker run ... kindly-web-search-mcp-server --http` | `SERPER_API_KEY` or `TAVILY_API_KEY` [11] |

***

### **4. Recommendation by Use Case**

| Your Need | Use... |
|-----------|--------|
| **Most powerful** | Firecrawl (search + scrape + crawl + browser) [1] |
| **Scale + reliability** | Brave Search (30B pages, #1 for LLMs) [4][6] |
| **Free no-auth** | OpenWebSearch or DuckDuckGo [13][16] |
| **Research + reasoning** | Perplexity (Sonar API) [8] |
| **Real-time parsing** | Kindly (headless browser, instant LLM content) [11] |

***

### **5. Confidence Assessment**

| Server | Working Status | Evidence Quality |
|--------|---------------|------------------|
| Firecrawl | ✅ Confirmed working | Official docs + user reports [1][3] |
| Brave | ✅ Confirmed working | Official + AWS Marketplace [4][6] |
| Perplexity | ✅ Confirmed working | Official docs [8] |
| Kindly | ✅ Open-sourced (Jan 2026) | GitHub + Reddit announcement [10][11] |
| OpenWebSearch | ✅ Free tier | Multiple sources [13][15] |

***

Do you want help setting up one of these? I'd recommend:
- **Brave Search** if you want reliability + scale
- **OpenWebSearch** if you want free/no-auth
- **Firecrawl** if you need scraping + search combined

Which would you prefer?

## Human

what are the free or 500+ searchs/month options?

## Assistant

Here are the **best free or 500+ searches/month options** for web search MCP servers:

## Free Version Options (No API Key Required)

| MCP Server | Searches/Month | Cost | Auth Required | Key Features |
|------------|---------------|------|---------------|--------------|
| **OpenWebSearch MCP** | Unlimited | Free | No | Bing, Baidu, DuckDuckGo, Brave, Exa, CSDN; multi-engine scraping; structured data [1][2][3] |
| **DuckDuckGo MCP** | Unlimited | Free | No | Privacy-focused; no authentication; instant setup [4] |
| **Google Search MCP (mrkrsl)** | Unlimited | Free | No | Direct connections; no API keys; for local LLMs [5] |
| **Google Search MCP (pskill9)** | Unlimited | Free | No | Free Google results via Playwright; bypasses anti-scraping [6] |
| **WebSearch-MCP** | Unlimited | Free | No | Self-hosted; entirely free [7] |

***

## Paid-Free Tier Options (500+ searches/month)

| MCP Server | Free Tier | Monthly Price | Cost/1K Queries | Features |
|------------|-----------|---------------|-----------------|----------|
| **Exa** | **20,000 requests/month** | Free tier | $3.00 | Best free tier! Web search + webpage text + highlights; 180ms–1s latency [8][9] |
| **Brave Search** | **2,000 queries/month** | $3/1K queries | $1.00 | 30B pages index; 5 snippets/result; web/local/images/news/search [10][11][12] |
| **Tavily** | **1,000 credits/month** | $30/4K credits | $4.00 | Real-time AI search; advanced depth + answer extraction; no credit card needed [13][14][15] |
| **Firecrawl** | 500 credits | $19/month | $5.00 | Web scraping + search + crawling; best for data extraction [7][16] |
| **Perplexity** | $5 free API credits/month | $5/1K requests | $5.00 | Sonar API; raw results + advanced filtering; 50 QPS limit [17][18] |

***

## Top Recommendations by Use Case

| Your Need | Best Option | Why |
|-----------|-------------|-----|
| **Most searches free** | **Exa** (20K/month) | 20x more than competitors; no credit card [8] |
| **No API key** | **OpenWebSearch** | Multi-engine, unlimited, zero auth [1][3] |
| **Reliability + scale** | **Brave Search** (2K/month) | Industry standard; 30B page index [10][12] |
| **AI research** | **Tavily** (1K/month) | Optimized for AI agents; answer extraction [13][15] |
| **Privacy focus** | **DuckDuckGo** | No tracking; no auth required [4] |

***

## Quick Setup Commands

```json
// OpenWebSearch (no auth)
{
  "mcp": {
    "open-websearch": {
      "command": "docker",
      "args": ["run", "-d", "-p", "3000:3000", "-e", "ENABLE_CORS=true", "ghcr.io/aas-ee/open-web-search:latest"]
    }
  }
}
```


```json
// Exa (20K free/month)
{
  "mcp": {
    "exa": {
      "command": "npx",
      "args": ["-y", "exa-mcp"],
      "environment": { "EXA_API_KEY": "YOUR_KEY" }
    }
  }
}
```


```json
// Brave Search (2K free/month)
{
  "mcp": {
    "brave-search": {
      "command": "npx",
      "args": ["-y", "brave-search-mcp", "--http", "--ui"],
      "environment": { "BRAVE_API_KEY": "YOUR_KEY" }
    }
  }
}
```


***

## Confidence Assessment

| Option | Working Status | Evidence |
|--------|---------------|----------|
| Exa | ✅ Confirmed (20K/month) | Official pricing page [8] |
| OpenWebSearch | ✅ Confirmed (unlimited) | Multiple sources [1][3] |
| Brave Search | ✅ Confirmed (2K/month) | Official + Apify docs [10][12] |
| Tavily | ✅ Confirmed (1K/month) | Official pricing [13][14] |

***

**My recommendations:**
1. **Exa** if you want maximum free searches (20K/month)
2. **OpenWebSearch** if you want zero auth + unlimited
3. **Brave Search** if you want reliability with 2K/month free

Would you like help setting up one of these?
