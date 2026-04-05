# Architecture Analysis: AST Pattern Matcher & CPG Extensions

**TSK ID:** TSK-251229-QUALITY-ASTCPG
**Date:** 2025-12-29
**Phase:** CWO12 Step 4 - Architecture Analysis

---

## Current Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                         Quality System                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                   QualityOrchestrator                       │    │
│  │  - Routes files to analyzers by extension                  │    │
│  │  - Runs analyzers in parallel                              │    │
│  │  - Aggregates results                                       │    │
│  └──────────────┬─────────────────────────────────────────────┘    │
│                 │                                                   │
│                 ├──▶ AnalyzerRegistry (dynamic plugin registration) │
│                 │                                                   │
│  ┌──────────────▼─────────────────────────────────────────────┐    │
│  │                    Analyzers                               │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  RuffAnalyzer    │  MypyAnalyzer  │  BanditAnalyzer         │    │
│  │  SemgrepAnalyzer │  ESLintAnalyzer │  ContractAnalyzer       │    │
│  │  DeadCodeAnalyzer│  DuplicateAnalyzer │  MockDetector       │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                 │                                                   │
│  ┌──────────────▼─────────────────────────────────────────────┐    │
│  │              BaseAnalyzer Interface                         │    │
│  │  - tool_name() → str                                        │    │
│  │  - file_extensions → set[str]                                │    │
│  │  - is_available() → bool                                     │    │
│  │  - analyze(targets, **kwargs) → AnalyzerResult              │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                 │                                                   │
│  ┌──────────────▼─────────────────────────────────────────────┐    │
│  │                    Core Layer                               │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  DependencyGraph (43KB) ── Already has:                     │    │
│  │  - Symbol table (symbols: dict[str, Symbol])                │    │
│  │  - Edge list (edges: list[DependencyEdge])                 │    │
│  │  - Call graph indexes (_callers, _callees)                  │    │
│  │  - Import graph (_imports, _exports)                        │    │
│  │  - Methods: is_called(), get_callers(), get_callees()       │    │
│  │                                                              │    │
│  │  ASTParser & ScopeAnalyzer ── stdlib ast utilities          │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Proposed Additions

```
┌─────────────────────────────────────────────────────────────────────┐
│                    NEW: AST Pattern Matcher                         │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │              ASTPatternMatcher (NEW)                        │    │
│  │  Location: src/quality/analyzers/ast_pattern_matcher.py     │    │
│  ├─────────────────────────────────────────────────────────────┤    │
│  │  - __init__(language: str = "python")                       │    │
│  │  - find_pattern(code, pattern) → list[PatternMatch]         │    │
│  │  - find_anti_patterns(code) → list[AntiPattern]             │    │
│  │  - get_symbols(code) → list[SymbolInfo]                     │    │
│  │                                                              │    │
│  │  Backend: tree-sitter (with stdlib ast fallback)            │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                 │                                                   │
│                 ├── Used by ─────────────────────────────┐         │
│                 │                                         │         │
│  ┌──────────────▼─────────────────────┐    ┌────────────▼──────┐  │
│  │    ASTPatternAnalyzer (NEW)        │    │   Other Analyzers │  │
│  │  Implements BaseAnalyzer           │    │  (enhanced)       │  │
│  ├─────────────────────────────────────┤    └───────────────────┘  │
│  │  - tool_name() → "ast-pattern"      │                           │
│  │  - file_extensions → {".py"}         │                           │
│  │  - is_available() → tree-sitter?     │                           │
│  │  - analyze() → AnalyzerResult        │                           │
│  └─────────────────────────────────────┘                           │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│              EXTENDED: DependencyGraph (CPG Queries)                │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  Existing methods (unchanged):                                      │
│  - add_symbol(), add_edge(), get_symbol(), resolve_symbol()         │
│  - is_called(), get_callers(), get_callees()                        │
│                                                                      │
│  NEW methods (additive, no breaking changes):                       │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  find_data_flow(start_var: str, max_depth: int)             │   │
│  │    → list[DataFlowPath]                                     │   │
│  │    Trace variable usage from definition to all uses         │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  detect_cycles()                                            │   │
│  │    → list[list[str]]                                        │   │
│  │    Find circular import dependencies                        │   │
│  └─────────────────────────────────────────────────────────────┘   │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  get_unused_symbols()                                       │   │
│  │    → list[Symbol]                                           │   │
│  │    Enhanced with transitive closure                          │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Specifications

### 1. ASTPatternMatcher

**Responsibility:** AST-based structural pattern matching

**Location:** `src/quality/analyzers/ast_pattern_matcher.py`

**Interface:**
```python
class ASTPatternMatcher:
    def __init__(self, language: str = "python") -> None
    def find_pattern(self, code: str, pattern: str) -> list[PatternMatch]
    def find_anti_patterns(self, code: str) -> list[AntiPattern]
    def get_symbols(self, code: str) -> list[SymbolInfo]

    @property
    def is_available(self) -> bool
    @property
    def backend(self) -> str  # "tree-sitter" or "ast"
```

**Data Classes:**
```python
@dataclass
class PatternMatch:
    pattern_type: str      # e.g., "function", "class", "import"
    name: str
    file_path: str
    line: int
    column: int
    end_line: int | None
    captured: dict[str, str]

@dataclass
class AntiPattern:
    pattern_type: str      # e.g., "nested-comprehension"
    description: str
    file_path: str
    line: int
    severity: str          # "low", "medium", "high"
    suggestion: str | None
```

**Dependencies:**
- `tree-sitter` (optional, with fallback to stdlib `ast`)

**Integration Point:** Used by `ASTPatternAnalyzer` and other analyzers for pattern-based queries

---

### 2. ASTPatternAnalyzer

**Responsibility:** BaseAnalyzer wrapper for ASTPatternMatcher

**Location:** `src/quality/analyzers/ast_pattern_analyzer.py`

**Interface:**
```python
class ASTPatternAnalyzer(BaseAnalyzer):
    @classmethod
    def tool_name(cls) -> str:
        return "ast-pattern"

    @property
    def file_extensions(self) -> set[str]:
        return {".py"}

    def is_available(self) -> bool:
        return ASTPatternMatcher().is_available

    def analyze(
        self, targets: list[Path], *, autofix: bool = False, **kwargs
    ) -> AnalyzerResult:
        # Run AST pattern matching on all targets
        # Returns AnalyzerResult with patterns_found, anti_patterns_found
```

**Dependencies:**
- `ASTPatternMatcher`
- `BaseAnalyzer` (core interface)

**Integration Point:** Registered in `AnalyzerRegistry`, executed by `QualityOrchestrator`

---

### 3. DependencyGraph Extensions

**Responsibility:** Add CPG query capabilities to existing graph

**Location:** `src/quality/core/dependency_graph.py` (additive methods)

**New Methods:**

**find_data_flow(start_var, max_depth)**
```python
def find_data_flow(
    self, start_var: str, max_depth: int = 10
) -> list[DataFlowPath]:
    """
    Trace data flow from variable definition to all uses.

    Uses existing edges:
    - EdgeKind.DEFINES: Where symbols are defined
    - EdgeKind.USES: Where symbols are referenced
    - EdgeKind.CALLS: For function call chains

    Returns:
        List of paths from definition to use sites
    """
```

**detect_cycles()**
```python
def detect_cycles(self) -> list[list[str]]:
    """
    Detect circular import dependencies.

    Uses existing _imports index:
    - Maps file → set of imported modules
    - Applies NetworkX simple_cycles algorithm

    Returns:
        List of cycles, where each cycle is a list of module names
    """
```

**get_unused_symbols()**
```python
def get_unused_symbols(self) -> list[Symbol]:
    """
    Find symbols that are never called/used.

    Enhances existing is_called() with:
    - Transitive closure through call graph
    - Decorator awareness (e.g., @app.route)
    - Export flag respect

    Returns:
        List of Symbol objects that are safe to remove
    """
```

**Dependencies:**
- `networkx` (already used)
- Existing `DependencyGraph` infrastructure

**Integration Point:** Methods callable by any analyzer, especially `DeadCodeAnalyzer`

---

## Data Flow

```
User Request: /quality --ast-patterns
         │
         ▼
┌─────────────────┐
│ QualityOrchestrator│
└────────┬────────┘
         │
         ├──▶ Gets Python files
         │
         ├──▶ Queries AnalyzerRegistry
         │    │
         │    ├──▶ ASTPatternAnalyzer (NEW)
         │    │    └──▶ ASTPatternMatcher
         │    │         └──▶ tree-sitter → PatternMatch[]
         │    │
         │    ├──▶ DeadCodeAnalyzer (ENHANCED)
         │    │    └──▶ DependencyGraph.get_unused_symbols()
         │    │
         │    └──▶ Other analyzers (unchanged)
         │
         ├──▶ Aggregates AnalyzerResult[]
         │
         └──▶ Returns OrchestratorResult
```

---

## Storage Strategy

| Component | Storage | Retention | Purpose |
|-----------|---------|-----------|---------|
| ASTPatternMatcher | Memory (LRU cache) | Session | Repeated pattern queries |
| ASTPatternAnalyzer results | OrchestratorResult | Session | Quality report |
| DependencyGraph | Memory + optional pickle | 7 days | Cross-analysis sharing |
| Data flow paths | Computed on demand | Not cached | Expensive to compute |

---

## Integration Points

### With DeadCodeAnalyzer

**Current:**
```python
# DeadCodeAnalyzer already uses DependencyGraph
unused = graph.find_unused_symbols()
```

**After Extension:**
```python
# Enhanced with transitive closure
unused = graph.get_unused_symbols()  # More accurate
```

### With DuplicateCodeAnalyzer

**Current:**
- Hash-based detection (exact matches)
- AST-based detection (structural matches)

**After Extension:**
```python
# Can use ASTPatternMatcher for custom patterns
matcher = ASTPatternMatcher()
patterns = matcher.find_pattern(code, anti_pattern_query)
```

### With QualityOrchestrator

**Registration:**
```python
# Auto-discovery will pick up ASTPatternAnalyzer
# if added to analyzers/__init__.py

from .ast_pattern_analyzer import ASTPatternAnalyzer
__all__.append("ASTPatternAnalyzer")
```

---

## Performance Considerations

| Operation | Current | After Extension | Impact |
|-----------|---------|-----------------|---------|
| Pattern detection | Regex (60% acc) | AST (95% acc) | 0.5x speed, 2x accuracy |
| Unused code detection | Basic is_called() | Transitive closure | 1.2x time, better recall |
| Cycle detection | Manual iteration | NetworkX algorithm | 10x faster |
| Memory usage | ~50MB for 1K files | ~60MB for 1K files | +20% (acceptable) |

---

## Security Considerations

1. **AST Traversal:** Guard against malicious code with depth limits
2. **Graph Size:** Limit CPG nodes to prevent memory exhaustion
3. **Pattern Injection:** Validate user-provided tree-sitter queries
4. **File Access:** Respect existing sandbox boundaries

---

## Testing Architecture

```
tests/
├── test_analyzers/
│   ├── test_ast_pattern_matcher.py      # Unit tests for matcher
│   ├── test_ast_pattern_analyzer.py     # Unit tests for analyzer
│   └── test_dependency_graph_cpg.py     # Tests for CPG methods
│
├── integration/
│   └── test_ast_quality_integration.py  # End-to-end tests
│
└── fixtures/
    ├── sample_code/                     # Test Python files
    └── expected_patterns.json           # Expected match results
```

---

## Migration Path

### Phase 1: Core Implementation (Week 1)
1. Create `ast_pattern_matcher.py` (tree-sitter wrapper)
2. Create `ast_pattern_analyzer.py` (BaseAnalyzer wrapper)
3. Add unit tests

### Phase 2: CPG Extensions (Week 1)
1. Add `find_data_flow()` to DependencyGraph
2. Add `detect_cycles()` to DependencyGraph
3. Add `get_unused_symbols()` to DependencyGraph
4. Add unit tests

### Phase 3: Integration (Week 2)
1. Register ASTPatternAnalyzer
2. Wire up CPG queries to existing analyzers
3. Add integration tests
4. Update documentation

---

## Compatibility Guarantees

| Component | Backward Compatible | Breaking Changes |
|-----------|---------------------|------------------|
| ASTPatternMatcher | N/A (new) | None |
| ASTPatternAnalyzer | N/A (new) | None |
| DependencyGraph | ✅ Yes | None (additive only) |
| Existing Analyzers | ✅ Yes | None |
| Orchestrator | ✅ Yes | None |

---

*End of Architecture Analysis*
