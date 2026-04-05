# AGENTS.md - AI Maintainer Documentation

This document provides guidance for AI assistants (Claude, Copilot, etc.) working on the loop-core codebase.

## Project Overview

**loop-core** is a terminal-local state management library for Ralph-style autonomous loops. It provides file-based state persistence that avoids Git race conditions in multi-terminal environments.

**Key Characteristics:**
- **Python library** (pip-installable package, NOT a Claude Code plugin)
- **Backend utility** for state management, plan parsing, and terminal detection
- **Multi-terminal isolation**: Each terminal has its own state directory
- **Crash-safe**: Atomic writes prevent corrupted state
- **Zero TTL**: State persists until explicitly deleted

## Architecture

### Core Components

1. **TerminalStateManager** (`loop_core/state_manager.py`)
   - Manages terminal-local state with atomic writes
   - PID-based lock files with automatic stale cleanup
   - State directory: `.claude/state/terminals/{terminal_id}/`

2. **Plan Parser** (`loop_core/plan_parser.py`)
   - Extracts tasks from markdown plan files
   - Supports metadata: tags `[tag:name]`, dependencies `after:TASK-ID`
   - Returns structured task dictionaries

3. **Terminal Detection** (`loop_core/terminal_detection.py`)
   - 5-priority fallback system for terminal ID detection
   - Thread-local caching for consistency
   - Windows Terminal, Console, and PID-based fallback

4. **Task Patterns** (`loop_core/patterns/task_patterns.py`)
   - Regex patterns for markdown task detection
   - Matches `- [ ]` format with checkboxes

### Design Principles

- **File-based state**: JSON files in terminal-local directories
- **Atomic writes**: Temp file + rename pattern for crash safety
- **PID-based locks**: Automatic cleanup of stale locks
- **No TTL**: State persists until explicitly deleted
- **Multi-terminal safe**: Complete isolation between terminals

## Development Workflow

### Running Tests

```bash
# All tests
pytest tests/ -v --cov=loop_core

# Specific module
pytest tests/test_state_manager.py -v

# With coverage threshold
pytest tests/ -v --cov=loop_core --cov-report=term --cov-fail-under=70
```

### Code Quality

```bash
# Linting
ruff check .

# Formatting
ruff format .

# Type checking
mypy loop_core/
```

### Adding New Features

1. **Write tests first** (TDD approach)
2. **Implement feature** in appropriate module
3. **Add type hints** to all functions
4. **Update docstrings** with examples
5. **Run full test suite** to ensure no regressions

### Common Patterns

**Atomic state write**:
```python
def write_state(self, key: str, value: dict[str, Any]) -> None:
    state_file = self.state_dir / f"{key}.json"
    with tempfile.NamedTemporaryFile(
        mode="w", dir=self.state_dir,
        prefix=f".{key}_", suffix=".tmp",
        delete=False
    ) as tmp:
        json.dump(value, tmp, indent=2)
        tmp_path = Path(tmp.name)
    tmp_path.replace(state_file)  # Atomic rename
```

**Lock acquisition**:
```python
if manager.acquire_lock("resource"):
    try:
        # Critical section
        pass
    finally:
        manager.release_lock("resource")
```

**Terminal ID detection**:
```python
from loop_core.terminal_detection import get_terminal_id

# Auto-detect (uses 5-priority fallback)
terminal_id = get_terminal_id()

# Explicit terminal ID
terminal_id = get_terminal_id({"terminal_id": "custom_id"})
```

## Constraints

### MUST NOT

- Use Git for runtime state (causes race conditions)
- Use TTL-based state expiration (causes stale data)
- Use `os.replace()` directly for atomicity (use temp file pattern)
- Skip lock cleanup in finally blocks
- Ignore type hints or mypy errors

### MUST

- Use tempfile + os.replace() for atomic writes
- Always use try/finally for lock release
- Check return values from state operations (may be None)
- Handle OSError and JSONDecodeError
- Maintain 80%+ test coverage
- Follow Python 3.14+ standards

## Platform Considerations

### Windows-Specific

- Use `Path.resolve().parent` instead of `Path(__file__).parent`
- Handle both `\` and `/` path separators
- Test with WT_SESSION and GetConsoleWindow detection

### Cross-Platform

- Use `os.path.join()` or `pathlib.Path` for paths
- Avoid platform-specific code where possible
- Provide .bat equivalents for any .sh scripts

## Testing Strategy

### Unit Tests
- Test individual functions and methods
- Mock file system operations for isolation
- Test error paths (corrupted files, missing directories)

### Integration Tests
- Test multi-terminal isolation
- Test lock acquisition and release
- Test plan parsing with real markdown files

### Regression Tests
- Prevent breaking changes to public APIs
- Test compatibility with Python 3.14+
- Ensure atomic writes work across platforms

## Common Tasks

### Add new state operation

```python
def merge_state(self, key: str, updates: dict[str, Any]) -> dict[str, Any]:
    """Merge updates into existing state."""
    current = self.read_state(key) or {}
    current.update(updates)
    self.write_state(key, current)
    return current
```

### Add new plan metadata

1. Add pattern to `loop_core/patterns/task_patterns.py`
2. Update `parse_plan_tasks()` to extract new metadata
3. Update task schema in docstring
4. Add tests for new metadata type

### Extend terminal detection

Add new detection method to `_detect_console_terminal()`:
```python
def _detect_custom_terminal() -> str:
    """Detect custom terminal from environment."""
    custom_id = os.environ.get("CUSTOM_TERMINAL_ID")
    if custom_id:
        return f"custom_{custom_id[:8]}"
    return ""
```

## Troubleshooting

### Lock not releasing

**Problem**: Lock file persists after process exits.
**Solution**: PID-based cleanup will detect stale PID on next acquisition.

### State not persisting

**Problem**: `read_state()` returns None after `write_state()`.
**Solution**: Check terminal ID consistency - each terminal has its own state directory.

### Plan parsing fails

**Problem**: Tasks not extracted from markdown.
**Solution**: Ensure format is `- [ ]` with space after bracket (not `-[ ]`).

## Contact

For questions or issues, please open a GitHub issue or contact maintainers.

## Version History

See [CHANGELOG.md](CHANGELOG.md) for detailed version history.
