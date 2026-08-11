---
title: Web Search and Page-Fetching Tool Selection (Grok Build)
created: 2026-08-10
host: grok
tags: [tool-selection, web-search, grok-build, quota-management]
---

# Web Search and Page-Fetching Tool Selection (Grok Build)

When the task requires real-time or external web information, prefer in this order:

## Web search preference order

1. **`search_web__query`** (MCP) — **DEFAULT FIRST CHOICE.** Searches
   Brave + Exa + DuckDuckGo in parallel, RRF-fuses the results, and returns
   ranked JSON with backend-agreement signals. **ALWAYS use this first.**
   Source: `~/.grok/search-mcp/server.py`. Usage:
   `use_tool("search_web__query", {"search_query": "your query", "num_results": 5})`.
2. **`context7` MCP** — for current library/framework/API documentation.
   Free, separate quota from Grok.
3. **`firecrawl__firecrawl_search`** (MCP) — for content-rich queries where
   full-page extraction adds value. Separate quota (freemium, 1000 credits/mo).
4. **`mmx search query "<q>"`** (CLI via `/mmx` skill) — MiniMax's search
   index, distinct from DDG/Brave/Exa. Separate MiniMax API quota.
5. **`perplexity` / `tavily` / `reddit` MCP servers** — specialist backends.
6. **~~`web-search-prime`~~** — **DISABLED**. Uses GLM coding plan quota.
7. **`web_search`** (built-in) — **last resort only.** Consumes Grok quota
   (runs `grok-4.20-multi-agent` model inference). Rate-limited (~2 RPS
   fleet-wide, 429-prone under parallel load).

**Decision rule:** before using ANY search tool, ask: "did I try
`search_web__query` first?" If no, use it.

**Quota hierarchy:** `search_web__query` (free) → `context7` (free) →
separate-pool tools (firecrawl, mmx, perplexity, tavily, reddit) →
Grok-quota tools (built-in web_search).

## Page-fetching preference order

1. **ChatPeek** — for ChatGPT shared links (`chatgpt.com/s/`). No browser,
   no quota. `python P:/packages/ChatPeek/ChatPeek.py <share-url>`.
2. **`web_fetch`** (built-in) — for static HTML, JSON, RSS. Fails on JS SPAs.
3. **`firecrawl_scrape`** (MCP) — for JS-rendered pages. Freemium.

## Tool-failure awareness

Before starting any task that depends on external tools, consult
`[[tool-fallbacks]]` for known failures and plan around working alternatives.
When you encounter a new tool failure mid-task, add it to `[[tool-fallbacks]]`.

## References

- `minimax-search` MCP removed 2026-07-28 (Claude Code compat artifact).
  Capabilities covered by `mmx search query` and `mmx vision describe`.
- Reference incident (2026-08-09): agent ran `/www` using built-in `web_search`
  while `search_web__query` was available the entire time.
