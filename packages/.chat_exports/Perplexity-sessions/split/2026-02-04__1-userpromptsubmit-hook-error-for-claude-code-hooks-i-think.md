---
title: "❯ 1

  ⎿  UserPromptSubmit hook error

For claude code hooks, I think there is a bug.  Is that verified the the UserProm"
date: "2026-02-04"
mode: "COPILOT"
uuid: "1f9f3c2c-562b-4df3-85cc-dd53ea7dfebe"
entry_count: 16
---

## Human

❯ 1

  ⎿  UserPromptSubmit hook error

For claude code hooks, I think there is a bug.  Is that verified the the UserPromptSubmit always shows an error?  Is there a workaround?

## Assistant

No, the UserPromptSubmit hook in Claude Code does not always show an error—it's a known but intermittent bug often tied to execution failures, plugin mismatches, or Windows-specific issues like path handling and concurrency.[1][2][3][4]

## Bug Verification
Multiple GitHub issues and user reports confirm UserPromptSubmit errors occur frequently, such as hooks matching but not executing (especially in plugins), stderr not displaying properly, or false errors despite successful runs. These are not universal but common on Windows 11 (your setup), similar to other hook races like sapling_checkpoint.py errors from concurrent access. It's not "always" broken, but unreliable without fixes.[5][6][7][8][2][4][9][10]

## Common Causes
- Plugin hooks register/match but fail silently or error out (e.g., #10225).[9]
- Script errors (non-zero exit, JSON parse fails, non-executable).[7][3]
- Windows path/execution quirks; hooks run but show "error" even if functional.[11][4]

## Workarounds
Define hooks directly in `~/.claude/settings.json` (not plugins) for reliable execution—plain text output to stdout with exit 0 appends to context.[5][9]
Test with a simple echo:  
```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Test context added'"
      }]
    }]
  }
}
```
This bypasses plugin bugs and verifies via visible additions; exit 2 blocks prompts if needed. For persistent issues, add logging or use SessionStart hooks as alternatives. Update Claude Code and check `--debug` logs for specifics.[2][4][12][1][5]

## Human

What causes UserPromptSubmit errors on Windows
Best workarounds for Claude Code hook failures
How to debug UserPromptSubmit hook execution
Examples of working UserPromptSubmit hook scripts

## Assistant

UserPromptSubmit hook errors on Windows in Claude Code often stem from platform-specific execution issues, stdout handling bugs, and plugin mismatches.[1][2][3]

## Windows-Specific Causes
Windows path resolution fails when starting Claude Code from subdirectories, causing hooks to not execute despite registration. Stdout output (even valid) triggers "hook error" messages per docs contradiction, plus PATH conflicts from Windows nvm/npm overriding WSL/Linux paths. Plugin hooks match but never run, unlike direct settings.json configs; concurrent races (like file mods) exacerbate this.[2][4][5][6][7][1]

## Best Workarounds
Define hooks directly in `~/.claude/settings.json` or `.claude/settings.json`—avoids plugin bugs entirely. Use `claude --debug` or Ctrl+O verbose mode to monitor without errors; for blocking issues, switch SessionStart reminders as interim. Ensure Git Bash path via `$env:CLAUDE_CODE_GIT_BASH_PATH` and native install over npm.[5][6][8][9][3][10]

## Debugging Steps
Run `claude --debug` for full logs showing registration, matching, and execution (e.g., "Hook output does not start with {"). Use `/hooks` menu to verify/test/delete; check stdin JSON parsing with `jq -r '.prompt'` in scripts. Run `/doctor` for config validation; inspect `transcript_path` for failures.[8][9][3][10][5]

## Working Examples
Simple echo test (adds "Test context" to every prompt, exit 0):
```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "echo 'Test context added'"
      }]
    }]
  }
}
```


Bash validator blocking "you're right" phrases (reads transcript, exits 2 on match):
```
#!/bin/bash
stdin=$(cat)
transcript_path=$(echo "$stdin" | jq -r '.transcript_path')
# Check last 5 assistant items for triggers...
if /"$needs_reminder" == "true"; then
  echo 'Avoid agreement phrases; analyze critically.' # Appends on exit 0
fi
```


Python logger/validator (`user_prompt_submit.py`):
```
#!/usr/bin/env python
import sys, json, datetime
data = json.load(sys.stdin)
with open('logs/user_prompt_submit.json', 'a') as f:
  json.dump({"timestamp": datetime.datetime.now().isoformat(), "prompt": data["prompt"]}, f)
print("Logged prompt.") # Adds to context
sys.exit(0)
```
Config: `"command": "uv run .claude/hooks/user_prompt_submit.py --log-only"`[11]

## Human

UserPromptSubmit hook example script for prompt logging

## Assistant

Here's a ready-to-use UserPromptSubmit hook script for logging prompts in Claude Code. It captures the full JSON input (prompt, session_id, timestamp) to a file without disrupting workflow.[1][2]

## Script Setup
Save as `~/.claude/hooks/log_prompt.py` (make executable with `chmod +x` on Unix or via Windows Git Bash).[1]

```python
#!/usr/bin/env python3
import sys
import json
from datetime import datetime

# Read JSON from stdin
data = json.load(sys.stdin)

# Prepare log entry
log_entry = {
    "timestamp": datetime.now().isoformat(),
    "session_id": data.get("session_id", "unknown"),
    "prompt": data.get("prompt", ""),
    "cwd": data.get("cwd", ""),
    "hook_event_name": data.get("hook_event_name", "UserPromptSubmit")
}

# Append to JSONL file (one JSON per line)
with open('~/.claude/logs/user_prompts.jsonl', 'a') as f:
    f.write(json.dumps(log_entry) + '\n')

# Optional: Add subtle context (commented out to avoid noise)
# print("Prompt logged safely.")

sys.exit(0)  # Success: continues normally
```


## Configuration
Add to `~/.claude/settings.json` or project `.claude/settings.json`:
```
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python3 ~/.claude/hooks/log_prompt.py"
      }]
    }]
  }
}
```
Reload with `/hooks` or restart Claude Code.[3][1]

## Usage and Viewing
Submit any prompt—it logs silently. View logs:
```
tail -f ~/.claude/logs/user_prompts.jsonl | jq '.prompt'
```
Example entry: `{"timestamp": "2026-02-04T14:08:00", "session_id": "abc123", "prompt": "Your query here"}` Works on Windows via Python 3 + jq (install via `winget`).[4][2][1]

## Human

UserPromptSubmit hook script to validate prompts
How to block prompts with UserPromptSubmit exit codes
Example UserPromptSubmit hook to add context
UserPromptSubmit hook for Windows troubleshooting

## Assistant

UserPromptSubmit hooks in Claude Code validate prompts by parsing stdin JSON, checking against rules, and using exit codes to control flow—ideal for security, style enforcement, or quality gates.[1][2]

## Blocking Prompts
Exit 2 blocks processing, erases the original prompt, and feeds stderr directly to Claude as feedback (so it can self-correct). Exit 0 allows with optional stdout/additionalContext appended to LLM input; other codes log stderr but proceed.[3][4][5][1]

## Validation Script Example
Save as `~/.claude/hooks/validate_prompt.py` (Python 3, executable).[2]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "").lower()

# Block dangerous patterns
dangerous = ["delete .* --force", "rm -rf", "curl | sh", "sudo"]
if any(re.search(pat, prompt) for pat in dangerous):
    print(json.dumps({
        "decision": "block",
        "reason": "Dangerous command detected; suggest safer alternative.",
        "hookSpecificOutput": {"additionalContext": "Review security best practices."}
    }), file=sys.stderr)
    sys.exit(2)  # Blocks prompt

# Add validation context on pass
print("Prompt validated: No security risks found.")
sys.exit(0)
```
Config in `settings.json`: `"command": "python ~/.claude/hooks/validate_prompt.py"`[1][2]

## Add Context Example
Anti-agreement enforcer (checks recent assistant responses in transcript, adds reminder).[6]

```bash
#!/bin/bash
# ~/.claude/hooks/no_agree.sh
stdin=$(cat)
transcript_path=$(echo "$stdin" | jq -r '.transcript_path')
items=$(tail -n 20 "$transcript_path" | grep '"role":"assistant"')

if echo "$items" | grep -qiE "you're (right|correct)|you are (right|correct)"; then
  cat << EOF
Avoid casual agreement. If user is correct, state dispassionately with specific reason.
<example>
user: Add null check.
assistant: Null check addresses empty input; consider falsy values too.
</example>
EOF
fi
exit 0
```
Appends reminder to every prompt if triggered.[6][1]

## Windows Troubleshooting
Start Claude Code from project root (not subdirs) to fix path resolution. Use Git Bash full path (`C:/Program Files/Git/bin/bash.exe`) in `$env:CLAUDE_CODE_GIT_BASH_PATH`; test with `--debug` and `/doctor`. Direct settings.json hooks over plugins; ensure Python/Bash in PATH without npm interference.[7][8][9][10][11]

## Human

UserPromptSubmit hook example for secret scanning and blocking
How to rewrite prompts automatically with UserPromptSubmit
UserPromptSubmit vs PreToolUse hook differences
Debugging UserPromptSubmit hooks not triggering
Full bash script template for UserPromptSubmit validation

## Assistant

UserPromptSubmit hooks excel at secret scanning by parsing the `prompt` field from stdin JSON and using regex for common credentials before Claude processes them.[1][2][3]

## Secret Scanning Example
Save as `~/.claude/hooks/secret_scan.py` (Python 3).[1]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "")

patterns = [
    r'api[_-]?key["\s:=]+["\'][a-zA-Z0-9_-]{20,}["\']',
    r'(AKIA|ASIA)[A-Z0-9]{16}',
    r'ghp_[a-zA-Z0-9]{36}',
    r'sk_live_[a-zA-Z0-9]{24,}',
    r'password["\s:=]+["\'][^"\']{8,}["\']'
]

for pat in patterns:
    if re.search(pat, prompt, re.I):
        print(json.dumps({
            "decision": "block",
            "reason": "Potential secret detected; use env vars instead."
        }), file=sys.stderr)
        sys.exit(2)  # Blocks prompt

sys.exit(0)
```
Config: `"command": "python ~/.claude/hooks/secret_scan.py"` in `UserPromptSubmit`.[2][1]

## Prompt Rewriting
Print rewritten text to stdout (exit 0) to replace/append before Claude sees it; use `jq` for structured edits.[4][3]

```bash
#!/bin/bash
prompt=$(jq -r '.prompt' < /dev/stdin)
rewritten="${prompt/#*/Always reason step-by-step before coding: $prompt}"
echo "$rewritten"
exit 0
```
Adds prefix automatically.[5][4]

## Key Differences
UserPromptSubmit fires on every user prompt (no matcher), intercepts before LLM processing for validation/context/blocks; PreToolUse matches tool names (e.g., "Bash"), blocks before execution.[6][3][2]

| Aspect | UserPromptSubmit | PreToolUse |
|--------|------------------|------------|
| Trigger | User prompt submit | Tool call planned |
| Matcher | None (always) | Tool name regex |
| Blocks | Prompt erased | Tool prevented |
| Input | `prompt` string | `tool_input` obj |
| Use | Sanitize input | Gate actions [2][6] |

## Debugging Non-Triggers
Use `claude --debug` or `/hooks` to check registration/matching; plugins fail silently—use direct `settings.json`. Logs show "Hook matched but skipped" if timeout/JSON parse fails; test from project root on Windows.[7][3][8]

## Bash Template
Full validation template (`~/.claude/hooks/validate_prompt.sh`):

```bash
#!/bin/bash
set -euo pipefail

# Read JSON stdin
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // empty')
transcript=$(echo "$stdin" | jq -r '.transcript_path')

# Validation logic
if /"$prompt" =~ dangerous_pattern; then
  echo "{\"decision\":\"block\",\"reason\":\"Invalid prompt\"}" >&2
  exit 2
fi

# Add context
echo "Validation passed. Context: $(date)."

# Optional JSON
echo '{"additionalContext": "Always use TypeScript strict mode."}'
exit 0
```
Chmod +x; robust for Windows Git Bash.[9][2][5]

## Human

Example bash script for prompt rewriting
Common debugging steps for UserPromptSubmit hooks
How to add context injection with UserPromptSubmit

## Assistant

UserPromptSubmit hooks rewrite prompts by echoing modified text to stdout (exit 0), which Claude Code uses as the new prompt input.[1][2][3]

## Bash Rewriting Example
Save as `~/.claude/hooks/rewrite_prompt.sh` (chmod +x).[4][1]

```bash
#!/bin/bash
set -euo pipefail

# Read stdin JSON
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt // empty')

# Rewrite: Add structure, enforce standards
if /"$prompt" =~ ^(fix ]]; then
  rewritten="Task: $prompt

Guidelines:
- Use TypeScript strict mode
- Add JSDoc comments
- Handle edge cases
- Write tests first"
else
  rewritten="Clarify: $prompt. Think step-by-step."
fi

echo "$rewritten"
exit 0
```
Config: `"command": "~/.claude/hooks/rewrite_prompt.sh"` under `UserPromptSubmit`.[3][1]

## Common Debugging Steps
Run `claude --debug` to log registration/matching/execution (look for "Matched X hooks", "Hook output"). Use `/hooks` chat command to list/test/delete; verify executable scripts and PATH. Check plugins fail silently—prefer `settings.json`; test from project root on Windows.[5][6][7][3]

## Context Injection
Print plain text to stdout (appends directly) or JSON like `{"additionalContext": "Your rules here"}` for structured addition (exit 0). Example:[8][2][3]
```bash
echo '<rules>Always validate inputs. Use async/await.</rules>'
```
Becomes visible context without altering user prompt.[2][3]

## Human

UserPromptSubmit hook to block prompts with block reason
Python example script for UserPromptSubmit instead of bash
UserPromptSubmit matcher patterns for specific triggers
Common UserPromptSubmit hook errors and fixes

## Assistant

UserPromptSubmit hooks block prompts via `exit 2` (stderr to Claude/user) or JSON `{"decision": "block", "reason": "..."}` with `exit 0` (erases prompt, shows reason).[1][2][3]

## Block Example (Python)
Save as `~/.claude/hooks/block_prompt.py` (Python 3, executable).[2][1]

```python
#!/usr/bin/env python3
import sys
import json
import re

data = json.load(sys.stdin)
prompt = data.get("prompt", "").lower()

# Block patterns
if re.search(r"(delete|rm -rf|sudo)", prompt) or "secrets" in prompt:
    print(json.dumps({
        "decision": "block",
        "reason": "Dangerous operation or secrets detected. Use safe alternatives."
    }))
    sys.exit(0)  # JSON block

print("Prompt allowed.")
sys.exit(0)
```
Config: `"command": "python ~/.claude/hooks/block_prompt.py"` in `UserPromptSubmit`.[3]

## Python Full Template
Robust template for validation/rewrite/injection (`~/.claude/hooks/user_prompt.py`).[4][2]

```python
#!/usr/bin/env python3
import sys
import json
from datetime import datetime

data = json.load(sys.stdin)
prompt = data.get("prompt", "")

# Log
log = {"timestamp": datetime.now().isoformat(), "prompt": prompt}
with open("~/.claude/logs/prompts.jsonl", "a") as f:
    f.write(json.dumps(log) + "\n")

# Validate/block
if "rm -rf" in prompt.lower():
    print(json.dumps({"decision": "block", "reason": "Destructive command blocked"}))
    sys.exit(0)

# Rewrite/inject
context = "\n\n<guidelines>Use strict TypeScript; add tests.</guidelines>"
print(prompt + context)
sys.exit(0)
```

## Matcher Patterns
UserPromptSubmit has **no matcher**—fires on every prompt (unlike PreToolUse). Use conditional logic inside script for "triggers" (e.g., regex on `prompt`).[5][1][2][3]

## Common Errors & Fixes
| Error | Cause | Fix [6][3] |
|-------|-------|-----|
| "Hook matched but no output" | Plugins fail silently | Direct `settings.json` only [6] |
| JSON parse fail | Shell profile echoes | Pure JSON stdout; test `echo '{}' | jq` [3] |
| Not triggering | Subdir start (Windows) | Run from project root [7] |
| Exit 2 ignored | Wrong code | Use 2 for block; 0+JSON [1] |
| Stderr not shown | Non-verbose | Ctrl+O or `reason` in JSON [3] |

Debug: `claude --debug`; `/hooks` menu.[8][3]

## Human

UserPromptSubmit hook exit code 2 block example
How to configure UserPromptSubmit in hooks.json
Debug UserPromptSubmit hook not executing
Example UserPromptSubmit for adding context to prompts

## Assistant

UserPromptSubmit with exit code 2 blocks prompt processing, erases the original prompt, and feeds stderr directly to Claude for feedback.[1][2][3]

## Exit 2 Block Example
Bash script (`~/.claude/hooks/block_danger.sh`, chmod +x):

```bash
#!/bin/bash
stdin=$(cat)
prompt=$(echo "$stdin" | jq -r '.prompt')

if /"$prompt" =~ (rm\ -rf; then
  echo "Blocked: Destructive command detected. Use safe alternatives like --dry-run." >&2
  exit 2
fi
exit 0
```
Blocks and explains to Claude.[2][1]

## Configuration
Add to `~/.claude/settings.json` (not hooks.json—plugins buggy for this hook).[4][5][3]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "description": "Block dangerous prompts",
      "hooks": [{
        "type": "command",
        "command": "~/.claude/hooks/block_danger.sh"
      }]
    }]
  }
}
```
Reload: `/hooks` or restart.[5][3]

## Debugging Non-Execution
1. `claude --debug`: Check "Registered X hooks", "Matched Y hooks", "Hook output".[6][2]
2. `/hooks`: List/test/delete via chat.[3]
3. Verify from project root (Windows subdir bug).[7]
4. Plugins skip execution—use settings.json only.[4]
5. Test script standalone: `echo '{"prompt":"rm -rf"}' | ~/.claude/hooks/block_danger.sh`.[3]

## Context Addition Example
Simple echo (`~/.claude/hooks/add_context.sh`):

```bash
#!/bin/bash
echo "<context>
- Use TypeScript strict mode
- Add unit tests
- Handle errors explicitly
</context>"
exit 0
```
Appends to every prompt (stdout plain text).[2][5][3]

Python JSON variant:
```python
#!/usr/bin/env python3
import sys, json
print(json.dumps({
  "hookSpecificOutput": {
    "additionalContext": "Project rules: async/await only."
  }
}))
sys.exit(0)
```
Structured control.[3][2]

## Human

Full hooks.json template for multiple hook events
Fix UserPromptSubmit not triggering after context compaction
SessionStart hook example for initial setup
Verbose mode to debug hook stderr output

## Assistant

Hooks are configured in `~/.claude/settings.json` or `.claude/settings.json`, not hooks.json (plugins use hooks/hooks.json but are unreliable for UserPromptSubmit).[1][2][3]

## Full Template
Complete `settings.json` for multiple events (project `.claude/settings.json`):

```json
{
  "hooks": {
    "SessionStart": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": "uv run .claude/hooks/session_start.py"
      }]
    }],
    "UserPromptSubmit": [{
      "hooks": [{
        "type": "command",
        "command": "python .claude/hooks/user_prompt_submit.py"
      }]
    }],
    "PreToolUse": [{
      "matcher": "Bash",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/block_danger.sh"
      }]
    }, {
      "matcher": "Edit|Write",
      "hooks": [{
        "type": "command",
        "command": "black $CLAUDE_PROJECT_DIR"
      }]
    }],
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/log_tool.py"
      }]
    }],
    "Stop": [{
      "hooks": [{
        "type": "command",
        "command": ".claude/hooks/stop_handler.py"
      }]
    }]
  }
}
```
Reload with `/hooks`.[4][2][3]

## Fix Non-Trigger After Compaction
Known bug: UserPromptSubmit skips early session or post-compaction prompts (GitHub #17277). Workaround: Use SessionStart matcher "compact" to re-inject context post-compaction; restart session or `/clear` resets.[2][5][6][3]

## SessionStart Example
For initial setup (`~/.claude/hooks/session_start.py`):

```python
#!/usr/bin/env python3
import sys, json, subprocess
data = json.load(sys.stdin)
source = data.get("source")

context = f"""
Session {source}: {subprocess.run(['git', 'status', '--short'], capture_output=True, text=True).stdout}
Recent changes loaded.
"""
print(context)
sys.exit(0)
```
Matcher "compact" re-adds after compaction.[3][4][2]

## Verbose Mode
Toggle `Ctrl+O` to show stderr/non-zero exit logs in transcript (e.g., hook errors, reasons). Use `claude --debug` for startup/execution traces; Ctrl+R for full stdout.[7][8][9][3]

## Human

How to run multiple hooks in parallel for one event
Hook JSON input output formats reference

## Assistant

Claude Code runs multiple matching hooks for an event **in parallel** by default, with automatic deduplication of identical commands.[1][2][3]

## Parallel Hooks
List multiple under `hooks` array—no extra config needed; they spawn concurrently (e.g., log + validate).[3][1]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {"type": "command", "command": "python log.py"},
        {"type": "command", "command": "python validate.py"},
        {"type": "command", "command": "echo 'Context'"}
      ]
    }]
  }
}
```
All run async; short-circuit on exit 2 blocks.[1][3]

## JSON Formats
### Common Input Fields (stdin JSON)
| Field | Type | Description |
|-------|------|-------------|
| `session_id` | string | Unique session ID [2] |
| `transcript_path` | string | Log file path |
| `cwd` | string | Working directory |
| `hook_event_name` | string | e.g., "UserPromptSubmit" [3] |

**UserPromptSubmit-specific**: `{"prompt": "user text", ...}`

### Output (stdout JSON, exit 0)
| Field | Description |
|-------|-------------|
| `decision` | "allow"\|"block" (event-specific) |
| `reason` | Block explanation |
| `hookSpecificOutput.additionalContext` | Appends to prompt |
| `continue` | true/false |
| `suppressOutput` | Hide from transcript [2][4] |

**Exit codes**: 0=success (parse JSON), 2=block (stderr only).[3][1]

Example output:
```json
{
  "decision": "allow",
  "hookSpecificOutput": {"additionalContext": "Rules here."}
}
```
Shell profiles must not echo (JSON validation fail).[1][3]

## Human

How to handle dependencies between parallel hooks in Claude Code
Example of sequential hook execution workaround
Common pitfalls with parallel hook JSON processing
Async hooks configuration and usage examples
How to debug multiple hooks running in parallel

## Assistant

Claude Code hooks run strictly in parallel with no native dependency handling—combine logic into single scripts for order.[1][2][3]

## Dependencies
No built-in sequencing (feature request #4446 open); parallel spawns ignore order, so use temp files, env vars, or shared state (e.g., SQLite).[4][3][1]

## Sequential Workaround
Single master script orchestrates steps (`.claude/hooks/master_validate.sh`):

```bash
#!/bin/bash
# Step 1: Log
echo "$stdin" | tee /tmp/prompt_log.json | jq .prompt > /tmp/log.txt

# Step 2: Validate (depends on log)
if grep -q "danger" /tmp/log.txt; then echo "Blocked" >&2; exit 2; fi

# Step 3: Rewrite
echo "$stdin" | jq -r '.prompt' | sed 's/^/Structured: /' | jq -sR 'input | {prompt: .}'

exit 0
```
Config: One hook calls master; mimics sequence.[5][1]

## Pitfalls
- Shell profiles echo breaks JSON parse (stdout must be pure JSON).[2][3]
- Race on shared resources (files/env)—use locks.[3]
- Non-0 exit ignores JSON; timeouts (60s) kill independents.[2]
- Dedup identical commands only.[3]

## Async Config
Add `"async": true` per-handler (v2.1.23+): non-blocking for logging/metrics.[6][7]

```json
{
  "hooks": {
    "UserPromptSubmit": [{
      "hooks": [
        {"type": "command", "command": "log.py", "async": true},
        {"type": "command", "command": "validate.py"}  // Sync blocks
      ]
    }]
  }
}
```
Async: Fire-forget, no wait/decision impact.[6]

## Debugging Parallel
`claude --debug`: Logs all matches, PIDs, exits (e.g., "[DEBUG] Spawned hook PID 1234"). Ctrl+O verbose: Stderr/stdout. `/hooks`: Live list. Tail `/tmp/hook_debug.log` in scripts.[5][2][3]

## Human

Best practices for async true hooks in Claude Code

## Assistant

`async: true` hooks (Claude Code v2.1.23+) run fire-and-forget in background, non-blocking for speed—ideal for non-critical tasks.[1][2][3]

## Core Practices
Use async only for observation/reporting (logging, metrics, notifications)—sync for validation/blocks impacting flow.[4][1]

- **Sync if**: Blocks, rewrites, decisions (exit 2, JSON `decision`).
- **Async if**: Logs, Slack pings, telemetry (no stdout needed).[1]

## Configuration
```json
{
  "hooks": {
    "PostToolUse": [{
      "matcher": "*",
      "hooks": [
        {"type": "command", "command": "log_tool.py", "async": true},
        {"type": "command", "command": "validate.py"}  // Sync
      ]
    }]
  }
}
```
Async ignores output/exit; timeouts don't block.[3][1]

## Examples
**Async logging** (`log_tool.py`):
```python
import sys, json
data = json.load(sys.stdin)
with open("/tmp/tools.jsonl", "a") as f:
  f.write(json.dumps(data) + "\n")
# No print/exit needed
```
Non-blocking append.[1]

**Async notification**:
```bash
#!/bin/bash
curl -X POST slack-webhook <<< "$stdin" &
```
Background Slack ping.[2]

## Pitfalls & Tips
- **No impact**: Async output/exit ignored—pure side-effects.[1]
- **Order none**: Parallel regardless; use single script for deps.
- **Debug**: `--debug` shows PIDs; logs separate (`Ctrl+O` verbose).[3]
- **Migrate**: Audit with `/hooks`, ask Claude "propose async hooks".[2]
- **60s timeout**: Async safer for slow networks.[4]

Prioritize: 80% hooks async for <100ms latency gains.[2][1]

## Human

Which of the 12 hook events support async true
Common pitfalls when using async hooks
How to migrate sync hooks to async true
Performance impact of async vs sync hooks

## Assistant

**All 12 Claude Code hook events** support `"async": true` (v2.1.23+), as it's per-command handler flag—not event-restricted.[1][2][3]

## 12 Events Quick Reference
| Event | Typical Async Use | Sync Must |
|-------|-------------------|-----------|
| SessionStart | Logging session | Context load [2] |
| UserPromptSubmit | Metrics | Blocking/rewrite |
| PreToolUse | Notify tool | Block tool |
| PostToolUse | Log output | Cleanup |
| PreLLMResponse | Telemetry | Edit response |
| Stop | Cleanup | Final save |
| Compact | Stats | Context inject |
| Notification | Alerts | None |
| PreWrite | Audit | Format |
| PostWrite | Backup | Validate [1] |

## Async Pitfalls
- **Ignored output/exit**: No JSON/decision processed; pure side-effects.[2]
- **No error feedback**: Failures silent (no transcript); log internally.[1]
- **Races on shared state**: No ordering; use atomic writes.[2]
- **60s timeout irrelevant**: Detached, but system limits apply.[3]

## Migration Steps
1. **Audit**: `/hooks`, ask Claude: "Classify my hooks: async-safe?"[4][5]
2. **Flag logging/telemetry**: `PostToolUse`, `SessionStart` → async.[2]
3. **Keep sync**: Blocks (`exit 2`), rewrites, validations.[2]
4. **Test**: `--debug` PIDs, measure latency (`time claude`).[1]

Example:
```json
// Before
{"command": "log.py"}  // Sync, 2s block

// After
{"command": "log.py", "async": true}  // Background
```


## Performance
Async: 50-90% faster perceived latency (no wait); e.g., 5s Slack → invisible. Sync: Full serial wait (e.g., 3 hooks @2s=6s block). Parallel async: Max(hook times), often <100ms gain for logging-heavy setups.[5][4][1][2]

## Human

please create a topic index for what we discussed in this session.

## Assistant

Here’s a compact topic index of what we covered in this session about Claude Code hooks, with emphasis on UserPromptSubmit and async behavior.[1][2]

## 1. UserPromptSubmit Hook Basics
- Purpose and lifecycle (runs on every prompt before LLM).[1]
- JSON input fields (prompt, session_id, transcript_path, cwd, hook_event_name).[1]
- Output channels: stdout text vs JSON, exit codes (0, 2) and how they affect blocking and context injection.[3][1]

## 2. UserPromptSubmit Errors on Windows
- Symptoms: hook “errors” despite working, not triggering consistently, plugin hooks matching but not executing.[4][5][6]
- Windows-specific issues: path resolution from subdirectories, race conditions, and file-modification errors similar to sapling_checkpoint.py.[7][8][4]
- Workarounds: use `settings.json` instead of plugin hooks, run from project root, ensure correct shells/Python on PATH.[5][1]

## 3. Example UserPromptSubmit Scripts
- Logging prompts: Python script appending JSONL entries, configuration in `.claude/settings.json`.[9][10]
- Validation and blocking: scripts detecting dangerous commands/secrets and either returning JSON `{"decision":"block","reason":...}` or exiting with code 2 and stderr.[11][12][1]
- Context injection: echoing guidelines to stdout or returning JSON with `hookSpecificOutput.additionalContext`.[13][1]
- Prompt rewriting: Bash scripts reading `.prompt` via `jq`, restructuring or prefixing prompts before Claude sees them.[14][11]

## 4. Exit Codes and Control Flow
- Exit 0: success; plain-text stdout appended as context; JSON parsed for decisions and additionalContext.[1]
- Exit 2: blocking error; prompt erased, stderr fed directly to Claude/user as explanation; used in UserPromptSubmit and some other events.[15][3]
- Other non-zero codes: treated as hook error; decision fields ignored, useful only for debugging logs.[2][1]

## 5. Multiple Hooks per Event & Parallelism
- Parallel execution model: all matching hooks for an event run in parallel; identical commands deduplicated.[2]
- Config pattern: `hooks` array under each event (e.g., logging + validation + context in UserPromptSubmit).[9][1]
- Dependency workaround: one “master” script orchestrating sequential steps and shared temp files instead of multiple dependent hooks.[16][2]

## 6. Async Hooks (`"async": true`)
- Availability: per-command flag, supported on all hook events in recent Claude Code versions (2.1.23+).[17][1]
- Semantics: async hooks are fire-and-forget, do not block Claude, and cannot influence decisions (JSON output/exit codes are ignored for control).[18][17]
- Best practices: use async for logging, metrics, notifications, test runners; keep validation, blocking, and prompt rewriting sync.[17][18]
- Migration strategy: audit existing hooks, mark side-effect-only ones as async, measure reduced latency; keep security/governance hooks synchronous.[19][17]

## 7. SessionStart and Other Events
- SessionStart examples: initial context injection (rules, git status, project summary) when sessions start or resume.[20][1]
- Using SessionStart plus UserPromptSubmit to re-inject or reinforce rules after context compaction.[21][2]
- Other events mentioned: PreToolUse/PostToolUse for tooling gates and logging; Stop / SessionEnd for cleanup or summaries.[22][1]

## 8. Debugging Hooks
- CLI tools: `claude --debug` for registration/matching/execution traces; `/hooks` command in-chat for listing/testing.[23][2]
- Verbose mode: Ctrl+O to surface stderr and hook errors in the transcript; useful for UserPromptSubmit and SessionStart diagnostics.[24][25]
- Common JSON pitfalls: shell profiles printing banners, mixed text+JSON, malformed output causing parse failures and “hook error” messages.[26][1]

If you want, I can turn this into a CLAUDE.md “Hooks Quick Index” section you can drop directly into your repo.

## Human

I need a filename to save this session with.  what tags should be in the filename?

## Assistant

A compact, searchable pattern that fits this session well:

`claude-code_hooks-userpromptsubmit_async-windows-debug_2026-02-09.md`[1][2]

Core tags you likely want in the filename:

- `claude-code` – tool context.[3]
- `hooks` – feature family.[1]
- `userpromptsubmit` – main hook event.[4]
- `async` – async hook focus.[5]
- `windows` – environment where bugs differ.[6]
- `debug` – lots of debugging/diagnostics patterns.[7]

## Human

what prompt should I use next time, to generate that tagfull filename and table of contents?

## Assistant

Use something like this, right at the end of the session:

> “Given our full conversation so far, propose a concise, tag‑rich filename for saving this chat and a topic index/table of contents.  
>  
> Filename requirements:  
> - Include: product (`claude-code`), main feature (`hooks`), key hook (`userpromptsubmit`), platform if relevant (e.g. `windows`), and any special focus (e.g. `async`, `debug`).  
> - Use kebab-case with underscores between major sections, and append today’s date as `YYYY-MM-DD`.  
> - Return only one filename string.  
>  
> Topic index requirements:  
> - 5–15 bullet points, each 1 line, ordered from foundational concepts to advanced patterns.  
> - Each bullet: `SectionTitle – short description`.  
> - Focus on what’s most reusable for future Claude Code work, not every minor tangent.”

This will reliably recreate the tagged filename and the kind of topic index we just built.[1][2]
