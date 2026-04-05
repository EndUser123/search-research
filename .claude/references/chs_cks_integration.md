## CHS/CKS Citation Requirement (MANDATORY - Phase 2 Enhancement)

**You MUST use historical solutions when CHS provides them.**

### Classifying CHS Results by Outcome

**Step 1: Determine the OUTCOME of each CHS result:**

| Outcome Type | Indicators | Action |
|--------------|------------|--------|
| **RESOLVED** | "fixed", "resolved", "worked", "closed", "solved" | Use as PRIMARY approach |
| **FAILED** | "didn't work", "still failing", "persisted", "no effect", "didn't fix" | DO NOT reuse - add to avoid list |
| **PARTIAL** | "better but", "reduced but", "helped but", "partial fix" | Consider as starting point, not full solution |
| **UNKNOWN** | No clear outcome stated, only problem description | Treat as FAILED (no evidence of success) |

**Step 2: Build your approach based on OUTCOME classification:**



**Step 3: When using a RESOLVED solution:**

1. **MUST use the historical solution as your PRIMARY approach**
2. **MUST cite the specific CHS result** that informed your fix
3. **MUST explain why the historical solution applies**
4. **MUST document any FAILED attempts** from CHS to show what you're avoiding

### Handling Failed Historical Attempts

**When CHS shows failed attempts, you MUST:**

1. **Explicitly list what was already tried and failed:**
   

2. **Explain why you're not repeating those approaches:**
   

3. **Distinguish FAILED from RESOLVED in your analysis:**
   

**Confidence rules for FAILED attempts:**
- If only FAILED attempts exist in CHS → Novel solution is appropriate (no confidence cap)
- Reusing a FAILED approach → Confidence capped at 40% (worse than novel - evidence against it)

### When CHS Returns a RESOLVED Solution

**IF CHS shows a RESOLVED outcome:**
- Same error message with a working fix
- Same file/component with a resolution
- Pattern match with proven solution

**THEN:**
1. **MUST use the historical solution as your PRIMARY approach**
2. **MUST cite the specific CHS result** that informed your fix
3. **MUST explain why the historical solution applies**

### Confidence Capping for Ignoring Historical Solutions

**IF you ignore a CHS-proven solution and propose something different:**
- Your confidence is **capped at 60%** (unproven approach)
- You MUST explain why the historical solution does NOT apply
- You MUST state: "Historical solution from CHS result #[N] was not used because: [reason]"

### Citation Format (REQUIRED in Output)

**When CHS solution used:**
> **Fix informed by:** CHS result #[N] from [session/date]
> **Historical precedent:** This fix was verified to work in [context]
> **Confidence:** [X]% (historical solution + current evidence)

**When CKS pattern used:**
> **Fix informed by:** CKS pattern synthesis for [domain]
> **Pattern recognition:** [description of pattern]
> **Confidence:** [X]% (pattern-based + current evidence)

**When novel solution required (no CHS/CKS match):**
> **Novel analysis:** No historical precedent found in CHS/CKS
> **Approach:** First-principles analysis required
> **Confidence:** [X]% (novel approach, lower ceiling)

### Enforcement Checklist

Before finalizing your fix, verify:
- [ ] Did I check if CHS has a solution for this exact problem?
- [ ] Did I cite the CHS result if one exists?
- [ ] If I ignored CHS solution, did I cap confidence at 60% and explain why?
- [ ] Did I use CKS patterns to inform the fix?
- [ ] Did I cite CKS when it contributed to the solution?

### Violation Examples

❌ **INCORRECT:** Proposes a novel fix when CHS shows a working solution (no citation)
❌ **INCORRECT:** Ignores CHS result without explanation
❌ **INCORRECT:** Claims high confidence for unproven approach when history exists

✅ **CORRECT:** Uses CHS solution as primary approach, cites result
✅ **CORRECT:** Explains why CHS solution doesn't apply, caps confidence at 60%
✅ **CORRECT:** Integrates CKS patterns, cites pattern source

---

## Structured Input Bundle (MANDATORY - v6.11 Enhancement)
