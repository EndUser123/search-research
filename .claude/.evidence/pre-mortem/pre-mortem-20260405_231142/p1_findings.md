## Triage Classification

**code** — Round-robin batch scheduler implementation for 429-resilient YouTube transcript downloads. New module + integration changes across 4 files.

## Dispatched Specialists

- **adversarial-state-machine**: Video lifecycle, channel cooldown state machine, StopIteration handling, yield_next termination
- **adversarial-performance**: Connection churn, jitter blocking, WAL contention, per-call connection overhead
- **adversarial-security**: SQLite injection, path handling, exception swallowing, WAL checkpoint contention
- **adversarial-testing**: Test coverage gaps for cross-terminal cooldown, concurrent races, boundary conditions, order verification

## Specialist Findings Summary

### adversarial-state-machine

**Domain:** Status field lifecycle, generator termination, state transitions

**Key findings:**
- [HIGH] `_recover_stale_attempting` runs only at `__init__` — no runtime recovery (batch_scheduler.py:58-67)
- [HIGH] StopIteration caught only for `next(self._iterators[channel])` — if it escapes elsewhere in the for-loop body, the for-loop exits silently with no error (batch_scheduler.py:188-201)
- [MEDIUM] BEGIN EXCLUSIVE re-check design is correct for the TOCTOU scenario (batch_scheduler.py:99-118)
- [MEDIUM] yield_next() is not safe for multi-worker consumption — StopIteration propagates out, terminating the generator mid-iteration (batch_scheduler.py:174-220)
- [LOW] `consecutive_429s` is written but never read — dead field (batch_scheduler.py:120-138)
- [LOW] Iterator refresh called per-channel per-pass even when channel already removed from active_channels (batch_scheduler.py:193-194)
- [LOW] `_is_in_cooldown` opens new connection per call — pattern is inefficient (batch_scheduler.py:88-97)
- [LOW] `_archive_status` opens new connection per call — same pattern (batch_scheduler.py:165-172)

### adversarial-performance

**Domain:** Hot paths, connection churn, WAL contention, generator stall

**Key findings:**
- [HIGH] yield_next() makes up to 5 sequential SQLite connections per outer while-loop iteration (batch_scheduler.py:188-215)
- [HIGH] `_is_in_cooldown` opens/closes a fresh connection on every call — N connections per pass (batch_scheduler.py:88-97)
- [HIGH] `_archive_status` same pattern, called inside for-channel loop (batch_scheduler.py:165-172)
- [HIGH] `_get_pending_channels` and `_get_pending_videos` open fresh connections with no caching in hot loop (batch_scheduler.py:69-86)
- [HIGH] `time.sleep(random.uniform(_JITTER_MIN, _JITTER_MAX))` sits INSIDE the generator loop — blocks the producer, not consumers; 8 workers cannot fill the pipe faster, they are serialized by this sleep (batch_scheduler.py:215)
- [MEDIUM] archive_finalize called individually per future — exclusive-lock stampede under 8 workers (batch.py:265,269)
- [MEDIUM] `_record_attempting` runs full BEGIN EXCLUSIVE + commit + close cycle per yielded video (batch_scheduler.py:98-118)
- [LOW] Active channels not re-evaluated between outer-while iterations (batch_scheduler.py:185)
- [MEDIUM] yield_next relies on yielded_this_pass to detect no-progress but can spin on a channel returning only archived videos (batch_scheduler.py:218-220)

### adversarial-security

**Domain:** Injection, path handling, exception handling, WAL safety

**Key findings:**
- [LOW] Cross-terminal sync silently swallowed in `_record_source_429` — SQLite failures go undetected (transcript.py:222-225)
- [LOW] Same silent swallowing in `_record_source_success` (transcript.py:236-239)
- [MEDIUM] New `BatchScheduler()` instantiated on every 429 — each runs `_recover_stale_attempting()` + `PRAGMA wal_checkpoint(TRUNCATE)` under high 429 rates (transcript.py:219-225)
- [LOW] `PRAGMA wal_checkpoint(TRUNCATE)` runs in `__init__` on every instantiation — multiple terminals can cause contention (batch_scheduler.py:33-36)
- [LOW] WAL mode and busy_timeout set per-connection, not globally enforced — future query without PRAGMAs could introduce races (batch_scheduler.py:39-56)
- [LOW] exec_module path from `__file__` is safe; no path injection risk found (batch.py:56-61)
- [INFO] All queries parameterized — no SQL injection risk (batch_scheduler.py)
- [INFO] db_path from hardcoded paths only — no path traversal risk (batch_scheduler.py:25-26)

### adversarial-testing

**Domain:** Test coverage gaps, missing scenarios, boundary conditions

**Key findings:**
- [LOW] test_round_robin_interleaving verifies channel counts but NOT round-robin ORDER — A1,A2,A3,B1,B2,B3,C1,C2,C3 would also pass (tests/test_batch_scheduler.py:99-121)
- [HIGH] test_all_channels_in_cooldown tests single-instance only — no cross-terminal test where Terminal B respects a cooldown written by Terminal A (tests/test_batch_scheduler.py:209-231)
- [MEDIUM] No test for concurrent yield_next() race between two simultaneous callers (tests/test_batch_scheduler.py:99-121)
- [MEDIUM] No test for archive_finalize called twice or for INSERT OR REPLACE updating existing row (tests/test_batch_scheduler.py:339-354)
- [MEDIUM] test_stale_attempting_recovery uses `_STALE_ATTEMPTING_SECONDS - 10` (29:50) — boundary at exactly 1800s not tested (tests/test_batch_scheduler.py:234-261)
- [LOW] test_empty_channel_handling actually tests single-channel, not empty active_channels (tests/test_batch_scheduler.py:285-299)
- [LOW] test_jitter_range measures single sample — cannot distinguish random from constant (tests/test_batch_scheduler.py:263-283)
- [MEDIUM] test_record_429_counter never calls record_success to verify counter resets (tests/test_batch_scheduler.py:301-319)

## Consolidated Findings

### Logical Gaps & Inconsistencies

1.1. [HIGH] (source: adversarial-state-machine) — StopIteration escape in yield_next for-loop: batch_scheduler.py:188-201. If StopIteration escapes from anywhere in the for-loop body, the for-loop exits silently without propagating the error. The outer while loop may then have depleted active_channels, causing the generator to yield nothing. No exception is raised to alert the caller.

1.2. [HIGH] (source: adversarial-performance) — Jitter blocks the generator producer, not workers: batch_scheduler.py:215. `time.sleep()` sits between yields inside the generator. Workers calling `next(scheduler.yield_next())` are serialized — only one yield per sleep cycle, regardless of 8 workers. Workers cannot interleave to fill the pipe faster.

1.3. [HIGH] (source: adversarial-performance) — 5 SQLite connections per yield pass: batch_scheduler.py:188-215. Each call to `_is_in_cooldown` (1 per channel), `_get_pending_videos` (on iterator rebuild), `_archive_status` (per candidate video), and `_record_attempting` (with EXCLUSIVE) opens/closes a fresh connection. WAL busy_timeout queues them, but the open/close overhead is paid per call.

1.4. [HIGH] (source: adversarial-state-machine) — No runtime stale attempting recovery: batch_scheduler.py:58-67. `_recover_stale_attempting` runs only at `__init__`. If a worker picks up a video, crashes, and never calls `archive_finalize`, the video stays `attempting` indefinitely. The 30-minute threshold is a startup-only gate.

1.5. [MEDIUM] (source: adversarial-performance) — Active channels not re-evaluated between outer-while passes: batch_scheduler.py:185. If a channel enters cooldown between outer-while iterations, stale channels may consume iterations before being filtered in the next `yield_next()` call.

### Hidden Assumptions & Fragile Dependencies

2.1. [MEDIUM] (source: adversarial-security) — Cross-terminal sync is best-effort with silent failures: transcript.py:222-225, 236-239. `try/except pass` silently swallows SQLite failures. The in-memory circuit breaker and shared SQLite cooldown can diverge without alerting. If WAL checkpoint contention causes failures repeatedly, cross-terminal protection degrades silently.

2.2. [MEDIUM] (source: adversarial-security) — `BatchScheduler()` instantiated per 429 under high rate: transcript.py:219-225. Each instantiation runs `_recover_stale_attempting()` UPDATE + `PRAGMA wal_checkpoint(TRUNCATE)`. Under a burst of 429s, this creates checkpoint contention on the shared WAL DB.

2.3. [MEDIUM] (source: adversarial-performance) — WAL busy_timeout=5000 is sufficient under 8-worker concurrent load: batch_scheduler.py. The timeout is 5 seconds, but with multiple connections competing for EXCLUSIVE locks (archive_finalize per completed worker), the queue could grow. Not measured under real load.

2.4. [LOW] (source: adversarial-state-machine) — `consecutive_429s` is written but never read — dead field: batch_scheduler.py:120-138. The cooldown state machine has no escalating behavior. Writing it is harmless but indicates the field was intended for a more complex state machine that was not implemented.

2.5. [LOW] (source: adversarial-security) — WAL PRAGMAs set per-connection, not enforced globally: batch_scheduler.py:39-56. A future code change that adds a query without these PRAGMAs could introduce a race condition. Consider a single connection factory.

### Missing Obvious Actions / Best Practices

3.1. [HIGH] (source: adversarial-testing) — No cross-terminal cooldown test: tests/test_batch_scheduler.py:209-231. The test_all_channels_in_cooldown is single-instance. There is no test where Terminal A writes a cooldown and a new BatchScheduler instance (simulating Terminal B) respects it.

3.2. [MEDIUM] (source: adversarial-testing) — Round-robin ORDER not verified: tests/test_batch_scheduler.py:99-121. The test checks channel counts but a non-interleaved result (A1,A2,A3,B1,B2,B3,C1,C2,C3) would also pass. Order should be asserted as A1,B1,C1,A2,B2,C2,A3,B3,C3.

3.3. [MEDIUM] (source: adversarial-testing) — Concurrent yield race untested: tests/test_batch_scheduler.py. The EXCLUSIVE transaction was added for this scenario but no test exercises two simultaneous `yield_next()` callers.

3.4. [MEDIUM] (source: adversarial-testing) — `record_success` reset not tested: tests/test_batch_scheduler.py:301-319. No test verifies `consecutive_429s` resets to 0 after a success.

3.5. [MEDIUM] (source: adversarial-testing) — Stale boundary at exactly 1800s not tested: tests/test_batch_scheduler.py:234-261. Uses `_STALE_ATTEMPTING_SECONDS - 10` (29:50). No test at the exact cutoff or just over.

3.6. [MEDIUM] (source: adversarial-testing) — Double `archive_finalize` not tested: tests/test_batch_scheduler.py:339-354. No test that calling `archive_finalize(vid, 'failed')` twice or updating `attempting→failed` is idempotent.

### Risks and Edge Cases

4.1. [MEDIUM] (source: adversarial-performance) — Worker completion creates EXCLUSIVE-lock stampede: batch.py:265,269. Each of 8 workers fires `archive_finalize()` (with BEGIN EXCLUSIVE) immediately on completion. Under rapid completions, workers queue behind each other's EXCLUSIVE locks.

4.2. [MEDIUM] (source: adversarial-state-machine) — yield_next generator termination on mid-pass channel exhaustion: batch_scheduler.py:174-220. If `StopIteration` propagates out of the inner for-loop, the generator terminates mid-iteration. Callers consuming `yield_next()` would silently stop receiving videos.

4.3. [LOW] (source: adversarial-performance) — yielded_this_pass spin risk under high archive-hit rate: batch_scheduler.py:218-220. If a channel returns only already-archived videos, the loop spins until at least one yield succeeds. Not a correctness issue but could add latency under high completion rates.

4.4. [LOW] (source: adversarial-security) — Silent failure on repeated cross-terminal sync failures: transcript.py:222-225, 236-239. No alerting when SQLite consistently fails. The cross-terminal protection degrades silently.

### Concrete Recommendations

5.1. [MEDIUM] (source: adversarial-performance) — Move jitter OUTSIDE the generator: batch_scheduler.py:215. Replace `time.sleep(random.uniform(_JITTER_MIN, _JITTER_MAX))` inside `yield_next()` with per-worker jitter in `batch.py` between worker submission and the next `yield_next()` call. This way the generator produces continuously and workers handle their own staggered delays.

5.2. [MEDIUM] (source: adversarial-performance) — Add connection reuse to `_is_in_cooldown` and `_archive_status`: batch_scheduler.py. These are called on every channel and every candidate video. At minimum, share a single connection across multiple calls within the same `yield_next()` iteration rather than open/close per call.

5.3. [MEDIUM] (source: adversarial-security) — Add a shared BatchScheduler singleton for cross-terminal writes: transcript.py. Instead of `BatchScheduler()` instantiated on every 429, use a module-level singleton. This avoids repeated `_recover_stale_attempting()` + `wal_checkpoint` overhead.

5.4. [MEDIUM] (source: adversarial-testing) — Add `test_cross_terminal_cooldown`: tests/test_batch_scheduler.py. Test where one BatchScheduler instance writes a cooldown, then a second instance (new connection) verifies the channel is skipped.

5.5. [MEDIUM] (source: adversarial-state-machine) — Add runtime stale recovery: batch_scheduler.py. Consider calling `_recover_stale_attempting()` periodically (e.g., every N yields) or on each `yield_next()` invocation rather than only at `__init__`.

5.6. [LOW] (source: adversarial-security) — Log cross-terminal sync failures: transcript.py:224-225, 238-239. Replace `try/except pass` with a log warning on failure so degradation is observable.

5.7. [LOW] (source: adversarial-testing) — Add round-robin order test: tests/test_batch_scheduler.py. Assert order is A1,B1,C1,A2,B2,C2,A3,B3,C3.

5.8. [LOW] (source: adversarial-state-machine) — Remove dead `consecutive_429s` field or use it: batch_scheduler.py. Either implement escalating cooldown based on consecutive count, or remove the field to avoid confusion.

### Open Questions / Unknowns

6.1. [LOW] (source: adversarial-performance) — WAL busy_timeout=5000 adequacy under 8-worker load: Not measured. Could connections queue beyond 5 seconds under extreme load? (batch_scheduler.py)

6.2. [LOW] (source: adversarial-state-machine) — yield_next() behavior when called from multiple consumers in same process: The generator is not thread-safe for multiple callers consuming the same instance. Only batch.py's pattern (single consumer pulling, workers as coroutines) is used. Multi-caller consumption from same generator was not a stated goal. (batch_scheduler.py:174-220)

6.3. [LOW] (source: adversarial-testing) — Jitter test robustness: Single-sample test with +0.5 fudge factor is very loose. The jitter is 2-10s by default; the fudge factor makes the assertion nearly meaningless. (tests/test_batch_scheduler.py:263-283)
