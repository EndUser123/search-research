# /arch SKILL.md Changes - ARCHITECTURE_REVIEW Intent Type

## Summary
Adding `ARCHITECTURE_REVIEW` intent type to prevent LLM from treating theoretical design reviews as "premature" or requiring installation first.

## Changes to Apply to SKILL.md

### 1. Update Intent Type Detection (Section 4, ~line 242)

**Current code:**
```python
improve_keywords = ["improve", "optimize", "harden", "stabilize", "enhance", "strengthen"]
subsystem_keywords = ["memory", "cks", "hooks", "research", "retro", "lesson", "ingestion", "validation"]

If any improve_keyword AND any subsystem_keyword:
    intent_type = "IMPROVE_SYSTEM"
Else:
    intent_type = "DEFAULT"
```

**Replace with:**
```python
improve_keywords = ["improve", "optimize", "harden", "stabilize", "enhance", "strengthen"]
subsystem_keywords = ["memory", "cks", "hooks", "research", "retro", "lesson", "ingestion", "validation"]
review_keywords = ["review", "evaluate", "assess", "analyze", "audit", "validate", "critique"]
design_keywords = ["design", "architecture", "integration", "proposal", "theoretical", "blueprint"]

# ARCHITECTURE_REVIEW: Explicit review of design/architecture
# Reviews are valid EVEN for theoretical/unimplemented designs
if any review_keyword AND (any design_keyword or "integration" in query.lower()):
    intent_type = "ARCHITECTURE_REVIEW"

# IMPROVE_SYSTEM: Optimize existing subsystem
elif any improve_keyword AND any subsystem_keyword:
    intent_type = "IMPROVE_SYSTEM"

# DEFAULT: General architecture decision
else:
    intent_type = "DEFAULT"
```

### 2. Update False Positive Prevention (Section, ~line 53)

**Add to "Do NOT trigger prerequisite gates for:" list:**
```markdown
- **Architecture/Design REVIEW queries** — "review this design", "evaluate this architecture"
  - Reviews are valid EVEN for theoretical/unimplemented designs
  - Never gate reviews behind installation or implementation status
```

### 3. Update Common Glossary

**Add to glossary:**
```markdown
- **ARCHITECTURE_REVIEW**: Query asks to review/evaluate proposed design or architecture
```

## Template Changes Required

Each template (fast.md, deep.md, cli.md, python.md, data-pipeline.md, precedent.md) needs:

### Add ARCHITECTURE_REVIEW Path

```markdown
## ARCHITECTURE_REVIEW Path

**Purpose**: Evaluate proposed architecture/design WITHOUT recommending alternatives or suggesting implementation first.

### Scope Constraints

**DO:**
- Identify gaps and risks in the proposed design
- Evaluate against best practices (from research)
- Assess feasibility and complexity
- Flag missing components or edge cases
- Cite evidence (files, lines, docs) for each finding

**DO NOT:**
- Suggest skipping or delaying the work
- Recommend installation before review
- Propose alternative architectures
- Gatekeep based on implementation status
- Declare design "premature" due to lack of installation

### Key Principle

> **Architecture reviews exist PRECISELY to evaluate designs BEFORE implementation.**
> Theoretical designs deserve rigorous analysis precisely to prevent costly mistakes.

### Review Stages

1. **Scope Verification** — Confirm understanding of what's being reviewed
2. **Gap Analysis** — Identify missing elements from proposed design
3. **Risk Assessment** — What could fail, based on research + codebase patterns
4. **Feasibility** — Can this be implemented with current constraints?
5. **Evidence Table** — Each finding backed by file:line or external source

### Output Format

```markdown
## Architecture Review: [Title]

### Scope
[What was reviewed]

### Findings

| ID | Severity | Finding | Evidence | Impact |
|-----|-----------|----------|-----------|---------|
| ARCH-001 | HIGH | [description] | [file:line or source] | [consequence] |
| ARCH-002 | MEDIUM | [description] | [file:line or source] | [consequence] |

### Summary
- Total findings: N
- HIGH: X, MEDIUM: Y, LOW: Z
```
```

## Evidence

These changes are based on verified analysis of chat log:
- File: `C:\Users\brsth\Downloads\I'm having problems with a LLM.  Can you filter ou.md`
- Lines 297-298: LLM stated "claude-mem is NOT installed" and "architectural proposals"
- Line 322: LLM labeled review as "Premature"
- Lines 330-334: LLM recommended installation before design
- Line 304: User's actual task was "Review integration"

The core issue: LLM treated a valid architecture review query as requiring implementation first.
