# Plan File Validation and Relocation - Implementation Summary

## Problem Identified
User reported that plan files written in worktrees were not being validated or relocated to central storage (`P:/.claude/plans/`), leading to:
- Plans remaining in worktree-specific locations
- No verification that plan content was written correctly
- False confidence when Claude Code reported "plan saved"
- Lost context (plans not visible to main P: sessions)

## Root Cause Analysis

**Evidence (Tier 1 - Code Inspection):**
1. `PostToolUse_file_relocator.py` existed with correct relocation logic
2. Hook was NOT integrated into any router execution chain
3. No validation hook existed to verify plan content

**Confidence:** 95% (direct code evidence)

## Implementation

### Changes Made

1. **Integrated File Relocator (`PostToolUse_write_router.py`)**
   - Added `PostToolUse_file_relocator.py` to HOOK_SEQUENCE
   - Positioned first to run before other validation hooks
   - Enabled by default (`FILE_RELOCATOR_ENABLED=true`)

2. **Created Plan Validator (`PostToolUse_plan_validator.py`)**
   - New hook validates plan files after writing
   - Checks:
     - File exists at expected location
     - Content is non-empty (>10 chars)
     - Basic structure present (headers)
     - File is in correct directory (`P:/.claude/plans/`)
   - Silent success (no noise for valid plans)
   - Loud failure (reports issues clearly)
   - Logs all validations to `P:/.claude/logs/plan_validations.jsonl`

3. **Integration Testing (`test_plan_relocation_validation.py`)**
   - Comprehensive end-to-end test
   - Simulates worktree plan write
   - Verifies relocation
   - Confirms validation
   - Checks logging

### Execution Flow

**Before Fix:**
```
Write plan in worktree → PostToolUse:Write error → Plan stays in worktree
→ User approves without knowing plan wasn't moved
```

**After Fix:**
```
Write plan in worktree → PostToolUse_file_relocator moves to P:/.claude/plans/
→ PostToolUse_plan_validator confirms content
→ Report relocation to user
→ Only then declare "plan saved"
```

### Hook Sequence (PostToolUse_write_router.py)

```python
HOOK_SEQUENCE = [
    ("PostToolUse_file_relocator.py", "FILE_RELOCATOR_ENABLED", "true"),
    ("PostToolUse_plan_validator.py", "PLAN_VALIDATOR_ENABLED", "true"),
    ("anti_sycophancy/toggle.py", "ANTI_SYCOPHANCY_ENABLED", "false"),
    ("PostToolUse_gate_3_comprehension.py", "GATE_3_COMPREHENSION_ENABLED", "true"),
    ("PostToolUse_gate_3_read_gate.py", "GATE_3_READ_GATE_ENABLED", "true"),
]
```

## Verification

**Test Results:**
- ✅ File relocates from worktree to `P:/.claude/plans/`
- ✅ New filename includes timestamp to prevent collisions
- ✅ Plan validator confirms content is valid
- ✅ Validation logged to `plan_validations.jsonl`
- ✅ User receives clear relocation message

**Test Output:**
```
✓ File relocated to: P:\.claude\plans\plan-20260123-134928-test-plan-intent-validation.md
✓ Validation passed (silent success)
✓ Log confirms validation passed
```

## Impact Assessment

**Reversibility:** 1.0 (Trivial to disable via env vars)

**Benefits:**
- Plans centrally tracked in `P:/.claude/plans/`
- Content verification prevents corrupted plans
- Clear user feedback on relocation
- Audit trail in validation log
- Works across all worktrees

**Risks:** None identified - fail-safe design (returns {} on any error)

## Environment Variables

Control hooks via environment variables:

```bash
# Disable file relocator (not recommended)
export FILE_RELOCATOR_ENABLED=false

# Disable plan validator
export PLAN_VALIDATOR_ENABLED=false
```

## Files Modified

- `P:\.claude\hooks\PostToolUse_write_router.py` (added 2 hooks to sequence)

## Files Created

- `P:\.claude\hooks\PostToolUse_plan_validator.py` (new validation hook)
- `P:\.claude\hooks\tests\test_plan_relocation_validation.py` (integration test)

## Logs Generated

- `P:/.claude/logs/plan_validations.jsonl` - Validation audit trail
- `P:/.claude/session_data/file_relocations.jsonl` - Relocation history

## Next Steps

None required - fix is complete and tested.

## Evidence Tier

- **Implementation:** Tier 1 (execution artifacts from test run)
- **Effectiveness:** Tier 1 (verified via integration test)
- **Confidence:** 95%

---

**Date:** 2026-01-23
**Issue:** Plan files not validated/relocated in worktrees  
**Status:** ✅ RESOLVED
