# Hook stderr Usage Style Guide

## Purpose

Prevent false "hook error" messages in Claude Code UI by using stderr correctly.

## Problem

Claude Code's UI treats **any stderr output** as "hook error" and displays it with the ⏿ prefix. Informational success messages printed to stderr cause misleading "hook error" notifications even when the hook works correctly.

## Rule

**Only print to stderr for:**
1. Actual errors (exceptions, failures)
2. Blocking actions (denied operations, violations)
3. Warning conditions (⚠️) that require user attention

**Do NOT print to stderr for:**
1. Success confirmations (✓, ✅)
2. Informational status ("Using feature X", "Loaded Y")
3. Debug logging (use DEBUG environment variable)

## Patterns

### ❌ WRONG (causes false "hook error" messages)

```python
# Success messages in stderr
print("✓ Operation completed", file=sys.stderr)
print("✅ Auto-stored 5 items", file=sys.stderr)
print("Loaded configuration", file=sys.stderr)

# Debug output in stderr
print(f"Processing {item}", file=sys.stderr)
print(f"Result: {result}", file=sys.stderr)
```

### ✅ CORRECT

```python
# Silent success
# (no output)

# Error messages in stderr
print(f"Error: {error_message}", file=sys.stderr)
print(f"⚠️ Warning: {warning}", file=sys.stderr)

# Blocked operations in stderr
print(f"🚫 Blocked: {reason}", file=sys.stderr)

# Debug output gated on environment variable
DEBUG = os.environ.get("HOOK_DEBUG", "0") == "1"
if DEBUG:
    print(f"Processing {item}", file=sys.stderr)
```

## Quick Reference

| Situation | Use stderr? | Example |
|-----------|-------------|---------|
| Hook blocked an action | ✅ Yes | `print("🚫 Path denied", file=sys.stderr)` |
| Hook encountered error | ✅ Yes | `print(f"Error: {e}", file=sys.stderr)` |
| Hook warning | ✅ Yes | `print("⚠️ Config missing", file=sys.stderr)` |
| Hook succeeded | ❌ No | (silent) |
| Hook status/info | ❌ No | Use DEBUG gate |
| Debug logging | ❌ No | Gate on DEBUG env var |

## DEBUG Variable Naming

Use descriptive names for DEBUG environment variables:

```python
# Good - specific to hook
DEBUG = os.environ.get("HOOK_NAME_DEBUG", "0") == "1"

# Examples:
HANDOFF_DEBUG = os.environ.get("HANDOFF_DEBUG", "0") == "1"
AUTO_CKS_DEBUG = os.environ.get("AUTO_CKS_DEBUG", "0") == "1"
CODE_VERIFICATION_DEBUG = os.environ.get("CODE_VERIFICATION_DEBUG", "0") == "1"
```

## Testing

To verify a hook doesn't produce spurious stderr:

```bash
# Run hook with empty input
echo '{}' | python hook_name.py 2>&1

# Should see only:
# - JSON output on stdout
# - No stderr output (unless actual error)
```

## Migration Checklist

When auditing hooks for stderr misuse:

- [ ] Search for `print.*file=sys.stderr`
- [ ] Identify lines that aren't errors/warnings/blocks
- [ ] Remove or gate on DEBUG variable
- [ ] Test hook produces clean output
- [ ] Verify JSON output on stdout

## References

- Fixed hooks: `agent_handoff_validator.py`, `auto_cks_storage.py`, `conversation_storage.py`, `commit_forgetfulness_check.py`, `PostToolUse_code_verification_gate.py`, `PostToolUse_outcome_validator.py`
- Related: `error_attribution_tracker.py` context filtering (filters ⏿ prefixed lines)
