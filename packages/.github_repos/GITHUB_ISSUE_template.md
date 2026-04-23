# Bug Report: Division by Zero in updateBranchMetrics()

## Summary
**Error**: `Cannot read properties of undefined (reading 'toFixed')`
**Location**: `src/branchManager.ts:704` in `updateBranchMetrics()`
**Severity**: High - Crashes when adding third thought to a branch
**Status**: Fixed locally, awaiting upstream PR

## Bug Description

When adding a third thought to a branch in the branch-thinking MCP server, the application crashes with:
```
Cannot read properties of undefined (reading 'toFixed')
```

### Root Cause

Division by zero occurs in `updateBranchMetrics()` when `branch.thoughts.length === 0`:

```typescript
// Line 704 in src/branchManager.ts
const avgConfidence = branch.thoughts.reduce((sum, t) => sum + t.metadata.confidence, 0) / branch.thoughts.length;
```

When the thoughts array is empty, division produces `NaN`. Later code attempts to call `avgConfidence.toFixed(2)`, which throws because `NaN.toFixed()` is invalid.

## Reproduction Steps

1. Start branch-thinking MCP server
2. Create a new branch
3. Add first thought → ✅ Success
4. Add second thought → ✅ Success
5. Add third thought → ❌ Crash with `.toFixed()` error

## Applied Fix

Added guard clause to prevent division by zero:

```typescript
private updateBranchMetrics(branch: ThoughtBranch): void {
  // Guard clause: if no thoughts yet, skip metrics update to prevent division by zero
  if (branch.thoughts.length === 0) {
    return;
  }

  const avgConfidence = branch.thoughts.reduce((sum, t) => sum + t.metadata.confidence, 0) / branch.thoughts.length;
  // ... rest of function
}
```

### Files Modified
- `src/branchManager.ts` (lines 699-702)
- `dist/branchManager.js` (compiled output, lines 647-650)

## Verification

✅ **Fixed**: Compiled successfully with `rm -rf dist/ && pnpm build`
✅ **Verified**: Guard clause present in compiled JavaScript
✅ **Tested**: Added 3 thoughts successfully (branchPriority: 2.1, 2.2, 2.3)
✅ **Required**: Claude Code restart to reload MCP server process

## Recommended Actions

1. **Merge this fix** to prevent crashes on empty branches
2. **Add unit tests** for `updateBranchMetrics()` with empty array scenario
3. **Add test suite** to project (currently has no tests)
4. **Consider adding validation** in other division operations

## Test Case Recommendation

```typescript
it('should handle empty thoughts array without throwing division by zero error', () => {
  const emptyBranch: ThoughtBranch = {
    id: 'test-branch',
    thoughts: [], // Empty array triggers the bug
    insights: [],
    crossRefs: [],
    priority: 0,
    confidence: 0,
    createdAt: new Date(),
    updatedAt: new Date(),
  };

  expect(() => {
    branchManager['updateBranchMetrics'](emptyBranch);
  }).not.toThrow();
});
```

## Environment

- **OS**: Windows 11
- **Node.js**: v22
- **Package**: @modelcontextprotocol/server-branch-thinking v0.1.1
- **Package Manager**: pnpm

## Related Issues

- None currently reported

## Additional Notes

This bug was discovered during normal usage when testing the branch-thinking MCP server integration with Claude Code. The guard clause pattern is a common defense against division by zero and should be considered for other arithmetic operations in the codebase.

---

**Reporter**: Claude Code user
**Date**: 2026-03-10
**Fix Available**: Yes (attached to this issue)
**Breaking Change**: No
