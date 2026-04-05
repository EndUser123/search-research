# Implementation Plan: Fix PostToolUse Hook Errors Using Python Logging Framework

**Created:** 2026-03-06
**Status:** DRAFT
**Author:** Claude Code (plan-workflow build mode)

---

## 1. Problem Statement

**PostToolUse hook writes to stderr in exception handler, triggering false "hook error" messages**

- **Current Behavior**: PostToolUse.py line 180 uses `print(f"PostToolUse Logging Error: {e}", file=sys.stderr)` in exception handler
- **User Impact**: Claude Code displays "PostToolUse:Bash hook error" after `rm -rf` and search operations, even when operations succeed
- **Root Cause**: Claude Code treats ANY stderr output from hooks as "hook error" (documented in HOOK_STDERR_STYLE_GUIDE.md)
- **Scope**: Single exception handler in PostToolUse.py lines 179-180

**Success Criteria:**
- ✅ No "PostToolUse:Bash hook error" messages appear after successful operations
- ✅ Diagnostic capability preserved for debugging (errors logged but not shown to user)
- ✅ Evidence logging failures are silent (best-effort system should not add noise)

---

## 2. Context Analysis

**Allowed APIs** (from documentation discovery):
- `logging.getLogger(__name__)` ✅ - Module-level logger
- `logger.debug()` ✅ - Debug-level logging (not visible in production)
- `logging.NullHandler()` ✅ - Prevents any stderr output from logging
- `logger.exception()` ✅ - Automatic traceback logging in exception handlers

**Existing Codebase Patterns** (17 files examined in `P:\.claude\hooks\`):

**Pattern A: NullHandler for Hooks** (RECOMMENDED - matches use case):
```python
# From SessionStart_folder_context.py
import logging

logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
```

**Exception Handling Patterns** (5 variations found):
- Pattern 1: Silent failure with `pass` (state operations)
- Pattern 2: `logger.debug()` for transient errors (non-critical)
- Pattern 3: `logger.error()` for fatal errors (operation fails)
- Pattern 4: Structured logging with keyword arguments
- Pattern 5: `logger.exception()` for automatic traceback

**Anti-Patterns to Avoid** (from HOOK_STDERR_STYLE_GUIDE.md):
- ❌ Using `print(..., file=sys.stderr)` in hooks
- ❌ Calling `basicConfig()` (creates StreamHandler to stderr by default)
- ❌ Adding handlers other than NullHandler in hooks

**Confidence Level**: HIGH
- Evidence: 17 files examined, official Python docs referenced, clear pattern separation

---

## 3. Existing Implementation Discovery

**File:** `P:\.claude\hooks\PostToolUse.py`

**Current Code (lines 179-180)**:
```python
except Exception as e:
    print(f"PostToolUse Logging Error: {e}", file=sys.stderr)
```

**Context**: Exception handler for `append_tool_event()` (lines 148-155) and signal file creation (lines 161-177)

**Why this exists**:
- Original intent: Provide diagnostic visibility for evidence logging failures
- Problem: Writes to stderr, which Claude Code treats as "hook error"

**Import Status**:
- ✅ `import logging` already present at line 25
- ✅ `import sys` already present at line 26
- No new imports required

**Related Code**:
- Lines 148-155: `append_tool_event()` function (evidence store)
- Lines 161-177: Signal file creation for async coordination
- Line 180: The problematic exception handler

---

## 4. Test Discovery

**No existing tests for PostToolUse.py exception handling behavior**

**Test Scenarios Required**:

1. **Happy Path**: Successful operations (no exception)
   - `append_tool_event()` succeeds
   - Signal file creation succeeds
   - Verify: No "hook error" message appears

2. **Exception Path**: Evidence logging fails
   - Simulate exception in `append_tool_event()`
   - Verify: Exception caught silently
   - Verify: No "hook error" message appears
   - Verify: Debug log contains error (if logging configured)

3. **Exception Path**: Signal file creation fails
   - Simulate permission denied, disk full
   - Verify: Exception caught silently
   - Verify: No "hook error" message appears

4. **Regression Test**: Evidence logging still works when no exception
   - Verify: Evidence store receives tool events
   - Verify: Signal files created correctly

**Test Location**: `P:\.claude\hooks\tests\test_posttooluse_logging.py` (new file)

**Verification Commands**:
```bash
# Run tests
pytest P:\.claude\hooks\tests\test_posttooluse_logging.py -v

# Manual test: Run rm -rf and check for hook errors
# (Will be done during implementation)
```

---

## 5. Proposed Solution

**Replace stderr print with Python logging framework using NullHandler pattern**

**Implementation**:

**Step 1**: Add logger initialization at module level (after line 26)
```python
import logging

# Configure logger for PostToolUse - no stderr output (Claude Code treats stderr as hook error)
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
```

**Step 2**: Replace exception handler (lines 179-180)
```python
# OLD CODE (PROBLEMATIC):
except Exception as e:
    print(f"PostToolUse Logging Error: {e}", file=sys.stderr)

# NEW CODE (FIXED):
except Exception as e:
    logger.debug(f"PostToolUse Logging Error: {e}")
```

**Why This Solution**:

1. **Follows existing patterns**: Matches Pattern A (NullHandler) used in 17 other hook files
2. **No stderr output**: `logger.debug()` with `NullHandler` produces no output
3. **Preserves diagnostics**: If user enables debug logging, errors are captured
4. **No configuration needed**: `NullHandler` ensures no accidental stderr
5. **Minimal change**: Single line change, no new imports (logging already imported)

**Alternatives Considered**:

- **Alternative 2** (Environment-gated stderr): More complex, not following codebase patterns
- **Alternative 3** (Diagnostic log file): Adds file I/O overhead, overkill for this use case
- **Simple `pass`**: Loses all diagnostic capability (rejected in architecture review)

---

## 6. Implementation Plan

**Prevention Checklist Verification**:

- [x] **Integration Points Defined**: PostToolUse.py (evidence store + signal files)
- [x] **Import Paths Verified**: `logging` and `sys` already imported
- [x] **Path Calculations Tested**: No path calculations in this change
- [x] **Configuration Documented**: No configuration needed (NullHandler)
- [x] **Tests Outlined**: 4 test scenarios identified above

**Step-by-Step Implementation**:

**Step 1**: Modify PostToolUse.py (2 changes)
- Add logger initialization after line 26
- Replace exception handler at lines 179-180

**Step 2**: Create test file
- Create `P:\.claude\hooks\tests\test_posttooluse_logging.py`
- Implement 4 test scenarios

**Step 3**: Manual verification
- Run `rm -rf` operation
- Run search operation
- Verify no "PostToolUse:Bash hook error" messages appear

**Step 4**: Run automated tests
- Execute `pytest P:\.claude\hooks\tests\test_posttooluse_logging.py -v`
- Verify all tests pass

**Estimated Effort**: 30 minutes
- Step 1: 10 minutes (code change)
- Step 2: 15 minutes (test creation)
- Step 3: 3 minutes (manual verification)
- Step 4: 2 minutes (automated tests)

**Ordering**: Sequential (Step 1 → Step 2 → Step 3 → Step 4)

---

## 7. Risks, Success Criteria, Dependencies

**Risks**:

1. **Risk: Silent evidence logging failures**
   - **Severity**: LOW
   - **Mitigation**: Evidence logging is best-effort system by design; failures are acceptable
   - **Detection**: User reports missing evidence (unlikely - evidence is advisory)

2. **Risk: Logging configuration issues**
   - **Severity**: LOW
   - **Mitigation**: `NullHandler` ensures no output regardless of configuration
   - **Rollback**: Revert to original code (simple 2-line change)

3. **Risk: Breaking existing behavior**
   - **Severity**: LOW
   - **Mitigation**: Change is isolated to exception handler; normal execution path unchanged
   - **Detection**: Automated tests catch regressions

**Success Criteria**:

1. ✅ No "PostToolUse:Bash hook error" messages appear after successful operations
2. ✅ Evidence logging continues to work when no exceptions occur
3. ✅ Exception handler catches errors silently (no stderr)
4. ✅ All automated tests pass

**Dependencies**:

- **Internal**: None (self-contained change)
- **External**: None (no new packages or services)
- **Blocking**: None

**Rollback Strategy**:

**Revert to original code** (2-line change):
```python
# REVERT:
logger.debug(f"PostToolUse Logging Error: {e}")

# TO:
print(f"PostToolUse Logging Error: {e}", file=sys.stderr)
```

Rollback time: < 1 minute

**Verification of Rollback**:
- Confirm "PostToolUse:Bash hook error" messages reappear (expected behavior)
- Evidence logging still works (unchanged in normal path)
