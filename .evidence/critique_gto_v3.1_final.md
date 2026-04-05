# Adversarial Critique: GTO v3.1 Self-Verifying Infrastructure

**Status:** Complete - Three-Phase Adversarial Review

---

## Health Score: 54%

The GTO v3.1 self-verifying infrastructure has significant architectural flaws that undermine its core promise. While the implementation is well-structured and follows good patterns (atomic writes, terminal isolation), critical verification loopholes and platform compatibility issues prevent reliable operation.

---

## 🔴 Critical Failures (Must Fix)

### 1. A3 "Implicit Pass" Defeats Viability Gate
**Location:** `gto-assertions.py:104`
**Severity:** CRITICAL

When viability files don't exist, A3 returns `True` with "implicit pass." This creates a verification bypass:
- Viability gate fails but doesn't create a file
- A3 sees no file → returns True (implicit pass)
- Assertions pass (5/5) → User claims "done"
- **BUT:** Viability check actually failed

**Fix:** A3 should FAIL when viability files are missing, not pass implicitly.

### 2. Stop Hook Fires on Every Session Exit
**Location:** `SKILL.md:18-21`
**Severity:** CRITICAL

The Stop hook has no scoping mechanism — it runs `gto_verify.sh` on **every** session exit, not just GTO sessions. This means:
- Working on unrelated tasks (editing config, running different skills) triggers GTO verification
- Assertions fail because no GTO artifacts exist
- User cannot exit session without running GTO first

**Fix:** Add conditional logic to skip verification when GTO wasn't invoked, or move verification to GTO's completion checkpoint.

### 3. Terminal ID "default" Breaks Multi-Terminal Isolation
**Location:** `gto_verify.sh:11`
**Severity:** CRITICAL

```bash
TERMINAL_ID="${TERMINAL_ID:-default}"
```

If TERMINAL_ID is unset, the hook uses "default" as fallback:
- Multiple terminals without TERMINAL_ID all use "default"
- All write to `.evidence/gto-state-default/`
- **Race condition:** Concurrent writes corrupt state
- **False positives:** Terminal A sees Terminal B's artifacts

**Fix:** Fail fast if TERMINAL_ID is unset — don't silently use "default."

---

## 🟠 High-Risk Issues

### 4. Stale Artifacts Cause False Positives
**Location:** `gto-assertions.py:60`
**Severity:** HIGH

A1 checks for artifacts modified in "last hour" (arbitrary threshold):
- User runs `/gto` at 2:00 PM → Creates artifacts
- User changes codebase
- At 2:45 PM, user claims "done" without re-running GTO
- Assertions pass (A1 sees artifacts from 2:00 PM)
- **BUT:** Codebase changed, artifacts are stale

**Fix:** Tie A1 to session lifecycle — check for artifacts created **after session started**, not "in last hour."

### 5. Windows Platform Incompatibility
**Location:** `gto_verify.sh:1`
**Severity:** HIGH

The Stop hook is a bash script (`.sh`) which assumes bash is available:
- Windows 11 uses PowerShell by default
- Bash available via WSL or Git Bash, but not guaranteed
- No fallback to PowerShell or `.bat` script
- Stop hook may fail silently or not run at all

**Fix:** Detect shell availability and provide Windows-native alternative.

### 6. No JSON Error Handling in Failure Capture
**Location:** `gto_failure_capture.py:121`
**Severity:** HIGH

```python
input_data = json.load(sys.stdin)
```

No try/except around JSON parsing. If stdin is malformed JSON, the entire hook crashes and logs nothing.

**Fix:** Wrap in try/except, return valid JSON even on parse failure.

---

## 🟡 Medium-Risk Issues

### 7. Hook Registration Mismatch
**Location:** `SKILL.md:13-17`
**Severity:** MEDIUM

PostToolUseFailure hook uses `matcher: "Bash"`:
- Only Bash command failures trigger classification
- If GTO is invoked via different mechanism (Python API, direct import), failures are NOT classified
- Hook has no filter for "gto" commands — classifies ANY Bash failure

The Python code filters with `if "gto" not in command.lower():` but this is fragile and bypassable.

### 8. State Directory Structure Assumption
**Location:** `gto-assertions.py:149`
**Severity:** MEDIUM

Code assumes `.evidence` directory exists within project root:
- If project_root is `P:\packages\handoff`, there may be NO `.evidence` directory there
- Code doesn't create directory if missing
- A5 checks existence but doesn't create

### 9. No Integration Tests
**Severity:** MEDIUM

Unit tests exist (`tests/test_lib.py`, `tests/test_orchestrator.py`) but no integration tests for:
- Complete hook → assertions → block flow
- GTO run → artifacts → assertions → pass
- Failure capture → classification → logging

### 10. Unbounded Log Accumulation
**Location:** `gto_failure_capture.py:92-115`
**Severity:** MEDIUM

Failure logs accumulate in `.claude/failure-patterns/` with no cleanup:
- No rotation, no size limits, no expiration
- Long-running sessions accumulate thousands of stale files

---

## 🔵 Low-Risk Issues

### 11. Health Score Extraction Fragility
**Location:** `gto-assertions.py:72-78`
**Severity:** LOW

A2 looks for lines containing "%" AND ("score" OR "health" in lowercase):
- Requires exact keyword co-occurrence
- "Health: 85%" (missing "score") or "Percentage: 75%" (missing "health") fails despite valid data

### 12. No Assertion State Caching
**Severity:** LOW

Each run re-scans all files and re-parses content. For large projects with many artifacts, this is wasteful.

### 13. Arbitrary Time Window
**Location:** `gto-assertions.py:60`
**Severity:** LOW

1-hour window for "recent" artifacts is arbitrary with no justification. Why 1 hour and not 30 minutes or 4 hours?

---

## 🟢 Concrete Recommendations

### Priority 1 (Fix Verification Loopholes)

1. **Fix A3 "Implicit Pass"**
   ```python
   # gto-assertions.py:104
   # OLD: return True, "No viability failures detected (implicit pass)"
   # NEW:
   return False, "No viability file found. Cannot verify completion."
   ```

2. **Scope Stop Hook or Remove**
   - Option A: Add conditional to skip when GTO not invoked
   - Option B: Move verification to GTO's completion checkpoint

3. **Validate TERMINAL_ID**
   ```bash
   # gto_verify.sh:11
   if [ -z "$TERMINAL_ID" ]; then
       echo "{\"decision\": \"block\", \"reason\": \"TERMINAL_ID not set\"}"
       exit 2
   fi
   ```

### Priority 2 (Fix Platform & Artifacts)

4. **Add PowerShell Fallback**
   - Detect shell availability
   - Provide `.ps1` equivalent for Windows

5. **Tie A1 to Session Lifecycle**
   ```python
   # Check artifacts created AFTER session start
   # Not "in last hour"
   def check_artifacts_exist(state_dir: Path, session_start: datetime):
       mtime = datetime.fromtimestamp(match.stat().st_mtime)
       if mtime > session_start:
           recent_files.append(match.name)
   ```

6. **Add JSON Error Handling**
   ```python
   # gto_failure_capture.py:121
   try:
       input_data = json.load(sys.stdin)
   except json.JSONDecodeError as e:
       print(json.dumps({"additionalContext": f"Parse error: {e}"}))
       return 0
   ```

### Priority 3 (Add Missing Validation)

7. **Create Integration Test**
   - Mock GTO run → create artifacts
   - Run assertions → verify exit 0
   - Delete artifact → verify exit 1
   - Test Stop hook block/pass

8. **Add Log Cleanup**
   ```python
   def cleanup_old_logs(patterns_dir: Path, max_entries: int = 100):
       logs = sorted(patterns_dir.glob("*.json"), key=lambda p: p.stat().st_mtime)
       for old_log in logs[:-max_entries]:
           old_log.unlink()
   ```

---

## ❓ Open Questions

1. **Why Use Stop Hook Instead of GTO Completion Check?**
   - Stop hooks fire on every session exit
   - Why not add verification to GTO's own completion logic?

2. **What Is the Expected Hook Input Format?**
   - `gto_failure_capture.py` assumes specific keys (`command`, `error`, `tool`)
   - No schema reference or documentation

3. **How Should Terminal ID Collision Be Detected?**
   - Legitimate collisions when terminal restarts and reuses PID
   - Should we add PID or timestamp to state directory?

4. **Should Assertions Verify Git Repository Health?**
   - A4 only checks `.git` existence
   - Should it verify `git status` is clean?

5. **What Happens When GTO Runs on Non-Git Directory?**
   - A4 fails but error message doesn't explain WHY or how to fix

---

## Summary

The GTO v3.1 self-verifying infrastructure is well-intentioned but has critical flaws:

**What Works:**
- Binary assertions framework is solid
- Terminal isolation design is correct
- Failure classification is useful
- Atomic writes prevent corruption

**What's Broken:**
- A3 "implicit pass" defeats viability gate
- Stop hook fires on every session (wrong enforcement point)
- TERMINAL_ID "default" breaks multi-terminal isolation
- Stale artifacts cause false positives
- Windows platform not supported

**Recommended Action:**
Fix the 3 CRITICAL issues before deploying. The current implementation provides a false sense of security — users can claim "done" without actually completing GTO analysis.

---

**Evidence Tier:** Tier 1 (direct code analysis)
**Confidence:** 95% (based on actual implementation, not speculation)
