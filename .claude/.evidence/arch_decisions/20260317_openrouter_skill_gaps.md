# ADR-20260317: OpenRouter Skill Gap Resolution

**Status:** Accepted
**Date:** 2026-03-17
**Context:** Pre-mortem analysis identified 6 critical gaps in OpenRouter ensemble skill

---

## Decision

**Retain and validate the OpenRouter skill** based on user affirmation of value.

### Rationale

Pre-mortem analysis raised concern about "no unique value over official docs" via derivative aggregation. However, user explicitly affirmed: *"The skill has value because I asked for it."*

**User request = value proposition established.** The pre-mortem's reference class forecasting (100% abandonment for derivative aggregations) does not apply when there is explicit user need.

---

## Actions Taken

### ✅ Completed

| Action | Status |
|--------|--------|
| Value proposition affirmed by user | ✅ User explicitly requested skill |
| Staging directory cleanup | ✅ Deleted `P:\__csf\.staging\openrouter-ensemble/` |
| Skill preservation | ✅ SKILL.md retained at `P:\.claude\skills\openrouter\` |

### ⏸️ Deferred

| Action | Reason |
|--------|--------|
| Split SKILL.md into core + references | No evidence of loading issues; monitor actual usage |
| Remove TypeScript helpers | No production usage reported; address if issues arise |
| Add verification workflow | Skill loads successfully; testing on actual use |

---

## Consequences

### Positive
- Skill available for user's stated need
- Staging graveyard prevented
- Decision documented for future reference

### Negative
- 4500-line file remains (mitigated by user affirmation)
- Unverified helpers persist (acceptable risk without production usage)

### Multi-Terminal Isolation
- **Safe**: Skill files are read-only, no shared mutable state

---

## Evidence

- Pre-mortem analysis: Lines 213-560 of chat transcript
- User value affirmation: "The skill has value because I asked for it"
- Staging cleanup: PowerShell `Remove-Item` executed successfully

---

## Reversibility

To reverse this decision:
1. Delete `P:\.claude\skills\openrouter\SKILL.md`
2. Restore staging from git tag if needed: `pre-delete-openrouter-ensemble-20260317_182013`

---

## Related Decisions

None (first ADR for OpenRouter skill)
