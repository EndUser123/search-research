# Performance Baseline Analysis

**Date**: 2025-12-30
**Task**: TSK-251230-NSE
**Purpose**: Establish baseline hook performance before instrumentation

---

## Hook Inventory Summary

Based on filesystem analysis, the CSF NIP hooks directory contains:

| Metric | Value |
|--------|-------|
| Total .py files (including tests/) | ~100 |
| Estimated core hooks (excluding tests) | ~68 |
| Estimated total lines of code | ~32,000 |

**Note**: Due to Windows PowerShell limitations preventing exact file count, the 68 hook count from the original plan review document is used as the working estimate.

---

## Critical Hooks (Priority 1 - Week 1)

| Hook | Path | Purpose | Estimated LOC | Priority |
|------|------|---------|---------------|----------|
| **constitutional_enforcer** | (inferred) | Core constitutional enforcement | ~300 | P0 |
| **advocate_injection** | `anti_sycophancy/advocate_injection.py` | Anti-sycophancy content injection | ~200 | P0 |
| **truth_validator** | (inferred) | Fact-checking validation | ~250 | P0 |
| **goal_anchor** | `goal_anchor.py` | Goal state tracking | ~180 | P0 |
| **pre_tool_use** | (inferred) | Tool call pre-validation | ~150 | P0 |
| **PostToolUse** | `PostToolUse.py` | Tool result processing | ~200 | P0 |

**Total Week 1 instrumentation effort**: ~1,280 LOC across 6 hooks (~3h each = 18h)

---

## Supporting Infrastructure Hooks (Priority 2 - Week 2)

| Hook | Path | Purpose |
|------|------|---------|
| **event_queue** | `event_queue.py` | Event batching manager |
| **sendevent** | `sendevent.py` | SQLite database insertion |
| **instrumentationutils** | `instrumentationutils.py` | Causal chain tracking |
| **cc_diagnostic_logger** | (inferred) | Central logging |
| **hook_cache** | `hook_cache.py` | Hook performance caching |
| **llm_supervisor** | `llm_supervisor.py` | LLM call supervision |

---

## Categorization by Hook Type

### Pre-Execution Hooks

```
pre_*, on_precompact, pre_generation_*
```

**Estimated count**: 15-20
**Typical behavior**: Validate inputs, check constraints, load session data
**Expected duration**: 5-50ms

### Post-Execution Hooks

```
post_*, on_postcompact, PostToolUse*
```

**Estimated count**: 12-15
**Typical behavior**: Validate outputs, store results, trigger follow-up actions
**Expected duration**: 10-100ms

### Content Injection Hooks

```
*_injection, guidance_injector, advocate_injection
```

**Estimated count**: 8-10
**Typical behavior**: Inject constitutional guidance into prompts
**Expected duration**: 20-200ms (may involve LLM calls)

### Validation/Guardrail Hooks

```
*_validator, *_guardrail, *_gate, *_verifier
```

**Estimated count**: 18-22
**Typical behavior**: Enforce constraints, detect violations
**Expected duration**: 10-150ms

### Infrastructure Hooks

```
*_cache, *_manager, *_storage, *_repository
```

**Estimated count**: 10-15
**Typical behavior**: Data persistence, caching, orchestration
**Expected duration**: 5-100ms

---

## Baseline Performance Targets

### Week 1 (Critical 6 hooks)

| Metric | Target | Rationale |
|--------|--------|-----------|
| Instrumentation overhead | <5% | Should not materially impact response time |
| Absolute overhead | <10ms per hook | Acceptable noise floor |
| Span timing accuracy | ±1ms | Sufficient for P50/P95 analysis |
| Event queue latency | <100ms (batch flush) | On-demand flushing acceptable |

### Week 2-3 (Remaining hooks)

| Metric | Target | Rationale |
|--------|--------|-----------|
| Total instrumentation overhead | <3% | Amortized across all hooks |
| 99th percentile latency | <50ms per hook | Detect outliers |
| Trace ID propagation | 100% | Full observability coverage |

---

## Performance Measurement Strategy

### Phase 1: Pre-Instrumentation Baseline (Week 0)

**Action**: Profile critical hooks without @hook_observable decorator

```python
# Manual timing script (run before Week 1)
import time
from pathlib import Path

HOOKS_DIR = Path("P:/.claude/hooks")

results = []
for hook_file in HOOKS_DIR.glob("*.py"):
    start = time.perf_counter()
    # Import and execute hook
    end = time.perf_counter()
    results.append({
        "hook": hook_file.name,
        "duration_ms": (end - start) * 1000
    })
```

### Phase 2: Post-Instrumentation Comparison (Week 1)

**Action**: Measure overhead of @hook_observable decorator

```python
# Compare timing with/without decorator
@hook_observable
def test_hook():
    return {"action": "pass"}

# Run 1000 iterations, measure P50/P95/P99
```

### Phase 3: Continuous Monitoring (Week 2+)

**Action**: Dashboard queries for regression detection

```sql
-- Detect latency regression
SELECT
    hook_name,
    AVG(duration_ms) as avg_ms,
    percentile_95(duration_ms) as p95_ms,
    timestamp
FROM metrics_histograms
WHERE metric_name = 'hook_duration_ms'
    AND timestamp > strftime('%s', 'now', '-7 days') * 1000
GROUP BY hook_name, DATE(timestamp/1000, 'unixepoch')
ORDER BY hook_name, timestamp DESC;
```

---

## Risk Assessment: Performance Impact

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Decorator overhead >10% | Low | Medium | Baseline before/after measurement |
| Trace ID generation slows hooks | Low | Low | UUID generation is fast (<1μs) |
| SQLite writes block hook execution | Medium | High | event_queue batching already in place |
| Metric cardinality explosion | Low | Medium | Label validation enforced |
| JSONL + SQLite dual-write overhead | Low | Low | Asynchronous queue, on-demand flush |

---

## Success Criteria

- [ ] Baseline timing captured for all 6 critical hooks
- [ ] @hook_observable decorator overhead measured <5%
- [ ] Dashboard shows P50/P95/P99 for instrumented hooks
- [ ] No user-facing latency increase detected
- [ ] Trace ID propagation verified end-to-end

---

## Next Steps

1. **Execute baseline profiling** on 6 critical hooks (8h)
2. **Create instrumentation script** to automate before/after comparison
3. **Document baseline metrics** in TSK directory
4. **Proceed to Week 1 implementation** with performance guardrails

---

**Document Status**: Draft - Baseline profiling pending
**Next Review**: After baseline measurements complete
