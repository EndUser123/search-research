# Architecture Analysis: Discover Module Enhancements

## Current Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      /discover                              │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐      ┌──────────────────────────────┐  │
│  │ ExplorerManager│ ────▶ │   DiscoveryDatabase          │  │
│  │                │      │   (SQLite: discover.db)      │  │
│  └────────┬───────┘      └──────────────────────────────┘  │
│           │                                                    │
│           ├──▶ BaseExplorer (interface)                       │
│           ├──▶ SmartExplorer (auto-optimization)             │
│           ├──▶ IntelligentExplorer (ML-enhanced)             │
│           │                                                    │
│           ├──▶ Hardware Acceleration                         │
│           │   ├── EnhancedTreeSitter                         │
│           │   ├── GPUResourceManager                         │
│           │   └── SymbolIndex (ctags)                        │
│           │                                                    │
│           └──▶ Cache                                         │
│               ├── AnalysisCache                              │
│               └── CacheKeyGenerator                          │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Proposed Enhancements

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Enhanced /discover                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌────────────────┐                                                │
│  │ ExplorerManager│                                               │
│  └───────┬────────┘                                                │
│          │                                                          │
│          ├──▶ NEW: ASTPatternMatcher                              │
│          │        └── tree-sitter pattern matching                 │
│          │                                                          │
│          ├──▶ NEW: CodePropertyGraph                               │
│          │        ├── Nodes (functions, classes, variables)        │
│          │        ├── Edges (calls, defines, uses, data_flow)      │
│          │        └── Queries (unused, cycles, paths)              │
│          │                                                          │
│          ├──▶ NEW: HybridCallGraph                                 │
│          │        ├── Static AST analysis                          │
│          │        ├── Dynamic runtime tracing                      │
│          │        └── Confidence scoring                           │
│          │                                                          │
│          ├──▶ NEW: IncrementalParser                               │
│          │        ├── Tree-sitter incremental parsing              │
│          │        ├── Edit detection                               │
│          │        └── Tree cache                                   │
│          │                                                          │
│          └──▶ EXISTING (unchanged)                                 │
│              ├── SmartExplorer                                     │
│              ├── IntelligentExplorer                               │
│              ├── Hardware Acceleration                             │
│              └── Cache layers                                      │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Component Specifications

### 1. ASTPatternMatcher

**Responsibility:** AST-based structural pattern matching

**Interface:**
```python
class ASTPatternMatcher:
    def __init__(self, language: str) -> None
    def find_pattern(self, code: str, pattern: str) -> list[Match]
    def find_anti_patterns(self, code: str, patterns: list[str]) -> list[Finding]
```

**Dependencies:** tree-sitter

**Integration Point:** Called by ExplorerManager during pattern-based exploration

### 2. CodePropertyGraph

**Responsibility:** Build and query code dependency graphs

**Interface:**
```python
class CodePropertyGraph:
    def __init__(self) -> None
    def add_node(self, node: CodeNode) -> None
    def add_edge(self, edge: CodeEdge) -> None
    def find_data_flow(self, start: str, max_depth: int) -> list[Path]
    def find_unused_code(self) -> list[str]
    def detect_cycles(self) -> list[Cycle]
```

**Dependencies:** NetworkX, tree-sitter

**Integration Point:** Used for dependency exploration and unused code detection

### 3. HybridCallGraph

**Responsibility:** Accurate call graph via static + dynamic analysis

**Interface:**
```python
class HybridCallGraphAnalyzer:
    def __init__(self) -> None
    def analyze_static(self, code: str, file_path: str) -> list[CallSite]
    def analyze_dynamic(self, func: Callable) -> list[CallSite]
    def merge_results(self) -> dict[tuple[str, str], float]
```

**Dependencies:** ast, inspect, sys.settrace

**Integration Point:** Used for call analysis exploration type

### 4. IncrementalParser

**Responsibility:** Efficient re-parsing for watch-mode

**Interface:**
```python
class IncrementalParser:
    def __init__(self, language: str) -> None
    def parse_file(self, file_path: str) -> Tree
    def parse_incremental(self, file_path: str, new_content: bytes) -> Tree
    def query_tree(self, tree: Tree, query: str) -> list[Capture]
```

**Dependencies:** tree-sitter

**Integration Point:** Replaces EnhancedTreeSitter for incremental updates

## Data Flow

```
User Request
     │
     ▼
┌─────────────────┐
│ ExplorerManager │
└────────┬────────┘
         │
         ├──► Is pattern-based?
         │       └──▶ ASTPatternMatcher
         │
         ├──► Is dependency analysis?
         │       └──▶ CodePropertyGraph
         │
         ├──► Is call analysis?
         │       └──▶ HybridCallGraph
         │
         └──► Is watch-mode?
                 └──▶ IncrementalParser
```

## Storage Strategy

| Component | Storage | Retention | Purpose |
|-----------|---------|-----------|---------|
| ASTPatternMatcher | Memory + Cache | Session | Repeated patterns |
| CodePropertyGraph | Memory + Disk (pickle) | 7 days | Large graphs |
| HybridCallGraph | Memory | Session | Call sites |
| IncrementalParser | Memory (LRU) | Session | Parsed trees |

## Integration Points

### With CKS (Cognitive Knowledge System)
```python
# Query CKS for existing patterns before exploration
cks_context = cks.search("code patterns", limit=5)
# Use to guide AST pattern selection
```

### With Quality Module
```python
# CPG results feed into quality analysis
cpg = CodePropertyGraph()
unused = cpg.find_unused_code()
quality_report.add_dead_code_findings(unused)
```

### With TaskMaster
```python
# Exploration results stored as task evidence
db.add_finding(
    session_id=tsk_id,
    tool_name="discover",
    finding_type="pattern",
    description=match.to_dict()
)
```

## Performance Considerations

| Operation | Current | With Enhancement | Speedup |
|-----------|---------|------------------|---------|
| Pattern detection | Regex (60% acc) | AST (95% acc) | 0.5x |
| Dependency analysis | None | CPG | New |
| Call graph | Static only | Hybrid | 1.5x accuracy |
| Re-parsing | Full | Incremental | 10-100x |

## Security Considerations

1. **AST Traversal:** Guard against malicious code with depth limits
2. **Graph Size:** Limit CPG nodes to prevent memory exhaustion
3. **Dynamic Tracing:** Sandbox runtime tracing to prevent code execution

## Testing Strategy

```
Unit Tests
├── test_ast_pattern_matcher.py (pattern detection)
├── test_code_property_graph.py (graph construction)
├── test_hybrid_call_graph.py (static + dynamic)
└── test_incremental_parser.py (incremental updates)

Integration Tests
├── test_explorer_integration.py (all components)
└── test_watch_mode.py (incremental + caching)

Performance Tests
├── test_large_codebase.py (1000+ files)
└── test_cache_hit_rate.py (repeated explorations)
```
