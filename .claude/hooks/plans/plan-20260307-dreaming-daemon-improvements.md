# Implementation Plan: Dreaming Daemon Improvements

**Date**: 2026-03-07
**Status**: READY-FOR-IMPLEMENTATION
**Phase**: 1 - Canonical PID Preservation (LOW RISK)
**Optional Phase**: 2 - Multi-Terminal Coordination (HIGH RISK, requires user approval)

---

## 1. Overview

Implement canonical PID preservation for the dreaming daemon to prevent accidental termination of the legitimate daemon process during zombie cleanup. This improvement addresses the cross-pollination opportunity from the semantic daemon: **read PID file first before checking process liveness, preserve canonical daemon PID when cleaning up stale processes**.

**Problem**: During zombie cleanup, the daemon may kill all daemon processes including the legitimate one, because zombie detection doesn't distinguish between stale processes and the canonical daemon.

**Solution**: Add `canonical_pid` to `DreamingState`, preserve first-acquired PID, and enhance zombie detection to check canonical PID before cleanup.

**Success Criteria**:
- Canonical PID preserved on first acquisition
- Zombie cleanup never kills canonical daemon
- PID reuse edge cases handled
- All existing tests pass + new tests added

**Estimated Effort**: 30 minutes (Phase 1 only)

---

## 2. Architecture

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ dreaming_daemon.py                                          │
│  ├── main_async()                                          │
│  │   ├── _check_for_zombie_daemon()                       │
│  │   │   └── acquire_singleton(force=True) [cleanup]     │
│  │   ├── acquire_singleton() [lock acquisition]           │
│  │   ├── load_state()                                     │
│  │   ├── JSONLTailer                                       │
│  │   ├── InsightsGenerator                                │
│  │   └── _daemon_loop_async()                             │
└─────────────────────────────────────────────────────────────┘
         ↓                              ↓
┌──────────────────────┐    ┌──────────────────────┐
│ dreaming_mutex.py    │    │ dreaming_state.py    │
│  ├── acquire_        │    │  ├── DreamingState   │
│  │   singleton()     │    │  │   ├── version      │
│  │   [Windows mutex  │    │  │   ├── offset       │
│  │    + PID file]    │    │  │   ├── heartbeat    │
│  └── release_        │    │  │   ├── current_file │
│      singleton()     │    │  │   └── shutdown     │
└──────────────────────┘    │  │   └── [NEW]        │
                            │  │       canonical_pid│
                            │  └── load/save_state()│
                            └──────────────────────┘
```

### Proposed Changes (Phase 1)

**1. DreamingState Extension** (`dreaming_state.py`):
```python
@dataclass
class DreamingState:
    version: int = 1
    offset: int = 0
    heartbeat: str = ""
    current_file: str = ""
    shutdown: bool = False
    canonical_pid: int = 0  # NEW - Preserve first-acquired PID
```

**2. Mutex Acquisition Enhancement** (`dreaming_mutex.py`):
```python
def acquire_singleton(pid_file: str, force: bool = False) -> tuple[bool, str]:
    """
    Acquire singleton lock using Windows mutex + PID file.

    Enhancement: Preserve canonical PID on first acquisition.
    """
    # Step 1: Check PID file (skip if force=True)
    # Step 2: Create Windows mutex
    # Step 3: Verify mutex not stale (skip if force=True)
    # Step 4: Write PID atomically + UPDATE canonical_pid in state
    # Step 5: Return result
```

**3. Zombie Detection Enhancement** (`dreaming_daemon.py`):
```python
def _check_for_zombie_daemon(config: dict) -> bool:
    """
    Check for stale mutex + heartbeat indicating zombie daemon.

    Enhancement: Check canonical_pid before cleanup.
    - If heartbeat stale AND PID not canonical → safe to cleanup
    - If heartbeat stale AND PID is canonical → CRITICAL, daemon failed
    """
```

### Optional Phase 2 (Multi-Terminal Coordination)

**Enhanced SessionStart Hook** (`SessionStart_dreaming_daemon.py`):
```python
# PROBLEM: Multiple terminals opening simultaneously race to start daemon
# SOLUTION: Windows mutex with randomized backoff (50-150ms jitter)

max_retries = 3
for attempt in range(max_retries):
    try:
        mutex = win32event.CreateMutex(None, False, DAEMON_MUTEX_NAME)
        if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
            # Another terminal is starting - wait with jitter
            jitter = random.randint(50, 150)
            wait_time = 100 + jitter
            win32event.WaitForSingleObject(mutex, wait_time)

            # Check if daemon is now running
            if is_daemon_running():
                return {"status": "started_by_other"}

            # Retry if not last attempt
            if attempt < max_retries - 1:
                time.sleep(0.05)
                continue

        break  # Got the mutex or daemon is running

    except Exception as e:
        if attempt < max_retries - 1:
            time.sleep(0.05)
            continue
```

---

## 3. Data Flow

### Canonical PID Preservation Flow

```
┌──────────────────────────────────────────────────────────────┐
│ Daemon Startup (main_async)                                   │
└──────────────────────────────────────────────────────────────┘
      ↓
      ├─→ _check_for_zombie_daemon()
      │   └─→ load_state(STATE_FILE)
      │       └─→ if heartbeat stale AND pid != canonical_pid
      │           └─→ acquire_singleton(force=True) [cleanup]
      │
      ├─→ acquire_singleton(pid_file)
      │   ├─→ [Windows mutex check]
      │   ├─→ [PID file check]
      │   └─→ **NEW**: if first acquisition
      │           ├─→ load_state()
      │           ├─→ state.canonical_pid = os.getpid()
      │           └─→ save_state(state) [atomic write]
      │
      └─→ _daemon_loop_async()
          └─→ Every poll interval:
              └─→ _update_heartbeat_and_state_async(state)
                  └─→ save_state() [includes canonical_pid]
```

### Zombie Detection Flow

```
┌──────────────────────────────────────────────────────────────┐
│ Zombie Detection (_check_for_zombie_daemon)                  │
└──────────────────────────────────────────────────────────────┘
      ↓
      ├─→ load_state(STATE_FILE)
      │   └─→ state.heartbeat, state.canonical_pid
      │
      ├─→ if heartbeat stale (>180s)
      │   ├─→ if state.canonical_pid == 0
      │   │   └─→ [No canonical PID yet] → safe to cleanup
      │   │
      │   ├─→ if stale_pid != state.canonical_pid
      │   │   └─→ [Stale PID is not canonical] → safe to cleanup
      │   │
      │   └─→ if stale_pid == state.canonical_pid
      │       └─→ **CRITICAL**: Canonical daemon failed!
      │           ├─→ Log ERROR, DO NOT CLEANUP
      │           └─→ Return False (let startup fail)
      │
      └─→ acquire_singleton(force=True) [if safe to cleanup]
          └─→ Skip process running check, acquire mutex
```

### Multi-Terminal Coordination Flow (Phase 2 - Optional)

```
┌──────────────────────────────────────────────────────────────┐
│ SessionStart Hook (multiple terminals racing)                │
└──────────────────────────────────────────────────────────────┘
Terminal A      Terminal B      Terminal C
    │               │               │
    ├─→ CreateMutex (WAIT)          │
    ├─→ WaitForSingleObject (100-250ms with jitter)
    │               ├─→ CreateMutex (WAIT)
    │               ├─→ WaitForSingleObject (100-250ms with jitter)
    │                                 ├─→ CreateMutex (WAIT)
    │                                 └─→ WaitForSingleObject
    │
    ├─→ Check daemon running → NO
    ├─→ Start daemon
    │   └─→ canonical_pid = PID_A
    │
    ├─→ ReleaseMutex
    │               ├─→ Check daemon running → YES
    │               └─→ Return "started_by_other"
    │                                 ├─→ Check daemon running → YES
    │                                 └─→ Return "started_by_other"
```

---

## 4. Error Handling

### Edge Cases and Failure Modes

**1. PID Reuse (OS reassigns PID to new process)**

*Problem*: OS may reuse canonical PID after daemon exits, making zombie detection think canonical daemon is still alive.

*Mitigation*:
- Check heartbeat freshness along with PID existence
- If heartbeat stale (>180s) even if PID exists → treat as zombie
- Log WARNING when PID reuse detected

*Test Scenario*:
```python
def test_pid_reuse_detection():
    """
    Test that zombie detection handles PID reuse correctly.

    Given: canonical_pid=1234, heartbeat stale (>180s), OS reassigned PID to new process
    When: _check_for_zombie_daemon() runs
    Then: Detect zombie (heartbeat stale) and cleanup safely
    """
```

**2. State File Corruption (canonical_pid lost)**

*Problem*: State file corrupted, canonical_pid reset to 0.

*Mitigation*:
- State file has backup rotation (.json.1, .json.2, .json.3)
- Load state tries all backups before falling back to default
- If canonical_pid == 0, treat as "no canonical PID yet" (safe to cleanup)

*Test Scenario*:
```python
def test_state_corruption_fallback():
    """
    Test that state corruption falls back to backups.

    Given: Primary state file corrupted, backup has canonical_pid=1234
    When: load_state() runs
    Then: Load from backup, canonical_pid preserved
    """
```

**3. Race Condition (Two terminals starting simultaneously)**

*Problem*: Both terminals detect stale heartbeat, both try cleanup.

*Mitigation* (Phase 2):
- Mutex-based coordination with randomized backoff (50-150ms jitter)
- Only one terminal gets mutex, performs cleanup
- Other terminals wait and retry

*Test Scenario*:
```python
def test_concurrent_startup():
    """
    Test that concurrent terminals don't race during startup.

    Given: 3 terminals start simultaneously, daemon not running
    When: All terminals call _check_for_zombie_daemon()
    Then: Only one terminal performs cleanup, others wait
    """
```

**4. Canonical Daemon Failure (heartbeat stale but PID is canonical)**

*Problem*: Canonical daemon crashed but OS hasn't reassigned PID yet.

*Mitigation*:
- Check heartbeat freshness along with PID existence
- If heartbeat stale (>180s) AND pid == canonical_pid → CRITICAL FAILURE
- Log ERROR, DO NOT CLEANUP, let startup fail
- User must manually kill stale process

*Test Scenario*:
```python
def test_canonical_daemon_failure():
    """
    Test that canonical daemon failure is detected.

    Given: canonical_pid=1234, heartbeat stale (>180s), PID still exists
    When: _check_for_zombie_daemon() runs
    Then: Return False (do not cleanup), log ERROR
    """
```

**5. Cross-Terminal State Consistency (multiple terminals reading/writing state)**

*Problem*: Two terminals simultaneously update state file, causing corruption.

*Mitigation*:
- `_state_lock` (threading.Lock) protects concurrent writes
- Atomic writes using `tempfile.NamedTemporaryFile + os.replace()`
- Daemon runs as singleton, only one process updates state

*Test Scenario*:
```python
def test_concurrent_state_updates():
    """
    Test that concurrent state updates are safe.

    Given: Daemon running, multiple threads call save_state()
    When: All threads write to state file simultaneously
    Then: No corruption, all writes serialized by _state_lock
    """
```

---

## 5. Test Strategy

### Unit Tests (Phase 1)

**Test Suite 1: Canonical PID Preservation**

```python
class TestCanonicalPidPreservation:
    """Tests for canonical PID preservation on first acquisition."""

    def test_first_acquisition_saves_canonical_pid(self, tmp_path):
        """
        Test that first acquisition saves canonical PID to state.

        Given: No PID file exists and canonical_pid=0 in state
        When: acquire_singleton() is called
        Then: state.canonical_pid == os.getpid()
        """

    def test_second_acquisition_preserves_canonical_pid(self, tmp_path):
        """
        Test that second acquisition preserves first canonical PID.

        Given: PID file exists with canonical_pid=1234
        When: acquire_singleton() is called again
        Then: state.canonical_pid remains 1234 (not updated to current PID)
        """

    def test_canonical_pid_persists_across_restarts(self, tmp_path):
        """
        Test that canonical PID persists across daemon restarts.

        Given: Daemon with canonical_pid=1234 exits and restarts
        When: New daemon loads state
        Then: state.canonical_pid == 1234 (preserved from previous run)
        """
```

**Test Suite 2: Zombie Detection with Canonical PID**

```python
class TestZombieDetectionWithCanonicalPid:
    """Tests for zombie detection using canonical PID."""

    def test_stale_non_canonical_pid_cleanup_allowed(self, tmp_path):
        """
        Test that stale non-canonical PID allows cleanup.

        Given: canonical_pid=1234, stale PID=5678 (heartbeat stale)
        When: _check_for_zombie_daemon() runs
        Then: Cleanup allowed (5678 != 1234)
        """

    def test_stale_canonical_pid_blocks_cleanup(self, tmp_path):
        """
        Test that stale canonical PID blocks cleanup.

        Given: canonical_pid=1234, stale PID=1234 (heartbeat stale)
        When: _check_for_zombie_daemon() runs
        Then: Cleanup blocked (CRITICAL FAILURE), return False
        """

    def test_no_canonical_pid_allows_cleanup(self, tmp_path):
        """
        Test that missing canonical PID allows cleanup.

        Given: canonical_pid=0, stale PID=5678 (heartbeat stale)
        When: _check_for_zombie_daemon() runs
        Then: Cleanup allowed (no canonical PID yet)
        """
```

**Test Suite 3: Edge Cases**

```python
class TestCanonicalPidEdgeCases:
    """Tests for canonical PID edge cases."""

    def test_pid_reuse_detected_by_heartbeat(self, tmp_path):
        """
        Test that PID reuse is detected by heartbeat freshness.

        Given: canonical_pid=1234, PID exists but heartbeat stale (>180s)
        When: _check_for_zombie_daemon() runs
        Then: Treat as zombie (heartbeat stale > PID existence)
        """

    def test_state_corruption_recovers_canonical_pid(self, tmp_path):
        """
        Test that state corruption recovers canonical PID from backup.

        Given: Primary state corrupted, backup has canonical_pid=1234
        When: load_state() runs
        Then: Load from backup, canonical_pid == 1234
        """

    def test_atomic_state_update_preserves_canonical_pid(self, tmp_path):
        """
        Test that atomic state updates preserve canonical PID.

        Given: state.canonical_pid=1234
        When: save_state() called during concurrent access
        Then: No corruption, canonical_pid preserved
        """
```

### Integration Tests (Phase 1)

**Test Suite 4: End-to-End Workflows**

```python
class TestCanonicalPidIntegration:
    """Integration tests for canonical PID preservation."""

    def test_full_daemon_lifecycle_preserves_canonical_pid(self, tmp_path):
        """
        Test full daemon lifecycle preserves canonical PID.

        Given: Daemon starts, runs, exits, restarts
        When: Full lifecycle executed
        Then: canonical_pid preserved across restart
        """

    def test_zombie_cleanup_preserves_canonical_daemon(self, tmp_path):
        """
        Test zombie cleanup preserves canonical daemon.

        Given: Daemon with canonical_pid=1234 running, stale daemon with PID=5678
        When: New terminal starts, detects zombie
        Then: Cleans up 5678, preserves 1234
        """

    def test_canonical_daemon_failure_detected(self, tmp_path):
        """
        Test canonical daemon failure is detected.

        Given: Daemon with canonical_pid=1234 crashed (heartbeat stale)
        When: New terminal starts, attempts cleanup
        Then: Detects canonical failure, blocks cleanup, logs ERROR
        """
```

### Optional Phase 2 Tests (Multi-Terminal Coordination)

**Test Suite 5: Multi-Terminal Coordination**

```python
class TestMultiTerminalCoordination:
    """Tests for multi-terminal startup coordination."""

    def test_concurrent_startup_mutex_coordination(self, tmp_path):
        """
        Test concurrent terminals coordinate via mutex.

        Given: 3 terminals start simultaneously, daemon not running
        When: All terminals run startup sequence
        Then: Only one starts daemon, others wait and detect "started_by_other"
        """

    def test_randomized_backoff_prevents_race(self, tmp_path):
        """
        Test randomized backoff prevents race conditions.

        Given: 5 terminals starting simultaneously
        When: All terminals use 50-150ms jitter
        Then: No race conditions, only one daemon starts
        """

    def test_terminal_jitter_distribution(self, tmp_path):
        """
        Test jitter distribution is within expected range.

        Given: 100 concurrent startup attempts
        When: Jitter applied each time
        Then: All values within 50-150ms range, distribution uniform
        """
```

### Test Execution Plan

```bash
# Phase 1 Tests (REQUIRED)
pytest P:/.claude/hooks/tests/test_dreaming_mutex.py -v
pytest P:/.claude/hooks/tests/test_dreaming_state.py -v
pytest P:/.claude/hooks/tests/test_dreaming_daemon.py -v

# Optional Phase 2 Tests (if user approves Phase 2)
pytest P:/.claude/hooks/tests/test_sessionstart_dreaming_daemon.py -v

# Full regression suite
pytest P:/.claude/hooks/tests/ -v --cov=dreaming_mutex --cov=dreaming_state --cov=dreaming_daemon
```

---

## 6. Standards Compliance

### Python 2025+ Best Practices

**Toolchain**:
- `uv` for package management
- `ruff` for linting and formatting
- `mypy` for type checking
- `pytest` for testing

**Type Hints**:
- All functions use type hints (`def func(x: int) -> str:`)
- Use `|` for union types (Python 3.10+)
- Generic types: `list[str]` not `List[str]`

**Async Patterns**:
- Use `asyncio` for I/O-bound operations (file reads, network calls)
- Avoid `asyncio.sleep()` in mutex acquisition (use time.sleep())
- Exception handling in async functions

**Code Quality**:
- `ruff check` — no warnings
- `ruff format` — consistent formatting
- `mypy` — strict type checking
- Coverage: 80%+ minimum (critical code: 90%+)

### Testing Best Practices

**Anti-Mock Stance**:
- Do NOT use Mock objects
- Test with real system resources (Windows mutex, PID files, state files)
- Tests verify actual behavior, not implementation assumptions

**Test Structure**:
- Arrange-Act-Assert (AAA) pattern
- Descriptive test names (`test_<what>_<when>_<then>`)
- Isolated tests (no dependencies between tests)

**Verification**:
- All tests pass before committing
- Coverage threshold enforced
- Manual TRACE verification for critical flows

---

## 7. Ramifications

### Impact on Existing Code

**Backward Compatibility**: ✅ FULLY COMPATIBLE

- `canonical_pid` field added to `DreamingState` with default value `0`
- Existing state files without `canonical_pid` load with default `0`
- No breaking changes to function signatures
- All existing tests continue to pass

**Migration Path**: AUTOMATIC

- Old state files (without `canonical_pid`) load with default `0`
- First acquisition after upgrade sets `canonical_pid`
- No manual migration required

### Rollback Strategy

**If issues detected**:

1. **Immediate rollback**: Revert code changes
2. **State cleanup**: Delete `canonical_pid` from state files (optional, defaults to `0`)
3. **Safe fallback**: Daemon works without `canonical_pid` (same as before)

**Rollback command**:
```bash
git revert <commit-hash>
pytest P:/.claude/hooks/tests/ -v  # Verify tests still pass
```

### Performance Impact

**Startup time**: +0ms (negligible)
- One additional state file read (already loading state)
- One integer comparison per zombie check

**Runtime overhead**: +0ms (no change)
- `canonical_pid` updated during existing heartbeat updates
- No additional polling or checks

**Memory overhead**: +8 bytes per state file
- One `int` field added to `DreamingState` dataclass

### Security Considerations

**No security impact**:
- Canonical PID is informational only
- No authentication/authorization changes
- No new attack vectors introduced

### Operational Impact

**Monitoring**: Enhanced observability
- `canonical_pid` visible in state file
- Easier to identify which daemon instance is canonical
- Better debugging for multi-terminal scenarios

**Troubleshooting**: Improved
- Canonical daemon failure detected and logged
- PID reuse edge case handled
- Clearer error messages

---

## 8. Pre-Mortem Analysis (Step 4.5)

**Failure Scenario**: "It's 3 months later. The dreaming daemon improvements were deployed, but users report daemon keeps terminating unexpectedly."

### Brainstorm Causes (10+)

1. **Canonical PID not preserved** → Bug in state.save(), canonical_pid lost on restart
2. **Zombie cleanup kills canonical daemon** → Logic error in canonical_pid check
3. **PID reuse confuses detection** → OS reuses PID, daemon thinks it's still running
4. **State file corruption** → Concurrent writes corrupt state, canonical_pid = 0
5. **Race condition in startup** → Two terminals start simultaneously, both cleanup
6. **Heartbeat freshness not checked** → Stale heartbeat not detected, zombie not cleaned
7. **Windows mutex leak** → Mutex not released, prevents future daemon starts
8. **Thread safety issue** → `_state_lock` not used, concurrent writes corrupt state
9. **Test false positives** → Tests pass but production fails (mock vs real system)
10. **Edge case unhandled** → PID=0 (invalid PID), negative PID, PID overflow
11. **Multi-terminal coordination failure** (Phase 2) → Jitter insufficient, races occur
12. **Daemon never starts** → Canonical daemon false positive blocks all startups

### Categorize Failure Modes

**People** (solo dev):
- Insufficient testing (mock tests vs real system)
- Edge cases overlooked (PID reuse, PID=0)

**Process**:
- No manual TRACE verification (tests pass but logic wrong)
- Incomplete error handling (edge cases crash daemon)

**Technology**:
- State file corruption (concurrent writes)
- Race conditions (multi-terminal startup)
- Windows mutex behavior (stale handles)

**External**:
- OS PID reuse behavior
- Windows mutex quirks

### Top 6 Priorities (Risk Score ≥ 6)

**1. [RISK:9] Canonical PID not preserved on first acquisition**
- **Prevent**: Add test `test_first_acquisition_saves_canonical_pid()`, TRACE through `acquire_singleton()`
- **Warning**: Daemon startups without canonical_pid in state
- **Owner**: Implementation phase

**2. [RISK:9] Zombie cleanup kills canonical daemon**
- **Prevent**: Add test `test_stale_canonical_pid_blocks_cleanup()`, verify logic before deploying
- **Warning**: Logs show "Cleaning up canonical daemon PID"
- **Owner**: Implementation phase

**3. [RISK:9] PID reuse confuses zombie detection**
- **Prevent**: Check heartbeat freshness along with PID existence, test `test_pid_reuse_detected_by_heartbeat()`
- **Warning**: Logs show "Daemon running but heartbeat stale"
- **Owner**: Implementation phase

**4. [RISK:6] State file corruption from concurrent writes**
- **Prevent**: Verify `_state_lock` protects all writes, test `test_atomic_state_update_preserves_canonical_pid()`
- **Warning**: JSON decode errors in state loading
- **Owner**: Implementation phase

**5. [RISK:6] Race condition in multi-terminal startup (Phase 2)**
- **Prevent**: Mutex-based coordination with randomized jitter, test `test_concurrent_startup()`
- **Warning**: Multiple daemons running simultaneously
- **Owner**: Phase 2 implementation (if approved)

**6. [RISK:6] Test false positives (mock tests vs real system)**
- **Prevent**: Follow anti-mock stance, test with real Windows mutex and PID files
- **Warning**: Tests pass but production fails
- **Owner**: Test phase

### Warning Signs to Monitor

- □ Daemon startups without canonical_pid in state (should always be set after first acquisition)
- □ Logs show "Cleaning up canonical daemon PID" (should never happen)
- □ Multiple daemons running simultaneously (indicates race condition)
- □ JSON decode errors when loading state (indicates corruption)
- □ Daemon startup failures (may indicate canonical daemon false positive)

---

## 9. Execution Path Verification (Step 4.5)

**Purpose**: Verify planned execution paths are reachable and complete before implementation.

**Target**: Non-linear flow in `acquire_singleton()` and `_check_for_zombie_daemon()`.

### TRACE: acquire_singleton() Execution Flow

```
1. Initial State
   - pid_file: str
   - force: bool = False
   - mutex: None
   - success: False

2. Check PID file exists (skip if force=True)
   ├─→ PID file not exist
   │   └─→ Continue to mutex creation
   │
   └─→ PID file exists
       ├─→ Read PID from file
       ├─→ Check if process running (skip if force=True)
       │   ├─→ Process running
       │   │   └─→ Return (False, "Daemon already running")
       │   │
       │   └─→ Process not running
       │       └─→ Continue to mutex creation
       │
       └─→ Error reading PID
           └─→ Continue to mutex creation (defensive)

3. Create Windows mutex
   ├─→ Mutex creation succeeds
   │   └─→ Continue to mutex check
   │
   └─→ Mutex creation fails
       └─→ Return (False, "Failed to create mutex")

4. Check if mutex already exists (skip if force=True)
   ├─→ Mutex exists and stale (GetLastError() == ERROR_ALREADY_EXISTS)
   │   ├─→ CloseHandle() on stale mutex
   │   └─→ Continue to PID write
   │
   ├─→ Mutex exists and not stale
   │   └─→ Return (False, "Daemon already running")
   │
   └─→ Mutex doesn't exist (we created it)
       └─→ Continue to PID write

5. Write PID atomically
   ├─→ Load state
   │   ├─→ state.canonical_pid == 0 (first acquisition)
   │   │   └─→ Set state.canonical_pid = os.getpid()
   │   │
   │   └─→ state.canonical_pid != 0 (subsequent acquisition)
   │       └─→ Keep existing canonical_pid
   │
   ├─→ Write state atomically (tempfile + os.replace())
   │
   ├─→ Write PID file atomically (tempfile + os.replace())
   │
   └─→ Return (True, "")

✓ All branches reachable
✓ Cleanup paths exist (error cases return early)
✓ No early exits that skip critical steps
✓ State updated atomically
✓ Defensive error handling
```

### TRACE: _check_for_zombie_daemon() Execution Flow

```
1. Initial State
   - config: dict
   - zombie_timeout: int (default 180)
   - state: DreamingState

2. Load state
   ├─→ Load succeeds
   │   └─→ Continue to heartbeat check
   │
   └─→ Load fails
       └─→ Return False (defensive, treat as no zombie)

3. Check heartbeat exists
   ├─→ No heartbeat in state
   │   └─→ Return False (no heartbeat to check)
   │
   └─→ Heartbeat exists
       └─→ Continue to age check

4. Check heartbeat age
   ├─→ Heartbeat fresh (<180s)
   │   └─→ Return False (daemon healthy)
   │
   └─→ Heartbeat stale (>180s)
       └─→ Continue to canonical PID check

5. Check canonical_pid
   ├─→ canonical_pid == 0 (no canonical PID yet)
   │   └─→ Safe to cleanup, continue to force acquisition
   │
   ├─→ Stale PID != canonical_pid
   │   └─→ Safe to cleanup (stale process is not canonical)
   │
   └─→ Stale PID == canonical_pid
       ├─→ Log ERROR "Canonical daemon failed, DO NOT CLEANUP"
       └─→ Return False (BLOCK CLEANUP)

6. Force acquire mutex (if safe to cleanup)
   ├─→ acquire_singleton(force=True) succeeds
   │   ├─→ Log INFO "Zombie daemon mutex cleaned up"
   │   └─→ Return True
   │
   └─→ acquire_singleton(force=True) fails
       ├─→ Log ERROR "Failed to clean zombie mutex"
       └─→ Return False

✓ All branches reachable
✓ Critical check (canonical PID) blocks cleanup
✓ No unreachable code
✓ Error paths logged
✓ Defensive programming (state load fails gracefully)
```

### Verification Results

**✅ PASS** - All execution paths verified:
- No unreachable branches
- No early exits that skip critical logic
- Cleanup paths exist for all error cases
- Canonical PID check is in correct location (before force acquisition)
- State updates are atomic
- Error handling is defensive

---

## 10. Implementation Tasks

### Phase 1: Canonical PID Preservation (REQUIRED)

**Task T-001**: Add `canonical_pid` field to `DreamingState` dataclass
- **File**: `P:/.claude/hooks/dreaming_state.py`
- **Action**: Add `canonical_pid: int = 0` field to dataclass
- **Acceptance**:
  - Field added with default value `0`
  - Type hint correct (`int`)
  - Backward compatible (existing state files load without error)
- **Verification**: `pytest tests/test_dreaming_state.py -v`

**Task T-002**: Enhance `acquire_singleton()` to preserve canonical PID
- **File**: `P:/.claude/hooks/dreaming_mutex.py`
- **Action**:
  - Load state before writing PID file
  - If `state.canonical_pid == 0`, set to `os.getpid()`
  - Save state atomically
- **Acceptance**:
  - First acquisition sets `canonical_pid`
  - Subsequent acquisitions preserve existing `canonical_pid`
  - State saved atomically
- **Verification**: `pytest tests/test_dreaming_mutex.py::TestCanonicalPidPreservation -v`

**Task T-003**: Enhance `_check_for_zombie_daemon()` to check canonical PID
- **File**: `P:/.claude/hooks/dreaming_daemon.py`
- **Action**:
  - Load state and check `state.canonical_pid`
  - If stale PID == canonical_pid, log ERROR and return False
  - If stale PID != canonical_pid, safe to cleanup
- **Acceptance**:
  - Canonical daemon failure detected and logged
  - Non-canonical zombie cleanup allowed
  - No cleanup when canonical PID is stale
- **Verification**: `pytest tests/test_dreaming_daemon.py::TestZombieDetectionWithCanonicalPid -v`

**Task T-004**: Add tests for canonical PID preservation
- **File**: `P:/.claude/hooks/tests/test_dreaming_mutex.py`
- **Action**: Add test class `TestCanonicalPidPreservation` with 3+ tests
- **Acceptance**:
  - Test first acquisition saves canonical PID
  - Test second acquisition preserves canonical PID
  - Test canonical PID persists across restarts
- **Verification**: `pytest tests/test_dreaming_mutex.py::TestCanonicalPidPreservation -v`

**Task T-005**: Add tests for zombie detection with canonical PID
- **File**: `P:/.claude/hooks/tests/test_dreaming_daemon.py`
- **Action**: Add test class `TestZombieDetectionWithCanonicalPid` with 3+ tests
- **Acceptance**:
  - Test stale non-canonical PID allows cleanup
  - Test stale canonical PID blocks cleanup
  - Test no canonical PID allows cleanup
- **Verification**: `pytest tests/test_dreaming_daemon.py::TestZombieDetectionWithCanonicalPid -v`

**Task T-006**: Add edge case tests
- **File**: `P:/.claude/hooks/tests/test_dreaming_state.py`
- **Action**: Add test class `TestCanonicalPidEdgeCases` with 3+ tests
- **Acceptance**:
  - Test PID reuse detected by heartbeat
  - Test state corruption recovers canonical PID
  - Test atomic state update preserves canonical PID
- **Verification**: `pytest tests/test_dreaming_state.py::TestCanonicalPidEdgeCases -v`

**Task T-007**: Run full regression suite
- **Action**: `pytest P:/.claude/hooks/tests/ -v`
- **Acceptance**:
  - All 115+ existing tests pass
  - All 9+ new tests pass
  - Coverage ≥80% (critical code ≥90%)
- **Verification**: Test output shows pass rate

### Optional Phase 2: Multi-Terminal Coordination (Requires User Approval)

**Task T-101**: Add multi-terminal coordination to SessionStart hook
- **File**: `P:/.claude/hooks/SessionStart_dreaming_daemon.py` (NEW)
- **Action**:
  - Implement Windows mutex-based startup coordination
  - Add randomized backoff (50-150ms jitter)
  - Add retry logic (max 3 attempts)
- **Acceptance**:
  - Concurrent terminals coordinate via mutex
  - Only one terminal starts daemon
  - Other terminals wait and detect "started_by_other"
- **Verification**: `pytest tests/test_sessionstart_dreaming_daemon.py -v`

**Task T-102**: Add multi-terminal tests
- **File**: `P:/.claude/hooks/tests/test_sessionstart_dreaming_daemon.py` (NEW)
- **Action**: Add test class `TestMultiTerminalCoordination` with 3+ tests
- **Acceptance**:
  - Test concurrent startup mutex coordination
  - Test randomized backoff prevents race
  - Test jitter distribution within range
- **Verification**: `pytest tests/test_sessionstart_dreaming_daemon.py -v`

---

## 11. Success Criteria

**Phase 1 (Canonical PID Preservation)**:
- ✅ All 7 tasks completed (T-001 through T-007)
- ✅ All 115+ existing tests pass
- ✅ All 9+ new tests pass
- ✅ Coverage ≥80% (critical code ≥90%)
- ✅ Manual TRACE verification passes
- ✅ No regressions in daemon behavior

**Optional Phase 2 (Multi-Terminal Coordination)**:
- ✅ Tasks T-101, T-102 completed (if user approves)
- ✅ All Phase 1 tests still pass
- ✅ All Phase 2 tests pass
- ✅ Coverage ≥80%
- ✅ No race conditions in concurrent startup

**Definition of Done**:
- Code changes committed to git
- Tests pass locally and in CI
- Documentation updated (CLAUDE.md if needed)
- Ready for /qa certification

---

## 12. Dependencies

**Required Dependencies** (already installed):
- Python 3.12+
- pytest (testing)
- ruff (linting/formatting)
- mypy (type checking)

**No new dependencies required** for Phase 1.

**Optional Phase 2 Dependencies** (if approved):
- pywin32 (Windows mutex API)

---

## 13. Timeline

**Phase 1**: 30 minutes
- T-001 to T-003: Implementation (15 min)
- T-004 to T-006: Tests (10 min)
- T-007: Regression suite (5 min)

**Optional Phase 2**: 1-2 hours (if user approves)
- T-101: Implementation (45 min)
- T-102: Tests (30 min)
- Regression suite (15 min)

**Total**: 30 minutes (Phase 1 only) or 1.5-2.5 hours (Phase 1 + Phase 2)

---

## 14. Next Actions

1. **User Approval**: Confirm Phase 1 implementation (canonical PID preservation)
2. **Optional**: Confirm if Phase 2 (multi-terminal coordination) is needed
3. **Begin TDD**: Start Phase 5 (TDD) with Task T-001

---

**Plan Status**: READY-FOR-IMPLEMENTATION
**Created**: 2026-03-07
**Phase**: 1 - Canonical PID Preservation (LOW RISK)
**Optional Phase**: 2 - Multi-Terminal Coordination (HIGH RISK, requires approval)
