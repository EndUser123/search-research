# Requirements Analysis: AST Pattern Matcher & CPG Extensions

**TSK ID:** TSK-251229-QUALITY-ASTCPG
**Date:** 2025-12-29
**From:** specify.md

---

## Functional Requirements

### FR-001: AST Pattern Matcher Core

**ID:** FR-001
**Priority:** High
**Source:** Specification
**Dependencies:** None

**Description:**
Implement a tree-sitter-based AST pattern matcher that provides 95%+ accuracy for detecting code patterns.

**Acceptance Criteria:**
- [ ] Class `ASTPatternMatcher` exists in `src/quality/analyzers/ast_pattern_matcher.py`
- [ ] Constructor accepts `language: str` parameter (default "python")
- [ ] `find_pattern(code, pattern)` returns list of matches with location (file, line, column)
- [ ] `find_anti_patterns(code)` detects at least 5 common anti-patterns
- [ ] `get_symbols(code)` extracts functions, classes, imports
- [ ] 95%+ accuracy on test suite (verified by pytest)

**Anti-Patterns to Detect:**
1. Nested list/dict comprehensions (>2 levels)
2. Functions longer than 50 lines
3. Classes with more than 10 methods
4. Duplicate import statements
5. Bare except clauses
6. Unused imports

---

### FR-002: BaseAnalyzer Integration

**ID:** FR-002
**Priority:** High
**Source:** Specification
**Dependencies:** FR-001

**Description:**
Create `ASTPatternAnalyzer` that wraps `ASTPatternMatcher` and implements the `BaseAnalyzer` interface.

**Acceptance Criteria:**
- [ ] Class `ASTPatternAnalyzer` implements `BaseAnalyzer`
- [ ] `tool_name()` returns "ast-pattern"
- [ ] `file_extensions` returns `{".py"}`
- [ ] `is_available()` returns False if tree-sitter not installed, True otherwise
- [ ] `analyze(targets, **kwargs)` returns `AnalyzerResult`
- [ ] Result includes: files_analyzed, patterns_found, anti_patterns_found
- [ ] Analyzer registered in `src/quality/analyzers/__init__.py`

---

### FR-003: CPG Data Flow Queries

**ID:** FR-003
**Priority:** High
**Source:** Specification
**Dependencies:** None (extends existing code)

**Description:**
Add `find_data_flow()` method to `DependencyGraph` for tracing variable usage across files.

**Acceptance Criteria:**
- [ ] Method `find_data_flow(start_var: str, max_depth: int = 10)` added to `DependencyGraph`
- [ ] Returns list of data flow paths from definition to all uses
- [ ] Each path includes: start location, intermediate steps, end location
- [ ] Respects `max_depth` parameter (limits traversal)
- [ ] Handles cross-file variable tracking
- [ ] Returns empty list if variable not found

---

### FR-004: Enhanced Cycle Detection

**ID:** FR-004
**Priority:** Medium
**Source:** Specification
**Dependencies:** None (extends existing code)

**Description:**
Add `detect_cycles()` method to `DependencyGraph` for identifying circular import dependencies.

**Acceptance Criteria:**
- [ ] Method `detect_cycles()` added to `DependencyGraph`
- [ ] Returns list of cycles (each cycle is a list of module names)
- [ ] Detects both direct cycles (A→B→A) and indirect cycles (A→B→C→A)
- [ ] Reports cycle length and involved modules
- [ ] Performance: <100ms for 1000-file project

---

### FR-005: Enhanced Unused Code Detection

**ID:** FR-005
**Priority:** Medium
**Source:** Specification
**Dependencies:** FR-003

**Description:**
Add `get_unused_symbols()` method to `DependencyGraph` using transitive closure for accuracy.

**Acceptance Criteria:**
- [ ] Method `get_unused_symbols()` added to `DependencyGraph`
- [ ] Returns list of `Symbol` objects that are never called/used
- [ ] Uses transitive closure to detect indirect usage
- [ ] Excludes symbols with specific decorators (e.g., `@app.route`)
- [ ] Respects `is_exported` flag (exported symbols not flagged as unused)
- [ ] Performance: <500ms for 1000-file project

---

### FR-006: Quality Orchestrator Integration

**ID:** FR-006
**Priority:** Medium
**Source:** Specification
**Dependencies:** FR-002

**Description:**
Integrate AST pattern analyzer into the quality orchestration system.

**Acceptance Criteria:**
- [ ] `ASTPatternAnalyzer` importable from `quality.analyzers`
- [ ] Configuration option `use_ast_patterns` added
- [ ] Orchestrator can conditionally enable/disable AST analyzer
- [ ] CPG query methods accessible to other analyzers
- [ ] Existing analyzers continue working without AST features

---

## Non-Functional Requirements

### NFR-001: Performance

**ID:** NFR-001
**Priority:** High

**Requirements:**
- AST parsing: <10ms per 100-line file
- Pattern matching: <5ms per query
- Data flow query: <1s for depth=10
- Cycle detection: <100ms for 1000-file project
- Memory usage: <100MB for 1000-file project

### NFR-002: Accuracy

**ID:** NFR-002
**Priority:** High

**Requirements:**
- Pattern detection: ≥95% accuracy
- False positive rate: <5%
- False negative rate: <5%
- Measured via comprehensive test suite

### NFR-003: Compatibility

**ID:** NFR-003
**Priority:** High

**Requirements:**
- Python 3.11+ compatibility
- Works on Windows (primary dev environment)
- Backward compatible with existing quality analyzers
- No breaking changes to DependencyGraph public API

### NFR-004: Reliability

**ID:** NFR-004
**Priority:** Medium

**Requirements:**
- Graceful degradation if tree-sitter unavailable
- No crashes on malformed Python code
- Clear error messages for configuration errors

### NFR-005: Testability

**ID:** NFR-005
**Priority:** High

**Requirements:**
- ≥80% code coverage
- All new code has unit tests
- Integration tests for cross-file scenarios
- BDD tests for user-facing features

---

## Technical Constraints

### TC-001: Tree-sitter Dependency

Tree-sitter libraries must be installed but analysis must continue if unavailable:
- If tree-sitter not installed: `ASTPatternAnalyzer.is_available()` returns False
- Existing analyzers must continue working
- Clear error message if user explicitly enables AST without tree-sitter

### TC-002: Memory Limits

CPG construction can consume significant memory:
- Implement node limit for large projects
- Provide option to analyze subset of files
- Monitor memory usage and warn when approaching limits

### TC-003: API Stability

`DependencyGraph` is used by multiple analyzers:
- New methods must be additive (no breaking changes)
- Existing method signatures unchanged
- Default behavior preserved

---

## Data Requirements

### DR-001: PatternMatch Format

```python
@dataclass
class PatternMatch:
    """A single pattern match result."""
    pattern_type: str      # e.g., "function", "class", "import"
    name: str              # Symbol name
    file_path: str         # Absolute path to file
    line: int              # Start line (1-indexed)
    column: int            # Start column (0-indexed)
    end_line: int | None   # End line if multi-line
    captured: dict[str, str]  # Named captures from query
```

### DR-002: AntiPattern Format

```python
@dataclass
class AntiPattern:
    """An anti-pattern detected in code."""
    pattern_type: str      # e.g., "nested-comprehension", "long-function"
    description: str       # Human-readable description
    file_path: str
    line: int
    severity: str          # "low", "medium", "high"
    suggestion: str | None # Suggested fix (optional)
```

### DR-003: DataFlowPath Format

```python
@dataclass
class DataFlowPath:
    """A data flow path from definition to use."""
    start_var: str
    start_location: tuple[str, int]  # (file, line)
    steps: list[tuple[str, int]]     # Intermediate locations
    end_location: tuple[str, int]    # Final use location
    confidence: float                 # 0-1, lower for inferred paths
```

---

## User Stories

### US-001: Developer Wants Accurate Dead Code Detection

**As a** developer
**I want** accurate dead code detection that doesn't flag exported functions
**So that** I can safely remove unused code without breaking my library

**Acceptance:** `get_unused_symbols()` respects `is_exported` flag

### US-002: Quality Engineer Wants Pattern-Based Search

**As a** quality engineer
**I want** to search for all functions with specific decorators
**So that** I can analyze patterns across the codebase

**Acceptance:** `find_pattern()` supports custom tree-sitter queries

### US-003: Developer Wants to Find Circular Dependencies

**As a** developer
**I want** to detect circular import dependencies
**So that** I can refactor to avoid import-time side effects

**Acceptance:** `detect_cycles()` returns all cycles with module paths

---

## Traceability Matrix

| Requirement | From Specification | Task ID |
|-------------|-------------------|---------|
| FR-001 | AST Pattern Matcher Implementation | task_20251229_220327_018088_1 |
| FR-002 | BaseAnalyzer Integration | task_20251229_220327_018088_1 |
| FR-003 | CPG Data Flow Queries | task_20251229_220327_018379_2 |
| FR-004 | Enhanced Cycle Detection | task_20251229_220327_018379_2 |
| FR-005 | Enhanced Unused Code Detection | task_20251229_220327_018379_2 |
| FR-006 | Quality Orchestrator Integration | task_20251229_220327_018088_1 |

---

## Risks and Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tree-sitter compilation fails on Windows | Medium | High | Provide pre-built wheels, fallback to AST module |
| Memory exhaustion on large projects | Low | High | Implement node limits, chunked processing |
| Breaking changes to DependencyGraph | Low | High | Strict API compatibility, comprehensive tests |
| Performance degradation | Low | Medium | Benchmark before/after, optimize hot paths |

---

## Dependencies

**External Dependencies:**
- `tree-sitter` ≥0.20.0
- `tree-sitter-python` ≥0.20.0
- `networkx` (already used by DependencyGraph)

**Internal Dependencies:**
- `src/quality/core/base_analyzer.py` - BaseAnalyzer interface
- `src/quality/core/dependency_graph.py` - Existing graph
- `src/quality/core/ast_utils.py` - AST utilities (may reuse)

---

*End of Requirements*
