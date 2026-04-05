# Knowledge Ecosystem Deprecation Timeline

**Document Version:** 1.0
**Date:** 2026-02-04
**Status:** Active

## Overview

This document tracks the deprecation timeline for the knowledge ecosystem migration from old import paths to the new `knowledge.*` structure.

## Migration Phases

### Phase 1: Structure Creation ✅ (Completed 2026-02-04)

**Objective:** Create new `src/knowledge/` directory structure with consolidated components.

**Status:** Complete
- All 19 atomic tasks executed
- Import validation passing (6/6 groups)
- New directory structure established

### Phase 2: Deprecation Shims ✅ (Completed 2026-02-04)

**Objective:** Add backward-compatible imports with deprecation warnings.

**Status:** Complete
- Deprecation warnings added to old import paths
- Old imports continue to work but emit `DeprecationWarning`
- New imports work without warnings

**Deprecated Paths:**
| Old Path | New Path | Warning Added |
|----------|----------|---------------|
| `src.cks` | `knowledge.systems.cks` | ✅ |
| `src.chs` | `knowledge.systems.chs` | ✅ |
| `src.search` | `knowledge.search` | ✅ |
| `modules.serena` | `knowledge.analysis.serena` | ✅ |
| `modules.code_analysis.hdma*` | `knowledge.analysis.hdma` | ✅ |

### Phase 3: Incremental Import Updates (Planned 2026-02-05 to 2026-04-04)

**Objective:** Update imports module-by-module in order of risk.

**Migration Order (Low Risk → High Risk):**
1. Test files (lowest risk, easy verification)
2. CLI scripts (isolated, easy to test)
3. Skill files (`.claude/skills/*/SKILL.md`)
4. Integration modules (`src/integration/`, `src/modules/integration/`)
5. Core systems (`src/core/` - migrate last)

**Per-Module Process:**
1. Identify all imports of deprecated paths
2. Update to new paths
3. Verify tests pass
4. Commit changes

**Rollback:** Revert individual module commits if issues arise.

### Phase 4: Cleanup (Planned 2026-08-04)

**Objective:** Remove old paths and deprecation shims.

**Prerequisites:**
- All consuming code updated to new paths
- No deprecation warnings in CI for 30 consecutive days
- Full test suite passing with new paths

**Actions:**
1. Remove old directory structures:
   - `src/cks/` → Keep only core CKS files
   - `src/chs/` → Remove
   - `src/search/` → Remove (consolidated into knowledge/)
   - `modules/serena/` → Remove
   - `modules/code_analysis/hdma*` → Remove

2. Remove deprecation warnings from remaining `__init__.py` files

3. Update documentation to reference new paths only

**Reversibility:** [R:4] - Cannot rollback after cleanup without git restore.

## Timeline Summary

| Phase | Dates | Duration | Status |
|-------|-------|----------|--------|
| Phase 1: Structure Creation | 2026-02-04 | 1 day | ✅ Complete |
| Phase 2: Deprecation Shims | 2026-02-04 | 1 day | ✅ Complete |
| Phase 3: Import Updates | 2026-02-05 to 2026-04-04 | ~2 months | 🔄 Pending |
| Phase 4: Cleanup | 2026-08-04 | 1 day | ⏳ Scheduled |

## Deprecation Period: 6 Months

**Start:** 2026-02-04 (Phase 2 completion)
**End:** 2026-08-04 (Phase 4 execution)

## CI Integration

To track deprecation warnings in CI:

```bash
# Count deprecation warnings in test output
pytest tests/ -v 2>&1 | grep -c "DeprecationWarning"

# Fail if deprecation count exceeds threshold
THRESHOLD=10
COUNT=$(pytest tests/ -v 2>&1 | grep -c "DeprecationWarning" || echo "0")
if [ $COUNT -gt $THRESHOLD ]; then
    echo "Too many deprecation warnings: $COUNT (threshold: $THRESHOLD)"
    exit 1
fi
```

## Migration Checklist

### For Module Maintainers

- [ ] Identify all imports from deprecated paths
- [ ] Update imports to new `knowledge.*` paths
- [ ] Verify tests pass with new imports
- [ ] Check for no deprecation warnings in output
- [ ] Submit PR with "Phase 3 Migration" label

### For Project Leads

- [ ] Track deprecation warning count in CI dashboard
- [ ] Ensure all critical modules migrated by 2026-04-04
- [ ] Schedule Phase 4 cleanup for 2026-08-04
- [ ] Update onboarding documentation with new paths

## Support

**Questions?** Reference the full plan at:
`P:\.claude\plans\knowledge-ecosystem-restructure.md`

**Issues?** Tag with `knowledge-migration` in issue tracker.
