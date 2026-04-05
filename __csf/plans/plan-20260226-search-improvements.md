# Implementation Plan: CSF NIP Search System Key Improvements

**Created:** 2026-02-26
**Status:** READY-FOR-REVIEW
**Priority:** HIGH

---

## Objective Summary

Fix the four high-priority improvement areas in the CSF NIP search system: (1) Complete migration from deprecated `src/search/` to authoritative `knowledge/search/` location, (2) Verify and document LSP backend availability, (3) Verify and document HNSW backend availability, (4) Create centralized documentation for all conditional backends with clear dependency requirements.

---

## 1. Problem Statement

### Current Issues

1. **Location Duplication**: Search system exists in two locations with ~22,000-23,000 lines each. The `src/search/` location is deprecated but still contains code, creating confusion about which location is authoritative.

2. **LSP/HNSW Integration Status**: Documentation claims LSP and HNSW backends are "complete but not integrated", but investigation reveals they ARE already integrated in the unified router (lines 1022-1028). The actual issue is missing dependencies and outdated documentation.

3. **Conditional Backend Documentation**: Backend availability flags and dependencies are scattered across multiple files (CLAUDE.md, STATUS.md, unified_router.py) with no centralized reference for:
   - Which backends require external dependencies
   - How to install missing dependencies (e.g., `pip install hnswlib`)
   - How to enable conditionally available backends

### Impact

- **Developer Confusion**: Unclear which search location to use, leading to imports from deprecated code
- **Underutilized Features**: LSP and HNSW backends are functional but not used due to missing dependencies
- **Onboarding Friction**: New developers lack clear guidance on enabling optional search capabilities

---

## 2. Context Analysis

### Documentation Discovery (Phase 0 Sources Consulted)

**Sources Reviewed:**
- `P:\__csf\src\search\__init__.py` (lines 9-14) - Deprecation warning
- `P:\__csf\src\knowledge\search\router.py` (lines 92-212) - Backend availability flags
- `P:\__csf\src\search\unified_router.py` (lines 1022-1028) - LSP/HNSW integration
- `P:\__csf\src\search\backends\lsp_backend.py` - LSP backend implementation
- `P:\__csf\src\search\backends\hnsw_backend.py` - HNSW backend implementation
- `P:\__csf\src\search\STATUS.md` - System status documentation
- `P:\__csf\src\search\CLAUDE.md` - Module architecture documentation
- `.claude/arch_reviews/2026-02-16-search-cds-integration.md` - Integration review

### Allowed APIs (Verified to Exist)

**Router APIs:**
- `EnhancedUnifiedSearchRouter` class (knowledge/search/router.py)
- `_get_backend_map()` method for backend registration
- `BACKEND_LSP = "LSP"` constant
- `BACKEND_HNSW = "HNSW"` constant

**Backend Classes:**
- `LSPSymbolBackend` (search/backends/lsp_backend.py)
- `HNSWVectorBackend` and `HNSWTextSearchBackend` (search/backends/hnsw_backend.py)

**Availability Flags:**
- `LSP_BACKEND_AVAILABLE` - set if `code_intelligence.lsp.client` imports successfully
- `HNSW_BACKEND_AVAILABLE` and `HAS_HNSW` - set if `hnswlib` package is installed
- `SEARCH_USE_MULTILANG=1` - environment variable to enable Tree-sitter backend

### Anti-patterns to Avoid

- **Do NOT import from `src.search`** - Use `knowledge.search` instead (deprecation warning in place)
- **Do NOT assume backends are "not integrated"** - Check unified_router.py for actual integration status
- **Do NOT invent integration code** - Backends use try/except conditional imports pattern
- **Do NOT modify backend_map directly** - Use the existing conditional import pattern

### System Architecture

```
Authoritative: P:\__csf\src\knowledge\search\
├── router.py (EnhancedUnifiedSearchRouter)
├── backends/
│   ├── _config.py (backend constants)
│   └── [backend implementations]
├── vector/, hybrid/, expansion/ (newer modules)
└── CLAUDE.md, STATUS.md

Deprecated: P:\__csf\src\search\
├── unified_router.py (DEPRECATED - use knowledge.search.router)
├── backends/
│   ├── lsp_backend.py (LSPSymbolBackend)
│   └── hnsw_backend.py (HNSWVectorBackend)
└── __init__.py (contains deprecation warning)
```

---

## 3. Existing Implementation Discovery

### Current State

#### 3.1 Location Duplication

| Aspect | `src/search/` | `knowledge/search/` | Status |
|--------|--------------|---------------------|--------|
| **Lines of Code** | 22,517 | 23,204 | Knowledge search larger |
| **Deprecation Status** | **DEPRECATED** (line 9-14 of __init__.py) | **ACTIVE** | Clear migration direction |
| **Unique Features** | temporal_boosting.py | vector/, hybrid/, expansion/ | Knowledge has newer modules |
| **Current Imports** | Mixed usage (some still use it) | Primary import target | Migration incomplete |

**Authoritative Source:** `P:\__csf\src\knowledge\search\` is confirmed authoritative based on:
1. Explicit deprecation warning in `src/search/__init__.py`
2. Modern import patterns in CLI files use `knowledge.search.router`
3. Active development (newer features: vector/, hybrid/, expansion/)

#### 3.2 LSP Backend Integration

**Status:** ✅ ALREADY INTEGRATED (contrary to outdated documentation)

**Integration Location:** `P:\__csf\src\search\unified_router.py` lines 1022-1024

```python
# Actual integration code (already exists)
lsp_backend = None
if LSP_BACKEND_AVAILABLE:
    from .backends.lsp_backend import LSPSymbolBackend
    lsp_backend = LSPSymbolBackend()
    backend_map[BACKEND_LSP] = lsp_backend
```

**Availability Check:**
```python
LSP_BACKEND_AVAILABLE = False
try:
    from code_intelligence.lsp.client import Language, LSPClientManager
    LSP_BACKEND_AVAILABLE = True
except ImportError:
    pass
```

**Why It Appears "Not Integrated":**
- LSP backend requires `code_intelligence.lsp.client` module
- If module is unavailable, `LSP_BACKEND_AVAILABLE = False` and backend is skipped
- No error is raised - graceful degradation

#### 3.3 HNSW Backend Integration

**Status:** ✅ ALREADY INTEGRATED (contrary to outdated documentation)

**Integration Location:** `P:\__csf\src\search\unified_router.py` lines 1026-1028

```python
# Actual integration code (already exists)
hnsw_backend = None
if HNSW_BACKEND_AVAILABLE:
    from .backends.hnsw_backend import HNSWTextSearchBackend
    hnsw_backend = HNSWTextSearchBackend()
    backend_map[BACKEND_HNSW] = hnsw_backend
```

**Availability Check:**
```python
from .hnsw_index import HAS_HNSW  # Checks hnswlib package
HNSW_BACKEND_AVAILABLE = HAS_HNSW
```

**Why It Appears "Not Integrated":**
- HNSW backend requires `hnswlib` pip package
- If package is not installed, `HAS_HNSW = False` and backend is skipped
- No installation instructions in documentation

#### 3.4 Conditional Backend Documentation

**Current State:** Scattered across multiple files

| Documentation Location | Content |
|------------------------|---------|
| `src/search/CLAUDE.md` | Architecture overview, backend mapping |
| `src/search/STATUS.md` | System status, backend availability |
| `src/knowledge/search/CLAUDE.md` | Knowledge search documentation |
| `unified_router.py` (lines 92-212) | Availability flags and imports |
| Arch review documents | Integration plans and status |

**Missing:** Single centralized reference for:
- All conditional backends and their dependencies
- Installation commands for missing packages
- Environment variables for enabling features

---

## 4. Test Discovery

### Existing Test Coverage

**Test Files Found:**
- `test_grep_backend.py` - 20 tests, 93% coverage
- `test_cds_backend.py` - 18 tests, 84% coverage
- `test_result_deduplicator.py` - 9 tests, 75% coverage
- `test_kg_backend.py` - 23 tests, ~90% coverage
- **Total:** 70 tests with ~87% coverage

### Test Requirements for This Plan

**New Tests Needed:**
1. **Location migration tests:** Verify imports resolve to `knowledge.search`
2. **LSP backend availability tests:** Test behavior with/without `code_intelligence.lsp.client`
3. **HNSW backend availability tests:** Test behavior with/without `hnswlib`
4. **Documentation completeness tests:** Verify all conditional backends are documented

### Test Scenarios

**Scenario 1: Deprecation Warning Test**
```python
def test_import_from_deprecated_location_warns():
    """Importing from src.search should trigger DeprecationWarning"""
    with warnings.catch_warnings(record=True) as w:
        from src.search import EnhancedUnifiedSearchRouter
        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "knowledge.search" in str(w[0].message)
```

**Scenario 2: LSP Backend Graceful Degradation**
```python
def test_lsp_backend_unavailable_without_dependency():
    """LSP backend should not be in backend_map if dependency missing"""
    # Mock LSP_BACKEND_AVAILABLE = False
    router = EnhancedUnifiedSearchRouter()
    assert "LSP" not in router.backend_map
```

**Scenario 3: HNSW Backend Availability**
```python
def test_hnsw_backend_available_with_hnswlib():
    """HNSW backend should be in backend_map if hnswlib installed"""
    # Only run if hnswlib is installed
    pytest.importorskip("hnswlib")
    router = EnhancedUnifiedSearchRouter()
    assert "HNSW" in router.backend_map
```

---

## 5. Proposed Solution

### Solution Overview

1. **Complete Location Migration**: Remove deprecated `src/search/` location after verifying all imports use `knowledge.search/`

2. **Document LSP/HNSW Integration**: Update documentation to reflect that backends ARE integrated, just gated by dependencies

3. **Create Conditional Backend Guide**: Centralize documentation for all conditional backends with installation instructions

4. **Add Dependency Installation Documentation**: Provide clear pip commands for optional dependencies

### Component Changes

#### 5.1 Complete Migration from `src/search/` to `knowledge/search/`

**Action:** Remove deprecated location after verification

**Steps:**
1. Audit all codebase imports from `src.search`
2. Replace with `knowledge.search` imports
3. Run tests to verify no breakage
4. Delete `src/search/` directory

**Files to Modify:**
- All files importing from `src.search`
- Update import statements: `from src.search.X` → `from knowledge.search.X`

#### 5.2 Update LSP/HNSW Documentation

**Action:** Correct documentation to reflect integration status

**Files to Modify:**
- `P:\__csf\src\knowledge\search\STATUS.md`
- `P:\__csf\src\knowledge\search\CLAUDE.md`
- Any arch review documents with outdated status

**Changes:**
- Remove "not integrated" language
- Document actual status: "Integrated, requires dependencies"
- Add dependency installation instructions

#### 5.3 Create Conditional Backend Guide

**Action:** Create centralized documentation

**New File:** `P:\__csf\src\knowledge\search\BACKEND_GUIDE.md`

**Content Structure:**
```markdown
# Conditional Backend Availability Guide

## Always Available Backends
[List backends with no external dependencies]

## Conditionally Available Backends

### LSP Backend
- **Purpose:** Symbol-aware code search via Language Server Protocol
- **Dependency:** `code_intelligence.lsp.client` module
- **Installation:** [Installation command if applicable]
- **Availability Flag:** `LSP_BACKEND_AVAILABLE`
- **Status:** Integrated, requires dependency

### HNSW Backend
- **Purpose:** Fast approximate nearest neighbor vector search
- **Dependency:** `hnswlib` package
- **Installation:** `pip install hnswlib`
- **Availability Flag:** `HNSW_BACKEND_AVAILABLE`, `HAS_HNSW`
- **Status:** Integrated, requires dependency

[... other backends ...]
```

---

## 6. Implementation Plan

### Phase 1: Discovery and Verification (Effort: M)

**Objective:** Confirm current state and identify all migration points

**Tasks:**
1. **Audit codebase imports** for `from src.search` usage
   - Command: `grep -r "from src.search" --include="*.py" P:/__csf/src/`
   - Document all files that need import updates
   - Acceptance: Complete list of files requiring migration

2. **Verify knowledge/search completeness**
   - Confirm all backends exist in knowledge/search/
   - Verify router.py has all functionality from unified_router.py
   - Acceptance: Feature parity checklist completed

3. **Identify LSP/HNSW dependencies**
   - Locate `code_intelligence.lsp.client` module
   - Confirm `hnswlib` package installation command
   - Acceptance: Dependency installation procedures documented

### Phase 2: Documentation Updates (Effort: S)

**Objective:** Update documentation to reflect accurate integration status

**Tasks:**
1. **Create BACKEND_GUIDE.md** in `P:\__csf\src\knowledge\search\`
   - Document all conditional backends
   - Include installation commands
   - List availability flags
   - Acceptance: Guide covers all 20+ backends with clear dependencies

2. **Update STATUS.md** in `P:\__csf\src\knowledge\search\`
   - Change LSP/HNSW status from "not integrated" to "integrated, requires dependencies"
   - Add links to BACKEND_GUIDE.md
   - Acceptance: Status accurately reflects integration state

3. **Update CLAUDE.md** in `P:\__csf\src\knowledge\search\`
   - Add reference to BACKEND_GUIDE.md
   - Correct any outdated integration claims
   - Acceptance: Documentation cross-references complete

### Phase 3: Import Migration (Effort: L)

**Objective:** Migrate all imports from deprecated `src.search` to `knowledge.search`

**Tasks:**
1. **Update import statements** in all identified files
   - Pattern: `from src.search.X` → `from knowledge.search.X`
   - Preserve all existing functionality
   - Acceptance: Zero imports from `src.search` remain in codebase

2. **Update test files** to use new imports
   - Modify test imports to use `knowledge.search`
   - Run all tests to verify no breakage
   - Acceptance: All 70+ tests pass with new imports

3. **Verify CLI entry points** use correct imports
   - Check `P:/__csf/src/cli/nip/search_enhanced.py`
   - Check other CLI files using search
   - Acceptance: All CLI files use `knowledge.search`

### Phase 4: Cleanup and Removal (Effort: M)

**Objective:** Remove deprecated `src/search/` location

**Tasks:**
1. **Final verification** that no code uses `src.search`
   - Run: `grep -r "from src.search" --include="*.py" P:/__csf/`
   - Expect: No results
   - Acceptance: Grep returns zero matches

2. **Backup deprecated location** (optional safety measure)
   - Create archive: `src-search-backup-YYYYMMDD.tar.gz`
   - Acceptance: Backup created (optional)

3. **Remove deprecated directory**
   - Delete: `P:\__csf\src\search\`
   - Acceptance: Directory no longer exists

4. **Update any cross-references** to deleted files
   - Update documentation referencing `src/search/` paths
   - Update arch review documents
   - Acceptance: No broken references to deleted paths

### Phase 5: Testing and Validation (Effort: M)

**Objective:** Verify system works correctly after migration

**Tasks:**
1. **Run existing test suite**
   - Command: `pytest P:/__csf/src/knowledge/search/tests/`
   - Expect: All 70+ tests pass
   - Acceptance: 100% test pass rate

2. **Test LSP backend availability** (if dependency available)
   - Test graceful degradation when dependency missing
   - Test functionality when dependency present
   - Acceptance: Backend behaves correctly in both cases

3. **Test HNSW backend availability** (if dependency available)
   - Test graceful degradation when dependency missing
   - Test functionality when dependency present
   - Acceptance: Backend behaves correctly in both cases

4. **Manual CLI testing**
   - Run: `python P:/__csf/src/cli/nip/search_enhanced.py "test query"`
   - Verify search works with all available backends
   - Acceptance: CLI returns results without errors

---

## 7. Risks, Success Criteria, Dependencies

### Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Hidden imports from src.search** | HIGH (breakage after deletion) | MEDIUM | Comprehensive grep audit before deletion; keep backup |
| **knowledge/search missing features** | HIGH (functionality loss) | LOW | Feature parity verification before migration |
| **LSP/HNSW dependency conflicts** | MEDIUM (backend unavailable) | LOW | Document dependencies clearly; graceful degradation |
| **Test failures after import changes** | MEDIUM (debugging time) | MEDIUM | Run tests after each file modification |
| **Documentation inaccuracies persist** | LOW (ongoing confusion) | MEDIUM | Peer review of BACKEND_GUIDE.md |

### Success Criteria

**Must Have (Blocking):**
- ✅ Zero imports from `src.search` remain in codebase
- ✅ All 70+ existing tests pass after migration
- ✅ `src/search/` directory removed
- ✅ BACKEND_GUIDE.md created with all conditional backends documented

**Should Have (Non-blocking but important):**
- ✅ LSP/HNSW status corrected from "not integrated" to "integrated, requires dependencies"
- ✅ All CLI entry points use `knowledge.search` imports
- ✅ Documentation cross-references complete

**Nice to Have (Future improvements):**
- Dependency installation automation (e.g., `pip install csf-search[optional]`)
- Health check CLI command: `search_enhanced.py --health`
- Performance benchmarks comparing pre/post migration

### Dependencies

**Internal Dependencies:**
- Must complete import audit before any file modifications
- Must verify knowledge/search completeness before deletion
- Test suite must pass before proceeding to next phase

**External Dependencies:**
- None required for core migration
- Optional LSP backend requires: `code_intelligence.lsp.client` module (internal)
- Optional HNSW backend requires: `pip install hnswlib` (external package)

**Critical Path:**
Phase 1 (Discovery) → Phase 2 (Documentation) → Phase 3 (Migration) → Phase 4 (Cleanup) → Phase 5 (Testing)

### Rollback Strategy

**If Migration Fails:**
1. Stop at any phase if blocking issues discovered
2. Restore from backup: `src-search-backup-YYYYMMDD.tar.gz`
3. Revert import changes using git (if committed in stages)
4. Document issues and create new plan

**Rollback Triggers:**
- More than 10% of tests fail after import changes
- Missing features discovered in knowledge/search
- Critical functionality broken with no clear fix

**Rollback Commands:**
```bash
# If backup created
tar -xzf src-search-backup-YYYYMMDD.tar.gz -C P:/__csf/src/

# If using git
git revert <migration-commit-range>
```

---

## Top Risks

1. **HIGH RISK:** Hidden imports from `src.search` discovered after deletion → Mitigation: Comprehensive grep audit + backup
2. **MEDIUM RISK:** knowledge/search missing features from src/search → Mitigation: Feature parity checklist before migration
3. **LOW RISK:** Test failures from import path changes → Mitigation: Incremental testing after each file change

---

## Next Actions

1. **Start Phase 1 - Discovery:**
   ```bash
   # Audit all imports from deprecated location
   grep -r "from src.search" --include="*.py" P:/__csf/src/ > import_audit.txt
   ```

2. **Verify knowledge/search completeness:**
   ```bash
   # Compare backend lists
   ls P:/__csf/src/search/backends/
   ls P:/__csf/src/knowledge/search/backends/
   ```

3. **Review plan with:**
   ```bash
   /plan-workflow review P:\__csf\plans\plan-20260226-search-improvements.md
   ```
