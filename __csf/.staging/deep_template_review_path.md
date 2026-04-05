# deep.md Template Changes - Add ARCHITECTURE_REVIEW Path

## Changes Required

### 1. Update Common Glossary (line 8-11)

**Current:**
```markdown
## Common Glossary
- **IMPROVE_SYSTEM:** Query asks to optimize/harden existing subsystem
- **DEFAULT:** General architecture decision without improvement intent
- **CKS.db:** Constitutional Knowledge System
```

**Replace with:**
```markdown
## Common Glossary
- **ARCHITECTURE_REVIEW:** Query asks to review/evaluate proposed design or architecture
- **IMPROVE_SYSTEM:** Query asks to optimize/harden existing subsystem
- **DEFAULT:** General architecture decision without improvement intent
- **CKS.db:** Constitutional Knowledge System
```

### 2. Update Stage 0 Intent Detection (line 25-34)

**Current:**
```markdown
## Stage 0: Detect IMPROVE_SYSTEM

From the user query, identify:
- **Is this an IMPROVE_SYSTEM request?**
  - Keywords: improve, optimize, harden, stabilize, enhance, strengthen
  - Subsystem: memory, CKS, hooks, research, retro, lesson, ingestion, validation

- **If YES:** Proceed to "Stage 0.3: Codebase-Aware Analysis"
- **If NO:** Proceed to "Stage 0.3: Codebase-Aware Analysis"
```

**Replace with:**
```markdown
## Stage 0: Detect Intent Type

From the user query, identify:

**Is this an ARCHITECTURE_REVIEW request?**
- Keywords: review, evaluate, assess, analyze, audit, validate, critique
- Context: design, architecture, integration, proposal, theoretical
- **If YES:** Proceed to "Stage 0: ARCHITECTURE_REVIEW Path" (below)

**Is this an IMPROVE_SYSTEM request?**
- Keywords: improve, optimize, harden, stabilize, enhance, strengthen
- Subsystem: memory, CKS, hooks, research, retro, lesson, ingestion, validation
- **If YES:** Proceed to "IMPROVE_SYSTEM Path"

**Otherwise (DEFAULT):**
- Proceed to "DEFAULT Decision Path"
```

### 3. Add ARCHITECTURE_REVIEW Path (Insert after Stage 0, before IMPROVE_SYSTEM)

**Insert this new section:**

```markdown
---

## Stage 0: ARCHITECTURE_REVIEW Path

**Purpose**: Evaluate proposed architecture/design WITHOUT recommending alternatives or suggesting implementation first.

### Scope Constraints

**CRITICAL: Architecture reviews are valid EVEN for theoretical/unimplemented designs.**

**DO:**
- Identify gaps and risks in the proposed design
- Evaluate against best practices (from web research in Stage 0.7)
- Assess feasibility and complexity
- Flag missing components or edge cases
- Cite evidence (files, lines, docs) for each finding

**DO NOT:**
- Suggest skipping or delaying the work
- Recommend installation before review
- Propose alternative architectures (that's DEFAULT path)
- Gatekeep based on implementation status
- Declare design "premature" due to lack of installation
- Tell user to "implement first, then review"

### Key Principle

> **Architecture reviews exist PRECISELY to evaluate designs BEFORE implementation.**
> Theoretical designs deserve rigorous analysis precisely to prevent costly mistakes.
> If the design were already implemented, we wouldn't need a review—we'd test it instead.

### Stage 0.3: Codebase-Aware Analysis (if applicable)

If the design references existing files/modules:
1. Glob/Grep to discover relevant files
2. Read top-level structure (first 50 lines, max 5 files)
3. Build internal CODEBASE CONTEXT block
4. Carry this context into review stages

Skip if query is purely theoretical or greenfield.

### Stage 0.7: Web Research (for best practices)

**Use Standard depth (2-4 searches, max 6).**

Generate searches targeting:
1. **Integration patterns** — Best practices for the architecture type being reviewed
2. **Failure modes** — What goes wrong with similar designs
3. **Security/compliance** — Relevant standards for this domain

### Review Stages

#### Stage 1: Scope Verification

Confirm understanding of what's being reviewed:
- What system/design is under review?
- What are the stated goals/non-goals?
- What constraints are assumed?

#### Stage 2: Gap Analysis

Identify missing elements from proposed design:
- Missing components (services, data stores, interfaces)
- Missing failure modes (timeouts, partitions, crashes)
- Missing data flows (edge cases, error paths)
- Missing operational concerns (monitoring, deployment, rollback)

#### Stage 3: Risk Assessment

What could fail, based on research + design analysis:
- Technical risks (complexity, dependencies, compatibility)
- Operational risks (scaling, monitoring, recovery)
- Integration risks (interface changes, data migration)

#### Stage 4: Evidence Table

Each finding MUST be backed by:
- Specific file:line from codebase (if applicable)
- Specific line from design document/proposal
- External source (web research, standards, best practices)

### Output Format

```markdown
## Architecture Review: [Title]

### Scope
[What was reviewed - 1-2 sentences]

### Design Summary
[Brief description of what the design proposes - 2-4 sentences]

### Findings

| ID | Severity | Finding | Evidence | Impact |
|-----|-----------|----------|-----------|---------|
| ARCH-001 | HIGH | [description] | [file:line or source] | [consequence] |
| ARCH-002 | MEDIUM | [description] | [file:line or source] | [consequence] |
| ARCH-003 | LOW | [description] | [file:line or source] | [consequence] |

### Risk Summary
- Technical: [summary]
- Operational: [summary]
- Integration: [summary]

### Conclusion
[Overall assessment - proceed with caution / needs clarification / looks viable with noted gaps]

---

**Confidence:** [X]%

**Evidence basis:**
- Design doc: [source]
- Web research: [count] sources
- Codebase analysis: [files reviewed]

**Key assumptions:**
1. [assumption]
2. [assumption]
```

### Stage 5: Adversarial Self-Review (MANDATORY)

Re-read entire review. Identify weakest finding. Challenge it:

```markdown
## Adversarial Self-Review

**Weakest finding:** [the weakest finding and why]
**If wrong:** [consequence]
**Alternative interpretation:** [what if this isn't actually a gap?]
```

### Stage 6: Persist Output

Auto-save to `P:/.claude/arch_reviews/` with metadata header.

```python
# Filename format
from datetime import datetime
date = datetime.now().strftime("%Y-%m-%d")
slug = re.sub(r'[^a-z0-9]+', '-', query[:50].lower()).strip('-')
filename = f"{date}_review_{slug}.md"
```

---
```

### 4. Update Stage 0.7 Skip Condition

**Add to skip conditions:**
```markdown
Skip ONLY if: query is purely about user's internal system AND CKS has sufficient historical data, OR user explicitly requests offline analysis, OR review is of purely theoretical design with no web-researchable patterns.
```

### 5. Update Pre-Mortem Stage for DEFAULT Path

**Add guardrail:**
```markdown
#### Stage 3: Pre-Mortem

What realistically fails in 6 months if we do this?

**Guardrail:** Do NOT suggest that design is "premature" or should be "implemented first" - that's a review task, not a design task.

Informed by real production failure post-mortems from Stage 0.7 research.
```
