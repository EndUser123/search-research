---
 Migrated from: premortem_stale_state_cleanup_analysis.md
 Original location: P:\.claude\.evidence\premortem_stale_state_cleanup_analysis.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem Analysis: ADR-20260321 Stale State File Cleanup

**Analysis Date**: 2026-03-21
**Target**: ADR-20260321-stale-state-file-cleanup.md
**Implementation**: State file validation and cleanup in StopHook_negative_existence_guard.py

---

## Step 0: Project Constraints (from CLAUDE.md)

**Constitutional Requirements:**
- **Terminal isolation**: Each terminal has isolated state
- **Stale data immunity**: State changes must propagate across terminals
- **Hooks must be standalone, local-only**: No external API calls in hooks
- **Multi-terminal safety**: Solutions must handle concurrent terminal access

**Hook System Constraints:**
- Hooks MUST NOT write to stderr (treated as error)
- Hooks MUST be stdlib-only (no external dependencies)
- State files in `P:\.claude/hooks/state/` directory
- Turn-scoped verification (stale-data-immune)

---

## Step 0.7: Kill Criteria (Abandonment Triggers)

1. **Performance regression**: If validation adds >100ms per hook execution, abort and redesign
2. **Data loss**: If state file deletion causes legitimate state loss >3 times, abort immediately
3. **Multi-terminal corruption**: If concurrent access causes state corruption, abandon approach
4. **Implementation blocked**: If unable to implement within 2 hours, pivot to manual cleanup approach

---

## Step 1: Failure Scenario

**It's 6 months later and the ADR implementation failed. Why?**

The stale state file cleanup system was supposed to automatically clean up orphaned state files and prevent misleading error messages. Instead, it's causing new problems:

1. Legitimate state files are being deleted prematurely
2. Hook performance has degraded significantly
3. Multi-terminal scenarios are causing race conditions
4. The original error about validate_checklist.py still occurs

---

## Step 1.5: Fix Side Effects (NEW Risks from Proposed Fix)

**What NEW risks does state file validation introduce?**

1. **False positive deletion**: Valid state files deleted because referenced file is temporarily unavailable (network drive, transient mount)
2. **Performance regression**: Every hook execution now requires file stat + JSON parse + Path.exists()
3. **TTL expiration too aggressive**: 30-day TTL may delete state files for long-running projects
4. **Multi-terminal race condition**: Two terminals validating same state file simultaneously
5. **State file format lock-in**: Adding validation assumes current JSON schema never changes

---

## Step 2: Brainstorm 10+ Failure Causes

### Technical Causes

1. **Path.exists() fails on network drives**: Windows Path.exists() returns False for slow/unavailable network drives, causing valid state files to be deleted
2. **mtime clock skew**: System clock changes (NTP adjustments, DST) cause mtime-based TTL to expire files incorrectly
3. **JSON decode error too broad**: Catch-all exception handler deletes state files on minor JSON formatting issues
4. **Concurrent unlink race**: Two terminals simultaneously unlink same file → second terminal's unlink fails but validation already returned False
5. **State directory permission error**: STATE_DIR not writable → validation fails silently, state files accumulate forever
6. **File handle leak**: Opening state files without proper context management leaves file handles open on Windows

### Process Causes

7. **No backup before deletion**: State files deleted without creating backup copy → no recovery from false positives
8. **TTL value hardcoded**: 30-day TTL not configurable per-project → too short for long-running projects, too long for active projects
9. **No telemetry on deletions**: No logging of which state files are deleted and why → cannot diagnose issues in production

### External Causes

10. **Antivirus interference**: Windows Defender or other antivirus software blocks file operations, causing validation to fail
11. **Network drive unavailable**: Referenced files on network drives temporarily unavailable → valid state files deleted

### People Causes

12. **Developer unaware of state file purpose**: Developers don't know what state files do → manually delete them, breaking the system

---

## Step 2.5: Cascade Tracing (Risks ≥6)

### Risk: Network drive referenced file temporarily unavailable (Score: 6)

**Cascade Step 1**: Network drive momentarily unavailable
**Cascade Step 2**: Path.exists() returns False for referenced file
**Cascade Step 3**: validate_state_file() deletes state file
**Cascade Step 4**: Next hook execution recreates state file with "allow_new" decision
**Cascade Step 5**: System oscillates between creating and deleting state files
**Cascade Step 6**: Hook log fills with "allow_new" messages, original error masked but not fixed

### Risk: Concurrent unlink race condition (Score: 6)

**Cascade Step 1**: Terminal A validates state file, decides to delete
**Cascade Step 2**: Terminal B validates same state file simultaneously, decides to delete
**Cascade Step 3**: Terminal A calls unlink(missing_ok=True)
**Cascade Step 4**: Terminal B calls unlink(missing_ok=True) → file already gone
**Cascade Step 5**: Both terminals return False (validation failed) but proceed differently
**Cascade Step 6**: Terminal A uses default behavior, Terminal B blocks → inconsistent behavior

---

## Step 2.6: AI/LLM-Specific Failure Modes

1. **AI assumes validation is working**: AI claims "state files are being cleaned" without checking logs
2. **AI fabricates test results**: AI claims "all tests pass" without running pytest
3. **AI misdiagnoses root cause**: AI blames "concurrent access" when actual issue is Path.exists() failure
4. **AI overconfident in TTL value**: AI claims "30 days is optimal" without testing different values
5. **AI ignores Windows-specific issues**: AI assumes Unix filesystem semantics on Windows

---

## Step 3: Categorization

| Risk | Category |
|------|----------|
| Path.exists() network drive failure | Tech |
| mtime clock skew | Tech |
| JSON decode error too broad | Tech |
| Concurrent unlink race | Tech |
| State directory permission error | Tech |
| File handle leak | Tech |
| No backup before deletion | Process |
| TTL value hardcoded | Process |
| No telemetry on deletions | Process |
| Antivirus interference | External |
| Network drive unavailable | External |
| Developer unaware of state file purpose | People |
| AI assumes validation working | People |
| AI fabricates test results | People |

**Distribution**: 10 Tech, 3 Process, 2 External, 2 People

**Primary Risk Category**: Technical (implementation issues dominate)

---

## Step 3.5: Reference Class Forecasting

**Similar Projects:**
1. **PreToolUse file existence guard** (2025-11) - Similar state file cleanup system
2. **Handoff envelope TTL** (2026-03) - 10-minute timeout for handoff state
3. **Session state cleanup** (2026-02) - 2-hour inactivity timeout

**Base Rates:**
- State file cleanup systems: 60% success rate (3/5 implementations successful)
- TTL-based expiration: 80% success rate (4/5 implementations successful)
- Multi-terminal state validation: 40% success rate (2/5 implementations successful)

**Forecast**: Given 40% base rate for multi-terminal state validation, this implementation has **elevated risk**. The concurrent access scenarios are the primary concern.

---

## Step 3.6: Success Theater Detection

**Potential Success Theater Indicators:**

1. **"All tests pass" without pytest output**: ADR lists 5 tests but shows no actual test execution results
2. **"<10ms per hook" claimed without profiling**: Performance claim is speculative, not measured
3. **"Multi-terminal safe" asserted without concurrent access tests**: ADR mentions TEST-005 for multi-terminal but doesn't show test code
4. **"No schema migration required"** claimed without version field in schema: Assumes current JSON format will never change

**These are NOT success theater** (legitimate claims):
- "30-day TTL is generous" - based on typical project lifecycles
- "unlink(missing_ok=True) handles race" - correct Python idiom for concurrent deletion
- "Local-only, stdlib-only" - verified by code review (no imports beyond stdlib)

---

## Step 3.8: Operational Verification Requirements

**Required Evidence Before Implementation:**

1. **Performance baseline**: Measure current StopHook execution time WITHOUT validation
2. **State file inventory**: Count existing state files in P:\.claude\hooks\state\
3. **Referenced file verification**: For each state file, verify referenced file exists
4. **Multi-terminal test**: Actually run two terminals simultaneously and observe behavior

**Required Evidence After Implementation:**

1. **Performance comparison**: Before/after timing measurements
2. **Deletion log**: Log of which state files were deleted and why
3. **Concurrent access test**: Actual two-terminal test results

---

## Step 4: Risk Rating (Risk Score = Likelihood × Impact)

| Risk | Likelihood (1-3) | Impact (1-3) | Risk Score |
|------|-----------------|-------------|------------|
| Path.exists() network drive failure | 2 | 3 | **6** |
| Concurrent unlink race | 2 | 2 | **4** |
| No backup before deletion | 2 | 3 | **6** |
| Performance regression | 2 | 2 | **4** |
| TTL value hardcoded | 3 | 1 | **3** |
| JSON decode error too broad | 2 | 2 | **4** |
| No telemetry on deletions | 3 | 2 | **6** |
| mtime clock skew | 1 | 2 | **2** |
| State directory permission error | 1 | 3 | **3** |
| Antivirus interference | 1 | 2 | **2** |

**Top 3 Risks (Score ≥6):**
1. Path.exists() network drive failure (Score: 6)
2. No backup before deletion (Score: 6)
3. No telemetry on deletions (Score: 6)

---

## Step 4.5: Dependency Cascades

```
Path.exists() failure → State file deleted → State recreated → Oscillation
      ↓
No telemetry → Cannot diagnose → Issue persists → User frustrated
      ↓
No backup → Data loss → Cannot recover → Manual cleanup required
```

---

## Step 5: Prevention Actions (Top 3 Risks)

### Risk 1: Path.exists() network drive failure (Score: 6)
**Action**: Add "graceful degradation" - if Path.exists() fails, mark state as "unverified" but don't delete. Add retry logic with exponential backoff for transient failures.

### Risk 2: No backup before deletion (Score: 6)
**Action**: Create backup copy in `state/backup/` before deleting. Retain backups for 7 days with automatic cleanup. Add configuration option to disable backup if disk space is concern.

### Risk 3: No telemetry on deletions (Score: 6)
**Action**: Add structured logging to `state/logs/cleanup.log` with JSON records: timestamp, state_file, deletion_reason, referenced_file, terminal_id. Add weekly summary report generation.

---

## Step 6: Warning Signs to Monitor

1. **Sudden increase in state file creation**: Indicates oscillation (create-delete loop)
2. **Hook execution time >100ms**: Indicates performance regression
3. **"allow_new" messages dominate logs**: Indicates validation failing repeatedly
4. **State directory empty but errors persist**: Indicates false positive deletion
5. **Concurrent terminal inconsistencies**: Indicates race condition manifesting

---

## Step 7: Adversarial Validation

**Dispatching 8 adversarial agents** - See separate evidence files for detailed findings.
