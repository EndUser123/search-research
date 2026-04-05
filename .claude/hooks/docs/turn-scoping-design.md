# Turn Scoping Design Document
**Task**: TASK-013 - Turn Scoping Implementation
**Date**: 2026-03-15
**Status**: COMPLETE
**Implementation Date**: 2026-03-18

---

## Root Cause Summary

**Problem**: All turn marker files in `state/turn_markers/` show `turn_start_event_id: 0`, indicating turn scoping is not functioning correctly.

**Investigation Findings**:

1. **Test Fixtures Create Stale Markers**:
   - Test files create turn marker JSON files with `turn_start_event_id: 0`
   - These are test artifacts, not production state
   - Location: `tests/test_*.py` files that reference turn markers

2. **Production Code Gap**:
   - File: `P:\.claude\hooks\__lib\hook_ledger.py`
   - Function: `start_turn()` at line 374
   - **Finding**: `start_turn()` writes to SQLite ledger but does NOT create JSON turn marker files
   - Turn marker files are expected by `load_tool_events_for_context()` but never created in production

3. **State File Mismatch**:
   - **Expected**: `state/turn_markers/turn_start_{session_id}__{terminal_id}.json` with current event_id
   - **Actual**: Either file doesn't exist, or exists with `turn_start_event_id: 0` (from tests)

**Root Cause**: `start_turn()` in `hook_ledger.py` creates SQLite ledger entries but doesn't write the JSON turn marker file that `load_tool_events_for_context()` reads for turn-scoped filtering.

---

## Fix Approach

### Option A: Add Turn Marker Writer to `start_turn()` (RECOMMENDED)

**Implementation**:
1. Extend `start_turn()` in `hook_ledger.py` to write JSON turn marker file
2. Extract current event_id from SQLite after inserting turn start event
3. Write to `state/turn_markers/turn_start_{session_id}__{terminal_id}.json`
4. Format: `{"turn_start_event_id": <actual_event_id>}`

**Pros**:
- Single source of truth (SQLite + JSON file created together)
- Consistent with existing `start_turn()` responsibility
- Feature flag can disable file write if needed

**Cons**:
- Adds I/O to `start_turn()` (minimal impact)

**Complexity**: Low (2-3 lines of code)

### Option B: Read Turn Start from SQLite Directly

**Implementation**:
1. Modify `load_tool_events_for_context()` to query SQLite for turn start
2. Remove dependency on JSON turn marker files
3. Query: `SELECT MAX(id) FROM tool_events WHERE session_id=? AND terminal_id=? AND event_type='turn_start'`

**Pros**:
- Eliminates JSON file dependency
- Single source of truth (SQLite only)

**Cons**:
- Changes `load_tool_events_for_context()` signature/behavior
- Requires SQL query on every load (performance concern)
- Breaking change to TASK-001 implementation

**Complexity**: Medium (SQL query + index)

### Option C: SessionStart Creates Turn Marker

**Implementation**:
1. SessionStart hook creates initial turn marker file with `event_id: 0`
2. PostToolUse updates marker after each tool event
3. `load_tool_events_for_context()` reads marker as currently designed

**Pros**:
- Minimal changes to existing code
- Maintains TASK-001 implementation

**Cons**:
- Turn marker lifecycle spread across multiple hooks
- Coordination complexity (SessionStart + PostToolUse)

**Complexity**: Medium (multi-hook coordination)

---

## Chosen Approach: Option A

**Rationale**:
- **Least invasive**: Extends existing `start_turn()`, doesn't change TASK-001
- **Single responsibility**: Turn start creates both SQLite and JSON state
- **Feature flag compatible**: Can be toggled via `VERIFICATION_USE_TURN_SCOPING`
- **Performance**: One file write per turn (negligible impact)

**Implementation Steps**:
1. Add JSON writer to `start_turn()` after SQLite insert
2. Extract `lastrowid` from cursor to get actual event_id
3. Ensure `state/turn_markers/` directory exists
4. Write `turn_start_{session_id}__{terminal_id}.json` with actual event_id
5. Add feature flag check before writing

---

## Known Unknowns

### Question 1: Turn Marker Lifecycle
**Unknown**: When should turn marker files be cleaned up?

**Options**:
- Clean up on session end (SessionStop hook)
- Clean up on next turn start (overwrite)
- Clean up after TTL (e.g., 2 hours)

**Recommendation**: Clean up on next turn start (overwrite) + session end cleanup

### Question 2: Event ID Reset
**Unknown**: Do event IDs reset between sessions?

**Assumption**: Yes, each new session starts with event_id = 1 or continues from previous session?

**Recommendation**: Verify SQLite `AUTOINCREMENT` behavior - IDs are global across all sessions, not reset

### Question 3: Multi-Terminal Turn Coordination
**Unknown**: Should turn markers be shared across terminals in same session?

**Current Design**: No - turn markers are terminal-scoped (`{terminal_id}` in filename)

**Recommendation**: Keep terminal-scoped - multi-terminal isolation is a design goal

### Question 4: Feature Flag Rollout
**Unknown**: Should turn scoping be enabled by default or require opt-in?

**Recommendation**: Opt-in (`VERIFICATION_USE_TURN_SCOPING=false` default) to validate behavior before widespread use

---

## Revised Estimate

**Original TASK-013 Estimate**: 5 points (contingent on TASK-006 findings)

**Revised Estimate**: 3 points

**Rationale**:
- Root cause is clear (missing JSON writer in `start_turn()`)
- Fix is straightforward (Option A: add file writer)
- No architectural changes needed
- Feature flag provides rollback safety

**Breakdown**:
- Implement JSON writer in `start_turn()`: 1pt
- Add feature flag check: 0.5pt
- Update `load_tool_events_for_context()` to use marker: 0.5pt
- Test with synthetic turn markers: 0.5pt
- Documentation and rollback plan: 0.5pt

**Total**: 3 points (down from 5)

---

## Dependencies

**Prerequisites**:
- TASK-001: `load_tool_events_for_context()` already implemented ✅
- TASK-006: Investigation complete ✅

**Blocking Tasks**:
- None - TASK-013 can proceed independently

**Related Tasks**:
- TASK-014, TASK-014b: Integration tests should validate turn scoping once implemented

---

## Acceptance Criteria

**TASK-013 Complete When**:
1. `start_turn()` writes JSON turn marker file with actual event_id (not 0)
2. `load_tool_events_for_context()` reads marker and filters `WHERE id > turn_start_event_id`
3. Feature flag `VERIFICATION_USE_TURN_SCOPING` controls filtering (default: false)
4. Integration test verifies turn isolation (events from previous turn excluded)
5. Rollback documentation complete (disable feature flag if issues arise)

**Verification Test**:
```python
# Create turn 1 marker
start_turn(session_id, terminal_id)  # Writes turn_start_event_id: 42

# Insert events in turn 1
append_tool_event(..., session_id, terminal_id)  # event_id: 43, 44, 45

# Create turn 2 marker
start_turn(session_id, terminal_id)  # Writes turn_start_event_id: 46

# Insert events in turn 2
append_tool_event(..., session_id, terminal_id)  # event_id: 47, 48

# Load with turn scoping enabled
events = load_tool_events_for_context(session_id, terminal_id, use_turn_scoping=True)
# Should return only event_ids 47, 48 (not 43, 44, 45)
```

---

## Next Steps

1. **Implement TASK-013** using Option A approach
2. **Add integration test** in TASK-014 to validate turn scoping
3. **Monitor performance** after rollout (check event loading latency)
4. **Roll out gradually** with feature flag (warn mode → block mode)
5. **Document findings** and update plan if new issues discovered
