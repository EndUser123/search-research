# Manual Integration Test: Two-Daemon Architecture

**Date**: 2026-03-08
**Purpose**: Verify both dreaming and search daemons can run simultaneously

---

## Test Prerequisites

1. Python 3.14+ installed
2. Terminal emulator capable of multiple sessions
3. Access to `P:\.claude\hooks\` directory

---

## Test Procedure

### Step 1: Start Dreaming Daemon (Terminal 1)

**Action**: Open a terminal and start the dreaming daemon

```bash
cd P:\.claude\hooks
python dreaming_daemon.py --daemon-type dreaming
```

**Expected Results**:
- Daemon starts without errors
- Log message: "Daemon starting..." with daemon type
- PID file created: `P:\.claude\hooks\state\dreaming-daemon.pid`
- State file created: `P:\.claude\hooks\state\dreaming-daemon-state.json`
- Log file created: `P:\.claude\hooks\logs\dreaming-daemon.log`

**Verification Commands** (in same terminal):
```bash
# Check PID file exists
ls -la P:/.claude/hooks/state/dreaming-daemon.pid

# Check daemon is running
cat P:/.claude/hooks/state/dreaming-daemon.pid
ps aux | grep $(cat P:/.claude/hooks/state/dreaming-daemon.pid)

# Check mutex was acquired (from logs)
tail -20 P:/.claude/hooks/logs/dreaming-daemon.log | grep -i mutex
```

---

### Step 2: Start Search Daemon (Terminal 2)

**Action**: Open a second terminal and start the search daemon

```bash
cd P:\.claude\hooks
python dreaming_daemon.py --daemon-type search
```

**Expected Results**:
- Daemon starts without errors
- Log message: "Daemon starting..." with daemon type
- PID file created: `P:\.claude\hooks\state\search-daemon.pid`
- State file created: `P:\.claude\hooks\state\search-daemon-state.json`
- Log file created: `P:\.claude\hooks\logs\search-daemon.log`

**Verification Commands** (in same terminal):
```bash
# Check PID file exists
ls -la P:/.claude/hooks/state/search-daemon.pid

# Check daemon is running
cat P:/.claude/hooks/state/search-daemon.pid
ps aux | grep $(cat P:/.claude/hooks/state/search-daemon.pid)

# Check mutex was acquired (from logs)
tail -20 P:/.claude/hooks/logs/search-daemon.log | grep -i mutex
```

---

### Step 3: Verify Both Daemons Running (Terminal 3)

**Action**: Open a third terminal and verify both daemons are running

```bash
# Check both PID files exist
ls -la P:/.claude/hooks/state/dreaming-daemon.pid
ls -la P:/.claude/hooks/state/search-daemon.pid

# Check both processes are running
ps aux | grep dreaming-daemon
ps aux | grep search-daemon

# Verify different mutex names (from logs)
echo "=== Dreaming Daemon Mutex ==="
tail -30 P:/.claude/hooks/logs/dreaming-daemon.log | grep -i "mutex\|singleton"

echo ""
echo "=== Search Daemon Mutex ==="
tail -30 P:/.claude/hooks/logs/search-daemon.log | grep -i "mutex\|singleton"
```

**Expected Results**:
- Both PID files exist
- Both processes are running (different PIDs)
- Dreaming daemon uses: `Global\ClaudeInsightDaemon`
- Search daemon uses: `Global\ClaudeSearchDaemon`

---

### Step 4: Test Singleton Enforcement (Terminal 1)

**Action**: Try to start a second dreaming daemon (should fail)

```bash
cd P:\.claude\hooks
python dreaming_daemon.py --daemon-type dreaming
```

**Expected Results**:
- Command exits with error code 1
- Error message: "Another daemon instance is already running with PID <pid>"
- No new PID file created
- Original daemon continues running

**Verification**:
```bash
# Check only one dreaming daemon PID file exists
ls -la P:/.claude/hooks/state/dreaming-daemon.pid

# Check original daemon still running
cat P:/.claude/hooks/state/dreaming-daemon.pid
ps aux | grep $(cat P:/.claude/hooks/state/dreaming-daemon.pid)
```

---

### Step 5: Test Search Singleton Enforcement (Terminal 2)

**Action**: Try to start a second search daemon (should fail)

```bash
cd P:\.claude\hooks
python dreaming_daemon.py --daemon-type search
```

**Expected Results**:
- Command exits with error code 1
- Error message: "Another daemon instance is already running with PID <pid>"
- No new PID file created
- Original search daemon continues running

**Verification**:
```bash
# Check only one search daemon PID file exists
ls -la P:/.claude/hooks/state/search-daemon.pid

# Check original daemon still running
cat P:/.claude/hooks/state/search-daemon.pid
ps aux | grep $(cat P:/.claude/hooks/state/search-daemon.pid)
```

---

### Step 6: Cleanup (Optional)

**Action**: Stop both daemons when testing is complete

```bash
# In Terminal 1
cd P:/.claude/hooks
python dreaming_daemon.py stop

# In Terminal 2
cd P:/.claude/hooks
python dreaming_daemon.py stop --daemon-type search
```

**Expected Results**:
- Both daemons shut down gracefully
- PID files deleted
- State files preserved
- Log files show shutdown messages

**Verification**:
```bash
# Check PID files are deleted
ls P:/.claude/hooks/state/dreaming-daemon.pid 2>&1 | grep "No such file"
ls P:/.claude/hooks/state/search-daemon.pid 2>&1 | grep "No such file"

# Verify processes stopped
ps aux | grep dreaming-daemon  # Should show nothing
ps aux | grep search-daemon    # Should show nothing
```

---

## Success Criteria

The manual integration test passes if:

- ✅ Dreaming daemon starts successfully with --daemon-type dreaming
- ✅ Search daemon starts successfully with --daemon-type search
- ✅ Both daemons run simultaneously (different PIDs, different mutexes)
- ✅ Second dreaming daemon is rejected (singleton enforcement works)
- ✅ Second search daemon is rejected (singleton enforcement works)
- ✅ Different mutex names are used (verified in logs)
- ✅ Different PID files are created (verified in filesystem)
- ✅ Different state files are created (verified in filesystem)
- ✅ Different log files are created (verified in filesystem)
- ✅ No WinError 32 file corruption errors
- ✅ Both daemons can be stopped independently

---

## Troubleshooting

### Issue: "Unknown daemon type" error

**Solution**: Verify `config/daemon_config.py` exists and contains DAEMON_TYPES

### Issue: "ModuleNotFoundError: No module named 'config.daemon_config'"

**Solution**: Ensure `config/__init__.py` exists and config package is importable

### Issue: Both daemons fail to start with mutex error

**Solution**: Check for zombie daemons:
```bash
ps aux | grep python | grep dreaming-daemon
ps aux | grep python | grep search-daemon
```
Kill zombie processes if found.

### Issue: Second daemon starts despite singleton enforcement

**Solution**: This is a bug! Report immediately with:
- PID files from both daemons
- Log output from both daemons
- `python -m pytest tests/test_two_daemon_architecture.py -v` output

---

## Test Report Template

After completing the manual test, report:

**Date**: [test date]
**Tester**: [your name]
**Test Environment**: [OS, Python version]

**Results**:
- [ ] Dreaming daemon starts successfully
- [ ] Search daemon starts successfully
- [ ] Both daemons run simultaneously
- [ ] Singleton enforcement works (dreaming)
- [ ] Singleton enforcement works (search)
- [ ] No WinError 32 errors
- [ ] Both daemons can stop independently

**Issues Found**: [list any issues or "None"]

**Overall Assessment**: [PASS / FAIL]

---

**Test Status**: READY FOR EXECUTION
**Created**: 2026-03-08
**Priority**: P1 - Manual integration verification
