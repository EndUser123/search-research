# Hook Development Guide

## Hook Development Checklist

Before committing a new hook:

- [ ] No `print(..., file=sys.stderr)` anywhere in hook
- [ ] Use `logging` module with `NullHandler` for debug output
- [ ] File-based logging to `hooks/logs/*.jsonl` for errors
- [ ] Test with `pytest tests/test_no_stderr_in_hooks.py`
- [ ] Verify no "hook error" messages in Claude Code after tool operations

## StdErr Anti-Pattern

**Problem**: Claude Code treats ANY stderr output from hooks as "hook error" message, even when the hook succeeds.

**Root Cause**: Direct `print(..., file=sys.stderr)` calls trigger Claude Code's error detection system.

## Correct Pattern

```python
import logging
import json
from pathlib import Path

# Logging setup with NullHandler (prevents stderr output)
HOOKS_DIR = Path(__file__).parent
logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())
log_dir = HOOKS_DIR / "logs"
log_dir.mkdir(parents=True, exist_ok=True)
log_file = log_dir / "hook_errors.jsonl"

# Inside error handling:
try:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_record) + "\n")
except (OSError, IOError):
    pass  # Best-effort logging, never block hook execution
```

## Debug Mode Pattern

```python
import os

# Optional debug mode
ROUTER_DEBUG = os.environ.get("ROUTER_DEBUG", "0") == "1"

# Only print to stdout in debug mode
if ROUTER_DEBUG:
    print(f"Debug info: {data}", file=sys.stdout)
```

## Detection

Run test: `pytest P:/.claude/hooks/tests/test_no_stderr_in_hooks.py`

## Prevention

Pre-commit hook scans for `print\(.*file=sys\.stderr\)` pattern in Python files.

## Common Mistakes

### ❌ Wrong: Direct stderr writes
```python
print("Hook error occurred", file=sys.stderr)  # TRIGGERS FALSE ERROR
```

### ❌ Wrong: Using sys.stderr.write()
```python
sys.stderr.write("Error message\n")  # TRIGGERS FALSE ERROR
```

### ✅ Correct: File-based logging
```python
try:
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps({"error": "message"}) + "\n")
except (OSError, IOError):
    pass  # Best-effort, never block
```

### ✅ Correct: Stdout in debug mode
```python
if ROUTER_DEBUG:
    print(f"Debug: {info}", file=sys.stdout)
```

## Related Documentation

- `CLAUDE.md` - Main hooks documentation with logging best practices
- `C:/Users/brsth/.claude/projects/P--/memory/bugfixes.md` - Historical bug fixes including Hook StdErr Anti-Pattern (2026-03-07)
- `tests/test_no_stderr_in_hooks.py` - Regression test for stderr writes
