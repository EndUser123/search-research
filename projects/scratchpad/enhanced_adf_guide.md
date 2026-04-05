# Enhanced Architecture Decision Framework (ADF)

Complete guide to evaluating structural code changes before implementation in Claude Code.

## Overview

The Architecture Decision Framework (ADF) is a systematic approach to evaluating whether proposed structural code changes are justified before implementation. It prevents over-engineering and unnecessary abstractions.

**Trigger Phrases:** "should I extract", "should this be separate", "new service", "new module", "add abstraction", "split this into", "refactor this", "reorganize"

**Response Format:** All ADF responses are prefixed with `[ADF]` to indicate the framework is active.

---

## Step 0 — Scope Check

First, determine if ADF is the right framework:

| Proposal Type | ADF Applies? | Action |
|---------------|--------------|--------|
| Extract/split/separate code | ✅ Yes | Continue to Step 1 |
| Add abstraction layer | ✅ Yes | Continue to Step 1 |
| Share existing capabilities | ❌ No | Evaluate as integration |
| Remove/consolidate code | ❌ No | Reduces complexity, proceed |

**Key Question:** Does this proposal ADD new boundaries/abstractions, or does it SHARE/REUSE existing ones?

---

## Step 1 — Clarify the Proposal

Ask the user:
1. What exact change is proposed?
2. What problem are you trying to solve?
3. What breaks if this change is NOT done?

If the user cannot provide a concrete problem or failure mode, recommend NOT doing the change.

---

## Step 2 — Problem Check (Evidence-Based)

**Evidence Collection Required:**
1. Execute current system with representative test cases
2. Document concrete failures or mismatches
3. Measure impact with specific metrics
4. Verify claims with actual execution results

**Tier 2 Evidence Sources:**
- System execution showing failures
- Real project examples with problems
- Metrics showing measurable impact
- Constitutional compliance gaps

**Vague justifications that require evidence:**
- "Better organization"
- "Cleaner code"
- "Future-proofing"
- "Best practice"

---

## Step 3 — Simpler Alternative

Check for the simplest viable option:
- Single function in existing file vs new service
- Adding to existing module vs new layer
- Waiting until problem observed more than once

---

## Step 4 — Complexity Tax

Calculate the complexity cost:

| Factor | Points |
|--------|--------|
| New file | +1 |
| New concept | +2 |
| New failure mode | +3 |
| New integration test | +2 |

**Threshold:**
- `tax ≤ 5` → Can proceed with basic evidence
- `tax > 5` → Requires Tier 2+ evidence (system execution, metrics)

**Example:**
```
Extracting auth service:
- 3 new files: +3
- 1 new concept (service abstraction): +2
- 1 new test: +2
Total: 7 (requires Tier 2+ evidence)
```

---

## Step 5 — Boundary Stability

Ask: How stable are requirements for this area over 6–12 months?

- **Stable** → Extraction safer
- **Volatile** → Keep together, revisit later

---

## Step 6 — Stop Signals

| Signal | Evidence Required | Decision |
|--------|------------------|----------|
| "Better organization" | Show concrete problems | Block if no evidence |
| "Best practice" | Show violation of standards | Block if no risk shown |
| "Future-proofing" | Show concrete future scenarios | Block if not specific |
| "Optimization" | Show suboptimal performance with metrics | Allow if measured |

**Allowable without additional evidence:**
- Constitutional compliance failures
- Measurable performance problems
- Duplicated fixes causing recurring bugs
- Measurably hard to test current code

---

## Step 7 — Output Format

For significant changes (tax > 5):

```
[ADF] Analysis

**Change:** [Proposed structural change]
**Problem:** [Concrete problem being addressed]
**Complexity tax:** [Score + breakdown]
**Evidence tier:** [Tier + source]
**Recommendation:** [Proceed / Simplify / Defer / Do not proceed]
```

---

## Step 8 — Execution Handoff

| Recommendation | Action |
|----------------|--------|
| **Proceed** (tax ≤ 5) | Execute immediately |
| **Proceed** (tax > 5) | Ask user confirmation first |
| **Simplify** | Propose simpler alternative |
| **Defer** | Explain conditions to revisit |
| **Do not proceed** | Explain why, suggest alternatives |

---

## Step 9 — SOLID Principles Check

After structural approval, validate the design against SOLID principles:

### S — Single Responsibility Principle
- **Question:** Does each module/class/function have ONE reason to change?
- **Violation signs:** "God object", multiple concerns, changing for unrelated reasons
- **Check:** "If X changes, do I also need to change Y for unrelated reasons?"

### O — Open/Closed Principle
- **Question:** Is code open for extension but closed for modification?
- **Violation signs:** `if type == X` everywhere, modifying to add features
- **Check:** "Can I add new behavior without touching existing working code?"

### L — Liskov Substitution Principle
- **Question:** Can subtypes replace base types without breaking correctness?
- **Violation signs:** `NotImplementedError` in subclasses, restrictive subtypes
- **Check:** "If I replace Parent with Child, does everything still work?"

### I — Interface Segregation Principle
- **Question:** Do clients depend only on methods they actually use?
- **Violation signs:** Fat interfaces (10+ methods), "do-nothing" implementations
- **Check:** "Are implementations forced to provide methods they don't need?"

### D — Dependency Inversion Principle
- **Question:** Do high-level modules depend on abstractions, not concretions?
- **Violation signs:** `new ConcreteClass()` in business logic, tight coupling
- **Check:** "Can I swap implementations without changing high-level code?"

### SOLID Violation Detection Table

| Code Smell | SOLID Violation | Refactoring Suggestion |
|------------|-----------------|----------------------|
| One class does everything | SRP | Extract responsibilities |
| `if type == X: ...` everywhere | OCP | Use polymorphism/strategy |
| `NotImplementedError` in subclass | LSP | Use composition instead |
| Interface with 10+ methods | ISP | Split into focused interfaces |
| `new ConcreteClass()` in logic | DIP | Inject via interface/abstract |

### When SOLID Doesn't Apply

| Situation | Override |
|-----------|----------|
| Simple scripts < 100 lines | YAGNI > SOLID |
| One-off data processing | Pragmatism > purity |
| Performance-critical paths | Duplication may be faster |
| Solo project, stable requirements | Simplicity > abstraction |

---

## Additional Quality Principles

### DRY — Don't Repeat Yourself
- **Rule:** Each piece of knowledge has a single, unambiguous representation
- **Violation:** Same logic in 3+ places = extract
- **Exception:** Duplicating to separate concerns is OK

### KISS — Keep It Simple, Stupid
- **Rule:** Maximize readability, minimize cleverness
- **Check:** "Would I understand this 6 months from now?"

### YAGNI — You Aren't Gonna Need It
- **Rule:** Don't build for hypothetical future requirements
- **Check:** "Is there a concrete need TODAY?"

---

## Quick Decision Tree

1. Collect evidence before blocking
2. Concrete failure prevented? No → **Don't change**
3. Constitutional compliance gaps? Yes → **Proceed with high priority**
4. Simpler fix works? Yes → **Use simpler option**
5. Complexity tax > 5? Yes → **Require Tier 2+ evidence**
6. Boundary stable 6–12 months? No → **Defer**
7. Aesthetics without evidence? Yes → **Block**
8. SOLID violations? Yes → **Refactor before proceeding**
9. Otherwise → **Proceed with structured output**

---

## Examples

### Justified Change
```
Change: Extract auth into dedicated service
Problem: Auth duplicated across 4 repos, changes require 4 PRs
Complexity tax: 7 (3 files, 1 concept, 1 test)
Evidence: Tier 2 — multiple incidents, coordination overhead
Recommendation: Proceed
```

### Unjustified Change
```
Change: Split utils into three services
Problem: "Better organized"
Recommendation: Do not proceed — no concrete problem
```

---

## Anti-Satisficing Check

When recommending "Simplify" or reduced scope, must list:
1. What useful content/features are NOT included
2. Classification of exclusion reason
3. Value estimate (HIGH/MEDIUM/LOW)
4. User confirmation for HIGH-value exclusions

**Constitutional prohibition:** Recommending "minimal" without listing what's excluded.

---

*This is the enhanced Architecture Decision Framework (ADF) used in Claude Code skills for evaluating structural code changes.*
*Last updated: December 2024*
