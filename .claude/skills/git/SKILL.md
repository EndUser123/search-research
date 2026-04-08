---
name: git
version: "2.0.0"
status: "stable"
category: vcs
enforcement: advisory
description: Git sync with multi-repo discovery, auto-push for main, interactive selection for others, worktree management, and smart conflict resolution.
triggers:
  - /git
args:
  - --verbose: Show full output during health check and sync
  - -v: Shorthand for --verbose
  - --health: Check configuration only (don't sync)
  - --fix: Auto-fix issues before syncing
  - --repos: Filter repos by type (all, packages, .claude, mcp, non-main)
  - --select: Select repos to push by index (e.g., "1,3" or "all")
  - --worktree: Worktree management mode (list, add, remove, prune)
  - --no-resolve: Skip automatic conflict resolution (manual mode)
execution:
  directive: "If --worktree: manage worktrees. Otherwise: discover all git repos, auto-sync main repo (commit + push), use --select for non-interactive push or present interactive selection. Non-interactive mode skips selection."
  default_args: ""
  examples:
    - "/git"
    - "/git --verbose"
    - "/git --health"
    - "/git --repos packages"
    - "/git --select 1,3"
    - "/git --select all"
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

# Git: Multi-Repo Sync + Worktree Management

## Quick Usage

```powershell
# Sync all repos (main auto-push, others interactive)
/git

# Health check - see all repos status
/git --health

# Verbose output
/git --verbose

# Filter to specific repo types
/git --repos packages        # Only package repos
/git --repos .claude         # Only .claude internal repos

# Push specific repos by index (use with /git --health to see indices)
/git --select 1,3            # Push repos 1 and 3
/git --select all            # Push all repos with unpushed commits

# Worktree management
/git --worktree                # List all worktrees
/git --worktree add name       # Create new worktree
/git --worktree remove name    # Remove worktree
/git --worktree prune          # Clean up stale worktrees
```

---

## ⚡ EXECUTE

**MANDATORY ACTION: Run sync.py for multi-repo sync + worktree management**

```bash
python P:/.claude/skills/git/sync.py [args]
```

---

## What It Does

### Multi-Repo Discovery
Discovers all `.git` directories under `P:/`:
- **Main repo** (`P:/.git`) - auto-sync, auto-push
- **Package repos** (`packages/*/.git`) - interactive selection
- **MCP repos** (`packages/.mcp/*/.git`) - interactive selection
- **Internal repos** (`.claude/hooks/`, `.claude/skills/*/`) - interactive selection

### Main Repo (Auto-Push)
- Auto-commits uncommitted changes with scoped commit messages
- Auto-pushes to remote (dynamic remote/branch detection)
- On push failure: shows actionable error with remote URL and fix advice

### Non-Main Repos (Interactive Selection)
Presents numbered list of repos with unpushed commits:

```
Non-main repos with unpushed commits:

  [1] packages\claude-log - 3 commit(s) ahead
  [2] packages\reflect-system - 8 commit(s) ahead
  [3] .claude\hooks - 12 commit(s) ahead

Select repos to push (e.g., 1,3 or 1-3 or all): _
```

- `all` or `*` = push all
- `1-3` = range selection
- `1,3` = specific selection
- Empty = skip all

### Health Check (`--health`)
Shows all repos with their status:
- Commits ahead of remote
- No remote configured
- Up-to-date

### Worktree Mode (`--worktree`)
| Action | Command | Description |
|--------|---------|-------------|
| List | `/git --worktree` | Show all worktrees with current (*) |
| Add | `/git --worktree add <name>` | Create worktree at `P:/worktrees/<name>` |
| Remove | `/git --worktree remove <name>` | Remove worktree (keeps branch) |
| Prune | `/git --worktree prune` | Clean up stale worktrees |

### Push Error Handling
Push failures show actionable messages:
- Authentication errors: suggests manual `git push` to authenticate
- Rejected pushes: suggests pulling first
- Missing remote: shows which repos have no remote

---

**Version:** 2.0
**Updated:** April 8, 2026
**Status:** Production ready - multi-repo sync + auto-push main + interactive selection
