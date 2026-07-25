---
title: "Web search tool routing: maximize the multi-backend fleet"
created: 2026-07-21
source: session-2026-07-21
tags: [web-search, routing, firecrawl, minimax-search, web-search-prime, duckduckgo, exa, tavily, brave, serper, serpapi, search-research, pwm, agy, tool-use, fleet]
summary: >
  This host has 20+ search surfaces across 4 layers: (1) active MCPs (minimax-search,
  firecrawl, web-search-prime), (2) built-in web_search fallback, (3) the local
  search-research CLI with 11+ providers (tavily, serper, exa, perplexity, glm, zai,
  ddgs, brave, github, google, kagi, mojeek, bing, you), and (4) cross-model CLIs
  (agy, mmx, codex, pwm). Perplexity MCP is DISABLED (expensive). Tavily key is EMPTY
  (MCP not wired). Strategy: intent-routed + parallelize + fallback-aware. Do NOT use
  agy for primary search — it is a second-opinion/research harness, not a search backend.
agent: grok
host: grok
cognitive_load: 3
verification: multi-source-verified
relations:
  - target: wiki/concepts/web-research-state-2026
    type: refines
  - target: wiki/concepts/model-picker-as-failover-not-router
    type: related
  - target: wiki/concepts/gemini-api-vs-agy-cli
    type: related
  - target: wiki/concepts/llm-council-and-model-fusion
    type: related
---

# Web search tool routing: maximize the multi-backend fleet

## Why this page exists

The operator observed: "we are not using our web search tools optimally, we have many
search tools that we are not using regularly and several are unlimited usage." The
first version of this page missed several backends (DuckDuckGo, Exa, Tavily, Brave,
search-research CLI, pwm) and misclassified agy as a search fallback. This is the
corrected, comprehensive inventory + routing strategy.

## Full inventory (verified 2026-07-21)

### Layer 1 — Active MCP servers (Grok session-start)

| MCP | Tools | Quota | Strength |
|-----|-------|-------|----------|
| **`minimax-search`** | 2 (`web_search`, `understand_image`) | **Unlimited** (operator-reported) | Default web search; distinct index; image understanding (JPEG/PNG/WebP) |
| **`firecrawl`** | 26 (search/scrape/crawl/map/extract/agent/research/feedback) | 1,000 credits/mo free; refundable via feedback | Full pipeline; clean markdown (94% token reduction); autonomous agent |
| **`web-search-prime`** | 1 (`web_search_prime`) | **Unlimited** (operator-reported) | `search_recency_filter`, `search_domain_filter`, `content_size: high` (2500 words) |

### Layer 2 — Built-in (Grok native)

| Tool | Quota | Role |
|------|-------|------|
| **`web_search`** | ~2 RPS fleet-wide; 429 under parallel load | **Last resort only — consumes Grok quota.** `web_search` runs `grok-4.20-multi-agent` model inference (confirmed 2026-07-24, `~/.grok/docs/user-guide/05-configuration.md:31`), NOT a free API call. MCP search tools (minimax-search, web-search-prime) use independent quota pools. Policy: use `web_search` only after all MCP search tools have failed. |

### Layer 3 — `search-research` CLI (local, 11+ providers)

**Binary:** `C:\Users\brsth\AppData\Roaming\Python\Python314\Scripts\search-research.exe`  
**Source:** `P:/packages/.claude-marketplace/plugins/search-research`  
**Backends dir:** `search_research/backends/` (13 Python modules)

| Provider | Mode flag | Env key | Status |
|----------|-----------|---------|--------|
| **Tavily** | `--mode tavily` | `TAVILY_API_KEY` | **EMPTY** — not usable until key set |
| **Serper** (Google-powered) | `--mode serper` | `SERPER_API_KEY` | SET — works |
| **Exa** | `--mode exa` | `EXA_API_KEY` | SET — works |
| **Perplexity** | `--mode perplexity` | (login) | Disabled as MCP; CLI mode may still work via `pwm` |
| **GLM (Zhipu)** | `--mode glm` | `ZHIPU_API_KEY` | SET — works |
| **ZAI** | `--mode zai` | (ZAI creds) | TBD |
| **Brave** | `brave.py` backend | `BRAVE_API_KEY` | SET — works via backend module |
| **DuckDuckGo (ddgs)** | `ddgs_backend.py` | None needed | **Free, no key** — works |
| **Google** | `google.py` | (SCRAPER) | TBD — likely scrapes |
| **Kagi** | `kagi.py` | (Kagi creds) | Not configured |
| **Mojeek** | `mojeek.py` | None | Free, no key — independent index |
| **Bing** | `bing.py` | None / scraper | TBD |
| **You.com** | `you.py` | (You creds) | TBD |
| **GitHub** | `--mode github` | (gh / token) | Works |
| **NotebookLM** | `--mode notebooklm` | (MCP) | TBD |
| **Claude built-in** | `--mode claude` | — | Bridges to Claude Code's web_search |

**Modes:** `auto`, `web` (multi: tavily + serper), `quick`, or any provider above.  
**Features:** HyDE enhancement (`--hyde`), multi-HyDE perspectives, saturation detection, JSON/markdown output, `--save`.

### Layer 4 — Cross-model CLIs (NOT primary search)

| CLI | Path | Use for search? |
|-----|------|-----------------|
| **`agy`** | `~/.AppData/Local/agy/bin/agy.exe` | **NO** — second-opinion/research harness only (see `gemini-api-vs-agy-cli`) |
| **`mmx`** | `~/.AppData/Roaming/npm/mmx.ps1` | Only as fallback when built-in `web_search` 429s: `mmx search query "<q>"` |
| **`codex`** | `~/.AppData/Roaming/npm/codex.ps1` | NO — code second-opinion, not search |
| **`pwm`** | `~/.local/bin/pwm.exe` | Perplexity CLI — works even though MCP disabled. Expensive; use sparingly. |

### Disabled / unwired backends

| Backend | State | Why |
|---------|-------|-----|
| **`perplexity` MCP** | `disabled_mcp_servers = ["perplexity"]` in config.toml | Operator disabled: **expensive** |
| **`exa-mcp-server@3.1.9`** | npm-installed globally, not in active MCP list | Install exists; wiring requires MCP config entry + restart |
| **`tavily-mcp@0.2.18`** | npm-installed globally, not active | `TAVILY_API_KEY` is **EMPTY** — can't auth |

### Env keys in `P:/.env` (search-related)

| Key | Status | Wired to |
|-----|--------|----------|
| `BRAVE_API_KEY` | SET | search-research `brave.py` (not MCP) |
| `EXA_API_KEY` | SET | search-research `exa.py`; exa-py SDK |
| `SERPAPI_API_KEY` | SET | serpapi Python package |
| `SERPER_API_KEY` | SET | search-research `serper.py` |
| `TAVILY_API_KEY` | **EMPTY** | Nothing until set |
| `FIRECRAWL_API_KEY` | EMPTY | Firecrawl uses OAuth MCP instead |
| `MINIMAX_API_KEY` | SET | minimax-search MCP, mmx CLI |
| `ZHIPU_API_KEY` | SET | search-research `glm` mode |
| `GEMINI_API_KEY` (×3) | SET | Gemini API, agy (different pool) |

### DuckDuckGo specifically

- **No API key required.** Free, anonymous.
- `search-research` `ddgs_backend.py` — Python `duckduckgo-search` library
- DDG Lite HTML endpoint: `https://lite.duckduckgo.com/lite/?q=<query>` (verified working 2026-07-21, returns 22KB HTML)
- DDG JSON endpoint (`duckduckgo.ggc-api.com`): **broken from this host** (DNS)
- Use case: quick anonymous lookups, rate-limit-free fallback when other backends are exhausted

## Intent-based routing (primary decision rule)

Match the query shape to the backend's strength. Order = preference within each row.

| Query shape | Primary | Escalate / alternate |
|-------------|---------|----------------------|
| **Default / catch-all** | `minimax-search__web_search` | `firecrawl_search`; `search-research --mode auto` |
| **Time-sensitive** ("latest", 2026 dates) | `web-search-prime` (`search_recency_filter=oneWeek`) | `firecrawl_search` (`tbs=qdr:d`); `search-research` |
| **Domain-scoped** (site:reddit.com, docs) | `web-search-prime` (`search_domain_filter`) | `firecrawl_search` (`includeDomains`); direct scrape |
| **Technical "explain X"** | `firecrawl_scrape` top result, or `pwm ask` if Perplexity budget allows | `search-research --mode exa` (semantic); `agy -p` (Gemini lens, sparingly) |
| **Deep multi-source research** | `firecrawl__firecrawl_agent` (1-5 min autonomous) | Parallel `web-search-prime` + `minimax-search` + scrape top 5 |
| **Academic / semantic** | `search-research --mode exa --hyde` | `firecrawl_research_search_papers` |
| **Fact-check / single URL** | `firecrawl_scrape` (URL known) | `web-search-prime` (to find URL first) |
| **Social signal** (reddit/x/linkedin/youtube) | `web-search-prime` + domain filter | See [[web-research-state-2026]] for PRAW, yt-dlp, oEmbed |
| **GitHub repo/issue** | `gh search repos`, or `search-research --mode github` | `web-search-prime` (`site:github.com`); `firecrawl_research_search_github` |
| **Anonymous / no-key lookup** | `search-research` ddgs backend, or DDG lite via curl | `minimax-search` (still anonymous to user) |
| **Google-indexed results** | `search-research --mode serper` | `SERPAPI_API_KEY` via serpapi Python pkg |
| **Image understanding** | `minimax-search__understand_image` | `mmx vision describe`, or `agy` multimodal (sparing) |
| **Structured extraction** (pricing, tables) | `firecrawl_extract` + JSON schema | `firecrawl_scrape` + parse |
| **Synthesized answer with citations** | `pwm ask` (if budget) or `firecrawl_agent` | Parent LLM synthesizes from scraped sources |

## When to use agy for search — almost never

**Rule: do NOT use agy as a primary or fallback search tool.** It is a second-opinion / research harness with a heavy conductor contract (assignment adequacy, run record, outcome labels). Using it for "search X" wastes the contract overhead and the Gemini subscription quota.

**Exceptions (agy is acceptable for search-adjacent work):**

1. You specifically need **Gemini's reasoning lens** on a research question (not just search results)
2. You want a **cross-family second opinion** on a claim surfaced by other search backends
3. You are already running an agy review session and want it to verify a source mid-flow

In all other cases: use `minimax-search`, `web-search-prime`, `firecrawl`, `search-research`, `mmx search query`, or even DDG — all are faster, cheaper, and purpose-built for search.

`tool-fallbacks.md` currently lists `agy -p` under "research / deep search" fallback. That entry should be read narrowly: agy is a fallback for **deep research with agent harness**, not for search queries. For pure search fallback, use `mmx search query` or `search-research`.

## Parallelization strategy (the underused lever)

**Most queries are independent → run them in parallel.** Single biggest improvement available.

### When to parallelize

- **Multi-faceted research** (e.g., "Gemini API vs agy" + "search tool optimization" — fire both in one tool block)
- **Confirmation + disconfirmation** ("evidence for X" + "evidence against X")
- **Source diversity** (same query across 2-3 backends to compare indices)
- **Depth sweep** (quick scan + deep scrape in parallel once top URLs known)
- **Multi-provider verification** (`minimax-search` + `web-search-prime` + `search-research --mode serper` on same query)

### When NOT to parallelize

- **Sequential dependency** (query B depends on A's results)
- **Rate-limited backend under load** (built-in `web_search` at 2 RPS)
- **Token budget concern** (scraping 8 sources when 3 suffice)

### Pattern

```
# Independent queries → one tool block, multiple use_tool calls
use_tool minimax-search(query="topic A facet 1")
use_tool web-search-prime(search_query="topic A facet 2", search_recency_filter=oneMonth)
use_tool firecrawl_search(query="topic A facet 3", limit=5)
# Or via search-research CLI in parallel shells:
run_terminal_command("search-research 'facet 1' --mode serper --output json --save r1.json &")
run_terminal_command("search-research 'facet 2' --mode exa --hyde --output json --save r2.json &")
```

## Maximizing outcomes (do's and don'ts)

### Do

- **Default to `minimax-search`.** Its MCP description says "MUST use this tool whenever you need to search." Unlimited for this operator.
- **Parallelize independent queries.** Highest-ROI change. Halves research time.
- **Use `web-search-prime` for recency and domain scoping.** Only backend with those filters. Unlimited.
- **Use `firecrawl_scrape` for full page content.** 94% token reduction vs raw HTML. Always `onlyMainContent: true, formats: ["markdown"]`.
- **Use `search-research` CLI for provider diversity.** One binary, 11+ backends. `--mode auto` picks; `--mode exa --hyde` for semantic depth.
- **Use DDG (ddgs backend or lite endpoint) for anonymous, no-key lookups.** Free, rate-limit-friendly.
- **Submit `firecrawl_search_feedback` after every substantive search.** Refunds 1 credit (search costs 2).
- **Reflex to `mmx search query` on built-in `web_search` failure.** Before retrying the built-in.
- **Self-rate-limit within a backend.** >3 calls in a row → pause 2-3 seconds.
- **Deduplicate by URL across backends.** Same URL from minimax and firecrawl = one source.
- **Score sources (CREDIBLE-lite).** Authority, recency, evidence, bias. ≤6 = triangulation only.
- **Wire the unused MCPs if you want them.** `exa-mcp-server` is installed; add to MCP config + set restart. Same for `tavily-mcp` (also needs `TAVILY_API_KEY`).

### Don't

- **Don't default to built-in `web_search`.** 2 RPS fleet-wide, 429-prone. Last resort.
- **Don't use `agy` for search.** It is a second-opinion harness. Slow, expensive, wrong tool shape. (See `gemini-api-vs-agy-cli`.)
- **Don't use `pwm` (Perplexity CLI) casually.** Perplexity is disabled as MCP because it's expensive. CLI is the same billing. Reserve for genuine deep-research needs.
- **Don't run all searches through one backend.** Different indices return different results. Cross-backend parallelism catches what one misses.
- **Don't scrape every search result.** Score first, scrape top 3-5 per depth. Token budget matters.
- **Don't forget `search_recency_filter`.** For anything time-sensitive, `oneMonth`/`oneWeek` filters stale results.
- **Don't use `firecrawl_agent` for simple lookups.** 1-5 min + credits-heavy. Use `firecrawl_search` (seconds) for simple queries.
- **Don't call Tavily backend without checking `TAVILY_API_KEY`.** It's empty. The CLI will fail auth.
- **Don't conflate search with research.** Search finds URLs; research synthesizes. Use `/www` for the full pipeline.
- **Don't trust a single source for load-bearing claims.** Triangulate ≥2 independent sources for `[HIGH]` confidence.

## Wiring currently-unused MCPs (optional, if wanted)

### Exa MCP (installed, not active)

```toml
# Add to ~/.grok/config.toml or MCP config
[mcp_servers.exa]
command = "npx"
args = ["-y", "exa-mcp-server"]
env = { EXA_API_KEY = "${EXA_API_KEY}" }
```

Then restart Grok. `EXA_API_KEY` already in `.env`.

### Tavily MCP (installed, key missing)

```toml
[mcp_servers.tavily]
command = "npx"
args = ["-y", "tavily-mcp"]
env = { TAVILY_API_KEY = "${TAVILY_API_KEY}" }
```

**Requires:** set `TAVILY_API_KEY` in `P:/.env` first. Without it, MCP will fail auth.

### Re-enabling Perplexity MCP (if budget allows)

Remove `"perplexity"` from `disabled_mcp_servers` in `~/.grok/config.toml`. Operator disabled because expensive; do not re-enable without explicit cost approval.

## Authority sources

| Source | Score | Key finding |
|--------|-------|-------------|
| [Vellum: Best Web Search APIs & MCPs 2026](https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents) | 11 | Firecrawl 94% token reduction; provider comparison |
| [LessWrong/FutureSearch: LLM-Assisted Web Research](https://www.lesswrong.com/posts/uAEhvX6scvcZANWwg/) | 12 | Regular + search often beats deep research; scaffolding matters; failure modes |
| [Brave: Best Search API 2026](https://brave.com/learn/best-search-api-2026/) | 10 | Provider comparison; Tavily vs Perplexity positioning |
| [Firecrawl: Best Web Search APIs 2026](https://www.firecrawl.dev/blog/best-web-search-apis) | 10 | Token efficiency claims |
| [Perplexity: Advancing Search-Augmented LMs](https://research.perplexity.ai/articles/advancing-search-augmented-language-models) | 11 | Iterative retrieval beats single-shot on multi-hop |
| Host `~/.grok/tool-fallbacks.md` | 11 | Verified broken combinations + CLI fallback table |
| Host `~/.grok/skills/web/SKILL.md` | 11 | Routing logic (needs update: still references perplexity) |
| Host `P:/packages/.claude-marketplace/plugins/search-research/CLI_USAGE.md` | 11 | 11+ provider modes, HyDE options |
| Host `P:/packages/.claude-marketplace/plugins/search-research/README.md` | 11 | Unified interface, HyDE, graceful degradation |

## Conflicts / caveats

- **⚠️ Vendor benchmarks are vendor-funded.** Vellum ranks Firecrawl #2; Firecrawl ranks itself #1. Trust relative rankings within one eval.
- **⚠️ "Unlimited" is operator-reported** for minimax-search and web-search-prime. Provider terms can change. Log failures.
- **⚠️ FutureSearch finding** ("regular + search beats deep research") is from June 2025; deep research tools improved since. Re-test if load-bearing.
- **⚠️ search-research backends** are not all verified working 2026-07-21. Serper/Exa/GLM keys are SET; others TBD. Probe before relying.
- **⚠️ DDG JSON endpoint** broken from this host (DNS). Use `ddgs_backend.py` (Python lib) or lite HTML endpoint.

## Recommended daily-use defaults

For this operator's volume (research-heavy, multi-topic, depth-standard):

| Priority | Backend | When |
|----------|---------|------|
| 1 (default) | `minimax-search__web_search` | Unlimited; first choice |
| 2 (scoped) | `web-search-prime__web_search_prime` | Recency/domain filters |
| 3 (content) | `firecrawl__firecrawl_scrape` | Full page markdown |
| 4 (diversity) | `search-research --mode auto` or `--mode serper/exa` | Different index; HyDE |
| 5 (anonymous) | `search-research --mode ddgs` or DDG lite via curl | No key, rate-friendly |
| 6 (deep) | `firecrawl__firecrawl_agent` | Autonomous 1-5 min |
| 7 (synthesis) | `pwm ask` (budget permitting) or parent LLM synthesis | Citations out of the box |
| 8 (fallback) | `mmx search query` | When built-in 429s |
| **Never default** | built-in `web_search` | 2 RPS, 429-prone |
| **Almost never** | `agy -p` for search | Second-opinion harness, not search |

**Parallelization rule:** if researching a topic with ≥2 independent angles, fire all searches in one tool block.

## Skill updates needed

| Skill / doc | Update |
|-------------|--------|
| `~/.grok/skills/web/SKILL.md` | Remove perplexity from "MCPs already connected"; add `search-research` CLI; correct "don't sign up for Tavily/Exa" (keys already exist; exa-mcp installed) |
| `~/.grok/tool-fallbacks.md` | Clarify agy is **not** a search fallback; demote to "deep research with agent harness" only. Primary search fallback is `mmx search query` or `search-research`. |

## Relationship to existing concepts

- **Refines** [[web-research-state-2026]] — adds routing strategy + local CLI backends.
- **Related** [[model-picker-as-failover-not-router]] — search backends recommend by intent; failure goes to fallback.
- **Related** [[gemini-api-vs-agy-cli]] — establishes agy ≠ search tool.
- **Related** [[llm-council-and-model-fusion]] — search backends feed Fusion panels.

## Sources

- https://www.vellum.ai/blog/best-web-search-apis-and-mcps-for-ai-agents (2026-06-30)
- https://www.lesswrong.com/posts/uAEhvX6scvcZANWwg/a-guide-for-llm-assisted-web-research (2025-06-26)
- https://brave.com/learn/best-search-api-2026/ (2026-05-27)
- https://www.firecrawl.dev/blog/best-web-search-apis (2026-06-04)
- https://research.perplexity.ai/articles/advancing-search-augmented-language-models (2026-04-22)
- `~/.grok/tool-fallbacks.md` (host-verified)
- `~/.grok/skills/web/SKILL.md` (host routing logic)
- `~/.grok/AGENTS.md` § "Web-search tool selection (Grok Build only)"
- `P:/packages/.claude-marketplace/plugins/search-research/CLI_USAGE.md` (host)
- `P:/packages/.claude-marketplace/plugins/search-research/README.md` (host)
- Host inventory probes 2026-07-21: npm list, pip list, env keys, MCP config

## Staleness

Provider pricing, quotas, and MCP availability change quarterly. Re-check Vellum/Brave/Firecrawl comparisons if >6 months old. Verify search-research backends by probing each mode once per quarter. Update `tool-fallbacks.md` on every new failure observed.
