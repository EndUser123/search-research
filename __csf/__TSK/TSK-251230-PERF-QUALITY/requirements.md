# Requirements: Quality System Performance Enhancements

**TSK:** TSK-251230-PERF-QUALITY
**Status:** Draft

## Functional Requirements

### FR1: Incremental File Analysis
**Priority:** P0 (Critical)
**Description:** Only analyze files that changed since last run

- FR1.1: Track SHA-256 hash of each analyzed file
- FR1.2: Store hash database in TSK state
- FR1.3: Detect changed files by comparing hashes
- FR1.4: Build dependency graph for import relationships
- FR1.5: Include dependent files in "dirty set" (transitive closure)

**Acceptance Criteria:**
- Single-file change triggers analysis of <100 files (not 28,000)
- Hash lookup completes in <1 second

### FR2: Parallel Phase Execution
**Priority:** P1 (High)
**Description:** Execute independent quality gates concurrently

- FR2.1: Identify phase dependencies (DAG)
- FR2.2: Execute independent phases in parallel
- FR2.3: Merge results after completion
- FR2.4: Handle phase failures gracefully

**Phase Dependency Graph:**
```
[Structure] ─┐
              ├─> [Governance] ─> [Architecture] ─> [Security] ─> [Final]
[Duplicates]─┘                                       ─>
                            [CodeReview] ──────────────┘
```

**Acceptance Criteria:**
- Structure + Duplicates run in parallel
- Overall execution time reduced by 30-50%

### FR3: UnifiedAnalyzer Direct Integration
**Priority:** P1 (High)
**Description:** Fix import issues to use direct tool calls

- FR3.1: Fix import paths for ruff/mypy/bandit
- FR3.2: Eliminate subprocess overhead
- FR3.3: Maintain error handling compatibility

**Acceptance Criteria:**
- No fallback to subprocess for common operations
- 20-30% performance improvement

### FR4: AST-Based Cache Invalidation
**Priority:** P2 (Medium)
**Description:** Use AST hash for cache keys instead of file paths

- FR4.1: Parse source code to AST
- FR4.2: Compute hash of AST structure
- FR4.3: Use AST hash as cache key
- FR4.4: Invalidate cache on structural changes

**Acceptance Criteria:**
- Functionally equivalent changes use cached result
- Structural changes trigger cache invalidation

## Non-Functional Requirements

### NFR1: Performance
| Metric | Target | Measurement |
|--------|--------|-------------|
| Single-file analysis | <10 seconds | Time from start to result |
| Incremental analysis | 10-50x faster | Compare to full analysis |
| Full analysis (parallel) | 2-3x faster | Compare to sequential |
| Hash lookup | <1 second | Database query time |

### NFR2: Maintainability
- Code must follow existing patterns
- No external dependencies beyond standard library
- Self-documenting with clear intent

### NFR3: Reliability
- Graceful degradation if features fail
- Fallback to full analysis if incremental fails
- No data loss (hash database must be durable)

### NFR4: Compatibility
- Python 3.14+
- Windows/Linux/macOS
- Existing qual-gate command interface

## Technical Requirements

### TR1: File Hash Storage
```python
# SQLite schema for hash database
CREATE TABLE file_hashes (
    path TEXT PRIMARY KEY,
    sha256 TEXT NOT NULL,
    ast_hash TEXT,
    last_analyzed TEXT,
    depends_on TEXT  -- JSON array of paths
);
```

### TR2: Dependency Graph
```python
# Track import relationships
class DependencyGraph:
    def add_edge(self, from_file: str, to_file: str)
    def get_dependents(self, file: str) -> set[str]
    def get_transitive_closure(self, files: set[str]) -> set[str]
```

### TR3: Parallel Execution
```python
# Phase executor with parallel support
async def execute_parallel(phases: list[Phase]) -> dict[str, Result]:
    # Build dependency graph
    # Execute independent phases concurrently
    # Wait for all to complete
    pass
```

## Data Requirements

### DR1: Hash Database
- Location: `{TSK_DIR}/file_hashes.db`
- Format: SQLite
- Size estimate: ~5MB for 28,000 files

### DR2: State Persistence
- Location: `{TSK_DIR}/qual-gate-state.json`
- Must include: last_run, completed_phases, file_hashes_version

## Security Requirements

- SR1: Hash database must validate paths (no directory traversal)
- SR2: Cache keys must use cryptographic hash (SHA-256)

## Compliance Requirements

- CR1: Follow CWO12 constitutional patterns
- CR2: Evidence-based development (store all analysis in evidence/)
- CR3: TDD implementation for all new code
