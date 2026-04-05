# Pre-Mortem: /verify Post-Hoc RTM Fix

**Date:** 2026-03-30
**Target:** `post_hoc_analyzer.py generate_rtm()` + `test_integration_post_hoc.py` weight fix
**Trigger:** Broken import `PlanVisualizer` from non-existent path; stale test weight expectations

---

## Step 0: Constraints (from CLAUDE.md)

- Evidence-first: verify complete before claiming success
- Fail fast: surface problems immediately
- Truthfulness > agreement
- 75-85% reliability target (solo dev)
- Test-driven pattern development: test corpus first, then modify
- Reversibility trivial (1.0-1.25): direct proceed

---

## Step 0.7: Kill Criteria

- If `extract_requirements()` or `extract_tasks()` diverge from expected schema → RTM silently produces wrong output
- If plan format changes → keyword overlap mapping silently breaks
- If weights change again → no mechanism to detect (test already wrong once)

---

## Step 1: Failure Scenario

**"It's 6 months later and the /verify post-hoc RTM analysis is producing silently wrong coverage percentages, causing the system to either falsely PASS incomplete work or fail work that's actually complete."**

---

## Step 1.5: Fix Side Effects (NEW Risks)

### Fix 1: Import `/planning/__lib/auto_verify.py` functions directly
- **NEW RISK:** Tight coupling to `/planning` skill internals. If `extract_requirements()` or `extract_tasks()` change output schema, `generate_rtm()` silently produces wrong data.
- **NEW RISK:** `/planning/__lib/` is a private module (`__lib` naming convention). No semver stability guarantee.

### Fix 2: Keyword-overlap coverage matrix
- **NEW RISK:** If two requirements share keywords but aren't actually addressed by the same task, false positive mapping.
- **NEW RISK:** If a requirement is detailed (many keywords) but task is terse (few keywords), lower overlap probability → false negative mapping.
- **NEW RISK:** No handling of negation ("not implement X" vs "implement X" could map incorrectly).

### Fix 3: Updated test weights (30/50/20 → 25/45/20/10)
- **NEW RISK:** No enforced contract between `evaluate_conversation_completeness()` weights and test expectations. Future refactor could silently diverge again.

---

## Step 2: Brainstormed Failure Causes

### People
- P1: Original developer placed `PlanVisualizer` at non-existent path — no discovery that `/planning` already had equivalent functionality
- P2: The `/planning` team (past self) refactored `PlanVisualizer` out but didn't update the reference in `/verify`
- P3: No one reviewed the broken import path before it was committed

### Process
- T1: No pre-commit or CI check that imports actually resolve in `post_hoc_analyzer.py`
- T2: No enforced rule that `/planning` internal modules shouldn't be imported directly by other skills
- T3: Test weight expectations (30/50/20) were never updated when scoring function changed from 3-component to 4-component
- T4: No integration test that actually ran the full `run_analysis()` with real plan + evidence before this session

### Tech
- T5: `generate_rtm()` had a dead import path — `P:/.claude/skills/plan-workflow/lib/plan_visualizer.py` never existed
- T6: Keyword-overlap algorithm is fragile: short requirements or tasks with acronyms may not map correctly
- T7: `extract_tasks()` detection of acceptance criteria requires specific `**Acceptance**:` header format — any format variation silently returns False
- T8: No schema validation between `generate_rtm()` output and `evaluate_conversation_completeness()` input

### External
- E1: If `/planning` skill updates `auto_verify.py` to change output format, `/verify` RTM breaks silently
- E2: Plan format conventions (what `extract_requirements()` and `extract_tasks()` expect) are undocumented outside the code

---

## Step 2.5: Cascade Analysis (risks ≥ 6)

### Risk T6 (score 6): Keyword-overlap fragility
1. Requirement has many technical keywords, task is brief
2. Overlap detection misses → orphan requirement flagged
3. Overall score drops → work incorrectly fails verification

### Risk T7 (score 6): Acceptance criteria format detection
1. Task has acceptance criteria but uses different header format (e.g., `**验收标准**:` or `**Criteria**:`)
2. `has_acceptance_criteria` returns False
3. Evidence quality score drops to 0 → overall score fails threshold

### Risk P1+T3 (score 7): Silent schema divergence
1. `/planning` updates `extract_tasks()` to change `has_acceptance_criteria` key
2. `generate_rtm()` silently produces different structure
3. `evaluate_conversation_completeness()` reads old key → returns 0
4. All post-hoc verifications fail until someone reads both files

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Context overflow**: Long plan with many requirements → keyword extraction overflows token budget (not likely — plan parsing is local)
- **Handoff knowledge loss**: The broken import path was never explained — future maintainer sees dead code and doesn't know it was intentional refactor remnant
- **Pattern misapplication**: Keyword overlap is a heuristic; LLM may over-trust it as "correct" mapping without empirical verification

---

## Step 2.7: Temporal Failure Modes

- **Context truncated**: If session is compacted mid-analysis of RTM, the insight that `/planning` has equivalent functionality might not persist
- **"What was the requirement again?"**: After session ends, no documentation of WHY `PlanVisualizer` was replaced vs fixed

---

## Step 3: Categorization

| ID | Category | Root Cause |
|----|----------|-----------|
| P1 | People | Dead import path not caught in review |
| P2 | Process | No cross-skill import governance |
| T3 | Process | Test weights diverged from implementation |
| T5 | Tech | Import path never validated |
| T6 | Tech | Keyword-overlap is fragile heuristic |
| T7 | Tech | Acceptance criteria format requirement undocumented |
| T8 | Tech | No schema validation between RTM and evaluation |
| E1 | External | `/planning` internal module used without contract |

---

## Step 3.5: Reference Class Forecasting

Similar past failures in this codebase:
- `debugRCA` skill renamed to `rca` with many dead imports (evidenced by git history showing `packages/debugRCA/` → `packages/rca/`)
- Skill import paths broken after plugin migrations (documented in `plugin_migration_imports.md`)

Base rate: ~30% of refactored skills leave dead import references.

---

## Step 3.6: Success Theater Detection

- "All 119 tests pass" is a real metric but tests only validate the fix path, not the original failure mode
- The original broken import (`PlanVisualizer`) would have been caught by running pytest once — yet it shipped
- Test weight fix was a one-off; no mechanism prevents it happening again

---

## Step 3.8: Operational Verification

- **Empirical check ran**: `pytest tests/test_integration_post_hoc.py tests/test_post_hoc.py` → 20 passed
- **Full suite**: `pytest tests/` → 119 passed, 1 skipped
- **Pre-existing test was broken**: Original code threw `ImportError` before reaching scoring — test never validated weights correctly
- **Evidence**: pytest output shows 0.30s for post-hoc tests, 13.24s full suite

---

## Step 4: Risk Ratings

| ID | Risk | L | I | Score |
|----|------|---|---|-------|
| E1 | `/planning` internal module change breaks RTM | 3 | 3 | **9** |
| T8 | No schema validation → silent wrong scores | 2 | 3 | **6** |
| T6 | Keyword-overlap fragility → wrong mappings | 2 | 3 | **6** |
| T7 | Acceptance criteria format change → 0 evidence quality | 2 | 3 | **6** |
| P1 | Dead import path not caught in review | 2 | 2 | **4** |
| T3 | Test weights diverged, no enforcement | 2 | 2 | **4** |
| T5 | Import path never validated at runtime | 1 | 3 | **3** |
| P2 | Cross-skill import governance gap | 1 | 2 | **2** |

---

## Step 5: Prevent Top 3

### 1 (E1): Add schema assertion between RTM and evaluation
**Evidence**: `post_hoc_analyzer.py:386` reads `statistics.get("tasks_with_acceptance_criteria")` — if key missing, returns 0 silently.
**Action**: Add assertion in `generate_rtm()` that output dict keys match what `evaluate_conversation_completeness()` expects.

### 2 (T6+T7): Document keyword-overlap limitations and acceptance criteria format
**Evidence**: `auto_verify.py:239` requires `\*\*[^*]+\*\*:` pattern for acceptance header — undocumented contract.
**Action**: Add inline comments in `generate_rtm()` explaining the keyword-overlap assumption and the acceptance criteria detection dependency on `extract_tasks()` format.

### 3 (T3): Add weight-coverage test that validates the weighted score formula
**Evidence**: `test_integration_post_hoc.py:467` had wrong weights for 9+ months.
**Action**: Add a test that explicitly checks the weighted score formula matches expected weights, with weights as constants defined in one place.

---

## Step 6: Warning Signs to Monitor

- RTM shows 0% or 100% requirement coverage with no middle ground (keyword-overlap boundary case)
- Post-hoc verification passes/fails for wrong reasons (symptom of T6/T7 fragility)
- `import` errors in `post_hoc_analyzer.py` after `/planning` skill updates
- pytest in `/verify` passes but `/planning` tests fail (schema divergence)

---

## REMAINING ITEMS

| Step | Status | Gap | Priority |
|------|--------|-----|----------|
| 5 (E1) | ❌ Open | Schema assertion not implemented | Medium |
| 5 (T6+T7) | ❌ Open | Inline comments on keyword-overlap limitations | Low |
| 5 (T3) | ❌ Open | Weight-coverage validation test | Medium |
