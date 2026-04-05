# Plan: Convention Fabrication Gate

**Created:** 2026-03-16
**Objective:** Stop Claude from inventing organizational conventions/policies as confident claims by (1) wiring the existing hypothesis-as-fact gate into the Stop router, (2) adding a CONVENTION claim type with no hedge bypass, and (3) adding a grounded-claims constraint to GTO.

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — Wire gate into Stop_router.py | ✅ COMPLETE | HOOK_SEQUENCE + ACTIVE_RUNTIME_HOOKS updated |
| Phase 2 — Add CONVENTION claim type | ✅ COMPLETE | detector + gate + 12 tests passing |
| Phase 3 — GTO SKILL.md grounded-claims constraint | ✅ COMPLETE | GROUNDED CLAIMS ONLY rule added |

---

## Problem Statement

Claude fabricates organizational conventions and project-specific policies without grounding in observed tool output. Example from this session: "Skip if micro-fix policy applies — many hook fixes go undocumented; your call." No such policy exists anywhere in this codebase. The phrase was invented.

**Why hedged conventions are the blind spot:**
- `HypothesisAsFactDetector` has a `has_hedge` bypass — if a sentence contains "typically", "usually", or "often", the claim is marked hedged and bypasses blocking regardless of content.
- Convention fabrications exploit this: "Hooks often go undocumented" sounds like a reasonable hedge but the underlying claim is invented.
- `Stop_hypothesis_as_fact_gate.py` exists and is fully functional internally, but is NOT in the live HOOK_SEQUENCE in `Stop_router.py` (built in a prior task, never wired).
- GTO SKILL.md output rules have no explicit grounded-claims constraint.

**Root cause chain:**
1. Gate exists but is not wired → no enforcement at all
2. Hedge bypass in `_should_block_claim()` would exempt convention fabrications even when wired
3. GTO skill output has no explicit grounded-claims rule

**Test coverage requirement:** All three changes require test coverage to prevent regression.
TASK-005 covers: CONVENTION detection, no-hedge-bypass behavior, and gate wiring.
TASK-006 provides regression protection over all existing gate and detector tests.

---

## Context Analysis

**Files involved:**
- `P:/.claude/hooks/Stop_router.py` — HOOK_SEQUENCE at lines 97–114, ACTIVE_RUNTIME_HOOKS at lines 128–136
- `P:/.claude/hooks/Stop_hypothesis_as_fact_gate.py` — `_should_block_claim` at lines 64–93
- `P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py` — ClaimType enum, RULE_PATTERNS, detect_claims
- `P:/.claude/skills/gto/SKILL.md` — Important Constraints section

**Stop_router.py HOOK_SEQUENCE insertion point (line 108):**

```
("StopHook_unverified_stance.py", "UNVERIFIED_STANCE_ENABLED", True, "inprocess"),
# INSERT Stop_hypothesis_as_fact_gate.py HERE
("Stop_negative_existence_guard.py", "NEGATIVE_EXISTENCE_GUARD_ENABLED", True, "inprocess"),
```

**`_should_block_claim()` critical bypass (Stop_hypothesis_as_fact_gate.py line 75):**

```python
if claim.has_hedge:
    return False  # Convention fabrications slip through here via "typically"/"usually"/"often"
```

**hypothesis_as_fact_detector.py:** Has partial coverage of convention phrases in RULE_PATTERNS
(`by convention/design`) but no dedicated CONVENTION type targeting invention-of-norms patterns.

**Confirmed:** `_log_decision()` in the gate handles all claim types generically — no type-specific code,
will log CONVENTION claims automatically once the type is added.

---

## Existing Implementation Discovery

**What already exists and works (confirmed by file reads this session):**
- `Stop_hypothesis_as_fact_gate.py`: fully functional, 283 lines, correct `run()` signature, fail-open on import errors, configurable via env vars
- `HypothesisAsFactDetector` with 4 claim types (ENTITY_ABSENCE, ENTITY_PRESENCE, RULE, SYSTEM): compiles patterns in `__init__`, `detect_claims()` dispatches to 3 type detectors
- `verification/claims.py` `extract_claims()` pipeline: already wired into the gate's `run()`
- `_log_decision()` in gate: type-agnostic, will handle CONVENTION automatically

**What is MISSING (gaps, not redesigns):**
1. Gate entry in HOOK_SEQUENCE (Stop_router.py)
2. Gate entry in ACTIVE_RUNTIME_HOOKS (Stop_router.py)
3. CONVENTION enum value in ClaimType
4. CONVENTION_PATTERNS list
5. `_detect_convention_claims()` method
6. Call to `_detect_convention_claims()` inside `detect_claims()`
7. Compile CONVENTION_PATTERNS in `_compile_patterns()`
8. No-hedge-bypass for CONVENTION in `_should_block_claim()` (Stop_hypothesis_as_fact_gate.py)
9. GROUNDED CLAIMS ONLY rule in GTO SKILL.md

---

## Test Discovery

**Existing tests (will run for regression):**
- `P:/.claude/hooks/tests/test_Stop_hypothesis_as_fact_gate.py`
- `P:/.claude/hooks/tests/test_stop_hypothesis_as_fact_refactor.py`
- `P:/.claude/hooks/anti_sycophancy/tests/test_hypothesis_as_fact_detector.py`

**New tests required:**
- CONVENTION claim detected for "hooks typically go undocumented" phrase
- CONVENTION claim NOT bypassed by hedge words (core behavioral change)
- Non-CONVENTION hedged claim still passes (regression protection)
- Gate appears in HOOK_SEQUENCE with enabled=True
- Gate appears in ACTIVE_RUNTIME_HOOKS

---

## Proposed Solution

### Change 1: Wire gate in Stop_router.py

In HOOK_SEQUENCE, insert after `StopHook_unverified_stance.py`:
```python
("Stop_hypothesis_as_fact_gate.py", "HYPOTHESIS_AS_FACT_GATE_ENABLED", True, "inprocess"),
```

In ACTIVE_RUNTIME_HOOKS set, add `"Stop_hypothesis_as_fact_gate.py"`.

Default: enabled=True. Mode is controlled by `HYPOTHESIS_AS_FACT_GATE_MODE` which defaults
to `warn` in the gate code.

### Change 2: CONVENTION claim type in hypothesis_as_fact_detector.py

Add to `ClaimType` enum:
```python
CONVENTION = "convention"  # Claims about org norms/policies (no hedge bypass)
```

Add `CONVENTION_PATTERNS` class attribute targeting invention-of-norms phrases.
Key patterns (from the fabrication example):
- "hooks typically go undocumented"
- "micro-fix policy"
- "by our convention/practice/policy"
- "the convention/policy is"

Add `_detect_convention_claims(sentence)` method (mirrors `_detect_rule_claims` but uses
CONVENTION type and `risk_domain=OTHER`).

Add to `_compile_patterns()` to compile the new patterns.

Add `claims.extend(self._detect_convention_claims(sentence))` in `detect_claims()` loop.

### Change 3: No-hedge-bypass for CONVENTION in Stop_hypothesis_as_fact_gate.py

Modify `_should_block_claim()`:
```python
# CONVENTION claims are never hedged-exempt (fabricated norms use hedge words deliberately)
is_convention = getattr(claim, "type", None) == "convention"

# Hedged claims pass without evidence (except CONVENTION type)
if claim.has_hedge and not is_convention:
    return False
```

### Change 4: GTO SKILL.md grounded-claims rule

In the **Important Constraints** section, add after "Cite evidence" bullet:
```
- **GROUNDED CLAIMS ONLY**: Never invent organizational policies, project conventions, or
  team practices that are not grounded in the current conversation. If unsure whether
  something is a real convention, omit it rather than qualify it with "typically" or "often."
```

---

## Implementation Plan

### Phase 1: Core Infrastructure

**TASK-001**: Wire Stop_hypothesis_as_fact_gate.py into Stop_router.py
- File: `P:/.claude/hooks/Stop_router.py`
- Action: Add gate to HOOK_SEQUENCE after StopHook_unverified_stance.py; add to ACTIVE_RUNTIME_HOOKS
- Points: 1
- Acceptance: Gate in HOOK_SEQUENCE with default_enabled=True; gate name in ACTIVE_RUNTIME_HOOKS
- Prerequisites: none

**TASK-002**: Add CONVENTION ClaimType and patterns to HypothesisAsFactDetector
- File: `P:/.claude/hooks/anti_sycophancy/hypothesis_as_fact_detector.py`
- Action: Add CONVENTION to ClaimType enum; add CONVENTION_PATTERNS; add `_detect_convention_claims()`; compile; call from `detect_claims()`
- Points: 3
- Acceptance: "hooks typically go undocumented" triggers CONVENTION detection; existing claim types unaffected; module imports without error
- Prerequisites: none

**TASK-003**: No-hedge-bypass for CONVENTION in gate
- File: `P:/.claude/hooks/Stop_hypothesis_as_fact_gate.py`
- Action: Modify `_should_block_claim()` to not exempt CONVENTION claims from hedge bypass
- Points: 1
- Acceptance: CONVENTION claim with "typically" still triggers warn/block; non-CONVENTION hedged claim still passes
- Prerequisites: TASK-002
- Pre-implementation check: Read `P:/.claude/hooks/verification/claims.py` to confirm `Claim.type` is a string field with value matching `ClaimType.CONVENTION.value` ("convention"). If the field name differs, adjust the `getattr(claim, "type", None)` check accordingly.

### Phase 2: Skill Layer

**TASK-004**: Add grounded-claims rule to GTO SKILL.md
- File: `P:/.claude/skills/gto/SKILL.md`
- Action: Add GROUNDED CLAIMS ONLY rule in Important Constraints section
- Points: 1
- Acceptance: Rule present; clearly states no inventing conventions
- Prerequisites: none

### Phase 3: Verification

**TASK-005**: Write tests for new behavior
- Files: `P:/.claude/hooks/anti_sycophancy/tests/test_hypothesis_as_fact_detector.py`, `P:/.claude/hooks/tests/test_Stop_hypothesis_as_fact_gate.py`
- Action: Tests for CONVENTION detection, no-hedge-bypass, gate wired in router
- Points: 3
- Acceptance: All new tests pass; no regressions in existing tests
- Prerequisites: TASK-001, TASK-002, TASK-003

**TASK-006**: Run full test suite
- Action: Run all existing gate and detector tests to confirm no regressions
- Points: 1
- Acceptance: All existing tests pass
- Prerequisites: TASK-001 through TASK-005

---

## Risks

1. **False positives from CONVENTION patterns**: Patterns may match legitimate recommendations. Mitigation: Start in warn mode, review logs before switching to block mode.
2. **Hedge bypass change correctness**: `claim.type` must match the string `"convention"`. Need to verify `verification/claims.py` Claim wrapper passes type through as a string (expected — `claim.type` is a string in the Claim dataclass).
3. **Performance overhead**: Adding one in-process gate. Gate is fail-open with try/except wrapper. Risk is low.

---

## Success Criteria

- [ ] `Stop_hypothesis_as_fact_gate.py` appears in HOOK_SEQUENCE (enabled=True)
- [ ] `Stop_hypothesis_as_fact_gate.py` appears in ACTIVE_RUNTIME_HOOKS
- [ ] "hooks typically go undocumented" triggers CONVENTION claim detection
- [ ] CONVENTION claim with hedge word is NOT bypassed (still warns/blocks)
- [ ] Non-CONVENTION hedged claim still passes (regression check)
- [ ] GTO SKILL.md contains GROUNDED CLAIMS ONLY constraint
- [ ] All existing tests pass

---

## Dependencies

- `P:/.claude/hooks/verification/claims.py`: verify Claim.type field passes string value; expected "convention" matching ClaimType.CONVENTION.value
- `P:/.claude/hooks/evidence_store.py`: existing gate dependency, no changes needed

---

*Plan: P:/.claude/hooks/plans/plan-20260316-convention-fabrication-gate.md*

## Risks, Success Criteria, Dependencies

### Risks
- [Risk 1]: [Mitigation]

### Success Criteria
- [ ] [Criterion 1]
- [ ] [Criterion 2]

### Dependencies
- [Dependency 1]
