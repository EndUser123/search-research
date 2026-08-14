---
title: "how can I implement .beads for Claude Code on Windows 11, and use it optimally?"
date: "2026-01-22"
mode: "COPILOT"
uuid: "e91bf9fe-19cf-44d2-97a0-df9c739a6467"
entry_count: 2
---

## Human

how can I implement .beads for Claude Code on Windows 11, and use it optimally?

## Assistant

Perfect. Now I have comprehensive information. Let me compile this into a detailed, expert-level implementation guide.

# Implementing and Optimizing .beads for Claude Code on Windows 11

## Overview

Beads (the `bd` command) is a git-backed distributed task tracker purpose-built for AI-assisted development workflows. For your Windows 11 Claude Code setup, it solves the core problem of agent amnesia across sessions—maintaining persistent context and dependency awareness when working on multi-step features spanning compaction cycles. Given your 5-6 concurrent Claude Code terminals and large codebases, this becomes critical infrastructure.

## Installation on Windows 11

### Step 1: Install the `bd` CLI

On Windows 11 with PowerShell 7.5.4, use the npm installation path for maximum compatibility with Node.js environments:

```powershell
npm install -g @beads/bd
```

Verify installation:

```powershell
bd --version
```

If npm installation fails or you prefer the native binary, use the Windows-specific installer:

```powershell
$url = "https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1"
Invoke-WebRequest -Uri $url -OutFile $env:TEMP\install.ps1
& $env:TEMP\install.ps1
```

Close and reopen PowerShell after installation to reload the PATH.

### Step 2: Project Initialization

For each project where you're using Claude Code with Beads:

```powershell
cd C:\path\to\your\project
bd init --quiet
bd hooks install
```

The `--quiet` flag skips interactive prompts and is ideal for automated setups. Git hooks are critical—they auto-sync your local SQLite cache (`beads.db`) with the committed JSONL file (`issues.jsonl`) on every commit/pull/merge, preventing stale data across your multiple terminal sessions.

### Step 3: Verify Installation

```powershell
bd doctor
```

Check for these indicators:
- ✅ `.beads/` directory exists
- ✅ Git hooks installed (pre-commit, post-merge, pre-push)
- ✅ JSONL file tracked in git
- ✅ Daemon running

## Optimal Configuration for Claude Code on Windows 11

### Hook Configuration for SessionStart/PreCompact

Create or update `.claude/settings.json` with hooks that inject Beads context automatically:

```json
{
  "hooks": {
    "SessionStart": {
      "command": "bd prime --json"
    },
    "PreCompact": {
      "command": "bd compact --analyze --json --days 30"
    }
  }
}
```

Or use the interactive setup:

```powershell
cd your-project
Claude Code
# Inside Claude Code:
/hooks setup
# Select: SessionStart event, bd prime command
```

The `bd prime` command injects a structured context summary (~1-2k tokens) showing:
- Ready work (issues with no blockers)
- Current epic progress
- Open dependencies
- Recently closed tasks

This is far more efficient than the raw `bd list --json` which can balloon to 50k+ tokens in large repositories.

### Critical: Disable Auto-Compaction at 95%

Add to `.claude/settings.json`:

```json
{
  "compaction": {
    "enable": true,
    "threshold": 0.75
  }
}
```

Trigger compaction at 75% context utilization, not 95%. This preserves 25% working memory (~50k tokens in a 200k window) for the model's reasoning processes. Performance research shows that triggering earlier improves code generation quality by 29-39% because the model has space to plan and evaluate alternatives before hitting crisis mode.

## Skills for Beads-Integrated Workflows

Create these three complementary skills in `~/.claude/skills/` to maximize Beads effectiveness:

### Skill 1: `brainstorming` (Feature Design)

Create `~/.claude/skills/brainstorming/SKILL.md`:

```markdown
---
name: brainstorming
description: "Design features with collaborative dialogue, then chain into planning → epic creation → execution"
---

# Brainstorming Ideas Into Designs

Start by understanding the project and asking one question at a time to refine the idea.
Present the design in 200-300 word sections, validating each before proceeding.

## The Process

**Understanding:**
- Check project state (files, docs, recent commits)
- Ask one question at a time
- Prefer multiple choice when possible
- Focus on: purpose, constraints, success criteria

**Exploring approaches:**
- Propose 2-3 different approaches with trade-offs
- Present options conversationally
- Lead with recommended option

**Presenting design:**
- Once understood, present design in sections
- Ask after each section: "Does this look right so far?"
- Cover: architecture, components, data flow, error handling

## After Design

### Phase 1: Documentation
- Write design to `docs/plans/YYYY-MM-DD-<topic>-design.md`
- Commit to git

### Phase 2: Implementation Plan
Ask: "Design complete. Ready to create the implementation plan?"
- Use `superpowers:writing-plans` to detail tasks
- Output: `docs/plans/YYYY-MM-DD-<topic>-plan.md`
- Commit to git

### Phase 3: Plan Review (CHECKPOINT)
Present the plan summary. Wait for user approval before proceeding.

### Phase 4: Epic Creation
Once approved:
- Use `/plan-to-epic docs/plans/YYYY-MM-DD-<topic>-plan.md`
- Creates beads epic with all tasks, dependencies inferred from file overlap
- Output: Epic ID (e.g., `platform-xyz`)

### Phase 5: Execution
Ask: "Epic created: <epic-id>. Ready to start execution?"
- Use `/epic-executor <epic-id>`
- Runs to completion autonomously
```

### Skill 2: `plan-to-epic` (Plan to Task Tracker)

Create `~/.claude/skills/plan-to-epic/SKILL.md`:

```markdown
---
name: plan-to-epic
description: Convert superpowers implementation plans into beads epics with dependencies and acceptance criteria
---

# Plan to Epic

Convert implementation plans into structured beads epics ready for `epic-executor`.

## Usage

```bash
/plan-to-epic docs/plans/YYYY-MM-DD-feature-plan.md
/plan-to-epic docs/plans/YYYY-MM-DD-feature-plan.md --design docs/plans/YYYY-MM-DD-feature-design.md
```

## Workflow

### Step 1: Parse Documents
- Read plan file, extract: title, goal, architecture, tech stack
- For each task: title, files to modify, steps, code snippets, expected outcomes
- If `--design` provided: extract architecture decisions, data flow, error handling

### Step 2: Create Epic
```bash
bd create --type=epic --priority=0 --title="<Plan Title>" --json
```

### Step 3: Analyze Dependencies
- **File overlap detection**: If Task N and Task M modify the same file, M depends on N
- **Explicit references**: Scan for "after Task N", create explicit dependency

### Step 4: Build Task Content
For each task, populate THREE fields:
- **Description**: Implementation-focused (files, steps, code, testing)
- **Design**: Context and rationale (epic goal, architecture decisions)
- **Notes**: Source document references (plan path, line numbers)

### Step 5: Create Tasks
```bash
bd create --type=task --parent=<epic-id> --priority=0 \
  --title="<Task Title>" \
  --body-file=/tmp/task-body.md \
  --design "$(cat /tmp/task-design.md)" \
  --json
```

### Step 6: Add Dependencies
```bash
bd dep add <dependent-task-id> <blocker-task-id> --json
```

### Step 7: Output Summary
```
Created epic: platform-abc "Feature Name"
Tasks (9): Ready to execute with /epic-executor platform-abc
```

## Key Principles

1. Preserve full detail—never summarize implementation steps
2. Always use `--json` for reliable parsing
3. Include design context in each task
4. Dependency inference prevents ordering errors
```

### Skill 3: `epic-executor` (Autonomous Task Execution)

Create `~/.claude/skills/epic-executor/SKILL.md`:

```markdown
---
name: epic-executor
description: Execute beads epic tasks sequentially with two-stage review (spec compliance, then code quality)
---

# Epic Executor

Execute all tasks in a beads epic with fresh subagent-per-task discipline.

## Usage

```bash
/epic-executor <epic-id>
```

## Setup Phase

### 1. Validate Epic
```bash
bd show <epic-id> --json
bd epic status <epic-id> --json
```

### 2. Note Base SHA
```bash
git rev-parse HEAD
```

## Execution Loop

For each task until 100% complete:

### 1. Check Completion
```bash
bd epic status <epic-id> --json
```

If 100% complete, announce and stop.

### 2. Get Next Ready Task
```bash
bd ready --parent=<epic-id> --limit=1 --json
```

If none ready but epic incomplete, check blockers.

### 3. Claim Task
```bash
bd update <task-id> --status=in_progress --json
```

### 4. Dispatch Implementer Subagent
- Fresh subagent per task (prevents context pollution)
- Provide: description, design context, epic context
- Instruct: ask questions before starting, self-review before reporting

### 5. Spec Compliance Review
- Verify implementation matches specification
- Read actual code, compare line-by-line to requirements
- Report: APPROVED or NEEDS_CHANGES with file:line references

### 6. Code Quality Review
- Only after spec compliance passes
- Use `superpowers:code-reviewer`
- Focus: security, test coverage, TypeScript best practices, performance

### 7. Handle Results
- If issues found: dispatch fix subagent, re-run failed review
- Repeat until both reviews pass

### 8. Close Task
```bash
bd close <task-id> --reason="Implemented and verified" --json
```

### 9. Continue to Next Task

## Key Principles

1. Sequential execution—one task at a time
2. Fresh subagent per task—no context pollution
3. Two-stage review—spec compliance first, code quality second
4. Fix before closing—don't skip issues
5. Always use `--json` for reliable parsing
```

## Optimal Usage Patterns for Your Workflow

### Pattern 1: Multi-Terminal Coordination

Since you run 5-6 Claude Code terminals simultaneously, Beads coordinates work via git:

**Terminal 1 (Orchestrator):**
```powershell
cd P:\projects\main
claude code
# /brainstorming → /plan-to-epic → /epic-executor
```

**Terminals 2-6 (Specialists):**
```powershell
# Each takes a specific task from the epic
bd ready --json | jq '.[0]'  # Get next unblocked task
bd update <task-id> --status in_progress
# Implement task
bd close <task-id> --reason "Complete"
bd sync  # Force immediate push
```

All terminals share the same `.beads/` database. Git hooks auto-sync, preventing conflicts.

### Pattern 2: Dependency-Aware Work Prevention

Before assigning work, query ready work:

```powershell
bd ready --priority 1 --json | jq '.[] | "\(.id): \(.title)"'
```

This immediately surfaces:
- Which tasks have no blockers
- Which tasks are blocked (and why)
- Suggested execution order

No more "let me check if that's done yet"—it's deterministic.

### Pattern 3: Session Resumption Without Context Loss

When you return to a project after closing a session:

```powershell
bd epic status <epic-id> --json
# Shows: 3 closed, 2 in_progress, 8 open
bd ready --json  # Next unblocked task
```

Claude Code's SessionStart hook injects `bd prime` output (~1-2k tokens), showing exactly where work stands. No context re-reading, no "remind me what we were doing."

### Pattern 4: Discovered Work Filing

During implementation, if you find a bug or realize an architectural issue:

```powershell
bd create "Fix: auth validation race condition" \
  --type bug \
  --priority 1 \
  --deps discovered-from:<current-task-id> \
  --json
```

The `discovered-from` relationship maintains audit trail and prevents lost work. The issue is automatically linked to the task that discovered it.

## Context Window Management Strategy

With your large monorepos, context efficiency is critical:

### Strategy 1: Use `bd prime` Instead of `bd list --json`

**Inefficient (~50k tokens):**
```powershell
bd list --json  # Full issue dump
```

**Efficient (~1-2k tokens):**
```powershell
bd prime --json  # Curated context
```

The `prime` command outputs:
- Ready work (unblocked tasks)
- In-progress tasks
- Top blockers
- Recent completions

Use this in SessionStart hooks and periodic context injection.

### Strategy 2: CLAUDE.md for Persistent Architecture

Create `.claude/CLAUDE.md` with:
```markdown
# Project Architecture

## Current Epics
- epic-alpha: Authentication system (3/10 tasks complete)
- epic-beta: Payment processing (0/8 tasks complete)

## Tech Stack
- Backend: Node.js 20+, TypeScript
- Database: PostgreSQL 15
- Frontend: React 18, Tailwind CSS

## Never-Forgotten Rules
1. All file changes must include tests
2. Database migrations require review
3. API changes need backward compatibility
4. Performance targets: <100ms latency, <1MB bundle
```

Claude Code's CLAUDE.md is injected fresh every session (not counted toward compaction), so core context never needs re-explanation.

### Strategy 3: Disable Auto-Compaction During Active Tasks

If you're mid-refactoring and approaching context limits:

```powershell
# In Claude Code:
/compact off
# Work continues without forced compaction
# When task complete:
/compact on
```

Manual control prevents compaction mid-task. Work completes with full context, then resets cleanly for the next phase.

## Performance Optimization Checklist

- ✅ Run `bd hooks install` in every project (auto-sync prevents stale data)
- ✅ Set compaction threshold to 75%, not 95% (preserves working memory)
- ✅ Use `bd prime` in SessionStart hooks, not `bd list --json` (1-2k vs 50k tokens)
- ✅ Maintain `.claude/CLAUDE.md` for architectural stability (not compacted)
- ✅ Run `bd sync` before ending sessions in multi-agent scenarios (ensures git push)
- ✅ Use `discovered-from` for found issues (maintains audit trail, prevents duplication)
- ✅ Query `bd ready` before assigning work (deterministic ordering, no blocking surprises)
- ✅ File issues as discovered (`bd create`), don't accumulate mental backlog (no lost work)

## Troubleshooting

**Issue: Daemon crashes after PowerShell restart**
```powershell
bd daemons killall
# Claude Code will restart daemon automatically on next command
```

**Issue: JSONL merge conflicts after git pull**
```powershell
bd doctor
# Auto-detects conflicts and offers repair
bd merge <base> <ours> <theirs>  # Manual merge if needed
```

**Issue: Hash-based IDs look different than expected**
```powershell
bd migrate --dry-run
# This is normal in v0.20.1+; hash IDs prevent collisions in parallel workflows
```

**Issue: SessionStart hook not injecting context**
```powershell
bd setup claude
# Re-runs hook configuration
bd doctor --fix
# Auto-repairs hook setup
```

## Summary

Beads transforms Claude Code from a single-session tool into a persistent, dependency-aware development partner. For your Windows 11 setup with multiple terminals, it provides:

1. **Distributed coordination** via git (no external service)
2. **Dependency tracking** preventing blocked work surprises
3. **Session resumption** without context re-reading
4. **Discovered work** auto-filing so nothing gets lost
5. **Multi-agent orchestration** via ready-work queries

Install it once (`bd init --quiet`), configure hooks (`bd hooks install`), add to CLAUDE.md, and your Claude Code instances gain persistent memory and intelligent task routing across all 5-6 terminals.

## Human

Any install or steady state issues on Windows 11?

## Assistant

# Windows 11 Installation & Steady State Issues for Beads + Claude Code

Based on recent bug reports and issue tracking from the Beads and Claude Code repositories, there are six critical issues you should know about on Windows 11:

## Installation Issues

### Issue 1: npm Install Fails on Windows[1]

The published npm package has a broken binary download URL. The script tries to fetch `beads_X.X.X_windows_amd64.zip` from an incorrect GitHub raw URL path.

**Symptom:**
```powershell
npm install -g @beads/bd
# Error: The beads_0.47.0_windows_amd64.zip file was not found
```

**Workaround:** Revert to the GitHub-hosted PowerShell installer:

```powershell
$url = "https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1"
Invoke-WebRequest -Uri $url -OutFile $env:TEMP\install.ps1
& $env:TEMP\install.ps1 -Version latest
```

Or use Homebrew if you have it installed:
```powershell
brew install steveyegge/beads/bd
```

### Issue 2: Database Not Initialized Errors[2][3]

After installation or upgrades, Beads crashes with:
```
Error: database not initialized: issue_prefix config is missing (run 'bd init')
```

This occurs even after `bd init` completes successfully, particularly on Windows 11's file system.

**Root Cause:** SQLite initialization race condition on Windows. The `.beads/beads.db` file isn't fully initialized before the first command attempts to read it.

**Fix:**

```powershell
# Step 1: Kill all running daemons
bd daemons killall --force

# Step 2: Reinitialize carefully
cd your-project
rm -r .beads  # Clean state
bd init --quiet --skip-merge-driver  # Skip git setup initially

# Step 3: Verify database
bd doctor
# If still failing, try:
bd daemons health
bd daemons killall
# bd will auto-restart daemon on next command
```

## Hook Configuration Issues

### Issue 3: Claude Code Hooks Don't Execute on Windows[4][5]

Claude Code's hook system has two Windows-specific failures:

**Problem 1: Path Escaping**
Windows paths require double backslashes in JSON, but even then, bash scripts won't execute.

```json
// WRONG - Claude Code expects JSON escaping
{
  "hooks": {
    "SessionStart": {
      "command": "C:\\Users\\YourName\\bin\\script.sh"
    }
  }
}

// CORRECT - Double escape for JSON
{
  "hooks": {
    "SessionStart": {
      "command": "C:\\\\Users\\\\YourName\\\\bin\\\\script.sh"
    }
  }
}
```

**Problem 2: Bash Scripts Don't Run**
Even with correct paths, Claude Code on Windows can't reliably execute bash scripts because stdin isn't passed to the hook command.

**Solution: Use PowerShell Instead**

```json
{
  "hooks": {
    "SessionStart": {
      "command": "powershell -NoProfile -Command \"& {bd prime --json}\""
    },
    "PreCompact": {
      "command": "powershell -NoProfile -Command \"& {bd compact --analyze --json --days 30}\""
    }
  }
}
```

Or for `.beads/hooks.json` (if manually configuring):

```bash
bd hooks install --shell powershell
```

### Issue 4: stdin Not Passed to Hooks[5]

When hooks expect JSON piped via stdin (e.g., `bd compact --json | jq ...`), Claude Code on Windows silently drops the pipe.

**Workaround:** Use file output instead of pipes:

```powershell
# Instead of: bd list --json | jq '.[]'
# Use:
$output = bd list --json
$output | ConvertFrom-Json | ForEach-Object { ... }
```

## Steady State Issues

### Issue 5: Daemon Crashes After PowerShell Restart[6]

The Beads daemon uses Unix socket communication by default, which fails on Windows. After restarting PowerShell or the system, you'll see:

```
Error calling tool 'show': Failed to connect to daemon asyncio.open_unix_connection not available on Windows
```

**Root Cause:** Beads v0.47.0+ attempted to use Unix sockets, which don't exist on Windows. This was partially fixed in later versions, but may still occur on fresh installs.

**Fix:**

```powershell
# Kill and restart the daemon
bd daemons killall
# Verify it restarts cleanly:
bd doctor
# Check logs:
bd daemons logs --follow
```

**Permanent Fix (if available in your version):**
Upgrade to the latest Beads version (check `bd --version`). The maintainers have since fixed this by implementing Windows named pipe support.

### Issue 6: CRLF Line Ending Conflicts in JSONL[7][8]

When you pull changes from other machines or branches, the `.beads/issues.jsonl` file may have CRLF (Windows) line endings mixed with LF (Unix) line endings. This causes:
- Git merge conflicts that shouldn't exist
- Import/export mismatches
- Sync failures

**Prevention:**

```powershell
# Set globally on your Windows machine
git config --global core.autocrlf false
git config --global core.eol lf

# Also set per-repo (inside your project)
cd your-project
git config core.autocrlf false
git config core.eol lf
```

Add to `.gitattributes`:

```
.beads/issues.jsonl text eol=lf
```

**If You Already Have Mixed Line Endings:**

```powershell
# Rewrite the file to LF only
git checkout --theirs .beads/issues.jsonl
bd import -i .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "Normalize JSONL line endings to LF"

# Or use a JSONL-aware merge tool:
git config merge.beads.driver "bd merge %A %O %L %R"
git config merge.beads.name "bd JSONL merge driver"
echo ".beads/beads.jsonl merge=beads" >> .gitattributes
```

## Pre-Installation Checklist for Windows 11

Before running `bd init`, verify your environment:

```powershell
# 1. PowerShell 7.5+ (you have this)
$PSVersionTable.PSVersion

# 2. Git with LF support configured
git config --list | grep -E "autocrlf|eol"
# Should show: core.autocrlf=false, core.eol=lf

# 3. Node.js and npm (if using npm install path)
node --version
npm --version

# 4. No conflicting tools
# - Check no Git Bash scripts are sourced in $PROFILE
# - Disable any pre-commit hooks in .git/hooks

# 5. Antivirus/Windows Defender whitelist
# Add your project folder to Defender exclusions to prevent SQLite lock contention
# Settings > Virus & threat protection > Manage settings > Add exclusions > C:\path\to\project
```

## Quick Recovery Procedure

If you hit an issue mid-session:

```powershell
# Step 1: Stop everything gracefully
bd daemons killall
cd your-project
git status  # Verify no uncommitted changes

# Step 2: Clear state
rm -r .beads/beads.db
rm -r .beads/*.lock

# Step 3: Reinitialize
bd init --quiet --skip-merge-driver
bd hooks install --shell powershell
bd doctor

# Step 4: Resume
bd ready --json
```

## Version Considerations

- **Beads v0.47.0 and earlier:** Broken npm binary URLs, Unix socket issues
- **Beads v0.47.1+:** npm fixed, partial Windows support
- **Beads v0.48.0+:** Windows named pipes support, more reliable daemon
- **Latest (v0.50.0+):** Recommended for Windows 11; all socket communication issues resolved

Check your version:
```powershell
bd --version
```

Upgrade if needed:
```powershell
# Via PowerShell installer (safest)
Invoke-WebRequest -Uri "https://raw.githubusercontent.com/steveyegge/beads/main/scripts/install.ps1" -OutFile $env:TEMP\install.ps1
& $env:TEMP\install.ps1 -Version latest
```
