# `/arch` Template Changes - COMPLETED

## Summary

All `ARCHITECTURE_REVIEW` path changes have been successfully applied to all `/arch` templates.

## Files Modified

| Template | Path | Status |
|-----------|------|--------|
| SKILL.md | `P:\.claude\skills\arch\SKILL.md` | ✅ Updated |
| deep.md | `P:\.claude\skills\arch\resources\deep.md` | ✅ Updated |
| fast.md | `P:\.claude\skills\arch\resources\fast.md` | ✅ Updated |
| cli.md | `P:\.claude\skills\arch\resources\cli.md` | ✅ Updated |
| python.md | `P:\.claude\skills\arch\resources\python.md` | ✅ Updated |
| data-pipeline.md | `P:\.claude\skills\arch\resources\data-pipeline.md` | ✅ Updated |
| precedent.md | `P:\.claude\skills\arch\resources\precedent.md` | ✅ Updated |

## Changes Applied to Each Template

### 1. Common Glossary Updates
Added `ARCHITECTURE_REVIEW` definition:
```markdown
- **ARCHITECTURE_REVIEW:** Query asks to review/evaluate proposed design or architecture
```

### 2. Stage 0: Detect Intent Type
Replaced simple IMPROVE_SYSTEM detection with three-path intent detection:

**Is this an ARCHITECTURE_REVIEW request?**
- Keywords: review, evaluate, assess, analyze, audit, validate, critique
- Context: design, architecture, integration, proposal, theoretical
- **If YES:** Proceed to "Stage 0: ARCHITECTURE_REVIEW Path"

**Is this an IMPROVE_SYSTEM request?**
- Keywords: improve, optimize, harden, stabilize, enhance, strengthen
- Subsystem: memory, CKS, hooks, research, retro, lesson, ingestion, validation
- **If YES:** Proceed to "IMPROVE_SYSTEM"

**Otherwise (DEFAULT):**
- Proceed to "DEFAULT" path

### 3. New ARCHITECTURE_REVIEW Path Section
Added comprehensive review path with:
- Purpose statement
- Scope Constraints (DO/DON'T lists)
- Key Principle about reviewing designs BEFORE implementation
- Review Stages (Scope Verification, Gap Analysis, Risk Assessment, Evidence Table)
- Output Format with findings table template
- Confidence scoring with evidence basis

## Key Principle Added

> **Architecture reviews exist PRECISELY to evaluate designs BEFORE implementation.**
> Theoretical designs deserve rigorous analysis precisely to prevent costly mistakes.
> If the design were already implemented, we wouldn't need a review—we'd test it instead.

## Next Steps

1. Test the `/arch` skill with a review query to verify the new path works correctly
2. Monitor for any issues with the new intent detection logic

## Original Issue Resolved

The chat log documented an LLM incorrectly treating an "architecture review" request as requiring implementation first. The LLM suggested the review was "premature" because the system wasn't installed.

**Root cause:** The `/arch` templates lacked explicit `ARCHITECTURE_REVIEW` intent type and corresponding review-first principles.

**Solution:** Added dedicated `ARCHITECTURE_REVIEW` path to all templates with explicit guardrails that:
- DO NOT suggest skipping or delaying work
- DO NOT recommend installation before review
- DO NOT declare designs "premature" due to lack of installation
- DO recognize that architecture reviews are valid EVEN for theoretical/unimplemented designs
