# Top Problems — 2026-04-02

**Window**: 3 days (since 2026-03-30) | **Sources**: 6 scanned | **Focus**: session_chain

---

## Evidence Summary

| Source | Findings |
|--------|----------|
| Pre-mortems (3-day window) | 2 files: `premortem_session_chain_20260331_203631.md`, `premortem_trace_bug_tot_tracer_20260401.md`, `premortem_violation_reporter_blocked_root_20260401.md` |
| Critiques | 1 session incomplete: `critique-20260402_083105/` (p1_findings.md never written — workflow incomplete) |
| Tasks | 632 tasks total, many blocked/in-progress multi-phase skills |
| Git | 8 commits since 2026-03-30 |
| Session errors | 0 errors in last 2 JSONL files |
| Auto-retries | 0 detected |

**Window note**: Expanded to include March 31 session_chain pre-mortem (one day outside 3-day window) — it covers the most recent major integration (commit f2eddb85b3).

---

## Vetoed Items

- **P-1 (depth > 1 heuristic)**: commit f2eddb85b3 replaced handoff_chain with unified session_chain — the specific line reference (session_chain.py:412) may no longer exist in the same form.
- **P-4 (sessions-index staleness)**: Origin tracking via `origin_session_id` added in f2eddb85b3 may partially address this.
- **IO-001 (case sensitivity boundary check)**: False positive — adversarial-logic verified that `str.lower()` preserves string length, so indexing after `.lower()` does NOT cause off-by-one errors. `normalized[len(exact_path)]` uses the already-lowercased `exact_path` length correctly.

---

## Cross-Source Dedup

| Problem | Sources | Root Cause |
|---------|---------|------------|
| Session chain incomplete integration | pre-mortem (P-1,P-4,P-8,P-11), tasks (#2600) | session_chain module replacing handoff_chain |
| Integration test coverage gap | pre-mortem (P-11) | No skill-path integration test |
| Fragile import via sys.path hack | pre-mortem (P-8), tasks (#2343) | Namespace package without __init__.py |
| Critique workflow incomplete | critique session not written | p1_findings.md never produced |

---

## Rankings

| # | Problem | Score | Impact | Fix | Sources | Confidence | Bucket | Fix Level | Trend |
|---|---------|-------|--------|-----|---------|-----------|--------|-------|--------|
| 1 | **session_chain P-11: No integration test for skill path** | 9.0 | 3 | 3 | premortem_session_chain:premortem_session_chain_20260331_203631.md:221,premortem_session_chain_20260331_203631.md:289 | [HIGH] | P2 | Band-Aid | new |
| 2 | **session_chain P-8: Fragile sys.path import hack (namespace package)** | 7.2 | 3 | 3 | premortem_session_chain_20260331_203631.md:86-87,tasks:#2343 | [HIGH] | P3 | Redesign | new |
| 3 | **Critique session incomplete: p1_findings.md never written** | 6.0 | 2 | 4 | critique-20260402_083105/ | [MED] | P3 | Local Optimum | new |
| 4 | **session_chain P-1: depth>1 fallback heuristic unverified** | 6.0 | 3 | 3 | premortem_session_chain_20260331_203631.md:65-66 | [MED] | P3 | Local Optimum | new |
| 5 | **session_chain P-4: sessions-index staleness returns empty chain** | 6.0 | 3 | 3 | premortem_session_chain_20260331_203631.md:74-75 | [MED] | P3 | Local Optimum | new |

### Scoring Notes

- P-11: `3 × 3 × 1.0 = 9.0` — cross-ref=1 (no diff available), impact=3 (specific workflow), fix=3 (2-3 files, clear path)
- P-8: `3 × 3 × 0.8 = 7.2` (P-8 appears in premortem + task #2343 = 2 sources)
- Others: `3 × 2 × 1.0 = 6.0` (single source each)

---

## Problem Cards

### P-1: session_chain P-11 — No Integration Test for Skill Path

**Score**: 9.0 | **Bucket**: P2 | **Confidence**: [HIGH]

**Evidence**: `premortem_session_chain_20260331_203631.md:221` — "27 tests pass, but all are unit tests. No integration test exercises: skill import → walk_session_chain → transcript parsing → output." | `premortem_session_chain_20260331_203631.md:289` — action item specifies: "Write a test that: creates a mock sessions-index + handoff structure, imports via the skill's sys.path mechanism, calls walk_session_chain, verifies correct entries returned."

**Impact**: Specific workflow — `/recap` and `/gto` depend on session_chain for historical context. If the integration breaks, neither skill works correctly, affecting every session that needs historical context.

**Fix**: Add `test_session_chain_integration.py` in `packages/search-research/tests/` that:
1. Creates a mock sessions-index + handoff file structure
2. Imports `session_chain` via the actual skill `sys.path` mechanism
3. Calls `walk_session_chain` with a known session ID
4. Verifies correct chain entries are returned

**Fix scope**: `packages/search-research/tests/test_session_chain_integration.py` (new file)

**Blocks**: P-1 (depth>1 heuristic), P-4 (sessions-index staleness) — integration tests would surface these

---

### P-2: session_chain P-8 — Fragile sys.path Import Hack

**Score**: 7.2 | **Bucket**: P3 | **Confidence**: [HIGH]

**Evidence**: `premortem_session_chain_20260331_203631.md:86-87` — "search-research package has no __init__.py, making it a namespace package. Import via sys.path.insert hack is fragile." | Task #2343 ("Migrate knowledge to search-research") was completed, suggesting csf/ migration happened, but namespace package structure may persist.

**Impact**: Specific workflow — if skills change their path computation (`parents[3]` vs `parents[2]`), the `sys.path.insert` points to wrong directory → silent import failure → `/recap` and `/gto` return empty chain.

**Fix Level**: **Redesign** — Add `__init__.py` to `packages/search-research/` converting namespace package to regular package. BUT: verify no other packages rely on namespace behavior first.

**Fix scope**: `packages/search-research/__init__.py` (new file) + verification across codebase

---

### P-3: Critique Session Incomplete — p1_findings.md Never Written

**Score**: 6.0 | **Bucket**: P3 | **Confidence**: [MED]**

**Evidence**: Session dir `critique-20260402_083105/` exists with `work.md` and `specialists/*.md` files, but no `p1_findings.md`, `p2.md`, or `p3.md`. The Phase 1 triage + dispatch was completed (4 specialists ran), Phase 2 meta-critique and Phase 3 synthesis were never executed.

**Impact**: Single hook edge case — the `is_allowed_external_path()` fix was reviewed by 4 adversarial specialists, but the cross-agent meta-critique (Phase 2) and synthesis (Phase 3) were never written, so there's no consolidated findings document. The fix itself was verified manually and by adversarial-logic (no issues found), but the formal critique workflow is incomplete.

**Fix Level**: **Local Optimum** — Write `p2.md` and `p3.md` to complete the critique session, then run skill coverage logging.

**Fix scope**: `P:/.claude/.evidence/critique/critique-20260402_083105/p2.md`, `p3.md`

---

### P-4: session_chain P-1 — depth>1 Fallback Heuristic Unverified

**Score**: 6.0 | **Bucket**: P3 | **Confidence**: [MED]**

**Evidence**: `premortem_session_chain_20260331_203631.md:65` — "depth > 1 heuristic in walk_session_chain (line 412) is wrong — a single-entry handoff chain looks identical to a full chain with one entry, so sessions-index fallback never fires for sessions that have no prior handoff files."

**Impact**: Specific workflow — `/recap` and `/gto` may silently return incomplete chains for sessions that genuinely have no prior sessions, indistinguishable from broken chains.

**Fix**: The heuristic needs to return a distinct marker for "definitely no prior" vs "single-entry chain", or always try sessions-index fallback for single-entry chains.

**Fix scope**: `packages/search-research/core/session_chain.py` (line ~412 in `walk_session_chain`)

---

### P-5: session_chain P-4 — sessions-index Staleness Returns Empty Chain

**Score**: 6.0 | **Bucket**: P3 | **Confidence**: [MED]**

**Evidence**: `premortem_session_chain_20260331_203631.md:74-75` — "session_id not in sessions in walk_sessions_index_chain (line 296) returns empty SessionChainResult() if sessions-index doesn't have an entry — even though the .jsonl file may exist on disk."

**Impact**: Specific workflow — common race: session created but sessions-index not yet updated → `/recap` and `/gto` return empty chain despite valid transcript on disk.

**Fix**: When `session_id not in sessions` but `Path(fullPath).exists()` → log warning and fall back to reading the file directly.

**Fix scope**: `packages/search-research/core/session_chain.py` (~line 296 in `walk_sessions_index_chain`)

---

## Directory Heat Map

```
packages/search-research/  ████░░░░░░  4 problems  (session_chain integration)
.claude/hooks/             █░░░░░░░░░  1 problem   (directory_policy fix review incomplete)
.claude/.evidence/         █░░░░░░░░░  1 problem   (critique workflow incomplete)
```

---

## Dependencies

```
P-1 (no integration tests) → blocks P-4, P-5 (integration tests would surface these)
P-2 (namespace package)    → blocks none directly
P-3 (critique incomplete)  → blocks critique skill coverage logging
```

---

## Vetoed

| Item | Reason |
|------|--------|
| IO-001 (case sensitivity boundary) | False positive — adversarial-logic confirmed lower() preserves length |
| P-1 (depth>1 heuristic) | May be partially fixed in commit f2eddb85b3; line reference is stale |
| P-4 (sessions-index staleness) | Partial mitigation via origin_session_id tracking in f2eddb85b3 |
| IO-002/IO-003/SEC-001 (lock timeout) | Deliberate fail-safe design choice; LOW severity; telemetry tracked |

---

## Quick Wins

- **P-3** (critique incomplete): `P-3` fix is a single skill workflow gap — write p2.md and p3.md to complete the session.
- **P-1** (P-11 integration tests): Write one integration test for session_chain + skill path.

## Suggested Commands

| Problem | Command |
|---------|---------|
| P-1 (P-11) | `Try: /task to create test_session_chain_integration.py` |
| P-2 | `Try: /plan to design namespace-package → regular-package migration` |
| P-3 | `Try: /task to write p2.md + p3.md for critique-20260402_083105` |
| P-4 | `Try: /plan to verify depth>1 heuristic empirically` |
| P-5 | `Try: /plan to add sessions-index staleness fallback` |
| Quality concern | `Try: /critique for adversarial review` |

---

*Run: `/top-problems --days 3 --diff` to compare with next run.*
