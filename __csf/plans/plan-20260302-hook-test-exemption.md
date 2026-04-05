# Implementation Plan: Hook Test File Exemption

**Created:** 2026-03-02
**Status:** READY-FOR-IMPLEMENTATION
**Priority:** HIGH

## 1. Overview

Fix hook architecture to allow test file creation in logical locations (`tests/`, `test/`) without blocking, while maintaining safety guarantees for non-test operations. Also add configurability to Tier 1 advisories.

## 2. Architecture

### Components

**A. Test Detection Module** (`__lib/test_detection.py`)
- Pytest-based discovery using `pytest.collect` API
- Caches discovered test files for performance
- Detects: `tests/`, `test/`, and module-specific test directories

**B. Hook Integration** (3 hooks)
- `recursive_failure_detector.py` - Add test exemption check
- `PreToolUse_require_plan_for_features.py` - Add test exemption check
- `PreToolUse_git_safety.py` - Add test exemption check

**C. Advisory Configuration** (`PreToolUse_risk_tier_gate.py`)
- Add `ADVISORY_SHOW_MODE` environment variable support
- Modes: `once` (default), `always`, `never`

**D. Documentation** (`CLAUDE.md`)
- Add "Test File Exemption Philosophy" section

### Data Flow

```
Hook receives Write/Edit operation
    ↓
Call is_test_file_operation(file_path)
    ↓
Check cache → hit? → return True/False
    ↓
Cache miss? → pytest.collect([file_path])
    ↓
Update cache
    ↓
Return True/False
```

## 3. Error Handling

**pytest import failure:**
- Graceful degradation to regex pattern matching
- Log warning to stderr (hook context, not user-visible)
- Continue operation (fail-open for test detection)

**pytest.collect failure:**
- Catch exception, return False (not a test file)
- Log error for diagnosis
- Don't block the operation

**Cache corruption:**
- Clear cache and rebuild on exception
- TTL: 5 minutes (stale test discovery acceptable)

## 4. Test Strategy

### Unit Tests
- Test `is_test_file_operation()` with various file paths
- Test cache hit/miss behavior
- Test pytest import failure handling
- Test `ADVISORY_SHOW_MODE` configuration parsing

### Integration Tests
- Create test file in `tests/` → should succeed
- Create test file in `src/` → should block (not test location)
- Tier 1 advisory with `ADVISORY_SHOW_MODE=never` → no output
- Tier 1 advisory with `ADVISORY_SHOW_MODE=once` → shows once

### Edge Cases
- `conftest.py` in subdirectories
- Test files with non-standard names (e.g., `test.py`)
- Symbolic links to test directories
- Pytest not installed (graceful degradation)

## 5. Standards Compliance

**Python 3.14+ Standards:**
- Type hints for all function signatures
- `try-except` for all external dependencies (pytest)
- Use `functools.lru_cache` for caching
- Environment variable access via `os.environ.get()`
- Logging via `logging` module (not print)

**Universal Principles:**
- DRY: Single `test_detection.py` module, not duplicated logic
- Separation of Concerns: Hooks call detection, don't implement it
- Fail-Open: Test detection failures don't block operations

## 6. Ramifications

### Breaking Changes
- None (purely additive)

### Backwards Compatibility
- Existing hooks continue to work without changes
- Test detection is opt-in via hook calls
- `ADVISORY_SHOW_MODE` defaults to current behavior (`once`)

### Performance Impact
- Cache hit: < 1ms (dict lookup)
- Cache miss: ~50-100ms (pytest.collect)
- Cold start: ~100ms for first test file detection
- Net impact: Negligible (caching eliminates repeated work)

### Migration Path
- No migration needed (additive feature)
- Hooks can adopt test detection incrementally

## 7. Pre-Mortem Analysis

### Failure Mode 1: Pytest API Changes
**Risk:** MEDIUM
**Scenario:** pytest changes `pytest.collect` API in future version
**Prevention:** Wrap pytest in try-except, fallback to regex patterns
**Detection:** Unit tests with pytest mocking
**Observability:** Log pytest import/call failures

### Failure Mode 2: Cache Staleness
**Risk:** LOW
**Scenario:** Test file deleted but cache says it's a test
**Impact:** False positive (allows test file creation where it shouldn't)
**Prevention:** 5-minute TTL, cache rebuild on exception
**Detection:** Integration test creates then deletes test file

### Failure Mode 3: Symbolic Link Loops
**Risk:** LOW
**Scenario:** Symlink creates infinite loop in pytest.collect
**Impact:** Hook hangs on cache miss
**Prevention:** 1-second timeout on pytest.collect
**Detection:** Timeout test with symlink loops

### Failure Mode 4: Advisory Configuration Confusion
**Risk:** LOW
**Scenario:** Users set `ADVISORY_SHOW_MODE` but forget it
**Impact:** Advisories silently suppressed
**Prevention:** Log mode on startup, document in settings.json template
**Detection:** Manual testing with different modes

### Failure Mode 5: Test Detection Too Broad
**Risk:** MEDIUM
**Scenario:** `is_test_file_operation()` returns True for non-test files
**Impact:** Safety checks bypassed incorrectly
**Prevention:** Conservative pytest patterns, validation tests
**Detection:** Negative tests (non-test files should return False)

## 8. Implementation Tasks

### Task 1: Create Test Detection Module
**File:** `__lib/test_detection.py`
**Acceptance:**
- `is_test_file_operation(file_path: str) -> bool`
- Uses pytest.collect when available
- Falls back to regex patterns
- Caching with TTL
- Type hints throughout

### Task 2: Integrate into recursive_failure_detector.py
**File:** `recursive_failure_detector.py`
**Changes:** Add early return if `is_test_file_operation()` returns True
**Acceptance:**
- Test file operations not blocked
- Non-test operations still checked for Catch-22

### Task 3: Integrate into require_plan_for_features.py
**File:** `PreToolUse_require_plan_for_features.py`
**Changes:** Add early return if `is_test_file_operation()` returns True
**Acceptance:**
- Test file operations allowed without plan
- Non-test features still require plan

### Task 4: Integrate into git_safety.py
**File:** `PreToolUse_git_safety.py`
**Changes:** Add early return if `is_test_file_operation()` returns True
**Acceptance:**
- Test file writes to git-tracked dirs allowed
- Non-test files still checked

### Task 5: Add Advisory Configuration
**File:** `PreToolUse_risk_tier_gate.py`
**Changes:**
- Read `ADVISORY_SHOW_MODE` from environment
- Implement `once` mode (track shown advisories per session)
- Implement `always` mode (current behavior)
- Implement `never` mode (suppress all advisories)
**Acceptance:**
- `ADVISORY_SHOW_MODE=never` suppresses output
- `ADVISORY_SHOW_MODE=always` always shows
- `ADVISORY_SHOW_MODE=once` shows once per advisory

### Task 6: Document Exemption Philosophy
**File:** `CLAUDE.md`
**Changes:** Add "Test File Exemption Philosophy" section
**Content:**
- Why test files are exempt
- Which hooks respect exemption
- How to add exemption to new hooks
**Acceptance:**
- Clear rationale documented
- Integration instructions provided
- Examples shown

### Task 7: Write Tests
**File:** `tests/test_test_detection.py`
**Coverage:**
- Unit tests for `is_test_file_operation()`
- Integration tests for each hook
- Edge cases (symlinks, missing pytest, cache)
**Acceptance:**
- All tests pass
- Coverage > 80%

### Task 8: Run Full Test Suite
**Command:** `pytest tests/ -v`
**Acceptance:**
- All existing tests pass
- New tests pass
- No regressions

### Task 9: Static Analysis
**Tools:** ruff, mypy
**Acceptance:**
- No ruff errors
- No mypy errors
- Code follows project standards

### Task 10: TRACE Verification
**Method:** `/trace code:__lib/test_detection.py` and modified hooks
**Scenarios:**
- Happy path: Test file detected correctly
- Error path: pytest import fails, graceful degradation
- Edge case: Symlink loop timeout
**Acceptance:**
- 0 logic errors
- 0 resource leaks
- All scenarios traced

---

**Total Estimated Time:** 60-90 minutes
**Risk Level:** LOW (additive changes, graceful degradation)
**Confidence:** HIGH (pytest API stable, pattern well-understood)
