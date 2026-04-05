# Implementation Plan: AST Pattern Matcher & CPG Extensions

**TSK ID:** TSK-251229-QUALITY-ASTCPG
**Date:** 2025-12-29
**Phase:** CWO12 Step 5 - Implementation Planning

---

## Overview

This plan implements AST-based pattern matching and Code Property Graph (CPG) query extensions for the CSF NIP quality analysis system. Total estimated effort: **11 hours**.

---

## Implementation Sequence

### Sprint 1: AST Pattern Matcher Foundation (Days 1-2)

#### Task 1.1: ASTPatternMatcher Core (3 hours)

**File:** `src/quality/analyzers/ast_pattern_matcher.py`

**Implementation Steps:**

1. **Setup and imports** (15 min)
   ```python
   from __future__ import annotations
   from dataclasses import dataclass
   from pathlib import Path
   from typing import Any

   try:
       import tree_sitter as ts
       TREE_SITTER_AVAILABLE = True
   except ImportError:
       TREE_SITTER_AVAILABLE = False

   import ast
   ```

2. **Data classes** (30 min)
   ```python
   @dataclass
   class PatternMatch:
       pattern_type: str
       name: str
       file_path: str
       line: int
       column: int
       end_line: int | None = None
       captured: dict[str, str] | None = None

   @dataclass
   class AntiPattern:
       pattern_type: str
       description: str
       file_path: str
       line: int
       severity: str
       suggestion: str | None = None
   ```

3. **ASTPatternMatcher class** (2 hours)
   ```python
   class ASTPatternMatcher:
       def __init__(self, language: str = "python"):
           self.language = language
           self.backend = "tree-sitter" if TREE_SITTER_AVAILABLE else "ast"
           # Initialize parser based on backend

       def find_pattern(self, code: str, pattern: str) -> list[PatternMatch]:
           # Pattern matching implementation

       def find_anti_patterns(self, code: str) -> list[AntiPattern]:
           # Anti-pattern detection

       def get_symbols(self, code: str) -> list[dict]:
           # Extract functions, classes, imports

       @property
       def is_available(self) -> bool:
           return TREE_SITTER_AVAILABLE or True  # stdlib ast always available
   ```

4. **Tree-sitter backend** (30 min)
   - Load Python grammar
   - Implement query parsing
   - Handle tree traversal

5. **Fallback to stdlib ast** (30 min)
   - Implement same interface using ast module
   - Ensure feature parity for basic patterns

**Acceptance Criteria:**
- [ ] Class exists with all methods
- [ ] Tree-sitter backend works when available
- [ ] Falls back to stdlib ast when tree-sitter unavailable
- [ ] `is_available` returns True in both cases

**Tests:**
```python
# tests/test_analyzers/test_ast_pattern_matcher.py
def test_matcher_init():
    matcher = ASTPatternMatcher()
    assert matcher.is_available

def test_find_functions():
    code = "def foo(): pass"
    matcher = ASTPatternMatcher()
    matches = matcher.find_pattern(code, "(function_definition name: (identifier) @name)")
    assert len(matches) > 0
```

---

#### Task 1.2: Anti-Pattern Detection (1.5 hours)

**Implementation:**

1. **Define anti-pattern queries** (30 min)
   ```python
   ANTI_PATTERNS = {
       "nested_comprehension": {
           "query": "...",
           "severity": "medium",
           "description": "Nested list/dict comprehension"
       },
       "long_function": {
           "threshold": 50,
           "severity": "low",
           "description": "Function exceeds 50 lines"
       },
       # ... more patterns
   }
   ```

2. **Implement detection logic** (1 hour)
   ```python
   def find_anti_patterns(self, code: str) -> list[AntiPattern]:
       results = []
       for pattern_name, config in ANTI_PATTERNS.items():
           matches = self._detect_single_pattern(code, pattern_name, config)
           results.extend(matches)
       return results
   ```

**Acceptance Criteria:**
- [ ] Detects at least 5 anti-patterns
- [ ] Returns severity levels
- [ ] Provides suggestions for fix

---

#### Task 1.3: ASTPatternAnalyzer (BaseAnalyzer wrapper) (1.5 hours)

**File:** `src/quality/analyzers/ast_pattern_analyzer.py`

**Implementation Steps:**

1. **Create class structure** (30 min)
   ```python
   from quality.core.base_analyzer import BaseAnalyzer, AnalyzerResult
   from .ast_pattern_matcher import ASTPatternMatcher

   class ASTPatternAnalyzer(BaseAnalyzer):
       @classmethod
       def tool_name(cls) -> str:
           return "ast-pattern"

       @property
       def file_extensions(self) -> set[str]:
           return {".py"}

       def is_available(self) -> bool:
           return ASTPatternMatcher().is_available
   ```

2. **Implement analyze() method** (1 hour)
   ```python
   def analyze(
       self, targets: list[Path], *, autofix: bool = False, **kwargs
   ) -> AnalyzerResult:
       import time
       start = time.time()

       matcher = ASTPatternMatcher()
       patterns_found = 0
       anti_patterns_found = 0
       files_analyzed = 0

       for target in targets:
           if target.is_file() and target.suffix == ".py":
               code = target.read_text()
               patterns = matcher.find_pattern(code, kwargs.get("pattern", ""))
               anti_patterns = matcher.find_anti_patterns(code)
               patterns_found += len(patterns)
               anti_patterns_found += len(anti_patterns)
               files_analyzed += 1

       duration_ms = (time.time() - start) * 1000

       return AnalyzerResult(
           tool_name=self.tool_name(),
           status="success",
           files_analyzed=files_analyzed,
           issues_found=patterns_found + anti_patterns_found,
           issues_fixed=0,
           duration_ms=duration_ms,
           details={
               "patterns_found": patterns_found,
               "anti_patterns_found": anti_patterns_found
           }
       )
   ```

**Acceptance Criteria:**
- [ ] Implements BaseAnalyzer interface
- [ ] Returns correct AnalyzerResult format
- [ ] Handles missing files gracefully

**Tests:**
```python
# tests/test_analyzers/test_ast_pattern_analyzer.py
def test_analyzer_interface():
    analyzer = ASTPatternAnalyzer()
    assert analyzer.tool_name() == "ast-pattern"
    assert ".py" in analyzer.file_extensions

def test_analyze_returns_result():
    analyzer = ASTPatternAnalyzer()
    result = analyzer.analyze([Path("test.py")])
    assert result.status in ("success", "error")
```

---

#### Task 1.4: Register and Test (2 hours)

1. **Update `__init__.py`** (15 min)
   ```python
   # src/quality/analyzers/__init__.py
   from .ast_pattern_analyzer import ASTPatternAnalyzer

   __all__ = [
       # ... existing
       "ASTPatternAnalyzer",
   ]
   ```

2. **Unit tests** (1 hour)
   - Test pattern extraction
   - Test anti-pattern detection
   - Test fallback behavior

3. **Integration test** (30 min)
   - Test with QualityOrchestrator
   - Verify result aggregation

4. **Benchmark accuracy** (15 min)
   - Run on sample codebase
   - Verify ≥95% accuracy

**Deliverable:** Working AST pattern matcher with 95%+ accuracy

---

### Sprint 2: CPG Extensions (Days 3-4)

#### Task 2.1: Data Flow Query (1.5 hours)

**File:** `src/quality/core/dependency_graph.py` (add method)

**Implementation:**

```python
def find_data_flow(
    self, start_var: str, max_depth: int = 10
) -> list[DataFlowPath]:
    """
    Trace data flow from variable definition to all uses.

    Args:
        start_var: Variable name to trace
        max_depth: Maximum traversal depth

    Returns:
        List of data flow paths
    """
    from dataclasses import dataclass

    @dataclass
    class DataFlowPath:
        start_var: str
        start_location: tuple[str, int]
        steps: list[tuple[str, int]]
        end_location: tuple[str, int]
        confidence: float

    paths = []

    # Find the symbol
    for symbol in self.symbols.values():
        if symbol.name == start_var:
            # Find all uses
            for edge in self.edges:
                if edge.kind == EdgeKind.USES and edge.target == symbol.qualified_name():
                    # Build path
                    path = DataFlowPath(
                        start_var=start_var,
                        start_location=(symbol.file_path, symbol.line),
                        steps=[],
                        end_location=(edge.file_path, edge.line),
                        confidence=edge.confidence
                    )
                    paths.append(path)

    return paths
```

**Acceptance Criteria:**
- [ ] Returns list of paths
- [ ] Each path has start, steps, end, confidence
- [ ] Respects max_depth parameter

---

#### Task 2.2: Cycle Detection (1 hour)

**File:** `src/quality/core/dependency_graph.py` (add method)

**Implementation:**

```python
def detect_cycles(self) -> list[list[str]]:
    """
    Detect circular import dependencies.

    Returns:
        List of cycles, where each cycle is a list of module names
    """
    import networkx as nx

    # Build import graph from _imports index
    G = nx.DiGraph()
    for file_path, imports in self._imports.items():
        module = self._file_to_module(file_path)
        for imp in imports:
            G.add_edge(module, imp)

    # Find cycles
    cycles = list(nx.simple_cycles(G))

    return cycles
```

**Acceptance Criteria:**
- [ ] Detects direct cycles (A→B→A)
- [ ] Detects indirect cycles (A→B→C→A)
- [ ] Performance: <100ms for 1000 files

---

#### Task 2.3: Enhanced Unused Code Detection (1.5 hours)

**File:** `src/quality/core/dependency_graph.py` (extend existing)

**Implementation:**

```python
def get_unused_symbols(self) -> list[Symbol]:
    """
    Find symbols that are never called/used using transitive closure.

    Returns:
        List of Symbol objects that are safe to remove
    """
    unused = []

    for symbol in self.symbols.values():
        # Skip exported symbols
        if symbol.is_exported:
            continue

        # Skip symbols with specific decorators
        if self._has_keeping_decorator(symbol):
            continue

        # Check if called (with transitive closure)
        if not self.is_called(symbol):
            unused.append(symbol)

    return unused

def _has_keeping_decorator(self, symbol: Symbol) -> bool:
    """Check if symbol has a decorator that marks it as used."""
    keeping_decorators = {
        "app.route", "click.command", "pytest.fixture",
        "property", "staticmethod", "classmethod"
    }
    return any(d in keeping_decorators for d in symbol.decorators)
```

**Acceptance Criteria:**
- [ ] Respects is_exported flag
- [ ] Respects keeping decorators
- [ ] Uses existing is_called() with transitive closure

---

#### Task 2.4: CPG Tests (1 hour)

**File:** `src/quality/tests/test_core/test_dependency_graph_cpg.py`

**Implementation:**

```python
import pytest
from quality.core.dependency_graph import DependencyGraph, DependencyEdge, EdgeKind, Symbol, SymbolKind

def test_find_data_flow():
    graph = DependencyGraph()
    # Add test symbols and edges
    # ...
    paths = graph.find_data_flow("test_var")
    assert isinstance(paths, list)

def test_detect_cycles():
    graph = DependencyGraph()
    # Add circular imports
    # ...
    cycles = graph.detect_cycles()
    assert len(cycles) > 0

def test_get_unused_symbols():
    graph = DependencyGraph()
    # Add unused symbol
    # ...
    unused = graph.get_unused_symbols()
    assert len(unused) > 0
```

**Deliverable:** CPG queries working with test coverage ≥80%

---

### Sprint 3: Integration and Documentation (Days 5-6)

#### Task 3.1: Orchestrator Integration (1 hour)

**Implementation:**

1. **Update configuration** (30 min)
   ```python
   # src/quality/core/config.py
   @dataclass
   class QualityConfig:
       # ... existing
       use_ast_patterns: bool = True
   ```

2. **Wire up to existing analyzers** (30 min)
   - DeadCodeAnalyzer: use `get_unused_symbols()`
   - DuplicateCodeAnalyzer: can query `find_data_flow()`

**Acceptance Criteria:**
- [ ] AST analyzer can be enabled/disabled via config
- [ ] Existing analyzers use CPG queries when available

---

#### Task 3.2: Documentation (1 hour)

**Files to update:**

1. **README** (15 min)
   - Add AST pattern matching section
   - Document tree-sitter installation

2. **API docs** (15 min)
   - Document ASTPatternMatcher API
   - Document CPG query methods

3. **Examples** (30 min)
   ```python
   # examples/ast_pattern_matching.py
   from quality.analyzers import ASTPatternAnalyzer

   analyzer = ASTPatternAnalyzer()
   result = analyzer.analyze(["src/"])
   print(f"Found {result.details['patterns_found']} patterns")
   ```

---

#### Task 3.3: End-to-End Testing (1 hour)

**Implementation:**

1. **Integration test** (30 min)
   ```python
   # tests/integration/test_ast_quality_integration.py
   def test_full_quality_workflow_with_ast():
       orchestrator = QualityOrchestrator()
       result = orchestrator.analyze(["src/quality/"])
       assert result.all_success
       assert "ast-pattern" in result.analyzer_results
   ```

2. **Benchmark** (30 min)
   - Run on 1000-file project
   - Verify performance targets
   - Document results

**Deliverable:** Fully integrated feature with documentation

---

## Testing Strategy

### Unit Tests

```bash
# AST Pattern Matcher
pytest src/quality/tests/test_analyzers/test_ast_pattern_matcher.py -v

# AST Pattern Analyzer
pytest src/quality/tests/test_analyzers/test_ast_pattern_analyzer.py -v

# CPG Extensions
pytest src/quality/tests/test_core/test_dependency_graph_cpg.py -v
```

### Integration Tests

```bash
# Full quality workflow
pytest src/quality/tests/integration/ -v

# With AST enabled
QUALITY_USE_AST=1 pytest src/quality/tests/integration/ -v
```

### Accuracy Tests

```python
# Benchmark: 95%+ accuracy target
def test_pattern_detection_accuracy():
    test_cases = load_accuracy_test_suite()
    correct = 0
    total = len(test_cases)

    for case in test_cases:
        matcher = ASTPatternMatcher()
        result = matcher.find_pattern(case.code, case.pattern)
        if len(result) == case.expected_matches:
            correct += 1

    accuracy = correct / total
    assert accuracy >= 0.95, f"Accuracy {accuracy:.2%} below 95% threshold"
```

---

## Success Criteria

| Criterion | Target | Measure |
|-----------|--------|---------|
| Pattern detection accuracy | ≥95% | Test suite pass rate |
| CPG query performance | <1s | Benchmark timing |
| Code coverage | ≥80% | pytest-cov |
| Zero breaking changes | 100% | Existing tests pass |
| Documentation complete | 100% | All APIs documented |

---

## Rollout Plan

1. **Alpha:** Internal testing (after Sprint 1)
2. **Beta:** Feature flag release (after Sprint 2)
3. **GA:** Full release (after Sprint 3)

---

## Risk Mitigation

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Tree-sitter compilation fails | Medium | High | Fallback to stdlib ast, pre-built wheels |
| Memory exhaustion | Low | High | Node limits, chunked processing |
| Breaking changes to DependencyGraph | Low | High | Strict API compatibility, comprehensive tests |
| Performance regression | Low | Medium | Benchmark before/after |

---

## Next Steps

1. Review and approve this plan
2. Start Sprint 1: AST Pattern Matcher Foundation
3. Create development branch if needed

---

*End of Implementation Plan*
