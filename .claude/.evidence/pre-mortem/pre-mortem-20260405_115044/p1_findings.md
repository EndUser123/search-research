## Triage Classification
code — Python implementation (session_memoizer.py + gto_orchestrator.py integration)

## Dispatched Specialists
- adversarial-logic: Chain signature validation, mtime checks, edge cases
- adversarial-security: Path traversal, TOCTOU, cache poisoning
- adversarial-performance: N+1 disk reads, stat() calls, redundant operations
- adversarial-io-validation: Atomic writes, path validation, exception handling

## Specialist Findings Summary

### adversarial-logic
**Domain:** Off-by-one, wrong operators, inverted conditionals, TOCTOU races
- [MEDIUM] Origin session mtime not re-validated after initial cache check (session_memoizer.py:213)
- [MEDIUM] Missing transcript_path causes mtime validation skip without cache miss (session_memoizer.py:227)
- [LOW] chain_depth not validated on cache retrieval (session_memoizer.py:172)
- [LOW] TOCTOU race between mtime check and cache write (session_memoizer.py:259)
- [LOW] Empty chain_signature not explicitly distinguished from non-existent cache

### adversarial-security
**Domain:** Path traversal, injection, cache poisoning, information disclosure
- [HIGH] Path traversal via unsanitized session_id (session_memoizer.py:58)
- [HIGH] Unvalidated transcript_path enables arbitrary file read (session_memoizer.py:95)
- [MEDIUM] Session chain relationship leakage via chain_signature (session_memoizer.py:74)
- [MEDIUM] TOCTOU race condition in cache file access (session_memoizer.py:86)
- [LOW] Missing bounds check on chain_depth (session_memoizer.py:97)
- [LOW] Unvalidated result dict structure (session_memoizer.py:100)

### adversarial-performance
**Domain:** Hot paths, loops, filesystem bottlenecks
- [HIGH] N+1 disk reads in get_cached_chain_result (session_memoizer.py:220)
- [HIGH] N+1 stat() calls per chain validation (session_memoizer.py:228)
- [MEDIUM] Redundant cache load for origin session (session_memoizer.py:205)
- [MEDIUM] Redundant mkdir on every cache write (session_memoizer.py:118)
- [LOW] SessionMemoizer instantiated per invocation (gto_orchestrator.py:1007)
- [LOW] _build_chain_signature is O(n) but unavoidable (no change needed)

### adversarial-io-validation
**Domain:** Path validation, atomicity, exception handling, external calls
- [HIGH] Non-atomic cache write can corrupt cache file on crash (session_memoizer.py:128)
- [HIGH] TOCTOU race between exists() check and open() (session_memoizer.py:86)
- [MEDIUM] Cache write has no exception handling in orchestrator (gto_orchestrator.py:1063)
- [MEDIUM] Transcript path not validated before mtime check (session_memoizer.py:226)
- [LOW] Path.home() can raise RuntimeError if HOME not set (session_memoizer.py:51)
- [LOW] Redundant exists() check in clear_cache before unlink (session_memoizer.py:280)
- [LOW] Cache miss list deduplication only on return, not during accumulation (session_memoizer.py:238)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-logic) — Origin session mtime not validated after chain_signature check: In `get_cached_chain_result()` lines 205-210, the origin session's cache is loaded and chain_signature is verified, but the origin's own transcript mtime is never re-checked. Only non-origin sessions get mtime validation in the loop at lines 215-235. This means the origin session's transcript could change after caching and stale data would still be returned. **Fix:** Add mtime validation for origin session after line 210.

1.2. [HIGH] (source: adversarial-logic) — Missing transcript_path silently skips mtime validation: At line 227, `if transcript_path:` continues to next iteration when path is absent, meaning a session with no transcript_path in the chain entry bypasses mtime validation entirely. The chain_signature check at line 234 still runs, so a cache hit could occur for a session whose underlying transcript was modified. **Fix:** If transcript_path is missing, treat as cache miss.

### Hidden Assumptions & Fragile Dependencies
2.1. [HIGH] (source: adversarial-security) — Path traversal via unsanitized session_id: `_get_session_cache_path()` at line 58 uses session_id directly in the file path without any sanitization. A malicious session_id containing `../` could escape `~/.claude/.evidence/gto-sessions/` and read/write files anywhere the user has access. **Fix:** Validate resolved path is within cache directory using `path.resolve().relative_to(cache_dir.resolve())`.

2.2. [HIGH] (source: adversarial-security) — Unvalidated transcript_path enables arbitrary file metadata access: The cached JSON stores `transcript_path` and `_get_session_mtime()` uses it for `stat()`. An attacker controlling cache contents could point to sensitive files and read metadata. **Fix:** Validate transcript_path is within expected session transcript directories.

2.3. [HIGH] (source: adversarial-io-validation) — Non-atomic cache write corrupts on interrupt: At line 128, `_save_session_cache` opens with mode `'w'` (truncating immediately) then writes JSON. If killed between truncate and write, the file is corrupted and silently discarded on next load. **Fix:** Use atomic write pattern — write to `.tmp` file then `os.replace()`.

2.4. [HIGH] (source: adversarial-io-validation) — TOCTOU between exists() and open(): At line 86, `cache_path.exists()` is checked before `open()`. On a concurrent system or network filesystem, the file could be deleted between check and open. **Fix:** Remove exists() check and let open() handle FileNotFoundError naturally.

2.5. [MEDIUM] (source: adversarial-security) — Session chain relationship leakage: `chain_signature` stores sorted session IDs in plain text, revealing which sessions are connected in a chain. **Fix:** Hash the chain_signature with a secret key.

2.6. [MEDIUM] (source: adversarial-io-validation) — Cache write has no exception handling in orchestrator: At line 1063, `memoizer.cache_session_result()` is called without try/except. Disk full or permission errors will propagate and fail the entire analysis. **Fix:** Wrap in try/except with logger.warning.

2.7. [MEDIUM] (source: adversarial-performance) — Redundant cache load for origin session: The origin session is loaded at line 205, then again at line 220 inside the loop. **Fix:** Store in local variable and reuse.

2.8. [MEDIUM] (source: adversarial-performance) — Redundant mkdir on every write: `_save_session_cache` calls `mkdir(parents=True)` before every write even though the directory already exists. **Fix:** Remove mkdir from `_save_session_cache`.

2.9. [LOW] (source: adversarial-io-validation) — Path.home() can raise RuntimeError: If HOME/USERPROFILE not set, `_get_sessions_cache_dir()` will throw at module load time. **Fix:** Add fallback to `/tmp/.claude/.evidence/gto-sessions/`.

2.10. [LOW] (source: adversarial-logic) — chain_depth not validated on cache retrieval: Cached `chain_depth` is not checked against `len(entries)`. **Fix:** Add `current_cache.chain_depth != len(entries)` as additional validation.

2.11. [LOW] (source: adversarial-io-validation) — Redundant exists() check in clear_cache: At line 280, `cache_path.exists()` is checked before `unlink()`. **Fix:** Use `cache_path.unlink(missing_ok=True)`.

2.12. [LOW] (source: adversarial-io-validation) — Cache miss list deduplication only at return: At line 238, `missed_sessions` is deduplicated via `set()` only at return, causing double-counting in the counter. **Fix:** Use a set from the start.

### Missing Obvious Actions / Best Practices
3.1. [HIGH] — No unit tests for session_memoizer: The module has zero test coverage despite being a performance-critical cache layer. Cache invalidation logic (mtime, chain_signature, chain_depth) is completely untested.

3.2. [HIGH] — No integration tests for cache hit/miss paths: The orchestrator integration has no tests verifying cache hit returns cached result, cache miss runs analysis, or write failures are handled gracefully.

3.3. [MEDIUM] — SessionMemoizer instantiated per call: At gto_orchestrator.py:1007, a new instance is created per invocation. Stats don't persist across calls. Consider module-level shared instance.

### Risks and Edge Cases
4.1. [MEDIUM] — TOCTOU race between mtime capture and cache write: In `cache_session_result()` at line 259, mtime is captured before calling `_save_session_cache()`. The file could change between capture and write. **Fix:** Re-read mtime inside `_save_session_cache()` and compare.

4.2. [LOW] — Empty chain_signature ambiguous: Returns `(None, [])` for both "empty chain" and "cache not found", making debugging harder. **Fix:** Log warning for empty chain.

4.3. [LOW] — Unvalidated result dict structure: The result dict is stored and returned without schema validation. **Fix:** Add validation of required fields before trusting cached data.

### Concrete Recommendations
5.1. [HIGH] Fix path traversal: Add path containment validation in `_get_session_cache_path()` (session_memoizer.py:58)
5.2. [HIGH] Fix non-atomic write: Use `os.replace()` pattern in `_save_session_cache()` (session_memoizer.py:128)
5.3. [HIGH] Fix TOCTOU load: Remove `exists()` check in `_load_session_cache()` (session_memoizer.py:86)
5.4. [HIGH] Fix origin session mtime validation gap (session_memoizer.py:213)
5.5. [HIGH] Fix missing transcript_path handling (session_memoizer.py:227)
5.6. [HIGH] Add unit tests for session_memoizer
5.7. [MEDIUM] Add try/except around cache write in orchestrator (gto_orchestrator.py:1063)
5.8. [MEDIUM] Remove redundant cache load (session_memoizer.py:205)
5.9. [MEDIUM] Remove redundant mkdir (session_memoizer.py:118)
5.10. [MEDIUM] Hash chain_signature to prevent session relationship leakage

### Open Questions / Unknowns
6.1. [LOW] Is `session_id` ever user-controlled, or always derived from Claude Code's internal session IDs? If always internal, path traversal risk is lower but still a defense-in-depth issue.
6.2. [LOW] What is the expected maximum chain depth? The code handles arbitrary depth but no limit is enforced.
6.3. [LOW] Should cache entries expire? Currently they persist indefinitely and are only invalidated by mtime changes or manual clear.
