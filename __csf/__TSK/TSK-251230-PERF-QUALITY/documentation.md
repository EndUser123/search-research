# Quality System Performance - Documentation

## API Reference

### Incremental Analysis

```python
from quality.incremental import IncrementalAnalyzer, create_incremental_analyzer

# Create analyzer with state tracking
analyzer = create_incremental_analyzer(".quality/state.db", enabled=True)

# Get dirty files (only changed files)
dirty = analyzer.get_dirty_files(file_list)

# Mark files as analyzed after processing
analyzer.mark_analyzed(processed_files, dependencies=file_imports)
```

### Parallel Execution

```python
from quality.parallel import AsyncPhaseExecutor, PhaseDAG

# Create executor with phase DAG
executor = AsyncPhaseExecutor(dag=PhaseDAG())
executor.phase_functions = {
    "ruff": run_ruff,
    "mypy": run_mypy,
    "bandit": run_bandit,
}

# Run all phases in parallel (respecting dependencies)
results = await executor.run_all()

# Get statistics
stats = executor.get_statistics()
```

### AST-Based Cache Keys

```python
from quality.incremental import compute_cache_key, ASTCacheKeyGenerator

# Generate cache key
key = compute_cache_key("ruff", "src/mylib.py", options={"fix": False})

# Check if cache should be invalidated
generator = ASTCacheKeyGenerator()
should_invalidate = generator.should_invalidate(old_key, new_content)
```

## Usage in qual-gate

```bash
# Run with incremental analysis (default)
qual-gate src/

# Run with parallel execution
qual-gate src/ --parallel

# Combined: incremental + parallel
qual-gate src/ --parallel
```

## Performance Characteristics

- **Incremental skips**: Unchanged files not re-analyzed
- **Parallel speedup**: 2-3x for independent phases
- **Cache hit detection**: Sub-millisecond for cached files
- **Scale**: Handles 1000+ files efficiently


