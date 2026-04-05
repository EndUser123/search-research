# Stop Router Diagnostic Patch - Missing Response Investigation

## Problem

Anti-sycophancy hooks (sycophancy_agreement, overconfidence_detector, lazy_closure_detector) stopped detecting patterns after Jan 25, 2026. Root cause: CC is calling Stop_router.py **without passing response text**, making pattern detection impossible.

## Evidence

- All `hook_decisions_*.jsonl` entries show `response_length: 0` since Jan 26
- Hooks successfully detected patterns Jan 22-25 (when response was provided)
- PROTOCOL.md marks `response` field as optional for Stop hooks
- Pattern-detection hooks require response text to function

## Diagnostic Patch Applied

### Changes to Stop_router.py

**1. Missing Response Detection (main function)**
```python
# Detects when response field is missing or empty
# Logs to stderr (visible in CC output)
# Logs to hook_decisions_*.jsonl with decision="diagnostic"
```

**2. Pattern Hook Warning (run_hooks function)**
```python
# Warns when pattern-detection hooks are active but response is empty
# Lists which hooks cannot function without response text
# Prints to stderr for visibility
```

### Log Entries Created

**Diagnostic entry format:**
```json
{
  "hook_name": "Stop_router",
  "decision": "diagnostic",
  "reason": "missing_response=field_absent|empty_string",
  "claim_snippet": "dict_keys(['key1', 'key2'])",
  "response_length": 0
}
```

**Warning to stderr:**
```
[Stop_router WARNING] Pattern-detection hooks active but response is empty!
  Active hooks: StopHook_sycophancy_agreement.py, StopHook_overconfidence_detector.py
  These hooks CANNOT detect patterns without response text.
  response_length: 0
```

## Analysis Tools

### Run Diagnostic Analysis

```bash
cd P:\.claude\hooks
python analyze_missing_response.py
```

**Output includes:**
- Count of missing response calls vs total calls
- Percentage of calls with missing response
- Available data keys when response is missing
- Response length distribution
- 7-day trend analysis

### Check Logs Manually

```bash
# Today's logs
cat P:\.claude\hooks\session_data\hook_decisions_2026-01-30.jsonl | grep "diagnostic"

# Count missing responses
cat P:\.claude\hooks\session_data\hook_decisions_2026-01-30.jsonl | grep '"decision":"diagnostic"' | wc -l

# Check stderr output in CC
# (CC should display warnings when Stop_router executes)
```

## Expected Findings

**If bug is active:**
- Every Stop_router call shows diagnostic entry
- stderr warnings appear in CC output
- 100% of hook executions show response_length: 0
- Pattern-detection hooks never log detections

**If bug is fixed:**
- No diagnostic entries
- No stderr warnings
- Hook executions show response_length > 0
- Pattern-detection hooks resume logging

## Next Steps

1. **Immediate**: Run diagnostic analysis to confirm bug is still present
2. **Locate CC code**: Find where CC invokes Stop hooks
3. **Fix integration**: Ensure CC passes `response` field
4. **Verify fix**: Check diagnostic logs show response_length > 0
5. **Test pattern detection**: Verify hooks catch "You're absolutely right" etc.

## Files Modified

- `P:\.claude\hooks\Stop_router.py` - Added diagnostics
- `P:\.claude\hooks\analyze_missing_response.py` - Analysis script

## Rollback

To remove diagnostic patch:
```bash
cd P:\.claude\hooks
git diff Stop_router.py  # Review changes
git checkout Stop_router.py  # Revert if needed
```

---

**Status**: Diagnostic patch active, awaiting next CC execution to collect data.
