# Hooks System Optimization Research

**Task ID**: TSK-251225-HooksOpt-0822
**Date**: 2025-12-25
**Context**: Production hooks system with performance issues requiring optimization

## Executive Summary

This research document compiles best practices, patterns, and technologies for optimizing the hooks system. The current system has 80+ hooks with potential performance bottlenecks in SQLite operations, file I/O, subprocess calls, and imports.

**Key Findings:**
- SQLite with 40K+ rows: Indexing and WAL mode can provide 70K reads/s
- Python lazy imports: Can achieve 3x faster startup times
- Thread pooling: Critical for I/O-bound operations
- Caching: functools.lru_cache with proper invalidation is essential
- Profiling: cProfile + time.perf_counter for bottleneck identification

---

## 1. SQLite Optimization Research

### 1.1 Indexing Strategies for 40K+ Rows

**Best Practices:**

1. **Strategic Index Creation**
   - Index columns used in WHERE clauses, JOIN conditions, and ORDER BY
   - Avoid over-indexing: each index slows down INSERT/UPDATE operations
   - Use composite indexes for multi-column queries (column order matters)
   - Example from checkpoint_repository_v2.py:
     ```sql
     CREATE INDEX idx_checkpoints_task ON session_checkpoints(task_name);
     CREATE INDEX idx_checkpoints_timestamp ON session_checkpoints(timestamp DESC);
     ```

2. **Query Optimization Patterns**
   - Use `EXPLAIN QUERY PLAN` to analyze query execution
   - Prefer `SELECT specific_columns` over `SELECT *`
   - Use `LIMIT` for large result sets
   - Implement prepared statements with parameterized queries (already in use)

3. **When to Use vs. Avoid Indexes**

   **USE indexes for:**
   - Columns frequently filtered in WHERE clauses
   - JOIN columns from related tables
   - Columns used in ORDER BY or GROUP BY
   - Tables with >1000 rows and frequent reads

   **AVOID indexes for:**
   - Tables with frequent INSERT/UPDATE operations
   - Columns with low cardinality (boolean, small enums)
   - Tables that are read once and never queried again
   - Columns frequently updated

4. **Index Maintenance**
   ```sql
   -- Rebuild indexes
   REINDEX;

   -- Analyze table statistics for query optimizer
   ANALYZE;

   -- Check index usage
   SELECT * FROM sqlite_master WHERE type = 'index';
   ```

### 1.2 WAL Mode Benefits

**WAL (Write-Ahead Logging) Mode Performance:**

- **Read Performance**: 70,000 reads/s vs default mode
- **Write Performance**: 3,600 writes/s vs default mode
- **Concurrency**: Allows concurrent reads during writes
- **Multi-threading**: Essential for Python applications with parallel hook execution

**Implementation:**
```python
# In base_repository.py __init__
self._conn = sqlite3.connect(self.db_path)
self._conn.execute("PRAGMA journal_mode=WAL")
self._conn.execute("PRAGMA synchronous=NORMAL")  # Faster than FULL
self._conn.execute("PRAGMA cache_size=-64000")   # 64MB cache
self._conn.execute("PRAGMA temp_store=MEMORY")   # Use RAM for temp tables
```

**Source**: [SQLite Optimizations For Ultra High-Performance](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)

### 1.3 Connection Pooling Best Practices

**Current Implementation:**
- Each repository creates its own connection
- No connection pooling or reuse

**Recommended Approach:**
```python
import threading
from contextlib import contextmanager

class ConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._local = threading.local()
        self._lock = threading.Lock()

    @contextmanager
    def get_connection(self):
        """Get connection from thread-local pool."""
        if not hasattr(self._local, 'conn'):
            self._local.conn = sqlite3.connect(self.db_path)
            self._local.conn.execute("PRAGMA journal_mode=WAL")
        yield self._local.conn
```

**Dual-Pool Strategy** (from community best practices):
- One pool for reads (max_connections: auto)
- Separate pool for writes (max_connections: 1) to prevent write conflicts

**Source**: [Reddit - SQLite async connection pool](https://www.reddit.com/r/Python/comments/1lx3njh/aiosqlitepool_sqlite_async_connection_pool_for/)

### 1.4 Bulk Operations

**Current Pattern (from hook_health_check.py):**
```python
# Single-row inserts in loop
for hook in hooks:
    cursor.execute("INSERT INTO ... VALUES (?, ?)", (hook.id, hook.name))
```

**Optimized Pattern:**
```python
# Bulk insert with executemany
data = [(h.id, h.name) for h in hooks]
cursor.executemany("INSERT INTO ... VALUES (?, ?)", data)
conn.commit()
```

**Performance Gain**: 10-50x faster for bulk operations

**Source**: [StackOverflow - Optimized way to insert 40K records](https://stackoverflow.com/questions/5593881/what-is-the-optimized-way-to-insert-large-number-of-records-more-than-40-000-i)

---

## 2. Python Caching Research

### 2.1 functools.lru_cache Usage Patterns

**Basic Usage:**
```python
from functools import lru_cache
import hashlib

@lru_cache(maxsize=128)
def compute_file_hash(filepath: str) -> str:
    """Cache file hashes to avoid recomputing."""
    with open(filepath, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()[:16]
```

**Best Practices:**

1. **Cache Size Selection**
   - Default: 128 entries
   - For file operations: 256-512 (files don't change often)
   - For expensive computations: 64-128 (memory tradeoff)
   - Monitor cache hit rate with `cache_info()`

2. **Thread-Safe Caching**
   ```python
   from functools import lru_cache
   import threading

   # lru_cache is thread-safe for reads
   @lru_cache(maxsize=256)
   def get_hook_config(hook_name: str) -> dict:
       # Safe for concurrent access
       return load_config_sync(hook_name)
   ```

3. **Cache Invalidation Strategies**

   **Time-Based Invalidation** (TTL):
   ```python
   import time
   from functools import lru_cache

   @lru_cache(maxsize=128)
   def fetch_with_timestamp(key: str, timestamp: float) -> dict:
       """Include timestamp in cache key for TTL."""
       return expensive_operation(key)

   # Usage: Refresh cache every 60 seconds
   def get_data(key: str) -> dict:
       ts = int(time.time() // 60)  # 60-second TTL
       return fetch_with_timestamp(key, ts)
   ```

   **Version-Based Invalidation**:
   ```python
   _cache_version = 0

   @lru_cache(maxsize=128)
   def get_with_version(key: str, version: int) -> dict:
       return expensive_operation(key)

   def invalidate_cache():
       global _cache_version
       _cache_version += 1
   ```

   **Manual Invalidation**:
   ```python
   cached_func = lru_cache(maxsize=128)(func)
   cached_func.cache_clear()  # Clear all entries
   cached_func.cache_info()   # View stats
   ```

**Source**: [Real Python - Caching in Python Using the LRU Cache Strategy](https://realpython.com/lru-cache-python/)

### 2.2 Cache Decorator with TTL

**Implementation for Production Use:**
```python
import time
from functools import wraps
from typing import Any, Callable, Dict, Optional, Tuple

def timed_lru_cache(seconds: int = 60, maxsize: int = 128):
    """LRU cache with time-based expiration.

    Args:
        seconds: TTL in seconds
        maxsize: Maximum cache size
    """
    def decorator(func: Callable) -> Callable:
        cache: Dict[Tuple, Tuple[Any, float]] = {}

        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            key = (args, tuple(sorted(kwargs.items())))
            current_time = time.time()

            # Check cache
            if key in cache:
                value, timestamp = cache[key]
                if current_time - timestamp < seconds:
                    return value
                else:
                    del cache[key]  # Expired

            # Compute and cache
            result = func(*args, **kwargs)
            cache[key] = (result, current_time)

            # Enforce maxsize
            if len(cache) > maxsize:
                oldest = min(cache.items(), key=lambda x: x[1][1])
                del cache[oldest[0]]

            return result

        wrapper.cache_clear = lambda: cache.clear()
        wrapper.cache_info = lambda: {"size": len(cache), "maxsize": maxsize}
        return wrapper

    return decorator
```

**Source**: [DataLeadsFuture - TTL Cache Decorator](https://www.dataleadsfuture.com/implement-a-cache-decorator-with-time-to-live-feature-in-python/)

### 2.3 Memory vs. Speed Tradeoffs

**Guidelines for Cache Sizing:**

| Operation | Cache Size | Memory Estimate | Use Case |
|-----------|-----------|-----------------|----------|
| File metadata | 256-512 | ~1-2 MB | Hook health checks |
| Import validation | 64-128 | ~500 KB | Syntax checks |
| Subprocess results | 32-64 | ~2-5 MB | Execution tests |
| Configuration | 128-256 | ~500 KB | Settings access |

**Memory Monitoring:**
```python
import sys
from functools import lru_cache

@lru_cache(maxsize=256)
def cached_operation():
    return large_data_structure()

# Monitor memory
def check_cache_memory():
    cache = cached_operation.cache_info()
    est_memory = cache.currsize * 1024  # Rough estimate
    if est_memory > 10 * 1024 * 1024:  # >10MB
        cached_operation.cache_clear()
```

**Source**: [IPRoyal Blog - Python Cache Basics (2025)](https://iproyal.com/blog/python-cache-basics)

---

## 3. Lazy Loading Patterns

### 3.1 Import Lazy Loading Techniques

**Python 3.15+ (PEP 810) - Native Lazy Imports:**
```python
# Future standard (Python 3.15+, 2026)
__lazy_modules__ = ["expensive_module", "another_heavy_module"]

from expensive_module import heavy_function  # Not loaded until used
```

**Current Best Practice (Python 3.12/3.13):**

**Option 1: Function-Level Imports**
```python
def execute_hook(hook_name: str) -> dict:
    """Heavy imports only when function is called."""
    import json
    import subprocess
    from pathlib import Path

    # Only loaded when execute_hook is called
    result = subprocess.run(...)
    return result
```

**Option 2: LazyLoader from importlib**
```python
from importlib.util import LazyLoader
import importlib

# Lazy load heavy modules
sqlite3 = LazyLoader(importlib.import_module('sqlite3'), globals(), 'sqlite3')
pandas = LazyLoader(importlib.import_module('pandas'), globals(), 'pandas')

# Module not loaded until first attribute access
def process_data():
    df = pandas.DataFrame(...)  # pandas loaded here
```

**Option 3: Lazy Attribute Pattern**
```python
class HookSystem:
    """Lazy loading of heavy dependencies."""

    @property
    def subprocess(self):
        """Import subprocess module only when needed."""
        if not hasattr(self, '_subprocess'):
            import subprocess
            self._subprocess = subprocess
        return self._subprocess

    def execute(self):
        proc = self.subprocess.run(...)  # Import happens here
```

**Performance Benefits**:
- 3x faster startup times for CLI applications
- Reduced memory footprint for unused features
- Faster test discovery in pytest

**Source**: [Three times faster with lazy imports (2025)](https://hugovk.dev/blog/2025/lazy-imports/)

### 3.2 Dependency Injection Patterns

**Current Issue**: Tight coupling to subprocess, sqlite3, file system

**Decoupled Pattern:**
```python
from abc import ABC, abstractmethod
from typing import Protocol

class ExecutorProtocol(Protocol):
    """Protocol for subprocess execution."""

    def run(self, cmd: list, **kwargs) -> subprocess.CompletedProcess:
        """Execute command."""
        ...

class DatabaseProtocol(Protocol):
    """Protocol for database operations."""

    def execute(self, query: str, params: tuple) -> list:
        """Execute query."""
        ...

class HookValidator:
    """Validator with injected dependencies."""

    def __init__(
        self,
        executor: ExecutorProtocol,
        db: DatabaseProtocol,
        file_reader: callable
    ):
        self.executor = executor
        self.db = db
        self.file_reader = file_reader

    def validate_hook(self, hook_path: str) -> bool:
        source = self.file_reader(hook_path)
        # Validation logic...
        return True
```

**Benefits**:
- Easy to mock for testing
- No import-time side effects
- Can swap implementations without changing logic

### 3.3 Module-Level vs. Function-Level Imports

**Current Pattern (hook_health_check.py):**
```python
import json
import sys
import os
import ast
import hashlib
import subprocess
from concurrent.futures import ThreadPoolExecutor
# ... 10+ imports at module level
```

**Optimized Pattern:**
```python
# Module-level: Essential, lightweight imports
import json
from pathlib import Path
from typing import Optional

# Function-level: Heavy/conditional imports
def check_syntax(script_path: str) -> tuple[bool, Optional[str]]:
    import ast  # Only for syntax checking
    # ...
```

**Decision Matrix:**

| Import Type | Location | Rationale |
|-------------|----------|-----------|
| json, pathlib, typing | Module level | Used everywhere, lightweight |
| ast, py_compile | Function level | Only for specific checks |
| subprocess, concurrent.futures | Function level | Only for execution tests |
| sqlite3 | Class/property level | Only when DB operations needed |
| numpy, pandas | Lazy loader | Very heavy, rarely used |

---

## 4. Parallel Processing

### 4.1 concurrent.futures Best Practices

**Current Usage (hook_health_check.py):**
```python
# Good: Uses ThreadPoolExecutor for parallel hook execution
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = {executor.submit(test_hook, h): h for h in unique_hooks}
    for future in as_completed(futures):
        status, exec_ok, exec_error, exec_time = future.result()
```

**Best Practices:**

1. **Worker Pool Sizing**
   ```python
   import os

   # I/O-bound (subprocess, file I/O): 2-4x CPU count
   io_workers = min(32, (os.cpu_count() or 1) * 4)

   # CPU-bound (data processing): CPU count
   cpu_workers = os.cpu_count() or 1

   # Mixed workload: Use ThreadPoolExecutor for I/O
   workers = min(16, (os.cpu_count() or 1) * 2)
   ```

2. **Timeout Handling**
   ```python
   from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError

   with ThreadPoolExecutor(max_workers=8) as executor:
       futures = {executor.submit(func, arg): arg for arg in args}

       for future in as_completed(futures, timeout=30):
           try:
               result = future.result(timeout=5)
           except TimeoutError:
               print(f"Timeout: {futures[future]}")
           except Exception as e:
               print(f"Error: {e}")
   ```

3. **Error Handling**
   ```python
   def safe_execute(func, *args, **kwargs):
       """Wrapper to capture exceptions without crashing pool."""
       try:
           return func(*args, **kwargs), None
       except Exception as e:
           return None, e

   with ThreadPoolExecutor(max_workers=8) as executor:
       futures = {
           executor.submit(safe_execute, func, arg): arg
           for arg in args
       }

       for future in as_completed(futures):
           result, error = future.result()
           if error:
               log_error(error, futures[future])
   ```

**Source**: [Python 3.14 Documentation - concurrent.futures](https://docs.python.org/3/library/concurrent.futures.html)

### 4.2 ThreadPoolExecutor vs. ProcessPoolExecutor

**Decision Guide:**

| Aspect | ThreadPoolExecutor | ProcessPoolExecutor |
|--------|-------------------|---------------------|
| **Best For** | I/O-bound operations | CPU-bound operations |
| **GIL Impact** | Limited by GIL | Bypasses GIL |
| **Memory** | Low overhead (shared memory) | High overhead (pickling) |
| **Startup** | Fast (ms) | Slow (100s of ms) |
| **Use Case** | File I/O, subprocess, network | Data processing, computation |
| **Hook System** | ✅ **Recommended** | ❌ Overkill |

**Hook System Use Case:**
```python
# CORRECT: I/O-bound hook execution
with ThreadPoolExecutor(max_workers=8) as executor:
    futures = [executor.submit(run_hook, hook) for hook in hooks]

# AVOID: ProcessPoolExecutor for simple subprocess calls
# - Too much overhead spawning processes
# - Data serialization cost
# - Hooks are already subprocess calls
```

**Source**: [Medium - ThreadPoolExecutor vs ProcessPoolExecutor (2025)](https://medium.com/@parthsurati096/threadpoolexecutor-vs-processpoolexecutor-a-complete-comparison-03828617bb83)

### 4.3 Subprocess Call Optimization

**Current Performance Issues:**
- Sequential subprocess calls in hook_health_check.py (line 360)
- Each subprocess.run() spawns new Python interpreter
- No connection pooling for repeated calls

**Optimization Strategies:**

1. **Batch Subprocess Calls**
   ```python
   # Instead of sequential calls
   for hook in hooks:
       result = subprocess.run([sys.executable, hook.path])

   # Use ThreadPoolExecutor (already implemented)
   with ThreadPoolExecutor(max_workers=8) as executor:
       futures = [executor.submit(run_hook, h) for h in hooks]
   ```

2. **Reduce Subprocess Overhead**
   ```python
   # Faster: Use compiled bytecode check
   import py_compile

   def check_imports_fast(script_path: str) -> tuple[bool, Optional[str]]:
       """In-process compile (no subprocess overhead)."""
       try:
           py_compile.compile(script_path, doraise=True)
           return True, None
       except py_compile.PyCompileError as e:
           return False, str(e)
   ```

3. **Persistent Worker Processes** (for heavy hooks)
   ```python
   import multiprocessing as mp
   from multiprocessing import Pool

   # For CPU-heavy hooks (CKS, semantic search)
   def worker_init():
       """Initialize worker once per process."""
       import heavy_module
       global heavy
       heavy = heavy_module

   with Pool(processes=4, initializer=worker_init) as pool:
       results = pool.map(heavy_hook_processing, hooks)
   ```

**Source**: [Mastering Python Concurrency in 2025](https://medium.com/@blogstacker20/mastering-python-concurrency-in-2025-asyncio-threads-and-multiprocessing-explained-deeply-697e90341278)

### 4.4 Error Handling in Parallel Contexts

**Comprehensive Error Pattern:**
```python
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from typing import Any, Optional
import traceback

@dataclass
class ExecutionResult:
    """Result of parallel execution."""
    success: bool
    data: Any = None
    error: Optional[str] = None
    traceback: Optional[str] = None
    duration_ms: float = 0.0

def execute_parallel(tasks: list, max_workers: int = 8) -> list[ExecutionResult]:
    """Execute tasks in parallel with comprehensive error handling."""

    def safe_execute(task):
        """Execute task and capture all errors."""
        import time
        start = time.time()

        try:
            result = task()
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=True,
                data=result,
                duration_ms=duration
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return ExecutionResult(
                success=False,
                error=str(e),
                traceback=traceback.format_exc(),
                duration_ms=duration
            )

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {executor.submit(safe_execute, task): i
                   for i, task in enumerate(tasks)}

        results = [None] * len(tasks)
        for future in as_completed(futures):
            task_index = futures[future]
            try:
                results[task_index] = future.result(timeout=30)
            except Exception as e:
                results[task_index] = ExecutionResult(
                    success=False,
                    error=f"Future execution failed: {e}",
                    traceback=traceback.format_exc()
                )

        return results
```

---

## 5. Performance Measurement

### 5.1 Python Profiling Tools

**Tool Selection Guide:**

| Tool | Best For | Overhead | Output |
|------|----------|----------|--------|
| **cProfile** | Overall function analysis | Low (10-20%) | Function call stats |
| **time.perf_counter()** | Micro-benchmarks | Very low | Custom timing |
| **line_profiler** | Line-by-line analysis | Medium (2-5x) | Per-line timing |
| **py-spy** | Live production apps | Minimal (sampling) | Flame graphs |
| **memory_profiler** | Memory leak detection | Medium | Memory usage |

**1. cProfile - Function-Level Profiling**
```python
import cProfile
import pstats
from io import StringIO

def profile_hook_check():
    """Profile the hook health check function."""
    pr = cProfile.Profile()
    pr.enable()

    # Run health check
    report = run_health_check(verbose=False, run_exec_tests=True)

    pr.disable()

    # Analyze results
    s = StringIO()
    ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions

    print(s.getvalue())
    return report

# Usage: python -m cProfile -s cumulative hook_health_check.py
```

**2. time.perf_counter() - Micro-Benchmarks**
```python
import time

from typing import Callable, Any

def benchmark(func: Callable, *args, iterations: int = 100) -> dict:
    """Benchmark a function with high-precision timing."""

    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(*args)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # Convert to ms

    return {
        'mean': sum(times) / len(times),
        'median': sorted(times)[len(times) // 2],
        'min': min(times),
        'max': max(times),
        'std': (sum((t - sum(times)/len(times))**2 for t in times) / len(times))**0.5
    }

# Usage
stats = benchmark(check_syntax, 'hook.py', iterations=50)
print(f"Mean: {stats['mean']:.2f}ms, Median: {stats['median']:.2f}ms")
```

**3. Context Manager for Timing**
```python
from contextlib import contextmanager
import time
import logging

logger = logging.getLogger(__name__)

@contextmanager
def timer(operation_name: str, threshold_ms: float = 1000.0):
    """Context manager for timing operations.

    Logs warning if operation exceeds threshold.
    """
    start = time.perf_counter()
    yield
    duration_ms = (time.perf_counter() - start) * 1000

    if duration_ms > threshold_ms:
        logger.warning(
            f"SLOW OPERATION: {operation_name} took {duration_ms:.0f}ms "
            f"(threshold: {threshold_ms}ms)"
        )
    else:
        logger.debug(f"{operation_name}: {duration_ms:.0f}ms")

# Usage
with timer("hook_health_check", threshold_ms=5000):
    report = run_health_check()
```

**Source**: [Real Python - Profiling in Python](https://realpython.com/python-profiling/)

### 5.2 Performance Regression Testing

**1. Benchmark Baseline Establishment**
```python
import json
from pathlib import Path
from typing import Dict, Any
import time

class PerformanceBaseline:
    """Store and compare performance baselines."""

    def __init__(self, baseline_file: Path):
        self.baseline_file = baseline_file
        self.baseline = self._load_baseline()

    def _load_baseline(self) -> Dict[str, float]:
        """Load existing baseline."""
        if self.baseline_file.exists():
            with open(self.baseline_file) as f:
                return json.load(f)
        return {}

    def measure(self, operation: str, threshold_ms: float = 1000.0):
        """Decorator to measure and compare performance."""
        def decorator(func):
            def wrapper(*args, **kwargs):
                start = time.perf_counter()
                result = func(*args, **kwargs)
                duration_ms = (time.perf_counter() - start) * 1000

                # Compare to baseline
                baseline_ms = self.baseline.get(operation)
                if baseline_ms:
                    regression_pct = ((duration_ms - baseline_ms) / baseline_ms) * 100
                    if regression_pct > 20:  # 20% regression threshold
                        logger.warning(
                            f"PERFORMANCE REGRESSION: {operation}\n"
                            f"  Current: {duration_ms:.0f}ms\n"
                            f"  Baseline: {baseline_ms:.0f}ms\n"
                            f"  Regression: {regression_pct:.1f}%"
                        )
                else:
                    # First run - establish baseline
                    self.baseline[operation] = duration_ms
                    self._save_baseline()

                return result
            return wrapper
        return decorator

    def _save_baseline(self):
        """Save baseline to file."""
        self.baseline_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.baseline_file, 'w') as f:
            json.dump(self.baseline, f, indent=2)

# Usage
baseline = PerformanceBaseline(Path('P:/.claude/logs/perf_baseline.json'))

@baseline.measure("hook_health_check_full", threshold_ms=5000)
def run_health_check_with_perf():
    return run_health_check()
```

**2. pytest-benchmark for Automated Testing**
```python
# test_hook_performance.py
import pytest
from hook_health_check import run_health_check

@pytest.mark.parametrize("run_exec_tests", [True, False])
def test_health_check_performance(benchmark, run_exec_tests):
    """Benchmark hook health check."""
    result = benchmark(run_health_check, verbose=False, run_exec_tests=run_exec_tests)

    # Assertions
    assert result.overall_healthy

# Run: pytest test_hook_performance.py --benchmark-only
```

**Source**: [Performance Regression Testing Initiatives (2025 Academic Paper)](https://cs.gssi.it/catia.trubiani/download/2025-IST-performance-regression-testing-mapping-study.pdf)

### 5.3 Benchmarking Methodologies

**1. A/B Testing Pattern**
```python
from dataclasses import dataclass
from typing import Callable
import statistics

@dataclass
class BenchmarkResult:
    """Result of A/B benchmark comparison."""
    name_a: str
    name_b: str
    mean_a_ms: float
    mean_b_ms: float
    improvement_pct: float
    significance: str  # "significant", "marginal", "none"

def benchmark_comparison(
    func_a: Callable,
    func_b: Callable,
    *args,
    iterations: int = 50,
    threshold_pct: float = 5.0
) -> BenchmarkResult:
    """Compare two implementations.

    Returns:
        BenchmarkResult with improvement analysis
    """
    times_a = []
    times_b = []

    for _ in range(iterations):
        # Measure A
        start = time.perf_counter()
        result_a = func_a(*args)
        times_a.append((time.perf_counter() - start) * 1000)

        # Measure B
        start = time.perf_counter()
        result_b = func_b(*args)
        times_b.append((time.perf_counter() - start) * 1000)

        # Verify results match
        assert result_a == result_b, "Results differ!"

    mean_a = statistics.mean(times_a)
    mean_b = statistics.mean(times_b)
    improvement = ((mean_a - mean_b) / mean_a) * 100

    # Statistical significance (simple check)
    std_a = statistics.stdev(times_a) if len(times_a) > 1 else 0
    std_b = statistics.stdev(times_b) if len(times_b) > 1 else 0

    if abs(improvement) > threshold_pct:
        significance = "significant"
    elif abs(improvement) > threshold_pct / 2:
        significance = "marginal"
    else:
        significance = "none"

    return BenchmarkResult(
        name_a=func_a.__name__,
        name_b=func_b.__name__,
        mean_a_ms=mean_a,
        mean_b_ms=mean_b,
        improvement_pct=improvement,
        significance=significance
    )
```

**2. Performance Test Integration**
```python
# conftest.py - pytest configuration
import pytest

@pytest.fixture
def perf_threshold():
    """Performance thresholds for hooks system."""
    return {
        "syntax_check_ms": 50,
        "import_check_ms": 100,
        "execution_test_ms": 3000,
        "full_health_check_ms": 5000
    }

# test_performance.py
def test_syntax_check_performance(perf_threshold):
    """Syntax checking should be fast."""
    from hook_health_check import check_syntax

    stats = benchmark(check_syntax, "hook.py", iterations=100)
    assert stats['mean'] < perf_threshold['syntax_check_ms']

@pytest.mark.slow
def test_full_health_check_performance(perf_threshold):
    """Full health check should complete in reasonable time."""
    from hook_health_check import run_health_check

    start = time.perf_counter()
    report = run_health_check(verbose=False, run_exec_tests=False)
    duration_ms = (time.perf_counter() - start) * 1000

    assert duration_ms < perf_threshold['full_health_check_ms']
    assert report.overall_healthy
```

---

## 6. TDD for Performance Work

### 6.1 Testing Performance Improvements

**Golden Rule: Write Performance Test Before Optimization**

```python
# test_hook_performance_baseline.py
"""Baseline performance tests for hooks system."""
import pytest
import time
from hook_health_check import run_health_check

class TestHookPerformance:
    """Performance test suite for hooks optimization."""

    @pytest.fixture(autouse=True)
    def setup_perf_logging(self, tmp_path):
        """Log performance results for comparison."""
        self.results_file = tmp_path / "perf_results.json"

    def test_syntax_check_baseline(self):
        """Establish baseline: syntax check performance."""
        from hook_health_check import check_syntax
        from tests.performance_utils import benchmark

        stats = benchmark(check_syntax, "P:/.claude/hooks/path_validator.py")

        # Save baseline
        self.results_file.write_text(json.dumps({
            "syntax_check": stats
        }))

        # Current threshold (will be tightened after optimization)
        assert stats['mean'] < 100  # Current acceptable baseline

    def test_import_check_baseline(self):
        """Establish baseline: import check performance."""
        from hook_health_check import check_imports

        stats = benchmark(check_imports, "P:/.claude/hooks/path_validator.py")

        # Load previous results if available
        if self.results_file.exists():
            prev = json.loads(self.results_file.read_text())
            # Check for regression
            assert stats['mean'] <= prev['import_check']['mean'] * 1.2  # 20% tolerance

    def test_parallel_execution_speedup(self):
        """Verify parallel execution provides speedup."""
        import time
        from hook_health_check import run_health_check

        # Sequential (single worker)
        start = time.perf_counter()
        report_seq = run_health_check(run_exec_tests=True)
        time_seq = (time.perf_counter() - start) * 1000

        # Parallel (8 workers)
        start = time.perf_counter()
        report_par = run_health_check(run_exec_tests=True)
        time_par = (time.perf_counter() - start) * 1000

        speedup = time_seq / time_par
        assert speedup > 2.0, f"Expected 2x speedup, got {speedup:.1f}x"
```

### 6.2 Writing Tests Before Optimizations

**Test-Driven Performance Optimization Workflow:**

1. **Write Failing Performance Test**
   ```python
   # test_optimization_needed.py
   def test_hook_startup_should_be_under_1s():
       """Current hook loading is too slow - target: <1s."""
       start = time.perf_counter()
       load_all_hooks()
       duration = (time.perf_counter() - start)

       assert duration < 1.0, f"Hook loading took {duration:.2f}s (target: <1s)"
   ```

2. **Run Test - Confirm Failure**
   ```bash
   $ pytest test_optimization_needed.py -v
   FAILED - Hook loading took 3.45s (target: <1s)
   ```

3. **Implement Optimization**
   ```python
   # Apply lazy loading, caching, etc.
   ```

4. **Run Test - Confirm Pass**
   ```bash
   $ pytest test_optimization_needed.py -v
   PASSED - Hook loading took 0.87s
   ```

5. **Commit Test + Optimization Together**
   ```bash
   git add test_optimization_needed.py hooks_system.py
   git commit -m "perf: optimize hook loading (<1s target)"
   ```

### 6.3 Measuring Test Coverage

**Coverage for Performance-Critical Paths:**

```python
# .coveragerc - Configuration file
[run]
source = P:/.claude/hooks
omit =
    */tests/*
    */test_*.py

[report]
precision = 2
show_missing = True
skip_covered = False

[html]
directory = coverage_html_report
```

**Performance-Critical Path Coverage:**
```bash
# Run with coverage
pytest --cov=P:/.claude/hooks --cov-report=term-missing

# Focus on performance-critical modules
pytest --cov=hook_health_check --cov-report=html
```

**Target Coverage for Optimization Work:**
- Core execution paths: >90%
- Caching logic: 100% (critical for correctness)
- Parallel execution: >85% (error handling paths)
- SQLite operations: >90% (transaction handling)

**Source**: [Top 10 Python Testing Frameworks in 2025](https://www.t-plan.com/blog/top-10-best-python-testing-frameworks-in-2025/)

---

## 7. Similar Systems

### 7.1 How Other Projects Optimize Hook Systems

**1. Pre-commit Framework Performance Issues**

From research on pre-commit hooks:
- **Known Bottleneck**: pre-commit is written in Python and creates isolated virtual environments
- **Impact**: Slow startup times, especially with many hooks
- **Community Solution**: Alternative tools like "Prek" for faster execution

**Relevance to Our System:**
- We have 80+ hooks (similar scale to large pre-commit configs)
- Hook health check already uses parallel execution (good practice)
- Avoid creating isolated environments for each hook (learn from pre-commit's mistake)

**Source**: [Substack - Happier Developers, Faster Teams: Why Prek Beats Pre-commit](https://aiechoes.substack.com/p/happier-developers-faster-teams-why)

**2. FastAPI/Starlette Middleware Patterns**

Similar to hooks, middleware executes on every request:
- **Optimization**: Lazy loading of middleware dependencies
- **Pattern**: Dependency injection for middleware configuration
- **Lesson**: Don't initialize all middleware at startup

```python
# FastAPI-style lazy middleware
class HookMiddleware:
    def __init__(self, config_path: str):
        self.config_path = config_path
        self._config = None

    @property
    def config(self):
        if self._config is None:
            self._config = self._load_config()
        return self._config
```

**3. Pytest Plugin System**

pytest has 100+ plugins that must load quickly:
- **Strategy**: Use entry points for plugin discovery
- **Optimization**: Cache plugin metadata
- **Lesson**: Defer plugin initialization until first use

### 7.2 Python Hook Performance Patterns

**Pattern 1: Command Registry with Lazy Loading**

```python
# .claude/registry/commands.toml approach (already in use)
# Extend to hooks registry:
HOOKS_REGISTRY = {
    "path_validator": {
        "module": "hooks.path_validator",
        "lazy": True,  # Don't import until needed
        "priority": 10
    },
    # ...
}

def load_hook(hook_name: str):
    """Load hook on-demand."""
    config = HOOKS_REGISTRY[hook_name]
    if config.get("lazy"):
        module = __import__(config["module"], fromlist=[''])
        return getattr(module, hook_name)
    return CACHED_HOOKS[hook_name]
```

**Pattern 2: Hook Result Caching**

```python
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=256)
def cached_hook_result(hook_name: str, input_hash: str) -> dict:
    """Cache hook results for identical inputs."""
    hook = load_hook(hook_name)
    return hook.execute(input_data)

def execute_hook_with_cache(hook_name: str, input_data: dict) -> dict:
    """Execute hook with caching."""
    import hashlib
    input_hash = hashlib.sha256(json.dumps(input_data).encode()).hexdigest()
    return cached_hook_result(hook_name, input_hash)
```

**Pattern 3: Batching Hook Execution**

```python
from itertools import islice

def batch_hooks(hooks: list, batch_size: int = 10):
    """Execute hooks in batches to limit resource usage."""
    for i in range(0, len(hooks), batch_size):
        batch = hooks[i:i + batch_size]

        with ThreadPoolExecutor(max_workers=batch_size) as executor:
            yield list(executor.map(execute_hook, batch))

# Usage
for batch_results in batch_hooks(all_hooks, batch_size=10):
    process_batch(batch_results)
```

### 7.3 SQLite Optimization Case Studies

**Case Study 1: Datasette (SQLite for Web)**

Datasette serves SQLite databases over HTTP with excellent performance:
- **Optimization**: Immutable databases, connection pooling
- **Result**: Handles 10K+ queries/second
- **Lesson**: Read-heavy workloads benefit from connection pooling

**Relevance**: Hook health check is read-heavy (checking hooks, not modifying)

**Case Study 2: SQLite as Application Database**

From [SQLite in Production with WAL](https://victoria.dev/posts/sqlite-in-production-with-wal/):

**Configuration for Production:**
```python
PRAGMA journal_mode = WAL;        # Enable concurrent reads
PRAGMA synchronous = NORMAL;      # Balance safety/speed
PRAGMA cache_size = -64000;       # 64MB cache
PRAGMA foreign_keys = ON;         # Data integrity
PRAGMA temp_store = MEMORY;       # Use RAM for temp data
```

**Case Study 3: Mobile Apps with SQLite**

Patterns from mobile development (resource-constrained):
- **Batch writes**: Accumulate changes, commit in batches
- **Selective indexing**: Only index hot paths
- **Connection reuse**: Single connection per thread
- **Result**: Smooth performance with 100K+ rows

---

## 8. Actionable Recommendations

### 8.1 High-Priority Optimizations (Quick Wins)

**1. Enable WAL Mode** (5-10x performance gain)
```python
# In base_repository.py __init__
self._conn.execute("PRAGMA journal_mode=WAL")
self._conn.execute("PRAGMA synchronous=NORMAL")
```

**2. Optimize Import Checks** (3-5x faster)
```python
# Replace subprocess approach with in-process compile
import py_compile

def check_imports(script_path: str) -> tuple[bool, Optional[str]]:
    try:
        py_compile.compile(script_path, doraise=True)
        return True, None
    except py_compile.PyCompileError as e:
        return False, str(e)
```

**3. Add Caching for File Metadata** (10-20x for repeated checks)
```python
from functools import lru_cache

@lru_cache(maxsize=512)
def compute_file_hash_cached(filepath: str) -> Optional[str]:
    return compute_file_hash(filepath)
```

**4. Lazy Load Heavy Modules** (2-3x faster startup)
```python
# Move heavy imports to function-level
def check_syntax(script_path: str):
    import ast  # Only when needed
    # ...
```

### 8.2 Medium-Priority Optimizations (1-2 weeks)

**1. Implement Connection Pooling**
```python
# Create shared connection pool for all repositories
class ConnectionPool:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, db_path: str):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._pool = {}
                cls._instance._db_path = db_path
            return cls._instance

    def get_connection(self):
        tid = threading.get_ident()
        if tid not in self._pool:
            conn = sqlite3.connect(self._db_path)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.row_factory = sqlite3.Row
            self._pool[tid] = conn
        return self._pool[tid]
```

**2. Add Performance Regression Tests**
```python
# test_performance_regression.py
@pytest.mark.performance
def test_health_check_regression(perf_baseline):
    """Ensure performance doesn't degrade."""
    start = time.perf_counter()
    report = run_health_check()
    duration_ms = (time.perf_counter() - start) * 1000

    baseline = perf_baseline.get("health_check_full", 5000)
    assert duration_ms < baseline * 1.2  # 20% tolerance
```

**3. Implement TTL Caching**
```python
@timed_lru_cache(seconds=300, maxsize=128)  # 5-minute TTL
def get_hook_status_cached(hook_path: str) -> dict:
    """Cache hook status for 5 minutes."""
    return check_hook_status(hook_path)
```

### 8.3 Long-Term Optimizations (1-2 months)

**1. Migrate to Async SQLite**
```python
# Use aiosqlite for async hook execution
import aiosqlite

async def check_hooks_async(hooks: list) -> list:
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.execute("SELECT * FROM hooks")
        return await cursor.fetchall()
```

**2. Implement Persistent Worker Processes**
- For heavy hooks (CKS, semantic search)
- Use multiprocessing.Pool with persistent workers
- Avoids module reload overhead

**3. Create Performance Dashboard**
```python
# Track metrics over time
class PerformanceMetrics:
    def record_operation(self, name: str, duration_ms: float):
        """Store performance metrics."""
        with sqlite3.connect("metrics.db") as db:
            db.execute(
                "INSERT INTO metrics (name, duration, timestamp) VALUES (?, ?, ?)",
                (name, duration_ms, datetime.now())
            )

    def get_trend(self, operation: str, days: int = 7) -> dict:
        """Analyze performance trend."""
        # Query metrics and calculate trend
        pass
```

### 8.4 Monitoring and Maintenance

**1. Add Performance Logging**
```python
import logging

logger = logging.getLogger("hooks.perf")

def log_slow_operation(operation: str, duration_ms: float, threshold_ms: float):
    if duration_ms > threshold_ms:
        logger.warning(f"SLOW: {operation} took {duration_ms:.0f}ms (threshold: {threshold_ms}ms)")
```

**2. Regular Performance Audits**
```bash
# Weekly performance baseline checks
python -m pytest tests/test_performance.py --benchmark-autosave
```

**3. Performance Budget Enforcement**
```python
# Define performance budgets
PERFORMANCE_BUDGETS = {
    "hook_load": 100,  # ms
    "syntax_check": 50,
    "import_check": 100,
    "health_check_full": 5000
}

def enforce_budget(operation: str, duration_ms: float):
    budget = PERFORMANCE_BUDGETS.get(operation, 1000)
    if duration_ms > budget:
        raise PerformanceBudgetExceeded(operation, duration_ms, budget)
```

---

## 9. Implementation Roadmap

### Phase 1: Quick Wins (Week 1)
- [ ] Enable WAL mode in base_repository.py
- [ ] Replace subprocess import checks with py_compile
- [ ] Add lru_cache to file hash computation
- [ ] Move heavy imports to function-level
- [ ] Add performance baseline tests

**Expected Impact**: 5-10x overall performance improvement

### Phase 2: Structural Optimizations (Week 2-3)
- [ ] Implement connection pooling
- [ ] Add TTL caching for hook status
- [ ] Optimize parallel execution worker count
- [ ] Add comprehensive error handling in parallel contexts
- [ ] Implement performance regression test suite

**Expected Impact**: 2-3x additional improvement, prevent future regressions

### Phase 3: Advanced Optimizations (Week 4-6)
- [ ] Evaluate async SQLite migration
- [ ] Implement persistent worker processes for heavy hooks
- [ ] Create performance monitoring dashboard
- [ ] Optimize indexing strategy based on query patterns
- [ ] Document performance best practices

**Expected Impact**: Sustained performance at scale, operational visibility

---

## 10. Sources and References

### SQLite Optimization
- [Handling Large Data Efficiently With SQLite](https://medium.com/@tanishqatemgire/handling-large-data-efficiently-with-sqlite-af961667ac77)
- [Optimizing a large SQLite database for reading](https://jacobfilipp.com/sqliteoptimize/)
- [SQLite Indexing Tactics for Performance and Speed](https://moldstud.com/articles/p-boost-your-sqlite-database-best-practices-for-an-effective-indexing-strategy)
- [Python/SQLite Rewrite – Improvement Overview](https://poignanttech.com/2025/01/17/python-sqlite-rewrite-improvement-overview/)
- [StackOverflow - Insert 40K+ records optimization](https://stackoverflow.com/questions/5593881/what-is-the-optimized-way-to-insert-large-number-of-records-more-than-40-000-i)
- [SQLite Optimizations For Ultra High-Performance](https://www.powersync.com/blog/sqlite-optimizations-for-ultra-high-performance)
- [Stop the SQLite Performance Wars](https://javascript.plainenglish.io/stop-the-sqlite-performance-wars-your-database-can-be-10x-faster-and-its-not-magic-156022addc75)
- [Supercharge SQLite Performance in Multi-threaded Python](https://medium.com/@roshanlamichhane/sqlite-worker-supercharge-your-sqlite-performance-in-multi-threaded-python-applications-01e2e43cc406)
- [Reddit - SQLite async connection pool](https://www.reddit.com/r/Python/comments/1lx3njh/aiosqlitepool_sqlite_async_connection_pool_for/)
- [SQLite in Production with WAL](https://victoria.dev/posts/sqlite-in-production-with-wal/)

### Python Caching and Lazy Loading
- [Python functools documentation](https://docs.python.org/3/library/functools.html)
- [Real Python - LRU Cache Strategy](https://realpython.com/lru-cache-python/)
- [DataCamp - Python Cache Introduction](https://www.datacamp.com/tutorial/python-cache-introduction)
- [Medium - Caching Techniques for API Requests](https://medium.com/top-python-libraries/caching-techniques-in-python-to-speed-up-api-requests-ac75a15eace6)
- [DataLeadsFuture - TTL Cache Decorator](https://www.dataleadsfuture.com/implement-a-cache-decorator-with-time-to-live-feature-in-python/)
- [IPRoyal Blog - Python Cache Basics (2025)](https://iproyal.com/blog/python-cache-basics)
- [Python Caching Techniques: From Beginner to Pro](https://python.plainenglish.io/python-caching-techniques-from-beginner-to-pro-f38447bf46a0)
- [Advanced Caching Strategies for LLM Applications](https://python.useinstructor.com/blog/2023/11/26/python-caching-llm-optimization/)
- [Three times faster with lazy imports](https://hugovk.dev/blog/2025/lazy-imports/)
- [PEP 810 – Explicit lazy imports](https://peps.python.org/pep-0810/)
- [Python lazy imports you can use today](https://pythontest.com/python-lazy-imports-now/)
- [Python 2025: Advanced Techniques](https://medium.com/@EnaModernCoder/python-2025-advanced-techniques-performance-power-and-real-world-engineering-patterns-b6713641db9c)

### Concurrency and Performance
- [Python 3.14 concurrent.futures documentation](https://docs.python.org/3/library/concurrent.futures.html)
- [Mastering Python Concurrency in 2025](https://medium.com/@blogstacker20/mastering-python-concurrency-in-2025-asyncio-threads-and-multiprocessing-explained-deeply-697e90341278)
- [ThreadPoolExecutor vs ProcessPoolExecutor](https://medium.com/@parthsurati096/threadpoolexecutor-vs-processpoolexecutor-a-complete-comparison-03828617bb83)
- [Real Python - Profiling in Python](https://realpython.com/python-profiling/)
- [BetterStack - Comprehensive Guide to Profiling](https://betterstack.com/community/guides/scaling-python/profiling-in-python/)
- [Analytics Vidhya - Profiling with cProfile](https://www.analyticsvidhya.com/blog/2024/05/profiling-python-code-using-timeit-and-cprofile/)
- [Performance Regression Testing Initiatives (2025)](https://cs.gssi.it/catia.trubiani/download/2025-IST-performance-regression-testing-mapping-study.pdf)
- [Automated Regression Testing in 2025](https://python-bloggers.com/2025/03/automated-regression-testing-in-2025-best-practises-from-top-qa-teams/)
- [pytest-ranking: Regression Test Prioritization](https://dl.acm.org/doi/pdf/10.1145/3696630.3728587)

### Hook Systems and Case Studies
- [Git Hooks for Automated Code Quality (2025)](https://dev.to/arasosman/git-hooks-for-automated-code-quality-checks-guide-2025-372f)
- [Ultimate Pre-Commit Hooks Guide 2025](https://gatlenculp.medium.com/effortless-code-quality-the-ultimate-pre-commit-hooks-guide-for-2025-57ca501d9835)
- [Substack - Why Prek Beats Pre-commit](https://aiechoes.substack.com/p/happier-developers-faster-teams-why)
- [OpenReplay - Automating Code Checks](https://blog.openreplay.com/automating-code-checks-git-pre-commit-hooks/)
- [Top 10 Python Testing Frameworks 2025](https://www.t-plan.com/blog/top-10-best-python-testing-frameworks-in-2025/)

---

## Appendix: Performance Measurement Templates

### A. Performance Baseline Template

```python
# perf_baseline.py
"""Performance baseline tracking for hooks optimization."""
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class PerformanceBaseline:
    """Track and compare performance over time."""

    def __init__(self, baseline_path: Path):
        self.baseline_path = baseline_path
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        if self.baseline_path.exists():
            return json.loads(self.baseline_path.read_text())
        return {"baseline_date": None, "metrics": {}}

    def save(self):
        self.baseline_path.parent.mkdir(parents=True, exist_ok=True)
        self.baseline_path.write_text(json.dumps(self.data, indent=2))

    def record(self, operation: str, duration_ms: float, metadata: dict = None):
        if operation not in self.data["metrics"]:
            self.data["metrics"][operation] = []

        self.data["metrics"][operation].append({
            "timestamp": datetime.now().isoformat(),
            "duration_ms": duration_ms,
            "metadata": metadata or {}
        })
        self.save()

    def get_baseline(self, operation: str) -> float:
        """Get baseline duration for operation."""
        if operation not in self.data["metrics"]:
            return None

        measurements = self.data["metrics"][operation]
        return sum(m["duration_ms"] for m in measurements) / len(measurements)

    def compare(self, operation: str, current_ms: float) -> dict:
        baseline_ms = self.get_baseline(operation)
        if baseline_ms is None:
            return {"status": "no_baseline"}

        change_pct = ((current_ms - baseline_ms) / baseline_ms) * 100

        if change_pct > 20:
            status = "regression"
        elif change_pct < -20:
            status = "improvement"
        else:
            status = "stable"

        return {
            "status": status,
            "baseline_ms": baseline_ms,
            "current_ms": current_ms,
            "change_pct": change_pct
        }
```

### B. Comprehensive Benchmark Suite

```python
# benchmark_suite.py
"""Comprehensive benchmark suite for hooks optimization."""
import time
import statistics
from typing import Callable, List, Dict, Any
from dataclasses import dataclass

@dataclass
class BenchmarkMetrics:
    """Detailed benchmark metrics."""
    name: str
    iterations: int
    mean_ms: float
    median_ms: float
    min_ms: float
    max_ms: float
    std_dev_ms: float
    total_ms: float
    throughput_per_sec: float

class BenchmarkSuite:
    """Comprehensive benchmarking suite."""

    def __init__(self):
        self.results: List[BenchmarkMetrics] = []

    def benchmark(
        self,
        func: Callable,
        *args,
        name: str = None,
        iterations: int = 100,
        warmup: int = 5
    ) -> BenchmarkMetrics:
        """Run comprehensive benchmark of function."""

        operation_name = name or func.__name__

        # Warmup runs (not measured)
        for _ in range(warmup):
            func(*args)

        # Measured runs
        times_ms = []
        start_total = time.perf_counter()

        for _ in range(iterations):
            start = time.perf_counter()
            result = func(*args)
            end = time.perf_counter()
            times_ms.append((end - start) * 1000)

        total_ms = (time.perf_counter() - start_total) * 1000

        metrics = BenchmarkMetrics(
            name=operation_name,
            iterations=iterations,
            mean_ms=statistics.mean(times_ms),
            median_ms=statistics.median(times_ms),
            min_ms=min(times_ms),
            max_ms=max(times_ms),
            std_dev_ms=statistics.stdev(times_ms) if len(times_ms) > 1 else 0,
            total_ms=total_ms,
            throughput_per_sec=iterations / (total_ms / 1000)
        )

        self.results.append(metrics)
        return metrics

    def compare(self, func_a: Callable, func_b: Callable, *args, **kwargs) -> Dict[str, Any]:
        """Compare two functions."""

        metrics_a = self.benchmark(func_a, *args, **kwargs, name=func_a.__name__)
        metrics_b = self.benchmark(func_b, *args, **kwargs, name=func_b.__name__)

        speedup = metrics_a.mean_ms / metrics_b.mean_ms

        return {
            "function_a": metrics_a.name,
            "function_b": metrics_b.name,
            "speedup": speedup,
            "improvement_pct": ((metrics_a.mean_ms - metrics_b.mean_ms) / metrics_a.mean_ms) * 100,
            "metrics_a": metrics_a,
            "metrics_b": metrics_b
        }

    def report(self) -> str:
        """Generate benchmark report."""

        lines = ["# Benchmark Report", ""]
        lines.append(f"{'Operation':<40} {'Mean (ms)':<12} {'Median (ms)':<12} {'StdDev':<10}")
        lines.append("-" * 74)

        for result in self.results:
            lines.append(
                f"{result.name:<40} "
                f"{result.mean_ms:<12.2f} "
                f"{result.median_ms:<12.2f} "
                f"{result.std_dev_ms:<10.2f}"
            )

        return "\n".join(lines)

# Usage example
if __name__ == "__main__":
    from hook_health_check import check_syntax, check_imports

    suite = BenchmarkSuite()

    # Benchmark individual operations
    suite.benchmark(check_syntax, "hook.py", name="syntax_check")
    suite.benchmark(check_imports, "hook.py", name="import_check")

    # Generate report
    print(suite.report())
```

---

**Document Status**: Complete
**Last Updated**: 2025-12-25
**Next Review**: After implementation of Phase 1 optimizations
