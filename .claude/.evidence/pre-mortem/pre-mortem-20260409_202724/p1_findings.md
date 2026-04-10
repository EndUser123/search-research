## Triage Classification
code — Python modules (cache.py, router_async.py) with async search and LRU cache optimizations

## Dispatched Specialists
- adversarial-performance: hot paths, asyncio concurrency, TTL thread
- adversarial-logic: conditionals, lock handling, edge cases
- adversarial-io-validation: file I/O, thread safety, daemon cleanup
- adversarial-quality: NOT COMPLETED (API overload 529) — can be re-run separately

## Specialist Findings Summary

### adversarial-performance
**Domain:** Performance hot paths, concurrent execution
**Key findings:**
- [CRITICAL] asyncio.gather has no overall timeout — can hang indefinitely if all backends are slow (router_async.py:291)
- [MEDIUM] TTL cleanup thread spawned per QueryCache instance — resource leak, redundant sweeps (cache.py:55)
- [LOW] _sweep_expired iterates entire cache under lock — inefficient for large caches (cache.py:65)
- [MEDIUM] HyDE cache check-then-act — but actually by design (router_async.py:270)
- [LOW] Non-atomic read-modify-write in LRU get (cache.py:112)

### adversarial-logic
**Domain:** Logic correctness, conditionals, edge cases
**Key findings:**
- [MEDIUM] TTL comparison uses `>` instead of `>=` — creates ~1 second grace period where entries at exactly TTL age are still valid (cache.py:107,71)
- [LOW] Multiple cleanup threads for same terminal_id — wasteful but not correctness-breaking (cache.py:53)
- [LOW] HyDE only caches enhanced query — original query searches miss cache (router_async.py:309-313)

### adversarial-io-validation
**Domain:** Path validation, file I/O, external calls
**Key findings:**
- [LOW] daemon=True cleanup thread doesn't block process exit — expired entries persist across abrupt shutdowns (cache.py:62)

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [MEDIUM] (source: adversarial-logic) — TTL uses `>` instead of `>=` at cache.py:107 and cache.py:71. Entry at exactly TTL age (e.g., 3600 seconds) evaluates as NOT expired. Low impact for 1-hour TTL but imprecise.
1.2. [LOW] (source: adversarial-logic) — LOGIC-002: Multiple cleanup threads spawned when same terminal_id shares cache across instances (cache.py:53). Wasteful but lock prevents correctness issues.

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-performance) — PERF-001: asyncio.gather() assumes individual backend timeouts prevent overall hang, but no total timeout wrapper. If all backends slow simultaneously, worst case is N×backend_timeout (up to 16s for 8 backends).
2.2. [LOW] (source: adversarial-io-validation) — IO-001: Cleanup thread is daemon — assumes process exit is graceful or cache pollution from abrupt shutdown is acceptable.

### Missing Obvious Actions / Best Practices
3.1. [MEDIUM] (source: adversarial-performance) — TTL cleanup thread per instance should be single module-level thread with coordination. Each QueryCache() with same terminal_id spawns redundant cleanup thread.

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-performance) — PERF-001: No overall timeout on asyncio.gather(). Fast mode expects <2s but worst case is 16s. May cause client timeouts.
4.2. [LOW] (source: adversarial-performance) — PERF-003: _sweep_expired() is O(n) under lock. For cache near max_size with few expired entries, this is wasteful but not blocking.

### Concrete Recommendations
5.1. [MEDIUM] Add overall timeout wrapper to asyncio.gather() — `await asyncio.wait_for(asyncio.gather(...), timeout=total_timeout)` (router_async.py:291)
5.2. [MEDIUM] Change TTL comparison from `>` to `>=` for precise expiration (cache.py:107,71)
5.3. [MEDIUM] Consider single module-level cleanup thread instead of per-instance (cache.py:55)
5.4. [LOW] Cache HyDE results under BOTH enhanced and original query keys for better hit rate (router_async.py:309-313)

### Open Questions / Unknowns
6.1. [LOW] (source: adversarial-performance) — What is the expected total timeout budget? If fast mode is <2s, PERF-001 is more critical. If 8s is acceptable for comprehensive, it's less urgent.
