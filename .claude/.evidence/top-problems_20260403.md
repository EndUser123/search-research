# Top Problems — 2026-04-03 (Session Update)

**Window**: Today (2026-04-03) | **Sources**: 6 scanned | **Focus**: session-chain from 2026-04-02 → 2026-04-03

---

## Evidence Summary

| Source | Findings |
|--------|---------|
| Pre-mortems (2-day window) | 3 files: `premortem_gto_project_root_removal_20260402.md`, `premortem_trace_bug_tot_tracer_20260401.md`, `premortem_violation_reporter_blocked_root_20260401.md` |
| Critiques | 2 new: `critique-20260403_102221` (HIGH: COMP-001/002/003, QUAL-001), `critique-20260402_143746` (HIGH: path mismatches, Step 8a gate bypass) |
| Tasks | 632 total — unchanged from yesterday |
| Git | skill-guard commits since Apr 2: frontmatter validation fixes (R1/R2/R3), test rewrites |
| Session errors | 0 errors, 0 retries in last session |
| Previous top-problems | 2026-04-03: P1=TOCTOU/sessions.json, P1=terminal_id divergence, P2=critique incomplete, P2=no session_chain integration test |

---

## Vetoed Items

- **RNS Blocking Steps R1/R2/R3 (skill_guard frontmatter)** — Implemented this session. R1 adds Stop hook consumer for `frontmatter_warnings`, R2 fixes path mismatch in `_validate_skill_frontmatter`, R3 documents early-return gate logic. Evidence: `skill_execution_state.py:241,360-368,886-920`

---

## Cross-Source Dedup

| Problem | Sources | Root Cause |
|---------|---------|-----------|
| **skill_guard test suite: 10 pre-existing failures from /arch skill evolution** | test_workflow_steps_parsing.py, test_arch_skill.py | Tests assert old `/arch` stage list; skill added `contract_sensitivity_classification`, `contract_boundary_inventory`, `contract_boundary_closure`, `emit_contract_authority_packet`, `adr_closure_consistency_check`, `adr_critic_review` since v3.4 |
| **Smoke tests require hooks runtime but run outside Claude Code** | test_skill_execution_state.py, test_StopHook_skill_execution_gate.py | Both import modules that depend on `__lib.hook_base` which is only available inside Claude Code hooks context. Were silently passing by resolving to wrong version. |

---

## Rankings

| # | Problem | Score | Impact | Fix | Sources | Confidence | Bucket | Fix Level |
|---|---------|-------|--------|-----|---------|-----------|--------|----------|
| 1 | **skill_guard: 10 arch-related tests fail (test assertions vs /arch skill drift)** | 12.0 | 4 | 2 | test_workflow_steps_parsing.py, test_arch_skill.py | [HIGH] | P1 | Local Optimum |
| 2 | **/critique: Step 8a confirmation gate bypasses user pause** | 9.0 | 3 | 3 | critique-20260402_143746:HIGH:QUAL-003 | [HIGH] | P2 | Band-Aid |
| 3 | **/critique: `_append_skill_coverage` called with wrong arg signature** | 9.0 | 3 | 3 | critique-20260403_102221:HIGH:COMP-002 | [HIGH] | P2 | Band-Aid |
| 4 | ~~sessions.json TOCTOU~~ ✅ RESOLVED | — | — | — | (see card) | — | — | — |
| 5 | ~~terminal_id divergence~~ ✅ RESOLVED | — | — | — | (see card) | — | — | — |
| 6 | ~~GTO silent cwd fallback~~ ✅ RESOLVED | — | — | — | (see card) | — | — | — |

---

## Problem Cards

### P1-1 — skill_guard: 10 arch-related tests fail (NEW this session)

- **Score**: 12.0 (4×3×1.0 — 1 source, direct evidence)
- **Evidence**: `test_workflow_steps_parsing.py` — test asserts `['preflight_checks', 'classify_intent', 'select_template', ...]` but `/arch` skill now includes `contract_sensitivity_classification`, `contract_boundary_inventory`, `contract_boundary_closure`, `emit_contract_authority_packet`, `adr_closure_consistency_check`, `adr_critic_review` between `classify_intent` and `select_template`
- **Evidence**: `test_arch_skill.py` — similar stage ordering assertion mismatch
- **Impact**: Every `pytest` run in skill_guard shows 10 failures. Blocks CI if added. Masks real regressions.
- **Fix**: Update test assertions to match current `/arch` SKILL.md stage list. `Try: /plan to update test expectations`
- **Confidence**: [HIGH] — Direct test output evidence
- **Fix Level**: Local Optimum — update assertions to match current skill definition
- **Conflicts**: None
- **Trend**: NEW this session

### P1-2 — sessions.json TOCTOU Race Condition ~~(from yesterday, unchanged)~~ ✅ FIXED 2026-04-03

- **Score**: 13.5 (3×3×1.5 — 3 sources)
- **Evidence**: `critique_iso.md:77` — `os.replace()` not atomic on Windows; concurrent `_save_registry` corrupts sessions.json
- **Fix Applied**: `_save_registry()` now wraps read-modify-write in `fcntl.LOCK_EX` / `msvcrt.LK_NBLCK` file lock. TOCTOU window eliminated.
- **Files Changed**: `P:\.claude\skills\critique\lib\critique_io.py`
- **Bucket**: P1 | **Fix Level**: Redesign
- **Trend**: ✅ RESOLVED

### P1-3 — terminal_id Algorithm Divergence ~~(from yesterday, unchanged)~~ ✅ FIXED 2026-04-03

- **Score**: 10.8 (3×3×1.2 — 2 sources)
- **Evidence**: `critique_iso:78`, `gto:RISK-T3`, `gto_orchestrator.py:164`, `state_manager.py:113-129`
- **Fix Applied**: `critique_io._get_terminal_id()` fallback now uses `hostname-pid` format matching `state_manager._resolve_terminal_id()`. Algorithm divergence eliminated.
- **Files Changed**: `P:\.claude\skills\critique\lib\critique_io.py`
- **Bucket**: P1 | **Fix Level**: Redesign
- **Trend**: ✅ RESOLVED

### P2-1 — /critique Step 8a Confirmation Gate Bypass ~~(unchanged)~~ ✅ FIXED 2026-04-03

- **Score**: 9.0 (3×3×1.0 — 1 source)
- **Evidence**: `critique-20260402_143746:HIGH:QUAL-003` — "Step 8a confirmation gate text says it 'requires acknowledgment' but implementation does not pause. The '0 — Do ALL' directive auto-executes without user confirmation."
- **Impact**: User's "0" directive auto-executes without pause, violating stated gate contract
- **Fix**: Add explicit `AskUserQuestion` or confirm directive that PAUSES before any file modification
- **Confidence**: [HIGH] — adversarial-quality specialist finding
- **Fix Level**: Band-Aid — gate text describes blocking but doesn't implement it
- **Trend**: NEW this session

### P2-2 — /critique `_append_skill_coverage` Wrong Arg Signature ~~(unchanged)~~ ✅ FIXED 2026-04-03

- **Score**: 9.0 (3×3×1.0 — 1 source)
- **Evidence**: `critique-20260403_102221:HIGH:COMP-002` — called with 5 positional args but `project_root` is keyword-only. Import error silently caught by bare `except Exception`, skill coverage never logged.
- **Confidence**: [HIGH]
- **Fix Level**: Band-Aid
- **Trend**: NEW this session

### P2-3 — GTO Auto-Detection Silent CWD Fallback ~~(unchanged)~~ ✅ FIXED 2026-04-03

- **Score**: 9.0 (3×3×1.0 — 1 source)
- **Evidence**: `gto:RISK-T1`
- **Bucket**: P2 | **Fix Level**: Local Optimum
- **Trend**: UNCHANGED

---

## Hardening / Follow-Up (from yesterday, unchanged)

| # | Problem | Score | Impact | Fix | Bucket |
|---|---------|-------|--------|-----|--------|
| H1 | Cleanup removes active session (mtime-based, no active flag) | 6.0 | 3 | 2 | P3 |
| H2 | Fix HyDE layer in search-research skill | 6.0 | 3 | 3 | P3 |
| H3 | Critique produces no p1_findings.md (workflow incomplete) | 4.5 | 2 | 4 | P3 |

---

## Quick Wins This Session

| Fix | Impact | Evidence |
|-----|--------|---------|
| R1: Stop hook consumer for `frontmatter_warnings` | Enables warning display | `StopHook_skill_execution_gate.py:887-921` |
| R2: `_validate_skill_frontmatter` path fixed | Aligns with `_load_skill_frontmatter` | `skill_execution_state.py:241` |
| R3: Early-return gate documented | Explains non-empty warnings prevent suppression | `skill_execution_state.py:360-368` |
| Frontmatter validation tests | **11 passed** in 0.85s | pytest `test_frontmatter_validation.py` |
| Full test suite | **302 collected**: 290 passed, 2 skipped, 10 pre-existing failures | pytest `tests/` |

---

## Summary

| Metric | Value |
|--------|-------|
| P1 | 3 (2 unchanged from yesterday + 1 NEW: arch-test drift) |
| P2 | 4 (1 unchanged + 2 NEW: critique gate bypass + skill_coverage sig + 1 unchanged) |
| P3 | 3 (unchanged) |
| Vetoed | 1 (RNS R1/R2/R3 — implemented) |
| Quick wins | 3 |
| New this session | 3 (arch-test drift, critique gate bypass, skill_coverage sig) |

---

## Suggested Commands

| Problem | Command |
|---------|---------|
| P1-1 (arch-test drift) | `Try: /plan — update test assertions for /arch stage list` |
| P1-2 (sessions.json TOCTOU) | `Try: /pre-mortem` for sessions.json redesign |
| P1-3 (terminal_id divergence) | `Try: /arch — unify terminal_id algorithm` |
| P2-1 (critique gate bypass) | `Try: /plan — add explicit pause to Step 8a` |
| P2-2 (skill_coverage sig) | `Try: /plan — fix append_skill_coverage call` |
| P2-3 (GTO cwd fallback) | `Try: /arch — add target validity check` |
