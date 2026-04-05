# Phase 1 Findings: Hook Optimization Recommendations

**Session**: critique-20260331_075801
**Date**: 2026-03-31
**Specialists**: adversarial-performance, adversarial-security, adversarial-io-validation

## Consolidated Findings

### 1. Lazy Regex Initialization

| Dimension | Finding |
|-----------|---------|
| **Severity** | CRITICAL |
| **Status** | CONFIRMED — 605 re.compile() at import time, ~3s startup |
| **Analyst** | adversarial-performance |

**Evidence**: 605 regex compilations across 121 files, module-level `_PATTERN = re.compile(...)`.

**TOCTOU**: None (regex is stateless), but eager compilation is itself the performance liability.

**Cross-validation**:
- adversarial-security agrees (SEC-002 LOW): module-level regex "not strictly security" but violates lazy init principle
- adversarial-io-validation: N/A — no code to analyze at recommendation level

**Recommendation**: Use `@cached_property` or class-based lazy compilation. Expected savings: 3s → <10ms.

---

### 2. Hard Timeout 200ms Budget

| Dimension | Finding |
|-----------|---------|
| **Severity** | HIGH |
| **Status** | NOT IMPLEMENTED — no timeout enforcement in hook_base.py |
| **Analyst** | adversarial-performance, adversarial-security |

**Evidence**:
- `hook_base.py` has no timeout mechanism (lines 67-71: plain wrapper, no signal/alarm/thread)
- Found timeouts: 0.5s FileLock, 30s SQLite — no 200ms enforcement anywhere
- Cascading failure: transcript JSONL parsing (10MB+) can block Stop hook for 2+ seconds

**Cross-validation**:
- adversarial-security (SEC-003 LOW): Confirms no 200ms budget exists
- adversarial-io-validation: N/A

**TOCTOU**: `StopHook_skill_execution_gate.py:300` — `transcript_path` read without FileNotFoundError guard.

**Recommendation**: Add 200ms hard cap at `hook_base.py` hook_main decorator. Also add try/except around transcript file reads.

---

### 3. Matcher Filters in settings.json

| Dimension | Finding |
|-----------|---------|
| **Severity** | MEDIUM |
| **Status** | PARTIAL — filters exist but post-import |
| **Analyst** | adversarial-performance |

**Gap**: Hooks are imported even when their matcher won't match. Filter is evaluated AFTER import, not before.

**Recommendation**: Add pre-import matcher filter in settings.json so non-matching hooks are never loaded.

---

### 4. SQLite WAL for Handoff State

| Dimension | Finding |
|-----------|---------|
| **Severity** | HIGH (security), INFO (performance) |
| **Status** | ALREADY IMPLEMENTED in evidence_store.py |
| **Analyst** | adversarial-security, adversarial-performance |

**Cross-validation**:
- adversarial-security (SEC-005 INFO): WAL already implemented at `evidence_store.py:64-68` with graceful fallback. **No action needed.**
- adversarial-performance: Claims "NOT VERIFIED" — pero confiesa uncertainty ("not verified in examined code")

**CRITICAL divergence**: adversarial-security found evidence_store.py uses JSONL NOT SQLite for skill_execution_gate state:
```
STATE_DIR = Path("P:/.claude/state")
LOG_FILE = Path("P:/.claude/logs/skill_execution_gate.jsonl")
```
But also found evidence_store.py (used by evidence spool) uses SQLite WAL. Two different systems with different stores.

**Remaining issue**: JSONL state files (skill_execution_gate.jsonl) are NOT using SQLite WAL. Concurrent terminal writes can corrupt JSONL.

**SEC-001 HIGH**: FileLock exception handling bug in `_write_spool_event()` — `except Exception: pass` falls through to unprotected temp file write. Not just TimeoutError. Data corruption risk in multi-terminal.

**Recommendation**:
1. WAL already done for evidence_store — no action
2. Fix SEC-001: restrict exception fallback to TimeoutError only
3. Migrate JSONL state files to SQLite WAL

---

### 5. QueueHandler for Hook I/O

| Dimension | Finding |
|-----------|---------|
| **Severity** | LOW |
| **Status** | NOT IMPLEMENTED — 0 QueueHandler references found |
| **Analyst** | adversarial-performance, adversarial-security |

**Evidence**: Grep for QueueHandler returns 0 matches across entire hooks/ directory.

**Cross-validation**: Both analysts agree — not implemented.

**Recommendation**: Consider async queue for high-throughput scenarios. Lower priority than items 1-3.

---

## Priority Matrix

| # | Recommendation | Severity | Status | Actionable |
|---|---------------|----------|--------|------------|
| 1 | Lazy regex init | CRITICAL | Confirmed | YES |
| 2 | Hard timeout 200ms | HIGH | Not implemented | YES |
| 3 | Matcher pre-filter | MEDIUM | Partial | YES |
| 4 | SQLite WAL | HIGH (JSONL) | Partially done | YES (JSONL→SQLite) |
| 5 | QueueHandler | LOW | Not implemented | MAYBE |

## Divergence Notes

1. **SQLite WAL confusion**: adversarial-performance said "NOT VERIFIED" but adversarial-security found it IS implemented in evidence_store.py. Resolution: evidence_store uses SQLite WAL, but skill_execution_gate.jsonl uses JSONL — two different systems.

2. **TOCTOU in transcript read**: adversarial-performance found it at StopHook_skill_execution_gate.py:300. adversarial-security did not report it. MEDIUM severity, fixable with try/except.

## Phase 1 Complete

Proceed to Phase 2: Meta-critique.
