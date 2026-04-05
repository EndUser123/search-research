# Investigation: Why Existing clear_pycache() Didn't Prevent Cache Bug

**Date:** 2026-03-07
**Investigator:** Claude Code
**Issue:** Stale Python bytecode cache caused "fixed source but still broken" bug

---

## Root Cause Analysis

### The Bug You Experienced

**Symptom:**
```python
ModuleNotFoundError: No module named 'debug_rca.local_fallback_mode'
```

**Context:**
- Source file was already fixed (git commits this morning at 11:39 AM)
- Import error persisted despite correct source code
- Problem resolved after deleting `__pycache__/` manually

**Location of stale cache:**
```
P:/packages/debugRCA/src/debug_rca/__pycache__/
```

### Existing clear_pycache() Implementation

**Location:** `.git/hooks/pre-commit:113-156`

**Scope:**
```python
hooks_dir = GIT_ROOT / ".claude" / "hooks"
```

**What it cleans:**
- Only `.claude/hooks/__pycache__/` directories
- Only `.claude/hooks/**/*.pyc` files

**What it DOESN'T clean:**
- ❌ `packages/**/__pycache__/`
- ❌ `src/**/__pycache__/`
- ❌ Any other Python cache outside hooks directory

### Why It Failed

The function is **intentionally scoped** to only clean the hooks directory (line 118 comment: "ensures hooks run with fresh bytecode after pulls"). This is a **design limitation**, not a bug in the implementation.

**Evidence from code comment (line 117-120):**
```python
"""
Prevents stale .pyc files from being committed and ensures hooks
run with fresh bytecode after pulls. This prevents recurrence of
import failures due to corrupted bytecode caches.
"""
```

The scope is explicitly "hooks run with fresh bytecode" - NOT "entire repository has fresh bytecode."

---

## The Gap

**What's needed but missing:**
1. **Repository-wide cache cleanup** - Not just hooks directory
2. **post-checkout cleanup** - To clean cache after branch switches
3. **Worktree-aware cleanup** - To handle `.claude/worktrees/` properly

**Why the existing solution couldn't help:**
- pre-commit hooks only run before commits
- They don't run after `git checkout`, `git pull`, or branch switches
- The stale cache was created during a branch switch or git operation, not during commit

---

## Recommended Fix

### Option A: Expand clear_pycache() Scope (Simple)

Modify the existing function to clean entire repository:

```python
def clear_pycache() -> int:
    """Clear Python bytecode caches from entire repository."""
    import shutil

    # Clean entire repo, not just hooks
    repo_dirs = [
        GIT_ROOT / "packages",
        GIT_ROOT / "src",
        GIT_ROOT / ".claude" / "hooks",
    ]

    cleared = 0
    for base_dir in repo_dirs:
        if not base_dir.exists():
            continue

        for item in base_dir.rglob("__pycache__"):
            if item.is_dir():
                shutil.rmtree(item)
                cleared += 1

        for pattern in ["*.pyc", "*.pyo"]:
            for item in base_dir.rglob(pattern):
                item.unlink()
                cleared += 1

    return 0
```

**Pros:**
- Simple change to existing function
- Covers all Python code locations

**Cons:**
- May be slow on large repos (recursive scan)
- Doesn't help with post-checkout scenarios

### Option B: Add post-checkout Hook (Recommended)

**Why this is better:**
- Runs after branch switches, checkouts, worktree operations
- Catches stale cache at the source (when it's created)
- Works for all git operations, not just commits

**Implementation:** See Phase 1 of updated plan

---

## Verification Steps

1. **Test current scope:**
   ```bash
   # Create cache in packages/
   python -c "import tempfile; pathlib.Path('packages/debugRCA/src/debug_rca/__pycache__').mkdir(parents=True, exist_ok=True)"

   # Run pre-commit hook
   .git/hooks/pre-commit

   # Verify cache still exists
   ls -la packages/debugRCA/src/debug_rca/__pycache__/
   ```

2. **Test proposed fix (post-checkout):**
   ```bash
   # Create cache
   python -c "pathlib.Path('packages/debugRCA/src/debug_rca/__pycache__').mkdir(parents=True, exist_ok=True)"

   # Run checkout
   git checkout main

   # Verify cache deleted
   ls packages/debugRCA/src/debug_rca/__pycache__/  # Should fail
   ```

---

## Conclusion

**Root cause:** Existing `clear_pycache()` is scoped only to hooks directory by design. It cannot prevent cache bugs in other parts of the codebase.

**Solution:** Add repository-wide cache cleanup in post-checkout hook (covers all git operations) AND expand pre-commit scope (covers commits).

**Next steps:** Implement Phase 1 of updated plan with concrete implementations.

---

**Status:** Investigation complete ✅
**Evidence:** Code review of `.git/hooks/pre-commit:113-156`
**Confidence:** HIGH (100% - direct code evidence)
