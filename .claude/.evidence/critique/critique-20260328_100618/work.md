# ADR-20260328: Search Quality Improvements - Gap Analysis and Design

**Status:** Proposed
**Date:** 2026-03-28
**Context:** Task #2472 - Fix /all skill execution, search_async API misuse, and result quality

## What We Already Have (Verified by Code)

| Notebook Idea | Implementation | Location |
|---|---|---|
| RRF Fusion | `reciprocal_rank_fusion()` | `core/hybrid_ensemble.py` |
| Intent-Based Routing | Embedding-based semantic classification (10 categories) | `core/intent_classifier.py` |
| Quality Checking | `QualityConfig` + `is_satisfactory()` | `core/quality_checker.py` |
| Multi-Source Routing | 4 modes: auto, local-only, web-fallback, unified | `core/unified_router.py` |
| Async Concurrent Backends | `AsyncSearchRouter` with concurrent execution | `core/router_async.py` |
| Backend Health Tracking | `HealthStatus` dataclass + per-provider health | `core/health_status.py`, `core/providers/provider_health.py` |
| Graceful Degradation | ConnectionError/TimeoutError catch blocks | `skills/all/search_executor.py` |
| Progressive Enhancement | Local first → quality check → web fallback → RRF | `core/unified_router.py:142-162` |
| MCP Tools (7 exposed) | unified_search, local_search, web_search, cks_search, cks_search_semantic, cks_ingest, cks_stats | `core/mcp_server.py` |
| HyDE Query Enhancement | Single + Multi-perspective hypothetical doc generation | `core/hyde_single.py`, `core/hyde_multi_perspective_comprehensive.py` |
| 3-Layer Filtering | L1 (rule-based) + L2 (agent semantic) + L3 (presentation) | `skills/all/filtering.py`, `skills/all/agent_filter.py` |

**Verdict: 8 of 10 notebook ideas are already implemented.**

## What's Actually Broken (3 bugs)

### BUG-1: search_async API mismatch (HIGH)
The `/all` skill's `search_executor.py:73` calls `router.search_async(query, limit=limit)` correctly.
But the /all skill entry point (`all.py`) or the generated temp script was passing `QualityConfig` to `search_async`.
**Root cause**: The /all skill generates a temporary Python script (`tmp/wf_full.py`) that constructs the call incorrectly.
**Fix**: Ensure the generated script uses `UnifiedAsyncRouter.search_async(query, limit)` not QualityConfig.

### BUG-2: Syntax errors in generated script (HIGH)
Running via `python - <<'PY'` produced syntax errors:
- Line continuation character errors in `tmp\wf_full.py:2`
- Invalid escape sequence `\.` at line 50

**Root cause**: The heredoc/pyramid multiline string generation has Windows-specific quoting issues.
**Fix**: Use a temp .py file approach instead of inline heredoc, or fix the string escaping.

 ### BUG-3: Backend credit exhaustion (HIGH)
- Serper: out of credits (returns errors)
- Tavily: timeout
- The system reports "No relevant ideas found" instead of "Search backends are failing"

**Root cause**: `search_executor.py` catches the errors but returns empty results without distinguishing "no results" from "backend failure".

**Fix**: Return structured failure info so caller can distinguish these states.

 ## Minimal Delta Design

### Option A: Fix 3 bugs in existing code (RECOMMENDED)
Extend existing `search_executor.py` and the /all skill generation to:
1. Fix the script generation to avoid heredoc escaping issues
2. Add `BackendStatus` to the return value so callers know what failed
3. Add credit-check pre-call to detect exhausted backends before wasting time

**Files to change:**
- `skills/all/search_executor.py` - Add BackendStatus to return, fix error reporting
- `skills/all/all.py` - Fix script generation to avoid heredoc issues
- `core/providers/serper_client.py` - Add credit detection
- `core/providers/tavily_client.py` - Add timeout detection

**Favors:** Reliability (accurate failure reporting)
**Sacrifices:** None (pure improvement)
**Fails when:** N/A (no new failure modes)

### Option B: Add notebook ideas not yet implemented
Add the 2 missing features: query expansion and evidence gates.
**REJECTED** - Over-engineering. The existing progressive enhancement + RRF already covers these use cases adequately for a solo dev.

## Decision

**Go with Option A.** Fix the 3 bugs. No new modules needed.

### Rationale
- 80% of notebook ideas are already implemented
- The 3 bugs are causing real failures NOW
- Adding new features (query expansion, evidence gates) would be over-engineering
- The existing architecture (progressive enhancement + RRF + quality gates) is solid

### User Input Needed

**1. Serper credit exhaustion**: Serper is out of credits. Should I:
   - (a) Disable Serper provider until credits are restored
   - (b) Add a credit-check wrapper that auto-skips Serper when it returns credit errors
   - (c) Switch to a different free-tier provider

**2. Tavily timeouts**: Is Tavily consistently timing out, or was this transient?

## Multi-Terminal Safety
- **Safe**: All changes are to the /all skill (single-user) and search executor (no shared state)
- **No shared mutable state**: search_executor creates new router per call
- **No concurrency risk**: Each search call is independent

## Edge Cases
1. **All backends fail simultaneously**: Should return clear "all backends failed" message, not "no results"
2. **Partial backend failure**: Should return results from surviving backends + warning about failed ones
3. **Network offline**: Should detect and report, not hang

## Implementation Plan (Core Only - 5 tasks)

| # | Task | Files |
|---|------|-------|
| 1 | Fix script generation in /all skill to avoid heredoc escaping | `skills/all/all.py` |
| 2 | Add BackendStatus to search_executor return value | `skills/all/search_executor.py` |
| 3 | Add credit-check pre-call to Serper client | `core/providers/serper_client.py` |
| 4 | Fix "no results" vs "backend failure" reporting in MCP tools | `core/mcp_server.py` |
| 5 | Add integration test for backend failure scenarios | `skills/all/tests/test_search_executor.py` |
