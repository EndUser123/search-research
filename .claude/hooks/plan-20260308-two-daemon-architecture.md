# Implementation Plan: Two-Daemon Architecture

**Date**: 2026-03-08
**Status**: FEATURE DEVELOPMENT
**Priority**: P1 - Multi-daemon infrastructure

---

## 1. Overview

**Objective**: Enable two separate daemons (dreaming and search) to run simultaneously with independent mutex enforcement, PID files, state files, and log files.

**Current Problem**: The dreaming daemon uses hardcoded mutex names and file paths, making it impossible to run multiple daemon types simultaneously without conflicts.

**Solution**: Make mutex names and file paths configurable through a unified daemon configuration system.

**Success Criteria**:
- ✅ Dreaming daemon continues working (backward compatible)
- ✅ Search daemon can run simultaneously with dreaming daemon
- ✅ Each daemon type enforces singleton within its type
- ✅ No WinError 32 file corruption between daemons
- ✅ Tests verify both daemons can run concurrently

**Estimated Effort**: 2-3 hours

---

## 2. Architecture

### Current State (Hardcoded)

```
dreaming_mutex.py:
  mutex_name = "Global\\ClaudeInsightDaemon"  # ← HARDCODED

dreaming_daemon.py:
  PID_FILE = STATE_DIR / "dreaming-daemon.pid"  # ← HARDCODED
  STATE_FILE = STATE_DIR / "dreaming-daemon-state.json"  # ← HARDCODED
  DAEMON_LOG = LOGS_DIR / "dreaming-daemon.log"  # ← HARDCODED
```

### Target State (Configurable)

```
dreaming_config.py:
  DAEMON_TYPES = {
    "dreaming": {
      "mutex_name": "Global\\ClaudeInsightDaemon",
      "pid_file": "dreaming-daemon.pid",
      "state_file": "dreaming-daemon-state.json",
      "daemon_log": "dreaming-daemon.log",
    },
    "search": {
      "mutex_name": "Global\\ClaudeSearchDaemon",
      "pid_file": "search-daemon.pid",
      "state_file": "search-daemon-state.json",
      "daemon_log": "search-daemon.log",
    }
  }

dreaming_mutex.py:
  def acquire_singleton(pid_file, mutex_name, state_file)
  def _create_windows_mutex(mutex_name)

dreaming_daemon.py:
  def main(daemon_type="dreaming")  # ← NEW PARAMETER
    config = DAEMON_TYPES[daemon_type]
    paths = build_paths(config)
    mutex_name = config["mutex_name"]
```

### Data Flow

```
User/Script starts daemon:
  ├── dreaming-daemon.py --daemon-type=dreaming
  │   ├── Load DAEMON_TYPES["dreaming"]
  │   ├── Build paths from config
  │   ├── acquire_singleton(pid_file, mutex_name, state_file)
  │   │   └── _create_windows_mutex("Global\\ClaudeInsightDaemon")
  │   └── Start daemon loop
  │
  └── dreaming-daemon.py --daemon-type=search  (future)
      ├── Load DAEMON_TYPES["search"]
      ├── Build paths from config
      ├── acquire_singleton(pid_file, mutex_name, state_file)
      │   └── _create_windows_mutex("Global\\ClaudeSearchDaemon")
      └── Start daemon loop
```

---

## 3. Component Changes

### File 1: `dreaming_config.py` (EXTEND)

**Changes**:
- Add `DAEMON_TYPES` configuration dictionary
- Add `get_daemon_config(daemon_type)` function
- Keep existing config unchanged (backward compatible)

### File 2: `dreaming_mutex.py` (MODIFY)

**Changes**:
- Modify `acquire_singleton()` signature: add `mutex_name` parameter
- Modify `_create_windows_mutex()` signature: add `mutex_name` parameter
- Update all call sites to pass mutex_name
- Default value maintains backward compatibility

**Backward Compatibility**:
```python
def acquire_singleton(pid_file: str, mutex_name: str = "Global\\ClaudeInsightDaemon",
                    state_file: str | None = None, force: bool = False):
```

### File 3: `dreaming_daemon.py` (MODIFY)

**Changes**:
- Add `--daemon-type` command-line argument
- Pass daemon_type to main() function
- Build paths from DAEMON_TYPES config
- Pass mutex_name to acquire_singleton()

**CLI Usage**:
```bash
# Default (backward compatible)
python dreaming-daemon.py

# Explicit dreaming daemon
python dreaming-daemon.py --daemon-type dreaming

# Search daemon (future)
python dreaming-daemon.py --daemon-type search
```

### File 4: `tests/test_two_daemon_architecture.py` (CREATE)

**New Tests**:
1. `test_dreaming_daemon_config_exists` - Verify dreaming config
2. `test_search_daemon_config_exists` - Verify search config
3. `test_mutex_names_are_different` - Verify different mutexes
4. `test_pid_files_are_different` - Verify different PID files
5. `test_state_files_are_different` - Verify different state files
6. `test_log_files_are_different` - Verify different log files
7. `test_both_daemons_can_acquire_mutex` - Verify concurrent mutex acquisition
8. `test_backward_compatibility_default_daemon_type` - Verify default is dreaming

---

## 4. Error Handling

### Error Scenarios

**Scenario 1: Invalid daemon type**
```python
if daemon_type not in DAEMON_TYPES:
    error_msg = f"Unknown daemon type: {daemon_type}. Known types: {list(DAEMON_TYPES.keys())}"
    logger.error(error_msg)
    sys.exit(1)
```

**Scenario 2: Missing required config key**
```python
config = DAEMON_TYPES.get(daemon_type)
required_keys = ["mutex_name", "pid_file", "state_file", "daemon_log"]
missing = [k for k in required_keys if k not in config]
if missing:
    error_msg = f"Daemon config missing keys: {missing}"
    logger.error(error_msg)
    sys.exit(1)
```

**Scenario 3: Mutex creation fails**
- Already handled by existing exception handling in dreaming_mutex.py
- Returns (False, error) from acquire_singleton()
- Daemon exits with error code 1

---

## 5. Test Strategy

### Unit Tests

**Test Suite 1: Configuration System**
```python
class TestDaemonConfig:
    def test_dreaming_config_exists(self)
    def test_search_config_exists(self)
    def test_get_daemon_config_returns_correct_type(self)
    def test_get_daemon_config_raises_on_unknown_type(self)
```

**Test Suite 2: Mutex System**
```python
class TestTwoDaemonMutex:
    def test_mutex_names_are_different(self)
    def test_both_daemons_can_acquire_mutex(self)
    def test_mutex_name_default_is_dreaming(self)
```

**Test Suite 3: Path Construction**
```python
class TestPathConstruction:
    def test_pid_files_are_different(self)
    def test_state_files_are_different(self)
    def test_log_files_are_different(self)
    def test_paths_are_absolute(self)
```

### Integration Tests

```python
class TestTwoDaemonIntegration:
    def test_both_daemons_start_simultaneously(self):
        """Start both dreaming and search daemons, verify both run."""

    def test_singleton_enforcement_within_type(self):
        """Verify only one dreaming daemon runs, only one search daemon runs."""
```

### Test Execution

```bash
# Unit tests
pytest P:/.claude/hooks/tests/test_two_daemon_architecture.py -v

# Integration tests (manual)
# Terminal 1: python dreaming-daemon.py --daemon-type dreaming
# Terminal 2: python dreaming-daemon.py --daemon-type search
# Terminal 3: python dreaming-daemon.py --daemon-type dreaming  # Should fail
```

---

## 6. Standards Compliance

### Python 2025+ Best Practices

- **Type hints**: All new functions use type hints
- **Error handling**: Explicit exceptions, no bare excepts
- **Configuration**: Structured dict-based config with validation
- **Testing**: Anti-mock stance, test with real system resources

### Code Quality

- **ruff check**: No warnings
- **mypy**: Strict type checking
- **Coverage**: 80%+ minimum (critical code: 90%+)

---

## 7. Ramifications

### Impact on Existing Code

**Breaking Changes**: NONE

- **Backward Compatible**: Default daemon_type="dreaming" maintains existing behavior
- **Optional Configuration**: Daemon type parameter is optional (defaults to dreaming)
- **No Migration Needed**: Existing dreaming-daemon.pid files continue working

### Risk Assessment

**Risk Level**: LOW
- Changes are additive (adding configurability)
- Existing behavior preserved via defaults
- Clear error messages for misconfiguration
- Tests verify backward compatibility

### Rollback Strategy

If issues arise:
1. Revert commits to dreaming_mutex.py, dreaming_daemon.py, dreaming_config.py
2. Daemons work as before (single dreaming daemon only)
3. No data loss or corruption

---

## 8. Pre-Mortem Analysis

**Failure Scenario**: "It's 2 weeks later. The two-daemon architecture is deployed, but users report daemons won't start."

### Potential Causes

1. **Config file missing** → Daemon crashes on startup
   - **Prevention**: Include default config in code, file is optional
   - **Detection**: Test with missing config file

2. **Wrong daemon type** → Typo in --daemon-type parameter
   - **Prevention**: Clear error message with known types listed
   - **Detection**: Test with invalid daemon type

3. **Mutex name collision** → Both daemons try to use same mutex
   - **Prevention**: Config validation ensures unique mutex names
   - **Detection**: Test mutex names are different

4. **Path conflicts** → Both daemons write to same file
   - **Prevention**: Path construction includes daemon type in filename
   - **Detection**: Test paths are different

### Observability Plan

**Metrics to show success**:
- Daemon startup logs show daemon type
- Mutex acquisition logs show mutex name
- File paths in logs include daemon type

**Alerts for failure**:
- Daemon exits with error code 1 (logged)
- Mutex acquisition failure (logged with mutex name)
- Config validation failure (logged with missing keys)

**Diagnosis points**:
- Log file: `{daemon_type}-daemon.log`
- PID file: `{daemon_type}-daemon.pid`
- State file: `{daemon_type}-daemon-state.json`

---

## 9. Implementation Tasks

### Task T-001: Extend dreaming_config.py

**File**: `P:\.claude\hooks\dreaming_config.py`

**Actions**:
1. Add `DAEMON_TYPES` configuration dictionary
2. Add `get_daemon_config(daemon_type: str) -> dict` function
3. Add validation for required config keys
4. Document configuration format

**Acceptance**:
- DAEMON_TYPES contains dreaming and search configs
- get_daemon_config() returns correct config
- Raises ValueError on unknown daemon_type
- Config contains mutex_name, pid_file, state_file, daemon_log

**Verification**: Read dreaming_config.py, verify structure

---

### Task T-002: Modify dreaming_mutex.py

**File**: `P:\.claude\hooks\dreaming_mutex.py`

**Actions**:
1. Add `mutex_name` parameter to `acquire_singleton()` with default value
2. Add `mutex_name` parameter to `_create_windows_mutex()`
3. Pass mutex_name through to CreateMutexW call
4. Update docstrings

**Acceptance**:
- acquire_singleton() accepts mutex_name parameter
- Default value is "Global\\ClaudeInsightDaemon" (backward compatible)
- _create_windows_mutex() uses provided mutex_name

**Verification**: Inspect function signatures, test with default and explicit mutex_name

---

### Task T-003: Modify dreaming_daemon.py

**File**: `P:\.claude\hooks\dreaming_daemon.py`

**Actions**:
1. Add `--daemon-type` argument to argparse
2. Pass daemon_type to main() function
3. Call get_daemon_config() to get config
4. Build paths from config
5. Pass mutex_name to acquire_singleton()
6. Update logging to show daemon type

**Acceptance**:
- `--daemon-type` argument works
- Default daemon_type is "dreaming"
- Config lookup works for both types
- Mutex name passed to acquire_singleton()
- Log messages include daemon type

**Verification**:
- `python dreaming-daemon.py` (default)
- `python dreaming-daemon.py --daemon-type dreaming`
- `python dreaming-daemon.py --daemon-type search`

---

### Task T-004: Create test suite

**File**: `P:\.claude\hooks\tests\test_two_daemon_architecture.py` (NEW)

**Actions**:
1. Test configuration system (4 tests)
2. Test mutex differences (2 tests)
3. Test path differences (3 tests)
4. Test backward compatibility (1 test)

**Acceptance**:
- 10 tests total
- All tests pass
- Coverage ≥80%
- Tests verify both daemon types work

**Verification**: `pytest tests/test_two_daemon_architecture.py -v`

---

### Task T-005: Manual integration test

**Actions**:
1. Start dreaming daemon in terminal 1
2. Start search daemon in terminal 2
3. Verify both are running (check PID files)
4. Try to start second dreaming daemon in terminal 3 (should fail)
5. Verify log files show correct daemon types

**Acceptance**:
- Both daemons run simultaneously
- Second dreaming daemon is rejected
- Log files are separate
- No WinError 32 errors

**Verification**: Manual terminal testing, check logs

---

### Task T-006: Update documentation

**File**: `P:\.claude\hooks\README.md` or `CLAUDE.md`

**Actions**:
1. Document two-daemon architecture
2. Add usage examples
3. Update daemon startup instructions
4. Add troubleshooting section

**Acceptance**:
- Documentation explains --daemon-type parameter
- Examples show how to run both daemons
- Troubleshooting covers common issues

**Verification**: Read documentation, verify clarity

---

## 10. Success Criteria

- ✅ Dreaming daemon works as before (backward compatible)
- ✅ Configuration system supports multiple daemon types
- ✅ Mutex names are configurable and different
- ✅ File paths are configurable and different
- ✅ All tests pass (10+ new tests)
- ✅ Manual integration test passes
- ✅ Documentation updated

---

## 11. Timeline

**Total**: 2-3 hours
- T-001: Config extension (30 min)
- T-002: Mutex modification (15 min)
- T-003: Daemon startup modification (30 min)
- T-004: Test suite creation (45 min)
- T-005: Manual integration test (30 min)
- T-006: Documentation (15 min)

---

## 12. Next Steps

1. **Start T-001**: Extend dreaming_config.py with DAEMON_TYPES
2. **Implement T-002**: Modify mutex system for configurability
3. **Implement T-003**: Update daemon startup
4. **Create T-004**: Write comprehensive test suite
5. **Manual T-005**: Integration testing with two terminals
6. **Update T-006**: Document new architecture

---

**Plan Status**: READY-FOR-IMPLEMENTATION
**Created**: 2026-03-08
**Priority**: P1 - Multi-daemon infrastructure
