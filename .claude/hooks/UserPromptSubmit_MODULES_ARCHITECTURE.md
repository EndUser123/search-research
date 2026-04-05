# UserPromptSubmit Hook Architecture

## Overview

The UserPromptSubmit hook uses a modular architecture with a router file and a package directory to avoid Python module naming conflicts.

## Problem Solved

**Issue**: Python's module import system treats `.py` files and package directories with the same name as conflicting. When both `UserPromptSubmit.py` and `UserPromptSubmit/` exist, the `.py` file shadows the package directory, causing `ImportError: attempted relative import with no known parent package`.

**Example of the problem**:
```python
# This fails if UserPromptSubmit.py exists
from UserPromptSubmit import registry  # Imports .py file, not package
# Then within UserPromptSubmit.py:
from UserPromptSubmit_modules import registry  # Relative import fails
```

## Solution

**Rename the package** to avoid naming conflict:
- Router file: `UserPromptSubmit.py` (kept as-is for HookImporter compatibility)
- Package directory: `UserPromptSubmit_modules/` (renamed from `UserPromptSubmit/`)

## Directory Structure

```
.claude/hooks/
├── UserPromptSubmit.py                 # Router entry point (main hook)
├── UserPromptSubmit_modules/           # Package directory (renamed)
│   ├── __init__.py                     # Package init with backward compatibility alias
│   ├── registry.py                     # Hook discovery and loading
│   ├── base.py                         # Base classes (HookContext, HookResult)
│   ├── conversation_gate.py            # Question/conversation intent guard
│   ├── unified_injector.py             # Solo dev context, goal anchor, falsification
│   ├── skill_enforcer.py               # Slash command detection and routing
│   ├── plan_injector.py                # Plan context injection and disambiguation
│   ├── diagnostic_guard.py             # Speculative claims, quantitative checks
│   └── intent_handlers.py              # Research directives, diagnostic questions
```

## Import Patterns

### Router File (UserPromptSubmit.py)

```python
# Router imports from the renamed package
from UserPromptSubmit_modules import registry
```

### Package Imports

```python
# Other modules can import from the package
from UserPromptSubmit_modules import registry, base

# Relative imports within the package work correctly
from .base import HookContext, HookResult
```

### Backward Compatibility

The `__init__.py` creates a sys.modules alias for backward compatibility:

```python
# UserPromptSubmit_modules/__init__.py
import sys

# Create alias for old package name
if __name__ == "UserPromptSubmit_modules":
    sys.modules["UserPromptSubmit"] = sys.modules["UserPromptSubmit_modules"]
```

This allows legacy imports to continue working:
```python
# Old import style still works via alias
import UserPromptSubmit  # Resolves to UserPromptSubmit_modules
```

## Key Design Decisions

### 1. Package Renaming (Not Router File)

**Decision**: Rename package directory, not router file
**Rationale**:
- HookImporter expects hooks to be named `{HookName}.py`
- Router file name is fixed by Claude Code hook system
- Package can have any name without breaking hook discovery

### 2. Backward Compatibility Alias

**Decision**: Create sys.modules alias instead of breaking changes
**Rationale**:
- Allows existing code to continue using old import style
- No need to update all import statements immediately
- Graceful migration path for dependent code

### 3. Separate Test Suites

**Decision**: Create dedicated test files for different concerns
**Rationale**:
- `test_multi_terminal_hooks.py`: Subprocess isolation testing
- `test_hook_loading.py`: Module import validation
- Each test suite can run independently
- Easier to identify which layer is failing

## Integration Points

### HookImporter System

```python
# HookImporter loads hooks by name
importer = HookImporter('P:/.claude/hooks')
result = importer.execute_hook('UserPromptSubmit')
# Looks for UserPromptSubmit.py
```

### Git Pre-Commit Hook

```python
# Automatically clears bytecode caches before commits
# Prevents stale .pyc files from causing import errors
# Location: .git/hooks/pre-commit
```

### SessionStart Health Check

```python
# Monitors hook import health at session start
# Early warning of module loading issues
# File: SessionStart_hook_import_health.py
```

## Testing

### Multi-Terminal Verification

```bash
# Run subprocess isolation tests
python .claude/hooks/tests/test_multi_terminal_hooks.py

# Expected output:
# Testing: UserPromptSubmit imports... ✓ PASS
# Testing: Registry imports... ✓ PASS
# Testing: Relative imports... ✓ PASS
# Testing: Backward compatibility... ✓ PASS
```

### Hook Loading Coverage

```bash
# Run comprehensive import tests
python .claude/hooks/tests/test_hook_loading.py

# Expected output:
# Results: 14 passed, 0 failed
```

## Maintenance Guidelines

### Adding New Hooks

1. Create new module in `UserPromptSubmit_modules/`
2. Register in `registry.py`:
   ```python
   @register_hook(priority=5.0)
   def my_new_hook(data, prompt, ctx=None):
       # Hook implementation
       pass
   ```
3. Add to `__init__.py` `__all__` list
4. Write tests in `test_hook_loading.py`

### Avoiding Naming Conflicts

**DO**:
- Package name: `{HookName}_modules/`
- Router file: `{HookName}.py`

**DON'T**:
- Package name: `{HookName}/` (conflicts with .py file)
- Both `{HookName}.py` and `{HookName}/` in same directory

### Debugging Import Errors

1. Check for naming conflicts
2. Clear bytecode caches: `find . -name __pycache__ -exec rm -rf {} +`
3. Run test suites: `python tests/test_multi_terminal_hooks.py`
4. Check SessionStart health check output

## Related Documentation

- `CLAUDE.md` - Hooks directory architecture and hook registration patterns
- `PROTOCOL.md` - Hook input/output specifications
- `README.md` - Complete hook catalog and usage guide
- `bugfixes.md` - Historical fixes for similar issues

## History

- **2026-03-06**: Package renamed from `UserPromptSubmit/` to `UserPromptSubmit_modules/` to resolve import shadowing issue
- **2026-03-06**: Added backward compatibility alias via sys.modules
- **2026-03-06**: Added git pre-commit hook for bytecode cache cleanup
- **2026-03-06**: Added multi-terminal and hook loading test suites
- **2026-03-06**: Added SessionStart health check for early warning

## See Also

- `bugfixes.md`: "Redis Import Crash - Python 3.14 Incompatibility" (similar bytecode cache issue)
- `test_multi_terminal_hooks.py`: Subprocess isolation tests
- `test_hook_loading.py`: Comprehensive import validation
- `SessionStart_hook_import_health.py`: Session start health monitoring
