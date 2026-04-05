# Specification: AST Pattern Matcher & CPG Extensions for Quality Analysis

**TSK ID:** TSK-251229-QUALITY-ASTCPG
**Date:** 2025-12-29
**Version:** 1.0

---

## Goal

Implement AST-based pattern matching and Code Property Graph (CPG) query extensions for the CSF NIP quality analysis system, providing 95%+ accuracy for code pattern detection vs 60% for regex-based approaches.

---

## Why

### Business Value
- **Improved Code Quality**: Higher accuracy pattern detection means fewer false positives/negatives in quality reports
- **Reduced Manual Review**: 95%+ AST accuracy reduces time spent investigating false positives
- **Scalability**: Tree-sitter incremental parsing enables efficient analysis of large codebases

### User Impact
- **Developers**: More accurate quality feedback, less noise in reports
- **Quality Engineers**: Better dependency analysis, improved dead code detection
- **System Integrators**: Reliable pattern-based code navigation and refactoring

### Technical Necessity
- Current regex-based pattern matching in quality analyzers achieves only ~60% accuracy
- Static call graph exists (dependency_graph.py) but lacks CPG query capabilities (data flow, unused code paths)
- Anti-pattern detection exists but could benefit from AST-based structural matching

---

## What

### FR-001: AST Pattern Matcher Implementation
Create `ASTPatternMatcher` class with tree-sitter backend for structural code pattern matching.

**Requirements:**
- Support Python AST parsing via tree-sitter
- Pattern detection: functions, classes, imports, decorators, async functions
- Anti-pattern detection: nested-comprehensions, long-functions, duplicate-imports
- 95%+ detection accuracy (measured via test suite)
- Integration with existing `BaseAnalyzer` interface

### FR-002: CPG Query Extensions
Extend existing `DependencyGraph` class with Code Property Graph query capabilities.

**Requirements:**
- `find_data_flow(start_var, max_depth)`: Trace variable usage across files
- Enhanced `find_unused_code()`: Use transitive closure for accurate detection
- `detect_cycles()`: Identify circular dependencies in import graph
- Integration with `ASTPatternMatcher` for semantic node linkage

### FR-003: Quality Analyzer Integration
Integrate new components into existing quality orchestration system.

**Requirements:**
- `ASTPatternAnalyzer` implements `BaseAnalyzer` interface
- Expose CPG queries to existing analyzers (dead_code, duplicate_code)
- Add configuration options to enable/disable AST-based features
- Backward compatibility with existing analyzers

---

## All Needed Context

### Files

**Existing Infrastructure:**
- `src/quality/core/base_analyzer.py` - BaseAnalyzer interface, AnalyzerResult dataclass
- `src/quality/core/dependency_graph.py` - DependencyGraph, Symbol, DependencyEdge classes (45KB)
- `src/quality/analyzers/__init__.py` - Analyzer registry and exports
- `src/quality/analyzers/dead_code_analyzer.py` - Dead code detection using DependencyGraph
- `src/quality/analyzers/duplicate_code_analyzer.py` - Duplicate detection (hash and AST-based)
- `src/quality/core/ast_utils.py` - ASTParser, ScopeAnalyzer utilities

**Tree-sitter Integration Points:**
- Check if tree-sitter is already installed or needs installation
- Tree-sitter Python grammar location

**Test Templates:**
- `src/quality/tests/test_analyzers/` - Analyzer test patterns
- `src/quality/tests/test_enhanced_execution_*.py` - Test structure examples

### APIs

**BaseAnalyzer Interface:**
```python
class BaseAnalyzer(ABC):
    @classmethod
    @abstractmethod
    def tool_name(cls) -> str: ...

    @property
    @abstractmethod
    def file_extensions(self) -> set[str]: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def analyze(self, targets: list[Path], *, autofix: bool = False, **kwargs) -> AnalyzerResult: ...
```

**DependencyGraph Query API:**
```python
class DependencyGraph:
    def add_symbol(self, symbol: Symbol) -> None: ...
    def add_edge(self, edge: DependencyEdge) -> None: ...
    def get_symbol(self, qualified_name: str) -> Symbol | None: ...
    def is_called(self, symbol: Symbol) -> bool: ...
    def get_callers(self, symbol: Symbol) -> list[Symbol]: ...
    def get_callees(self, symbol: Symbol) -> list[Symbol]: ...
```

### Docs

**External References:**
- Tree-sitter documentation: https://tree-sitter.github.io/tree-sitter/
- Tree-sitter Python grammar: https://github.com/tree-sitter/tree-sitter-python
- CPG research: `.speckit/memory/TSK-251229-2116-DiscoverEnhancements/research.md`

**Internal References:**
- Original 68-hour plan: `.speckit/memory/TSK-251229-2116-DiscoverEnhancements/plan.md`
- Architecture doc: `.speckit/memory/TSK-251229-2116-DiscoverEnhancements/arch.md`

### Gotchas

1. **Tree-sitter Installation**: May need compilation; handle gracefully if not available
2. **Memory Usage**: Large codebases may exceed memory limits with full CPG; implement node limits
3. **Circular Dependencies**: Existing dependency_graph.py may have issues with import cycles; verify detect_cycles works
4. **Test Coverage**: DependencyGraph already has good coverage; add tests for new methods only
5. **Backward Compatibility**: Existing analyzers must continue working; AST features should be opt-in

---

## Implementation Blueprint

### 1. ASTPatternMatcher Core Class

**Location:** `src/quality/analyzers/ast_pattern_matcher.py`

**Input:**
- `code: str` - Python source code to analyze
- `pattern: str` - Tree-sitter query pattern

**Output:**
- `list[PatternMatch]` - Match objects with location, type, captured nodes

**Tests:**
- Syntax check: `ruff check ast_pattern_matcher.py`
- Unit test: `pytest tests/test_analyzers/test_ast_pattern_matcher.py`
- Integration: `pytest tests/integration/test_ast_pattern_integration.py`

**Key Methods:**
```python
class ASTPatternMatcher:
    def __init__(self, language: str = "python"):
        # Load tree-sitter language and parser

    def find_pattern(self, code: str, pattern: str) -> list[PatternMatch]:
        # Find all matches of pattern in code

    def find_anti_patterns(self, code: str) -> list[AntiPattern]:
        # Detect common anti-patterns

    def get_symbols(self, code: str) -> list[Symbol]:
        # Extract functions, classes, imports
```

### 2. ASTPatternAnalyzer (BaseAnalyzer wrapper)

**Location:** `src/quality/analyzers/ast_pattern_analyzer.py`

**Input:**
- `targets: list[Path]` - Files to analyze
- `autofix: bool` - Not applicable for AST analysis (read-only)
- `patterns: list[str]` - Optional custom patterns

**Output:**
- `AnalyzerResult` - Standard result format

**Tests:**
- Syntax check: `ruff check ast_pattern_analyzer.py`
- Unit test: `pytest tests/test_analyzers/test_ast_pattern_analyzer.py`
- Integration: Test against sample codebase

**Key Methods:**
```python
class ASTPatternAnalyzer(BaseAnalyzer):
    @classmethod
    def tool_name(cls) -> str:
        return "ast-pattern"

    @property
    def file_extensions(self) -> set[str]:
        return {".py"}

    def is_available(self) -> bool:
        # Check if tree-sitter-python is installed

    def analyze(self, targets, **kwargs) -> AnalyzerResult:
        # Run AST pattern matching on all targets
```

### 3. DependencyGraph CPG Extensions

**Location:** `src/quality/core/dependency_graph.py` (add methods)

**Input:**
- `start_var: str` - Variable name to trace
- `max_depth: int` - Maximum traversal depth

**Output:**
- `list[DataFlowPath]` - Paths showing variable usage

**Tests:**
- Syntax check: `ruff check dependency_graph.py`
- Unit test: Extend existing `test_dependency_graph.py`
- Integration: Test with real codebase

**Key Methods:**
```python
class DependencyGraph:
    def find_data_flow(self, start_var: str, max_depth: int = 10) -> list[DataFlowPath]:
        # Trace data flow from variable definition to all uses

    def detect_cycles(self) -> list[list[str]]:
        # Find circular import dependencies

    def get_unused_symbols(self) -> list[Symbol]:
        # Enhanced unused code detection using transitive closure
```

### 4. Quality Orchestrator Integration

**Location:** `src/quality/orchestration/` (existing)

**Input:** N/A (uses existing configuration)

**Output:** Updated orchestrator with AST analyzer support

**Tests:**
- Run full quality suite with AST enabled
- Verify backward compatibility with AST disabled

**Changes:**
- Add `ASTPatternAnalyzer` to analyzer registry
- Add `use_ast_patterns` config option
- Wire CPG queries to existing analyzers

---

## Validation Loop

### Level 1 (Syntax)
```bash
ruff check src/quality/analyzers/ast_pattern_*.py
ruff check src/quality/core/dependency_graph.py
```

### Level 2 (Unit)
```bash
pytest src/quality/tests/test_analyzers/test_ast_pattern_matcher.py -v
pytest src/quality/tests/test_analyzers/test_ast_pattern_analyzer.py -v
pytest src/quality/tests/test_core/test_dependency_graph_cpg.py -v
```

### Level 3 (Integration)
```bash
# Run full quality suite on test codebase
pytest src/quality/tests/integration/ -v

# End-to-end test
python -m quality.analyzers.ast_pattern_analyzer src/quality/
```

---

## BDD Scenarios

### Scenario 1: Happy Path - Pattern Detection
```
Given Python code with function definitions
When ASTPatternMatcher scans for functions
Then all function names and locations are returned
And accuracy is ≥95% compared to manual count
```

### Scenario 2: Anti-Pattern Detection
```
Given Python code with nested list comprehensions
When ASTPatternMatcher detects anti-patterns
Then nested-comprehension is flagged with line number
And suggested refactoring is provided
```

### Scenario 3: Data Flow Tracing
```
Given variable 'user_data' defined in module A
And used in modules B and C
When find_data_flow('user_data') is called
Then paths A→B and A→C are returned
And all intermediate usage points are included
```

### Scenario 4: Cycle Detection
```
Given modules A imports B imports C imports A
When detect_cycles() is called
Then cycle [A, B, C] is identified
And breaking point is suggested
```

### Scenario 5: Tree-sitter Unavailable
```
Given tree-sitter-python is not installed
When ASTPatternAnalyzer.is_available() is called
Then False is returned
And analyzer gracefully skips analysis
```

---

## Success Criteria

| Criterion | Target | Measure |
|-----------|--------|---------|
| Pattern detection accuracy | ≥95% | Test suite pass rate |
| CPG query performance | <1s | Benchmark timing |
| Code coverage | ≥80% | pytest-cov |
| Integration with /discover | Functional | End-to-end test |
| Zero breaking changes | 100% | Existing tests pass |

---

## Dependencies

**External:**
- `tree-sitter` - Core parsing library
- `tree-sitter-python` - Python grammar

**Internal:**
- `src/quality/core/base_analyzer.py` - BaseAnalyzer interface
- `src/quality/core/dependency_graph.py` - Existing graph implementation
- `src/quality/core/ast_utils.py` - AST utilities (may reuse)

---

## Estimate

| Task | Hours |
|------|-------|
| ASTPatternMatcher implementation | 4 |
| ASTPatternAnalyzer implementation | 2 |
| CPG extensions to DependencyGraph | 2 |
| Tests and integration | 2 |
| Documentation | 1 |
| **Total** | **11** |

*(Note: Previously estimated at 12 hours total across 2 tasks)*

---

*End of Specification*
