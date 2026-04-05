# ADR-20260327: Hook Stderr — Phased Remediation Plan

**Status:** Proposed
**Date:** 2026-03-27
**Context:** Claude Code hooks use `print(..., file=sys.stderr)` for informational output, triggering false "hook error" displays. The root cause is that Claude Code treats ANY stderr output from hooks as a control signal (exit code 2 + stderr = fed back to Claude automatically). Scope: 245 occurrences across 76 files.

---

## Decision

Implement a phased remediation approach using the classification system from `HOOK_STDERR_STYLE_GUIDE.md`:

| Category | Action | stderr permitted? |
|----------|--------|-----------------|
| **REMOVE** | Success confirmations, informational status | No |
| **GATE on DEBUG** | Debug logging, trace output | Only if DEBUG env var set |
| **KEEP** | Actual errors, warnings, blocking actions | Yes |

**Recommended:** Option C — Phased approach (5-6 hours total)

---

## Scope Quantification

| Metric | Value |
|--------|-------|
| Total stderr prints | 245 |
| Files affected | 76 |
| High-frequency hooks (fires often) | PreToolUse, Stop, PostToolUse |
| Blocking files (verified violations) | `validate_code_phase_order.py`, `SessionEnd_tdd_cleanup.py`, `StopHook_tdd_continuation.py` |

---

## Phase 1: Fix Blocking Files (30 min)

**Priority:** Fix the 3 files already identified with verified stderr violations.

### Files to Fix

| File | Lines | Issue | Fix |
|------|-------|-------|-----|
| `validate_code_phase_order.py` | 84, 94, 107, 115 | Informational prints | Remove or gate on DEBUG |
| `SessionEnd_tdd_cleanup.py` | 95 | Informational print | Remove |
| `StopHook_tdd_continuation.py` | 82 | Informational print | Remove |

### Classification Process

For each print statement:
1. **Is it an error/warning?** → KEEP (actual problem)
2. **Is it success confirmation (✓, ✅)?** → REMOVE
3. **Is it informational status?** → REMOVE
4. **Is it debug trace?** → GATE on DEBUG env var

### Reference

See `P:\.claude\hooks\docs\HOOK_STDERR_STYLE_GUIDE.md` for the authoritative classification guide.

---

## Phase 2: Classify All Occurrences (2 hours)

**Tool:** Run existing classification script or create one if needed.

### Classification Categories

```python
REMOVE = "informational prints to be removed"
DEBUG_GATE = "debug prints to gate on DEBUG env var"
KEEP = "actual errors that should remain"
```

### Expected Distribution (estimated)

| Category | Estimated % | Count |
|----------|-------------|-------|
| REMOVE | ~60% | ~147 |
| DEBUG_GATE | ~25% | ~61 |
| KEEP | ~15% | ~37 |

---

## Phase 3: Fix High-Frequency Offenders (2 hours)

**Priority:** Fix hooks that fire on every tool use.

### Hook Frequency Order

1. **PreToolUse** — fires on every tool
2. **Stop** — fires on every response
3. **PostToolUse** — fires on every tool completion

### Strategy

Fix these hooks first because:
- Maximum user-visible impact (most false error displays)
- Common pattern: informational prints in error handlers
- Lowest risk: exception handlers are rarely critical path

---

## Phase 4: Add PreToolUse Lint Rule (1 hour)

**Purpose:** Prevent new informational stderr prints from being committed.

### Implementation

Add a PreToolUse lint hook that blocks Edit/Write on hook files when the edit introduces a `print(..., file=sys.stderr)` that matches informational patterns.

### Blocking Patterns

```python
INFO_PRINT_PATTERNS = [
    r'print\([^)]*file\s*=\s*sys\.stderr[^)]*\)',  # print(..., file=sys.stderr)
    r'print\([^)]*\)[\s\n]*#[^\n]*(?:info|status|loaded|initializing)',  # Info comments
]
```

### Bypass

`--allow-hook-stderr` flag in the edit message.

---

## Multi-Terminal Safety Assessment

| Phase | Pre-Fix | Post-Fix |
|-------|---------|----------|
| Phase 1 | 3 files with false errors | No false errors from fixed files |
| Phase 2 | 245 violations | All classified |
| Phase 3 | High-frequency hooks noisy | High-frequency hooks clean |
| Phase 4 | No prevention | Lint gate prevents new violations |

**Post-fix:** All hooks are multi-terminal safe — this is pure intra-process Python refactoring with no shared state.

---

## Consequences

**Positive:**
- Eliminates false "hook error" displays
- Classification enables targeted fixes (not blanket changes)
- Lint gate prevents regression
- Debug capability preserved via DEBUG-gated prints

**Negative:**
- 5-6 hours of careful refactoring required
- Risk of accidentally removing useful error output
- Classification requires judgment calls on edge cases

---

## Edge Case Considerations

1. **Silent error loss:** If we remove too many prints, real errors become invisible
   - **Mitigation:** KEEP category preserves actual errors; only REMOVE informational prints

2. **DEBUG gate false negatives:** Hooks that don't check DEBUG won't show debug output
   - **Mitigation:** Standard DEBUG env var check pattern; documentation in HOOK_STDERR_STYLE_GUIDE.md

3. **Multi-terminal stderr collision:** Multiple terminals printing to stderr simultaneously
   - **Mitigation:** Not a concern for informational prints (these should be removed anyway)

4. **Hook protocol misunderstanding:** Future hook authors may reintroduce the pattern
   - **Mitigation:** Phase 4 lint gate blocks new violations; HOOK_STDERR_STYLE_GUIDE.md documents correct pattern

---

## Implementation Notes

1. **Test after each fix:** Run `python -m pytest P:\.claude\hooks\tests\` to verify no regressions
2. **Use existing conventions:** Follow `CONVENTIONS.md` NullHandler pattern for new logging
3. **Document exceptions:** When KEEP is chosen for a print, add a comment explaining why
4. **Batch classification:** Phase 2 can be parallelized with multiple agents scanning different file sets

---

## Related Documentation

- `P:\.claude\hooks\docs\HOOK_STDERR_STYLE_GUIDE.md` — Authoritative classification guide
- `P:\.claude\hooks\CONVENTIONS.md` (lines 128-143) — NullHandler pattern
- `P:\.claude\hooks\plans\plan-20260306-posttooluse-logging-fix.md` — Original plan (Phase 1 scope)
- `P:\.claude\hooks\CLAUDE.md` — Logging Best Practices section
