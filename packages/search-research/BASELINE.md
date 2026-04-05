# unified-search Performance Baseline (Component-Level)

**Generated**: 2026-03-06 15:23:30

## Context

This baseline measures performance of available unified-search **components**:
- QueryCache (LRU cache with TTL)
- BackendHealthRegistry (health tracking)

**Note**: Full unified-search router is not functional due to missing `unified_search.backends` module.
This baseline establishes component-level performance before implementing search-research.

---

## Cache Performance Baseline

### SET Operation

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | 2.53 | 394882 |
| **Median** | 2.5 | - |
| **p95** | 2.59 | - |
| **p99** | 3.5 | - |

### GET Operation (Hit)

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | 2.51 | 397662 |
| **Median** | 2.5 | - |
| **p95** | 2.6 | - |
| **p99** | 3.2 | - |

### GET Operation (Miss)

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | 2.33 | 428394 |
| **Median** | 2.3 | - |
| **p95** | 2.4 | - |
| **p99** | 2.5 | - |

### Cache Statistics

| Metric | Value |
|--------|-------|
| **Hit rate** | 50.0% |
| Total hits | 1000 |
| Total misses | 1000 |

### Regression Thresholds

- **⚠️  WARNING**: Cache ops > 20% slower indicates regression
- **🚨 CRITICAL**: Cache ops > 50% slower indicates severe regression

---

## Backend Health Tracking Baseline

### Record Result Operation

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | 106.3 | 9408 |
| **Median** | 100.8 | - |

### Is Available Operation

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | 0.16 | 6067962 |
| **Median** | 0.2 | - |

### Backend Status

| Metric | Value |
|--------|-------|
| **Status** | ready |
| **Consecutive failures** | 0 |

---

## Methodology

1. **Cache Benchmark**: 1000 SET/GET operations with 5 sample queries
2. **Health Benchmark**: 1000 record_success + check_health operations
3. **Measurement**: `time.perf_counter()` for high-precision timing
4. **Statistics**: Mean, median, p95, p99 latency

## Usage in Tests

```python
# Cache regression check
def test_cache_performance(benchmark):
    from unified_search.cache import QueryCache

    cache = QueryCache(max_size=1000)
    result = benchmark(cache.set, "test", {"data": "test_value"})

    # Regression check
    assert result.stats["mean"] < BASELINE_CACHE_SET_MEAN * 1.20
```

---

## Next Steps

1. ✅ Component baselines established
2. ⚠️  Full router baseline blocked by missing backends module
3. 🔧 Need to investigate unified-search structure or use mock backend

---

*This baseline was established before implementing search-research package features*
