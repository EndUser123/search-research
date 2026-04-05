# Architecture Decision: /package Documentation Quality System

**Date:** 2025-03-07
**Type:** IMPROVE_SYSTEM
**Status:** PROPOSED

## Decision

Implement a 3-phase documentation quality system with automated validation, structured completeness checks, and dependency verification to prevent circular references and incomplete content in the `/package` skill documentation.

## Rationale

1. **Root cause analysis revealed**: Circular reference (PHASE 1.6 ↔ brownfield-conversion.md) went undetected because no validation exists for documentation cross-references
2. **Execution vs audit mode gap**: Documentation flaws invisible during tool use but obvious during audit → needs automated validation that doesn't depend on human vigilance
3. **Version drift**: HYBRID_GAPS.md (v5.1) conflicts with SKILL.md (v5.2) → needs dependency tracking to obsolete documentation
4. **Progressive disclosure violation**: 17-line stub file referenced as "complete workflow" → needs content completeness validation

## Alternatives Considered

1. **Manual documentation audit** - Rejected because doesn't scale, requires human vigilance each time /package changes
2. **Remove reference system entirely** - Rejected because loses progressive disclosure benefits, bloats SKILL.md to 10,000+ lines
3. **Convert to single-file documentation** - Rejected because violates /package's own architectural pattern (lean body + detailed refs)

## Risk

- **Over-engineering validation** - Could create complex schema validation that's harder to maintain than the documentation itself
- **False positives** - Over-strict validation might block valid documentation changes
- **Schema drift** - Validation schema itself becomes outdated documentation

## Implementation Phases

### Phase 1: Automated Documentation Validation (HIGH Impact, MEDIUM Effort)
- Create `DocumentationValidator` class in `resources/validate_docs.py`
- Implement checks: circular references, reference completeness, version consistency, cross-reference validity
- Create `PostToolUse_documentation_validator.py` hook
- Register in settings.json

**Effort:** 4-6 hours development + 2 hours testing
**Risk:** LOW - Automated validation, doesn't block writes (just warns)
**Impact:** HIGH - Prevents circular references and incomplete documentation

### Phase 2: Complete Brownfield Documentation (HIGH Impact, LOW Effort)
- Expand `references/brownfield-conversion.md` from 17 lines to ~200 lines
- Add pre-conversion checklist (5 items: hardcoded paths, platform code, error handling, dependencies, tests)
- Document conversion workflow with 7 steps
- Add common issues and solutions table
- Include skill-guard as real-world example

**Effort:** 2-3 hours to write documentation
**Risk:** LOW - Documentation only, no code changes
**Impact:** HIGH - Provides missing guidance, prevents failed conversions

### Phase 3: Update SKILL.md PHASE 1.6 (HIGH Impact, LOW Effort)
- Replace circular reference with clear checklist reference
- Add 5-item pre-conversion checklist
- Summarize conversion steps
- Document rollback procedure

**Effort:** 15 minutes to edit SKILL.md
**Risk:** LOW - Documentation update only
**Impact:** HIGH - Points users to complete documentation

### Phase 4: Archive or Update HYBRID_GAPS.md (MEDIUM Impact, LOW Effort)
- Option A: Archive as `.archive/v5.1/HYBRID_GAPS.md` with README
- Option B: Update with version warnings and remaining gaps

**Effort:** 30 minutes (archive) or 1 hour (update)
**Risk:** LOW - Documentation cleanup only
**Impact:** MEDIUM - Eliminates confusion, maintains historical record

## Skills, Workflows, and Hooks to Update

### Update `/package` Skill
- `SKILL.md` (Phase 1.6 update)
- `references/brownfield-conversion.md` (expand from 17 to ~200 lines)
- `references/brownfield-next-steps.md` (create new)
- Update Bundled Resources section

### Create Validation Hook
- `PostToolUse_documentation_validator.py` (new file)
- Register in settings.json PostToolUse hooks

### Update `/learn` Skill
- Add "execution mode vs audit mode" pattern to CKS

### Update `/plan-workflow` Skill
- Add pre-flight check for documentation completeness in PHASE 0

### Create New Skill: `/docs-validate`
- Standalone command to validate documentation quality
- Trigger: "/docs-validate" or "check documentation"
- Integrate into /package as PHASE 4.5

## Confidence

87% - High confidence based on specific evidence from session analysis, Python best practices, and feasible implementation. Adversarial self-review identified weakest assumption: automated validation won't create noise pollution.

## Evidence Sources

- Session analysis: 11 documentation gaps identified
- Python best practices: Type hints, automated validation
- Implementation patterns: PostToolUse hooks for validation

## Next Steps

1. Implement Phase 1 (validator + hook) - highest priority, prevents recurrence
2. Implement Phase 2 (brownfield docs) - unblocks skill-guard conversion
3. Implement Phase 3 (SKILL.md update) - improves user experience
4. Consider Phase 4 (HYBRID_GAPS.md) - lower priority, cleanup
5. Create `/docs-validate` skill - standalone utility
