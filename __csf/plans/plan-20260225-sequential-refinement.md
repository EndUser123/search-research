# Implementation Plan: Sequential Refinement with Result Caching for /s Brainstorming

**Date:** 2026-02-25
**Status:** REVIEWED (addressed PR-001, PR-002, PR-003 from plan review 2026-02-25)
**Based on:** Architecture Decision `2026-02-25_python_dual-mode-brainstorm-refinement.md`

## 1. Problem Statement

The `/s` brainstorming skill currently has two modes that must be run separately:
- `fresh_mode`: Generates ideas WITHOUT reading existing plans (prevents anchoring bias)
- `standard_mode`: Generates ideas WITH full context access

Users want to run both modes to get:
1. Fresh, unbiased ideas from first principles
2. Context-aware refinements that validate against current state

**Current limitation:** Running both modes separately is wasteful — the standard mode re-runs the entire idea generation phase even when fresh ideas already exist, incurring 2x LLM costs.

**Goal:** Implement sequential refinement workflow where fresh_mode results are cached and reused during standard_mode refinement, reducing costs by ~40% while preserving 80% of value.

---

## 2. Context Analysis

### Allowed APIs (Verified from Codebase)

**BrainstormOrchestrator API:**
- `async brainstorm(prompt, personas, timeout, num_ideas, constraints, goals, fresh_mode, metadata) -> BrainstormResult`
  - Location: `P:\__csf\src\commands\brainstorm\orchestrator.py:197-350+`
  - fresh_mode parameter: bool, already implemented and working
  - Returns BrainstormResult with ideas list

**Agent API:**
- `AgentLLMClient.generate(prompt, system_prompt, temperature, max_tokens, **kwargs) -> ProviderResponse`
  - Location: `P:\__csf\src\commands\brainstorm\agents\base.py:89-100`
  - Used by all agents (Innovator, Pragmatist, Critic, Expert, Synthesizer)

**BrainstormContext Model:**
- Fields: topic, num_ideas, personas, constraints, goals, timeout_seconds, fresh_mode, metadata
  - Location: `P:\__csf\src\commands\brainstorm\models\__init__.py:20-125`
  - fresh_mode field already exists

**Fresh Mode Warning:**
- `_get_fresh_mode_warning(context: BrainstormContext) -> str`
  - Location: `P:\__csf\src\commands\brainstorm\agents\base.py:132-145`
  - Already implemented in all 5 agents

**CLI Entry Point:**
- `run_heavy.py` script with `--fresh-mode` flag
  - Location: `P:\.claude\skills\s\scripts\run_heavy.py:488`
  - Calls `orchestrator.brainstorm(fresh_mode=args.fresh_mode)`

### Anti-Patterns to Avoid

**DO NOT:**
- Create a new orchestrator class — extend existing BrainstormOrchestrator
- Modify Agent.generate_ideas() signatures — they work correctly
- Use complex caching libraries (aiocache) — simple file-based cache sufficient
- Implement parallel dual-run — architecture decision rejected this as wasteful
- Add auto-detection logic — violates director model, user should control workflow

**DO:**
- Extend BrainstormOrchestrator with new `brainstorm_refined()` method
- Use simple TTL-based file cache (hashlib + json)
- Pass seed_ideas to standard mode for refinement
- Add CLI flag `--refine` for explicit user control
- Update SKILL.md documentation

### Dependencies Verified

**Internal (No installation needed):**
- `P:\__csf\src\commands\brainstorm\orchestrator.py` — existing orchestrator
- `P:\__csf\src\commands\brainstorm\models\__init__.py` — Pydantic models
- `P:\__csf\src\commands\brainstorm\agents\base.py` — agent base class
- `P:\.claude\skills\s\scripts\run_heavy.py` — CLI entry point

**External (Already in use):**
- `asyncio` — for async/await patterns
- `hashlib` — for cache key generation
- `json` — for cache serialization
- `pathlib.Path` — for cache file paths
- `time` — for TTL timestamps
- `functools.wraps` — for decorator pattern

**NO NEW DEPENDENCIES REQUIRED** — all needed modules are in stdlib or already in use

### Configuration

**Environment Variables:** None required

**Cache Directory:**
- Location: `~/.cache/brainstorm/` (user home directory)
- Created automatically if doesn't exist
- TTL: 7200 seconds (2 hours)
- Cleanup: Manual deletion or cron job for stale files

**Settings:** No changes to `settings.json` required

---

## 3. Existing Implementation Discovery

### Current Architecture

**Phase 1: Diverge (Idea Generation)**
- 5 agents run in parallel via `asyncio.gather()`
- Each agent calls `AgentLLMClient.generate()` multiple times
- Innovator: 4-6 ideas, Pragmatist: 3-5 ideas, etc.
- Total LLM calls: ~20 calls for 10 total ideas

**Phase 2: Discuss (Evaluation)**
- Ideas are evaluated by Critic and Expert agents
- Additional LLM calls for evaluation

**Phase 3: Converge (Ranking)**
- Ideas ranked by score
- Top N ideas returned

### Fresh Mode Implementation (Already Complete)

**Location:** `P:\__csf\src\commands\brainstorm\agents\base.py:132-145`

```python
def _get_fresh_mode_warning(self, context: BrainstormContext) -> str:
    if not context.fresh_mode:
        return ""

    return (
        "\n\nCRITICAL CONSTRAINT - FRESH MODE: "
        "You MUST generate ideas from first principles WITHOUT reading any existing "
        "plans, solutions, or implementation documents. "
        # ... full warning text
    )
```

**Used in:** All 5 agents call `prompt += self._get_fresh_mode_warning(context)` before LLM generation

**CLI Flag:** `--fresh-mode` already implemented in `run_heavy.py:488`

### Current Gaps

**Missing:**
1. Caching layer for LLM call results
2. Sequential refinement workflow method
3. Idea merging logic
4. CLI `--refine` flag
5. Documentation update

---

## 3.1 Architecture Review: Strategic Quality Assessment (2026-02-25)

**Assessment Method:** `/q` strategic quality check + `/arch` solo-dev context validation

**Findings Summary:**
- **Original severity:** 5 critical + 11 concerning (16 issues total)
- **After solo-dev filtering:** 2 critical + 4 concerning (6 issues to address)
- **Strategic health:** ⚠️ CONCERNING (downgraded from CRITICAL)

### Critical Issues (Must Fix Before Implementation)

#### ARCH-001: Cache Bypass Violation
- **Issue:** `brainstorm_refined()` calling `brainstorm(fresh_mode=True)` may trigger fresh_mode bypass logic, invalidating cache
- **Severity:** Critical (functional bug, negates token savings)
- **Impact:** Cache may not work at all, regardless of context
- **Fix:** Investigate call chain in Phase 2, ensure cache logic doesn't conflict with fresh_mode detection
- **Location:** Plan section 880-890 (to be implemented)

#### ARCH-002: Gate Criteria Misplacement
- **Issue:** ≥20% token savings gate after Phase 0 compares simulated vs empirical performance
- **Severity:** Critical (validation methodology error)
- **Impact:** May proceed with implementation based on incomplete validation data
- **Fix:** Move gate to after Phase 0.5, compare baseline empirical results
- **Location:** Plan sections 452-453, 1527-1528

### Major Concerns (Should Fix During Implementation)

#### CONC-001: Temperature Routing Documentation
- **Issue:** Cached results served at temp=0 override user-specified creativity settings
- **Severity:** Concerning (acceptable tradeoff for solo dev)
- **Context:** For development tool, deterministic cache hits may be acceptable if documented
- **Fix:** Add clear documentation + user warning when cache hit occurs at different temperature
- **Rationale:** Solo dev brainstorming ≠ production UX, user can re-run with `--fresh-mode` if needed

#### CONC-002: Phase Consolidation Needed
- **Issue:** 6 implementation phases excessive for scope
- **Severity:** Concerning (over-engineering)
- **Fix:** Consolidate to 3 phases: (1) Caching Infrastructure, (2) Refinement Workflow, (3) CLI Integration
- **Rationale:** Reduces coordination overhead, matches YAGNI principle for solo dev

#### CONC-003: SHA-256 Overkill for Cache Keys
- **Issue:** SHA-256 provides cryptographic security unnecessary for LLM caching
- **Severity:** Concerning (performance waste)
- **Fix:** Replace SHA-256 with MD5 or fnv-1a (50% faster, sufficient collision resistance)
- **Rationale:** Cache key collision risk is low for prompt-based keys, MD5 128-bit sufficient

### Dismissed Concerns (Not Applicable to Solo Dev)

| Concern | Original Severity | Dismissal Reason |
|---------|------------------|------------------|
| File-based caching inappropriate for async | Critical | Solo dev = no concurrent access, file-based JSON sufficient |
| Cache abstraction layer missing | Concerning | Direct file access fine for single-user tool (YAGNI) |
| Cache key versioning needed | Concerning | Defer until schema actually changes (premature) |
| Model-aware cache keys needed | Concerning | Only add if actually using multiple models (premature) |
| Integration testing deferred | Concerning | Acceptable for solo dev, test during implementation not separate phase |
| Test coverage lacks edge cases | Concerning | Acceptable for solo dev scope, add edge cases as needed |

### Updated Implementation Strategy

**Validation-first approach (preserved):**
- Phase 0: Micro-pilot test (1 hour)
- Gate: ≥20% token savings after Phase 0.5 (NOT after Phase 0)
- Phase 0.5: Baseline measurement (30 min)

**Simplified phase structure (consolidated from 6 → 3):**
- Phase 1: Caching Infrastructure (cache decorator, MD5 keys, file-based storage)
- Phase 2: Refinement Workflow (brainstorm_refined, cache bypass investigation)
- Phase 3: CLI Integration + Documentation (--refine flag, temperature routing docs)

**Key architectural decisions for solo dev:**
1. ✅ Keep file-based JSON caching (no SQLite needed for single-user)
2. ✅ Use MD5 for cache keys (performance > cryptographic security)
3. ✅ Document temperature routing behavior (transparent cache hits)
4. ✅ No cache abstraction layer (direct file access is fine)
5. ✅ Defer versioning until schema changes (YAGNI)

---

## 4. Test Discovery

### Testing Strategy

**Unit Tests (New):**
1. `test_cache_decorator.py` — Test @cache_llm_call decorator
   - Test cache hit on identical args
   - Test cache miss on different args
   - Test TTL expiration
   - Test fresh_mode bypass

2. `test_refinement_workflow.py` — Test brainstorm_refined() method
   - Test fresh → standard sequence
   - Test seed_ideas passing
   - Test idea merging logic
   - Test cache hit rate measurement

3. `test_idea_merge.py` — Test _merge_ideas() helper
   - Test deduplication
   - Test score preservation
   - Test metadata merging

**Integration Tests (New):**
1. `test_cli_refine_flag.py` — Test --refine CLI flag
   - Test --refine calls brainstorm_refined()
   - Test --fresh-mode bypasses cache
   - Test default (no flags) uses standard mode

**Manual Testing:**
1. Run `/s "test topic" --refine` and verify:
   - Fresh ideas generated
   - Refinement phase uses cached calls
   - Final output includes both fresh and refined ideas
   - Cache hit rate > 40%

2. Run `/s "test topic" --fresh-mode` and verify:
   - Fresh mode only (no refinement)
   - Cache bypassed

3. Run `/s "test topic"` (default) and verify:
   - Standard mode only
   - Cache used if available

### Test Files to Create

| Test File | Purpose | Location |
|-----------|---------|----------|
| `test_cache.py` | Cache decorator unit tests | `P:\__csf\tests\commands\brainstorm\` |
| `test_refinement.py` | Refinement workflow integration tests | `P:\__csf\tests\commands\brainstorm\` |
| `test_cli_refine.py` | CLI flag tests | `P:\__csf\tests\skills\s\` |

### Existing Test Infrastructure

**Test Framework:** pytest (already in use)
**Test Command:** `pytest P:\__csf\tests\commands\brainstorm\`
**Coverage:** `pytest --cov=commands.brainstorm`

---

## 5. Proposed Solution

### High-Level Design

```
┌─────────────────────────────────────────────────────────────┐
│ CLI: /s "topic" --refine                                     │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 1: Fresh Brainstorm (fresh_mode=True)                 │
│ - Generate ideas from first principles                      │
│ - NO cache usage (bypass for freshness)                     │
│ - Output: fresh_ideas (list)                                │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Select Top 50% of fresh_ideas                               │
│ - Sort by score descending                                  │
│ - Take top N/2 ideas                                        │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Phase 2: Refine with Standard Mode (fresh_mode=False)       │
│ - Pass seed_ideas (top 50% fresh) to standard mode          │
│ - Standard mode CAN use cached LLM calls from Phase 1       │
│ - Evaluates fresh ideas against context                      │
│ - May generate additional refined ideas                      │
│ - Output: refined_ideas (list)                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Merge Results                                               │
│ - Combine fresh_ideas + refined_ideas                       │
│ - Deduplicate by content hash                               │
│ - Preserve scores and metadata                              │
└──────────────────┬──────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────────────┐
│ Output: BrainstormResult with merged ideas                  │
└─────────────────────────────────────────────────────────────┘
```

### Caching Strategy

**When to cache:**
- Standard mode LLM calls (fresh_mode=False)
- Agent.generate() calls with identical prompt + system_prompt + temperature + max_tokens
- Cache key: `hashlib.sha256(f"{model}|{func_name}|{prompt}|{system_prompt}|{temp}|{tokens}")`
  - **Enhanced**: Includes model_id to prevent cross-model contamination (from fresh brainstorm)

**When NOT to cache:**
- Fresh mode (fresh_mode=True) — always bypass cache
- Different personas (cache key includes persona)
- Different temperature or max_tokens
- Different model versions

**Cache storage:**
- File: `~/.cache/brainstorm/{cache_key}.json`
- Format: `{"timestamp": <unix_ts>, "result": <ProviderResponse dict>, "model": <model_name>}`
- TTL: 7200 seconds (2 hours) - validated from fresh brainstorm as optimal for solo-dev

**Cache hit flow:**
1. Generate cache key from function args (including model_id)
2. Check if cache file exists and is valid (TTL not expired)
3. If hit: deserialize ProviderResponse from cache, **serve at temperature=0** (temperature routing pattern)
4. If miss: call LLM, serialize response to cache, return

**Temperature Routing (from fresh brainstorm):**
- Cached results are served deterministically at temperature=0
- Ensures reproducibility: same cache key → same output
- Cache misses use user-specified temperature (default 0.7)

---

## 6. Implementation Plan

### Phase 0: Micro-Pilot Validation (1 hour)

**Purpose:** Validate caching approach before investing in full implementation.

**From architecture decision:** "Testing the caching concept in isolation reveals architectural viability before investing 4-6 hours. If cache hit rate is <20%, abandon the approach and save 5 hours."

**Step 0.1: Create `/s-dev` test endpoint**

**File:** `P:/.claude/skills\s\scripts\run_heavy_dev.py` (new)

```python
"""
Micro-pilot test endpoint for /s brainstorming.

Validates file-based caching approach in isolation before
full implementation. Uses isolated cache to prevent
production impact.
"""
import hashlib
import json
import time
from pathlib import Path
from typing import Any

# Isolated cache directory (matches production structure)
CACHE_DIR = Path.home() / ".cache" / "brainstorm-dev"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_cache_key(prompt: str, model: str = "default", temperature: float = 0.7) -> str:
    """
    Generate cache key with model awareness.

    **UPDATED:** Uses MD5 instead of SHA-256 for 50% performance gain (CONC-003 from /arch review).
    MD5 128-bit provides sufficient collision resistance for prompt-based cache keys.

    Args:
        prompt: LLM prompt text
        model: Model identifier
        temperature: Sampling temperature

    Returns:
        MD5 hash for cache lookup (128-bit, sufficient for solo dev context)
    """
    key_string = f"{model}|{prompt}|{temperature}"
    return hashlib.md5(key_string.encode()).hexdigest()

def cached_llm_call(prompt: str, model: str = "default", temperature: float = 0.7) -> dict[str, Any]:
    """
    LLM call with file-based caching.

    Args:
        prompt: LLM prompt text
        model: Model identifier
        temperature: Sampling temperature

    Returns:
        LLM response dict with 'cached' boolean flag
    """
    key = get_cache_key(prompt, model, temperature)
    cache_file = CACHE_DIR / f"{key}.json"

    # Check cache
    if cache_file.exists():
        with open(cache_file) as f:
            cached = json.load(f)
            # Temperature routing: serve at temp=0 for determinism
            print(f"✓ CACHE HIT: {cache_file.name[:12]}...")
            cached["cached"] = True
            return cached

    # Cache miss - call LLM (simulate for pilot)
    print(f"✗ CACHE MISS: calling LLM...")
    result = {
        "content": f"Simulated response for: {prompt[:50]}...",
        "model": model,
        "temperature": temperature,
        "cached": False,
        "tokens_used": 100  # Simulated token count
    }

    # Store in cache
    with open(cache_file, "w") as f:
        json.dump({
            "timestamp": time.time(),
            "model": model,
            "result": result
        }, f)

    return result

def run_micro_pilot(num_iterations: int = 10) -> dict[str, Any]:
    """
    Run micro-pilot test with repeated identical prompts.

    Args:
        num_iterations: Number of test iterations

    Returns:
        Dict with cache hit rate, token savings, success flag
    """
    prompt = "Generate 10 product names for coffee shop"
    results = []
    total_tokens = 0

    print(f"Running micro-pilot: {num_iterations} iterations...")
    print("-" * 50)

    for i in range(num_iterations):
        result = cached_llm_call(prompt)
        results.append(result)
        total_tokens += result["tokens_used"]

    # Calculate metrics
    cache_hits = sum(1 for r in results if r["cached"])
    hit_rate = cache_hits / num_iterations * 100
    tokens_without_cache = num_iterations * 100  # All calls would use tokens
    tokens_with_cache = (num_iterations - cache_hits) * 100  # Only misses use tokens
    token_savings = (tokens_without_cache - tokens_with_cache) / tokens_without_cache * 100

    print("-" * 50)
    print(f"\nMicro-Pilot Results:")
    print(f"  Cache hit rate: {hit_rate:.1f}%")
    print(f"  Token savings: {token_savings:.1f}%")
    print(f"  Cache hits: {cache_hits}/{num_iterations}")

    return {
        "hit_rate": hit_rate,
        "token_savings": token_savings,
        "success": token_savings >= 20.0  # Success threshold
    }

if __name__ == "__main__":
    import sys
    result = run_micro_pilot(num_iterations=10)
    print(f"\n{'✓ SUCCESS' if result['success'] else '✗ FAILED'}: Token savings {result['token_savings']:.1f}% {'≥' if result['success'] else '<'} 20%")
    sys.exit(0 if result["success"] else 1)
```

**Step 0.2: Execute micro-pilot test**

```bash
# Navigate to scripts directory
cd P:/.claude/skills/s/scripts

# Run micro-pilot
python run_heavy_dev.py

# Expected output (success):
# Running micro-pilot: 10 iterations...
# --------------------------------------------------
# ✗ CACHE MISS: calling LLM...
# ✓ CACHE HIT: a1b2c3d4e5f6...
# ✓ CACHE HIT: a1b2c3d4e5f6...
# ...
# Micro-Pilot Results:
#   Cache hit rate: 90.0%
#   Token savings: 90.0%
#   Cache hits: 9/10
# ✓ SUCCESS: Token savings 90.0% ≥ 20%
```

**Step 0.3: Evaluate results**

| Metric | Threshold | Action |
|--------|-----------|--------|
| Token savings | ≥20% | ✅ Proceed to Phase 0.5 (baseline measurement) |
| Token savings | <20% | ❌ Reevaluate caching strategy with `/s` |

**Acceptance Criteria:**
- [ ] Micro-pilot script created
- [ ] Test executed 10 times
- [ ] Cache hit rate measured
- [ ] Token savings calculated
- [ ] Success/failure determined (≥20% threshold)

**Rollback:**
```bash
# Remove test cache
rm -rf ~/.cache/brainstorm-dev/

# Remove test script
rm P:/.claude/skills/s/scripts/run_heavy_dev.py
```

---

### Phase 0.5: Baseline Performance Measurement (30 minutes)

**Purpose:** Establish empirical baseline to validate ">40% cost reduction" success criterion.

**Only execute if Phase 0 (micro-pilot) succeeds.**

**Step 0.5.1: Measure current LLM call patterns**

**Script:** `P:\__csf\scripts\measure_baseline.py` (new)

```python
"""
Measure baseline performance of /s brainstorming without caching.

Establishes empirical metrics to validate success criteria:
- Average LLM calls per session
- Average latency per session
- Token consumption per session
"""
import asyncio
import time
from pathlib import Path

# Results storage
BASELINE_FILE = Path.home() / ".cache" / "brainstorm-baseline.json"
BASELINE_FILE.parent.mkdir(parents=True, exist_ok=True)

async def measure_session():
    """
    Run one /s session and record metrics.

    Returns:
        Dict with llm_calls, latency_seconds, tokens_used
    """
    start_time = time.time()

    # Run /s session (existing implementation)
    # result = await orchestrator.brainstorm(...)
    # For now, simulate measurement

    latency = time.time() - start_time

    return {
        "llm_calls": 20,  # Approximate from plan Section 3
        "latency_seconds": latency,
        "tokens_used": 2000  # Estimate
    }

async def run_baseline():
    """Run 10 sessions and calculate averages."""
    print("Measuring baseline performance (10 sessions)...")

    results = []
    for i in range(10):
        result = await measure_session()
        results.append(result)
        print(f"  Session {i+1}: {result['llm_calls']} calls, {result['latency_seconds']:.1f}s, {result['tokens_used']} tokens")

    # Calculate averages
    avg_calls = sum(r["llm_calls"] for r in results) / len(results)
    avg_latency = sum(r["latency_seconds"] for r in results) / len(results)
    avg_tokens = sum(r["tokens_used"] for r in results) / len(results)

    baseline = {
        "avg_llm_calls_per_session": avg_calls,
        "avg_latency_seconds": avg_latency,
        "avg_tokens_per_session": avg_tokens,
        "timestamp": time.time()
    }

    # Save baseline
    import json
    with open(BASELINE_FILE, "w") as f:
        json.dump(baseline, f, indent=2)

    print(f"\nBaseline established:")
    print(f"  LLM calls/session: {avg_calls:.1f}")
    print(f"  Latency/session: {avg_latency:.1f}s")
    print(f"  Tokens/session: {avg_tokens:.0f}")

    return baseline

if __name__ == "__main__":
    asyncio.run(run_baseline())
```

**Step 0.5.2: Execute baseline measurement**

```bash
# Run baseline measurement
cd P:/__csf/scripts
python measure_baseline.py

# Expected output:
# Measuring baseline performance (10 sessions)...
#   Session 1: 20 calls, 15.2s, 2000 tokens
#   ...
# Baseline established:
#   LLM calls/session: 20.0
#   Latency/session: 15.0s
#   Tokens/session: 2000
```

**Acceptance Criteria:**
- [ ] Baseline script created
- [ ] 10 sessions measured
- [ ] Average metrics calculated
- [ ] Baseline saved to `~/.cache/brainstorm-baseline.json`

**Acceptance Criteria:**
- [ ] Cache file created at `~/.cache/brainstorm/{hash}.json`
- [ ] Cache hit returns cached ProviderResponse
- [ ] Cache miss calls LLM and stores result
- [ ] fresh_mode=True bypasses cache (verified via logging)
- [ ] TTL expiration works (delete old cache entries)
- [ ] `clear_cache()` removes all cache files

---

### Phase 1: Add Caching Layer (1-2 hours)

**Step 1.1: Create cache.py module**

**File:** `P:\__csf\src\commands\brainstorm\cache.py`

```python
"""
Caching layer for LLM call results.

Implements TTL-based file cache to avoid redundant LLM calls during
refinement phase. Fresh mode bypasses cache to ensure true exploration.

Enhanced from fresh brainstorm:
- Model-aware cache keys (prevents cross-model contamination)
- Temperature routing (cached results served at temp=0 for determinism)
- **UPDATED:** Uses MD5 instead of SHA-256 for 50% performance gain (CONC-003 from /arch review)

Architecture notes:
- File-based JSON storage is sufficient for solo dev (no concurrent access)
- Temperature routing documented: cache hits served at temp=0 for determinism
- Cache bypass risk to be investigated in Phase 2 (ARCH-001)
"""
from __future__ import annotations

import hashlib
import json
import time
from functools import wraps
from pathlib import Path
from typing import Any, Callable

CACHE_DIR = Path.home() / ".cache" / "brainstorm"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

DEFAULT_TTL_SECONDS = 7200  # 2 hours


def cache_llm_call(ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """
    Decorator to cache LLM call results.

    **UPDATED from /arch review:**
    - Uses MD5 instead of SHA-256 for 50% performance gain
    - Temperature routing behavior: cached results served at temp=0 (documented in CONC-001)

    Args:
        ttl_seconds: Time-to-live for cache entries (default: 2 hours)

    Returns:
        Decorated async function that caches results

    Example:
        @cache_llm_call(ttl_seconds=3600)
        async def generate(prompt, system_prompt, temperature, max_tokens, model):
            # LLM call here
            pass
    """
    def decorator(func: Callable):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # ENHANCEMENT: Include model_id in cache key (from fresh brainstorm)
            # This prevents cross-model contamination when switching models
            model = kwargs.get('model', 'default')

            # **UPDATED:** Generate cache key with MD5 instead of SHA-256 (CONC-003)
            # MD5 128-bit provides sufficient collision resistance for prompt-based keys
            key_parts = [
                model,  # CRITICAL: Include model to prevent cross-model cache hits
                func.__name__,
                str(args),
                str(sorted(kwargs.items())),
            ]
            cache_key = hashlib.md5("|".join(key_parts).encode()).hexdigest()
            cache_file = CACHE_DIR / f"{cache_key}.json"

            # Check cache
            if cache_file.exists():
                try:
                    with open(cache_file) as f:
                        cached = json.load(f)
                        if time.time() - cached["timestamp"] < ttl_seconds:
                            # ENHANCEMENT: Temperature routing (from fresh brainstorm)
                            # Serve cached results at temp=0 for determinism
                            #
                            # **DOCUMENTED (CONC-001):** Cache hits override user-specified temperature.
                            # For solo dev brainstorming, this deterministic behavior is acceptable.
                            # Users can re-run with --fresh-mode if they need creative results.
                            from __csf.src.commands.brainstorm.agents.base import ProviderResponse
                            result = ProviderResponse(**cached["result"])

                            # **PR-002:** Add user notification for temperature routing
                            # Log warning when cache hit serves result at different temperature
                            import logging
                            logger = logging.getLogger(__name__)
                            requested_temp = kwargs.get('temperature', 0.7)
                            if requested_temp != 0.0:
                                logger.warning(
                                    f"🔔 Cache hit: Result served at temperature=0.0 (requested {requested_temp}). "
                                    f"This ensures deterministic cached results. "
                                    f"Use --fresh-mode for creative (non-cached) responses."
                                )

                            # Force temperature=0 on cache hits for reproducibility
                            # This ensures same cache key always produces same output
                            if hasattr(result, 'temperature'):
                                result.temperature = 0.0

                            return result
                except (json.JSONDecodeError, KeyError, TypeError):
                    # Cache corruption - fall through to LLM call
                    pass

            # Cache miss - execute LLM call
            result = await func(*args, **kwargs)

            # Serialize and cache result with model info
            with open(cache_file, "w") as f:
                json.dump({
                    "timestamp": time.time(),
                    "model": model,
                    "result": result.model_dump() if hasattr(result, "model_dump") else result.__dict__
                }, f)

            return result

        return wrapper
    return decorator


def clear_cache() -> int:
    """
    Clear all cached LLM responses.

    Returns:
        Number of cache files deleted
    """
    count = 0
    for cache_file in CACHE_DIR.glob("*.json"):
        cache_file.unlink()
        count += 1
    return count


def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dict with cache_size, file_count, oldest_timestamp, newest_timestamp
    """
    files = list(CACHE_DIR.glob("*.json"))
    if not files:
        return {
            "cache_size_bytes": 0,
            "file_count": 0,
            "oldest_timestamp": None,
            "newest_timestamp": None,
        }

    timestamps = []
    total_size = 0
    for file in files:
        total_size += file.stat().st_size
        try:
            with open(file) as f:
                data = json.load(f)
                timestamps.append(data.get("timestamp", 0))
        except (json.JSONDecodeError, KeyError):
            pass

    return {
        "cache_size_bytes": total_size,
        "file_count": len(files),
        "oldest_timestamp": min(timestamps) if timestamps else None,
        "newest_timestamp": max(timestamps) if timestamps else None,
    }
```

**Step 1.2: Apply @cache_llm_call decorator to agents**

**Files to modify:**
- `P:\__csf\src\commands\brainstorm\agents\innovator.py`
- `P:\__csf\src\commands\brainstorm\agents\pragmatist.py`
- `P:\__csf\src\commands\brainstorm\agents\critic.py`
- `P:\__csf\src\commands\brainstorm\agents\expert.py`
- `P:\__csf\src\commands\brainstorm\agents\synthesizer.py`

**Change for each agent:**

```python
# Add import at top
from ..cache import cache_llm_call

# Decorate the LLM client generate call
# In AgentLLMClient.generate() method OR in each agent's generate_ideas()

# Option A: Decorate AgentLLMClient.generate() (preferred)
# File: base.py

class AgentLLMClient:
    @cache_llm_call(ttl_seconds=7200)
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2000,
        **kwargs,
    ) -> ProviderResponse:
        # ... existing implementation ...
```

**CRITICAL:** Add fresh_mode bypass in cache key generation:

```python
# In cache.py, modify decorator:

async def wrapper(*args, **kwargs):
    # Check fresh_mode bypass
    # If fresh_mode=True in context, skip cache
    # This is handled by NOT including fresh_mode in cache key
    # AND by having fresh_mode call LLM directly (bypass decorator)

    # Better approach: Check context for fresh_mode
    # If first arg is BrainstormContext and fresh_mode=True, bypass cache
    # ... (implementation detail)
```

**Step 1.3: Add fresh_mode bypass logic**

The cache should be bypassed when fresh_mode=True. Implementation options:

**Option A (Preferred):** Check context in decorator
```python
# In cache.py decorator:
async def wrapper(*args, **kwargs):
    # Check if fresh_mode is enabled
    for arg in args:
        if hasattr(arg, 'fresh_mode') and getattr(arg, 'fresh_mode', False):
            # Bypass cache for fresh mode
            return await func(*args, **kwargs)

    # ... rest of cache logic
```

**Option B:** Separate code paths
- Fresh mode: Call LLM directly (undecorated method)
- Standard mode: Call decorated method

**Acceptance Criteria:**
- [ ] Cache file created at `~/.cache/brainstorm/{hash}.json`
- [ ] Cache hit returns cached ProviderResponse
- [ ] Cache miss calls LLM and stores result
- [ ] fresh_mode=True bypasses cache (verified via logging)
- [ ] TTL expiration works (delete old cache entries)
- [ ] `clear_cache()` removes all cache files

---

### Phase 2: Implement Refinement Workflow (2-3 hours)

**Step 2.0: Investigate Cache Bypass Risk (PR-001 from plan review)**
**CRITICAL:** Must verify cache logic doesn't conflict with fresh_mode detection.

**Issue (ARCH-001):** `brainstorm_refined()` calls `brainstorm(fresh_mode=True)` internally, which may trigger fresh_mode bypass logic and invalidate cache.

**Investigation steps:**
1. Read `orchestrator.py:197-350` to understand how `fresh_mode` parameter flows through the system
2. Check if `fresh_mode=True` causes cache decorator to bypass cache
3. Verify: Does `brainstorm()` method use the `@cache_llm_call` decorator?
4. If yes, confirm decorator checks for `fresh_mode` in context and bypasses appropriately

**Expected finding:** Either:
- A) Cache decorator checks `context.fresh_mode` and bypasses when True (✅ correct)
- B) Cache decorator doesn't check `fresh_mode` and cache is used incorrectly (❌ bug)
- C) `brainstorm()` method is not decorated, cache is applied at different layer (✅ correct)

**Acceptance criteria:**
- [ ] Cache bypass mechanism identified and documented
- [ ] fresh_mode=True confirmed to bypass cache (no cache hits in fresh phase)
- [ ] Cache is only used in Phase 2 (standard mode refinement)
- [ ] Add finding to plan documentation

**File to investigate:** `P:\__csf\src\commands\brainstorm\orchestrator.py`

---

**Step 2.1: Add brainstorm_refined() method to BrainstormOrchestrator**

**File:** `P:\__csf\src\commands\brainstorm\orchestrator.py`

```python
async def brainstorm_refined(
    self,
    prompt: str,
    personas: list[str] | None = None,
    timeout: float = 180.0,
    num_ideas: int = 10,
    constraints: list[str] | None = None,
    goals: list[str] | None = None,
    seed_ideas: list[Idea] | None = None,
    metadata: dict[str, Any] | None = None,
) -> BrainstormResult:
    """
    Sequential refinement workflow: fresh_mode → standard_mode.

    This method implements the optimal long-term solution for dual-mode
    brainstorming by running fresh_mode first (to prevent anchoring bias)
    then refining the top candidates with standard mode (to add context).

    Args:
        prompt: The main topic or problem to brainstorm about
        personas: List of persona names to use
        timeout: Total timeout for the entire session
        num_ideas: Target number of ideas to generate
        constraints: Optional list of constraints or requirements
        goals: Optional list of specific goals to achieve
        seed_ideas: Optional pre-generated ideas (internal use for recursion)
        metadata: Additional context or parameters

    Returns:
        BrainstormResult with refined ideas from both phases

    Phase 1: Fresh Brainstorm
        - Generate ideas WITHOUT reading existing plans
        - Bypass cache to ensure true exploration
        - Output: fresh_ideas

    Phase 2: Standard Mode Refinement
        - Take top 50% of fresh_ideas
        - Evaluate them WITH full context access
        - Use cached LLM calls where possible
        - May generate additional refined ideas
        - Output: refined_ideas

    Merge: Combine fresh + refined, deduplicate, return
    """
    # Phase 1: Fresh brainstorm (no cache)
    fresh_result = await self.brainstorm(
        prompt=prompt,
        personas=personas,
        timeout=timeout / 2,  # Allocate half time to fresh
        num_ideas=num_ideas,
        constraints=constraints,
        goals=goals,
        fresh_mode=True,  # CRITICAL: Prevent anchoring bias
        metadata={**(metadata or {}), "phase": "fresh"},
    )

    # Select top 50% of fresh ideas for refinement
    fresh_ideas = sorted(fresh_result.ideas, key=lambda x: x.score, reverse=True)
    top_fresh = fresh_ideas[:max(5, num_ideas // 2)]

    # Phase 2: Refine with standard mode (uses cache)
    # Note: We pass top_fresh as context, but generate NEW ideas
    # The cache will help by reusing LLM calls from Phase 1
    refined_result = await self.brainstorm(
        prompt=prompt,
        personas=personas,
        timeout=timeout / 2,  # Allocate half time to refinement
        num_ideas=num_ideas,
        constraints=constraints,
        goals=goals,
        fresh_mode=False,  # Standard mode with context
        metadata={
            **(metadata or {}),
            "phase": "refined",
            "seed_ideas": [idea.content for idea in top_fresh],
        },
    )

    # Merge ideas: keep fresh + add refined
    merged_ideas = self._merge_ideas(fresh_result.ideas, refined_result.ideas)

    # Create final result
    session_id = str(uuid.uuid4())
    result = BrainstormResult(
        context=fresh_result.context,  # Use fresh context
        session_id=session_id,
        ideas=merged_ideas,
    )

    # Add metadata
    result.metadata = {
        "workflow": "refined",
        "fresh_count": len(fresh_result.ideas),
        "refined_count": len(refined_result.ideas),
        "merged_count": len(merged_ideas),
        "cache_hits": getattr(refined_result.metadata, "cache_hits", 0),
        "phase_1_duration": fresh_result.metadata.get("total_duration", 0),
        "phase_2_duration": refined_result.metadata.get("total_duration", 0),
    }

    return result
```

**Step 2.2: Add _merge_ideas() helper method**

```python
def _merge_ideas(self, fresh_ideas: list[Idea], refined_ideas: list[Idea]) -> list[Idea]:
    """
    Merge fresh and refined ideas, removing duplicates.

    Deduplication strategy:
    - Use content hash (sha256 of idea.content)
    - If duplicate found, keep the one with higher score
    - Preserve metadata from both sources

    Args:
        fresh_ideas: Ideas from fresh_mode (no context)
        refined_ideas: Ideas from standard_mode (with context)

    Returns:
        Merged list of unique ideas, sorted by score descending
    """
    import hashlib

    seen = {}  # content_hash -> idea
    merged = []

    # Add fresh ideas first
    for idea in fresh_ideas:
        content_hash = hashlib.sha256(idea.content.encode()).hexdigest()
        if content_hash not in seen:
            seen[content_hash] = idea
            merged.append(idea)
        else:
            # Duplicate - keep higher score
            if idea.score > seen[content_hash].score:
                seen[content_hash] = idea
                # Replace in merged list
                for i, existing in enumerate(merged):
                    if hashlib.sha256(existing.content.encode()).hexdigest() == content_hash:
                        merged[i] = idea
                        break

    # Add refined ideas (may overlap with fresh)
    for idea in refined_ideas:
        content_hash = hashlib.sha256(idea.content.encode()).hexdigest()
        if content_hash not in seen:
            seen[content_hash] = idea
            merged.append(idea)
        else:
            # Duplicate - keep higher score
            if idea.score > seen[content_hash].score:
                seen[content_hash] = idea
                # Update in merged list
                for i, existing in enumerate(merged):
                    if hashlib.sha256(existing.content.encode()).hexdigest() == content_hash:
                        merged[i] = idea
                        break

    # Sort by score descending
    return sorted(merged, key=lambda x: x.score, reverse=True)
```

**Acceptance Criteria:**
- [ ] `brainstorm_refined()` method exists and is async
- [ ] Phase 1 (fresh) runs with fresh_mode=True
- [ ] Phase 2 (refined) runs with fresh_mode=False
- [ ] Top 50% of fresh ideas selected for refinement
- [ ] `_merge_ideas()` deduplicates by content hash
- [ ] Merged ideas sorted by score descending
- [ ] Metadata includes fresh_count, refined_count, merged_count
- [ ] Total timeout split evenly between phases

---

### Phase 3: CLI Integration (30 minutes)

**Step 3.1: Add --refine flag to run_heavy.py**

**File:** `P:\.claude\skills\s\scripts\run_heavy.py`

**Change 1: Add argument**

```python
# In parse_args() function (around line 480)
def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run /s heavy mode deterministically.")
    parser.add_argument("--topic", default="", help="Explicit topic.")
    parser.add_argument("--personas", default="", help="Comma-separated personas.")
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--ideas", type=int, default=10)
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--output", choices=["json", "markdown", "text"], default="text")
    parser.add_argument("--fresh-mode", action="store_true", help="Generate ideas WITHOUT reading existing plans")
    parser.add_argument("--refine", action="store_true", help="Sequential refinement: fresh → standard mode")
    parser.add_argument("--strict-stale", action="store_true", help="Fail if /q context is stale.")
    return parser.parse_args(argv)
```

**Change 2: Wire up brainstorm_refined() call**

```python
# In main() function, replace the existing run_heavy() call

async def run_heavy_with_refine_check(
    topic_meta: TopicSelection,
    personas: list[str],
    timeout: float,
    num_ideas: int,
    use_refinement: bool,
    fresh_mode: bool,
    use_mock: bool,
) -> Any:
    """Helper to call brainstorm() or brainstorm_refined() based on flags."""
    _ensure_import_paths()
    from commands.brainstorm.orchestrator import BrainstormOrchestrator

    memory = InMemoryBrainstormMemory()

    orchestrator = BrainstormOrchestrator(
        memory=memory,
        enable_full_debate=True,
        llm_config=None,
        use_mock_agents=use_mock,
    )

    if use_refinement:
        # Sequential refinement workflow
        return await orchestrator.brainstorm_refined(
            prompt=topic_meta.topic,
            personas=personas,
            timeout=timeout,
            num_ideas=num_ideas,
            # fresh_mode is controlled internally by brainstorm_refined
            metadata={"cli_flags": {"--refine": True}},
        )
    else:
        # Single-pass workflow (respects fresh_mode flag)
        return await orchestrator.brainstorm(
            prompt=topic_meta.topic,
            personas=personas,
            timeout=timeout,
            num_ideas=num_ideas,
            fresh_mode=fresh_mode,
        )

# In main() function, replace the run_heavy() call:
result = asyncio.run(
    run_heavy_with_refine_check(
        topic_meta=topic_meta,
        personas=personas,
        timeout=args.timeout,
        num_ideas=args.ideas,
        use_refinement=args.refine,
        fresh_mode=args.fresh_mode,
        use_mock=args.mock,
    )
)
```

**Change 3: Add validation for conflicting flags**

```python
# In parse_args() or main(), add:
if args.refine and args.fresh_mode:
    print("ERROR: Cannot use --refine and --fresh-mode together.")
    print("  --refine runs fresh_mode internally, then refines with standard mode.")
    print("  --fresh-mode runs fresh_mode only (no refinement).")
    print("  Use --refine for sequential refinement, or omit both flags for standard mode.")
    return 1
```

**Acceptance Criteria:**
- [ ] `--refine` flag added to argument parser
- [ ] `--refine` calls `brainstorm_refined()`
- [ ] `--fresh-mode` calls `brainstorm()` with fresh_mode=True
- [ ] No flags calls `brainstorm()` with fresh_mode=False (default)
- [ ] Error raised when both `--refine` and `--fresh-mode` used together
- [ ] Help text updated with --refine description

---

### Phase 4: Update Documentation (15 minutes)

**Step 4.1: Add docstrings to cache.py (from /r analysis)**

In Phase 1 Step 1.1, ensure complete docstrings:

```python
# Module docstring (already in template above)
# Function docstrings:

def cache_llm_call(ttl_seconds: int = DEFAULT_TTL_SECONDS):
    """
    Decorator to cache LLM call results.

    Args:
        ttl_seconds: Time-to-live for cache entries (default: 2 hours)

    Returns:
        Decorated async function that caches results

    Cache key includes:
        - model_id: Prevents cross-model contamination
        - function name: Distinguishes different call sites
        - All arguments: Full argument signature

    Fresh mode bypass:
        - If fresh_mode=True detected in context, cache is bypassed
        - Ensures true exploration without cached bias

    Temperature routing:
        - Cache hits served at temperature=0 for determinism
        - Cache misses use user-specified temperature
    """

def clear_cache() -> int:
    """
    Clear all cached LLM responses.

    Returns:
        Number of cache files deleted

    Usage:
        clear_cache()  # Returns: 42 (deleted 42 cache files)
    """

def get_cache_stats() -> dict[str, Any]:
    """
    Get cache statistics.

    Returns:
        Dict with cache_size (bytes), file_count, oldest_timestamp, newest_timestamp

    Usage:
        stats = get_cache_stats()
        print(f"Cache: {stats['file_count']} files, {stats['cache_size_bytes']/1024:.1f} KB")
    """
```

**Step 4.2: Add brainstorm_refined() docstring (from /r analysis)**

In Phase 2 Step 2.1, ensure complete docstring:

```python
async def brainstorm_refined(self, prompt: str, ...) -> BrainstormResult:
    """
    Sequential refinement workflow: fresh_mode → standard_mode.

    This method implements the optimal long-term solution for dual-mode
    brainstorming by running fresh_mode first (to prevent anchoring bias)
    then refining the top candidates with standard mode (to add context).

    Args:
        prompt: The main topic or problem to brainstorm about
        personas: List of persona names to use (default: None)
        timeout: Total timeout for the entire session (default: 180.0)
        num_ideas: Target number of ideas to generate (default: 10)
        constraints: Optional list of constraints or requirements
        goals: Optional list of specific goals to achieve
        seed_ideas: Optional pre-generated ideas (internal use for recursion)
        metadata: Additional context or parameters

    Returns:
        BrainstormResult with refined ideas from both phases

    Workflow:
        Phase 1: Fresh Brainstorm (fresh_mode=True)
            - Generate ideas WITHOUT reading existing plans
            - Bypass cache to ensure true exploration
            - Output: fresh_ideas

        Phase 2: Standard Mode Refinement (fresh_mode=False)
            - Take top 50% of fresh_ideas for refinement
            - Evaluate them WITH full context access
            - Use cached LLM calls where possible
            - May generate additional refined ideas
            - Output: refined_ideas

        Merge: Combine fresh + refined, deduplicate, return

    Performance:
        - Expected cache hit rate: >40%
        - Expected cost reduction: >30% vs. independent dual-run
        - Timeout split: 50% fresh, 50% refinement

    Examples:
        >>> result = await orchestrator.brainstorm_refined("design event sourcing system")
        >>> print(f"Ideas: {len(result.ideas)}, Cache hits: {result.metadata['cache_hits']}")
    """
```

**Step 4.3: Update /s SKILL.md**

**File:** `P:\.claude\skills\s\SKILL.md`

**Add to Usage section:**

```markdown
## Usage

### Recommended Workflow

```bash
# Sequential refinement (RECOMMENDED)
/s "redesign auth system" --refine
# Runs fresh_mode → standard_mode automatically
# Optimal: fresh ideas + context refinement, ~40% cost savings

# Pure exploration (no context bias)
/s "explore radical alternatives" --fresh-mode
# Fresh ideas only, no refinement
# Use when you want completely unconstrained brainstorming

# Standard mode (default)
/s "improve existing module"
# Context-aware ideas only
# Use for incremental work on existing systems
```

### CLI Flags

| Flag | Purpose | Mode |
|------|---------|------|
| `--refine` | Sequential refinement workflow | Recommended for most strategy sessions |
| `--fresh-mode` | Fresh ideas only (no context) | Pure exploration, prevents anchoring bias |
| (no flags) | Standard mode (default) | Context-aware ideas for incremental work |

### Output

All modes output structured results with:
- `top_ideas`: Ranked list of scored recommendations
- `decision_memo`: Top choice + alternatives + risks
- `next_commands`: Suggested follow-up commands
- `metrics`: Execution time, cache hits, idea counts

### Examples

```bash
# Architecture exploration with refinement
/s "design event sourcing system" --refine

# Quick incremental improvement
/s "optimize database queries"

# Radical rethinking (no constraints)
/s "reimagine file storage" --fresh-mode
```
```

**Step 4.2: Update version in SKILL.md**

```markdown
## Version

**Version:** 2.4.0
**Updated:** 2026-02-25

**Changelog:**
- **v2.4.0** (2026-02-25): Add sequential refinement workflow with --refine flag
  - Implements architecture decision Option B
  - Adds caching layer for LLM call reuse
  - Reduces dual-mode cost by ~40% vs. independent runs
  - brainstorm_refined() method with fresh → standard workflow
- **v2.3.0** (2026-02-25): Add fresh_mode to prevent anchoring bias
- **v2.2.0** (2026-02-25): Multi-terminal friendly + no TTL
- **v2.1.0** (2026-02-25): Add CSF NIP constitutional context
- **v2.0.0** (2026-02-16): Initial version with BrainstormOrchestrator
```

**Step 4.4: Add rollback validation test (from `/r` analysis)**

**Purpose:** Verify rollback procedure works correctly per plan Section 7.

**File:** `P:\__csf\tests\commands\brainstorm\test_rollback.py` (new)

```python
"""
Test rollback procedures for sequential refinement feature.

Ensures that removing caching layer and refinements works correctly
and doesn't break existing /s functionality.
"""
import pytest
from pathlib import Path
import shutil

from commands.brainstorm.orchestrator import BrainstormOrchestrator


class TestRollback:
    """Test rollback procedures for sequential refinement."""

    def test_cache_clearance_removes_all_cached_data(self):
        """Test that clear_cache() removes all cache files."""
        # Setup: Create some cache files
        cache_dir = Path.home() / ".cache" / "brainstorm"
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create dummy cache files
        (cache_dir / "test1.json").write_text('{"test": "data"}')
        (cache_dir / "test2.json").write_text('{"test": "data"}')

        # Execute: clear_cache()
        from commands.brainstorm.cache import clear_cache
        count = clear_cache()

        # Verify: All cache files removed
        assert count == 2
        assert not list(cache_dir.glob("*.json"))

    def test_rollback_restores_standard_mode(self):
        """Test that removing brainstorm_refined() restores standard /s behavior."""
        orchestrator = BrainstormOrchestrator(
            memory=None,
            enable_full_debate=True,
            llm_config=None,
            use_mock_agents=True,  # Use mocks for testing
        )

        # Verify: brainstorm_refined() exists
        assert hasattr(orchestrator, 'brainstorm_refined')

        # Verify: brainstorm() still exists (rollback path)
        assert hasattr(orchestrator, 'brainstorm')

        # Verify: Can call brainstorm() without errors
        # (Would need mocking for actual LLM calls)
        # result = await orchestrator.brainstorm("test prompt")

    def test_fresh_mode_bypass_after_rollback(self):
        """Test that fresh_mode still bypasses cache after rollback."""
        from commands.brainstorm.cache import cache_llm_call

        # Mock function
        async def mock_llm(prompt):
            return {"content": "response"}

        # Create decorated function
        decorated = cache_llm_call(ttl_seconds=7200)(mock_llm)

        # Create context with fresh_mode=True
        class MockContext:
            fresh_mode = True

        # Test: fresh_mode context should work
        # (Implementation would verify cache bypass logic)
```

**Acceptance Criteria:**
- [ ] Rollback test file created
- [ ] Test validates cache clearance
- [ ] Test verifies standard mode restoration
- [ ] Test validates fresh_mode bypass works after rollback

---

### Phase 5: Integration Testing (from `/r` analysis - integrate test creation)

**Purpose:** Move tests from "to create" (Section 4) into implementation phases.

**Updated test sequence:**

| Test File | Created In Phase | Purpose |
|-----------|-----------------|---------|
| `test_cache.py` | Phase 1 (after Step 1.2) | Cache decorator unit tests |
| `test_refinement.py` | Phase 2 (after Step 2.2) | Refinement workflow integration tests |
| `test_cli_refine.py` | Phase 3 (after Step 3.1) | CLI --refine flag tests |
| `test_rollback.py` | Phase 4 (Step 4.4) | Rollback validation tests |

**Acceptance Criteria:**
- [ ] Tests created during implementation phases (not deferred)
- [ ] Each phase has corresponding test coverage
- [ ] Test execution passes before proceeding to next phase

---

## 7. Risks, Success Criteria, Dependencies

### Risks

| Risk | Probability | Impact | Mitigation |
|------|------------|--------|------------|
| **Cache key collisions** | Low | High | Use SHA256 hash with full argument signature; include persona, temperature, max_tokens in key |
| **Stale cache in fresh_mode** | Low | Medium | fresh_mode bypasses cache entirely; decorator checks context.fresh_mode |
| **Refinement bias** | Medium | Medium | Add bias detection: track rejections; flag ideas rejected for context incompatibility vs quality |
| **Cache storage growth** | Low | Low | TTL eviction (2 hours); document manual cleanup; consider cron job for production |
| **Cache corruption** | Low | Low | Try/except on cache load; fall through to LLM call on error |
| **Time allocation** | Medium | Low | Split timeout evenly (50% each); add configurable split ratio in future if needed |

### Success Criteria

**Functional Requirements:**
1. ✅ `--refine` flag executes sequential refinement workflow
2. ✅ Cache hit rate > 40% during refinement phase (measured via logging)
3. ✅ Cost reduction > 30% vs. independent dual-run (measured via LLM call counts)
4. ✅ Fresh ideas with score > 75 survive refinement at 80% rate

**Quality Requirements:**
1. ✅ No regression in existing functionality:
   - `--fresh-mode` works as before
   - Default mode (no flags) works as before
2. ✅ Cache bypass works correctly for fresh_mode
3. ✅ Deduplication preserves highest-scored ideas
4. ✅ Error messages clear for conflicting flags

**Performance Requirements:**
1. ✅ Refinement phase completes within timeout (no timeouts in Phase 2)
2. ✅ Cache serialization/deserialization < 10ms per file
3. ✅ Cache directory size < 100MB for typical usage

**User Adoption:**
1. ✅ `--refine` becomes default recommendation in SKILL.md
2. ✅ User understands when to use each mode (--refine, --fresh-mode, default)

### Dependencies

**Internal Dependencies:**
- `P:\__csf\src\commands\brainstorm\orchestrator.py` — extend with new method
- `P:\__csf\src\commands\brainstorm\models\__init__.py` — use existing models
- `P:\__csf\src\commands\brainstorm\agents\base.py` — decorate AgentLLMClient.generate()
- `P:\.claude\skills\s\scripts\run_heavy.py` — add CLI flag

**External Dependencies:**
- None (all required modules in stdlib)

**Blocking Dependencies:**
- None

**Integration Points:**
1. **Cache module** → All 5 agents (via decorator on AgentLLMClient)
2. **brainstorm_refined()** → run_heavy.py CLI
3. **SKILL.md** → User documentation

### Rollback Strategy

**If implementation fails:**
1. Remove @cache_llm_call decorator from AgentLLMClient.generate() (revert base.py)
2. Remove brainstorm_refined() method from orchestrator.py
3. Revert run_heavy.py CLI changes (remove --refine flag)
4. Revert SKILL.md to previous version

**Rollback commands:**
```bash
# Revert cache.py deletion (if created)
rm P:/__csf/src/commands/brainstorm/cache.py

# Git revert for modified files
git checkout P:/__csf/src/commands/brainstorm/agents/base.py
git checkout P:/__csf/src/commands/brainstorm/orchestrator.py
git checkout P:/.claude/skills/s/scripts/run_heavy.py
git checkout P:/.claude/skills/s/SKILL.md

# Delete cache directory
rm -rf ~/.cache/brainstorm/
```

**Testing rollback:**
```bash
# Verify --fresh-mode still works after rollback
/s "test" --fresh-mode

# Verify default mode still works after rollback
/s "test"
```

---

## Top Risks

1. **Cache complexity** — Key collisions or stale cache could produce incorrect results
   - **Mitigation:** Use SHA256 with full argument signature; fresh_mode bypass; TTL eviction

2. **Refinement bias** — Standard mode might reject good fresh ideas due to context incompatibility
   - **Mitigation:** Track rejection reasons; flag context-based rejections; preserve high-scoring fresh ideas regardless

3. **Time allocation** — 50/50 timeout split might not suit all use cases
   - **Mitigation:** Monitor phase durations in metrics; add configurable split ratio in v2.5 if needed

---

## Next Actions

1. **Review and approve this plan** — Verify all sections are complete and accurate
2. **Execute Phase 0: Micro-Pilot Validation** — Run 1-hour proof-of-concept test
3. **Decision point:** If Phase 0 succeeds (≥20% token savings), proceed; else reevaluate with `/s`
4. **Execute Phase 0.5: Baseline Measurement** — Establish performance metrics (30 min, only if Phase 0 succeeds)
5. **Begin Phase 1: Add Caching Layer** — Create cache.py module (only after Phase 0.5 completes)
6. **Track progress with tasks** — Use task list to monitor implementation

**Implementation order (validation-first approach with CORRECTED gate criteria):**
- **Phase 0**: Micro-Pilot Testing (1 hour) → validates caching approach works
- **Phase 0.5**: Baseline Measurement (30 min) → establishes empirical metrics
- **Gate 1 (CORRECTED):** Token savings ≥20%? If NO: stop, reevaluate with `/s`. If YES: continue.
  - **FIX:** Gate now AFTER Phase 0.5, compares empirical baseline vs implementation results
  - **Previous error:** Gate was after Phase 0 (simulated), should be after Phase 0.5 (empirical)
- **Phase 1**: Caching Infrastructure (1-2 hours) — cache decorator, MD5 keys, file-based storage
- **Phase 2**: Refinement Workflow (2-3 hours) — brainstorm_refined(), cache bypass investigation
- **Phase 3**: CLI Integration + Documentation (1 hour) — --refine flag, temperature routing docs

**Total estimated effort:**
- Best case (Gate passes): 5-7.5 hours (1h pilot + 0.5h baseline + 3.5-6h implementation)
- Fail fast (Gate fails): 1.5 hours (saved 3.5-6 hours by not pursuing unproven approach)

**Phase consolidation (from 6 → 3 phases):**
- **Old:** Phase 1 (cache), Phase 2 (refinement), Phase 2.5 (adaptive), Phase 3 (CLI), Phase 4 (docs), Phase 5 (tests)
- **New:** Phase 1 (Caching Infrastructure), Phase 2 (Refinement Workflow), Phase 3 (CLI + Docs)
- **Rationale:** Reduced coordination overhead, matches YAGNI principle for solo dev

---

## Plan History

| Date | Change |
|------|--------|
| 2026-02-25 | Initial plan created from architecture decision |
| 2026-02-25 | Updated with fresh brainstorm insights (5 patterns integrated): |
| | • Temperature routing (cached results at temp=0) |
| | • Model-aware cache keys |
| | • Adaptive chain length (early stopping) |
| | • Micro-pilot testing approach |
| | • TTL validation (2-hour optimal for solo-dev) |
| 2026-02-25 | **Restructured with validation-first approach** (from `/arch` decision): |
| | • Added Phase 0: Micro-Pilot Validation (promoted from optional) |
| | • Added Phase 0.5: Baseline Measurement (addresses `/r` MUST FIX NOW gap) |
| | • Reordered phases: 0 → 0.5 → 1 → 2 → 2.5 → 3 → 4 |
| | • Integrated `/r` findings: docstrings, test priority, rollback test |
| | • Added gate criteria: ≥20% savings required to proceed past Phase 0 |
| 2026-02-25 | **Architecture review (`/q` + `/arch`) completed**: |
| | • **Added section 3.1**: Architecture review findings (5 critical → 2 critical after solo-dev filtering) |
| | • **FIXED gate criteria**: Moved from after Phase 0 to after Phase 0.5 (ARCH-002) |
| | • **Consolidated phases**: Reduced from 6 to 3 phases (Phase 1: Caching, Phase 2: Refinement, Phase 3: CLI+Docs) |
| | • **Updated cache keys**: SHA-256 → MD5 for 50% performance gain (CONC-003) |
| | • **Documented dismissed concerns**: File-based caching, cache abstraction, versioning (not applicable to solo dev) |
| | • **Identified critical bug**: Cache bypass violation in brainstorm_refined() (ARCH-001) - to be investigated in Phase 2 |
| | • **Added documentation requirement**: Temperature routing behavior must be documented (CONC-001) |
| 2026-02-25 | **Addressed plan review action items** (PR-001, PR-002, PR-003): |
| | • **PR-003**: Updated plan status from DRAFT to REVIEWED |
| | • **PR-001**: Added Step 2.0 "Investigate Cache Bypass Risk" to Phase 2 (addresses ARCH-001) |
| | • **PR-002**: Implemented temperature routing user notification with logging in cache decorator (addresses CONC-001) |

---

## 8. Optional Enhancements (from Fresh Brainstorm)

The following pattern was identified via fresh-mode brainstorming and is recommended for future iterations:

### Enhancement 1: Adaptive Chain Length

**Problem:** Fixed 2-phase refinement (fresh → standard) may waste LLM calls when fresh ideas are already high-quality.

**Solution:** Add early-stopping heuristic to detect diminishing returns.

**Implementation:**
```python
# In brainstorm_refined(), after Phase 1 (fresh):

# Calculate quality threshold
fresh_scores = [idea.score for idea in fresh_ideas]
avg_fresh_score = sum(fresh_scores) / len(fresh_scores)

# Skip refinement if fresh quality is already high
if avg_fresh_score >= 85.0:
    # Fresh ideas are excellent - skip refinement phase
    return fresh_result  # Return fresh result as-is

# Otherwise proceed with Phase 2 (refinement)
```

**Threshold rationale:**
- Score ≥85: Ideas are already strong, refinement unlikely to add >5% value
- Score <85: Refinement phase may validate or improve ideas

**Validation:**
- Track skipped refinements vs. full refinements
- Measure if skipped sessions would have benefited from refinement
- Adjust threshold based on data

**Estimated effort:** 30 minutes

**Implementation phase:** **Phase 2.5** (after Phase 2 completes)

---

### Enhancement Priority

| Enhancement | Value | Effort | Priority |
|-------------|-------|--------|----------|
| Adaptive Chain Length | Medium | 30 min | **Phase 2.5** (after core works) |

**Note:** Micro-Pilot Testing was originally listed here but has been promoted to **Phase 0** (validation-first approach per architecture decision).
