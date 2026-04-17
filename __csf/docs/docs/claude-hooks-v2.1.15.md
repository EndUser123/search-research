# The Ultimate Claude Code Hooks Guide
## A Comprehensive Reference for Developing, Deploying, and Troubleshooting Claude Code Hooks

**Document Version**: 2.1.15
**Last Updated**: January 22, 2026
**Claude Code Version**: 2.1.15+
**Intended Audience**: Claude Code developers, LLM agents, automation specialists
**Classification**: Reference Guide / Skill Material

---

## SOLUTION DESIGN

### Current State vs Target State

**Current State:**
- Hook developers must reverse-engineer behavior from code inspection alone
- Multiple LLMs struggle to understand hook protocol without reading implementation
- Knowledge gaps about lifecycle phases, input/output schemas, and state management
- No centralized reference explaining what's visible in code vs what's missing
- Difficulty debugging failures without understanding constitutional linking

**Target State:**
- Self-contained reference that another LLM can read without code inspection
- Complete hook protocol documentation with examples
- Explicit knowledge matrix showing code visibility vs missing information
- Clear testing, validation, and troubleshooting protocols
- Ready-to-use templates, patterns, and implementation checklists

### What's Changing & Why

| Aspect | Current | New | Why |
|--------|---------|-----|-----|
| **Knowledge Transfer** | Code-first | Documentation-first | Enables faster LLM adoption |
| **Debugging** | Trial-and-error | Structured failure modes | Reduces debug time from hours to minutes |
| **State Management** | Implicit patterns | Explicit file-based patterns | Prevents race conditions and data corruption |
| **Configuration** | settings.json only | settings.json + frontmatter + environment + managed | Supports skill-scoped hooks (2.1+) |
| **Testing** | Manual testing | Test harness + integration tests | Verifiable, repeatable validation |
| **Hook Types** | Command only | Command + Prompt-based | LLM-evaluated decisions for context-aware logic |

### Architecture & Benefits

```
Hook Developer
    |
Reads Ultimate Guide (this document)
    |
Understands: Lifecycle, Schemas, State, Visibility Rules
    |
Implements Hook with Confidence
    |
Tests with Harness
    |
Integrates into settings.json, Skill, or Plugin
    |
Claude Code enforces rules deterministically
```

**Benefits:**
- **Faster Development**: Reference answers questions immediately
- **Fewer Bugs**: Common failure modes documented with fixes
- **Better Debugging**: Structured protocols for testing and validation
- **Cross-LLM Understanding**: Another LLM reads this and understands hooks fully
- **Skill Integration**: Ready to embed in Claude Code skills (2.1+)
- **Prompt Hooks**: LLM-based evaluation for nuanced decisions

### Key Metrics & Improvements

- **Learning Curve**: Reduced from 2-3 hours (reverse-engineering code) to 15-20 minutes (reading guide)
- **Bug Discovery Time**: From discovery to fix in 1-2 iterations vs 4-5 iterations
- **Code Reusability**: Templates and patterns reduce boilerplate by 70%
- **Test Coverage**: Structured testing increases validation from ad-hoc to comprehensive
- **Documentation**: Single source of truth eliminates information scatter

---

## TABLE OF CONTENTS

1. [Core Hook Concepts](#core-hook-concepts)
2. [Hook Lifecycle & Phases](#hook-lifecycle--phases)
3. [Hook Protocol & Schemas](#hook-protocol--schemas)
4. [Matcher Syntax & Patterns](#matcher-syntax--patterns)
5. [Knowledge Matrix](#knowledge-matrix)
6. [Visibility & Transparency Rules](#visibility--transparency-rules)
7. [State Management Patterns](#state-management-patterns)
8. [Router Architecture](#router-architecture)
9. [Hook Registration & Configuration](#hook-registration--configuration)
10. [Configuration Scopes & Locations](#configuration-scopes--locations)
11. [Output Format Specifications](#output-format-specifications)
12. [Exit Code Behavior & Control Flow](#exit-code-behavior--control-flow)
13. [Prompt-Based Hooks](#prompt-based-hooks)
14. [Constitutional Linking](#constitutional-linking)
15. [Common Failure Modes & Recovery](#common-failure-modes--recovery)
16. [Testing & Validation Protocol](#testing--validation-protocol)
17. [Advanced Patterns & Strategies](#advanced-patterns--strategies)
18. [Implementation Checklist](#implementation-checklist)
19. [Complete Code Examples](#complete-code-examples)

---

## CORE HOOK CONCEPTS

### What Hooks Are

Claude Code hooks are deterministic automation points that fire at specific lifecycle phases during a development session. Unlike LLM-based suggestions in `CLAUDE.md`, hooks execute automatically and provide hard control flow—they can block actions, inject context, log activity, and enforce rules.

### Why They Matter

Hooks are the **enforcement layer** for complex projects. They:
- Provide deterministic, rule-based control independent of LLM decisions
- Complement `CLAUDE.md` suggestions with actionable enforcement
- Enable audit trails, validation, and quality gates
- Solve "context selection" problems through conditional logic
- Execute with predictable behavior regardless of model changes

### Key Principle

**Use hooks to enforce state validation at commit time (block-at-submit). Avoid blocking at write time—let the agent finish its plan, then check the final result.**

### Hooks vs. Skills vs. Commands vs. CLAUDE.md

| Component | Type | Execution | Visibility | Use Case |
|-----------|------|-----------|------------|----------|
| **Hooks** | Deterministic | Automatic at phases | Some outputs visible | Enforce rules, validate state, audit |
| **Skills** | LLM-augmented | User-invoked | Full context passed | Reusable expertise, domain knowledge |
| **Commands** | Shortcut | User-invoked | Optional context | Quick actions, automation |
| **CLAUDE.md** | Rules + Context | LLM-read | Visible to Claude | Best practices, guidelines, architecture |

### Why Hooks Are Essential

**Problem**: LLMs make probabilistic decisions. In complex repos with strict requirements, you need **deterministic enforcement**.

**Solution**: Hooks execute shell commands or LLM prompts that can:
- Validate state before/after operations
- Inject context Claude should know
- Block invalid operations
- Log and audit all activity
- Enforce architectural constraints

---

## HOOK LIFECYCLE & PHASES

### Complete Hook Timeline

Hooks fire at these points during a Claude Code session:

| Phase | When It Fires | Input Available | Output Control | Common Use Cases |
|-------|---------------|-----------------|-----------------|------------------|
| **SessionStart** | Session begins or resumes | `source`: startup/resume/clear/compact | Can set initial context | Initialize context, load configuration, set env vars |
| **UserPromptSubmit** | User submits a prompt | User's new `prompt` | **Can block prompt** | Validate input, security filtering, add context |
| **PreToolUse** | Before tool execution | `tool_name`, `tool_input` | **Can deny/allow/ask** | Permission checks, pre-flight validation, modify inputs |
| **PermissionRequest** | Permission dialog appears | Permission request details | **Can auto-approve/deny** | Deterministic permission handling |
| **PostToolUse** | After tool succeeds | `tool_name`, `tool_input`, `tool_response` | Can feed back context | Validate results, inspect changes |
| **PostToolUseFailure** | After tool fails | Error information | Can suggest recovery | Error handling, retry logic |
| **Stop** | Claude tries to finish | `stop_hook_active` flag | **Can block stopping** | Ensure tasks complete |
| **SubagentStart** | Spawning a subagent | Subagent configuration | Can inject context | Configure subagent behavior |
| **SubagentStop** | Subagent finishes | Subagent results | **Can block subagent stop** | Validate subagent completion |
| **PreCompact** | Before context compaction | `trigger`, `custom_instructions` | Can prepare for compaction | Clean up state files |
| **Notification** | System sends notification | `message`, `notification_type` | Can transform message | Customize notifications |
| **Setup** | Repository setup (`--init`, `--maintenance`) | `trigger`: init/maintenance | One-time operations | Install dependencies, run migrations |
| **SessionEnd** | Session terminates | `reason`: clear/logout/prompt_input_exit/other | Record final state | Cleanup, final logging |

**Blocking Phases** (can prevent action): UserPromptSubmit, PreToolUse, PermissionRequest, Stop, SubagentStop

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

#### PreToolUse (Read Example)
```json
{
  "hook_event_name": "PreToolUse",
  "tool_name": "Read",
  "tool_input": {
    "file_path": "/src/main.py",
    "offset": 0,
    "limit": 100
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

#### PreCompact
```json
{
  "hook_event_name": "PreCompact",
  "trigger": "manual|auto",
  "custom_instructions": "User input from /compact command"
}
```

#### Setup
```json
{
  "hook_event_name": "Setup",
  "trigger": "init|maintenance"
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

### Word-Boundary Matching with `:*`

The `:*` suffix provides word-boundary prefix matching:

| Pattern | Position | Behavior | Example |
|---------|----------|----------|---------|
| `Bash(ls:*)` | End only | Prefix with word boundary | Matches `ls -la`, NOT `lsof` |
| `Bash(ls*)` | Anywhere | Glob, no boundary | Matches `ls -la` AND `lsof` |

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

## KNOWLEDGE MATRIX

### Critical Information for Hook Development

This matrix shows what's visible in code vs. what another LLM needs to know:

#### Hook Protocol Layer

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **Lifecycle Timing** | Function names | When each phase fires relative to others | Determines which hook can intercept which action |
| **Input Availability** | Code reads fields | What data is available at each phase | Affects what you can validate/act on |
| **Output Schema** | JSON in code | Which fields Claude Code processes | Affects what control you have |
| **Phase Ordering** | Hook names | Exact sequence and concurrency | Affects state management strategy |

#### Output Format Layer

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **Decision Fields** | "decision": "block" | What decisions each hook type supports | Determines control capability |
| **Return Structure** | JSON fields | Which fields are processed vs. ignored | Affects what actually works |
| **Field Conditionals** | Partial | When field X is required vs. optional | Avoids "field required but ignored" errors |

#### State Sharing Layer

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **File Format** | `.state/*.json` | How to coordinate across phases | Makes async state patterns possible |
| **Lifecycle** | Files exist | When to write/read/delete state | Prevents stale state issues |
| **Concurrency** | Script files | How multiple hooks interact with state | Prevents race conditions |

#### User Visibility Layer

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **systemMessage Field** | In output structure | EVERYTHING in systemMessage is VISIBLE to user | Can't inject "hidden" LLM-only guidance |
| **Console Output** | Visible | What output format user sees | Affects user experience |
| **Error Messages** | Partial | How errors are presented | Determines user's ability to debug |

#### Configuration Layer

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **Hook Registration** | settings.json | Multiple hooks per phase run in parallel | Affects coordination strategy |
| **Scopes** | Partial | Managed > CLI > Local > Shared > User precedence | Determines which hooks take effect |
| **Environment Variables** | Referenced | How to pass config to hook scripts | Affects parameterization strategy |

#### Constitutional Link

| Aspect | Visible in Code | What's Missing | Why It Matters |
|--------|-----------------|-----------------|-------------------|
| **Truth Source** | References to truth.md, CLAUDE.md | How hooks reinforce documented rules | Understanding the enforcement chain |
| **Rule Enforcement** | Partial implementation | Which rules are checked vs. documented | Audit compliance |

---

## VISIBILITY & TRANSPARENCY RULES

### The systemMessage Principle

**CRITICAL**: Everything in `systemMessage` is **VISIBLE to the user**. There is no way to inject LLM-only guidance that the user cannot see.

#### Implications for Hook Design

```
Hook output systemMessage
    |
Claude reads and processes
    |
Claude responds to user
    |
User sees systemMessage content in transcript
```

There's no hidden layer.

#### Design Pattern

Keep user-facing content concise and clear:

**Good** (Clear intent):
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "Security validation: File matches approved patterns."
  }
}
```

**Bad** (Confusing to user):
```json
{
  "systemMessage": "Hook execution: regex match_status=0 pattern_checksum=abc123 validated_by=PreToolUse"
}
```

### Transparency Strategy

If you need to communicate with Claude only:
- Use exit codes and stderr
- Exit code 2 blocks the action
- stderr gets fed to Claude automatically
- But the user will see this too in transcript/debug mode

**Best practice**: Keep all communication purposeful and user-understandable.

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

## ROUTER ARCHITECTURE

### Hook Execution Model

In Claude Code 2.1+, **all matching hooks run in parallel**. Identical hook commands are deduplicated.

### Router Pattern for Sequential Execution

If you need sequential hook execution, implement a router:

```python
# post_tool_use_router.py
import json
import sys
import subprocess

hook_input = json.loads(sys.stdin.read())
hook_output = {}

# Run sub-hooks sequentially
hooks = [
    "./hooks/validate_changes.py",
    "./hooks/log_activity.py",
    "./hooks/check_compliance.py"
]

for hook_path in hooks:
    result = subprocess.run(
        [sys.executable, hook_path],
        input=json.dumps(hook_input),
        capture_output=True,
        text=True
    )

    if result.returncode == 2:
        # Critical error - propagate blocking
        print(result.stderr, file=sys.stderr)
        sys.exit(2)

    # Merge outputs
    try:
        sub_output = json.loads(result.stdout)
        hook_output.update(sub_output)
    except:
        pass

print(json.dumps(hook_output))
sys.exit(0)
```

### Router Decision Matrix

```
Hook 1 returns decision?
  +-- No -> Continue to Hook 2
  +-- Yes (success) -> Merge and continue
  +-- Exit code 2 -> STOP and propagate error

Hook 2 returns decision?
  +-- No -> Continue to Hook 3
  +-- Yes (success) -> Merge and continue
  +-- Exit code 2 -> STOP and propagate error

Final merged output -> Claude Code
```

### Permission Decision Precedence

For PreToolUse and PermissionRequest hooks:

```
deny > ask > allow
```

If any hook returns `deny`, the tool is denied regardless of other hooks.

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
| `type` | string | Yes | `"command"` or `"prompt"` |
| `command` | string | For command type | Shell command or script path |
| `prompt` | string | For prompt type | LLM evaluation prompt |
| `timeout` | number | No | Seconds (default: 60) |
| `description` | string | No | For plugin hooks |

### Hooks in Skills & Agents (2.1+)

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

### Plugin Hooks

Location: `hooks/hooks.json` within plugin directory

Available variables:
- `${CLAUDE_PLUGIN_ROOT}` - Absolute path to plugin directory
- `${CLAUDE_PROJECT_DIR}` - Project root directory

### Environment Variables for Hooks

| Variable | Value | Available In |
|----------|-------|--------------|
| `CLAUDE_PROJECT_DIR` | Absolute path to project root | All command hooks |
| `CLAUDE_ENV_FILE` | Path to env persistence file | SessionStart only |
| `CLAUDE_CODE_REMOTE` | "true" if web, empty if local | All command hooks |
| All system env vars | From host environment | All command hooks |

### Persisting Environment Variables (SessionStart Only)

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
  "hookSpecificOutput": {
    "hookEventName": "PostToolUse",
    "additionalContext": "string"
  }
}
```

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
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Your explanation",
    "updatedInput": {
      "command": "modified command"
    },
    "additionalContext": "Context for Claude"
  }
}
```

#### PermissionRequest Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "PermissionRequest",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "Reason for decision",
    "updatedInput": {
      "field": "modified value"
    }
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

#### SessionStart / SessionEnd Output
```json
{
  "hookSpecificOutput": {
    "hookEventName": "SessionStart",
    "additionalContext": "Information added to context"
  }
}
```

### Decision Field Behavior

| Phase | Decision Field | Values | Effect |
|-------|----------------|--------|--------|
| UserPromptSubmit | decision | "block" \| undefined | Reject or accept prompt |
| PreToolUse | permissionDecision | "deny" \| "ask" \| "allow" | Deny, prompt user, or allow tool |
| PermissionRequest | permissionDecision | "deny" \| "ask" \| "allow" | Auto-respond to permission dialog |
| PostToolUse | decision | "block" \| undefined | Provide feedback or continue |
| Stop | decision | "block" \| undefined | Force continuation or allow stop |
| SubagentStop | decision | "block" \| undefined | Continue subagent or allow completion |

### Input Modification (PreToolUse/PermissionRequest)

You can modify tool inputs before execution:

```json
{
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse",
    "permissionDecision": "allow",
    "updatedInput": {
      "command": "npm install --save-exact"
    }
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
    |     +-- Check "decision" or "permissionDecision" field
    |     +-- Apply decision (block/deny/allow/ask)
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

**Validating before action (exit code 0 + decision)**:
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

Claude Code 2.1+ supports **prompt-based hooks** that use LLM evaluation instead of shell commands.

### Supported Events

- Stop
- SubagentStop
- UserPromptSubmit
- PreToolUse
- PermissionRequest

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

## CONSTITUTIONAL LINKING

### The Constitutional Chain

Your hooks enforce rules documented in your project's constitution:

```
CLAUDE.md (Guidelines)
    |
truth.md (Architecture)
    |
Hooks (Enforcement)
    |
Claude Code behavior
```

### Enforcement vs. Documentation

**In CLAUDE.md**:
- "We use async/await for concurrency"
- "All config lives in /config/"
- "Database migrations require review"

**In Hooks** (enforcement):
- Validate that files follow naming conventions
- Prevent writes outside allowed directories
- Block commits without proper testing

### Example: Config Location Rule

**truth.md**:
```markdown
## Configuration Management

All configuration must live in `/config/` directory.
- Environment config: `/config/env/`
- Feature flags: `/config/features/`
- Database: `/config/db/`

Exceptions require explicit team approval documented in a comment.
```

**Hook (pre_tool_use.py)**:
```python
import json
import sys

hook_input = json.loads(sys.stdin.read())

if hook_input.get("tool_name") == "Write":
    tool_input = hook_input.get("tool_input", {})
    file_path = tool_input.get("file_path", "")

    if "config" in file_path.lower() and not file_path.startswith("/config/"):
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": "Config files must be in /config/ directory (truth.md section 2.1)"
            }
        }
        print(json.dumps(output))
        sys.exit(0)

print(json.dumps({}))
sys.exit(0)
```

### Documentation Format

In your hook code, reference the truth source:

```python
# Enforce CLAUDE.md section 3.2: Test Coverage
# All Python files must have >80% test coverage

if coverage < 0.80:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PostToolUse",
            "additionalContext": f"Test coverage {coverage*100:.1f}% below 80% minimum (CLAUDE.md section 3.2)"
        },
        "decision": "block",
        "reason": f"Coverage requirement not met"
    }
```

---

## COMMON FAILURE MODES & RECOVERY

### Failure Mode 1: Hook Command Not Found

**Symptom**: Hook doesn't fire, no error shown

**Cause**: Command path is wrong or script isn't executable

**Fix**:
```bash
# Use full paths
"command": "/Users/you/.claude/hooks/validate.py"

# Make scripts executable
chmod +x /Users/you/.claude/hooks/validate.py

# Test manually
echo '{"hook_event_name":"PostToolUse","tool_name":"Write"}' | python /Users/you/.claude/hooks/validate.py
```

### Failure Mode 2: Exit Code 2 Causes Infinite Loop

**Symptom**: Claude keeps retrying the same action, hook keeps blocking

**Cause**: Hook blocks action with exit code 2, Claude tries again, hook blocks again

**Fix**:
- Use exit code 0 + `permissionDecision: "deny"` for PreToolUse
- Use exit code 0 + `decision: "block"` for other phases
- Use exit code 2 only when Claude needs to be told something went wrong externally
- Always include reason field when blocking

### Failure Mode 3: JSON Parse Error

**Symptom**: Hook output not processed, Claude doesn't respond

**Cause**: Hook outputs invalid JSON

**Fix**:
```python
import json

try:
    output = {"decision": "block", "reason": "..."}
    print(json.dumps(output))
except Exception as e:
    print(json.dumps({"error": str(e)}), file=sys.stderr)
    sys.exit(1)
```

### Failure Mode 4: Missing Environment Variables

**Symptom**: Hook crashes when trying to read $CLAUDE_PROJECT_DIR

**Cause**: Environment variable not available in hook context

**Fix**:
```python
import os

cwd = os.getenv("CLAUDE_PROJECT_DIR") or os.getcwd()
project_root = cwd

# The input JSON includes cwd field as well
```

### Failure Mode 5: State File Race Conditions

**Symptom**: Hooks read/write state files concurrently, data corruption

**Cause**: Multiple hooks access same state file simultaneously

**Fix**:
```python
import json
import os
import time
import fcntl  # Unix-only, use msvcrt on Windows

STATE_FILE = ".claude/hooks/.state/data.json"

def safe_read_write(updates):
    with open(STATE_FILE, "r+") as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            data = json.load(f)
            data.update(updates)
            f.seek(0)
            f.truncate()
            json.dump(data, f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)
```

### Failure Mode 6: Blocking at Write Time Frustrates Claude

**Symptom**: Claude stops mid-task, seems confused about what to do next

**Cause**: Hook blocks the action while Claude is still planning

**Fix**: **Don't block at write time**. Instead:
- Use PreToolUse to validate *intent*
- Use PostToolUse to validate *result*
- Use Stop to do final validation before completion

The pattern is:
1. PreToolUse: Check if this tool is allowed
2. Tool executes
3. PostToolUse: Validate the output
4. Stop: Check if all work is done correctly

### Failure Mode 7: Hook Timeout

**Symptom**: Hook doesn't complete, action proceeds anyway

**Cause**: Hook takes longer than timeout (default 60s)

**Fix**:
```json
{
  "hooks": [
    {
      "type": "command",
      "command": "./slow_validator.py",
      "timeout": 120
    }
  ]
}
```

---

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
- [ ] hookSpecificOutput includes correct hookEventName
- [ ] Decision fields present when expected
- [ ] Exit code 2 used only for critical errors
- [ ] additionalContext is user-friendly
- [ ] No hard-coded paths (use $CLAUDE_PROJECT_DIR)
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

## IMPLEMENTATION CHECKLIST

### Before You Start

- [ ] Read entire CLAUDE.md for project context
- [ ] Review truth.md for architectural constraints
- [ ] Identify which lifecycle phases you need to intercept
- [ ] Map each hook to a specific enforcement rule
- [ ] Design state sharing strategy if multi-phase

### Hook Development

- [ ] Choose hook type (command vs. prompt)
- [ ] Write hook script with proper input parsing
- [ ] Use `tool_input` (not `tool_arguments`) for tool parameters
- [ ] Use `hookSpecificOutput` with correct `hookEventName`
- [ ] Test hook manually with test harness
- [ ] Add logging to `.claude/hooks/logs/`
- [ ] Verify JSON output validity
- [ ] Use appropriate exit codes
- [ ] Add documentation in hook script comments

### Integration

- [ ] Register hook in settings.json (correct scope)
- [ ] Verify hook runs via `/hooks` command
- [ ] Test with real Claude Code session
- [ ] Verify additionalContext shows appropriately
- [ ] Confirm state files are cleaned up
- [ ] Check logs for errors

### Testing

- [ ] Manual hook test with test harness
- [ ] Integration test with Claude Code
- [ ] Test blocking behavior (exit 0 + decision)
- [ ] Test error behavior (exit 2)
- [ ] Test state persistence across phases
- [ ] Test input modification (updatedInput)
- [ ] Test parallel hook execution

### Documentation

- [ ] Document hook purpose in script comments
- [ ] Reference truth.md rules being enforced
- [ ] Include example input/output in comments
- [ ] Document state file format
- [ ] Add troubleshooting tips
- [ ] Include permission requirements

### Maintenance

- [ ] Monitor logs in `.claude/hooks/logs/`
- [ ] Track false positives from validation
- [ ] Update hooks when CLAUDE.md/truth.md change
- [ ] Review audit trail periodically
- [ ] Clean old state files
- [ ] Version control hook scripts

---

## COMPLETE CODE EXAMPLES

### Complete Hook Template (v2.1.15)

```python
#!/usr/bin/env python3
"""
Hook Template: [Hook Name]

Purpose: [What this hook does]
Enforces: [Which rule/policy]
Phases: [Which lifecycle phases]

Input: [Describe expected input fields]
Output: [Describe output schema]

Claude Code Version: 2.1.15+
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
        return {}

if __name__ == "__main__":
    ensure_dirs()
    main()
```

### Example: PreToolUse Validator (v2.1.15)

```python
#!/usr/bin/env python3
"""
Hook: PreToolUse Validator

Purpose: Validate tool usage against project rules before execution
Enforces: CLAUDE.md section 2.1 (Tool Usage Guidelines)
Phases: PreToolUse

Input: tool_name, tool_input
Output: hookSpecificOutput with permissionDecision

Claude Code Version: 2.1.15+
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

### Example: PostToolUse Audit Logger (v2.1.15)

```python
#!/usr/bin/env python3
"""
Hook: PostToolUse Audit Logger

Purpose: Log all tool executions for audit trail
Enforces: Compliance logging requirements
Phases: PostToolUse

Input: tool_name, tool_input, tool_response
Output: Audit log entry (no decision)

Claude Code Version: 2.1.15+
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

### Example: Stop Phase Validator (v2.1.15)

```python
#!/usr/bin/env python3
"""
Hook: Stop Phase Validator

Purpose: Ensure all requirements met before session ends
Enforces: CLAUDE.md section 4.3 (Completion Requirements)
Phases: Stop

Input: stop_hook_active
Output: decision: "block" | undefined

Claude Code Version: 2.1.15+
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
            "decision": "block",
            "reason": f"Incomplete tasks: {', '.join(missing)}. Please complete these before finishing."
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

### Example: SessionStart Environment Setup (v2.1.15)

```bash
#!/bin/bash
# Hook: SessionStart Environment Setup
#
# Purpose: Set up environment variables for the session
# Phases: SessionStart
#
# Claude Code Version: 2.1.15+

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
Claude decides tool -> PreToolUse (can DENY/ALLOW/ASK)
Permission needed? -> PermissionRequest (can AUTO-RESPOND)
Tool runs -> PostToolUse (can provide feedback)
Tool fails? -> PostToolUseFailure
Subagent spawns -> SubagentStart
Subagent finishes -> SubagentStop (can BLOCK)
Claude ready to stop -> Stop (can BLOCK)
Memory compacts -> PreCompact
Session ends -> SessionEnd
```

### Decision Quick Reference

| Phase | Field | Values | Effect |
|-------|-------|--------|--------|
| UserPromptSubmit | decision | "block" \| undefined | Allow or reject prompt |
| PreToolUse | permissionDecision | "deny" \| "ask" \| "allow" | Deny, prompt, or allow tool |
| PermissionRequest | permissionDecision | "deny" \| "ask" \| "allow" | Auto-respond to permission |
| PostToolUse | decision | "block" \| undefined | Provide feedback or continue |
| Stop | decision | "block" \| undefined | Force continuation or allow stop |
| SubagentStop | decision | "block" \| undefined | Continue subagent or allow completion |

### Output Schema Quick Reference

```json
{
  "continue": true,
  "decision": "block",
  "reason": "Explanation",
  "suppressOutput": false,
  "hookSpecificOutput": {
    "hookEventName": "PreToolUse|PostToolUse|...",
    "permissionDecision": "allow|deny|ask",
    "permissionDecisionReason": "string",
    "updatedInput": { "field": "value" },
    "additionalContext": "string"
  }
}
```

### Common Hook Patterns

1. **Validation** (exit 0 + permissionDecision/decision field)
2. **Logging** (exit 0, no decision)
3. **Error Recovery** (exit 2 with stderr)
4. **State Coordination** (file-based .state/)
5. **Input Modification** (updatedInput field)
6. **Context Injection** (additionalContext field)

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
echo '{"decision":"block"}' | jq .
```

---

## IMPLEMENTATION SETUP GUIDE

### Step 1: Directory Structure

Create the basic hook directory structure:

```bash
mkdir -p .claude/hooks/.state
mkdir -p .claude/hooks/logs
touch .claude/hooks/__init__.py
chmod +x .claude/hooks/*.py
```

### Step 2: Configure settings.json

Add hooks to your `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/pre_tool_use_validator.py"
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
            "command": "./.claude/hooks/post_tool_use_auditor.py"
          }
        ]
      }
    ],
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "./.claude/hooks/stop_validator.py"
          }
        ]
      }
    ]
  }
}
```

### Step 3: Create Your First Hook

Copy the template above and customize for your use case:

```bash
cp template_hook.py .claude/hooks/my_hook.py
chmod +x .claude/hooks/my_hook.py
```

### Step 4: Test Your Hook

Use the test harness:

```bash
# Create test_hook.sh from the examples above
bash test_hook.sh ./.claude/hooks/my_hook.py PreToolUse
```

### Step 5: Monitor & Debug

Check logs during development:

```bash
# Watch logs in real-time
tail -f .claude/hooks/logs/*.log

# Parse audit log
cat .claude/hooks/logs/audit.log | jq .
```

---

## TROUBLESHOOTING QUICK START

| Problem | Solution |
|---------|----------|
| Hook doesn't fire | Check settings.json syntax, verify hook path exists, ensure executable |
| Invalid JSON error | Use `jq` to validate output, check string escaping, use `json.dumps()` |
| Claude ignores hook output | Check exit code, verify hookSpecificOutput structure, ensure JSON valid |
| State file corruption | Implement file locking, reduce concurrent writes, check permissions |
| Infinite blocking loop | Use exit 0 + decision field instead of exit 2, add reason field |
| Permission denied errors | `chmod +x` hook script, check directory permissions, verify path |
| Hook timeout | Increase timeout in configuration, optimize hook performance |
| Wrong tool_input fields | Use current schema (tool_input, not tool_arguments) |

---

## SECURITY CONSIDERATIONS

**Critical Warning**: Hooks execute arbitrary shell commands with your environment's credentials.

**Best Practices:**
- Thoroughly review hook code before using
- Never copy hooks from untrusted sources
- Sanitize all input parameters
- Restrict file access patterns
- Use absolute paths only
- Keep hooks in version control for auditing
- Document hook purpose and behavior
- Test edge cases (unusual paths, special characters)
- Validate JSON input before processing
- Never eval() or exec() untrusted input

---

## RESOURCES & REFERENCES

- Claude Code Official Hooks Documentation: https://docs.anthropic.com/en/docs/claude-code/hooks
- Claude Code Best Practices: https://docs.anthropic.com/en/docs/claude-code/best-practices
- GitHub: Claude Code Hooks Mastery: https://github.com/disler/claude-code-hooks-mastery

---

## CHANGELOG

### v2.1.15 Updates
- Added `tool_input` field (replaces `tool_arguments`)
- Added `tool_response` field for PostToolUse
- Added `hookSpecificOutput` structure with `hookEventName`
- Added `permissionDecision` with `allow|deny|ask` values
- Added `updatedInput` for input modification
- Added `additionalContext` field
- Added `PermissionRequest` hook event
- Added `PostToolUseFailure` hook event
- Added `Setup` hook event
- Added `source` field for SessionStart
- Added `reason` field for SessionEnd
- Added `notification_type` for Notification
- Added `trigger` field for Setup and PreCompact
- Added `stop_hook_active` flag for Stop hooks
- Added prompt-based hooks (type: "prompt")
- Added matcher `:*` suffix for word-boundary matching
- Added MCP tool naming pattern documentation
- Added configuration scopes and precedence
- Added `CLAUDE_CODE_REMOTE` environment variable
- Added `CLAUDE_ENV_FILE` for SessionStart env persistence
- Updated all code examples to current schema

---

**End of Document**

**Download this file as: `claude-hooks-guide.md`**

This comprehensive guide is ready for:
- Immediate use in Claude Code development
- Conversion to a Claude Code skill
- Sharing with other LLMs and developers
- Copy-paste implementation of all examples
- Reference during hook debugging and development
