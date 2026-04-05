# TDD-95 Architecture: Frictionless Test-Driven Development

**Status**: Design Document - Ready for Implementation
**Created**: 2025-02-12
**Goal**: Make TDD the default for 95% of development work with near-zero friction

---

## Problem Statement

**Current State**: TDD exists but is rarely used (~5% of work).

**Root Causes Identified**:

1. **Complex State Machine** - 6 phases (IDLE, DISCOVER, AWAITING_RED, RED_CONFIRMED, GREEN_CONFIRMED, REFACTORING)
2. **Manual Activation Required** - Must invoke `/tdd` skill explicitly
3. **No Auto-Scaffolding** - Tests must be written manually from scratch
4. **Blocking Without Guidance** - PreToolUse_tdd_gate.py blocks edits but doesn't help create tests
5. **Opt-In vs Opt-Out** - TDD is "optional" by default, requiring explicit activation

**User Requirement**: TDD should be used 95% of the time, automatically, with minimal friction.

---

## Design Principles

1. **Default ON** - TDD is the default, not the exception
2. **Auto-Scaffold** - Tests are created automatically when impl files are created
3. **Smart Detection** - Recognize when TDD is needed vs when it's not
4. **Progressive Enhancement** - Simple path (auto-test) → full TDD cycle if needed
5. **Graceful Degradation** - Never block without offering a path forward

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                         TDD-95 SYSTEM                                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                       │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ PreWriteHook     │    │ AutoScaffolder   │    │ /tdd Skill    │  │
│  │ (detects impl    │───▶│ (creates test    │───▶│ (manual TDD   │  │
│  │  file creation) │    │  stub)           │    │  override)    │  │
│  └──────────────────┘    └──────────────────┘    └──────────────┘  │
│           │                       │                       │           │
│           ▼                       ▼                       ▼           │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │                    TDD State Manager (Simplified)             │  │
│  │  States: NONE → TEST_EXISTS → FAILING → PASSING → COMPLETE   │  │
│  └──────────────────────────────────────────────────────────────┘  │
│           │                       │                       │           │
│           ▼                       ▼                       ▼           │
│  ┌──────────────────┐    ┌──────────────────┐    ┌──────────────┐  │
│  │ PreToolUse Gate  │    │ PostToolUse      │    │ Test Runner  │  │
│  │ (blocks if       │    │ State Tracker    │    │ (detects     │  │
│  │  no test/fail)   │    │ (updates state)  │    │  results)    │  │
│  └──────────────────┘    └──────────────────┘    └──────────────┘  │
│                                                                       │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Simplified State Machine

**Current (6 states)**: IDLE → DISCOVER → AWAITING_RED → RED_CONFIRMED → GREEN_CONFIRMED → REFACTORING

**New (5 states)**:
```python
class TDD95State(Enum):
    NONE = "none"              # No test file exists
    TEST_EXISTS = "test_exists" # Test file created, not yet run
    FAILING = "failing"        # Test runs but fails (RED)
    PASSING = "passing"        # Test passes (GREEN)
    COMPLETE = "complete"      # TDD cycle done, can refactor
```

**Key Simplification**:
- Remove DISCOVER phase (too much friction)
- Remove AWAITING_RED vs RED_CONFIRMED distinction (just FAILING)
- Merge GREEN_CONFIRMED + REFACTORING into PASSING (can refactor while passing)

---

## Component 2: Auto-Scaffolding Hook

**File**: `P:\.claude\hooks\PostToolUse_tdd_autoscaffold.py`

**Trigger**: Write/Edit creates implementation file without corresponding test

**Behavior**:
1. Detect impl file creation: `src/module.py` written
2. Check if test exists: `tests/test_module.py`
3. If NO test exists → Auto-scaffold test stub
4. If YES test exists → Check if it's minimal/empty, suggest enhancement

**Test Stub Template**:
```python
#!/usr/bin/env python3
"""Test for {module_name} (auto-scaffolded)"""

import pytest
from {import_path} import {export_name}


def test_{module_name}_exists():
    """Smoke test: {module_name} can be imported."""
    assert {module_name} is not None


# TODO: Add more tests based on actual functionality
# Run: pytest tests/test_{module_name}.py -v
```

**Configuration** (settings.json):
```json
{
  "tdd95": {
    "autoscaffold_enabled": true,
    "test_patterns": [
      "tests/test_{stem}.py",
      "tests/{stem}_test.py",
      "test_{stem}.py"
    ],
    "exempt_patterns": [
      "**/__init__.py",
      "**/conftest.py",
      "**/tests/**/*.py"
    ]
  }
}
```

---

## Component 3: Smart TDD Detection

**File**: `P:\.claude\hooks\PreToolUse_tdd95_gate.py`

**Replaces**: `PreToolUse_tdd_gate.py` (skill-based version)

**Key Innovation**: Instead of complex state machine, use **evidence-based** checking:

```python
def should_allow_edit(file_path: str, test_file: str | None) -> tuple[bool, str]:
    """
    Evidence-based TDD checking.

    Allow if:
    1. File is exempt (docs, config, __init__.py)
    2. Test file exists AND test has been run recently (< 10 min)
    3. Edit is to test file itself
    4. /tdd skill is active (manual override)

    Block with help if:
    1. No test file exists → Auto-suggest test creation
    2. Test exists but never run → Suggest running test
    3. Test is failing → Allow (trying to fix)
    """
```

**Flowchart**:
```
┌─────────────────────────────────────────────────────────────┐
│  User: Edit src/module.py                                     │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  Is file exempt? ──YES──▶ ALLOW                              │
│       │                                                       │
│      NO                                                       │
│       │                                                       │
│  Does tests/test_module.py exist? ──NO──▶ AUTOSCAFFOLD + WARN │
│       │                                                       │
│      YES                                                      │
│       │                                                       │
│  Has test been run recently? ──NO──▶ ALLOW + SUGGEST RUN TEST │
│       │                                                       │
│      YES                                                      │
│       │                                                       │
│  Is test passing? ──NO──▶ ALLOW (fixing failure)             │
│       │                                                       │
│      YES                                                      │
│       │                                                       │
│  ALLOW (TDD satisfied)                                       │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## Component 4: Integration Test Runner

**File**: `P:\.claude\hooks\PostToolUse_tdd_runner.py`

**Trigger**: Bash command matches test pattern (`pytest`, `python -m test`, `npm test`, etc.)

**Behavior**:
1. Detect test execution
2. Parse results (using existing `TestResultParser` from `tdd_core.py`)
3. Update TDD state:
   - Failed → `TDD95State.FAILING`
   - Passed → `TDD95State.PASSING`
4. Run related tests if config enabled

**Configuration**:
```json
{
  "tdd95": {
    "auto_related_tests": true,
    "max_related_tests": 10,
    "test_commands": [
      "pytest",
      "python -m pytest",
      "python -m unittest",
      "npm test",
      "yarn test",
      "cargo test",
      "go test"
    ]
  }
}
```

---

## Component 5: /tdd Skill Integration

**Current**: `/tdd` skill must be manually invoked

**New**: Automatic detection + manual override

**Automatic Triggers** (from settings.json tdd.tiers):
- TIER0 (critical): `**/*.py`, `**/*.js`, `**/*.ts` → Auto-scaffold + warn
- TIER1 (production): `src/**`, `lib/**`, `app/**` → Auto-scaffold + warn
- TIER2 (experimental): `experimental/**` → Optional
- TIER3 (docs/tests): Exempt

**Manual Override**:
- User invokes `/tdd` → Full TDD cycle with PARALLEL subagents
- User sets `TDD_BYPASS=1` → Skip TDD for this session

**Activation Triggers** (existing, kept):
```python
activation_triggers: [
    'implement', 'refactor', 'fix', 'bug', 'broken', 'error',
    'add.*function', 'new feature', 'unit.*test', 'regression.*test'
]
```

---

## Implementation Plan

### Phase 1: Core Infrastructure (Day 1)

1. **Create `tdd95_core.py`** - Simplified state management
   - `TDD95State` enum (5 states)
   - `TDD95StateManager` class (load/save/cleanup)
   - Auto-scaffolding templates

2. **Create `PreToolUse_tdd95_gate.py`** - Evidence-based gate
   - Exemption checking
   - Test file detection
   - Test recency checking
   - Helpful block messages

3. **Create `PostToolUse_tdd_autoscaffold.py`** - Auto-test creation
   - Detect impl file write
   - Generate test stub
   - Write test file

### Phase 2: Test Integration (Day 2)

4. **Create `PostToolUse_tdd_runner.py`** - Test result tracking
   - Parse test output
   - Update state based on results
   - Run related tests

5. **Update `settings.json`** - TDD-95 configuration
   - `tdd95` section
   - Enable PreToolUse_tdd95_gate
   - Configure auto-scaffolding

### Phase 3: /tdd Skill Enhancement (Day 3)

6. **Update `/tdd` skill** - Integration with TDD-95
   - Read TDD95 state on skill start
   - Use simplified state
   - Provide exit summary

7. **Create migration script** - From old TDD to TDD-95
   - Convert existing TDD states
   - Clean up old state files

### Phase 4: Testing & Validation (Day 4)

8. **Create test suite** - `tests/test_tdd95_*.py`
   - Auto-scaffolding tests
   - Gate behavior tests
   - State management tests
   - Integration tests

9. **Manual validation** - Real workflow testing
   - Create new file → verify scaffold
   - Run failing test → verify state
   - Fix code → verify pass
   - Refactor → verify still pass

---

## Configuration Reference

### Full settings.json tdd95 section:

```json
{
  "tdd95": {
    "enabled": true,
    "enforcement_mode": "smart",

    "autoscaffold": {
      "enabled": true,
      "on_create": true,
      "on_edit_missing": true,
      "template": "minimal"
    },

    "gate": {
      "check_test_exists": true,
      "check_test_recency_minutes": 10,
      "check_test_passing": false,
      "block_on_missing": "warn",
      "block_on_stale": "suggest"
    },

    "test_runner": {
      "auto_detect": true,
      "auto_related": true,
      "max_related_tests": 10,
      "parallel_related": true
    },

    "exemptions": {
      "patterns": [
        "**/__init__.py",
        "**/conftest.py",
        "**/tests/**/*.py",
        "**/*.md",
        "**/*.json",
        "**/*.yaml"
      ],
      "directories": [
        "docs",
        "tests",
        ".git",
        "__pycache__"
      ]
    },

    "tiers": {
      "TIER0": {
        "enabled": true,
        "files": ["**/*.py", "**/*.js", "**/*.ts"],
        "action": "scaffold"
      },
      "TIER1": {
        "enabled": true,
        "files": ["src/**", "lib/**"],
        "action": "scaffold"
      },
      "TIER2": {
        "enabled": false,
        "files": ["experimental/**"],
        "action": "optional"
      }
    }
  }
}
```

---

## Migration from Existing TDD

### What Changes:

| Component | Old | New |
|-----------|-----|-----|
| State file | `P:/.claude/state/tdd/{terminal_id}/tdd.{hash}.json` | `P:/.claude/state/tdd95/{terminal_id}/{test_hash}.json` |
| State enum | `TDDPhase` (6 states) | `TDD95State` (5 states) |
| Gate hook | `PreToolUse_tdd_gate.py` (skill) | `PreToolUse_tdd95_gate.py` (global) |
| State tracker | `PostToolUse_tdd_state.py` | `PostToolUse_tdd_runner.py` |
| Auto-scaffold | None | `PostToolUse_tdd_autoscaffold.py` |

### Compatibility:

- Old `/tdd` skill continues to work
- Old TDD state files are read but migrated to new format
- `TDD_BYPASS=1` still works
- Exemption logic preserved

---

## Success Metrics

**Target**: 95% TDD adoption

**Measured by**:
1. **Test coverage**: % of code with tests (target: >80%)
2. **Test file ratio**: test files / impl files (target: >0.8)
3. **Autoscaffold usage**: % of impl files with scaffolded tests (target: >90%)
4. **Gate compliance**: % of edits passing TDD gate (target: >95%)

**Monitoring**:
```python
# Add to hooks/tests/test_tdd95_metrics.py
def measure_tdd_adoption():
    """Return TDD-95 adoption metrics."""
    impl_files = glob("**/*.py", exclude="tests/**")
    test_files = glob("tests/**/*.py")

    has_test = sum(1 for f in impl_files if has_corresponding_test(f))

    return {
        "coverage": has_test / len(impl_files) if impl_files else 0,
        "test_ratio": len(test_files) / len(impl_files) if impl_files else 0,
        "files_with_tests": has_test,
        "total_files": len(impl_files)
    }
```

---

## FAQ

### Q: Won't this slow me down?

**A**: Auto-scaffolding takes <100ms. The test stub is minimal. You can extend it or delete it. The goal is to make "no test" the exception, not the rule.

### Q: What if I don't want TDD for a quick fix?

**A**: Three options:
1. Set `TDD_BYPASS=1` in your environment
2. Use `/tdd` skill for manual control
3. Edit the test file directly (always allowed)

### Q: Does this work with existing tests?

**A**: Yes. TDD-95 detects existing tests and only scaffolds when missing.

### Q: What about non-Python code?

**A**: The architecture is language-agnostic. Auto-scaffolding templates can be added for JS, TS, Go, Rust, etc.

### Q: Can I customize the test template?

**A**: Yes. Add `tdd95.templates.custom` to settings.json with your template.

---

## Next Steps

1. **Review this design** - Confirm it addresses the 95% goal
2. **Approve implementation** - I'll implement Phase 1 (core infrastructure)
3. **Test drive** - Use TDD-95 for a real task and provide feedback
4. **Iterate** - Refine based on actual usage

---

## Appendix: File Manifest

```
P:\.claude\hooks\
├── tdd95_core.py                          # NEW: Simplified state management
├── PreToolUse_tdd95_gate.py               # NEW: Evidence-based gate
├── PostToolUse_tdd_autoscaffold.py        # NEW: Auto-test creation
├── PostToolUse_tdd_runner.py              # NEW: Test result tracking
├── tests\
│   ├── test_tdd95_autoscaffold.py         # NEW: Test auto-scaffolding
│   ├── test_tdd95_gate.py                 # NEW: Test gate behavior
│   ├── test_tdd95_runner.py               # NEW: Test result tracking
│   └── test_tdd95_migration.py            # NEW: Migration tests
└── .claude\
    └── settings.json                       # MODIFY: Add tdd95 section
```

**Estimated Implementation Time**: 4 days for full system, 1 day for MVP (core only)
