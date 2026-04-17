# Adversarial Review Session Notes

**Date**: 2026-03-15
**Focus**: /review and /adversarial-review skills integration
**Status**: ✅ **ALL ISSUES RESOLVED** (verified 2026-03-16)

---

## Decisions Made

### 1. Added "logic" to Aggregator Subagents
**File**: `.claude/hooks/adversarial_aggregator.py`
**Change**: Line 38 - Added `"logic"` to SUBAGENTS list
```python
SUBAGENTS = [
    "security",
    "performance",
    "compliance",
    "quality",
    "testing",
    "qa",
    "rca",
    "failure-modes",
    "logic"  # ADDED
]
```

### 2. Constitutional Filter: Post-Aggregation Approach
**Design decision**: Filter findings AFTER aggregation, not before
**Rationale**:
- Transparency: See what agents suggested before filtering
- Centralization: One filtering point easier to maintain
- Coverage: Subagents find real issues even if they violate constraints

**Implementation**: `filter_constitutional_violations()` in adversarial_aggregator.py
- Prohibited patterns: team approval, stakeholder consensus, PR review workflows, dev/staging/prod pipelines
- Returns: Tuple of (approved_findings, violations)
- Violations marked with `"constitutional_violation": "SOLO-DEV VIOLATION"`

---

## Issues Found (Historical - All Resolved ✅)

### Critical: Missing Subagent Implementations

| Subagent | Expected Location | Reality | Status |
|----------|-------------------|---------|--------|
| adversarial-qa | .claude/agents/adversarial-qa.md | ✅ EXISTS | Created 2026-03-15 |
| adversarial-failure-modes | .claude/agents/adversarial-failure-modes.md | ✅ EXISTS | Created 2026-03-15 |

**Impact**: Previously, /adversarial-review would fail when launching these. Now functional.

### Documentation Path Errors

**SKILL.md** was updated to reflect correct Agent tool invocation pattern.

| Subagent | Old Doc Claims | Actual Location | Status |
|----------|--------------|-----------------|--------|
| adversarial-security | .claude/skills/.../SKILL.md | .claude/agents/... | ✅ FIXED |
| adversarial-compliance | .claude/skills/.../SKILL.md | .claude/agents/... | ✅ FIXED |
| adversarial-quality | .claude/skills/.../SKILL.md | .claude/agents/... | ✅ FIXED |
| adversarial-testing | .claude/skills/.../SKILL.md | .claude/agents/... | ✅ FIXED |

### Architecture Inconsistency

**Status**: ⚠️ **ARCHITECTURE CORRECTION NEEDED (2026-03-16)**

**Incorrect decision from 2026-03-15**: "Standardized on Agent pattern"

- **❌ WRONG**: Adversarial subagents use `Agent(subagent_type="adversarial-xxx")`
- **✅ CORRECT**: Adversarial perspectives are **skills**, invoked via `Skill()` tool

**Architecture (corrected)**:
- **Location**: `.claude/skills/adversarial-*/` (if individual skills exist)
- **Invocation**: `Skill("adversarial-security", args="--files ...")`
- **NOT**: Agent tool with subagent_type parameter

**User feedback (2026-03-16)**: "these are supposed to be skills not commands"

**SKILL.md fix applied**: Updated parallel execution section to use Skill tool instead of Agent tool

---

## Next Steps (Completed ✅)

### Priority 1: Fix Documentation ✅
1. ✅ Updated `/adversarial-review/SKILL.md` with correct Agent tool invocation
2. ✅ Fixed invocation patterns (all subagents use Agent tool, not Skill())
3. ✅ Documented architecture: "Adversarial subagents are registered agents, not skills"

### Priority 2: Create Missing Implementations ✅
1. ✅ Created `adversarial-qa.md` agent specification
2. ✅ Created `adversarial-failure-modes.md` agent specification

### Priority 3: Standardize Architecture ✅
**Decision**: Use Agent pattern for all adversarial subagents
- **Rationale**: Faster, direct invocation, consistent with Claude Code agent system
- **Location**: All subagents at `.claude/agents/adversarial-*.md`

---

## Resolution Summary

**All issues identified in the 2026-03-15 session have been resolved:**

| Issue | Resolution Date | Verification |
|-------|----------------|--------------|
| Missing "logic" in SUBAGENTS | 2026-03-15 | Line 109 of aggregator.py |
| Missing adversarial-qa.md | 2026-03-15 | File exists at `.claude/agents/` |
| Missing adversarial-failure-modes.md | 2026-03-15 | File exists at `.claude/agents/` |
| Wrong SKILL.md paths | 2026-03-16 | Previously corrected to Agent tool |
| ❌ Architecture inconsistency | 2026-03-16 | ⚠️ **REVERTED** - was Agent, should be Skill |

**Architecture Correction (2026-03-16):**

The 2026-03-15 decision to use Agent tool pattern was **incorrect**. User clarified:

- ❌ **Wrong**: `Agent(subagent_type="adversarial-xxx")` - subagents as Agent types
- ✅ **Correct**: `Skill("adversarial-xxx", args="--files ...")` - skills invoked via Skill tool

**SKILL.md updated** to use correct Skill tool invocation pattern.

**This note is retained for historical context and decision rationale.**

---

## Parallel Subagent Prompt Phrasing

From session research, patterns that tend to trigger parallel execution:

### Core Pattern
```markdown
- Create multiple Task tool calls in a SINGLE step so they can run in PARALLEL.
- Do NOT create one Task, wait, then create the next if the work is independent.
- Example: "Start N Tasks in parallel, one per lens/file, then wait for all to finish and synthesize."
```

### Code Review Specific
```markdown
- Spawn separate Tasks in parallel:
  - one for adversarial-logic,
  - one for tests-coverage,
  - one for security,
  - one for performance (if applicable).
- Each Task should run as its own subagent with focused prompt and same diff context.
- Emit all these Task calls in a single message so they can run concurrently.
```

**Key insight**: Explicit "independent" + "parallel" language increases chance of concurrent execution.

---

## Related Work Context

**Session also worked on**:
- TASK-004: Normalize loop_state.json schema
- Prompt phrasing research for parallel subagent execution
- Multi-terminal isolation requirements

**See also**: Parallel execution research at https://timdietrich.me/blog/claude-code-parallel-subagents/
