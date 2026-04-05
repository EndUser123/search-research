# Architecture: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Step**: 5 (Architecture)

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    /discover Command                        │
│                                                             │
│  ┌──────────────────────────────────────────────────────┐  │
│  │     HardwareAcceleratedExplorer (explorer_spec.py)  │  │
│  │                                                      │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │  CodeIntelligenceExplorer (NEW INTEGRATION)    │ │  │
│  │  │                                                │ │  │
│  │  │  • LSP Client                                  │ │  │
│  │  │  • AST-GREP Client (FIXED)                     │ │  │
│  │  │  • Graph Database Client                       │ │  │
│  │  │  • Cross-Repo Search                           │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  │                      ↓                              │  │
│  │  ┌────────────────────────────────────────────────┐ │  │
│  │  │         CKS Pre-Query Enhanced                 │ │  │
│  │  └────────────────────────────────────────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

```
User Query → HardwareAcceleratedExplorer
                    ↓
    CodeIntelligenceExplorer.explore(query)
                    ↓
    ┌───────────────┼───────────────┐
    ↓               ↓               ↓
LSP Search    AST-GREP      Graph Search
              Pattern
              Search
    └───────────────┼───────────────┘
                    ↓
        CKS Pre-Query (context)
                    ↓
        Unified Results → User
```

## Module Interactions

### 1. CodeIntelligenceExplorer

**File**: `src/code_intelligence/integration/discover_integration.py`

**Key Methods**:
- `explore(query, options)`: Main exploration entry point
- `_lsp_search(query, path)`: LSP-based code search
- `_pattern_search(query, path)`: AST pattern matching
- `_graph_search(query, options)`: Graph database traversal
- `_cross_repo_search(query)`: Multi-repository search

### 2. AST-GREP Client

**File**: `src/code_intelligence/ast_grep/client.py`

**Key Changes**:
- PatternLibrary class (lines 99-440) - converted to CLI syntax
- `search_all_patterns()` method - runs all ERROR/WARNING patterns
- `search_pattern()` method - runs specific pattern with CLI

**Pattern Format**:
```python
"pattern_name": {
    "pattern": "simple-cli-pattern",  # e.g., "except:", "exec("
    "severity": Severity.ERROR,
    "message": "Human-readable message",
    "fix": "Suggested fix (optional)"
}
```

### 3. explorer_spec.py Integration

**File**: `src/modules/discover/explorer_spec.py`

**Integration Points**:

**Lines 59-66**: Import with fallback
```python
try:
    from code_intelligence.integration import CodeIntelligenceExplorer
    CODE_INTEL_AVAILABLE = True
except ImportError as e:
    CODE_INTEL_AVAILABLE = False
    CodeIntelligenceExplorer = None
```

**Line 202**: Instance variable
```python
self.code_intelligence_explorer = None
```

**Lines 297-312**: Initialization
```python
if CODE_INTEL_AVAILABLE and CodeIntelligenceExplorer:
    code_intel_config = {
        "project_path": str(csf_nip_root),
        "enable_lsp": True,
        "enable_ast_grep": True,
        "enable_graph": True,
        "enable_cross_repo": True
    }
    self.code_intelligence_explorer = CodeIntelligenceExplorer(code_intel_config)
```

## Error Handling

### Graceful Degradation

1. **Import Fails**: Set `CODE_INTEL_AVAILABLE = False`, continue without code intelligence
2. **Pattern Fails**: Log warning, continue with other tools
3. **Tool Unavailable**: Report as unavailable in health check, don't crash

### Health Check

Run `check_tool_health()` to verify:
- LSP: Language servers available
- AST-GREP: CLI available + patterns loaded
- GRAPH: tree-sitter available + entities indexed
- CROSS-REPO: Repository index ready

## Performance Considerations

| Operation | Expected Time | Notes |
|-----------|---------------|-------|
| LSP Search | 100-500ms | Per file |
| AST-GREP Pattern | < 1s | Simple patterns |
| Graph Search | 200ms-2s | Depends on query |
| Full Discovery | 5-30s | All tools combined |
