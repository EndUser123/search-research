# Specification: Discover Module Enhancements

## Goal
Enhance the `/discover` module with AST-based pattern matching, code property graphs, and improved static analysis capabilities.

## Why
- **Technical Necessity:** Current regex-based pattern detection has only ~60% accuracy
- **User Impact:** More accurate code exploration reduces time spent understanding large codebases
- **Code Quality:** Better dead code detection and dependency analysis

## What
FR-001: AST-based pattern matching using tree-sitter
FR-002: Code Property Graph (CPG) for dependency analysis
FR-003: Hybrid static + dynamic call graph analysis
FR-004: Incremental parsing for watch-mode support
FR-005: LSP-MCP bridge for IDE integration

## All Needed Context

### Files
- `__csf.nip/src/modules/discover/explorer_spec.py` - Main explorer implementation
- `__csf.nip/src/modules/discover/discover_database.py` - Storage layer
- `__csf.nip/src/modules/discover/base_explorer.py` - Base explorer interface

### APIs
- `ExplorerManager.explore(config: ExplorationConfig)` - Main exploration entry point
- `DiscoverDatabase.create_session()` - Create exploration sessions
- `DiscoverDatabase.add_finding()` - Store findings

### Docs
- [Tree-sitter Documentation](https://tree-sitter.github.io/)
- [ast-grep Documentation](https://ast-grep.github.io/)
- [NetworkX Documentation](https://networkx.org/) for graph operations

### Gotchas
- Tree-sitter parsers must be compiled before use
- GPU acceleration requires CUDA-compatible hardware
- LSP servers may not be available on all systems

## Implementation Blueprint

### 1. AST Pattern Matcher (ast_pattern_matcher.py)
- Input: Source code, pattern string
- Output: List of match locations with metadata
- Tests: Verify pattern matching on sample Python files

### 2. Code Property Graph (code_property_graph.py)
- Input: List of parsed AST nodes
- Output: NetworkX DiGraph with nodes and edges
- Tests: Verify graph construction, detect cycles, find unused code

### 3. Hybrid Call Graph (hybrid_call_graph.py)
- Input: Python source files
- Output: Call graph with confidence scores
- Tests: Compare static vs dynamic analysis results

## Validation Loop
- **Level 1 (Syntax):** `ruff check --fix ast_pattern_matcher.py`
- **Level 2 (Unit):** `pytest tests/test_discover/`
- **Level 3 (Integration):** Run `/discover` on test codebase

## BDD Scenarios

**Scenario 1: AST Pattern Detection**
```
Given Python source code with function definitions
When searching for pattern "(function_definition name: (identifier) @name)"
Then returns list of all function names with line numbers
```

**Scenario 2: Find Unused Code**
```
Given a codebase with defined functions
When building Code Property Graph
Then identifies functions with zero incoming edges as unused
```

**Scenario 3: Incremental Parsing**
```
Given a previously parsed file
When file is modified with minor changes
Then re-parses only changed regions (not entire file)
```
