# Architecture Decision: Optimal Long-Term Solution for Dual-Mode Brainstorming

**Date:** 2026-02-25
**Status:** ACCEPTED
**Decision:** Implement Option B (Sequential Refinement with Result Caching)

## Problem Statement

The `/s` brainstorming skill has two modes:
- **fresh_mode** (`--fresh-mode`): Agents generate ideas WITHOUT reading existing plans (prevents anchoring bias)
- **standard_mode** (default): Agents have full context access (produces contextually-grounded results)

User wants to run both modes to get:
1. Fresh, unbiased ideas from first principles
2. Context-aware refinements that validate against current state

**Question:** What is the optimal long-term architectural solution?

## Analysis

### Current State
- BrainstormOrchestrator uses asyncio correctly for I/O-bound LLM calls
- 5 agents (Innovator, Pragmatist, Critic, Expert, Synthesizer) run in parallel via `asyncio.gather()`
- fresh_mode adds warning to agent prompts: "You MUST generate ideas from first principles WITHOUT reading any existing plans"
- Two modes are currently independent: user runs `/s --fresh-mode` then `/s` (standard) separately

### Options Evaluated

| Option | Approach | Cost | Time | Value | Dev Effort |
|--------|----------|------|------|-------|------------|
| **A: Parallel Dual-Run** | Run both modes independently, merge results | 2x baseline | Same (agents already parallel) | ~20% additional value (edge cases) | Low (3-4 hours) |
| **B: Sequential Refinement** | fresh_mode → standard_mode with caching | ~1.4x baseline | ~1.2x baseline (cached calls) | ~80% value (optimal balance) | Medium (4-6 hours) |
| **C: Smart Auto-Detect** | System decides when to use fresh_mode | Variable | Variable | Unknown | High (8-10 hours) |

### Decision: Option B (Sequential Refinement)

**Rationale:**

1. **I/O-bound workload**: LLM calls are network I/O bound; asyncio already provides parallel agent execution. Parallel dual-run adds no time benefit.

2. **Cost efficiency**: Sequential refinement reuses ~60% of LLM calls (idea generation phase). Standard mode evaluation phase can skip re-generating ideas that already exist.

3. **Value preservation**: Fresh ideas that survive refinement filtering are retained; standard mode adds contextual grounding without discarding high-quality fresh concepts.

4. **Director model compliance**: User controls workflow via `--refine` flag, not autonomous system. Aligns with CSF NIP constitutional constraints.

5. **Python 3.12+ asyncio**: Current architecture already optimal for I/O-bound workload per web research on [parallel vs sequential patterns for LLM agents](https://www.python-engineer.com/posts/asyncio-parallel-external-http-requests-python/).

6. **Result caching**: Async caching patterns ([aiocache](https://github.com/aio-libs/aiocache), [cachetools-async](https://pypi.org/project/cachetools-async/)) can eliminate redundant LLM calls during refinement phase.

### Implementation

**Phase 1: Add Caching Layer**
- TTL-based file cache (2-hour default per async caching best practices)
- Cache key generation: `hashlib.sha256(func_name + args + sorted_kwargs)`
- Apply to agent LLM calls in `Innovator`, `Pragmatist`, `Critic`, `Expert`, `Synthesizer`

**Phase 2: Implement Refinement Workflow**
- New method: `BrainstormOrchestrator.brainstorm_refined()`
- Phase 1: Generate fresh ideas (fresh_mode=True)
- Phase 2: Refine top 50% with standard mode (fresh_mode=False, seed_ideas=top_fresh)
- Merge: Retain fresh ideas that survive refinement + new refined ideas

**Phase 3: CLI Integration**
- Add `--refine` flag to run_heavy.py
- If `--refine`: call `brainstorm_refined()`
- Else: call `brainstorm()` with `fresh_mode` flag

**Phase 4: SKILL.md Update**
- Document `--refine` flag as recommended default
- `--fresh-mode` for pure exploration only
- Default (no flags): standard mode for incremental work

### Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| Cache complexity (key collisions) | Use `frozenset(sorted(kwargs.items()))` for dict args |
| Stale cache in fresh_mode | fresh_mode bypasses cache; only standard mode uses cache |
| Refinement bias (rejecting fresh ideas) | Add bias-detection: flag rejections for context incompatibility vs. quality |
| Cache storage growth | TTL eviction (2 hours) + periodic cleanup of `.cache/brainstorm/` |

### Alternatives Rejected

**Option A (Parallel Dual-Run):**
- Wasteful: re-runs entire idea generation phase
- 100% cost for ~20% additional value
- Only justified if fresh and standard results are completely disjoint (rare)

**Option C (Smart Auto-Detect):**
- Violates director model: user should decide strategy
- Over-engineering for simple toggle
- Adds complexity without clear benefit

### Confidence Assessment

**Confidence:** 85%

**Basis:**
- Current codebase analysis confirms asyncio is correctly used for I/O-bound workload
- Web research validates parallel vs sequential patterns for LLM agents
- Mature async caching ecosystem (aiocache ⭐1.3K, cachetools-async with 2025 releases)

**Weakest Assumption:** That 60% of LLM calls can be reused from fresh mode in standard mode without quality degradation.

**Consequence if wrong:** Refinement phase might need to re-run most LLM calls anyway, making sequential approach only marginally better than parallel dual-run. Mitigation: Implement caching incrementally; measure hit rate; expand only if effective.

### Evidence Sources

- **Python async caching patterns:**
  - [aiocache GitHub Repository](https://github.com/aio-libs/aiocache) (⭐1.3K)
  - [cachetools-async PyPI (v0.0.5, June 2025)](https://pypi.org/project/cachetools-async/)

- **Asyncio parallel vs sequential:**
  - [Python-engineer.com - Asyncio Parallel External HTTP Requests](https://www.python-engineer.com/posts/asyncio-parallel-external-http-requests-python/)
  - [Real Python - Async IO in Python: A Complete Walkthrough](https://realpython.com/async-io-python/)

- **Current codebase:**
  - `P:\__csf\src\commands\brainstorm\orchestrator.py:78-82` (phase timeouts)
  - `P:\__csf\src\commands\brainstorm\models\__init__.py:20-125` (Idea, Evaluation models)
  - `P:\.claude\skills\s\scripts\run_heavy.py:462` (fresh_mode parameter)

## Implementation Roadmap

**Total Effort:** 4-6 hours

**Phase 1: Add Caching Layer** (1-2 hours)
- Create `P:/__csf/src/commands/brainstorm/cache.py`
- Implement `@cache_llm_call(ttl_seconds=7200)` decorator
- Add to all agent `_generate_ideas()` methods

**Phase 2: Implement Refinement Workflow** (2-3 hours)
- Add `BrainstormOrchestrator.brainstorm_refined()` method
- Implement seed_ideas passing to standard mode
- Add `_merge_ideas()` helper

**Phase 3: CLI Integration** (30 minutes)
- Add `--refine` flag to run_heavy.py
- Wire up `brainstorm_refined()` call

**Phase 4: Update Documentation** (15 minutes)
- Update `/s` SKILL.md with `--refine` usage
- Add examples and recommendation

## Success Criteria

1. **Cache hit rate > 40%** during refinement phase (measured via logging)
2. **Cost reduction > 30%** vs. parallel dual-run (measured via LLM call counts)
3. **Quality preservation**: Fresh ideas with score > 75 survive refinement at 80% rate
4. **User adoption**: `--refine` becomes default recommendation in SKILL.md

## Version History

- **2026-02-25**: Initial decision (Option B: Sequential Refinement)
