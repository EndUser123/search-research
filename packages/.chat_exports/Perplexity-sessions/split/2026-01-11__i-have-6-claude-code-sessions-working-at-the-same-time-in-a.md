---
title: "I have 6 claude code sessions working at the same time in a large repo.  Is there a best practice way that they can 'che"
date: "2026-01-11"
mode: "COPILOT"
uuid: "1de27352-9f35-4572-b680-f05bf6b76d75"
entry_count: 3
---

## Human

I have 6 claude code sessions working at the same time in a large repo.  Is there a best practice way that they can 'check out' and 'check in' code, so that other sessions don't have a conflict/race condition?

## Assistant

**Yes, the established best practice for coordinating multiple Claude Code sessions in a large repo is using Git worktrees.** This allows each session to work on an isolated branch in its own directory, eliminating file conflicts and race conditions without needing manual checkouts.[1][2]

## Git Worktrees Setup
Run `git worktree add ../session-feature-x feature-x` from your main repo directory to create a new worktree on branch `feature-x`.[2]
Launch Claude Code in each: `cd ../session-feature-x && claude`.[2]
Each session operates independently on non-overlapping tasks, like one refactoring auth while another builds UI components.[2]

## Integration Workflow
Sessions commit locally to their branches without interference.[3]
Merge via `git worktree remove ../session-feature-x` after review, or use PRs from feature branches.[2]
For Windows/PowerShell, script worktree creation with your multi-terminal setup for quick spins.

## Alternatives
- **Hooks in GitButler**: Auto-creates branches per session via Claude hooks, committing per chat round.[3][4]
- **File Locks**: Custom scripts for checkout/checkin, but less efficient than worktrees.[3]
Avoid shared directories to prevent model conflicts seen in your LiteLLM setups.[5][1]

## Human

wouldn't a slash command effectively do the same thing?  Or a few slash commands?  create the tree, work in the tree, merge to main, sync, etc?

## Assistant

**Slash commands can fully automate the Git worktree workflow, making it even more seamless than manual commands.** Users commonly define custom slash commands in `.claude/commands/` to handle creating worktrees, working on tasks, merging, and syncing—all from within a Claude Code session.[1][2][3]

## Defining Slash Commands
Create `.claude/commands/worktree.md` with instructions like: "Create a new git worktree for $ARGUMENTS: `git worktree add ../{branch} {branch}` where {branch} is a descriptive name from arguments."[2][3][4]
Claude executes via Bash tools, pulling latest main first and naming consistently (e.g., `/worktree signup-fix`).[5][6][2]
Project-scoped commands override user ones for repo-specific logic.[3]

## Full Workflow Commands
- **/worktree "task-name"**: Creates branch/worktree, suggests `cd ../task-name && claude` for new terminal.[7][2]
- **/merge-main**: Squash-merges PR, deletes branch, cleans worktree, pulls main.[6]
- **/sync**: `git pull main && git worktree prune` to update all.[1][6]
Invoke as `/worktree auth-refactor`—no manual git recall needed.[2]

## Benefits Over Manual
Automation reduces errors in your 6-session setup; natural language args fit your PowerShell multi-terminal flow.[6]
Combine with subagents for parallel work per tree.[8][1]
Test by asking Claude: "Create /worktree slash command for my repo."[9]

## Human

Do you see any issue or opportunity with this?

[Prompt Enhancements.](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)/
Here's a conversation I had with P: Library Recent I have 6 claude code sessions working at the same time in a large repo. Is there a best practice wa Is there an easy way to see in qbittorent 5.x how many seeds there are, before I spend quota trying what are some popular ways to mount a powerb
pasted
7:50 PM
I notice the user prompt is empty, so I cannot determine the primary language or provide an appropriate summary. Please provide the actual user prompt so I can create an accurate summary in the correct language.







System Understanding
This is workflow design for multi-session coordination—greenfield for enforcement mechanisms.
Core requirements:
Enforcement: Prevent accidental work on main
Sync timing: Know WHEN to sync, not just HOW
Merge discipline: Clean history without PR ceremony
Solution: Worktree-First Workflow
1. Enforcement: Guard Against Main
Option A: Pre-commit hook (lightweight)
bash
# .git/hooks/pre-commit
#!/bin/bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "⛔ Direct commits to main blocked. Use worktree."
  echo "   Run: /worktree <feature-name>"
  exit 1
fi
Option B: Claude Code hook (catches intent earlier)
Add to .claude/hooks/pre-tool-use.sh:
bash
#!/bin/bash
# Block file writes if in main worktree
if [ "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" = "main" ]; then
  if /"$TOOL_NAME" =~ ^(write; then
    echo '{"decision": "block", "reason": "Create worktree first: /worktree <name>"}'
    exit 0
  fi
fi
echo '{"decision": "allow"}'
Recommendation: Both. Pre-commit is backup; CC hook catches earlier.
2. Slash Commands
.claude/commands/worktree.md
markdown
# /worktree

Create isolated worktree for task. IMMEDIATELY:

1. Ensure main is current: `git checkout main && git pull`
2. Create worktree: `git worktree add ../wt-$ARGUMENTS $ARGUMENTS`
3. Report: "Worktree ready at ../wt-$ARGUMENTS. Start new terminal there."

Arguments: branch name (kebab-case, e.g., "auth-refactor")

If branch exists, attach to it instead of creating.
.claude/commands/sync.md
markdown
# /sync

Sync current worktree with main. IMMEDIATELY:

1. Stash uncommitted: `git stash push -m "sync-$(date +%s)"`
2. Fetch: `git fetch origin main`
3. Rebase: `git rebase origin/main`
4. Pop stash if exists: `git stash pop` (report conflicts if any)
5. Report status

DO NOT run on main branch—warn and abort.
.claude/commands/ship.md
markdown
# /ship

Merge current worktree to main (solo dev flow). IMMEDIATELY:

1. Verify not on main
2. Verify clean working tree (or offer to commit)
3. Switch to main: `cd ../main-repo && git checkout main && git pull`
4. Squash merge: `git merge --squash ../wt-$CURRENT_BRANCH`
5. Commit with message: "feat: $CURRENT_BRANCH" (editable)
6. Push: `git push origin main`
7. Cleanup: `git worktree remove ../wt-$CURRENT_BRANCH`
8. Report completion

Arguments: Optional commit message override
```

---

### 3. Sync Timing Rules

| Scenario | Action | Why |
|----------|--------|-----|
| Starting new work | `/worktree` (auto-syncs) | Fresh base |
| Work >4 hours old | `/sync` before continuing | Reduce merge pain |
| Before shipping | `/sync` then test | Catch conflicts early |
| Mid-task, main changed | **Don't sync** unless blocked | Avoid churn |
| Conflict reported | Resolve, then `/sync` | Clear state |

**Heuristic:** Sync at boundaries (start, before ship), not during flow.

---

### 4. Directory Structure
```
P:\projects\
├── my-repo/              # Main checkout (read-mostly)
├── wt-auth-refactor/     # Session 1 worktree
├── wt-ui-dashboard/      # Session 2 worktree
├── wt-api-endpoints/     # Session 3 worktree
└── ...
```

Each CC session launches in its worktree directory. Main stays clean.

---

### 5. Professional Solo Dev Merge Checklist

Before `/ship`:
```
[ ] Tests pass locally
[ ] No console.log/debug cruft
[ ] Commit message describes WHAT changed (not HOW)
[ ] Single logical change (split if >1 feature)
```

**Commit message format:**
```
feat: add user authentication flow
fix: resolve race condition in queue processing  
refactor: simplify config loading
No PR ceremony needed. Squash keeps history clean. Tag releases quarterly or at milestones.
Confidence
[HIGH] Git worktrees are established best practice for parallel work.
[MEDIUM] CC hook enforcement—depends on hook reliability in your setup.
[HIGH] Sync timing rules—standard rebase workflow.
Next Step
Create .claude/commands/worktree.md and test with: /worktree test-feature. Verify it creates the worktree and you can launch CC in it.
Note that we are on Windows 11 with PowerShell 7.5.4.  
P: is root
P:/__csf.nip is where all the claude workflows are that are not in P:/.claude
P:/projects is where the development projects are.
P:/.git is where git is.
What would you suggest for the worktree location?
8:56 PM
Analyzed repository structure and weighed worktree placement options.






Worktree Location Analysis
Given P:\ is the git repo root (P:.git exists), worktrees must be outside the main working tree but can be on the same drive.
Recommended: P:\__worktrees\
Reasoning:
Parallels your __csf.nip naming convention (double underscore = system/infra)
At root level, easy to find and clean
Clearly separate from P:\projects\ (actual project code)
Git worktrees work fine as subdirectories of the parent repo's drive
Structure:
P:\
├── .claude\              # CC runtime
├── .git\                 # Main repo git dir
├── __csf.nip\            # CSF framework
├── __worktrees\          # NEW: worktree home
│   ├── auth-refactor\
│   ├── hook-validation\
│   └── ui-dashboard\
└── projects\             # Project source
Updated Slash Command
.claude/commands/worktree.md
markdown
# /worktree

Create isolated worktree for task. IMMEDIATELY:
```powershell
# Ensure main is current
git checkout main
git pull origin main

# Create worktree (Windows path)
git worktree add "P:\__worktrees\$ARGUMENTS" -b $ARGUMENTS

# Report
Write-Host "Worktree ready at P:\__worktrees\$ARGUMENTS"
Write-Host "Launch new terminal: cd P:\__worktrees\$ARGUMENTS; claude"
```

Arguments: branch name (kebab-case, e.g., "auth-refactor")

If branch exists: `git worktree add "P:\__worktrees\$ARGUMENTS" $ARGUMENTS` (no -b)
```

### Gitignore Addition

Add to `P:\.gitignore`:
```
__worktrees/
This prevents worktree directories from appearing as untracked in the main repo.
Alternative Considered
LocationProsCons
P:\__worktrees\
Matches convention, root-level
None significant
P:\projects\wt-*\
Near related code
Pollutes projects folder
P:\.worktrees\
Hidden on Unix
Visible on Windows anyway
Different drive
Complete isolation
Complicates paths
Next Step
powershell
mkdir P:\__worktrees
Add-Content P:\.gitignore "`n__worktrees/"
Then test: /worktree test-branch
I usually run with 6 CC sessions, in w1t1..6 and w3t1..2
What should we call the worktrees?  The same name as the terminal session name?  Or something different?
8:58 PM
Weighed semantic naming against terminal mapping for worktree conventions.








Naming Analysis
Core tension: Terminals are ephemeral (restart, reassign), worktrees are persistent (survive sessions, become branches/history).
Recommendation: Semantic Names for Worktrees
P:\__worktrees\
├── auth-refactor\        # What the work IS
├── hook-validation\
├── api-cleanup\
└── test-harness\
Not wt-w1t3\ because:
Branch names end up in git log—feat: w1t3 means nothing in 2 weeks
If terminal crashes and you reopen in w1t5, the name is now wrong
Can't tell what work is in progress from directory listing
Track Terminal ↔ Worktree at Runtime
Option A: PowerShell prompt shows branch
Add to $PROFILE:
powershell
function prompt {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branch) {
        "$pwd [$branch]> "
    } else {
        "$pwd> "
    }
}
Result: P:\__worktrees\auth-refactor [auth-refactor]>
Option B: Terminal title
powershell
$host.UI.RawUI.WindowTitle = "CC: $(Split-Path -Leaf $pwd)"
Option C: Quick status command
.claude/commands/where.md:
markdown
# /where

Show current worktree context. IMMEDIATELY run:
```powershell
Write-Host "Directory: $pwd"
Write-Host "Branch: $(git rev-parse --abbrev-ref HEAD)"
Write-Host "Worktree: $(git worktree list --porcelain | Select-String 'worktree')"
```
```

---

### Workflow Mapping

When starting 6 sessions, you assign semantically:

| Terminal | Worktree | Task |
|----------|----------|------|
| w1t1 | `P:\__worktrees\auth-refactor` | Auth system |
| w1t2 | `P:\__worktrees\hook-validation` | Hook testing |
| w1t3 | `P:\__worktrees\api-cleanup` | API work |
| w1t4 | `P:\` (main) | Read-only reference |
| ... | ... | ... |

Keep one terminal on main for quick lookups without modifying.

---

### Naming Convention for Branches/Worktrees
```
{type}-{feature}

Types: feat, fix, refactor, test, docs, spike
Examples: feat-auth-flow, fix-race-condition, spike-new-db
Short, lowercase, hyphenated. Matches commit prefix convention.
Confidence
[HIGH] Semantic naming is standard practice.
[MEDIUM] Prompt/title modifications—depends on your terminal setup preferences.
Next Step
Pick Option A, B, or C for runtime tracking. I'd start with the prompt modification—lowest friction, always visible.
Option A is temporary?  Or terminal isolated?
9:00 PM
Examined persistence scope based on configuration location.



PowerShell Prompt Behavior
It depends where you put it:
LocationPersistenceScope
Run directly in terminal
Session only—gone on close
That terminal only
Add to $PROFILE
Permanent—survives restarts
All PowerShell terminals for your user
Add to project-specific script
On-demand
Terminals where you source it
Your Options
A1: Global (all terminals, permanent)
powershell
# Add to $PROFILE (run `notepad $PROFILE` to edit)
function prompt {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branch) { "$pwd [$branch]> " }
    else { "$pwd> " }
}
Every PowerShell window shows branch. Simple. Recommended.
A2: Project-specific (opt-in)
Create P:\__csf.nip\scripts\worktree-prompt.ps1:
powershell
function prompt {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branch) { "$pwd [$branch]> " }
    else { "$pwd> " }
}
Write-Host "Worktree prompt enabled"
Then source when wanted:
powershell
. P:\__csf.nip\scripts\worktree-prompt.ps1
More control, more friction.
A3: Session-only (testing)
Just paste the function directly—gone when terminal closes. Good for trying it out.
Recommendation
Start with A3 (paste to test), then move to A1 (add to $PROFILE) once you like it.
powershell
# Check your profile path
$PROFILE

# Create if doesn't exist
if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -Force }

# Edit
notepad $PROFILE
Ok, how should we implement?
9:01 PM
Architected comprehensive worktree workflow implementation strategy.



Implementation Plan
Reversibility: 1.25 (additive files, easy to remove)
Step 1: Directory + Gitignore
powershell
# Create worktree home
New-Item -ItemType Directory -Path "P:\__worktrees" -Force

# Add to gitignore
Add-Content -Path "P:\.gitignore" -Value "`n# Worktrees`n__worktrees/"
Step 2: Prompt Modification
powershell
# Test first (paste directly)
function prompt {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    if ($branch) { "$pwd [$branch]> " }
    else { "$pwd> " }
}
If you like it:
powershell
# Open profile for editing
if (!(Test-Path $PROFILE)) { New-Item -Path $PROFILE -ItemType File -Force }
notepad $PROFILE
Paste the function, save, restart terminals.
Step 3: Slash Commands
P:.claude\commands\worktree.md
markdown
# /worktree

Create isolated worktree for task. IMMEDIATELY execute:

1. Ensure on main and current:
```powershell
cd P:\
git checkout main
git pull origin main
```

2. Create worktree with branch:
```powershell
git worktree add "P:\__worktrees\$ARGUMENTS" -b $ARGUMENTS
```

3. Report:
```
✅ Worktree ready: P:\__worktrees\$ARGUMENTS
   Branch: $ARGUMENTS
   
   Next: Open new terminal and run:
   cd P:\__worktrees\$ARGUMENTS; claude
```

**Arguments:** Branch name in kebab-case (e.g., `feat-auth-flow`, `fix-race-condition`)

**If branch already exists:** Use `git worktree add "P:\__worktrees\$ARGUMENTS" $ARGUMENTS` (no -b flag)

**DO NOT** summarize this file or describe what worktrees are.
P:.claude\commands\sync.md
markdown
# /sync

Sync current worktree with main. IMMEDIATELY execute:

1. Verify not on main:
```powershell
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -eq "main") { Write-Error "Already on main. Nothing to sync."; return }
```

2. Stash any uncommitted work:
```powershell
git stash push -m "sync-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

3. Fetch and rebase:
```powershell
git fetch origin main
git rebase origin/main
```

4. Pop stash if exists:
```powershell
git stash pop 2>$null
```

5. Report status:
```powershell
git status --short
```

**If rebase conflicts:** Stop and report files. Do not auto-resolve.

**DO NOT** run this on main branch.
P:.claude\commands\ship.md
markdown
# /ship

Merge current worktree to main (solo dev squash flow). IMMEDIATELY execute:

1. Verify not on main:
```powershell
$branch = git rev-parse --abbrev-ref HEAD
if ($branch -eq "main") { Write-Error "Cannot ship from main."; return }
$worktreePath = $pwd.Path
```

2. Verify clean state:
```powershell
$status = git status --porcelain
if ($status) { 
    Write-Host "Uncommitted changes:" 
    git status --short
    Write-Host "`nCommit these first, then re-run /ship"
    return
}
```

3. Switch to main repo and merge:
```powershell
cd P:\
git checkout main
git pull origin main
git merge --squash $branch
```

4. Commit (use argument or branch name):
```powershell
$msg = if ("$ARGUMENTS") { "$ARGUMENTS" } else { "feat: $branch" }
git commit -m $msg
```

5. Push:
```powershell
git push origin main
```

6. Cleanup:
```powershell
git worktree remove $worktreePath --force
git branch -d $branch
```

7. Report:
```
✅ Shipped: $branch → main
   Commit: $msg
   Worktree removed: $worktreePath
```

**Arguments:** Optional commit message (default: "feat: {branch-name}")

**DO NOT** proceed if uncommitted changes exist.
P:.claude\commands\where.md
markdown
# /where

Show current worktree context. IMMEDIATELY execute:
```powershell
Write-Host "Directory: $pwd"
Write-Host "Branch:    $(git rev-parse --abbrev-ref HEAD)"
Write-Host "Status:    $(git status --short | Measure-Object -Line | Select-Object -Exp Lines) uncommitted files"
Write-Host ""
Write-Host "All worktrees:"
git worktree list
```

**DO NOT** add commentary. Just show the info.
Step 4: Main Protection (Optional but Recommended)
P:.git\hooks\pre-commit (no extension)
bash
#!/bin/bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "⛔ Direct commits to main blocked."
  echo "   Create worktree: /worktree <feature-name>"
  exit 1
fi
Make executable:
powershell
# Git hooks need to be executable (Git handles this on Windows)
# Just create the file - no chmod needed on Windows
Step 5: Verification
powershell
# Test worktree creation
cd P:\
# Then in Claude Code: /worktree test-setup

# Verify it created:
Get-ChildItem P:\__worktrees\

# Test from new terminal:
cd P:\__worktrees\test-setup
git status

# Cleanup test:
git worktree remove P:\__worktrees\test-setup
git branch -d test-setup
File Creation
Want me to create these files directly? I can use:
Desktop Commander to write to P:\.claude\commands\
Or output the content for you to copy
Which approach?
Can I copy them to a simpler model to implement?
9:05 PM
Consolidated implementation steps for seamless transfer.


Yes. Here's a consolidated handoff:
markdown
# Task: Implement Git Worktree Workflow

## Context
Windows 11, PowerShell 7.5.4. Git repo at P:\

## Create These Files

### 1. Directory
```powershell
New-Item -ItemType Directory -Path "P:\__worktrees" -Force
```

### 2. Append to P:\.gitignore
```
# Worktrees
__worktrees/
```

### 3. Create P:\.claude\commands\worktree.md
```markdown
# /worktree

Create isolated worktree for task. IMMEDIATELY execute:

1. Ensure on main and current:
git checkout main
git pull origin main

2. Create worktree with branch:
git worktree add "P:\__worktrees\$ARGUMENTS" -b $ARGUMENTS

3. Report:
✅ Worktree ready: P:\__worktrees\$ARGUMENTS
   Branch: $ARGUMENTS
   Next: cd P:\__worktrees\$ARGUMENTS; claude

Arguments: Branch name in kebab-case (e.g., feat-auth-flow)

If branch already exists: git worktree add "P:\__worktrees\$ARGUMENTS" $ARGUMENTS (no -b)

DO NOT summarize this file.
```

### 4. Create P:\.claude\commands\sync.md
```markdown
# /sync

Sync current worktree with main. IMMEDIATELY execute:

1. Verify not on main (abort if so)
2. git stash push -m "sync-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
3. git fetch origin main
4. git rebase origin/main
5. git stash pop (if stash exists)
6. git status --short

If rebase conflicts: Stop and report. Do not auto-resolve.

DO NOT run on main branch.
```

### 5. Create P:\.claude\commands\ship.md
```markdown
# /ship

Merge current worktree to main. IMMEDIATELY execute:

1. Verify not on main (abort if so)
2. Verify clean working tree (abort if uncommitted changes)
3. Save current path: $worktreePath = $pwd.Path
4. Save branch: $branch = git rev-parse --abbrev-ref HEAD
5. cd P:\
6. git checkout main && git pull origin main
7. git merge --squash $branch
8. git commit -m "$ARGUMENTS" (default: "feat: $branch")
9. git push origin main
10. git worktree remove $worktreePath --force
11. git branch -d $branch
12. Report completion

Arguments: Optional commit message

DO NOT proceed with uncommitted changes.
```

### 6. Create P:\.claude\commands\where.md
```markdown
# /where

Show current worktree context. IMMEDIATELY execute:

Write-Host "Directory: $pwd"
Write-Host "Branch: $(git rev-parse --abbrev-ref HEAD)"
git worktree list

DO NOT add commentary.
```

### 7. Create P:\.git\hooks\pre-commit (no extension)
```bash
#!/bin/bash
BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [ "$BRANCH" = "main" ] || [ "$BRANCH" = "master" ]; then
  echo "⛔ Direct commits to main blocked. Use /worktree"
  exit 1
fi
```

## Verify After Creation
```powershell
Test-Path P:\__worktrees
Test-Path P:\.claude\commands\worktree.md
Test-Path P:\.claude\commands\sync.md
Test-Path P:\.claude\commands\ship.md
Test-Path P:\.claude\commands\where.md
Test-Path P:\.git\hooks\pre-commit
```
Copy everything above. Hand to Claude Code or similar with "Implement this."

[Claude is AI and can make mistakes. Please double-check responses.](https://support.anthropic.com/en/articles/8525154-claude-is-providing-incorrect-or-misleading-responses-what-s-going-on)
[](https://claude.ai/project/019af216-64e8-729b-b960-1769b854af2b)

## Assistant

Looking at this workflow design, I see several **strong points** and a few **opportunities to strengthen it**:

## Strong Points ✅

1. **Semantic naming** (`feat-auth-flow` not `w1t1`) — survives restarts, readable in git history
2. **Enforcement at two levels** — pre-commit hook + CC hook catches mistakes early
3. **Clear sync heuristics** — start, before ship, mid-task-only-if-blocked
4. **PowerShell-native** — uses `Get-Date`, `Write-Host`, matches your environment
5. **Reversible** — all additive, easy to remove if needed

## Opportunities I'd Flag

### 1. **The `/ship` Command Has a Logic Gap**
When you `/ship` from a worktree, the script does `git merge --squash $branch`, but `$branch` is a *local variable* that gets lost after `cd P:\`. You're merging a branch name, not a worktree path.

**Better approach:**
```powershell
# Capture before switching
$currentBranch = git rev-parse --abbrev-ref HEAD
$worktreePath = $pwd.Path

# Later, use the captured branch name
git merge --squash $currentBranch
```

### 2. **No Handling for Stale Worktrees**
After 6 concurrent sessions, you'll accumulate old worktrees. Add a `/cleanup` command:

```markdown
# /cleanup

List and remove stale worktrees. IMMEDIATELY execute:

git worktree list
Write-Host "Remove with: git worktree remove P:\__worktrees\<name> --force"
```

Or even more aggressive—auto-remove if branch is already merged to main.

### 3. **`/sync` Stash Naming Could Improve**
Current: `sync-20260110-203045`  
**Better:** `sync-{branch}-{timestamp}` so you know which worktree the stash came from if there's a crash.

```powershell
$branch = git rev-parse --abbrev-ref HEAD
git stash push -m "sync-${branch}-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
```

### 4. **Missing: Quick Status Across All 6 Sessions**
With 6 worktrees running, you'll want a `/status-all` that shows:
- Which worktrees exist
- Which branches they're on
- How many uncommitted files in each
- Which ones are ahead of main

```powershell
# .claude/commands/status-all.md
git worktree list --porcelain | ForEach-Object {
    if ($_ -match "worktree (.+)") {
        $path = $Matches[1]
        $branch = git -C $path rev-parse --abbrev-ref HEAD
        $commits = git -C $path rev-list --count main..$branch
        Write-Host "$(Split-Path -Leaf $path): $branch (+$commits commits)"
    }
}
```

### 5. **Pre-commit Hook on Windows May Not Execute**
Git hooks on Windows can be finicky. Add a **CI/CD check** (GitHub Actions, pre-push hook, or CC hook) as backup. The pre-commit hook is good but not *reliable* on Windows.

**Safer:** Add the CC hook earlier:
```bash
# .claude/hooks/pre-tool-use.sh
if [ "$(git rev-parse --abbrev-ref HEAD 2>/dev/null)" = "main" ]; then
  if /"$TOOL_NAME" =~ ^(write; then
    echo '{"decision": "block", "reason": "Create worktree: /worktree <name>"}'
    exit 0
  fi
fi
```

This **prevents Claude from even attempting writes on main**, pre-commit.

### 6. **No Conflict Resolution Strategy**
`/sync` says "report conflicts, do not auto-resolve," but 6 concurrent sessions will hit conflicts. Add guidance:

```markdown
# When /sync reports conflicts:

1. Open the conflicted file
2. Resolve markers manually
3. git add <file>
4. git rebase --continue
5. Run /sync again
```

### 7. **Terminal Tracking: Missing Terminal ID**
You have `w1t1..w3t2` (8 terminals). The prompt shows only branch, not terminal ID.

**Add to PowerShell $PROFILE:**
```powershell
function prompt {
    $branch = git rev-parse --abbrev-ref HEAD 2>$null
    $termId = $env:TERM_ID  # You'd set this per terminal
    if ($branch) { "[$termId] $pwd [$branch]> " }
    else { "[$termId] $pwd> " }
}

# Then in each terminal session startup, set:
$env:TERM_ID = "w1t1"  # or w1t2, w1t3, etc.
```

***

## Recommendation: Two-Phase Rollout

**Phase 1 (This Week):**
- Create the 4 core commands (worktree, sync, ship, where)
- Add pre-commit hook
- Test with 2 sessions first

**Phase 2 (Next Week):**
- Add CC hook for enforcement
- Add `/cleanup` and `/status-all`
- Add conflict resolution docs
- Scale to full 6 sessions

***

## Questions Before Handoff to Simpler Model

1. **Do your 6 sessions run continuously, or restart each day?** (Affects stale worktree risk)
2. **How often do you expect merge conflicts?** (Small repo = rare, large = frequent)
3. **Should `/ship` also run tests before merging?** (Add `npm test` / `pytest`?)
4. **Want the CC hook or just git pre-commit?**

What would you like me to prioritize in the final handoff?
