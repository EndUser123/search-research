# Claude Code Hooks – Operational Guide (v2.1.31)

**Latest version**: Claude Code v2.1.31 (February 2026)

Practical, implementation-focused guide for building reliable hook systems in Claude Code. Covers all 13 hook events, three hook handler types (command, prompt, agent), and async execution patterns.

---

## Table of Contents

1. [Core Mental Model](#core-mental-model)
2. [Hook Events Reference](#hook-events-reference)
3. [Hook Handler Types](#hook-handler-types)
4. [Configuration and Setup](#configuration-and-setup)
5. [UserPromptSubmit Deep Dive](#userpromptsubmit-deep-dive)
6. [Master Script Pattern](#master-script-pattern)
7. [Async Hooks in Practice](#async-hooks-in-practice)
8. [Decision Control & Output](#decision-control--output)
9. [Windows-Specific Operational Notes](#windows-specific-operational-notes)
10. [Debugging and Testing](#debugging-and-testing)
11. [Best Practices Checklist](#best-practices-checklist)

---

## Core Mental Model

Claude Code hooks are **event-driven middleware** that intercept lifecycle points in your Claude session. When an event fires, Claude spawns hook handlers (shell commands, LLM prompts, or agents) that can:

- **Observe** actions (log, audit, notify)
- **Validate** decisions (block dangerous operations)
- **Shape** interactions (inject context, modify tool input)
- **Control flow** (block/allow/continue)

All matching hooks for an event **run in parallel**; there is no built-in sequencing. Exit codes and JSON output determine the outcome.

**Key principle**: Hooks are the **hard rails**. They always fire, consistently execute, and are version-controlled. Use them for invariants, not suggestions.

---

## Hook Events Reference

### Complete Lifecycle (13 Events)

| # | Event | When it fires | Blockable | Matcher support | Best for |
|---|-------|---------------|-----------|-----------------|----------|
| 1 | **SessionStart** | Session begins/resumes | No | `startup`, `resume`, `clear`, `compact` | Load project context, setup env vars |
| 2 | **UserPromptSubmit** | User submits prompt (before Claude sees it) | **Yes** | None (always fires) | Validate, inject rules, block bad prompts |
| 3 | **PreToolUse** | Before tool executes | **Yes** | Tool names (Bash, Edit, Write, Read, Glob, Grep, WebFetch, Task, etc.) + MCP patterns | Security gates, auto-approve, modify input |
| 4 | **PermissionRequest** | Permission dialog appears | **Yes** | Tool names | Auto-grant safe ops, deny risky ones |
| 5 | **PostToolUse** | After tool succeeds | No | Tool names | Format code, log actions, verify output |
| 6 | **PostToolUseFailure** | After tool fails | No | Tool names | Log errors, send alerts, suggest fixes |
| 7 | **Notification** | Claude sends notification | No | `permission_prompt`, `idle_prompt`, `auth_success`, `elicitation_dialog` | Desktop alerts, forwarding to third-party |
| 8 | **SubagentStart** | Subagent spawned (Task tool) | No | Agent types (Bash, Explore, Plan, or custom) | Inject subagent context, track spawning |
| 9 | **SubagentStop** | Subagent finishes | **Yes** | Agent types | Verify completion, block if needed |
| 10 | **Stop** | Main agent finishes responding | **Yes** | None (always fires) | Check if work is done, force continuation |
| 11 | **PreCompact** | Before context compaction | No | `manual`, `auto` | Log pre-compact state, notify user |
| 12 | **SessionEnd** | Session terminates | No | `clear`, `logout`, `other` | Cleanup, save session data |

---

## Hook Handler Types

### 1. Command Hooks (`type: "command"`)

Executes a shell command. Most flexible and most common.

```json
{
  "type": "command",
  "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/my-hook.sh",
  "timeout": 120,
  "async": false
}
```

**Input**: JSON on stdin (event-specific schema)  
**Output**: Exit code + stdout (parsed as JSON or plain text) + stderr  
**Timeout**: Default 600s; configurable  
**Async**: `true` = fire-and-forget (output ignored)

**Exit codes**:
- **0** = success; stdout is processed (plain text appended to context for `UserPromptSubmit`; JSON parsed for decisions)
- **2** = blocking error; stderr fed back to Claude as feedback
- **Other** = non-blocking error; stderr shown in verbose mode only

### 2. Prompt Hooks (`type: "prompt"`)

Delegates decision-making to a Claude model (Haiku by default). Single LLM turn.

```json
{
  "type": "prompt",
  "prompt": "Is this command safe? Respond with {\"ok\": true/false, \"reason\": \"...\"}",
  "model": "haiku",
  "timeout": 30
}
```

**Input**: `$ARGUMENTS` placeholder replaced with hook input JSON  
**Output**: LLM response as JSON: `{"ok": true/false, "reason": "..."}`  
**Timeout**: Default 30s  
**Async**: Not supported (always sync)

**Model options**: Use fast model by default; specify `"model": "sonnet"` for complex reasoning

### 3. Agent Hooks (`type: "agent"`)

Spawns a subagent with tool access (Read, Grep, Glob, etc.). Multi-turn LLM + tools.

```json
{
  "type": "agent",
  "prompt": "Verify tests pass. $ARGUMENTS",
  "timeout": 120
}
```

**Input**: `$ARGUMENTS` placeholder + subagent tools  
**Output**: JSON: `{"ok": true/false, "reason": "..."}`  
**Timeout**: Default 60s (can run longer)  
**Max turns**: 50  
**Async**: Not supported

---

## Configuration and Setup

### Configuration Locations (Priority Order)

1. **`~/.claude/settings.json`** – User scope, all projects
2. **`.claude/settings.json`** – Project scope, shared via git (**recommended**)
3. **`.claude/settings.local.json`** – Project scope, gitignored
4. **Managed policy** – Enterprise-wide (admin-controlled)
5. **Plugin `hooks/hooks.json`** – Bundled with plugin
6. **Skill/Agent frontmatter** – Scoped to component (**recommended for skill-specific hooks**)

**Best practice**: Use **skill frontmatter hooks** for skill-specific workflow enforcement. Use **project `.claude/settings.json`** for repo-wide policies; reserve global for cross-project policies.

### Frontmatter Hooks (Claude Code 2.1+)

**Skills and agents can define hooks directly in their SKILL.md frontmatter.** This is the recommended pattern for skill-specific behavior enforcement.

**Why frontmatter hooks:**
- **Self-contained**: Hook travels with the skill; no external config required
- **Scoped**: Only runs when skill is invoked; no global side effects
- **Distributable**: Skills with hooks work out-of-box when shared
- **Auto-discovery**: No settings.json editing required for skill users

**Example frontmatter hook in a skill:**
```yaml
---
name: task
description: Task orchestration
hooks:
  PostToolUse:
    - type: prompt
      prompt: |
        Verify /task list workflow was executed completely:
        1. TaskList() was called
        2. Results were filtered by terminal_id
        3. /search was called for context

        If any step was skipped, return {"ok": false, "reason": "..."}
      model: haiku
      timeout: 30
user-invocable: true
---
```

**Supported events in frontmatter:**
- `UserPromptSubmit` – Validate/modify before skill executes
- `PreToolUse` – Intercept tool calls during skill execution
- `PostToolUse` – Verify after tool completes (workflow enforcement)
- `Stop` – Prevent incomplete skill termination
- `SubagentStart` / `SubagentStop` – Subagent lifecycle

**Frontmatter hook handler types:**
- `type: "prompt"` – LLM decision (fast, no tool access)
- `type: "agent"` – Full agent with tool access (slow, powerful)
- `type: "command"` – Shell command (not recommended in frontmatter)

**When to use frontmatter hooks vs settings.json:**

| Scenario | Recommended approach |
|----------|---------------------|
| Skill-specific workflow enforcement | **Frontmatter hooks** in SKILL.md |
| Project-wide policies (linting, security) | `.claude/settings.json` |
| Cross-project standards (all repos) | `~/.claude/settings.json` |
| Temporary experiments | `.claude/settings.local.json` |

### Basic Hook Configuration

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "matcher": null,
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master.py",
            "async": false,
            "timeout": 60
          }
        ]
      }
    ],
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "prettier --write",
            "async": true,
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

### Using `/hooks` Interactive Menu

```bash
claude code
/hooks
```

- View all hooks by event
- Add/delete hooks interactively
- Changes take effect immediately
- No JSON editing required

---

## UserPromptSubmit Deep Dive

### Why UserPromptSubmit Matters

`UserPromptSubmit` fires **before Claude sees any prompt**. This makes it the first line of defense and enhancement:

- **Position**: Injected context lands closest to user prompt, highest attention.
- **Timing**: Runs before LLM processing, so you can block, rewrite, or augment.
- **Scope**: Fires on every prompt in a session, keeping invariants always present.

### Input Schema

```json
{
  "session_id": "abc123",
  "transcript_path": "/Users/.../.claude/projects/.../session.jsonl",
  "cwd": "/repo/root",
  "permission_mode": "default",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Write a function to calculate factorial"
}
```

Parse with: `jq -r '.prompt'` (bash) or `data = json.load(sys.stdin)` (Python).

### Output Options

#### 1. Plain Text stdout (exit 0)

Simplest: appends text directly to Claude's context.

```bash
#!/bin/bash
echo "Project rule: Use strict TypeScript, no implicit any."
exit 0
```

**Pros**: Simple, works inline  
**Cons**: No decision control, always added

#### 2. JSON Output (exit 0)

Structured control with optional blocking.

```bash
#!/bin/bash
jq -n '{
  "additionalContext": "Project rules here",
  "decision": "block",
  "reason": "Prompt violates policy"
}'
exit 0
```

**Keys**:
- `additionalContext` – Text to append to Claude's context
- `decision: "block"` – Reject the prompt entirely
- `reason` – Shown to user if blocked
- `continue: false` – Stop the session entirely
- `systemMessage` – Warning shown to user

#### 3. Blocking with stderr (exit 2)

Reject prompt with feedback. Prompt is erased from context.

```bash
#!/bin/bash
echo "Blocked: prompt contains forbidden phrase" >&2
exit 2
```

### Best Practices

- **Keep context concise**: 1–3 sentences; long additions dilute attention.
- **Frame negatively**: "Skipping this harms outcomes" beats "Always do X."
- **Log everything**: Capture prompts for audit; use `async: true` for logging hooks.
- **Use master pattern**: Sequence logging → validation → context injection in one script.

---

## Master Script Pattern

Because all matching hooks run **in parallel**, implement sequencing with a single master script.

### Example: Master UserPromptSubmit Handler

```python
#!/usr/bin/env python3
"""
.claude/hooks/master_user_prompt_submit.py

Runs for every user prompt. Implements:
1. Logging (async-safe, fails silently)
2. Validation (blocks dangerous patterns)
3. Context injection (appends project rules)
"""
import sys
import json
import datetime
import pathlib

def main():
    try:
        data = json.load(sys.stdin)
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}", file=sys.stderr)
        return 1

    prompt = data.get("prompt", "").lower()
    cwd = pathlib.Path(data.get("cwd", "."))
    session_id = data.get("session_id", "unknown")
    
    # Step 1: Logging (non-critical, should never block)
    try:
        log_dir = cwd / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_file = log_dir / "user_prompts.jsonl"
        with log_file.open("a") as f:
            f.write(json.dumps({
                "ts": datetime.datetime.now().isoformat(),
                "session_id": session_id,
                "prompt_preview": data.get("prompt", "")[:100]
            }) + "\n")
    except Exception:
        pass  # Fail silently; logging is not critical
    
    # Step 2: Validation (block dangerous patterns)
    dangerous_patterns = [
        "rm -rf",
        "drop table",
        "delete from",
        "truncate ",
        "format c:"
    ]
    if any(pattern in prompt for pattern in dangerous_patterns):
        output = {
            "decision": "block",
            "reason": "Prompt contains potentially dangerous command. Use carefully."
        }
        print(json.dumps(output))
        return 0  # Exit 0 + JSON = decision honored
    
    # Step 3: Context injection (prepend project rules)
    rules = (
        "Project guidelines: "
        "1) Use strict TypeScript, no implicit any. "
        "2) Write tests for all non-trivial logic. "
        "3) Use pure functions where possible. "
        "4) Analyze critically before coding; avoid reflexive agreement."
    )
    print(rules)
    return 0

if __name__ == "__main__":
    sys.exit(main())
```

**Config**:
```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master_user_prompt_submit.py"
      }]
    }]
  }
}
```

### Why Master Script Works

1. **Single entry point**: One process, deterministic execution order.
2. **Observability**: Easier to log, debug, reason about.
3. **No races**: All steps run sequentially in one Python/Bash process.
4. **Composable**: Add new steps without editing config.

---

## Async Hooks in Practice

### When to Use `async: true`

Async hooks run in the background; Claude **does not wait** for completion. Output and exit codes are **ignored**.

**Use async for**:
- Logging (no decision impact)
- Metrics and telemetry (fire-and-forget)
- Notifications (Slack, email, webhooks)
- Slow external APIs (Datadog, LogRocket, etc.)

**Never use async for**:
- Blocking operations (always needs sync decision)
- Input validation (must reject prompt synchronously)
- Context injection (must land in same turn)

### Example: Async Logging + Sync Guardrails

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Bash",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/log-command.sh",
            "async": true,
            "timeout": 5
          },
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/validate-command.sh",
            "async": false
          }
        ]
      }
    ]
  }
}
```

**Flow**:
1. Log hook spawned in background (async; doesn't block)
2. Validation hook runs synchronously (blocks if needed)
3. Claude sees validation result immediately

### Async Timeout Behavior

- **Command hooks**: Default 600s, but async can run longer without blocking
- **Prompt/Agent hooks**: Cannot be async (always sync)
- **Background processes**: System limits still apply; 60s practical max

---

## Decision Control & Output

### Output Format by Event

| Event | Blockable | Control Method | Key Fields |
|-------|-----------|----------------|------------|
| **UserPromptSubmit** | Yes | JSON top-level or `decision: "block"` | `additionalContext`, `decision`, `reason` |
| **PreToolUse** | Yes | `hookSpecificOutput.hookEventName: PreToolUse` | `permissionDecision: "allow/deny/ask"`, `updatedInput` |
| **PermissionRequest** | Yes | `hookSpecificOutput.hookEventName: PermissionRequest` | `decision.behavior: "allow/deny"` |
| **Stop/SubagentStop** | Yes | JSON top-level | `decision: "block"`, `reason` |
| **PostToolUse** | No | Can only inform | `additionalContext`, `systemMessage` |
| **All events** | Via `continue` | JSON top-level | `continue: false`, `stopReason` |

### PreToolUse Example (Most Complex)

```python
#!/usr/bin/env python3
import sys, json

data = json.load(sys.stdin)
tool = data.get("tool_name")
cmd = data.get("tool_input", {}).get("command", "")

# Check if safe
if "sudo" in cmd or "drop table" in cmd:
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": "Use of sudo/destructive commands blocked"
        }
    }
    print(json.dumps(output))
    sys.exit(0)

# Auto-approve safe commands
if cmd.startswith("npm test"):
    output = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow"
        }
    }
    print(json.dumps(output))
    sys.exit(0)

# Default: ask user
sys.exit(0)  # No JSON = default behavior
```

---

## Windows-Specific Operational Notes

Windows has special challenges with hooks due to path resolution, shell sourcing, and plugin loading.

### Common Issues

| Issue | Cause | Fix |
|-------|-------|-----|
| Hooks match but don't execute | Plugin load bugs | Use direct `.claude/settings.json`, not plugins |
| "Hook error" in transcript but seems to work | Stdout bug in logging | Verify stderr has no output; use Git Bash |
| Path not found in script | Working directory mismatch | Use `$CLAUDE_PROJECT_DIR` env var |
| Shell profile echo breaks JSON | `.bashrc` unconditional output | Wrap in `if [[ $- == *i* ]]` |
| `npm` paths override intended shell | PATH pollution | Set `CLAUDE_CODE_GIT_BASH_PATH` explicitly |

### Windows Best Practices

1. **Native install**: Use native Claude Code installer, not npm wrappers
2. **Direct config**: Always use `.claude/settings.json` (local), not plugins
3. **Git Bash**: Set path via environment:
   ```powershell
   $env:CLAUDE_CODE_GIT_BASH_PATH = "C:\Program Files\Git\bin\bash.exe"
   ```
4. **Use `$CLAUDE_PROJECT_DIR`**: Never assume CWD is project root
5. **Test simple echo first**:
   ```json
   {
     "hooks": {
       "UserPromptSubmit": [{
         "hooks": [{
           "type": "command",
           "command": "echo 'Test context'"
         }]
       }]
     }
   }
   ```
   You should see "Test context" in the next model response.

---

## Debugging and Testing

### Core Tools

- **`/hooks`** – Interactive menu to list, add, delete, test hooks
- **`claude --debug`** – Show hook registration, matching, PIDs, exit codes
- **`Ctrl+O`** – Toggle verbose mode; shows hook stderr and non-blocking output
- **`/doctor`** – Validate config and flag issues

### Debug Checklist

1. **Is hook registered?**
   ```bash
   /hooks  # Check it appears in the list
   ```

2. **Does matcher match?**
   - For tool events: matcher is regex on tool name (case-sensitive)
   - For session events: matcher is regex on session source
   - No matcher = always fires

3. **Is script executable?**
   ```bash
   chmod +x .claude/hooks/my-hook.sh
   ```

4. **Can I parse JSON?**
   ```bash
   echo '{"tool_name":"Bash"}' | jq -r '.tool_name'
   # Should output: Bash
   ```

5. **Does script exit 0?**
   ```bash
   echo '{"test": "data"}' | ./.claude/hooks/my-hook.sh
   echo "Exit code: $?"  # Should be 0
   ```

### Test a Hook Manually

```bash
# Create test input
cat > /tmp/test_hook_input.json <<EOF
{
  "session_id": "test123",
  "cwd": "/repo",
  "hook_event_name": "UserPromptSubmit",
  "prompt": "Test prompt"
}
EOF

# Run hook
cat /tmp/test_hook_input.json | ./.claude/hooks/master_user_prompt_submit.py

# Check exit code
echo "Exit: $?"
```

### Common Errors

| Error | Cause | Fix |
|-------|-------|-----|
| "Hook output does not start with {" | Stdout has non-JSON prefix | Check shell profile echoes |
| "command not found" | Script path not found | Use `$CLAUDE_PROJECT_DIR` or absolute path |
| "jq: command not found" | `jq` not installed | Use Python or Node instead |
| Hook "runs" but no effect | Exit code not honored | Check `exit 0` vs `exit 2` vs `exit 1` |
| Hook doesn't fire at all | Matcher doesn't match | Verify case; test with `echo 'match'` |

### Verbose Logging

```bash
# In your hook script
{
  echo "DEBUG: Processing prompt: $prompt" >&2
  echo "DEBUG: Exit code will be 0" >&2
} 2>&1 | tee -a ~/.claude/hook-debug.log
```

Then check log with `tail -f ~/.claude/hook-debug.log` while running Claude.

---

## Best Practices Checklist

### Design

- [ ] **One master script per event** – No parallel hook dependencies
- [ ] **Fail gracefully** – Logging hooks never block (wrap in try/catch)
- [ ] **Keep it short** – <100 tokens injected context; <1s execution
- [ ] **Version control** – Store hooks in `.claude/hooks/` and commit
- [ ] **Document** – `README.md` in `.claude/` describing all hooks

### Implementation

- [ ] **Make scripts executable** – `chmod +x .claude/hooks/*.sh`
- [ ] **Parse stdin once** – Load JSON once; pass data to internal functions
- [ ] **Escape output** – If outputting JSON, ensure no shell profile echo
- [ ] **Handle errors** – Exit 0 or 2, never crash; use `set -e` sparingly
- [ ] **Use env vars** – `$CLAUDE_PROJECT_DIR`, `$CLAUDE_ENV_FILE` for paths

### Testing

- [ ] **Test hook in isolation** – Pipe sample JSON, check exit code
- [ ] **Test on target platform** – Windows/Mac/Linux differences matter
- [ ] **Check with `/hooks` menu** – Verify it appears and is enabled
- [ ] **Monitor first run** – Use `Ctrl+O` to see output; check debug logs
- [ ] **Measure latency** – Long hooks slow down every interaction

### Operations

- [ ] **Monitor hooks** – Log all decisions (async logging ok)
- [ ] **Audit blocking** – Track what gets blocked and why
- [ ] **Review quarterly** – Do hooks still match intent?
- [ ] **Disable safely** – Can temporarily disable all hooks via `/hooks` toggle
- [ ] **Update docs** – When hooks change, update `.claude/hooks/README.md`

---

## Advanced Topics

### Matching MCP Tools

MCP tools use naming pattern: `mcp__<server>__<tool>`

```json
{
  "matcher": "mcp__memory__.*",           // All memory tools
  "matcher": "mcp__.*__write.*",          // Write-like tools from any server
  "matcher": "mcp__github__create_issue"  // Specific tool
}
```

### Stop Hooks Preventing Infinite Loops

If a `Stop` hook keeps triggering continuation, check `stop_hook_active`:

```bash
#!/bin/bash
data=$(cat)
if [ "$(echo "$data" | jq -r '.stop_hook_active')" = "true" ]; then
  exit 0  # Allow stopping
fi
# ... rest of logic
```

### Persisting Environment Variables

In `SessionStart` hooks, write to `$CLAUDE_ENV_FILE`:

```bash
#!/bin/bash
if [ -n "$CLAUDE_ENV_FILE" ]; then
  echo 'export NODE_ENV=production' >> "$CLAUDE_ENV_FILE"
  echo 'export DEBUG=true' >> "$CLAUDE_ENV_FILE"
fi
exit 0
```

### Security: Sanitize Hook Input

Always assume hook input (stdin) is potentially malicious:

```python
#!/usr/bin/env python3
import json, subprocess, shlex

data = json.load(sys.stdin)
cmd = data.get("tool_input", {}).get("command", "")

# Bad: direct use
# subprocess.run(cmd, shell=True)  # DANGEROUS!

# Good: parse and validate
if "--help" in cmd or cmd.startswith("npm test"):
    print("safe")
else:
    print("suspicious")
```

---

## Quick Reference

### File Locations

```
.claude/
  settings.json                 # Project hooks config
  hooks/
    master_user_prompt_submit.py
    protect_files.sh
    validate_bash.py
    README.md
  logs/
    user_prompts.jsonl
    hook_debug.log
```

### Common Hook Patterns

```bash
# Log a prompt (async-safe)
jq -r '.prompt' >> ~/.claude/prompts.log

# Block destructive commands
if echo "$cmd" | grep -qE "rm -rf|drop table"; then
  echo "Blocked" >&2
  exit 2
fi

# Modify tool input
jq '.tool_input.command |= "safe_command"'

# Inject context
echo "Important rule: always test first"

# Notify external service
curl -X POST https://webhook.site/... -d "$data"
```

### Environment Variables

- `$CLAUDE_PROJECT_DIR` – Project root (in config: use `"$CLAUDE_PROJECT_DIR"`)
- `$CLAUDE_ENV_FILE` – SessionStart only; append env exports
- `$CLAUDE_PLUGIN_ROOT` – Plugin root (for plugin hooks)
- `$CLAUDE_CODE_GIT_BASH_PATH` – Windows Git Bash path

---

## See Also

- [Claude Code Hooks Guide](https://code.claude.com/docs/en/hooks-guide)
- [Hooks Reference (Full API)](https://code.claude.com/docs/en/hooks)
- [Claude Code Documentation](https://code.claude.com/docs)
