# Implementation Plan: Fix P2 Review Findings

## Overview

Fix 8 code quality findings from P2 review to improve error handling, maintainability, and style compliance. This is a targeted improvement task for the `/p` skill infrastructure.

## Architecture

**Module scope:**
- `hooks/validate_p_phase_order.py` - Add error handling (P1-001)
- `lib/file_utils.py` - Improve temp cleanup (P1-002), add type hints (P3-002)
- `lib/evidence_patterns.py` - NEW: Extract shared patterns (P2-001)
- `tests/test_file_utils.py` - Add symlink tests (P2-003)
- `tests/test_validate_p_phase_order.py` - Add marker integrity tests (P2-004)

**No external dependencies** - uses only stdlib

## Data Flow

```
Fix Task 1 (P1-001)
  validate_p_phase_order.py → JSON parse error → deny request
                                              ↓
                                          Tests verify deny on error

Fix Task 2 (P1-002)
  file_utils.py → atomic_write → temp cleanup fails → log + retry
                                                ↓
                                          Tests verify retry logic

Fix Task 3-8 (P2/P3 findings)
  Extract shared module, add tests, standardize formatting
```

## Error Handling

**P1-001:** Wrap `json.loads()` in try/except
- On `JSONDecodeError`: return `{"continue": False}` with error message
- Log to stderr for debugging

**P1-002:** Improve temp cleanup in `atomic_write`
- First attempt: try to unlink
- On failure: log warning, retry once
- On second failure: log error, continue (non-blocking)

## Test Strategy

**Unit tests per fix:**
1. P1-001: Test malformed JSON input returns deny
2. P1-002: Test temp cleanup retry on locked file
3. P2-003: Test atomic_write with symlink targets
4. P2-004: Test marker validation with corrupted/empty markers

**Regression tests:**
- Run all 42 existing tests after each fix
- Verify no functionality breaks

**Edge cases:**
- Empty JSON input
- Locked temp files (Windows file locking)
- Circular symlinks
- Zero-byte marker files

## Standards Compliance

**Python 2025+ standards:**
- Type hints on all public functions
- Explicit error handling (no bare `except:`)
- Logging via stdlib `logging` module
- pytest for testing
- f-strings for formatting

## Ramifications

**Impact on existing code:** None - all changes are additive

**Breaking changes:** None - all fixes are backward compatible

**Risk assessment:** LOW
- Well-defined fixes with clear success criteria
- Comprehensive test coverage
- No architectural changes

## Pre-Mortem Analysis

**Potential failure modes (6 months from now):**

1. **Failure Mode:** Temp file accumulation on Windows due to file locking issues
   - **Root cause:** `os.unlink()` fails on locked files, retry logic insufficient
   - **Preventive action:** Max 3 retries with exponential backoff, log cumulative failures
   - **TRACE scenario:** Test with locked file (open handle in another process)

2. **Failure Mode:** Tests pass but production hook still crashes on malformed JSON
   - **Root cause:** Test mock doesn't match real stdin input format
   - **Preventive action:** Integration test with actual JSON via stdin
   - **TRACE scenario:** Manual test with `echo '{}' | python hook.py`

3. **Failure Mode:** Marker validation too strict, rejects valid markers
   - **Root cause:** Content validation assumes specific format that changes
   - **Preventive action:** Validate only prefix, not full content
   - **TRACE scenario:** Test with marker created by P1 phase

## Task List

### Task 1: Fix P1-001 - Add JSON error handling
- [ ] Wrap `json.loads()` in try/except in `validate_p_phase_order.py:42`
- [ ] Return deny on `JSONDecodeError`
- [ ] Add test for malformed JSON input
- [ ] Verify hook denies bad input

### Task 2: Fix P1-002 - Improve temp cleanup
- [ ] Replace `except OSError: pass` with retry logic
- [ ] Add logging for cleanup failures
- [ ] Add test for temp cleanup retry
- [ ] Verify retry logic works

### Task 3: Fix P2-001 - Extract evidence patterns (VERIFY FIRST)
- [ ] **Check if Stop hooks actually exist** (finding may be false positive)
- [ ] If they exist: Extract to `lib/evidence_patterns.py`
- [ ] Update both Stop hooks to import from shared module
- [ ] Test that patterns still work

### Task 4: Fix P2-002 - Replace magic number
- [ ] Find magic number `[┌├└│┐┤┘─┬┴┼]{10,}` in halt validator
- [ ] Extract to `MIN_BOX_DRAWING_CHARS = 10` constant
- [ ] Add docstring explaining threshold
- [ ] Test that validation still works

### Task 5: Fix P2-003 - Add symlink tests
- [ ] Add `TestAtomicWriteSymlinks` class to `test_file_utils.py`
- [ ] Test symlink target behavior
- [ ] Test circular symlink handling
- [ ] Verify atomicity guarantees

### Task 6: Fix P2-004 - Add marker integrity checks
- [ ] Update `marker_exists()` to validate content
- [ ] Check marker has expected prefix ("Phase X complete")
- [ ] Add test for corrupted marker files
- [ ] Test empty marker rejection

### Task 7: Fix P3-001 - Standardize error messages
- [ ] Audit all phase files for error message format
- [ ] Standardize to markdown header format: `## Status:`
- - [ ] Update inconsistent messages

### Task 8: Fix P3-002 - Add type hints
- [ ] Add `-> None` return type to `atomic_write()`
- [ ] Add `-> str` return type to `sha256sum_file()`
- [ ] Add `-> Dict[str, float]` return type to `get_file_mtime_snapshot()`
- [ ] Run mypy to verify

### Final verification
- [ ] Run all 42 existing tests
- [ ] Run all new tests
- [ ] Run mypy type checking
- [ ] Manual TRACE of critical fixes (P1 findings)

## Execution Order

**Priority sequence (blocking → non-blocking):**
1. Task 1 (P1-001) - CRITICAL error handling
2. Task 2 (P1-002) - CRITICAL error handling
3. Task 3 (P2-001) - VERIFY first, may be N/A
4. Task 4 (P2-002) - HIGH maintainability
5. Task 5 (P2-003) - MEDIUM test coverage
6. Task 6 (P2-004) - MEDIUM validation
7. Task 7 (P3-001) - LOW style
8. Task 8 (P3-002) - LOW type safety

**TDD discipline:** Each task follows RED → GREEN → REFACTOR cycle

## Exit Criteria

Phase is complete when:
- [ ] All 8 findings fixed with tests
- [ ] All 42 existing tests pass
- [ ] New tests pass
- [ ] mypy validation passes (no type errors)
- [ ] Manual TRACE of P1 fixes complete
