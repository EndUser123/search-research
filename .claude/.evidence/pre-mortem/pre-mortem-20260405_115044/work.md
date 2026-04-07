# Memoization Implementation for GTO Session Chain Analysis

## Overview
Implement per-session caching for GTO v3 session chain analysis to avoid re-analyzing unchanged sessions.

## Files Modified
- **CREATED**: `P:/.claude/skills/gto/lib/session_memoizer.py` — new module
- **MODIFIED**: `P:/.claude/skills/gto/gto_orchestrator.py` — `_run_session_chain_analysis` method modified

## Architecture

### Cache Structure
- Location: `~/.claude/.evidence/gto-sessions/{session_id}.json`
- Per-session JSON with: `session_id`, `transcript_path`, `mtime`, `chain_depth`, `analyzed_at`, `chain_signature`, `result`
- `chain_signature`: sorted session IDs joined with commas (e.g. `"a,b,c"`)

### Cache Hit Logic
1. Build chain signature from sorted session IDs in `SessionChainEntry` objects/dicts
2. Load cache for current (origin) session
3. Verify chain signature matches cached chain_signature
4. For each session in chain: verify current mtime == cached mtime
5. If ALL match → return cached `ChainAnalysisResult` without LLM call

### Cache Miss Logic
1. Run full critique loop analysis
2. Call `memoizer.cache_session_result()` with session_id, transcript_path, chain_depth, chain_signature, result dict

### Integration Point
In `gto_orchestrator.py` `_run_session_chain_analysis`:
- Cache check inserted BEFORE critique loop
- On hit: reconstruct `ChainAnalysisResult` from cached dict and return immediately
- After successful analysis: cache result via `memoizer.cache_session_result()`

### Key Functions
- `_build_chain_signature(entries)`: extracts session IDs from entries (supports both objects and dicts), sorts, joins with commas
- `_get_session_mtime(path)`: returns `stat().st_mtime` or None
- `SessionMemoizer.get_cached_chain_result(entries)`: returns `(cached_result, missed_sessions_list)`
- `SessionMemoizer.cache_session_result(...)`: persists result after successful analysis
- `_load_session_cache(session_id)`: loads `CachedSessionAnalysis` or None
- `_save_session_cache(...)`: writes cache JSON to disk

## Cache Invalidation Strategy
- File mtime comparison: if session transcript file's mtime differs from cached mtime → cache miss
- Chain composition check: if sorted session IDs changed → cache miss
- Manual clear: `SessionMemoizer.clear_cache(session_id)` or `clear_cache(None)` for all

## Test Coverage
- `test_orchestrator.py` had 3 pre-existing test failures (now fixed):
  1. `enable_subagents` default was `False` not `True`
  2. `OrchestratorResult` required `health_report` field
  3. Gap rendering uses `gap.message` not `gap.gap_id`
