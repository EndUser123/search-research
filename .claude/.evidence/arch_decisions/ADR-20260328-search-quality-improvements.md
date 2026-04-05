# ADR-20260328: Search Quality Improvements - Bug Fix (Post-Adversarial Review)

**Status:** Accepted
**Date:** 2026-03-28
**Context:** Task #2472 - Fix quality gate non-functional, backend failure masking

## What We Already Have (Verified by Code + Adversarial Review)

| Feature | Implementation | Location |
|---|---|---|
| RRF Fusion | `reciprocal_rank_fusion()` | `core/hybrid_ensemble.py` |
| Intent-Based Routing | Embedding-based semantic classification (10 categories) | `core/intent_classifier.py` |
| Quality Checking | `QualityConfig` + `is_satisfactory()` | `core/quality_checker.py` |
| Multi-Source Routing | 4 modes: auto, local-only, web-fallback, unified | `core/unified_router.py` |
| Async Concurrent Backends | `AsyncSearchRouter` with concurrent execution | `core/router_async.py` |
| Backend Health Tracking | `HealthStatus` dataclass + per-provider health | `core/health_status.py` |
| Progressive Enhancement | Local first → quality check → web fallback → RRF | `core/unified_router.py:168-191` |
| MCP Tools (7 exposed) | unified_search, local_search, web_search, cks_search, cks_search_semantic, cks_ingest, cks_stats | `core/mcp_server.py` |
| HyDE Query Enhancement | Single + Multi-perspective hypothetical doc generation | `core/hyde_single.py`, `core/hyde_multi_perspective.py` |
| 3-Layer Filtering | L1 (rule-based) + L2 (agent semantic) + L3 (presentation) | `skills/all/filtering.py`, `skills/all/agent_filter.py` |

## What's Actually Broken (3 verified bugs)

### BUG-1: Quality gate never passes — field name mismatch (CRITICAL)

**Impact:** Every search in `auto` and `web-fallback` mode ALWAYS triggers expensive web search, even when local results are excellent.

**Root cause:** `_search_result_to_dict()` in `unified_router.py:245-265` produces a dict with keys `score` and `source`. But `is_satisfactory()` in `quality_checker.py` checks for `confidence` (line 91) and `sources` (line 134). The fields never match, so:
- `_check_confidence()` returns False (no `confidence` key)
- `_check_backend_diversity()` returns False (no `sources` key)
- `is_satisfactory()` ALWAYS returns False

**Fix applied:**
- Updated `_search_result_to_dict()` to produce BOTH `score`/`source` (existing) AND `confidence`/`sources` (quality checker contract) fields
- Changed `QualityConfig.min_backends` default from 3 to 1 (a single result can only come from 1 source)

### BUG-2: Exception handlers in search_executor.py are dead code (MEDIUM)

**Impact:** Error information is lost two levels deeper than the ADR originally diagnosed.

**Root cause:** `UnifiedAsyncRouter.search_async()` at `unified_router.py:169-191` catches ALL exceptions internally (both in local and web search phases). The `except ConnectionError` / `except TimeoutError` blocks in `search_executor.py:74-85` can never execute because `search_async` never raises them.

**Status:** Documented but not fixed in this iteration. The current behavior (swallow errors, return empty) is safe — the fix would be to propagate failure info from the router level, which is a larger refactor.

### BUG-3: Callable import missing in mcp_server.py (LOW)

**Impact:** Would crash if annotations are evaluated at runtime. Currently safe due to `from __future__ import annotations` (PEP 563).

**Root cause:** `mcp_server.py:100` uses `Callable` in type hint but only imports `Any` from `typing`.

**Fix applied:** Added `Callable` import (auto-corrected to `collections.abc.Callable` by linter).

## Implementation Plan (Revised)

| # | Task | Files | Status |
|---|------|-------|--------|
| 1 | Fix `_search_result_to_dict()` to produce quality checker compatible fields | `core/unified_router.py` | DONE |
| 2 | Change `QualityConfig.min_backends` default from 3 to 1 | `core/quality_checker.py` | DONE |
| 3 | Add `Callable` import to mcp_server.py | `core/mcp_server.py` | DONE |
| 4 | Update tests for new `min_backends` default | `tests/test_quality_checker.py` | DONE |
| 5 | Add debug logging to quality check in `_should_skip_web_search()` | `core/unified_router.py` | DONE |

## Decision

Fix the 3 bugs. No new modules needed. The existing architecture (progressive enhancement + RRF + quality gates) is solid — it just wasn't wired up correctly.

### Rationale
- The quality gate was non-functional due to field name mismatch
- Fixing the adapter (`_search_result_to_dict`) is the lowest-risk approach — quality_checker's contract and tests remain unchanged
- `min_backends=1` is the correct default for single-result quality checking (one result = one source)
- The 80% of notebook ideas already implemented work correctly once the quality gate is functional

## What Was Wrong With the Original ADR

The original ADR contained 2 fabricated bugs:
- **Original BUG-1**: Claimed a temp script `tmp/wf_full.py` was generated with incorrect QualityConfig calls. No such script or generation mechanism exists in the codebase.
- **Original BUG-2**: Claimed heredoc syntax errors in temp script. Same non-existent code.

Both were identified by adversarial compliance and critic specialists during `/critique` review. The actual critical bug (quality checker field mismatch) was discovered by the critique process.

## Multi-Terminal Safety
- **Safe**: All changes are to adapter code (no shared state)
- **No new shared mutable state**: `_search_result_to_dict()` creates a new dict per call
- **No concurrency risk**: Each search call is independent
