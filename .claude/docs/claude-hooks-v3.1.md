# Claude Code Hooks Guide

**v3.1 | April 2026 | 2.1.89+ | Reference**

---

## CHANGELOG FROM v2.1.15

| Aspect | v2.1.15 (Jan 2026) | v3.0 (Apr 2026) |
|--------|-------------------|-----------------|
| Hook events | 16 | **27** (+ StopFailure, PermissionDenied, TeammateIdle, TaskCreated, TaskCompleted, InstructionsLoaded, ConfigChange, CwdChanged, FileChanged, WorktreeCreate, WorktreeRemove, Elicitation, ElicitationResult) |
| Hook types | command, prompt | **command, prompt, http, agent** (+ http, agent) |
| Config locations | 5 | **6** (+ skill/agent frontmatter) |
| PreToolUse decisions | deny, ask, allow | **deny, ask, allow, defer** (+ defer, v2.1.89+) |
| Async hooks | not documented | **async field supported** |
| New schema fields | hookSpecificOutput | **continue, stopReason, suppressOutput, systemMessage** |
| New hook phases | — | **Worktree events, Elicitation, ConfigChange, CwdChanged, FileChanged** |
| Section 6.1/6.2 | — | **Skill Frontmatter BPs + Hooks-Skills-Agents Interactions** |
| Sections 13.1, 15.1, 17, 18 | — | **Known Bugs, Pattern Catalog, Daemonization, MCP Integration** |

---

## v3.1 CHANGELOG (Section 6 Update)

| Aspect | v3.0 (Apr 2026) | v3.1 (Apr 2026) |
|--------|----------------|----------------|
| Section 6.1 | — | **Skill Frontmatter Best Practices** (+6 BPs: Tiered Cascade, Self-Verify, once:true, Binary Prompt, Daemon HTTP, Gerund Name) |
| Section 6.2 | Subagent Recursive Enforcement (partial) | **Hooks-Skills-Agents Interactions** (Recursion Guards, Skill-Hook Bundles, Agent Chains, Metrics, CLAUDE.md Synergy, 95-Hook Setups, Recipes, Plugins) |
| Component-scoped | documented | **Strengthened** (gerund naming, once:true, self-verify loop) |
| Plugin hardening | — | **allowManagedHooksOnly:true** documented |

---

## TABLE OF CONTENTS

1. [Core Hook Concepts](#core-hook-concepts)
2. [Hook Lifecycle & Phases](#hook-lifecycle--phases)
3. [Hook Protocol & Schemas](#hook-protocol--schemas)
4. [Matcher Syntax & Patterns](#matcher-syntax--patterns)
5. [State Management Patterns](#state-management-patterns)
6. [Hook Registration & Configuration](#hook-registration--configuration)
6.1 [Skill Frontmatter Best Practices](#skill-frontmatter-best-practices)
6.2 [Hooks-Skills-Agents Interactions](#hooks-skills-agents-interactions)
7. [Configuration Scopes & Locations](#configuration-scopes--locations)
8. [Output Format Specifications](#output-format-specifications)
9. [Exit Code Behavior & Control Flow](#exit-code-behavior--control-flow)
10. [Prompt-Based Hooks](#prompt-based-hooks)
11. [HTTP and Agent Hooks](#http-and-agent-hooks)
12. [Async Hooks](#async-hooks)
13. [Common Failure Modes & Recovery](#common-failure-modes--recovery)
13.1 [Known Bugs, Quirks & Workarounds](#known-bugs-quirks--workarounds-v2189--21116)
14. [Testing & Validation Protocol](#testing--validation-protocol)
15. [Advanced Patterns & Strategies](#advanced-patterns--strategies)
15.1 [Hook Pattern Catalog](#hook-pattern-catalog-index)
16. [Implementation Checklist](#implementation-checklist)
17. [Daemonization & Performance Benchmarks](#daemonization--performance-benchmarks-new)
18. [External Tools & MCP Integration](#external-tools--mcp-integration-new)
19. [Complete Code Examples](#complete-code-examples)
17. [Production Patterns](#production-patterns-v31)
18. [v3.1 Section 6 Update](#v31-section-6-update)

### Quick Navigation by Intent

| I want to... | Go to |
|---|---|
| Block a dangerous tool call | §4 Matcher Syntax → §12 Async Hooks (Ladder of Sophistication) |
| Write a hook script | §6 Hook Registration → §14 Testing |
| Control hook execution order | §11 Execution Model → Router Patterns |
| Understand exit codes | §9 Exit Code Behavior |
| Debug why hook doesn't fire | §13 Failure Modes → §14 Testing |
| Set up per-skill hooks | §6 → Component-Scoped Hooks |
| Block a Stop loop | §13 Failure Mode 9 |
| Add fast non-regex matching | §4 → Non-Regex Exact String Matching |
| Understand async hooks | §12 Async Hooks |
| Configure permission rules | §4 → Permission Rule Syntax with `if` |
| Report a bug or quirk | §13.1 Known Bugs & Quirks |
| Find a pattern by name | §15.1 Pattern Catalog |
| Run hooks at scale | §17 Daemonization & Performance |
| Integrate with Slack/MCP | §18 External Tools & MCP |

---

## CORE HOOK CONCEPTS

Hooks are deterministic automation points firing at lifecycle phases. They provide hard control flow independent of LLM decisions — blocking actions, injecting context, logging activity, enforcing rules.

### Hooks vs. Skills vs. Commands vs. CLAUDE.md

| Component | Type | Execution | Visibility | Use Case |
|-----------|------|-----------|------------|----------|
| **Hooks** | Deterministic | Automatic at phases | Some outputs visible | Enforce rules, validate state, audit |
| **Skills** | LLM-augmented | User-invoked | Full context passed | Reusable expertise, domain knowledge |
| **Commands** | Shortcut | User-invoked | Optional context | Quick actions, automation |
| **CLAUDE.md** | Rules + Context | LLM-read | Visible to Claude | Best practices, guidelines, architecture |

---

## HOOK LIFECYCLE & PHASES

**27 hook events** across session, tool, permission, async/monitoring, worktree, compaction, and elicitation categories:

| Phase | Fires | Can Block | Phase | Fires | Can Block |
|-------|-------|-----------|-------|-------|-----------|
| SessionStart | Session begins/resumes | — | TeammateIdle | Teammate idle | **Yes** |
| SessionEnd | Session terminates | — | TaskCreated | Task created | **Yes** |
| UserPromptSubmit | Prompt submitted | **Yes** | TaskCompleted | Task done | — |
| Stop | Claude tries to stop | **Yes** | InstructionsLoaded | Instructions load | — |
| StopFailure | Stop fails | — | ConfigChange | Config changes | — |
| PreToolUse | Before tool exec | **Yes** | CwdChanged | Cwd changes | — |
| PostToolUse | After tool succeeds | — | FileChanged | File changes | — |
| PostToolUseFailure | Tool fails | — | WorktreeCreate | Worktree created | **Yes** |
| PermissionRequest | Permission dialog | **Yes** | WorktreeRemove | Worktree removed | — |
| PermissionDenied | Permission denied | — | PreCompact | Before compaction | — |
| SubagentStart | Subagent spawns | — | PostCompact | After compaction | — |
| SubagentStop | Subagent finishes | **Yes** | Notification | System notification | — |
| Elicitation | Clarification needed | — | ElicitationResult | Elicitation answered | — |

**Blocking Phases** (can prevent action): UserPromptSubmit, PreToolUse, PermissionRequest, PermissionDenied, Stop, StopFailure, SubagentStop, TeammateIdle, TaskCreated, WorktreeCreate

---

## HOOK PROTOCOL & SCHEMAS

### Hook Input Schema (stdin)

All hooks receive a JSON object via stdin with this structure:

```json
{
  "hook_event_name": "PostToolUse",
  "session_id": "abc123def456",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/Users/dev/project",
  "permission_mode": "default"
}
```

### Common Input Fields (All Phases)

```json
{
  "hook_event_name": "string",
  "session_id": "string",
  "transcript_path": "string",
  "cwd": "string",
  "permission_mode": "default|plan|acceptEdits|dontAsk|bypassPermissions"
}
```

### Phase-Specific Input Fields

#### SessionStart
```json
{
  "hook_event_name": "SessionStart",
  "source": "startup|resume|clear|compact"
}
```

#### UserPromptSubmit
```json
{
  "hook_event_name": "UserPromptSubmit",
  "prompt": "string"
}
```

#### PreToolUse (Bash Example)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm install",
    "description": "Install dependencies",
    "timeout": 120000,
    "run_in_background": false
  },
  "tool_use_id": "toolu_01ABC123..."
}
```

#### PreToolUse (Write Example)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/src/main.py",
    "content": "# File content here"
  }
}
```

#### PreToolUse (Edit Example)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Edit",
  "tool_input": {
    "file_path": "/src/main.py",
    "old_string": "original text",
    "new_string": "replacement text",
    "replace_all": false
  }
}
```

#### PermissionRequest
```json
{
  "hook_event_name": "PermissionRequest",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules"
  }
}
```

#### PermissionDenied
```json
{
  "hook_event_name": "PermissionDenied",
  "tool_name": "Bash",
  "tool_input": {
    "command": "rm -rf node_modules"
  }
}
```

#### PostToolUse
```json
{
  "hook_event_name": "PostToolUse",
  "tool_name": "Write",
  "tool_input": {
    "file_path": "/src/main.py",
    "content": "..."
  },
  "tool_response": {
    "filePath": "/src/main.py",
    "success": true
  }
}
```

#### PostToolUseFailure
```json
{
  "hook_event_name": "PostToolUseFailure",
  "tool_name": "Bash",
  "tool_input": {
    "command": "npm test"
  },
  "error": "Exit code 1: Tests failed"
}
```

#### Stop / SubagentStop
```json
{
  "hook_event_name": "Stop",
  "stop_hook_active": true
}
```

Note: `stop_hook_active` is `true` if Claude is already continuing from a previous Stop hook.

#### StopFailure
```json
{
  "hook_event_name": "StopFailure",
  "stop_hook_active": true,
  "failure_reason": "string"
}
```

#### TeammateIdle
```json
{
  "hook_event_name": "TeammateIdle",
  "teammate_name": "string",
  "idle_duration_ms": 0
}
```

#### TaskCreated
```json
{
  "hook_event_name": "TaskCreated",
  "task_id": "string",
  "task_type": "string"
}
```

#### TaskCompleted
```json
{
  "hook_event_name": "TaskCompleted",
  "task_id": "string",
  "task_type": "string",
  "result": {}
}
```

#### WorktreeCreate
```json
{
  "hook_event_name": "WorktreeCreate",
  "worktree_path": "string",
  "branch": "string"
}
```

#### WorktreeRemove
```json
{
  "hook_event_name": "WorktreeRemove",
  "worktree_path": "string"
}
```

#### PreCompact / PostCompact
```json
{
  "hook_event_name": "PreCompact",
  "trigger": "manual|auto",
  "custom_instructions": "User input from /compact command"
}
```

#### Elicitation
```json
{
  "hook_event_name": "Elicitation",
  "elicitation_id": "string",
  "prompt": "string"
}
```

#### ElicitationResult
```json
{
  "hook_event_name": "ElicitationResult",
  "elicitation_id": "string",
  "answer": "string"
}
```

#### Notification
```json
{
  "hook_event_name": "Notification",
  "message": "Claude needs your permission to use Bash",
  "notification_type": "permission_prompt|idle_prompt|auth_success|elicitation_dialog"
}
```

#### ConfigChange
```json
{
  "hook_event_name": "ConfigChange",
  "config_file": "string",
  "change_type": "added|removed|modified"
}
```

#### CwdChanged
```json
{
  "hook_event_name": "CwdChanged",
  "cwd": "string",
  "previous_cwd": "string"
}
```

#### FileChanged
```json
{
  "hook_event_name": "FileChanged",
  "path": "string",
  "change_type": "created|modified|deleted"
}
```

#### SessionEnd
```json
{
  "hook_event_name": "SessionEnd",
  "reason": "clear|logout|prompt_input_exit|other"
}
```

---

## MATCHER SYNTAX & PATTERNS

### Basic Matching

Matchers are used in PreToolUse, PostToolUse, and PermissionRequest to target specific tools:

| Matcher | Effect | Example |
|---------|--------|---------|
| `Write` | Exact match only | Matches Write tool |
| `Edit\|Write` | Regex OR | Matches Edit or Write |
| `Notebook.*` | Regex pattern | Matches NotebookEdit, NotebookRead |
| `*` or `""` | Match all tools | Universal hook |
| `^Notebook` | Regex start anchor | Matches NotebookEdit, NotebookRead |

### Word-Boundary Matching with `:*`

The `:*` suffix provides word-boundary prefix matching:

| Pattern | Position | Behavior | Example |
|---------|----------|----------|---------|
| `Bash(ls:*)` | End only | Prefix with word boundary | Matches `ls -la`, NOT `lsof` |
| `Bash(ls*)` | Anywhere | Glob, no boundary | Matches `ls -la` AND `lsof` |

### Non-Regex Exact String Matching

If the matcher contains only **letters, digits, underscores, and pipes** (`|`), Claude Code evaluates it as an exact string or `|`-separated list — bypassing the JavaScript regex engine entirely:

```json
{ "matcher": "Bash" }        // Exact match only
{ "matcher": "Edit|Write" }  // Exact match of Edit OR Write
{ "matcher": "*" }           // Match all (catch-all)
{ "matcher": "" }            // Match all (catch-all)
```

This is significantly faster than regex evaluation for simple tool-name matching.

### Permission Rule Syntax with `if`

The `if` field provides subcommand-level matching:

```json
{
  "matcher": "Bash",
  "hooks": [
    {
      "type": "command",
      "command": "./audit-git.sh",
      "if": "Bash(git *)"
    }
  ]
}
```

Matches `Bash` when the command starts with `git`.

#### `if` Field Performance: Process Avoidance

The `if` field is evaluated **inside the Claude Code engine before any hook process is spawned**. This eliminates `T_spawn` from the latency equation:

```
Hook latency L = T_spawn + T_parse + T_logic + T_IO
                 ↑
          Eliminated when if condition is false
```

**Practical impact**: If `if: "Bash(git *)"` returns false, the hook process is never created — `T_spawn ≈ 0` for all non-matching commands. For high-frequency `PreToolUse` hooks, this prevents hook overhead on every unrelated tool call.

### MCP Tool Naming

MCP tools follow the pattern: `mcp__<server>__<tool>`

```json
{
  "matcher": "mcp__memory__.*",
  "hooks": [...]
}
```

Examples:
- `mcp__memory__.*` - All memory server tools
- `mcp__.*__write.*` - All write operations across MCP servers
- `mcp__github__create_issue` - Specific MCP tool

### Matcher Configuration Examples

```json
{
  "PreToolUse": [
    {
      "matcher": "Bash",
      "hooks": [{ "type": "command", "command": "./validate_bash.py" }]
    },
    {
      "matcher": "Edit|Write",
      "hooks": [{ "type": "command", "command": "./validate_edits.py" }]
    },
    {
      "matcher": "mcp__.*",
      "hooks": [{ "type": "command", "command": "./audit_mcp.py" }]
    }
  ]
}
```

### Common Tool Names for Matchers

**Core Tools:**
- `Bash` - Shell commands
- `Read` - File reading
- `Write` - File creation
- `Edit` - File modification
- `Glob` - Pattern matching
- `Grep` - Content search
- `WebFetch` - URL fetching
- `WebSearch` - Web searching
- `Task` - Subagent execution
- `Skill` - Skill invocation
- `NotebookEdit` - Jupyter notebook modification
- `NotebookRead` - Jupyter notebook reading
- `TodoWrite` - Task list creation
- `AskUserQuestion` - User interaction

---

## STATE MANAGEMENT PATTERNS

### Why File-Based State?

Hooks are **stateless processes**. Each hook execution is independent. To coordinate across phases, use files:

```
Phase 1 (PreToolUse)
    |
Write validation result to .state/phase1.json
    |
Phase 2 (PostToolUse)
    |
Read phase1.json, make decision
    |
Clear state file
```

### State Directory Structure

```
.claude/
  hooks/
    .state/
      validation.json      # Cross-phase communication
      context.json         # Shared context
      audit.json          # Activity log
    user_prompt_submit.py
    pre_tool_use.py
    post_tool_use.py
    logs/
      hook_execution.log
      errors.log
```

### Pattern: PreToolUse -> PostToolUse Coordination

**Scenario**: You want to validate a file write, let it complete, then verify it in PostToolUse.

```python
# pre_tool_use.py
import json
import sys

hook_input = json.loads(sys.stdin.read())
tool_name = hook_input.get("tool_name")

if tool_name == "Write":
    # Mark that we're watching this
    tool_input = hook_input.get("tool_input", {})
    with open(".claude/hooks/.state/write_tracking.json", "w") as f:
        json.dump({
            "tracked_write": True,
            "file": tool_input.get("file_path")
        }, f)

sys.exit(0)
```

```python
# post_tool_use.py
import json
import sys
import os

hook_input = json.loads(sys.stdin.read())

# Check if we were tracking
state_file = ".claude/hooks/.state/write_tracking.json"
if os.path.exists(state_file):
    with open(state_file) as f:
        state = json.load(f)

    # Validate the write
    file_path = state.get("file")
    # ... validation logic ...

    # Clear state
    os.remove(state_file)

sys.exit(0)
```

### Pattern: Session-Level State

For state that persists across multiple tool calls:

```python
# In any hook
STATE_FILE = ".claude/hooks/.state/session_state.json"

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def update_state(updates):
    state = read_state()
    state.update(updates)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)
```

---

## HOOK REGISTRATION & CONFIGURATION

### settings.json Hook Registration

```json
{
  "hooks": {
    "SessionStart": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/session_start.py"
          }
        ]
      }
    ],
    "UserPromptSubmit": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/user_prompt_submit.py"
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/bash_validator.py",
            "timeout": 30
          }
        ]
      },
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/write_validator.py"
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/post_tool_use_router.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/completion_validator.py"
          }
        ]
      }
    ]
  }
}
```

### Hook Configuration Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `type` | string | Yes | `"command"`, `"prompt"`, `"http"`, or `"agent"` |
| `command` | string | For command type | Shell command or script path |
| `prompt` | string | For prompt type | LLM evaluation prompt |
| `http` | string | For http type | URL to POST to |
| `agent` | string | For agent type | Agent configuration |
| `timeout` | number | No | Seconds (default: 60, max: 600) |
| `if` | string | No | Permission rule syntax for subcommand matching |
| `async` | boolean | No | Run hook asynchronously (non-blocking) |
| `once` | boolean | No | Run hook only once per session (skills only) |
| `description` | string | No | For plugin hooks |

### Hooks in Skills & Agents

Modern Claude Code supports hooks in skill/agent frontmatter:

```markdown
---
name: Database Migration Skill
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: ./validate_schema.py
  PostToolUse:
    - matcher: "Edit|Write"
      hooks:
        - type: command
          command: ./verify_migration.py
  Stop:
    - hooks:
        - type: command
          command: ./check_completion.py
  once: true
---

# Database Migration Guide
...
```

The `once: true` option runs the hook only once per session (skills only).

### Subagent Recursive Enforcement

Hooks automatically fire for subagents. If an agent spawns a subagent, security gates inspect every tool the subagent attempts to use — preventing blast-radius escalation:

```
Main agent → PreToolUse hook fires
Main agent spawns subagent → PreToolUse hook fires for subagent
Subagent calls Bash → PreToolUse hook fires again with subagent context
```

This means a single security hook in the top-level `settings.json` protects all nested subagent tool calls without additional configuration.

### Component-Scoped Hooks (Skill/Agent Frontmatter)

Hooks embedded in skill or agent frontmatter **only execute while that skill/agent is active**. This prevents global hook sprawl:

```markdown
---
name: Database Migration Skill
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: ./validate_schema.sh
  once: true
---

# Database Migration Guide
```

Benefits:
- **Scoped**: Only runs during this skill's context — no global side effects
- **Explicit**: Team can see migration-specific gates are active
- **Versioned**: Hook behavior travels with the skill definition

---

## 6.1 Skill Frontmatter Best Practices

Best practices for hooks embedded in skill/agent frontmatter:

| BP | Phase | YAML/Example | Rationale |
|----|------|-------------|-----------|
| **Tiered Cascade** | PreToolUse | L1:`if` fast-deny → L2:prompt LLM → L3:agent deep | 95% blocked at L1, LLM only on edge cases |
| **Self-Verify Loop** | PostToolUse | `{"ok": bool, "reason": str}` JSON → re-inject if !ok | Catch rollback side-effects |
| **once:true State** | Any | `once: true` on skill activate, file flag for idempotence | Prevent re-trigger on resume |
| **Binary Prompt** | UserPromptSubmit | Condensed deny/allow prompt (50ms avg) | Ladder: fast-deny pattern → full LLM on uncertain |
| **Daemon HTTP** | async | HTTP hook with external service polling | Scale: webhook → queue → async worker |
| **Gerund Name** | Stop | Skill name ends in `-ing` (e.g., `migrating-db`) | Human-readable active-context label |

### Self-Verifying YAML Example

```markdown
---
name: migrating-db
hooks:
  PreToolUse:
    - matcher: "Bash.*DROP"
      hooks:
        - type: prompt
          prompt: |
            BLOCK if command contains DROP TABLE or DROP DATABASE.
            ALLOW otherwise.
          timeout: 5
  PostToolUse:
    - matcher: "*"
      hooks:
        - type: command
          command: ./verify_migration_state.py
          once: true
---

# Database Migration Guide
...
```

**Test specification:**
```
/skill migrating-database
→ Bash "DROP TABLE users;"
expect: deny (PreToolUse blocks)
→ Bash "SELECT * FROM users;"
expect: allow
```

## 6.2 Hooks-Skills-Agents Interactions

### Subagent Recursive Enforcement

Hooks automatically fire for subagents. If an agent spawns a subagent, security gates inspect every tool the subagent attempts to use — preventing blast-radius escalation:

```
Main agent → PreToolUse hook fires
Main agent spawns subagent → PreToolUse hook fires for subagent
Subagent calls Bash → PreToolUse hook fires again with subagent context
```

**Pitfall (Infinite Loop Trap):** When using `Stop` or `SubagentStop` hooks to force task completion, you MUST check the `stop_hook_active` boolean. If `true`, exit cleanly — otherwise the hook fires again when the agent stops, creating an infinite recursion loop.

**Recursion guard pattern:**

```json
{
  "SubagentStop": [
    {
      "hooks": [
        {
          "type": "command",
          "command": "./enforce_depth.sh",
          "if": "stop_hook_active == true"
        }
      ]
    }
  ]
}
```

| Topic | Why Experts Want | Gap | Example |
|-------|------------------|-----|---------|
| **Recursion Guards** | Loop prevention | Partial | SubagentStop: `if depth>3 continue:false` |
| **Skill-Hook Bundles** | Marketplace distribution | No | `hooks.json` + `SKILL.md` zip |
| **Agent Chains** | e2e workflows | No | `/implement`: decomposer skill → executor agent |
| **Metrics** | Observability | Partial | FileChanged → Prometheus; TeammateIdle heartbeat |
| **CLAUDE.md Synergy** | Rule enforcement | Core only | PreToolUse: Grep md violations |
| **95-Hook Setups** | Prod extremes | No | safety(PreToolUse)/blog(Stop) gates |

### Recipes (Expert Workflows)

**1. End-to-End Implement** — `commands/implement.md` (skill: decompose → subagent exec) + `hooks/review.py` (Stop quality gate)

**2. Marketplace Plugin** — `hooks.json` (http:`$CLAUDEPLUGINROOT/api`) + `SKILL.md`; MCP share

```yaml
# hooks/hooks.json
hooks:
  PreToolUse:
    - matcher: "*"
      hooks:
        - type: http
          http: "$CLAUDEPLUGINROOT/api/guard"
          timeout: 100
```

Variables: `$CLAUDE_PLUGIN_ROOT` (plugin dir), `$CLAUDE_PROJECT_DIR` (project root).

**Plugin hardening (v2.1.116+):** Add `"allowManagedHooksOnly": true` to teams to restrict to managed hooks only.

### Component-Scoped Hooks (Skill/Agent Frontmatter)

Hooks embedded in skill or agent frontmatter **only execute while that skill/agent is active**. This prevents global hook sprawl:

```markdown
---
name: Database Migration Skill
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: command
          command: ./validate_schema.sh
  once: true
---

# Database Migration Guide
```

Benefits:
- **Scoped**: Only runs during this skill's context — no global side effects
- **Explicit**: Team can see migration-specific gates are active
- **Versioned**: Hook behavior travels with the skill definition


---

## CONFIGURATION SCOPES & LOCATIONS

### Scope Precedence (Highest to Lowest)

```
Managed (highest precedence)
  |
Command line flags
  |
Local project settings (.claude/settings.local.json)
  |
Shared project settings (.claude/settings.json)
  |
User settings (lowest) (~/.claude/settings.json)
```

### Configuration File Locations

| Scope | Location | Use Case |
|-------|----------|----------|
| **Managed** | `/etc/claude-code/managed-settings.json` (Linux/WSL) | Enterprise policies |
| | `/Library/Application Support/ClaudeCode/managed-settings.json` (macOS) | |
| | `C:\Program Files\ClaudeCode\managed-settings.json` (Windows) | |
| **Local** | `.claude/settings.local.json` | Personal overrides (gitignored) |
| **Shared** | `.claude/settings.json` | Team hooks (committed) |
| **User** | `~/.claude/settings.json` | Global user preferences |
| **Plugin** | `hooks/hooks.json` within plugin directory | When plugin enabled |
| **Skill frontmatter** | In skill SKILL.md frontmatter | While skill is active |

### Plugin Hooks

Location: `hooks/hooks.json` within plugin directory

Available variables:
- `${CLAUDE_PLUGIN_ROOT}` - Absolute path to plugin directory
- `${CLAUDE_PROJECT_DIR}` - Project root directory

### Environment Variables for Hooks

| Variable | Value | Available In |
|----------|-------|--------------|
| `CLAUDE_PROJECT_DIR` | Absolute path to project root | All command hooks |
| `CLAUDE_ENV_FILE` | Path to env persistence file | SessionStart, CwdChanged, FileChanged |
| `CLAUDE_CODE_REMOTE` | "true" if web, empty if local | All command hooks |
| All system env vars | From host environment | All command hooks |

### Persisting Environment Variables (SessionStart, CwdChanged, FileChanged)

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export PATH="$PATH:./node_modules/.bin"' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

---

## OUTPUT FORMAT SPECIFICATIONS

### Hook Output Schema (stdout)

Hook commands must output valid JSON (exit code 0 only):

```json
{
  "continue": true,
  "stopReason": "optional message",
  "suppressOutput": false,
  "systemMessage": "warning message",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "string"
  }
}
```

### Universal Output Fields

| Field | Type | Behavior |
|-------|------|----------|
| `continue` | boolean | Allow or block (false = block for blocking phases) |
| `stopReason` | string | Message shown to user when blocking |
| `suppressOutput` | boolean | Hide hook output from user |
| `systemMessage` | string | Warning message shown to user |

### Phase-Specific Output Fields

#### UserPromptSubmit Output
```json
{
  "decision": "block",
  "reason": "Shown to user (not to Claude)",
  "hookSpecificOutput": {
    "hookEventName": "UserPromptSubmit",
    "additionalContext": "Added to Claude's context"
  }
}
```

#### PreToolUse Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "Your explanation",
    "updatedInput": {
      "command": "modified command"
    },
    "additionalContext": "Context for Claude"
  }
}
```

**`permissionDecision` values:**
- `allow` - Tool proceeds
- `deny` - Tool blocked
- `ask` - User prompted for permission
- `defer` - Defer to AskUserQuestion in non-interactive mode (v2.1.89+)

#### PermissionRequest Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "decision": {
      "behavior": "allow|deny|ask"
    },
    "reason": "Reason for decision"
  }
}
```

#### PostToolUse Output
```json
{
  "decision": "block",
  "reason": "Explanation for blocking",
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Additional information for Claude"
  }
}
```

#### Stop / SubagentStop Output
```json
{
  "decision": "block",
  "reason": "Must explain why Claude should continue"
}
```

#### TeammateIdle Output
```json
{
  "continue": false,
  "stopReason": "Teammate not ready to proceed"
}
```

#### TaskCreated Output
```json
{
  "continue": false,
  "stopReason": "Task creation blocked: reason"
}
```

#### SessionStart / SessionEnd Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Information added to context"
  }
}
```

### Exit Code Behavior

| Exit Code | Status | Behavior | Use Case |
|-----------|--------|----------|----------|
| **0** | Success | Hook succeeded, JSON output processed | Normal operation |
| **2** | Blocking Error | stderr fed to Claude, action blocked | Validation failure |
| **1, 3-255** | Non-blocking Error | stderr shown in verbose mode, continue | Warnings, logging |

---

## EXIT CODE BEHAVIOR & CONTROL FLOW

### Exit Code Decision Tree

```
Hook executes
    |
Check exit code
    +-- 0: Success path
    |     +-- Parse JSON output
    |     +-- Check "continue" or "decision" field
    |     +-- Apply decision (block/allow)
    |
    +-- 2: Blocking error
    |     +-- stderr -> fed to Claude
    |     +-- Action blocked
    |     +-- Claude prompted with error
    |
    +-- 1, 3-255: Non-blocking error
          +-- stderr -> shown in verbose mode
          +-- Continue normally
```

### When Each Exit Code Matters

**Exit code 0**: Hook succeeded
- Output JSON processed normally
- Use when you want decision fields to control behavior
- Most common case

**Exit code 2**: Hook failed, needs Claude intervention
- stderr becomes input to Claude
- Block action and let Claude handle it
- Use for: "This is wrong, Claude needs to know about it"

**Exit code 1**: Hook failed, not Claude's problem
- Don't block Claude
- Just inform user something happened
- Use for: logging, notifications, non-critical errors

### Common Patterns

**Validating before action (exit code 0 + permissionDecision)**:
```python
if not is_valid(file):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": f"File {file} violates pattern {PATTERN}"
        }
    }
    print(json.dumps(output))
    sys.exit(0)  # Tell Claude via decision field

print(json.dumps({"continue": True}))
sys.exit(0)
```

**Validation error that Claude should fix (exit code 2)**:
```python
try:
    validate(file)
except ValidationError as e:
    print(f"Validation failed: {str(e)}", file=sys.stderr)
    sys.exit(2)  # Claude gets error and responds

sys.exit(0)
```

**Logging without control (exit code 0)**:
```python
log_activity(hook_input)
print(json.dumps({}))  # Nothing to control
sys.exit(0)
```

---

## PROMPT-BASED HOOKS

### Overview

Claude Code supports **prompt-based hooks** that use LLM evaluation instead of shell commands.

### Supported Events

All phases support prompt hooks.

### Configuration

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "Evaluate if the task is complete. The response was: $ARGUMENTS",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Prompt Variables

- `$ARGUMENTS` - JSON representation of hook input

### Response Schema

Prompt hooks must return JSON:

```json
{
  "ok": true,
  "reason": "Optional explanation (required when ok is false)"
}
```

### Behavior

| `ok` Value | Effect |
|------------|--------|
| `true` | Allow action to proceed |
| `false` | Block action, `reason` shown to Claude |

### Example: Task Completion Validation

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "prompt",
            "prompt": "You are a completion validator. Check if the following response indicates the task was fully completed, including tests and documentation updates. Response: $ARGUMENTS. Return {\"ok\": true} if complete, or {\"ok\": false, \"reason\": \"explanation\"} if incomplete."
          }
        ]
      }
    ]
  }
}
```

### When to Use Prompt Hooks

| Use Case | Command Hook | Prompt Hook |
|----------|--------------|-------------|
| Pattern matching | Preferred | - |
| File validation | Preferred | - |
| Context-aware decisions | - | Preferred |
| Semantic understanding | - | Preferred |
| Deterministic rules | Preferred | - |
| Complex logic | Preferred | - |

---

## HTTP AND AGENT HOOKS

### HTTP Hooks

Send hook input to an HTTP endpoint:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "hooks": [
          {
            "type": "http",
            "http": "https://internal.example.com/hook-handler",
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

The request body is the same JSON input as command hooks. Response format must match hook output schema.

### Agent Hooks (Experimental)

Spawn a subagent to handle the hook:

```json
{
  "hooks": {
    "TaskCreated": [
      {
        "hooks": [
          {
            "type": "agent",
            "agent": {
              "prompt": "Analyze this task: $ARGUMENTS. Return {\"ok\": true} to allow or {\"ok\": false, \"reason\": \"...\"} to block.",
              "tools": ["Read", "Bash"]
            }
          }
        ]
      }
    ]
  }
}
```

---

## ASYNC HOOKS

### Overview

Hooks can run asynchronously to avoid blocking the main execution flow:

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "async": true,
            "command": "./long-running-task.sh"
          }
        ]
      }
    ]
  }
}
```

### Behavior

- `async: true` hooks run in background
- Claude continues without waiting for result
- Exit codes are not actionable for blocking
- Use for: logging, analytics, external notifications
- **Results delivered on next conversational turn** — async hooks cannot block the current turn

### Use Cases

| Scenario | Async? | Reason |
|----------|--------|--------|
| Audit logging | Yes | Non-blocking, no decision |
| External notification | Yes | Fire-and-forget |
| Blocking validation | No | Need result before proceeding |
| State coordination | No | Need result for next step |
| Long-running test suite | Yes | Non-blocking, results on next turn |
| Code review deep scan | Yes | 10-60s operation, background |

### Ladder of Sophistication (Tiered Cascade)

Production hook systems use a three-tier architecture balancing speed and safety:

```
Level 1: Deterministic Command Hooks (<50ms)
  └── Ultra-fast shell script or `if` filter
  └── Instantly approves safe commands (ls, git status)
  └── Instantly blocks known dangerous commands (rm -rf /)
  └── Zero LLM cost, zero spawn cost with `if` filter

Level 2: Prompt Hooks (1-5s)
  └── Single-turn LLM evaluation for ambiguous cases
  └── Fast, cheap model returns {"ok": true/false}
  └── Escalates when Level 1 is inconclusive

Level 3: Agent Hooks (10-60s)
  └── Full subagent with Read/Grep tools
  └── Up to 50 turns for deep investigation
  └── Use for: code logic audit, architectural validation
```

**Why cascade?** Level 1 catches 90%+ of calls with near-zero latency. Only ambiguous cases escalate to LLM evaluation. This prevents slowdowns on every tool call while maintaining safety.

### Execution Model: Parallel + Most Restrictive Wins

All matching hooks for an event **run in parallel** — there is no first-match-wins ordering:

```
When 10 hooks evaluate a PreToolUse event:
  - All 10 run simultaneously
  - 9 return allow, 1 returns deny → action BLOCKED
  - All return allow but 1 returns ask → user prompted
  - Most restrictive decision wins regardless of order
```

**Multiple `updatedInput` modifications**: If several `PreToolUse` hooks return `updatedInput`, the last one to finish wins (non-deterministic). Avoid having multiple hooks modify the same tool input.

### Router Patterns: Performance Gating and Hook Sequencing

Despite hooks running in parallel, routers enable two architectural patterns that would otherwise seem impossible:

#### Pattern 1: Subprocess Performance Gate

Route expensive L2/L3 hooks behind a cheap L1 gate. The router script itself runs as a PreToolUse/PostToolUse command, but only invokes the expensive subprocess when criteria are met:

```yaml
PreToolUse:
  - matcher: "Bash"
    hooks:
      - type: command                    # L1: fast path check (subprocess, <5ms)
        command: |
          # Lightweight pre-check only
          if echo "$TOOL_INPUT" | grep -qE "git push|rm -rf"; then
            echo "BLOCKED: dangerous command"
            exit 1
          fi
          exit 0                         # Allow; router below will still fire
      - type: command                    # Router: decides whether to invoke slow path
        command: |
          # Runs after the fast check above
          if echo "$TOOL_INPUT" | grep -qE "pytest|npm test"; then
            # Expensive test-coverage hook fires here
            /path/to/coverage_audit.sh "$TOOL_INPUT"
          fi
```

**Why this works**: Both run in parallel, but the router's subprocess can itself be a dispatcher that conditionally runs a third script. True sequential chaining requires PostToolUse coordination via state files.

#### Pattern 2: Hook Order via State-File Sequencing

For multi-phase sequences impossible to express as parallel hooks, use a state file written by a fast PostToolUse and consumed by the next phase's PreToolUse:

```python
# post_tool_use_phase1.py — runs in parallel with all other PostToolUse hooks
import json, sys
hook_input = json.loads(sys.stdin.read())
state = {
    "phase1_completed": True,
    "file_modified": hook_input.get("tool_name") == "Write"
}
with open(".claude/hooks/.state/sequence.json", "w") as f:
    json.dump(state, f)
```

```python
# pre_tool_use_phase2.py — reads phase1 result before allowing the next tool
import json, os, sys
state_path = ".claude/hooks/.state/sequence.json"
if os.path.exists(state_path):
    state = json.load(open(state_path))
    if not state.get("phase1_completed"):
        print("ERROR: phase1 not complete")
        sys.exit(1)
sys.exit(0)
```

#### What routers cannot do

- **True sequential ordering** of multiple independent hooks on the same event — hooks fire simultaneously; use PostToolUse state-file coordination for phase sequencing
- **Blocking one hook to wait for another** on the same event — the execution model is parallel; a router can only decide which additional hooks to spawn after its own completion
- **Guaranteed ordering of side effects** across multiple tool calls — each tool call is an independent event with its own hook set

---

## COMMON FAILURE MODES & RECOVERY

### Failure Mode 1: Hook Command Not Found

**Symptom**: Hook doesn't fire, no error shown.

**Fix**: Use full paths, `chmod +x` scripts, test manually:
```bash
echo '{"hook_event_name":"PostToolUse","tool_name":"Write"}' | python hook.py
```

### Failure Mode 2: Exit Code 2 Causes Infinite Loop

**Symptom**: Claude retries same action, hook keeps blocking.

**Fix**: Use `permissionDecision: "deny"` (PreToolUse) or `decision: "block"` (other phases) with exit 0. Exit 2 only when Claude needs external intervention.

### Failure Mode 3: JSON Parse Error

**Symptom**: Hook output not processed, Claude doesn't respond.

**Fix**:
```python
try:
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
```

### Failure Mode 4: Missing Environment Variables

**Symptom**: Hook crashes on `$CLAUDE_PROJECT_DIR`.

**Fix**: `cwd = os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd()` — input JSON also includes `cwd` field.

### Failure Mode 5: State File Race Conditions

**Symptom**: Concurrent hooks corrupt state files.

**Fix**: Use file locking:
```python
import fcntl  # Unix; use msvcrt on Windows
with open(STATE_FILE, "r+") as f:
    fcntl.flock(f.fileno(), fcntl.LOCK_EX)
    data = json.load(f); data.update(updates)
    f.seek(0); f.truncate(); json.dump(data, f)
    fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### Failure Mode 6: Blocking at Write Time

**Symptom**: Claude stops mid-task, confused.

**Fix**: Don't block at write time. PreToolUse = validate *intent*. PostToolUse = validate *result*. Stop = final validation.

### Failure Mode 7: Hook Timeout

**Symptom**: Hook doesn't complete, action proceeds anyway.

**Fix**: Increase timeout (default 60s, max 600s):
```json
{ "type": "command", "command": "./slow.py", "timeout": 120 }
```

### Failure Mode 8: Shell Profile Pollution (JSON Corruption)

**Symptom**: Hook output causes JSON parse error — but the script works fine in terminal.

**Cause**: Shell profile (`.bashrc`, `.zshrc`, PowerShell profile) emits unconditional text (NVM, MOTD, echo statements) that prepends to hook stdout.

**Fix**: Wrap interactive-only output:
```bash
# In .bashrc / .zshrc — don't run in non-interactive hook shells
if [[ $- == *i* ]]; then
    echo "Welcome back"
fi
```

### Failure Mode 9: Stop/SubagentStop Infinite Loop

**Symptom**: Claude never stops — the Stop hook fires, blocks, Claude works, finishes, Stop hook fires again, blocks... infinite loop.

**Cause**: Hook returns blocking decision without checking `stop_hook_active`.

**Fix**: Always check the `stop_hook_active` flag:
```python
hook_input = json.loads(sys.stdin.read())
if hook_input.get("stop_hook_active"):
    # Already inside a Stop hook — must exit cleanly to prevent loop
    print(json.dumps({"decision": "continue", "reason": "Stop completed"}))
    sys.exit(0)
# Normal Stop validation logic...
```

### Failure Mode 10: Exit Code 2 Discards JSON

**Symptom**: `stderr` is shown but `stdout` JSON is ignored.

**Cause**: Exit code 2 signals a blocking error. Claude reads **only stderr** for the error message — `stdout` JSON is discarded.

**Fix**: Write error context to stderr, not stdout:
```python
# WRONG — JSON on stdout with exit 2
print(json.dumps({"error": "Invalid path"}))  # DISCARDED
sys.exit(2)

# CORRECT — context on stderr
print("Error: path contains forbidden pattern", file=sys.stderr)
sys.exit(2)  # Claude reads stderr, uses it to self-correct
```

### Failure Mode 11: Missing Script Permissions

**Symptom**: Hook silently does nothing.

**Cause**: Script not executable (`chmod +x` not run).

**Fix**: Always ensure executability:
```bash
chmod +x ./hooks/pre_tool_use.sh
# Verify
ls -la ./hooks/pre_tool_use.sh  # should show -rwx--
```

### Failure Mode 12: Silent Timeout Kill

**Symptom**: Long-running hook disappears without warning, action proceeds.

**Cause**: Default timeout is 60s for command hooks, 30s for prompts. Exceeding timeout silently kills the hook.

**Fix**:
```json
{ "type": "command", "command": "./full-test-suite.sh", "timeout": 300 }
```
For known long operations, set explicit timeout. Monitor logs for killed hooks.

---



---

## 13.1 Known Bugs, Quirks & Workarounds (v2.1.89–2.1.116+)

> This section tracks observed issues from docs, GitHub, and community threads and how to mitigate them. It is intentionally conservative: prefer safe fallbacks over cleverness.

**1. Prompt-based hook recursion with summaries**
- **Symptom**: Stop / prompt hooks appear to fire repeatedly when summaries or session-compaction are enabled.
- **Likely cause**: Model-generated follow-up turns still satisfy Stop conditions; summary-related hooks re-trigger on synthetic turns.
- **Mitigation**:
  - Use `once: true` for summary-related Stop/UserPromptSubmit hooks.
  - Inspect `stop_hook_active` and always allow when already in a continuation.
  - Gate on metadata fields (skip when `source == "compact"` or similar summary reasons).

**2. Subagent explosion in recursive agents**
- **Symptom**: Agent skills that spawn subagents recursively (e.g. task decomposition chains) trigger many SubagentStart / SubagentStop events, causing "hook storms" and latency spikes.
- **Mitigation**:
  - Maintain a `depth` counter in session-level state and deny or downgrade behavior when `depth > N`.
  - Prefer component-scoped hooks in specific skills for deep agent trees, not heavy global hooks in `settings.json`.

**3. Silent HTTP hook failures under load**
- **Symptom**: `type: "http"` hooks occasionally time out or fail transiently; Claude proceeds as if the hook never responded.
- **Mitigation**:
  - Always set an explicit `timeout` lower than your daemon's own timeout.
  - Log timeouts on the server side and implement retries when the operation is idempotent.
  - Keep critical safety hooks as `type: "command"` locally; use HTTP hooks for soft enforcement, analytics, or logging.

**4. Plugin hook misconfiguration**
- **Symptom**: Third-party plugins ship `hooks.json` that conflict with project or managed policies (for example, unexpected PreToolUse behavior).
- **Mitigation**:
  - Use managed settings to enforce `allowManagedHooksOnly: true` in sensitive environments.
  - Document which plugins are allowed to register hooks and at which phases.

**[Add more entries here as your team encounters new quirks.]**

## TESTING & VALIDATION PROTOCOL

### Test Harness

```bash
#!/bin/bash
# test_hook.sh - Test a hook without Claude Code

HOOK_PATH="$1"
PHASE="$2"
TOOL_NAME="${3:-Write}"

# Generate test input
TEST_INPUT=$(cat <<EOF
{
  "hook_event_name": "$PHASE",
  "session_id": "test_sess_123",
  "transcript_path": "/tmp/test_transcript.jsonl",
  "cwd": "$(pwd)",
  "permission_mode": "default",
  "tool_name": "$TOOL_NAME",
  "tool_input": {
    "file_path": "/tmp/test.txt",
    "content": "test content"
  }
}
EOF
)

echo "Testing: $HOOK_PATH"
echo "Input: $TEST_INPUT"
echo ""
echo "Output:"

echo "$TEST_INPUT" | python "$HOOK_PATH"
EXIT_CODE=$?

echo ""
echo "Exit Code: $EXIT_CODE"
```

Usage:
```bash
bash test_hook.sh ./hooks/pre_tool_use.py PreToolUse Write
```

### Integration Testing

```python
# test_integration.py

import json
import subprocess
import sys

def test_hook(hook_path, hook_input):
    """Test a hook with given input"""
    result = subprocess.run(
        [sys.executable, hook_path],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    try:
        output = json.loads(result.stdout)
    except:
        output = {"error": "Invalid JSON output", "stdout": result.stdout}

    return {
        "exit_code": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
        "output": output
    }

# Test blocking behavior
test_input = {
    "hook_event_name": "PreToolUse",
    "tool_name": "Write",
    "tool_input": {"file_path": "/src/dangerous.py", "content": "..."}
}

result = test_hook("./hooks/pre_tool_use.py", test_input)
assert result["exit_code"] == 0
assert result["output"].get("hookSpecificOutput", {}).get("permissionDecision") == "deny"
```

### Verification Checklist

- [ ] Hook command runs successfully (exit 0 on success)
- [ ] Output is valid JSON
- [ ] `continue` or `decision` field present when expected
- [ ] Exit code 2 used only for critical errors
- [ ] `systemMessage` or `additionalContext` is user-friendly
- [ ] No hard-coded paths (use `$CLAUDE_PROJECT_DIR`)
- [ ] State files cleaned up after use
- [ ] Logging goes to `.claude/hooks/logs/`
- [ ] Timeout specified for long-running hooks
- [ ] Works when called manually with test input

---

## ADVANCED PATTERNS & STRATEGIES

### Pattern 1: Multi-Phase Validation

Validate across multiple lifecycle phases:

```python
# Phase 1: Warn about intent
# UserPromptSubmit hook
if "delete database" in prompt.lower():
    return {
        "hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit",
            "additionalContext": "Warning: This prompt mentions deleting a database. This will require explicit confirmation."
        }
    }

# Phase 2: Block dangerous operations
# PreToolUse hook
if tool_name == "Bash" and "DROP" in tool_input.get("command", ""):
    return {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Database deletion requires team approval"
        }
    }

# Phase 3: Audit what actually happened
# PostToolUse hook
log_operation(tool_name, tool_input, tool_response)
```

### Pattern 2: Context Injection

Use hooks to inject context without blocking:

```python
# post_tool_use.py
if tool_name == "Bash":
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": "Note: For database operations in this project, use the /scripts/db-query.sh wrapper. See CLAUDE.md section 4.2 for examples."
        }
    }
    print(json.dumps(output))
    sys.exit(0)
```

### Pattern 3: Conditional Permission

```python
# pre_tool_use.py - Intelligent permission control
def should_allow_bash(tool_input):
    command = tool_input.get("command", "")

    # Always allow safe reads
    if command.startswith("cat ") or command.startswith("ls "):
        return "allow"

    # Ask for writes
    if any(op in command for op in ["rm", "mv", "touch", ">"]):
        return "ask"

    # Allow most other commands
    return "allow"

if hook_input.get("tool_name") == "Bash":
    decision = should_allow_bash(hook_input.get("tool_input", {}))
    if decision != "allow":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": decision,
                "permissionDecisionReason": "Destructive bash operations require confirmation"
            }
        }
        print(json.dumps(output))
        sys.exit(0)
```

### Pattern 4: State Machine

Track multi-step workflows:

```python
# Workflow: Test -> Review -> Deploy

STATE_FILE = ".claude/hooks/.state/deployment.json"

def read_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {"phase": "start"}

def update_state(updates):
    state = read_state()
    state.update(updates)
    with open(STATE_FILE, "w") as f:
        json.dump(state, f)

# In Stop hook: Check if we've completed all phases
state = read_state()
required_phases = ["test_complete", "review_complete"]

if not all(state.get(phase) for phase in required_phases):
    output = {
        "decision": "block",
        "reason": f"Deployment workflow incomplete: {state}"
    }
    print(json.dumps(output))
    sys.exit(0)
```

### Pattern 5: Audit Trail

Log all activity for compliance:

```python
# audit_logger.py
import json
import datetime

AUDIT_FILE = ".claude/hooks/logs/audit.log"

def log_event(hook_input):
    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "phase": hook_input.get("hook_event_name"),
        "session_id": hook_input.get("session_id"),
        "tool": hook_input.get("tool_name", "N/A"),
        "action": str(hook_input.get("tool_input", {}))[:200]
    }

    with open(AUDIT_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

# Called from every hook
log_event(hook_input)
```

### Pattern 6: Input Modification

Modify tool inputs before execution:

```python
# pre_tool_use.py - Add safety flags to npm commands
if tool_name == "Bash":
    command = tool_input.get("command", "")

    if command.startswith("npm install") and "--save-exact" not in command:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "updatedInput": {
                    "command": command + " --save-exact"
                },
                "additionalContext": "Added --save-exact flag per project standards"
            }
        }
        print(json.dumps(output))
        sys.exit(0)
```

---



---

## 15.1 Hook Pattern Catalog (Index)

This catalog names common patterns, links them to phases, and points to examples in this guide.

| Pattern | Goal | Best Phases | Example Section | Notes |
|---------|------|-------------|-----------------|-------|
| **Multi-Phase Validation** | Intent → result → final Stop gate | UserPromptSubmit, PreToolUse, PostToolUse, Stop | §15 | Multi-stage DB delete guard. |
| **Evidence Gate** | Require on-record evidence before key claims | Stop, SubagentStop | §15 | Perf/timing, safety-critical claims. |
| **Audit Trail** | Full tool execution log | PostToolUse | §12 | Log to `.claude/hooks/logs/`. |
| **CI Runner** | Run tests on key events | PostToolUse, TaskCompleted | §12 | `npm test` / `pytest` hooks. |
| **Prompt Injector Guard** | Scan prompts for sensitive tokens | UserPromptSubmit | §13 | Secret scanning, prompt-injection filters. |
| **Budget Governor** | Enforce cost/latency budgets | PreToolUse, Stop | §15 | Limit expensive tools/models or agents. |
| **Skill Self-Verify** | Skills check their own outputs | Stop (skill-scoped frontmatter) | §6.1 | Binary eval + artifact/evidence checks. |
| **Plugin Guard** | Inspect plugin / MCP tool calls | PreToolUse (MCP tools, plugin tools) | §6.2 | `matcher: "mcp.*"` HTTP/command guard. |

## IMPLEMENTATION CHECKLIST

### Before You Start
- CLAUDE.md context -> truth.md constraints -> phase mapping -> enforcement rule mapping -> state strategy

### Hook Development
- Hook type selection -> input parsing (`tool_input`) -> decision fields (continue/permissionDecision) -> exit codes

### Integration
- settings.json scope -> `/hooks` verify -> real session test -> additionalContext check -> state cleanup -> log review

### Testing
- Manual test -> integration test -> blocking (exit 0 + continue:false) -> error (exit 2) -> state persistence -> updatedInput -> async

### Documentation
- Script comments -> truth.md refs -> I/O examples -> state format -> troubleshooting -> permissions

### Maintenance
- Log monitor -> false positive tracking -> CLAUDE.md/truth.md sync -> audit review -> state cleanup -> version control

---



---

## 17. Daemonization & Performance Benchmarks

This section is optional but recommended if you run many hooks (50–100+).

### 17.1 Why Run a Hook Daemon?

Command hooks spawn a new process on every event. At small scale this is fine; at high frequency it becomes a measurable overhead. Moving logic into an HTTP daemon can reduce per-hook latency and CPU usage, especially for logging and analytics hooks.

**Typical migration strategy:**
1. Keep critical safety hooks as `type: "command"` at first.
2. Migrate read-only and logging hooks to `type: "http"` targeting a local daemon.
3. Once stable and observable, consider migrating more complex validation logic.

### 17.2 Example: Migrating a Validator to HTTP

1. Start a local daemon (Python/Node/Go) that exposes `/pretooluse` and `/stop` endpoints.
2. Translate existing command-hook logic into HTTP handlers that accept the same JSON payload and return the same JSON output schema.
3. Update settings:
   - Replace `type: "command"` with `type: "http"`.
   - Set `http: "http://127.0.0.1:8080/pretooluse"` (or your chosen URL).
   - Add an explicit `timeout` and appropriate logging on the daemon side.
4. Monitor for correctness before removing the original command hook.

### 17.3 Benchmark Template

Suggested metrics to capture in your own environment:

| Setup | Hooks Count | Hook Type | p50 (ms) | p95 (ms) | Notes |
|-------|------------|-----------|----------|----------|-------|
| A | 10 | command | 20 | 70 | Baseline. |
| B | 50 | command | 30 | 110 | Noticeable overhead. |
| C | 50 | http daemon | 8 | 25 | 3–4× faster in test environment. |
| D | 95 | mixed | 10 | 35 | Real-world (safety + quality set). |

Populate with your actual measurements to make this section concrete for your team.

## COMPLETE CODE EXAMPLES

### Complete Hook Template (v3.0)

```python
#!/usr/bin/env python3
"""
Hook Template: [Hook Name]

Purpose: [What this hook does]
Enforces: [Which rule/policy]
Phases: [Which lifecycle phases]

Input: [Describe expected input fields]
Output: [Describe output schema]

Claude Code Version: 3.0+
"""

import json
import sys
import os
from datetime import datetime

# Configuration
LOG_FILE = ".claude/hooks/logs/hook_execution.log"
STATE_DIR = ".claude/hooks/.state"

def ensure_dirs():
    """Create necessary directories"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

def log(message):
    """Log hook execution"""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{datetime.now().isoformat()}] {message}\n")

def main():
    try:
        # Parse input
        hook_input = json.loads(sys.stdin.read())
        hook_event = hook_input.get("hook_event_name", "Unknown")

        log(f"Hook fired: {hook_event}")

        # Your logic here
        result = validate(hook_input)

        # Output result
        print(json.dumps(result))
        sys.exit(0)

    except Exception as e:
        log(f"ERROR: {str(e)}")
        print(f"Hook error: {str(e)}", file=sys.stderr)
        sys.exit(1)

def validate(hook_input):
    """Implement your validation logic"""
    hook_event = hook_input.get("hook_event_name")

    # Return appropriate output based on hook type
    if hook_event == "PreToolUse":
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "allow",
                "additionalContext": "Validation passed"
            }
        }
    elif hook_event == "PostToolUse":
        return {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse",
                "additionalContext": "Post-execution check complete"
            }
        }
    elif hook_event == "Stop":
        return {
            "continue": True
        }
    else:
        return {"continue": True}

if __name__ == "__main__":
    ensure_dirs()
    main()
```

### Example: PreToolUse Validator (v3.0)

```python
#!/usr/bin/env python3
"""
Hook: PreToolUse Validator

Purpose: Validate tool usage against project rules before execution
Enforces: CLAUDE.md section 2.1 (Tool Usage Guidelines)
Phases: PreToolUse

Input: tool_name, tool_input
Output: hookSpecificOutput with permissionDecision

Claude Code Version: 3.0+
"""

import json
import sys
import os

FORBIDDEN_PATHS = ["/etc", "/sys", "/proc", "~/.ssh"]
DANGEROUS_COMMANDS = ["rm -rf /", "dd if=", "mkfs", "> /dev/"]

def validate(hook_input):
    """Validate tool usage"""
    tool_name = hook_input.get("tool_name")
    tool_input = hook_input.get("tool_input", {})

    if tool_name == "Bash":
        return validate_bash(tool_input)
    elif tool_name == "Write":
        return validate_write(tool_input)
    elif tool_name == "Edit":
        return validate_edit(tool_input)

    return {"continue": True}

def validate_bash(tool_input):
    """Validate bash operations"""
    command = tool_input.get("command", "")

    # Check for dangerous commands
    for dangerous in DANGEROUS_COMMANDS:
        if dangerous in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Dangerous command pattern detected: {dangerous}"
                }
            }

    # Check for forbidden paths
    for path in FORBIDDEN_PATHS:
        if path in command:
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": f"Access to {path} is restricted"
                }
            }

    return {"continue": True}

def validate_write(tool_input):
    """Validate file writes"""
    file_path = tool_input.get("file_path", "")

    # Check for sensitive files
    sensitive_patterns = [".env", "credentials", "secrets", ".pem", ".key"]
    for pattern in sensitive_patterns:
        if pattern in file_path.lower():
            return {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "ask",
                    "permissionDecisionReason": f"Writing to potentially sensitive file: {file_path}"
                }
            }

    return {"continue": True}

def validate_edit(tool_input):
    """Validate file edits"""
    file_path = tool_input.get("file_path", "")

    # Prevent editing lock files
    if file_path.endswith(".lock"):
        return {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Lock files should not be edited directly"
            }
        }

    return {"continue": True}

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
        result = validate(hook_input)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"Hook error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example: PostToolUse Audit Logger (v3.0)

```python
#!/usr/bin/env python3
"""
Hook: PostToolUse Audit Logger

Purpose: Log all tool executions for audit trail
Enforces: Compliance logging requirements
Phases: PostToolUse

Input: tool_name, tool_input, tool_response
Output: Audit log entry (no decision)

Claude Code Version: 3.0+
"""

import json
import sys
import os
import datetime

LOG_FILE = ".claude/hooks/logs/audit.log"
STATE_DIR = ".claude/hooks/.state"

def ensure_dirs():
    """Create necessary directories"""
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    os.makedirs(STATE_DIR, exist_ok=True)

def log_event(hook_input):
    """Log tool execution"""
    tool_response = hook_input.get("tool_response", {})

    event = {
        "timestamp": datetime.datetime.now().isoformat(),
        "session_id": hook_input.get("session_id"),
        "phase": hook_input.get("hook_event_name"),
        "tool": hook_input.get("tool_name"),
        "success": tool_response.get("success", True),
        "input_summary": str(hook_input.get("tool_input", {}))[:200]
    }

    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(event) + "\n")

def main():
    try:
        ensure_dirs()
        hook_input = json.loads(sys.stdin.read())
        log_event(hook_input)

        # No blocking - just log
        output = {
            "continue": True,
            "hookSpecificOutput": {
                "hookEventName": "PostToolUse"
            }
        }
        print(json.dumps(output))
        sys.exit(0)
    except Exception as e:
        print(f"Audit log error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example: Stop Phase Validator (v3.0)

```python
#!/usr/bin/env python3
"""
Hook: Stop Phase Validator

Purpose: Ensure all requirements met before session ends
Enforces: CLAUDE.md section 4.3 (Completion Requirements)
Phases: Stop

Input: stop_hook_active
Output: continue: true/false

Claude Code Version: 3.0+
"""

import json
import sys
import os

STATE_FILE = ".claude/hooks/.state/task_tracking.json"

def read_state():
    """Read task tracking state"""
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE) as f:
            return json.load(f)
    return {}

def validate_completion(hook_input):
    """Validate that work is complete"""

    # Check if we're already in a stop hook loop
    if hook_input.get("stop_hook_active"):
        # Don't block again if already continuing
        return {"continue": True}

    state = read_state()

    # Check for required completions
    required = state.get("required_tasks", [])
    completed = state.get("completed_tasks", [])

    missing = [t for t in required if t not in completed]

    if missing:
        return {
            "continue": False,
            "stopReason": f"Incomplete tasks: {', '.join(missing)}. Please complete these before finishing."
        }

    return {"continue": True}

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
        result = validate_completion(hook_input)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"Stop validator error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example: TaskCreated Validator (v3.0)

```python
#!/usr/bin/env python3
"""
Hook: TaskCreated Validator

Purpose: Validate task before creation
Enforces: Task naming and scope rules
Phases: TaskCreated

Input: task_id, task_type
Output: continue: false to block

Claude Code Version: 3.0+
"""

import json
import sys
import os

# Block tasks with certain prefixes
BLOCKED_PREFIXES = ["debug-", "temp-", "test-"]

def validate_task(hook_input):
    """Validate task creation"""
    task_id = hook_input.get("task_id", "")
    task_type = hook_input.get("task_type", "")

    for prefix in BLOCKED_PREFIXES:
        if task_id.startswith(prefix):
            return {
                "continue": False,
                "stopReason": f"Task ID '{task_id}' starts with blocked prefix '{prefix}'"
            }

    return {"continue": True}

def main():
    try:
        hook_input = json.loads(sys.stdin.read())
        result = validate_task(hook_input)
        print(json.dumps(result))
        sys.exit(0)
    except Exception as e:
        print(f"TaskCreated validator error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
```

### Example: SessionStart Environment Setup (v3.0)

```bash
#!/bin/bash
# Hook: SessionStart Environment Setup
#
# Purpose: Set up environment variables for the session
# Phases: SessionStart
#
# Claude Code Version: 3.0+

# Persist environment variables if env file available
if [ -n "$CLAUDE_ENV_FILE" ]; then
    # Add project-specific paths
    echo 'export PATH="$PATH:./node_modules/.bin:./scripts"' >> "$CLAUDE_ENV_FILE"

    # Set development environment
    echo 'export NODE_ENV=development' >> "$CLAUDE_ENV_FILE"

    # Add project aliases
    echo 'alias test="npm test"' >> "$CLAUDE_ENV_FILE"
fi

# Output JSON response
cat << 'EOF'
{
  "continue": true,
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Environment initialized with project paths and aliases"
  }
}
EOF

exit 0
```

---

## QUICK REFERENCE GUIDES

### Hook Lifecycle at a Glance

```
Session starts -> SessionStart
User types prompt -> UserPromptSubmit (can BLOCK)
Claude decides tool -> PreToolUse (can DENY/ALLOW/ASK/DEFER)
Permission needed? -> PermissionRequest (can AUTO-RESPOND)
Permission denied? -> PermissionDenied
Tool runs -> PostToolUse (can provide feedback)
Tool fails? -> PostToolUseFailure
Subagent spawns -> SubagentStart
Subagent finishes -> SubagentStop (can BLOCK)
Teammate idle -> TeammateIdle (can BLOCK)
Task created -> TaskCreated (can BLOCK)
Task completes -> TaskCompleted
Instructions loaded -> InstructionsLoaded
Config changes -> ConfigChange
Cwd changes -> CwdChanged
File changes -> FileChanged
Worktree created -> WorktreeCreate (can BLOCK)
Worktree removed -> WorktreeRemove
Claude ready to stop -> Stop (can BLOCK)
Stop fails -> StopFailure
Memory compacts -> PreCompact -> PostCompact
Session ends -> SessionEnd
```

### Decision Quick Reference

| Phase | Field | Values | Effect |
|-------|-------|--------|--------|
| UserPromptSubmit | decision | "block" \| undefined | Allow or reject prompt |
| PreToolUse | permissionDecision | "deny" \| "ask" \| "allow" \| "defer" | Deny, prompt, allow, or defer |
| PermissionRequest | decision.behavior | "allow" \| "deny" \| "ask" | Auto-respond to permission |
| PermissionDenied | continue | false | Block workflow |
| PostToolUse | decision / continue | "block" / false | Provide feedback or continue |
| Stop | decision / continue | "block" / false | Force continuation or allow stop |
| SubagentStop | decision / continue | "block" / false | Continue subagent or allow completion |
| TeammateIdle | continue | false | Block idle continuation |
| TaskCreated | continue | false | Block task creation |

### Output Schema Quick Reference

```json
{
  "continue": true,
  "stopReason": "message",
  "suppressOutput": false,
  "systemMessage": "warning",
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse|PostToolUse|...",
    "permissionDecision": "allow|deny|ask|defer",
    "permissionDecisionReason": "string",
    "updatedInput": { "field": "value" },
    "additionalContext": "string"
  }
}
```

### Common Hook Patterns

1. **Validation** (exit 0 + continue: false)
2. **Logging** (exit 0, no decision)
3. **Error Recovery** (exit 2 with stderr)
4. **State Coordination** (file-based .state/)
5. **Input Modification** (updatedInput field)
6. **Context Injection** (additionalContext field)
7. **Async Fire-and-Forget** (async: true)

### Debugging Commands

```bash
# Check hook registration
/hooks

# Run hook manually
echo '{"hook_event_name":"PreToolUse","tool_name":"Write","tool_input":{"file_path":"/test.txt"}}' | python hook.py

# View hook logs
cat .claude/hooks/logs/hook_execution.log

# Debug mode
claude --debug

# Test JSON validity
echo '{"continue":true}' | jq .
```

---

## TROUBLESHOOTING QUICK START

| Problem | Solution |
|---------|----------|
| Hook doesn't fire | settings.json syntax, path exists, executable (`chmod +x`) |
| Invalid JSON | `jq` validate, `json.dumps()`, check string escaping |
| Claude ignores output | exit code, output structure, JSON validity |
| State corruption | File locking, reduce writes, check permissions |
| Infinite loop | exit 0 + continue:false (not exit 2), add reason |
| Permission denied | `chmod +x`, dir permissions, path verification |
| Hook timeout | Increase timeout config, optimize performance |
| Wrong tool_input | Use `tool_input` (not `tool_arguments`) |

---

## SECURITY CONSIDERATIONS

**Hooks execute arbitrary shell commands with your environment's credentials.**

**Do**: Review code thoroughly, use absolute paths, keep hooks in version control, sanitize input, validate JSON before processing.

**Never**: Copy untrusted hooks, eval() or exec() untrusted input.

---

## PRODUCTION PATTERNS (v3.1)

### Tiered Cascade (Ladder of Sophistication)

Production hook systems use a three-tier cascade balancing speed and safety:

```
Level 1: Deterministic Command Hooks (<50ms)
  └── `if` filter eliminates T_spawn for non-matches
  └── 90%+ of tool calls rejected at engine level
  └── Example: block rm*, git rm* instantly

Level 2: Prompt Hooks (1-5s)
  └── Single-turn LLM evaluation for ambiguous cases
  └── Returns {"ok": true/false, "reason": "..."}
  └── Fast model (claude-3.5-sonnet or equivalent)

Level 3: Agent Hooks (10-60s)
  └── Full subagent with Read/Grep tools
  └── Up to 50 turns for deep investigation
  └── Use for: architectural validation, security audits
```

### Tiered Cascade YAML Configuration

```yaml
hooks:
  PreToolUse:
    - matcher: "Bash"
      hooks:
        - type: "command"       # L1: Fast deterministic filter
          if: "Bash(rm *|git rm *|sudo *|chmod 777 *)"
          command: "$CLAUDE_PROJECT_DIR/.claude/hooks/block-destruct.sh"
        - type: "prompt"        # L2: Semantic evaluation
          if: "Bash(git|docker|npm|uv|pip *)"
          prompt: |-
            $ARGUMENTS
            Return JSON: {"ok": true/false, "reason": "..."}
          model: "claude-3.5-sonnet-20241022"
        - type: "agent"          # L3: Deep investigation
          if: "Bash(deploy|migrate|drop *)"
          prompt: |-
            Analyze $ARGUMENTS with Read/Grep tools.
            Block if unsafe. Return {"ok": true/false, "reason": "..."}
```

### State Management & Logging

```yaml
# Central state file per session
hooks:
  SessionStart:
    - hooks:
        - type: "command"
          command: |
            mkdir -p "$CLAUDE_PROJECT_DIR/.claude/hooks/state"
            echo '{"session_id":"$CLAUDE_SESSION_ID","tasks":[],"approvals":[]}' \
              > "$CLAUDE_PROJECT_DIR/.claude/hooks/state/$CLAUDE_SESSION_ID.json"

  TaskCompleted:
    - matcher: "*"
      hooks:
        - type: "command"
          command: |
            # Append to session state
            jq ".tasks += [{\"id\":\"$ARGUMENTS.taskId\",\"result\":\"done\"}]" \
              "$CLAUDE_PROJECT_DIR/.claude/hooks/state/$CLAUDE_SESSION_ID.json"

# Log rotation via cron or hook:
# 0 * * * * rotatelogs /var/log/claude-hooks.log 86400
```

### Performance Optimizations

| Technique | Latency Reduction | Example |
|-----------|-----------------|---------|
| `if` filter | Eliminates T_spawn on non-match | `if: "Bash(git status|diff|log *)"` |
| Alphanumeric matchers | 10x faster than regex | `matcher: "Bash"` (exact, no regex) |
| `once: true` | Run hook only once per session | SessionStart hooks |
| Short timeout | Fail fast, don't hang | `timeout: 5000` |
| Exit 2 early | Block before heavy processing | Destructive commands |

```yaml
# Fast filter: 0ms for non-matching calls
- matcher: "Bash"
  hooks:
    - type: "command"
      if: "Bash(git status|git diff|git log|git branch|ls|pwd|ps *)"
      command: "./fast-allow.sh"

# Exit 2 on dangerous patterns immediately
if command matches "rm -rf|sudo |chmod 777"; then
  echo "Blocked: destructive command" >&2
  exit 2
fi
```

### Resilience Patterns

**Stop/SubagentStop Infinite Loop Prevention**:

```python
hook_input = json.loads(sys.stdin.read())
if hook_input.get("stop_hook_active"):
    # Already inside a Stop hook — must exit cleanly
    print(json.dumps({"decision": "continue", "reason": "Stop completed"}))
    sys.exit(0)
```

**Graceful Degradation with Fallback**:

```python
try:
    result = validate(hook_input)
    print(json.dumps({"ok": True, "result": result}))
except Exception as e:
    print(json.dumps({"ok": True, "fallback": True, "error": str(e)}))
sys.exit(0)  # Never block on internal errors
```

**JSON Validation Before Processing**:

```python
import json, sys
data = json.loads(sys.stdin.read())
if not isinstance(data.get("hook_event_name"), str):
    print("Error: invalid hook input", file=sys.stderr)
    sys.exit(1)
```

### Enhanced Test Harness

```bash
#!/bin/bash
# testhook-multi.sh — parallel hook testing across phases

HOOK_DIR="$1"
PHASE="${2:-PreToolUse}"
TOOL="${3:-Bash}"

mkdir -p /tmp/hook-tests
cat > /tmp/hook-tests/input.json <<EOF
{
  "hook_event_name": "$PHASE",
  "session_id": "test-$$",
  "cwd": "$PWD",
  "tool_name": "$TOOL",
  "tool_input": {"command": "ls -la"},
  "permission_mode": "default"
}
EOF

# Run all hooks in parallel
for hook in "$HOOK_DIR"/*.sh; do
    [ -x "$hook" ] || continue
    name=$(basename "$hook")
    echo "Testing: $name"
    cat /tmp/hook-tests/input.json | "$hook" > "/tmp/hook-tests/out-$name" 2>&1 &
done
wait

# Check results
for f in /tmp/hook-tests/out-*; do
    echo "=== $(basename $f) ==="
    cat "$f"
    echo ""
done
```

### MCP Integration Patterns

| Pattern | Phase | Output | Use Case |
|---------|-------|--------|----------|
| Memory sync | TaskCompleted | `systemMessage: "mcp.memory.update {id:$TASK_ID,done:true}"` | Long-running task memory |
| Slack alert | PostToolUse | `mcp__slack__chat_postMessage` | Notify on failures |
| Git guard | PreToolUse git* | `updatedInput.command` rewrite | Audit trail |
| LLM escalate | PermissionDenied | `continue: false` + reason | Hybrid auto-approve |
| Context inject | PostToolUse Write | `additionalContext` | Inline guidance |

### Monitoring & Observability

```yaml
# File change monitoring → Prometheus metrics
hooks:
  FileChanged:
    - hooks:
        - type: "command"
          command: |
            echo "file_changes_total{path=\"$ARGUMENTS.path\"} 1" >> /tmp/hook-metrics

# CwdChanged tracking
  CwdChanged:
    - hooks:
        - type: "command"
          command: |
            echo "cwd_changes{path=\"$ARGUMENTS.cwd\"} 1" >> /tmp/hook-metrics

# TeammateIdle heartbeat
  TeammateIdle:
    - hooks:
        - type: "command"
          command: |
            jq ".last_heartbeat = \"$(date -Iseconds())\" | .idle_duration_ms = $ARGUMENTS.idle_duration_ms" \
              "$CLAUDE_PROJECT_DIR/.claude/hooks/state/$CLAUDE_SESSION_ID.json"
```

### HTTP Hooks for Multi-Agent Orchestration

```yaml
hooks:
  Stop:
    - matcher: "*"
      hooks:
        - type: "http"
          http: "http://localhost:8000/hooks/stop"
          timeout: 30000
```

```python
# stop_router.py — example HTTP hook handler
from fastapi import FastAPI, HookEvent
app = FastAPI()

@app.post("/hooks/stop")
async def handle_stop(event: HookEvent):
    if event.stop_hook_active:
        return {"continue": False, "reason": "nested stop blocked"}
    # Check workflow state
    state = read_workflow_state()
    if state.complete:
        return {"continue": True}
    return {"continue": False, "stopReason": "workflow incomplete"}
```

### Plugin Hardening (v2.1.116+)

```json
{
  "allowManagedHooksOnly": true,
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "./enforce-policy.sh"
          }
        ]
      }
    ]
  }
}
```

### Integration Checklist

- [ ] L1 deterministic filters in place for common dangerous patterns
- [ ] L2 prompt hooks configured for ambiguous cases
- [ ] L3 agent hooks available for deep audits
- [ ] State file per session with rotation
- [ ] Log aggregation configured
- [ ] `stop_hook_active` anti-loop pattern in all Stop hooks
- [ ] Fallback `continue: true` for non-critical hooks
- [ ] `if` filters used to eliminate T_spawn overhead
- [ ] Alphanumeric matchers for simple tool-name matching
- [ ] Timeout set appropriately (5s command, 30s prompt)
- [ ] MCP memory sync for long-running tasks
- [ ] Prometheus metrics emitted for FileChanged/CwdChanged

---



---

## 18. External Tools & MCP Integration

Hooks become significantly more powerful when combined with external tools and MCP servers.

### 18.1 Common Integration Targets

- **Slack / Chat**: Notify humans when high-risk actions are attempted or blocked.
- **Issue Trackers**: File tickets automatically on repeated failures.
- **Vector Stores / Databases**: Check for existing evidence, designs, or decisions before letting Claude proceed.
- **Cost / Usage Meters**: Enforce monthly or per-session budgets.

### 18.2 MCP-based Patterns

**Example: Evidence-aware Stop hook.**

1. Use `PostToolUse` hooks to log relevant information to an MCP memory server (for example, `mcp.memory.write`).
2. Use a Stop `type: "agent"` hook with Read/Grep tools to verify that evidence exists for a claim or decision being made.
3. If no evidence is found, return `continue: false` with a `systemMessage` instructing Claude to gather evidence first, then try stopping again.

### 18.3 Cost / Budget Governor

- Use a PreToolUse hook to track tool usage or estimated cost in a state file or external cost service.
- When thresholds are exceeded, block expensive tools or models and suggest cheaper alternatives or human escalation instead.

### 18.4 Compliance Logging to External Systems

- Use PostToolUse hooks to stream structured events (tool name, input summary, outcome) to a SIEM or external logging service.
- Ensure sensitive secrets are not logged; apply redaction in the hook process before sending.

**(Adapt tool names, MCP endpoints, and security requirements to your environment.)**

## RESOURCES & REFERENCES

- Claude Code Official Hooks Documentation: https://code.claude.com/docs/en/hooks
- Claude Code Best Practices: https://docs.anthropic.com/en/docs/claude-code/best-practices

---

**End of Document**

**Download this file as: `claude-hooks-guide.md`**

This guide is ready for:
- Immediate use in Claude Code development
- Conversion to a Claude Code skill
- Sharing with other LLMs and developers
- Copy-paste implementation of all examples
- Reference during hook debugging and development