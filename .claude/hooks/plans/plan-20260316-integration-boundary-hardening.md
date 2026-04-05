# Plan: Integration Boundary Test Hardening

**Created:** 2026-03-16
**Objective:** Implement three process improvements identified in retrospective + /arch analysis to prevent mock-based unit tests from bypassing cross-module contracts — specifically the `claims.py` field transformation boundary.

---

## Status Summary

| Phase | Status | Notes |
|-------|--------|-------|
| Phase 1 — conftest.py fixture | ✅ COMPLETE | `make_real_claim` fixture + `real_claim_from_text()` added |
| Phase 2 — Integration boundary tests | ✅ COMPLETE | `TestMakeRealClaimFixture` + `TestConventionGateEndToEnd` (5 tests, all GREEN) |
| Phase 3 — plan-workflow contract requirement | ✅ COMPLETE | Module Boundary Contract added to Prevention Checklist |
| Phase 4 — Verification | ✅ COMPLETE | 5 new tests pass; 3 pre-existing pass; 24 pre-existing failures unchanged |

---

## Problem Statement

Two bugs in the CONVENTION claim type implementation slipped through unit tests and were only caught by `/verify` Tier 3 E2E:

1. **Uppercase mismatch**: `_should_block_claim()` checked `claim.type == "convention"` but `claims.py` uppercases all claim types via `_raw_claim_to_claim()`, so real `Claim.type == "CONVENTION"`. Mock tests set `claim.type = "convention"` directly, bypassing this transform.

2. **Confidence threshold bypass**: `_calculate_confidence()` subtracts 0.2 for hedged sentences. A CONVENTION claim with hedge words gets `confidence = 0.7 - 0.2 = 0.5 < 0.7`, triggering the confidence bypass. Mock tests set `claim.confidence = 0.8` directly, hiding this.

**Root cause of both bugs**: Mocks fabricate `Claim` objects with hand-set field values, bypassing the `claims.py` transformation pipeline entirely. The correct test exercises the real pipeline from text input to gate output.

**Why mocks accumulated**: Using `extract_claims(text)` in tests requires knowing the import path. Without a ready-made fixture, mocking is the path of least resistance.

**Process gap**: Plan task "verify field name" is insufficient — the needed check is "trace the full value transformation chain and verify a test exercises it end-to-end."

---

## Context Analysis

**Files involved:**

- `P:/.claude/hooks/tests/conftest.py` — shared fixtures; has cleanup/env setup, NO claim-building helper
- `P:/.claude/hooks/tests/test_Stop_hypothesis_as_fact_gate.py` — gate tests; `_should_block_claim()` tests use `Mock(type=..., confidence=...)` directly; no integration-boundary tests
- `P:/.claude/hooks/anti_sycophancy/tests/test_hypothesis_as_fact_detector.py` — detector tests; correctly tests CONVENTION detection patterns
- `P:/.claude/skills/plan-workflow/SKILL.md` — Prevention Checklist at line 444; no integration contract requirement for cross-module tasks

**Confirmed pipeline:**

```
text
  → extract_claims(text)             [verification/claims.py]
      → _raw_claim_to_claim()
          → Claim(type="CONVENTION", confidence=0.5)
                   ^^^^^^^^^^^        ^^^^
                   UPPERCASE          hedge penalty applied (-0.2)
  → build_verdicts(claims, tool_events)  [verification/engine.py]
      → List[VerificationVerdict]
  → _should_block_claim(claim, verdict)  [Stop_hypothesis_as_fact_gate.py]
```

**Confirmed**: `_raw_claim_to_claim()` applies `.upper()` at line 103 of `claims.py`. `_calculate_confidence()` subtracts 0.2 for hedge words. Both transformations are invisible when mocking `Claim` directly.

---

## Existing Implementation Discovery

**conftest.py** (lines 1–111): Three autouse fixtures — `isolate_notifications`, `enable_dependency_verification_gate`, `clean_test_state`. No shared claim-building utility. `sys.path` setup pattern already established.

**test_Stop_hypothesis_as_fact_gate.py** `TestConventionClaimNoHedgeBypass`: Uses `Mock()` with `type`, `confidence`, `has_hedge` set directly. Tests `_should_block_claim()` in isolation only. Integration path untested.

**Missing**: `TestConventionGateEndToEnd` class calling `gate.run()` with fabrication text and real `extract_claims()`.

**`build_verdicts` return type** (engine.py line 56): `List[VerificationVerdict]` — one verdict per claim. Integration test mock must return a list.

---

## Test Discovery

**Existing tests to preserve:**
- `P:/.claude/hooks/tests/test_Stop_hypothesis_as_fact_gate.py` — 41 tests, all passing
- `P:/.claude/hooks/anti_sycophancy/tests/test_hypothesis_as_fact_detector.py` — passing
- `P:/.claude/hooks/tests/test_stop_hypothesis_as_fact_refactor.py` — passing

**New tests required:**
- `test_make_real_claim_returns_convention_type` — fixture returns `Claim` with `type == "CONVENTION"`
- `test_make_real_claim_confidence_includes_hedge_penalty` — fixture returns `Claim` with `confidence < 0.7`
- `TestConventionGateEndToEnd.test_convention_fabrication_blocked_end_to_end` — full `gate.run()` block mode, `allow == False`
- `TestConventionGateEndToEnd.test_convention_fabrication_warned_end_to_end` — full `gate.run()` warn mode, `allow == True`

---

## Proposed Solution

### Change 1: `make_real_claim()` fixture in conftest.py

```python
@pytest.fixture
def make_real_claim():
    """Return a factory that builds real Claim objects via the full extract_claims() pipeline.

    Use this instead of Mock(type=..., confidence=...) for any test covering
    code that consumes Claim objects from claims.py. Exercises cross-module
    contracts: .upper() on claim.type, hedge penalty on confidence.
    """
    import sys
    from pathlib import Path
    hooks_dir = Path(__file__).resolve().parent.parent
    if str(hooks_dir) not in sys.path:
        sys.path.insert(0, str(hooks_dir))
    try:
        from verification import extract_claims
    except ImportError:
        pytest.skip("verification module unavailable")

    def _factory(text: str, index: int = 0):
        claims = extract_claims(text)
        assert claims, f"extract_claims produced no claims for: {text!r}"
        return claims[index]

    return _factory
```

Also expose `real_claim_from_text(text, index=0)` as a module-level function for non-fixture use.

### Change 2: Integration-boundary tests in test_Stop_hypothesis_as_fact_gate.py

Add `TestConventionGateEndToEnd` class. Mock only:
- `load_tool_events_for_context` → returns `[]`
- `build_verdicts` → returns `[VerificationVerdict(status=VerificationStatus.SILENT, supporting_evidence=[], refuting_evidence=[])]`

Do NOT mock `Claim` fields. `extract_claims()` runs real.

### Change 3: Module Boundary Contract in plan-workflow SKILL.md

In the **Prevention Checklist** section (line 444), add after existing items:

```markdown
- [ ] **Module Boundary Contract**: For any task that imports and consumes output from another module
  (e.g., `from verification import extract_claims`), acceptance criteria MUST include:
  (a) an integration test exercising the real module output (not a mock of the consumed type),
  and (b) an explicit statement of what transformations the boundary applies.
  Example: "claims.py uppercases `.type`, subtracts 0.2 from `.confidence` for hedged text."
```

---

## Implementation Plan

### Phase 1: Core Infrastructure

**TASK-001**: Add `make_real_claim()` fixture and `real_claim_from_text()` helper to conftest.py
- File: `P:/.claude/hooks/tests/conftest.py`
- Action: Add non-autouse `make_real_claim` pytest fixture (returns factory function) and `real_claim_from_text()` module-level function. Both run `extract_claims(text)` and return `claims[index]`. Import guard: `pytest.skip()` if verification module unavailable.
- Points: 2
- Acceptance:
  - `make_real_claim("hooks typically go undocumented").type == "CONVENTION"` (uppercase, from real pipeline)
  - `make_real_claim("hooks typically go undocumented").confidence < 0.7` (hedge penalty applied)
  - `real_claim_from_text()` callable at module level without pytest context
  - Import failure triggers `pytest.skip()`, not `ImportError`
- Prerequisites: none
- Integration contract: `claims.py` `_raw_claim_to_claim()` uppercases `.type`; `_calculate_confidence()` subtracts 0.2 for hedge words. Fixture returns real `Claim` with no field overrides.

**TASK-002**: Add `TestConventionGateEndToEnd` to test_Stop_hypothesis_as_fact_gate.py
- File: `P:/.claude/hooks/tests/test_Stop_hypothesis_as_fact_gate.py`
- Action: Add class with two tests using `make_real_claim` fixture and `gate.run()`. Mock only `load_tool_events_for_context` (returns `[]`) and `build_verdicts` (returns `[VerificationVerdict(status=VerificationStatus.SILENT, supporting_evidence=[], refuting_evidence=[])]`). Do NOT mock `Claim` fields.
- Points: 3
- Acceptance:
  - `test_convention_fabrication_blocked_end_to_end`: `HYPOTHESIS_AS_FACT_GATE_MODE=block`, `gate.run({"session_id": "test", "terminal_id": "test", "response_text": "hooks typically go undocumented"})` returns `{"allow": False, ...}`
  - `test_convention_fabrication_warned_end_to_end`: `HYPOTHESIS_AS_FACT_GATE_MODE=warn`, same input returns `{"allow": True, ...}`
  - Tests use `make_real_claim` fixture; no `Mock(type=..., confidence=...)` on Claim fields
  - Reverting uppercase fix (`== "CONVENTION"` → `== "convention"`) makes block-mode test RED
- Prerequisites: TASK-001
- Integration contract: `gate.run()` calls `extract_claims(response_text)` (real) → `build_verdicts()` (mocked SILENT) → `_should_block_claim()` (real). Only I/O boundary mocked.

### Phase 2: Skill Layer

**TASK-003**: Add Module Boundary Contract checklist item to plan-workflow SKILL.md
- File: `P:/.claude/skills/plan-workflow/SKILL.md`
- Action: In the Prevention Checklist section (line 444), add Module Boundary Contract item as specified in Change 3. One checklist item with inline example.
- Points: 1
- Acceptance:
  - Prevention Checklist contains "Module Boundary Contract" item
  - Item requires both (a) integration test and (b) explicit transformation statement
  - Example references `claims.py` behavior
- Prerequisites: none

### Phase 3: Verification

**TASK-004**: Run full test suite
- Action: `pytest P:/.claude/hooks/tests/ -v` — confirm all existing tests pass plus new integration tests pass
- Points: 1
- Acceptance: All 41 existing tests pass; `TestConventionGateEndToEnd` block and warn tests GREEN
- Prerequisites: TASK-001, TASK-002, TASK-003

---

## Risks, Success Criteria, Dependencies

### Risks

1. **`extract_claims()` import may fail** in conftest if path not set. Mitigation: fixture mirrors the `sys.path.insert()` pattern already in conftest. Fallback: `pytest.skip()`.
2. **`make_real_claim` returns wrong index** if fabrication text produces multiple claims. Mitigation: use exact phrase "hooks typically go undocumented" confirmed to produce one CONVENTION claim.
3. **`build_verdicts` mock must return a list**. Confirmed: `engine.py` line 56 returns `List[VerificationVerdict]`. Mock must return `[VerificationVerdict(...)]`, not a single object.

### Success Criteria

- [ ] `make_real_claim("hooks typically go undocumented").type == "CONVENTION"`
- [ ] `make_real_claim("hooks typically go undocumented").confidence < 0.7`
- [ ] `TestConventionGateEndToEnd` tests pass in block and warn modes
- [ ] Reverting uppercase fix to `"convention"` makes block-mode test RED
- [ ] All 41 existing tests continue to pass
- [ ] plan-workflow Prevention Checklist contains Module Boundary Contract item

### Dependencies

- `P:/.claude/hooks/verification/claims.py`: `extract_claims()` importable; `.type` uppercase at line 103 confirmed
- `P:/.claude/hooks/verification/engine.py`: `build_verdicts()` returns `List[VerificationVerdict]`; `VerificationStatus.SILENT` confirmed
- `P:/.claude/hooks/Stop_hypothesis_as_fact_gate.py`: `gate.run()` with `session_id`, `terminal_id`, `response_text` keys confirmed
- File-based changes — no deployment tasks needed

---

*Plan: P:/.claude/hooks/plans/plan-20260316-integration-boundary-hardening.md*
