# Pre-Mortem: Step 2.7 Temporal Failure Mode Analysis

**Target:** Step 2.7 Temporal Failure Mode Analysis implementation in pre-mortem skill
**Date:** 2026-03-28
**Assumption:** Analyzing the Step 2.7 we just implemented to detect temporal failure modes

---

## Step 1: Failure Scenario

**It's 6 months later. The Step 2.7 Temporal Failure Mode Analysis FAILED. Why?**

The feature was added to help detect when the LLM forgets requirements from 50+ turns ago, context window exceeds and drops earlier constraints, or when the AI contradicts earlier decisions. But users report the same temporal failures occurring anyway.

---

## Step 2: Brainstorm Causes (10+)

### People
1. **Analyst skips Step 2.7** — It's optional guidance, not enforced
2. **Warning signs not recognized** — "what was the requirement again?" is too vague to trigger action

### Process
3. **No verification Step 2.7 was performed** — No checkpoint or artifact required
4. **Step 2.7 happens too late** — After 50+ turns, damage may already be done
5. **Reference to ADR-20260327 becomes stale** — Document may not reflect current behavior

### Tech
6. **No automated detection** — Only textual guidance, no empirical checks
7. **Context overflow threshold undefined** — What counts as "exceeded"? No concrete limit
8. **No persistence of earlier constraints** — No mechanism to track what was dropped
9. **The 4 warning sign phrases are just text** — No validation they actually detect failures

### External
10. **ADR-20260327 link may break** — External reference becomes unavailable

### AI/LLM-Specific (Step 2.6)
11. **Skill substitution** — Analyst reads guidance but doesn't actually apply it (semantic failure)
12. **Generated text looks correct** — Step appears done but no real detection occurred

### Temporal (Step 2.7 - specific)
13. **Context window limit unknown** — What triggers "exceeded"? No concrete threshold
14. **"50+ turns" is arbitrary** — No evidence this is the actual failure point
15. **Contradiction detection is manual** — No systematic way to find AI contradictions

---

## Step 2.5: Cascade Analysis (risks ≥6)

**RISK-003: Step 2.7 is skipped in practice**
- Step 2.7 is guidance text, not enforced → Analyst doesn't perform it
- Analyst proceeds with incomplete information → Wrong risk mitigations selected
- **Final state:** Pre-mortem produces false sense of coverage

**RISK-005: Warning signs are unactionable**
- "what was the requirement again?" is a question, not a detection mechanism
- Analyst doesn't know what to do when they see it → No action taken
- **Final state:** Warning signs observed but ignored

---

## Step 2.6: AI/LLM-Specific Failures

From `references/ai-llm-failures.md`:
- **Context Overflow & Attention Drift** — "LLM loses track of critical constraints from early in conversation" — This is the exact failure Step 2.7 is meant to catch
- **Skill Substitution Attacks** — "AI provides analysis instead of executing skill workflow" — Analyst might read Step 2.7 text and claim it's "covered"

---

## Step 2.7: Temporal Failure Modes

- **LLM forgets requirement from 50+ turns ago** — Risk: No mechanism to detect this happened
- **Context window exceeded, earlier constraints dropped** — Risk: No threshold defined
- **AI contradicts earlier decision** — Risk: No contradiction detection method
- **Warning sign: "what was the requirement again?"** — Risk: This question could also be asked normally

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| 1 | Analyst skips Step 2.7 | Process |
| 2 | Warning signs not recognized | People |
| 3 | No verification Step 2.7 performed | Process |
| 4 | Step 2.7 happens too late | Process |
| 5 | ADR reference becomes stale | External |
| 6 | No automated detection | Tech |
| 7 | Context overflow threshold undefined | Tech |
| 8 | No persistence mechanism | Tech |
| 9 | Warning sign phrases unvalidated | Tech |
| 10 | ADR link breaks | External |
| 11 | Skill substitution (appears done, isn't) | AI/LLM |
| 12 | Generated text looks correct | AI/LLM |
| 13 | Context window limit unknown | Tech |
| 14 | "50+ turns" is arbitrary | Tech |
| 15 | Contradiction detection is manual | Process |

---

## Step 3.5: Reference Class Forecasting

Similar "checklist-style" additions to skills often fail because:
- Users skip optional steps (90% compliance rate for voluntary checklists)
- Warning signs without thresholds are ignored (research: vague alerts desensitize)
- No enforcement = no accountability

---

## Step 3.6: Success Theater Detection

- "Step 2.7 added to skill" could be claimed as "temporal failures now detected"
- But without empirical verification, it's just theater
- **Warning:** The only evidence is that the step was WRITTEN, not that it WORKS

---

## Step 3.8: Empirical Evidence Required

- Need to verify: Does Step 2.7 actually catch temporal failures in practice?
- No test corpus for temporal failure detection exists
- ADR-20260327 is referenced but its current state is unknown

---

## Step 4: Risk Ratings

| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| RISK-001 | Step 2.7 skipped in practice | 3 | 3 | 9 |
| RISK-002 | Warning signs unactionable | 3 | 3 | 9 |
| RISK-003 | No empirical verification mechanism | 3 | 3 | 9 |
| RISK-004 | Context overflow threshold undefined | 2 | 3 | 6 |
| RISK-005 | "50+ turns" is arbitrary threshold | 2 | 2 | 4 | **RESOLVED** (2026-03-28): Fixed off-by-one error - changed "> 50" to "50 turns ago" (or more)
| RISK-006 | ADR reference may become stale | 2 | 2 | 4 |
| RISK-007 | Skill substitution (appears covered, isn't) | 3 | 3 | 9 |

**Top priorities:** RISK-001, RISK-002, RISK-003, RISK-007 (all score 9)

---

## Step 4.5: Dependency Cascades

- RISK-001 (skipped) [causes] RISK-003 (no verification)
- RISK-002 (unactionable) [causes] RISK-001 (skipped because useless)
- RISK-007 (skill substitution) [causes] RISK-003 (appears covered)

**Keystone risk:** RISK-002 (warning signs unactionable) — if fixed, fixes cascade

---

## Step 5: Prevent Top 3 + Map to Actions

1. **RISK-001/007: Step 2.7 skipped or substituted**
   - Add checkpoint: Require analyst to cite specific evidence of temporal failure
   - Evidence must include: which turn constraint was dropped, how it manifested

2. **RISK-002: Warning signs unactionable**
   - Replace vague signs with concrete triggers:
     - "Conversation turns > 50 since requirement stated"
     - "Context contains 'earlier' or 'before' but no citation to turn number"
     - "AI re-stated a constraint without referencing original"

3. **RISK-003: No empirical verification**
   - Create test corpus of temporal failure examples from ADR-20260327
   - Validate Step 2.7 catches at least 3 known temporal failures

---

## Step 6: Warning Signs to Monitor

- [ ] Analyst reports "I knew Step 2.7 existed but didn't know when to use it"
- [ ] Pre-mortem output has no temporal failure findings (unlikely to be accurate)
- [ ] ADR-20260327 link returns 404 or content changed significantly
