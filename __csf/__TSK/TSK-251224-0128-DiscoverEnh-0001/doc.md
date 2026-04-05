# Documentation: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Step**: 11 (Documentation)

## User Documentation

### Enhanced /discover Command

The `/discover` command now includes integrated code intelligence tools for more powerful code exploration.

#### Available Tools

1. **LSP (Language Server Protocol)**
   - Provides code intelligence features like goto-definition, find-references
   - Supports multiple languages via language servers

2. **AST-GREP (Pattern-Based Search)**
   - Search code using AST patterns
   - Find code quality issues automatically
   - Supports Python, TypeScript, JavaScript, Go, Rust

3. **GRAPH (Code Graph Database)**
   - Traverse code relationships
   - Find dependencies and call graphs
   - Uses tree-sitter for parsing

4. **CROSS-REPO (Multi-Repository Search)**
   - Search across multiple repositories
   - Find patterns and usages globally

#### Usage

```bash
# Basic discovery (uses all available tools)
/discover "async function patterns" --project-path P:/__csf.nip/src

# Pattern-based code search
/discover "bare except clauses" --type pattern --pattern "except:"

# Graph database query
/discover "entities related to authentication" --type graph

# Cross-repository search
/discover "UserAuth class" --type cross-repo
```

#### Health Check

Check tool availability:
```bash
python -c "
from code_intelligence.integration import check_tool_health, format_tool_health
health = check_tool_health()
print(format_tool_health(health))
"
```

Expected output:
```
Code Intelligence Tool Health
==================================================
[✓] LSP - AVAILABLE
[✓] AST-GREP - AVAILABLE (24 Python, 15 TypeScript, 15 JavaScript patterns)
[✓] GRAPH - AVAILABLE (353 entities, 124 relations)
[✓] CROSS-REPO - AVAILABLE (0 indexed repos)
```

## Developer Documentation

### Architecture

See `arch.md` for detailed architecture documentation.

### Integration Points

#### Adding CodeIntelligenceExplorer to Your Code

```python
from code_intelligence.integration import CodeIntelligenceExplorer

# Create explorer with config
config = {
    "project_path": "/path/to/project",
    "enable_lsp": True,
    "enable_ast_grep": True,
    "enable_graph": True,
    "enable_cross_repo": True
}

explorer = CodeIntelligenceExplorer(config)

# Explore query
results = await explorer.explore(
    query="async function patterns",
    options={"max_results": 10}
)
```

#### Using AST-GREP Patterns

```python
from code_intelligence.ast_grep import ASTGrepClient

client = ASTGrepClient()

# Search for specific pattern
results = client.search_pattern(
    pattern_id="bare_except",
    language="python",
    path="/path/to/code"
)

# Search all patterns
all_results = client.search_all_patterns(
    language="python",
    path="/path/to/code"
)
```

### Pattern Library

Patterns are defined in `src/code_intelligence/ast_grep/client.py` in the `PatternLibrary` class.

#### Pattern Format

```python
"pattern_name": {
    "pattern": "cli-compatible-pattern",  # Simple string pattern
    "severity": Severity.ERROR,           # ERROR, WARNING, INFO
    "message": "Human-readable message",
    "fix": "Suggested fix (optional)"
}
```

#### Adding New Patterns

```python
# In PatternLibrary.PYTHON_PATTERNS
"my_custom_pattern": {
    "pattern": "my_pattern($)",           # Use $ for wildcard
    "severity": Severity.WARNING,
    "message": "Description of issue",
    "fix": "my_pattern_fixed($)"
}
```

### API Reference

#### CodeIntelligenceExplorer

**File**: `src/code_intelligence/integration/discover_integration.py`

**Methods**:
- `explore(query, options)`: Main exploration method
- `_lsp_search(query, path)`: LSP-based search
- `_pattern_search(query, path)`: AST pattern search
- `_graph_search(query, options)`: Graph database search
- `_cross_repo_search(query)`: Cross-repository search

#### ASTGrepClient

**File**: `src/code_intelligence/ast_grep/client.py`

**Methods**:
- `search_pattern(pattern_id, language, path)`: Search specific pattern
- `search_all_patterns(language, path)`: Search all patterns
- `check_available()`: Check if ast-grep CLI is available

## Troubleshooting

### Issue: Tools Not Available

**Symptom**: Health check shows tools as unavailable

**Solutions**:
1. Ensure ast-grep CLI is installed: `ast-grep --version`
2. Ensure tree-sitter parsers are installed
3. Check Python environment has required packages

### Issue: Pattern Returns No Matches

**Symptom**: Expected matches but got 0 results

**Solutions**:
1. Verify pattern syntax is CLI-compatible (not YAML rule syntax)
2. Test pattern manually: `ast-grep run -l python -p "pattern" path`
3. Check that code actually contains the pattern

### Issue: Import Error

**Symptom**: `ImportError: No module named 'code_intelligence'`

**Solutions**:
1. Ensure you're running from `P:/__csf.nip` directory
2. Add `src` to Python path: `export PYTHONPATH=$PYTHONPATH:P:/__csf.nip/src`

## Examples

### Example 1: Find Bare Except Clauses

```bash
# Using /discover
/discover "bare except clauses" --type pattern --pattern "except:"

# Using Python directly
python -c "
from code_intelligence.ast_grep import ASTGrepClient
client = ASTGrepClient()
results = client.search_pattern('bare_except', 'python', 'src')
for r in results:
    print(f'{r[\"file\"]}:{r[\"line\"]} - {r[\"text\"][:50]}')
"
```

### Example 2: Check Tool Health

```bash
python -c "
from code_intelligence.integration import check_tool_health, format_tool_health
health = check_tool_health()
print(format_tool_health(health))
"
```

### Example 3: Explore with Code Intelligence

```python
from code_intelligence.integration import CodeIntelligenceExplorer
import asyncio

async def main():
    explorer = CodeIntelligenceExplorer({
        "project_path": "P:/__csf.nip/src",
        "enable_lsp": True,
        "enable_ast_grep": True,
        "enable_graph": True,
        "enable_cross_repo": True
    })

    results = await explorer.explore(
        query="authentication system",
        options={"max_results": 20}
    )

    print(f"Found {len(results.get('findings', []))} findings")

asyncio.run(main())
```

## See Also

- **Architecture**: See `arch.md` for detailed system architecture
- **Implementation**: See `implementation_summary.md` for code changes
- **Quality Gate**: See `qual-gate.md` for validation results
- **Research**: See `research.md` for technical findings

---

**Document Version**: 1.0
**Last Updated**: 2025-12-24
**Author**: CWO12 Workflow
