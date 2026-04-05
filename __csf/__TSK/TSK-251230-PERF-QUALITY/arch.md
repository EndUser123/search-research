# Architecture: Quality System Performance Enhancements

**TSK:** TSK-251230-PERF-QUALITY
**Status:** Draft

## System Architecture

### Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        qual-gate.py                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │              State Management                         │  │
│  │  • file_hashes: dict[str, str]                       │  │
│  │  • completed_phases: list[str]                       │  │
│  │  • last_run: datetime                                │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │           Sequential Phase Executor                   │  │
│  │  Structure → Duplicates → Governance → Architecture   │  │
│  │       → Security → APIs → CodeReview → Performance    │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            UnifiedAnalyzer (or subprocess)            │  │
│  │  • ruff    → linting                                 │  │
│  │  • mypy    → type checking                           │  │
│  │  • bandit  → security scanning                       │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Target Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        qual-gate.py                          │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Incremental Analysis Layer                  │  │
│  │  • FileHashDB: SQLite-based hash storage            │  │
│  │  • DependencyGraph: Import relationship tracker     │  │
│  │  • DirtySet: Changed files + transitive deps         │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Parallel Phase Executor (async)              │  │
│  │  Structure │ Duplicates ──┐                           │  │
│  │            │              ├──> Governance ─> ...      │  │
│  │  ┌─────────┴─────────┐    │                           │  │
│  │  │   Phase DAG       │    │                           │  │
│  │  │   (dependencies)  │    │                           │  │
│  │  └──────────────────┘    │                           │  │
│  └──────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌──────────────────────────────────────────────────────┐  │
│  │          Direct Tool Integration                      │  │
│  │  • ruff    → direct Python calls                     │  │
│  │  • mypy    → direct Python calls                     │  │
│  │  • bandit  → direct Python calls                     │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Component Design

### C1: FileHashDB

**Purpose:** Persistent storage of file hashes and metadata

**Schema:**
```sql
CREATE TABLE file_hashes (
    path TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    ast_hash TEXT,
    last_analyzed TIMESTAMP,
    file_size INTEGER,
    depends_on TEXT  -- JSON array of paths this file imports
);

CREATE INDEX idx_sha256 ON file_hashes(sha256);
CREATE INDEX idx_last_analyzed ON file_hashes(last_analyzed);
```

**API:**
```python
class FileHashDB:
    def __init__(self, db_path: Path)
    def get_hash(self, path: str) -> str | None
    def set_hash(self, path: str, sha256: str, ast_hash: str = None)
    def get_dirty_files(self, changed_paths: list[str]) -> set[str]
    def update_dependencies(self, path: str, depends_on: list[str])
```

### C2: IncrementalAnalyzer

**Purpose:** Determine minimal set of files to analyze

**Algorithm:**
```
1. Scan target directory for all Python files
2. For each file:
   a. Compute SHA-256 hash
   b. Compare with stored hash
   c. If different: mark as dirty
3. For dirty files:
   a. Parse AST to find imports
   b. Build dependency graph
   c. Compute transitive closure (dependents)
4. Return dirty set for analysis
```

**Complexity:**
- Hash computation: O(n) where n = total files
- Dependency lookup: O(d) where d = dirty files
- Transitive closure: O(d * avg_deps)

### C3: ParallelPhaseExecutor

**Purpose:** Execute independent phases concurrently

**Phase Dependency DAG:**
```python
PHASE_DEPENDENCIES = {
    "constitutional": [],  # No deps
    "structure": [],       # No deps
    "duplicates": [],      # No deps
    "governance": ["constitutional"],
    "architecture": ["structure", "duplicates"],
    "security": ["governance"],
    "apis_services": ["architecture", "security"],
    "code_review": ["architecture"],
    "performance": ["apis_services", "code_review"],
    "final_check": ["performance"],
}
```

**Execution Strategy:**
```python
async def execute_parallel(phases: list[str]):
    # 1. Build dependency graph
    dag = build_phase_graph(phases)

    # 2. Find executable phases (no pending deps)
    ready = find_ready_phases(dag)

    # 3. Execute in parallel
    tasks = [asyncio.create_task(run_phase(p)) for p in ready]

    # 4. Wait for completion, repeat until done
    while tasks:
        done, pending = await asyncio.wait(tasks)
        for task in done:
            mark_complete(task.result)
        ready = find_ready_phases(dag)
        tasks = pending + [asyncio.create_task(run_phase(p)) for p in ready]
```

### C4: UnifiedAnalyzer Fix

**Issue:** Import paths broken after module restructure

**Solution:**
```python
# Before (broken):
from src.quality.tools import ruff, mypy, bandit

# After (fixed):
from __csf.nip.src.quality.tools import ruff, mypy, bandit
# OR
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from quality.tools import ruff, mypy, bandit
```

## Data Flow

### Incremental Analysis Flow

```
User runs /quality
       │
       ▼
┌──────────────────┐
│  FileHashDB.get  │  ← Look up stored hashes
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Scan directory  │  ← Find all .py files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Compute hashes   │  ← SHA-256 for each file
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Compare hashes   │  ← dirty = changed files
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ DependencyGraph  │  ← Get dependents of dirty files
│  .get_dependents │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│  Transitive      │  ← Full dirty set
│    closure       │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Run phases on    │  ← Only analyze dirty files
│  dirty_set only  │
└──────────────────┘
```

## Reversibility Assessment

| Component | Reversibility | Rollback Plan |
|-----------|--------------|---------------|
| FileHashDB | High | Delete DB, falls back to full analysis |
| ParallelExecutor | High | Flag to disable parallelism |
| UnifiedAnalyzer fix | Medium | Keep subprocess fallback |
| Dependency tracking | Medium | Fallback to file list scan |

**Overall Reversibility Score:** 1.8 (Very Reversible)

## Blast Radius Analysis

| Change | Affected Components | Risk Level |
|--------|-------------------|------------|
| FileHashDB | qual-gate.py, state files | Low |
| Parallel execution | Phase execution only | Low |
| UnifiedAnalyzer fix | Tool integration | Medium |
| Dependency graph | Existing component, enhancement | Low |

**Maximum Blast Radius:** Limited to quality gate execution

## Testing Strategy

### Unit Tests
- `test_file_hash_db.py` - CRUD operations
- `test_incremental_analyzer.py` - Dirty set computation
- `test_parallel_executor.py` - Phase DAG resolution

### Integration Tests
- `test_qual_gate_incremental.py` - End-to-end incremental flow
- `test_parallel_phases.py` - Concurrent phase execution

### Performance Tests
- `test_benchmark_single_file.py` - <10 sec target
- `test_benchmark_parallel.py` - 2-3x improvement target
