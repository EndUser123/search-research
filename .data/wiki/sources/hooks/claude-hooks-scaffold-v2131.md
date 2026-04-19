# Claude Code Hooks – Scaffold & Starter Kit (v2.1.31)

**Purpose**: Go from zero to fully-hooked environment in 5 minutes with production-ready patterns.

**Prerequisites**: 
- Claude Code v2.1.31+
- Python 3.8+ (for Python examples) or Bash
- `jq` installed (optional but recommended for JSON manipulation)

---

## Table of Contents

1. [Quick Start (Copy-Paste Setup)](#quick-start-copy-paste-setup)
2. [Directory Structure](#directory-structure)
3. [Configuration Files](#configuration-files)
4. [Master Scripts (Production-Ready)](#master-scripts-production-ready)
5. [Testing Harness](#testing-harness)
6. [Validation Checklist](#validation-checklist)
7. [Common Customizations](#common-customizations)
8. [Troubleshooting](#troubleshooting)

---

## Quick Start (Copy-Paste Setup)

Run this in your project root to create the complete structure:

```bash
# Create directory structure
mkdir -p .claude/hooks .claude/logs

# Create hook scripts
cat > .claude/hooks/master_prompt.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Master UserPromptSubmit Handler
Implements: Logging → Validation → Context Injection
"""
import sys
import json
import datetime
import pathlib

# --- CONFIGURATION (Edit these for your project) ---
PROJECT_RULES = """
Project Guidelines (injected by hook):
1. Use TypeScript for all new code; match existing style in legacy files
2. Write unit tests for non-trivial logic
3. No console.log in production code; use proper logging
4. Run tests before claiming work complete
"""

DANGEROUS_PATTERNS = [
    "rm -rf /",
    "rm -rf .",
    "drop database",
    "drop table",
    "truncate table",
    "delete from",
    "format c:",
    "sudo rm"
]

def get_log_path():
    """Returns project-local log path."""
    try:
        cwd = pathlib.Path.cwd()
        log_dir = cwd / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "user_prompts.jsonl"
    except Exception:
        # Fallback to home directory if project dir unavailable
        home = pathlib.Path.home()
        log_dir = home / ".claude" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir / "global_prompts.jsonl"

def log_prompt(data):
    """
    Async-safe logging: writes to disk but swallows errors.
    Never blocks user interaction.
    """
    try:
        log_path = get_log_path()
        entry = {
            "ts": datetime.datetime.now().isoformat(),
            "session_id": data.get("session_id", "unknown"),
            "prompt_preview": data.get("prompt", "")[:200],  # First 200 chars
            "cwd": data.get("cwd", "")
        }
        with log_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        # Log to stderr for debugging, but don't fail
        print(f"[Hook Warning] Logging failed: {e}", file=sys.stderr)

def validate_prompt(prompt):
    """
    Returns (is_blocked, reason).
    Checks for obviously dangerous patterns.
    """
    prompt_lower = prompt.lower()
    for pattern in DANGEROUS_PATTERNS:
        if pattern in prompt_lower:
            return True, f"Blocked: prompt contains dangerous pattern '{pattern}'"
    return False, None

def main():
    # 1. Read stdin (Claude's JSON input)
    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
    except json.JSONDecodeError as e:
        print(f"[Hook Error] JSON parse failed: {e}", file=sys.stderr)
        sys.exit(0)  # Fail open: don't block on parse errors
    except Exception as e:
        print(f"[Hook Error] Unexpected error: {e}", file=sys.stderr)
        sys.exit(0)

    prompt = data.get("prompt", "")

    # 2. Telemetry (fire-and-forget; never blocks)
    log_prompt(data)

    # 3. Validation (blocking if dangerous)
    is_blocked, reason = validate_prompt(prompt)
    if is_blocked:
        # Return JSON decision to block
        output = {
            "decision": "block",
            "reason": reason
        }
        print(json.dumps(output))
        sys.exit(0)

    # 4. Context injection (append rules to Claude's context)
    print(PROJECT_RULES)
    sys.exit(0)

if __name__ == "__main__":
    main()
PYTHON_EOF

cat > .claude/hooks/master_tool.py << 'PYTHON_EOF'
#!/usr/bin/env python3
"""
Master PreToolUse Handler
Validates and gates tool execution (especially Bash, Write, Edit)
"""
import sys
import json

# --- CONFIGURATION ---
BASH_BLOCKLIST = [
    "sudo",
    "rm -rf /",
    "dd if=",
    "mkfs",
    "format",
    "> /dev/",
    "curl | bash",
    "wget | sh"
]

BASH_ALLOWLIST_PREFIXES = [
    "npm test",
    "npm run test",
    "pytest",
    "cargo test",
    "go test",
    "make test"
]

PROTECTED_FILES = [
    "package.json",
    "Cargo.toml",
    "go.mod",
    ".env",
    ".env.production",
    "docker-compose.yml",
    "terraform.tfvars"
]

def validate_bash_command(cmd):
    """Returns (allow, reason)."""
    cmd_lower = cmd.lower().strip()
    
    # Check allowlist first (auto-approve)
    for prefix in BASH_ALLOWLIST_PREFIXES:
        if cmd_lower.startswith(prefix.lower()):
            return True, "Auto-approved: safe test command"
    
    # Check blocklist
    for pattern in BASH_BLOCKLIST:
        if pattern in cmd_lower:
            return False, f"Blocked: command contains dangerous pattern '{pattern}'"
    
    # Default: allow but log
    return True, "Allowed (default)"

def validate_file_write(path):
    """Returns (allow, reason)."""
    filename = path.split("/")[-1]
    
    if filename in PROTECTED_FILES:
        return False, f"Blocked: '{filename}' is a protected file. Manual review required."
    
    return True, "Allowed"

def main():
    try:
        raw_input = sys.stdin.read()
        data = json.loads(raw_input) if raw_input.strip() else {}
    except Exception as e:
        print(f"[Hook Error] {e}", file=sys.stderr)
        sys.exit(0)
    
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input", {})
    
    # Handle Bash tool
    if tool_name == "Bash":
        cmd = tool_input.get("command", "")
        allow, reason = validate_bash_command(cmd)
        
        if not allow:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason
                }
            }
            print(json.dumps(output))
            sys.exit(0)
    
    # Handle Write/Edit tools
    elif tool_name in ["Write", "Edit"]:
        path = tool_input.get("path", "")
        allow, reason = validate_file_write(path)
        
        if not allow:
            output = {
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "deny",
                    "permissionDecisionReason": reason
                }
            }
            print(json.dumps(output))
            sys.exit(0)
    
    # Default: allow
    sys.exit(0)

if __name__ == "__main__":
    main()
PYTHON_EOF

# Make scripts executable
chmod +x .claude/hooks/*.py

# Create settings.json
cat > .claude/settings.json << 'JSON_EOF'
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Master prompt handler: logging, validation, context injection",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master_prompt.py",
            "async": false,
            "timeout": 30
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",
        "description": "Tool validation and safety gates",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master_tool.py",
            "async": false,
            "timeout": 30
          }
        ]
      }
    ]
  }
}
JSON_EOF

# Create README
cat > .claude/hooks/README.md << 'README_EOF'
# Project Hooks Documentation

## Active Hooks

### UserPromptSubmit
- **Script**: `master_prompt.py`
- **Purpose**: Validates prompts, blocks dangerous patterns, injects project rules
- **Mode**: Sync (blocking)
- **What it blocks**: Commands like `rm -rf /`, `drop table`, etc.
- **What it injects**: Project coding guidelines on every prompt

### PreToolUse (Bash|Write|Edit)
- **Script**: `master_tool.py`
- **Purpose**: Gates tool execution to prevent dangerous operations
- **Mode**: Sync (blocking)
- **What it blocks**: 
  - Bash: `sudo`, destructive commands, pipe-to-shell
  - Write/Edit: Protected config files (package.json, .env, etc.)
- **What it allows**: Test commands auto-approved

## Logs

Prompt logs stored in: `.claude/logs/user_prompts.jsonl`

View recent prompts:
```bash
tail -20 .claude/logs/user_prompts.jsonl | jq -r '.prompt_preview'
```

## Customization

Edit the configuration sections in:
- `master_prompt.py` → `PROJECT_RULES`, `DANGEROUS_PATTERNS`
- `master_tool.py` → `BASH_BLOCKLIST`, `PROTECTED_FILES`

## Testing

Test hooks locally without Claude:
```bash
echo '{"prompt":"rm -rf /"}' | python3 .claude/hooks/master_prompt.py
```

See `mock-claude.py` in this directory for full testing harness.
README_EOF

echo "✅ Hook scaffold created successfully!"
echo ""
echo "Next steps:"
echo "1. Review .claude/settings.json"
echo "2. Customize rules in .claude/hooks/master_*.py"
echo "3. Test with: echo '{\"prompt\":\"test\"}' | python3 .claude/hooks/master_prompt.py"
echo "4. Start Claude Code and verify with /hooks command"
```

---

## Frontmatter Hooks for Skills (Claude Code 2.1+)

**Skills and agents can define hooks directly in their SKILL.md frontmatter.** This is the recommended pattern for skill-specific behavior enforcement.

**Why frontmatter hooks:**
- **Self-contained**: Hook travels with the skill; no external config required
- **Scoped**: Only runs when skill is invoked; no global side effects
- **Distributable**: Skills with hooks work out-of-box when shared
- **Auto-discovery**: No settings.json editing required for skill users

### Example: Workflow Enforcement Hook

```yaml
---
name: task
description: Task orchestration
category: workflow
triggers:
  - /task

hooks:
  PostToolUse:
    - type: prompt
      prompt: |
        Verify /task list workflow was executed completely:
        1. TaskList() was called
        2. Results were filtered by terminal_id
        3. /search was called for context
        4. CHS search for unresolved items

        If any step was skipped, return {"ok": false, "reason": "..."}
      model: haiku
      timeout: 30
user-invocable: true
---

# /task - Task Orchestration

## Purpose

Orchestrator for Claude Code task list operations...
```

### Quick Start: Add Frontmatter Hook to Existing Skill

```bash
# Edit your skill's SKILL.md
cd .claude/skills/your-skill

# Add hooks section to frontmatter
# See example above for format
```

### Frontmatter Hook Reference

| Event | When it fires | Use for |
|-------|---------------|---------|
| `UserPromptSubmit` | Before skill executes | Validate/modify user input |
| `PreToolUse` | Before tool call during skill | Intercept/modify tool calls |
| `PostToolUse` | After tool call completes | Verify workflow execution |
| `Stop` | When skill claims done | Prevent incomplete termination |

### Handler Types

| Type | Description | Speed | Tool Access |
|------|-------------|-------|-------------|
| `prompt` | LLM decision (fast) | Fast | No |
| `agent` | Full subagent | Slow | Yes |
| `command` | Shell script | Fast | No (not recommended) |

### When to Use Frontmatter vs Settings.json

| Scenario | Recommended approach |
|----------|---------------------|
| Skill-specific workflow enforcement | **Frontmatter hooks** in SKILL.md |
| Project-wide policies (linting, security) | `.claude/settings.json` |
| Cross-project standards | `~/.claude/settings.json` |

---

## Directory Structure

After running the setup, you'll have:

```
.claude/
├── settings.json           # Hook configuration (commit to git)
├── hooks/
│   ├── README.md          # Documentation (commit to git)
│   ├── master_prompt.py   # UserPromptSubmit handler (commit to git)
│   ├── master_tool.py     # PreToolUse handler (commit to git)
│   └── mock-claude.py     # Testing harness (optional)
└── logs/
    └── user_prompts.jsonl # Prompt logs (add to .gitignore)
```

**Gitignore recommendations**:
```bash
echo ".claude/logs/" >> .gitignore
echo ".claude/settings.local.json" >> .gitignore
```

---

## Configuration Files

### `.claude/settings.json` (Annotated)

```json
{
  "hooks": {
    "UserPromptSubmit": [
      {
        "description": "Master prompt handler: logging, validation, context injection",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master_prompt.py",
            "async": false,  // Sync: must complete before Claude sees prompt
            "timeout": 30    // Fail after 30s
          }
        ]
      }
    ],
    "PreToolUse": [
      {
        "matcher": "Bash|Write|Edit",  // Regex on tool names
        "description": "Tool validation and safety gates",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/master_tool.py",
            "async": false,
            "timeout": 30
          }
        ]
      }
    ]
  }
}
```

**Key points**:
- Use `$CLAUDE_PROJECT_DIR` for portability across machines
- `async: false` for all decision-making hooks
- `matcher` is case-sensitive regex
- `description` field is optional but recommended for documentation

---

## Master Scripts (Production-Ready)

The scaffold includes two production-ready master scripts with:

### `master_prompt.py` Features

✅ **Graceful error handling**: Never blocks on logging failures  
✅ **JSON parse safety**: Fails open if input is malformed  
✅ **Configurable rules**: Edit `PROJECT_RULES` and `DANGEROUS_PATTERNS`  
✅ **Local + global logging**: Falls back to home directory if project log unavailable  
✅ **Truncated logging**: Only logs first 200 chars (privacy + performance)  
✅ **Proper exit codes**: Exit 0 with JSON decision for blocks  

### `master_tool.py` Features

✅ **Allowlist + blocklist**: Auto-approve safe commands, block dangerous ones  
✅ **Protected files**: Prevents accidental edits to critical configs  
✅ **Tool-specific validation**: Different logic for Bash vs Write vs Edit  
✅ **Clear feedback**: Detailed reasons for blocks  
✅ **Extensible**: Easy to add new tools or patterns  

### Customization Points

**In `master_prompt.py`**:
```python
# Line ~11: Edit project-specific rules
PROJECT_RULES = """
Your project guidelines here
"""

# Line ~18: Add/remove dangerous patterns
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "your-dangerous-pattern",
]
```

**In `master_tool.py`**:
```python
# Line ~10: Edit Bash blocklist
BASH_BLOCKLIST = [
    "sudo",
    "your-blocked-command",
]

# Line ~18: Edit test command allowlist
BASH_ALLOWLIST_PREFIXES = [
    "npm test",
    "your-safe-command",
]

# Line ~26: Edit protected files
PROTECTED_FILES = [
    "package.json",
    "your-critical-file.conf",
]
```

---

## Testing Harness

### `mock-claude.py` - Local Hook Tester

Save this as `.claude/hooks/mock-claude.py`:

```python
#!/usr/bin/env python3
"""
Mock Claude Hook Harness
Simulates Claude Code calling your hooks with sample JSON.

Usage:
  ./mock-claude.py prompt ./.claude/hooks/master_prompt.py
  ./mock-claude.py tool ./.claude/hooks/master_tool.py

Events: prompt, tool, session_start
"""
import sys
import json
import subprocess
import time
from pathlib import Path

# Sample inputs for different events
SAMPLE_DATA = {
    "prompt": {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Please delete the database using DROP TABLE",
        "session_id": "mock-session-123",
        "cwd": str(Path.cwd()),
        "transcript_path": "/tmp/mock-transcript.jsonl"
    },
    "prompt_safe": {
        "hook_event_name": "UserPromptSubmit",
        "prompt": "Write a function to calculate factorial",
        "session_id": "mock-session-123",
        "cwd": str(Path.cwd())
    },
    "tool": {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "sudo rm -rf /"},
        "session_id": "mock-session-123",
        "cwd": str(Path.cwd())
    },
    "tool_safe": {
        "hook_event_name": "PreToolUse",
        "tool_name": "Bash",
        "tool_input": {"command": "npm test"},
        "session_id": "mock-session-123",
        "cwd": str(Path.cwd())
    },
    "session_start": {
        "hook_event_name": "SessionStart",
        "session_id": "mock-session-123",
        "session_source": "startup",
        "cwd": str(Path.cwd())
    }
}

def run_test(event_type, script_path, custom_data=None):
    """Run a hook with sample data and display results."""
    if event_type not in SAMPLE_DATA and not custom_data:
        print(f"❌ Unknown event type: {event_type}")
        print(f"Available: {list(SAMPLE_DATA.keys())}")
        sys.exit(1)
    
    payload = json.dumps(custom_data if custom_data else SAMPLE_DATA[event_type])
    
    print("=" * 60)
    print(f"🧪 Testing Hook: {script_path}")
    print(f"📋 Event: {event_type}")
    print(f"📥 Input Payload:")
    print(json.dumps(json.loads(payload), indent=2))
    print("-" * 60)
    
    start = time.time()
    
    try:
        # Determine execution command
        if script_path.endswith('.py'):
            cmd = [sys.executable, script_path]
        else:
            cmd = [script_path]
        
        # Run hook process
        process = subprocess.Popen(
            cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=Path.cwd()
        )
        
        stdout, stderr = process.communicate(input=payload, timeout=30)
        duration = (time.time() - start) * 1000
        
        print(f"⏱️  Duration: {duration:.2f}ms")
        print(f"🔢 Exit Code: {process.returncode}")
        print()
        
        # Parse and display output
        print("📤 STDOUT (What Claude sees):")
        if stdout.strip():
            try:
                parsed = json.loads(stdout)
                print(json.dumps(parsed, indent=2))
                
                # Interpret decision
                if "decision" in parsed:
                    if parsed["decision"] == "block":
                        print("\n🛑 DECISION: BLOCKED")
                        print(f"Reason: {parsed.get('reason', 'No reason given')}")
                    else:
                        print(f"\n✓ DECISION: {parsed['decision']}")
                        
                if "hookSpecificOutput" in parsed:
                    decision = parsed["hookSpecificOutput"].get("permissionDecision")
                    if decision:
                        symbol = "🛑" if decision == "deny" else "✓"
                        print(f"\n{symbol} PERMISSION DECISION: {decision.upper()}")
                        reason = parsed["hookSpecificOutput"].get("permissionDecisionReason")
                        if reason:
                            print(f"Reason: {reason}")
            except json.JSONDecodeError:
                # Plain text output
                print(stdout)
        else:
            print("(empty)")
        
        print()
        print("⚠️  STDERR (Debug/Errors):")
        print(stderr if stderr.strip() else "(empty)")
        print()
        print("-" * 60)
        
        # Final verdict
        if process.returncode == 0:
            if stdout.strip() and "block" in stdout.lower():
                print("✅ Test Result: Hook executed and BLOCKED action")
            else:
                print("✅ Test Result: Hook executed successfully")
        elif process.returncode == 2:
            print("🛑 Test Result: Hook intentionally BLOCKED (exit 2)")
        else:
            print("❌ Test Result: Hook failed with error")
        
        print("=" * 60)
        return process.returncode
        
    except subprocess.TimeoutExpired:
        print("⏱️  ERROR: Hook timed out after 30s")
        process.kill()
        return -1
    except Exception as e:
        print(f"❌ ERROR: {e}")
        return -1

def main():
    if len(sys.argv) < 3:
        print(__doc__)
        print("\nExamples:")
        print("  ./mock-claude.py prompt ./.claude/hooks/master_prompt.py")
        print("  ./mock-claude.py prompt_safe ./.claude/hooks/master_prompt.py")
        print("  ./mock-claude.py tool ./.claude/hooks/master_tool.py")
        print("  ./mock-claude.py tool_safe ./.claude/hooks/master_tool.py")
        sys.exit(1)
    
    event_type = sys.argv[1]
    script_path = sys.argv[2]
    
    # Validate script exists
    if not Path(script_path).exists():
        print(f"❌ Script not found: {script_path}")
        sys.exit(1)
    
    run_test(event_type, script_path)

if __name__ == "__main__":
    main()
```

Make it executable:
```bash
chmod +x .claude/hooks/mock-claude.py
```

### Usage Examples

```bash
# Test prompt validation (should block)
./.claude/hooks/mock-claude.py prompt ./.claude/hooks/master_prompt.py

# Test safe prompt (should allow + inject rules)
./.claude/hooks/mock-claude.py prompt_safe ./.claude/hooks/master_prompt.py

# Test dangerous bash command (should block)
./.claude/hooks/mock-claude.py tool ./.claude/hooks/master_tool.py

# Test safe bash command (should auto-approve)
./.claude/hooks/mock-claude.py tool_safe ./.claude/hooks/master_tool.py
```

---

## Validation Checklist

After setup, validate your hooks work correctly:

### 1. Verify Files Exist
```bash
ls -la .claude/hooks/
# Should show: master_prompt.py, master_tool.py, README.md (all executable)

ls -la .claude/settings.json
# Should exist
```

### 2. Test Scripts Locally
```bash
# Test dangerous prompt (should block)
echo '{"prompt":"rm -rf /"}' | python3 .claude/hooks/master_prompt.py
# Expected: JSON with "decision": "block"

# Test safe prompt (should inject rules)
echo '{"prompt":"write a function"}' | python3 .claude/hooks/master_prompt.py
# Expected: Plain text with PROJECT_RULES

# Test dangerous bash (should block)
echo '{"tool_name":"Bash","tool_input":{"command":"sudo rm"}}' | \
  python3 .claude/hooks/master_tool.py
# Expected: JSON with permissionDecision: "deny"
```

### 3. Verify in Claude Code
```bash
claude code
/hooks
# Should see your hooks listed under UserPromptSubmit and PreToolUse
```

### 4. Test Live Blocking
In Claude Code session:
```
User: "Please run: rm -rf /"
# Should be blocked before Claude sees it

User: "Edit package.json and change version"
# Should be blocked with message about protected file
```

### 5. Check Logs
```bash
tail .claude/logs/user_prompts.jsonl
# Should show logged prompts
```

---

## Common Customizations

### Add More Dangerous Patterns

Edit `master_prompt.py`:
```python
DANGEROUS_PATTERNS = [
    "rm -rf /",
    "drop database",
    # Add your patterns:
    "exec(",           # Prevent code execution
    "eval(",
    "__import__",
    "system(",
]
```

### Add Project-Specific Bash Blocklist

Edit `master_tool.py`:
```python
BASH_BLOCKLIST = [
    "sudo",
    "rm -rf",
    # Add project-specific:
    "docker rm",       # Prevent container deletion
    "kubectl delete",  # Prevent k8s resource deletion
    "terraform destroy",
]
```

### Add Auto-Approve Patterns

Edit `master_tool.py`:
```python
BASH_ALLOWLIST_PREFIXES = [
    "npm test",
    "pytest",
    # Add your safe commands:
    "npm run lint",
    "cargo check",
    "make build",
]
```

### Add Async Logging Hook

Edit `.claude/settings.json` to add async telemetry:
```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": ".*",
        "description": "Log all tool usage",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/log_tools.py",
            "async": true,
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Add SessionStart Setup

```json
{
  "hooks": {
    "SessionStart": [
      {
        "matcher": "startup",
        "hooks": [
          {
            "type": "command",
            "command": "$CLAUDE_PROJECT_DIR/.claude/hooks/session_init.sh"
          }
        ]
      }
    ]
  }
}
```

---

## Troubleshooting

### Hook Not Firing

**Symptom**: Hook doesn't appear in `/hooks` or doesn't execute

**Solutions**:
1. Check JSON syntax: `jq . .claude/settings.json`
2. Verify script is executable: `chmod +x .claude/hooks/*.py`
3. Test script manually: `echo '{}' | python3 .claude/hooks/master_prompt.py`
4. Restart Claude Code: `/reload` or restart session
5. Check matcher syntax: Use regex tester for pattern

### Hook Fires But No Effect

**Symptom**: Hook runs but doesn't block/inject context

**Solutions**:
1. Check exit code: Script must exit 0
2. Verify stdout: `echo '{"prompt":"test"}' | script.py`
3. Check for stderr leakage: Might be going to wrong stream
4. Use `mock-claude.py` to see exact output
5. Check `async` field: Async hooks' output is ignored

### JSON Parse Error

**Symptom**: "Hook output does not start with {"

**Solutions**:
1. Check for shell profile echo: `~/.bashrc`, `~/.bash_profile`
2. Wrap profile output: `if [[ $- == *i* ]]; then echo ...; fi`
3. Test stdin parsing: `echo '{"test":1}' | python3 -c 'import sys,json; print(json.load(sys.stdin))'`
4. Ensure no `print()` debug statements before final output

### Hook Too Slow

**Symptom**: Hooks add noticeable latency

**Solutions**:
1. Use `async: true` for non-decision hooks
2. Reduce logging frequency
3. Cache expensive operations
4. Lower `timeout` value to fail faster
5. Profile script: `time echo '{}' | script.py`

### Protected File Not Blocking

**Symptom**: Edit to package.json not blocked

**Solutions**:
1. Check `matcher`: Must include `Write|Edit`
2. Verify tool name in input: `echo '{"tool_name":"Edit"}' | script.py`
3. Case sensitivity: Tool names are case-sensitive
4. Check file path extraction logic in script

### Windows-Specific Issues

**Symptom**: Hooks fail on Windows

**Solutions**:
1. Use Python instead of Bash scripts
2. Set Git Bash path: `$env:CLAUDE_CODE_GIT_BASH_PATH`
3. Use forward slashes in paths: `.claude/hooks/script.py`
4. Test with: `python .claude\hooks\script.py < test.json`
5. Check file permissions: Windows may need explicit executable flag

---

## Next Steps

1. **Review the Operational Guide** for deep dives into each event type
2. **Review the Conceptual Guide** for strategy and mental models
3. **Customize rules** in the master scripts for your project
4. **Add more hooks** as needed (SessionStart, PostToolUse, Stop, etc.)
5. **Monitor logs** to understand Claude's behavior patterns
6. **Iterate** based on what you observe being blocked/allowed

---

## See Also

- [Claude Code Hooks – Operational Guide](./claude-hooks-ops-v2131.md)
- [Claude Code Hooks – Conceptual Guide](./claude-hooks-concept-v2131.md)
- [Official Hooks Reference](https://code.claude.com/docs/en/hooks)
