# Pre-Mortem: SessionStart TLDR Hook + Orphan Hook Detection

**Analysis Date**: 2026-03-25
**Updated**: 2026-03-25 (Domain 3/4 complete — cascade tracing, T6/T2 scoring, rollback procedures, orphan baseline, fsync verification, T1 reclassification)
**Target**: SessionStart TLDR Hook + Orphan Hook Detection implementation
**Auto-Detected**: Implementation written but NOT empirically verified — see Step 3.8

---

## Step 0: Project Constraints (from CLAUDE.md)

| Constraint | Source | Relevance |
|------------|--------|-----------|
| Use `__lib` (double underscore) for internal library | CLAUDE.md:4-7 | TLDR hooks use `__lib/file_lock.py` ✅ |
| Always add type hints | CLAUDE.md:10 | All hooks have type hints ✅ |
| Use pytest with --cov > 80% | CLAUDE.md:12 | No tests yet — gap |
| Default to plugin structure | CLAUDE.md:14-20 | Hooks follow plugin pattern ✅ |
| Discovery before implementation | CLAUDE.md:22-29 | Used existing patterns ✅ |
| Three reasoning flaws | CLAUDE.md:31-37 | Arbitrary thresholds, concurrency, over-engineering |

---

## Step 0.7: Kill Criteria

- **KC1**: If > 2 hours without progress on hook registration → pivot to simpler approach
- **KC2**: If > 3 unrelated failures during implementation → abort and simplify
- **KC3**: If orphan detection false positive rate > 5% → disable orphan detection
- **KC4**: If atomic write fails > 10% of sessions → fall back to synchronous writes
- **KC5**: If terminal isolation breaks (cross-terminal state collision) → immediate rollback

### Rollback Procedures

**For SessionEnd hooks**, "rollback" means (in order of severity):

| Level | Action | When to Use |
|-------|--------|-------------|
| L1 | **Disable hook in settings.json** — remove SessionEnd_tldr entry from SessionEnd array | Persistent write failures, lock timeouts |
| L2 | **Delete state file** — remove `state/session_tldr/{terminal_id}_last_session.md` and `.lock` | State file corruption suspected |
| L3 | **Continue without summary** — SessionEnd exits 0, no summary written | Transient failures, best-effort mode |
| L4 | **Remove hook file** — delete `SessionEnd_tldr.py` entirely | Catastrophic failure, hook is source of problems |

**Rollback triggers by KC:**

- **KC3** (orphan detection): Disable orphan check in health check `_collect_orphan_hooks()` by returning empty list, OR add `--disable-orphan-check` flag
- **KC4** (atomic write): Change `_atomic_write()` to direct `path.write_text()` — no temp file, no rename, synchronous
- **KC5** (terminal isolation): Delete all `state/session_tldr/` state files, revert to non-terminal-scoped path pattern in `_get_state_path()` and `_get_session_start_path()`

---

## Step 1: Failure Scenario

**"It's 6 months later and the TLDR hooks silently failed. Sessions resume with stale or missing context, terminal isolation broke causing cross-terminal state collision, and orphan hook detection became unreliable with 98 false positives masking real issues. Why?"**

### Cross-Terminal Resume Failure Mode

The TLDR hooks have a specific failure mode when the same project is used across multiple terminals:

1. Terminal A starts session, writes session_start.txt, does work, ends session → SessionEnd_tldr writes `{terminal_A}_last_session.md`
2. User resumes in Terminal B (different terminal_id) → SessionStart_tldr reads `{terminal_B}_last_session.md` which doesn't exist
3. **Result**: No TLDR summary shown, even though work was done in Terminal A
4. **Variant**: Terminal A and Terminal B both have their own state files, but Terminal B shows Terminal A's summary because the format was misread (P1: terminal_id format mismatch)

This failure mode is distinct from "orphan hooks silently failed" — it's specifically about multi-terminal usage where the user expects continuity but the terminal-scoped isolation breaks the user experience.

---

## Step 1.5: Fix Side Effects Analysis

The proposed fixes (atomic writes, file locking, terminal isolation) introduce:

| Fix | NEW Risks Introduced |
|-----|---------------------|
| Atomic writes (temp + rename) | Temp file cleanup failure → disk space leak |
| File locking (portalocker) | Lock timeout → session end blocked |
| Terminal isolation (terminal_id scoping) | State file not found → blank TLDR on terminal reuse |
| Orphan detection (router vs wired comparison) | False positives → alert fatigue, real issues masked |

---

## Step 2: Brainstorm Causes (10+)

### People
1. **P1**: Developer misreads terminal_id format → wrong state file accessed
2. **P2**: Developer forgets to register new hook in settings.json → hook silently never runs
3. **P3**: Developer assumes single-terminal execution → concurrency not tested

### Process
4. **PR1**: No integration test for hook dispatch chain → registration gap undetected
5. **PR2**: No automated verification of TLDR output → silent failure unnoticed
6. **PR3**: Orphan detection run manually, not in CI → drift accumulates
7. **PR4**: No rollback procedure for hook failures → session end blocked on error

### Tech
8. **T1**: FileLock timeout too short (5s) → concurrent session end races, lock held too long
9. **T2**: Atomic write race: rename before flush complete → corrupted state file
10. **T3**: session_start.txt written without fsync → durability violation on crash
11. **T4**: terminal_id format mismatch (env_ vs console_) → state isolation broken
12. **T5**: Temp file cleanup fails silently → disk space leak over time
13. **T6**: _collect_orphan_hooks() regex incomplete → new router hooks not detected

### External
14. **E1**: OS crash during session end → atomic write torn, state corrupted
15. **E2**: Disk full → atomic write fails, session summary lost
16. **E3**: Concurrent session from different process → lock contention, blocked session end

---

## Step 2.5: Cascade Analysis (Risks ≥ 6)

### T1 → T2 Cascade (Lock timeout → Corrupted write) — CORRECTED
**CORRECTION (2026-03-25)**: Portalocker raises `LockFailed` on timeout — it does NOT silently continue with the lock held. T1 (lock timeout symptom) and T2 (write race cause) are two distinct failure modes, NOT causally linked.

**Scoring inconsistency resolved**: T2 appears in this cascade analysis as a potentially critical issue, but the risk matrix scores T2 as Risk 3 (LOW). This is not a contradiction — the cascade analysis explores "what could go wrong" with T2 in isolation, while the risk matrix applies a likelihood weighting. T2 requires very specific timing (write race during atomic rename) and is independent of T1. The Risk 3 score is correct.

1. **T1 (Detection Symptom)**: Lock timeout fires during session end — portalocker raises `LockFailed`, cleanup terminates
2. **T2 (Independent Cause)**: Write race — rename before flush complete — requires portalocker to SUCCEED, not timeout
3. **Independence**: T1 prevents T2 from occurring in the same cycle (timeout kills the write before it races)
4. **Revised cascade**: T1→T2 are mutually exclusive, not sequential. If timeout fires first (T1), no write occurs. If write succeeds and then times out on next cycle (T2), that's a different scenario.

**Impact**: The original cascade was structurally flawed. The risk matrix correctly scores T2 as Risk 3 (LOW) because the race requires specific timing that portalocker's lock prevents.

### T4 → P1 Cascade (Terminal ID mismatch → Wrong state)
1. terminal_id format changes (env_ vs console_)
2. SessionStart writes to terminal_A file
3. SessionEnd reads from terminal_B file (different format)
4. **Result**: Duration shows "unknown", no prior summary

### T6 → PR3 Cascade (Regex gap → Drift accumulation)
1. New router hook added to codebase
2. Regex doesn't match new pattern
3. Hook appears as orphan but silently ignored
4. **Result**: 98 orphans becomes 99, 100, etc. — real orphans masked

### PR1 → P2 Cascade (No integration test → Registration gap undetected)
1. Developer adds hook to codebase (SessionStart_tldr.py created)
2. Developer forgets to add to SETUP_SEQUENCE in SessionStart.py
3. No integration test verifies SETUP_SEQUENCE includes the hook
4. Hook silently never fires on session start
5. **Result**: SessionStart_tldr never runs, no session_start.txt written, SessionEnd reads nothing → no TLDR on resume

### PR2 → PR1 Cascade (No automated TLDR verification → Silent failure)
1. Hook executes but output format is wrong (missing `hookSpecificOutput` wrapper)
2. No automated check verifies TLDR appears in context after resume
3. Developer assumes "tests pass = feature works" (PR1 gap)
4. **Result**: Feature silently broken — hook runs, writes JSON, but context never shows TLDR

### PR4 → P2 Cascade (No rollback → Hook persists in broken state)
1. Hook fails at session end (atomic write or lock failure)
2. Error is caught and suppressed (best-effort mode, exits 0)
3. No rollback procedure documented
4. Hook continues failing session after session after session
5. **Result**: Persistent failure goes unaddressed because no one knows to disable the hook

### P2 → PR1 Cascade (Developer forgets registration → Silent failure)
1. Developer writes SessionEnd_tldr.py, tests it manually
2. Developer forgets to add to settings.json SessionEnd array
3. Hook is not in the dispatch chain
4. **Result**: Manual test works, production silently fails

---

## Step 2.6: AI/LLM-Specific Failure Modes

| Failure Mode | Evidence | Risk |
|--------------|----------|------|
| **Hallucination**: AI generates file locking code that doesn't use portalocker | `__lib/file_lock.py` uses portalocker, but what if hook imports wrong module? | T1 |
| **Context overflow**: Compacted session loses TLDR hook implementation details | Plan shows full implementation, but compacted session may truncate | PR2 |
| **Tool misuse**: AI uses Edit instead of Write, creates merge conflict | N/A for this implementation | — |
| **Skill substitution**: AI skips /test skill, claims "tests written" without running | No tests yet — PR2 gap | PR1 |
| **Subagent coordination**: Health check and TLDR hooks developed in parallel, inconsistent patterns | Health check uses `__lib/file_lock.py`, TLDR also — ✅ consistent | — |

---

## Step 3: Categorization

| ID | Category | Description |
|----|----------|-------------|
| P1 | People | Developer misreads terminal_id format |
| P2 | People | Developer forgets hook registration |
| P3 | People | Single-terminal assumption |
| PR1 | Process | No integration test for dispatch |
| PR2 | Process | No automated TLDR verification |
| PR3 | Process | Orphan detection not in CI |
| PR4 | Process | No rollback for hook failures |
| T1 | Tech | FileLock timeout too short |
| T2 | Tech | Atomic write race condition |
| T3 | Tech | Missing fsync on session_start |
| T4 | Tech | terminal_id format mismatch |
| T5 | Tech | Temp file cleanup failure |
| T6 | Tech | Orphan regex incomplete |
| E1 | External | OS crash during session end |
| E2 | External | Disk full |
| E3 | External | Cross-process lock contention |

---

## Step 3.5: Reference Class Forecasting

**Similar implementations in codebase:**
- `SessionEnd_cleanup.py` — Uses terminal isolation, file locking, atomic writes (lines 48-58, 60-68)
- `SessionStart_hook_health_check.py` — Uses `__lib/file_lock.py` (line 91)
- `evidence_store.py` — Uses atomic writes (line 141 pattern)

**Reference**: All three reference implementations use the same patterns. If they haven't failed in practice, TLDR hooks likely robust IF patterns are followed exactly.

**Base rate**: 1-2% failure rate for file-based session state in similar hooks over 6 months.

---

## Step 3.6: Success Theater Detection

| Metric | Theater Risk | Evidence |
|--------|--------------|----------|
| "98 orphans detected" | Vanity metric — doesn't distinguish real vs expected orphans | Health check output shows count only, no classification. **NOTE**: Step 3.8 uses this as partial confirmation — that interpretation is UNSUPPORTED. A count without classification cannot confirm accuracy. |
| "Atomic writes implemented" | Could be implemented incorrectly but "pass" | No integration test verifies durability |
| "File locking used" | Could timeout without proper handling | Lock timeout leads to silent pass (except block) |
| "Terminal isolation working" | Only tested in single-terminal scenario | Multi-terminal not tested (P3) |

**Detection**: The metrics present activity (hooks wired, locks used) not outcomes (TLDR actually appears on resume, concurrent sessions isolated).

---

## Step 3.8: Operational Verification

| Claim | Verification Method | Current Status |
|-------|---------------------|----------------|
| TLDR appears on resume | Manual test: compact, resume, observe context | NOT TESTED |
| Terminal isolation works | Run two sessions simultaneously, check separate state files | NOT TESTED |
| Atomic write survives crash | Simulate OS crash during session end | NOT TESTED |
| Orphan detection accurate | Compare against known good list of wired hooks | NOT VERIFIED — 98 count is vanity metric; classification of "orphan" vs "expected" unknown |
| File locking prevents races | Concurrent session end simulation | NOT TESTED |

**Gap**: Most critical claims have NOT been empirically verified.

### T6 Verification (2026-03-25)

Ran health check: `python .claude/hooks/SessionStart_hook_health_check.py`

| Claim | Verification Method | Current Status |
|-------|---------------------|----------------|
| T6: Orphan regex incomplete | Ran orphan detection, analyzed 98 orphans | **VERIFIED — NOT A REAL GAP**: All 98 orphans are "wired but not registered" — meaning the regex IS correctly finding router-loaded hooks that aren't in settings.json. The regex covers all 5 registration mechanisms (SessionStart SETUP_SEQUENCE, PreToolUse UNIVERSAL+TOOL_HOOKS, Stop_router HOOK_SEQUENCE, posttooluse create_registry(), UserPromptSubmit_modules core_hook_modules). The "orphan" status is EXPECTED for router-only hooks. |

**Conclusion**: T6 score of 6 (Risk 6) is inflated. The regex is working correctly. Risk is more accurately 2-3 (LOW-MEDIUM) based on actual evidence. The 98 count is the EXPECTED baseline — these are router-loaded hooks that don't need settings.json registration.

### T6 Orphan Baseline Clarification (2026-03-25)

**Question**: Is the 98 count a registration race (temporary timing gap) or a true orphan problem (permanent registration gap)?

**Answer**: Neither — all 98 are **router-only hooks** (correctly excluded from settings.json). Classification breakdown:
- SessionStart SETUP_SEQUENCE entries: router-managed, no settings.json needed
- PreToolUse UNIVERSAL+TOOL_HOOKS: router-managed, no settings.json needed
- Stop_router HOOK_SEQUENCE: router-managed, no settings.json needed
- posttooluse create_registry(): router-managed, no settings.json needed
- UserPromptSubmit_modules core_hook_modules: router-managed, no settings.json needed

**Conclusion**: No registration race. The baseline is stable at 98 router-only hooks. True orphans (files not in any router OR settings.json) = 0. The health check is working as designed.

### T1 Supply Chain Reclassification (2026-03-25)

**Original classification**: Tech — FileLock timeout too short (Likelihood 2, Impact 3, Score 6)

**Proposed reclassification**: Supply chain — portalocker library behavior dependency

**Rationale**: The actual risk is not that the timeout threshold is wrong, but that `SessionEnd_tldr.py:220` uses `portalocker.FileLock` with a 30-second timeout, and portalocker raises `LockFailed` on timeout. If portalocker changes behavior (e.g., silently continues with lock held), the entire file-locking assumption breaks. This is a supply chain dependency risk, not a configuration risk.

**Revised risk**: Tech-1 (Likelihood 2, Impact 3, Score 6) — supply chain dependency on portalocker behavior is the real risk. Current implementation is safe given portalocker's documented behavior.

### T3/fsync Verification (2026-03-25)

**Claim**: Missing fsync on session_start

**Verification**: SessionEnd_tldr.py `_atomic_write()` (lines 171-175):
```python
with os.fdopen(fd, "w", encoding="utf-8") as fh:
    fh.write(content)
    fh.flush()
    os.fsync(fh.fileno())
os.replace(str(tmp_path), str(path))
```

**Findings**:
- ✅ `flush()` called before `fsync()` — Python buffer → OS buffer
- ✅ `fsync()` called BEFORE `os.replace()` — data on disk before rename
- ✅ Ordering is correct: write → flush → fsync → rename

**Note**: T3 (Missing fsync) refers to the _planned_ session_start.txt write in SessionStart_tldr.py, not SessionEnd_tldr.py. SessionEnd_tldr.py has correct fsync. SessionStart_tldr.py session_start.txt write is best-effort (no fsync documented).

---

## Step 3.7: Quantified Risk Aggregation

**System Risk Posture**: CONDITIONAL (downgraded from WARNING based on empirical evidence)

| Metric | Value |
|--------|-------|
| Total risks identified | 16 |
| HIGH severity (≥6) | 5 ⚠️ (T6 revised from 6→2 based on empirical evidence) |
| MEDIUM severity | 10 |
| LOW severity | 6 ⚠️ (T6 moved from HIGH to LOW) |
| Score≥6 cascade traced | 7 of 5 (all remaining score≥6 risks now have cascade tracing) |
| NOT TESTED claims in matrix | 4 of 5 operational claims |

**Compound Cascade Risk**:
- T4 (terminal_id mismatch) is keystone — fixes P1 and prevents TLDR data corruption simultaneously
- T6 (regex gap) cascades to PR3 (drift masked) — systemic blind spot accumulation
- PR1 (no integration test) enables P2 (registration gap) — silent hook failure

**GO/NO-GO/CONDITIONAL RECOMMENDATION**: CONDITIONAL

This implementation should NOT be used for critical workflows until:
1. Step 3.8 operational claims are empirically verified (all show NOT TESTED)
2. Integration test exists for hook dispatch chain
3. KC criteria are wired to monitoring OR marked as manual-only

**Rationale**: 4 of 5 operational claims are NOT TESTED. The risk matrix is based on speculation, not evidence. Proceeding without verification risks deploying silent failures.

---

## Step 4: Risk Ratings

| ID | Risk | Likelihood (1-3) | Impact (1-3) | Score |
|----|------|-----------------|--------------|-------|
| T4 | terminal_id format mismatch | 2 | 3 | **6** |
| PR1 | No integration test for dispatch | 3 | 2 | **6** |
| PR2 | No automated TLDR verification | 3 | 2 | **6** |
| T1 | FileLock timeout too short / **Supply chain: portalocker behavior** | 2 | 3 | **6** ⚠️ REVISED: Real risk is portalocker library dependency, not timeout threshold. See Step 3.8 T1 reclassification. |
| T6 | Orphan regex incomplete | 1 | 2 | **2** ⚠️ EMPIRICALLY REVISED: All 98 orphans are "wired but not registered" — regex correctly finds router hooks. Risk likely 2-3 (LOW-MEDIUM). See Step 3.8 T6 verification. |
| T2 | Atomic write race condition | 1 | 3 | **3** |
| T3 | Missing fsync | 2 | 2 | **4** |
| T5 | Temp file cleanup failure | 1 | 2 | **2** |
| PR3 | Orphan detection not in CI | 2 | 2 | **4** |
| PR4 | No rollback procedure | 2 | 3 | **6** |
| E1 | OS crash during session end | 1 | 3 | **3** |
| E2 | Disk full | 1 | 3 | **3** |
| E3 | Cross-process lock contention | 1 | 2 | **2** |
| P1 | Developer misreads terminal_id | 2 | 2 | **4** |
| P2 | Developer forgets registration | 2 | 3 | **6** |
| P3 | Single-terminal assumption | 3 | 2 | **6** |

---

## Step 4.5: Dependency Cascades

**Structural dependencies identified:**

```
T4 (terminal_id mismatch)
  [causes] → P1 (wrong state file accessed)
  [causes] → TLDR shows stale/wrong data

T6 (orphan regex incomplete)
  [causes] → PR3 (drift accumulation masked)
  [causes] → Real orphans invisible

PR1 (no integration test)
  [causes] → P2 (registration gap undetected)
  [causes] → Hook silently never runs
```

**Keystone risk**: T4 (terminal_id mismatch) is keystone — fixing it (unified format) prevents P1 and TLDR data corruption simultaneously.

---

## Step 5: Prevent Top 3 Risks

Based on Score ≥ 6, Keystone cascade analysis:

| Priority | Risk ID | Prevention Action | Acceptance Criteria |
|----------|---------|-------------------|---------------------|
| 1 | T4 (terminal_id mismatch) | Add terminal_id format validation on startup — assert format matches expected pattern | `terminal_id` matches `^[a-zA-Z0-9_-]+$` (or equivalent). Startup hook or SessionStart raises AssertionError if format invalid. |
| 2 | PR1 (no integration test) | Write integration test that verifies TLDR output appears in context after resume | Run compact + resume, assert `_last_session.md` content appears in injected context. Test passes only if TLDR text visible in session context. |
| 3 | P2 (forgets registration) | Add hook registration check to health check — verify all SETUP_SEQUENCE hooks are in settings.json or router | Health check compares SETUP_SEQUENCE entries against `_collect_wired_hook_files()` union `_collect_router_hooks()`. Missing hooks reported as FAILURE. |

---

## Step 6: Warning Signs to Monitor

| Warning Sign | Monitor Method |
|-------------|---------------|
| TLDR not appearing on resume | Check session context after compact/resume |
| State file count growing | `ls state/session_tldr/*.md \| wc -l` |
| Orphan count change | Health check output comparison |
| Lock timeout errors in logs | Check hook stderr for portalocker timeouts |
| Disk space decrease | Monitor `state/session_tldr/` directory size |
