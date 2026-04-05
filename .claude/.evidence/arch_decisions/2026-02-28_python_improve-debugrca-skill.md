# Architecture Decision: Improve debugRCA Skill with Pattern Audit

**Date:** 2026-02-28
**Status:** Proposed
**Decision:** Add systematic pattern audit (Step 1.5) and completeness verification (Step 8.5) to debugRCA methodology

---

## Problem Statement

During investigation of flashing progress bar issue, debugRCA workflow produced incomplete fix:
- **First attempt:** Fixed manual stdout writes (wrong symptom)
- **Second attempt:** Fixed 3 of 4 Progress contexts (incomplete search)
- **Third attempt:** Found missing 4th Progress context (root cause)

**Root cause:** Methodology jumped to symbol-level tracing before comprehensive codebase audit.

---

## Decision

Add two new steps to debugRCA methodology:

### Step 1.5: Pattern Audit (NEW)
Before tracing symbol-level data flow, grep entire codebase for ALL instances of the pattern.

**When to use:**
- Library/API issues (e.g., Rich Progress, SQLAlchemy queries)
- Configuration parameter searches
- Finding all usages of a function/class

**Example:**
```bash
# Find ALL Progress contexts before diving in
Grep pattern="with Progress\(" path="src/"

# Find ALL refresh rate configurations
Grep pattern="refresh_per_second" path="src/"
```

### Step 8.5: Completeness Verification (NEW)
Before declaring fix complete, verify no other instances exist.

**Process:**
1. Re-run pattern audit grep from Step 1.5
2. Verify ALL instances have been addressed
3. Investigate if count differs from initial audit
4. Only proceed to Step 9 (verification) after completeness confirmed

---

## Rationale

1. **Pattern-first approach** - Grep finds ALL instances faster than execution path tracing
2. **Completeness gates** - Prevents partial fixes by requiring verification
3. **Right tool guidance** - Clarifies when to use Grep vs Serena MCP
4. **Evidence calibration** - Confidence caps based on search completeness

---

## Alternatives Considered

| Option | Pros | Cons | Decision |
|--------|------|-------|----------|
| A: Multi-agent requirement | Thorough | High token cost, complex | Rejected |
| B: Mandatory code exploration | Maps codebase | Overkill for patterns | Rejected |
| C: Status quo | Simple | Allows incomplete fixes | Rejected |

**Selected:** Add Steps 1.5 and 8.5 (documentation change, low risk)

---

## Evidence Tiers

| Search Completeness | Confidence Ceiling |
|---------------------|-------------------|
| Partial codebase | 60% (Tier 3) |
| Full grep + targeted Read | 85% (Tier 2) |
| Execution verification | 95% (Tier 1) |

---

## Python Implementation Notes

- Use regex patterns: `with Progress\(`, `refresh_per_second\s*=`
- pathlib for recursive searches if needed
- Type hints help identify related modules

---

## Related Changes

- Update: `.claude/skills/debugRCA/SKILL.md`
- Step 2: Clarify Grep-first vs Serena MCP usage
- Add confidence scoring based on completeness

---

**Confidence:** 92%
**Evidence basis:** Direct analysis of incomplete fix failure mode
