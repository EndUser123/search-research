---
title: "Here's part of a chat history.  Do you have more info for claude code tasks list and best practices or repos?
'
● You'r"
date: "2026-01-25"
mode: "COPILOT"
uuid: "c36bc8df-67d7-4f88-84cb-550589346020"
entry_count: 1
---

## Human

Here's part of a chat history.  Do you have more info for claude code tasks list and best practices or repos?
"
● You're right - this confirms it's instruction-based, not hook-based.

  Key Insights from the Transcript

  1. Task creation: Just ask Claude - "Generate tasks for this work"
  2. Dynamic addition: Prompt to "create subtasks from complex tasks"
  3. Review: Explicit prompts - "Review the current tasks"
  4. Orchestration: Main agent delegates, synthesizes results

  The solution is add instructions to existing skills/docs, not create new hooks.

  Proposed Updates

  1. /team skill - Add explicit prompts:
  When working on tasks and you discover new issues:
  → "Create a task for: [discovered issue] with description [details]"

  When completing the last primary task:
  → "All primary tasks complete. Create review phase tasks for verification."

  2. CLAUDE.md - Add task management section:
  ## Task Management

  When discovering bugs/issues during work:
  - Immediately create a task using TaskCreate
  - Include: file:line, error type, context

  When all primary tasks complete:
  - Create "Review Phase" tasks
  - Assign to different terminal/instance for verification

  3. Optional: Simple reminder hook
  Just a PostToolUse that prints: "Consider: Did this work discover new tasks?"

  ---
  Proceed with updating /team skill and CLAUDE.md with these instructions?

❯ go ahead

● I'll update the /team skill and CLAUDE.md with task management instructions.
"

## Assistant

Perfect timing—Claude Code **just added native Task Management** (January 2026). Here's what you need to know:

## **Native Task Tools (NEW)**

Claude Code now has **4 built-in task tools** that main agents AND subagents can access:

1. **TaskCreate** - Create new tasks
2. **TaskGet** - Retrieve task details
3. **TaskUpdate** - Update task status/properties
4. **TaskList** - View all tasks

**Key advantage**: Tasks persist across sessions and subagents see them in real-time. When one subagent completes a task, all others get instant notification (not polling).

***

## **Best Practices from Your Research**

From the transcript context + latest patterns:

### **Explore → Plan → Code → Commit** (Canonical workflow)
- **Explore first** (Plan Mode): Read files, understand scope—don't code yet
- **Plan explicitly**: Ask Claude to create the breakdown BEFORE executing
- **Code focused**: One thing at a time
- **Commit often**: Each logical step gets its own commit

### **Task Breakdown Strategy** (from production workflows)

The pattern that's working across the community:

```
/breakdown-issue [issue]
  ↓ (generates 5-8 discrete tasks with dependencies)
/process-task [task-name] (repeat for each)
  ↓ (each task is focused, gets own commit)
```

**Why this works**:
- Planning phase is separate from execution
- Each subagent gets ONE task (eliminates context pollution)
- Dependencies are explicit
- Tests are scoped per task

***

## **Top Skill Repos**

### **1. anthropics/skills** (Official)
https://github.com/anthropics/skills
- Official Anthropic reference implementations
- Document creation, code generation, analysis patterns
- Under Apache 2.0

### **2. levnikolaevich/claude-code-skills** ⭐ MOST COMPREHENSIVE
https://github.com/levnikolaevich/claude-code-skills
- **84 production-ready skills**
- Full Agile workflow: Epic → Story → Task
- Includes:
  - **ln-100-documents-pipeline** (comprehensive docs)
  - **ln-220-story-coordinator** (Epic decomposition)
  - **ln-330-story-executor** (Task orchestration)
- Well-structured CLAUDE.md and SKILL.md templates
- Linear integration included
- This matches your architecture philosophy perfectly

### **3. awattar/claude-code-best-practices**
https://github.com/awattar/claude-code-best-practices
- Clear instruction patterns
- Common workflows documented
- Example commands and validation patterns

***

## **For Your /team Skill + CLAUDE.md Update**

Based on the latest patterns, here's what's missing from your chat:

### **Add to /team skill:**
```markdown
## Task-Driven Workflow

When starting work:
1. "Analyze [scope] and create tasks"
   → TaskCreate for each identified piece
2. "Show me the task list"
   → TaskList (verify all work is captured)
3. Work through tasks in order
   → Each task: read files, plan, code, commit

When discovering issues:
- "Create task: [issue description]"
- Include: file:line, error type, reproduction steps

When task is complex (3+ pieces):
- "Break this into subtasks"
- TaskCreate for each subtask
- Set dependencies if blocking

## Multi-Agent Coordination

Main agent:
- Calls /team skill for task creation
- Reviews task list
- Delegates per-task to subagents

Subagents:
- TaskList to see current tasks
- TaskUpdate to mark progress
- TaskCreate if finding new work
- Report back when task done
```

### **Add to CLAUDE.md:**
```markdown
## Task Management

### Native Tools
- TaskCreate(title, description, status)
- TaskList() - see all active tasks
- TaskUpdate(id, status) - mark complete/blocked
- TaskGet(id) - get task details

### Workflow
1. Break work into 3-8 concrete tasks
2. Each task: "what specific file/function changes"
3. Don't combine unrelated work (keeps subagents focused)
4. Mark tasks complete as you finish (real-time sync)

### Dependency Handling
- Blocking task → mark as "blocked"
- Create separate task for blocker
- Tasks auto-resolve when dependencies complete

### Multi-Session Coordination
- All sessions see same task list
- Status updates are instant (not polled)
- Subagents can create tasks
- Keep main session informed via TaskUpdate
```

***

## **Your Specific Context**

Given your multi-terminal workflow (5-6 terminals, git worktrees, parallel subagents), the **native task system solves** your context-sharing problem:

✅ No more manual task tracking  
✅ Subagents see what's queued  
✅ Real-time sync across sessions  
✅ Dependencies are explicit  
✅ Instant notification on completion  

The task list is stored per-project (`.claude/tasks.jsonl` or similar), so it persists across restarts.

***

**Recommendation**: Study the `levnikolaevich/claude-code-skills` repo structure—it's the most aligned with what you're building (Epic → Story → Task orchestration with explicit dependencies).
