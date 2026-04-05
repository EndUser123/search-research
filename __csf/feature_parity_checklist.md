# Feature Parity Checklist: src/search → knowledge/search Migration

**Created:** 2026-02-26
**Status:** ❌ INCOMPLETE - Missing 4 critical backends

---

## Backend File Comparison

| Backend File | src/search/ | knowledge/search/ | Status |
|--------------|-------------|-------------------|--------|
| `ast_code_backend.py` | ✅ | ✅ | ✅ Complete |
| `call_graph_backend.py` | ✅ | ✅ | ✅ Complete |
| `cds_backend.py` | ✅ | ✅ | ✅ Complete |
| `chs_fts_backend.py` | ✅ | ✅ | ✅ Complete |
| `chs_fts_backend_enhanced.py` | ❌ | ✅ | ✅ **Enhancement in new location** |
| `chs_gpu.py` | ✅ | ✅ | ✅ Complete |
| `chs_incremental.py` | ✅ | ✅ | ✅ Complete |
| `chs_migrate.py` | ✅ | ✅ | ✅ Complete |
| `chs_quantized.py` | ✅ | ✅ | ✅ Complete |
| `chs_tiered.py` | ✅ | ✅ | ✅ Complete |
| `cks_metadata_backend.py` | ✅ | ✅ | ✅ Complete |
| `code_analysis_backend.py` | ✅ | ✅ | ✅ Complete |
| `code_backend.py` | ✅ | ✅ | ✅ Complete |
| `cpg_backend.py` | ✅ | ❌ | ❌ **MISSING** - Code Property Graph |
| `dedup.py` | ✅ | ✅ | ✅ Complete |
| `dependency_backend.py` | ✅ | ❌ | ❌ **MISSING** - Dependency Analysis |
| `fuzzy_matcher.py` | ✅ | ✅ | ✅ Complete |
| `grep_backend.py` | ✅ | ✅ | ✅ Complete |
| `hnsw_backend.py` | ✅ | ✅ | ✅ Complete |
| `hybrid_scorer.py` | ✅ | ✅ | ✅ Complete |
| `kg_backend.py` | ✅ | ✅ | ✅ Complete |
| `lsp_backend.py` | ✅ | ❌ | ❌ **CRITICAL MISSING** - LSP Symbol Search |
| `lsp_protocol.py` | ✅ | ❌ | ❌ **CRITICAL MISSING** - LSP Protocol Support |
| `multilang_backend.py` | ✅ | ✅ | ✅ Complete |
| `persona_memory_backend.py` | ✅ | ✅ | ✅ Complete |
| `rlm_ab_test_framework.py` | ✅ | ✅ | ✅ Complete |
| `rlm_backend.py` | ✅ | ✅ | ✅ Complete |
| `rlm_internet_research_backend.py` | ✅ | ✅ | ✅ Complete |
| `skills_backend.py` | ✅ | ✅ | ✅ Complete |

---

## Router Integration Status

| Feature | src/search/unified_router.py | knowledge/search/router.py | Status |
|---------|----------------------------|---------------------------|--------|
| **HNSW Backend** | ✅ Integrated (conditional) | ✅ Available (line 115) | ✅ Complete |
| **LSP Backend** | ✅ Integrated (lines 112-126) | ❌ Not referenced | ❌ **Missing** |
| **LSP Availability Flag** | `LSP_BACKEND_AVAILABLE` | Not defined | ❌ **Missing** |
| **LSP Backend Constant** | `BACKEND_LSP = "LSP"` | Not defined | ❌ **Missing** |
| **Backend Map Integration** | Line 1024: `all_backends[BACKEND_LSP]` | Not present | ❌ **Missing** |

---

## Critical Blocking Issues

### Issue #1: LSP Backend Missing from Authoritative Location
- **Impact**: High - LSP symbol-aware search will be lost if src/search/ is deleted
- **Files Affected**:
  - `src/search/backends/lsp_backend.py` (not in knowledge/search/)
  - `src/search/backends/lsp_protocol.py` (not in knowledge/search/)
- **Router Changes Needed**:
  - Add LSP conditional import to `knowledge/search/router.py`
  - Add `BACKEND_LSP` constant
  - Add to backend map in `_get_backend_map()`

### Issue #2: CPG Backend Missing
- **Impact**: Medium - Code Property Graph analysis functionality will be lost
- **Files Affected**: `src/search/backends/cpg_backend.py`
- **Action**: Copy to `knowledge/search/backends/`

### Issue #3: Dependency Backend Missing
- **Impact**: Low-Medium - Dependency analysis functionality will be lost
- **Files Affected**: `src/search/backends/dependency_backend.py`
- **Action**: Copy to `knowledge/search/backends/`

---

## Required Actions Before src/search/ Deletion

### Action 1: Copy Missing Backends
```bash
# Copy LSP backends (CRITICAL)
cp P:/__csf/src/search/backends/lsp_backend.py P:/__csf/src/knowledge/search/backends/
cp P:/__csf/src/search/backends/lsp_protocol.py P:/__csf/src/knowledge/search/backends/

# Copy other missing backends
cp P:/__csf/src/search/backends/cpg_backend.py P:/__csf/src/knowledge/search/backends/
cp P:/__csf/src/search/backends/dependency_backend.py P:/__csf/src/knowledge/search/backends/
```

### Action 2: Update knowledge/search/router.py
Add LSP backend integration (similar to deprecated unified_router.py lines 112-126):

```python
# LSP backend import (conditional)
LSP_BACKEND_AVAILABLE = False
BACKEND_LSP = "LSP"

try:
    from code_intelligence.lsp.client import Language, LSPClientManager
    from .backends.lsp_backend import LSPSymbolBackend, BACKEND_LSP_SYMBOL
    BACKEND_LSP = BACKEND_LSP_SYMBOL
    LSP_BACKEND_AVAILABLE = True
except ImportError:
    pass

# In _get_backend_map() method:
if LSP_BACKEND_AVAILABLE:
    from .backends.lsp_backend import LSPSymbolBackend
    backend_map[BACKEND_LSP] = LSPSymbolBackend()
```

### Action 3: Update BACKEND_GUIDE.md Documentation
Document LSP and HNSW conditional availability:
- LSP: Requires `code_intelligence.lsp.client` module
- HNSW: Requires `hnswlib` package (`pip install hnswlib`)

---

## Acceptance Criteria

**Phase 1 cannot be complete until:**
- [ ] All 4 missing backends are copied to knowledge/search/backends/
- [ ] LSP backend is integrated in knowledge/search/router.py
- [ ] HNSW backend availability is verified (already marked available)
- [ ] Feature parity checklist shows 100% completion
- [ ] All imports from the 6 identified files are migrated

---

## Dependencies Identified

### LSP Backend Dependency
- **Module**: `code_intelligence.lsp.client`
- **Required Classes**: `Language`, `LSPClientManager`
- **Import Location**: Internal CSF module
- **Installation**: No pip package needed (internal)

### HNSW Backend Dependency
- **Package**: `hnswlib`
- **Installation Command**: `pip install hnswlib`
- **Purpose**: Fast approximate nearest neighbor vector search
- **Status**: Available in router.py (line 115: `HNSW_BACKEND_AVAILABLE = True`)

---

## Summary

**Status**: ❌ **BLOCKED** - Cannot proceed with Phase 3 (Migration) or Phase 4 (Cleanup) until missing backends are copied and integrated.

**Path Forward**:
1. Complete Action 1: Copy 4 missing backends to knowledge/search/backends/
2. Complete Action 2: Integrate LSP backend in knowledge/search/router.py
3. Re-run feature parity checklist
4. Then proceed with Phase 2: Documentation Updates
5. Then Phase 3: Import Migration (6 files already identified)
