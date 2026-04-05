# Runbook: In-Process Hook Conversion for Immediate Effect

> **TL;DR**: Convert subprocess hooks to in-process functions to eliminate caching and enable immediate effect without session restart.

## Definition of Done
This is complete when:
- [ ] Hook function extracted to shared module
- [ ] Function registered in `IN_PROCESS_HOOKS`
- [ ] Router updated to use in-process version
- [ ] Testing confirms immediate effect
- [ ] Documentation updated

## When to Use This

Run this runbook when:
- Hook changes don't take effect until session restart
- Need immediate feedback during development
- Converting blocking hooks to in-process for performance

## The Process

### 1. Identify Cached Hook Problem

**Symptom**: Modified hook file (e.g., `PreToolUse_directory_policy.py`) but changes don't take effect. Router still uses old cached code.

**Root Cause**:
```python
# In PreToolUse.py router
import PreToolUse_directory_policy  # Cached at import time
```

Python caches imports at module level. Changes to the file aren't picked up until:
- Python process restarts, OR
- Function is moved to a module that gets re-imported

### 2. Extract Function to Shared Module

**Action**: Move function to `P:/.claude/hooks/__lib/` where it can be re-imported.

**Target**: Any function called by routers via `IN_PROCESS_HOOKS`

**Example**:
```python
# Original: P:/.claude/hooks/PreToolUse_directory_policy.py
def check_external_path_consent(file_path: str) -> tuple[bool, str]:
    # ... implementation

# Extracted to: P:/.claude/hooks/__lib/pre_tool_use_logic.py
def check_external_path_consent(file_path: str) -> tuple[bool, str]:
    # ... same implementation
```

**Benefits**:
- `__lib/` modules can be updated and re-imported
- Shared across multiple hooks
- No subprocess overhead

### 3. Register in IN_PROCESS_HOOKS

**Action**: Add function to `IN_PROCESS_HOOKS` dictionary in router.

**Location**: `P:/.claude/hooks/PreToolUse.py` (or relevant router)

**Code Pattern**:
```python
# At top of router
try:
    sys.path.insert(0, str(HOOKS_DIR / "__lib"))
    import pre_tool_use_logic

    IN_PROCESS_HOOKS = {
        "PreToolUse_syntax_gate.py": pre_tool_use_logic.check_syntax,
        "recursive_failure_detector.py": pre_tool_use_logic.check_recursive_failure,
        # ... other hooks
        "check_external_path_consent": pre_tool_use_logic.check_external_path_consent,  # NEW
    }
except ImportError as e:
    print(f"⚠️ Optimization Warning: Could not import in-process hooks: {e}", file=sys.stderr)
    IN_PROCESS_HOOKS = {}
```

### 4. Update Hook to Use In-Process First

**Action**: Modify hook's `run()` to try in-process import.

**Pattern**:
```python
def run(data: dict, verbose: bool = False) -> dict | None:
    # Try in-process first
    try:
        import pre_tool_use_logic
        if hasattr(pre_tool_use_logic, 'check_external_path_consent'):
            res = pre_tool_use_logic.check_external_path_consent(path)
            if res == "subprocess":
                pass  # Force subprocess fallback
            else:
                return res
    except Exception:
        pass  # Fall back to subprocess call
```

**Fallback Strategy**: If in-process import/call fails, use subprocess version.

### 5. Verify Immediate Effect

**Test**: Edit the function in `__lib/` and test immediately.

```bash
# 1. Edit function in __lib/pre_tool_use_logic.py
# 2. Test without session restart
python -c "
import sys
sys.path.insert(0, '.claude/hooks/__lib')
from pre_tool_use_logic import check_external_path_consent
print(check_external_path_consent('.claude/skills/test/file.txt'))
"
```

**Expected**: Changes take effect immediately.

### 6. Handle Path Resolution Issues

**Common Pitfall**: Functions using `Path(__file__).parent` get wrong directory.

**Problem**:
```python
# In __lib/pre_tool_use_logic.py
HOOKS_DIR = Path("P:/.claude/hooks")  # Resolved to import location
CLAUDE_DIR = HOOKS_DIR.parent  # Wrong! Gets P:/.claude/
```

**Fix**: Define paths explicitly or use correct anchor:
```python
HOOKS_DIR = Path("P:/.claude/hooks")
CLAUDE_DIR = HOOKS_DIR.parent.parent  # Gets P:/
```

Or import from context:
```python
from pathlib import Path
CLAUDE_DIR = Path("P:/")  # Explicit
```

## Verify Completion

- [x] Function extracted to `__lib/` module
- [x] Added to `IN_PROCESS_HOOKS` dictionary
- [x] Hook updated to try in-process first
- [x] Testing confirms immediate effect
- [x] Path resolution issues fixed
- [x] No session restart required for changes

## Performance Impact

| Metric | Before | After |
|--------|--------|-------|
| Hook execution | Subprocess (~50ms) | In-process (<1ms) |
| Cache invalidation | Session restart required | Immediate |
| Development velocity | Stop-edit-test loop | Continuous |

## When Things Go Wrong

| Error | Fix |
|-------|-----|
| `ImportError` | Check `sys.path.insert(0, str(HOOKS_DIR / "__lib"))` in router |
| `AttributeError: module has no attribute` | Verify function name matches in `IN_PROCESS_HOOKS` |
| Changes don't take effect | Router needs restart OR `IN_PROCESS_HOOKS` not updated |
| Path resolution wrong | Use `Path.cwd().parent` or explicit paths |
| Falls back to subprocess | Exception in try/except or function not in `__lib` |

## Related Documentation

- `P:/.claude/hooks/README.md` - Hook catalog
- `P:/.claude/hooks/ARCHITECTURE.md` - Constitutional enforcement
- `P:/.claude/hooks/PROTOCOL.md` - Hook specifications

## Examples

### Example 1: Simple Function Extraction

```python
# Original: PreToolUse_directory_policy.py
def my_check(data: dict) -> dict:
    file_path = data.get("file_path", "")
    # ... logic
    return {"decision": "block", "message": "reason"}

# Extracted to: pre_tool_use_logic.py
def my_check(file_path: str) -> dict:
    # ... same logic
    return {"decision": "block", "message": "reason"}
```

### Example 2: In-Process Registration

```python
# In PreToolUse.py router
IN_PROCESS_HOOKS = {
    "my_hook.py": lambda data: my_check(data.get("file_path", "")),
}
```

### Example 3: Fallback Pattern

```python
# In hook file
def run(data: dict) -> dict | None:
    try:
        import shared_logic
        return shared_logic.fast_check(data)
    except Exception:
        # Fallback to subprocess
        pass  # Continue to subprocess call
```
