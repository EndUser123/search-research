# Code Review Report

**Target:** `P:/packages/snapshot`
**Date:** 2026-05-02
**Review Type:** Multi-Agent Adversarial Review (5 specialists)

---

## Summary

The snapshot package is a well-structured Claude Code plugin for session snapshot capture and restore. It uses a V2 handoff envelope with resume snapshot, decision register, evidence index, and SHA256 checksum validation. The code is generally sound with good architectural decisions around multi-terminal isolation and stateless design.

However, several issues were identified across security, logic, performance, I/O validation, and quality domains. The most critical issues are in the I/O validation space regarding race conditions in active-session file writes and path validation bypass vulnerabilities.

---

## Health Score: 67%

Calculated as: `100 - (CRITICAL×20 + HIGH×10 + MEDIUM×5 + LOW×2)`, capped at 0-100.

| Severity | Count |
|----------|-------|
| CRITICAL | 2 |
| HIGH | 6 |
| MEDIUM | 7 |
| LOW | 12 |

---

## Findings

### Critical Issues

1. **[CRITICAL] Haiku subprocess spawn with unsanitized transcript content** (`SEC-001`)
   - **Location:** `PreCompact_snapshot_capture.py:959`
   - **Problem:** Subprocess.Popen passes transcript content directly without sanitization, creating potential for unexpected behavior or data exposure
   - **Recommendation:** Sanitize transcript content before passing to subprocess

2. **[CRITICAL] Backward scan loads entire transcript into memory** (`PERF-001`)
   - **Location:** `transcript.py:936` — `gather_context_with_boundaries()`
   - **Problem:** `f.readlines()` loads entire transcript file into memory, causing O(n) memory spike at restore time. For 50MB+ files, this causes significant memory pressure
   - **Recommendation:** Use `collections.deque(maxlen=max_messages)` for memory-efficient streaming

### High Priority

1. **[HIGH] Path.resolve() follows symlinks, bypassing validation** (`SEC-002`)
   - **Location:** `snapshot_v2.py:476` — `validate_envelope`
   - **Problem:** `Path.resolve()` follows symlinks before boundary check, allowing path traversal bypass
   - **Recommendation:** Use `os.path.realpath()` instead

2. **[HIGH] SNAPSHOT_PROJECT_ROOT allows arbitrary directory control** (`SEC-003`)
   - **Location:** `project_root.py:41` — `detect_project_root`
   - **Problem:** Env var overrides project root without validation, allowing arbitrary file writes
   - **Recommendation:** Validate SNAPSHOT_PROJECT_ROOT is within expected boundaries

3. **[HIGH] Active-session file write uses non-atomic rename pattern** (`IO-001`)
   - **Location:** `SessionStart_snapshot_restore.py:136-144`
   - **Problem:** Manual `unlink + rename` sequence is vulnerable to concurrent access race conditions
   - **Recommendation:** Use `atomic_write_with_retry` pattern with FileLock

4. **[HIGH] Temp file creation bypasses atomic_write_with_retry** (`IO-002`)
   - **Location:** `snapshot_files.py:126-131` and `terminal_file_registry.py:139-148`
   - **Problem:** Uses `os.fdopen + write` instead of `atomic_write_with_retry`, failing silently on Windows with active antivirus
   - **Recommendation:** Use `atomic_write_with_retry(temp_path, target_file)` in primary save path

5. **[HIGH] Topic-shift thresholds inconsistent between functions** (`LOGIC-001`)
   - **Location:** `transcript.py:999-1000` vs `1134-1135`
   - **Problem:** `gather_context_with_boundaries` uses 0.2 (20%) while `extract_last_substantive_user_message` uses 0.3 (30%)
   - **Impact:** Same transcript produces different boundary results with identical input
   - **Recommendation:** Use consistent 0.3 threshold across both functions

6. **[HIGH] Session registry path hardcoded to P: drive** (`SEC-005`)
   - **Location:** `session_registry.py:16` — `DEFAULT_REGISTRY_PATH`
   - **Problem:** Hardcoded `P:/.claude/.artifacts/` fails on Unix
   - **Recommendation:** Use platform-aware path

### Medium Priority

1. **[MEDIUM] Active session file writes outside project directory** (`SEC-004`)
   - **Location:** `SessionStart_snapshot_restore.py:137` — `Path.home()`
   - **Problem:** Session tracking leaks outside project into user home directory
   - **Recommendation:** Write to `project_root/.claude/state/` instead

2. **[MEDIUM] _read_last_phase scans entire accumulator file on every tool use** (`PERF-002`)
   - **Location:** `snapshot_accumulator.py:46`
   - **Problem:** Every PostToolUse triggers full backward iteration through all events
   - **Recommendation:** Cache last phase in memory, invalidate on phase_transition events

3. **[MEDIUM] TranscriptParser extract methods do redundant full-pass iterations** (`PERF-003`)
   - **Location:** `transcript.py:1720,1762,1811,1894,1961,2019`
   - **Problem:** 6 methods × 50,000 entries = 300,000 redundant iterations
   - **Recommendation:** Pre-compute type-filtered entry caches once

4. **[MEDIUM] mkdir fails propagate and lose handoff data** (`IO-003`)
   - **Location:** `snapshot_files.py:109`
   - **Problem:** `handoff_dir.mkdir()` has no error handling — disk full causes compaction block failure
   - **Recommendation:** Wrap in try/except, return False with logging

5. **[MEDIUM] Truncation return value discarded** (`IO-004`)
   - **Location:** `snapshot_store.py:349-432`
   - **Problem:** `atomic_write_with_validation` returns truncation flag but caller discards it
   - **Impact:** Silent data loss when handoff exceeds 500KB
   - **Recommendation:** Check return value and log warning if truncated

6. **[MEDIUM] Type ignore masks potential type mismatch** (`QUAL-001`)
   - **Location:** `handover.py:141`
   - **Problem:** `# type: ignore[return-value]` compromises type safety
   - **Recommendation:** Use `typing.cast()` or adjust TypedDict

7. **[MEDIUM] Pre-compiled regex patterns not grouped** (`QUAL-005`)
   - **Location:** `transcript.py:35`
   - **Problem:** 150+ lines of pattern definitions at module level rather than isolated
   - **Recommendation:** Consider extracting to `scripts/hooks/__lib/patterns.py`

### Low Priority

1. **[LOW] Magic number 5 for pending operations display** (`QUAL-002`)
2. **[LOW] Duplicate exception handling pattern** (`QUAL-003`)
3. **[LOW] Quality weight constants lack derivation documentation** (`QUAL-004`)
4. **[LOW] Multiple direct _get_parsed_entries calls in PreCompact** (`PERF-004`)
5. **[LOW] compute_file_content_hash lacks caching** (`PERF-005`)
6. **[LOW] Inconsistent file handling patterns in transcript.py** (`QUAL-006`)
7. **[LOW] Non-standard class attribute pattern in handover.py** (`QUAL-007`)
8. **[LOW] 50MB file size magic number lacks explanation** (`QUAL-008`)
9. **[LOW] Missing 'directive' key in intent_prefixes** (`LOGIC-002`)
10. **[LOW] PreCompact has no stdin size bound** (`SEC-006`)

---

## Recommendations

### Immediate (Critical + High)

1. **Fix Haiku subprocess sanitization** — transcript content must be escaped before passing to subprocess
2. **Fix path validation** — replace `Path.resolve()` with `os.path.realpath()` in `validate_envelope`
3. **Fix atomic write pattern** — use `atomic_write_with_retry` for active-session files in `SessionStart_snapshot_restore.py`
4. **Align topic-shift thresholds** — make both functions use 0.3 (30%)

### Short-term (Medium)

5. **Add memory-efficient context gathering** — replace `readlines()` with deque-based streaming
6. **Cache _read_last_phase** — avoid full file scan on every PostToolUse
7. **Handle mkdir failure gracefully** — prevent compaction block on disk full

### Long-term (Low)

8. **Extract patterns to submodule** — isolate regex definitions
9. **Add type safety for HandoverBuilder** — use typing.cast instead of type: ignore
10. **Document quality weight derivation** — explain why specific values were chosen

---

## Files Reviewed

**Core Python Files:**
- `scripts/hooks/PreCompact_snapshot_capture.py` — Main capture hook
- `scripts/hooks/SessionStart_snapshot_restore.py` — Main restore hook
- `scripts/hooks/__lib/transcript.py` — Transcript parsing (large, 2000+ lines)
- `scripts/hooks/__lib/snapshot_v2.py` — V2 envelope schema
- `scripts/hooks/__lib/snapshot_store.py` — Quality scoring
- `scripts/hooks/__lib/snapshot_files.py` — File I/O
- `scripts/hooks/__lib/snapshot_accumulator.py` — Phase tracking
- `scripts/hooks/__lib/project_root.py` — Project root detection
- `scripts/hooks/__lib/handover.py` — Handover builder
- `scripts/hooks/__lib/session_registry.py` — Session registry

**Test Files:** 99 Python files total across `tests/` and `scripts/tests/`

---

## Positive Observations

- Multi-terminal isolation is well-implemented
- SHA256 checksum validation is present and working
- FileLock pattern used correctly for TOCTOU protection
- Session boundary detection works correctly
- Type hints are present throughout most of the codebase
- Tests have good coverage with proper isolation (temp-root fixtures)