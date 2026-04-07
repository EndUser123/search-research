# ADR: Stop_hook_premortem_quality_gate.py Placement Optimality

**Date:** 2026-04-05
**Status:** Draft
**Topic:** Stop_hook_premortem_quality_gate.py placement optimality

## Context

A quality gate implementing three validation rules (QA-001: non-empty findings, QA-002: valid severity, QA-003: file:line citations for HIGH/CRITICAL) was implemented as a Stop subprocess hook. This ADR evaluates the optimal placement of this validation logic.

## Key Findings

1. The quality gate (QA-001: non-empty findings, QA-002: valid severity, QA-003: file:line citations for HIGH/CRITICAL) is implemented as a Stop subprocess hook
2. The same validation logic already exists as MANDATORY in p3_synthesis.md (Phase 3 synthesis step)
3. The hook was a stub that returned `{"decision": "allow"}` -- invalid Stop schema (requires "approve"/"block")
4. The hook is NOT registered in Stop_router.py ACTIVE_RUNTIME_HOOKS -- it never actually fires
5. Option A (keep as Stop hook): subprocess overhead for 100% of non-pre-mortem stops, schema mismatch issue
6. Option B (inline into Stop_router.py): couples pre-mortem concerns to core router
7. Option C (embed into p3_synthesis.md as hard precondition): validates at origin, no extra hook, prevents bad output at creation not observation

## Decision

**Recommended: Option C** -- embed quality enforcement in Phase 3 synthesis itself

## Contract Boundaries

- **Producer:** Pre-mortem skill (SKILL.md Phase 3)
- **Consumer:** Stop_router.py
- **Evidence path:** ~/.claude/.evidence/pre-mortem-{terminal_id}/p3.md
- **Failure behavior:** bypass_when_unresolved (currently stub returns approve, correct would be block)

## Options Analysis

### Option A: Keep as Stop Hook
- **Pros:** Centralized enforcement point
- **Cons:** Subprocess overhead for 100% of non-pre-mortem stops; schema mismatch (returns "allow" instead of "approve"/"block")

### Option B: Inline into Stop_router.py
- **Pros:** Direct integration
- **Cons:** Couples pre-mortem concerns to core router

### Option C: Embed in p3_synthesis.md
- **Pros:** Validates at origin; no extra hook; prevents bad output at creation not observation
- **Cons:** None identified

## Validation Requirements

| ID | Requirement | Severity | Enforcement |
|----|-------------|----------|-------------|
| QA-001 | Non-empty findings | HIGH | MANDATORY in p3_synthesis.md |
| QA-002 | Valid severity | HIGH | MANDATORY in p3_synthesis.md |
| QA-003 | file:line citations for HIGH/CRITICAL | HIGH | MANDATORY in p3_synthesis.md |

## Conclusion

The quality gate should be embedded as a hard precondition in p3_synthesis.md Phase 3 synthesis step, not implemented as a Stop hook. The Stop hook was never registered and never fired. Embedding at the origin prevents bad output at creation rather than observing it downstream.
