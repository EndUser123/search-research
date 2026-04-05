# Implementation Plan: think_trigger.py Validation Gap Fix

**Created:** 2026-03-08
**Status:** Ready for Implementation
**Last Updated:** 2026-03-08 (Applied 2 improvements from verification)
**Effort Estimate:** 3-4 hours (Phase 1: 15 min, Phase 2: 30-45 min, Phase 3: 2-3 hours)
**Architecture Decision:** P:/.claude/arch_decisions/2026-03-08_python_think-trigger-validation-gap-optimal-solution.md

---

## Problem Statement

The `think_trigger.py` module has a structural validation gap: it defines 7 profiles in pattern dictionaries (`_STRONG_PATTERNS`, `_WEAK_PATTERNS`) but only 4 templates in `_PROFILES`, causing runtime `KeyError: 'security_review'` when the hook detects security-related prompts.

**Root Cause:** No invariant enforcement ensures pattern definitions and template definitions stay aligned.

**Impact:** User-facing hook errors with unclear error messages, dormant until specific keywords trigger missing profiles.

---

## Context Analysis

**Current State:**
- Module: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Three separate dictionaries with 200+ line separation:
  - `_STRONG_PATTERNS` (lines 46-124): 7 profiles
  - `_WEAK_PATTERNS` (lines 127-198): 7 profiles
  - `_PROFILES` (lines 260-321): 4 profiles (missing 3)
- Detection logic (line 332): `template = _PROFILES[profile]` → KeyError if profile missing

**Recently Fixed:**
- Added missing templates for `security_review`, `performance_analysis`, `multi_file_refactor`
- Cleared Python bytecode cache

**Remaining Gap:** No validation prevents this from recurring when new profiles are added.

**Environment:**
- Python 3.12+
- Hook system: subprocess execution with JSON I/O
- Test infrastructure: pytest, `comprehensive_hook_health_check.py`
- CI/CD integration (assumed)

---

## Existing Implementation Discovery

**Files Involved:**

1. **P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py**
   - Current size: 334 lines
   - Pattern detection: Lines 46-198
   - Template definitions: Lines 260-321
   - Hook function: `think_trigger()` at line 325
   - **Insertion point for invariant check:** After line 321 (after `_PROFILES` closes)

2. **P:/.claude/hooks/comprehensive_hook_health_check.py**
   - Current structure: Tests hooks with synthetic payloads
   - Tests: UserPromptSubmit, PreToolUse, PostToolUse, Stop
   - **Gap:** Does not test all code paths through `think_trigger` (only default payload)
   - **Insertion point:** Add new test function alongside existing `test_hook()` function

3. **P:/.claude/hooks/UserPromptSubmit_modules/base.py**
   - Contains `HookResult` class
   - Required parameter: `tokens` (previous issue with stale cache)
   - **Reference:** Understand hook return format

**Dependencies:**
- No external packages required
- Standard library only: `dataclasses` (for Phase 3)
- Python 3.12+ features: `if __debug__`, `@dataclass(frozen=True)`, `|` union operator

**Integration Points:**
- Hook router: `UserPromptSubmit_router.py` (calls `think_trigger()`)
- Health check: Standalone script, can be run independently
- CI/CD: Unknown pipeline, assume health check runs before merge

---

## Test Discovery

**Existing Tests:**
- `comprehensive_hook_health_check.py` - Tests all 4 hooks with basic payloads
- Manual test script: `test_code_skill_activation.py` (tests UserPromptSubmit with /code payload)

**Test Coverage Gaps:**
1. No test verifies all 7 profile names exist in both patterns and templates
2. No test triggers `security_review`, `performance_analysis`, or `multi_file_refactor` detection
3. No test verifies import-time assertion behavior
4. No test verifies health check catches misalignment

**Test Strategy:**
- Unit test for invariant check (Phase 1)
- Integration test for health check (Phase 1)
- Manual verification test (Phase 2)
- Regression test suite for dataclass refactor (Phase 3)

---

## Proposed Solution

**Hybrid Approach: Immediate protection + long-term structural fix**

### Phase 1: Import-Time Assertions (Immediate)
Add module-level invariant check that runs on import, fails immediately if misaligned.

**Benefits:**
- Fails fast during development
- Zero production overhead (`if __debug__` optimized out with `-O`)
- Clear error message points to problem
- <10 lines of code

### Phase 2: Expanded Health Check (Complementary)
Add profile consistency test to `comprehensive_hook_health_check.py`.

**Benefits:**
- Catches misalignment in CI/CD
- Tests all code paths (not just default payload)
- Integrates with existing infrastructure

### Phase 3: Single-Source Dataclass (Long-term)
Refactor to `@dataclass(frozen=True)` pattern where each profile co-locates all data.

**Benefits:**
- Eliminates misalignment class of bug permanently
- Type-safe, immutable
- Self-documenting
- Compiler/IDE enforces completeness

---

## Implementation Plan

### Phase 1: Immediate Protection (15 minutes)

**T-001:** Add import-time invariant to think_trigger.py
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Action: Insert 9-line invariant check after line 321
- Acceptance Criteria:
  - Module imports successfully with current code
  - Removing a template from `_PROFILES` causes AssertionError on import
  - Error message includes: missing templates, missing patterns, profile counts
- Effort: S (5 minutes)

**T-002:** Add profile consistency test to health check
- File: `P:/.claude/hooks/comprehensive_hook_health_check.py`
- Action: Add `test_think_trigger_profile_consistency()` function
- Acceptance Criteria:
  - Function returns `{"status": "success"}` with current code
  - Function returns `{"status": "error"}` if profiles misaligned
  - Integrates into main test loop (called alongside other hook tests)
- Effort: S (10 minutes)

**T-003:** Verify health check integration
- File: `P:/.claude/hooks/comprehensive_hook_health_check.py`
- Action: Call new test function in `main()` test loop
- Acceptance Criteria:
  - Health check output includes "✓ PASS (exit 0)" for think_trigger profile test
  - Test appears in summary count
- Effort: S (2 minutes)

### Phase 2: Validation (30 minutes)

**T-004:** Test import-time assertion behavior
- Action: Manually remove a template from `_PROFILES`, attempt import
- Acceptance Criteria:
  - `python -c "from UserPromptSubmit_modules.think_trigger import _PROFILES"` raises AssertionError
  - Error message shows missing profile name
  - Restoring template allows import to succeed
- Effort: S (5 minutes)

**T-005:** Verify health check detects misalignment
- Action: Run `comprehensive_hook_health_check.py` with broken code
- Acceptance Criteria:
  - Status shows "✗ FAIL" for think_trigger profile test
  - Error message includes mismatch details
  - Fixing misalignment makes test pass
- Effort: S (5 minutes)

**T-006:** Clear Python bytecode cache
- Action: Run `rm -rf P:/.claude/hooks/UserPromptSubmit_modules/__pycache__`
- Acceptance Criteria:
  - No `.pyc` files remain in directory
  - Import behavior reflects code changes immediately
- Effort: S (1 minute)

**T-007:** Document invariant check in CLAUDE.md
- File: `P:/.claude/hooks/CLAUDE.md`
- Action: Add section "Invariant Validation Pattern" with example
- Acceptance Criteria:
  - Section explains `if __debug__` pattern for cross-structure validation
  - Example shows think_trigger.py usage
  - Links to Python assertion documentation
- Effort: M (10 minutes)

**T-008:** Verify CI/CD integration (INVESTIGATIONAL)
- Type: Investigative task (CI/CD system unknown)
- Action: Confirm health check runs in CI/CD pipeline before merge
- Investigation Steps:
  1. Identify CI/CD system (GitHub Actions, Jenkins, GitLab CI, etc.)
  2. Locate pipeline configuration files
  3. Verify health check script is called before merge
  4. If not integrated, add manual gate or integrate into pipeline
- Acceptance Criteria:
  - CI/CD system identified
  - Health check integration status confirmed (integrated, needs integration, or manual process)
  - If not integrated: Document manual verification step or create integration task
- Effort: M (15-30 minutes, depends on CI/CD complexity)
- **Dependency:** Unknown CI/CD system - investigation required

### Phase 3: Structural Refactor (2-3 hours, Next Sprint)

**T-009:** Create ThinkProfile dataclass
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Action: Define `@dataclass(frozen=True) class ThinkProfile`
- Code: `from dataclasses import dataclass`
- Acceptance Criteria:
  - Fields: `name: str`, `template: str`, `strong_patterns: list[str]`, `weak_patterns: list[str] | None`
  - Class is immutable (`frozen=True`)
  - Docstring explains single-source purpose
  - Import statement added at module level: `from dataclasses import dataclass`
- Effort: M (15 minutes)

**T-010:** Migrate all 7 profiles to dataclass format
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Action: Create `_THINK_PROFILES: dict[str, ThinkProfile]` with all profiles
- Acceptance Criteria:
  - All 7 profiles co-located (debug_rca, tradeoff_decision, architecture, pre_commit_risk, security_review, performance_analysis, multi_file_refactor)
  - Each profile has: name, template (full content), strong_patterns, weak_patterns
  - No profile data separated across different dictionaries
- Effort: L (60 minutes)

**T-011:** Derive existing dictionaries from single source
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Action: Derive `_PROFILES`, `_STRONG_PATTERNS`, `_WEAK_PATTERNS` from `_THINK_PROFILES`
- Acceptance Criteria:
  - `_PROFILES = {name: p.template for name, p in _THINK_PROFILES.items()}`
  - `_STRONG_PATTERNS = {name: p.strong_patterns for name, p in _THINK_PROFILES.items()}`
  - `_WEAK_PATTERNS = {name: (p.weak_patterns or []) for name, p in _THINK_PROFILES.items()}`
  - All existing code continues to work (no API changes)
- Effort: S (15 minutes)

**T-012:** Remove import-time assertion (no longer needed)
- File: `P:/.claude/hooks/UserPromptSubmit_modules/think_trigger.py`
- Action: Delete invariant check added in T-001
- Acceptance Criteria:
  - Dataclass structure makes assertion redundant
  - Module still fails fast if profile incomplete (dataclass enforces)
- Effort: S (2 minutes)

**T-013:** Run full test suite
- Action: Execute `pytest P:/.claude/hooks/tests/ -v`
- Acceptance Criteria:
  - All existing tests pass
  - No regressions in hook behavior
  - Profile detection still works for all 7 profiles
- Effort: M (20 minutes)

**T-014:** Update health check test for new structure
- File: `P:/.claude/hooks/comprehensive_hook_health_check.py`
- Action: Modify `test_think_trigger_profile_consistency()` to check `_THINK_PROFILES` keys
- Acceptance Criteria:
  - Test verifies `_THINK_PROFILES` has all 7 profiles
  - Test verifies each profile has required fields (name, template, patterns)
- Effort: S (10 minutes)

**T-015:** Update CLAUDE.md documentation
- File: `P:/.claude/hooks/CLAUDE.md`
- Action: Document dataclass pattern as single-source best practice
- Acceptance Criteria:
  - Section explains ThinkProfile dataclass usage
  - Example shows how to add new profile
  - References think_trigger.py as canonical example
- Effort: M (15 minutes)

**T-016:** Git commit with descriptive message
- Action: Commit all Phase 3 changes
- Acceptance Criteria:
  - Commit message follows conventional commit format
  - Message references architecture decision document
  - All changes included in single commit
- Effort: S (5 minutes)

---

## Risks, Success Criteria, Dependencies

### Risks

1. **Import-time assertion not triggered** (LOW)
   - **Risk:** Team only tests hooks via subprocess, never imports directly
   - **Impact:** Bug survives until health check expansion deployed
   - **Mitigation:** Deploy Phase 1 and Phase 2 together (assertion + health check)

2. **CI/CD pipeline unknown** (MEDIUM)
   - **Risk:** Health check may not run automatically in CI/CD
   - **Impact:** Misalignment could reach production
   - **Mitigation:** Verify CI/CD integration in Phase 2 (T-008), add manual gate if needed

3. **Dataclass refactor complexity** (MEDIUM)
   - **Risk:** Large refactor (200+ lines) could introduce regressions
   - **Impact:** Hook behavior changes, new bugs introduced
   - **Mitigation:** Comprehensive testing in Phase 3 (T-013), rollback strategy

4. **Merge conflicts in Phase 3** (LOW)
   - **Risk:** Others modifying think_trigger.py during refactor
   - **Impact:** Rebase conflicts, lost changes
   - **Mitigation:** Coordinate with team, use feature branch, short refactor window

### Success Criteria

**Phase 1 Success:**
- Module fails to import with AssertionError if profiles misaligned
- Health check reports misalignment before merge
- Zero production overhead (optimized out with `-O`)

**Phase 2 Success:**
- All validation tests pass
- CI/CD integration verified
- Documentation complete

**Phase 3 Success:**
- All 7 profiles co-located in `_THINK_PROFILES` dataclass
- Existing dictionaries derived from single source
- Full test suite passes
- No regressions in hook behavior
- Adding new profile requires all fields (compiler-enforced)

### Dependencies

**Phase 1 Dependencies:**
- None (self-contained)

**Phase 2 Dependencies:**
- Phase 1 complete
- CI/CD pipeline access (for T-008)

**Phase 3 Dependencies:**
- Phase 2 complete
- Team coordination (minimize concurrent changes)
- Test environment available

### Rollback Strategy

**Phase 1 Rollback:**
- Git revert commit adding invariant check
- No data migration, no state changes

**Phase 2 Rollback:**
- Git revert commit adding health check test
- No impact to production code

**Phase 3 Rollback:**
- Git revert dataclass refactor commit
- Restore previous think_trigger.py from git history
- Verify hooks still work with reverted code

---

## Top Risks

1. **CI/CD pipeline unknown** - May not run health check automatically, requiring manual gate
2. **Dataclass refactor complexity** - 200+ line changes could introduce regressions
3. **Import-time assertion bypass** - Team workflow may not trigger assertion (subprocess-only testing)

---

## Next Actions

1. Execute T-001: Add import-time invariant to think_trigger.py
2. Execute T-002: Add profile consistency test to health check
3. Execute T-003: Verify health check integration
4. Execute T-006: Clear Python bytecode cache
5. Run comprehensive_hook_health_check.py to verify Phase 1 complete
6. Plan Phase 3 for next sprint (coordinate with team)

**Commands:**

```bash
# Phase 1: Execute immediately
cd P:/.claude/hooks
# T-001, T-002, T-003 implementation (manual edits)
# T-006: Clear cache
rm -rf UserPromptSubmit_modules/__pycache__
# Verify
python comprehensive_hook_health_check.py

# Phase 2: Validate (manual testing)
# T-004, T-005: Manual verification tests
# T-007: Document in CLAUDE.md
# T-008: Verify CI/CD (investigation required)

# Phase 3: Next sprint (team coordination)
# T-009 through T-016: Dataclass refactor
```

---

**Plan persisted as:** `P:/.claude/hooks/plans/plan-20260308-think-trigger-validation-fix.md`
