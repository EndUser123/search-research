# Research: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Step**: 3

## Key Findings

### 1. ast-grep Pattern Syntax Issue

**Problem**: ast-grep has two different pattern syntaxes:
- **YAML Rule Files**: Use `$VAR`, `$$ARGS`, `!` for negation (complex patterns)
- **CLI -p Flag**: Uses simple string patterns (limited syntax)

**Example**:
```yaml
# YAML Rule File (works)
pattern: |
  try:
    $BODY
  except:
    $HANDLER
```

```bash
# CLI -p flag (ERROR node detected)
ast-grep run -l python -p "try: $BODY except: $HANDLER"
# Warning: Pattern contains an ERROR node

# Correct CLI pattern
ast-grep run -l python -p "except:"
# Works: finds bare except clauses
```

**Resolution**: Convert all patterns to simple CLI-compatible syntax.

### 2. CodeIntelligenceExplorer Architecture

**Location**: `P:/__csf.nip/src/code_intelligence/integration/discover_integration.py`

**Components**:
- `CodeIntelligenceExplorer` class (lines 53-127)
- `check_tool_health()` function (lines 130-174)
- `format_tool_health()` function (lines 177-213)
- `get_tool_summary()` function (lines 216-249)

**Tool Registration**: `register_code_intelligence_tools()` supports `with_health=True` parameter.

### 3. explorer_spec.py Integration Points

**Target Class**: `HardwareAcceleratedExplorer`

**Integration Strategy**:
1. Import CodeIntelligenceExplorer with graceful fallback
2. Add `code_intelligence_explorer` instance variable
3. Initialize in `_initialize_components()` method

**Location**: Lines 59-66, 202, 297-312 of explorer_spec.py

## Pattern Testing Results

### Before Fix
```
=== SEARCHING FOR PATTERNS ===
Patterns with matches: 0
Total matches: 0
```

### After Fix
```
=== TESTING FIXED AST-GREP PATTERNS ===
bare_except pattern found: 2 matches
  - test_bare_except.py:4
  - test_bare_except.py:10
```

## References

- ast-grep Documentation: https://ast-grep.github.io/
- Code Intelligence Integration: `P:/__csf.nip/src/code_intelligence/integration/`
- explorer_spec.py: `P:/__csf.nip/src/modules/discover/explorer_spec.py`

## Recommendations

1. **Keep Patterns Simple**: Complex patterns (multi-line with constraints) require YAML rule files
2. **CLI for Common Cases**: Simple patterns like `except:`, `exec(` work well with CLI
3. **Test Patterns**: Always test patterns against known test code before relying on results
