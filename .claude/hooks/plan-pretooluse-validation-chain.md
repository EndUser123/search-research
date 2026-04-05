# Plan: PreToolUse Validation Chain

## Overview
Build a PreToolUse validation chain to catch syntax/coding errors BEFORE tool execution, shifting from reactive PostToolUse validation to proactive PreToolUse validation.

## Architecture
Three independent PreToolUse hooks in validation chain:
1. **PreToolUse_python_c_syntax_gate.py** - Wrapper around existing check_python_c() from __lib/pre_tool_use_logic.py
2. **PreToolUse_bash_syntax_gate.py** - NEW: bash -n for syntax validation
3. **PreToolUse_ruff_check_gate.py** - NEW: ruff check --no-fix for linting

## Data Flow
```
User invokes Bash/Edit/Write tool
    ↓
PreToolUse event triggers
    ↓
Chain runs sequentially (independent):
    1. PreToolUse_python_c_syntax_gate (if Bash + python -c)
    2. PreToolUse_bash_syntax_gate (if Bash)
    3. PreToolUse_ruff_check_gate (if Write/Edit .py)
    ↓
If ALL gates pass (or don't apply) → Allow tool execution
If ANY gate blocks → Block with error message
```

## Error Handling
- Each gate has enabled/mode env vars for graceful degradation
- Modes: off (skip), warn (allow with message), block (halt execution)
- Missing tools (ruff, bash) → Gate logs warning and allows (fail-open)
- Invalid JSON input → Gate allows (fail-safe)

## Test Strategy

### Unit Tests (per gate)
- **PreToolUse_python_c_syntax_gate.py**:
  - Valid python -c → allow
  - Invalid syntax → block
  - Shell-escape normalization → auto-fix
  - Not a python -c command → allow

- **PreToolUse_bash_syntax_gate.py**:
  - Valid bash command → allow
  - Invalid syntax (e.g., unescaped backslash) → block
  - Not a bash command → allow
  - bash not available → allow (fail-open)

- **PreToolUse_ruff_check_gate.py**:
  - Clean .py file → allow
  - Ruff errors → block
  - Not a .py file → allow
  - ruff not available → allow (fail-open)

### Integration Tests
- All three gates registered in settings.json
- Chain validation order (python-c → bash → ruff)
- Env var overrides (enabled/mode)

### Regression Tests
- Existing PostToolUse_bash_syntax_gate.py still works
- Existing PreToolUse_python_c_validator.py behavior unchanged

## Standards Compliance
- **Python**: PEP 8, type hints, docstrings
- **Hook protocol**: Exit 0 (allow), exit 2 (block)
- **Error handling**: Graceful degradation, fail-safe defaults
- **Testing**: pytest with >80% coverage

## Ramifications
- **Breaking changes**: None (additive only)
- **Performance**: 10-50ms overhead per gate (acceptable)
- **Backwards compatibility**: Existing gates unchanged
- **Configuration**: Env vars for each gate (default: warn mode)

## Pre-Mortem Analysis

### Failure Mode 1: Gate blocks legitimate workflow
**Scenario**: Ruff gate blocks development code with style violations
**Root cause**: Overly strict linting in development phase
**Prevention**: Warn mode by default, block mode opt-in
**Test**: Test with intentionally messy code (verify warn allows it)

### Failure Mode 2: Bash syntax gate has false positives
**Scenario**: Valid bash command blocked as "syntax error"
**Root cause**: bash -n is stricter than actual bash execution
**Prevention**: Validate gate against common bash patterns (heredocs, pipes, redirects)
**Test**: Test real bash commands from codebase (git log, grep, sed)

### Failure Mode 3: Missing tool causes excessive warnings
**Scenario**: ruff not installed, every write shows warning
**Root cause**: No graceful degradation when tool missing
**Prevention**: Check tool availability once, cache result, silent fail-open
**Test**: Test with ruff missing from PATH (verify no spam)

## Observability
- **Metrics**: Gate execution time, block/warn/allow counts
- **Logs**: Hook execution log in state/logs/
- **Alerts**: High block rate (>10%) indicates over-sensitive gate
- **Diagnosis**: First check - run hooks in verbose mode to see which gate blocks
