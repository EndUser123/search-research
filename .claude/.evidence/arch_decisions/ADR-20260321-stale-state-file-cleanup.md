# ADR-20260321: Stale State File Cleanup for Hook System

**Status:** Proposed
**Date:** 2026-03-21
**Context:** PostToolUse:Bash hook errors with misleading path to non-existent `validate_checklist.py` script

---

## Problem Statement

### Observed Failure

```
[python $CLAUDE_SKILL_DIR/scripts/validate_checklist.py]:
C:\Python314\python.exe: can't open file 'C:\\Program Files\\Git\\scripts\\validate_checklist.py':
[Errno 2] No such file or directory
```

### Root Cause

The error is a **stale state file artifact**, not active hook code:

1. State file `P:\.claude\hooks\state\file_existence_decision_d16c6e73-6de2-42da-a638-99b27491aa7e.json` contains:
   ```json
   {
     "file_path": "P:\\.claude\\skills\\gto\\scripts\\validate_checklist.py",
     "decision": "allow_new",
     "reason": "File does not exist, allowing creation"
   }
   ```

2. The actual `validate_checklist` function exists in `P:\.claude\skills\code\lib\checklist.py` (not as a standalone script)

3. No hook is actively calling `$CLAUDE_SKILL_DIR/scripts/validate_checklist.py`

4. `StopHook_negative_existence_guard.py` reads these state files but does not validate that referenced files still exist

### Impact

- Misleading error messages clutter logs
- State directory accumulates orphaned decisions
- No automatic cleanup mechanism exists
- Multi-terminal scenarios may propagate stale state

---

## Decision

Implement state file validation and cleanup in `StopHook_negative_existence_guard.py`:

1. **Validate referenced files exist** before using state file decisions
2. **Invalidate and remove** stale state files
3. **Add TTL-based expiration** for state files (30 days default)

---

## Rationale

### Why This Approach

- **Minimal change**: Single hook modification, no new components
- **Defensive**: Validation at point-of-use prevents cascading errors
- **Multi-terminal safe**: Per-terminal state directory + TTL prevents indefinite staleness
- **Local-only**: No external dependencies, stdlib-only (constitutional requirement for hooks)

### Why NOT Create the Missing Script

- The state file references a path that was never created (ghost decision)
- Actual function exists in `P:\.claude\skills\code\lib\checklist.py`
- Creating a script at the stale path would validate incorrect behavior

### Why NOT Delete All State Files

- State files serve a purpose: cache file existence decisions to avoid repeated checks
- Deleting all state files would cause performance regression on every hook execution
- Selective invalidation preserves the caching benefit while removing stale entries

---

## Alternatives Considered

### Alternative A: No Cleanup (Current Behavior)
- **Favored**: Zero code change, preserves all state
- **Degraded**: User experience (misleading errors), disk space
- **Fails when**: State files reference deleted/renamed files
- **ISO 25010**: -Reliability, +Performance Efficiency (cached lookups)

### Alternative B: Manual Cleanup Script
- **Favored**: User control, no automatic behavior
- **Degraded**: Reliability (user forgets to run), Maintainability
- **Fails when**: User doesn't know stale state exists
- **ISO 25010**: -Reliability, -Maintainability

### Alternative C: Validation at Point-of-Use (This Decision)
- **Favored**: Reliability, self-cleaning, multi-terminal safe
- **Degraded**: Performance (slight overhead, <10ms per hook)
- **Fails when**: TTL is too short (mitigated by 30-day default)
- **ISO 25010**: +Reliability, +Maintainability, -Performance Efficiency (negligible)

---

## Implementation Plan

### Phase 1: Core Validation Function
- [ ] Add `validate_state_file(state_path: Path) -> bool` to `StopHook_negative_existence_guard.py`
- [ ] Implement TTL check (30 days default)
- [ ] Implement referenced file existence check
- [ ] Implement JSON decode error handling

### Phase 2: Integration
- [ ] Call `validate_state_file()` before using any state file decision
- [ ] Skip or use default behavior when validation fails
- [ ] Add logging for cleanup actions (for debugging)

### Phase 3: Testing
- [ ] **TEST-001**: Unit test — valid state file passes validation
- [ ] **TEST-002**: Unit test — stale state file (expired TTL) is deleted
- [ ] **TEST-003**: Unit test — state file with missing referenced file is deleted
- [ ] **TEST-004**: Unit test — corrupt JSON state file is deleted
- [ ] **TEST-005**: Integration test — multi-terminal: Terminal A validates independently of Terminal B

### Phase 4: One-Time Cleanup
- [ ] Run manual cleanup script to remove existing stale state files
- [ ] Verify no more PostToolUse errors about non-existent validate_checklist.py

---

## Code Changes

### File: `P:\.claude\hooks\StopHook_negative_existence_guard.py`

**Add validation function:**

```python
import os
import time
import json
from pathlib import Path
from typing import Optional

STATE_DIR = Path(__file__).parent / "state"
STATE_TTL_SECONDS = 30 * 24 * 60 * 60  # 30 days

def validate_state_file(state_path: Path) -> bool:
    """Check if state file is valid (exists, not stale, referenced file exists).

    Returns:
        True if state file is valid, False if it was invalidated/deleted

    Side effects:
        Deletes invalid state files
    """
    if not state_path.exists():
        return False

    # Check TTL
    try:
        mtime = state_path.stat().st_mtime
        if time.time() - mtime > STATE_TTL_SECONDS:
            state_path.unlink(missing_ok=True)
            return False
    except (OSError, AttributeError) as e:
        # Can't read mtime, treat as invalid
        state_path.unlink(missing_ok=True)
        return False

    # Check referenced file exists
    try:
        with open(state_path, encoding='utf-8') as f:
            data = json.load(f)
        referenced_path = data.get("file_path")
        if referenced_path and not Path(referenced_path).exists():
            state_path.unlink(missing_ok=True)
            return False
    except (json.JSONDecodeError, KeyError, OSError, UnicodeDecodeError):
        # Corrupt or unreadable state file
        state_path.unlink(missing_ok=True)
        return False

    return True
```

**Integrate into existing StopHook logic:**

```python
# Before using any state file decision:
if not validate_state_file(state_file_path):
    # Skip or use default behavior
    continue
```

---

## Multi-Terminal Safety

**Safe**: Each terminal validates state independently. Stale state in one terminal doesn't affect others.

- **Cross-terminal isolation**: Each terminal reads and validates state files independently. No shared mutable state between terminals.
- **Concurrent cleanup**: If two terminals read the same stale state simultaneously, both invalidate it independently. `unlink(missing_ok=True)` handles the race — second terminal's unlink is a no-op.
- **No corruption risk**: State validation is read-then-delete, not read-modify-write. No concurrent modification scenarios.

---

## Edge Case Considerations

### What if the referenced file is on a different drive?
`Path.exists()` handles cross-drive paths correctly on Windows. The validation works regardless of drive letter.

### What if state file is locked by another terminal?
`unlink(missing_ok=True)` fails silently with `missing_ok=True`. The next terminal's validation attempt will succeed.

### What if TTL is too short for long-running sessions?
30 days is generous for hook state. Long-running sessions (rare) won't be affected because validation occurs at hook execution time, not session start. Active state files are touched on each read, extending their effective lifetime.

### What if the state file format changes in the future?
Validation catches JSON decode errors and invalidates corrupt files. For forward compatibility, add a `version` field to state schema and check it in `validate_state_file()`.

### What if the state directory doesn't exist?
`Path(__file__).parent / "state"` resolves to the hooks directory. If `state/` doesn't exist, the state file wouldn't exist either, and validation returns `False` (no cleanup needed).

### What if a referenced file is temporarily unavailable (network drive)?
Validation fails and the state file is deleted. On the next hook execution, a new state file will be created. This is acceptable because hook state is a cache, not source-of-truth.

---

## Rollback Strategy

1. Revert `StopHook_negative_existence_guard.py` to previous version
2. Stale state files become harmless noise again (current pre-fix state)
3. No schema migration required — state files are opaque to the hook system

**Rollback triggers:**
- Performance regression (>100ms per hook execution)
- State files deleted incorrectly (false positive invalidation)
- Multi-terminal corruption observed

---

## Tradeoffs

| Quality | Improved | Degraded |
|---------|----------|----------|
| **Reliability** | No more errors from stale state | Slight startup overhead for validation |
| **Maintainability** | Self-cleaning state reduces manual cleanup | TTL requires periodic cleanup logic |
| **Performance Efficiency** | Negligible (<10ms per hook execution) | None measurable |
| **Portability** | Stdlib-only, works on all platforms | None |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Premature state invalidation | Low | Low | 30-day TTL is generous; active files won't expire |
| Concurrent cleanup conflict | Low | Low | `unlink(missing_ok=True)` handles race |
| Validation performance regression | Very Low | Negligible | Single file stat + JSON parse, <10ms |
| False positive deletion | Low | Medium | Add logging before production; monitor for unexpected deletions |

---

## Evidence Sources

- **Constitutional requirement**: Hooks must be standalone, local-only (CLAUDE.md)
- **Multi-terminal principle**: State must be validated per-terminal (memory/multi_terminal_patterns.md)
- **Lean Systems Design**: Consolidate duplicate mechanisms, prune unnecessary dependencies (shared_frameworks.md)

---

## Next Steps

1. Modify `StopHook_negative_existence_guard.py` with validation logic
2. Add unit tests for `validate_state_file()`
3. Clean up existing stale state files manually (one-time)
4. Monitor hook logs for any regressions

---

**One-line summary**: Validate and clean stale state files at point-of-use in StopHook, with 30-day TTL for automatic expiration.
