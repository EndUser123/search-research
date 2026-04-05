# Implementation Plan: Quality System Performance

**TSK:** TSK-251230-PERF-QUALITY
**Status:** Draft

## Sprint Overview

| Sprint | Focus | Duration | Deliverables |
|--------|-------|----------|--------------|
| **Sprint 1** | Incremental Analysis Foundation | Week 1 | FileHashDB, dirty set detection |
| **Sprint 2** | Parallel Execution | Week 2 | Phase DAG, concurrent execution |
| **Sprint 3** | Tool Integration & Polish | Week 3 | UnifiedAnalyzer fix, AST hashing |

---

## Sprint 1: Incremental Analysis Foundation

### Goal
Enable fast analysis of small changes by only analyzing affected files.

### Tasks

#### T1.1: FileHashDB Implementation
**File:** `src/quality/incremental/file_hash_db.py`
**Effort:** 3 hours

**Acceptance Criteria:**
- [ ] SQLite database created in TSK directory
- [ ] `get_hash()` returns stored hash or None
- [ ] `set_hash()` stores hash with timestamp
- [ ] `get_dirty_files()` returns changed paths
- [ ] Schema includes dependencies column

**TDD Tests:**
```python
def test_store_and_retrieve_hash():
    db = FileHashDB(":memory:")
    db.set_hash("test.py", "abc123")
    assert db.get_hash("test.py") == "abc123"

def test_dirty_file_detection():
    db = FileHashDB(":memory:")
    db.set_hash("test.py", "old_hash")
    changed = db.get_dirty_files({"test.py": {"new_hash"}})
    assert "test.py" in changed
```

#### T1.2: Hash Computation Utility
**File:** `src/quality/incremental/hasher.py`
**Effort:** 2 hours

**Acceptance Criteria:**
- [ ] `compute_sha256()` for file content
- [ ] `compute_ast_hash()` using ast.dump()
- [ ] Batch hash computation for efficiency
- [ ] Handles errors gracefully (skip unreadable files)

**TDD Tests:**
```python
def test_sha256_computation():
    result = compute_sha256("print('hello')")
    assert len(result) == 64  # SHA-256 hex length

def test_ast_hash_ignores_whitespace():
    h1 = compute_ast_hash("print(  'hello'  )")
    h2 = compute_ast_hash("print('hello')")
    assert h1 == h2  # Functionally equivalent
```

#### T1.3: Dirty Set Propagation
**File:** `src/quality/incremental/dirty_set.py`
**Effort:** 4 hours

**Acceptance Criteria:**
- [ ] Uses existing DependencyGraph for import tracking
- [ ] Computes transitive closure of dependents
- [ ] Returns minimal set for re-analysis
- [ ] Handles circular dependencies

**TDD Tests:**
```python
def test_transitive_closure():
    # A imports B, B imports C
    # If C changes, A, B, C all need re-analysis
    dirty = get_dirty_set(["C.py"], dependency_graph)
    assert dirty == {"A.py", "B.py", "C.py"}
```

#### T1.4: Integration with qual-gate
**File:** `src/quality/qual-gate.py` (modify)
**Effort:** 2 hours

**Changes:**
- [ ] Import IncrementalAnalyzer
- [ ] Use dirty set for phase execution
- [ ] Update state management with FileHashDB
- [ ] Fallback to full analysis on error

---

## Sprint 2: Parallel Execution

### Goal
Execute independent quality gates concurrently for 2-3x speedup.

### Tasks

#### T2.1: Phase DAG Definition
**File:** `src/quality/parallel/phase_dag.py`
**Effort:** 2 hours

**Acceptance Criteria:**
- [ ] Define PHASE_DEPENDENCIES mapping
- [ ] `get_ready_phases()` returns executable phases
- [ ] `mark_complete()` updates DAG state
- [ ] Detect cycles (error if found)

**TDD Tests:**
```python
def test_phase_dependencies():
    dag = PhaseDAG(PHASE_DEPENDENCIES)
    assert dag.get_ready_phases() == ["constitutional", "structure", "duplicates"]
    dag.mark_complete("structure")
    assert "architecture" in dag.get_ready_phases()
```

#### T2.2: Async Phase Executor
**File:** `src/quality/parallel/async_executor.py`
**Effort:** 4 hours

**Acceptance Criteria:**
- [ ] Execute phases using asyncio
- [ ] Run independent phases concurrently
- [ ] Respect dependency ordering
- [ ] Handle phase failures without stopping others

**TDD Tests:**
```python
async def test_parallel_execution():
    executor = AsyncPhaseExecutor()
    results = await executor.run(["structure", "duplicates"])  # Can run in parallel
    assert len(results) == 2
```

#### T2.3: Qual-Gate Integration
**File:** `src/quality/qual-gate.py` (modify)
**Effort:** 3 hours

**Changes:**
- [ ] Add `--parallel` flag
- [ ] Use AsyncPhaseExecutor when flag set
- [ ] Maintain backward compatibility (default sequential)
- [ ] Log parallel execution status

---

## Sprint 3: Tool Integration & Polish

### Goal
Fix UnifiedAnalyzer imports and add AST-based caching.

### Tasks

#### T3.1: UnifiedAnalyzer Import Fix
**File:** `src/quality/unified_analyzer.py`
**Effort:** 2 hours

**Acceptance Criteria:**
- [ ] Fix ruff import path
- [ ] Fix mypy import path
- [ ] Fix bandit import path
- [ ] Remove subprocess fallback (or keep as emergency)

**TDD Tests:**
```python
def test_direct_ruff_call():
    analyzer = UnifiedAnalyzer()
    result = analyzer.run_ruff("test.py")
    assert not result["used_subprocess"]

def test_direct_mypy_call():
    analyzer = UnifiedAnalyzer()
    result = analyzer.run_mypy("test.py")
    assert not result["used_subprocess"]
```

#### T3.2: AST-Based Cache Keys
**File:** `src/quality/incremental/cache.py`
**Effort:** 3 hours

**Acceptance Criteria:**
- [ ] `compute_cache_key()` uses AST hash
- [ ] Cache invalidation on structural changes
- [ ] Fallback to SHA-256 if AST parsing fails
- [ ] Cache statistics reporting

**TDD Tests:**
```python
def test_cache_key_ignores_comments():
    k1 = compute_cache_key("# comment\ncode()")
    k2 = compute_cache_key("code()")
    assert k1 == k2

def test_cache_key_detects_structure_change():
    k1 = compute_cache_key("def foo(): pass")
    k2 = compute_cache_key("def bar(): pass")
    assert k1 != k2
```

#### T3.3: Performance Benchmarking
**File:** `tests/quality/test_performance.py`
**Effort:** 2 hours

**Acceptance Criteria:**
- [ ] Benchmark single-file analysis (<10 sec target)
- [ ] Benchmark parallel vs sequential (2-3x target)
- [ ] Report baseline vs optimized metrics
- [ ] Test with 1, 10, 100, 1000 file changes

---

## Implementation Order

### Week 1: Foundation First
```
Day 1-2: T1.1, T1.2 (HashDB + Hasher)
Day 3-4: T1.3 (Dirty Set)
Day 5:   T1.4 (Integration)
```

### Week 2: Parallel Execution
```
Day 1-2: T2.1 (Phase DAG)
Day 3-4: T2.2 (Async Executor)
Day 5:   T2.3 (Integration)
```

### Week 3: Polish
```
Day 1-2: T3.1 (UnifiedAnalyzer)
Day 3-4: T3.2 (AST Cache)
Day 5:   T3.3 (Benchmarks + Documentation)
```

---

## Risk Mitigation

| Risk | Mitigation | Plan B |
|------|-----------|-------|
| Dependency graph inaccurate | Extensive testing | Fall back to file list |
| Async execution causes deadlock | Timeout mechanism | Sequential fallback |
| Hash database corruption | Atomic writes | Rebuild from scratch |
| Import fix breaks things | Keep subprocess fallback | Revert changes |

---

## Definition of Done

Each Sprint is complete when:
- [ ] All acceptance criteria met
- [ ] All TDD tests passing
- [ ] Code reviewed
- [ ] Documentation updated
- [ ] Performance measured vs baseline

Project complete when:
- [ ] All 3 sprints complete
- [ ] Single-file analysis <10 sec
- [ ] Full analysis 2-3x faster
- [ ] No regressions in existing functionality
