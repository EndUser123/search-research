# Adversarial Compliance Review: ADR-20260328-search-quality-improvements

**Reviewed:** P:/.claude/arch_decisions/ADR-20260328-search-quality-improvements.md
**Date:** 2026-03-28
**Reviewer:** adversarial-compliance specialist

---

## 1. Spec Alignment (ADR claims vs actual code)

### [HIGH] BUG-1 root cause is fabricated -- no temp script generation exists

ADR line 30 claims: "The /all skill generates a temporary Python script (`tmp/wf_full.py`) that constructs the call incorrectly."

**Evidence against this claim:**
- `all.py` (the /all skill entry point) imports `search_executor` directly and calls `execute_search()` at line 167. There is NO temp script generation, NO heredoc, NO `wf_full.py` anywhere in the codebase (glob search returned zero matches for `**/tmp/wf_full.py`).
- `search_executor.py:73` calls `router.search_async(query, limit=limit)` with the correct signature (`query: str, limit: int`). No `QualityConfig` is passed to `search_async`.
- The ADR's own BUG-1 description contradicts itself: line 28 says "calls `router.search_async(query, limit=limit)` correctly" then immediately claims the "generated temp script" passes QualityConfig to search_async. There is no generated temp script.

**Impact:** The entire basis for Task 1 ("Fix script generation in /all skill to avoid heredoc escaping") targets non-existent code. The bug as described cannot exist because the code path the ADR describes does not exist.

### [HIGH] BUG-2 references non-existent file and non-existent mechanism

ADR line 35-36 claims: "Line continuation character errors in `tmp\wf_full.py:2`" and "Running via `python - <<'PY'` produced syntax errors."

**Evidence against this claim:**
- No `wf_full.py` exists anywhere under `P:/packages/search-research/`.
- The `/all` skill (`all.py`) is a standard Python script invoked via `python all.py "query"`. There is no heredoc generation, no `python - <<'PY'` pattern, no inline script construction anywhere in the skill's codebase (grep for `heredoc`, `wf_full`, `<<'PY'` all returned zero matches).

**Impact:** Task 1 is entirely based on a fabricated bug. If this was a real error from a past session, the ADR provides no evidence and the code does not contain the mechanism described.

### [MEDIUM] Line number reference "unified_router.py:142-162" is inaccurate

ADR line 18 claims: "Progressive Enhancement: Local first -> quality check -> web fallback -> RRF at `core/unified_router.py:142-162`"

**Actual code:** Lines 142-162 contain the `search_async` method *signature and docstring only* (def, parameters, return type, raises). The actual progressive enhancement logic (Phase 1 local search, Phase 2 quality check, Phase 3 web search, Phase 4 RRF fusion) is at lines 168-191. The line range cited points to the wrong location.

### [MEDIUM] QualityConfig description in ADR is incomplete

ADR line 13 describes QualityConfig as: "`QualityConfig` + `is_satisfactory()`"

**Actual code:** QualityConfig has three specific thresholds: `confidence_threshold` (float, default 0.8), `freshness_hours` (int, default 24), and `min_backends` (int, default 3). The ADR omits these specifics, making it impossible to verify whether the quality checking thresholds are appropriate for the claimed use cases.

### [LOW] MCP tool description partially inaccurate for web_search

ADR line 19 lists: "MCP Tools (7 exposed) -- unified_search, local_search, web_search, cks_search, cks_search_semantic, cks_ingest, cks_stats"

**Verification:** All 7 tools exist (confirmed at `mcp_server.py` lines 183, 247, 296, 390, 436, 486, 559). The list is accurate. However, the ADR claims "7 exposed" but does not mention that `web_search`'s description says "multiple providers (Tavily, Serper, Exa, Brave)" -- the accuracy of this provider list depends on API key availability, which is not discussed.

### [LOW] HyDE file name discrepancy

ADR line 20 lists: "`core/hyde_single.py`, `core/hyde_multi_perspective_comprehensive.py`"

**Actual files:** `core/hyde_single.py` and `core/hyde_multi_perspective.py` both exist, plus `core/hyde_multi_perspective_comprehensive.py`. The ADR lists only one of the two multi-perspective files. Minor omission.

---

## 2. Completeness (ADR template compliance)

### [HIGH] Missing "Decision Maker" field

The project's ADR template (per `ADR-20260321-gto-viability-gate-fix.md`) includes a **Decision Maker** field. This ADR omits it entirely.

### [MEDIUM] Missing "Context and Problem Statement" section header

Established ADRs in this project use a structured `## Context and Problem Statement` section. This ADR uses `## What We Already Have` and `## What's Actually Broken` instead, which is non-standard formatting. The context is scattered across multiple sections rather than consolidated.

### [MEDIUM] Missing "Consequences" section

The ADR has no explicit consequences section describing what happens after implementation: no migration notes, no backward compatibility discussion, no deprecation plan.

### [LOW] Status is "Proposed" but implementation task exists

Task #2472 is already `in_progress` ("Fix /all skill execution - search_async API misuse and result quality"). The ADR status should reflect this reality. If implementation has started, the status should be "Accepted" or "Implementing".

---

## 3. Contract Accuracy

### [HIGH] search_async signature is correctly described but the "bug" claim is wrong

ADR line 28 states: "search_executor.py:73 calls `router.search_async(query, limit=limit)` correctly."

**Verified:** The actual signature at `unified_router.py:142-146` is `async def search_async(self, query: str, limit: int = 10) -> list[SearchResult]`. The call at `search_executor.py:73` is `results = await router.search_async(query, limit=limit)`. This IS correct. The ADR admits this call is correct, then claims a different code path (non-existent temp script) is the problem. This is internally inconsistent.

### [MEDIUM] ADR claims search_executor passes QualityConfig to search_async

ADR line 29 says: "the /all skill entry point (`all.py`) or the generated temp script was passing `QualityConfig` to `search_async`."

**Verified:** `search_executor.py:57-68` creates `QualityConfig` and passes it to `UnifiedAsyncRouter.__init__()` as `quality_config=quality_config`. This is the CORRECT usage -- QualityConfig is a constructor parameter, not a `search_async` argument. The ADR's claim that QualityConfig was ever passed to `search_async` is unsupported by the code.

### [LOW] Return type not discussed

`search_async` returns `list[SearchResult]`. The ADR's Task 2 proposes adding `BackendStatus` to the "return value" but does not specify whether this changes the signature, wraps the list, or uses a different mechanism. This ambiguity makes the task unclear.

---

## 4. Implementation Plan Feasibility

### [HIGH] Task 1 targets non-existent code

Task 1: "Fix script generation in /all skill to avoid heredoc escaping" -- `skills/all/all.py`

There is no script generation, no heredoc, no temp file creation in `all.py`. The file is a straightforward argparse script that calls `search_executor.execute_search()`. This task cannot be implemented as described because the code it targets does not exist.

### [MEDIUM] Task 2 is underspecified

Task 2: "Add BackendStatus to search_executor return value"

The current `execute_search()` returns `list` (not `list[SearchResult]` -- the type hint is just `list`). Adding `BackendStatus` requires:
1. Defining a `BackendStatus` dataclass or similar
2. Changing the return type from `list` to a composite type
3. Updating ALL callers (`all.py:167`, `mcp_server.py:236`, any other consumers)

The ADR does not discuss caller impact or the API contract change.

### [MEDIUM] Task 3 targets may not have the expected structure

Task 3: "Add credit-check pre-call to Serper client" -- `core/providers/serper_client.py`

The ADR provides no evidence about the current serper_client.py structure. Without verifying the client's API, it is unclear whether a "credit-check pre-call" is feasible. Some search APIs do not expose credit status programmatically.

### [LOW] Task 4 scope is reasonable but overlaps with Task 2

Task 4: "Fix 'no results' vs 'backend failure' reporting in MCP tools" -- `core/mcp_server.py`

This is a reasonable change. The MCP tools currently format results with "No results found." for empty lists. However, this change depends on Task 2 providing the BackendStatus information. The dependency is not explicitly stated.

### [LOW] Task 5 path may be incorrect

Task 5: "Add integration test for backend failure scenarios" -- `skills/all/tests/test_search_executor.py`

A test directory at `skills/all/tests/` may not exist. The ADR does not verify this path.

---

## 5. Multi-Terminal Safety Assessment

### [MEDIUM] "No shared mutable state" claim is partially wrong

ADR line 92-94 claims: "All changes are to the /all skill (single-user) and search executor (no shared state). No shared mutable state. search_executor creates new router per call."

**Analysis:**
- `search_executor.execute_search()` DOES create a new `UnifiedAsyncRouter` per call (line 63). This part is correct.
- However, the ADR proposes adding `BackendStatus` to the return value. If BackendStatus tracks provider health state (e.g., "Serper is out of credits"), and this state is cached or persisted anywhere, it becomes shared mutable state accessible across terminals.
- The proposed "credit-check pre-call" in Task 3 may involve caching credit status, which would be shared state.
- The ADR's multi-terminal safety claim is only valid for the current code. The proposed changes may introduce shared state without acknowledgment.

### [LOW] _get_cks() uses functools.cache -- potential singleton issue

`mcp_server.py:67` uses `@functools.cache` for `_get_cks()`. This is a process-level singleton, safe across MCP invocations within one process but not across multiple MCP server instances. The ADR does not discuss this.

---

## Summary of Findings

| Severity | Count | Key Issues |
|----------|-------|------------|
| HIGH | 4 | BUG-1 fabricated (no temp script), BUG-2 fabricated (no heredoc), Task 1 targets non-existent code, Missing Decision Maker |
| MEDIUM | 6 | Wrong line numbers, incomplete QualityConfig description, non-standard format, missing consequences, Task 2 underspecified, multi-terminal claim incomplete |
| LOW | 5 | HyDE file omission, status mismatch, return type ambiguity, Task 4/5 overlap, CKS singleton |

**Overall Assessment:** The ADR's implementation table and 3 of its 5 bugs/tasks reference code that does not exist in the codebase. The core analysis of "what we already have" (the 10-row table) is largely accurate, but the "what's broken" section and the resulting implementation plan are built on unsubstantiated claims. The ADR should be revised to: (1) remove BUG-1 and BUG-2 or provide evidence they exist, (2) reframe Task 1 around actual code, (3) specify BackendStatus contract, and (4) follow the project ADR template.
