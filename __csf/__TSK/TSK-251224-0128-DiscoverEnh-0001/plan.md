# Implementation Plan: Discover Enhancements

**TSK-ID**: TSK-251224-0128-DiscoverEnh-0001
**Step**: 6 (Planning)

## Overview

This document outlines the implementation plan for enhancing the `/discover` command. All core implementation is complete; this plan documents what was done.

## Implementation Status: ✅ COMPLETE

### Phase 1: CodeIntelligenceExplorer Integration

**Status**: ✅ Complete

**Files Modified**:
- `P:/__csf.nip/src/modules/discover/explorer_spec.py`

**Changes Made**:
1. Added import block (lines 59-66)
2. Added instance variable (line 202)
3. Added initialization logic (lines 297-312)

**Testing**:
```python
# Verify import works
from code_intelligence.integration import CodeIntelligenceExplorer

# Verify initialization
explorer = CodeIntelligenceExplorer({
    "project_path": "P:/__csf.nip/src",
    "enable_lsp": True,
    "enable_ast_grep": True,
    "enable_graph": True,
    "enable_cross_repo": True
})
```

### Phase 2: ast-grep Pattern Fixes

**Status**: ✅ Complete

**Files Modified**:
- `P:/__csf.nip/src/code_intelligence/ast_grep/client.py`

**Changes Made**:
- Converted 24 Python patterns to CLI syntax
- Converted 15 TypeScript/JavaScript patterns
- Converted 11 Go patterns
- Converted 9 Rust patterns

**Pattern Conversion Examples**:

| Before (YAML) | After (CLI) |
|---------------|-------------|
| `pattern: "try: $BODY except:"` | `pattern: "except:"` |
| `pattern: "exec($INPUT)"` | `pattern: "exec("` |
| `pattern: "global $VAR"` | `pattern: "global $"` |

**Testing**:
```bash
# Test bare except pattern
ast-grep run -l python -p "except:" --json test_file.py

# Test exec pattern
ast-grep run -l python -p "exec(" --json test_file.py
```

### Phase 3: CWO12 Documentation

**Status**: ✅ In Progress (this document)

**Files Created**:
- TSK directory with full workflow documentation
- This implementation plan
- Requirements analysis
- Architecture documentation

## Validation Checklist

- [x] CodeIntelligenceExplorer imports successfully
- [x] Patterns return matches (tested with `except:`, `exec(`)
- [x] No "ERROR node" warnings for simple patterns
- [x] All 4 tools show as available in health check
- [x] Documentation created in TSK directory

## Rollback Plan

If issues arise:

1. **Revert explorer_spec.py changes**:
   - Remove lines 59-66 (import block)
   - Remove line 202 (instance variable)
   - Remove lines 297-312 (initialization)

2. **Revert ast-grep patterns**:
   - Restore old PatternLibrary from git history
   - File: `src/code_intelligence/ast_grep/client.py`

3. **Test**:
   ```bash
   cd P:/__csf.nip
   git diff src/code_intelligence/ast_grep/client.py
   git checkout -- src/code_intelligence/ast_grep/client.py
   ```

## Future Enhancements

### Potential Improvements

1. **YAML Rule File Support**: Add support for complex patterns via YAML files
2. **Pattern Auto-Testing**: Test all patterns against codebase on startup
3. **Performance Caching**: Cache pattern results for repeated searches
4. **Custom Patterns**: Allow users to define custom patterns

### Not in Scope

- Pattern language translation (CLI ↔ YAML)
- Pattern editor UI
- Pattern recommendation engine
