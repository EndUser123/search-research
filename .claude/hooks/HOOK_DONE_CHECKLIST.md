# Pre-DONE Checklist for Hook Code

**MANDATORY** - Complete this checklist before claiming DONE on ANY hook code modification.

**Purpose**: Catch integration bugs that unit tests and function-level TRACE miss. Prevents "tests pass but integration fails" bugs.

---

## Before Claiming DONE on Hook Code

### 1. Unit Tests (Existing Requirement)
- [ ] All unit tests pass
- [ ] New tests added for new functionality
- [ ] Edge cases covered

### 2. Static Analysis (Existing Requirement)
- [ ] Ruff/linter passes
- [ ] Type checking passes (mypy/pyright if applicable)
- [ ] No blocking issues

### 3. TRACE (Enhanced - See Below)
- [ ] Functions traced (3 scenarios each)
- [ ] **NEW: Integration verification completed** (see below)

---

## Integration Verification (MANDATORY for Hooks)

### A. Cross-Module Contract Check
- [ ] List all exported schemas/types from all dependency modules
- [ ] Verify each schema is handled in consuming modules
- [ ] Verify no silent fall-through to `return None`

**How to verify**:
```bash
# 1. List exports from dependency module
grep "schema.*=" artifact_grounder.py
# Output: "blocked_command", "git_safety_block"

# 2. Check handler in consumer module
grep "schema.*==" PostToolUse_artifact_validator.py
# Output: "blocked_command"
# Missing: "git_safety_block" → BUG FOUND
```

### B. Main() Execution Path TRACE
- [ ] Trace actual entry point with real input
- [ ] Follow flow through all function calls
- [ ] Mark cleanup points in all exit paths
- [ ] Verify no early return skips cleanup

**How to verify**:
```python
# Create state table for main():
# Line 110: injection_result = check_and_inject_artifact(data)
# Line 111: if injection_result: → TRUE
# Line 112: print(...)
# Line 113: cleanup_stale_artifact(data)
# Line 114: sys.exit(0)
# Line 117: cleanup_stale_artifact(data) ← NEVER REACHED
```

### C. Integration Test (Run Actual Code)
- [ ] Create synthetic test input (temp files, mock stdin)
- [ ] Run actual hook with synthetic input
- [ ] Verify file system side effects (created/deleted)
- [ ] Run 10 consecutive times → verify no state accumulation

**How to verify**:
```python
# 1. Create artifact
artifact_path.write_text(json.dumps({...}))

# 2. Run hook
echo '{"session_id": "test", ...}' | python PostToolUse_artifact_validator.py

# 3. Verify side effects
assert not artifact_path.exists(), "Artifact should be deleted"

# 4. Run 10x to check for accumulation
for i in range(10):
    # Create artifact, run hook, verify deleted
```

---

## Common Hook Bugs This Checklist Catches

| Bug Type | Unit Test | Function TRACE | Integration Test |
|----------|-----------|----------------|------------------|
| Cleanup skipped in early exit path | ✗ Passes | ✗ Passes | ✅ **Catches** |
| Schema from dependency never handled | ✗ Passes | ✗ Passes | ✅ **Catches** |
| State accumulates across runs | ✗ Passes | ✗ Passes | ✅ **Catches** |
| File never deleted (orphan accumulation) | ✗ Passes | ✗ Passes | ✅ **Catches** |
| Wrong module imported at runtime | ✗ May pass | ✗ Passes | ✅ **Catches** |

---

## Acceptance Criteria

**Hook code is DONE only when**:
1. ✅ All unit tests pass
2. ✅ All static analysis passes
3. ✅ TRACE completed (functions + integration verification)
4. ✅ Integration test passes (10 consecutive runs, no state accumulation)
5. ✅ No orphaned files in `hooks/state/` after test runs

---

## Examples

### Example 1: GAV Bug (Fixed)
**Bug**: Artifact never deleted, infinite injection loop

**What caught it**:
- Integration test: Artifact still exists after injection
- Main() TRACE: Line 138 `sys.exit(0)` skips cleanup at line 143

**Fix**: Add `cleanup_stale_artifact(data)` before `sys.exit(0)`

### Example 2: Schema Gap (Fixed)
**Bug**: `git_safety_block` written but never injected

**What caught it**:
- Cross-module contract check: `artifact_grounder.py` exports 2 schemas, validator only handles 1

**Fix**: Add `if schema == "git_safety_block":` handler

---

## How to Use This Checklist

1. **Before claiming DONE**: Run through all sections
2. **Document evidence**: Save integration test output
3. **Mark checkboxes**: `[x]` when completed
4. **If any check fails**: Fix before claiming DONE

**Time required**: 10-15 minutes for typical hook code

**ROI**: Catches 100% of integration bugs that would otherwise ship to production.
