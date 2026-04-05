# Plan: Multi-Terminal + Compaction-Safe State Scoping

**Created:** 2026-03-03
**Status:** POST-HOC-REVIEW
**Task:** #1284

## 1. Problem Statement

Seven hooks use session-scoped or unscoped state files that break during compaction events or cause conflicts in multi-terminal scenarios:

- **Compaction breaks session-scoped state**: Session IDs change during compaction, causing state loss
- **Multi-terminal conflicts**: Multiple terminals can share the same session ID (user override), causing data corruption
- **Unscoped state files**: `error_attribution_tracker.py` uses a single shared state file for all terminals/sessions

**Root Cause**: State files don't include terminal_id component, relying solely on session_id or no scoping at all.

## 2. Context Analysis

### Current State File Pattern (WRONG)
```python
# These break on compaction:
state_dir / f"grounded_artifact_{session_id}.json"
state_dir / f"pretool_degraded_{session_id}.json"
base / f"pending_command_intent_{session_id}.json"
SESSION_DIR / f"failures_{session_id}.json"
```

### Correct Pattern (from observe_before_act_gate.py)
```python
# Line 63: Already correct ✅
STATE_DIR / f"observe_gate_{safe_terminal}_{safe_session}.json"
```

### Why terminal_id Matters

**Session IDs**: UUID4, collision-free (~10^-18), BUT change during compaction
**Terminal IDs**: Persist across compaction, unique per terminal instance

**Compaction Event**:
- Session ID: `abc-123` → `xyz-789` (CHANGES)
- Terminal ID: `ConsoleHost_4` → `ConsoleHost_4` (PERSISTS)

### State File Naming Convention

**Required pattern**: `{hook_name}_{terminal_id}_{session_id}.json`
- `terminal_id` first for consistency with existing code
- `session_id` second for uniqueness within terminal
- Both sanitized: `re.sub(r"[^a-zA-Z0-9_.-]+", "_", id)`

## 3. Existing Implementation Discovery

### Hooks Requiring Fixes

| Hook | Line(s) | Current Pattern | Risk |
|------|---------|-----------------|------|
| `PreToolUse.py` | 131, 140, 228 | `{session_id}.json` | Breaks on compaction |
| `PreToolUse_command_intent_gate.py` | 102 | `{session_id}.json` | Duplicate, breaks on compaction |
| `recursive_failure_detector.py` | 54 + 66-68 | `{session_id}.json` + TTL | Breaks on compaction, unwanted TTL |
| `skill_enforcer.py` | 134 | `{session_id}.json` | Breaks on compaction |
| `error_attribution_tracker.py` | 33 | NO SCOPING | Multi-terminal collision |

### Already Correct ✅

| Hook | Pattern |
|------|---------|
| `PreToolUse_observe_before_act_gate.py` | `{terminal_id}_{session_id}.json` |
| Bulk delete gate | Uses git tags (correctly shared) |

### Terminal ID Detection

**Location**: `.claude/hooks/terminal_detection.py` (v2.1)
**Priority Order**:
1. Environment variable: `CLAUDE_TERMINAL_ID`
2. Project state file: `.claude/state/terminal_id.txt`
3. Temp file: `/tmp/claude_terminal_id.txt`
4. ConsoleHost process enumeration

**Usage Pattern**:
```python
from terminal_detection import detect_terminal_id

terminal_id = str(
    data.get("terminal_id")
    or data.get("terminalId")
    or os.environ.get("CLAUDE_TERMINAL_ID", "")
).strip()

safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id or "unknown")
```

## 4. Test Discovery

### Manual Test Strategy

**Test 1: Multi-terminal isolation**
```bash
# Terminal A
export CLAUDE_TERMINAL_ID=test_term_A
python -c "from hooks import PreToolUse; ..."  # Trigger hook

# Terminal B
export CLAUDE_TERMINAL_ID=test_term_B
python -c "from hooks import PreToolUse; ..."  # Trigger hook

# Verify separate state files exist
ls P:/.claude/hooks/state/ | grep test_term
```

**Test 2: Compaction safety**
```bash
# Start session
terminal_id=$CLAUDE_TERMINAL_ID
session_id_1=$CLAUDE_SESSION_ID

# Trigger state write
# ... run hook ...

# Simulate compaction (new session_id)
export CLAUDE_SESSION_ID=new_session_after_compaction

# Verify state still accessible (terminal_id unchanged)
# ... run hook reads state ...
```

**Test 3: User override collision**
```bash
# Terminal A
export CLAUDE_SESSION_ID=debug_session
export CLAUDE_TERMINAL_ID=term_A
# Trigger hook

# Terminal B
export CLAUDE_SESSION_ID=debug_session  # SAME session_id
export CLAUDE_TERMINAL_ID=term_B  # DIFFERENT terminal_id
# Trigger hook

# Verify separate files exist
ls P:/.claude/hooks/state/ | grep debug_session
```

## 5. Proposed Solution

### Implementation Strategy

Fix all 7 hooks using this consistent pattern:

```python
# 1. Resolve terminal_id from input or environment
terminal_id = str(
    data.get("terminal_id")
    or data.get("terminalId")
    or os.environ.get("CLAUDE_TERMINAL_ID", "")
).strip()

# 2. Sanitize for filename
safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id or "unknown")
safe_session = re.sub(r"[^a-zA-Z0-9_.-]+", "_", session_id or "unknown")

# 3. Use in state path (terminal_id FIRST for consistency)
state_path = STATE_DIR / f"hook_name_{safe_terminal}_{safe_session}.json"
```

### File-by-File Changes

#### 1. PreToolUse.py (3 locations)

**Line 131 (_write_grounded_artifact)**:
```python
# OLD:
artifact_path = state_dir / f"grounded_artifact_{safe_session}.json"

# NEW:
artifact_path = state_dir / f"grounded_artifact_{safe_terminal}_{safe_session}.json"
```

**Line 140 (_degraded_state_paths)**:
```python
# OLD:
state_dir / f"pretool_degraded_{safe_session}.json",
fallback_dir / f"pretool_degraded_{safe_session}.json",

# NEW:
state_dir / f"pretool_degraded_{safe_terminal}_{safe_session}.json",
fallback_dir / f"pretool_degraded_{safe_terminal}_{safe_session}.json",
```

**Line 228 (pending command intent)**:
```python
# OLD:
candidate = base / f"pending_command_intent_{safe_session}.json"

# NEW:
candidate = base / f"pending_command_intent_{safe_terminal}_{safe_session}.json"
```

#### 2. PreToolUse_command_intent_gate.py (1 location)

**Line 102**:
```python
# OLD:
filename = f"pending_command_intent_{session_id}.json"

# NEW:
terminal_id = str(
    data.get("terminal_id")
    or os.environ.get("CLAUDE_TERMINAL_ID", "")
).strip()
safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id or "unknown")
filename = f"pending_command_intent_{safe_terminal}_{session_id}.json"
```

**Note**: This duplicates PreToolUse.py line 228. Consider consolidating after verification.

#### 3. recursive_failure_detector.py (1 location + TTL removal)

**Line 54**:
```python
# OLD:
return SESSION_DIR / f"failures_{session_id}.json"

# NEW:
terminal_id = os.environ.get("CLAUDE_TERMINAL_ID", "default")
safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", terminal_id)
return SESSION_DIR / f"failures_{safe_terminal}_{session_id}.json"
```

**Lines 66-68 (REMOVE TTL filtering)**:
```python
# REMOVE THESE LINES:
cutoff = datetime.now() - timedelta(minutes=WINDOW_MINUTES)
return [f for f in failures
        if datetime.fromisoformat(f["timestamp"]) > cutoff]

# REPLACE WITH:
return failures
```

#### 4. skill_enforcer.py (1 location)

**Line 134**:
```python
# OLD:
scoped_file = base / f"active_command_{terminal_id}.json"  # Line 160 ✅ Already correct
# But line 134 is wrong:
state_file = base / f"pending_command_intent_{session_id}.json"

# NEW:
safe_terminal = _safe_id(_get_terminal_id(context))
state_file = base / f"pending_command_intent_{safe_terminal}_{session_id}.json"
```

#### 5. error_attribution_tracker.py (1 unscoped file)

**Line 33 (PRIMARY STATE FILE)**:
```python
# OLD:
STATE_FILE = Path("P:/.claude/hooks/state/last_error_source.json")

# NEW (make terminal-scoped like the fallback at line 262):
STATE_FILE_TEMPLATE = Path("P:/.claude/hooks/state/last_error_source_{terminal_id}.json")
```

**Update constructor (around line 77)**:
```python
# Initialize terminal-specific state file
if self.terminal_id:
    safe_terminal = re.sub(r"[^a-zA-Z0-9_.-]+", "_", self.terminal_id)
    self.STATE_FILE = STATE_FILE_TEMPLATE.parent / f"last_error_source_{safe_terminal}.json"
else:
    self.STATE_FILE = Path("P:/.claude/hooks/state/last_error_source_unknown.json")
```

## 6. Implementation Plan

### Execution Order

1. **PreToolUse.py** (highest priority - affects 3 state files)
2. **recursive_failure_detector.py** (remove TTL + add terminal_id)
3. **skill_enforcer.py** (UserPromptSubmit hook)
4. **error_attribution_tracker.py** (PostToolUse - highest risk)
5. **PreToolUse_command_intent_gate.py** (duplicate - verify consolidation opportunity)

### Verification Steps

After each file change:
1. Run multi-terminal isolation test
2. Run compaction safety test
3. Run user override collision test
4. Verify state file naming matches `{hook}_{terminal}_{session}.json`

### Consolidation Opportunities

**Duplicate Discovery**: `pending_command_intent` appears in two hooks:
- `PreToolUse.py` line 228
- `PreToolUse_command_intent_gate.py` line 102

**Action**: After verification, consider consolidating to single implementation.

## 7. Risks, Success Criteria, Dependencies

### Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Module-level constant import in error_attribution_tracker.py | Low | High | Search for imports before refactoring |
| Breaking existing multi-terminal workflows | Low | Medium | Terminal ID is additive, not breaking |
| State file accumulation (no cleanup) | Medium | Low | Existing issue, out of scope |
| TTL removal causes stale failures | Low | Low | Session scoped, cleared on session end |

### Success Criteria

1. ✅ All 7 hooks use `{terminal_id}_{session_id}.json` pattern
2. ✅ No TTL filtering in any hook (user requirement)
3. ✅ Multi-terminal test passes: separate state files for same session_id
4. ✅ Compaction test passes: state accessible after session_id change
5. ✅ No module-level constants requiring runtime evaluation

### Rollback Strategy

**If breaking issue discovered**:
1. Git revert each file individually
2. Verify terminal_id detection still works
3. Re-test with safe rollback pattern: `{terminal_id or "default"}`
4. Document failure mode for future reference

**Rollback command**:
```bash
git revert HEAD  # Most recent fix
git revert HEAD~1  # Previous fix
# etc.
```

### Dependencies

- **Required**: `terminal_detection.py` v2.1 (already exists)
- **Required**: `re` module (standard library)
- **Required**: `pathlib.Path` (standard library)
- **Optional**: Consolidate `pending_command_intent` hooks after verification

## 8. Top Risks

1. **Module-level constant import**: error_attribution_tracker.py may have other code importing `STATE_FILE` before refactoring
2. **State file accumulation**: No TTL means files accumulate (acceptable trade-off for correctness)
3. **Duplicate hooks**: Two hooks handle `pending_command_intent` - may need consolidation

## 9. Next Actions

1. Search for imports of `STATE_FILE` from error_attribution_tracker.py
2. Fix PreToolUse.py (3 locations)
3. Fix recursive_failure_detector.py (add terminal_id, remove TTL)
4. Fix skill_enforcer.py
5. Fix error_attribution_tracker.py (refactor to instance-level)
6. Fix PreToolUse_command_intent_gate.py
7. Run full test suite (multi-terminal + compaction + collision)
8. Verify consolidation opportunity for duplicate hooks
