# Implementation Plan: Fix Hook StdErr Output (Complete Fix)

**Created:** 2026-03-07
**Status:** DRAFT
**Author:** Claude Code (/code workflow)

---

## 1. Overview

Remove all `sys.stderr` writes from PostToolUse hooks to eliminate false "hook error" messages. Replace with Python logging framework that writes to log files instead of stderr.

**Impact:** Stops "PreToolUse:* hook error" and "PostToolUse:* hook error" messages from appearing after every tool operation.

---

## 2. Architecture

**Files to modify:**
1. `P:\.claude\hooks\PostToolUse_router.py` - 16 stderr writes (15 remaining after partial fix)
2. `P:\.claude\hooks\PostToolUse_ruff_fix_gate.py` - 4 stderr writes

**Components:**
- Python `logging` module with `NullHandler` for stdout-only logging
- Log file output to `P:\.claude\hooks\logs\hook_errors.jsonl` for diagnostics
- Error caching in `ERROR_CACHE` (existing, keeps deduplication)

---

## 3. Data Flow

```
Tool execution → PostToolUse hook → Error occurs
                                              ↓
                                    _handle_tracking_error()
                                              ↓
                          Log to file (hooks/logs/hook_errors.jsonl)
                                              ↓
                          No stderr output (Claude Code sees no error)
```

---

## 4. Error Handling

**Graceful degradation:**
- Logging failures are silent (best-effort system)
- Log file creation failures don't block hook execution
- Error messages preserved in file for debugging

---

## 5. Test Strategy

**Test scenarios:**
1. **Happy path**: Tool executes successfully → no stderr output
2. **Error path**: Tool tracking fails → error logged to file, no stderr
3. **Debug mode**: ROUTER_DEBUG=1 → debug output to stdout, no stderr
4. **Edge case**: Log directory doesn't exist → created automatically

**Test location:** `P:\.claude\hooks\tests\test_no_stderr_in_hooks.py` (existing test, extend coverage)

---

## 6. Standards Compliance

**Python standards** (`/code-python`):
- Use `logging` module from standard library
- `NullHandler` prevents any stderr output
- File-based logging for diagnostics
- Type hints for function signatures

**Universal principles** (`/code-standards`):
- DRY: Reuse logging pattern across all hooks
- SoC: Separate error logging from stderr output
- Testing: Verify no stderr in tests

---

## 7. Ramifications

**Impact on existing code:**
- **No breaking changes**: Hook behavior unchanged (no stderr vs. log file)
- **Backwards compatible**: Hook output format unchanged
- **Performance**: Negligible impact (file I/O only on errors)
- **User-facing**: Fewer noise messages, cleaner UI

**Migration:**
- No migration needed (drop-in replacement)
- Existing tests pass unchanged

---

## Pre-Mortem Analysis (5 minutes)

**Imagine: 6 months from now, this feature failed. Why?**

### Failure Mode 1: Log file grows too large
- **Root cause**: Unchecked error spam fills disk
- **Prevention**: Log rotation, ERROR_CACHE deduplication (already in place)
- **Observability**: Monitor file size, add alert if > 100MB
- **TRACE scenario**: Verify ERROR_CACHE prevents duplicates

### Failure Mode 2: Silent errors hide real problems
- **Root cause**: Errors only in file, nobody checks them
- **Prevention**: Document log file location in CLAUDE.md
- **Observability**: Add log check to hook diagnostics script
- **TRACE scenario**: Verify errors still logged with `-v` flag

### Failure Mode 3: Permission errors creating log file
- **Root cause**: Read-only filesystem or permission denied
- **Prevention**: Silent fail (graceful degradation), never block
- **Observability**: No log file = silent failure (acceptable)
- **TRACE scenario**: Test with read-only directory

---

## Tasks

1. **[IN_PROGRESS]** Add logging setup to PostToolUse_router.py
2. **[PENDING]** Replace `log()` function stderr writes with file logging
3. **[PENDING]** Replace `_handle_tracking_error()` stderr writes with file logging
4. **[PENDING]** Replace line 327 stderr write with file logging
5. **[PENDING]** Fix PostToolUse_ruff_fix_gate.py stderr writes
6. **[PENDING]** Run tests to verify no stderr output
7. **[PENDING]** Update CHANGELOG.md with fix details

---

## Success Criteria

- [ ] No `print(..., file=sys.stderr)` in PostToolUse_router.py
- [ ] No `print(..., file=sys.stderr)` in PostToolUse_ruff_fix_gate.py
- [ ] All existing tests pass
- [ ] No "hook error" messages after tool operations
- [ ] Error logging works (verify log file created on error)
