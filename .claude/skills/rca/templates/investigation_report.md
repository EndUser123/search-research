# Investigation Report

Complete documentation of debugging or RCA investigation.

## Metadata

- **Date**: [YYYY-MM-DD]
- **Investigator**: [Name/Agent]
- **Session ID**: [From rca session]
- **Investigation Type**: [Debug / RCA]
- **Severity**: [Critical / High / Medium / Low]

## Problem Statement

### What is broken?
[One sentence description]

### Expected Behavior
[What should happen]

### Actual Behavior
[What actually happens]

### Impact
[Who is affected and how]

## Investigation Summary

### Root Cause
**[Root cause statement]**

### Evidence Chain

1. **Phase 0: Reproduction**
   - Steps: [How to reproduce]
   - Result: [What happened]

2. **Phase 1: Data Flow / Mental Trace**
   - Trace: [Code path analysis]
   - Finding: [What was discovered]

3. **Phase 2: Hypothesis Testing**
   - Hypothesis 1: [Description] - Rejected
   - Hypothesis 2: [Description] - Confirmed

4. **Phase 3: Root Cause Analysis**
   - 5 Whys: [Why chain]
   - Root Cause: [Final answer]

### Fix Applied

```python
# [Code change or description]
```

### Verification

- [x] Test passes
- [x] Reproduction steps no longer trigger issue
- [x] Regression test added

## Lessons Learned

### What went well?
- [What worked in this investigation]

### What could be improved?
- [What could be done better next time]

### Prevention
- [How to prevent this type of issue]

## Related Issues

- [Links to related issues, PRs, or investigations]
