# Beads Setup Guide

Complete guide for installing and configuring Beads (bd) task tracker on Windows 11 with multi-worktree setup.

## Overview

Beads is a distributed, git-backed task tracker for AI-assisted development. This system uses a **shared database** architecture where all worktrees use `P:\.beads\` as the single source of truth.

## Installation

### 1. Install Beads Binary

**The npm package is broken on Windows.** Use the Windows binary instead:

```powershell
# Download latest Windows binary
$url = "https://github.com/steveyegge/beads/releases/download/v0.49.0/beads_0.49.0_windows_amd64.zip"
Invoke-WebRequest -Uri $url -OutFile $env:TEMP/bd.zip
Expand-Archive -Path $env:TEMP/bd.zip -DestinationPath $env:TEMP/bd_extract

# Install to PATH
Copy-Item "$env:TEMP/bd_extract/bd.exe" "C:\Users\$env:USERNAME\AppData\Roaming\npm\bd.exe"

# Remove old npm wrappers (if present)
Remove-Item "C:\Users\$env:USERNAME\AppData\Roaming\npm\bd" -ErrorAction SilentlyContinue
Remove-Item "C:\Users\$env:USERNAME\AppData\Roaming\npm\bd.cmd" -ErrorAction SilentlyContinue
Remove-Item "C:\Users\$env:USERNAME\AppData\Roaming\npm\bd.ps1" -ErrorAction SilentlyContinue

# Verify
bd --version
```

### 2. Initialize Shared Database

From the main repository:

```powershell
cd P:\
bd init --quiet
```

This creates `P:\.beads\` with:
- `beads.db` - SQLite database
- `issues.jsonl` - Git-backed storage
- `metadata.json` - Configuration

### 3. Configure Redirect Files

**Main repo redirect** (self-reference for completeness):

```powershell
mkdir P:\.beads
echo "P:\.beads" > P:\.beads\redirect
```

**Worktree redirects** (automatically inherited via git):

```powershell
# Each worktree gets this automatically from git:
# P:/worktrees/wXtX/.beads/redirect → "P:\.beads"
```

### 4. Commit Redirect to Git

```powershell
cd P:\
echo ".beads/" >> .gitignore
echo "!.beads/redirect" >> .gitignore
git add .beads/redirect .gitignore
git commit -m "Add beads redirect for shared task database"
```

Now all new worktrees automatically get the redirect file.

### 5. Install Claude Code Hooks

```powershell
cd P:\
bd setup claude
```

This adds to `C:\Users\brsth\.claude\settings.json`:

```json
{
  "hooks": {
    "SessionStart": { "command": "bd prime" },
    "PreCompact": { "command": "bd prime" }
  }
}
```

## Architecture

```
P:\                              # Main repository
├── .beads/                      # Shared task database
│   ├── beads.db                # SQLite database
│   ├── issues.jsonl            # Git storage
│   ├── redirect                # "P:\.beads"
│   └── metadata.json
│
└── worktrees/
    ├── w1t1/.beads/redirect   → "P:\.beads"
    ├── w1t2/.beads/redirect   → "P:\.beads"
    ├── w1t3/.beads/redirect   → "P:\.beads"
    └── w2t1/.beads/redirect   → "P:\.beads"
```

## Usage

### From Any Worktree

```bash
# Show ready (unblocked) tasks
bd ready

# Create new task
bd create "Fix auth bug" -p 1

# List all tasks
bd list

# Show task details
bd show <id>

# Close task
bd close <id>
```

### Dependencies

```bash
# Add dependency (task B blocks task A)
bd dep add <task-a> <task-b>

# Show dependency tree
bd show <id>
```

### Context Injection

Claude Code automatically runs `bd prime` on session start, injecting:
- Ready work
- In-progress tasks
- Recent completions
- Top blockers

## Troubleshooting

### "npm install @beads/bd fails"

**Problem:** npm package has broken binary download URLs on Windows.

**Solution:** Use manual binary download (see step 1 above).

### "cannot run bd init from within a git worktree"

**Problem:** Running init from worktree instead of main repo.

**Solution:** Run `bd init` from `P:\` (main repository).

### "No beads.db found"

**Problem:** Database not initialized or incorrect redirect path.

**Solution:**
```bash
# Check redirect file content
cat P:/worktrees/w2t1/.beads/redirect
# Should output: P:\.beads

# Check database exists
ls P:\.beads\beads.db
```

### Tasks not syncing between worktrees

**Problem:** Redirect file missing or incorrect.

**Solution:** Verify each worktree has `.beads/redirect` pointing to `P:\.beads`.

### Daemon crashes

**Problem:** Beads daemon uses Unix sockets (not available on Windows) in older versions.

**Solution:**
```bash
bd daemons killall
# Daemon auto-restarts on next command
```

## Maintenance

```bash
# Health check
bd doctor

# Compact old closed tasks (saves tokens)
bd compact --days 30

# Sync with git (if using sync-branch mode)
bd sync
```

## Version History

| Date | Version | Changes |
|------|---------|---------|
| 2026-01-22 | v0.49.0 | Initial setup, shared database architecture |

## References

- [Beads GitHub](https://github.com/steveyegge/beads)
- [Beads Documentation](https://github.com/steveyegge/beads/blob/main/docs)
- [Windows Installation Issues](../.beads/README.md)
