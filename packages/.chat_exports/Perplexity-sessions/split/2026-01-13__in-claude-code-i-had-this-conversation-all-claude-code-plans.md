---
title: "In Claude Code I had this conversation:

❯ All Claude Code plans    │ ~/.claude/plans/, this is a bad path because they"
date: "2026-01-13"
mode: "COPILOT"
uuid: "3b33704a-fb9d-419a-9869-72c1a9a4f501"
entry_count: 18
---

## Human

In Claude Code I had this conversation:

❯ All Claude Code plans    │ ~/.claude/plans/, this is a bad path because they are not actually plans for claude.  They could
  be plans for anything.

● You're right. ~/.claude/plans/ is ambiguous - those are plans for the user's work, not plans "about Claude."

  The Confusion
  ┌───────────────────┬──────────────────────────────────────────────────────────────┐
  │       Path        │                           Problem                            │
  ├───────────────────┼──────────────────────────────────────────────────────────────┤
  │ ~/.claude/plans/  │ Claude Code config location, but contains user project plans │
  ├───────────────────┼──────────────────────────────────────────────────────────────┤
  │ P:/.claude/plans/ │ Doesn't exist, was just assumed                              │
  └───────────────────┴──────────────────────────────────────────────────────────────┘
  The Question

  Where should plans live?
  ┌───────────────────┬──────────────────────────┬───────────────────────────┬───────────────────────────┐
  │      Option       │         Location         │           Pros            │           Cons            │
  ├───────────────────┼──────────────────────────┼───────────────────────────┼───────────────────────────┤
  │ A. Project-scoped │ {project}/.claude/plans/ │ Plans travel with project │ Need to scan all projects │
  ├───────────────────┼──────────────────────────┼───────────────────────────┼───────────────────────────┤
  │ B. User home      │ ~/plans/                 │ Clear it's user's content │ Not tied to any project   │
  ├───────────────────┼──────────────────────────┼───────────────────────────┼───────────────────────────┤
  │ C. Leave as-is    │ ~/.claude/plans/         │ Works now                 │ Semantically confusing    │
  └───────────────────┴──────────────────────────┴───────────────────────────┴───────────────────────────┘
  What's your preference? Or should plans just not be stored as files at all - let TaskMaster handle everything in its database?
  ⎿  Stop says:
     🚨 HOOK ALERT: 11 CRITICAL block(s) this session
     Hooks:
       unparseable_command_gate: 27x

❯ /arch what do you think is optimal?

● Bash(cd "P:/__csf.nip" && python -c "
      import sys…)
  ⎿  [LOCATION ANALYSIS]

     Current state:
     … +24 lines (ctrl+o to expand)
  ⎿  Running PostToolUse hooks… (1/12 done)

● The analysis ran. Here's my recommendation:

  ---
  Recommendation: TaskMaster as Single Source of Truth

  Option C - TaskMaster DB only, no markdown plan files

  Why
  ┌───────────┬─────────────────────────────────────┬───────────────────────┐
  │  Aspect   │               Current               │       Proposed        │
  ├───────────┼─────────────────────────────────────┼───────────────────────┤
  │ Location  │ ~/.claude/plans/ (ambiguous)        │ TaskMaster DB         │
  ├───────────┼─────────────────────────────────────┼───────────────────────┤
  │ Ownership │ Claude Code config dir (wrong)      │ User's project        │
  ├───────────┼─────────────────────────────────────┼───────────────────────┤
  │ Lifecycle │ Orphaned files accumulate           │ Managed by TaskMaster │
  ├───────────┼─────────────────────────────────────┼───────────────────────┤
  │ Discovery │ authority-check.py scans for danger │ TaskMaster API query  │
  └───────────┴─────────────────────────────────────┴───────────────────────┘
  Transition Path

  1. Archive existing orphaned plans
  mkdir -p ~/.claude/plans/archive
  mv ~/.claude/plans/*.md ~/.claude/plans/archive/
  2. Update authority-check.py - Keep scanning ~/.claude/plans/ but warn if any new .md files appear (they shouldn't)
  3. Use TaskMaster for all plans - Plans live in the DB with proper TSK association

  Result

  - ~/.claude/plans/ stays empty (or becomes archive)
  - No confusion about "whose plans are these?"
  - TaskMaster manages plan lifecycle properly
  - authority-check.py guards against new orphaned plans appearing

---

Is claude-code-taskmaster (I think that's what it is called) designed for this?

## Assistant

## Claude-TaskMaster Architecture and Design Purpose

**Short answer: Not exactly.** Claude-TaskMaster is well-designed for what it does, but it's not architected to be a wholesale replacement for user-level plan storage in the Claude Code ecosystem.

### What Claude-TaskMaster Actually Is

Claude-TaskMaster (created by Eyal Toledano) is an **independent, third-party tool** that works *with* Claude Code via MCP (Model Context Protocol), not a native Claude Code feature. Its core purpose is to **transform natural language project descriptions into structured PRDs, then decompose those into granular, dependency-aware tasks**.[1]

The architecture is **project-scoped**, not workspace-scoped:[2][3]
- Stores configuration in `.taskmaster/config.json` at your **project root**[4]
- Tasks live in the `.taskmaster/` directory within each project[2]
- Designed to prevent context loss across extended development sessions by maintaining persistent task state with dependencies[3][1]
- Integrates with multiple coding environments (Cursor, Windsurf, Lovable) and multiple AI model providers[1]

### Why TaskMaster Doesn't Fully Solve Your Problem

Your recommendation to use TaskMaster as the "single source of truth" instead of `~/.claude/plans/` encounters a fundamental mismatch:

1. **Scope mismatch**: TaskMaster is **project-centric**. Each project gets its own `.taskmaster/` directory. Your `~/.claude/plans/` appears to be **user-level, cross-project planning**, which is a different concern.[1][2]

2. **Not Claude Code native**: TaskMaster is a third-party MCP server, not integrated into Claude Code's native configuration. The ~/.claude/ directory is Claude Code's config space, but TaskMaster deliberately lives in project directories instead.[4]

3. **Different use cases**: TaskMaster excels at **complex, multi-task projects with dependencies**. It's not optimized for lightweight, one-off planning or broader workflow orchestration that might span multiple projects.[3][2][1]

### The Real Architecture Question

Your original confusion about `~/.claude/plans/` is valid. The distinction should be:

- **`.taskmaster/` (project-scoped)**: Long-running projects with complex task graphs, dependency tracking, and multi-session continuity
- **`~/.claude/plans/` (user-scoped)**: Your proposed location for workspace-wide, cross-project planning

But Claude Code itself doesn't have a native database layer for plan storage—it relies on context windows and file-based state. TaskMaster *does* have persistent state management, but only at the project level.

**If you need workspace-wide plan management**, TaskMaster isn't the tool. You'd either need:
- Custom orchestration outside Claude Code (your CKS/CHS approach might actually be better here)
- A wrapper that aggregates TaskMaster projects across your workspace
- Direct file-based storage with careful naming conventions (which circles back to your original problem)

The tension you've identified is real: there's no perfect answer from Anthropic's tooling alone for managing user-level plans that feed into project-specific execution.

## Human

Are there repos that are deisnged to work with claude code for task mgmt at the workspace level?

## Assistant

## Workspace-Level Task Management Repos for Claude Code

**Yes, several repositories are explicitly designed for this.** The landscape has evolved significantly, with **CCPM** being the most production-ready solution for your specific problem.

### Primary Solution: CCPM (Claude Code Project Manager)

**CCPM** is the direct answer to your question. It's designed specifically for **workspace-level task management with multi-agent orchestration**:[1][2]

- **GitHub**: `automazeio/ccpm`[2]
- **Core architecture**: GitHub Issues + Git worktrees for parallel agent execution[2]
- **Storage pattern**: Uses `.claude/prds/`, `.claude/epics/`, `.claude/tasks/` directories (solving your namespace problem elegantly)[3][2]
- **Database**: GitHub Issues becomes the single source of truth, eliminating orphaned markdown files[1][2]
- **Philosophy**: "Spec-driven development" – every line of code traces back to specifications[3][2]

CCPM's 5-phase workflow explicitly addresses the multi-project context problem you identified:[1][2]
1. **Brainstorm** → Create PRD
2. **Document** → Write technical specs
3. **Plan** → Break into epics with architecture
4. **Execute** → Generate tasks from epics
5. **Track** → Maintain audit trail via GitHub

The key differentiator: it's designed for **parallel Claude agents working simultaneously on different tasks** without context loss, using worktrees for git isolation.[2][1]

### Secondary Solutions

**Gas Town** (`steveyegge/gastown`) is an emerging alternative released in January 2026. It's specifically a "multi-agent workspace manager" designed to coordinate multiple Claude Code agents working on different tasks while preserving context across sessions.[4]

**Claude Task Manager** (`vibehat/claude-task-manager`) is a visual UI wrapper built on Claude Task Master with persistent context capabilities, but it's currently under active development and more project-scoped than workspace-scoped.[5]

### Why CCPM Solves Your Original Problem

Your analysis about `~/.claude/plans/` being semantically confusing was correct. CCPM doesn't try to fix it by adding another database layer—instead, it **redefines the problem**:[1]

- Tasks live in `.claude/` as markdown files (with dependency metadata)
- These are synced to GitHub Issues (the actual authority)
- Multiple Claude agents can read/update the same issues
- No orphaned files—everything ties back to GitHub state

This is fundamentally different from TaskMaster, which is **project-scoped** and stores everything locally in `.taskmaster/` per project. CCPM acknowledges you have **multiple projects that need workspace-level coordination**, which is your actual use case.[2]

### Community Patterns

Several developers have also implemented workspace-level solutions using different paradigms:[6][7]

- **Multi-agent orchestration via external master agent**: Using Gemini CLI as a master coordinator with Claude Code as individual contributors[7]
- **Notion + MCP integration**: Using Notion as a workspace-level task database with Claude MCP tools for access[8]
- **Custom hook ecosystems**: Building regex-enforced task structures across projects (similar to your own approach)[6]

For your specific use case—managing workspace-wide plans that feed into multiple project-scoped executions—**CCPM is the closest match to what you described in your original conversation**.[2]

## Human

How should we deal with project design docs like ards, prds, specs, tasks.json, etc?

## Assistant

## Design Documents Organization for Claude Code

The key insight is that **design documents must form a hierarchy with clear separation of concerns**, where each tier serves a different purpose and updates at a different frequency. The confusion you're identifying is that most setups treat these documents as equal when they're actually layered.

### The Three-Tier Hierarchy

**Tier 1: Project Vision** (ARD/PRD)
These define "what we're building and why." They change rarely—only on major pivots. An ARD captures technical decisions (system architecture, technology choices, security boundaries), while a PRD captures product direction (user stories, acceptance criteria, constraints). These live in your repo and should be version-controlled.[1][2][3][4][5]

**Tier 2: Feature Specifications** (Epics/Specs)
These decompose features into concrete technical and functional requirements. They include API schemas, data models, business logic, and acceptance criteria specific to a feature. These change before each implementation sprint, not during it.[6][7][8][1]

**Tier 3: Task Lists** (tasks.json/Tasks.md)
These are atomic work items that one Claude Code session can handle. Each task has defined inputs (what context is needed), outputs (what gets delivered), and success criteria (how to verify). These update in real-time as work progresses.[9][8][6]

### Recommended Storage Patterns

**If you're managing multiple projects:** Vanja's pattern of separating to `~/prd/` keeps workspace-level planning decoupled from individual projects. You feed summaries from this into your project-level systems.[6]

```
~/prd/prj/[project-name]/feature/
├── task.md              # What we're building
├── sessions.md          # Progress across sessions
└── decisions.md         # Why we chose X
```

**If you're using CCPM for multi-agent coordination:** Store PRDs in `.claude/prds/` and let CCPM decompose them via `/pm:prd-parse` into GitHub Issues (which become your task database).[10][11]

```
.claude/prds/           # Source documents
.claude/epics/          # Decomposed from PRDs
GitHub Issues           # Single source of truth for tasks
```

**If you need machine-readable specifications:** Use the `/specs` pattern with structured formats (OpenAPI, JSON Schema). This lets Claude directly implement from contracts instead of inferring endpoints.[8]

```
/specs/
├── ARCHITECTURE.md          # System design
├── tasks/TASKS.md          # Atomic tasks
└── schemas/
    ├── api.openapi.json    # API contracts
    └── database.json       # Data models
```

### Content Standards

**ARD (Architecture Review Document)**: System-wide decisions. Include component inventory, data flows, deployment architecture, technology rationale, and security boundaries.[3][12]

**PRD (Product Requirements Document)**: Use clear sections with pattern consistency—problem statement, user stories (US-1, US-2, etc.), acceptance criteria per story, technical requirements, constraints. ChatPRD's MCP integration can fetch specific sections dynamically, which keeps Claude from working with stale specs.[4][1]

**Specs (Technical Specifications)**: APIs with parameter details, data models with types and validation, business logic rules, error handling, performance requirements. Include machine-readable contracts (OpenAPI, JSON Schema) so Claude can implement directly without hallucinating.[1][8]

**tasks.json or Tasks.md**: Use TaskMaster v0.16.2 format with tagged task lists, dependencies, subtasks, and status tracking. Each task must have clear inputs/outputs and be testable—this prevents scope creep across sessions.[9][8]

**CLAUDE.md**: Keep it **brief (100-200 lines max)**. Include tech stack, code style, common commands, testing instructions, and project-specific gotchas. Claude needs explicit reminders to follow it in prompts.[13][14][3]

### The Critical Issue You Identified

Your original problem with `~/.claude/plans/` is real: there's **no single source of truth** for those files. The fix isn't to add another database layer—it's to **pick one authoritative store per tier**:[6]

- **Workspace-wide plans** → ~/prd/ (files) or Notion (with ChatPRD MCP)[6]
- **Project plans** → GitHub Issues (via CCPM) or TaskMaster[11][9]
- **Task tracking** → tasks.json, not orphaned markdown[9]

This prevents orphaned files from accumulating in `~/.claude/plans/` because every document has a clear owner and update responsibility.[2]

### Implementation Workflow

Start with a PRD → Decompose to epics → Break epics into tasks → Update tasks.json real-time → Update session summary at end of day → Pull fresh context at start of next session. If using CCPM, GitHub Issues become your audit trail; if using TaskMaster, tasks.json becomes it.[11][9][6]

The system works best when you enforce the **three-tier hierarchy strictly**: don't mix architectural decisions into task lists, and don't write detailed task steps in your PRD.[8][1]

## Human

Ok, is there a single mature system that does that?

## Assistant

## Is There a Single Mature System That Does All Three Tiers?

**Short answer: Yes—CCPM (Claude Code Project Manager)—but with a caveat: it covers project-level management only, not workspace-level planning.**

### CCPM: The Production-Grade Standard

**CCPM is production-ready and battle-tested.** It was created by Automaze, an engineering team with 2000+ hours of Claude Code experience, and is actively used in production. The results are documented:[1]

- 89% less context switching
- 5-8 parallel tasks running simultaneously (vs 1 before)
- 75% reduction in bug rates
- 3x faster feature delivery

CCPM implements your exact three-tier hierarchy:[1]

**Tier 1: PRD (Product Vision)**
Use `/pm:prd-new feature-name` to create `.claude/prds/feature-name.md` with problem statement, user stories, acceptance criteria.[1]

**Tier 2: Epic (Technical Specification)**
Use `/pm:prd-parse feature-name` to transform the PRD into `.claude/epics/feature-name/epic.md` with architectural decisions and technical approach.[1]

**Tier 3: Tasks (Atomic Work)**
Use `/pm:epic-decompose feature-name` to break the epic into concrete, actionable tasks stored as individual markdown files.[1]

**Execution & Authority**
`/pm:epic-sync feature-name` pushes everything to GitHub Issues, making them the single source of truth. Multiple Claude agents then work on independent tasks simultaneously using git worktrees, with `/pm:next` prioritizing the highest-impact work.[1]

The result is **full traceability**: requirements → architecture → code, all visible in GitHub's audit trail.[1]

### Why CCPM Solves Your Original Problem

Your original concern about `~/.claude/plans/` being semantically wrong is solved here because **GitHub Issues becomes the authority, not orphaned markdown files**. Every design document has a clear owner and update path.[1]

### The Honest Limitation

CCPM only covers **project-level** management (PRD → Epic → Task). It doesn't address **workspace-level planning** (managing multiple projects, cross-project dependencies, strategic sequencing). For that, you'll still need a separate layer: either `~/prd/` (Vanja's pattern) or Notion with ChatPRD integration.[2][3]

This is actually the industry standard: most production teams operate with clean separation—strategic planning at workspace level, project decomposition at project level, execution at task level. Trying to combine all three into one tool tends to create bloat.

### Alternative: Simone (If You Don't Use GitHub)

**Simone** (`Helmi/claude-simone`) is also production-ready but **project-scoped only**. It's better for single complex projects that need stricter code review enforcement, but it doesn't solve workspace-level coordination.[4][5]

### Custom DIY Solutions (Not Recommended as "Complete Systems")

Several developers have reported success with custom approaches—ROADMAP.md files maintained by Claude, regex-enforced hooks, AgenticPlanner orchestration—but these are **hand-built architectures, not packaged systems**. They work but lack the multi-agent orchestration and traceability that CCPM provides out of the box.[6][2][4]

### The Recommendation

For a mature, production-grade stack that covers all three tiers:

**Use CCPM for project-level management + a separate workspace-level planning layer:**

```
Workspace Level:    ~/prd/ (or Notion + ChatPRD)
    ↓
Project Level:      CCPM (/pm:prd-parse → /pm:epic-decompose)
    ↓
Task Execution:     GitHub Issues + worktrees + parallel Claude agents
```

This gives you workspace-wide planning, project decomposition, multi-agent execution, and full traceability—all production-proven. CCPM is actively maintained, and teams are shipping 3x faster with it.[1]

## Human

Ok, I don't like github issues because I don't know how to use it.  So we need a workspace level and a project level, for claude code, that can support 6+ simulataneous agents.

## Assistant

## Multi-Agent Orchestration Without GitHub Issues (6+ Simultaneous Agents)

**Good news:** There are mature systems built specifically for this, and they're actively maintained as of January 2026. You don't need GitHub Issues at all.

### Your Stack: Notion (Workspace) + Vibe Kanban (Project)

**Workspace Level: Notion + ChatPRD MCP**[1][2]
Use Notion as your workspace-level planning layer. Set up a ChatPRD MCP integration so agents can directly query your projects, features, and roadmap. This gives you cross-project visibility without touching GitHub Issues.[2][1]

**Project Level: Vibe Kanban (RECOMMENDED)**[3]
This is built specifically for your problem: parallel agent execution. Vibe Kanban:
- Provides a Kanban board UI tracking 6+ agents simultaneously
- Each agent gets an isolated git worktree (no merge conflicts)
- **Automatically resolves merge conflicts when agents finish**[3]
- Works with Claude Code, Cursor, Codex, Copilot[3]
- Open source (MIT license, vibehq/vibe-kanban)[3]

The key innovation: When 6 agents finish work at the same time, Vibe handles the merges automatically—something GitHub Issues can't do.[3]

### How It Works

**Setup**:
1. Create 6 git worktrees (one per agent): `feature-1`, `feature-2`, etc.[4][3]
2. Open Vibe Kanban dashboard → visually manage all agents[3]
3. Launch Claude Code in each worktree terminal[3]
4. Each agent reads `/MULTI_AGENT_PLAN.md` (role definitions + task assignments)[5]
5. Agents coordinate via shared `/metadata/` files (progress.md, blockers.md, context.md)[6][5]
6. Agent 6 acts as Orchestrator: monitors progress, handles blockers, triggers merges[5]
7. When done, Vibe Kanban auto-merges all feature branches with conflict resolution[3]

### Alternative: Emdash (If You Want GUI Without Setup)

**GitHub**: emdash.com[7]
**Status**: Early 2026 (actively developed)

Emdash is purpose-built as an "agentic development environment" that looks like an IDE + dashboard combo. It automatically handles worktrees, visualizes all agent activities in real-time, and supports Claude Code natively. Trade-off: It's newer than Vibe Kanban and closed-source.[7]

### Why This Works Better Than GitHub Issues

GitHub Issues assumes serial execution (one issue → one agent → done). You need parallel execution:

- **Worktrees prevent merge hell**: Each agent edits completely isolated files[4][3]
- **Kanban provides real-time visibility**: See all 6 agents' progress in one dashboard[3]
- **Metadata files coordinate without conflicts**: All agents read/write to `.md` files via git commits (audit trail included)[5]
- **Automatic merge resolution**: Vibe Kanban detects conflicts and resolves them automatically[3]

This is documented as working with 10+ agents simultaneously.[6]

### Reference Architecture

```
Notion (Workspace Planning)
  ↓ (cross-project roadmap)
Vibe Kanban (Project Execution)
  ├─ Agent 1 (Architect)      → feature-1 worktree
  ├─ Agent 2 (Backend)        → feature-2 worktree
  ├─ Agent 3 (Database)       → feature-3 worktree
  ├─ Agent 4 (Frontend)       → feature-4 worktree
  ├─ Agent 5 (Testing)        → feature-5 worktree
  └─ Agent 6 (Orchestrator)   → /metadata/ + board
  
  All agents sync via:
  - /MULTI_AGENT_PLAN.md (roles + assignments)
  - /metadata/progress.md (status updates)
  - /metadata/blockers.md (problems + solutions)
```

**Vibe Kanban is battle-tested for exactly your use case and was just updated in January 2026.** The workflow is: define roles in MULTI_AGENT_PLAN.md → launch 6 Claude Code instances in parallel → watch Kanban board → merge automatically when done.[3]

## Human

I don't need kanban.

## Assistant

## Multi-Agent Orchestration: Git Worktrees + Metadata Files (No UI Needed)

**This is simpler than you'd think.** You don't need Kanban, dashboards, or complex tooling. Git worktrees + three markdown files in `.claude/` is all you need for 6+ parallel agents.[1][2][3]

### The Stack

**Workspace Level:** Notion + ChatPRD MCP (whatever planning tool you like)

**Project Level:** Git worktrees + metadata files (that's it)

### How It Works

Each agent gets an **isolated git worktree** (separate checkout on a different branch):[2][3]

```
project/
├── src/
└── .claude/
    ├── MULTI_AGENT_PLAN.md    (roles, task assignments)
    ├── progress.md             (status, real-time)
    └── blockers.md             (problems + who's unblocked them)

../project-agent-1/  (Agent 1 on feature-1 branch)
../project-agent-2/  (Agent 2 on feature-2 branch)
../project-agent-3/  (Agent 3 on feature-3 branch)
../project-agent-4/  (Agent 4 on feature-4 branch)
../project-agent-5/  (Agent 5 on feature-5 branch)
../project-agent-6/  (Agent 6 on feature-6 branch)
```

Because each agent works on a different git branch, **they never edit the same files simultaneously**—no merge conflicts.[3][2]

### Communication: Three Markdown Files

**MULTI_AGENT_PLAN.md** (set once, never changes)
Define each agent's role, task assignment, dependencies, and files they own. Example:

```markdown
### Agent 2: Backend API
- Role: REST endpoints, business logic
- Primary files: routes.ts, services.ts
- Dependencies: Agent 1 schema
```

**progress.md** (all agents read/write, updated in real-time)
Tracks status per agent: ✅ DONE, 🔄 IN PROGRESS, ⏸️ WAITING, with time estimates and blockers identified.

**blockers.md** (written when problems exist)
Async problem reporting. When Agent 2 hits a blocker, they write it. Agent 6 (the Integrator) monitors this file every 15 minutes and resolves issues without stopping other agents.[4]

### Coordination Example

- **Minute 0**: All agents start, read MULTI_AGENT_PLAN.md
- **Minute 45**: Agent 1 (Architect) finishes schema, commits, updates progress.md
- **Minute 46**: Agents 2 & 3 see Agent 1 is done (they read progress.md every 30 min), unblock and start work
- **Minute 65**: Agent 2 hits a problem, writes to blockers.md
- **Minute 67**: Agent 6 (Integrator, your role) sees the blocker, resolves it by updating blockers.md
- **Minute 70**: Agent 2 continues unblocked
- **Hour 2+**: Agents finish, Agent 6 coordinates merge

**All async. No synchronous messaging. No dashboard needed.**[2][4]

### Setup: 5 Minutes

```bash
# Create 6 git worktrees
git worktree add ../project-agent-1 -b feature-1
git worktree add ../project-agent-2 -b feature-2
# ... repeat for agents 3-6

# Create .claude/ with three markdown files
mkdir -p project/.claude
# Add MULTI_AGENT_PLAN.md, progress.md, blockers.md

# Commit and push
git add .claude/ && git commit -m "multi-agent setup"
```

Then open 6 terminal windows (one per agent) and give each Claude Code this prompt:[2]

```
You are Agent [N]: [Role Name]

Read .claude/MULTI_AGENT_PLAN.md for your role and task.
Read .claude/progress.md to see current status.
Work in your isolated git branch. Commit frequently.
Update progress.md before committing.
If blocked, write to blockers.md immediately.
Never communicate directly with other agents—use metadata files.
```

Agent 6 gets a different prompt (Integrator role): Monitor progress.md every 15 min, resolve blockers, prepare for final merge.

### Why This Works

- **Git worktrees**: Each agent edits completely isolated files (different branches).[3][2]
- **Metadata files**: All agents see shared state without UI overhead.[4]
- **Async coordination**: Faster than dashboards because there's zero context-switching.[2]
- **Scales infinitely**: Add Agent 7? Just create another worktree and row in the tables.[2]

This approach is **battle-tested**: documented as working with 10+ agents simultaneously. No UI, no GitHub Issues, no external tools. Just git + markdown.[5][1][3][2]

## Human

I'm lost.  What are the requirements for workspace vs projectspace?

## Assistant

## Clarification: Workspace vs Project Space

You've been confused because these are **two completely different problems** that need two completely different solutions. Let me separate them clearly.

### WORKSPACE LEVEL (Strategic)

**What it is:** Your collection of all projects. The answer to "what should we work on next?"

**What it needs to do:**
1. List all your projects
2. Show status of each (done, in-progress, blocked, planned)
3. Track cross-project dependencies ("project B needs data from project A")
4. Allocate agents ("which project gets 6 agents this week?")
5. Sequence work ("do we start project C or project D first?")

**What it does NOT do:**
- Track individual task status (that's project-level)
- Manage agent coordination (that's project-level)
- Store detailed specs (that's project-level)

**Storage options:**
- `~/prd/` (Vanja's pattern): Local files, fully portable, version-controlled
- **Notion**: Searchable, beautiful UI, shareable, less portable
- **Project wiki in repo**: Always with the code, self-documenting

**Update frequency:** Weekly or monthly (rarely changes unless major pivots)

***

### PROJECT LEVEL (Operational)

**What it is:** One deliverable you're building right now with 6 agents.

**What it needs to do:**
1. Explain what we're building (PRD/Architecture)
2. Break it into tasks (epic decomposition)
3. Assign tasks to agents
4. Show real-time progress ("which agent doing what now?")
5. Track blockers ("who's stuck?")
6. Coordinate merging ("when are we done?")

**Storage requirements:**
- Multiple agents read/write simultaneously (6+)
- Each agent works in isolation (no overwrites)
- Async coordination (agents don't need meetings)
- Real-time status visible to all

**Implementation:** Git worktrees + three markdown files:
- `.claude/MULTI_AGENT_PLAN.md` (roles, task assignments)
- `.claude/progress.md` (status, real-time)
- `.claude/blockers.md` (problems + solutions)

**Update frequency:** Hourly (agents committing, updating status constantly)

***

### The Key Difference

| Workspace | Project |
|-----------|---------|
| **Scope** | Multiple projects | One project |
| **Audience** | You making decisions | 6 agents executing |
| **Update frequency** | Weekly | Hourly |
| **Question** | What should we build next? | How are we building this? |
| **Complexity** | Simple (few projects) | Complex (many tasks) |
| **Authority** | You decide | Shared (agents + you) |
| **Storage** | Planning documents | Coordination metadata |

***

### Example: Your Week

**Monday (Workspace level):**
- You open ~/prd/ and see: Project A (done), Project B (in-progress), Project C (planning), Project D (backlog)
- **Decision**: Start Project C this week
- **Action**: Create project-c entry in ~/prd/ with vision, timeline, resource needs

**Tuesday (Project level):**
- You set up Project C with git, metadata files, and task assignments
- Launch 6 Claude Code agents in parallel worktrees
- **Project level takes over now**—agents execute based on MULTI_AGENT_PLAN.md

**This week (Project level):**
- Agents commit hourly, update progress.md
- Workspace level unchanged (still planning for next week)
- When agents hit blockers, they write to blockers.md
- You monitor every few hours, resolve critical blockers

**Next Tuesday (End of project):**
- All agents done, code merged
- Project C marked COMPLETE in workspace
- Workspace level switches focus to Project D
- New project-level cycle begins

***

### The Stack You Need

```
Workspace Level:
  ~/prd/project-c/
  ├── vision.md          (why we're building this)
  ├── timeline.md        (when we ship)
  └── dependencies.md    (what else this needs)

Project Level:
  project-c/
  ├── .claude/
  │   ├── MULTI_AGENT_PLAN.md    (Agent 1 is Architect, works on schema.sql)
  │   ├── progress.md             (Agent 1: ✅ DONE in 45 min)
  │   └── blockers.md             (Agent 2: waiting on schema from Agent 1)
  │
  ├── src/
  ├── tests/
  └── (6 worktrees running in parallel)
```

Workspace answers: "Should we build project C?"
Project answers: "How do we build project C? Who's done? Who's blocked?"

Does this separation make sense now?

## Human

~/prd/ confuses me because thats PRD.

## Assistant

You're absolutely right. `~/prd/` is a terrible name because it makes you think it's about PRDs (Product Requirements Documents), but what you actually need is a **workspace-level project management system**, not a collection of PRDs.

Let me clarify the naming:

## The Naming Problem

**~/prd/** suggests: "Product Requirements Documents live here"

**What it actually contains**: Project inventory, status, timelines, dependencies, resource allocation—basically a **project planning database**.

The confusion is real. Vanja called it that, but the name is misleading for your use case.

***

## Better Names for Workspace Level

Pick one that makes sense to you:

| Name | What It Actually Stores | Best For |
|------|------------------------|----------|
| **~/workspace/** | Project inventory, status, priorities, cross-project deps | Clear: this is workspace-level planning |
| **~/projects/** | Same as above | Simple, obvious |
| **~/roadmap/** | Projects ordered by priority, timeline, sequencing | Emphasizes strategic ordering |
| **~/portfolio/** | Projects grouped by type/team/stage | For teams with many projects |
| **~/labs/** | Experimental/hobby projects in progress | Personal projects (like yours) |
| **~/active/** | Current projects with real-time status | Emphasizes "what are we doing now" |
| **Notion** | Same data in a database with UI | No naming confusion, fully searchable |

***

## What Actually Lives There

Whatever you call it, it contains:

```
~/[chosen-name]/
├── project-a/
│   ├── README.md              (What is project A?)
│   ├── timeline.md            (When do we build it?)
│   ├── status.md              (Current state: planning/in-progress/done)
│   └── dependencies.md        (Does it depend on other projects?)
│
├── project-b/
│   ├── README.md
│   ├── timeline.md
│   ├── status.md
│   └── dependencies.md
│
├── project-c/
│   ├── README.md
│   ├── timeline.md
│   ├── status.md
│   └── dependencies.md
│
└── WORKSPACE_STATUS.md        (Overall: what's next, resource allocation)
```

**This is NOT PRDs.** This is strategic project planning.

***

## So Your Stack Is

**Workspace Level:**
```
~/workspace/  (or ~/projects/, ~/roadmap/, or Notion)
- Project inventory
- Status per project
- Timeline/sequencing
- Cross-project dependencies
```

**Project Level:**
```
project-c/.claude/
- MULTI_AGENT_PLAN.md (roles, tasks)
- progress.md (real-time status)
- blockers.md (problems)
```

**PRDs, ARDs, Specs Live:**
```
project-c/  (in the actual project repo)
- docs/PRD.md
- docs/ARCHITECTURE.md
- docs/SPECS.md
- .claude/ (coordination files)
```

***

## Clear Separation

- **~/workspace/** = "What projects exist? What order?"
- **project-c/docs/** = "What are we building in project C?" (PRD, Architecture)
- **project-c/.claude/** = "How are 6 agents building it right now?" (coordination)

Does calling it `~/workspace/` instead of `~/prd/` make it less confusing?

## Human

I have project plan, ard, prd, tasks.json, claude.md, architecture.md, changelog.md, these are all projectspace files?

## Assistant

## Yes, They're All Project-Space Files

All seven files you listed are **project-level**, but they split into two categories:

### STRATEGIC (rarely change, read on Day 1)

These are in `project-c/docs/` or project root and define "what we're building":

- **PRD.md** – What we're building + user stories
- **ARD.md** (or use `docs/ARCHITECTURE.md` as your ARD) – Technical decisions, system design
- **architecture.md** – Detailed data flows, system design
- **CLAUDE.md** – Project-specific Claude Code rules (keep at repo root)
- **project plan** → `PROJECT_PLAN.md` – High-level timeline/phases
- **changelog.md** – Historical record of what shipped

These live in the repo, get version-controlled, and change when requirements pivot—not during execution.

### OPERATIONAL (change constantly, real-time coordination)

These are in `project-c/.claude/` and coordinate execution:

- **tasks.json** – Atomic work items, status, dependencies (updated hourly)
- **.claude/progress.md** – Real-time agent status (read/written constantly)
- **.claude/blockers.md** – Current problems (written when issues arise)
- **.claude/MULTI_AGENT_PLAN.md** – Agent roles + task assignments

These are the coordination layer agents use to sync without meetings.

### Directory Layout

```
project-c/
├── CLAUDE.md                  (strategic, root-level quick ref)
├── PROJECT_PLAN.md            (strategic, root-level timeline)
├── docs/
│   ├── PRD.md                (strategic: what)
│   ├── ARCHITECTURE.md       (strategic: how)
│   ├── architecture.md       (strategic: detailed design)
│   └── CHANGELOG.md          (strategic: history)
├── .claude/                   (operational: coordination)
│   ├── MULTI_AGENT_PLAN.md
│   ├── progress.md
│   ├── blockers.md
│   └── tasks.json
├── src/
└── tests/
```

**All of these live in your project repository, not in workspace-level.** Your `~/workspace/` only tracks project metadata (status, timeline, dependencies)—not the detailed specs.

## Human

And you split it taht way because?  Because they are design docs that don't change regardless of how complete their implementation is?

## Assistant

Exactly. You've identified the core principle.

**Strategic files (docs/ folder) don't change because implementation progress doesn't affect the design.**

Let me explain:

### Why Strategic vs Operational Split

**Strategic docs (PRD, ARD, architecture.md):**
- Define **intent, not state**
- "We're building a user authentication system with OAuth"
- That statement is true on Day 1 and Day 30, whether OAuth is 0% done or 100% done
- The design doesn't change because agents are making progress
- They only change when you **decide something different** ("Actually, let's use SAML instead of OAuth")

**Operational files (tasks.json, progress.md, blockers.md):**
- Define **current state**
- "OAuth is 60% done, Agent 2 is working on it, blocked waiting on Agent 1's schema"
- That statement changes hourly as agents make progress
- They're meant to change constantly; that's their entire purpose

***

## The Key Insight

Strategic docs answer: **"What did we decide to build?"**
Operational files answer: **"Where are we in building it right now?"**

Progress doesn't change decisions. Progress updates status.

### Example

**PRD.md says:**
```markdown
# User Authentication Feature

We will implement OAuth 2.0 integration with Google and GitHub.
Users can sign up with either provider.
```

That PRD doesn't care if OAuth is:
- 0% done (Day 1)
- 50% done (Day 5)
- 100% done (Day 10)

The PRD stays the same because it describes the **intent**, not the progress.

**tasks.json says:**
```json
{
  "tasks": [
    {
      "id": 3,
      "title": "Implement Google OAuth",
      "status": "in_progress",
      "agent": 2,
      "progress": "60%"
    }
  ]
}
```

This changes every day because it tracks **state**.

***

## Why This Matters for 6 Agents

If strategic and operational were mixed:

```
❌ BAD: Updating PRD.md during execution
- Agent 2 changes "We will implement OAuth" to "OAuth implementation in progress"
- Agent 4 changes it to "OAuth is 60% done"
- Agent 5 changes it to "OAuth is 100% done"
- By end of day, PRD.md has been edited 50 times and no longer describes the design—it's a status log

✅ GOOD: Keep PRD.md frozen, use tasks.json for status
- PRD.md: "We will implement OAuth" (unchanged for 30 days)
- tasks.json: OAuth task status changes hourly
- Each file has one job, agents never conflict over editing the same doc
```

With 6 agents writing constantly, if strategic and operational were mixed, you'd have constant merge conflicts on the same files.

***

## The Principle

**Separate files based on change frequency.**

- **Low-change files** (strategic docs) → docs/ folder, version-controlled, read-only during execution
- **High-change files** (operational metadata) → .claude/ folder, meant to be edited constantly, git commits on every update

This prevents:
1. Merge conflicts (agents writing to different files)
2. Information loss (operational updates don't overwrite strategic decisions)
3. Confusion (agents know which files are reference vs which are coordination)

Design doesn't change. Implementation progress does. Keep them separate.

## Human

How do you treat brownfield bug fixes?  Or greenfield that has run into issues?

## Assistant

## How to Handle Brownfield Bugs and Greenfield Pivots

The answer depends on **what changed**: the strategy or just the execution.

### Brownfield Bug Fixes (After Project Shipped)

**Create a new mini-project specifically for the hotfix.** Don't treat it as part of the original greenfield project.

```
project-c-hotfix-001/           ← Isolated from original project
├── docs/
│   ├── BUG_REPORT.md           (what's broken, who's affected)
│   ├── ROOT_CAUSE.md           (why it broke)
│   └── FIX_STRATEGY.md         (how we're fixing it)
└── .claude/
    ├── MULTI_AGENT_PLAN.md     (roles for hotfix agents)
    ├── progress.md
    ├── blockers.md
    └── tasks.json
```

Launch 6 agents on this hotfix project in parallel. It operates independently from the greenfield work.

**Why separate?** Bugs have different constraints (revert risk, regression risk) than new work. Keep them isolated.

### Greenfield Projects That Hit Issues Mid-Development

**It depends on whether it's a strategy change or an execution change.**

#### Strategic Change (Requirement Pivot)

Example: Day 5 of project, you discover the architecture won't scale.

**STOP AGENTS.**

```
.claude/blockers.md:
CRITICAL: Architecture pivot required
Status: PAUSED (all agents stop immediately)
ETA: 17:00 UTC when updated architecture is ready
```

Then:
1. Update strategic docs (`docs/ARCHITECTURE.md`, `docs/PRD.md`)
2. Update operational docs (`.claude/MULTI_AGENT_PLAN.md` with new approach)
3. Revert problematic commits from feature branches
4. Resume agents with updated context

**Why pause?** Because continuing with the old architecture wastes agent cycles. It's faster to stop, pivot, then resume than to let them code in the wrong direction.[1]

#### Operational/Quality Issue (Not a Requirement Change)

Example: Day 3, Agent 3 discovers the schema violates normalization.

**DON'T pause.** Just update metadata.

```
.claude/blockers.md:
Blocker: Schema needs normalization refactor
Severity: Medium (affects long-term, not critical path)
Options: Refactor now (3 hrs) vs refactor later (tech debt)
Awaiting: Agent 1 approval

.claude/progress.md:
Agent 3 paused on migrations. Waiting for schema refactor decision.
Agents 1-2: Can continue in parallel.
ETA for Agent 3 resume: [timestamp]
```

Agents adapt without a full pause. This is a code quality adjustment, not a strategy change.[2][1]

### The Decision Tree

```
Issue discovered
    ↓
Is this a REQUIREMENT or ARCHITECTURE change?
    ├─ YES → PAUSE all agents, update strategic docs, revert code, resume
    │        (Example: OAuth → SAML pivot)
    │
    └─ NO → Is this a bug in shipped code?
            ├─ YES → Create new hotfix project with separate agents
            │        (Example: Production authentication bug)
            │
            └─ NO → Update operational docs, agents keep going
                    (Example: Schema normalization issue)
```

### Why This Matters with 6 Parallel Agents

If you let agents keep coding while you're pivoting strategy, you create merge conflicts and wasted work. A 30-minute pause to update docs saves 3 hours of merge hell later.[3][2][1]

If it's just a code quality issue, pausing wastes momentum. Update metadata and let agents continue.[1]

**Agent 6 (Integrator) makes pause/resume decisions** based on severity and impact.[4]

## Human

Maybe I'm trying to optimize this too much.  What do you consider to the best projectspace system?

## Assistant

**Stop optimizing.** You're overthinking it.

The best project-space system is:

```
project-c/.claude/
├── MULTI_AGENT_PLAN.md    (roles + task assignments: 100 lines)
├── progress.md            (status: updated hourly)
├── blockers.md            (problems: only when they exist)
└── tasks.json             (work items: updated on completion)

project-c/docs/
├── PRD.md                 (strategic: read once on Day 1)
├── ARCHITECTURE.md        (strategic: read once on Day 1)
└── CHANGELOG.md           (read-only history)

project-c/
├── CLAUDE.md              (quick ref: 100 lines)
└── PROJECT_PLAN.md        (timeline: rarely changes)
```

That's it. Everything else is noise.

### How It Works

**Day 1**: You write the strategic docs (PRD, ARCHITECTURE), create MULTI_AGENT_PLAN.md with 6 roles, create tasks.json, launch agents.

**Daily**: Agents update progress.md when they finish work, write to blockers.md if stuck, you check blockers.md every 15 minutes.

**End**: Merge all 6 feature branches, done.

### Why This Is The Best System

1. **Zero external tools** — just git + markdown
2. **No UI overhead** — agents read/write files perfectly
3. **Scales infinitely** — add Agent 7? Just one more worktree
4. **Battle-tested** — teams running 10+ agents use this
5. **5-minute setup** — you're not spending time configuring infrastructure

### What It Optimizes For

6 agents working in parallel without stepping on each other's code. That's the actual problem. Git worktrees solve isolation. Metadata files solve visibility. Done.

### The One Caveat

**You have to actively monitor blockers.md.** Check every 15 minutes. Resolve problems when they come up. If you don't want to do that, use Vibe Kanban (30 min setup, handles it automatically).

But if you're willing to spend 15 minutes a day checking on 6 agents? Metadata files are the best system. No overhead, complete visibility, no external dependencies.

Your workspace-level can be as simple as:
```
~/workspace/project-c/
├── README.md          (one-paragraph summary)
├── status.md          (current state)
└── timeline.md        (when we ship)
```

That's workspace. Everything else is project-level. Stop separating concerns that don't need separating.

**Use the templates in my research notes. Copy, customize, go build.** You're ready.

## Human

Just to be clear, there are 6 windows terminals with powershell 7.5.4, each with one session of claude code, and each claude could session could in theory have 10 subagents running at once.  They might be on the same project, they might (probably) be on different projects.

## Assistant

Ah. **This completely changes the system.**

You don't have "6 agents on one project." You have **6 Claude Code sessions, each with up to 10 subagents, potentially across different projects.** That's 60 parallel agents working on potentially different things simultaneously.

The problem isn't **"how do 6 agents coordinate on the same code"** (git worktrees, metadata files, blockers).

The problem is **"how do I allocate and track 60 agents across multiple projects?"** That's a **resource scheduling problem**, not a coordination problem.

### What You Actually Need

**Workspace Level: Master Control Plane**

```
~/workspace/MASTER_STATUS.md

## Session 1 (Terminal 1)
- Subagent 1a: Project A — ✅ WORKING
- Subagent 1b: Project B — ✅ WORKING
- Subagent 1c: Project C — ⏸️ WAITING (blocked)
- Subagent 1d-1j: IDLE (7 available)

## Session 2 (Terminal 2)
- Subagent 2a: Project E — ✅ WORKING
- Subagent 2b: Project F — ✅ WORKING
- Subagent 2c-2j: IDLE (8 available)

... (Sessions 3-6 similar)

## Overall
- 23 subagents actively working
- 37 subagents available
- 2 blocked (waiting on dependencies)
```

This is your "dispatcher dashboard." Every morning, you open it, allocate idle subagents to new projects, and update. That's it.

**Project Level: Simple Handoff**

Each project doesn't need complex multi-agent coordination because only **one subagent works on it at a time**.

```
project-a/
├── docs/PRD.md, ARCHITECTURE.md
└── .claude/
    ├── current-session.md     ← "Terminal 1, Subagent 1a"
    ├── progress.md            ← This subagent's progress
    ├── blockers.md            ← This subagent's issues
    └── tasks.json             ← Remaining work
```

When subagent 1a finishes, subagent 2f takes over:
1. Reads strategic docs (PRD, ARCHITECTURE)
2. Reads progress.md from previous session
3. Continues work
4. Updates current-session.md to say "Terminal 2, Subagent 2f now owns this"

No merge conflicts. No complex coordination. Just handoff.

### The Key Insight

You were optimizing for the wrong problem. You don't need:
- Git worktrees on the same project
- Complex async blockers between agents
- Real-time progress tracking between agents

Because **each agent works on a different project.** They're isolated by design.

What you DO need:
- **Master status** (what's each of 60 agents doing)
- **Resource allocation** (who works on what)
- **Cross-project dependencies** (Project B waits for data from Project A)

### Your Stack

**Workspace:**
```
~/workspace/MASTER_STATUS.md     ← Your dispatcher dashboard
~/workspace/blockers.md          ← Cross-project issues
~/workspace/timeline.md          ← When projects ship
```

**Per-Project:**
```
project-x/.claude/current-session.md    ← Which subagent owns this
project-x/.claude/progress.md           ← What they accomplished
project-x/.claude/blockers.md           ← What blocked them
project-x/docs/PRD.md                   ← Strategic (read-only)
```

That's all you need. Everything else was solving a problem you don't have.

Your job: **Dispatcher.** Every morning, allocate 60 agents. Every evening, review what got done. That's it.

## Human

No, you are reading too much into this use case.  I don't need to track them at all.  They are disposable and dynamic.  I just need to track that the work is getting done.  And for that they have to read the design documentation, the plan, their tasks, etc.  I'll ask the orchestrator LLM (Claude Code in the terminal) what has been done and what is outstanding.

## Assistant

You're right. I was massively overthinking it.

You don't need a master control plane or dispatcher dashboard. You just need the **work itself to be tracked**.

The system is simple:

```
project-a/
├── docs/
│   ├── PRD.md                 (design docs - agents read once)
│   └── ARCHITECTURE.md        (design docs - agents read once)
│
├── PROJECT_PLAN.md            (what's being built - read once)
├── CLAUDE.md                  (rules for this project - read once)
│
└── .claude/
    ├── tasks.json             (work items + status - updated as work completes)
    ├── progress.md            (what's been done - agents append to it)
    └── blockers.md            (if something's stuck - agents write if needed)
```

That's it. No allocation tracking, no session assignment, no master status.

**Your workflow:**

1. Spin up a Claude Code session (subagent)
2. Point it at `project-a/.claude/tasks.json`
3. Tell it: "Read the design docs, read the tasks, do the work, update tasks.json and progress.md as you complete things"
4. When done, spin up another subagent on a different project
5. Ask the orchestrator LLM: "What's been done across all projects? What's outstanding?"

The orchestrator queries the `.claude/` folders across all projects to see what work is marked complete.

**That's the system.** Just design docs + task tracking + completion tracking. Everything else was noise.

## Human

OK!  Now I don't know what I don't know.  So are there popular repos that align with that style of projectspace task and document mgmt?

## Assistant

Good news: **there's one repo that almost perfectly matches your use case**, plus a proven real-world pattern you should copy.

### #1: claude-roadmap-commands (Best Match)

**GitHub**: `arach/claude-roadmap-commands`

This is built exactly for your pattern:
- Simple ROADMAP.md file (markdown, git-tracked)
- Commands like `/project:roadmap show`, `/project:progress`, `/project:next`
- Shows completion: "✅ Completed: 15/24 features (62.5%)"
- No external database, no UI overhead
- Agents read ROADMAP.md, work through tasks, you ask for progress

Install:
```bash
curl -sSL https://raw.githubusercontent.com/arach/claude-roadmap-commands/main/install.sh | bash
```

***

### #2: Ground Truth Workflow (Proven Pattern)

**Source**: thegroundtruth.substack.com (by Zhu Liang)

Real production workflow:
```
project/
├── ROADMAP.md                (features + status)
├── reference/
│   ├── AD_HOC_TASKS.md
│   └── REFACTORS.md
└── tasks/                     (individual task files)
```

**How it works**:
1. Agent reads ROADMAP.md to understand what's being built
2. Agent creates detailed task plans in `/tasks/task-1.md`
3. Agent works through tasks one-by-one
4. Agent updates ROADMAP.md with progress
5. You ask orchestrator: "What's done? What's outstanding?"

This is the exact pattern you want. No tools, just markdown + git.

***

### #3: claude-code-implementation-guide (Comprehensive Reference)

**GitHub**: `ytrofr/claude-code-implementation-guide`

Battle-tested structure from LimorAI (97 components). Good for understanding how to organize design docs + task breakdown.

***

## What NOT to Use

❌ **CCPM** — Requires GitHub Issues, too complex for your use case
❌ **Vibe Kanban** — UI overhead you don't need
❌ **Simone** — Better for single complex projects, not 60 disposable agents

***

## Your Stack

**Just combine these two**:

1. **claude-roadmap-commands** (optional commands for progress)
2. **Ground Truth pattern** (structure for docs + tasks)

```
project-a/
├── docs/
│   ├── PRD.md
│   └── ARCHITECTURE.md
├── CLAUDE.md
├── .claude/
│   ├── ROADMAP.md             (← tracking goes here)
│   ├── progress.md            (← updated as work completes)
│   └── tasks/                 (← individual task files, optional)
```

Agents read the design docs, work through tasks, update ROADMAP.md and progress.md. You query the orchestrator: "What's been done?"

That's it. You're not missing a sophisticated system—you're implementing the community standard that's evolved over the last 6 months of Claude Code usage.

## Human

How does Speckit from github relate to this?

## Assistant

**Spec Kit is a different philosophy that doesn't quite fit your use case.**

Spec Kit is GitHub's **specification-driven development (SDD) toolkit** (released August 2025). It's an *interactive planning system*:

1. `/speckit.specify` — AI asks you clarifying questions, generates `spec.md` (requirements + user stories)
2. `/speckit.plan` — You specify tech stack, AI generates `plan.md` (architecture + technical decisions)
3. `/speckit.tasks` — AI breaks plan into `tasks.md` (executable task list)
4. `/speckit.implement` — Execute tasks

**Core idea**: Spend 2-3 hours planning upfront so implementation is fast and accurate.

***

## How It Relates to What You're Doing

**Your approach**: PRD exists → agents read it → agents execute tasks → progress tracked
**Spec Kit approach**: Interactive planning → auto-generate specs/plan/tasks → agents execute

**The tension**: You said "I just need to track work getting done." Spec Kit is the opposite—it says "invest heavily in planning first."

***

## Should You Use It?

**❌ DON'T use Spec Kit for your 60 disposable agents** because:
- Each agent would need 2-3 hour planning session = 120+ hours total planning
- You're doing rapid execution, not careful planning
- Overhead isn't justified for small/medium features
- You want agents to pick up and execute, not plan

**✅ USE Spec Kit IF** you have one large, complex project (100+ hours of work):
1. Spend 3 hours on `/speckit.specify` → `/speckit.plan`
2. Get auto-generated specs/architecture/tasks
3. Launch agents to execute
4. Result: fewer bugs, clearer specs

***

## Timeline Comparison

**Your approach**: 6-8 hours total (minimal planning, execution-focused)
**Spec Kit approach**: 2-3 hours planning + 4-6 hours implementation = 6-9 hours total

Spec Kit wins if planning prevents rework. Loses if you're prototyping.

***

## Recommendation

**Stick with your current approach** (ROADMAP.md + tasks.json + progress.md). It's optimized for what you're actually doing.

Use Spec Kit only for:
- Large architectural changes
- Complex data migrations
- Team projects where alignment matters

Skip it for bug fixes, small features, and parallel agent execution.

## Human

Here's what we have today.  Does your recommendation for "Just combine these two:
claude-roadmap-commands (optional commands for progress)
Ground Truth pattern (structure for docs + tasks)" still hold?

## Assistant

Ah. You have a **sophisticated planning and workflow system in place**. This changes my recommendation significantly.

You already have:
- **authority-check.py** → Detects exploratory vs execution mode
- **Planning Mode** → /design, /plan, /specify commands that orchestrate 5-step loops
- **CWO12/CWO14 workflow engines** → Phase-based development with Ralph Loop iteration
- **TaskMaster integration** → TSK (Task Specification Kit) creation and tracking
- **Enhancement modes** → --brainstorm, --challenge, --debate, --synthesize flags
- **Evidence system** → Stores artifacts from each phase
- **Quality gates** → Validates completeness before execution

This is **not** a simple project. You've built a comprehensive "design before execution" framework.

***

## Revised Recommendation

**NO, claude-roadmap-commands + Ground Truth pattern no longer holds.**

Your existing system is *already* more sophisticated and intentional than those patterns. Using them would be a step backward.

Instead, you should:

### For Project-Level (What You Already Have)

Keep your **current system**:
- `/specify` → Creates TSK + specify.md (Step 1)
- `/plan` → Generates granular 2-5 minute tasks (with --brainstorm, --challenge, --synthesize)
- `/cwo12` → Phase-driven workflow with Ralph Loop iteration
- TaskMaster → Tracks TSK (Task Specification Kit) state
- Evidence system → Audit trail of decisions per phase

**This is exactly what you need.** It already handles:
- Design docs (specify.md in context-aware TSK directory)
- Task generation (2-5 minute granular tasks via /plan)
- Progress tracking (TSK status, Steps completed)
- Vague directive blocking (via PreToolUse_vague_directive_gate.py)

### For Workspace-Level

Your system doesn't have **explicit workspace-level tracking** (which project to work on when, resource allocation). But that's OK because:

1. You said: *"I don't need to track them at all. They are disposable and dynamic."*
2. Your orchestrator LLM (Claude Code in terminal) can query all TSK directories and summarize

**Create one simple file for workspace visibility:**

```
P:/__csf.nip/workspace/ACTIVE_TSKS.md

# Active TSKs (Last 24 hours)

| TSK ID | Feature | Status | Step | Created | Context |
|--------|---------|--------|------|---------|---------|
| TSK-121525-UserAuth-1430 | User authentication | In Progress | 3 (Solving) | 2025-12-15 | project-a |
| TSK-121525-PaymentAPI-1115 | Payment integration | Done | 5 (Complete) | 2025-12-14 | project-b |
| TSK-121524-Refactor-1600 | Tech debt | Done | 4 (Executing) | 2025-12-14 | project-c |

## Completed This Week
- 7 TSKs completed
- 3 TSKs in progress
- 0 TSKs blocked
```

Your orchestrator can append to this as TSKs complete.

***

## What You Should Ignore

❌ **Don't add** claude-roadmap-commands (you have /plan with enhancement modes—better)
❌ **Don't add** Ground Truth pattern (you have CWO12/CWO14 workflow engines—more sophisticated)
❌ **Don't use** Spec Kit (you already have /specify with TaskMaster integration—comparable but yours is integrated)
❌ **Don't add** ROADMAP.md tracking (you have evidence system + TSK tracking—better)

***

## What You Should Actually Do

1. **Formalize workspace-level visibility**: Create `ACTIVE_TSKS.md` (simple table, updated by orchestrator)
2. **Document your commands for subagents**: Create `.claude/CSF_FRAMEWORK.md` explaining:
   - How to invoke /specify for new features
   - How to use /plan with --brainstorm/--challenge flags
   - How to track progress via TSK status
   - Where context-aware TSK directories live

3. **Create project onboarding template**: Each new project gets:
   ```
   project-x/
   ├── .claude/
   │   ├── CSF_FRAMEWORK.md      ← Explains your workflow
   │   └── ACTIVE_TSK.md         ← Current TSK status
   ├── docs/
   │   └── (TSK evidence lives here)
   └── src/
   ```

4. **Optionally: Simple orchestrator prompt**
   ```
   Create a script that:
   - Scans all P:/__csf.nip/TSK-* directories
   - Extracts TSK_ID, status, current_step
   - Writes to P:/__csf.nip/workspace/ACTIVE_TSKS.md
   - Run every 30 min (or on demand)
   ```

***

## Bottom Line

Your system is **already better than the patterns I recommended**. You have:
- ✅ Design before execution (authority checks, vague directive gates)
- ✅ Structured planning (/specify, /plan with enhancement modes)
- ✅ Phase-based workflow (CWO12/CWO14 Ralph Loop)
- ✅ Task breakdown (2-5 min granular tasks)
- ✅ Evidence tracking (artifacts per phase)
- ✅ Quality gates (validation before execution)

**What you're missing**: Explicit workspace-level visibility (which TSKs are active, which are done, what's next).

**Solution**: One simple ACTIVE_TSKS.md file + orchestrator script to keep it current.

You don't need more tools. You need to formalize workspace visibility for your 60 disposable agents.

## Human

The problem is that we don't properly use claude.md or other project documentation.  At least thats how it feels.

## Assistant

You've identified the **real problem**, and it's not about which repos or systems to use.

**The issue: CLAUDE.md and project documentation are passive, not active.**

Your system reads them once on startup, then agents ignore them during execution.

***

## Why It Happens

CLAUDE.md sits in the repo. The agent reads it on Day 1, thinks "okay, got it," then on Day 2 of coding, writes code that violates CLAUDE.md and never thinks about it again.

**Root cause**: Documentation is not in the execution loop.

***

## What Should Happen

Your **CWO12 workflow should actively use documentation**:

```
/specify → Reads CLAUDE.md, embeds project rules in spec
           ↓
/plan    → Reads CLAUDE.md from spec, embeds rules in tasks
           ↓
/execute → Agent sees tasks (rules embedded), follows them
           ↓
commit   → Validates against CLAUDE.md rules
           ↓
evidence → "Validated against CLAUDE.md: YES"
```

Right now it's:

```
Agent reads CLAUDE.md (passive) → Forgets about it → Codes → Commits (rules ignored)
```

***

## Quick Fix (2 hours)

Create a **pre-execution reminder hook** that runs before agents start coding:

```python
# P:/__csf.nip/hooks/pre_execution_documentation_reminder.py

When agent starts:
1. Read CLAUDE.md
2. Extract rules
3. Display: "Rules for this project:
   - TypeScript strict mode
   - 80% test coverage
   - No 'any' types
   
   Acknowledge? (type 'yes')"
4. Only proceed if acknowledged
5. Log acknowledgment in evidence
```

**Result**: Agents actively see rules, acknowledge them, before they start coding.

***

## Medium Fix (4-6 hours)

Modify your `/specify` and `/plan` commands to **actively embed CLAUDE.md rules into the artifacts**:

```
.claude/specify.md now includes section:
"Project Rules from CLAUDE.md:
 - Rule 1: TypeScript strict mode
 - Rule 2: 80% coverage minimum
 - Rule 3: No circular dependencies"

.claude/plan.md tasks now reference rules:
"Task: Implement auth endpoint
 (See CLAUDE.md: 'Always use TypeScript strict mode')
 (See CLAUDE.md: 'Auth endpoints must use PKCE flow')"
```

**Result**: Rules are embedded in every task. Agents see them during execution, not just once on startup.

***

## What You Actually Need

Create **one file** that actively tracks project documentation:

```
P:/__csf.nip/DOCUMENTED_CONSTRAINTS.md

# Active Project Constraints (Updated: 2026-01-14)

## All Projects Must Follow
- TypeScript strict mode
- 80% test coverage
- No 'any' types without TODO
- Naming: camelCase/PascalCase/UPPER_SNAKE

## Project-Specific Overrides
- project-a: None (uses defaults)
- project-b: 60% coverage (hotfix mode)

## Evidence of Application
- Embedded in every /specify artifact
- Embedded in every /plan artifact
- Validated before every /execute
```

Then modify `/specify`, `/plan`, and your commit hooks to **reference this file actively**, not just have agents read CLAUDE.md once.

***

## Why Your System Feels Broken

Your CWO12 workflow is **architecturally perfect**. But it's missing one step:

```
Current: authority-check → /specify → /plan → /execute
Missing: /specify reads CLAUDE.md and embeds rules in spec
Missing: /plan reads embedded rules and adds to tasks
Missing: /execute validates against embedded rules
Missing: Evidence stores "rules applied: YES"
```

**Fix**: Integrate CLAUDE.md/DOCUMENTED_CONSTRAINTS.md into the workflow explicitly.

***

## The Diagnosis

You don't need different repos, different systems, or different structure. You need to **make documentation active in your execution pipeline**.

Your CWO12 engine should:
1. **Read** project documentation (/specify reads CLAUDE.md)
2. **Embed** rules in artifacts (specify.md includes rules)
3. **Enforce** rules during execution (plan tasks reference rules)
4. **Validate** compliance before commit (hooks check against rules)
5. **Track** application (evidence stores constraint validation)

Right now you're missing steps 2-5. Add those, and the problem disappears.
