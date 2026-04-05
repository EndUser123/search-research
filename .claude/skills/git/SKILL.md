---
name: git
version: "1.0.0"
status: "stable"
category: vcs
description: Git sync with health check, auto-fix, smart conflict resolution, and worktree management.
triggers:
  - /git
args:
  - --verbose: Show full output during health check and sync
  - -v: Shorthand for --verbose
  - --health: Check configuration only (don't sync)
  - --fix: Auto-fix issues before syncing
  - --tasks-only: Check Tasks configuration only
  - --worktree: Worktree management mode (list, add, remove, prune)
  - --no-resolve: Skip automatic conflict resolution (manual mode)
execution:
  directive: "If --worktree: manage worktrees. Otherwise: run health check, auto-fix if needed, sync with smart conflict resolution, validate post-merge. Context-aware for main vs worktree."
  default_args: ""
  examples:
    - "/git"
    - "/git --verbose"
    - "/git --health"
    - "/git --fix"
    - "/git --worktree"
    - "/git --worktree add feature-name"
    - "/git --worktree remove feature-name"
    - "/git --worktree prune"
    - "/git --no-resolve"
do_not:
  - summarize this skill
  - search for sync.py implementation
  - use alternative approaches
---

# Git: Sync + Worktree + Smart Conflict Resolution

## Quick Usage

```powershell
# Sync with health check (default)
/git

# Health check only (no sync)
/git --health

# Auto-fix issues then sync
/git --fix

# Verbose output
/git --verbose

# Check specific layer
/git --health --tasks-only

# Worktree management
/git --worktree                # List all worktrees
/git --worktree add name       # Create new worktree
/git --worktree remove name    # Remove worktree
/git --worktree prune          # Clean up stale worktrees

# Manual conflict resolution
/git --no-resolve              # Skip auto-resolution, handle manually
```

---

## ⚡ EXECUTE

**MANDATORY ACTION: Run sync.py for health check + smart sync + worktree management**

```bash
# From any directory, invoke:
python .claude/skills/git/sync.py [args]

# Or with full path:
python P:/.claude/skills/git/sync.py [args]
```

The `sync.py` script handles:
- Environment detection (main vs worktree)
- Auto-fix for missing configurations
- Bidirectional sync (worktree ↔ main)
- Worktree management (list, add, remove, prune)
- Smart conflict resolution (file-type based)
- Post-merge validation

**Python implementation:** See `sync.py` for full source code.

---

## What It Does

### Worktree Mode (--worktree)
| Action | Command | Description |
|--------|---------|-------------|
| List | `/git --worktree` | Show all worktrees with current (*) |
| Add | `/git --worktree add <name>` | Create worktree at `P:/worktrees/<name>` |
| Remove | `/git --worktree remove <name>` | Remove worktree (keeps branch) |
| Prune | `/git --worktree prune` | Clean up stale worktrees |

### Health Check Phase
- Detects location (main vs worktree)
- Checks `.claude/settings.json` and `CLAUDE_CODE_TASK_LIST_ID`
- Reports issues clearly

### Auto-Fix Phase (--fix)
- Creates missing `.claude/settings.json`

### Sync Phase (default)
- Cleans stale git locks
- Auto-commits uncommitted changes
- Merges main → worktree (pull)
- Merges worktree → main (push)
- **Auto-resolves conflicts** based on file type
- Post-merge validation
- Skips unnecessary merges (optimization)

### Conflict Resolution (automatic)
| File Pattern | Strategy | Rationale |
|--------------|----------|-----------|
| `.claude/sessions/*` | Ours (keep local) | Session state is local, never shared |
| `*.py`, `*.md`, `*.json`, code | Theirs (use incoming) | Committed code in main is source of truth |
| `.env`, config files | Manual | May need both sides |

Use `/git --no-resolve` to skip auto-resolution and handle conflicts manually.

---

## References

| File | Contents |
|------|----------|
| `references/post-sync-verification.md` | Post-sync verification commands and checklist |
| `references/user-home-backup.md` | User-home backup setup, automation, and recovery |

---

**Version:** 4.2
**Updated:** March 7, 2026
**Status:** Production ready - sync + worktree + smart conflict resolution + verification + user-home backup
