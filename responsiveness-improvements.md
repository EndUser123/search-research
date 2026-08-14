# Making search-research more responsive

The 99.21s first-call latency we just observed is the core problem. Here are the concrete improvements, grounded in CKS patterns from the 508k knowledge base and direct observation:

## Root cause: cold-start tax

`CKS.__init__` always loads `all-MiniLM-L6-v2` (SentenceTransformer) for semantic search, even when the query is a simple keyword match. The model takes 30-60s on first load, and 5-10s on subsequent loads from disk cache. The FTS5 path is fast (<100ms) but only runs after the semantic model initializes.

## Recommendation: Add a `lite` mode to `CKS.__init__`

```python
# core/cks/unified.py
def __init__(self, db_path=None, enable_semantic: bool = True, ...):
```

**The fastest fix is to skip semantic init when only FTS is needed.** The `CKS.search()` method already has an FTS-or-LIKE path. If `enable_semantic=False`, skip loading `all-MiniLM-L6-v2` entirely. The MCP `cks_search` tool already exposes a `limit` parameter — it can use FTS only by default and only load the model when `semantic=true` is explicitly requested.

The `hooks` already do this (`CKS_SPELL_CORRECTION_ENABLED=false` to avoid 12s vocab load). Extend the same pattern to semantic search.

## Recommendation: Lazy-load backends in `AsyncSearchRouter`

From the 99% responsiveness code patterns in the database:
- The 3-tier lazy loading pattern from `working_principles.md` is already partially implemented in `core/router_async.py:200-225` (CKS/KG/RLM backends wrapped in try/except).
- Extend this: only initialize backends on first use, not in `__init__`. The 39s first call I observed earlier (when calling `tool.fn` directly) was the cost of loading FAISS, AST, LSP, NLM, etc. all at once.

## Recommendation: Defer `__init__` work in `UnifiedAsyncRouter`

```python
# core/unified_router.py:146-150
@property
def _local_router(self) -> AsyncSearchRouter:
    """Get or create the local search router."""
    if self._async_local_router is None:
        self._async_local_router = AsyncSearchRouter(enable_jmri=self.enable_jmri)
    return self._async_local_router
```

This is already lazy for the local router — good. But the web router at line 159-166 is also lazy. The issue is that when `unified_search` is called, it constructs a new `UnifiedAsyncRouter` per invocation (line 252-255 in mcp_server.py). The first call triggers the full lazy-init chain.

**Fix**: Make the MCP tool functions accept an optional pre-initialized router via dependency injection, or cache a long-lived `UnifiedAsyncRouter` instance per daemon process.

## Recommendation: Set `CKS_SPELL_CORRECTION_ENABLED=false` in the MCP daemon environment

The `run_mcp.py` wrapper doesn't set this. Adding it to `run_mcp.py` or the `.mcp-mux.json` config would skip the 12s vocabulary load on every CKS init:

```python
# run_mcp.py
import os
os.environ.setdefault("CKS_SPELL_CORRECTION_ENABLED", "false")
os.environ.setdefault("CKS_ENABLE_SEMANTIC_DEFAULT", "false")  # opt-in only
```

## Recommendation: Pre-warm the daemon at startup

Instead of lazy init on first request, the Node.js wrapper (`mcp-start.mjs`) could pre-warm the daemon in the background after startup. The first user query would then be fast. Add a `--prewarm` flag to `run_mcp.py` that triggers a warmup search (e.g., `"warmup"` query) in a background thread after `mcp.run()` starts.

## Recommendation: Increase `.mcp-mux.json` timeouts

Current `.mcp-mux.json`:
```json
"requestTimeoutMs": 60000
```

The 99s model load exceeds this. Either:
- Increase `requestTimeoutMs` to 180000 (3 min) to handle cold start
- Or: make the first call return a "still loading" status quickly, then retry

The second is better UX — return `{"status": "loading", "retry_after_ms": 5000}` on the first call, then return results on retry.

## Recommendation: Persistent CKS instance across tool calls

The `functools.cache` on `_get_cks()` (line 70-78 of `core/mcp_server.py`) does cache across calls within a daemon process. But the SentenceTransformer model is loaded once per daemon process. If the daemon stays running (which `.mcp-mux.json` mode `shared` enables), subsequent calls are fast. The issue is only the first call.

**Verify**: After the first 99s call, subsequent calls should be <2s.

## Summary of priorities

| Priority | Change | Expected impact |
|---|---|---|
| 1 | Add `enable_semantic: bool` to `CKS.__init__` and default to `False` in MCP | -60s on first call |
| 2 | Add `CKS_SPELL_CORRECTION_ENABLED=false` to `run_mcp.py` | -12s on every daemon start |
| 3 | Cache `UnifiedAsyncRouter` per daemon process | -5s per call |
| 4 | Increase `requestTimeoutMs` to 180000 | Prevents timeout errors |
| 5 | Pre-warm daemon in background thread | First user query is fast |

The single biggest win is #1 — the SentenceTransformer model is the 99s bottleneck. Make it opt-in, not opt-out.

## Evidence from CKS

The patterns above are grounded in:
- `working_principles.md: Design for Stateless, Multi-Terminal Operation` — event-driven, avoid TTL
- `bugfixes.md: SessionStart Semantic Daemon Startup Fix` — daemon startup race conditions
- `questioning_patterns.md: Arbitrary Threshold Detection` — don't use timeouts without empirical basis
- CKS entries #2 and #5: latency tradeoffs are explicit decisions, not defaults
