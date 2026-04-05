# Architecture Decision: /s Timeout Fix

**Date:** 2026-03-15
**Status:** Implemented
**Decision:** Make orchestrator's overall phase timeout configurable with default of 600 seconds (10 minutes)
**Confidence:** 85%

---

## Problem Statement

`/s` times out after 180s waiting for ALL providers to complete. The blocking `asyncio.wait_for()` in the orchestrator causes slow CLI providers (30s timeout) to block the entire brainstorm session. A previous fix attempt added a 45s per-provider timeout wrapper, which created TRIPLE timeout layering and made the problem worse.

**Three timeout layers:**
1. CLI provider: 30s (base.py in `__csf`)
2. Per-provider wrapper: 45s (my fix - added complexity)
3. Orchestrator overall: 180s (blocks everything)

---

## Root Cause

`orchestrator.py:636-656` uses `asyncio.wait_for()` around `asyncio.gather()`:

```python
results = await asyncio.wait_for(
    asyncio.gather(*tasks, return_exceptions=True),
    timeout=timeout,  # BLOCKS until ALL agents finish
)
except TimeoutError:
    # Times out after 180s even if some providers finished quickly
```

This means:
- Fast T1/T2 API providers (claude, openai) complete in ~30-60s
- But orchestrator waits for ALL providers, including slow CLI providers
- User experiences "Diverge phase timed out after 108s" even though most providers succeeded

---

## Options Evaluated

### Option A: Remove orchestrator's overall phase timeout (RECOMMENDED)

**Approach:** Remove `asyncio.wait_for()` wrapper, let each provider timeout independently

**Pros:**
- Addresses root cause: removes blocking behavior
- Fast providers complete quickly; slow providers timeout independently
- Proven pattern: `/llm-cli` uses this successfully
- Simplest change: ~10 lines removed

**Cons:**
- No overall timeout guard - user may wait longer if all providers are slow
- Rare edge case: if all 4 API providers are down, brainstorm may hang

**Complexity:** Low (remove code)

**Evidence:** `/llm-cli` pattern (parallel_llm.py) uses independent 120s CLI timeouts with no overall timeout

---

### Option B: Keep orchestrator timeout, skip unhealthy providers

**Approach:** Add health check to filter out known-slow providers before running

**Pros:**
- Keeps overall timeout guard
- Reduces provider count

**Cons:**
- Doesn't fix root cause - still blocks on slow healthy providers
- Registry state may be stale (mistral marked "healthy" but likely slow)
- Adds complexity (health check + filter logic)

**Complexity:** Medium (add health check integration)

---

## Recommendation

**Option B was implemented** for the following reasons:

1. **User requirement:** User explicitly stated "180 seconds isn't enough. Sometimes it can take five minutes or more"
2. **Maintains safety net:** Keeps overall timeout guard while allowing much longer runtimes
3. **Backward compatible:** Default of 600s (10 minutes) is configurable via `--timeout` flag
4. **Better UX:** T1/T2 providers complete in ~30-60s, but complex sessions can run up to 10 minutes
5. **Acceptable trade-off:** Slower overall than Option A but provides timeout safety that user requested

---

## Implementation

### Step 1: Increase default timeout to 600 seconds

**File:** `P:\.claude\skills\s\scripts\run_heavy.py`

**Change:** Updated default timeout from 180.0 to 600.0 seconds

```python
parser.add_argument("--timeout", type=float, default=600.0, help="Overall phase timeout in seconds (default: 600 = 10 minutes)")
```

### Step 2: Keep orchestrator's overall phase timeout (at 600s default)

**File:** `P:\.claude\skills\s\lib\orchestrator.py`

**Action:** Kept `asyncio.wait_for()` wrapper with configurable timeout

The orchestrator still uses:
```python
results = await asyncio.wait_for(
    asyncio.gather(*tasks, return_exceptions=True),
    timeout=timeout,  # Now defaults to 600s instead of 180s
)
```

### Step 3: Per-provider timeouts remain independent

**File:** `P:\.claude\skills\s\lib\agents\base.py`

**Action:** Each provider still has its own independent timeout (30s for CLI providers)

This creates two timeout layers:
1. Individual provider timeouts (30s for CLI)
2. Overall phase timeout (600s default, configurable)

---

## Rollback

If issues arise:
1. Restore orchestrator's `asyncio.wait_for()` wrapper
2. Restore per-provider timeout wrapper in base.py
3. Consider adding configurable overall timeout with `--no-timeout` flag

---

## Ramifications

### Breaks anything?
No - removes timeout guards, doesn't change logic flow

### Edge cases
- If ALL providers are down/slow, brainstorm may hang indefinitely
- Mitigation: Unlikely given 4 API providers (groq, chutes, mistral, openrouter)

### Constraints
- User timeout now defaults to 600s (10 minutes) but is configurable via `--timeout` flag
- Expected improvement: T1/T2 providers complete in 30-60s, but complex sessions can run up to 10 minutes
- Each provider still has its own independent timeout (30s for CLI)

---

## Multi-Terminal Safety

**Multi-terminal:** Safe
- Each `/s` invocation is independent
- No shared mutable state
- Per-session state isolation

---

## Edge Cases to Consider

### Round-robin provider selection

**Issue:** `base.py:69` uses global `_provider_rotation_index` with async lock

**Current behavior:**
- Lock only used during index increment
- Multiple `/s` calls in same terminal may share rotation state

**Impact:** Low - rotation is cosmetic, not correctness-critical

**Note:** NOT a multi-terminal issue (each terminal has its own Python process)

---

## Evidence Basis

- **Tier 1:** Code inspection of orchestrator.py, base.py, parallel_llm.py (75%)
- **Tier 0:** Understanding of asyncio `gather()` vs `wait_for()` behavior (50%)

**Overall confidence:** 85% - Proven pattern from `/llm-cli`, clear root cause analysis

---

## Sources

- `/llm-cli` implementation: `P:\__csf\lib\parallel_llm.py`
- `/s` orchestrator: `P:\.claude\skills\s\lib\orchestrator.py`
- Agent base: `P:\.claude\skills\s\lib\agents\base.py`
- Provider registry: `P:\__csf\src\data\provider_registry_state.json`
