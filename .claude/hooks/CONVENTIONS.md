# Claude Code Hook Conventions

This document defines standard conventions for Claude Code skill-based hooks to ensure consistency across the ecosystem.

## Exit Code Conventions

All hooks MUST use these exit codes to indicate their decision:

| Exit Code | Meaning | When to Use |
|-----------|---------|-------------|
| **0** | Pass/Allow | Action is permitted, session can continue |
| **1** | Advisory warning | Action allowed, but warning message shown to user |
| **2** | Block | Action denied, user must retry or fix the issue |

### Exit Code by Hook Type

Different hook events have specific expectations:

| Hook Event | Exit 0 | Exit 1 | Exit 2 |
|------------|--------|--------|--------|
| **PreToolUse** | Allow/pass-through | Advisory only - warn but allow | **Block** the tool from executing |
| **PostToolUse** | Always exit 0 | Advisory only - show warning | Never use (PostToolUse should not block) |
| **Stop** | Allow session to end | Advisory only - show warning | **Block** session end (force continuation) |
| **UserPromptSubmit** | Always exit 0 | Advisory only - inject context | Never use (UserPromptSubmit should not block) |

### Examples

**PreToolUse blocking (Exit 2):**
```python
def run(data: dict) -> dict:
    if not_meets_preconditions(data):
        print("Action blocked: reason...")
        return {"continue": False, "reason": "Preconditions not met"}
    return {"continue": True}
```

**Stop hook blocking (Exit 2):**
```python
def run(data: dict) -> dict:
    if not_verified_success(data):
        print("Cannot stop: verification incomplete")
        return {"allow": False, "reason": "Verification incomplete"}
    return {"allow": True}
```

## Scope Guard Pattern

Hooks SHOULD implement scope guards to skip execution when the skill was never invoked.

**Purpose**: Prevents running verification hooks when the skill was never used, reducing unnecessary overhead.

**Pattern:**
```python
from hook_platform import scope_guard_check

should_skip, reason = scope_guard_check(
    project_root,
    "skill-state-{terminal_id}",  # State directory pattern
    terminal_id
)

if should_skip:
    print(f"Scope guard: {reason}")
    return 0  # Skip (pass)
```

**State Directory Patterns:**

| Skill | Pattern | Location |
|-------|---------|----------|
| GTO | `gto-state-{terminal_id}` | `.evidence/gto-state-{terminal_id}/` |
| /arch | `arch-decisions-{terminal_id}` | `.claude/arch_decisions/arch_{terminal_id}/` |

## Platform Detection

Use the shared `run_platform_hook()` function for cross-platform hook execution:

```python
from hook_platform import run_platform_hook

exit_code, stdout, stderr = run_platform_hook(
    script_dir=Path(__file__).parent,
    script_name="hook_name",  # Will resolve to hook_name.ps1 or hook_name.sh
    env={"VAR": "value"},
    timeout=30,
)
```

**Script naming:**
- Windows: `hook_name.ps1` (PowerShell)
- Unix/Linux/macOS: `hook_name.sh` (Bash)

## JSON Output Format

Hooks that return JSON MUST use these schemas:

### PreToolUse Output
```json
{
  "continue": true|false,
  "reason": "Explanation (required if continue=false)"
}
```

### Stop Output
```json
{
  "allow": true|false,
  "reason": "Explanation (required if allow=false)"
}
```

### PostToolUse Output
```json
{
  "warning": "Advisory message (optional)",
  "additionalContext": "Context injection (optional)"
}
```

### UserPromptSubmit Output
```json
{
  "additionalContext": "Context text to inject (optional)"
}
```

## Logging Best Practices

1. **Use stdout, not stderr**: Claude Code treats stderr as errors
2. **Structured JSON for hooks**: Use JSON output format for hook decisions
3. **Human-readable for users**: Use plain text for user-facing messages

**Anti-pattern:**
```python
print("Error occurred", file=sys.stderr)  # ❌ TRIGGERS FALSE ERROR
```

**Correct pattern:**
```python
print("Status message", file=sys.stdout)  # ✅ OK
print(json.dumps({"allow": False, "reason": "..."}))  # ✅ OK
```

## Version History

- 2026-03-23: Initial version - exit codes, scope guards, platform detection
