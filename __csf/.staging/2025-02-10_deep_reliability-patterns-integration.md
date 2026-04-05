# Architecture Decision: Reliability Patterns Integration

**Date:** 2025-02-10
**Template:** deep
**Complexity:** HIGH (multi-system)
**Confidence:** 82%

## Question

How do we incorporate the finding about Highest Reliability into our solutions? /code, /debug, /rca, /tdd, non-skill tasks, etc.

## Mental Model

**Design Pattern:** Cross-Cutting Reliability Layer

High reliability comes from **resilience patterns** (Bulkhead, Circuit Breaker, Retry, Fallback) applied at the **workflow orchestration level**, not just individual API calls.

**Key patterns from [Portkey.ai](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps) (July 2025):**
- **Retry** = transient glitch recovery (with exponential backoff + jitter)
- **Circuit Breaker** = persistent outage containment
- **Fallback** = continuity when primary fails
- **Bulkhead** = resource isolation

**Layered Stack Pattern** (innermost → outermost):
```
@with_fallback(lambda: safe_default_result())
@with_circuit_breaker(failure_threshold=5, recovery_timeout=60)
@with_retry(max_attempts=3, backoff_base=2, jitter=True)
async def execute_subagent(agent_type, prompt):
    return await agent_type.delegate(prompt)
```

**Why this order matters:**
1. Retry handles transient glitches first (most common case)
2. Circuit Breaker prevents cascading failures during outages
3. Fallback ensures continuity when all else fails

## Pre-Mortem: What Fails in 6 Months?

| Failure Mode | Likelihood | Impact | Mitigation |
|--------------|------------|-------|------------|
| Hook timeout cascades | HIGH | Blocks all tool use | Circuit breaker at hook level |
| Subagent runaway | MEDIUM | Cost overruns | Budget caps + timeout enforcement |
| State corruption between retries | MEDIUM | Wrong "next step" | Idempotency checks |
| False positives blocking work | MEDIUM | User frustration | Manual override fallback |
| Race conditions in circuit breaker state | MEDIUM | Inconsistent breaker state | Thread-safe state with locks |
| Missing observability | HIGH | Can't measure effectiveness | Structured logging + metrics export |

## Quantitative Success Criteria

**How we know it works:**

| Metric | Baseline | Target | Measurement |
|--------|----------|--------|-------------|
| Subagent timeout failures | ~15% estimated | <7.5% (50% reduction) | Track timeout errors before/after |
| Circuit breaker triggers | N/A | <5 per 1000 calls | Log breaker state transitions |
| MTTR for transient failures | Manual retry | <10 seconds auto | Time from first failure to success |
| False positive rate | N/A | <1% | Manual override usage rate |
| Cost overhead | 0% | <5% additional | Track retry attempts vs single calls |

**A/B Testing Protocol** (pilot on /tdd):
1. **Week 1-2**: Run with decorator in dry-run mode (log only, no enforcement)
2. **Week 3-4**: Enable decorator for 50% of /tdd invocations (random sample)
3. **Week 5**: Compare metrics, decide on full rollout

## Async/Threading Safety

**Challenge**: PARALLEL subagent delegation means concurrent decorator execution.

**Solution**: Thread-safe circuit breaker state using `asyncio.Lock`:

```python
class CircuitBreakerState:
    def __init__(self):
        self._failure_count = 0
        self._last_failure_time = None
        self._state = "closed"  # closed, open, half_open
        self._lock = asyncio.Lock()

    async def record_failure(self):
        async with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.time()
            if self._failure_count >= self._failure_threshold:
                self._state = "open"

    async def record_success(self):
        async with self._lock:
            self._failure_count = 0
            self._state = "closed"

    async def allow_request(self) -> bool:
        async with self._lock:
            if self._state == "closed":
                return True
            if self._state == "open":
                if time.time() - self._last_failure_time > self._recovery_timeout:
                    self._state = "half_open"
                    return True
                return False
            # half_open: allow one request to test
            return True
```

## Alternatives

### Option A: Per-Skill Resilience Wrappers

Add resilience patterns directly to each skill's orchestration code.

**Pros:** Each skill owns its reliability, failure isolated
**Cons:** Code duplication, maintenance burden
**Risk:** HIGH technical, MEDIUM schedule

### Option B: Central Resilience Orchestrator

Create a shared resilience service that all skills call.

**Pros:** Single implementation, consistent behavior
**Cons:** Single point of failure
**Risk:** HIGH technical, HIGH schedule

### Option C: Pattern Library + Opt-In Decorator (RECOMMENDED)

**Differs on:** Adoption model (opt-in vs automatic), Coupling (library vs framework)

Create a pattern library with decorator:

```python
# P:\__csf\src\lib\resilience_patterns.py
def with_resilience(patterns=['retry', 'circuit_breaker']):
    """Decorator to add resilience patterns to skill orchestration."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            return await resilience_execute(func, patterns, *args, **kwargs)
        return wrapper
    return decorator

# Usage:
@with_resilience(['retry', 'circuit_breaker'])
async def execute_subagent(agent_type, prompt):
    return await agent_type.delegate(prompt)
```

**Pros:** Lowest technical risk, skills can opt in gradually, no single point of failure
**Cons:** Relies on developers remembering to use it
**Risk:** LOW technical, LOW schedule

## Recommendation

**Option C** is best because:
1. **Lowest coupling** - patterns don't become dependency
2. **Easiest rollback** - remove decorator if needed
3. **Fastest implementation** - ~1 week vs 2-4 weeks
4. **Opt-in** - skills adopt at their own pace

## Implementation Timeline

**Phase 1: Foundation (Day 1)**
- Create `P:\__csf\src\lib\resilience_patterns.py`
- Implement Retry (with jitter), Circuit Breaker (thread-safe), Fallback patterns
- Add unit tests for each pattern
- Add structured logging with event types: `retry_attempt`, `circuit_open`, `circuit_closed`, `fallback_used`

**Phase 2: Pilot on /tdd (Day 2-3)**
- /tdd is ideal pilot: heaviest subagent delegation (PARALLEL test-writer agents)
- Add decorator to /tdd subagent delegation points only
- Start with dry-run mode (log only, no enforcement)
- Verify no regressions in existing /tdd tests

**Phase 3: A/B Testing (Day 4-7)**
- Enable decorator for 50% of /tdd invocations (hash-based sampling)
- Collect metrics: timeout rate, retry count, breaker triggers
- Compare against baseline (dry-run logs)

**Phase 4: Evaluation & Decision (Day 8)**
- Review metrics against success criteria
- If target met: proceed to Phase 5
- If not: iterate on parameters or abort

**Phase 5: Rollout to Other Skills (Day 9-10)**
- /code (second heaviest subagent use)
- /rca (moderate subagent use)
- Update SKILL.md files with decorator usage

**Phase 6: Optional PreToolUse Hook (Day 11+)**
- Non-blocking audit hook to check decorator presence
- Warns (not blocks) when subagent delegation lacks resilience
- Only if metrics justify the overhead

## Rollback Plan

1. Remove decorator from skills
2. Delete library file
3. Remove imports
4. Test skills work without patterns

**Rollback time:** <5 minutes

## Tech Debt

| Metric | Score |
|--------|-------|
| Coupling | LOW |
| Maintainability | HIGH |
| Future debt | LOW |

## Monitoring Integration

**Structured Events** (log to `__csf/data/resilience_events.jsonl`):

```json
{"event": "retry_attempt", "fn": "execute_subagent", "attempt": 2, "reason": "timeout", "ts": "2025-02-10T12:00:00Z"}
{"event": "circuit_open", "fn": "execute_subagent", "failure_count": 5, "ts": "2025-02-10T12:01:00Z"}
{"event": "circuit_closed", "fn": "execute_subagent", "recovery_time": 60, "ts": "2025-02-10T12:02:00Z"}
{"event": "fallback_used", "fn": "execute_subagent", "fallback": "safe_default", "ts": "2025-02-10T12:03:00Z"}
```

**Metrics to Track:**
- `retry_rate`: % of calls that trigger retry
- `circuit_breaker_triggers`: per 1000 calls
- `fallback_usage`: % of calls falling back
- `mttr_transient`: mean time to recovery for transient failures
- `cost_overhead`: % additional API calls from retries

**Health Endpoint** (optional):
```python
# P:\__csf\src\lib\resilience_patterns.py
async def health_check() -> dict:
    """Return resilience system health status."""
    return {
        "circuit_breakers": {
            name: {"state": cb.state, "failures": cb.failure_count}
            for name, cb in _breaker_registry.items()
        },
        "total_retries": _retry_counter.total,
        "total_fallbacks": _fallback_counter.total,
    }
```

## Confidence: 82%

**Evidence:**
- Tier 2 (Official docs): [Portkey.ai](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps), [Azure patterns](https://dev.to/paulotorrestech/building-resilient-and-fault-tolerant-applications-with-azure-resiliency-patterns-49an)
- Tier 3 (Logical derivation): Async safety via asyncio.Lock is standard pattern
- Tier 1 (Execution): /tdd has heaviest PARALLEL subagent delegation (verified from SKILL.md)
- Tier 4 (Gap): No production case studies for decorator-based resilience in AI workflows

**Confidence increased** (78% → 82%) because:
- Added specific pilot strategy reduces risk
- Quantitative criteria provide go/no-go decision points
- A/B testing validates before full commitment

## Sources

- [Retries, Fallbacks, and Circuit Breakers in LLM Apps - Portkey.ai](https://portkey.ai/blog/retries-fallbacks-and-circuit-breakers-in-llm-apps) (July 2025)
- [Building Resilient Applications with Azure Resiliency Patterns](https://dev.to/paulotorrestech/building-resilient-and-fault-tolerant-applications-with-azure-resiliency-patterns-49an) (January 2025)
- [Multi-Agent AI Failure Recovery - Galileo.ai](https://galileo.ai/blog/multi-agent-ai-system-failure-recovery) (July 2025)
- [Exponential Backoff With Jitter - AWS Architecture Blog](https://aws.amazon.com/blogs/architecture/exponential-backoff-and-jitter/) (jitter best practice)
- [asyncio.Lock - Python Documentation](https://docs.python.org/3/library/asyncio-sync.html#asyncio.Lock) (async safety)
- [ai-patterns - Yarn Classic](https://classic.yarnpkg.com/en/package/ai-patterns)
- [chuk-tool-processor - GitHub](https://github.com/chrishayuk/chuk-tool-processor)
- [Resilience Patterns Claude Code Skill | MCP Market](https://mcpmarket.com/ko/tools/skills/system-resilience-patterns)

## Added Value Summary

**Incorporated from Perplexity feedback:**

| Category | Additions | Impact |
|----------|-----------|--------|
| **Implementation** | Layered decorator stack order, jitter in retry backoff, thread-safe circuit breaker | Higher reliability through proven patterns |
| **Measurement** | Quantitative success criteria (MTTR, failure rate), A/B testing protocol | Evidence-based go/no-go decisions |
| **Strategy** | Pilot on /tdd first, 50% rollout sampling | Reduced risk through gradual adoption |
| **Observability** | Structured logging, health endpoint, metrics export | Can measure effectiveness |

**Not incorporated (lower value):**
- Complete DEFAULT Decision Path examples - useful as reference material but not critical to this specific decision
- SceMethod case study - adds complexity without immediate implementation benefit
- Extensive probability estimation - overkill for 1-week pilot phase
