# Implementation Plan: Tree-Sitter Multi-Language Backend Integration

**Date:** 2025-03-08
**Status:** REVISED (after adversarial review)
**Decision:** Create hybrid tree-sitter backend for search-research package
**ADVERSARIAL REVIEW:** 24 findings applied (7 CRITICAL, 11 HIGH, 6 MEDIUM)

---

## Problem Statement

Our current search system has a Python-only AST backend (CDS) that provides fast docstring and symbol search with 10-50x cache speedup. However, we cannot search non-Python codebases (JavaScript, TypeScript, Go, Rust, Java, PHP, etc.) which limits our code exploration capabilities.

**Key Constraints:**
- Must preserve existing CDS optimizations for Python
- Must integrate with `search-research` package (NOT deprecated `unified_router.py`)
- Must be token-efficient for AI agent consumption
- Solo-dev appropriate (no enterprise infrastructure)

---

## Context Analysis

### Current Architecture

**CDS Backend** (`P:/__csf/src/search/backends/cds_backend.py`):
- Python's built-in `ast` module for parsing
- Persistent disk cache with mtime invalidation
- Docstring search, symbol finding, importer discovery
- Integrated into unified router with CHS, CKS, Grep backends
- 10-50x speedup on subsequent searches via caching

### Research Findings (Tavily Research)

**Proven Architecture Pattern:**
- Hybrid index: trigram + FTS5 + AST metadata + optional vector layer [16,44,45]
- Official tree-sitter Python bindings [6]
- Prebuilt language packs (165+ languages) [1,2,3,4]
- Incremental parsing via `tree.edit()` [45]
- multiprocessing for CPU-bound parsing (avoid GIL) [48,49]

**Performance Expectations:**
- Parse throughput: 100-1000 files/sec [10]
- Search latency: <50ms for indexed queries [16]
- Index size: 2-5x original source [16]
- Memory: ~1-2GB per 100K files (cached trees) [10]

---

## Existing Implementation Discovery

### Current CDS Implementation

**File:** `P:/__csf/src/search/backends/cds_backend.py`

**Key Classes:**
- `CDSBackend` - Main backend class with caching
- `build_index()` - AST indexing with persistent cache
- `search()` - Symbol and docstring search
- `find_importers()` - Import dependency discovery
- `find_definition()` - Symbol location lookup

**Cache Strategy:**
- Pickle-based index storage (`~/.cache/cds/index.pkl`)
- JSON metadata with mtimes (`~/.cache/cds/meta.json`)
- mtime-based invalidation (checks if source files newer than cache)
- Cache key from root paths MD5

**Integration Points:**
- `search-research` package (PRIMARY integration target)
- CDS backend for Python (keep existing)
- Language-based routing via search-research API

### Dependencies to Verify

**Required Packages:**
- `tree-sitter` - Official Python bindings [6]
- `tree-sitter-language-pack` - **CHOSEN**: 165+ languages, Python ≥3.10 [3]
  - **Rationale**: Broader language coverage (165 vs 48), prebuilt wheels, active maintenance
  - **Alternative considered**: `py-tree-sitter-languages` (48 languages) [1,2] - rejected due to limited coverage
- `lmdb` - Storage engine for AST metadata [39]
  - **Location**: Add to `P:/__csf/pyproject.toml` under dependencies

**Storage Engine Selection:**
- `lmdb` - **CHOSEN**: Lockless reads, MVCC, high read performance [39]
  - **Rationale**: Better for read-heavy workloads (search queries), simpler API than RocksDB
  - **Alternative considered**: `rocksdb` (better write throughput) [38] - rejected due to complexity

**SQLite FTS5** (built into Python 3.10+) for token search [44]

**Python Version Compatibility:**
- Current system: Python 3.14.0 ✅
- Required: Python ≥3.10 (tree-sitter-language-pack requirement) [3]
- **Action**: Verify Python 3.14 compatibility with tree-sitter-language-pack before implementation

### Existing Tree-Sitter Implementations

**Discovery:** Found 4 existing tree-sitter files that need audit/integration:

1. **`P:/__csf/src/cli/nip/tree_sitter_wrapper.py`**
   - Purpose: Unknown (needs audit)
   - Action: Review for reuse or deprecation

2. **`P:/__csf/src/commands/rca/tree_sitter_integration.py`**
   - Purpose: RCA integration
   - Action: Review for API patterns

3. **`P:/__csf/src/modules/discover/hardware_accelerated/tree_sitter_enhanced.py`**
   - Purpose: Discovery enhancement
   - Action: Review for consolidation

4. **`P:/__csf/src/quality/refactor_orchestrator/tree_sitter_parser.py`**
   - Purpose: Refactoring support
   - Action: Review for API compatibility

**Integration Strategy:**
- Audit these files for reusable patterns
- Consolidate or deprecate redundant implementations
- Ensure API compatibility across all tree-sitter usage

---

## Test Discovery

### Test Coverage Needed

**Unit Tests:**
1. Tree-sitter parser initialization for target languages
2. Incremental parsing via `tree.edit()`
3. Symbol extraction (functions, classes, methods)
4. Trigram index build/search
5. FTS5 token search
6. Cache invalidation (mtime-based)
7. Language routing logic

**Integration Tests:**
1. search-research package integration (Python → CDS, other → tree-sitter)
2. Cross-language symbol search
3. Cache coherency between CDS and tree-sitter
4. Performance benchmarks (parse throughput, search latency)

**Edge Cases:**
1. Large files (>10K lines)
2. Binary file detection
3. Symlink handling
4. Concurrent indexing (multiprocessing)
5. Cache corruption recovery
6. Deep nesting (50+ levels) - TEST-003
7. Malformed files with syntax errors - TEST-008
8. File encoding issues (Latin-1, UTF-16, mixed) - EDGE-007
9. Circular symlinks - TEST-009

**Performance Tests:**
1. Parse 100 Python files (CDS vs tree-sitter)
2. Search latency p50/p95/p99
3. Memory footprint during indexing
4. Index size on disk

### Test File Locations

**Unit Tests:**
- `P:/__csf/src/search/backends/tests/test_tree_sitter_parser.py`
- `P:/__csf/src/search/backends/tests/test_trigram_index.py`
- `P:/__csf/src/search/backends/tests/test_fts5_prefilter.py`
- `P:/__csf/src/search/backends/tests/test_ast_metadata_store.py`

**Integration Tests:**
- `P:/__csf/src/search/backends/tests/test_tree_sitter_integration.py`
- `P:/__csf/src/search/backends/tests/test_search_research_routing.py`

**Performance Tests:**
- `P:/__csf/src/search/benchmarks/test_tree_sitter_performance.py`

**Test Fixtures:**
- `P:/__csf/src/search/backends/tests/fixtures/`

**Basic Fixtures (100 lines each):**
  - `python_sample.py`
  - `javascript_sample.js`
  - `typescript_sample.ts`
  - `go_sample.go`
  - `rust_sample.rs`
  - `java_sample.java`
  - `php_sample.php`

**Stress Fixtures (TEST-003):**
  - `python_large.py` (2000 lines, 50+ nesting levels)
  - `real_world_sample.py` (5000 lines from open-source)
  - `rust_complex.rs` (complex generics, macros)
  - `go_build_tags.go` (build tag variations)

**Malformed Fixtures (TEST-008):**
  - `syntax_error_mid.js` (error at line 500)
  - `truncated.py` (incomplete function)
  - `binary_misclassified.txt` (binary file)

**Encoding Fixtures (EDGE-007):**
  - `latin1_file.py` (Latin-1 encoding)
  - `utf16_file.js` (UTF-16)
  - `mixed_encoding.ts` (mixed encodings)

**Symlink Fixtures (TEST-009):**
  - `symlink_file.py` (file symlink)
  - `symlink_dir/` (directory symlink)
  - `circular_symlink.py` (circular link test)

---

## Proposed Solution

### Architecture

```
src/search/backends/
├── cds_backend.py              # KEEP: Python AST (fast, docstrings)
├── tree_sitter_backend.py      # NEW: Multi-language hybrid
│   ├── TrigramIndex            # Zoekt-style literal/regex [16]
│   ├── FTS5Prefilter           # SQLite token search [44]
│   ├── ASTMetadataStore        # LMDB/RocksDB [38,39]
│   └── TreeSitterParser        # Official bindings [6]
└── unified_router.py           # UPDATE: Language-based routing
```

### Hybrid Design

**Per-query pipeline:**
1. Trigram index → candidate files (literal/regex) [16]
2. FTS5 → token prefiltering [44]
3. AST metadata → structural queries [11]
4. Optional: Vector re-rank for semantic [45]

**Backend Selection:**
```python
def route_search(language: str, query_type: str) -> str:
    if language == "python" and query_type in ["docstring", "symbol"]:
        return "cds"  # Use optimized Python backend
    else:
        return "tree_sitter"  # Multi-language support
```

### Key Features from jcodemunch-mcp

**Extract (don't clone):**
1. Stable symbol IDs: `{file_path}::{qualified_name}#{kind}`
2. Byte-offset seeking for O(1) retrieval
3. Multi-language symbol extraction
4. Import dependency indexing

**NOT implementing:**
- MCP server layer (we have unified router)
- GitHub repo indexing (use local file system)
- Token cost tracking (not relevant for backend)

---

## Implementation Plan

### Phase -1: Strategic Validation (NEW - 2-3 days)
**ADDED:** Validate plan premises before committing resources.

**T-NEG-001: Validate multi-language search demand**
- File: Search query logs analysis
- Action: Audit last 3 months of search queries to quantify non-Python demand
- Acceptance:
  - Calculate % of non-Python search queries
  - Document grep/ripgrep usage patterns for non-Python files
  - If non-Python demand <20%, STOP and use grep/ripgrep instead
  - If non-Python demand >20%, proceed to Phase 0
- **Rationale:** Solo-dev constraint - don't build for edge cases without evidence

**T-NEG-002: Audit existing tree-sitter implementations FIRST**
- File: `P:/__csf/src/cli/nip/tree_sitter_wrapper.py` (and 3 others)
- Action: Functional testing of all 4 existing implementations
- Acceptance:
  - Document what each implementation already does
  - Measure their performance on realistic workloads
  - Identify gaps (what's missing vs. what works)
  - Decision: extend existing vs. build new
- **Rationale:** QUAL-001 - Avoid creating duplicate implementations

**T-NEG-003: ROI analysis - CDS optimization vs. tree-sitter**
- File: CDS backend performance measurement
- Action: Measure CDS current performance, identify optimization opportunities
- Acceptance:
  - Measure CDS parse throughput and search latency
  - Identify bottlenecks (cache warmup? serialization?)
  - Estimate improvement potential from CDS optimization (1 week work)
  - If CDS optimization yields >50% latency reduction, prioritize that
  - If CDS improvements <30%, proceed with tree-sitter
- **Rationale:** STRAT-004 - Opportunity cost assessment

### Phase 0: Pre-Implementation Tasks (1-2 days)
**UPDATED:** Added dependency verification and API discovery tasks.

**T-000: Review search-research package migration guide**
- File: `P:/packages/search-research/MIGRATION.md`
- Action: Understand correct integration target and API patterns
- Acceptance:
  - **VERIFIED:** MIGRATION.md file exists and is readable
  - Document backend registration API with code examples
  - Document routing mechanism with integration test
  - Document cache coherency requirements with API signatures
  - Create stub backend that registers successfully (proof of API access)
- **ADDED:** COMP-002 - Must verify API before designing backend

**T-000.0: Define LMDB storage strategy and limits**
- File: Storage design document (NEW)
- Action: Design LMDB map_size management, memory budget, and growth strategy
- Acceptance:
  - Define explicit memory budget (e.g., 500MB cap for cached trees)
  - Document LMDB map_size configuration strategy
  - Implement pre-flight check: calculate estimated index size before building
  - Error with clear message if exceeding safe threshold
  - **Passive checks:** Log warning on startup if LMDB >80% capacity (NOT always-running monitoring service)
- **ADDED:** EDGE-001, EDGE-003 - Address LMDB 2GB limit and memory exhaustion

**T-000.1: Audit existing tree-sitter implementations (MOVED TO FIRST)**
- File: `P:/__csf/src/cli/nip/tree_sitter_wrapper.py` (and 3 others)
- Action: Review for reusable patterns, API compatibility, consolidation opportunities
- Acceptance:
  - Document each implementation's purpose, API, and usage patterns
  - Identify reusable code patterns
  - Create decision matrix: consolidate vs. deprecate vs. keep separate
  - Integration test: load all 4 implementations simultaneously, verify no conflicts
  - **BLOCKS T-001** until audit complete
- **UPDATED:** QUAL-001 - Must complete before installing dependencies
- **ORDERING:** LOGIC-001 - Moved before T-001

**T-000.2: Verify Python 3.14 compatibility**
- File: Test script (NEW)
- Action: Test tree-sitter-language-pack with Python 3.14
- Acceptance:
  - Import tree-sitter successfully
  - Load and parse files with 7 language grammars (expanded from 2)
  - Test multiprocessing with tree-sitter (Python 3.14 spawn behavior on Windows)
  - Test LMDB integration
  - Test tree.edit() incremental parsing
  - Document any compatibility issues
- **UPDATED:** COMP-010 - Expanded to test production usage patterns

**T-000.3: Verify CDS backend API compatibility**
- File: `P:/__csf/src/search/backends/cds_backend.py`
- Action: Review CDS API for tree-sitter backend design compatibility
- Acceptance:
  - Document CDS backend interface
  - Identify shared patterns (cache, indexing)
  - Ensure consistent query/response formats
- **NOTE:** LOGIC-001 - This should come AFTER T-000 documents search-research API

**T-000.4: Add security and sanitization layer**
- File: File classification module (NEW)
- Action: Implement input validation and sensitive data detection
- Acceptance:
  - File classification: exclude .env, .pem, .key, credentials files
  - High-entropy string detection (potential secrets)
  - Implement content sanitization before indexing
  - Configurable denylist for sensitive paths
  - Add opt-in/out for specific file patterns
- **ADDED:** SEC-001 - Prevent data leaks from indexed files

### Phase 1: Proof of Concept (2 days)

**T-001: Install dependencies and validate tree-sitter**
- File: `requirements.txt` or `pyproject.toml`
- Action: Add `tree-sitter`, `tree-sitter-language-pack`, `lmdb`
- Acceptance:
  - `import tree_sitter` succeeds
  - Load 2 languages (Python, JavaScript)
  - Parse 5 Python files successfully (gates T-002)
  - **Addresses:** LOGIC-003 (temporal contradiction)

**T-002: Benchmark tree-sitter vs CDS for Python**
- File: `P:/__csf/src/search/benchmarks/tree_sitter_bench.py` (NEW)
- Action: Parse 100 Python files with both backends, measure time
- Acceptance:
  - **Token measurement:** Compare full-file token count vs AST metadata, establish threshold <20% of full-file tokens
  - **Single-pass benchmarking:** Parse 100 files once, 1,000 files once, document actual times
  - Document parse throughput (files/sec)
  - Document search latency (ms)
  - Decision: "Is tree-sitter slowdown acceptable?" (<2x CDS)
  - **Addresses:** LOGIC-005 (undefined metric), simplified for solo dev pragmatism

**T-011: Integrate with search-research package** (MOVED from Phase 3)
- File: `P:/packages/search-research/src/backends/tree_sitter_backend.py` (NEW)
- Action: Register tree-sitter backend with search-research router
- Acceptance:
  - Python queries route to CDS
  - Other languages route to tree-sitter
  - Fallback to Grep for unknown
  - Cache coherency maintained
  - **Reason:** Must validate integration before building backend
  - **Addresses:** QUAL-005

**T-003: Basic symbol extraction test**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py` (NEW)
- Action: Extract functions/classes from 10 files
- Acceptance:
  - **File parsing safety:** Implement file classification before T-003, apply security sanitization from T-000.4
  - Extract symbol names correctly
  - Generate stable symbol IDs
  - Store in LMDB
  - **Addresses:** SEC-001, SEC-007

**T-012: Create multi-language test fixtures** (MOVED from Phase 3)
- File: `P:/__csf/src/search/backends/tests/fixtures/` (NEW DIRECTORY)
- Action: Create sample code files in 7 languages (Python, JS, TS, Go, Rust, Java, PHP)
- Acceptance:
  - Each file has functions, classes, methods
  - Files represent realistic code patterns
  - Used for cross-language testing
  - **Reason:** T-006 needs test fixtures before parsing 7 languages
  - **Addresses:** LOGIC-010

### Phase 2: Minimal Backend (3 days)

**T-004: Implement TrigramIndex**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: Build Zoekt-style trigram index for literal/regex
- Acceptance:
  - Create proof-of-concept trigram index, measure actual Python performance
  - Handle Unicode correctly
  - **Addresses:** PERF-001, PERF-006 (unrealistic expectations)

**T-005: Implement FTS5Prefilter**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: SQLite FTS5 token search for prefiltering
- Acceptance:
  - Tokenize code correctly
  - Prefix search works
  - **Parameterized query requirement:** Use parameterized queries exclusively (never string interpolation), implement query parsing for boolean operators
  - **Addresses:** SEC-006 (SQL injection prevention)

**T-006: Implement TreeSitterParser**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: Wrapper for official tree-sitter bindings
- Acceptance:
  - Parse 7 languages (Python, JS, TS, Go, Rust, Java, PHP)
  - Incremental parsing via `tree.edit()`
  - Error recovery for malformed files
  - **Error handling policy:** Parse errors should log file+error, skip with warning, NEVER crash indexing, store 'parse_failed' flag in metadata
  - **Symbol ID format:** `{file_path}::{language}::{qualified_name}#{kind}`
  - **Addresses:** EDGE-002 (malformed file handling), EDGE-009 (symbol collisions)

**T-007: Implement ASTMetadataStore**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: LMDB storage for AST metadata
- Acceptance:
  - Store symbol locations (byte ranges)
  - Query by symbol ID <10ms
  - Cache hot files in memory
  - **LMDB permissions enforcement:** Enforce 0600 permissions on database creation
  - **Cache corruption recovery test:** Test: Corrupt LMDB file, verify detection and rebuild
  - **LMDB map_size monitoring:** Test: Index 10K files, verify map_size growth
  - **Addresses:** SEC-002 (access controls), QUAL-003, EDGE-010, TEST-007, EDGE-001

### Phase 3: Advanced Features (5 days)

**T-008: REMOVED** - Incremental parsing invalidates byte offsets (EDGE-006)
- **REPLACED WITH:** Reparse changed files, update LMDB entries
- **Addresses:** EDGE-006

**T-009: Add structural query API**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: Tree-sitter query language support
- Acceptance:
  - Support S-expression patterns
  - Pattern metavariables (@capture)
  - Verification against cached trees

**T-010: Implement multiprocessing for parsing**
- File: `P:/__csf/src/search/backends/tree_sitter_backend.py`
- Action: Parse files in parallel (avoid GIL)
- **CHANGED:** Multiprocessing strategy - Use single-process writer with multiprocessing queue, subprocesses return parsed ASTs → main process writes to LMDB
- Acceptance:
  - 4x speedup on 4-core machine
  - Correct error handling in subprocesses
  - Progress tracking
  - **ADDED TEST:** 4 processes writing 1000 files each, verify no corruption
  - **Addresses:** EDGE-004 (multiprocessing corruption), TEST-001

**T-010.5: Token efficiency measurement** (NEW)
- File: `P:/__csf/src/search/benchmarks/token_efficiency.py` (NEW)
- Action: Measure token reduction: full-file vs AST metadata
- Acceptance:
  - Baseline: Current search token count
  - Target: <20% of full-file tokens
  - Document actual reduction ratio
  - **Addresses:** LOGIC-005

**T-011 and T-012: MOVED to Phase 1** - See Phase 1 section above

**T-013: Integration testing**
- File: `P:/__csf/src/search/backends/tests/test_tree_sitter_integration.py` (NEW)
- Action: Test cross-language search, cache coherency
- Acceptance:
  - Search JS symbols from Python code
  - Cache invalidation works
  - No duplicate results across backends

**T-013.5: Cache coherency model definition** (NEW)
- File: `P:/__csf/src/search/backends/cache_coherency.py` (NEW)
- Action: Define cache coherency semantics
- Acceptance:
  - Define cache coherency semantics
  - Document invalidation propagation
  - Define merge strategy for conflicting cache states
  - Test: verify invalidation propagates within 1 second
  - **Addresses:** QUAL-008, COMP-008

**T-013.6: CDS + tree-sitter cache coherency test** (NEW)
- File: `P:/__csf/src/search/backends/tests/test_cache_coherency.py` (NEW)
- Action: Create test: modify file externally, query both backends
- Acceptance:
  - Modify file externally, query both backends
  - Verify both return fresh data
  - Test cache invalidation race conditions
  - **Addresses:** TEST-002, EDGE-08

### Phase 4: Documentation & Rollout (2 days)

**T-014: Update documentation**
- File: `P:/__csf/src/search/README.md`
- Action: Document tree-sitter backend, configuration
- Acceptance:
  - Installation instructions
  - Configuration options (languages, cache paths)
  - Performance characteristics

**T-015: Create migration guide**
- File: `P:/__csf/docs/migration/tree_sitter.md` (NEW)
- Action: Guide for migrating from CDS-only to hybrid
- Acceptance:
  - When to use CDS vs tree-sitter
  - Performance expectations
  - Troubleshooting common issues

**T-016: Rollout to production**
- File: N/A (deployment)
- Action: Deploy to production, monitor
- Acceptance:
  - No regression in Python search performance
  - New languages searchable
  - Memory usage within limits (<2GB per 100K files)

---

## Risks, Success Criteria, Dependencies

### Top Risks

1. **Integration with deprecated unified_router** - Plan initially targeted deprecated `unified_router.py` (EOL 2026-09-01)
   - **Mitigation:** Use `search-research` package as integration target, follow migration guide at `P:/packages/search-research/MIGRATION.md`

2. **Conflict with existing tree-sitter code** - 4 existing tree-sitter implementations may have conflicting patterns
   - **Mitigation:** Audit all existing implementations in Phase 0 (T-000.1), consolidate or deprecate redundant code

3. **Performance degradation** - tree-sitter 2-10x slower than Python AST for same files
   - **Mitigation:** Keep CDS for Python, use tree-sitter only for non-Python

4. **Memory footprint** - Cached parse trees consume 1-2GB per 100K files
   - **Mitigation:** Cache hot files only, reparse cold files on demand

5. **Maintenance burden** - Upstream grammar updates require monitoring
   - **Mitigation:** Pin language pack versions, schedule quarterly updates

6. **LMDB 2GB database limit** (EDGE-001)
   - **Mitigation:** Pre-flight size estimation, map_size configuration, monitoring

7. **Memory exhaustion** - 100K files could consume 100-250GB (EDGE-003)
   - **Mitigation:** 500MB memory cap, LRU eviction, sliding window cache

8. **Multiprocessing LMDB corruption** (EDGE-004)
   - **Mitigation:** Single-process writer with multiprocessing queue

9. **Incremental parsing breaks byte offsets** (EDGE-006)
   - **Mitigation:** Removed T-008, use full reparse instead

10. **False dichotomy in routing logic** (LOGIC-002)
    - **Mitigation:** Pipeline stages apply to all languages, remove artificial either/or

11. **Circular dependency in task ordering** (LOGIC-001, LOGIC-003)
    - **Mitigation:** Reordered tasks, added explicit gates

12. **165 language claim vs. 7 tested** (COMP-001)
    - **Mitigation:** Document support tiers, add "beta" disclaimer for untested

13. **Data leaks from indexed code** (SEC-001)
    - **Mitigation:** File classification, high-entropy detection, denylists

14. **LMDB access control gaps** (SEC-002)
    - **Mitigation:** 0600 permissions, optional encryption

15. **Parser exploitability** (SEC-003)
    - **Mitigation:** 5s timeout per file, memory limits, max file size limits

16. **Supply chain attacks** (SEC-004)
    - **Mitigation:** Dependency pinning with checksums, SBOM generation

17. **Pickle deserialization risks** (SEC-005)
    - **Mitigation:** Consider safe serialization (JSON, msgpack) for future

18. **SQL injection via FTS5** (SEC-006)
    - **Mitigation:** Parameterized queries exclusively

### Success Criteria

**Functional:**
- Search 7 validated languages with documented support matrix (COMP-001, COMP-004)
  - Support tiers: Validated (tested, performance baselined), Experimental (parses, no performance guarantees), Unsupported
- Integration with search-research package router successful
- Cache coherency between CDS and tree-sitter backends

**Performance:**
- Parse throughput: MEASURED in T-002 (single-pass: 100 files, 1,000 files)
- Search latency: <100ms for typical indexed queries (measured once)
- Tree-sitter slowdown: <2x CDS for Python OR <5x for non-Python (LOGIC-006)
- Token efficiency: AST metadata <20% of full-file token count (LOGIC-005)

**Security:**
- No indexing of .env, .pem, .key files without opt-in (SEC-001)
- LMDB databases have 0600 permissions (SEC-002)
- Malformed files never crash indexing (EDGE-002)

**Maintainability:**
- Test coverage >80%, measured with pytest-cov (LOGIC-007)
- Language support matrix documents validation status for all 165 languages (COMP-001)
- Cache coherency model documented and tested (QUAL-008)

**User-Facing Metrics** (STRAT-008):
- Reduce average investigation time by 70%
- 90% of symbol searches return relevant result in <30 seconds
- Zero "I can't find X" complaints for 3 months post-deployment

### Dependencies

**Blocking:**
- None (can start immediately)

**Required:**
- Python ≥3.10 (tree-sitter-language-pack requirement) [3]
- LMDB or RocksDB installation [38,39]
- tree-sitter Python bindings [6]

**Nice-to-have:**
- Vector store (Qdrant/FAISS) for semantic re-ranking [45]

---

## Rollback Strategy

**LMDB corruption recovery** (EDGE-010):
1. On startup: Run LMDB mdb_stat check
2. Verify integrity in read-only mode
3. If corrupted: restore from backup or force rebuild
4. Implement periodic backups (copy LMDB directory after full index)

**If performance unacceptable (<2x CDS slowdown):**
1. Disable tree-sitter backend in router
2. Revert to CDS-only for Python
3. Keep tree-sitter available for explicit opt-in (--backend tree-sitter flag)

**If memory footprint too high:**
1. Reduce in-memory cache size
2. Disable tree caching for large files (>10K lines)
3. Fall back to on-demand parsing

**If integration issues:**
1. Opt-in via configuration flag or per-command flag (--backend tree-sitter)
2. User enables when ready via configuration (REMOVED: gradual rollout and feature flag - COMP-004, COMP-009)
3. Monitor error rates, latency p95

**Value checkpoints** (STRAT-009):
- **Phase -1 → GO/NO-GO decision** based on demand validation
  - If <20% multi-language demand: STOP, use grep/ripgrep instead
  - If existing implementation sufficient: EXTEND vs. BUILD NEW decision
  - If CDS optimization yields >50% improvement: PRIORITIZE CDS work
- **Phase 1 → Proof of value**: Benchmark shows acceptable performance (<2x CDS for Python, <5x for non-Python)
- **Phase 2 → Working prototype**: Functional on real data (7 languages, 100+ files)
- **Phase 3 → Production-ready**: All features implemented and tested

---

## Evidence Sources

1. **tree-sitter documentation** - Official Python API [6]
2. **stsearch research** - Parse vs search separation methodology [10]
3. **Zoekt (Sourcegraph)** - Trigram indexing architecture [16]
4. **SQLite FTS5** - Compact token search [44]
5. **tree-sitter-language-pack** - Prebuilt grammars [3]
6. **LMDB performance** - Lockless reads, MVCC [39]
7. **ast-grep** - Structural pattern language [15]
8. **jcodemunch-mcp repo** - Multi-language symbol extraction patterns

---

## Total Effort Estimate

- **Phase -1 (Strategic Validation):** 2-3 days
- **Phase 0 (Pre-Implementation):** 1-2 days
- **Phase 1 (Proof of Concept):** 2-3 days
- **Phase 2 (Minimal Backend):** 3-4 days
- **Phase 3 (Advanced Features):** 6-7 days
- **Phase 4 (Documentation & Rollout):** 2-3 days
- **search-research learning curve:** +2-3 days (new package integration)

**Total:** 19-23 days (approximately 4 weeks)

**Confidence:** 70% - Increased from 65% due to simplified benchmarking

**Effort breakdown from original 15-16 days:**
- **Phase -1 (Strategic Validation):** +2-3 days
  - T-NEG-001: Validate multi-language search demand
  - T-NEG-002: Audit existing tree-sitter implementations
  - T-NEG-003: ROI analysis - CDS optimization vs. tree-sitter
- **Phase 0 (Pre-Implementation):** +0.5 days (new tasks T-000.0, T-000.4)
- **Phase 1 (Proof of Concept):** +0 days (simplified benchmarking, token measurement, integration stub)
- **Phase 2 (Minimal Backend):** +0.5 days (security, error handling, LMDB configuration)
- **Phase 3 (Advanced Features):** +1 day (removed T-008, added T-010.5, T-013.5, T-013.6)
- **Phase 4 (Documentation & Rollout):** +0.5 days (language support matrix, user-facing metrics)
