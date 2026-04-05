# Pre-Mortem: AP3 (Band-Aid Chain) + AP5 (Filesystem Freshness Validator)

**Target**: `StopHook_rca_contract.py` — RCA anti-pattern detectors for AP3 and AP5
**Date**: 2026-04-04
**Analysis**: Bruce Thomson

## Step 3.8: Verified Critical/High Findings

### CRIT-001 | Silent `_save_band_aid_state` failure (RISK-5)
**Severity**: HIGH
**Likelihood**: 40% | **Confidence**: 75%
**Governing principle**: Fail-open on error — but silent data loss is worse than failure
**Evidence**: `StopHook_rca_contract.py:425` — `except Exception: pass` (no logging, no retry)
**Cascade**: `_save_band_aid_state` fails silently → band-aid state not persisted → next RCA turn resets count → AP3 never triggers → RCA continues patching same file → symptom-patch loop
**Cascade probability**: "sure" (>70%)

### CRIT-002 | `_get_file_mtime` silently returns None for all errors (RISK-4)
**Severity**: HIGH
**Likelihood**: 30% | **Confidence**: 70%
**Governing principle**: Caller cannot distinguish "file not found" from "permission denied"
**Evidence**: `StopHook_rca_contract.py:504-505` — bare `except Exception: pass`
**Cascade**: Returns None → `_check_stale_execution_path` skips file → no block → stale execution path allowed through → wrong root cause → wasted investigation
**Cascade probability**: "sure"

### RISK-7 | `session_start_ts` may not be populated in `data` dict
**Severity**: HIGH
**Likelihood**: 50% | **Confidence**: 80%
**Governing principle**: Contract — data dict must supply required fields
**Evidence**: `StopHook_rca_contract.py:888` — `data.get("session_start_ts", None)`
**Cascade**: AP5 permanently fail-open → AP5 non-functional → stale path undetected
**Cascade probability**: "maybe" (30-70%) — depends on Stop_router populating the field

## Medium Risk Findings

### RISK-1 | TTL clock-jump vulnerability
**Severity**: MEDIUM
**Governing principle**: TTL safety uses wall-clock time
**Evidence**: `StopHook_rca_contract.py:402` — `time.time() - data.get("_ts", 0) > BAND_AID_STATE_TTL`
**Issue**: NTP sync or system sleep can cause clock to jump forward, invalidating TTL prematurely or extending it indefinitely

### RISK-2 | Block messages use raw f-strings not BLOCK_REASONS template
**Severity**: LOW-MEDIUM
**Governing principle**: DRY — template defined but not used
**Evidence**: `StopHook_rca_contract.py:147-151` vs `StopHook_rca_contract.py:537`
**Issue**: BLOCK_REASONS["stale-execution-path"] is a template with `{file}` placeholder but `_check_stale_execution_path` returns a raw f-string that bypasses the template. Works but inconsistent with band-aid-chain pattern (which correctly uses `.format()`).

### RISK-3 | `_extract_fix_files` regex matches `.py` substrings
**Severity**: LOW-MEDIUM
**Governing principle**: Precision — pattern should match whole file extensions
**Evidence**: `StopHook_rca_contract.py:436` — `[\w./\\-]+\.py\b` can match `foo.py.bak` or `test.py.bak`
**Issue**: Low risk since `.bak` files rarely appear in RCA Fix sections

### RISK-6 | TTL=3600 means band-aid chains survive across work sessions
**Severity**: LOW
**Governing principle**: User understanding — state persists longer than expected
**Evidence**: `StopHook_rca_contract.py:386`
**Issue**: Morning session band-aid state may persist into afternoon session if TTL=3600 and user was active within the hour

## Blocking Steps

### BLOCKING BEFORE IMPLEMENTATION

**RISK-5 → CRIT-001** - Silent band-aid state loss
- **Type**: ROOT-CAUSE FIX
- **Owner**: `/code`
- **Blocking**: yes
- **Survives compaction**: yes
- **Why**: Silent failure means AP3 is unreliable — when state doesn't persist, the detector provides false confidence
- **Prevention action**: In `_save_band_aid_state`, replace `except Exception: pass` with logging to hook diagnostics and returning False. In `_check_band_aid_chain`, check save failure and warn.
- **Proof action**: Write test that monkeypatches `_save_band_aid_state` to fail, verify warning is logged and AP3 degrades gracefully

**RISK-4 → CRIT-002** - Silent mtime lookup failure
- **Type**: ROOT-CAUSE FIX
- **Owner**: `/code`
- **Blocking**: yes
- **Survives compaction**: yes
- **Why**: Silent None return makes AP5 unreliable — cannot distinguish "no stale files" from "couldn't check"
- **Prevention action**: In `_get_file_mtime`, log individual failures (permission denied, not found, etc.) with file path. Return a sentinel that distinguishes "error" from "not found".
- **Proof action**: Write test that monkeypatches `Path.stat` to raise OSError, verify failure is logged and AP5 returns distinguishable error result

**RISK-7 → CRIT-003** - AP5 permanently fail-open
- **Type**: ROOT-CAUSE FIX
- **Owner**: `/verify --contracts`
- **Blocking**: yes
- **Survives compaction**: yes
- **Why**: If `session_start_ts` is never populated, AP5 never works
- **Prevention action**: Verify Stop_router actually passes `session_start_ts` in the data dict for RCA turns. Add debug logging in `check()` when rca_timestamp is None.
- **Proof action**: Add integration test: call `check()` with and without `session_start_ts`, verify AP5 fires only when timestamp present
