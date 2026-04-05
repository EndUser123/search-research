# RCA Anti-Patterns Research: Task #2625

## Problem Statement

Five RCA failure modes identified by user:
1. Overfits to first plausible explanation
2. Reasons from partial reads instead of tracing full execution path
3. Defends local consistency too long
4. Treats workaround as root-cause fix
5. Does not re-ground after codebase changes

## Gap Analysis

### AP1: Overfits to First Plausible Explanation
**Coverage:** Partial — `StopHook_overconfidence_detector.py` catches causal assertions without evidence, but no structural enforcement for hypothesis count.
**Gap:** No enforcement requiring ≥2 ranked alternatives before root cause can be named.

### AP2: Reasons from Partial Reads
**Coverage:** Partial — `StopHook_rca_contract.py` had marker-based dead-code detection ("0 callers" text required).
**Gap:** Automatic function-name scanning didn't exist; required explicit mention.

### AP3: Defends Local Consistency Too Long
**Coverage:** Zero — No band-aid chain detector exists.
**Gap:** Repeated patches to same file aren't flagged as XY-SUSPECT.

### AP4: Treats Workaround as Root-Cause Fix
**Coverage:** Partial — `Stop_lazy_workaround_gate.py` detected accept-as-feature patterns only.
**Gap:** try/except suppression, timeout reduction, skip/bypass logic not covered.

### AP5: Does Not Re-ground After Codebase Changes
**Coverage:** Zero — No git freshness validation.
**Gap:** RCA conclusions stale when codebase mutates underneath.

## Implemented Fixes

### AP1: Hypothesis Density Enforcement
**File:** `StopHook_rca_contract.py`
**Added:** `_count_hypothesis_rows()` — parses markdown table rows with scores
**Added:** `BLOCK_REASONS["single-hypothesis-lock"]` — blocks when <2 ranked hypotheses
**Check:** Before Field 4 (Root Cause), if `root_cause` present with `alternative`, requires `hypo_count >= 2`

### AP2: Automatic Dead-Code + Call-Site Evidence
**File:** `StopHook_rca_contract.py`
**Replaced:** `_check_dead_code()` (marker-based) with `_check_dead_code_auto()` (scans ALL function names in Executed Path)
**Added:** `_has_call_site_evidence()` — checks Evidence shows grep/caller patterns for Executed Path functions
**Added:** `BLOCK_REASONS["no-call-site-evidence"]` and `["auto-dead-code"]`
**Check:** Field 3 (Executed Path) — if function names present without call-site evidence, block
**Check:** Field 6 (Root Cause) — if any function in Executed Path has 0 callers, block

### AP4: Lazy Workaround Pattern Expansion
**File:** `Stop_lazy_workaround_gate.py`
**Added 8 patterns:**
- try/except error suppression: `added try*/except to suppress`, `wrapped in try*/except to hide`, `catch the exception and ignore`, `except: pass`
- timeout reduction: `reduced timeout to N`, `shortened timeout`
- skip/bypass logic: `skip the check/validation`, `bypass the check/validation`

## Test Coverage

**File:** `tests/test_StopHook_rca_contract.py`
- `TestCheckDeadCodeAuto`: 4 tests for automatic dead-code detection
- `TestCountHypothesisRows`: 5 tests for hypothesis density parsing
- `TestHasCallSiteEvidence`: 6 tests for call-site proof enforcement
- `TestBareExceptBinding`: 3 tests for P1-1 (pre-existing)

Total: 18 tests, all passing.

## Remaining Work (Not Implemented)

### AP3: Band-Aid Chain Detector
- Would need to track file paths mentioned across multiple RCA turns
- Flag when ≥3 patches target same file as XY-SUSPECT
- Requires cross-turn state (session-scoped)

### AP5: Git Freshness Validator
- Would need to compare RCA timestamp against file modification times
- Block when executed_path references files modified after RCA was written
- Requires git integration or filesystem stat

## Files Modified

| File | Change |
|------|--------|
| `StopHook_rca_contract.py` | Added `_count_hypothesis_rows`, `_check_dead_code_auto`, `_has_call_site_evidence` + 3 block reasons + 2 structural checks |
| `Stop_lazy_workaround_gate.py` | Added 8 anti-pattern-4 patterns |
| `tests/test_StopHook_rca_contract.py` | Added 11 new tests (3 classes) |

## Evidence

- pytest output: 18 passed in 0.26s
- All 3 new detection functions have test coverage
- Pattern expansion covers 8 new workaround forms
