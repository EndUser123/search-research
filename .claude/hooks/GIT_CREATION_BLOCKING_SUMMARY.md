# Git Creation Operation Blocking

**Date:** 2026-03-08
**Status:** ✅ Complete

---

## Summary

Enhanced `PreToolUse_destructive_git_guard.py` to block git commands that create files or folders. This prevents inappropriate use of git as a file system tool - git should be used for version control, not file/directory creation.

---

## Problem Solved

### Before: Git Could Be Misused as File System Tool

Claude could use git commands to create files and directories:
- `git worktree add <path>` - Creates new worktree directories
- `git init <directory>` - Creates new .git directories
- `git clone <url>` - Creates entire repository directories
- `git checkout -b <branch>` - Creates new branches

These operations create files/folders on the filesystem, which is inappropriate use of git.

### After: Git Operations Categorized by Type

**Two categories of protected operations:**

1. **Destructive** - Data loss operations (already protected)
   - `git reset --hard`
   - `git clean -f`
   - `git stash drop`
   - `git rebase --onto`

2. **Creative** - File/folder creation operations (NEW)
   - `git worktree add`
   - `git init`
   - `git clone`
   - `git checkout -b`

---

## Protected Creative Operations

| Command | What It Creates | Severity | Alternative |
|---------|----------------|----------|-------------|
| `git worktree add <path> <branch>` | New worktree directory | HIGH | Use `/git worktree` or Claude Code worktree feature |
| `git init <directory>` | New .git directory | HIGH | Use `git init` in terminal directly if needed |
| `git clone <url>` | New repository directory | HIGH | Use `gh repo clone` or clone in terminal |
| `git checkout -b <branch>` | New branch | MEDIUM | Use `/git workflow` or `git switch -c` explicitly |

---

## How It Works

### Example 1: Blocking Git Worktree Creation

**Command:**
```bash
git worktree add ../feature-branch feature-branch
```

**Result:** ❌ BLOCKED
```
⚠️ CREATIVE GIT OPERATION DETECTED
======================================================================

Command: git worktree add ../feature-branch feature-branch
Severity: HIGH
Impact: Create new git worktree directory
Target: ../feature-branch

======================================================================
GIT IS NOT A FILE SYSTEM TOOL
======================================================================

Git should be used for version control, not creating files or folders.
This operation creates new git objects on the filesystem.

Better alternative:
Use /git worktree command or create worktree via Claude Code worktree feature

======================================================================
To proceed, you MUST:
1. Confirm you understand git is not the right tool for file creation
2. Use explicit approval flag: --i-understand-irreversible

Example:
  git worktree add ../feature-branch feature-branch --i-understand-irreversible

❌ BLOCKED: Missing explicit approval flag --i-understand-irreversible
```

### Example 2: Blocking Git Clone

**Command:**
```bash
git clone https://github.com/user/repo.git
```

**Result:** ❌ BLOCKED
```
⚠️ CREATIVE GIT OPERATION DETECTED
======================================================================

Command: git clone https://github.com/user/repo.git
Severity: HIGH
Impact: Clone repository (creates directory)
Target: https://github.com/user/repo.git

======================================================================
GIT IS NOT A FILE SYSTEM TOOL
======================================================================

Git should be used for version control, not creating files or folders.
This operation creates new git objects on the filesystem.

Better alternative:
Use gh repo clone or clone in terminal directly

❌ BLOCKED: Missing explicit approval flag --i-understand-irreversible
```

### Example 3: Allowing with Approval Flag

**Command:**
```bash
git worktree add ../feature-branch feature-branch --i-understand-irreversible
```

**Result:** ✅ ALLOWED (user explicitly confirmed)

---

## Implementation Details

### Modified File
- **File:** `P:\.claude\hooks\PreToolUse_destructive_git_guard.py`
- **Changes:**
  1. Added `CREATIVE_OPS` dictionary for creation operations
  2. Added `BRANCH_OPS` dictionary for branch creation
  3. Enhanced `check_git_command()` to detect creative operations
  4. Added `category` field to distinguish destructive vs creative
  5. Updated warning messages with "GIT IS NOT A FILE SYSTEM TOOL"
  6. Added alternative suggestions for each creative operation

### New Test Suite
- **File:** `P:\.claude\hooks\tests\test_git_creation_blocking.py`
- **Tests:** 17 tests covering creation operation blocking
- **Coverage:**
  - ✅ All creative operations detected
  - ✅ Existing branch checkout allowed
  - ✅ Destructive operations still work correctly
  - ✅ Target extraction works
  - ✅ Appropriate warning messages
  - ✅ Approval flag bypass works

---

## Architecture

### Operation Categories

The hook now categorizes protected operations into two types:

```python
CREATIVE_OPS = {
    "worktree": {
        "danger_subcommands": {"add"},
        "description": "Create new git worktree directory",
        "severity": "HIGH",
        "category": "creative",
        "alternative": "Use /git worktree command..."
    },
    "init": {
        "description": "Initialize new git repository",
        "severity": "HIGH",
        "category": "creative",
        "alternative": "Use 'git init' in terminal directly..."
    },
    "clone": {
        "description": "Clone repository (creates directory)",
        "severity": "HIGH",
        "category": "creative",
        "alternative": "Use gh repo clone or clone in terminal..."
    }
}
```

### Warning Message Logic

```python
if danger_info.get("category") == "creative":
    # Show "GIT IS NOT A FILE SYSTEM TOOL" warning
    # Provide alternative approach
else:
    # Show "CRITICAL: This operation cannot be undone!" warning
    # Show affected files
```

---

## Testing

### Test Suite 1: Original Destructive Operations
```bash
python P:\.claude\hooks\tests\test_destructive_git_guard.py
# ✅ All 13 tests passed
```

### Test Suite 2: New Creation Operations
```bash
python P:\.claude\hooks\tests\test_git_creation_blocking.py
# ✅ All 17 tests passed
```

**Total:** 30 tests passing (13 original + 17 new)

---

## Why This Matters

### Inappropriate Git Usage

**Problem:** Git is designed for version control, not file system operations.

**Examples of misuse:**
- Creating directories with `git worktree add` when `mkdir` would be clearer
- Initializing repos with `git init` when file operations are needed
- Cloning repos with `git clone` when file copy would be more explicit
- Creating branches with `git checkout -b` without clear intent

**Better alternatives:**
- Use file system tools (`mkdir`, `cp`, `New-Item`)
- Use `/git worktree` command for intentional worktree creation
- Use `gh repo clone` for GitHub repositories
- Use explicit `git switch -c` for branch creation

### Safety Benefits

1. **Prevents accidental directory creation** - Forces explicit confirmation
2. **Encourages right tool for the job** - Suggests better alternatives
3. **Clear intent signaling** - Approval flag confirms user understands
4. **Maintains git's purpose** - Git for version control, not file management

---

## Examples of Proper Usage

### ✅ Correct: Explicit Worktree Creation

```bash
# User explicitly wants a worktree and confirms understanding
git worktree add ../feature-branch feature-branch --i-understand-irreversible
```

### ✅ Correct: Using File System Tools

```bash
# Creating directory (not a git operation)
mkdir new-project-dir
cd new-project-dir
git init
```

### ✅ Correct: Using GitHub CLI

```bash
# Cloning with appropriate tool
gh repo clone user/repo
```

### ❌ Incorrect: Implicit Git Creation

```bash
# Claude tries to create worktree without explicit intent
git worktree add ../temp-branch temp-branch
# BLOCKED: Missing --i-understand-irreversible flag
```

---

## Integration with Existing Safety Hooks

This enhancement works alongside existing git safety hooks:

| Hook | Scope | Event |
|------|-------|-------|
| `PreToolUse_destructive_git_guard.py` | Destructive + Creative git/gh operations | PreToolUse |
| `PreToolUse_git_safety.py` | Worktree cross-contamination | PreToolUse |
| `.git/hooks/pre-commit` | Python cache cleanup | Git hook |
| `.git/hooks/post-checkout` | Python cache cleanup | Git hook |

---

## Configuration

### Bypass Mechanism

If you need to disable this hook:

**Temporary bypass:**
```bash
export CONSTITUTIONAL_HOOKS_BYPASS=1
```

**Permanent bypass:**
Edit `P:\.claude/settings.json` and remove the hook importer line from PreToolUse hooks.

### Approval Flag

To allow a creative operation, add the approval flag:
```bash
git worktree add <path> <branch> --i-understand-irreversible
```

---

## Files Modified

1. **`P:\.claude\hooks/PreToolUse_destructive_git_guard.py`** - Enhanced with creation operation blocking
2. **`P:\.claude\hooks\tests/test_git_creation_blocking.py`** - Created new test suite
3. **`P:\.claude\hooks/GIT_CREATION_BLOCKING_SUMMARY.md`** - This documentation

---

## Verification

Test the hook is working:

```bash
# Test 1: Verify worktree creation is blocked
echo '{"tool_name":"Bash","tool_input":{"command":"git worktree add ../feature-branch feature-branch"}}' | python P:\.claude\hooks\PreToolUse_destructive_git_guard.py
# Expected: Exit code 2, "GIT IS NOT A FILE SYSTEM TOOL" in output

# Test 2: Verify git init is blocked
echo '{"tool_name":"Bash","tool_input":{"command":"git init new-repo"}}' | python P:\.claude\hooks\PreToolUse_destructive_git_guard.py
# Expected: Exit code 2, blocked message

# Test 3: Verify approval flag works
echo '{"tool_name":"Bash","tool_input":{"command":"git worktree add ../feature-branch feature-branch --i-understand-irreversible"}}' | python P:\.claude\hooks\PreToolUse_destructive_git_guard.py
# Expected: Exit code 0 (allowed)
```

---

## Future Enhancements

Possible future improvements (not implemented):

1. **Scope validation** - Check if worktree path is within project bounds
2. **Clone destination validation** - Warn about cloning to unexpected locations
3. **Branch naming policies** - Enforce branch naming conventions
4. **Worktree cleanup detection** - Suggest removing stale worktrees
5. **Integration with `/git` skill** - Automatic worktree management

---

## Conclusion

✅ **Hook enhanced to protect against inappropriate git file/folder creation**

✅ **All 30 tests passing (13 original + 17 new)**

✅ **Clear distinction between destructive and creative operations**

✅ **Helpful alternative suggestions for each blocked operation**

✅ **Prevents git from being used as a file system tool**

**Implementation Date:** 2026-03-08
**Test Status:** All tests passing (30/30)
**Integration Status:** Active and registered via hook importer
