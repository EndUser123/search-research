# Terminal ID Detection Fix - Implementation Plan

**Date**: 2026-03-09
**Status**: DRAFT
**Priority**: HIGH

## Problem Statement

The handoff system is experiencing degraded quality with `terminal_id="unknown"` appearing in handoffs. Both PreCompact and SessionStart hooks are attempting to retrieve `terminalId` from hook input data, but Claude Code does not provide this field.

**Impact**:
- Handoff quality score drops from 0.95 → 0.55
- All handoffs degraded to `terminal_id="unknown"`
- Cross-terminal fallback triggered unnecessarily
- Loss of terminal-scoped session continuity

**Root Cause**:
- `SessionStart_handoff_restore.py:375` - defaults to "unknown"
- `PreCompact_handoff_capture.py:831` - attempts fallback to task tracker search
- Empirical evidence from debug logs confirms NO `terminalId` field in hook input

## Context Analysis

### Current Architecture

**Handoff Storage**: Terminal-scoped at `.claude/state/handoff/{terminal_id}_handoff.json`

**Hook Input Fields** (empirically verified):
```json
{
  "session_id": "uuid",
  "transcript_path": "path/to/session.jsonl",
  "cwd": "P:\\.claude\\hooks",
  "hook_event_name": "SessionStart|PreCompact",
  "source": "compact",
  "model": "claude-sonnet-4-6"
}
```

**Missing Field**: `terminalId` is NOT provided by Claude Code

### Existing Solution

**Module**: `P:\.claude\hooks\terminal_detection.py`

**Key Function**: `resolve_terminal_key(input_data: dict) -> str`

**Detection Priority**:
1. `input_data["terminal_id"]` (not currently provided)
2. `CLAUDE_TERMINAL_ID` environment variable
3. `detect_terminal_id()` with 4-tier fallback:
   - Environment variables (process-scoped)
   - Project state file with PID/timestamp validation
   - Temp file with age validation
   - Windows ConsoleHost handle
4. Returns "unknown" if all fail

### Known Issues

**Issue 1**: `_read_project_state()` (line 389) relies on `PROJECT_ROOT` environment variable which may not be set in hook execution context.

**Issue 2**: SessionStart and PreCompact hooks already add handoff package to `sys.path` manually, but `terminal_detection.py` runs at module import time before this happens.

## Existing Implementation Discovery

### Files Requiring Changes

1. **`P:\.claude\hooks\terminal_detection.py`**
   - Function: `_read_project_state()` (lines 369-462)
   - Issue: Environment variable dependency
   - Fix: Use hooks-aware directory traversal

2. **`P:\.claude\hooks\SessionStart_handoff_restore.py`**
   - Line 375: `terminal_id = input_data.get("terminalId", "unknown")`
   - Fix: Use `resolve_terminal_key(input_data)`

3. **`P:\.claude\hooks\PreCompact_handoff_capture.py`**
   - Line 831: `terminal_id = input_data.get("terminalId", None)`
   - Lines 834-835: Task tracker fallback (unreliable)
   - Fix: Use `resolve_terminal_key(input_data)`

### Dependencies

**Required Modules**:
- `terminal_detection.py` (same directory - no import issues)
- `handoff.hooks.__lib.handoff_files` (already imported in both hooks)
- `handoff.hooks.__lib.project_root` (already imported in both hooks)

**No New Dependencies Required**

## Test Discovery

### Existing Test Coverage

**Current Tests**:
- `P:\.claude\hooks\tests/test_terminal_detection.py` (if exists)
- Handoff integration tests in `P:\packages\handoff\src\tests/`

### Required Test Scenarios

1. **Terminal ID Detection**
   - Environment variable set → use env var
   - Project state file present with valid PID → use project state
   - Temp file present and fresh → use temp file
   - Windows ConsoleHost available → use console handle
   - All methods fail → return "unknown"

2. **Hooks Integration**
   - SessionStart receives no terminalId → uses detection
   - PreCompact receives no terminalId → uses detection
   - Both hooks use same terminal_id for same terminal
   - Cross-terminal isolation preserved

3. **Regression Prevention**
   - Handoff quality score ≥0.90 after fix
   - No "unknown" terminal_id when detection succeeds
   - Session continuity across compaction

4. **Edge Cases**
   - PROJECT_ROOT env var not set → directory traversal works
   - Stale project state file (>2 hours) → rejected
   - PID mismatch → rejected
   - Parent PID match → accepted (process restart)

## Proposed Solution

### Architecture Decision

**Approach**: Use existing `resolve_terminal_key()` from `terminal_detection.py` with enhanced project root detection.

**Rationale**:
- Reuses proven 180-line detection module
- Clean separation of concerns (hooks vs. OS interface)
- Graceful degradation to "unknown"
- No new dependencies

### Changes Required

#### Change 1: Fix `_read_project_state()` in `terminal_detection.py`

**Location**: Lines 369-462

**Current Code**:
```python
def _read_project_state() -> str | None:
    project_root = os.environ.get("PROJECT_ROOT")
    if not project_root:
        return None
```

**Fixed Code**:
```python
def _read_project_state() -> str | None:
    # Detect project root using hooks-aware directory traversal
    try:
        current_dir = Path.cwd()
        hooks_dir_str = str(current_dir).replace("\\", "/")

        # Check if we're in .claude/hooks/ directory
        if "/.claude/hooks" in hooks_dir_str or "/.claude/hooks/" in hooks_dir_str:
            project_root = current_dir.parent.parent
        elif "/.claude/" in hooks_dir_str or "/.claude" in hooks_dir_str:
            parts = hooks_dir_str.split("/.claude")[0]
            project_root = Path(parts) if parts else current_dir.parent
        else:
            # Standard upward traversal
            project_root = current_dir
            for _ in range(10):
                if (project_root / ".claude").exists():
                    break
                if project_root == project_root.parent:
                    return None
                project_root = project_root.parent
    except Exception:
        return None

    state_file = project_root / ".claude" / "state" / "terminal_id.json"
    # ... rest of validation logic unchanged
```

**Benefits**:
- Removes environment variable dependency
- Works from `.claude/hooks/` execution context
- No external imports (avoids ImportError risk)
- Preserves all PID/timestamp validation

#### Change 2: Update SessionStart Hook

**Location**: `P:\.claude\hooks\SessionStart_handoff_restore.py:375`

**Current Code**:
```python
terminal_id = input_data.get("terminalId", "unknown")
```

**Fixed Code**:
```python
# Import at top of file
from terminal_detection import resolve_terminal_key

# Line 375
terminal_id = resolve_terminal_key(input_data)
```

#### Change 3: Update PreCompact Hook

**Location**: `P:\.claude\hooks\PreCompact_handoff_capture.py:831-835`

**Current Code**:
```python
terminal_id = input_data.get("terminalId", None)

if not terminal_id and session_id:
    terminal_id = find_terminal_id_from_task_tracker(debug_project_root, session_id)
```

**Fixed Code**:
```python
# Import at top of file
from terminal_detection import resolve_terminal_key

# Lines 831-835 replaced with:
terminal_id = resolve_terminal_key(input_data)
```

**Note**: Remove `find_terminal_id_from_task_tracker()` function if no other callers.

## Implementation Plan

### Phase 1: Fix Core Detection (30 min)

**Task T-001**: Update `_read_project_state()` in `terminal_detection.py`
- File: `P:\.claude\hooks\terminal_detection.py`
- Action: Replace lines 369-462 with hooks-aware project root detection
- Acceptance Criteria:
  - Function works when executed from `.claude/hooks/`
  - No dependency on `PROJECT_ROOT` environment variable
  - All existing PID/timestamp validation preserved
  - No external imports added
- Effort: M
- Depends On: None

**Task T-002**: Test `_read_project_state()` fix
- File: `P:\.claude\hooks\tests/test_terminal_detection.py` (create if needed)
- Action: Add tests for hooks directory execution context
- Acceptance Criteria:
  - Test passes when run from `.claude/hooks/`
  - Test covers path traversal logic
  - Test verifies stale state rejection (>2 hours)
  - Test verifies PID validation
  - **[PR-001] Test covers Windows backslash handling** - verify path string replacement works correctly
- Effort: M
- Depends On: T-001

### Phase 2: Update Hooks (15 min)

**Task T-003**: Update SessionStart hook
- File: `P:\.claude\hooks\SessionStart_handoff_restore.py`
- Action:
  1. Add `from terminal_detection import resolve_terminal_key` at top
  2. Replace line 375 with `terminal_id = resolve_terminal_key(input_data)`
- Acceptance Criteria:
  - Import succeeds (terminal_detection.py in same directory)
  - No syntax errors
  - Change is minimal and localized
- Effort: S
- Depends On: T-001

**Task T-004**: Update PreCompact hook
- File: `P:\.claude\hooks\PreCompact_handoff_capture.py`
- Action:
  1. Add `from terminal_detection import resolve_terminal_key` at top
  2. Replace lines 831-835 with `terminal_id = resolve_terminal_key(input_data)`
  3. **[PR-002] Verify no other callers** - grep entire codebase for `find_terminal_id_from_task_tracker` references
  4. Remove `find_terminal_id_from_task_tracker()` if verified unused
- Acceptance Criteria:
  - Import succeeds
  - **[PR-002] Codebase search shows no other callers** - document grep results
  - Task tracker fallback code removed
  - Change is minimal and localized
- Effort: S
- Depends On: T-001

### Phase 3: Integration Testing (30 min)

**Task T-005**: Test hook integration
- Action: Run `/compact` and verify handoff quality
- Acceptance Criteria:
  - Handoff quality score ≥0.90
  - `terminal_id` is not "unknown" (if detection succeeds)
  - No errors in hook execution logs
  - Cross-terminal fallback not triggered unnecessarily
- Effort: M
- Depends On: T-003, T-004

**Task T-006**: Verify session continuity
- Action: Test handoff before/after compaction
- Acceptance Criteria:
  - Same `terminal_id` used before and after compaction
  - Handoff restored successfully
  - No loss of session state
- Effort: M
- Depends On: T-005

### Phase 4: Documentation & Cleanup (15 min)

**Task T-006**: Verify session continuity
- Action: Test handoff before/after compaction
- Acceptance Criteria:
  - Same `terminal_id` used before and after compaction
  - Handoff restored successfully
  - No loss of session state
- Effort: M
- Depends On: T-005

**Task T-007**: **[PR-003] Test cross-terminal isolation**
- File: `P:\.claude\hooks\tests/test_terminal_detection.py`
- Action: Add integration test for cross-terminal isolation (security property)
- Acceptance Criteria:
  - Terminal A and Terminal B get different terminal_ids
  - Handoff from Terminal A not accessible to Terminal B
  - No contamination even with stale temp files or project state
  - PID validation prevents cross-terminal bleeding
- Effort: M
- Depends On: T-005

**Task T-008**: Update debug log analysis
- Action: Document expected terminal_id format in debug logs
- Acceptance Criteria:
  - `sessionstart_input_debug.log` shows resolved terminal_id
  - Format: `{source}_{id}` (e.g., `env_abc123`, `console_1a2b3c`)
- Effort: S
- Depends On: T-007

**Task T-009**: Clean up test artifacts
- Action: Remove temporary debug logs if present
- Acceptance Criteria:
  - No stale test files in `.claude/logs/`
  - Debug logging functionality preserved
- Effort: S
- Depends On: T-008

**Task T-010**: **[BC-001] Fix backward compatibility in next_step_choice_state.py**
- File: `P:\.claude\hooks\__lib\next_step_choice_state.py`
- Action: Update logic to handle actual terminal_ids correctly (not just "unknown")
- Current Breaking Code (line 69):
  ```python
  resolved = resolve_terminal_key(data)
  return "" if resolved == "unknown" else str(resolved)
  ```
- Fix Required: Update to handle actual terminal_ids when detection returns real IDs instead of "unknown"
- Acceptance Criteria:
  - Function works with actual terminal_ids (not just "unknown")
  - Preserves existing behavior for empty/unknown cases
  - No breaking changes to next step choice logic
  - Terminal ID detection improvement doesn't break next step choices
- Effort: S
- Depends On: T-001 (core terminal_id fix needed first)

## Risks, Success Criteria, and Dependencies

### Top Risks

1. **Import Timing Issue** (Severity: MEDIUM)
   - Risk: `terminal_detection.py` may import before hooks add handoff package to `sys.path`
   - Mitigation: No external imports in fixed code (pure Python directory traversal)
   - Fallback: If import fails, hooks will crash with clear ImportError

2. **Path Detection Failure** (Severity: LOW)
   - Risk: Directory traversal may fail in unusual directory structures
   - Mitigation: Multiple fallback strategies (env vars, temp file, ConsoleHost)
   - Fallback: Returns "unknown" (graceful degradation)

3. **Cross-Terminal Bleeding** (Severity: LOW)
   - Risk: Stale temp file or project state could cause cross-terminal contamination
   - Mitigation: Age validation (2-hour timeout) and PID validation already in place
   - Fallback: Falls back to ConsoleHost (true process isolation)

### Success Criteria

1. **Functional**: Handoff quality score returns to ≥0.90
2. **Reliability**: Terminal ID detection succeeds in >95% of cases
3. **Compatibility**: No breaking changes to hook interfaces
4. **Performance**: No measurable latency increase (<50ms per hook execution)
5. **Isolation**: Cross-terminal contamination prevented

### Dependencies

**External Dependencies**: None

**Internal Dependencies**:
- T-001 must complete before T-002, T-003, T-004, T-010 (core fix needed first)
- T-003, T-004 must complete before T-005 (both hooks need update)
- T-005 must complete before T-006, T-007 (integration tests before isolation test)
- T-006, T-007 must complete before T-008 (verification before documentation)
- T-008 must complete before T-009 (documentation before cleanup)
- T-010 can run in parallel with T-002 through T-009 (only depends on T-001)

**No Prohibited Dependencies** (all are solo-dev compatible)

### Rollback Strategy

**If Issues Detected**:
1. Revert changes to `terminal_detection.py` (restore original `_read_project_state()`)
2. Revert changes to `SessionStart_handoff_restore.py` (restore `input_data.get("terminalId", "unknown")`)
3. Revert changes to `PreCompact_handoff_capture.py` (restore task tracker fallback)
4. System returns to current degraded state (quality score 0.55)

**Rollback Trigger**:
- Handoff quality score <0.80 after fix
- Hook execution errors increase
- Cross-terminal contamination detected

## Next Actions

1. Execute T-001: Fix `_read_project_state()` in terminal_detection.py
2. Execute T-002: Test the fix with unit tests
3. Execute T-010: Fix backward compatibility in next_step_choice_state.py
4. Execute T-003: Update SessionStart hook
5. Execute T-004: Update PreCompact hook
6. Execute T-005: Run integration tests with `/compact`
7. Execute T-006: Verify session continuity
8. Execute T-007: Test cross-terminal isolation
9. Execute T-008: Update documentation
10. Execute T-009: Clean up test artifacts
