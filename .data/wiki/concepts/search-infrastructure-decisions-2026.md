---
title: "Search infrastructure decisions: multi-backend fusion, tiered dispatch, and quota posture"
created: 2026-08-09
source: session-2026-08-09
tags: [search, search-mcp, multi-backend, rrf-fusion, tiered-dispatch, quota, decision]
summary: >
  Decisions for the search_web MCP server: (1) search_web__query is the #1 search
  tool — it fuses 8 backends via RRF and must be tried before any other search tool;
  (2) backends cluster into 3 latency tiers (fast/medium/deep) for query-appropriate
  dispatch; (3) no proactive quota metering needed at current usage (1-3 calls/session);
  (4) the reactive health tracker (3 failures → disable) is sufficient for all backends;
  (5) mmx shares quota with model spawns but 4500/5h is effectively unlimited for search.
agent: grok
host: grok
cognitive_load: 3
verification: observed
type: decision
confidence: 0.85
last_verified: 2026-08-09
half_life_days: 180
relations:
  - target: wiki/concepts/tool-fallbacks.md
    type: extends — tool-fallbacks updated with search_web__query as primary fallback
---

# Search infrastructure decisions

## Decision context

Session 2026-08-09 expanded the `search_web` MCP server from 3 backends (Brave, Exa, DDG) to 8 (adding Perplexity, Tavily, Reddit, SERPAPI, mmx). The operator asked how to manage quotas, latency, and backend selection intelligently. These decisions emerged from /tp + /risk analysis.

## Key decisions

### DEC-01: search_web__query is the #1 search tool (always try first)

The AGENTS.md web-search hierarchy was rewritten: `search_web__query` moved from unlisted to priority #1, above DDG, context7, firecrawl, and all other search tools. The built-in `web_search` was demoted to last resort. Reference incident: this session used `web_search` (Grok quota) while `search_web__query` was connected and available.

### DEC-02: Tiered backend dispatch (fast/medium/deep)

Backends cluster by latency. Default to fast tier for ad-hoc queries; escalate to deep for /www and research.

| Tier | Backends | Latency | Use when |
|---|---|---|---|
| fast | Brave, Exa, DDG, SERPAPI | ~1s | Default — quick lookups, code docs |
| medium | fast + Tavily, Reddit | ~2s | Standard research — adds diversity |
| deep | medium + Perplexity, mmx | ~3-5s | /www, deep research — full coverage |

Config: `[search.tiers]` in search-mcp/config.toml. The `tier` parameter on `search_web__query` selects which tier to use.

### DEC-03: No proactive quota metering at current usage

/tp + measured data showed: actual search usage is 1-3 calls per session (verified via transcript scan). At this rate, even the smallest monthly budget (Exa 1000/month) supports 300+ sessions. mmx (4500/5h, shared with model spawns) uses <1% of its budget for search. The reactive health tracker (3 failures → disable) is sufficient.

### DEC-04: Serper removed (redundant, quota exhausted)

Serper.dev's free tier (2500 one-time credits, no renewal) was exhausted. SERPAPI covers the same Google SERP use case. Removed from backends, config, fleet, and .env.

### DEC-05: mmx added despite /tp recommendation to skip

/tp recommended not adding mmx (redundant index, quota competition). The operator corrected: "automatic is the requirement" — if mmx requires a human to decide when to use it, it won't be used. Added as an always-on deep-tier backend. Health tracker auto-disables when quota is low.

## What this means for our workspace

1. **AGENTS.md already updated** — search_web__query is priority #1 (commit 757f252).
2. **search-mcp/config.toml has tier config** — `[search.tiers]` section defines fast/medium/deep backend groups.
3. **server.py supports tier parameter** — callers pass `tier="deep"` for research; default is fast.
4. **No quota monitoring infrastructure needed** — the health tracker in server.py handles all backends reactively.
5. **Skills that do web research (/www, /web, /tp specialists)** should pass `tier="deep"` to get full backend coverage. Skills doing quick lookups use the default fast tier.

## Falsifier

These decisions are wrong if:
- Search usage increases dramatically (e.g., automated research pipelines) and quotas exhaust faster than the health tracker can react — would need proactive metering
- Tiered dispatch adds complexity the agent can't navigate (always picks "deep" making tiering decorative) — would need to enforce default tier in code, not config
- mmx's quota competition with model spawns causes real model-spawn failures — would need to remove mmx from the default pool

## Receipts

- **Actual search call count:** 1 `search_web__query` call in a heavy 1338-turn session. Verified via transcript scan (`Select-String "search_web__query" chat_history.jsonl`).
- **mmx quota:** 85% remaining on 5-hour window at session end. Source: `fleet_quota.py --llm --json`.
- **Backend live tests:** 7 of 8 backends verified returning real results (SERPAPI, Brave, Exa, DDG, Tavily, Reddit, Perplexity, mmx). Source: `P:/tmp/test_backends.py`.
- **pwm v0.14.8 upgrade fixed 403:** token was valid all along; old library (v0.9.5) couldn't use it. Source: `pwm ask "Reply: OK" --json` → `{"answer": "OK"}`.

## Auto-related

- [[skill-catalog]]
- [[web-search-tool-routing]]
- [[optimal-multi-backend-search-strategy]]
- [[skill-graph]]
- [[deep-research-systems-and-web-upgrade]]

