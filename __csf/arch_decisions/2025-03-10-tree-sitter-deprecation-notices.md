# Tree-Sitter Deprecation Notices

**Date**: 2026-03-10
**Status**: Active
**Related Tasks**: #1523, #1524

## Overview

Following the consolidation of tree-sitter code into `src/search/backends/tree_sitter_utils.py`, the following modules contain duplicate tree-sitter implementations that should be migrated to use `tree_sitter_utils`.

## Deprecated Direct Imports

The following modules directly use `tree_sitter.Language()` constructor with PyCapsule wrapping:

### High Priority (Actively Used)

1. **src/modules/discover/ast_pattern_matcher.py**
   - **Usage**: Used by code_property_graph, explorer, static_call_graph, quality analyzers
   - **Issue**: Direct `Language(ptr)` construction (line ~50)
   - **Migration**: Use `TreeSitterParser` from `search.backends.tree_sitter_utils`

2. **src/modules/discover/code_property_graph.py**
   - **Usage**: Core CPG builder, used by explorer, cpg_storage, cached_cpg_builder
   - **Issue**: Direct `Language(lang_capsule)` wrapping (line ~60)
   - **Migration**: Use `LanguageRegistry` and `TreeSitterParser` from `tree_sitter_utils`

3. **src/modules/discover/incremental_parser.py**
   - **Usage**: Incremental parsing for large codebases
   - **Issue**: Direct `Language(ptr)` construction (line ~45)
   - **Migration**: Use `TreeSitterParser` from `tree_sitter_utils`

4. **src/modules/discover/hardware_accelerated/tree_sitter_enhanced.py**
   - **Usage**: GPU-accelerated tree-sitter operations
   - **Issue**: Direct tree-sitter Language/Parser usage
   - **Migration**: Use `TreeSitterParser` from `tree_sitter_utils`

5. **src/quality/analyzers/ast_pattern_matcher.py**
   - **Usage**: AST pattern matching for quality analysis
   - **Issue**: Direct `Language(tsp.language())` construction (line ~85)
   - **Migration**: Use `TreeSitterParser` from `tree_sitter_utils`

### Low Priority (Standalone Tools)

6. **src/commands/rca/tree_sitter_integration.py**
   - **Usage**: RCA tool for syntax analysis
   - **Issue**: Direct `Language()` imports without language loading
   - **Migration**: Use `TreeSitterParser` from `tree_sitter_utils`

## Migration Pattern

### Before (Deprecated):
```python
from tree_sitter import Language, Parser
import tree_sitter_python

# Direct PyCapsule wrapping
lang_capsule = tree_sitter_python.language()
lang = Language(lang_capsule)
parser = Parser()
parser.language = lang
```

### After (Recommended):
```python
from search.backends.tree_sitter_utils import TreeSitterParser

# Use consolidated parser
parser = TreeSitterParser('python')
# Access language object via parser
lang = parser.parser.language
```

## Benefits of Migration

1. **Single source of truth** for language loading
2. **Python 3.14+ PyCapsule compatibility** handled centrally
3. **LanguageRegistry** for consistent file extension → language mapping
4. **Reduced code duplication** across the codebase
5. **Easier maintenance** - bug fixes apply to all consumers

## Migration Plan

### Phase 1: Add Deprecation Warnings ✅
- [x] Document deprecated modules
- [x] Add deprecation notices to code (inline comments)
- [ ] Add `warnings.warn()` deprecation warnings

### Phase 2: Refactor High-Priority Modules
- [ ] Migrate `ast_pattern_matcher.py`
- [ ] Migrate `code_property_graph.py`
- [ ] Migrate `incremental_parser.py`
- [ ] Migrate `tree_sitter_enhanced.py`
- [ ] Migrate `quality/analyzers/ast_pattern_matcher.py`

### Phase 3: Refactor Low-Priority Modules
- [ ] Migrate `rca/tree_sitter_integration.py`

### Phase 4: Verification
- [ ] Run test suites for discover modules
- [ ] Verify explorer functionality
- [ ] Verify CPG building
- [ ] Verify quality analyzers

## Implementation Notes

### Breaking Changes
None - this is deprecation only. Existing code continues to work.

### Timeline
- **Phase 1**: Complete (2026-03-10)
- **Phase 2**: Future work (can be done incrementally)
- **Phase 3**: Future work (low priority)
- **Phase 4**: After Phase 2-3 complete

## References

- Task #1522: multilang_backend.py integration (completed)
- Task #1523: refactor_orchestrator integration (completed)
- Task #1524: Deprecation notices (this task)
- `src/search/backends/tree_sitter_utils.py`: Consolidated implementation
- `src/search/CLAUDE.md`: Search module documentation
