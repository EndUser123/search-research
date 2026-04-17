#!/usr/bin/env python3
"""
Simplified Baseline Performance Benchmark for unified-search

This is a simplified version that tests the components that actually exist:
- Cache performance (QueryCache)
- Backend health tracking (BackendHealthRegistry)
- Query intent classification (if available)

This establishes a baseline before implementing search-research features.
"""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path
from typing import Any

# Add unified-search to path
unified_search_src = Path(__file__).parents[2] / "unified-search" / "src"
sys.path.insert(0, str(unified_search_src))

# Import available components directly from module files (bypassing __init__.py)
try:
    # Direct imports to avoid router.py's backend dependencies
    import importlib.util
    import sys

    # Load cache module
    cache_path = unified_search_src / "unified_search" / "cache.py"
    cache_spec = importlib.util.spec_from_file_location("unified_search.cache", cache_path)
    cache_module = importlib.util.module_from_spec(cache_spec)
    sys.modules["unified_search.cache"] = cache_module
    cache_spec.loader.exec_module(cache_module)
    QueryCache = cache_module.QueryCache

    # Load backend_health module
    health_path = unified_search_src / "unified_search" / "backend_health.py"
    health_spec = importlib.util.spec_from_file_location("unified_search.backend_health", health_path)
    health_module = importlib.util.module_from_spec(health_spec)
    sys.modules["unified_search.backend_health"] = health_module
    health_spec.loader.exec_module(health_module)
    BackendHealthRegistry = health_module.BackendHealthRegistry
    BackendHealth = health_module.BackendHealth

    print("✅ Successfully imported unified-search components")
except Exception as e:
    print(f"ERROR: Cannot import unified-search components: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)


def benchmark_cache_performance() -> dict[str, Any]:
    """Benchmark cache operations."""
    print("💾 Benchmarking cache performance...")

    cache = QueryCache(max_size=1000, ttl_seconds=300)

    # Sample data
    sample_queries = [
        ("async function", {"results": [{"title": "async def"}]}),
        ("authentication", {"results": [{"title": "auth flow"}]}),
        ("database", {"results": [{"title": "db connection"}]}),
        ("error handling", {"results": [{"title": "try/except"}]}),
        ("testing", {"results": [{"title": "pytest"}]}),
    ]

    # Benchmark cache SET operation
    set_times = []
    for query, results in sample_queries * 200:  # 1000 operations
        start = time.perf_counter()
        cache.set(query, results)
        end = time.perf_counter()
        set_times.append((end - start) * 1_000_000)  # Microseconds

    # Benchmark cache GET operation (hit)
    get_hit_times = []
    for query, _ in sample_queries * 200:
        start = time.perf_counter()
        cache.get(query)
        end = time.perf_counter()
        get_hit_times.append((end - start) * 1_000_000)

    # Benchmark cache GET operation (miss)
    get_miss_times = []
    for _ in range(1000):
        start = time.perf_counter()
        cache.get("nonexistent query")
        end = time.perf_counter()
        get_miss_times.append((end - start) * 1_000_000)

    # Get final stats
    stats = cache.get_stats()

    return {
        "set": {
            "mean_us": round(statistics.mean(set_times), 2),
            "median_us": round(statistics.median(set_times), 2),
            "p95_us": round(statistics.quantiles(set_times, n=20)[18], 2),
            "p99_us": round(statistics.quantiles(set_times, n=100)[98], 2),
            "ops_per_sec": round(1_000_000 / statistics.mean(set_times), 0),
        },
        "get_hit": {
            "mean_us": round(statistics.mean(get_hit_times), 2),
            "median_us": round(statistics.median(get_hit_times), 2),
            "p95_us": round(statistics.quantiles(get_hit_times, n=20)[18], 2),
            "p99_us": round(statistics.quantiles(get_hit_times, n=100)[98], 2),
            "ops_per_sec": round(1_000_000 / statistics.mean(get_hit_times), 0),
        },
        "get_miss": {
            "mean_us": round(statistics.mean(get_miss_times), 2),
            "median_us": round(statistics.median(get_miss_times), 2),
            "p95_us": round(statistics.quantiles(get_miss_times, n=20)[18], 2),
            "p99_us": round(statistics.quantiles(get_miss_times, n=100)[98], 2),
            "ops_per_sec": round(1_000_000 / statistics.mean(get_miss_times), 0),
        },
        "stats": {
            "hit_rate": round(stats["hit_rate"] * 100, 2),
            "hits": stats["hits"],
            "misses": stats["misses"],
        }
    }


def benchmark_backend_health() -> dict[str, Any]:
    """Benchmark backend health tracking."""
    print("🏥 Benchmarking backend health tracking...")

    registry = BackendHealthRegistry()

    # Benchmark health check recording
    record_times = []
    for _ in range(1000):
        start = time.perf_counter()
        registry.record_result("CDS", success=True)
        end = time.perf_counter()
        record_times.append((end - start) * 1_000_000)  # Microseconds

    # Benchmark health status retrieval
    check_times = []
    for _ in range(1000):
        start = time.perf_counter()
        registry.is_available("CDS")
        end = time.perf_counter()
        check_times.append((end - start) * 1_000_000)

    # Get stats
    status = registry.get_status("CDS")

    return {
        "record_result": {
            "mean_us": round(statistics.mean(record_times), 2),
            "median_us": round(statistics.median(record_times), 2),
            "ops_per_sec": round(1_000_000 / statistics.mean(record_times), 0),
        },
        "is_available": {
            "mean_us": round(statistics.mean(check_times), 2),
            "median_us": round(statistics.median(check_times), 2),
            "ops_per_sec": round(1_000_000 / statistics.mean(check_times), 0),
        },
        "backend_status": {
            "status": status.status if status else "unknown",
            "consecutive_failures": status.consecutive_failures if status else 0,
        }
    }


def save_baseline_md(results: dict[str, Any], output_path: Path) -> None:
    """Save baseline results as markdown."""
    output_path.parent.mkdir(parents=True, exist_ok=True)

    md_content = f"""# unified-search Performance Baseline (Component-Level)

**Generated**: {time.strftime("%Y-%m-%d %H:%M:%S")}

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
| **Mean** | {results['cache']['set']['mean_us']} | {results['cache']['set']['ops_per_sec']:.0f} |
| **Median** | {results['cache']['set']['median_us']} | - |
| **p95** | {results['cache']['set']['p95_us']} | - |
| **p99** | {results['cache']['set']['p99_us']} | - |

### GET Operation (Hit)

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | {results['cache']['get_hit']['mean_us']} | {results['cache']['get_hit']['ops_per_sec']:.0f} |
| **Median** | {results['cache']['get_hit']['median_us']} | - |
| **p95** | {results['cache']['get_hit']['p95_us']} | - |
| **p99** | {results['cache']['get_hit']['p99_us']} | - |

### GET Operation (Miss)

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | {results['cache']['get_miss']['mean_us']} | {results['cache']['get_miss']['ops_per_sec']:.0f} |
| **Median** | {results['cache']['get_miss']['median_us']} | - |
| **p95** | {results['cache']['get_miss']['p95_us']} | - |
| **p99** | {results['cache']['get_miss']['p99_us']} | - |

### Cache Statistics

| Metric | Value |
|--------|-------|
| **Hit rate** | {results['cache']['stats']['hit_rate']}% |
| Total hits | {results['cache']['stats']['hits']} |
| Total misses | {results['cache']['stats']['misses']} |

### Regression Thresholds

- **⚠️  WARNING**: Cache ops > 20% slower indicates regression
- **🚨 CRITICAL**: Cache ops > 50% slower indicates severe regression

---

## Backend Health Tracking Baseline

### Record Result Operation

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | {results['health']['record_result']['mean_us']} | {results['health']['record_result']['ops_per_sec']:.0f} |
| **Median** | {results['health']['record_result']['median_us']} | - |

### Is Available Operation

| Metric | Value (μs) | Ops/sec |
|--------|-----------|---------|
| **Mean** | {results['health']['is_available']['mean_us']} | {results['health']['is_available']['ops_per_sec']:.0f} |
| **Median** | {results['health']['is_available']['median_us']} | - |

### Backend Status

| Metric | Value |
|--------|-------|
| **Status** | {results['health']['backend_status']['status']} |
| **Consecutive failures** | {results['health']['backend_status']['consecutive_failures']} |

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
    result = benchmark(cache.set, "test", {{"data": "test_value"}})

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
"""

    output_path.write_text(md_content)
    print(f"✅ Baseline saved to: {output_path}")


def main():
    print("=" * 60)
    print("  unified-search Component Baseline Benchmark")
    print("=" * 60)
    print()

    # Run benchmarks
    results = {
        "cache": benchmark_cache_performance(),
        "health": benchmark_backend_health(),
    }

    print()
    print("=" * 60)
    print("  📊 Baseline Results Summary")
    print("=" * 60)
    print(f"Cache SET: {results['cache']['set']['mean_us']}μs mean")
    print(f"Cache GET (hit): {results['cache']['get_hit']['mean_us']}μs mean")
    print(f"Health record: {results['health']['record_result']['mean_us']}μs mean")
    print("=" * 60)
    print()

    # Save results
    output_path = Path(__file__).parent.parent / "BASELINE.md"
    save_baseline_md(results, output_path)

    # Also save JSON for programmatic access
    json_path = output_path.with_suffix(".json")
    json_path.write_text(json.dumps(results, indent=2))
    print(f"✅ JSON saved to: {json_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
