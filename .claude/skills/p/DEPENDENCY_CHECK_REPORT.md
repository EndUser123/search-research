# Dependency Check Report - p-skill Consolidation

## Check Date
2026-02-27

## Objective
Verify no references to old `/p0-6` directory structure remain before deletion.

## Check Command
```bash
rg "P:/.claude/skills/p[0-6]/" "p/" -n
```

## Result
**ZERO MATCHES** - All critical directory path references have been updated.

## Changes Made

### 1. Script Path References
Updated all script paths from `P:/.claude/skills/p[0-6]/scripts/` to `P:/.claude/skills/p/scripts/`:
- `p/phases/p6.md`: security.py, cve_scan.py
- `p/phases/p3.md`: All stage scripts (stage1_syntax.py, stage2_pylint_delta.py, etc.)
- `p/phases/p2.md`: Duplication check script reference
- `p/scripts/main_p5.py`: Self-reference update

### 2. Flow and Template Paths
Updated operational asset paths:
- `p/phases/p5.md`: flow and templates paths
- From `P:/.claude/skills/p5/flows/certify.md` → `P:/.claude/skills/p/flows/certify.md`
- From `P:/.claude/skills/p5/resources/` → `P:/.claude/skills/p/resources/`

### 3. Command Examples
Updated executable command examples to use `/p --phase=N` syntax:
- All phase files (`p/phases/p[0-6].md`): Command invocations
- `p/SKILL.md`: `/p3 --publish` reference
- Helper scripts (`find_similar_to_p*.py`): Command references
- QA report template: Certification badge reference

### 4. Test File Cleanup
- **Deleted**: `p/tests/test_p5_executable.py` (obsolete test for old /p5 directory)

### 5. Remaining Conceptual References
The following remain unchanged as they are conceptual descriptions, not executable references:
- Phase file paths: `P:/.claude/skills/p/phases/p0.md` etc. (correct - these are actual files)
- Pipeline flow diagrams: `/p1 → /p2 → /p3 → /p4` (conceptual phase relationships)
- Phase descriptions: "P6 runs after P5" (phase ordering descriptions)
- SKILL.md warning: "Do NOT invoke `/p0`-`/p6` skills" (accurate deprecation notice)

## Acceptance Criteria Met
- [x] Command returns zero matches for old directory paths
- [x] All script paths point to `/p/scripts/`
- [x] All flow/template paths point to `/p/`
- [x] All executable command examples use `/p --phase=N` syntax

## Safe to Proceed
The `/p0-6` directories can now be safely deleted without breaking any references.
