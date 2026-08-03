---
title: "Social media data extraction landscape: tool selection per platform (2026)"
created: 2026-08-02
source: session-2026-08-02-www
tags: [social-media, scraping, browser-automation, cdp, research, practitioner-signal, architecture]
summary: >
  The 2026 social media scraping landscape splits into API-first tools
  (twscrape for X.com, Reddit MCP, yt-dlp for video) and browser-automation
  fallbacks (CDP/Playwright for sites without APIs). The architectural
  decision: use the highest-level tool that works per platform, falling
  back to CDP browser automation only when no API or GraphQL endpoint
  exists. twscrape is the highest-ROI addition for X.com; existing tools
  (Reddit MCP, yt-dlp, HN Algolia, firecrawl) already cover the other
  major platforms.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
---

# Social media data extraction landscape

## Decision context

**Why this research was needed:** the `/www` Phase 2b practitioner signal
pass needs social media data from multiple platforms (X.com, Reddit,
YouTube, Rumble, others). Reddit was just fixed (OAuth MCP), but X.com
has no usable free API ($5K/month paid tier). The operator asked: what
repos and tools exist to close this gap, and would browser automation
(CDP/Puppeteer/Playwright) work across platforms?

**What alternatives were explored:** direct API access (dead for X.com),
managed scraping services (Apify, Brightdata — paid, external dependency),
browser automation frameworks (chrome-devtools-mcp, Playwright MCP,
Puppeteer MCP), and dedicated scraping libraries (twscrape, snscrape,
Scweet, cdp-browser, browser-use, pupplet).

## Key Findings

### The three-layer tool stack (API → GraphQL → Browser)

The 2026 landscape has three layers, each higher-friction than the last:

| Layer | When to use | Tools | Friction |
|---|---|---|---|
| **1. Official API** | Platform offers usable free API | Reddit MCP (60 QPM), YouTube yt-dlp | Lowest |
| **2. GraphQL/unofficial endpoints** | Platform has no API but endpoints are reverse-engineerable | twscrape (X.com), gallery-dl | Low-medium (account pool management) |
| **3. Browser automation (CDP)** | Platform blocks all non-browser access | chrome-devtools-mcp, Playwright MCP, cdp-browser | Highest (DOM fragility, anti-bot) |

### Per-platform tool selection

| Platform | Best tool | Why | Status |
|---|---|---|---|
| **Reddit** | reddit MCP (authenticated) | Full API, 60 QPM, scores + comments + threads | ✅ Working (fixed 2026-08-02) |
| **X.com** | **twscrape** | Async Python CLI, hits GraphQL endpoints, account pool rotation, returns structured data | **Recommended addition** |
| **YouTube** | yt-dlp + youtube-transcript-api | Metadata + transcripts for 1000+ sites | ✅ Already installed |
| **Rumble** | yt-dlp (supported) + firecrawl | yt-dlp handles video metadata; firecrawl for page content | ✅ Already available |
| **HN** | HN Algolia API (free, no key) | Stories + comments, scored | ✅ Already in /www Phase 2b |
| **LinkedIn** | firecrawl (risky) or skip | Aggressive anti-scraping, account suspension risk | ⚠️ Low priority |
| **Telegram** | telethon (Python) or web preview | Public channel posts via web.telegram.org | Medium effort |
| **Unknown sites** | chrome-devtools-mcp | CDP to real Chrome, navigate + extract from any rendered page | ✅ Already available via /model-web |

### twscrape: the highest-ROI addition

[vladkens/twscrape](https://github.com/vladkens/twscrape) is an async Python
library and CLI for X/Twitter scraping via GraphQL endpoints. Key features:
- **Account pool with rotation:** uses multiple X.com accounts, rotates on
  rate-limit, stores sessions in SQLite
- **CLI pattern:** `twscrape search "few-shot prompting" --limit 20` →
  structured JSON (text, likes, retweets, replies, date, author)
- **Same pattern as ddgs_search.py:** the /www Phase 2b can call it via
  `run_terminal_command` exactly like DDG
- **No browser needed:** hits GraphQL directly, not DOM scraping

**Note:** the existing `web-research-state-2026.md` concept called twscrape
"low maintenance." This is outdated — the repo is active in 2026 with the
GraphQL endpoint approach being the community-standard replacement for the
dead snscrape/twint libraries.

### Browser automation: when GraphQL doesn't work

For platforms where no API or GraphQL endpoint exists, browser automation
is the universal fallback. The 2026 comparison (mcp.directory,
verified 2026-05-08):

| MCP Server | Maintainer | Tools | Best for | Page perception |
|---|---|---|---|---|
| chrome-devtools-mcp | Google | 26 | Profiling, debugging, real-Chrome CDP | a11y snapshot + screenshots + traces |
| Playwright MCP | Microsoft | 22 | Cross-browser, deterministic actions, anti-reflow | a11y snapshot (text-based, token-efficient) |
| Puppeteer MCP | Anthropic | 7 | Minimal surface, screenshot-driven | Screenshots + JS evaluate |

**Critical insight:** all three use CDP under the hood. They are NOT
alternatives to CDP — they are abstraction layers on top of it. The choice
is about the abstraction level, not the protocol.

**For social media specifically:** Playwright MCP's accessibility-snapshot
model is structurally better than chrome-devtools-mcp's approach because
social media sites reflow constantly (infinite scroll, lazy-load) and
Playwright's stable element refs survive layout changes that break
snapshot-based extraction.

**However:** the mcp.directory article warns against stacking all three
("55 browser-related tool descriptions in every prompt — the model gets
confused"). The recommendation is one per workspace, or two if genuinely
needed for different use cases.

### Anti-detection: cdp-browser for protected platforms

[dao-ai/cdp-browser](https://github.com/dao-ai/cdp-browser) is purpose-built
for anti-bot bypass on social platforms: pure CDP over WebSocket (zero
Puppeteer/Playwright/Selenium dependency), anti-detection injection,
humanized mouse trajectories (Bézier curves), simulated typing, random
viewport jitter. Documented working on Douyin, Xiaohongshu, Kuaishou.

**Relevance:** if standard CDP via chrome-devtools-mcp gets detected and
blocked on a target platform, cdp-browser's anti-detection patterns are
the reference implementation. Not needed for X.com (twscrape handles that)
but relevant for heavily-protected platforms.

### What we already have vs what's missing

```
Social data needed
  ├─ X.com?        → ❌ MISSING → twscrape (install)
  ├─ Reddit?       → ✅ reddit MCP (authenticated, 60 QPM)
  ├─ YouTube?      → ✅ yt-dlp + transcript API
  ├─ HN?           → ✅ HN Algolia API
  ├─ Rumble?       → ✅ yt-dlp (video) + firecrawl (page)
  ├─ Other sites?  → ✅ chrome-devtools-mcp (CDP, real Chrome)
  └─ Anti-bot?     → ⚠️ cdp-browser patterns (if standard CDP blocked)
```

Only one gap: X.com. Everything else is covered by existing tools.

## What this means for our workspace

1. **Install twscrape** — it's the single highest-ROI addition. Same CLI
   pattern as ddgs_search.py, returns structured JSON, handles X.com rate
   limits via account pooling. A single `pip install twscrape` + account
   setup unlocks the last major platform gap.

2. **Wire twscrape into /www Phase 2b** — add alongside Reddit MCP and
   HN Algolia as a third practitioner-signal source. The call pattern:
   `twscrape search "<topic> experience" --limit 10` → JSON.

3. **Do NOT install Playwright MCP yet.** chrome-devtools-mcp already
   covers browser automation via /model-web. Playwright MCP would add 22
   tool descriptions for a use case (social scraping on unknown platforms)
   that firecrawl and chrome-devtools-mcp already handle. Add it only if
   anti-reflow resilience becomes a documented friction point.

4. **Update web-research-state-2026.md** — the existing concept calls
   twscrape "low maintenance." This is outdated. twscrape is the
   community-standard X.com scraper in 2026.

## Evidence

All findings externally sourced from GitHub repos, mcp.directory comparison
(verified 2026-05-08), DDG search results, and Reddit practitioner data.
No local code inspection performed. The tool-stack recommendation is
[INFERENCE] derived from applying the landscape analysis to this workspace's
existing tool inventory.

## Falsifier

This concept is wrong if: (a) twscrape's GraphQL endpoints get blocked by
X.com (making the CLI approach non-viable), (b) a free X.com API tier
returns (making scraping unnecessary), or (c) the browser-automation MCP
servers add native social-media-aware tools that make the separate
scraping libraries redundant.

## Sources

- [vladkens/twscrape](https://github.com/vladkens/twscrape) — X.com GraphQL scraper
- [mcp.directory: Chrome DevTools vs Playwright vs Puppeteer MCP](https://mcp.directory/blog/chrome-devtools-mcp-vs-playwright-mcp-2026) (2026-05-08)
- [dao-ai/cdp-browser](https://github.com/dao-ai/cdp-browser) — anti-detection CDP
- [EngineeredReiwa/pupplet](https://github.com/EngineeredReiwa/pupplet) — X.com DOM automation via CDP
- [JustAnotherArchivist/snscrape](https://github.com/JustAnotherArchivist/snscrape) — legacy, maintenance mode
- [scrapfly.io: Best social media scraping tools 2026](https://scrapfly.io/blog/posts/best-social-media-scraping-tools)
- [dev.to: Twitter/X scraping frameworks 2026](https://dev.to/ashish_soni08/comprehensive-guide-to-twitterx-scraping-frameworks-and-tools-in-2026-37p2)
- [browser-use/browser-use](https://github.com/browser-use/browser-use) — AI browser agent

## Related

- [[web-research-state-2026]] — existing social media state (needs twscrape update)
- [[social-media-as-structured-research-data-for-ai-agents]] — the original research
- [[cdp-network-interception-and-sse-capture-for-llm-chat]] — CDP SSE capture technique
- [[concurrent-cdp-auth-contention]] — multi-terminal CDP invariant

## Auto-related

- [[skill-catalog]]
- [[router-proxy-tool-calling-normalization-patterns]]
- [[model-tool-calling-capability-matrix]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[youtube-transcript-extraction-techniques]]

