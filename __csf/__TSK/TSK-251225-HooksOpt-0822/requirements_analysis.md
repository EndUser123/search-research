# Hooks Performance Optimization Plan - Requirements Analysis

**Project ID:** TSK-251225-HooksOpt-0822
**Date:** 2025-12-25
**Status:** Step 2 - Requirements Analysis
**Workflow:** CWO12

---

## Executive Summary

This document analyzes all requirements for optimizing Claude Code hooks performance. The current hooks system at `P:/.claude/hooks` contains 90+ Python files totaling 30,385 lines of code, with database performance being the primary bottleneck. The optimization aims for 5-15x speedup while maintaining 100% backward compatibility.

**Current State Analysis:**
- Database: `events.db` (8.8MB) with 40,285 rows in `constitutional_events` table
- Zero indexes defined on the primary table (confirmed via query plan: SCAN)
- Largest hooks: `pre_tool_use.py` (3,591 lines), `llm_supervisor.py` (2,250 lines), `path_validator.py` (1,444 lines)
- No connection pooling, no config caching, no lazy imports
- Subprocess calls are sequential, not parallel

**Performance Bottlenecks Identified:**
1. **Database queries**: Full table scans on every query (no indexes)
2. **Config file loading**: Repeated JSON parsing on every hook execution
3. **Module imports**: All modules imported at top level (no lazy loading)
4. **Subprocess execution**: Sequential execution where parallel is possible
5. **No connection pooling**: New database connection per operation

---

## 1. Functional Requirements

### 1.1 Database Indexing (Priority: CRITICAL)

**Current State:**
- Table: `constitutional_events` with 40,285 rows
- Columns: `id`, `sessionid`, `event_type`, `timestamp`, `evidence_tier`, `layer`, `payload`, `created_at`
- Zero indexes (confirmed via query plan: `SCAN constitutional_events`)
- Query example shows full table scan: `EXPLAIN QUERY PLAN SELECT * FROM constitutional_events WHERE sessionid = "test"` returns `SCAN`

**Required Indexes:**

```sql
-- Primary query patterns identified from codebase analysis
CREATE INDEX idx_events_sessionid ON constitutional_events(sessionid);
CREATE INDEX idx_events_event_type ON constitutional_events(event_type);
CREATE INDEX idx_events_timestamp ON constitutional_events(timestamp DESC);
CREATE INDEX idx_events_session_timestamp ON constitutional_events(sessionid, timestamp DESC);
CREATE INDEX idx_events_session_type ON constitutional_events(sessionid, event_type);
CREATE INDEX idx_events_causal_chain ON constitutional_events(causal_chain_id);
CREATE INDEX idx_events_hook_name ON constitutional_events(hook_name);
```

**Acceptance Criteria:**
- All indexes created successfully
- Query plan shows `SEARCH` instead of `SCAN` for indexed queries
- No degradation in write performance (measure INSERT times)
- Indexes are maintained in sendevent.py schema creation

**Implementation Notes:**
- Indexes already defined in `sendevent.py` lines 93-99 but not applied to existing DB
- Need migration script to add indexes to existing database
- Monitor index size vs database size ratio

### 1.2 Configuration Caching System (Priority: HIGH)

**Current State:**
- `hook_config.py`: Simple dict-based config, no caching
- `path_validator.py`: Loads `directory_policy.json` on every instantiation (441 lines)
- Config files loaded repeatedly across hook executions

**Required Implementation:**

```python
from functools import lru_cache
from pathlib import Path
import json
import time

@lru_cache(maxsize=128)
def get_cached_config(config_path: str) -> dict:
    """Load and cache configuration file."""
    return json.loads(Path(config_path).read_text())

class DirectoryPolicy:
    _instance_cache = {}

    @classmethod
    def get_cached(cls, config_path: Path) -> 'DirectoryPolicy':
        """Get cached instance of DirectoryPolicy."""
        path_str = str(config_path)
        if path_str not in cls._instance_cache:
            cls._instance_cache[path_str] = cls(config_path)
        return cls._instance_cache[path_str]
```

**Acceptance Criteria:**
- Config files loaded only once per session
- `lru_cache` usage verified in tests
- Cache invalidation mechanism for config changes
- Thread-safe cache access
- Memory usage monitored (cache hit rate > 95%)

**Implementation Notes:**
- Use `functools.lru_cache` for simple config dicts
- Use singleton pattern for complex config objects (DirectoryPolicy)
- Consider `cachetools` for size-limited caching with TTL
- File watcher for cache invalidation (optional phase 2)

### 1.3 Lazy Import Loading (Priority: HIGH)

**Current State:**
- All imports at top level in `pre_tool_use.py` (lines 21-202)
- Imports include: `yaml`, `sqlite3`, `testing.test_quarantine`, `config.system_config`, etc.
- Heavy modules imported even when not used

**Required Implementation:**

```python
# Move heavy imports inside functions
def validate_tool_use(tool_name: str, tool_input: dict) -> dict:
    """Validate tool use with lazy imports."""
    # Import only when needed
    from path_validator import create_path_validator  # Lazy import
    from universal_guardrail_engine import get_guardrail_engine  # Lazy import

    validator = create_path_validator()
    # ... rest of validation
```

**Target Modules for Lazy Import:**
- `yaml` (used only for specific tool inputs)
- `testing.test_quarantine` (used only when QUARANTINE_SYSTEM_AVAILABLE)
- `calibration.override_tracker` (used only when OVERRIDE_TRACKER_AVAILABLE)
- `config.feature_toggles` (used only when FEATURE_TOGGLES_AVAILABLE)
- All CSF NIP integration modules

**Acceptance Criteria:**
- Startup time reduced by >50%
- Import only when module actually needed
- Graceful degradation when optional modules unavailable
- No circular import issues introduced

**Implementation Notes:**
- Move imports inside functions that use them
- Use try/except blocks for optional imports
- Keep stdlib imports at top (sqlite3, json, os, etc.)
- Measure import time before/after

### 1.4 Connection Pooling (Priority: CRITICAL)

**Current State:**
- `sendevent.py`: New connection per operation (line 173, 137)
- `base_repository.py`: Has connection property but not true pooling
- No thread-safe connection reuse
- Each query creates new connection

**Required Implementation:**

```python
import sqlite3
import threading
from typing import Optional

class ConnectionPool:
    """Thread-safe SQLite connection pool."""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self._local = threading.local()
        self._lock = threading.Lock()
        self._connections = []

    def get_connection(self) -> sqlite3.Connection:
        """Get thread-local connection from pool."""
        if not hasattr(self._local, 'conn') or self._local.conn is None:
            with self._lock:
                if len(self._connections) < self.pool_size:
                    conn = sqlite3.connect(self.db_path)
                    conn.row_factory = sqlite3.Row
                    self._connections.append(conn)
                    self._local.conn = conn
                else:
                    self._local.conn = self._connections.pop()
        return self._local.conn

    def return_connection(self, conn: sqlite3.Connection):
        """Return connection to pool."""
        self._local.conn = None
        with self._lock:
            self._connections.append(conn)

# Global pool instance
_db_pool: Optional[ConnectionPool] = None

def get_db_pool() -> ConnectionPool:
    """Get global database connection pool."""
    global _db_pool
    if _db_pool is None:
        _db_pool = ConnectionPool(str(Path.home() / ".claude" / "events.db"))
    return _db_pool
```

**Acceptance Criteria:**
- Connection pool size: 5 connections (configurable)
- Thread-safe access verified
- Connection reuse rate > 90%
- No connection leaks (all connections properly returned)
- Automatic connection closing on pool shutdown

**Implementation Notes:**
- Use `threading.local()` for thread-local connections
- Pool size matches expected concurrent access (typically 1-5)
- Connection timeout handling (stale connections)
- Pool statistics (hits, misses, wait time)

### 1.5 Parallel Subprocess Execution (Priority: MEDIUM)

**Current State:**
- 14 subprocess calls found across hooks
- All sequential execution
- Example: `hook_health_check.py` line 643 uses ThreadPoolExecutor for hooks, but subprocess calls still sequential

**Required Implementation:**

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import subprocess
from typing import List, Tuple

def run_subprocesses_parallel(commands: List[List[str]], max_workers: int = 4) -> List[Tuple[bool, str]]:
    """Run multiple subprocesses in parallel."""
    results = []

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_to_cmd = {
            executor.submit(subprocess.run, cmd, capture_output=True, text=True): cmd
            for cmd in commands
        }

        for future in as_completed(future_to_cmd):
            cmd = future_to_cmd[future]
            try:
                result = future.result()
                success = result.returncode == 0
                output = result.stdout if success else result.stderr
                results.append((success, output))
            except Exception as e:
                results.append((False, str(e)))

    return results
```

**Target Operations for Parallelization:**
- Hook health checks (already partially parallel)
- Multiple git status checks across repos
- Multiple file validation operations
- Batch event processing

**Acceptance Criteria:**
- Subprocess execution time reduced by >60% (4x parallelization)
- Error handling maintained (individual failures don't abort all)
- Output ordering preserved when needed
- No resource exhaustion (limit max_workers)

**Implementation Notes:**
- Use `ThreadPoolExecutor` for I/O-bound subprocesses
- Max workers = 4 (configurable based on CPU cores)
- Preserve error handling and logging
- Consider `ProcessPoolExecutor` for CPU-intensive operations

### 1.6 Performance Instrumentation (Priority: HIGH)

**Current State:**
- `instrumentationutils.py` exists but limited usage
- No systematic performance tracking
- `hook_health_check.py` measures execution time but not integrated

**Required Implementation:**

```python
import time
import functools
from contextlib import contextmanager

def measure_time(func):
    """Decorator to measure function execution time."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start = time.perf_counter()
        result = func(*args, **kwargs)
        elapsed = time.perf_counter() - start
        logger.info(f"{func.__name__} executed in {elapsed:.3f}s")
        return result
    return wrapper

@contextmanager
def database_operation_context(operation_name: str):
    """Context manager for database operation timing."""
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed = time.perf_counter() - start
        # Record metric to database or log
        record_performance_metric(operation_name, elapsed)

# Example usage
@measure_time
def validate_tool_use(tool_name: str, tool_input: dict) -> dict:
    with database_operation_context("tool_validation"):
        # Validation logic
        pass
```

**Metrics to Track:**
- Hook execution time (per hook, aggregated)
- Database query time (per query type)
- Config load time (cache hit/miss)
- Import time (lazy vs eager)
- Subprocess execution time (sequential vs parallel)

**Acceptance Criteria:**
- All hooks instrumented with execution time tracking
- Database queries instrumented
- Performance metrics logged to database/events table
- Performance report generation (before/after comparison)
- No significant overhead from instrumentation (<5%)

**Implementation Notes:**
- Use `time.perf_counter()` for high-resolution timing
- Store metrics in database for trend analysis
- Create `/perf-stats` slash command for viewing metrics
- Alert on performance degradation (e.g., >2x baseline)

### 1.7 Central Hook Manager (Priority: MEDIUM)

**Current State:**
- No central hook orchestration
- Each hook manages its own lifecycle
- Duplicated initialization code across hooks

**Required Implementation:**

```python
class HookManager:
    """Central manager for hook lifecycle and common operations."""

    def __init__(self):
        self.db_pool = get_db_pool()
        self.config_cache = ConfigCache()
        self.metrics = PerformanceMetrics()

    @lru_cache(maxsize=256)
    def get_config(self, config_path: str) -> dict:
        """Get cached configuration."""
        return self.config_cache.get(config_path)

    def get_db_connection(self) -> sqlite3.Connection:
        """Get connection from pool."""
        return self.db_pool.get_connection()

    def record_metric(self, name: str, value: float):
        """Record performance metric."""
        self.metrics.record(name, value)

# Global instance
_hook_manager: Optional[HookManager] = None

def get_hook_manager() -> HookManager:
    """Get global hook manager instance."""
    global _hook_manager
    if _hook_manager is None:
        _hook_manager = HookManager()
    return _hook_manager
```

**Acceptance Criteria:**
- Single entry point for common hook operations
- Centralized connection pooling
- Centralized config caching
- Centralized metrics collection
- Backward compatible (hooks can opt-in gradually)

**Implementation Notes:**
- Opt-in pattern (hooks use if needed, not required)
- Singleton pattern for global manager
- Thread-safe initialization
- Graceful fallback if manager unavailable

---

## 2. Non-Functional Requirements

### 2.1 Performance

**Target Metrics:**

| Metric | Baseline | Target | Measurement Method |
|--------|----------|--------|-------------------|
| Hook startup time | ~500ms | <100ms | Time from import to ready |
| Database query (sessionid) | ~200ms | <20ms | EXPLAIN QUERY PLAN + timing |
| Config file load | ~50ms | <1ms (cached) | Load time comparison |
| Full hook execution | ~1000ms | <200ms | End-to-end timing |
| Subprocess batch (10 cmds) | ~5000ms | <1500ms | Parallel execution timing |

**Overall Speedup Target:**
- Minimum: 5x faster
- Target: 10x faster
- Stretch goal: 15x faster

**Performance Testing Requirements:**
- Benchmark suite for before/after comparison
- Statistical significance (run each test 100x, use median)
- Profile hot spots with `cProfile` or `py-spy`
- Monitor memory usage (no memory leaks)

### 2.2 Compatibility

**Backward Compatibility Requirements:**

1. **Hook Interfaces**: All existing hooks must work without modification
   - Function signatures unchanged
   - Return values unchanged
   - Exceptions unchanged

2. **Database Schema**: Must maintain existing schema
   - New columns allowed (with defaults)
   - New tables allowed
   - Indexes added (not removed)

3. **Configuration Files**: Must read existing configs
   - No breaking changes to config format
   - New config fields optional (with defaults)
   - Legacy config support

4. **CLI Behavior**: All existing commands must work
   - Command arguments unchanged
   - Output format unchanged
   - Exit codes unchanged

**Compatibility Testing:**
- Test all hooks with existing test suite
- Manual testing of critical user workflows
- Regression test suite (automated)

### 2.3 Testing (TDD Approach)

**Test-First Development Requirements:**

1. **Write Test Before Implementation**
   - Each optimization must have failing test first
   - Test documents expected behavior
   - Test serves as acceptance criteria

2. **Test Types Required:**
   - **Unit Tests**: Test individual functions/classes in isolation
   - **Integration Tests**: Test hook interactions with database
   - **Performance Tests**: Benchmark before/after
   - **Regression Tests**: Ensure existing behavior preserved

3. **Test Coverage Requirements:**
   - Minimum: 80% code coverage
   - Target: 90% code coverage
   - All new code must be tested
   - Critical paths must have 100% coverage

4. **Test Structure:**
   ```
   tests/
   ├── unit/
   │   ├── test_config_cache.py
   │   ├── test_connection_pool.py
   │   ├── test_lazy_imports.py
   │   └── test_parallel_subprocess.py
   ├── integration/
   │   ├── test_database_operations.py
   │   ├── test_hook_execution.py
   │   └── test_config_loading.py
   ├── performance/
   │   ├── test_database_index_performance.py
   │   ├── test_hook_execution_performance.py
   │   └── benchmark_suite.py
   └── regression/
       ├── test_hook_compatibility.py
       └── test_database_compatibility.py
   ```

**TDD Workflow:**
1. Write failing test
2. Run test, confirm failure
3. Implement minimum code to pass test
4. Run test, confirm pass
5. Refactor if needed
6. Repeat

### 2.4 Reliability

**Conservative Deployment Requirements:**

1. **Phased Rollout** (see project charter):
   - Phase 1: Database indexing (lowest risk)
   - Phase 2: Config caching
   - Phase 3: Lazy imports
   - Phase 4: Connection pooling
   - Phase 5: Parallel subprocesses
   - Each phase independently deployable

2. **Easy Rollback**:
   - Database migrations must be reversible
   - Feature flags for each optimization
   - Config-based enable/disable
   - Git-based rollback (simple revert)

3. **Monitoring and Alerting**:
   - Health check command (`/hook-health`)
   - Performance metrics dashboard
   - Error rate tracking
   - Automatic rollback on critical failures

4. **Data Safety**:
   - Database backups before migrations
   - Transactional operations
   - No data loss scenarios
   - Recovery procedures documented

**Rollback Plan:**
- Database: `DROP INDEX` statements prepared
- Code: Git revert to previous commit
- Config: Feature flag set to `false`
- Recovery time: <5 minutes

### 2.5 Monitoring

**Performance Metrics Dashboard:**

| Metric | Collection Method | Alert Threshold |
|--------|------------------|-----------------|
| Avg hook execution time | Instrumentation | >2x baseline |
| Database query time (p95) | Query timing | >100ms |
| Cache hit rate | Cache stats | <90% |
| Connection pool wait time | Pool stats | >50ms |
| Subprocess failure rate | Results tracking | >5% |
| Memory usage | Process monitoring | >500MB |

**Monitoring Tools:**
- SQLite database for metric storage
- CLI command: `/perf-stats` for viewing metrics
- JSON output for integration with monitoring systems
- Log-based metrics (structured logging)

**Alerting:**
- Console warnings on threshold breach
- Optional: Integration with external monitoring (Phase 2)

---

## 3. Technical Requirements

### 3.1 Python Compatibility

**Python Version Support:**
- Primary: Python 3.9+
- Target: Python 3.11 (optimize for current version)
- Fallback: Python 3.8 (if needed for compatibility)

**Python Features Used:**
- `functools.lru_cache` (stdlib, 3.8+)
- `contextlib.contextmanager` (stdlib)
- `typing` module (3.9+ for new syntax)
- `threading.local()` (stdlib)
- `concurrent.futures` (stdlib)

**External Dependencies:**
- None for core optimizations (stdlib only)
- Optional: `cachetools` for advanced caching (Phase 2)

### 3.2 Thread-Safety

**Thread-Safety Requirements:**

1. **Connection Pool**:
   - Thread-local connections
   - Lock-based pool management
   - No shared connection objects

2. **Config Cache**:
   - `lru_cache` is thread-safe (CPython implementation)
   - Custom cache needs locks
   - Immutable config objects (preferred)

3. **Metrics Collection**:
   - Thread-safe metrics recording
   - Lock for metric aggregation
   - Atomic counters

**Thread-Safety Testing:**
- Multi-threaded test suite
- Stress test with 100+ concurrent operations
- Race condition detection

### 3.3 SQLite Optimization

**SQLite Configuration:**

```python
# Connection optimization
conn = sqlite3.connect(
    db_path,
    isolation_level=None,  # Autocommit mode
    check_same_thread=False,  # Allow cross-thread access (with pooling)
)

# Performance pragmas
conn.execute("PRAGMA journal_mode = WAL")  # Better concurrency
conn.execute("PRAGMA synchronous = NORMAL")  # Faster writes
conn.execute("PRAGMA cache_size = -64000")  # 64MB cache
conn.execute("PRAGMA temp_store = MEMORY")  # In-memory temp tables
conn.execute("PRAGMA mmap_size = 268435456")  # 256MB mmap
```

**Query Optimization:**
- Use prepared statements (parameterized queries)
- Avoid `SELECT *` (specific columns only)
- Use `EXPLAIN QUERY PLAN` for all queries
- Batch operations where possible

**Index Maintenance:**
- `ANALYZE` command for query planner statistics
- `REINDEX` if index fragmentation detected
- Monitor index size vs table size

### 3.4 Caching Strategy

**Cache Types:**

1. **lru_cache** (functools):
   - Use for: Simple function results, config dicts
   - Maxsize: 128-512 entries
   - Thread-safe: Yes
   - Example: `get_cached_config()`

2. **Custom Singleton Cache**:
   - Use for: Complex objects, Database connections
   - Lifecycle: Session-long
   - Thread-safe: Requires locks
   - Example: `DirectoryPolicy.get_cached()`

3. **TTL Cache** (optional, Phase 2):
   - Use for: Configs that may change
   - Library: `cachetools.TTLCache`
   - TTL: 5-15 minutes
   - Example: Hot-reloadable configs

**Cache Invalidation:**
- Manual: `cache_clear()` method
- Automatic: TTL-based (Phase 2)
- File watcher: `watchdog` library (Phase 2)

**Cache Statistics:**
- Hit rate tracking
- Miss rate tracking
- Eviction count
- Size monitoring

### 3.5 Parallelization Strategy

**Concurrency Models:**

1. **ThreadPoolExecutor**:
   - Use for: I/O-bound operations (subprocess, network)
   - Max workers: 4-8 (CPU cores * 2)
   - Example: Parallel subprocess execution

2. **ProcessPoolExecutor** (optional, Phase 2):
   - Use for: CPU-bound operations (parsing, computation)
   - Max workers: CPU cores
   - Example: Batch JSON parsing

3. **Async/Await** (optional, Phase 2):
   - Use for: Async database operations
   - Library: `aiosqlite`
   - Example: Async event processing

**Parallelization Patterns:**

```python
# Pattern 1: Map-Reduce
def map_reduce_parallel(items, map_func, reduce_func, workers=4):
    """Map-reduce pattern with ThreadPoolExecutor."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        mapped = executor.map(map_func, items)
        return reduce_func(mapped)

# Pattern 2: Batch Processing
def batch_parallel(items, batch_size, process_func, workers=4):
    """Process items in parallel batches."""
    batches = [items[i:i+batch_size] for i in range(0, len(items), batch_size)]
    with ThreadPoolExecutor(max_workers=workers) as executor:
        results = executor.map(process_func, batches)
        return list(results)

# Pattern 3: Error-Tolerant Execution
def parallel_execute_safe(tasks, workers=4):
    """Execute tasks in parallel with error isolation."""
    with ThreadPoolExecutor(max_workers=workers) as executor:
        future_to_task = {executor.submit(task): task for task in tasks}
        results = []
        for future in as_completed(future_to_task):
            try:
                results.append(future.result())
            except Exception as e:
                results.append({'error': str(e), 'task': future_to_task[future]})
        return results
```

---

## 4. TDD Requirements

### 4.1 Unit Tests

**Test Structure:**

```python
# tests/unit/test_config_cache.py
import pytest
from hooks.config_cache import get_cached_config, clear_config_cache

class TestConfigCache:
    """Unit tests for configuration caching."""

    def setup_method(self):
        """Clear cache before each test."""
        clear_config_cache()

    def test_cache_miss_first_load(self):
        """Test first call loads from file."""
        config = get_cached_config("test_config.json")
        assert config == expected_config

    def test_cache_hit_second_load(self):
        """Test second call uses cache."""
        config1 = get_cached_config("test_config.json")
        config2 = get_cached_config("test_config.json")
        assert config1 is config2  # Same object

    def test_cache_invalidates_on_clear(self):
        """Test cache invalidation."""
        config1 = get_cached_config("test_config.json")
        clear_config_cache()
        config2 = get_cached_config("test_config.json")
        assert config1 is not config2

    @pytest.mark.parametrize("config_path", [
        "config1.json",
        "config2.json",
        "config3.json",
    ])
    def test_multiple_configs_cached(self, config_path):
        """Test multiple configs cached independently."""
        config = get_cached_config(config_path)
        assert config is not None
```

**Coverage Requirements:**
- All public functions tested
- All edge cases covered (None, empty, errors)
- All branches tested (if/else, try/except)
- Thread-safety scenarios tested

### 4.2 Integration Tests

**Test Structure:**

```python
# tests/integration/test_database_operations.py
import pytest
from hooks.repositories.base_repository import BaseRepository

class TestDatabaseOperations:
    """Integration tests for database operations."""

    @pytest.fixture
    def db_connection(self, tmp_path):
        """Create test database."""
        db_path = tmp_path / "test.db"
        # Setup schema
        yield db_path
        # Cleanup

    def test_indexed_query_performance(self, db_connection):
        """Test that indexed queries meet performance target."""
        # Insert test data
        # Query without index (baseline)
        time_without_index = measure_query_time(db_connection, query)
        # Create index
        # Query with index
        time_with_index = measure_query_time(db_connection, query)
        # Assert speedup
        assert time_with_index < time_without_index * 0.1  # 10x faster

    def test_connection_pool_reuse(self, db_connection):
        """Test connection reuse in pool."""
        pool = ConnectionPool(str(db_connection), pool_size=2)
        conn1 = pool.get_connection()
        conn2 = pool.get_connection()
        assert conn1 is not conn2  # Different connections
        pool.return_connection(conn1)
        conn3 = pool.get_connection()
        assert conn3 is conn1  # Reused connection
```

### 4.3 Performance Benchmarks

**Benchmark Structure:**

```python
# tests/performance/benchmark_suite.py
import pytest
import time

class TestPerformanceBenchmarks:
    """Performance benchmarks for hook optimizations."""

    @pytest.mark.benchmark
    def test_hook_execution_baseline(self, benchmark):
        """Baseline: Hook execution time without optimizations."""
        result = benchmark(run_hook_without_optimizations)
        assert result['success']

    @pytest.mark.benchmark
    def test_hook_execution_optimized(self, benchmark):
        """Optimized: Hook execution time with all optimizations."""
        result = benchmark(run_hook_with_optimizations)
        assert result['success']

    def test_speedup_achieved(self, benchmark_data):
        """Assert speedup target met."""
        baseline_time = benchmark_data['baseline']['median']
        optimized_time = benchmark_data['optimized']['median']
        speedup = baseline_time / optimized_time
        assert speedup >= 5.0  # 5x minimum speedup

    @pytest.mark.benchmark
    def test_database_query_with_index(self, benchmark):
        """Test database query performance with index."""
        result = benchmark(query_events_by_sessionid)
        assert result['time'] < 0.02  # <20ms target
```

**Benchmark Requirements:**
- Run 100 iterations per test
- Use median (not mean) for stability
- Record min, max, median, p95, p99
- Store results in database for trend analysis
- Compare before/after each optimization phase

### 4.4 Regression Tests

**Regression Test Structure:**

```python
# tests/regression/test_hook_compatibility.py
import pytest

class TestHookCompatibility:
    """Regression tests for backward compatibility."""

    @pytest.mark.parametrize("hook_name", [
        "pre_tool_use",
        "llm_supervisor",
        "path_validator",
        "user_prompt_submit_cks",
        # ... all 90+ hooks
    ])
    def test_hook_loads_without_error(self, hook_name):
        """Test all hooks load without import errors."""
        module = import_hook(hook_name)
        assert module is not None

    def test_hook_signature_unchanged(self):
        """Test hook function signatures unchanged."""
        # Compare to expected signatures
        actual_sig = get_signature(pre_tool_use_hook)
        expected_sig = "(tool_name: str, tool_input: dict) -> dict"
        assert signatures_match(actual_sig, expected_sig)

    def test_database_compatibility(self):
        """Test existing database still works."""
        # Use actual events.db
        # Run queries
        # Assert results valid
        pass

    def test_config_compatibility(self):
        """Test existing config files still work."""
        # Load existing configs
        # Assert no errors
        # Assert values correct
        pass
```

**Regression Checklist:**
- [ ] All hooks load without error
- [ ] All hook signatures unchanged
- [ ] All database queries return correct results
- [ ] All config files load correctly
- [ ] All CLI commands work
- [ ] No new exceptions raised
- [ ] No changes to output formats
- [ ] No changes to exit codes

---

## 5. Constraint Analysis

### 5.1 No Breaking Changes

**Constraint:**
All hook interfaces must remain 100% backward compatible. No existing functionality may be broken or changed in behavior.

**Implications:**
- New features must be opt-in, not forced
- Existing code paths must continue to work
- Performance optimizations must be transparent
- Database schema changes must be additive only

**Validation:**
- Comprehensive regression test suite
- Manual testing of critical workflows
- User acceptance testing (UAT) before full deployment

### 5.2 Preserve Safety Checks

**Constraint:**
All safety checks must remain in place. Performance optimizations must not bypass validation logic.

**Safety-Critical Components:**
- Path validation (deny_root_write.py, path_validator.py)
- Dangerous command detection
- Repository reality enforcement
- Constitutional compliance checks

**Validation:**
- Security audit of all optimizations
- Penetration testing
- Code review of all database query changes
- Verify safety checks still execute

### 5.3 Reversible Database Migration

**Constraint:**
All database schema changes must be reversible. Rollback must restore database to previous state.

**Reversible Changes:**
- Indexes: `DROP INDEX IF EXISTS idx_name`
- Tables: `DROP TABLE IF EXISTS table_name`
- Columns: SQLite doesn't support DROP COLUMN (workaround: recreate table)

**Rollback Script:**
```sql
-- Rollback script for indexes
DROP INDEX IF EXISTS idx_events_sessionid;
DROP INDEX IF EXISTS idx_events_event_type;
DROP INDEX IF EXISTS idx_events_timestamp;
DROP INDEX IF EXISTS idx_events_session_timestamp;
DROP INDEX IF EXISTS idx_events_session_type;
DROP INDEX IF EXISTS idx_events_causal_chain;
DROP INDEX IF EXISTS idx_events_hook_name;
```

**Migration Testing:**
- Test migration on copy of production database
- Test rollback script
- Verify no data loss
- Measure migration time

### 5.4 Independent Phase Deployment

**Constraint:**
Each optimization phase must be independently deployable. Partial deployment must not break the system.

**Phase Independence:**
- Phase 1 (Database indexing): Can deploy alone
- Phase 2 (Config caching): Can deploy without Phase 1
- Phase 3 (Lazy imports): Can deploy without Phases 1-2
- Phase 4 (Connection pooling): Can deploy without Phases 1-3
- Phase 5 (Parallel subprocesses): Can deploy alone

**Feature Flags:**
```python
# Feature flag configuration
FEATURE_FLAGS = {
    'database_indexes': True,
    'config_caching': True,
    'lazy_imports': True,
    'connection_pooling': True,
    'parallel_subprocess': True,
}

# Usage
if FEATURE_FLAGS['config_caching']:
    config = get_cached_config(config_path)
else:
    config = load_config_direct(config_path)
```

**Rollback Granularity:**
- Individual feature can be disabled
- Individual phase can be reverted
- No cascading dependencies between phases

---

## 6. Success Criteria

### 6.1 Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Overall speedup | 5-15x | Benchmark suite |
| Database query time | <20ms | Query timing |
| Hook execution time | <200ms | End-to-end timing |
| Config load time (cached) | <1ms | Cache hit timing |
| Memory overhead | <100MB | Process monitoring |

### 6.2 Quality Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Test coverage | >90% | pytest --cov |
| Regression tests pass | 100% | pytest tests/regression/ |
| Performance tests pass | 100% | pytest tests/performance/ |
| Code review approved | Yes | Peer review |
| Documentation complete | Yes | Doc review |

### 6.3 Reliability Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Uptime during deployment | >99% | Monitoring |
| Rollback time | <5 min | Drill testing |
| Data loss incidents | 0 | Audit |
| Performance regression | 0% | Benchmark comparison |

---

## 7. Risk Assessment

### 7.1 Technical Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Database migration fails | Medium | High | Test on copy, backup first |
| Indexes slow down writes | Low | Medium | Benchmark write performance |
| Cache invalidation bugs | Medium | Medium | Comprehensive cache tests |
| Thread-safety issues | Low | High | Multi-threaded stress tests |
| Lazy import circular deps | Low | Medium | Careful import ordering |
| Parallel subprocess race conditions | Medium | Medium | Error isolation, retries |

### 7.2 Operational Risks

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Performance regression | Low | High | Benchmark suite, gradual rollout |
| Deployment downtime | Low | Medium | Feature flags, quick rollback |
| User workflow disruption | Low | High | Comprehensive testing, UAT |
| Increased complexity | High | Medium | Documentation, code reviews |

### 7.3 Mitigation Strategies

**Pre-Deployment:**
- Comprehensive test suite
- Performance benchmarking
- Security audit
- Code review
- Documentation review

**During Deployment:**
- Feature flags for each optimization
- Gradual rollout (phase by phase)
- Real-time monitoring
- Quick rollback plan

**Post-Deployment:**
- Performance monitoring
- Error tracking
- User feedback collection
- Iterative improvements

---

## 8. Dependencies

### 8.1 Internal Dependencies

- **Hook health check system**: Used for validation
- **Database schema**: Must understand before adding indexes
- **Config file formats**: Must understand before caching
- **Existing test suite**: Must extend, not replace

### 8.2 External Dependencies

**Python Standard Library:**
- `functools.lru_cache` (stdlib, no install)
- `concurrent.futures` (stdlib, no install)
- `threading` (stdlib, no install)
- `sqlite3` (stdlib, no install)
- `contextlib` (stdlib, no install)

**Optional Dependencies (Phase 2):**
- `cachetools` (advanced caching)
- `watchdog` (file watching for cache invalidation)
- `aiosqlite` (async database operations)

### 8.3 Tool Dependencies

**Testing:**
- `pytest` (test framework)
- `pytest-cov` (coverage reporting)
- `pytest-benchmark` (benchmarking)
- `pytest-xdist` (parallel test execution)

**Development:**
- `black` (code formatting)
- `pylint` (linting)
- `mypy` (type checking)

---

## 9. Documentation Requirements

### 9.1 Code Documentation

**Required Documentation:**
- Docstrings for all new functions/classes
- Inline comments for complex logic
- Type hints for all function signatures
- Usage examples in docstrings

**Example:**
```python
def get_cached_config(config_path: str) -> dict:
    """
    Load and cache configuration file.

    Uses LRU cache to avoid repeated file I/O. Cache is thread-safe
    and automatically handles eviction when cache is full.

    Args:
        config_path: Absolute path to JSON configuration file

    Returns:
        Parsed configuration dictionary

    Raises:
        FileNotFoundError: If config file doesn't exist
        json.JSONDecodeError: If config file is invalid JSON

    Example:
        >>> config = get_cached_config("P:/.claude/hooks/config/directory_policy.json")
        >>> print(config['workspace_root']['required_directories'])
    """
```

### 9.2 Architecture Documentation

**Required Documents:**
- Architecture decision records (ADRs)
- Performance optimization guide
- Database schema documentation
- Testing strategy document
- Deployment guide
- Rollback procedures

### 9.3 User Documentation

**Required Documents:**
- Performance monitoring guide (how to use `/perf-stats`)
- Feature flag configuration guide
- Troubleshooting guide
- FAQ

---

## 10. Acceptance Criteria

### 10.1 Functional Acceptance

- [ ] All 7 indexes created and verified with `EXPLAIN QUERY PLAN`
- [ ] Config caching implemented with >95% hit rate
- [ ] Lazy imports reduce startup time by >50%
- [ ] Connection pooling implemented with <5ms wait time
- [ ] Parallel subprocess execution shows >60% time reduction
- [ ] Performance instrumentation shows <5% overhead
- [ ] Central hook manager available for opt-in use

### 10.2 Non-Functional Acceptance

- [ ] Overall speedup: 5-15x (measured by benchmark suite)
- [ ] All 90+ hooks still load and execute without errors
- [ ] Test coverage >90%
- [ ] All regression tests pass
- [ ] Database migration reversible (rollback tested)
- [ ] Each phase independently deployable
- [ ] Zero data loss incidents
- [ ] Zero safety check bypasses

### 10.3 Documentation Acceptance

- [ ] All new code documented with docstrings
- [ ] Architecture decisions documented
- [ ] Deployment guide written
- [ ] Rollback procedures documented
- [ ] User guide for performance monitoring
- [ ] Code review approved
- [ ] All tests passing

---

## 11. Next Steps

### 11.3 Immediate Actions (Step 3: Design)

1. **Create detailed design documents:**
   - Database index schema design
   - Config cache architecture
   - Connection pool implementation
   - Lazy import refactoring plan
   - Parallel subprocess strategy

2. **Create test plan:**
   - Unit test specifications
   - Integration test scenarios
   - Performance benchmark suite
   - Regression test checklist

3. **Create implementation plan:**
   - Phase-by-phase breakdown
   - Task dependencies
   - Timeline estimates
   - Risk mitigation strategies

### 11.4 Preparation for Implementation (Step 4)

1. **Setup development environment:**
   - Create test database fixture
   - Setup benchmark suite
   - Configure test coverage tracking

2. **Create baseline measurements:**
   - Run performance benchmarks (before optimization)
   - Document current performance
   - Establish performance baseline

3. **Prepare rollback strategy:**
   - Create database backup scripts
   - Prepare rollback git branches
   - Test rollback procedures

---

## Appendix A: Current Database Schema

```sql
CREATE TABLE constitutional_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sessionid TEXT NOT NULL,
    event_type TEXT NOT NULL,
    timestamp INTEGER NOT NULL,
    evidence_tier TEXT NOT NULL,
    layer TEXT,
    payload TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Row count: 40,285
-- Database size: 8.8MB
-- Indexes: 0 (NONE)
```

## Appendix B: Largest Hooks (By Line Count)

| Hook | Lines | Primary Function |
|------|-------|------------------|
| pre_tool_use.py | 3,591 | Tool validation, safety checks |
| llm_supervisor.py | 2,250 | LLM output supervision |
| path_validator.py | 1,444 | Path validation policy |
| user_prompt_submit_cks.py | 836 | CKS storage |
| hook_health_check.py | 827 | Hook health monitoring |
| intelligent_stop_hook.py | 789 | Stop condition detection |
| explore_gate.py | 729 | Explore command gating |
| goal_anchor.py | 649 | Goal anchoring logic |
| explore_opportunity_detector.py | 621 | Opportunity detection |
| guidance_cache.py | 569 | Guidance caching |

## Appendix C: Subprocess Calls Found

14 subprocess calls across hooks:
- `event_queue.py:83`
- `commit_msg_validator.py:62, 75`
- `hook_health_check.py:360`
- `on_precompact.py:103`
- `on_exit_plan_mode.py:35`
- `hook_bridge.py:84`
- `postcompact_git_state_verifier.py:28`
- `task_identity_manager.py:126`
- `pre_tool_use.py:2711`
- `test_observability.py:63, 214`
- `session_init.py:59`
- `task_context_manager.py:73`
- `unified_context_adapter.py:322`

---

**Document Status:** Complete
**Next Phase:** Step 3 - Design
**Last Updated:** 2025-12-25

---

## Change Log

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-12-25 | 1.0 | Initial requirements analysis | CWO12 Workflow |
