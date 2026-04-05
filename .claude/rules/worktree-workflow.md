# Git Worktree Path Awareness

CRITICAL: When working in a git worktree, ALL edits MUST use the worktree path prefix.

## Detection

You are in a worktree if the current working directory contains worktrees followed by a name.

## Required Behavior

WRONG: Editing main branch directly at P:/projects/yt-fts/src/

RIGHT: Editing worktree version at P:/worktrees/w1t4/projects/yt-fts/src/

## Workflow

1. Make changes in worktree - Edit files with worktree path prefix
2. Commit in worktree - git commit within worktree
3. Sync to main - User invokes git-sync to merge worktree to main
4. NEVER edit main directly while worktree is active

## Verification

After any file edit, run git status and git diff HEAD to verify changes are in the worktree.

## Why This Matters

- Edits to main branch get overwritten during rebase and sync operations
- Worktree is the source of truth for ongoing work
- git-sync merges worktree to main, not the reverse
