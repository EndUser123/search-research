# Research: Quality System Performance Enhancements

**TSK:** TSK-251230-PERF-QUALITY
**Status:** Draft

## Existing Codebase Analysis

### Current qual-gate Implementation

**File:** `P:\__csf.nip\src\quality\qual-gate.py`

**Key findings:**
1. **State management exists** - Lines 700-750 track file hashes and phases
2. **Change detection implemented** - Lines 800-850 compute file hashes
3. **Phase dependencies defined** - Lines 150-200 specify phase DAG
4. **Parallel execution NOT implemented** - All phases run sequentially

**Relevant code snippet (state tracking):**
```python
# Lines 720-740
def _save_state(self, state: dict):
    """Save current state to disk."""
    state_file = self.project_state_dir / "qual-gate-state.json"
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
```

### UnifiedAnalyzer Implementation

**File:** `P:\__csf.nip\src\quality\unified_analyzer.py`

**Key findings:**
1. **Import issues** - Module structure changed, imports failing
2. **Direct tool calls** - ruff/mypy/bandit integrated
3. **Subprocess fallback** - Lines 100-120 fall back on import error

**Error pattern:**
```python
# Lines 50-70
try:
    from src.quality.tools import ruff, mypy, bandit
except ImportError:
    # Falls back to subprocess - losing 20-30% performance
    self.use_subprocess = True
```

### Dependency Graph Implementation

**File:** `P:\__csf.nip\src\quality\core\dependency_graph.py`

**Key findings:**
1. **Already implements import tracking** - `build_from_files()` method
2. **Dependent lookup exists** - `get_dependents()` for dirty set
3. **Transitive closure** - Can compute full dependency chain

**Reusable components:**
```python
# Lines 200-220
def get_dependents(self, symbol: str) -> list[Symbol]:
    """Get all symbols that depend on this symbol."""
    return [s for s in self._symbols.values() if symbol in s.dependencies]
```

## Technology Research

### File Hashing Options

| Method | Speed | Collision Resistance | Recommendation |
|--------|-------|---------------------|----------------|
| hashlib.sha256 | Fast | Excellent | ✅ Use |
| hashlib.md5 | Very Fast | Good | ⚠️ Acceptable |
| xxhash | Very Fast | Good | ⚠️ Requires external lib |

**Selected:** `hashlib.sha256` (standard library, no dependencies)

### AST Hashing Options

| Method | Accuracy | Speed | Complexity |
|--------|----------|-------|------------|
| ast.dump() + hash | High | Medium | Low |
| ast.unparse() + hash | Very High | Slow | Medium |
| Custom AST walker | High | Fast | High |

**Selected:** `ast.dump() + sha256` (balance of accuracy and simplicity)

### Parallel Execution Options

| Method | Complexity | Compatibility | Recommendation |
|--------|-----------|--------------|----------------|
| asyncio | Medium | Python 3.7+ | ✅ Use |
| threading | Low | Limited by GIL | ❌ Not for CPU-bound |
| multiprocessing | High | All platforms | ⚠️ Overkill |
| concurrent.futures | Low | Python 3.2+ | ✅ Alternative |

**Selected:** `asyncio` with `concurrent.futures.ThreadPoolExecutor` for I/O-bound phases

## Best Practices Research

### Incremental Analysis Patterns

**From: Mozilla Build System**
- Hash-based invalidation
- Dependency propagation
- Pristine "environment" concept

**From: Cargo (Rust)**
- Fingerprint-based cache keys
- Transitive dependency tracking
- Fine-grained invalidation

**Key insight:** Track *inputs* not *outputs* for cache invalidation

### Phase Execution Patterns

**From: Bazel (Google)**
- Topological sorting of DAG
- Parallel execution of independent nodes
- Hermetic execution (no side effects)

**From: Make**
- Dependency graph with timestamps
- Parallel execution with `-j`
- Prerequisite checking

**Key insight:** Build explicit DAG, use topological sort for execution order

## Performance Benchmarks

### Current Performance (Baseline)

| Operation | Time | Files |
|-----------|------|-------|
| Full qual-gate | ~5 min | 28,000 |
| Structure gate | ~30 sec | All |
| Governance gate | ~45 sec | All |
| Duplicate detection | ~2 min | All |

### Expected Performance (After Optimization)

| Operation | Target | Improvement |
|-----------|--------|-------------|
| Single-file change | <10 sec | 30x faster |
| 10-file change | <30 sec | 10x faster |
| Full (parallel) | ~2 min | 2.5x faster |

## Implementation Risks

### Risk 1: Dependency Graph Accuracy
**Probability:** Medium
**Impact:** High
**Mitigation:** Use AST-based import extraction, fall back to full analysis on error

### Risk 2: Hash Database Corruption
**Probability:** Low
**Impact:** Medium
**Mitigation:** Atomic writes, backup on every update

### Risk 3: Phase Deadlock in Parallel Execution
**Probability:** Low
**Impact:** High
**Mitigation:** Timeout mechanism, explicit DAG validation

## Open Questions

1. **Q:** Should hash database be per-project or global?
   **A:** Per-project (TSK directory) for isolation

2. **Q:** How to handle generated files?
   **A:** Exclude via .qualignore pattern

3. **Q:** Should we track line-level changes?
   **A:** No - file-level is sufficient for quality gates

## References

- `P:\__csf.nip\src\quality\qual-gate.py` - Main orchestrator
- `P:\__csf.nip\src\quality\core\dependency_graph.py` - Dependency tracking
- `P:\__csf.nip\src\quality\unified_analyzer.py` - Tool integration
- CWO12 Constitution - Evidence-based development patterns
