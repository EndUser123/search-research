---
title: "Use GitButler + Claude Code Hooks [Advanced]
GitButler's experimental CLI integrates with Claude Code lifecycle hooks, a"
date: "2025-12-29"
mode: "COPILOT"
uuid: "3dd51489-f1dc-4ec7-aaa9-404b6d9e6a3a"
entry_count: 3
---

## Human

Use GitButler + Claude Code Hooks [Advanced]
GitButler's experimental CLI integrates with Claude Code lifecycle hooks, automatically segregating work from simultaneous sessions into separate branches—no worktrees needed:
powershell
# Install GitButler CLI
# Configure Claude Code hooks (documented in GitButler help)
# Multiple Claude sessions now auto-branch their changes

Result: One commit per Claude chat round, one branch per session, automatically managed.
Prevention: Configure Claude Code Safely
Add to .claude/settings.json (or ~/.claude.json):
json
{
  "allowedTools": [
    "Bash(git add:*)",
    "Bash(git commit:*)",
    "Bash(git push:*)",
    "Edit"
  ]
}

Better yet, add to your CLAUDE.md:
text
## Git Workflow

- **DO NOT** run multiple Claude Code sessions in the same working directory
- Use `git worktree` for parallel tasks instead
- Each chat session handles one logical task
- Always verify `git status` is clean before starting a new session
- If you encounter index.lock errors, ask user to manually remove: `Remove-Item -Force .git/index.lock`

## Commands to Remember

- `git worktree add ../project-name branch-name` - Create isolated workspace
- `git worktree list` - View all worktrees
- `git worktree remove ../project-name` - Clean up after task

---

please describe how we can use this?  Are there other repos that would have similar outcomes?

## Assistant

Now I have comprehensive research. Let me create the final answer:

## GitButler + Claude Code Hooks: Advanced Multi-Session Branching Architecture

### Core Mechanism: Lifecycle Hook Integration

GitButler's Claude Code hooks system eliminates the complexity of managing parallel AI coding sessions by automatically segregating changes into isolated branches within a single working directory. The architecture consists of three lifecycle hooks that intercept Claude Code's agent loop:[1]

- **`but claude pre-tool`** – Executes before any file edit operations begin
- **`but claude post-tool`** – Executes after edits complete, allowing file monitoring
- **`but claude stop`** – Finalizes the session, commits changes, and updates branch metadata

This differs fundamentally from git worktree approaches: instead of creating separate filesystem copies, GitButler uses virtual branch management—the same underlying model that powers its core change management system. When you run three simultaneous Claude sessions, each communicates with GitButler at each step, and GitButler automatically assigns changes to separate branches, generates contextually aware commit messages from your prompts, and prevents merge conflicts.[2]

### Configuration Pattern

The hooks are defined in Claude Code's settings hierarchy:[3]

```json
{
  "hooks": [
    {
      "toolUse": [
        {
          "type": "bash",
          "command": "but claude pre-tool"
        },
        {
          "type": "bash", 
          "command": "but claude post-tool"
        }
      ]
    },
    {
      "stop": [
        {
          "type": "bash",
          "command": "but claude stop"
        }
      ]
    }
  ]
}
```

Critically, you should add a memory note instructing Claude not to manage git commits directly—GitButler handles that entirely. The configuration respects a priority hierarchy: project-local settings (`.claude/settings.json`) override user-global settings (`~/.claude/settings.json`), allowing both team standards and personal customizations.[4][3]

### Operational Advantages Over Worktrees

**Single Directory Simplification:** Traditional git worktrees require managing parallel checkouts in separate folders (e.g., `../project-feature-a`, `../project-bugfix`), each with its own HEAD, index, and working state. GitButler's virtual branches operate within one directory, eliminating:
- Context-switching overhead between folders
- Index.lock conflicts from simultaneous git operations  
- Directory traversal in scripts and terminal sessions
- Complexity of granting Claude access via `/add-dir`[5]

**Automatic Branch Naming & Commits:** Each session generates one commit per Claude interaction round with a commit message derived from your prompt context. The system infers sensible branch names and creates proper PR references without manual intervention.[2]

**No Merge Coordination Cost:** Unlike worktrees where you manually rebase or merge back to main, GitButler's change management engine handles internal coordination. You can push each branch independently as a PR without worrying about state synchronization.[2]

### Ecosystem Patterns with Similar Outcomes

#### **Cursor IDE Hooks** (`.cursor/hooks.json`)
Cursor 1.7+ implements a compatible hook system with `afterFileEdit` and `stop` lifecycle events, with GitButler integration support. The hook execution pattern mirrors Claude Code, making it possible to write hooks that work across both tools:[6]

```json
{
  "version": 1,
  "hooks": {
    "afterFileEdit": [
      { "command": "but cursor after-edit" }
    ],
    "stop": [
      { "command": "but cursor stop" }
    ]
  }
}
```

#### **Cline (Claude in VS Code)**
The Cline project is actively implementing Claude Code-compatible hooks with a tool-name compatibility layer, enabling universal interoperability. The proposal includes PreToolUse, PostToolUse, Notification, and SubagentStop hook types, designed so any hook written for Claude Code works without modification.[5]

#### **DoltHub's Containerized Agent Pattern**
For even greater isolation, DoltHub uses Docker containers with mounted repositories, where each agent gets its own pristine environment. While heavier than hooks, this pattern provides OS-level isolation when you need complete environment divergence:[7]

```bash
# Each agent gets isolated container with shared repo mounted
docker run -it --rm -v /repo:/work agent:latest
# Pre-push hooks prevent main branch interference
git hook set pre-push "reject-main-branch"
```

#### **LiteLLM Proxy's `async_pre_call_hook` Pattern**
A complementary hooks ecosystem exists in LiteLLM's proxy layer, where `async_pre_call_hook` intercepts LLM requests before execution. This is strategically positioned for enforcing policies, masking PII, dynamic model routing, and rate limiting. While not directly a VCS pattern, it demonstrates how hook-based middleware becomes the standard intervention point across AI infrastructure.[8]

### Broader Ecosystem Standardization Trends

**MCP Apps Extension (SEP-1865):** Anthropic and OpenAI collaborated in November 2025 to standardize interactive UI capabilities across agentic systems. This signals industry-wide movement toward interoperability over proprietary lock-in. The hook pattern—allowing external intervention at critical moments—is now the standard architectural pattern for AI agent infrastructure.[9]

**Open Agent Specification (Agent Spec):** A JSON-based declarative standard for describing agents, multi-agent workflows, and tool orchestration is gaining adoption across LangGraph, CrewAI, and WayFlow. This enables teams to separate business logic from execution concerns, supporting version control, automated testing, and runtime swapping without proprietary adapters.[10]

**Jujutsu (jj) Version Control:** An alternative VCS built on stack-based commits and automatic snapshotting. Jujutsu maintains working copy == commit invariant, eliminating git's staging area complexity. While not using hooks like GitButler, it solves parallel development differently: every operation is snapshotted, all changes are directly editable (no rebasing needed), and operations are stored in a traversable log for time-travel debugging.[11][12]

### Best Practices for Multi-Session Workflows

1. **Tool Restriction via `allowedTools`:** Prevent unintended git operations by specifying exactly which tools Claude can invoke:[4]
   ```json
   {
     "allowedTools": [
       "Bash(git add:*)",
       "Bash(git commit:*)",
       "Edit"
     ]
   }
   ```

2. **Matcher Patterns for Performance:** Use targeted matcher patterns instead of wildcards to minimize hook overhead:[13]
   ```json
   {
     "matcher": "Edit|MultiEdit|Write",
     "hooks": [...]  // Only fire on file modifications
   }
   ```

3. **Timeout Protection:** Set explicit timeout values (default 60 seconds, minimum 1 second) to prevent runaway hooks from blocking agent execution.[13]

4. **Idempotent Hook Design:** Design hooks to be safely retryable. If a pre-tool hook fails mid-execution and retries, state should remain consistent.[13]

5. **Local Settings for Secrets:** Use `.claude/settings.local.json` (git-ignored) for personal API keys or sensitive configurations, while committing `.claude/settings.json` as team standards.[3]

### When to Choose Each Pattern

| Approach | Use Case | Trade-off |
|----------|----------|-----------|
| **GitButler Hooks** | Multiple parallel feature development in single repo, mixed CI/CD needs | Requires GitButler CLI installation |
| **Git Worktrees** | Isolated environments with separate dependencies, extreme isolation concerns | Filesystem clutter, context-switching overhead |
| **Docker Containers** | Multi-agent systems with conflicting tool versions or OS-level isolation | Significant overhead for simple changes |
| **Jujutsu (jj)** | Change-centric workflows preferring direct history editing | Requires full VCS migration, smaller ecosystem |

### Practical Example: Three Simultaneous Features

```powershell
# PowerShell: Configure hooks in ~/.claude/settings.json
# Then launch three Claude Code sessions

# Terminal 1: Feature A
claude

# Terminal 2: Feature B  
claude

# Terminal 3: Feature C
claude

# Result (automatically): 
# - feature/session-a branch created, changes committed
# - feature/session-b branch created, changes committed  
# - feature/session-c branch created, changes committed
# - Can create independent PRs from each without conflicts
# - git status stays clean throughout all sessions
```

The hooks infrastructure invisible to Claude—it simply works on files, and GitButler automatically manages the branching orchestration behind the scenes.

---

## Human

What are good git worktree solutions for claude code in github.com

## Assistant

Now I'll create the final comprehensive report:

## Git Worktree Solutions for Claude Code in GitHub Environments

Git worktrees solve the parallelization problem by allowing multiple Claude Code sessions to work simultaneously on different branches without the file system clutter of worktrees. The landscape includes both manual workflows and purpose-built automation tools, each with distinct trade-offs.

### The Foundation: Why Worktrees Beat Branch Switching

Traditional git workflow requires constant stashing/switching, which fragments Claude's context and forces you to mentally track multiple disconnected conversations. Worktrees maintain independent file states across branches in separate directories, preserving Claude's understanding of each task's codebase simultaneously. The key insight: worktrees are invisible containers that eliminate context pollution—Claude in one worktree never sees code from another branch, so it can't accidentally reference or modify unrelated files.[1]

The Anthropic Claude Code team explicitly recommends this pattern as a best practice. Their core workflow:[2]
```powershell
# Create worktree for task
git worktree add ../project-feature-a feature-a

# Launch Claude in isolated environment
cd ../project-feature-a
claude
```

### Solution Landscape: Manual → Automated

#### Option 1: Manual Git Commands (Simplest Start)

For straightforward two-to-three worktree setups, raw git commands provide full control with minimal overhead:[1]

```powershell
# Create worktrees with sensible naming
git worktree add .trees/feature-auth feature/user-authentication
git worktree add .trees/bugfix-login bugfix/login-validation

# List active worktrees
git worktree list

# Launch Claude in each
cd .trees/feature-auth
claude

# Cleanup when done
git worktree remove .trees/feature-auth
git worktree prune  # Clean orphaned references
```

**Best for:** Small projects, learning the concept, <3 simultaneous sessions  
**Trade-off:** Manual path management, no automation, easy to forget cleanup

#### Option 2: Branchlet CLI Tool

A lightweight wrapper built specifically for Claude Code workflows:[3]

```powershell
# Install
branchlet install

# Create and open
branchlet create feature-name
# Auto-opens in your IDE, copies .env, runs setup commands

# List, open, delete
branchlet list
branchlet open feature-name
branchlet remove feature-name
```

**Features:**
- Configuration for auto-copying `.env` and other files
- IDE auto-launch (VS Code, Cursor, etc.)
- Installation command execution per worktree
- Simplified deletion with metadata cleanup

**Best for:** Quick local development, macOS/Linux, small teams  
**Trade-off:** Less feature-rich than specialized tools, limited GitHub integration

#### Option 3: WTP (Powerful Worktree Manager)

A production-grade worktree CLI tool that eliminates path friction entirely:[4]

```powershell
# Smart path generation - no typing paths!
wtp add feature/auth
# Creates: ../worktrees/feature/auth (automatically organized)

# Navigation with tab completion
wtp cd feature/auth  # Jump between worktrees instantly
wtp cd @             # Return to main worktree

# Atomic removal - branch + worktree in one command
wtp remove --with-branch feature/done

# Smart listing
wtp list
```

**Configuration (`.wtp.yml`):**
```yaml
base_dir: "../worktrees"
setup:
  commands:
    - npm install
    - npm run setup
  env_files:
    - .env
    - .env.local
```

**Advanced Features:**
- Automatic remote branch tracking
- Project-specific setup hooks
- Preserves directory hierarchy from branch names (`feature/auth` → `../worktrees/feature/auth`)
- Error handling for conflicting branches across remotes

**Best for:** Medium-to-large projects, teams with standardized setup, frequent worktree creation  
**Trade-off:** Requires installation, adds complexity to simple workflows

#### Option 4: Claude Code Crew (Web-Based Dashboard)

Full-featured browser UI for managing multiple concurrent Claude Code sessions:[5]

**Architecture:**
- Backend: Node.js + Express + Socket.io for real-time updates
- Frontend: React + TypeScript + Material-UI
- Terminal: xterm.js for full terminal emulation
- Single-port deployment (no CORS overhead)

**Features:**
- Visual worktree sidebar with branch info
- Browser-based terminal for each session
- Real-time session state monitoring (busy/waiting/idle)
- Create/delete/merge worktrees from UI
- Switch between sessions without terminal gymnastics
- Terminal history preserved across sessions

**Usage:**
```powershell
# Clone and run
git clone https://github.com/to-na/claude-code-crew.git
cd claude-code-crew
npm install
npm start

# Access: http://localhost:3000
# Click worktree → Creates Claude Code session in browser terminal
```

**Best for:** Remote teams, monitoring multiple agent work, visual preference, high session count (5+)  
**Trade-off:** Adds infrastructure dependency, requires Node.js, more moving parts

#### Option 5: GitHub Issues Integration (Workflow Automation)

Direct GitHub-to-worktree automation for issue-driven development:[6][7]

**Worktree CLI + GitHub (agenttools/worktree):**
```powershell
# Requirements: git, tmux, GitHub CLI (gh), Claude Code CLI

# Open issue #1 in dedicated worktree + tmux session
worktree open 1

# This automatically:
# 1. Creates folder: ../project-name-issue-1
# 2. Creates branch: issue/1
# 3. Launches tmux session with Claude Code
# 4. Displays Claude output in tmux window
```

**Synaptic Canvas GitHub Issue Manager Skill:**
- Manages full lifecycle: list issues → triage → worktree → implement → test → PR
- Customizable branch patterns and PR templates
- Integrates with `sc-git-worktree` for isolation
- GitHub CLI credentials flow for seamless auth

**Best for:** Issue-driven teams, automation-heavy workflows, GitHub-first process  
**Trade-off:** Requires GitHub CLI setup, tmux familiarity on macOS/Linux

### Platform-Specific Setup (macOS Recommended)

**iTerm2 Multi-Pane Workflow:**

The most practical high-throughput setup uses iTerm2's split panes:[8][1]

```powershell
# Open iTerm2
# Split horizontally: Cmd+Shift+D
# Split vertically: Cmd+D (create grid)

# Terminal 1 (top-left pane):
cd .trees/feature-auth
claude

# Terminal 2 (top-right pane):
cd .trees/feature-ui
claude

# Terminal 3 (bottom pane):
cd .trees/bugfix-critical
claude
```

**Pro Tips:**
- Use Cmd+I to set custom title for each pane (e.g., "AUTH", "UI", "BUG")
- Enable iTerm notifications for when Claude needs attention
- Each pane maintains independent Claude context indefinitely (no restart needed)
- Switch panes with Cmd+[] or click directly

**Windows PowerShell Alternative:**

Windows doesn't have iTerm2, but several approaches work:

```powershell
# Option A: Windows Terminal tabs
wt -w 0 nt -d .trees/feature-auth powershell -c "claude"
wt -w 0 nt -d .trees/feature-ui powershell -c "claude"

# Option B: Multiple VS Code windows
# Open each worktree in separate VS Code instance with "Claude Code" extension

# Option C: WSL + tmux (advanced)
wsl
tmux new-session -d -s work -c .trees/feature-auth -c "cd .trees/feature-auth && claude"
```

### Configuration Pattern for Claude Scope

Each worktree needs explicit scope instructions to prevent Claude from interfering across branches:

**.trees/feature-auth/.claude/rules.md:**
```markdown
## Worktree Boundaries

- **Active Branch:** feature/user-authentication
- **Workspace Path:** {git rev-parse --show-toplevel}/.trees/feature-auth
- **Scope:** Only modify files in this directory

## Safe Operations
- Create commits in this worktree
- Create local branches
- Push to origin/feature/user-authentication

## Prohibited
- Delete or modify other worktrees
- Force push without permission
- Operations affecting repository-wide settings
```

**Prompt Template:**
```
I've set up a worktree at `.trees/feature-auth` for the authentication feature.
Please work only within this directory. Use `git rev-parse --show-toplevel` if you need the absolute path.

Reference your branch with: feature/user-authentication
Safe to push: origin/feature/user-authentication
```

### Practical Comparison Table

| Solution | Setup Time | Learning Curve | GitHub Integration | GUI | API Cost | Best Use Case |
|----------|-----------|-----------------|-------------------|-----|----------|----------------|
| **Manual Git** | 2 min | Low | Manual | No | Free | Learning, small teams |
| **Branchlet** | 5 min | Low | No | No | Free | Quick local dev (2-3 tasks) |
| **WTP** | 10 min | Medium | No | CLI | Free | Medium projects, frequent use |
| **Claude Code Crew** | 20 min | High | No | Yes | Free | Remote teams, visual preference |
| **GitHub Issues → Worktrees** | 15 min | Medium | Yes | CLI | Free | Issue-driven teams |

### Recommended Startup Sequence

**For Your Use Case (Windows 11, Solo Developer, GitHub Focus):**

1. **Start with manual git commands** to understand the pattern:
   ```powershell
   git worktree add .trees/task-1 feature/task-1
   cd .trees/task-1
   claude
   ```

2. **Create a PowerShell alias** for common operations:
   ```powershell
   function New-Worktree {
     param([string]$TaskName)
     git worktree add ".trees/$TaskName" "feature/$TaskName"
     Set-Location ".trees/$TaskName"
     claude
   }
   ```

3. **Evaluate WTP** if you regularly manage >3 worktrees:
   - Cleaner automation
   - Setup hooks for your environment
   - Better navigation experience

4. **Consider Claude Code Crew** if you need monitoring:
   - Browser-based dashboard
   - Real-time session state
   - No terminal tab confusion

### Integration with Your LLM Routing System

Your multi-provider LLM routing (OpenRouter, Chutes.ai, Z.ai) works seamlessly with worktrees because each worktree's Claude Code session is independent. Each gets its own API tokens/routing configuration:[1]

```powershell
# Each worktree can have independent provider routing
# In .trees/feature-auth/.claude/settings.json:
{
  "modelRouting": {
    "provider": "openrouter",
    "fallback": ["chutes.ai", "z.ai"]
  }
}

# In .trees/feature-ui/.claude/settings.json:
{
  "modelRouting": {
    "provider": "z.ai",  # Different provider per task
    "fallback": ["openrouter"]
  }
}
```

This enables load balancing and cost optimization across tasks.

***

**Citations:**[9][7][3][8][6][5][2][4][1]

## Human

I'm a solo dev who doesn't like to be told what to do, but I hate bloat.  I have 5 terminals of claude code open right now.  What solution do you think is best for me?

## Assistant

Based on your profile—solo dev, 5 active Claude sessions, preference for autonomy over prescriptive solutions, and hatred of bloat—**WTP (Powerful Worktree CLI)** is your best fit, with a manual git baseline.

Here's why:

**WTP aligns with your constraints:**

1. **Zero bloat.** It's a single CLI binary (~15MB), no Node.js dependency, no web server, no Docker. Just `wtp add`, `wtp cd`, `wtp remove`. Pure git worktree abstractions without opinion.[1]

2. **No management overhead.** You already have 5 terminals open—WTP doesn't force you into iTerm panes or a web dashboard. It works with your existing terminal setup, whether that's VS Code terminals, Windows Terminal tabs, or raw PowerShell windows.

3. **Minimal learning curve.** Coming from 5 manual sessions, you already understand the problem. WTP just eliminates friction:
   - Replace: `git worktree add ../projects/task-1 feature/task-1`
   - With: `wtp add feature/task-1` (auto-paths, no typing)
   - Replace: `cd ../projects/task-1` + path confusion
   - With: `wtp cd feature/task-1` (instant jump + tab completion)

4. **Configuration, not coercion.** `.wtp.yml` sits in your repo, you own it. WTP reads it—doesn't enforce anything. You can have zero config and it works fine.

**Your current 5-terminal setup suggests:**

You've already solved the hard part—context management. You know which Claude is working on what, you have the muscle memory for switching, and you're not drowning in coordination overhead.

WTP just makes that **faster** without changing your mental model. That's it.

**The minimal setup:**

```powershell
# Install (one time)
# Windows: choco install wtp  OR  scoop install wtp
# macOS: brew install wtp
# Linux: cargo install wtp

# Create worktrees for your 5 tasks (do this now to replace current mess)
wtp add feature/task-1
wtp add feature/task-2
wtp add feature/task-3
wtp add feature/task-4
wtp add feature/task-5

# Navigate between them (in any terminal)
wtp cd feature/task-1  # Instant jump
wtp cd @               # Back to main

# List them (sanity check)
wtp list

# When task done (one command, no cleanup mess)
wtp remove --with-branch feature/task-1
```

That's the entire workflow. No configuration needed unless you want setup hooks (like `npm install` per worktree).

**Why not the others for you:**

- **Manual git:** You'd stay where you are now—5 terminals, which works but lacks the navigation speed benefit.
- **Branchlet:** Adds IDE integration overhead you don't need.
- **Claude Code Crew:** Classic over-engineering for a solo dev. Web dashboard is bloat for someone who thinks in terminals.
- **GitHub Issues integration:** Useful for teams, adds ceremony for solo work.

**One thing to watch:**

Windows Terminal doesn't have native tab-to-directory memory like iTerm. So `wtp cd feature/task-1` will work, but you'll need to keep your 5 PowerShell windows open (which you're already doing). WTP just makes switching between them faster—`wtp cd @` jumps you back to main in that window, so no getting lost in 5 open directories.

**Try this tomorrow:**

```powershell
# Install WTP
scoop install wtp

# Organize your current 5 sessions into worktrees
wtp add feature/current-task-1
wtp add feature/current-task-2
# ... etc

# Replace your 5 existing terminal directories with the worktrees
# Then just use `wtp cd` to navigate—takes 2 seconds vs finding the folder in your head

# If you hate it, delete it in 30 seconds and go back to raw git. Zero install footprint beyond a binary.
```

The litmus test: Does WTP reduce friction without adding opinion? Yes. Does it respect your autonomy? Yes. Does it bloat your system? No. Those are your three requirements, and it's the only solution that nails all three for someone in your situation.
