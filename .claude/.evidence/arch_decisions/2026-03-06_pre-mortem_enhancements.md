# Architecture Decision: Pre-Mortem Enhancement Priorities

**Date:** 2026-03-06
**Template:** fast
**Decision:** Implement 6 relevant enhancements, defer 4 irrelevant ones

---

## Filtering Analysis

**From the 10 enhancements identified in previous session:**

### ✅ KEEP (6 enhancements) - Relevant to solo dev AI/LLM workflow

1. **AI/LLM-Specific Failure Modes** - Our daily reality
4. **Kill Criteria** - Prevents sunk cost fallacy in solo dev
6. **Success Theater Detection** - Common software anti-pattern
7. **Pre-Mortem Re-Mortem Cycle** - Learning loop from actual failures
9. **Second-Order Success** - Scaling breaks optimizations
10. **Stakeholder Blind Spot** - Solo dev lacks team perspectives

### ❌ FILTER OUT (4 enhancements) - Not relevant or duplicate

2. **FMEA Integration** - Over-engineering; current L×I scoring is sufficient
3. **"Premortem" Bias Detection** - Team dynamics issue; solo dev doesn't have this problem
5. **Black Swan Analysis** - Edge case; rare catastrophes not our daily risk
8. **Outside View Reference Class Tuning** - DUPLICATE; already exists as Step 3.5

---

## Prioritization of 6 Relevant Enhancements

### Tier 1: Implement Immediately (High ROI, Low Complexity)

**1. AI/LLM-Specific Failure Modes** ⭐ **HIGHEST PRIORITY**
- **Why**: Our workflow IS AI/LLM-augmented - this is daily reality
- **Evidence**: Skill pattern gate bug was exactly this type of failure
- **Effort**: 2-3 hours
- **Impact**: Prevents repeat of recent bugs

**2. Success Theater Detection**
- **Why**: Complements Step 3.8 (Operational Verification)
- **Evidence**: "Tests pass but system broken" is common
- **Effort**: 1-2 hours
- **Impact**: Prevents false confidence

**3. Kill Criteria**
- **Why**: Prevents sunk cost fallacy in solo dev
- **Evidence**: Solo devs susceptible to "keep going" trap
- **Effort**: 1 hour
- **Impact**: Stops zombie projects

**Tier 1 Total: 4-6 hours**

---

### Tier 2: Consider After Tier 1 Validation

**4. Second-Order Success**
- **Why**: Optimizations that work for solo dev break at scale
- **Evidence**: Solo → team patterns often fail
- **Effort**: 1-2 hours
- **Impact**: Prevents scaling failures

**5. Stakeholder Blind Spot**
- **Why**: Current personas (Engineer, DevOps) miss key perspectives
- **Evidence**: Solo dev lacks team perspective by design
- **Effort**: 2-3 hours
- **Impact**: Broadens risk coverage

**6. Pre-Mortem Re-Mortem**
- **Why**: Learning loop from actual failures
- **Evidence**: We learn from bugs we find in workflow
- **Effort**: 2-3 hours
- **Impact**: Continuous improvement

**Tier 2 Total: 5-8 hours**

---

## Filtered Out Enhancements (Why Not Relevant)

### 2. FMEA Integration - ❌ OVER-ENGINEERING

**What it is**: Systematic engineering approach (Severity × Occurrence × Detection)

**Why filtered out:**
- Current L×I scoring (Likelihood × Impact) is sufficient for our use case
- FMEA adds complexity without proportional value
- Standard in automotive/aerospace but overkill for solo dev projects

**Evidence**: Pre-mortem v3.6 already has quantitative scoring; adding RPN (Risk Priority Number) would be redundant.

---

### 3. "Premortem" Bias Detection - ❌ NOT RELEVANT

**What it is**: Psychological safety check for team environments

**Why filtered out:**
- Research (2023-2024) shows TEAMS avoid pre-mortems due to negativity/politics
- Solo dev doesn't have team dynamics or political concerns
- We're already doing pre-mortems - bias not an issue

**Evidence**: User runs pre-mortems voluntarily; no resistance detected.

---

### 5. Black Swan Analysis - ❌ EDGE CASE

**What it is**: Analysis of rare catastrophes (10x events, market crashes)

**Why filtered out:**
- Rare catastrophes not our daily risk
- Solo dev projects unlikely to experience black swans
- Time better spent on common failure modes

**Evidence**: No black swan events in our workflow history; all failures were foreseeable.

---

### 8. Outside View Reference Class Tuning - ❌ DUPLICATE

**What it is**: Kahneman's technique for using historical base rates

**Why filtered out:**
- Already implemented as Step 3.5 (Reference Class Forecasting)
- Adding duplicate would be confusing

**Evidence**: SKILL.md already has "Reference Class: Similar solo dev CLI tools" with base rate extraction.

---

## Decision Options

### Option A: Implement Tier 1 (RECOMMENDED)

**Pro:** Immediate value for daily workflow
**Pro:** Low effort (4-6 hours)
**Pro:** Addresses domain-specific gap (AI/LLM workflows)
**Pro:** Each enhancement can be removed independently if needed
**Con:** Doesn't include Tier 2 enhancements
**Con:** May need Tier 2 enhancements later
**Differs on:** Targeted vs. comprehensive approach

### Option B: Implement All 6 Relevant Enhancements

**Pro:** Comprehensive coverage of relevant risks
**Pro**: Future-proofs for broader use cases
**Con:** Significant effort (9-14 hours)
**Con**: Tier 2 value unproven in our workflow
**Differs on:** Comprehensive vs. incremental approach

### Option C: No Changes (Status Quo)

**Pro:** v3.6 is already excellent
**Pro:** Zero implementation effort
**Con:** Continued blindness to AI/LLM-specific failures
**Con:** Repeat of skill pattern gate bug type
**Differs on:** Stagnation vs. evolution

---

## Recommendation

**Option A (Tier 1 only)** is recommended because:

1. **Immediate ROI**: All 3 Tier 1 enhancements address daily workflow risks
2. **Evidence-based**: Skill pattern gate bug proves AI/LLM gap is real
3. **Low risk**: Each enhancement is additive and independently removable
4. **Validate first**: Implement Tier 1, validate value, then consider Tier 2
5. **Properly filtered**: Removed 4 irrelevant enhancements (FMEA, Bias, Black Swan, Outside View duplicate)

**Implementation order:**
1. **AI/LLM Failure Modes** (2-3 hours) - DO THIS FIRST
2. **Success Theater Detection** (1-2 hours) - DO SECOND
3. **Kill Criteria** (1 hour) - DO THIRD

**Validation plan:**
- Week 1: Implement all Tier 1 enhancements
- Week 2: Use with real workflow bugs
- Week 3: Assess value, decide on Tier 2

---

## 5. Quick Ramifications

- **Breaks anything?** No - all changes are additive
- **Edge cases?** Non-AI workflows skip Step 2.6
- **Constraints?** Adds ~3KB to SKILL.md, +30-60 seconds per pre-mortem

---

## 6. Confidence

**Confidence: 95%** — Based on:
- **Proper filtering**: Removed 4 irrelevant enhancements (over-engineering, team issues, edge cases, duplicates)
- **Direct evidence**: Skill pattern gate bug proves AI/LLM gap is real
- **High relevance**: All 6 kept enhancements address solo dev AI/LLM workflow risks
- **Low risk**: Tier 1 enhancements are additive, independently removable

**Weakest assumption**: Tier 1 enhancements will provide sufficient value. If wrong: May need Tier 2 enhancements (Second-Order Success, Stakeholder Blind Spot, Re-Mortem Cycle). Mitigation: Weekly value assessment during validation period.

---

## 7. Implementation Timeline

**Week 1: Implementation**
- Day 1-2: AI/LLM Failure Modes (Step 2.6)
- Day 3: Success Theater Detection (Step 3.6)
- Day 4: Kill Criteria (Step 0.7)
- Day 5: Integration testing

**Week 2: Validation**
- Use enhanced pre-mortem on real workflow bugs
- Assess value of each enhancement
- Document findings

**Week 3: Decision Point**
- If Tier 1 valuable → Consider Tier 2
- If Tier 1 insufficient → Re-evaluate approach
- If Tier 1 successful → Standardize as v3.7

---

## 8. Tier 2 Considerations (Deferred)

Implement **after** Tier 1 validation:

**Second-Order Success** (1-2 hours)
- Addresses: "Optimization worked for solo dev, breaks for teams"
- Add after Step 2.5 (Second-Order Effects)
- Trigger: If scaling issues emerge

**Stakeholder Blind Spot** (2-3 hours)
- Addresses: Missing perspectives in solo dev
- Add new personas: End User, Maintainer
- Trigger: If stakeholder gaps identified

**Pre-Mortem Re-Mortem** (2-3 hours)
- Addresses: Learning loop from actual failures
- Add Step 7: "Review actual failure vs. predicted"
- Trigger: After first major bug in enhanced workflow

---

## 9. Summary

**Implement**: 6 relevant enhancements (3 immediate, 3 deferred)
**Filter out**: 4 irrelevant enhancements (over-engineering, team issues, edge cases, duplicates)
**Total effort**: Tier 1 (4-6 hours) + Tier 2 (5-8 hours if needed)

---

**Auto-saved to:** `P:\.claude\arch_decisions\2026-03-06_pre-mortem_enhancements.md`
