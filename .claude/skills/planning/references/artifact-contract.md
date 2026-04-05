# Artifact Contract & V1 vs V2 Differences

## Key Differences from v1

| Aspect | v1 | v2 |
|--------|----|----|
| Artifact shape | Normalized plan + findings + verification in one file | Plan artifact only; findings in separate files |
| Placeholder handling | auto_fix inserts placeholder content | auto_fix does NOT insert placeholders; draft stays draft |
| Readiness gate | `auto_verify` passes if no HIGH findings | Blocked if any placeholders, contradictions, or unresolved blockers |
| Status tracking | None | `draft` -> `in-review` -> `implementation-ready` |
| auto_fix scope | Adds missing sections with placeholder content | Non-semantic repairs only (headers, ordering, metadata) |
| Review output | Appended to plan file | Separate `*.review.summary.md`; plan stays pure |

## Separate Files (not merged into plan)

- **Plan artifact**: `*.md` -- only the implementation specification
- **Verification result**: `*.review.result.json` -- deterministic check output
- **Findings**: `*.review.findings.json` -- raw adversarial findings per agent
- **Review summary**: `*.review.summary.md` -- synthesized change list plus machine-readable disposition table

## Plan Artifact Structure

Every plan artifact MUST begin with this status header:

```markdown
---
status: draft | in-review | implementation-ready
source: <path to ADR, transcript, or null>
unresolved_blockers: <integer>
---

# Plan: <title>
```

The plan artifact itself must contain ONLY:
- Goal
- Current state with evidence
- Design decisions and invariants
- Implementation changes (with concrete scope per change)
- Test matrix
- Assumptions/defaults
- Open questions

Legacy v1 section headings are accepted during migration, but `auto_fix.py` normalizes them to the v2 canonical headings above.

The plan artifact must NOT contain:
- Raw adversarial findings tables
- Verification dumps or audit logs
- Placeholder text (`TODO`, `TBD`, `path/to/`, `Component A`, etc.)

## Review Summary Disposition Table

`*.review.summary.md` MUST include a disposition table:

```markdown
## Finding Dispositions

| Finding ID | Disposition | Rationale |
|------------|-------------|-----------|
| SEC-001 | accepted | Incorporated into locking design |
| TEST-004 | deferred | Follow-up task after v1 rollout |
| LOGIC-002 | rejected | Reviewer concern invalid after state-machine simplification |
```
