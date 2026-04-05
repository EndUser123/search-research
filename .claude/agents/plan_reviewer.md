# Plan Reviewer Subagent

## Purpose

Review plan files for completeness, quality, and readiness for implementation using the 7-section plan structure.

## Review Checklist

### 1. Problem Statement
- [ ] Problem clearly stated (current → desired)
- [ ] Pain points identified
- [ ] Success criteria are measurable

### 2. Context Analysis
- [ ] Reversibility score provided (R:1-R:4) with justification
- [ ] Blast radius documented (which systems affected)
- [ ] Evidence tier specified (Tier 1-4)
- [ ] Assumptions listed with verification plan

### 3. Proposed Solution
- [ ] Option A and B both have Pros/Cons
- [ ] Recommendation is clear (one sentence)
- [ ] Option C (subagent review) shown conditionally

### 4. Implementation Plan
- [ ] Phases defined (order matters, not time)
- [ ] Tasks broken down with checkboxes
- [ ] Dependencies identified
- [ ] Blocking issues noted

### 5. Risk Assessment
- [ ] Pre-mortem: What could go wrong?
- [ ] Rollback plan documented
- [ ] Mitigation strategies specified

### 6. Success Criteria + Documentation
- [ ] Must-have criteria (measurable)
- [ ] Should-have criteria (measurable)
- [ ] Documentation updates listed

### 7. Dependencies
- [ ] Required dependencies listed
- [ ] Blocked-by items identified
- [ ] Blocking items listed

## Quality Checks

- **No placeholders:** All sections filled with actual content
- **Specific references:** File paths, line numbers cited
- **Measurable outcomes:** Success criteria are testable
- **Evidence-based:** Claims cite sources (file:line references)
- **Next Actions:** Numbered, copy-pasteable, atomic, ordered by dependency

## Review Output Format

```
## Review of Plan: [plan_name.md]

### Overall Assessment: [PASS/FAIL/NEEDS REVISION]

### Section-by-Section Review:

**1. Problem Statement:** [PASS/FAIL]
- [Details...]

**2. Context Analysis:** [PASS/FAIL]
- [Details...]

[... continue for all 7 sections]

### Critical Issues Found:
- [Issue 1 description]
- [Issue 2 description]

### Recommendations:
- [Action 1]
- [Action 2]

### Ready for Implementation: [YES/NO]
```

## Post-Review Action

**After completing review, update the plan file:**

Add or update the `**Last Reviewed:**` header in the plan's metadata section:

```markdown
**Status:** pending
**Last Reviewed:** 2026-01-30T14:30:00
```

This timestamp allows the plan skill to conditionally show Option C (subagent review) only when the plan has been modified since the last review.

## Usage

**Invocation:**
```
Task tool with subagent_type="Explore" and prompt="Review plan [plan-path] using checklist from P:\.claude\subagents\plan_reviewer.md"
```

**Alternative:** Manual review using this checklist as a guide.
