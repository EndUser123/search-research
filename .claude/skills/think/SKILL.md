---
name: think
description: Lightweight to comprehensive analysis gate - pause and think before implementing
version: "1.0.0"
status: stable
category: meta
triggers:
  - /think
aliases:
  - /think

suggest:
  - /s
  - /r
  - /sequential-thinking
  - /nse
  - /analyze
---

# Analysis Gate

**Comprehensive framework for pre-build analysis.**

For routine decisions, focus on sections 1, 3, 5, 11. For architecture decisions, use all 12 sections.

## Project Context

### Constitution / Constraints

- **Evidence-first**: Verify assumptions before implementing
- **Solo-dev constraint**: Analysis must be proportional to task complexity
- **Vague Directive Gate**: This skill helps clarify vague directives before execution

### Technical Context

- Simple template-based analysis framework
- Integrates with /nse, /sequential-thinking for deeper analysis

### Architecture Alignment

- **Gate pattern**: Pauses execution for analysis without requiring full workflow
- **Composability**: Can be combined with other analysis skills

## Your Workflow

1. **Receive invocation** - User runs /think with a decision or problem to analyze
2. **Check for /q context** - Run context check before analysis
3. **Apply framework internally** - Use relevant sections (1,3,5,11 for routine; all 12 for architecture)
4. **Output distilled analysis** - Present structured recommendation, NOT the filled template
5. **Present second-order effects** - Show what this enables and risks
6. **Assess complexity tax** - Justify for solo dev context
7. **STOP and wait** - Do not proceed until user approval

**Critical:** The 12-section framework is INTERNAL scaffolding for your thinking. Output a distilled recommendation based on the framework, not the filled template itself.

### Context Awareness

Before starting analysis, check for /q context:

```python
python -c "
from lib.q_context import read_context
ctx = read_context('$WT_SESSION', check_stale=True)
if ctx:
    stale = ctx.get('stale', {})
    if stale.get('is_stale'):
        print(f'⚠️ Context is stale: {stale.get(\"reason\")}')
        print('Recommend running /q to refresh before proceeding.')
    else:
        print(f'Context: {ctx.get(\"work_summary\", \"No summary\")}')
        print(f'Mode: {ctx.get(\"mode\", \"unknown\")}, Issues: {ctx.get(\"issues\", 0)}')
else:
    print('No /q context found.')
"
```

If context is stale, warn user and offer to refresh with `/q`.

## Validation Rules

### Prohibited Actions

- **Do not proceed without approval** - Always wait for user confirmation
- **Do not skip for complex tasks** - If task has >3 steps, use this gate

### When to Skip

- Trivial requests (<20 lines, obvious solution)
- Pure information questions
- User says "just do it"


---

## Internal Framework

Use these 12 sections as internal scaffolding for your analysis. Do NOT output this template—use it to structure your thinking, then provide distilled recommendations.

```
## Critical Thinking Analysis

### 1. Problem Clarification
**What are we building?**
- [Restate the feature/change in your own words]
- [What problem does it solve?]

### 2. Constraints
**What are the limitations?**
- [Technical constraints: performance, security, compatibility]
- [Resource constraints: time, budget, quota]
- [User constraints: platform, permissions, workflow]

### 3. Assumptions
**What assumptions am I (Claude) making?**
- [List all implicit assumptions]
- [Which assumptions, if wrong, would break the solution?]
- [Example: "User always runs from project root", "Bash is available", "Folder names are unique"]

### 4. Design Space
**Different approaches:**
1. [Approach A] - Description
2. [Approach B] - Description
3. [Approach C] - Description

### 5. Trade-off Analysis
**Comparing approaches:**
- [Performance vs. complexity]
- [Security vs. usability]
- [Speed vs. correctness]
- [Short-term vs. long-term]

### 6. Failure Analysis
**What can go wrong?**
| Failure | Likelihood | Severity | Mitigation |
|---------|-----------|----------|------------|
| [Failure 1] | Low/Med/High | Low/Med/High | [Mitigation] |
| [Failure 2] | Low/Med/High | Low/Med/High | [Mitigation] |

### 7. Boundaries & Invariance
**What must stay constant?**
- [Invariants: "X must never happen", "Y must always be true"]
- [Boundaries: "Only works when...", "Fails gracefully if..."]

### 8. Observability & Control
**How do we monitor and steer?**
- [Metrics: what to measure]
- [Logging: what to log]
- [Control: how to adjust behavior]

### 9. Reversibility
**Can we undo this?**
- **Reversibility Score:** [R:1-R:4]
- **Rollback plan:** [How to undo]
- **Entropy control:** [What side effects persist]

### 10. Adversarial Review
**Paranoid staff engineer objections:**
- [Objection 1: "This is fragile and will break because..."]
- [Objection 2: "You're solving a tool limitation with a hack. File a feature request instead."]
- [Objection 3: "Over-engineering for a one-off use case."]
- [Counterarguments for each objection]

### 11. AI Delegation Assessment
**What's safe to delegate to AI subagents?**
✅ **Safe to delegate:**
- [Task 1: Clear spec, deterministic, reversible] → Delegate to: [specific subagent type]
- [Task 2: Well-scoped, testable] → Delegate to: [specific subagent type]

⚠️ **Human oversight required:**
- [Task 1: Security-sensitive, architecture decision] → Human reviews, then delegates implementation
- [Task 2: User-facing, business logic] → Human validates output

❌ **Human-only:**
- [Task 1: User preference, UX decision] → User decides, no AI
- [Task 2: Domain-specific knowledge] → User provides input

### 12. Decision Summary
**Short-term:**
- [Immediate benefits, quick wins]

**Long-term:**
- [Strategic value, technical debt implications]

**Remaining unknowns:**
- [What we don't know yet]

**Follow-up questions:**
- [Questions to answer after implementation]

**Dependency mapping:**
- [What this depends on, what depends on this]

**Migration / Rollout strategy:**
- [How to deploy safely, backward compatibility]

**Security threat modeling:**
- [Attack surface, data sensitivity, access control]

**Blast radius analysis:**
- [What breaks if this goes wrong]

**Operational runbook preview:**
- [How to monitor, debug, troubleshoot in production]

---

**Severity Guide:**
- **Small changes:** Use sections 1, 3, 5, 11 internally
- **New features:** Use sections 1, 3, 5, 11 internally
- **Architecture decisions:** Use all 12 sections internally
- **New solutions from scratch:** Use all 12 sections internally

After internal analysis, provide distilled recommendation to user. Then STOP and wait for user approval before implementing.
```

## When to Use

- Big features with multiple components
- Architecture decisions
- New solutions from scratch
- Security-sensitive changes
- Data migrations
- Infrastructure changes

## Skip For

- Trivial requests (<20 lines, obvious solution)
- Pure information questions
- User says "just do it"
