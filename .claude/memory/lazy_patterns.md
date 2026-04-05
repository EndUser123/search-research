# Lazy LLM Workaround Patterns

## Problem Statement

LLMs sometimes suggest accepting bugs as features instead of fixing root causes. This creates technical debt and is unacceptable.

## Detected Lazy Patterns

### Pattern 1: "Accept As Feature"
- **Detection**: `accept.*as.*(visible logging|feature|design|cosmetic)`
- **Example**: "Accept duplicate task bars as 'visible logging'"
- **Correct Action**: Fix the duplication, don't document it
- **Root Cause**: Lazy investigation - stopping at symptom instead of tracing to cause

### Pattern 2: "Live With It"
- **Detection**: `live with.*(bug|issue|problem|limitation)`
- **Example**: "Just live with the race condition, it's rare"
- **Correct Action**: Fix the race condition or add proper synchronization
- **Root Cause**: Avoiding hard problems

### Pattern 3: "That's Expected"
- **Detection**: `(duplicate|redundant|extra).*(is fine|acceptable|expected|normal)`
- **Example**: "Duplicate bars are expected behavior"
- **Correct Action**: Investigate why duplication occurs
- **Root Cause**: Treating symptoms as design

## Enforcement: Lazy Workaround Detector Hook

**File**: `P:/.claude/hooks/Stop_lazy_workaround_gate.py`

**Patterns to block:**
1. Accepting bugs as "visible logging"
2. Documenting workarounds instead of fixes
3. "That's acceptable" for actual problems
4. "Cosmetic issue" for functional bugs

**Required behavior:**
- TRACE: Find root cause first
- FIX: Address the actual problem
- VERIFY: Confirm the fix works
- DOCUMENT: Only document decisions, not workarounds

## Examples from Your Codebase

### Bad Example (What NOT to do)
```
Issue: Duplicate task bars appearing
Lazy suggestion: "Accept duplicate bars as visible logging"
Problem: User has to see confusing duplicate UI
Correct fix: Investigate why TaskOutput creates duplicates
```

### Good Example (What TO do)
```
Issue: Duplicate task bars appearing
Investigation: Add logging to TaskOutput.create()
Finding: Task is created twice due to race condition
Fix: Add deduplication check or prevent double-call
Verify: No more duplicates in testing
```

## Testing the Gate

Add to `P:/.claude/hooks/tests/test_lazy_workaround_gate.py`:
```python
def test_accept_as_feature_blocked():
    response = "Let's accept the duplicate bars as visible logging"
    result = check_lazy_workarounds(response)
    assert result["decision"] == "block"
    assert "lazy workaround" in result["message"].lower()

def test_root_cause_approach_allowed():
    response = "Let me trace where the duplicate tasks are created and fix the source"
    result = check_lazy_workarounds(response)
    assert result["decision"] == "allow"
```

## Integration Point

Add to `Stop.py` after `behavior_audit`:
```python
from Stop_lazy_workaround_gate import check_lazy_workarounds

lazy_result = check_lazy_workarounds(response)
if lazy_result["decision"] == "block":
    return lazy_result
```

## Confidence Level

**HIGH** - This pattern is consistently lazy and should always be blocked.
