# Terminal ID Detection - Quick Reference

**Last Updated**: 2026-03-09
**Status**: Working correctly with hooks-aware directory traversal

---

## Common Issues and Solutions

### Issue: terminal_id Shows "unknown"

**Symptom**: Handoff files show `"terminal_id": "unknown"`

**Diagnosis Steps**:
1. Check which detection method should be working:
   ```bash
   # Check environment variables
   echo $CLAUDE_TERMINAL_ID
   echo $TERMINAL_ID
   ```

2. Verify project state file exists:
   ```bash
   ls -la P:/.claude/state/terminal_id.json
   ```

3. Check hook execution directory:
   ```bash
   pwd  # Should show .claude/hooks/ when hook runs
   ```

**Common Causes**:
- **Environment variable not set** → Expected, fallback to project state
- **Project state file missing** → Create via SessionStart hook
- **Execution context wrong** → Hooks run from `.claude/hooks/`, not project root

**Solution**: The fix handles all these cases automatically. If you see "unknown", check:
1. Is `CLAUDE_TERMINAL_ID` set?
2. Does `P:/.claude/state/terminal_id.json` exist?
3. Are hooks running from correct directory?

---

### Issue: "Handoff restore failed" Error

**Symptom**: SessionStart shows error loading handoff

**Diagnosis**:
```bash
# Check if handoff file exists
ls -la P:/.claude/state/handoff/*_handoff.json

# Verify handoff structure
cat P:/.claude/state/handoff/*_handoff.json | grep terminal_id
```

**Common Causes**:
- Handoff file corrupted
- Wrong terminal_id in filename vs content
- Missing handoff_internal structure

**Solution**: Delete stale handoff file, allow re-creation on next compaction

---

### Issue: Tests Failing with RuntimeError

**Symptom**: Tests fail with "Terminal ID detection failed"

**Context**: Expected behavior after fix - fail-fast instead of silent fallback

**Legacy tests expecting old behavior**:
```python
# Old test (expects fallback to "terminal_1")
terminal_id = detect_terminal_id()
assert terminal_id == "terminal_1"  # ❌ NOW FAILS
```

**Updated test**:
```python
# New test (expects fail-fast)
with pytest.raises(RuntimeError):
    terminal_id = detect_terminal_id()  # ✅ CORRECT
```

**Solution**: Update tests to expect RuntimeError, not fallback

---

## Detection Priority Order

The system tries these methods in order:

1. **Environment Variables** (priority 1)
   - `CLAUDE_TERMINAL_ID` - Process-scoped, inherited by subprocesses
   - `TERMINAL_ID`, `TERM_ID`, `SESSION_TERMINAL` - Legacy names

2. **Project State File** (priority 2)
   - Location: `P:/.claude/state/terminal_id.json`
   - Validation: PID match OR parent PID match
   - Freshness: <2 hours old

3. **Temp File** (priority 3)
   - Location: `%TEMP%\claude_terminal_id.txt`
   - Freshness: <48 hours old
   - Deprecated - can cause cross-session bleeding

4. **ConsoleHost Handle** (priority 4)
   - Windows only: `GetConsoleWindow()`
   - Returns hex window handle

5. **Fail-Fast** (priority 5)
   - Raises RuntimeError if all methods fail
   - No silent fallback to "unknown"

---

## Format Standards

**Normalized Format**: `{source}_{id}`

| Source | Prefix | Example |
|--------|--------|---------|
| Environment variable | `env_` | `env_abc123-def456` |
| Project state | `project_` | `project_1a2b3c` |
| Temp file | `tempfile_` | `tempfile_9f8e7d` |
| ConsoleHost | `console_` | `console_123abc` |

**Legacy Format Handling**:
- `ConsoleHost_XXXX` → Normalized to `console_XXXX`
- `session_XXXX` → Normalized to `env_XXXX` (came from SessionStart)

---

## Security Properties

### Cross-Terminal Isolation (NON-NEGOTIABLE)

**Requirement**: Different terminals MUST get different terminal_ids

**Verification**:
```python
# Test: Different env vars → different IDs
os.environ["CLAUDE_TERMINAL_ID"] = "terminal_a"
id_a = resolve_terminal_key({})

os.environ["CLAUDE_TERMINAL_ID"] = "terminal_b"
id_b = resolve_terminal_key({})

assert id_a != id_b  # ✅ SECURITY PROPERTY PRESERVED
```

**Why this matters**:
- Prevents cross-terminal bleeding of handoff state
- Ensures concurrent sessions don't interfere
- Critical for multi-terminal workflows

### PID Validation

**Purpose**: Prevent reuse of stale state files

**Rules**:
- Exact PID match → Same process, allow
- Parent PID match → Same terminal (process restart), allow
- No PID match → Different terminal/session, reject
- Missing timestamp → Reject (stale)

**Freshness**:
- State file <2 hours old → Accept
- State file >2 hours old → Reject (stale)

---

## Testing Commands

### Run All Terminal Detection Tests
```bash
pytest P:/.claude/hooks/tests/test_terminal_detection.py -v
```

### Run Hooks-Aware Tests Only
```bash
pytest P:/.claude/hooks/tests/test_terminal_detection.py::TestReadProjectStateHooksAware -v
```

### Run Cross-Terminal Isolation Tests Only
```bash
pytest P:/.claude/hooks/tests/test_terminal_detection.py::TestCrossTerminalIsolation -v
```

### Integration Test (Manual)
```bash
# 1. Set environment variable
export CLAUDE_TERMINAL_ID="test_terminal_123"

# 2. Run compaction
/compact

# 3. Check handoff file
cat P:/.claude/state/handoff/*_handoff.json | grep terminal_id

# Expected: "terminal_id": "env_test_terminal_123"
```

---

## File Locations

| Component | Path |
|-----------|------|
| Detection Module | `P:\.claude\hooks\terminal_detection.py` |
| Test Suite | `P:\.claude\hooks\tests\test_terminal_detection.py` |
| Handoff Storage | `P:\.claude\state\handoff\{terminal_id}_handoff.json` |
| State File | `P:\.claude\state\terminal_id.json` |
| Documentation | `P:\.claude\docs\handoff-system-fix-summary.md` |
| ADR | `P:\.claude\docs\adr-terminal-id-detection-20260309.md` |

---

## Key Design Decisions

### Why Hooks-Aware Directory Traversal?

**Problem**: `_read_project_state()` depended on `PROJECT_ROOT` environment variable that Claude Code doesn't set

**Solution**: Detect execution context and navigate appropriately
- `.claude/hooks/` → Navigate up 2 levels
- `.claude/` → Navigate to parent
- Other → Search upward for `.claude`

**Benefits**:
- ✅ No environment variable dependencies
- ✅ Works from any execution context
- ✅ Portable to other hook systems
- ✅ Self-contained implementation

### Why Fail-Fast Instead of Fallback?

**Problem**: Silent fallback to "unknown" degraded system security

**Solution**: Raise RuntimeError when all detection methods fail

**Benefits**:
- ✅ Fails loudly when broken
- ✅ Forces investigation of root cause
- ✅ Prevents silent security degradation
- ✅ Clear error message about what failed

### Why Environment Variable Priority?

**Problem**: Temp file fallback caused cross-session bleeding

**Solution**: Prioritize environment variables (process-scoped, inherited correctly)

**Priority Order**:
1. Environment variables (process-scoped, inherited)
2. Project state (PID validation prevents bleeding)
3. Temp file (48-hour age limit, last resort)
4. ConsoleHost handle (Windows-only isolation)

**Benefits**:
- ✅ Correct process isolation
- ✅ No cross-session contamination
- ✅ Fallback chain still exists for edge cases

---

## Performance Characteristics

| Operation | Time | Notes |
|-----------|------|-------|
| Environment variable lookup | <1ms | O(1) dictionary access |
| Project state read | 5-10ms | File I/O + JSON parsing |
| Temp file read | 5-10ms | File I/O + age validation |
| ConsoleHost handle | <1ms | Windows API call |
| Directory traversal | 1-5ms | Max 10 levels up |

**Overall**: <20ms for complete detection chain

---

## Common Debugging Scenarios

### Scenario 1: "Why did my handoff quality drop to 0.55?"

**Diagnosis**:
```bash
# Check terminal_id in handoff
cat P:/.claude/state/handoff/*_handoff.json | jq '.terminal_id'

# If "unknown" → detection failed
# If actual ID → different issue (no active task)
```

**Solution**:
- If "unknown" → Terminal detection broken (check environment variables)
- If actual ID but 0.55 → No active task (expected for /compact workflow)

### Scenario 2: "Why are tests failing with RuntimeError?"

**Diagnosis**:
```bash
# Check test expectations
grep -r "terminal_1" P:/.claude/hooks/tests/

# Old tests expect fallback behavior
```

**Solution**: Update tests to expect RuntimeError, not fallback

### Scenario 3: "Why did I get a different terminal_id?"

**Diagnosis**:
```bash
# Check environment variables
echo $CLAUDE_TERMINAL_ID

# Check project state file
cat P:/.claude/state/terminal_id.json

# Check temp file age
stat %TEMP%\claude_terminal_id.txt
```

**Solution**:
- Environment variable changed → New terminal ID (expected)
- State file stale (>2 hours) → Rejected, falls back to other methods
- Temp file stale (>48 hours) → Rejected, falls back to other methods

---

## Related Documentation

- **Handoff System Fix Summary**: `P:\.claude\docs\handoff-system-fix-summary.md`
- **Architectural Decision Record**: `P:\.claude\docs\adr-terminal-id-detection-20260309.md`
- **Implementation Plan**: `P:\.claude\hooks\plans\plan-handoff-refinements-20260308.md`
- **Terminal Detection Module**: `P:\.claude\hooks\terminal_detection.py`
