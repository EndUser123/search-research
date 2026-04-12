# Phase 1 Findings — Skill-guard breadcrumb tracker

## Triage Classification
**code** — Python module (skill-guard breadcrumb system) analyzed for logic errors, I/O hazards, quality issues, and test coverage

## Dispatched Specialists
- **adversarial-logic**: Off-by-one, wrong operators, inverted conditionals, state machine bugs
- **adversarial-io-validation**: Path validation, file existence, external calls, hardcoded paths
- **adversarial-quality**: Tech debt, maintainability, silent error swallowing, global mutable state
- **adversarial-testing**: Missing tests, coverage gaps, brittle tests, cache/state issues

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pure logic errors, operator bugs, conditional inversions

- **[BLOCKER] LOGIC-001 (tracker.py:350, enforcement.py:183-207)**: `tool_count` is initialized to 0 but never incremented anywhere. MINIMAL and STANDARD enforcement call `_verify_minimal` which checks `tool_count < 2` — this always evaluates True, so these enforcement levels always fail. Only STRICT works.
- **[HIGH] LOGIC-002 (tracker.py:316-321)**: `initialize_breadcrumb_trail` returns early when `workflow_steps` is empty. Subsequent `set_breadcrumb` calls with `force=False` also return early (trail exists = None). No trail ever created. Skills without workflow_steps silently opt out.
- **[MEDIUM] LOGIC-003 (cache.py:157-169)**: `_load_from_log` assumes first log entry contains `completed_steps` key. If first entry is `trail_initialized` without that key, `KeyError` on first `step_complete` processing.
- **[LOW] LOGIC-004 (tracker.py:258-280)**: Regex pattern for workflow_steps fallback only captures step ID before colon. YAML dict-format items like `{id: analyze, description: Analyze}` not handled correctly by regex.

### adversarial-io-validation
**Domain:** I/O operations, path handling, external service assumptions, file operations

- **[BLOCKER] IO-001 (tracker.py:54, database.py:39-40)**: Hardcoded `P:` drive paths (`STATE_DIR`, `DEFAULT_DB_PATH`) with no validation or fallback. If P: drive unavailable (VPN drop, network mapped drive), all breadcrumb operations crash with `OSError`.
- **[HIGH] IO-002 (tracker.py:183-226, 230-281)**: YAML parse failure → regex fallback → returns empty list. No way to distinguish "no workflow_steps declared" vs "YAML parse error" vs "regex parse error".
- **[HIGH] IO-003 (database.py:138, 90)**: `get_connection()` catches all exceptions and returns None. No distinction between database locked, corrupted, permissions error, or file not found.
- **[MEDIUM] IO-004 (log.py:134-136, 176-195)**: TOCTOU race in `_rotate_log`: size check before write, no lock held between check and rename. Concurrent terminals can cause rotation to fail silently.
- **[MEDIUM] IO-005 (tracker.py:316-321)**: `initialize_breadcrumb_trail` returns early silently when workflow_steps is empty. No log entry, no breadcrumb file created.
- **[MEDIUM] IO-006 (tracker.py:100-116)**: Bare `except Exception: pass` in `_append_ledger_event` silently swallows all exceptions from `hook_ledger.append_event`. Audit trail gaps are invisible.
- **[LOW] IO-007 (tracker.py:501-525)**: `_windows_safe_unlink` catches OSError and silently proceeds. Orphaned rename fallback also catches and passes.
- **[LOW] IO-008 (database.py:116-118)**: `db_path.parent.mkdir` has no error handling — permission errors propagate with less clear message.
- **[LOW] IO-009 (cache.py:171-173)**: `_load_from_log` returns None on any error — caller cannot distinguish incomplete state from empty state.
- **[LOW] IO-010 (tracker.py:145-149)**: Path traversal check only blocks `.` and `..` — simplistic validation that doesn't handle homoglyphs or encoded characters.

### adversarial-quality
**Domain:** Tech debt, maintainability, error handling, code clarity

- **[MEDIUM] QUAL-001 (tracker.py:94)**: `_append_ledger_event` silently swallows all exceptions — no logging, no warning. Debugging ledger integration failures requires adding debug prints.
- **[MEDIUM] QUAL-002 (cache.py:171)**: `_load_from_log` catches all exceptions and returns None — conflates "log file doesn't exist" with "log file corrupted".
- **[MEDIUM] QUAL-005 (tracker.py:145)**: Path traversal check incorrectly blocks dots in skill names (`.` only, not `..`). Valid plugin-style skill names rejected.
- **[MEDIUM] QUAL-010 (tracker.py:59, 67)**: Global `_db_initialized` flag has no locking — race condition in multi-threaded hook execution.
- **[LOW] QUAL-003 (tracker.py:54)**: `STATE_DIR` hardcoded as `P:/` with no env var override (unlike `DB_PATH` which uses `CLAUDE_STATE_DIR`).
- **[LOW] QUAL-004 (tracker.py:369-390)**: Misleading comments say "fallback" but code always does dual-write (SQLite + file).
- **[LOW] QUAL-006 (enforcement.py:232-235)**: Keyword-based verification uses substring matching — "preverified" matches "verify", "testimony" matches "test".
- **[LOW] QUAL-007 (cache.py:42)**: `SNAPSHOT_INTERVAL = 30.0` magic number with no rationale comment.
- **[LOW] QUAL-008 (tracker.py:230-281)**: No test coverage for `_regex_workflow_steps_fallback`.
- **[LOW] QUAL-009 (cache.py:175-185)**: LRU eviction provides no logging or metrics about which skill was evicted.

### adversarial-testing
**Domain:** Test coverage gaps, missing scenarios, brittle tests

- **[HIGH] TEST-001 (cache.py:162)**: `_load_from_log` only reconstructs `completed_steps` from log entries. Does not reconstruct `steps` dict, `current_step`, `tool_count`, or evidence. Cache invalidation loses critical data.
- **[HIGH] TEST-009 (enforcement.py:139-180)**: Evidence is stored in `steps[step]['evidence']` but `verify_breadcrumb_trail()` never validates it. A skill can claim completion with empty evidence.
- **[MEDIUM] TEST-002 (tracker.py:258)**: Regex pattern only matches single-line step entries. Multi-line YAML step descriptions silently return empty steps.
- **[MEDIUM] TEST-003 (tracker.py:453-466)**: SQLite succeeds but file write fails → divergent state. No reconciliation mechanism.
- **[MEDIUM] TEST-005 (tracker.py:145)**: Skill names with dots create non-standard breadcrumb files (`breadcrumb_foo.bar.json`).
- **[MEDIUM] TEST-006 (tracker.py:572-586)**: TOCTOU race in `get_breadcrumb_trail` — cache returns at line 109, file re-read at line 576 for terminal_id verification. No lock between.
- **[MEDIUM] TEST-010 (cache.py:158)**: `_load_from_log` reverses log entries expecting oldest first, but `replay()` returns newest first. `entries[0]` after reversal is newest, not trail_initialized.
- **[LOW] TEST-004 (tracker.py:115)**: `_append_ledger_event` bare `except` — no DEBUG logging, no metrics for caught exceptions.
- **[LOW] TEST-007 (cache.py:91)**: `_get_cache_key` doesn't include `run_id` — force=True re-initialization corrupts cached state.
- **[LOW] TEST-008 (log.py:186)**: Log rotation archives (`*_{timestamp}.jsonl`) are never cleaned up. Disk space grows unbounded.

---

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. **[BLOCKER] (adversarial-logic)**: `tool_count` never incremented — MINIMAL/STANDARD enforcement always fail (tracker.py:350, enforcement.py:183-207)
1.2. **[HIGH] (adversarial-logic)**: `initialize_breadcrumb_trail` silently returns on empty workflow_steps — breadcrumb tracking never starts (tracker.py:316-321)
1.3. **[MEDIUM] (adversarial-logic)**: `_load_from_log` assumes `completed_steps` in first log entry — KeyError if missing (cache.py:157-169)
1.4. **[MEDIUM] (adversarial-testing)**: `_load_from_log` reverses log expecting oldest first but replay returns newest first (cache.py:158)

### Hidden Assumptions & Fragile Dependencies
2.1. **[HIGH] (adversarial-io-validation)**: P: drive always available — no validation/fallback when drive unavailable (tracker.py:54)
2.2. **[HIGH] (adversarial-io-validation)**: Cannot distinguish "no steps declared" vs "parse error" vs "regex failed" — all return empty list (tracker.py:183-226)
2.3. **[HIGH] (adversarial-testing)**: Cache replay only reconstructs `completed_steps` — loses `steps` dict, evidence, `tool_count` (cache.py:162)
2.4. **[MEDIUM] (adversarial-io-validation)**: Database errors return None without distinguishing corruption from other failures (database.py:138)
2.5. **[MEDIUM] (adversarial-testing)**: SQLite and file storage can diverge — no reconciliation (tracker.py:453-466)
2.6. **[MEDIUM] (adversarial-quality)**: `_db_initialized` global has no threading lock — race condition (tracker.py:67)

### Missing Obvious Actions / Best Practices
3.1. **[BLOCKER] (adversarial-logic)**: Add `tool_count` increment in `set_breadcrumb()` or separate `increment_tool_count()` function called by PostToolUse hook
3.2. **[HIGH] (adversarial-testing)**: Add evidence validation in `_verify_strict` — check evidence is non-empty dict with required fields (enforcement.py:139-180)
3.3. **[HIGH] (adversarial-io-validation)**: Add env var override for `STATE_DIR` (like `DB_PATH` does with `CLAUDE_STATE_DIR`) (tracker.py:54)
3.4. **[MEDIUM] (adversarial-io-validation)**: Add file locking during log rotation or make rotation idempotent (log.py:134-136)
3.5. **[MEDIUM] (adversarial-quality)**: Distinguish error types in `get_connection()` — file not found vs permission vs corruption (database.py:138)
3.6. **[MEDIUM] (adversarial-quality)**: Return structured result from `_load_workflow_steps` that distinguishes "no steps" from "parse error" (tracker.py:183-226)
3.7. **[MEDIUM] (adversarial-quality)**: Change path traversal check to only block `..`, not `.` (tracker.py:145)

### Risks and Edge Cases
4.1. **[HIGH] (adversarial-io-validation)**: Concurrent terminals — both check size < MAX_LOG_SIZE, both append, one renames, other rename fails silently (log.py:193-195)
4.2. **[MEDIUM] (adversarial-io-validation)**: `initialize_breadcrumb_trail` early return gives no indication whether skill has no steps or error loading them (tracker.py:316-321)
4.3. **[MEDIUM] (adversarial-quality)**: Substring keyword matching — "preverified" matches "verify", "testimony" matches "test" (enforcement.py:232-235)
4.4. **[MEDIUM] (adversarial-testing)**: `run_id` not in cache key — force=True re-init corrupts prior state (cache.py:91)
4.5. **[LOW] (adversarial-io-validation)**: `_windows_safe_unlink` silently proceeds on failure — orphaned files accumulate (tracker.py:501-525)
4.6. **[LOW] (adversarial-testing)**: Rotated log archives never cleaned up — disk growth unbounded (log.py:186)

### Concrete Recommendations
5.1. **[BLOCKER]** In `set_breadcrumb()`, increment `trail['tool_count']` and persist on every call (tracker.py:350)
5.2. **[HIGH]** In `initialize_breadcrumb_trail`, when workflow_steps is empty, create minimal trail with default step `invoke_skill` so tool_count/duration still track (tracker.py:320-321)
5.3. **[HIGH]** Add env var `CLAUDE_STATE_DIR` override for `STATE_DIR` (tracker.py:54)
5.4. **[HIGH]** Extend `_load_from_log` to reconstruct complete trail state including `steps` dict and evidence (cache.py:162)
5.5. **[MEDIUM]** Add word-boundary regex matching for verification keywords (enforcement.py:232-235)
5.6. **[MEDIUM]** Include `run_id` in cache key or invalidate cache on `force=True` (cache.py:91)
5.7. **[MEDIUM]** Add threading.Lock around `_db_initialized` check (tracker.py:67)
5.8. **[MEDIUM]** Log at WARNING when regex fallback is used for workflow_steps (tracker.py:210-218)
5.9. **[MEDIUM]** Return `(state, is_complete)` from `_load_from_log` or set `replay_error` flag (cache.py:171-173)

### Open Questions / Unknowns
6.1. **[HIGH] (adversarial-logic)**: Is `tool_count` tracking intentionally not implemented (deferred)? Docstrings and enforcement.py reference it but implementation doesn't support it.
6.2. **[MEDIUM] (adversarial-io-validation)**: What is the recovery procedure when `diagnostics.db` is corrupted — should it be rebuilt from file-based sources?
6.3. **[LOW] (adversarial-quality)**: Should skills without `workflow_steps` be allowed to use MINIMAL enforcement with just duration + tool_count checks? Current behavior is silent failure.
