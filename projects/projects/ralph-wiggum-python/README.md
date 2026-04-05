# Ralph Wiggum Python Plugin

Windows-compatible Python version of the Ralph Wiggum loop plugin.

## What This Does

- **Ralph Loop**: Self-referential development loop - your output is fed back as input
- **Stop Hook**: Prevents session exit until completion promise or max iterations
- **CWO12 Integration**: Auto-detects CWO12 workflows and integrates with TaskMaster
- **Python-only**: No bash dependencies (Windows compatible)

## Installation

```powershell
# Copy to local plugins (prevents marketplace overwrite)
Copy-Item -Path "P:\projects\ralph-wiggum-python" -Destination "C:\Users\brsth\.claude\plugins\local\ralph-wiggum-python" -Recurse -Force

# Or use the setup script
P:\projects\ralph-wiggum-python\install.ps1
```

## Usage

```bash
# Basic usage
/ralph-loop "your task here" --completion-promise "DONE" --max-iterations 10

# CWO12 integration (auto-detected)
/ralph-loop /cwo12 my-project "Build feature" --tsk-id TSK-123ABC

# Direct script invocation
python P:/projects/ralph-wiggum-python/scripts/setup-ralph-loop.py "task" --tsk-id TSK-123
```

## Options

| Option | Description |
|--------|-------------|
| `PROMPT` | Task description (required) |
| `--max-iterations N` | Stop after N iterations (default: pattern-based) |
| `--completion-promise TEXT` | Exit when you output `<promise>TEXT</promise>` (default: auto-detected) |
| `--test-required` | **v7.1**: Explicitly enable test gate (overrides auto-detection) |
| `--no-tests` | **v7.1**: Disable test gate (overrides auto-detection) |
| `--project-root PATH` | **v7**: Project root for test execution (default: current dir) |
| `--test-timeout SECONDS` | **v7**: Maximum time to wait for test execution (default: 60) |
| `--coverage-threshold PERCENT` | **v7**: Minimum coverage percentage required (default: 80) |
| `--tsk-id TSK_ID` | CWO12 TaskMaster ID (e.g., `TSK-251230-NSE`) |
| `--force` | Skip task-fit assessment |

## Test Verification Gate (v7.1)

**Smart Auto-Detection**: Tests are automatically enabled for code changes:

```bash
# Tests auto-enabled (bug fix pattern)
/ralph-loop "Fix the auth bug"

# Tests auto-enabled (feature pattern)
/ralph-loop "Add user authentication"

# Override auto-detection
/ralph-loop "Quick fix" --no-tests
/ralph-loop "Update docs" --test-required
```

**Manual Test Gate** (v7 style):

```bash
# Explicitly require tests
/ralph-loop "Add feature" --test-required --max-iterations 5

# With coverage threshold
/ralph-loop "Refactor" --test-required --coverage-threshold 90
```

**How it works**:

The v7 update adds a **test gate** that blocks loop exit until tests pass:

```bash
# Require tests before exit
/ralph-loop "Add feature with tests" --test-required --max-iterations 5

# With coverage threshold
/ralph-loop "Refactor with coverage" --test-required --coverage-threshold 90

# What happens on exit attempt:
# 1. Check if test.json exists and is fresh (from current session)
# 2. If fresh → use cached results (fast)
# 3. If stale/missing → run pytest subprocess (fallback)
# 4. Block exit if tests fail or coverage below threshold
# 5. Re-feed prompt to continue iterating
```

**Test Result Sources** (checked in order):
1. **TDD Guard cached** (`test.json`) - Fast, uses pytest plugin
2. **Subprocess pytest** - Fallback if cache unavailable

**Exit Conditions** (with `--test-required`):
- All tests pass AND
- Coverage meets threshold (if specified) AND
- Completion promise detected

## Auto-Detection (v7.1)

Ralph automatically detects task type and sets appropriate defaults:

| Task Type | Keywords | Tests | Iterations | Promise |
|-----------|----------|-------|------------|---------|
| **Bug Fix** | fix, debug, broken, error, crash | ✅ ON | 8 | BUG_FIXED |
| **Feature** | add, create, build, implement, develop | ✅ ON | 12 | FEATURE_COMPLETE |
| **Refactor** | refactor, migrate, cleanup, optimize | ✅ ON | 10 | REFACTORING_COMPLETE |
| **Docs** | doc, readme, document, comment | ❌ OFF | 3 | DOCS_COMPLETE |
| **Explore** | explore, investigate, research | ❌ OFF | 3 | INVESTIGATION_COMPLETE |
| **Analysis** | analyze, review, examine, audit | ❌ OFF | 3 | ANALYSIS_COMPLETE |
| Default | other | ❌ OFF | 5 | TASK_COMPLETE |

**Override examples**:
```bash
/ralph-loop "Quick fix" --no-tests              # Disable auto-detected tests
/ralph-loop "Update docs" --test-required        # Enable tests for docs task
```

## CWO12 Integration

**CWO12 automatically invokes Ralph Loop with TDD** - no manual setup needed.

When you run `/cwo12`, Ralph Loop is automatically activated with:
- TDD enabled by default (tests required to complete)
- 20 iterations maximum
- Completion promise: `CWO12_ALL_16_STEPS_COMPLETED`

```bash
# CWO12 with automatic Ralph Loop + TDD
/cwo12 "Build REST API with authentication"

# What happens automatically:
# 1. Ralph Loop activates (no opt-in needed)
# 2. TDD is enabled (tests required to exit)
# 3. 20 iterations maximum (for complex 16-step workflow)
# 4. Only exits when CWO12_ALL_16_STEPS_COMPLETED detected
```

**Manual invocation** (if needed):
```bash
/ralph-loop /cwo12 my-project "Build feature" --tsk-id TSK-251230-NSE
```

**Completion Criteria** (for CWO12 loops):
- All 16 steps must have artifacts in TSK directory
- Code changes tested and working
- Quality gates passed
- Documentation complete

**Only when all criteria are met**:
```xml
<promise>CWO12_ALL_16_STEPS_COMPLETED</promise>
```

## Files

```
ralph-wiggum-python/
├── commands/
│   └── ralph-loop.md       # Slash command definition
├── hooks/
│   ├── hooks.json          # Hook configuration
│   └── stop-hook.py        # Stop hook (v7: test gate, TDD Guard integration)
├── scripts/
│   └── setup-ralph-loop.py # Setup script (v7: test gate flags)
├── tests/
│   └── test_stop_hook_v7.py # TDD tests for v7 features
├── conftest.py             # Registers TDD Guard pytest plugin
├── tdd_guard_reporter.py   # Pytest plugin (writes test.json)
├── .data/
│   └── ralph-loop.local.md # Active loop state
├── .claude/tdd-guard/data/
│   └── test.json           # Cached test results (generated)
└── .claude-plugin/
    └── plugin.json         # Plugin metadata
```

## Completion Example

```bash
/ralph-loop "Fix the bug" --completion-promise "BUG FIXED"

# ... work on the bug ...

# When truly done, output:
<promise>BUG FIXED</promise>
```

## Monitoring

```bash
# View current loop state
head -10 P:/projects/ralph-wiggum-python/.data/ralph-loop.local.md

# Check iteration count
grep "iteration:" P:/projects/ralph-wiggum-python/.data/ralph-loop.local.md
```

## Emergency Stop

```bash
# Cancel active loop immediately
echo "active: false" > P:/projects/ralph-wiggum-python/.data/ralph-loop.local.md

# Or delete state entirely
rm P:/projects/ralph-wiggum-python/.data/ralph-loop.local.md
```

## Uninstall

```powershell
# Remove local plugin
Remove-Item -Path "C:\Users\brsth\.claude\plugins\local\ralph-wiggum-python" -Recurse -Force

# Or cancel active loop
/cancel-ralph
```
