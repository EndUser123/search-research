# Claude Code Parallel Subagents – Design & Implementation Spec (v2.2)

**Author:** System Architect (for downstream LLM implementation)

**Target:** Any capable coding LLM (Claude Code, Roo Code, etc.)

**Goal:** Implement a robust, low-friction pattern so `/cwo` (Cognitive Workflow Orchestrator) and `/exec` (Executor) can **reliably use multiple parallel subagents** when running via Claude Code (or compatible IDE agents).

The design assumes:
- You are on **Windows 11**, working primarily in **Claude Code** (not VSCode).
- You are using **Claude Code or a similar MCP/agentic coding environment** with filesystem access.
- You want **real parallelism** (multiple agents working at once), not fake "parallel Task calls in a single response".

This document is written so another LLM can pick it up and implement everything with minimal back-and-forth.

---

## Quick Start (30 seconds)

1. **Invoke `/cwo` with your epic:**
   ```bash
   claude "You are /cwo. User request: Implement user authentication system.
   Create .claude/ORCHESTRATION.md and output launch instructions for parallel agents."
   ```

2. **Copy-paste the generated `claude` commands into separate terminals:**
   ```bash
   # Terminal B
   claude "You are the Test-Writer agent. Open .claude/ORCHESTRATION.md..."

   # Terminal C
   claude "You are the Implementer agent. Open .claude/ORCHESTRATION.md..."
   ```

3. **All agents coordinate via the shared `.claude/ORCHESTRATION.md` file.**

That's it. No XML, no fake APIs, no single-session parallelism claims. Just multiple terminals, one shared file, and clear roles.

---

## 1. Core Principles & Constraints

### 1.1 Reality Check About Claude Code Subagents

Any LLM reading this must **not assume** marketing claims like:
- "Just make multiple Task calls in one response and they run in parallel"
- "Use `<invoke>` XML and `subagent_type` for parallelism"

These are **incorrect for Claude Code** as of early 2026.

**Ground truth:**
- Claude Code **subagents** are defined via markdown files under a directory like `.claude/agents/`.
- Subagents are **invoked via natural language**, not custom XML.
- The internal tool calls (e.g. `Task`, `Read`, `Write`, `Bash`) are **sequential** within a given conversation.
- True parallelism is achieved only by **running multiple Claude Code sessions in parallel** (e.g., multiple terminals / panes / VS Code instances) operating on the same repository.

### 1.2 Architectural Strategy

We will architect a system that:
1. Uses a **central orchestration file** (e.g. `.claude/ORCHESTRATION.md`) as the shared state.
2. Uses **multiple dedicated roles/agents** (Test Writer, Implementer, Reviewer, etc.).
3. Allows `/cwo` to:
   - Parse high-level requests
   - Break them into **parallelizable subtasks**
   - Write these tasks into the orchestration file
4. Allows `/exec` to:
   - Generate concrete **launch instructions** for parallel agents
   - Emphasize running them in **multiple terminals** for genuine parallel work
5. Avoids any fake constructs (`<invoke>`, `subagent_type`, "parallel Task" fiction).

### 1.3 Design Goals

- **Portable**: Can be used in Claude Code, Roo Code, or any other tool that can:
  - Read/write markdown files
  - Run multiple sessions against the same filesystem
- **LLM-friendly**: All behaviors driven by **prompts + simple file conventions**, no deep custom plugins required.
- **Observable**: State of all subtasks is visible in one place: `.claude/ORCHESTRATION.md`.
- **Recoverable**: If a session crashes, another agent can read ORCHESTRATION.md and pick up.
- **Failure-aware**: Explicit failure modes prevent cascading waits and resource stalls.

---

## 2. High-Level Architecture

### 2.1 Components

1. **/cwo (Cognitive Workflow Orchestrator)**
   - A top-level system/prompt used in one Claude session.
   - Given a user request (e.g. "Implement feature X"), it:
     - Decomposes into subtasks
     - Classifies which can run in parallel vs which are dependent
     - Writes/updates `.claude/ORCHESTRATION.md`
     - Outputs recommended commands/prompts for parallel agents.

2. **/exec (Executor)**
   - Focused on turning a **specific request** into an **executable plan**.
   - Uses the orchestration state created by `/cwo`.
   - Emits:
     - Explicit instructions like:
       - "Open a new terminal and run: `claude "<prompt>"`"
       - "Start Agent: Test-Writer"
     - Guidance about ordering, dependencies, and failure handling.

3. **Subagent Roles** (implemented by separate LLM sessions)
   - **Architect / Planner** – designs changes & high-level structure.
   - **Test Writer (TDD)** – writes/maintains tests.
   - **Implementer / Dev** – modifies codebases.
   - **Reviewer** – reviews code for quality & security.
   - **Ops / Docs** – updates docs, migration notes, etc.

   Each role is:
   - Defined by a **prompt template**.
   - Also by a `.claude/agents/<name>.md` descriptor (auto-discovered by Claude Code).

4. **Orchestration File** – `.claude/ORCHESTRATION.md`
   - A human & LLM-readable **task board**.
   - Single source of truth for:
     - What tasks exist
     - Which agent owns them
     - Status: TODO / IN_PROGRESS / FAILED / DONE
     - Dependencies between tasks
     - Failure reasons and blocked downstream tasks

### 2.2 Parallelism Model

- A **single** Claude Code session is **sequential**.
- **Parallelism** is achieved by running **multiple sessions** (terminals / panes) simultaneously.
- All sessions **share the same working directory** so they see the same `.claude/ORCHESTRATION.md` and repository.

The design therefore focuses on:
- Making it trivial for `/exec` to output **copy-pasteable shell commands** to spawn these parallel sessions.
- Making it trivial for each session to know **what to do** and **when** via the orchestration file.
- Making it trivial for agents to signal **failure, not just success**.

---

## 3. Orchestration File Design (`.claude/ORCHESTRATION.md`)

### 3.1 File Purpose

Central coordination mechanism for all agents.

**Responsibilities:**
- Task definition
- Ownership
- Status tracking
- Dependencies
- High-level notes/decisions
- Failure signaling

### 3.2 File Location & Lifetime

- File path: `./.claude/ORCHESTRATION.md`
- Checked into git? **Optional**. Usually **yes** during long-lived efforts (multi-day/multi-branch work).
- Created and maintained primarily by `/cwo` and updated by all agents.

### 3.3 Recommended Structure

Example initial template for the file:

```markdown
# Orchestration Board

## Overview
- Epic: Implement XYZ feature
- Created by: /cwo
- Last updated: 2026-01-05T15:10:00Z

## Task Legend
- Status values: TODO | IN_PROGRESS | FAILED | DONE

## Tasks

### [T-001] Write Auth Tests
- Status: TODO
- Owner: Test-Writer
- Depends on: (none)
- Blocked by: (none)
- Description: Write failing tests covering login, logout, password reset, lockout.
- Notes:

### [T-002] Implement Auth Logic
- Status: BLOCKED
- Owner: Implementer
- Depends on: T-001
- Blocked by: (none)
- Description: Implement auth flows to satisfy tests.
- Notes:

### [T-003] Security Review
- Status: BLOCKED
- Owner: Reviewer
- Depends on: T-002
- Blocked by: (none)
- Description: Review for OWASP Top 10 issues, auth hardening.
- Notes:

## Global Notes / Decisions
- TBD
```

### 3.4 Update Rules for Agents

Any LLM agent editing this file should follow these rules:

1. **Never remove tasks** unless explicitly told to.
2. **Only modify:**
   - `Status`
   - `Notes`
   - `Blocked by` (if your task fails and blocks downstream)
   - `Last updated` (update at file level)
3. **Preserve IDs (`[T-00X]`)** to avoid confusion.
4. When starting a task, change `Status: TODO` → `IN_PROGRESS`.
5. When blocked on a dependency, set `Status: BLOCKED` and explain in `Notes`.
6. **When your task fails**, set `Status: FAILED`, document the error in `Notes`, and **update downstream tasks' `Blocked by` field** to alert dependent agents.
7. When finished successfully, set `Status: DONE` and summarize outcomes in `Notes`.

This should be made explicit in the system prompts for all subagents.

### 3.5 File Contention & Synchronization

**Multi-Agent File Access:**

When multiple agents update `ORCHESTRATION.md` simultaneously, conflicts can occur. This design employs a **simple, LLM-friendly approach**:

#### Strategy: Lightweight Locking Convention

Add an optional `## Lock` section to signal who is currently modifying the file:

```markdown
## Lock
- Held by: Test-Writer
- Since: 2026-01-05T15:10:00Z
- Purpose: Updating [T-001] Status and Notes
```

**Agent behavior:**

1. Before editing the file, check if a lock exists.
2. If yes **and recent** (< 2 minutes old), **wait 10-30 seconds and retry** (exponential backoff).
3. If no lock, **add a lock with current timestamp**, make edits, **remove the lock**.
4. If you encounter a **stale lock** (> 2 minutes old), you may overwrite it with your own.
   - This guards against crashed agents that forgot to release their locks.

**Best Practice: Simple Status Updates (<30 seconds)**

For quick status updates (changing TODO→IN_PROGRESS, adding brief notes), aim to complete the entire edit cycle in **under 30 seconds**:
- Add lock
- Make minimal changes
- Remove lock

This minimizes contention and reduces retry attempts by other agents.

**Rationale:**
- No central server required.
- Works with git (lock is a comment, not a data field).
- LLMs understand the convention easily.
- Simple enough that agents don't need a specialized library.
- **2-minute timeout** balances responsiveness (for quick tasks) with safety (avoiding false positives).

#### Alternative: Git Conflict Resolution

If you prefer a more robust approach (e.g., for high-frequency updates):
- Agents commit their changes to git after each task update.
- Use git's built-in merge/conflict resolution.
- Re-read the file after a commit to ensure consistency.

**Recommendation:** Start with the lightweight locking convention. If you find contention is a real problem in practice, upgrade to git-based versioning.

### 3.6 Heartbeat Format (for detecting crashed agents)

**Purpose:** Detect when an agent has crashed while a task is IN_PROGRESS, so another agent can pick up the work.

**Format (Reader-Calculated Age):**

```markdown
### [T-001] Write Auth Tests
- Status: IN_PROGRESS
- Owner: Test-Writer
- Last heartbeat: 2026-01-05T15:10:30Z
```

**How it works:**

1. **Writer (Agent)**: Updates `Last heartbeat` with current timestamp whenever working on the task (e.g., every few minutes).
2. **Reader (Other agents / /cwo)**: Calculates `Age = current_time - Last heartbeat` and interprets:
   - Age < 5 minutes → Agent is alive and working
   - Age 5-10 minutes → Agent may be idle or stuck; check status
   - Age > 10 minutes → Agent likely crashed; reassign task

**Why Reader-Calculated Age is Optimal:**

| Approach | Pros | Cons |
|----------|------|------|
| **Writer-calculated** (file shows "Age: ~2 min") | Reader sees age immediately | - Writer must calculate age<br>- Requires derived data in file<br>- Different agents may need different timeout thresholds<br>- Timestamp can drift |
| **Reader-calculated** (file shows timestamp only) | - Single source of truth (raw timestamp)<br>- Flexible (different agents can apply different timeout thresholds)<br>- No derived data in file<br>- Simpler writer logic | - Reader must calculate age (trivial for LLMs) |

**Best Practice:** Use reader-calculated age. The writer stores only the raw ISO timestamp. Each reader applies its own timeout logic based on the use case.

**Example Reader Logic:**

```python
# An agent checking if T-001 is stalled
heartbeat = "2026-01-05T15:10:30Z"  # Read from file
current_time = "2026-01-05T15:20:00Z"  # Current time
age_minutes = (current_time - heartbeat).total_seconds() / 60  # ~10 minutes

if age_minutes > 10:
    # Agent likely crashed; consider reassigning
    mark_task_stale("T-001", reason="No heartbeat for ~10 minutes")
```

---

## 4. CLI Syntax & Invocation

### 4.1 Claude Code CLI Format

The examples in this spec assume the **simplest invocation style**:

```bash
claude "Your prompt here"
```

**For verification & portability:**
- Test your specific Claude Code version: `claude --version`
- If `claude "prompt"` doesn't work, check if your CLI requires:
  - `claude --prompt "prompt"` or
  - `echo "prompt" | claude` or
  - Another variant documented in `claude --help`

Update all shell commands in this spec to match your actual CLI once verified.

### 4.2 Recommended Invocation Pattern

For `/cwo` and `/exec`, the cleanest pattern is:

```bash
# Simple one-liner (preferred)
claude "You are /cwo. User request: Implement feature X. Create ORCHESTRATION.md and output launch instructions."

# Or, if your CLI requires flags:
claude --prompt "You are /cwo. User request: Implement feature X. Create ORCHESTRATION.md and output launch instructions."

# Or, from a file (for longer prompts):
cat /tmp/cwo_prompt.txt | claude
```

Agents should use whichever works on your platform (Windows 11 PowerShell, bash, etc.).

### 4.3 Windows 11 PowerShell Specifics

On Windows 11 with PowerShell, quote escaping can be tricky. **Recommended patterns:**

**Simple prompts (one-liners):**
```powershell
claude "You are /cwo. Create ORCHESTRATION.md..."
```

**Complex prompts with nested quotes:**
```powershell
# Avoid this (error-prone):
# claude "You said: `"Implement feature X`"..."

# Use here-strings instead (recommended):
$prompt = @"
You are /cwo.
Analyze the user request: Implement user authentication
Create ORCHESTRATION.md and output launch instructions.
"@
claude $prompt
```

**With dynamic variables:**
```powershell
$userRequest = "Implement user authentication"
$epic = "Auth System v2"

$prompt = @"
You are /cwo.
Epic: $epic
User request: $userRequest
Create ORCHESTRATION.md and output launch instructions.
"@
claude $prompt
```

Test this in your environment before rolling out to agents.

---

## 5. /cwo Design (Cognitive Workflow Orchestrator)

### 5.1 Role Summary

`/cwo` converts a **high-level user request** into:
- A structured set of tasks appropriate for multiple agents.
- An `ORCHESTRATION.md` snapshot.
- Instructions for `/exec` and for human/automation about how to launch these in parallel.

### 5.2 Recommended System Prompt for /cwo

Below is a prompt template another LLM can adopt directly:

```text
You are /cwo – the Cognitive Workflow Orchestrator for a multi-agent Claude Code environment.

Your goals:
1. Analyze the user request.
2. Decompose it into well-scoped tasks that can be worked on by specialized agents
   (e.g. Planner, Test-Writer, Implementer, Reviewer, Docs).
3. Identify which tasks can run in parallel vs which have dependencies.
4. Create or update the file `.claude/ORCHESTRATION.md` as the single source of truth.
5. Output:
   - A summary of the task graph
   - Concrete launch instructions that /exec or a human can use to start parallel agents.

Constraints and truths about Claude Code:
- A single Claude Code session is sequential, not parallel.
- True parallelism happens when multiple sessions/terminals run simultaneously on the same repo.
- Do NOT invent XML, `<invoke>`, `subagent_type`, or "parallel Task" semantics.
- Subagents are invoked via natural language and/or `.claude/agents/*.md` definitions.
- File contention is handled via lightweight Lock mechanism (2-minute timeout).

When editing `.claude/ORCHESTRATION.md`:
- Follow the existing structure if it exists.
- Preserve task IDs and existing content except where updating Status/Notes/Blocked by/Last updated.
- Use Status values: TODO, IN_PROGRESS, FAILED, DONE.
- Use the Lock mechanism to minimize contention during writes.
- For heartbeats, write raw timestamp; let readers calculate age.
- If a task is marked FAILED, update all downstream dependent tasks' "Blocked by" field.

When you respond:
1. Show the **updated ORCHESTRATION.md content**.
2. Show a **Task Graph Summary** (list tasks, owners, dependencies).
3. Show **Launch Instructions** – commands/prompts to run in separate terminals for parallel work.
```

### 5.3 Example /cwo Output Shape

An ideal `/cwo` response (for another LLM to emulate) looks like:

```markdown
## Updated .claude/ORCHESTRATION.md
```markdown
# Orchestration Board

## Overview
- Epic: Implement user authentication system
- Created by: /cwo
- Last updated: 2026-01-05T15:10:00Z

## Task Legend
- Status values: TODO | IN_PROGRESS | FAILED | DONE

## Tasks

### [T-001] Write Auth Tests
- Status: TODO
- Owner: Test-Writer
- Depends on: (none)
- Blocked by: (none)
- Description: Write failing tests for login, logout, password reset, lockout.
- Notes:

### [T-002] Implement Auth Logic
- Status: BLOCKED
- Owner: Implementer
- Depends on: T-001
- Blocked by: (none)
- Description: Implement auth flows to satisfy tests.
- Notes:

### [T-003] Security Review
- Status: BLOCKED
- Owner: Reviewer
- Depends on: T-002
- Blocked by: (none)
- Description: Review auth implementation for security issues.
- Notes:

## Global Notes / Decisions
- Auth will use JWT + refresh tokens.
```

```markdown
## Task Graph Summary
- T-001 (Test-Writer): No dependencies – can start immediately.
- T-002 (Implementer): Depends on T-001 being DONE.
- T-003 (Reviewer): Depends on T-002 being DONE.

### Parallelizable now:
- T-001 can start immediately.
```

```bash
## Launch Instructions (Run in separate terminals)

# Terminal A – Orchestrator (optional, for monitoring only)
claude "You are /cwo Orchestrator. Monitor .claude/ORCHESTRATION.md and help adjust tasks as needed."

# Terminal B – Test Writer (T-001)
claude "You are the Test-Writer agent. Open .claude/ORCHESTRATION.md, locate task [T-001], and execute it.

Rules:
- Set Status to IN_PROGRESS when you start.
- Write failing tests for auth.
- Update heartbeat timestamp every few minutes.
- If you encounter an error, set Status to FAILED and explain in Notes.
- When done successfully, set Status to DONE and summarize in Notes.
"

# Terminal C – Implementer (T-002)
# (Run after T-001 is DONE, or in parallel if you accept waiting)
claude "You are the Implementer agent. Open .claude/ORCHESTRATION.md, locate task [T-002], and execute it.

Rules:
- Only start once T-001 is DONE.
- If T-001 shows FAILED, check 'Blocked by' field and decide to abort or retry.
- Implement code to satisfy tests.
- When done, set Status to DONE and summarize in Notes.
"

# Terminal D – Reviewer (T-003)
claude "You are the Reviewer agent. After [T-002] is DONE, review changes for security and quality, then update T-003."
```

This structure is what another LLM should aim to output.

---

## 6. /exec Design (Execution-Focused Agent)

### 6.1 Role Summary

`/exec` takes a **concrete execution request** (e.g. "implement feature X now") and:
- Reads the current `.claude/ORCHESTRATION.md`.
- Decides which tasks should be launched now and in parallel.
- Emits **very explicit instructions** for launching parallel agents, including **failure handling**.
- Optionally acts as one of the agents itself in the current session.

### 6.2 Recommended System Prompt for /exec

```text
You are /exec – the Execution Orchestrator.

Your responsibilities:
1. Read and interpret `.claude/ORCHESTRATION.md` if it exists.
2. For the current user request, determine which tasks should be:
   - Started now
   - Started later (blocked by dependencies)
3. Generate a concrete execution plan focusing on **parallelism and failure handling**.
4. Output:
   - A short plan
   - Copy-pasteable shell commands for parallel Claude Code sessions
   - Role-specific prompt templates for each parallel agent

Facts about the environment:
- True parallel work = multiple terminals or panes, each running its own Claude Code session.
- Do NOT invent XML (<invoke>), subagent_type, or "parallel Task" language.
- You are not responsible for low-level OS automation; just output commands and prompts.
- Agents must be aware of failure modes: upstream FAILED means dependent tasks are "stuck, not waiting".

When responding:
1. Show a concise **Execution Plan**, including failure scenarios.
2. Show **Launch Commands** as shell snippets (verify against section 4.1 for CLI syntax).
3. Show **Role Prompts** that each parallel agent should use, including failure handling instructions.
```

### 6.3 Status Polling & Dependency Handling

Dependent agents (e.g., Implementer waiting on Test-Writer) need a way to detect when upstream tasks are complete **or have failed**.

**Recommended approach: Simple polling with explicit failure detection**

```markdown
## Polling Instructions for Dependent Agents

When you are BLOCKED on upstream tasks:

1. **Check interval:** Poll `.claude/ORCHESTRATION.md` every **30-60 seconds**.
2. **Backoff:** If the dependency is still incomplete, wait longer (exponential backoff: 30s → 60s → 120s).
3. **Detect completion:** When your dependency shows `Status: DONE`, proceed to `IN_PROGRESS`.
4. **Detect failure:** When your dependency shows `Status: FAILED`:
   - Check the `Notes` field for the failure reason.
   - Check if your task is mentioned in the `Blocked by` field.
   - **Decision:** Either abort your task gracefully, retry the upstream task, or escalate to `/cwo`.
5. **Log your actions:** Optionally add a note like "Polled at 15:12:05Z - T-001 still TODO" or "Detected T-001 FAILED: test framework error" to track polling activity.

Example (as Implementer waiting on Test-Writer):
- 15:10:00Z: Detect T-001 is TODO. Start 30s polling.
- 15:10:30Z: Check again. Still TODO. Extend to 60s.
- 15:11:30Z: Check again. T-001 is DONE! Begin implementation.
- **Alternative scenario:**
- 15:11:30Z: Check again. T-001 is FAILED: "Test framework not found". Abort my task and alert /cwo.
```

**Rationale:**
- Simple for LLMs to understand and implement.
- No filesystem watchers or complex async required.
- Adds minimal overhead (file read every 30-60s).
- Works across platforms (Windows, Linux, macOS).
- Prevents infinite waiting if upstream fails.

**Alternative: Filesystem Watcher (Advanced)**

If you want lower latency:
```bash
# Example using 'watch' (Linux/macOS)
watch -n 5 "grep -A 2 '\[T-001\]' .claude/ORCHESTRATION.md"
```

However, this requires environment-specific tools and is harder to generalize. **Start with polling.**

### 6.4 Example /exec Output Shape

```markdown
## Execution Plan

- Start Test-Writer for [T-001] in parallel.
- Once [T-001] is DONE, start Implementer for [T-002].
- If [T-001] FAILS, mark [T-002] and [T-003] as "Blocked by T-001 failure".
- Once [T-002] is DONE, start Reviewer for [T-003].

Initially parallelizable:
- Only [T-001], but we can still start multiple agents if we accept waiting/blocked behavior.

Failure scenarios:
- If Test-Writer fails to find a test framework, downstream tasks will stall. /cwo should be notified.
```

```bash
## Launch Commands (copy-paste into separate terminals)

# Terminal B – Test Writer
claude "You are the Test-Writer agent working on task [T-001] from .claude/ORCHESTRATION.md.
Follow TDD best practices, write failing tests, update the file's Status/Notes as you go.
Update heartbeat every few minutes.
If you encounter an error (missing framework, syntax issues), set Status to FAILED and document in Notes."

# Terminal C – Implementer (can be started now, but will wait logically on T-001)
claude "You are the Implementer agent working on task [T-002] from .claude/ORCHESTRATION.md.
Do not begin coding until T-001 is marked DONE.
Polling instruction: Check .claude/ORCHESTRATION.md every 30-60 seconds.
- If T-001 is DONE, proceed to IN_PROGRESS.
- If T-001 is FAILED, check the error reason, decide to abort or retry, and update your Notes accordingly.
Then implement auth to satisfy the tests."

# Terminal D – Reviewer
claude "You are the Reviewer agent working on task [T-003].
Periodically check .claude/ORCHESTRATION.md every 30-60 seconds.
- If T-002 is FAILED, check 'Blocked by' field and update your Notes.
- Once T-002 is DONE, review the work for security and quality issues."
```

```markdown
## Role Prompt Templates

### Test-Writer Role
"""
You are the Test-Writer agent in a multi-agent environment.

Instructions:
- Open `.claude/ORCHESTRATION.md`.
- Locate the task assigned to you (e.g., [T-001]).
- Set its Status to IN_PROGRESS.
- Write or update tests in the repo to satisfy the Description.
- When you need to modify code, do it via best-practice edits.
- **Failure handling:** If you encounter an error:
  - Set Status to FAILED
  - Document the error reason in Notes (e.g., "test framework not found")
  - Do NOT set it back to TODO
  - Downstream agents will detect the FAILED status and act accordingly
- When done successfully, set Status to DONE and summarize in Notes.
"""

### Implementer Role
"""
You are the Implementer agent in a multi-agent environment.

Instructions:
- Open `.claude/ORCHESTRATION.md`.
- Locate the task assigned to you (e.g., [T-002]).
- Poll the file every 30-60 seconds until dependencies are resolved:
  - If dependency shows Status DONE, proceed to IN_PROGRESS.
  - If dependency shows Status FAILED, check the error in Notes. Decide to:
    a) Abort your task and mark it BLOCKED with reason "Upstream T-001 failed: [reason]"
    b) Retry or work around the failure if possible
    c) Escalate to /cwo for guidance
- Implement the required changes.
- Keep updates incremental and well-documented.
- **Failure handling:** If you encounter an error:
  - Set Status to FAILED
  - Document the error reason in Notes
  - Update your downstream tasks' "Blocked by" field if applicable
- When done successfully, set Status to DONE and summarize in Notes.
"""

### Reviewer Role
"""
You are the Reviewer agent in a multi-agent environment.

Instructions:
- Open `.claude/ORCHESTRATION.md`.
- Locate your assigned task (e.g., [T-003]).
- Poll the file every 30-60 seconds for dependency changes:
  - If dependency shows Status DONE, proceed.
  - If dependency shows Status FAILED, check the reason and decide whether to continue or abort.
- Review the changes for security, correctness, maintainability.
- Add findings and decisions to Notes.
- **Failure handling:** If you encounter issues:
  - Set Status to FAILED and document the issues
  - If your review blocks publication, update downstream tasks' "Blocked by" field
- When you're satisfied with the quality, set Status to DONE.
"""
```

---

## 7. Subagent Definition Files (Recommended)

### 7.1 `.claude/agents/*.md` Descriptor Pattern

Claude Code **supports and auto-discovers** `.claude/agents/*.md` subagent definitions. Define files like:

**File: `.claude/agents/test-writer.md`**
```markdown
---
name: test-writer
description: Writes and maintains tests in a TDD style.
model: sonnet
---

You are a Test-Writer specializing in TDD. You:
- Analyze feature descriptions
- Write failing tests first
- Collaborate with Implementer agents via `.claude/ORCHESTRATION.md`
- Update task status as you progress
- Report failures explicitly when tests can't be written
```

**File: `.claude/agents/implementer.md`**
```markdown
---
name: implementer
description: Implements code changes driven by TDD tests.
model: sonnet
---

You are an Implementer agent. You:
- Read tests and feature specs
- Implement the minimal correct code
- Keep code clean and maintainable
- Update `.claude/ORCHESTRATION.md` as you progress
- Poll upstream dependencies before starting work
- Fail gracefully if tests are broken or missing
```

**File: `.claude/agents/reviewer.md`**
```markdown
---
name: reviewer
description: Reviews code for security, correctness, and maintainability.
model: sonnet
---

You are a Reviewer agent. You:
- Review diffs and relevant files
- Check for bugs, security issues, regressions
- Provide actionable feedback
- Finalize by marking tasks DONE when appropriate
- Poll upstream dependencies before starting work
- Escalate blockers if code quality is insufficient
```

### 7.2 Agent Discovery & Invocation

**Claude Code Integration:**

Claude Code **automatically discovers and indexes** these files. You can invoke agents naturally:

```
"Use the test-writer agent to write TDD tests for the auth module."
"Have the implementer build the feature based on [T-002]."
"Ask the reviewer to check my changes."
```

Claude Code will:
1. Recognize the agent by name.
2. Load the descriptor (name, description, model).
3. Execute the agent with the specified prompt.

**For CLI-only or non-Claude Code environments:**
- Agents are invoked purely via prompt engineering using `/exec` role prompts (section 6.4).
- The `.claude/agents/*.md` files still serve as documentation and reference.

**Best practice:**
- Always maintain `.claude/agents/*.md` files as the source of truth for agent definitions.
- Use them in Claude Code for natural language invocation.
- Reference them in CLI workflows for consistency.
- This keeps both workflows aligned and documented.

---

## 8. Implementation Checklist for Another LLM

When a downstream LLM receives this document and needs to implement the system, it should:

1. **Verify CLI syntax** (section 4.1):
   - Run `claude --help` and confirm the invocation format.
   - Test: `claude "echo hello"` or equivalent.
   - Update all shell commands in this spec to match.

2. **Create the orchestration file support:**
   - Implement logic/prompts to create and maintain `.claude/ORCHESTRATION.md` with the structure in section 3.3.
   - Implement the lightweight Lock mechanism (section 3.5) with **2-minute timeout**.
   - Implement heartbeat with **reader-calculated age** (section 3.6).

3. **Implement /cwo behavior:**
   - Add a `/cwo` command or entry point that:
     - Reads user epic/feature requests
     - Decomposes into tasks
     - Writes/updates `.claude/ORCHESTRATION.md`
     - Outputs task graph + launch instructions (section 5.3)

4. **Implement /exec behavior:**
   - Add a `/exec` command or entry point that:
     - Reads `.claude/ORCHESTRATION.md`
     - Determines what can run now/parallel
     - **Identifies failure scenarios** and blocked downstream tasks
     - Emits concrete terminal commands and role prompts for each parallel agent (section 6.4)
     - Recommends polling intervals for dependent agents (section 6.3)

5. **Define role prompts and agent descriptors:**
   - Create stable prompts for Test-Writer, Implementer, Reviewer, etc. (section 6.4 & 7.1)
   - Maintain `.claude/agents/*.md` files as the source of truth.
   - Include **explicit failure handling** instructions in all role prompts.

6. **Implement failure handling:**
   - Agents must set Status to FAILED (not just TODO or BLOCKED) on errors.
   - Dependent agents must detect FAILED status and respond appropriately.
   - Add "Blocked by" field to task template for tracking failure propagation.

7. **Respect constraints:**
   - Never claim single-session parallelism.
   - Never invent XML or fake task APIs.
   - Assume parallelism = multiple OS processes / terminals.

8. **Provide examples and templates:**
   - Generate example `/cwo` and `/exec` runs for typical scenarios (new feature, refactor, bug triage).
   - Create a simple test case (e.g., "Implement a simple calculator with tests, implementation, review").
   - Show failure scenarios (e.g., "What happens if Test-Writer can't find pytest?").

9. **Test on target platform (Windows 11 + Claude Code):**
   - Verify all shell commands work in PowerShell.
   - Test multi-terminal launch with actual agent role-playing.
   - Verify ORCHESTRATION.md reads/writes and Lock mechanism in practice.
   - **Test failure scenarios** to ensure dependent agents handle FAILED status correctly.

---

## 9. How to Use This with Another LLM

To use this document with another LLM (Claude, Roo, OpenAI, etc.):

1. Paste or upload this `.md` file as a reference.
2. Say something like:

> "You are going to implement the multi-agent orchestration pattern described in this spec. Start by:
> 1) Verifying the CLI invocation format (section 4.1) for your environment,
> 2) Creating `.claude/ORCHESTRATION.md` support with FAILED status,
> 3) Defining the /cwo and /exec prompts/commands with failure handling,
> 4) Providing example launch instructions for parallel agents.
> 5) Implementing the polling strategy (section 6.3) with explicit failure detection.
> 6) Using reader-calculated heartbeat age (section 3.6)."

3. Then iterate:
   - Ask it to generate `/cwo` and `/exec` prompt files.
   - Ask it to simulate a run for a toy feature (e.g., "simple calculator").
   - **Ask it to simulate a failure scenario** (e.g., "Test-Writer fails to find pytest").
   - Test in actual terminals on your platform.
   - Refine as needed.

---

## 10. Answers to Common Implementation Questions

### Q1: Claude Code CLI Syntax – Is it `claude "..."` or `claude --prompt "..."`?

**Answer:**
Check your specific version: `claude --version`

The **simplest common form** is:
```bash
claude "Your prompt here"
```

If that doesn't work, test:
```bash
claude --prompt "Your prompt here"
echo "Your prompt" | claude
```

Once you confirm which works, **update section 4.1 with the verified syntax** and ensure all agents use it consistently.

### Q2: File Contention – What if two agents try to update ORCHESTRATION.md at the same time?

**Answer:**
Use the **lightweight Lock mechanism** (section 3.5):

1. Agent checks for a Lock section.
2. If present and < 2 minutes old, wait and retry.
3. If absent or > 2 minutes old (stale), agent adds Lock, makes edits, removes Lock.

The **2-minute timeout** balances:
- **Responsiveness:** For quick tasks (most edits take <30 seconds), a 2-minute window is safe.
- **Safety:** Prevents false positives for slightly longer tasks.

**Best practice:** Aim to complete simple status updates in <30 seconds to minimize contention.

If you find contention is a real problem, upgrade to git-based versioning (each agent commits its changes).

### Q3: Agent Discovery – How do `.claude/agents/*.md` files work with Claude Code?

**Answer:**
Claude Code **automatically discovers and indexes** these files. You can invoke agents naturally:
- "Use the test-writer agent"
- "Have the implementer build this"
- Agents are invoked by name from the descriptor frontmatter

For non-Claude Code environments (CLI-only), agents are invoked via prompt engineering (section 6.4). The `.claude/agents/*.md` files still document agent definitions.

### Q4: Status Polling – Should agents use a filesystem watcher or simple polling?

**Answer:**
**Start with simple polling** (section 6.3):
- Every 30-60 seconds, agent reads ORCHESTRATION.md and checks dependencies.
- If dependency is DONE, proceed; if FAILED, handle gracefully; otherwise, wait.
- Simple, platform-agnostic, LLM-friendly.

**Advanced:** If you need lower latency, use environment-specific tools (e.g., `watch` on Linux). But this adds complexity.

### Q5: What if an agent crashes mid-task?

**Answer:**
The system is **fault-tolerant by design**:

1. The crashed agent's task will remain `IN_PROGRESS`.
2. Use **heartbeat monitoring** (section 3.6) to detect stale tasks:
   - Check `Last heartbeat` timestamp
   - Calculate age: if >10 minutes old, agent likely crashed
3. Another agent (or a human operator) can read ORCHESTRATION.md, see the stale task, and:
   - Decide to continue the work in a new session.
   - Rollback the task to `TODO` if the previous work is discarded.

**Example heartbeat check:**
```python
heartbeat = "2026-01-05T15:10:30Z"  # From file
current = "2026-01-05T15:25:00Z"    # Now
age = (current - heartbeat).total_seconds() / 60  # ~15 minutes

if age > 10:
    # Task is stale; reassign
    mark_task_stale("T-001")
```

### Q6: Can multiple /cwo instances run in parallel?

**Answer:**
**No, not recommended.** Only one `/cwo` should be active at a time (it owns the ORCHESTRATION.md file).

However:
- **Multiple /exec instances** are fine (they read ORCHESTRATION.md and spawn agents).
- **Multiple agent role instances** (Test-Writer, Implementer, etc.) run in parallel.

If you need concurrent planning, use a **branching strategy**:
- Each /cwo creates a separate `.claude/ORCHESTRATION_<branch>.md`.
- Merge them back together manually or via git.

### Q7: How do I avoid tasks being decomposed so finely that coordination overhead dominates?

**Answer:**
Task decomposition is an art, not a science. Guidelines:

- **Minimum task size:** >10 minutes of work (overhead is ~2-5 minutes for coordination/polling).
- **Maximum task size:** <2 hours (avoids long locks, enables parallel progress).
- **Dependency depth:** Ideally ≤4 levels (T-001 → T-002 → T-003 → T-004).
- **True parallelism:** Tasks at the same dependency level should outnumber the dependent chain.

Example (good decomposition for "Auth System"):
- **L1 (parallel):** T-001 (tests), T-002 (docs)
- **L2 (parallel):** T-003 (implementation), T-004 (database schema)
- **L3:** T-005 (integration tests)
- **L4:** T-006 (security review)

This gives 2-4 parallel opportunities at each level, amortizing coordination cost.

**If lock timeout is hitting 30 minutes:**
- Your tasks are too coarse (one agent monopolizing the file).
- Break the next task into smaller chunks.
- Or, switch to git-based conflict resolution for high-frequency updates.

### Q8: Heartbeat Parsing – Writer-calculated vs Reader-calculated?

**Answer:**
**Reader-calculated age is optimal** (section 3.6).

**Why:**
- **Single source of truth:** File contains only raw timestamp (no derived data)
- **Flexibility:** Different agents can apply different timeout thresholds (5 min, 10 min, etc.)
- **Simpler:** Writer just stores `Last heartbeat: <timestamp>`; reader calculates age
- **No drift:** Timestamp is immutable; age calculation is always fresh

**Format:**
```markdown
- Last heartbeat: 2026-01-05T15:10:30Z
```

Reader logic:
```python
age_seconds = (now - heartbeat).total_seconds()
if age_seconds > 600:  # 10 minutes
    # Task is stale
```

### Q9: Lock Timeout – What if I need longer locks for complex edits?

**Answer:**
The **2-minute lock timeout** is a balance:
- Short enough to detect crashed agents
- Long enough for most ORCHESTRATION.md updates

**Best practice:**
- Simple status updates (TODO→IN_PROGRESS): Aim for **<30 seconds**
- Complex edits (adding tasks, restructuring): Accept up to 2 minutes

**If you consistently hit timeout:**
- Your updates are too complex. Split into smaller edits.
- Or, use git-based versioning instead of locks.

**Remember:** The lock timeout is a **safety mechanism**, not a workflow constraint. If a lock is stale (>2 min), another agent can override it.

---

## 11. Key Takeaways

- **True parallelism with Claude Code-like tools is achieved by multiple concurrent sessions**, not by pretending multiple tool calls in one response are "parallel".
- A **shared markdown orchestration file** is a simple, robust coordination backbone that all agents (and all LLMs) understand.
- `/cwo` = thinking, decomposition, and planning. `/exec` = concrete, parallel-friendly launch instructions.
- **File contention** is handled via lightweight Lock conventions with a **2-minute timeout**.
- **Heartbeats use reader-calculated age** for flexibility and simplicity.
- **Agent coordination** is handled via polling with **explicit failure detection**. Both are LLM-native.
- **Failure handling is explicit:** Agents set Status to FAILED, not just TODO/BLOCKED. Dependent agents detect failures and respond (abort, retry, escalate).
- This document is deliberately implementation-agnostic and LLM-friendly, so any competent model can wire it into your current workflow with minimal friction.

---

## 12. Hello World Example

This section walks through a complete, minimal example to demonstrate the parallel subagent pattern.

### 12.1 The Task

**Build a simple calculator with:**
- `add(a, b)` function that returns sum
- `multiply(a, b)` function that returns product
- Tests for both functions
- Code review for quality

### 12.2 Step 1: Invoke /cwo

```bash
claude "You are /cwo. User request: Implement a simple calculator with add() and multiply() functions, including tests and code review. Create .claude/ORCHESTRATION.md and output launch instructions for parallel agents."
```

### 12.3 ORCHESTRATION.md After /cwo

```markdown
# Orchestration Board

## Overview
- Epic: Simple Calculator Implementation
- Created by: /cwo
- Last updated: 2026-01-05T10:00:00Z

## Task Legend
- Status values: TODO | IN_PROGRESS | FAILED | DONE

## Tasks

### [T-001] Write Calculator Tests
- Status: TODO
- Owner: Test-Writer
- Depends on: (none)
- Blocked by: (none)
- Description: Write failing tests for add() and multiply() functions.
- Notes:

### [T-002] Implement Calculator
- Status: BLOCKED
- Owner: Implementer
- Depends on: T-001
- Blocked by: (none)
- Description: Implement add() and multiply() to satisfy tests.
- Notes:

### [T-003] Code Review
- Status: BLOCKED
- Owner: Reviewer
- Depends on: T-002
- Blocked by: (none)
- Description: Review calculator implementation for correctness and style.
- Notes:

## Global Notes / Decisions
- Store in calculator.py at project root.
- Use pytest for testing.
```

### 12.4 Launch Commands

/cwo outputs these commands to run in separate terminals:

```bash
# Terminal B – Test Writer
claude "You are the Test-Writer agent. Open .claude/ORCHESTRATION.md, locate [T-001], and execute it. Write tests for a calculator with add() and multiply()."

# Terminal C – Implementer (start in parallel; will wait for T-001)
claude "You are the Implementer agent. Open .claude/ORCHESTRATION.md, locate [T-002], wait for [T-001] to be DONE, then implement the calculator."

# Terminal D – Reviewer
claude "You are the Reviewer agent. Open .claude/ORCHESTRATION.md, locate [T-003], wait for [T-002] to be DONE, then review the code."
```

### 12.5 Expected Workflow

**Phase 1: Test Writer (Terminal B) works on T-001**

1. Reads ORCHESTRATION.md, sees [T-001] is TODO
2. Sets Status to IN_PROGRESS
3. Creates `test_calculator.py`:
   ```python
   def test_add():
       from calculator import add
       assert add(2, 3) == 5

   def test_multiply():
       from calculator import multiply
       assert multiply(2, 3) == 6
   ```
4. Sets [T-001] Status to DONE

**Phase 2: Implementer (Terminal C) detects T-001 is DONE**

1. Polls ORCHESTRATION.md every 30-60 seconds
2. Detects [T-001] is DONE
3. Sets [T-002] Status to IN_PROGRESS
4. Creates `calculator.py`:
   ```python
   def add(a, b):
       return a + b

   def multiply(a, b):
       return a * b
   ```
5. Runs tests: `pytest test_calculator.py` → passes
6. Sets [T-002] Status to DONE

**Phase 3: Reviewer (Terminal D) detects T-002 is DONE**

1. Polls ORCHESTRATION.md
2. Detects [T-002] is DONE
3. Sets [T-003] Status to IN_PROGRESS
4. Reviews `calculator.py` and `test_calculator.py`
5. Adds finding to Notes: "Code looks good. Simple, clean, well-tested."
6. Sets [T-003] Status to DONE

### 12.6 Final ORCHESTRATION.md State

```markdown
# Orchestration Board

## Overview
- Epic: Simple Calculator Implementation
- Created by: /cwo
- Last updated: 2026-01-05T10:15:00Z

## Task Legend
- Status values: TODO | IN_PROGRESS | FAILED | DONE

## Tasks

### [T-001] Write Calculator Tests
- Status: DONE
- Owner: Test-Writer
- Depends on: (none)
- Blocked by: (none)
- Description: Write failing tests for add() and multiply() functions.
- Notes: Created test_calculator.py with test_add() and test_multiply().

### [T-002] Implement Calculator
- Status: DONE
- Owner: Implementer
- Depends on: T-001
- Blocked by: (none)
- Description: Implement add() and multiply() to satisfy tests.
- Notes: Created calculator.py. Tests pass.

### [T-003] Code Review
- Status: DONE
- Owner: Reviewer
- Depends on: T-002
- Blocked by: (none)
- Description: Review calculator implementation for correctness and style.
- Notes: Code reviewed. Simple, clean, well-tested. Approved.

## Global Notes / Decisions
- Store in calculator.py at project root.
- Use pytest for testing.
```

### 12.7 Expected File Structure

```
project/
├── .claude/
│   └── ORCHESTRATION.md
├── calculator.py
└── test_calculator.py
```

### 12.8 Key Points Demonstrated

1. **Parallel launch:** Three terminals started simultaneously
2. **Dependency handling:** Implementer and Reviewer waited for upstream tasks
3. **Polling:** Dependent agents checked ORCHESTRATION.md periodically
4. **Status progression:** TODO → IN_PROGRESS → DONE
5. **No single-session parallelism:** Each terminal is a separate Claude Code session
6. **Shared state:** ORCHESTRATION.md is the single source of truth

### 12.9 Failure Scenario Example

**If Test Writer (T-001) FAILED:**

```markdown
### [T-001] Write Calculator Tests
- Status: FAILED
- Owner: Test-Writer
- Depends on: (none)
- Blocked by: (none)
- Description: Write failing tests for add() and multiply() functions.
- Notes: pytest not found in environment. Cannot proceed.

### [T-002] Implement Calculator
- Status: BLOCKED
- Owner: Implementer
- Depends on: T-001
- Blocked by: T-001 (pytest not found)
- Description: Implement add() and multiply() to satisfy tests.
- Notes: Waiting for T-001 to be resolved.

### [T-003] Code Review
- Status: BLOCKED
- Owner: Reviewer
- Depends on: T-002
- Blocked by: T-001 (pytest not found)
- Description: Review calculator implementation for correctness and style.
- Notes: Waiting for T-002, which is blocked by T-001 failure.
```

The Implementer and Reviewer agents would:
1. Detect T-001 is FAILED
2. Check their `Blocked by` field
3. Decide to abort or escalate to /cwo
4. Not wait indefinitely for a task that cannot succeed

---

**End of v2.2 Specification**
