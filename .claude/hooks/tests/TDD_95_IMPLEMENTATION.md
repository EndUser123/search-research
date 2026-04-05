# TDD-95 Implementation Guide

**Status**: Ready for Implementation
**Created**: 2026-02-12
**Goal**: Make TDD default for 95% of development work with near-zero friction

---

## Implementation Complete

All components have been created:

| Component | File | Status |
|-----------|------|--------|
| Core Module | `P:\.claude\hooks\tdd95_core.py` | ✅ Complete |
| Gate Hook | `P:\.claude\hooks\PreToolUse_tdd95_gate.py` | ✅ Complete |
| Auto-Scaffold Hook | `P:\.claude\hooks\PostToolUse_tdd95_autoscaffold.py` | ✅ Complete |
| Test Runner Hook | `P:\.claude\hooks\PostToolUse_tdd95_runner.py` | ✅ Complete |
| Critical Hooks Manifest | `P:\.claude\hooks\critical_hooks.json` | ✅ Complete |
| Settings Updated | `P:\.claude\settings.json` | ✅ Complete |

---

## File Layout

```
P:\.claude\
├── hooks\
│   ├── tdd95_core.py                          # Core module
│   ├── PreToolUse_tdd95_gate.py               # Gate hook
│   ├── PostToolUse_tdd95_autoscaffold.py        # Auto-scaffold
│   ├── PostToolUse_tdd95_runner.py              # Test runner
│   ├── critical_hooks.json                      # Critical hooks manifest
│   └── tests\
│       ├── test_tdd95_core_unit.py            # TODO: Core tests
│       ├── test_tdd95_autoscaffold_unit.py     # TODO: Scaffold tests
│       └── test_tdd95_gate_unit.py           # TODO: Gate tests
└── state\
    └── tdd95\                               # Auto-created state directory
        ├── {terminal_id}\                      # Per-terminal state
        │   ├── {hash}.json                    # File state
        └── global.json                         # Cross-terminal index
```

---

## Core Module: `tdd95_core.py`

### Path Handling (Windows-safe)

All path operations use `pathlib.Path` internally:

```python
# ALWAYS use this for path normalization
from tdd95_core import canonicalize_path, path_to_posix, path_from_posix

# Input: raw path string (may have backslashes, env vars, etc.)
impl_path = canonicalize_path("P:/project/src/module.py")

# Storage: always use POSIX-style for JSON
posix_str = path_to_posix(impl_path)  # "P:/project/src/module.py"

# Reconstruction: get back Path object
impl_path = path_from_posix(posix_str)
```

### State Enum

```python
class TDD95State(Enum):
    NONE = "none"              # No test file exists
    TEST_EXISTS = "test_exists" # Test file created, not yet run
    FAILING = "failing"        # Test runs but fails (RED)
    PASSING = "passing"        # Test passes (GREEN)
    COMPLETE = "complete"      # TDD cycle done, can refactor
```

### File ↔ Test Mapping

Python implementation → tests:
```python
from tdd95_core import get_test_candidates

# src/module.py → tests/test_module.py
candidates = get_test_candidates(impl_path)
# Returns: [Path("P:/project/tests/test_module.py")]
```

TypeScript implementation → tests:
```python
# src/module.ts → tests/module.test.ts
candidates = get_test_candidates(impl_path)
# Returns: [Path("P:/project/tests/module.test.ts")]
```

### Critical Hooks Detection

```python
from tdd95_core import is_critical_hook, get_critical_hook_tests

# Check if file is a critical hook
if is_critical_hook(impl_path):
    tests = get_critical_hook_tests(impl_path.stem)
    # tests.required_tests = ["tests/test_x_unit.py", ...]
    # tests.requires_integration = True
```

### State Manager

```python
from tdd95_core import TDD95StateManager

mgr = TDD95StateManager()  # Auto-detects terminal ID

# Record impl edit (creates state if needed)
mgr.record_impl_edit(impl_path)

# Record test run (updates all related impl files)
mgr.record_test_run(test_path, TDD95State.PASSING)

# Get current state
state = mgr.get_state_for_impl(impl_path)
# Returns FileState(impl_path, test_paths, state, last_test_run, ...)
```

---

## Gate Hook: `PreToolUse_tdd95_gate.py`

### Decision Flow

```
User: Edit src/module.py
│
├─ TDD_BYPASS=1? ─YES→ ALLOW immediately
│
├─ File exempt? ─YES→ ALLOW
│
├─ File is test? ─YES→ ALLOW
│
├─ Critical hook without tests?
│  └─ YES → BLOCK with scaffold offer
│
├─ No test file exists?
│  └─ YES → SCAFFOLD or WARN (based on config)
│
├─ Test exists but never run?
│  └─ YES → SUGGEST running tests
│
├─ Test failing? ─YES→ ALLOW (fixing failure)
│
└─ Test passing? ─YES→ ALLOW
```

### Configuration (from `tdd95` section in settings.json)

```json
{
  "tdd95": {
    "enabled": true,
    "enforcement_mode": "smart",  // smart, strict, warn, disabled

    "autoscaffold": {
      "enabled": true,
      "on_create": true,
      "on_edit_missing": true,
      "template": "minimal"  // minimal, full
    },

    "gate": {
      "check_test_exists": true,
      "check_test_recency_minutes": 10,
      "block_on_missing": "scaffold",  // warn, scaffold, block
      "block_on_stale": "suggest"  // suggest, block, allow
    },

    "exemptions": {
      "patterns": ["**/__init__.py", "**/*.md", ...],
      "directories": ["docs", "tests", ...]
    },

    "tiers": {
      "TIER0": {
        "files": ["**/*.py", "**/*.ts"],
        "action": "scaffold"
      },
      "TIER1": {
        "files": ["src/**", "lib/**"],
        "action": "scaffold"
      }
    },

    "critical_hooks": {
      "enabled": true,
      "require_integration_tests": true,
      "manifest_path": "P:/.claude/hooks/critical_hooks.json"
    }
  }
}
```

---

## Auto-Scaffold Hook: `PostToolUse_tdd95_autoscaffold.py`

### Triggers

- PostToolUse on Write/Edit of implementation files
- Only when test file doesn't exist
- Respects `tdd95.autoscaffold.enabled` config

### Test Templates

**Python Minimal Template:**
```python
"""Auto-scaffolded test for {module_name}."""

import pytest
from {import_path} import {export_name}

def test_{module_name}_exists():
    """Smoke test: {module_name} can be imported."""
    assert {export_name} is not None

# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_{module_name}.py -v
```

**Python Hook Template (for critical hooks):**
```python
"""Auto-scaffolded test for critical hook: {hook_name}."""

import pytest
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from {import_name} import main

def test_{hook_name}_exists():
    """Smoke test: {hook_name} can be imported."""
    assert main is not None

def test_{hook_name}_hook_structure():
    """Test that hook has required main() function."""
    assert callable(main)

def test_{hook_name}_input_output():
    """Test hook processes JSON input and outputs JSON."""
    # ... subprocess test ...

# TODO: Add integration-style tests with realistic tool sequences
```

**TypeScript Template:**
```typescript
/**
 * Auto-scaffolded test for {module_name}
 */

import {{ {export_name} }} from './{module_path}';

describe('{module_name}', () => {{
  it('should exist', () => {{
    expect({export_name}).toBeDefined();
  }});

  // TODO: Add more tests
  // Run: npm test -- {test_file}
}});
```

---

## Test Runner Hook: `PostToolUse_tdd95_runner.py`

### Test Command Detection

```python
# Detects these patterns as test commands:
PYTHON_TEST_COMMANDS = {
    "pytest",
    "python -m pytest",
    "python -m unittest",
}

TS_TEST_COMMANDS = {
    "npm test",
    "pnpm test",
    "yarn test",
    "npx vitest",
    "npx jest",
}
```

### Result Parsing

```python
def parse_test_result(command, exit_code, stdout, stderr):
    """
    Returns (TDD95State, details_message)

    Detection priority:
    1. Error patterns (AssertionError, FAILED, ×, etc.)
    2. Pass patterns (passed, ✓, √)
    3. Exit code (non-zero = fail)
    """
```

---

## Critical Hooks Manifest

Located at: `P:\.claude\hooks\critical_hooks.json`

### Format

```json
{
  "hook_name": {
    "required_tests": [
      "tests/test_hook_name_unit.py",
      "tests/test_hook_name_integration.py"
    ],
    "requires_integration": true,
    "description": "Human-readable description"
  }
}
```

### Detection Methods

1. **Manifest file**: Explicit entries in `critical_hooks.json`
2. **Naming convention**: `@critical_hook` marker in hook file
3. **Hook directory**: Hooks under `P:\.claude/hooks/` are candidates

### Enforcement

- Critical hook edits are **BLOCKED** if required tests are missing
- Integration tests must simulate realistic tool sequences
- Unit tests cover individual functions

---

## Multi-Terminal Coordination

### Architecture

```
Each terminal has:
- P:/.claude/state/tdd95/{terminal_id}/
  └── {hash}.json  (file-specific state)

Shared global index:
- P:/.claude/state/tdd95/global.json
  ├── version: "1"
  ├── files: {
  │   "P:/project/src/module.py": {
  │     "impl_path": "P:/project/src/module.py",
  │     "test_paths": ["P:/project/tests/test_module.py"],
  │     "state": "passing",
  │     "last_test_run": "2026-02-12T12:00:00",
  │     ...
  │   }
  ├── last_updated: "2026-02-12T12:00:00"
```

### Terminal ID Detection

Uses existing `terminal_detection.py`:
- Priority: `CLAUDE_TERMINAL_ID` env var (process-scoped)
- Fallback: ConsoleHost handle (Windows)
- Last resort: `fallback_1`

### Conflict Handling

- **Last write wins** for global index updates
- File-level locking for per-terminal state files
- No git dependency - all state from file tracking

---

## Environment Variables

| Variable | Default | Purpose |
|-----------|---------|---------|
| `TDD_BYPASS` | 0 | Skip TDD for this session |
| `TDD95_ENABLED` | true | Master enable/disable |
| `CLAUDE_TERMINAL_ID` | auto | Terminal isolation |

---

## Registration in settings.json

### PreToolUse Registration

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          {
            "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PreToolUse_tdd95_gate.py --timeout 3.0",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

### PostToolUse Registration

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "^(Write|Edit|MultiEdit)$",
        "hooks": [
          {
            "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_tdd95_autoscaffold.py --timeout 5.0",
            "timeout": 5
          }
        ]
      }
    ]
  }
}
```

### Bash Registration (for test runner)

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "^Bash$",
        "hooks": [
          {
            "command": "python P:/.claude/hooks/__lib/hook_runner.py P:/.claude/hooks/PostToolUse_tdd95_runner.py --timeout 3.0",
            "timeout": 3
          }
        ]
      }
    ]
  }
}
```

---

## Usage Examples

### Example 1: New Python File

```
User: Create a new module
AI: [Writes src/calculator.py]

→ PostToolUse_tdd95_autoscaffold.py triggers
→ Creates tests/test_calculator.py with minimal stub

→ User sees:
"Auto-scaffolded test: tests/test_calculator.py"
```

### Example 2: Editing Critical Hook

```
User: Fix the assumption audit hook
AI: [Edit P:/.claude/hooks/assumption_audit_v2.py]

→ PreToolUse_tdd95_gate.py triggers
→ Checks critical_hooks.json
→ Missing tests: tests/test_assumption_audit_v2_unit.py

→ Gate BLOCKS with message:
"Critical hook requires tests. Create them first:
- Create test: tests/test_assumption_audit_v2_unit.py"
```

### Example 3: Running Tests

```
User: Run pytest
AI: [Bash: pytest tests/test_calculator.py]

→ PostToolUse_tdd95_runner.py triggers
→ Detects test command
→ Parses output (exit code, stdout)
→ Updates state for src/calculator.py

→ State transitions: TEST_EXISTS → FAILING or PASSING
```

### Example 4: TDD Bypass

```
User: Quick fix without tests
AI: Set TDD_BYPASS=1, then edit file

→ PreToolUse_tdd95_gate.py sees TDD_BYPASS=1
→ Allows immediately with bypass message
```

---

## Testing TDD-95

### Unit Tests

```bash
# Test core functionality
pytest P:/.claude/hooks/tests/test_tdd95_core_unit.py -v

# Test path handling (Windows-specific)
pytest P:/.claude/hooks/tests/test_tdd95_paths.py -v
```

### Integration Tests

```bash
# Test full workflow
pytest P:/.claude/hooks/tests/test_tdd95_workflow_integration.py -v

# Test multi-terminal scenarios
pytest P:/.claude/hooks/tests/test_tdd95_multi_terminal.py -v
```

### Manual Validation

1. Create new file → verify scaffold appears
2. Run failing test → verify state transitions
3. Fix code → verify pass transition
4. Edit test file → verify allowed
5. Set TDD_BYPASS=1 → verify bypass works

---

## Troubleshooting

### Hook Not Firing

1. Check registration in settings.json
2. Check `tdd95.enabled` in settings.json
3. Check hook file syntax: `python -m py_compile <hook>.py`

### State Issues

1. Check state directory: `P:/.claude/state/tdd95/`
2. Check terminal ID: `echo $CLAUDE_TERMINAL_ID`
3. Enable debug: Set `CSF_HOOK_DEBUG=1`

### Path Issues on Windows

1. Always use `canonicalize_path()` from tdd95_core
2. Never do manual string replace on paths
3. Use `Path.match()` for glob patterns
4. Store as POSIX: `path_to_posix()`, load with `path_from_posix()`

---

## Design Principles Reference

| Principle | Implementation |
|-----------|----------------|
| Default ON | `tdd95.enabled: true` in settings.json |
| Auto-Scaffold | `PostToolUse_tdd95_autoscaffold.py` |
| Smart Detection | Evidence-based checks in gate hook |
| Progressive Enhancement | Simple scaffold → full TDD cycle via /tdd |
| Graceful Degradation | Never block without actionable message |
| No Git Dependency | State from files only, not git diff |
| Windows-Safe | `pathlib.Path` everywhere, POSIX storage |
| Multi-Terminal | Per-terminal state + global index |
| Python + TS Only | Configured via `tdd95.tiers` |

---

## Next Steps

1. **Create tests** - Implement test suite in `tests/test_tdd95_*.py`
2. **Manual testing** - Use TDD-95 for real work
3. **Metrics monitoring** - Track adoption rate over time
4. **Refinement** - Adjust thresholds based on usage
