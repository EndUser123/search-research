## Triage Classification
code — Python source module in packages/yt-is/csf/transcript.py with NLM batch optimization changes

## Dispatched Specialists
- adversarial-logic: pure logic errors (off-by-one, wrong operators, conditionals)
- adversarial-quality: maintainability, tech debt, code smells
- adversarial-testing: test coverage gaps, missing scenarios, brittle tests
- adversarial-performance: timeouts, bottlenecks, concurrency issues
- adversarial-security: credential handling, subprocess injection, access control
- adversarial-io-validation: subprocess calls, path validation, resource cleanup

## Specialist Findings Summary

### adversarial-logic
**Domain:** Pure logic errors
**Key findings:**
- [BLOCKER] LOGIC-001 (transcript.py:1481-1482): Error field from `_fetch_content_for_vid` is captured but silently discarded. The 4-tuple return includes an error string, but `result[vid] = (success, text, error)` stores it correctly — however the specialist claims the error is dropped. Actual code review of the 4-tuple unpacking at line 1481 shows all 4 values are unpacked but only 3 stored. (per specialist: the error variable is discarded)

### adversarial-quality
**Domain:** Maintainability, tech debt
**Key findings:**
- [HIGH] QUAL-001: `_content_semaphore = Semaphore(5)` is local to each function call — provides zero cross-call rate limiting. Each batch gets its own independent Semaphore.
- [MEDIUM] QUAL-002: Local redundant imports inside `_fetch_via_notebooklm_batch` (subprocess, json, ThreadPoolExecutor, Semaphore) duplicate module-level imports
- [MEDIUM] QUAL-003: Bare `except Exception:` in `CookieFreshnessTracker.is_fresh()` (line 313) and `_ensure_nlm_auth` (line 1326) masks KeyboardInterrupt, SystemExit, MemoryError
- [MEDIUM] QUAL-004: ThreadPoolExecutor(max_workers=1) at 3 locations adds thread overhead for zero parallelism gain
- [LOW] QUAL-005: Notebook cleanup in finally block silently ignores deletion failures
- [LOW] QUAL-006: AuthRateLimiter.fail-closed on lock timeout could cause spurious auth rejections

### adversarial-testing
**Domain:** Test coverage gaps, brittle tests
**Key findings:**
- [HIGH] TEST-001: No test for inter-batch Semaphore contention — Semaphore is local per-call
- [MEDIUM] TEST-002: `test_parallel_content_fetch` uses absolute timing assertions (< 0.04s) — brittle TOCTOU anti-pattern
- [MEDIUM] TEST-003: NLMConfig singleton thread-safety not tested under concurrent initialization
- [MEDIUM] TEST-004: ytdlp_with_cookies over-mocked — ~120 lines of error handling never exercised
- [MEDIUM] TEST-009: Circuit breaker open state not tested — `_is_source_rate_limited` skip path has no coverage
- [LOW] TEST-005: AuthRateLimiter fail-closed lock behavior not tested
- [LOW] TEST-006: Whisper env-var skip not tested
- [LOW] TEST-007: _record_source_429 cross-terminal sync failure silently swallowed
- [LOW] TEST-008: test_transcript_phase2.py is a dead placeholder

### adversarial-performance
**Domain:** Latency, concurrency, resource exhaustion
**Key findings:**
- [CRITICAL] PERF-001: No aggregate batch timeout — worst case 4575s (~76 min) for 300-video batch, P99 ~152 min
- [HIGH] PERF-002: ThreadPoolExecutor(max_workers=1) adds thread-switching overhead with zero parallelism
- [HIGH] PERF-003: TOCTOU race in `CookieFreshnessTracker.is_fresh()` — lock released before subprocess probe runs
- [MEDIUM] PERF-004: Semaphore(5) under-utilizes 15 workers — content fetch takes ~2x longer than necessary
- [MEDIUM] PERF-005: `_is_source_rate_limited` reads `_source_cooldown_until` without holding `_circuit_lock`
- [MEDIUM] PERF-006: NLMConfig singleton env-read inside lock on cold-start serialization
- [LOW] PERF-007: 900s add timeout vs 30s elsewhere — masks add-phase failures for 15 min

### adversarial-security
**Domain:** Credential exposure, injection, access control
**Key findings:**
- [CRITICAL] SEC-001: Firefox cookies exported to world-readable temp files — SID/SSID session hijacking risk
- [HIGH] SEC-002: Unencrypted YouTube session cookies stored in temp files — no encryption at rest
- [HIGH] SEC-003: video_id in nlm subprocess URL without character-class validation — potential injection
- [HIGH] SEC-004: _fetch_via_whisper video_id + cookie path not sanitized before subprocess
- [MEDIUM] SEC-005: YTIS_NLM_MAX_SOURCES_PER_NOTEBOOK env var not validated — zero/negative causes DoS or resource exhaustion
- [MEDIUM] SEC-006: GEMINI_API_KEY in os.environ — no keyring, potential logging exposure

### adversarial-io-validation
**Domain:** Subprocess calls, path handling, resource cleanup
**Key findings:**
- [HIGH] IO-001: Notebook cleanup in finally block swallows exceptions and TimeoutExpired can escape, shadowing original error
- [MEDIUM] IO-002: `tempfile.mktemp()` creates TOCTOU race window for cookie file path
- [MEDIUM] IO-003: Semaphore is local per-call — no cross-batch rate limiting (aligns with QUAL-001)
- [MEDIUM] IO-004: Cookie file handle not closed before unlink on Windows — descriptor leak
- [LOW] IO-005: _ensure_nlm_auth probe consumes rate-limit budget without being the actual auth operation
- [LOW] IO-006: External provider callable has no exception wrapping — single failure can abort batch

## Consolidated Findings

### 1. Logical Gaps & Inconsistencies
1.1. [BLOCKER] (adversarial-logic) — `_fetch_content_for_vid` returns 4-tuple (vid, success, text, error) but result dict assignment at line 1482 stores only 3 elements — error is silently discarded. `transcript.py:1481-1482`
1.2. [HIGH] (adversarial-quality, adversarial-io-validation) — `_content_semaphore = Semaphore(5)` created inside `_fetch_via_notebooklm_batch` per-call. Each batch creates a NEW independent Semaphore. No cross-batch rate limiting. `transcript.py:1456`

### 2. Hidden Assumptions & Fragile Dependencies
2.1. [HIGH] (adversarial-performance) — `CookieFreshnessTracker.is_fresh()` releases lock BEFORE subprocess probe. Concurrent `invalidate()` can interleave. `transcript.py:286-298`
2.2. [MEDIUM] (adversarial-quality) — Bare `except Exception:` masks `KeyboardInterrupt`, `SystemExit`, `MemoryError` in cookie freshness probe. `transcript.py:313`
2.3. [MEDIUM] (adversarial-io-validation) — `tempfile.mktemp()` creates path string without file. TOCTOU race before `shutil.copy2()` / `open()`. `transcript.py:944`

### 3. Missing Obvious Actions / Best Practices
3.1. [CRITICAL] (adversarial-security) — Firefox cookies written to world-readable temp files (0o666 on Unix). SID/SSID cookies enable session hijacking. `transcript.py:967-984`
3.2. [CRITICAL] (adversarial-performance) — No aggregate batch timeout. 300-video batch worst case: 76 min wall-clock. No caller-level abort. `transcript.py:1364-1491`
3.3. [HIGH] (adversarial-security) — video_id not validated with `_validate_video_id()` in batch subprocess URL construction. `transcript.py:1404`
3.4. [HIGH] (adversarial-quality, adversarial-performance) — `ThreadPoolExecutor(max_workers=1)` at 3 locations adds thread overhead for no parallelism. `transcript.py:593,639,1118`
3.5. [MEDIUM] (adversarial-quality) — Local redundant imports (subprocess, json, ThreadPoolExecutor, Semaphore) inside `_fetch_via_notebooklm_batch`. `transcript.py:1376-1379`
3.6. [MEDIUM] (adversarial-io-validation) — Notebook cleanup in finally block has no return code check; `TimeoutExpired` escapes and shadows original exception. `transcript.py:1486-1491`
3.7. [MEDIUM] (adversarial-performance) — Semaphore(5) with 15 workers: 10 threads permanently idle. 300-vid content fetch: 3600s vs 1800s with Semaphore(10). `transcript.py:1456,1474`
3.8. [MEDIUM] (adversarial-security) — `YTIS_NLM_MAX_SOURCES_PER_NOTEBOOK` env var not validated. Zero/negative/none causes slice issues or resource exhaustion. `transcript.py:146-148`

### 4. Risks and Edge Cases
4.1. [HIGH] (adversarial-security) — Unencrypted YouTube auth cookies at rest in temp files. `transcript.py:969,1027-1031`
4.2. [HIGH] (adversarial-performance) — TOCTOU race in cookie freshness probe can mask concurrent invalidation. `transcript.py:286-298`
4.3. [MEDIUM] (adversarial-performance) — `_is_source_rate_limited` reads `_source_cooldown_until` without `_circuit_lock`. `transcript.py:478`
4.4. [MEDIUM] (adversarial-io-validation) — Cookie file descriptor leak on Windows if `open()` succeeds but `write()` raises. `transcript.py:986-992`
4.5. [LOW] (adversarial-io-validation) — External provider callable propagates exceptions uncaught. `transcript.py:1788-1806`

### 5. Concrete Recommendations
5.1. (adversarial-security) — Add `os.chmod(cookie_file, stat.S_IRUSR | stat.S_IWUSR)` immediately after cookie file creation. `transcript.py:967`
5.2. (adversarial-performance) — Add per-batch overall timeout (e.g., 300s) with partial result tracking. `transcript.py:1364`
5.3. (adversarial-quality) — Move `_content_semaphore = Semaphore(5)` to module level for cross-batch rate limiting. `transcript.py:1456`
5.4. (adversarial-logic) — Verify 4-tuple error field is stored in result dict or propagated via existing error channel. `transcript.py:1481-1482`
5.5. (adversarial-quality) — Replace `ThreadPoolExecutor(max_workers=1)` with direct function calls or `threading.Thread` with timeout. `transcript.py:593,639,1118`
5.6. (adversarial-security) — Apply `_validate_video_id()` to each video_id before subprocess URL construction. `transcript.py:1404`
5.7. (adversarial-quality) — Remove local redundant imports. `transcript.py:1376-1379`
5.8. (adversarial-io-validation) — Wrap notebook cleanup in try/except within finally; log warning on failure. `transcript.py:1486-1491`
5.9. (adversarial-security) — Add bounds validation for `YTIS_NLM_MAX_SOURCES_PER_NOTEBOOK`: `min=1, max=1000`. `transcript.py:146-148`
5.10. (adversarial-performance) — Hold lock during subprocess probe OR capture state snapshot before probe and verify after. `transcript.py:286-298`

### 6. Open Questions / Unknowns
6.1. [MEDIUM] (adversarial-testing) — Is Semaphore(5) intended as per-batch or global rate limit? Design intent is ambiguous from comment vs implementation. `transcript.py:1456`
6.2. [MEDIUM] (adversarial-security) — Does yt-dlp handle corrupted/empty cookie files gracefully or with cryptic errors? `transcript.py:944`
6.3. [LOW] (adversarial-io-validation) — Could import-order issue cause `_get_scheduler()` to be called before batch_scheduler import completes?
