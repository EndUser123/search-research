# GitHub CLI Safety Hook Implementation

**Date:** 2026-03-08
**Status:** ✅ Complete

---

## Summary

Expanded the existing `PreToolUse_destructive_git_guard.py` hook to protect against **both local git operations** and **GitHub CLI (gh) destructive operations**.

This prevents accidental deletion of GitHub repositories by requiring explicit approval with the `--i-understand-irreversible` flag.

---

## What Changed

### Before: Only Local Git Protection

The hook only protected against local git operations:
- `git reset --hard`
- `git clean -f`
- `git stash drop`
- `git rebase --onto`

**Gap:** GitHub CLI operations like `gh repo delete` were completely unprotected.

### After: Dual Protection (Git + GitHub)

The hook now protects against:

**Local Git Operations** (unchanged):
- `git reset --hard` (CRITICAL)
- `git clean -f` (HIGH)
- `git stash drop` (HIGH)
- `git rebase --onto` (MEDIUM)

**GitHub CLI Operations** (NEW):
- `gh repo delete` (CRITICAL) ← **Prevents repository deletion**
- `gh api --method DELETE` (HIGH)
- `gh org delete` (CRITICAL)
- `gh release delete` (HIGH)
- `gh gist delete` (MEDIUM)

---

## Implementation Details

### Modified File
- **File:** `P:\.claude\hooks\PreToolUse_destructive_git_guard.py`
- **Lines Added:** ~120 (from 233 to 363 lines)
- **Changes:**
  1. Added `check_gh_command()` function for GitHub CLI detection
  2. Refactored `check_bash_command()` to route to `check_git_command()` or `check_gh_command()`
  3. Updated `main()` and `run()` to handle both operation types
  4. Enhanced warning messages with GitHub-specific information

### New Test Suite
- **File:** `P:\.claude\hooks\tests\test_destructive_git_guard.py`
- **Tests:** 13 tests covering both git and gh operations
- **Coverage:**
  - ✅ All destructive operations detected
  - ✅ Non-destructive operations allowed
  - ✅ Approval flag bypass works correctly
  - ✅ Hook integration tests pass

---

## How It Works

### Example 1: Blocking Repository Deletion

**Command:**
```bash
gh repo delete EndUser123/portfolio-media
```

**Result:** ❌ BLOCKED
```
☢️ DESTRUCTIVE GITHUB CLI OPERATION DETECTED
======================================================================

Command: gh repo delete EndUser123/portfolio-media
Severity: CRITICAL
Impact: Permanently delete GitHub repository
Target: EndUser123/portfolio-media

======================================================================
CRITICAL: This operation cannot be undone!
======================================================================

To proceed, you MUST:
1. Confirm you understand what will be deleted
2. Confirm the target repository is correct
3. Use explicit approval flag: --i-understand-irreversible

Example safe usage:
  gh repo delete EndUser123/portfolio-media --yes --i-understand-irreversible

WARNING: This will permanently delete the GitHub repository. This cannot be undone!

❌ BLOCKED: Missing explicit approval flag --i-understand-irreversible
```

### Example 2: Allowing Deletion with Approval

**Command:**
```bash
gh repo delete EndUser123/portfolio-media --yes --i-understand-irreversible
```

**Result:** ✅ ALLOWED
```
(Exit code 0 - command proceeds)
```

---

## Protected Operations

| Command | Severity | Requires | Target Display |
|---------|----------|----------|----------------|
| `gh repo delete <repo>` | CRITICAL | `--i-understand-irreversible` | Yes (repo name) |
| `gh org delete <org>` | CRITICAL | `--i-understand-irreversible` | Yes (org name) |
| `gh api <endpoint> --method DELETE` | HIGH | `--i-understand-irreversible` | Yes (endpoint) |
| `gh release delete <id>` | HIGH | `--i-understand-irreversible` | Yes (release ID) |
| `gh gist delete <id>` | MEDIUM | `--i-understand-irreversible` | Yes (gist ID) |

---

## Testing

Run the test suite:

```bash
python P:\.claude\hooks\tests\test_destructive_git_guard.py
```

**Expected Output:**
```
Running destructive git guard tests...

✅ Test passed: git reset --hard is detected
✅ Test passed: git reset --soft is allowed
✅ Test passed: gh repo delete is detected
✅ Test passed: gh api DELETE is detected
✅ Test passed: gh api GET is allowed
✅ Test passed: gh org delete is detected
✅ Test passed: gh release delete is detected
✅ Test passed: gh gist delete is detected
✅ Test passed: gh repo view is allowed
✅ Test passed: gh repo delete with approval flag is detected
✅ Test passed: check_bash_command routing works correctly
✅ Test passed: Hook blocks gh repo delete without approval flag
✅ Test passed: Hook allows gh repo delete with approval flag

✅ All tests passed!
```

---

## Why This Matters

### Problem Solved

**Before this change:**
- `gh repo delete` would execute immediately without confirmation
- No protection against accidental repository deletion
- User could delete wrong repository in a moment of confusion

**After this change:**
- All destructive GitHub CLI operations require explicit approval
- Clear warning messages show exactly what will be deleted
- Forces user to confirm they understand the operation is irreversible

### Real-World Scenario

**Scenario:** User wants to delete deprecated `portfolio-media` repository

**Old behavior (unsafe):**
```bash
$ gh repo delete portfolio-media
• Repository deleted immediately
• No confirmation required
• Easy to accidentally delete wrong repo
```

**New behavior (safe):**
```bash
$ gh repo delete portfolio-media
❌ BLOCKED: Missing explicit approval flag

$ gh repo delete portfolio-media --yes --i-understand-irreversible
✅ Proceeds with explicit confirmation
```

---

## Architecture Decisions

### Why Expand Existing Hook?

**Option A:** Expand `PreToolUse_destructive_git_guard.py` ✅ **CHOSEN**
- Pros:
  - Consistent pattern with existing git protection
  - Single hook for all destructive operations
  - Shared approval flag (`--i-understand-irreversible`)
  - Less maintenance overhead
- Cons:
  - Slightly larger file (363 lines vs 233)

**Option B:** Create new `PreToolUse_destructive_github_guard.py`
- Pros:
  - Separate concerns
  - Smaller files
- Cons:
  - Duplicate code and patterns
  - Two approval flags to remember
  - More maintenance burden

**Decision:** Expand existing hook for consistency and simplicity.

---

## Integration with Existing Hooks

This hook works alongside existing safety hooks:

| Hook | Scope | Event |
|------|-------|-------|
| `PreToolUse_destructive_git_guard.py` | Local git + GitHub CLI | PreToolUse |
| `PreToolUse_git_safety.py` | Worktree cross-contamination | PreToolUse |
| `.git/hooks/pre-commit` | Python cache cleanup | Git hook |
| `.git/hooks/post-checkout` | Python cache cleanup | Git hook |

---

## Bypass Mechanism

If you need to disable this hook:

**Temporary bypass:**
```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

**Permanent bypass:**
Edit `P:\.claude/settings.json` and remove `PreToolUse_destructive_git_guard.py` from PreToolUse hooks.

**⚠️ WARNING:** Disabling safety hooks removes protection against data loss.

---

## Future Enhancements

Possible future improvements (not implemented):

1. **Scope validation** - Check if repository name matches current directory
2. **Multiple confirmation** - Require repo name to be typed twice
3. **Dry-run mode** - Show what would be deleted without executing
4. **Audit logging** - Log all destructive operations to file
5. **Grace period** - 30-second delay before executing deletion

---

## Files Modified

1. **`P:\.claude\hooks\PreToolUse_destructive_git_guard.py`** - Expanded to cover GitHub CLI
2. **`P:\.claude\hooks\tests\test_destructive_git_guard.py`** - Created comprehensive test suite

---

## Verification

To verify the hook is working:

```bash
# Test 1: Verify blocking works
echo '{"tool_name":"Bash","tool_input":{"command":"gh repo delete test-repo"}}' | python P:\.claude\hooks\PreToolUse_destructive_git_guard.py
# Expected: Exit code 2, JSON output with "decision": "block"

# Test 2: Verify approval flag works
echo '{"tool_name":"Bash","tool_input":{"command":"gh repo delete test-repo --i-understand-irreversible"}}' | python P:\.claude\hooks\PreToolUse_destructive_git_guard.py
# Expected: Exit code 0 (no output)
```

---

## Conclusion

✅ **Hook successfully expanded to protect against GitHub CLI destructive operations**

✅ **All 13 tests passing**

✅ **Consistent with existing git protection patterns**

✅ **Prevents accidental repository deletion with explicit approval requirement**

**Implementation Date:** 2026-03-08
**Test Status:** All tests passing (13/13)
**Integration Status:** Active and registered in settings.json
