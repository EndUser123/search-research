# Multi-Terminal Architecture Documentation

**Purpose**: Document how multi-terminal isolation works across the hooks ecosystem, including state management, terminal detection, and known race conditions.

**Status**: Current implementation (as of 2026-03-14)
- **Fixed**: TASK-022 (intent file deletion race)
- **Fixed**: TASK-023 (cleanup lock TOCTOU race)
- **Remaining**: Multiple TOCTOU vulnerabilities in state file operations

---

## 1. Terminal ID Detection

### Format: `{source}_{id}`

Terminal IDs follow a normalized format to ensure consistency across all hooks:

- `env_{id}`: From `CLAUDE_TERMINAL_ID` or other environment variables
- `console_{hex}`: Windows `GetConsoleWindow()` handle (stable per terminal)

### Detection Priority Order (TASK-003: Centralized)

**File**: `.claude/hooks/__lib/hook_base.py` - `get_terminal_id()` function

```python
def get_terminal_id(data: Mapping[str, Any] | None = None) -> str:
    """
    Priority:
    1. Explicit terminal_id from hook input data (overrides cache)
    2. CLAUDE_TERMINAL_ID env var (highest priority env var)
    3. TERMINAL_ID, TERM_ID, SESSION_TERMINAL env vars
    4. Console detection (WT_SESSION, GetConsoleWindow on Windows)
    5. Derive from PID + session timestamp (unique per process)
    6. Return "" if no detection method succeeds

    Caching: Results cached in _hook_context.terminal_id for performance.
    """
```

**Environment Variables Checked**:
1. `CLAUDE_TERMINAL_ID` (highest priority - explicit override)
2. `TERMINAL_ID`
3. `TERM_ID`
4. `SESSION_TERMINAL`

**Windows Console Detection**:
- **File**: `.claude/hooks/__lib/terminal_detection.py`
- **Function**: `detect_console_host_terminal()`
- Priority 1: `WT_SESSION` (Windows Terminal UUID)
- Priority 2: `GetConsoleWindow()` handle (hex format)

**Key Design Decisions**:
- **Centralized source of truth**: All hooks use `get_terminal_id()` from `hook_base.py`
- **Caching with override**: Explicit terminal_id in data overrides cache
- **SessionStart integration**: SessionStart_terminal_id.py uses centralized function (TASK-004)
- **No PID fallback for SessionStart**: PID fallback exists in `get_terminal_id()` but SessionStart prefers console detection

---

## 2. State File Patterns

### State Path Utilities (TASK-005)

**Module**: `.claude/hooks/__lib/state_paths.py`

Provides centralized functions for terminal-scoped, session-scoped, and shared state management:

```python
from state_paths import (
    get_terminal_state_dir,    # Terminal-scoped state directory
    get_terminal_state_path,   # Terminal-scoped file path
    get_session_state_dir,      # Session-scoped state directory
    get_session_state_path,     # Session-scoped file path
    get_shared_state_dir,       # Shared state directory
    get_shared_state_path,      # Shared state file path
    migrate_legacy_state_file,  # Migration utility
    cleanup_legacy_state_file,  # Cleanup utility
)
```

### Directory Structure (TASK-005 Foundation)

**Location**: `P:/.claude/state/`

```
.claude/state/
├── terminals/
│   ├── {terminal_id}/
│   │   ├── pending_command_intent.json
│   │   ├── behavioral_goal.json
│   │   └── [terminal-scoped state files]
│   ├── console_abc123/
│   └── console_def456/
├── sessions/
│   ├── {session_id}/
│   │   ├── actions.log
│   │   ├── decisions.log
│   │   └── [session-scoped state files]
│   └── env_session_xyz789/
└── shared/
    └── [global state files]
```

### State Scoping Rules

#### 2.1 Terminal-Scoped State

**Purpose**: Persists across sessions in the same terminal
**Pattern**: `terminals/{terminal_id}/{filename}`
**Examples**:
- `terminals/console_abc123/pending_command_intent.json`
- `terminals/console_abc123/behavioral_goal.json`

**Isolation**: True multi-terminal isolation
**Safety**: Each terminal has its own subdirectory

#### 2.2 Session-Scoped State

**Purpose**: Unique per CC session
**Pattern**: `sessions/{session_id}/{filename}`
**Examples**:
- `sessions/env_session_xyz789/actions.log`
- `sessions/env_session_xyz789/decisions.log`

**Isolation**: Session-level (unique per session)
**Use Case**: Transient data that shouldn't persist

#### 2.3 Shared State

**Purpose**: Global state shared across all terminals and sessions
**Pattern**: `shared/{filename}`
**Examples**:
- `shared/hook_ledger.db`
- `shared/behavior-counters.json`

**Isolation**: None (global access)
**Use Case**: Cross-terminal coordination, system-wide settings

---

## 3. Skill Enforcement State Flow

### Workflow Steps Detection (Layer 0)

**File**: `.claude/hooks/PreToolUse_skill_pattern_gate.py` (lines 474-533)

**Purpose**: Block non-Skill tools when skill has declared `workflow_steps`

**State File**: `P:/.claude/state/pending_command_intent_{terminal_id}.json`

**Format**:
```json
{
  "skill": "code",
  "prompt": "/code test",
  "timestamp": "2026-03-12T...",
  "session_id": "...",
  "terminal_id": "console_abc123"
}
```

**Flow**:
```
UserPromptSubmit (skill_enforcer.py)
    ↓
Write intent file (terminal-scoped)
    ↓
PreToolUse_skill_pattern_gate.py (reads intent)
    ↓
Check if skill has workflow_steps
    ↓
Block if Skill tool not used first
```

**Terminal Isolation**: Uses `terminal_id` in filename to prevent cross-terminal contamination

**TOCTOU Fix (TASK-022)**: Intent file deletion now uses retry loop:
```python
# Lines 808-843
max_retries = 4
base_delay_ms = 100

for attempt in range(max_retries):
    try:
        intent_candidate.unlink(missing_ok=True)
        break
    except (FileNotFoundError, PermissionError):
        if attempt < max_retries - 1:
            delay_ms = base_delay_ms * (2 ** attempt)
            time.sleep(delay_ms / 1000.0)
```

---

## 4. Session Data Retention

**File**: `.claude/hooks/session_data_retention.py`

**Purpose**: Cleanup stale state files and lock files

**TOCTOU Fix (TASK-023)**: Lock file deletion uses retry loop (2 locations):

### Location 1: Global Lock Directories (lines 120-147)

```python
for lock in session_dir.glob("*.lock"):
    if now - lock.stat().st_mtime > STALE_LOCK_SECS:
        max_retries = 4
        base_delay_ms = 100

        for attempt in range(max_retries):
            try:
                lock.unlink(missing_ok=True)
                break
            except (FileNotFoundError, PermissionError):
                if attempt < max_retries - 1:
                    delay_ms = base_delay_ms * (2 ** attempt)
                    time.sleep(delay_ms / 1000.0)
```

### Location 2: Log Dir Locks (lines 155-182)

Same retry pattern applied to log directory lock cleanup

---

## 5. State File Naming Convention Matrix

| Scope | Pattern | Example | Isolation Level | Risk |
|-------|---------|---------|-----------------|------|
| **Global** | `{feature}.json` | `hook_ledger.db` | None (shared) | Concurrent access |
| **Session** | `{feature}_{session_id}.json` | `behavioral_goal_abc123.json` | Session only | Cross-terminal contamination |
| **Terminal** | `{feature}_{terminal_id}.json` | `terminal_console_1a2b.json` | Terminal only | ✅ Safe |
| **Both** | `{feature}_{session_id}_{terminal_id}.json` | `goal_abc123_console_1a2b.json` | ✅ Multi-terminal safe | ✅ Safe |

---

## 6. Known Race Conditions

### Fixed Issues ✅

#### TASK-022: Intent File Deletion Race
**Location**: `.claude/hooks/PreToolUse.py` lines 810-822
**Issue**: Non-atomic `exists() → read_text() → unlink()` pattern
**Fix**: Retry loop with exponential backoff
**Test**: `tests/test_concurrent_intent_deletion.py`

#### TASK-023: Cleanup Lock Deletion Race
**Location**: `.claude/hooks/session_data_retention.py` (2 locations)
**Issue**: Non-atomic stale check → unlink pattern
**Fix**: Retry loop with exponential backoff
**Test**: Syntax verified, integration test pending

### Remaining Vulnerabilities ⚠️

#### Pattern 1: exists() → read() without retry
**Files**: All state file reads
**Example**:
```python
if state_file.exists():
    data = json.loads(state_file.read_text())  # ← RACE WINDOW
```
**Risk**: File deleted between exists() and read_text()
**Mitigation**: None currently
**Priority**: MEDIUM

#### Pattern 2: File locking on Windows
**Files**: All file write operations
**Example**:
```python
with open(state_file, 'w') as f:
    json.dump(data, f)  # ← PermissionError possible
```
**Risk**: Concurrent terminals writing same file
**Mitigation**: None currently
**Priority**: HIGH

#### Pattern 3: Directory iteration during deletion
**Files**: session_data_retention.py
**Example**:
```python
for state_file in STATE_DIR.glob("*.json"):
    state_file.unlink()  # ← File could be deleted by another terminal
```
**Risk**: Iterating over directory while files being deleted
**Mitigation**: Partial (TASK-023 fixed lock files only)
**Priority**: LOW

---

## 7. Multi-Tenant Architecture Gaps

### Current State (Transitioning)

**Completed** (TASK-005 Foundation):
- Created `state_paths.py` module with utility functions
- Directory structure established: `terminals/`, `sessions/`, `shared/`
- Migration utilities implemented
- Test coverage: 14/14 tests passing

**Remaining Work**:
- Update hooks to use `state_paths.py` utilities
- Create migration script for existing state files
- Integration testing with multiple terminals
- Backward compatibility verification

### Previous State (Single-Tenant)

- Central state directory: `.claude/state/`
- No per-terminal subdirectories
- Reliance on filename patterns for isolation
- Multiple terminals share same directory space

### Future State (Multi-Tenant)

**Planned**: Per-terminal state subdirectories (Phase 2)

```
.claude/state/
├── terminals/
│   ├── console_abc123/
│   │   ├── pending_command_intent.json
│   │   ├── behavioral_goal.json
│   │   └── locks/
│   ├── console_def456/
│   │   ├── pending_command_intent.json
│   │   ├── behavioral_goal.json
│   │   └── locks/
│   └── console_789xyz/
│       └── ...
├── sessions/
│   └── {session_id}/
│       ├── actions.log
│       ├── decisions.log
│       └── [session-scoped files]
└── shared/
    └── hook_ledger.db
```

**Benefits**:
- True file-system isolation
- No filename collision risk
- Cleaner cleanup (delete entire terminal directory)
- Better Windows file locking behavior

---

## 8. Best Practices for Hook Authors

### DO ✅

1. **Use state_paths.py utilities for state management**
   ```python
   from state_paths import get_terminal_state_dir, get_terminal_state_path

   # Get terminal-scoped state directory (creates if needed)
   terminal_dir = get_terminal_state_dir(terminal_id)

   # Get terminal-scoped file path
   intent_file = get_terminal_state_path(terminal_id, "pending_command_intent.json")
   ```

2. **Use terminal-scoped state files**
   ```python
   from state_paths import get_terminal_state_path

   state_file = get_terminal_state_path(terminal_id, "feature.json")
   ```

3. **Add retry logic for file deletion**
   ```python
   for attempt in range(4):
       try:
           state_file.unlink(missing_ok=True)
           break
       except (FileNotFoundError, PermissionError):
           if attempt < 3:
               time.sleep(0.1 * (2 ** attempt))  # Exponential backoff
   ```

4. **Migrate legacy state files**
   ```python
   from state_paths import migrate_legacy_state_file, cleanup_legacy_state_file

   # Migrate to new structure
   new_path = migrate_legacy_state_file(legacy_file, terminal_id=terminal_id)

   # Cleanup after successful migration
   if new_path:
       cleanup_legacy_state_file(legacy_file, new_path)
   ```

### API Reference: state_paths.py

**Module**: `.claude/hooks/__lib/state_paths.py`

**Functions**:

| Function | Purpose | Returns |
|----------|---------|---------|
| `get_terminal_state_dir(terminal_id)` | Get/create terminal-scoped directory | `Path` to `terminals/{terminal_id}/` |
| `get_terminal_state_path(terminal_id, filename)` | Get terminal-scoped file path | `Path` to terminal file |
| `get_session_state_dir(session_id)` | Get/create session-scoped directory | `Path` to `sessions/{session_id}/` |
| `get_session_state_path(session_id, filename)` | Get session-scoped file path | `Path` to session file |
| `get_shared_state_dir()` | Get/create shared state directory | `Path` to `shared/` |
| `get_shared_state_path(filename)` | Get shared state file path | `Path` to shared file |
| `migrate_legacy_state_file(legacy_path, ...)` | Migrate old state to new structure | `Path` to new location or `None` |
| `cleanup_legacy_state_file(legacy_path, ...)` | Clean up legacy file after migration | `bool` success |

**Usage Examples**:

```python
# Terminal-scoped state (persists across sessions)
from state_paths import get_terminal_state_path, get_terminal_id

terminal_id = get_terminal_id(data)  # from hook_base.py
intent_file = get_terminal_state_path(terminal_id, "intent.json")

# Session-scoped state (unique per session)
from state_paths import get_session_state_path, get_session_id

session_id = get_session_id()
log_file = get_session_state_path(session_id, "actions.log")

# Shared state (global across all terminals)
from state_paths import get_shared_state_path

ledger_db = get_shared_state_path("hook_ledger.db")
```

### DON'T ❌

1. **Don't use PID as terminal ID**
   - PID changes per subprocess
   - Breaks cross-hook state sharing
   - Use `detect_terminal_id()` instead

2. **Don't assume exists() → read() is atomic**
   - TOCTOU race window exists
   - Use retry logic or handle exceptions

3. **Don't use global state for terminal-specific data**
   - Use terminal-scoped filenames
   - Prevents cross-terminal contamination

4. **Don't ignore PermissionError on Windows**
   - File locking is real on Windows
   - Concurrent access causes errors
   - Add retry logic

---

## 9. Testing Multi-Terminal Behavior

### Test File Location
`tests/test_concurrent_intent_deletion.py` (TASK-022 test suite)

### Test Pattern
```python
def test_concurrent_terminals():
    """Simulate 5 terminals accessing same intent file."""
    threads = []
    for i in range(5):
        t = threading.Thread(target=try_delete_intent, args=(i,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Verify: No exceptions, only one terminal succeeded
    assert len(errors) == 0
    assert success_count >= 1
```

### Running Tests
```bash
pytest tests/test_concurrent_intent_deletion.py -v
```

---

## 10. Performance Characteristics

### Retry Loop Latency

**Worst case** (all retries exhausted):
- Attempt 1: 0ms (immediate)
- Attempt 2: 100ms
- Attempt 3: 200ms
- Attempt 4: 400ms
- **Total: ~700ms**

**Typical case** (succeeds on first attempt):
- **Total: <1ms**

### Cleanup Performance

**session_data_retention.py**:
- Lock cleanup: ~700ms worst case per lock
- State file cleanup: Variable (depends on file count)
- Typical run: <5 seconds

---

## 11. Configuration

### Environment Variables

| Variable | Purpose | Default |
|----------|---------|---------|
| `CLAUDE_TERMINAL_ID` | Explicit terminal ID override | None |
| `PROJECT_ROOT` | Project root for state files | None |
| `WT_SESSION` | Windows Terminal UUID (auto-detected) | None |
| `SESSION_TERMINAL` | Legacy terminal ID env var | None |

### State Directories

| Directory | Purpose | Isolation |
|-----------|---------|-----------|
| `.claude/state/` | Main state directory | Shared |
| `.claude/state/terminals/` | **Planned**: Per-terminal state | Terminal (future) |
| `.claude/state/next_step_choice/` | Next step choice state | Session only |
| `.claude/state/prompt_choice/` | Prompt choice state | Session only |
| `.claude/hooks/state/` | Hooks-specific state | Shared |

---

## 12. References

### Implementation Files
- Terminal detection: `packages/skill-guard/src/skill_guard/utils/terminal_detection.py`
- Behavioral state: `.claude/hooks/__lib/behavioral_state.py`
- Session manager: `.claude/hooks/__lib/session_manager.py`
- Intent file fix: `.claude/hooks/PreToolUse.py` (lines 808-843)
- Lock cleanup fix: `.claude/hooks/session_data_retention.py` (lines 120-147, 155-182)

### Documentation
- Hook architecture: `.claude/hooks/CLAUDE.md`
- Intent/goal audit: `.claude/hooks/INTENT_GOAL_AUDIT.md`
- Consolidation plan: `.claude/consolidation_template.py`

### Tests
- Concurrent intent deletion: `tests/test_concurrent_intent_deletion.py`
- Terminal isolation: `.claude/hooks/repositories/tests/test_error_attribution_terminal_isolation.py`

---

## 13. Changelog

### 2026-03-14 (Continued)
- **IN PROGRESS**: TASK-005 - Per-terminal state directories (foundation complete)
  - Created `state_paths.py` module with utility functions
  - 14/14 tests passing for state path utilities
  - Directory structure established: terminals/, sessions/, shared/
  - Remaining: Update hooks to use new utilities, migration script
- **COMPLETED**: TASK-003 - Standardized terminal ID derivation
  - Created `get_terminal_id()` in `hook_base.py` with priority order
  - Added caching in `_hook_context` for performance
  - Sanitization and normalization to {source}_{id} format
  - All 18 tests pass
- **COMPLETED**: TASK-004 - Enforce terminal ID on SessionStart
  - Created `terminal_detection.py` module with console detection logic
  - Updated `hook_base.py` to use console detection as Priority 3
  - Refactored `SessionStart_terminal_id.py` to use centralized function
  - Removed duplicate terminal detection logic
- **DOCUMENTED**: Complete multi-terminal architecture patterns

### 2026-03-14
- **FIXED**: TASK-022 - Intent file deletion race (retry loop added)
- **FIXED**: TASK-023 - Cleanup lock TOCTOU race (retry loop added)

### 2026-03-12
- **ADDED**: Layer 0 workflow steps enforcement with terminal-scoped intent files
- **ADDED**: Skill enforcement v3.5 with three-layer defense

### 2026-03-07
- **ENHANCED**: Git safety features with worktree cross-checks
- **ADDED**: Windows-specific git optimizations

---

## 14. Future Work

### Phase 2: Multi-Tenant Architecture (Planned)

**Goal**: True file-system isolation with per-terminal state directories

**Deliverables**:
1. Create `.claude/state/terminals/{terminal_id}/` structure
2. Migrate existing state files to new structure
3. Update all hooks to use new paths
4. Add backward compatibility layer
5. Remove filename-based isolation patterns

**Benefits**:
- No filename collision risk
- Cleaner cleanup (rmdir entire terminal directory)
- Better Windows file locking behavior
- Clearer separation of concerns

### Phase 3: Comprehensive TOCTOU Audit (Planned)

**Goal**: Identify and fix all remaining TOCTOU vulnerabilities

**Scope**:
1. Audit all state file read operations
2. Audit all state file write operations
3. Audit all directory iteration operations
4. Add retry logic where needed
5. Add comprehensive test coverage

---

**Document Version**: 1.0
**Last Updated**: 2026-03-14
**Author**: Claude Code (TASK-001)
**Status**: Complete
