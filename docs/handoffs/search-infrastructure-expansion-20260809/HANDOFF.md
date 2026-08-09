---
thread_id: search-infrastructure-expansion-20260809
parent_handoff_path: none
current_session_id: 019fe4c1-43c3-7432-b211-926e806dd7a6
produced_at: 2026-08-09T00:00:00Z
status: OPEN
handoff_type: implementation_plan
---

# HANDOFF: Search infrastructure expansion — backends, fleet registration, file search

## Status
OPEN — design + implementation needed

## Objective
Expand the `search_web` MCP server to include all available search backends (Perplexity, Tavily, Reddit, mmx), register it in the search-fleet registry, and wire file-server search options (Serena, claude-mem) so the agent has ONE fused search entry point for both web and local knowledge.

## Context

**Trigger (session 2026-08-09):** during `/www` research on agent polling/timeout patterns, the agent defaulted to the built-in `web_search` (last-resort provider, consumes Grok quota) while `search_web__query` — an MCP server that fuses Brave+Exa+DDG in parallel — was connected and available the entire time. Six MCP search servers were connected; zero were used. The AGENTS.md rule was on the books; it did not fire.

**Root cause:** the AGENTS.md web-search priority list ranked DDG (direct Python script) as #1, not `search_web__query` (the MCP aggregator). The agent reached for the first thing that looked like "search" and got the built-in. Promoting `search_web__query` to #1 (done this session in AGENTS.md) is the behavioral fix; expanding its backend coverage is the structural fix.

## Current state of search_web MCP server

**Location:** `~/.grok/search-mcp/server.py`
**Config:** `~/.grok/search-mcp/config.toml`
**Backends:** `~/.grok/search-mcp/backends.py` — currently 3 backends:
- `brave` (Brave Search API, key from `BRAVE_API_KEY`)
- `exa` (Exa API, key from `EXA_API_KEY`)
- `ddg` (DuckDuckGo, no key needed)

**Architecture:** each query calls all enabled+healthy backends in parallel via `httpx.AsyncClient`, normalizes to `SearchResult` dataclass, RRF-fuses into one ranked list. Health tracking (failure threshold = 3 consecutive failures → skip). Config-driven (add a `[backends.<name>]` block + write an adapter).

**NOT registered in search-fleet.toml** — the fleet registry lists individual backends (sr-serper, sr-exa, sr-brave, sr-ddgs) but not the aggregating `search_web` MCP server. This means `/search-fleet` skill doesn't know about it.

## Track A: Add web search backends to search_web

### A1. Perplexity backend
Perplexity MCP (pplx_sonar / pplx_smart_query) provides AI-synthesized answers with citations — different from raw SERP. Add as a `search_web` backend:
- Write `async def search_perplexity(client, query, num, api_key)` in backends.py
- Perplexity API: `POST https://api.perplexity.ai/chat/completions` with model `sonar`, returns answer + `citations` array
- Register in `BACKEND_REGISTRY`; add `[backends.perplexity]` to config.toml
- **Note:** Perplexity has quota limits (Pro searches weekly). Gate behind config `enabled` flag so it's opt-in per query, not always-on.

### A2. Tavily backend
Tavily MCP provides academic/structured research with source focus filters. Add as a `search_web` backend:
- Write `async def search_tavily(client, query, num, api_key)` in backends.py
- Tavily API: `POST https://api.tavily.com/search` with `api_key`, returns `results` array
- Register in `BACKEND_REGISTRY`; add `[backends.tavily]` to config.toml
- Key from `TAVILY_API_KEY`

### A3. Reddit backend
Reddit MCP provides practitioner experience reports — critical for "what actually works in production" perspectives that vendor docs and academic sources miss. Add as a `search_web` backend:
- Write `async def search_reddit(client, query, num, api_key)` in backends.py
- Reddit API: `GET https://oauth.reddit.com/search` with OAuth bearer token, OR use PRAW
- Scope to relevant subreddits: `r/LocalLLaMA`, `r/LangChain`, `r/AI_Agents`, `r/machinelearning`
- Register in `BACKEND_REGISTRY`; add `[backends.reddit]` to config.toml
- **Note:** Reddit OAuth credentials are wired (resolved 2026-08-02 per tool-fallbacks). Use the existing OAuth flow.

### A4. mmx (MiniMax) backend
mmx CLI provides a distinct search index (MiniMax's own). Currently called as a CLI (`mmx search query "<q>"`). Could be added as an HTTP backend to search_web:
- MiniMax API endpoint for search (verify via `mmx search query --help` or API docs)
- OR: keep as CLI and fuse via `search_web__fuse` (the existing pattern — call mmx CLI separately, then fuse its results with search_web's results)
- **Recommendation:** keep mmx as CLI + fuse, rather than reimplementing its API in backends.py. The fuse tool exists for exactly this. Document the pattern in AGENTS.md.

### A5. Default backends config update
After adding A1-A3, update `config.toml`:
```toml
default_backends = ["brave", "exa", "ddg", "perplexity", "tavily", "reddit"]
```
This makes `search_web__query` call 6 backends in parallel by default, RRF-fusing all of them.

## Track B: Register search_web in search-fleet.toml

### B1. Add search_web as a fleet tool
The search-fleet registry (`~/.grok/search-fleet.toml`) doesn't know about `search_web` MCP. Add:
```toml
[tools.search-web-mcp]
enabled = true
layer = "mcp"
capabilities = ["web_search", "semantic_search"]
cost = "free"
quota = "unlimited"
strengths = ["multi_backend_fusion", "rrf", "backend_agreement_signal", "single_call_covers_brave_exa_ddg"]
drawbacks = ["depends_on_individual_backend_keys"]
mitigations = ["health_tracking_skips_failed_backends"]
invocation = { type = "mcp", server = "search_web", tool = "query", query_param = "search_query" }
priority = 1
```
This makes `/search-fleet` skill route to it as the primary web search tool.

## Track C: File-server / local knowledge search

The operator mentioned Serena, claude-mem (Clogmem), and other file-server search options. These are LOCAL search (codebase, memory, knowledge base), not web search. They belong in a different capability class.

### C1. Serena (code search)
**Status:** Serena is an LSP-based code intelligence server. If installed as an MCP server, it provides symbol search, references, definitions — deeper than grep/ripgrep for code navigation.
**Action:** check if Serena MCP is configured. If not, evaluate whether to add it. Its capability is `code_search` / `symbol_navigation`, not `web_search`. It would NOT go in `search_web` (which is web-only) but could be a separate fleet entry or a `search_local` equivalent.
**Check:** `~/.grok/config.toml` for `[mcp_servers.serena]`; if absent, this is an install+config task.

### C2. claude-mem (Clogmem) memory search
**Status:** claude-mem is a persistent cross-session memory database (the `claude-mem` / `cmem` plugin). It has `mem-search` for searching past sessions. This is `memory_search` capability.
**Action:** verify claude-mem is installed and `mem-search` works. If it does, register in search-fleet as a `memory_search` tool. This overlaps with `mcp-search` MCP (which does corpus/knowledge search) — clarify the boundary.

### C3. mcp-search (knowledge corpus search)
**Status:** already connected. Provides `smart_search` (tree-sitter AST code search), `search` (memory/observation search), `query_corpus` (primed knowledge base Q&A). This is the existing local-search MCP.
**Action:** register in search-fleet.toml if not already. Clarify: `mcp-search` = codebase + memory; `search_web` = web. They're complementary, not overlapping.

### C4. search_wiki MCP
**Status:** already connected (1 tool). Searches the local wiki vault. This is `local_knowledge_search` capability.
**Action:** register in search-fleet.toml.

### C5. Unified local search?
**Open question:** should there be a `search_local__query` equivalent of `search_web__query` that fuses Serena (code) + claude-mem (memory) + mcp-search (corpus) + search_wiki (wiki) into one ranked local-search result? This would mirror the web-search fusion pattern.
**Recommendation:** measure first. If the agent frequently needs to search multiple local sources, a fusion layer helps. If local search is usually single-source (just wiki, or just code), the individual tools suffice. Don't build the fusion layer speculatively.

## Acceptance criteria

- Track A: Perplexity, Tavily, Reddit backends added to `search_web` MCP; `search_web__query` calls 6 backends by default
- Track B: `search_web` registered in search-fleet.toml with priority 1; `/search-fleet` routes to it
- Track C: Serena + claude-mem availability verified; registered in search-fleet if present; local-search fusion evaluated (measure first)
- AGENTS.md priority updated (DONE this session)

## Key files
- `~/.grok/search-mcp/server.py` — the MCP server
- `~/.grok/search-mcp/backends.py` — backend adapters (add A1-A3 here)
- `~/.grok/search-mcp/config.toml` — backend config (add `[backends.<name>]` blocks)
- `~/.grok/search-fleet.toml` — fleet registry (add B1)
- `~/.grok/AGENTS.md` — priority list (DONE)

## Suggested next invocation
```
/go Read P:/docs/handoffs/search-infrastructure-expansion-20260809/HANDOFF.md and implement Track A + Track B. Track C (local search fusion) is measure-first — verify Serena/claude-mem availability but don't build fusion speculatively.
```

## References
- Incident: session 2026-08-09, `/www` research used built-in web_search instead of search_web__query
- AGENTS.md § Web-search tool selection (updated this session, commit pending)
- `~/.grok/search-mcp/server.py` — current 3-backend implementation
- [[tool-fallbacks]] — updated with search_web__query as primary fallback
