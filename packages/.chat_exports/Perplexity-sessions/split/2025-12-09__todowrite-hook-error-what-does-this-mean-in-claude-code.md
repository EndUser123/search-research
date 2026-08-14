---
title: "TodoWrite hook error, what does this mean in claude code?"
date: "2025-12-09"
mode: "COPILOT"
uuid: "1746d01d-32c3-452f-a045-84d43c73c7c1"
entry_count: 4
---

## Human

TodoWrite hook error, what does this mean in claude code?

## Assistant

**"TodoWrite hook error" in Claude Code indicates a failure in a user-configured hook triggered by the TodoWrite tool, which manages TODO lists for task planning and subagent workflows.**[1][2]

## Common Causes
This error often stems from hook misconfiguration, such as invalid JSON syntax, incorrect matchers (e.g., "TodoWrite" case sensitivity), or script execution failures like missing permissions or unescaped quotes.  Exit code 2 from the hook script blocks the tool and displays "hook error," even if the underlying TodoWrite operation partially succeeds, as seen in known bugs where successful executions are mislabeled.[3][2][4][1]

## Troubleshooting Steps
- Run `/hooks` to verify registration and syntax; reload if edited externally.[2]
- Test the hook command manually with `claude --debug` to check logs, environment variables like `$CLAUDE_TOOL_NAME`, and substitution issues.[5][2]
- Ensure TodoWrite is enabled in agent config, as it's sometimes unavailable due to settings like "todo tool usage: false."[4][6]

## Fixes
Update hooks in `~/.claude/settings.json` or `.claude/settings.json` with exact matchers like `"matcher": "TodoWrite"` and executable scripts using full paths via `$CLAUDE_PROJECT_DIR`.  For persistent issues in your RCA/debugging workflows, check recent subagent configs, as these errors have appeared in Task/TodoWrite sequences.[7][8][6][2]

## Human

Common causes of hooks returning exit code 2 in Claude Code

## Assistant

## Common Causes of Hooks Returning Exit Code 2 in Claude Code

**Exit code 2 signals a blocking error that halts execution, not a failure of the hook itself.**  This is the intended design—exit code 2 is the mechanism Claude Code uses to intentionally block tool calls, permission requests, or Claude's stoppage.[1]

### What Exit Code 2 Actually Does

Exit code 2 is a **deliberate blocking signal**, not an error condition. Different hook events interpret it differently:[1]

| Hook Event | Behavior |
|--|--|
| `PreToolUse` | Blocks the tool call and shows stderr to Claude |
| `PermissionRequest` | Denies the permission and shows stderr to Claude |
| `PostToolUse` | Shows stderr to Claude (tool already executed) |
| `Stop` / `SubagentStop` | Blocks stoppage and shows stderr to Claude |
| `UserPromptSubmit` | Blocks prompt processing, erases prompt from context |

When exit code 2 is returned, **only stderr is used as the error message** in the format `[command]: {stderr}`. Any JSON in stdout is ignored.[1]

### Common Misunderstandings That Cause Exit Code 2 Issues

**1. Plugin-based hooks interpret exit code 2 differently than direct hooks**

A documented bug shows that when hooks are installed via the plugin marketplace rather than directly in `.claude/hooks/`, exit code 2 behavior diverges. Stop hooks that correctly exit with code 2 may display `⏺ Stop hook prevented continuation` and halt instead of resuming with instructions, breaking reflexive workflows.[2][3]

**2. Exit code 1 vs. 2 confusion**

Many developers accidentally use exit code 1 expecting non-blocking behavior, but it actually blocks execution. According to documentation, only exit code 0 is fully non-blocking; exit code 1 halts Claude's progression. The correct behavior is:[4][5]
- Exit code 0: Success, continues normally
- Exit code 1: Unexpected issue—blocks execution (undocumented behavior)
- Exit code 2: Intentional blocking—also blocks, but documented as deliberate

**3. JSON output misconfiguration**

For exit code 2, Claude Code ignores JSON output in stdout and only processes stderr. If your hook script relies on JSON in stdout to communicate decision logic when returning exit code 2, that output will be discarded.[1]

### Causes Leading to Unintended Exit Code 2 Returns

**Script failures producing exit code 2 accidentally:**
- Bash script exits with `set -e` on any command failure, which may exit 1 or higher
- Python scripts raising unhandled exceptions sometimes exit with code 2
- Missing file paths or permission errors in scripts

**Incorrect matcher configuration:**
- Case-sensitive matcher names (`TodoWrite` vs. `todowrite`)[6][1]
- Regex patterns not matching intended tool names

**Environment variable substitution failures:**
- `$CLAUDE_PROJECT_DIR` or `$CLAUDE_PLUGIN_ROOT` undefined, causing script not found[7]
- Shell escaping issues with quoted variables in JSON settings

**Plugin architecture issues:**
- Hooks work in `.claude/hooks/` but fail when packaged as plugins[3]
- Different code paths for plugin-based vs. directly installed hooks

### Troubleshooting Exit Code 2 Issues

Run `/hooks` to verify registration and test hook commands manually before Claude invokes them. Use `claude --debug` to see detailed execution logs showing exit codes and stderr output. Ensure scripts are executable with full absolute paths (`$CLAUDE_PROJECT_DIR/script.sh` rather than `./script.sh`). If blocking is unexpected, check if the script logic is intentionally calling `sys.exit(2)` or `exit 2`, or if it's an accidental failure.[8][1]

## Human

Is there logging we can enable?

## Assistant

## Debug Logging Options in Claude Code

Yes, multiple logging levels can be enabled for troubleshooting hooks and exit code issues.

### Official Logging Mechanisms

**Verbose Mode Flag**[1]

Run Claude Code with the `--verbose` flag to activate detailed logging across multiple components including command processing, parameter parsing, validation checks, and tool execution tracking:

```bash
claude --verbose [command]
```

Redirect verbose output to a file for systematic analysis:[1]

```bash
claude --verbose [command] > debug.log 2>&1
```

**Hook Status Visibility**[2]

Use the `/hooks` command within Claude Code to verify hook registration, syntax validation, and execution status. This shows which hooks are active and reports any configuration issues.

### Undocumented Environment Variables

These powerful debugging variables are built into Claude Code but not officially documented:[3]

**`DEBUG=1`** — Enables verbose debug logging to see internal operations[3]

Add to `.claude/settings.json`:

```json
"env": {
  "DEBUG": "1"
}
```

**`CLAUDE_CODE_DEBUG_LOGS_DIR`** — Routes debug logs to a custom directory instead of the default location[3]

```json
"env": {
  "CLAUDE_CODE_DEBUG_LOGS_DIR": "/path/to/custom/logs"
}
```

**`DEBUG_SDK=1`** — Enables SDK-level debug output[3]

**`MCP_TIMEOUT=60000`** — Extends Model Context Protocol timeout to prevent premature disconnects[3]

### The "Nuclear Debugging" Alias

For comprehensive debugging of hooks and MCP issues, use this combined alias:[3]

```bash
alias dclaude="export DEBUG_SDK=1 MCP_TIMEOUT=60000 CLAUDE_CODE_DEBUG_LOGS_DIR=~/claude-debug && claude"
```

This activates all debugging outputs and centralizes logs in `~/claude-debug`. Use `dclaude` instead of `claude` when diagnosing hook failures, MCP server issues, or permission problems.[3]

### Community Logging Tools

**claude-code-logger**  provides CLI-based analysis of Claude Code traffic with visualization of system prompts, file contents, and tool usage tracking. Run with the `-v` verbose flag for unpacked prompts.[4]

**claude-log**  sets up a hook that logs all interactions to `~/claude-log.jsonl`, capturing transcripts and hook activities, with a Python parser for structured analysis.[5]

### Hook-Specific Debugging

For hook exit code issues specifically, combine `--verbose` output with custom logging in your hook scripts to capture stderr and exit codes:[6]

```bash
#!/bin/bash
set -x  # Enable command tracing
echo "Hook executing for tool: $CLAUDE_TOOL_NAME" >&2
# ... your hook logic ...
exit_code=$?
echo "Hook exiting with code: $exit_code" >&2
exit $exit_code
```

The `--verbose` flag displays hook completion messages and event ordering, helping identify when and why exit code 2 is being returned.[6]

## Human

example logging code for debugging that doesn't involved restarting claude code.

## Assistant

## Real-Time Logging Without Restarting Claude Code

The best approach is to use **hook scripts that write directly to log files** in real-time as Claude Code executes tools. No restart required—the hooks activate automatically on each tool invocation.

### Basic File Logging Hook

Here's a simple `PreToolUse` hook that logs all tool calls with timestamps and exit codes in real-time:[1]

```bash
jq -r '"\(.timestamp // now | todate) | Tool: \(.tool) | Command: \(.tool_input.command // "N/A")"' >> ~/.claude/debug.log
```

This appends to `~/.claude/debug.log` every time a tool is about to execute. Watch it in real-time with:

```bash
tail -f ~/.claude/debug.log
```

### Advanced Python Logging Hook with Exit Code Tracking

Create `.claude/hooks/debug_logger.py` for more detailed logging that captures the full hook context: []

```python
#!/usr/bin/env python3
import json
import sys
from datetime import datetime

def log_hook_event():
    try:
        # Read the hook input data from stdin
        data = json.load(sys.stdin)
        
        # Extract relevant fields
        tool_name = data.get('tool', 'unknown')
        tool_input = data.get('tool_input', {})
        hook_event = data.get('hook_event', 'unknown')
        session_id = data.get('session_id', 'unknown')
        
        # Format the log entry
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'event': hook_event,
            'tool': tool_name,
            'session': session_id,
            'command': tool_input.get('command', 'N/A'),
            'file_path': tool_input.get('file_path', 'N/A'),
        }
        
        # Append to log file
        with open(os.path.expanduser('~/.claude/hooks.log'), 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
        
        # Return success (exit code 0)
        sys.exit(0)
    
    except Exception as e:
        # Log errors to stderr so Claude sees them
        print(f"Logging error: {e}", file=sys.stderr)
        sys.exit(0)  # Don't block execution if logging fails

if __name__ == '__main__':
    log_hook_event()
```

Make it executable:

```bash
chmod +x .claude/hooks/debug_logger.py
```

### Hook Configuration in `.claude/settings.json`

Add this configuration to log all tool executions and their exit codes: []

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "*",
        "hooks": [
          {
            "type": "command",
            "command": "uv run $CLAUDE_PROJECT_DIR/.claude/hooks/debug_logger.py"
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
            "command": "jq -r '\"[PostToolUse] Tool: \\(.tool) | Exit: \\(.exit_code) | Timestamp: \\(.timestamp // now | todate)\"' >> ~/.claude/hooks.log"
          }
        ]
      }
    ]
  }
}
```

### Real-Time Log Monitoring (Without Restart)

In a separate terminal, watch logs as they're written during Claude Code execution:

```bash
# Watch combined hook logs
tail -f ~/.claude/hooks.log

# Or filter by event type
tail -f ~/.claude/hooks.log | grep "PostToolUse"

# Or use jq to parse JSON logs
tail -f ~/.claude/hooks.log | jq 'select(.event == "PostToolUse")'
```

### Bash-Specific Command Logging

For debugging Bash exit codes specifically, use this PreToolUse hook: []

```bash
jq -r 'if .tool == "Bash" then "\(.timestamp // now | todate) | Bash Command: \(.tool_input.command)" else empty end' >> ~/.claude/bash-debug.log
```

After Claude executes the Bash command, the `PostToolUse` hook captures the exit code:

```bash
jq -r 'if .tool == "Bash" then "\(.timestamp // now | todate) | Exit Code: \(.exit_code)" else empty end' >> ~/.claude/bash-debug.log
```

### Full Debugging Context with Timestamps

For comprehensive debugging without restart, log the entire hook context as JSON: []

```bash
jq '.' >> ~/.claude/full-context.log
```

This captures all available data—tool names, inputs, outputs, session IDs, exit codes—in machine-readable JSON format. Parse it later:

```bash
jq '.[] | select(.exit_code == 2)' ~/.claude/full-context.log
```

### Key Advantages

- **No restart required**: Hooks run automatically on each tool invocation
- **Real-time visibility**: Use `tail -f` to watch logs as Claude Code executes
- **Persistent storage**: Logs survive Claude Code sessions for post-analysis
- **Non-blocking**: Logging hooks with exit code 0 don't interfere with execution
- **Exit code capture**: Both `PreToolUse` and `PostToolUse` can log exit codes for diagnosing failures []
