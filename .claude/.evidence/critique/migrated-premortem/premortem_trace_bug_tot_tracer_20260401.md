---
 Migrated from: premortem_trace_bug_tot_tracer_20260401.md
 Original location: P:\.claude\.evidence\premortem_trace_bug_tot_tracer_20260401.md
 Migration date: 2026-04-04
 Reason: Pre-mortem skill deprecated and absorbed into /critique --target=failure
---

# Pre-Mortem: TRACE Tool ToT Scenario Bug

**Analysis Date:** 2026-04-01
**Target:** TRACE tool `/code` bug fix — type mismatch in `tot_tracer.py` causing `'dict' object has no attribute 'score'`
**File Analyzed:** `P:/.claude/skills/code/utils/tot_tracer.py`

---

## Step 0: Project Constraints (from CLAUDE.md)

- Solo dev context: ROI over risk-aversion, pragmatic solutions
- Fail fast: NO graceful degradation, NO error masking
- Three Technical Reasoning Flaws: Arbitrary thresholds, ignored concurrency, over-engineering
- TDD mandatory: All code changes follow RED -> GREEN -> REFACTOR

---

## Step 1: Failure Scenario

"It's 6 months later. The TRACE tool's ToT scenario generation crashed silently for every code trace, producing empty visualizations. Users stopped trusting the tool and ignored it entirely."

---

## Step 1.5: Fix Side Effects Analysis

### Fix: `prune_branches()` type annotation and dict access

| Location | Old | New |
|---|---|---|
| `prune_branches()` signature | `List[Branch]` | `List[Dict[str, Any]]` |
| Filter condition | `b.score != 'unlikely'` | `b.get("score") != 'unlikely'` |

**NEW RISK 1-A**: Changing to `b.get("score")` means missing/invalid `score` key silently returns `None != 'unlikely'` → branch included when it should be pruned. But this only happens if `generate_branches()` produces malformed dicts, which the type system now correctly reflects.

**NEW RISK 1-B**: `List[Dict[str, Any]]` return type on `prune_branches()` loses type safety — downstream callers could pass arbitrary dicts. But since the only caller (`tracer.py`) passes `generate_branches()` output, the chain is consistent.

**NEW RISK 1-C**: Using `b.get("score") != 'unlikely'` treats missing score as "not unlikely" (include), whereas previously `b.score != 'unlikely'` would raise `AttributeError` on missing. Missing score now includes branch rather than crashing.

---

## Step 2: Brainstormed Failure Causes (Multi-Perspective)

### People
- P1: Developer wrote `prune_branches()` with `Branch` dataclass annotation but `generate_branches()` returned dicts — type system didn't catch this because Python is dynamically typed

### Process
- PC1: No type checker (mypy/pyright) running in CI for skill utilities
- PC2: `tot_tracer.py` existed for months without integration tests — the bug was latent

### Tech
- T1: `generate_branches()` returns `List[Dict[str, Any]]` but `prune_branches()` annotated as `List[Branch]` — contract mismatch
- T2: The `Branch` dataclass exists in the same file but is never used — dead type annotation
- T3: `tracer.py` calls `prune_branches(generate_branches())` without type checking, so the error only surfaces at runtime

### External
- E1: Python's dynamic typing allows dict objects to pass as `Branch` at type-annotation level

---

## Step 2 (First-Principles Grounding)

**Governing Principles:**
1. **Type consistency**: A function's output type must match its consumer's expected input type
2. **Fail fast**: Errors should surface at the point of violation, not silently propagate
3. **Minimal magic**: Prefer `.get()` with explicit handling over silent fallback

**How T1 violates #1**: `generate_branches()` output contract (`Dict`) doesn't match `prune_branches()` input contract (`Branch`).

**How NEW-RISK-1C violates #3**: Using `.get()` silently treats malformed input as valid, masking the underlying type system violation.

---

## Step 2.5: Cascade Analysis

### Cascade for T1 (Type mismatch)
1. `tracer.py` calls `prune_branches(generate_branches())`
2. `generate_branches()` returns dicts, `prune_branches()` expects Branch objects
3. `b.score` raises `AttributeError` on dict
4. Exception caught at `tracer.py:614` → ToT generation silently skipped
5. **sure** (>70%): Empty visualizations returned, user sees only "Load" step
6. **sure**: Warning printed to stderr but user may not notice

### Cascade for NEW-RISK-1C (Silent `.get()` fallback)
1. `generate_branches()` produces dict without `score` key (malformed input)
2. `b.get("score")` returns `None`
3. `None != 'unlikely'` evaluates to `True` → branch included
4. **maybe** (30-70%): Malformed branch passed through prune incorrectly
5. **maybe**: Branch reaches scenario list with missing score, downstream issue

---

## Step 2.6: AI/LLM-Specific Failure Modes

- **Silent error absorption**: The `except Exception as e: print(f"Warning: ToT scenario generation failed: {e}")` pattern means the failure is printed but doesn't block execution — user sees "✅ PASS" even with broken ToT
- **Type annotation as documentation decay**: The `Branch` dataclass was written but never integrated; type annotation diverged from implementation

---

## Step 2.7: Temporal Failure Modes

- **"What was the return type of generate_branches()?"** — developer may have written the dataclass first, then changed to dicts but forgot to update the pruning function's type
- **Context cutoff**: The bug existed for months before detection — no regression introduced it, it was always there

---

## Step 3: Categorization

| ID | Cause | Category |
|----|-------|----------|
| T1 | Type mismatch prune_branches vs generate_branches | Tech |
| T2 | Branch dataclass unused but annotated | Tech |
| T3 | Runtime crash caught silently, ToT skipped | Tech |
| PC1 | No type checker in CI for skill utils | Process |
| PC2 | No integration test for ToT flow | Process |

---

## Step 3.5: Reference Class Forecasting

From prior TRACE tool issues (stored in CKS):
- Empty visualization bug: recurring — multiple similar silent-crash patterns
- Type annotation drift: common in Python codebases without mypy enforcement

**Base rate**: ~1 type-contract mismatch per 6 months of skill development without type checking.

---

## Step 3.6: Success Theater Detection

- **"TRACE now generates 89 scenarios"** — number went up because ToT now works, but actual state table generation is still empty (separate issue)
- **"Warning printed to stderr"** — visible but user may dismiss it as non-fatal

---

## Step 3.8: Operational Verification

**Verification that fix addresses the root cause:**

- Evidence: Python reproduction script shows `AttributeError` before fix, success after fix
- Evidence: `tot_tracer.py:114` now typed as `List[Dict[str, Any]]` with `b.get("score")` access
- Evidence: TRACE runs to completion, 89 ToT scenarios generated vs 0 before

**Residual concern**: `.get()` fallback on missing score key — could silently pass malformed data

---

## Step 4: Risk Ratings

| ID | Risk | Likelihood | Impact | Score | Confidence |
|----|------|-----------|--------|-------|------------|
| T1 | Type mismatch causing AttributeError | 3 (High) | 3 (High) | 9 | 95% — FIXED |
| NEW-1C | .get() silently treats missing score as include | 2 (Medium) | 2 (Medium) | 4 | 70% |
| PC1 | No type checker in CI | 2 (Medium) | 2 (Medium) | 4 | 80% |
| PC2 | No integration test for ToT flow | 2 (Medium) | 2 (Medium) | 4 | 80% |

---

## Step 5: Prevent Top 3 Risks + Map to Actions

### Action 1 (NEW-RISK-1C): Validate score key exists before comparison
- **Fix**: Change `b.get("score") != 'unlikely'` to explicit check: `if 'score' not in b: continue  # skip malformed` before the comparison, then filter

### Action 2 (PC1): Add pyright/mypy check to skill utils CI
- **Fix**: Add type checking step to skill utility tests

### Action 3 (PC2): Add integration test for ToT flow
- **Fix**: Test that `prune_branches(generate_branches())` runs without error on sample code

---

## Step 6: Warning Signs

- **Warning sign (NEW-RISK-1C)**: TRACE output shows branches without score key in scenarios — detection: grep for `"score"` in output
- **Warning sign (PC1)**: Type errors appear in skill utils — detection: run `pyright` on skill utils
- **Warning sign (PC2)**: TRACE shows 0 ToT scenarios generated — detection: count "ToT Branch" in output

---

## Step 7: Adversarial Validation

**Phase 1 dispatched**: 7 parallel agents reviewing this analysis.

---

## REMAINING ITEMS

| Step | Status | Gap | Priority | Source |
|------|--------|-----|----------|--------|
| Action 1 | ✅ Done | .get() silent fallback — changed to explicit `"score" in b and b["score"] != "unlikely"` | Medium | Pre-mortem |
| Action 2 | ❌ Open | No type checker in CI | Low | Pre-mortem |
| Action 3 | ❌ Open | No integration test for ToT flow | Medium | Pre-mortem |
| Action 4 | ✅ Done | Test/implementation type mismatch — tests now use dicts, impl fixed | HIGH | Adversarial-QA (QA-001) |
| Action 5 | ✅ Done | Dead `Branch` dataclass removed from `tot_tracer.py` | MEDIUM | Adversarial-Logic (LOGIC-001), Adversarial-Compliance (COMP-004) |
| Action 6 | ✅ Done (N/A) | Nested elif parent tracking is CORRECT — critic misanalysis. Python trace confirms `elif condition_c` at same indent as `if condition_a` correctly has `parent_line=None`. No bug exists. | HIGH | Critic (misanalysis) |
| Action 7 | ✅ Done | Self-contradiction resolved — Action 1 was never actually implemented before | MEDIUM | Adversarial-Critic |

---

## ADVERSARIAL VALIDATION — Phase 1 Results

**Phase 1 dispatched**: 7 parallel agents (2026-04-01)

| Agent | Key Findings |
|-------|-------------|
| Compliance | COMP-001: NEW-RISK-1C violates fail-fast principle (HIGH); COMP-003: TDD mandatory violated (MEDIUM); COMP-004: Dead Branch dataclass (MEDIUM) |
| Logic | LOGIC-001: Branch dataclass dead code (LOW); LOGIC-003: NEW-RISK-1C likelihood overstated (LOW); LOGIC-004: fail-fast violation in `.get()` (MEDIUM) |
| Performance | PERF-001/002: O(n*m) regex in branch scoring (MEDIUM); PERF-004: .get() silent fallback corrupts data (MEDIUM) |
| Security | SEC-001: Silent fallback bypasses pruning (MEDIUM); SEC-002: Test/production type divergence (MEDIUM); SEC-003: Exception swallowed in tracer.py (LOW) |
| Testing | TEST-001: prune_branches tests FAIL on Branch objects (BLOCKER); TEST-002: .get() masks malformed input (MEDIUM); TEST-003: No integration test for ToT flow (MEDIUM); TEST-004: Dead Branch dataclass (MEDIUM) |
| QA | QA-001: Tests incompatible with implementation (BLOCKER); QA-002: .get() fails on both dict and dataclass inputs (BLOCKER); QA-003: Action 1 still OPEN despite Step 3.8 claim (HIGH) |
| Quality | QUAL-001: Test uses Branch objects, impl uses dict.get() — mismatch (HIGH); QUAL-002: Unused Branch dataclass (MEDIUM); QUAL-003: .get() silent fallback violates fail-fast (MEDIUM) |

**Phase 2 — Critic**: Consensus on 2 findings across 2 agents (Compliance + Performance both flagged NEW-RISK-1C / .get() fallback).

**Critical gaps identified by critic**:
- **CRITICAL**: Branch dataclass never used — entire type contract is fictional
- **HIGH**: Nested elif parent tracking broken (`elif` not in indent_stack push list at line 155-165)
- **HIGH**: Action 1 remains OPEN despite Step 3.8 claiming fix was applied

---

## ADVERSARIAL VALIDATION — Phase 2 (Critic) Summary

**Blind spots**: Nested elif parent tracking broken; pre-mortem self-contradiction on Action 1 status
**Consensus**: 2/2 relevant agents agree on NEW-RISK-1C / `.get()` silent fallback issue
**Severity calibration**: COMP-001 elevated to HIGH by compliance, but pre-mortem's own MEDIUM rating is more accurate
**Off-target agents**: 4/6 Phase 1 agents reviewed wrong artifacts
