# Claude Code Hook Protocol v2.1

**Purpose**: Document actual (not assumed) hook input/output formats.

**Updated**: 2026-03-12 - Standardized on stdout JSON as the primary contract

---

## Key Insight

Most hooks in this repo are executed through wrapper layers such as
`hook_runner.py` or `hook_importer.py`. Those wrappers capture stdout/stderr,
normalize some legacy behavior, and forward structured output back to Claude Code.

Because of that, the primary hook contract for this repo is:

- Emit structured JSON on stdout for any intentional decision or message
- Exit `0` after emitting that payload
- Use file-based logging for diagnostics
- Reserve `stderr` for last-resort runner failures or compatibility shims

Legacy `stderr` + exit-code patterns may still be normalized by wrappers, but
they should be treated as compatibility behavior, not the target design for new hooks.

---

## UserPromptSubmit

Fires before Claude processes user's message.

### Input (JSON via stdin)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `prompt` | string | Yes | User's message text |

### Output

| Format | Description |
|--------|-------------|
| Raw text (no JSON) | Context to inject into conversation |

### Exit Code

| Code | Meaning |
|------|---------|
| 0 | Always exit 0 |

---

## PreToolUse

Fires before a tool is executed. Can block execution.

### Input (JSON via stdin)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_name` | string | Yes | Name of tool being called |
| `tool_input` | dict | Yes | Parameters passed to the tool |

### Output Options

**Recommended: structured JSON on stdout**
```python
output = {
    "hookSpecificOutput": {
        "hookEventName": "PreToolUse",
        "permissionDecision": "deny",  # or "allow" or "ask"
        "permissionDecisionReason": "Why blocked"
    }
}
print(json.dumps(output))
sys.exit(0)
```

**Compatibility only: legacy stderr + exit code**
```python
print("Blocked: reason here", file=sys.stderr)
sys.exit(2)
```

Use this only when a wrapper explicitly depends on it or when maintaining an
older direct hook. Do not use it for new routed hooks.

### Exit Code

| Code | Meaning |
|------|---------|
| 0 | Success - parse stdout for JSON |
| 2 | Legacy block path; wrappers may normalize it |

### permissionDecision Values

| Value | Effect |
|-------|--------|
| `deny` | Block tool execution, reason shown to Claude |
| `allow` | Permit execution, bypass permission prompt |
| `ask` | Prompt user for confirmation |
| `modify` | Modify tool input and continue execution (see below) |

### Modify Decision (NEW)

The `modify` decision allows hooks to correct tool input before execution. This is useful for:
- Auto-fixing syntax errors (e.g., Windows backslashes → forward slashes in bash paths)
- Normalizing parameters (e.g., adding default values, correcting typos)
- Security hardening (e.g., adding escape sequences, sanitizing input)

**Modify Decision Format:**
```python
return {
    "decision": "modify",
    "tool_input": {
        # Modified tool input fields
        "command": 'ls "P:/.claude/hooks"'  # Fixed backslashes
    }
}
```

**Example: Auto-fix Windows paths in bash commands**
```python
def check_windows_paths_in_bash(data):
    """Detect and fix Windows backslash paths in bash commands."""
    command = data["tool_input"].get("command", "")

    # Detect Windows drive paths with backslashes
    if not re.search(r'[A-Za-z]:\\', command):
        return None

    # Build corrected version
    fixed = re.sub(r'[A-Za-z]:\\[^\s"\']*',
                   lambda m: m.group(0).replace("\\", "/"),
                   command)

    # Return modify decision
    return {
        "decision": "modify",
        "tool_input": {"command": fixed}
    }
```

**Behavior:**
- Hooks continue processing after modify (loop doesn't break)
- Modified `tool_input` is merged into the data passed to subsequent hooks
- Final modified data is output to Claude Code for execution
- Malformed modify responses (missing `tool_input`) fall back to block

**Backward Compatibility:**
- Existing hooks returning `deny`, `allow`, `ask`, or `None` work unchanged
- Hooks that don't return `decision` field are treated as `None` (allow)

### Working References

- Direct: `path_resolution_orchestrator.py` (uses exit 2)
- Routed: `PreToolUse_tdd_gate.py` (uses JSON)
- Modify: `PreToolUse_bash_syntax_validator.py` (auto-fixes Windows backslash paths)

---

## PostToolUse

Fires after a tool completes. Advisory only - cannot block.

### Input (JSON via stdin)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `tool_name` | string | Yes | Name of tool that was called |
| `tool_input` | dict | Yes | Parameters passed to the tool |
| `tool_response` | dict | Yes | Result returned by the tool |

### Output (JSON via stdout)

```python
# Provide feedback to Claude
output = {
    "hookSpecificOutput": {
        "hookEventName": "PostToolUse",
        "additionalContext": "Feedback message"
    }
}
print(json.dumps(output))
sys.exit(0)
```

### Exit Code

| Code | Meaning |
|------|---------|
| 0 | Always exit 0 |

---

## Stop

Fires when Claude is about to stop responding. Can block stopping.

### Input (JSON via stdin)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transcript_path` | string | No | Path to conversation transcript |
| `conversation` | array | No | Array of conversation messages |
| `response` | string | No | Claude's response text |

### Output

**To block (force continuation):**
```python
output = {"decision": "block", "reason": "What to do instead"}
print(json.dumps(output))
sys.exit(0)
```

**To allow (let Claude stop):**
```python
print("{}")
sys.exit(0)
```

### Exit Code

| Code | Meaning |
|------|---------|
| 0 | Success - parse stdout for JSON |
| 2 | Legacy compatibility path only |

---

## Router Implementation

Wrappers that call hooks via subprocess MUST treat stdout JSON as the primary contract.
Compatibility handling for legacy exit-code hooks may still be needed:

```python
def run_hook_subprocess(hook_name: str, input_data: dict) -> dict | None:
    result = subprocess.run(...)
    
    # Primary path: parse JSON output first
    payload = json.loads(result.stdout.decode() or "{}")
    ...

    # Compatibility path for legacy hooks
    if result.returncode == 2:
        stderr_msg = result.stderr.decode().strip()
        ...
```

Wrappers should also avoid re-emitting child-hook stderr back to Claude Code
unless they intentionally want Claude Code to render a hook error.

---

## Importer Diagnostics Contract

`hook_importer.py` records importer anomalies in the shared SQLite diagnostics
database at `P:/.claude/hooks/logs/diagnostics/diagnostics.db`.

This is the primary diagnostics contract for importer failures. Standalone
`hook_importer_*.jsonl` files are fallback-only and should appear only if the
SQLite diagnostics path is unavailable.

### Logged Phases

- `load` - module import or exec failure while loading a hook
- `execute` - runtime exception in hook execution or importer runtime failure
- `timeout` - hook thread exceeded timeout
- `stderr` - captured child-hook stderr was non-empty

### Required Fields

Each importer anomaly record should include:

- `hook_name`
- `phase`
- `session_id` when present in hook input
- `terminal_id` when present in hook input
- `tool_name` when present in hook input
- `input_hash` - short hash of raw stdin payload
- `input_bytes` - raw stdin size in bytes
- `error_text`
- `traceback` when available

### Retention And Maintenance

- Importer diagnostics older than 14 days are pruned by default
- Pruning runs at most once per 24 hours
- Optional `VACUUM` may run after pruning when the database exceeds the
  configured size threshold
- Environment overrides:
  - `CC_IMPORTER_RETENTION_DAYS`
  - `CC_IMPORTER_VACUUM_INTERVAL_HOURS`
  - `CC_IMPORTER_VACUUM_THRESHOLD_BYTES`

---

## Repo Guidance

- New hooks should emit structured JSON on stdout.
- Existing hooks that still use `stderr` + exit codes should be migrated when touched.
- Diagnostics belong in logs, not stderr.
- If a hook is executed through `hook_runner.py` or `hook_importer.py`, assume
  stdout JSON is required unless that wrapper explicitly documents otherwise.

---

## Fixed Routers (2026-01-23)

| Router | Status | Hooks Affected |
|--------|--------|----------------|
| `PreToolUse_bash_router.py` | ✅ Fixed v1.1 | authorization_gate, falsification_gate, tdd_gate |
| `PreToolUse_write_router.py` | ✅ Fixed v1.4 | session_reversion_check, exec_orchestrator |
| `Stop_router.py` | ✅ Fixed v1.1 | All Stop hooks |
| `path_resolution_orchestrator.py` | N/A (direct) | deny_root_write |

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 2.1 | 2026-03-12 | Standardized stdout JSON as primary contract; relegated stderr/exit-code behavior to compatibility only |
| 2.0 | 2026-01-23 | Fixed router exit code handling, clarified direct vs routed |
| 1.0 | 2025-01-09 | Initial documentation |
