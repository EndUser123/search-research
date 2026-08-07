# MCP Search Server Improvement Design

**Date:** 2026-08-07
**Status:** Approved (post /tp critique + /risk assessment)
**Session:** 019fd8dc

## Problem statement

The two MCP search servers built in session 019fd8dc are functionally thin across three axes:

1. **Search intelligence** — search_wiki indexes only frontmatter (~10% of content); search_web does no caching or re-ranking
2. **Composition** — the two servers don't combine; no unified entry point
3. **Usage driving** — nothing reliably steers the model to check the wiki before external research

Evidence-first evaluation (20 golden queries) found current frontmatter-only FTS5 achieves ~90% recall@1 — higher than expected. This re-prioritizes the axes: **composition and usage-driving first, intelligence later**.

## Design decisions (evidence-based)

### Decision 1: Composition over intelligence (phasing)

Evidence showed intelligence is lower priority than framed. The actual gaps are composition (no unified entry point) and usage-driving (model doesn't reliably call wiki first).

**Phasing:**
- Phase 1: Contract + Composition (foundation)
- Phase 2: Evaluation + Observability (measurement)
- Phase 3: Caching (operational optimization)
- Phase 4: Body-text FTS5 (intelligence — only if metrics show a gap)
- Phase 5: Embeddings + Reranking (conditional — only if Phase 4 shows residual gap)

### Decision 2: Composition library over third server

`search_all` is a **second tool within the search_wiki server**, not a third MCP server. Rationale:
- A third server that imports both implementations creates misleading topology (different initialization, config, lifecycle)
- A composition library avoids the boundary ambiguity
- The search_wiki server already runs as a process; adding a tool costs nothing

Rejected alternatives:
- **Third MCP server** — boundary ambiguity, misleading topology (codex critique finding #1)
- **True MCP protocol orchestrator** — JSON-RPC roundtrip overhead, Grok Build MCP SDK may not support nested client connections cleanly

### Decision 3: Async-native composition, no asyncio.run()

The search_wiki MCP server is already async. The `search_all` tool handler is async-native, using `asyncio.gather()` for concurrent wiki + web calls with `asyncio.wait_for()` timeout. No `asyncio.run()` in the call path (risk of nested event loop failure — codex critique finding #2).

## Architecture

```
MCP client (Grok)
  ├── search_wiki server (1 process, 2 tools)
  │     ├── query()         → FTS5 lookup (synchronous, sub-10ms)
  │     └── search_all()    → wiki + web composition (async, concurrent)
  │
  └── search_web server (1 process, 1 tool)
        └── query()         → Brave + Exa + DDG via RRF
```

### search_all composition flow

1. FTS5 lookup (synchronous, in-process, sub-10ms)
2. Web search via `parallel_search()` from search-mcp library (async, 15s timeout)
3. Both run concurrently via `asyncio.gather(wiki_task, web_task, return_exceptions=True)`
4. Results mapped to shared `SearchResult` contract
5. Merged with `[INTERNAL]` / `[EXTERNAL]` labels, typed deduplication
6. Per-source status block (machine-readable)
7. Internal results always surfaced first; web results labeled and deduplicated

## Shared result contract

Both search functions return results mapped to this typed structure before composition:

```python
@dataclass
class SearchResult:
    source: str           # "wiki" | "web:brave" | "web:exa" | "web:ddg"
    id: str               # canonical ID: wiki filename or normalized URL
    title: str
    url: str              # clickable path (file:/// for wiki, https:// for web)
    snippet: str          # summary or excerpt (~500 chars max, snippet_mode)
    score: float          # relevance score (0.0-1.0)
    retrieved_at: str     # ISO-8601 timestamp
    freshness: str        # "evergreen" | "recent" | "stale-check"
    status: str           # "ok" | "partial" | "failed" | "timeout"
```

**Per-source status block** (machine-readable, returned with every search_all response):

```json
{
  "sources": {
    "wiki": {"status": "ok", "count": 5, "latency_ms": 8},
    "web": {"status": "partial", "count": 3, "latency_ms": 2400, "failed_backends": ["exa"]}
  },
  "results": [...]
}
```

This makes partial failure observable — the model can distinguish "web timed out" from "web returned nothing" from "web succeeded."

## Components

### search_wiki server (existing, modified)

Two tools:

| Tool | Description |
|---|---|
| `query` | "Search the workspace knowledge base of 990+ concepts covering prior decisions, documented patterns, and design rationale. Use for workspace-specific knowledge — the workspace likely already has relevant findings that external research would re-derive." |
| `search_all` (NEW) | "Search both the workspace knowledge base AND the web in one call. Returns internal results labeled [INTERNAL] and external results labeled [EXTERNAL], with per-source status. Use when you need both workspace context and external validation." |

**Tool descriptions use selection semantics** (when to use each tool), not commands ("ALWAYS call this first"). This avoids contradictory choice architecture between search_wiki and search_all (codex critique finding #6).

### search_web server (existing, unmodified in Phase 1)

| Tool | Description |
|---|---|
| `query` | "Search the web (Brave + Exa + DDG, fused via RRF). Use when you need current information, external best practices, or community knowledge not in the workspace." |

### search_all implementation (in search_wiki_server.py)

```python
@server.call_tool()
async def call_tool(name: str, arguments: dict):
    if name == "query":
        # existing FTS5 lookup (synchronous, fast)
        ...
    elif name == "search_all":
        return await handle_search_all(arguments)

async def handle_search_all(arguments: dict):
    query = arguments["query"]
    web_enabled = arguments.get("web_enabled", True)

    # Run wiki and web concurrently (not serialized)
    wiki_task = asyncio.create_task(run_wiki_search(query))
    web_task = asyncio.create_task(run_web_search(query)) if web_enabled else asyncio.create_task(asyncio.sleep(0))

    wiki_results, web_results = await asyncio.gather(wiki_task, web_task, return_exceptions=True)

    # Handle exceptions as status, not crashes
    wiki_status = parse_status(wiki_results)
    web_status = parse_status(web_results)

    # Map to shared contract
    wiki_mapped = [map_wiki_result(r) for r in extract_results(wiki_results)]
    web_mapped = [map_web_result(r) for r in extract_results(web_results)]

    # Typed deduplication
    merged = deduplicate(wiki_mapped, web_mapped)

    return build_composition_response(merged, wiki_status, web_status)

async def run_web_search(query: str):
    """Lazy import: if search-mcp import fails, return empty + failed status."""
    try:
        sys.path.insert(0, "C:/Users/brsth/.grok/search-mcp")
        from server import parallel_search
        return await asyncio.wait_for(parallel_search(query, num_results=5), timeout=15.0)
    except Exception as e:
        return {"_error": str(e), "_status": "failed"}
```

**Key implementation details:**
- **Lazy import** of `parallel_search` inside the handler function, not at module top (risk mitigation #2 — if config is malformed, only search_all fails, not the entire search_wiki server)
- **Concurrent execution** via `asyncio.gather()` — wiki results ready in 10ms don't wait for web's 15s timeout (risk mitigation #3)
- **Exception handling** via `return_exceptions=True` — failures become status, not crashes

## Deduplication (typed provenance)

Replace naive "lowercase title strip" with typed dedup (codex critique finding #5):

1. **URL-based**: normalize URLs (strip query params, trailing slashes, www prefix). If two results share a normalized URL, keep the higher-scored one.
2. **Title similarity (fuzzy)**: for wiki results where a web result's title has >0.85 similarity (`difflib.SequenceMatcher`), keep both but mark the web result as `[EXTERNAL — relates to internal concept]`.
3. **Never drop wiki results** — internal knowledge always surfaces, even if duplicated by web.

## Error handling (fail-open with machine-readable status)

| Failure | Behavior | Status block |
|---|---|---|
| search_wiki FTS5 index missing | search_all returns web-only | `{"wiki": {"status": "failed", "error": "index missing"}, "web": {"status": "ok"}}` |
| search_web all backends fail | search_all returns wiki-only | `{"wiki": {"status": "ok"}, "web": {"status": "failed", "failed_backends": ["brave", "exa", "ddg"]}}` |
| search_web partial (1-2 backends fail) | search_all returns wiki + partial web | `{"wiki": {"status": "ok"}, "web": {"status": "partial", "failed_backends": ["exa"]}}` |
| search_web timeout (>15s) | search_all returns wiki + timeout note | `{"wiki": {"status": "ok"}, "web": {"status": "timeout"}}` |
| search-mcp import fails | search_all returns wiki-only, search_web server unaffected | `{"wiki": {"status": "ok"}, "web": {"status": "failed", "error": "import error"}}` |

**Principle:** every path returns SOMETHING, with machine-readable status distinguishing availability from correctness (codex critique finding #3).

## Privacy option

`search_all` accepts an optional `web_enabled: bool` parameter (default `true`). When set to `false`, it performs wiki-only search — for sensitive workspace topics where sending internal terms to web backends is undesirable (codex critique finding #8). The AGENTS.md convention notes this option exists.

## Risk mitigations (from /risk assessment)

All 8 risks from the risk scan have mitigations folded into Phase 1:

| Risk | Mitigation | Implementation |
|---|---|---|
| SDK pin breakage (#1) | Version check at startup; pin `mcp<2` in requirements | `if mcp.__version__ >= "2.0": raise RuntimeError("MCP SDK 2.0 not supported")` at top of server |
| Import-time side effects (#2) | Lazy import inside handler function with try/except | `from server import parallel_search` inside `run_web_search()`, not at module top |
| No timeout isolation (#3) | Concurrent execution via `asyncio.gather()` | Wiki and web run in parallel, not serial |
| Multi-terminal API amplification (#4) | Phase 3 caching + future Streamable HTTP | Documented; deferred to Phase 3 |
| Dedup fuzzy matching (#5) | Never drop wiki results; flag web as "relates to" | In deduplication logic |
| Contract drift (#6) | Shared SearchResult dataclass with type checking | Both mapper functions import from same module |
| Stale index (#7) | Add `refresh_index()` MCP tool + incremental rebuild | New tool in search_wiki server; call after /wiki writes |
| No observability (#8) | Query log file (JSONL) | All three tools append `{tool, query, timestamp, result_count, latency_ms}` to `~/.grok/hooks/scripts/search_query_log.jsonl` |

## AGENTS.md convention

One-line addition to the web-search tool selection rule:

> Before external web research, check if `search_wiki` has relevant workspace knowledge — if the topic involves prior decisions, patterns, or documented solutions, the workspace likely already covers it. Use `search_all` when you need both.

## Phasing

| Phase | What ships | Why this order |
|---|---|---|
| **Phase 1: Contract + Composition** | Shared SearchResult contract, search_all tool (async-safe), per-source status, typed dedup, revised tool descriptions, AGENTS.md convention, SDK pin check, lazy import, query log, refresh_index tool | Foundation — everything else depends on a stable result contract |
| **Phase 2: Evaluation + Observability** | Expand golden-query eval to 30 queries, add latency/cost/source-completeness metrics, measure search_all vs search_wiki vs search_web selection behavior via query log | Need measurement before adding intelligence — prevents optimizing the wrong behavior |
| **Phase 3: Caching** | Wire QueryCache from search-research into search_web, with cache-key normalization and freshness metadata | Only after query semantics stabilize (Phase 1-2) — prevents caching stale poor results |
| **Phase 4: Body-text FTS5** | Expand wiki index to full concept body (section-aware chunking), add min_score filtering | Closes recall gap for conceptual queries — only if Phase 2 metrics show a gap |
| **Phase 5: Embeddings + Reranking** (conditional) | bge-small-en-v1.5 embeddings via FastEmbed ONNX, cross-encoder reranking (ms-marco-MiniLM-L-6-v2), MMR diversification | Only if Phase 4 body-text FTS5 shows recall still below target |

## Testing

| Test type | What | Phase |
|---|---|---|
| **Shared contract tests** | Both search functions return SearchResult with all required fields | Phase 1 |
| **Per-source status tests** | Partial failure, timeout, success all produce correct machine-readable status | Phase 1 |
| **Dedup accuracy** | Same-URL results merge, similar-title results cross-reference, wiki results never dropped | Phase 1 |
| **Lazy import isolation** | search-mcp import failure doesn't crash search_wiki server's `query` tool | Phase 1 |
| **SDK version check** | Server warns clearly if mcp >= 2.0 | Phase 1 |
| **Query log verification** | All three tools append to JSONL log with correct fields | Phase 1 |
| **Golden query eval (30 queries)** | Recall@1, recall@5 for wiki search (frontmatter and later body text) | Phase 2 |
| **Latency metrics** | p50/p95 for search_all (combined), search_wiki alone, search_web alone | Phase 2 |
| **Tool selection A/B** | Over 10+ sessions, track which tool the model calls for different query types via query log | Phase 2 |
| **Source completeness audit** | Per-query: did wiki return results? did web? did either timeout? | Phase 2 |
| **Cache hit/miss + freshness** | First vs second call latency, cache invalidation on wiki concept writes | Phase 3 |
| **Body-text recall improvement** | Compare recall@5 before/after body-text index | Phase 4 |

## Provenance

- **Research:** `/www` validated approach via lyonzin/knowledge-rag (v4.8.0, 557 tests), olafgeibig/knowledge-mcp, Airweave, search-research package analysis
- **Evidence:** Golden-query evaluation (20 queries, ~90% recall@1), search-research importability test (modules import cleanly)
- **Critique:** `/tp {3}` produced 8 design findings (all addressed in revised sections); `/risk` scan found 8 risks (all mitigated in Phase 1)
- **Wiki:** `[[mcp-search-server-improvement-research-2026]]`

## Falsifier

This design is wrong if:
- Phase 1 ships and the model never calls `search_all` (the composition tool isn't useful)
- The per-source status block is ignored by the model (partial-failure observability doesn't change behavior)
- The query log shows the model still calls `search_web` before `search_wiki` despite revised descriptions
- Phase 2 metrics show frontmatter-only FTS5 recall is sufficient (intelligence phases unnecessary)

If any pattern appears after 5 sessions, iterate the design or retire the composition approach.
