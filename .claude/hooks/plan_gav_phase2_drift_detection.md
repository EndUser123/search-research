# Plan: GAV Phase 2 - Drift Detection

## Overview
Add drift detection to PostToolUse_artifact_validator.py to validate that RCA/explanation output references the correct grounded artifact. Implements warning-only checks (no blocking).

## Architecture
**Single module addition** - Extend PostToolUse_artifact_validator.py with new function:
- `validate_rca_against_artifact(data: dict) -> dict | None`
- Wired into main() after injection branch, before cleanup

## Data Flow

```
PostToolUse receives tool_result
    ↓
validate_rca_against_artifact() called
    ↓
Check: artifact exists? → No: return None
    ↓ Yes
Check: output > 50 chars? → No: return None
    ↓ Yes
Check: has RCA markers? → No: return None
    ↓ Yes
Check: command substring in output? → Yes: return None
    ↓ No
Check: token overlap ratio < 0.3? → Yes: WARNING
    ↓ No
Check: tool-type drift? → Yes: WARNING
    ↓ No
return None (valid)
```

## Error Handling
- Best-effort: wrap all logic in try/except with pass
- Never write to stderr
- Validation failures return None (skip validation gracefully)
- File read failures handled gracefully

## Test Strategy

### Unit Tests (extend existing file)
1. **No drift when command mentioned** - RCA quotes actual command → no warning
2. **Drift when wrong command** - RCA talks about git safety but command was python → warning
3. **Low token overlap** - RCA about unrelated topic → warning
4. **Short output skip** - Output < 50 chars → skip validation
5. **No RCA markers skip** - No "root cause", "rca", etc. → skip validation
6. **Tool-type drift heuristic** - Git safety phrases vs python command → warning
7. **No artifact** - No grounded artifact exists → skip validation
8. **Best-effort error handling** - Malformed artifact JSON → skip gracefully

### Pre-mortem Analysis
**Failure Mode #1**: False positives on valid paraphrases
- **Root cause**: Substring check too strict, paraphrased RCAs flagged
- **Prevention**: Token overlap check provides fallback, 0.3 threshold tuned for paraphrasing
- **Test case**: Test #1 verifies quoting works

**Failure Mode #2**: Drift detection crashes hook
- **Root cause**: Unhandled exception in validation logic
- **Prevention**: All logic wrapped in try/except with pass
- **Test case**: Test #8 verifies error handling

**Failure Mode #3**: Performance regression on every PostToolUse
- **Root cause**: Validation runs on every tool call
- **Prevention**: Early exit conditions (artifact exists, output length, RCA markers)
- **Observability**: Monitor PostToolUse hook latency

## Standards Compliance
**Python 2025+ standards**:
- Type hints: `dict | None` return types
- Best-effort error handling with try/except
- No stderr output (hook requirement)
- Clean function separation (single responsibility)

## Ramifications
- **Backwards compatible**: Existing behavior unchanged (adds warnings, doesn't block)
- **No breaking changes**: Adds new optional validation only
- **Performance**: Minimal impact (< 1ms validation, early exits)
- **Test impact**: Extends existing test file (no new files)

## Tasks
1. Add `validate_rca_against_artifact()` function to PostToolUse_artifact_validator.py
2. Wire function into `main()` after injection, before cleanup
3. Add 8 test cases to test_artifact_validation_hooks.py
4. Run tests and verify all pass
5. Run ruff for code quality check
