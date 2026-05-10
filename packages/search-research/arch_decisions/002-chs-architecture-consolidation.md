# ADR-002: CHS Architecture Consolidation

**Status:** Accepted | **Date:** 2026-03-19 | **Context:** CHS source code fragmentation
**Implementation:** Completed 2026-03-21

---

## Context

Chat History Search (CHS) core system is currently located in `P:\\\\\\__csf/src/knowledge/systems/chs/v2/`, which is infrastructure/data storage territory. However, CHS is an application feature, not infrastructure.

**Current CHS Locations:**

| Component | Location | Type |
|-----------|----------|------|
| CHS v2 Core | `P:\\\\\\__csf/src/knowledge/systems/chs/v2/` | Application code (CLI, DB init, indexer) |
| /chs skill | `P:\\\\\\packages/search-research/skills/chs/` | Skill wrapper |
| CHS backend | `P:\\\\\\packages/search-research/core/backends/local/chs_incremental.py` | Backend implementation |
| Duplicate | `P:\\\\\\packages/search-backends/.../chs_incremental.py` | Duplicate code |
| Data files | `P:\\\\\\__csf/data/` | Database, FAISS index, state |

**Problems:**
1. **Core application code in infrastructure directory** - CHS is a feature, not infrastructure
2. **Duplicate `chs_incremental.py`** - Exists in both `search-research` and `search-backends`
3. **Fragmented ownership** - No single place owns "CHS the feature"
4. **Confusion about where CHS lives** - Developers find code in 3+ different locations

**Root Cause:** CHS was developed as part of `__csf` infrastructure before `search-research` package existed as the application layer.

---

## Decision

### Core Principle

**Application features belong in application packages (`search-research`), not in infrastructure (`__csf`).**

### Architecture

**Move CHS core system to `search-research`:**

```
packages/search-research/ (application package)
├── core/chs/                          ← NEW: CHS core system
│   ├── __init__.py
│   ├── cli.py                          ← CHS CLI (move from __csf)
│   ├── database.py                     ← Database operations (move from __csf)
│   ├── indexer.py                      ← Indexing logic (move from __csf)
│   └── models.py                       ← Schema definitions
├── skills/chs/                        ← /chs skill wrapper
│   └── scripts/chs_cli.py             ← Imports from core.chs.cli
└── core/backends/local/
    └── chs_incremental.py            ← Internal backend (keep)

packages/search-backends/ (shared library)
└── REMOVE chs_incremental.py         ← Delete duplicate

__csf/ (infrastructure/data)
└── data/                             ← CHS data only
    ├── chat_history.db
    ├── chat_history_faiss_424k/
    └── chs_index_state.json
```

### Ownership

| Concern | Owner | Location |
|---------|-------|----------|
| CHS application logic | `search-research` | `core/chs/` |
| CHS skill interface | `search-research` | `skills/chs/` |
| CHS data storage | `__csf` | `data/` |
| CHS shared backend | None (internal only) | `search-research/core/chs/` |

---

## Consequences

### Positive

✅ **Single source of truth** - All CHS code lives in one place
✅ **Clear ownership** - `search-research` owns CHS the feature
✅ **No duplication** - Remove duplicate `chs_incremental.py`
✅ **Proper separation** - Application code in packages, data in __csf
✅ **Easier maintenance** - Developers know where to find CHS code
✅ **Simpler architecture** - Reduced cognitive load

### Negative

⚠️ **Migration effort** - Move files from `__csf` to `search-research`
⚠️ **Import updates** - Update all imports pointing to old location
⚠️ **Breaking change** - Any external code importing from `__csf` will break

### Migration Required

1. **Create** `packages/search-research/core/chs/` directory structure
2. **Move** CHS core files from `__csf/src/knowledge/systems/chs/v2/scripts/`:
   - `chs_cli.py` → `core/chs/cli.py`
   - `init_db.py` → `core/chs/database.py`
   - `run_indexer.py` → `core/chs/indexer.py`
3. **Update** `packages/search-research/skills/chs/scripts/chs_cli.py` to import from new location
4. **Update** all imports in `search-research` that point to old location
5. **Remove** duplicate `chs_incremental.py` from `search-backends`
6. **Delete** old CHS directory in `__csf/src/knowledge/systems/chs/v2/`
7. **Update** ADR-001 to reflect new architecture (CHS now in `search-research`)
8. **Update** documentation to reflect new file locations

---

## Alternatives Considered

### Alternative A: Keep CHS in __csf

**Rejected:** `__csf` is infrastructure/data storage. CHS is application code. Mixing concerns violates separation of concerns.

### Alternative B: Move CHS to search-backends

**Rejected:** `search-backends` is a shared library for other projects to import. CHS is a `search-research` feature, not a shared library.

### Alternative C: Split CHS across both packages

**Rejected:** Creates fragmentation and duplication. Single owner principle is violated.

---

## References

- ADR-001: CHS Path Configuration (established env var pattern for data paths)
- Issue: "not initialized" errors due to fragmented architecture
- Related: Chat history analysis showing CHS problems

---

**Decided by:** TBD
**Implementation:** Pending
**Review Date:** 2026-09-19 (6 months post-implementation)

## Implementation Checklist

**Phase 1: Prepare**
- [ ] Create `packages/search-research/core/chs/` directory
- [ ] Document all files in `__csf/src/knowledge/systems/chs/v2/`
- [ ] Search for all imports of old location

**Phase 2: Move**
- [ ] Move `chs_cli.py` → `core/chs/cli.py`
- [ ] Move `init_db.py` → `core/chs/database.py`
- [ ] Move `run_indexer.py` → `core/chs/indexer.py`
- [ ] Create `__init__.py` with proper exports

**Phase 3: Update Imports**
- [ ] Update `skills/chs/scripts/chs_cli.py` to import from `core.chs.cli`
- [ ] Search and replace all imports in `search-research`
- [ ] Test imports work correctly

**Phase 4: Cleanup**
- [ ] Remove duplicate `chs_incremental.py` from `search-backends`
- [ ] Delete old `__csf/src/knowledge/systems/chs/v2/` directory
- [ ] Verify no broken imports remain

**Phase 5: Documentation**
- [ ] Update ADR-001 to reflect new architecture
- [ ] Update READMEs with new file locations
- [ ] Update CHANGELOG.md

**Phase 6: Verification**
- [ ] Run `python -m search_research.core.chs.database` (init_db)
- [ ] Test `/chs` skill works
- [ ] Verify database operations work
- [ ] Verify indexing works
