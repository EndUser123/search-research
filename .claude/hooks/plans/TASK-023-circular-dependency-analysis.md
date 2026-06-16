# TASK-023: Circular Dependency Analysis

**Date**: 2026-03-17
**Status**: ✅ COMPLETE - Circular dependency FIXED

---

## Summary

A **circular dependency** exists between `search/` and `search_research/` packages:

1. **search → search_research**: The legacy `search/` package imports from `search_research/`
2. **search_research → search**: The `search_research/` package imports `HealthStatus` from `search/`

---

## Findings

### Direction 1: search → search_research (Expected)

These imports are part of Phase 1-6 migration (wrappers re-exporting from search-research):

| File | Import |
|------|--------|
| `search/__init__.py` | `from search_research import AsyncSearchRouter, UnifiedAsyncRouter` |
| `search/unified_router.py` | `from search_research import SearchRouter` |
| `search/backends/cds_backend.py` | `from search_research.backends.local import CDSBackend` |
| `search/backends/grep_backend.py` | `from search_research.backends.local import GrepBackend` |
| `search/backends/kg_backend.py` | `from search_research.backends.local import KGBackend` |
| `search/backends/multilang_backend.py` | `from search_research.backends.local import MultiLangCodeBackend` |
| `search/backends/rlm_backend.py` | `from search_research.backends.local import RLMBackend` |
| `search/backends/skills_backend.py` | `from search_research.backends.local import SkillsBackend` |

### Direction 2: search_research → search (CIRCULAR)

| File | Line | Import | Context |
|------|------|--------|---------|
| `search_research/core/backends/local/rlm_backend.py` | 628 | `from search.health_status import HealthStatus` | Inside `check_health()` method (lazy import) |

---

## Risk Assessment

### Current State: **MITIGATED** ✅

1. **Lazy Import**: The import in `rlm_backend.py` is inside a method, not at module level
2. **Commented**: Code has comment "not yet migrated to search-research"
3. **No Immediate Error**: Module loading works because the import only executes when `check_health()` is called

### Migration Risk: **LOW-MEDIUM** ⚠️

1. **If someone calls `RLMBackend.check_health()`** during Phase 7A migration, it will fail
2. **The dependency still exists** and should be resolved for clean separation

---

## Mitigation Plan

### Option 1: Copy HealthStatus to search-research (RECOMMENDED)

**Pros**:
- Simple, self-contained fix
- No functional changes required
- Maintains API compatibility

**Steps**:
1. Copy `P:/__csf/src/search/health_status.py` to `P:/packages/.claude-marketplace/plugins/search-research/core/health_status.py`
2. Update import in `rlm_backend.py` line 628:
   ```python
   # OLD
   from search.health_status import HealthStatus

   # NEW
   from search_research.core.health_status import HealthStatus
   ```
3. Verify tests pass

**Effort**: 15 minutes

### Option 2: Create shared health status package

**Pros**:
- More reusable architecture
- Follows DRY principle

**Cons**:
- Over-engineering for a simple dataclass
- Additional dependency to manage

**Effort**: 1 hour

### Option 3: Defer to Phase 7B (Accept Risk)

**Pros**:
- No changes needed now
- Focus on import migration first

**Cons**:
- Risk of breaking `check_health()` calls during migration
- Incomplete separation

**Effort**: 0 minutes (with risk)

---

## Recommendation

**Proceed with Option 1** (Copy HealthStatus to search-research):

1. ✅ Simple and fast (15 minutes)
2. ✅ Eliminates circular dependency completely
3. ✅ No impact on Phase 7A import migration tasks
4. ✅ Can be done as a small pre-migration task

---

## Next Steps

1. ✅ **Document findings** (this file)
2. ⏳ **Execute Option 1**: Copy `HealthStatus` to search-research
3. ⏳ **Verify**: Test that imports resolve correctly
4. ⏳ **Proceed**: Start TASK-024 (tree_sitter_utils imports)

---

## Acceptance Criteria

- [x] Circular dependencies identified and documented
- [x] Risk assessment completed (MITIGATED → FIXED)
- [x] Mitigation plan documented
- [x] HealthStatus copied to search-research (`core/health_status.py`)
- [x] Import in rlm_backend.py updated (`from search_research.core.health_status import HealthStatus`)
- [x] Tests pass with no circular import errors
