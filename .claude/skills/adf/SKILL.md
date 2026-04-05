---
name: adf
description: Evaluate whether structural code changes are justified. Prevents over-engineering.
version: "1.0.0"
status: stable
category: strategy
triggers:
  - /adf
aliases:
  - /adf

suggest:
  - /arch
  - /r
  - /nse
---

# ADF: Architecture Decision Framework

## Purpose

Evaluate whether structural code changes are justified - prevents over-engineering.

## Project Context

### Constitution/Constraints
- Best long-term solution first (no quick fixes without explicit authorization)
- Investigation before recommendation required
- Evidence-based decisions (Tier 1-2 required for complexity >5)

### Technical Context
- ADF scope: ADDS new boundaries/abstractions (not sharing existing ones)
- Complexity tax assessment required
- Boundary stability analysis (6-12 months)
- CKS integration for extended documentation

### Architecture Alignment
- Part of strategy skills (with /arch, /r, /nse)
- Cognitive frameworks (Cynefin, Inversion, Chesterton's Fence, Devil's Advocate) now automatic via cognitive_enhancers hook
- Supports SOLID validation workflow
- Outputs to /subagent-driven-development for implementation

## Your Workflow

1. **Scope Check** - Verify ADF applies (new boundaries vs. capability sharing)
2. **Collect Evidence** - Execute current system, demonstrate failures
3. **Problem Check** - Concrete failure this prevents?
4. **Simpler Alternative** - Can existing code solve this?
5. **Complexity Tax** - Calculate overhead of proposed change
6. **Boundary Stability** - Will this survive 6-12 months?
7. **Stop Signals** - SOLID violations, aesthetics-only justification
8. **Value Completeness** - Anti-satisficing gate
9. **Output or Handoff** - Structured output or delegate to implementation

## Validation Rules

### Prohibited Actions
- **NEVER block without evidence** - execute current system first
- **NEVER approve aesthetics-only changes** - require concrete problem
- **NEVER skip complexity tax calculation** for changes >5 files
- **NEVER proceed with SOLID violations** - refactor first

### Required Output Format
- All responses prefixed with `[ADF]`
- Evidence tier cited for claims
- Complexity tax score (1-10 scale)
- Proceed/Block/Simplify recommendation with rationale

## Response Format

**All responses using this framework MUST be prefixed with `[ADF]`** to indicate the Architecture Decision Framework is active.

Example: `[ADF] Before proposing this extraction, I need to understand...`

---

## Objective

Evaluate a proposed structural change (new file/module/service/boundary) and decide:
- proceed as-is
- proceed but simplify
- block as unjustified
- require formal justification

Always ask the user clarifying questions if the proposal is underspecified.

## Step 0 — Scope Check (Is ADF the right framework?)

**Before applying this framework, determine if the proposal is:**

| Proposal Type | ADF Applies? | Instead |
|---------------|--------------|--------|
| Extract/split/separate code into new boundaries | ✅ Yes | Continue to Step 1 |
| Reorganize/restructure existing code | ✅ Yes | Continue to Step 1 |
| Share existing capabilities more broadly | ❌ No | This is reuse, not new complexity. Evaluate as integration. |
| Give module Y access to module X's tools | ❌ No | This reduces duplication. Evaluate ROI directly. |
| Add abstraction layer | ✅ Yes | Continue to Step 1 |
| Remove/consolidate existing code | ❌ No | This reduces complexity. Proceed. |

**Key question:** Does this proposal ADD new boundaries/abstractions, or does it SHARE/REUSE existing ones?

- Adding new → Apply ADF
- Sharing existing → Skip ADF, evaluate integration benefits directly

**If ADF doesn't apply:** State `[ADF] Scope check: This is capability sharing, not structural extraction. ADF not applicable. Proceeding with integration analysis.`

---

## CKS: Extended Reference Documentation

**Detailed decision framework documentation is stored in CKS.** Use `/cks` to query:

- **Step 1**: `/cks "architecture-decision-framework: Step 1 — Clarify the proposal"`
- **Step 2**: `/cks "architecture-decision-framework: Step 2 — Problem check (ENHANCED)"`
- **Step 2.5**: `/cks "architecture-decision-framework: Step 2.5 — Constitutional Impact Analysis (NEW)"`
- **Step 3**: `/cks "architecture-decision-framework: Step 3 — Simpler alternative"`
- **Step 4**: `/cks "architecture-decision-framework: Step 4 — Complexity tax"`
- **Step 5**: `/cks "architecture-decision-framework: Step 5 — Boundary stability"`
- **Step 6**: `/cks "architecture-decision-framework: Step 6 — Stop signals (ENHANCED)"`
- **Step 7**: `/cks "architecture-decision-framework: Step 7 — Output (significant changes only)"`
- **Step 7.5**: `/cks "architecture-decision-framework: Step 7.5 — Value Completeness Check (Anti-Satisficing Gate)"`
- **Step 8**: `/cks "architecture-decision-framework: Step 8 — Execution Handoff"`
- **Examples**: `/cks "architecture-decision-framework: Examples"`
- **Quick Decision Tree**: `/cks "architecture-decision-framework: Quick Decision Tree (ENHANCED)"`


## Examples

**Justified:**
```
Change: Extract auth into dedicated service
Problem: Auth duplicated across 4 repos, changes require 4 PRs
Complexity tax: 7 (3 files, 1 concept, 1 test)
Reversibility: 1.8
Evidence: Tier 2 — multiple incidents, high coordination overhead
Recommendation: Proceed
```

**Unjustified:**
```
Change: Split utils into three services
Problem: "Better organized"
Recommendation: Do not proceed — no concrete problem
```

## Quick Decision Tree (ENHANCED)

1. **Collect evidence** before blocking: Execute current system, demonstrate failures
2. Concrete failure this prevents? No → **Don't change**
3. Constitutional compliance gaps? Yes → **Proceed with high priority**
4. Simpler fix works? Yes → **Use simpler option**
5. Complexity tax > 5? Yes → **Require Tier 2+ evidence**
6. Boundary survives 6–12 months? No → **Defer**
7. Primary justification is aesthetics without evidence? Yes → **Block**
8. SOLID violations detected? Yes → **Refactor before proceeding** (see CKS)
9. Otherwise → **Proceed with structured output**

---

## CKS: Extended Reference Documentation

**Detailed reference documentation is stored in CKS**. Use `/cks` to query:

| Topic | CKS Query |
|-------|-----------|
| SOLID principles (S, O, L, I, D) with examples | `/cks "SOLID principles software architecture"` |
| DRY/KISS/YAGNI principles | `/cks "DRY KISS YAGNI software principles"` |
| Cognitive frameworks (Cynefin, Inversion, Chesterton's Fence) | `/cks "cognitive frameworks architecture decisions"` |
| Complexity Gate integration | `/cks "Complexity Gate architectural changes"` |

### SOLID Check Workflow

After structural approval, validate proposed design against SOLID principles:

1. Query CKS: `/cks "SOLID principles software architecture"`
2. Apply each principle to the proposed design
3. Document any violations found
4. Recommend refactoring if violations detected

---

## Integration with Cognitive Frameworks

When `/arch` is invoked, the `cognitive-frameworks` skill applies mental models:

| Framework | Purpose |
|-----------|---------|
| **Cynefin** | Problem classification (Clear/Complicated/Complex) |
| **Inversion** | Failure mode identification |
| **Chesterton's Fence** | Respect existing decisions |
| **Devil's Advocate** | Stress-test proposals |

Query CKS for details: `/cks "cognitive frameworks architecture decisions"`
