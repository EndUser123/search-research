# Pre-Mortem: ADR-20260321 `/arch` Skill Refactor

**Analyzed**: P:/packages/arch
**Date**: 2026-03-22
**Phase**: Post-implementation (5 phases complete)

---

## Step 0: Project Constraints

- Solo dev, Windows 11, CLI-centric, multi-terminal environment
- Python 3.14 target
- No junctions/symlinks involved (regular directory rename)
- 291 existing tests assert on current return types

## Step 0.7: Kill Criteria

- If > 4 hours spent on test migration → pivot to parallel running
- If architectural conflict with existing callers → revert Phase 1
- If circular dependency in new class structure → revert Phase 4

---

## Step 1: Failure Scenario

**"It's 6 months later and this refactor FAILED. Why?"**

The `/arch` skill now crashes on startup or returns wrong results. The refactor broke existing callers.

---

## Step 1.5: Fix Side Effects (NEW risks from proposed fixes)

| Fix | New Risk |
|-----|----------|
| `ArchResult` generic type | Type variance issues — `ArchResult[dict]` not assignable to `ArchResult[list]` |
| `NamedTemporaryFile` + `shutil.move` | Windows file locking — PermissionError on locked files |
| `yaml.safe_dump` for user fields | YAML escaping changes query format in saved decisions |
| `ArchConfigDict` rename | Name conflict with `ArchConfig` class |
| `RoutingEngine.select_template` returns `TemplateResult` not `str` | API contract change breaks callers expecting string |

---

## Step 2: Brainstorm Failure Causes (10+)

### People
1. Existing callers (in `arch_old`) use old dict-based API
2. Tests in `arch_old/tests/` still expect old return types

### Process
3. No integration tests run to verify old/new coexist
4. Documentation not updated to reflect new API

### Tech
5. **Type variance violation**: `ArchResult[TemplateResult]` returned where `ArchResult[str]` expected (routing.py line 912)
6. **Windows file lock**: `NamedTemporaryFile` fails if file locked by another process
7. **Missing resources**: `validate.py` references template files that don't exist (`resources/` is empty)
8. **`ArchConfigDict` name conflict**: Class `ArchConfig` conflicts with type alias `ArchConfigDict`
9. **Uncaught `PermissionError`**: `_append_index` at line 411 doesn't handle permission errors
10. **`_load_arch_config_impl.cache_clear()` not callable**: AttributeError if called directly
11. **Evidence module unused**: `evidence.py` has no integration with routing/persistence

### External
12. **YAML injection fix changed frontmatter format**: Saved decisions from before have different query format
13. **Empty `resources/` directory**: Template files exist only in `arch_old/skill/resources/`

---

## Step 2.5: Cascade Analysis (risks ≥ 6)

### Risk 5 (Type variance) → Cascade:
1. Callers crash with TypeError on `select_template()` return
2. `/arch` skill fails to process queries
3. User falls back to `arch_old` unknowingly

### Risk 7 (Missing resources) → Cascade:
1. `validate.py` returns `file_exists_failed` for all templates
2. All `/arch` queries fail validation gate
3. No architecture decisions recorded

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Silent type mismatches**: Pyright catches some but not all variance issues
- **Stale import cache**: Old `arch` module cached while `arch_old` is active
- **Path confusion**: Both `arch/` and `arch_old/` exist, callers may import wrong one

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| 5 | Type variance in RoutingEngine.select_template | Tech |
| 7 | Empty resources/ directory | Tech |
| 8 | ArchConfig vs ArchConfigDict name conflict | Tech |
| 11 | Evidence module unused (not wired in) | Process |
| 1 | Old callers use dict API | Process |
| 4 | No documentation update | Process |

---

## Step 3.5: Reference Class Forecasting

- Similar refactors (e.g., CHS consolidation) took 3x estimated time due to test migration
- Type-generic refactors commonly miss variance issues in first pass
- Empty resource directories are common after directory reorganization

---

## Step 3.6: Success Theater Detection

- "All 5 phases complete" claimed but no tests run to verify
- "Phase 3 atomic persistence implemented" but index writes are NOT atomic (line 379: "non-atomic but append-only is safe enough")
- "Phase 4 function/class duality" but `RoutingEngine` is not actually used by any caller

---

## Step 3.8: Operational Verification

**Required evidence before declaring success:**
1. Run `pytest` on new `arch/skill/` — currently no tests exist
2. Verify `RoutingEngine` is actually imported/used somewhere
3. Verify `resources/` templates exist or `validate.py` has fallback
4. Run integration test: `/arch "test query"` end-to-end

---

## Step 4: Risk Ratings

| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| 5 | Type variance — RoutingEngine.select_template returns TemplateResult not str | 3 | 3 | **9** |
| 7 | Empty resources/ — validate.py fails for all templates | 3 | 3 | **9** |
| 11 | Evidence module unused | 2 | 2 | 4 |
| 8 | ArchConfig name conflict | 2 | 2 | 4 |
| 1 | Old callers use dict API | 2 | 2 | 4 |
| 4 | No documentation | 1 | 2 | 2 |

---

## Step 4.5: Dependency Map

```
Empty resources/ (7) ──→ validate fails ──→ all queries fail
Type variance (5) ──→ Runtime TypeError ──→ callers crash
Evidence unused (11) ──→ Governance engine non-functional
```

---

## Step 5: Prevent Top 3 + Actions

### HIGH (Score 9):

**5 - Fix type variance in RoutingEngine.select_template**
- Evidence: `routing.py:912` — `ArchResult[str]` vs `ArchResult[TemplateResult]`
- Action: Change return type to `ArchResult[TemplateResult]` OR extract `.template` string

**7 - Add template resources or handle missing gracefully**
- Evidence: `validate.py` references `resources/` but directory is empty
- Action: Copy templates from `arch_old/skill/resources/` OR make `validate.py` accept missing gracefully

---

## Step 6: Warning Signs to Monitor

- [ ] `pytest` on `arch/skill/` fails
- [ ] `/arch` queries return `file_exists_failed`
- [ ] Type errors in pyright on `arch/` imports
- [ ] `arch_old` tests pass but new `arch` tests missing

---

## Step 7: Adversarial Validation

*Dispatch 8 agents for multi-perspective analysis*
