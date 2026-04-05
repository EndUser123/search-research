# Plan: Fix Cleanup Verifier Architecture

## Overview
Fix critical architectural flaw in cleanup verifier: Stop hook doesn't receive `toolHistory` field. Move tool tracking to PostToolUse hook (per-tool execution) and keep final verification in Stop hook (session end).

## Architecture

### Components

**1. PostToolUse_cleanup_tracker.py** (NEW)
- Runs after each tool execution
- Accumulates tool history to session-scoped file: `state/cleanup_history_{session_id}.json`
- Format: `{"tools": [{"name": "...", "input": {...}, "timestamp": "..."}]}`

**2. Stop_cleanup_verifier.py** (MODIFY)
- Read accumulated tool history from file instead of expecting `data.get("toolHistory")`
- File path: `P:/.claude/state/cleanup_history_{session_id}.json`
- Fallback: If file missing, return None (no verification without history)

**3. PostToolUse_router.py** (MODIFY)
- Register cleanup_tracker in registry (in-process execution)

### Data Flow

```
Tool executes → PostToolUse_cleanup_tracker.py
                ↓
                Append tool event to state/cleanup_history_{session_id}.json
                ↓
Session ends → Stop_cleanup_verifier.py
                ↓
                Read state/cleanup_history_{session_id}.json
                ↓
                Detect work type from accumulated tools
                ↓
                Check cleanup requirements
                ↓
                Display warnings (or block if CLEANUP_VERIFIER_MODE=block)
```

## Error Handling

**File write failures** (PostToolUse): Silent fail (best-effort tracking)
**File read failures** (Stop): Return None (no verification without history)
**Missing session_id**: Skip tracking (cannot scope file safely)
**Stale files**: Clean up files > 24 hours old

## Test Strategy

**Unit tests:**
1. `test_cleanup_tracker_creates_file()` - Verify file creation
2. `test_cleanup_tracker_append_multiple_tools()` - Verify accumulation
3. `test_cleanup_verifier_reads_history()` - Verify Stop hook reads file
4. `test_detect_work_type_from_history()` - Verify work type detection
5. `test_cleanup_requirements_check()` - Verify cleanup checks

**Integration test:**
1. Execute tools → Verify tracker accumulates history
2. Trigger Stop hook → Verify verifier reads history and detects work type

**Edge cases:**
- Empty tool history
- Missing session_id
- File read/write permissions
- Concurrent sessions (different session_ids)

## Standards Compliance

**Python 3.12+ patterns:**
- Type hints on all functions
- f-strings for formatting
- Pathlib for file paths
- Context managers for file I/O
- Exception handling with specific exceptions

**Code quality:**
- Defensive programming (check file exists before read)
- No bare list/string access (guard clauses)
- Error paths documented (graceful degradation)
- ruff linting compliance

## Ramifications

**Breaking changes:** None (cleanup verifier was non-functional, this fixes it)

**Backwards compatibility:**
- Old Stop_cleanup_verifier.py expected `toolHistory` field (never existed)
- New version reads from file (actual working implementation)
- Environment variables unchanged: `CLEANUP_VERIFIER_ENABLED`, `CLEANUP_VERIFIER_MODE`

**Performance impact:**
- PostToolUse: ~5-10ms per tool (file append, in-process)
- Stop: ~50-100ms (file read + work type detection)
- Acceptable overhead for cleanup verification benefit

**File storage:**
- Location: `P:/.claude/state/cleanup_history_{session_id}.json`
- Size per session: ~1-10 KB (depends on tool count)
- Cleanup: Delete files > 24 hours old (PostToolUse cleanup pass)

## Pre-Mortem Analysis (6-month future)

**Failure Scenario:** "Cleanup verification stopped working, developers forgot cleanup steps again."

**Root Causes:**
1. **File path collision** - Multiple sessions overwrote same history file
   - *Prevention:* Session-scoped filenames (`{session_id}.json`)

2. **Permission errors** - Hook couldn't write to state directory
   - *Prevention:* Silent fail with log to stderr (best-effort)

3. **Stale files** - Old sessions left files that confused new sessions
   - *Prevention:* Cleanup pass in PostToolUse (delete > 24h old)

4. **Memory leak** - State files accumulated indefinitely
   - *Prevention:* Auto-cleanup on PostToolUse execution

**Observability:**
- Log tracking failures to stderr: `[PostToolUse:cleanup_tracker] Failed to write history`
- Log verification failures: `[Stop:cleanup_verifier] Failed to read history`
- State file location: `P:/.claude/state/cleanup_history_{session_id}.json` (for debugging)
