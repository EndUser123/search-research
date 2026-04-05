# Review Bundle: loop-core

**Generated**: 2026-03-14 22:40
**Scope**: P:/packages/loop-core/
**File Count**: 49 files
**Execution Mode**: 2-agent (10-50 files)

---

## 1. PROJECT CONTEXT

### Domain & Purpose

loop-core is a **Claude Code plugin** that provides terminal-local state management for Ralph-style autonomous AI development loops. It solves the problem of Git race conditions when multiple terminals run parallel autonomous loops by using file-based state persistence with terminal isolation.

**Critical use case**: Enables autonomous AI loops to track completion state across iterations without conflicting with each other or with Git operations.

### Scale Metrics

- **LOC**: 526 lines of Python code (scripts/)
- **Subsystems**: 3 major components (State Management, Plan Parsing, /loop-core Skill)
- **Deployment**: Claude Code plugin (auto-discovered, no pip install)
- **Change Frequency**: Active development (v0.3.0 released 2026-03-14)

### Your Environment

- **OS**: Windows 11 Pro (10.0.26200)
- **Shell**: bash (Unix shell syntax)
- **Languages**: Python 3.14+
- **Frameworks**: pytest, pytest-cov
- **External Services**: None (file-based only)

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────────┐
│                    loop-core Plugin                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │     User    │───→│ /loop-core   │───→│   /code      │  │
│  │  (plan.md)  │    │    Skill     │    │  workflow    │  │
│  └─────────────┘    └──────────────┘    └──────────────┘  │
│         │                                      │           │
│         │         ┌──────────────┐             │           │
│         └────────→│Plan Parser   │←────────────┘           │
│                   │(parse_plan)  │                         │
│                   └──────────────┘                         │
│                          │                                 │
│                   ┌──────────────┐                         │
│                   │State Manager │                         │
│                   │(TerminalState)│                        │
│                   └──────────────┘                         │
│                          │                                 │
│                   ┌──────────────┐                         │
│                   │Terminal      │                         │
│                   │Detection     │                         │
│                   └──────────────┘                         │
└─────────────────────────────────────────────────────────────┘
```

### Major Subsystems

#### 1. State Management (`scripts/state_manager.py`)
- **Purpose**: File-based state persistence with atomic writes
- **Files**: `scripts/state_manager.py`, `scripts/state_paths.py`
- **Entry Point**: `TerminalStateManager` class
- **Dependencies**: None (stdlib only)
- **Critical Invariants**:
  - State directory structure: `.claude/state/terminals/{terminal_id}/`
  - Atomic writes (temp file + rename)
  - PID-based lock ownership with stale cleanup

#### 2. Plan Parsing (`scripts/plan_parser.py`)
- **Purpose**: Extract tasks from markdown plan files
- **Files**: `scripts/plan_parser.py`, `scripts/patterns/task_patterns.py`
- **Entry Point**: `parse_plan_tasks()` function
- **Dependencies**: `scripts.patterns.task_patterns`
- **Critical Invariants**:
  - Task format: `- [ ] TASK-ID text [tag:name] after:TASK-ID`
  - Returns: list[dict] with id, text, complete, tags, dependencies
  - Raises: `PlanParseError` if file not found

#### 3. /loop-core Skill (`skills/loop-core/SKILL.md`)
- **Purpose**: Ralph-style autonomous loop orchestration
- **Files**: `skills/loop-core/SKILL.md`
- **Entry Point**: `/loop-core path/to/plan.md`
- **Dependencies**: State Manager, Plan Parser, /code workflow
- **Critical Invariants**:
  - Dual-condition exit gate (completion_indicators >= 2 AND EXIT_SIGNAL: true)
  - State persistence across iterations
  - Multi-terminal safe isolation

---

## 3. EXECUTION AND DATA FLOW

### Execution Sequences

**Skill Invocation**:
```
User: /loop-core plan.md
  ↓
Skill reads plan.md
  ↓
Parse plan → extract tasks
  ↓
Loop: For each incomplete task
  ↓
  Execute /code workflow
  ↓
  Update state (current_task_id, completion_indicators)
  ↓
  Check exit conditions
  ↓
  If BOTH conditions met → EXIT
  If EITHER condition false → CONTINUE
```

### State Management

**State Stores**:
- Terminal-local directories: `.claude/state/terminals/{terminal_id}/`
- State files: `loop_state.json`, `completed_tasks.log`, `loop_metrics.json`

**Consistency Model**:
- **Isolation**: Each terminal gets isolated state directory
- **Atomicity**: Temp file + rename pattern (no partial writes)
- **Locking**: PID-based locks with automatic stale cleanup
- **Durability**: File-based (survives crashes and reboots)

### Error Handling

**Fail-Open Policy**:
- Plan file not found → Raise `PlanParseError`
- State file corrupted → Raise `LoopStateError`
- Lock acquisition fails → Return False (non-blocking)
- Stale lock detected → Auto-cleanup and retry

**No Retries**:
- Write operations fail immediately (raise exception)
- No built-in retry logic for I/O errors
- No timeout for lock acquisition (default 30s)

---

## 4. COMPONENT INVENTORY

### Core Logic

**`scripts/state_manager.py`** (186 LOC)
- `TerminalStateManager.read_state(key)` → dict | None
- `TerminalStateManager.write_state(key, value)` → None
- `TerminalStateManager.acquire_lock(lock_name, timeout_sec)` → bool
- `TerminalStateManager.release_lock(lock_name)` → None
- `TerminalStateManager._is_pid_running(pid)` → bool
- **Limitation**: No built-in retry on write failures

**`scripts/plan_parser.py`** (127 LOC)
- `parse_plan_tasks(plan_path)` → list[dict]
- `extract_task_metadata(task_text)` → dict
- `detect_incomplete_tasks(tasks)` → list[dict]
- **Limitation**: Only parses markdown checkbox format

**`scripts/terminal_detection.py`** (104 LOC)
- `get_terminal_id(data)` → str
- `_detect_console_terminal()` → str
- **Limitation**: Console detection Windows-only

### Utilities/Helpers

**`scripts/state_paths.py`** (54 LOC)
- `get_terminal_state_dir(terminal_id)` → Path
- `get_terminal_state_path(terminal_id, filename)` → Path

**`scripts/patterns/task_patterns.py`**
- `TASK_PATTERN`: Regex for markdown checkboxes
- `TAG_PATTERN`: Regex for `[tag:name]` syntax
- `DEPENDENCY_PATTERN`: Regex for `after:TASK-ID` syntax

### Configuration

**`.claude-plugin/plugin.json`**
```json
{
  "name": "loop-core",
  "description": "Terminal-local state management for Ralph-style autonomous loops",
  "author": {"name": "loop-core contributors"}
}
```

**`.github/workflows/test.yml`**
- Python 3.14
- pytest with pytest-cov
- Coverage threshold: 70%

### Infrastructure

**`tests/test_*.py`** (3 test files, 45 tests)
- `test_state_manager.py`: Unit tests for TerminalStateManager
- `test_plan_parser.py`: Unit tests for plan parsing
- `test_integration.py`: Integration tests for loop lifecycle
- **Coverage**: 79%

---

## 5. DESIGN INTENT AND NON-NEGOTIABLES

### Architectural Pillars

1. **Terminal-Local State**: Each terminal gets isolated state directory (NO shared state)
2. **Atomic Writes**: Temp file + rename pattern (NO partial writes)
3. **No TTL**: State persists until explicitly deleted (NO expiration)
4. **PID-Based Locks**: Automatic stale cleanup (NO manual lock expiration)
5. **Plugin Structure**: Auto-discovered by Claude Code (NO pip install)

### Technology Constraints

- **Python 3.14+**: Modern type hints required
- **File-Based Only**: No database dependencies
- **No Git for Runtime State**: Avoid Git race conditions
- **Stdlib Only**: No external dependencies for core logic
- **Claude Code Plugin**: Uses `.claude-plugin/` and `scripts/` structure

### Performance SLAs

- **Write Operations**: <10ms for typical state (atomic file rename)
- **Read Operations**: <5ms for typical state (file read + JSON parse)
- **Lock Acquisition**: <1ms for uncontended lock
- **Test Coverage**: 70% minimum threshold

### Things That Must NOT Change

1. **State Directory Structure**: `.claude/state/terminals/{terminal_id}/`
2. **Atomic Write Pattern**: Temp file + rename (NOT write-in-place)
3. **PID-Based Locking**: Check `os.kill(pid, 0)` for stale locks
4. **Terminal ID Format**: `{source}_{id}` (e.g., `pid_12345_1234567890`)
5. **Import Path**: `from scripts import TerminalStateManager` (NOT `from loop_core`)

---

## 6. KNOWN ISSUES

### Issue 1: CI Config Coverage Module Mismatch
**Scenario**: GitHub Actions workflow runs `--cov=loop_core` but module is now `scripts`
**Expected**: Coverage report for `scripts/` module
**Actual**: Coverage report fails (module `loop_core` doesn't exist)
**Impact**: CI/CD pipeline broken
**Workaround**: Update `.github/workflows/test.yml` line 29: `--cov=scripts`
**Fix Required**: Yes (CI broken until fixed)

### Issue 2: Console Detection Windows-Only
**Scenario**: `_detect_console_terminal()` only works on Windows
**Expected**: Cross-platform console detection
**Actual**: macOS/Linux terminals fall back to PID-based detection
**Impact**: Terminal IDs less stable on Unix systems
**Workaround**: Set `CLAUDE_TERMINAL_ID` environment variable
**Fix Required**: Optional (low priority, fallback works)

### Issue 3: No Retry on Write Failures
**Scenario**: `write_state()` fails immediately on I/O error
**Expected**: Retry with exponential backoff
**Actual**: Raises `LoopStateError` immediately
**Impact**: Transient failures cause loop crash
**Workaround**: None (caller must handle retry)
**Fix Required**: Optional (consider if reliability issues arise)

---

## 7. INTEGRATION POINTS

### Where New Solutions Can Plug In

**1. Custom State Backends**
- **Interface**: Extend `TerminalStateManager` class
- **Current**: File-based (JSON files)
- **Alternative**: SQLite, Redis, etcd
- **Constraint**: Must maintain atomic write guarantees

**2. Custom Plan Parsers**
- **Interface**: Replace `parse_plan_tasks()` function
- **Current**: Markdown checkbox format
- **Alternative**: JSON plans, YAML plans, API-based
- **Constraint**: Must return compatible task dict schema

**3. Custom Exit Detection**
- **Interface**: Modify dual-condition gate in `/loop-core` skill
- **Current**: completion_indicators >= 2 AND EXIT_SIGNAL: true
- **Alternative**: Custom heuristics, LLM judgment only
- **Constraint**: Must prevent premature exit

**4. Custom Lock Implementations**
- **Interface**: Replace `acquire_lock()` / `release_lock()` methods
- **Current**: PID-based file locks
- **Alternative**: flock, mutex, distributed locks
- **Constraint**: Must maintain multi-terminal safety

### Data Exchange Contracts

**State File Schema** (`loop_state.json`):
```json
{
  "current_task_id": "TASK-003",
  "completed_tasks": ["TASK-001", "TASK-002"],
  "failed_tasks": [],
  "completion_indicators": 2,
  "loop_metadata": {
    "plan_path": "/path/to/plan.md",
    "started_at": "2026-03-14T10:00:00",
    "last_update": "2026-03-14T10:15:00",
    "iterations": 3
  }
}
```

**Task Schema** (from `parse_plan_tasks()`):
```json
{
  "id": "TASK-001",
  "text": "Task description",
  "complete": false,
  "tags": ["important"],
  "dependencies": ["TASK-000"],
  "raw_line": "- [ ] TASK-001 Task description"
}
```

### Exit Codes and Expectations

**Skill Exit Conditions**:
- **Success**: Both exit conditions met → Exit code 0
- **Failure**: Plan file not found → Exit code 1
- **Failure**: Invalid plan format → Exit code 1
- **Loop Interrupt**: User cancels → Exit code 130

**No daemon mode** → Skill runs once per invocation

---

## 8. APPENDIX: SAMPLE RUNS

### Test Run (Integration Test)

```python
# From tests/test_integration.py
def test_full_lifecycle_parse_and_persist(self, sample_plan, state_manager):
    # Parse plan
    tasks = parse_plan_tasks(sample_plan)
    assert len(tasks) == 4

    # Get incomplete tasks
    incomplete = detect_incomplete_tasks(tasks)
    assert len(incomplete) == 3

    # Persist current task to state
    state_manager.write_state("loop_state", {
        "current_task_id": incomplete[0]["id"],
        "completed_tasks": ["TASK-004"],
        "failed_tasks": [],
    })

    # Verify state persistence
    loaded_state = state_manager.read_state("loop_state")
    assert loaded_state["current_task_id"] == "TASK-001"
    assert loaded_state["completed_tasks"] == ["TASK-004"]
```

**Result**: ✅ PASS (all 45 tests passing, 79% coverage)

### Typical Loop Execution

```bash
$ /loop-core path/to/plan.md

→ Parsing plan: found 5 tasks (3 incomplete)
→ Iteration 1: TASK-001 Initialize state
→ Executing /code TASK-001 Initialize state
→ State updated: current_task_id=TASK-001, completion_indicators=1
→ Iteration 2: TASK-002 Process data
→ Executing /code TASK-002 Process data
→ State updated: current_task_id=TASK-002, completion_indicators=2
→ Checking exit conditions...
→ completion_indicators (2) >= 2 ✓
→ EXIT_SIGNAL (false) not set ✗
→ Continuing to next task...
→ Iteration 3: TASK-003 Save results
→ Executing /code TASK-003 Save results
→ State updated: current_task_id=TASK-003, completion_indicators=3
→ Checking exit conditions...
→ completion_indicators (3) >= 2 ✓
→ EXIT_SIGNAL (true) set ✓
→ Both conditions met → EXIT
→ Loop complete: 3 iterations, 3 tasks completed
```

---

## END OF BUNDLE

**Next Steps**:
1. Fix CI coverage module mismatch (`--cov=scripts`)
2. Consider retry logic for write failures
3. Evaluate cross-platform console detection
4. Monitor lock contention in production

**Contact**: loop-core contributors via GitHub issues
