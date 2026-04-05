# Adversarial Critique: ADR-20260328 Search Quality Improvements

**Date:** 2026-03-28
**Reviewer:** adversarial-critic specialist
**ADR Status:** Proposed

---

## Summary

The ADR identifies 3 bugs and proposes a minimal fix approach (Option A). The overall direction is reasonable -- fix real bugs rather than add features. However, the analysis contains factual inaccuracies about the code, an internally contradictory bug description, a missing import that would crash the MCP server, and an unverified claim about a file that does not exist. Several edge cases are listed but not addressed in the implementation plan.

---

## Findings

### [HIGH] BUG-1 description contradicts itself -- the "correct" code is already correct

The ADR claims `search_executor.py:73` calls `router.search_async(query, limit=limit)` "correctly", then immediately claims the `/all` skill "was passing `QualityConfig` to `search_async`" and that a generated temp script constructs the call incorrectly.

Evidence from `search_executor.py:73`:
```python
results = await router.search_async(query, limit=limit)
```

This is the ONLY call site in search_executor.py. The `all.py` entry point at line 167-175 calls `search_executor.execute_search()`, which constructs the router with `QualityConfig` passed to the constructor (line 57-68), NOT to `search_async`. The `QualityConfig` is correctly passed to `UnifiedAsyncRouter.__init__()` via the `quality_config` parameter.

The ADR's "Root cause" references `tmp/wf_full.py` -- a generated temporary file that does not exist on disk (verified: `Glob` for `tmp/wf_full.py` returned no results). The ADR bases a HIGH-severity bug claim on a file that may only have existed during a single session's execution, with no evidence the generation code itself is broken.

**Impact:** Task 1 ("Fix script generation in /all skill to avoid heredoc escaping") may target non-existent code. The `all.py` file at `P:/packages/search-research/skills/all/all.py` is a clean Python script -- it does NOT generate heredoc-based temp scripts. The ADR conflates a past observed error with the current codebase state.

---

### [HIGH] BUG-2 references a non-existent file and unverified generation mechanism

The ADR states:
- "Line continuation character errors in `tmp\wf_full.py:2`"
- "Invalid escape sequence `\.` at line 50"
- "Root cause: The heredoc/pyramid multiline string generation has Windows-specific quoting issues"

The file `tmp/wf_full.py` does not exist. The `all.py` entry point is a standalone Python script, not a heredoc generator. No code in `all.py`, `search_executor.py`, or the broader `/all` skill directory generates `tmp/wf_full.py`.

Without evidence of the generation mechanism, this bug cannot be reproduced or fixed as described. The ADR fails the Green State Axiom -- it attributes errors to code without tracing the causal chain.

---

### [HIGH] Quality check will NEVER pass -- `is_satisfactory()` receives incompatible data

At `unified_router.py:217-219`:
```python
best_result = local_results[0]
result_dict = self._search_result_to_dict(best_result)
return is_satisfactory(result_dict, self.quality_config)
```

The `_search_result_to_dict()` method (line 245-265) produces a dict with keys: `id`, `title`, `content`, `score`, `source`, `url`, `file_path`, `line_number`, `metadata`, `created_at`.

`is_satisfactory()` in `quality_checker.py:145-189` checks THREE conditions, ALL must pass:
1. `confidence` field exists and >= threshold (field name: `confidence`) -- NOT present in dict
2. `created_at` field exists and is fresh -- present but may be None
3. `sources` field (plural) exists as list/set with >= min_backends entries -- NOT present in dict

The dict has `score` (not `confidence`), `source` (singular, not `sources`), and `created_at` (may be None). The quality check will return `False` for every result because:
- `_check_confidence()` returns False (no `confidence` key)
- `_check_backend_diversity()` returns False (no `sources` key)

This means `is_satisfactory()` ALWAYS returns False in practice, causing the router to ALWAYS proceed to web search in `auto` and `web-fallback` modes, even when local results are excellent. This is a significant logic bug not identified in the ADR.

---

### [HIGH] MCP server has missing `Callable` import -- would crash at runtime

In `mcp_server.py:100`:
```python
format_item: Callable[[int], list[str]],
```

But `Callable` is never imported. The imports at lines 49-52 are:
```python
import functools
import logging
import time
from typing import Any
```

`Callable` requires `from typing import Callable` (or `from collections.abc import Callable`). Due to `from __future__ import annotations` at line 47, this won't crash at import time (PEP 563 defers annotation evaluation), but it WILL crash if `_format_markdown_results()` is ever called with runtime type checking or if the annotations are evaluated.

This is not mentioned in the ADR at all.

---

### [MEDIUM] BUG-3 root cause misidentified -- error handling already exists but is insufficient

The ADR says `search_executor.py` catches errors but returns empty results without distinguishing "no results" from "backend failure". The actual code at `search_executor.py:72-87`:

```python
try:
    results = await router.search_async(query, limit=limit)
except ConnectionError as e:
    print(f"[Search Executor] ConnectionError: {e}")
    results = []
except TimeoutError as e:
    print(f"[Search Executor] TimeoutError: {e}")
    results = []
except Exception as e:
    print(f"[Search Executor] Unexpected error: {type(e).__name__}: {e}")
    results = []
```

The deeper issue is that `UnifiedAsyncRouter.search_async()` at `unified_router.py:169-191` ALREADY catches all exceptions internally and returns empty lists or partial results. It never raises `ConnectionError` or `TimeoutError` to the caller. The `except` blocks in `search_executor.py` are dead code -- they can never execute because `search_async` handles errors internally.

Similarly, `AsyncSearchRouter._search_web_provider_async()` (router_async.py:699-740) catches `TimeoutError` and generic exceptions, returning `[]`. The `BackendHealthRegistry` already records failures at lines 734 and 739.

So the problem isn't that error information is lost at the executor level -- it's lost TWO levels deeper, in `AsyncSearchRouter` and `UnifiedAsyncRouter`. Adding `BackendStatus` to `search_executor.py` (Task 2) won't fix this unless the underlying routers also propagate failure information.

---

### [MEDIUM] Task 4 target (mcp_server.py) is misaligned with the described bug

The ADR says Task 4 is "Fix 'no results' vs 'backend failure' reporting in MCP tools" targeting `core/mcp_server.py`. But `mcp_server.py` at lines 221-244 already has error handling that returns "Search Error" messages with exception details. The `unified_search` tool catches `Exception` and formats it with the error message.

The actual problem is upstream: `UnifiedAsyncRouter.search_async()` swallows all errors and returns empty lists, so the MCP tool never sees an exception to catch. The fix needs to be in `unified_router.py`, not `mcp_server.py`.

---

### [MEDIUM] QualityConfig parameter mapping is semantically incorrect

At `search_executor.py:57-60`:
```python
quality_config = QualityConfig(
    confidence_threshold=min_score,
    min_backends=min_results
)
```

The `min_score` parameter (described as "Minimum relevance score for quality floor") is mapped to `confidence_threshold`, which expects a confidence value (0.0-1.0). The `min_results` parameter (described as "Minimum result count") is mapped to `min_backends`, which expects the number of unique backends.

These are semantically different concepts:
- A relevance score threshold is not the same as a confidence threshold
- A minimum result count is not the same as a minimum backend diversity count

The ADR does not identify this parameter mismatch.

---

### [MEDIUM] Edge cases listed but not addressed in implementation plan

The ADR lists three edge cases (lines 96-99):
1. "All backends fail simultaneously" -- no task addresses this
2. "Partial backend failure" -- no task addresses this
3. "Network offline" -- no task addresses this

These are listed as "Edge Cases" but none of the 5 implementation tasks target them. The tasks focus on script generation (Task 1), BackendStatus (Task 2), credit-check (Task 3), MCP reporting (Task 4), and integration tests (Task 5). If these edge cases are real risks, they should have corresponding tasks. If they are not, they should not be listed.

---

### [MEDIUM] Option B dismissed without evidence

Option B (add query expansion and evidence gates) is rejected as "over-engineering" with the justification that "existing progressive enhancement + RRF already covers these use cases adequately." However, as demonstrated above, the progressive enhancement is broken because `is_satisfactory()` never passes due to field name mismatches. The quality gate is non-functional, so claiming it "already covers" anything is inaccurate.

Whether query expansion and evidence gates are over-engineering is a legitimate judgment call, but the justification should not rely on broken infrastructure.

---

### [LOW] Multi-terminal safety claims are partially incorrect

The ADR states "No shared mutable state: search_executor creates new router per call." While `search_executor.py` does create a new `UnifiedAsyncRouter` per call, the `AsyncSearchRouter` inside it uses:
- `QueryCache` (shared state, though per-instance)
- `BackendHealthRegistry` (per-instance, not shared between calls)
- `get_async_client()` in provider clients (shared HTTP client via module-level singleton)

The `serper_client.py` and `tavily_client.py` both use `get_async_client()` from `search_research.http_client`, which is likely a module-level singleton. If two terminals run searches concurrently, they share the same HTTP connection pool. This is generally fine (connection pooling is designed for this), but the blanket "no shared mutable state" claim is inaccurate.

---

### [LOW] "8 of 10 notebook ideas are already implemented" is unverified

The ADR states this as a verified fact but provides no evidence of what the original "10 notebook ideas" were. The table lists 10 rows, suggesting all 10 were checked, but there's no link to the source notebook or requirements document. The claim is Tier 4 (unverified) without a citation.

---

### [LOW] Inconsistency in Serper client: API key in POST body vs header

The `serper_client.py` sends the API key as `apiKey` in the JSON POST payload (line 98: `"apiKey": self._api_key`). Serper's actual API expects the key as an `X-API-KEY` header. Sending it in the body may cause authentication failures that the ADR attributes to "credit exhaustion." This is a potential misdiagnosis -- the "out of credits" error could actually be an auth failure from incorrect key placement.

---

## Recommendations

1. **Re-verify BUG-1 and BUG-2** against the current codebase. The `all.py` file does not generate temp scripts. If a previous session generated `tmp/wf_full.py`, that generation code no longer exists (or never existed in the committed codebase).

2. **Add the `is_satisfactory()` field mismatch** as a HIGH-severity bug. The quality gate is non-functional due to field name mismatches (`score` vs `confidence`, `source` vs `sources`). This affects every search in `auto` and `web-fallback` modes.

3. **Fix the `Callable` import** in `mcp_server.py` -- add `from typing import Callable`.

4. **Re-target Task 2 and Task 4** to address error propagation in `unified_router.py` and `router_async.py`, not just `search_executor.py` and `mcp_server.py`. The errors are swallowed before they reach the executor.

5. **Investigate Serper auth mechanism** before assuming credit exhaustion -- the API key placement may be incorrect.

6. **Either add tasks for the 3 edge cases or remove them** from the ADR. Listing risks without mitigation tasks creates a false sense of coverage.
