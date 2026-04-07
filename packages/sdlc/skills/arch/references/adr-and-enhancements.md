# ADR and Enhancements Reference

## Architecture Decision Record (ADR) Template

When `/arch` produces a formal ADR, use this structure:

```markdown
# ADR-NNN: <title>

**Date:** YYYY-MM-DD
**Status:** Proposed | Accepted | Deprecated | Superseded
**Context:** <query or issue that prompted this ADR>
**Decision:** <the decision made>
**Consequences:** <what follows from this decision>

## Context
<What is the issue that we're seeing that motivated us to make this decision?>

## Decision
<What is the change that we're proposing and/or doing?>

## Consequences
<What becomes easier or more difficult as a result of this decision?>

## Alternatives Considered
1. **<Alternative 1>** — <Why rejected>
2. **<Alternative 2>** — <Why rejected>

## Implementation
<If implementation-oriented: task list or changes>

## Contract Authority Packet
<Machine-readable boundary definitions, if contract-sensitive>

## Planning Handoff Packet
<Machine-readable planning handoff, if feeding /planning>
```

---

## ARCHITECTURE.md Guidance

If the project has an `ARCHITECTURE.md` file, `/arch` should:

1. **Read it before making recommendations** — understand existing architecture decisions
2. **Reference it when proposing changes** — cite relevant sections
3. **Update it when decisions are made** — suggest additions/changes
4. **Not override it without justification** — existing architecture decisions are presumed valid unless evidence shows otherwise

---

## Graph-Aware Reasoning

When GoT is enabled (default), `/arch` reasoning includes:

1. **Node extraction**: Identify key decisions, constraints, dependencies, risks, and tradeoffs
2. **Edge analysis**: Map SUPPORTS, CONTRADICTS, DEPENDS, and MITIGATES relationships
3. **Cycle detection**: Identify circular dependencies and recommend breaking points
4. **Scoring**: Evaluate options on feasibility, completeness, novelty, and risk
5. **Comparison**: Produce multi-alternative comparison table

See `references/got-integration.md` for full details.

---

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 5.1 | Current | GoT integration v2.5, Lean System Design v4.0, contract primitives |
| 5.0 | 2026-03 | Contract Authority Packets, Planning Handoff Packets, Stage 1.4-1.8 |
| 4.0 | 2026-02 | Lean System Design integration, template chaining |
| 3.0 | 2026-01 | GoT integration, ADR persistence |
| 2.0 | 2025-12 | Multi-template support, domain detection |
| 1.0 | 2025-11 | Initial release with fast/deep templates |

---

## Decision Persistence

ADRs are auto-saved to `P:/.claude/arch_decisions/` unless output is under 2KB or user requests ephemeral.

**Filename format**:
```
{date}_{template_type}_{slug}.md
```

Where:
- `date` = YYYY-MM-DD (actual datetime, not hardcoded)
- `template_type` = fast, deep, cli, python, data-pipeline, precedent
- `slug` = first 50 chars of query, lowercased, non-alphanumeric replaced with hyphens

---

## Enhancement Integration Points

### CKS Integration
If CKS is available, `/arch` performs semantic search for relevant architecture patterns, decisions, and code precedents. See `resources/cks_query_templates.md` for query patterns.

### AID Integration
AID (Architecture Impact Diagram) integration generates visual impact analysis for proposed changes. Opt-in via `--aid` flag.

### Pre-Mortem Integration
When `/arch` is invoked by `/pre-mortem`, it focuses on failure mode analysis and prevention strategies.
