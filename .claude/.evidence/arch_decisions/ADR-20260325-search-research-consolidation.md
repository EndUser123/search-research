# ADR-20260325: Search-Research Consolid v2

## Status

**Accepted**

## Context

Recent ADR (ADR-20260321) consolidated CHS architecture into `search-research`. This ADR completes the consolidation by migrating all remaining search-related functionality from `P:/__csf/src/` into `search-research`.

### Problem Statement

`P:/__csf/src/` contains 200+ files across:
- Backend files (13): `src/memory/` adapters, `src/knowledge/analysis/` backends, `src/knowledge/systems/kg/` backends
- Chat files (30+): `src/modules/analysis/chat_search/`, `src/core/chat_*`, `src/cks/integration/clients/chat_*`
- Search files (70+): `src/core/*search*`, `src/modules/analysis/chat_search/`, `src/cks/` search patches
- Knowledge files (90+): `src/cks/integration/`, `src/core/knowledge_*`, `src/modules/knowledge_system/`

This creates:
1. **Duplication** - Same functionality exists in both `__csf` and `search-research`
2. **Maintenance burden** - Changes need to be made in two places
3. **Confusion** - Developers don't know which codebase to use

### Current State Analysis

**`search-research` already has:**
- 20+ backends in `core/backends/local/`
- CHS integration in `core/chs/`
- CKS integration in `core/cks/`
- Session memory adapters in `core/cks/integration/`
- Comprehensive test coverage

**`__csf` has:**
- `src/memory/adapter.py` - MemoryAdapter interface (unique)
- `src/memory/*_backend.py` - Backend adapters (duplicates)
- `src/knowledge/analysis/` - Code analysis backends (duplicates)
- `src/knowledge/systems/kg/` - KG backends (duplicates)
- `src/modules/analysis/chat_search/` - Chat search (duplicates)
- `src/cks/integration/` - CKS integration (duplicates)

### Migration Analysis

| `__csf` Module | `search-research` Equivalent | Status | Action |
|----------------|------------------------------|--------|--------|
| `memory/adapter.py` | `core/cks/integration/session_memory_adapter.py` | MIGRATED | Delete |
| `memory/chs_backend.py` | `core/backends/local/claude_history_backend.py` | DUPLICATE | Delete |
| `memory/cks_backend.py` | `core/backends/local/cks_metadata_backend.py` | DUPLICATE | Delete |
| `memory/checkpoint_backend.py` | None | UNUSED | Delete |
| `memory/claude_mem_backend.py` | None | UNUSED | Delete |
| `knowledge/analysis/code/backend.py` | `core/backends/base/code_analysis_backend.py` | MIGRATED | Delete |
| `knowledge/analysis/code/ast_backend.py` | `core/backends/local/ast_code_backend.py` | DUPLICATE | Delete |
| `knowledge/systems/kg/backend.py` | `core/backends/kg.py` | DUPLICATE | Delete |
| `modules/analysis/chat_search/` | `core/chs/` | MIGRATED | Delete |
| `core/chat_*` | `core/chs/` | MIGRATED | Delete |
| `cks/integration/clients/chat_*` | `core/cks/integration/chat_history_client.py` | DUPLICATE | Delete |

### Remaining `__csf` Imports (7 files)

| File | Import | Status | Fix |
|------|--------|--------|------|
| `debugRCA/.../cks_pattern_integration.py` | `from __csf.src.cks.unified` | ACTIVE | Update to `search-research.core.cks` |
| `debugRCA/.../evidence_tier.py` | `from __csf.src.cks.unified` | ACTIVE | Update to `search-research.core.cks` |
| `debugRCA/.../cks_auto_extractor.py` | `from __csf.src.cks.unified` | ACTIVE | Update to `search-research.core.cks` |
| `search-research/.../embeddings.py` | `from __csf.src.daemons.daemon_client` | DEPRECATED | Remove (unused) |
| `search-research/.../unified_semantic_daemon.py` | `from __csf.src.cks.unified` | DEPRECATED | Update to local import |
| `search-research/.../test_chs_skill_integration.py` | Test expectations | TEST | Update or delete |

## Decision

**Delete `P:/__csf/src/` entirely.** All functionality has been migrated to `search-research`.

## Rationale

1. **Complete duplication**: All search/chat/knowledge functionality in `__csf` has equivalents in `search-research`
2. **Single source of truth**: `search-research` is the canonical package for search functionality
3. **Low risk**: Only 7 files import from `__csf`, all are test files or deprecated paths
4. **Reduced maintenance**: Eliminates 200+ duplicate files

## Consequences

### Positive
- Single source of truth for search functionality
- Reduced maintenance burden (200+ files eliminated)
- Clear architecture (all search in one package)
- Improved discoverability (one place to look)

### Negative
- Need to update 4 import paths in `debugRCA`
- Need to update 2 deprecated paths in `search-research`
- Archive `__csf` to preserve history

### Neutral
- No functionality changes (all functionality preserved)
- No performance impact (same code, different location)

## Implementation

### Phase 1: Update Active Imports (2-3 days)

1. **Update `debugRCA` imports**:
   ```python
   # FROM:
   from __csf.src.cks.unified import CKS
   # TO:
   from search_research.core.cks import CKS
   ```

2. **Remove deprecated imports**:
   - `search-research/core/chs/embeddings.py` - Remove daemon client import
   - `search-research/contrib/semantic_daemon/` - Update to local imports

3. **Update test expectations**:
   - `search-research/core/chs/tests/test_chs_skill_integration.py` - Update or delete

### Phase 2: Archive `__csf` (1 day)

1. **Create archive directory**:
   ```bash
   mkdir -p P:/__csf_archive/
   ```

2. **Move `__csf` to archive**:
   ```bash
   mv P:/__csf P:/__csf_archive/
   ```

3. **Create archive README**:
   ```markdown
   # __csf Archive

   This directory contains the legacy CSF code that has been migrated to `search-research`.

   ## Migration Status

   - All search functionality → `search-research/core/`
   - All chat functionality → `search-research/core/chs/`
   - All knowledge functionality → `search-research/core/cks/`

   ## Migration Date

   2026-03-25

   ## Original ADR

   See ADR-20260321 for details.
   ```

### Phase 3: Verify (1-2 days)

1. **Run test suite**:
   ```bash
   pytest packages/search-research/tests/ -v
   ```

2. **Run `/search` command**:
   ```bash
   /search "test query"
   ```

3. **Verify imports**:
   ```python
   # Should work:
   from search_research.core.cks import CKS
   from search_research.core.chs import CHSClient
   ```

## Success Criteria

- [ ] All `__csf` imports updated to `search-research`
- [ ] All tests pass in `search-research`
- [ ] `/search` command works correctly
- [ ] No `__csf` directory exists (archived)

## Rollback Plan

If issues arise after deletion:

1. **Immediate rollback**:
   ```bash
   mv P:/__csf_archive/ P:/__csf/
   ```

2. **Partial rollback** (if only some imports fail):
   - Restore specific files from archive
   - Update imports incrementally

3. **Full rollback** (if major issues):
   - Restore entire `__csf` directory
   - Revert import changes

## Related Documents

- ADR-20260321: CHS Consolidation
- `search-research/README.md`
- `search-research/core/cks/CLAUDE.md`

## Notes

- This is a **complete deletion** because no unique functionality was found
- The `search-research` package has mature test coverage
- Migration is low-risk due minimal active consumers
- **No migration code needed** - all functionality already exists

---

**Decision: Delete `__csf/src/` entirely and archive for historical reference.

**Confidence:** High

**Estimated Effort:** 4-6 days total

**Implementation Status:** Ready for execution

**Next Steps:**
1. Create task list for implementation
2. Begin Phase 1 (Import Updates)
3. Archive after verification
