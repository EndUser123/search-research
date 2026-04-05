# Git Safety Enhancements for Windows 11 + Claude Code

**Implementation Date**: 2026-03-07
**Plan ID**: plan-20260307-git-safety-enhancements
**Status**: ✅ COMPLETE (All 5 phases implemented)

---

## Overview

This document describes the comprehensive git safety enhancements implemented to prevent data loss, cache-related bugs, and worktree accidents in Claude Code workflows on Windows 11.

**What was solved**:
- ✅ Stale Python bytecode cache causing "fixed source but still broken" bugs
- ✅ Worktree cross-contamination risk when modifying files across worktrees
- ✅ Outdated git usage patterns (`git checkout --` vs `git restore`)
- ✅ Missing automation for worktree management in multi-terminal workflows
- ✅ Suboptimal Windows git configuration causing performance issues

**Implementation Summary**: 5 phases, 9 tasks (T-002 through T-008)

---

## Phase 1: Python Cache Cleanup (T-003, T-004)

### Problem

Previous cache cleanup only worked in `.claude/hooks/` directory, missing cache in `packages/`, `src/`, and `scripts/`. This caused the bug experienced on 2026-03-07 where fixed source code still failed due to stale bytecode.

### Solution

**Enhanced post-checkout Hook** (T-003)
- **File**: `P:/.git/hooks/post-checkout`
- **Language**: Bash (fast, works in Git Bash on Windows)
- **Trigger**: Runs after `git checkout`, `git worktree add`, branch switches
- **Action**: Removes all `__pycache__/` directories, `.pyc`, and `.pyo` files
- **Performance**: <500ms per checkout
- **Logging**: Set `GIT_PYCACHE_CLEANUP_VERBOSE=true` to see cleanup messages

**Enhanced pre-commit Hook** (T-004)
- **File**: `P:/.git/hooks/pre-commit`
- **Function**: `clear_pycache()` (expanded scope)
- **Scope**: `packages/`, `src/`, `.claude/hooks/`, `scripts/`
- **Behavior**: Fails open (cleanup errors don't block commits)
- **Logging**: Optional via `GIT_PYCACHE_CLEANUP_VERBOSE=true`

### Usage

```bash
# Normal operation (automatic - no action needed)
git checkout main  # Cache automatically cleaned

# Enable verbose logging to see what's being cleaned
export GIT_PYCACHE_CLEANUP_VERBOSE=true
git checkout main
# Output: [post-checkout] Cleaning Python cache files...
#         [post-checkout] Python cache cleanup complete

# Pre-commit cleanup (automatic)
git commit -m "fix: update imports"
# Cache cleaned before commit if present
```

### Troubleshooting

**Cache not being cleaned?**
```bash
# Check if post-checkout hook exists and is executable
ls -la .git/hooks/post-checkout
# Should show: -rwxr-xr-x (executable)

# Test manually
bash .git/hooks/post-checkout
```

**Slow checkouts?**
- Normal performance: <500ms per checkout
- If slower, check for large `__pycache__` directories
- Profile with: `time bash .git/hooks/post-checkout`

**See also**: `P:/__csf/.staging/cache_bug_investigation_20260307.md` for complete root cause analysis

---

## Phase 2: Worktree Cross-Checks (T-002)

### Problem

When working with multiple git worktrees, it's easy to accidentally modify files in the wrong worktree (e.g., restoring a file in worktree A while targeting a file in worktree B). This causes confusion and potential data loss.

### Solution

**Worktree Cross-Contamination Check**
- **File**: `P:/.claude/hooks/PreToolUse_git_safety.py`
- **Function**: `check_worktree_cross_contamination()`
- **Trigger**: Before git commands that operate on files (restore, checkout, etc.)
- **Action**: Blocks operations targeting files outside current worktree
- **Bypass**: Add `--allow-cross-worktree` to user message

**How it works**:
1. Detects current worktree using `worktree_helper.py`
2. Parses git command to extract target file paths
3. Validates paths are within current worktree boundaries
4. Blocks with clear error message if violations detected

### Usage

**Blocked operation example**:
```bash
# In worktree P:/.claude/worktrees/ai-task-20260307-143000
git restore packages/debugRCA/src/debug_rca/__pycache__

# Output:
# ⛔ CROSS-WORKTREE ACCESS DETECTED
#
# This git operation targets 1 file(s) outside your current worktree:
#   Current worktree: P:/.claude/worktrees/ai-task-20260307-143000
#
#   • packages/debugRCA/src/debug_rca/__pycache__
#
# Cross-worktree operations can cause confusion and data loss.
# Each worktree should operate on its own files independently.
#
# To bypass: Add --allow-cross-worktree to your message.
```

**Safe operation example**:
```bash
# In worktree P:/.claude/worktrees/ai-task-20260307-143000
git restore file.py  # ✅ Allowed (within current worktree)

# Switch to target worktree first
cd P:/.claude/worktrees/other-worktree
git restore file.py  # ✅ Allowed (now in correct worktree)
```

**Bypass example** (use sparingly):
```bash
# "I understand the risks, proceed anyway"
git restore ../other-worktree/file.py --allow-cross-worktree
```

### Troubleshooting

**False positive - legitimate cross-worktree operation?**
- Use bypass flag: `--allow-cross-worktree`
- Consider if operation should be in target worktree instead

**Worktree detection failing?**
```bash
# Check worktree helper is available
python -c "from hooks.__lib.worktree_helper import get_current_worktree; print(get_current_worktree())"

# Should print current worktree path or main repo path
```

**See also**: `P:/.claude/hooks/__lib/worktree_helper.py` for worktree detection implementation

---

## Phase 3: Git Restore Suggestions (T-002)

### Problem

The legacy `git checkout -- file` pattern is unclear and has multiple meanings (branch switching, file restoration, detached HEAD). Modern Git (2.23+) provides clearer alternatives: `git restore` for files, `git switch` for branches.

### Solution

**Git Restore Suggestion**
- **File**: `P:/.claude/hooks/PreToolUse_git_safety.py`
- **Function**: `suggest_git_restore()`
- **Trigger**: Detects `git checkout -- file` pattern
- **Action**: Advisory suggestion to use `git restore file` instead
- **Bypass**: Add `--allow-legacy-checkout` to suppress suggestion
- **Behavior**: Never blocks, only advises

### Usage

**Legacy pattern detected**:
```bash
git checkout -- file.py

# Output:
# 💡 SUGGESTION: Use modern 'git restore' instead of 'git checkout --'
#
# Detected: git checkout -- file.py
# Recommended: git restore file.py
#
# Why 'git restore' is better:
#   • Purpose-built for restoring working tree files
#   • Clearer intent (restore vs checkout's multiple meanings)
#   • Separated from branch switching (git switch)
#   • Safer: won't accidentally create branches
#
# Migration:
#   git checkout -- file.py
#   → git restore file.py
#
# To suppress this suggestion: Add --allow-legacy-checkout to your message.
```

**Modern pattern** (recommended):
```bash
git restore file.py  # ✅ Clear, modern, safe
```

**Multiple files**:
```bash
# Legacy
git checkout -- file1.py file2.py file3.py

# Modern
git restore file1.py file2.py file3.py
```

**With commit specification** (still needs checkout):
```bash
# Restore from specific commit (checkout is correct here)
git checkout HEAD~1 -- file.py

# But if restoring to current commit, use restore:
git restore file.py  # Simpler when you want current commit version
```

**Bypass example** (if you prefer legacy pattern):
```bash
git checkout -- file.py --allow-legacy-checkout
```

### Migration Guide

| Old Pattern | New Pattern | When to Use |
|-------------|-------------|-------------|
| `git checkout -- file` | `git restore file` | Restore to current commit |
| `git checkout branch -- file` | `git restore --source branch file` | Restore from specific branch |
| `git checkout branch` | `git switch branch` | Switch branches |
| `git checkout -b new-branch` | `git switch -c new-branch` | Create and switch to new branch |

---

## Phase 4: PowerShell Worktree Automation (T-005, T-006, T-007)

### Problem

Creating and managing git worktrees for parallel task workflows is tedious and error-prone. Manual worktree creation leads to inconsistent naming, forgotten cleanup, and cache-related issues.

### Solution

**Three PowerShell scripts** in `P:/scripts/git/`:

#### 1. New-ClaudeWorktree.ps1 (T-005)

**Purpose**: Create new Claude Code worktree with automatic setup

**Features**:
- Auto-generates task name: `ai-task-YYYYMMDD-HHMMSS`
- Creates branch: `ai/ai-task-YYYYMMDD-HHMMSS`
- Worktree location: `P:/.claude/worktrees/ai-task-YYYYMMDD-HHMMSS`
- Automatically cleans Python cache
- Checks for existing worktrees (prevents duplicates)

**Usage**:
```powershell
# Default (auto-generated task name)
.\New-ClaudeWorktree.ps1
# Creates: P:/.claude/worktrees/ai-task-20260307-150000
# Branch: ai/ai-task-20260307-150000

# Custom task name
.\New-ClaudeWorktree.ps1 -Task "fix-auth-bug"
# Creates: P:/.claude/worktrees/fix-auth-bug
# Branch: ai/fix-auth-bug

# Custom branch name
.\New-ClaudeWorktree.ps1 -Task "experiment" -Branch "feature/experiment-123"
# Creates: P:/.claude/worktrees/experiment
# Branch: feature/experiment-123
```

**Output**:
```
✅ Created worktree: P:\.claude\worktrees\ai-task-20260307-150000
📍 Branch: ai/ai-task-20260307-150000
🧹 Python cache cleaned
💡 Ready to start work!
```

#### 2. Status-AllWorktrees.ps1 (T-006)

**Purpose**: Show all Claude Code worktrees with status

**Features**:
- Lists all worktrees in `P:/.claude/worktrees/`
- Shows branch name and clean/dirty status
- Color-coded output (PowerShell 7+)

**Usage**:
```powershell
.\Status-AllWorktrees.ps1
```

**Output**:
```
Claude Code Worktrees Status
============================

✅ P:\.claude\worktrees\ai-task-20260307-143000
   Branch: ai/ai-task-20260307-143000
   Status: Clean (no uncommitted changes)

⚠️  P:\.claude\worktrees\ai-task-20260307-150000
   Branch: ai/ai-task-20260307-150000
   Status: Dirty (3 modified files)

✅ P:\.claude\worktrees\fix-auth-bug
   Branch: ai/fix-auth-bug
   Status: Clean (no uncommitted changes)

Total: 3 worktrees (2 clean, 1 dirty)
```

#### 3. Cleanup-ClaudeWorktrees.ps1 (T-007)

**Purpose**: Remove old Claude Code worktrees safely

**Features**:
- **Dry-run mode by default** (shows what would be deleted)
- Removes worktree and associated branch
- Safe cleanup (prevents accidental data loss)
- Prompts for confirmation before actual deletion

**Usage**:
```powershell
# Preview mode (safe - shows what would be deleted)
.\Cleanup-ClaudeWorktrees.ps1
# Output:
# Would remove: P:\.claude\worktrees\ai-task-20260307-140000 [ai/ai-task-20260307-140000]
# Would remove: P:\.claude\worktrees\ai-task-20260307-130000 [ai/ai-task-20260307-130000]
# Run with -DryRun \$false to actually remove these worktrees.

# Actual cleanup (removes worktrees)
.\Cleanup-ClaudeWorktrees.ps1 -DryRun \$false
# Output:
# 🗑️ Removed: P:\.claude\worktrees\ai-task-20260307-140000
# 🗑️ Removed: P:\.claude\worktrees\ai-task-20260307-130000
```

**Safety features**:
- Always previews first (dry-run)
- Only removes worktrees in `P:/.claude/worktrees/` (never main repo)
- Requires explicit `-DryRun $false` to actually delete

### Workflow Examples

**Parallel task workflow**:
```powershell
# Terminal 1: Fix auth bug
.\New-ClaudeWorktree.ps1 -Task "fix-auth-bug"
cd P:\.claude\worktrees\fix-auth-bug
# ... work on auth bug ...

# Terminal 2: Refactor database (simultaneously)
.\New-ClaudeWorktree.ps1 -Task "refactor-db"
cd P:\.claude\worktrees\refactor-db
# ... work on database refactor ...

# Check status
.\Status-AllWorktrees.ps1

# After merging both tasks, clean up
.\Cleanup-ClaudeWorktrees.ps1 -DryRun \$false
```

**Experiment workflow**:
```powershell
# Create experiment branch
.\New-ClaudeWorktree.ps1 -Task "experiment-new-feature" -Branch "experiment/new-api"
cd P:\.claude\worktrees\experiment-new-feature

# ... experiment with new API ...

# If experiment fails:
.\Cleanup-ClaudeWorktrees.ps1 -DryRun \$false  # Remove worktree
git branch -D experiment/new-api  # Remove branch

# If experiment succeeds:
git checkout main
git merge experiment/new-api
.\Cleanup-ClaudeWorktrees.ps1 -DryRun \$false
```

### Troubleshooting

**PowerShell execution policy error?**
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Worktree already exists?**
```powershell
# Script detects this and shows existing worktree
.\New-ClaudeWorktree.ps1 -Task "existing-task"
# Output: ❌ Worktree exists: P:\.claude\worktrees\existing-task
#         Switching to existing worktree...
```

**Cache not being cleaned?**
- Check script has permission to run `bash -c "find ..."`
- Test manually: `bash -c "find . -type d -name __pycache__ -delete"`

---

## Phase 5: Windows Git Config (T-008)

### Problem

Default Git configuration on Windows 11 is suboptimal for Claude Code workflows, causing performance issues, line ending pollution, and compatibility problems.

### Solution

**One-time Windows git configuration script**
- **File**: `P:/__csf/.staging/apply-git-config.ps1`
- **Scope**: Global git configuration (`~/.gitconfig`)
- **Safe**: Only sets optimal values, no destructive changes

### Usage

```powershell
# Apply Windows git optimizations (one-time setup)
pwsh P:/__csf/.staging/apply-git-config.ps1

# Verify settings
git config --global --list
```

### Settings Applied

**Core settings**:
```bash
core.autocrlf=input          # LF only (no CRLF pollution)
core.filemode=false          # Ignore Windows chmod noise
core.preloadindex=true       # Faster git status
core.longpaths=true          # Windows 260 char path limit
init.defaultBranch=main      # Claude expects 'main'
pull.rebase=false            # Safer merges
```

**Performance optimizations**:
```bash
diff.algorithm=histogram     # Faster diffs
status.submoduleSummary=false # Less noise in status
```

**Why these settings?**

| Setting | Problem Solved | Benefit |
|---------|----------------|---------|
| `core.autocrlf=input` | CRLF line endings in commits | Clean LF line endings in repo |
| `core.filemode=false` | chmod noise in git status | No "mode change" spam on Windows |
| `core.preloadindex=true` | Slow git status | Faster index operations |
| `core.longpaths=true` | 260 char path limit | Support long paths (common in Windows) |
| `diff.algorithm=histogram` | Slow git diff | Better performance on large files |
| `init.defaultBranch=main` | Default branch varies | Consistent with Claude Code expectations |

### Verification

```bash
# Check all applied settings
git config --global --list | grep -E "(autocrlf|filemode|preloadindex|longpaths|defaultBranch|diff.algorithm|status.submoduleSummary)"

# Expected output:
# core.autocrlf=input
# core.filemode=false
# core.preloadindex=true
# core.longpaths=true
# init.defaultbranch=main
# diff.algorithm=histogram
# status.submodulesummary=false
```

### Rollback

If you need to revert any setting:
```bash
# Example: revert autocrlf setting
git config --global --unset core.autocrlf

# Revert all settings (manual)
git config --global --edit
# Remove the relevant sections from ~/.gitconfig
```

---

## Quick Reference

### Bypass Flags

| Flag | Purpose | Use Case |
|------|---------|----------|
| `--allow-cross-worktree` | Bypass worktree cross-check | Legitimate cross-worktree operation (rare) |
| `--allow-legacy-checkout` | Suppress git restore suggestion | Prefer legacy checkout pattern |

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `GIT_PYCACHE_CLEANUP_VERBOSE` | Enable cache cleanup logging | `false` (quiet) |

### File Locations

| Component | Location |
|-----------|----------|
| Worktree cross-checks | `P:/.claude/hooks/PreToolUse_git_safety.py` |
| Git restore suggestions | `P:/.claude/hooks/PreToolUse_git_safety.py` |
| post-checkout hook | `P:/.git/hooks/post-checkout` |
| pre-commit hook | `P:/.git/hooks/pre-commit` |
| Worktree automation | `P:/scripts/git/*.ps1` |
| Git config script | `P:/__csf/.staging/apply-git-config.ps1` |
| Worktree helper library | `P:/.claude/hooks/__lib/worktree_helper.py` |
| Cache bug investigation | `P:/__csf/.staging/cache_bug_investigation_20260307.md` |

### Performance Targets

| Component | Max Latency | Measurement Method |
|-----------|-------------|-------------------|
| PreToolUse hooks (git_safety.py) | 100ms | Python `time.process_time()` |
| post-checkout hook | 500ms | Bash `time` command |
| pre-commit hook | 1s | Bash `time` command |
| PowerShell scripts | 5s | PowerShell `Measure-Command` |

---

## Troubleshooting

### Common Issues

**Issue**: "post-checkout hook not running"
```bash
# Check hook exists and is executable
ls -la .git/hooks/post-checkout
# Should show: -rwxr-xr-x (executable)

# If not executable, fix permissions
chmod +x .git/hooks/post-checkout
```

**Issue**: "Worktree cross-check false positive"
```bash
# Check worktree detection
python -c "from hooks.__lib.worktree_helper import get_current_worktree; print(get_current_worktree())"

# Use bypass if needed
git restore file.py --allow-cross-worktree
```

**Issue**: "PowerShell scripts blocked by execution policy"
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

**Issue**: "Cache cleanup slow"
```bash
# Profile the hook
time bash .git/hooks/post-checkout

# Check for large __pycache__ directories
du -sh */__pycache__
```

**Issue**: "Git restore suggestion annoying"
```bash
# Add bypass flag to suppress
git checkout -- file.py --allow-legacy-checkout
```

### Debug Mode

Enable verbose logging for cache cleanup:
```bash
export GIT_PYCACHE_CLEANUP_VERBOSE=true
git checkout main
```

Check hook registration:
```bash
python P:/.claude/hooks/tests/test_hook_registration.py
```

---

## Related Documentation

- **Implementation Plan**: `P:/__csf/.staging/plan-20260307-git-safety-enhancements.md`
- **Cache Bug Investigation**: `P:/__csf/.staging/cache_bug_investigation_20260307.md`
- **Hook Architecture**: `P:/.claude/hooks/CLAUDE.md`
- **Worktree Helper**: `P:/.claude/hooks/__lib/worktree_helper.py`

---

## Summary

**What changed**:
- ✅ Automatic Python cache cleanup after branch switches
- ✅ Worktree cross-contamination prevention
- ✅ Modern git pattern suggestions (`git restore`)
- ✅ Automated worktree management (create, status, cleanup)
- ✅ Windows-specific git optimizations

**Benefits**:
- ✅ No more "fixed source but still broken" cache bugs
- ✅ Safer multi-worktree workflows
- ✅ Clearer git commands (restore vs checkout)
- ✅ Faster worktree creation and cleanup
- ✅ Better git performance on Windows

**Maintenance**:
- All hooks individually reversible
- Comprehensive test coverage
- Clear documentation for troubleshooting

---

**End of Documentation**
