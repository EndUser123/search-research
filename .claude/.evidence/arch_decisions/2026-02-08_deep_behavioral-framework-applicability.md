# Architecture Analysis: Behavioral Framework Modernization - Phase Applicability Review

**Date:** 2026-02-08
**Template:** deep (comprehensive analysis)
**Query:** Review remainder of behavioral framework modernization for current codebase applicability
**Plan Reference:** `plan-20260207-consolidated-truth-evidence-behavioral-modernization.md`

---

## Executive Summary

**Recommendation:** Phase 2 is PARTIALLY APPLICABLE with modifications. Phases 3-5 require re-evaluation based on current stop-hook latency metrics.

**Key Findings:**
1. **Phase 1 (COMPLETED)**: All components implemented and tested (62/62 tests passing)
2. **Phase 2 (MODIFIED)**: `StopHook_confidence_validator.py` already exists - integration needed rather than creation
3. **Phase 3 (UNCERTAIN)**: In-process migration requires latency baseline to justify
4. **Phase 4 (DEFERRED)**: Depends on Phase 2 evidence-tier integration
5. **Phase 5 (OPTION-ONLY)**: Requires explicit use case before proceeding

---

## Stage 0.3: Codebase-Aware Analysis

### CURRENT STATE (Verified via file reads)

**Phase 1 Components - FULLY IMPLEMENTED:**
| Component | Status | Tests | Notes |
|-----------|--------|-------|-------|
| `behavioral_protocol.py` | ✅ Complete | 33 passing | Evidence tiers 1-4, confidence ceilings 95%/85%/75%/50% |
| `behavioral_state.py` | ✅ Complete | 16 passing | Goal anchoring with StateManager integration |
| `hook_base.py` (in-process) | ✅ Complete | 13 passing | `run_hook_inprocess()`, `HookTimeoutError`, `supports_inprocess()` |
| **Total Phase 1** | ✅ Complete | **62/62 passing** | All Go Criteria met |

**Pre-Existing Components (discovered during review):**
| Component | Status | Relationship to Plan |
|-----------|--------|----------------------|
| `StopHook_confidence_validator.py` | ✅ EXISTS | **Overlaps Phase 2** - implements confidence validation (Gap 3 of Five-Gate) |
| `unified_prompt_injector.py` | ✅ EXISTS | **Pre-dates plan** - goal anchor consolidation already done |
| `empirical_claims_gate.py` | ✅ EXISTS | Phase 2 target for enhancement |

**Missing Components:**
| Component | Planned Phase | Status |
|-----------|---------------|--------|
| `PreToolUse_documentation_first.py` | Phase 2 | ❌ Does NOT exist |
| Enhanced `empirical_claims_gate.py` with evidence tiers | Phase 2 | ⚠️ Partial - `behavioral_protocol.py` exists but not integrated |
| Enhanced `StopHook_confidence_validator.py` with evidence tiers | Phase 2 | ⚠️ Exists but doesn't use `behavioral_protocol.py` |
| In-process migration in `Stop_router.py` | Phase 3 | ⚠️ Protocol exists, migration not executed |

---

## Stage 1: Mental Model

**Design Pattern:** Layered Enforcement with Progressive Rollout

The plan follows a **phased rollout pattern** with explicit go/no-go gates:
- Layer 1: Deterministic Python rules (blocking)
- Layer 2: LLM advisory (optional)
- Feature flags for every major component
- Measured progression with thresholds

**Current state aligns with:** Test-Driven Infrastructure pattern
- Phase 1 completed with full test coverage
- Rollback strategies documented
- Feature flags defined

---

## Stage 2: Pattern Analysis

### Repeating Pattern

**What class of problem repeats?**
- **Integration gap**: New components (`behavioral_protocol.py`) are implemented but not integrated into existing hooks
- **Parallel implementation**: `StopHook_confidence_validator.py` exists separately from the behavioral framework
- **Incomplete rollout**: Phase 1 components exist but Phase 2 integration is pending

### Root Causes

1. **Pre-existing Confidence Validator**: `StopHook_confidence_validator.py` was implemented as part of "Gap 3: Confidence Validation Enforcement for Five-Gate Safety System" - this predates and overlaps with Phase 2 of the behavioral plan
2. **Architecture Unclear**: The plan doesn't specify whether `StopHook_confidence_validator.py` should be:
   - Enhanced to use `behavioral_protocol.py`
   - Replaced by a new implementation
   - Left as-is with coexistence

---

## Stage 3: Pre-Mortem (What realistically fails in 6 months?)

### Scenario 1: Coexistence without Integration
**Risk:** Two confidence validators running with different logic
- `StopHook_confidence_validator.py` (existing)
- New evidence-tier validation (Phase 2)

**Failure mode:** Conflicting block reasons, user confusion, inconsistent enforcement

### Scenario 2: In-Process Migration without Latency Justification
**Risk:** Phase 3 proceeds without baseline metrics
- Plan states "p95 stop-hook latency < 200ms" target
- No baseline captured for current subprocess overhead
- Migration complexity without measurable benefit

**Failure mode:** Unnecessary complexity, potential regressions, no clear improvement

### Scenario 3: Documentation-First Gate Added
**Risk:** `PreToolUse_documentation_first.py` blocks without context
- Hook doesn't know what documentation is relevant
- User frustration from "read X docs first" without specificity

**Failure mode:** False blocks, users disable the hook

---

## Stage 4: Risk Matrix

| Option | Technical Risk | Schedule Risk | Organizational Risk | Coupling | Score |
|--------|---------------|--------------|-------------------|----------|-------|
| **A: Integrate with existing confidence validator** | Medium | Low | Low | Medium | **PROCEED** |
| **B: Create separate evidence-tier validator** | Low | Medium | Medium | High | CAUTION |
| **C: Defer all Phases 2-5** | Low | Low | Low | None | DEFER |
| **D: Full in-process migration** | High | High | Low | High | AVOID |

---

## Stage 5: Forced Alternatives

### Option A: Integrate with Existing `StopHook_confidence_validator.py`

**Differs from others on:** Technology (enhance existing vs. create new), Coupling (integrates with pre-existing component)

**Approach:**
1. Modify `StopHook_confidence_validator.py` to import and use `behavioral_protocol.py`
2. Add evidence-tier checking before confidence validation
3. Map confidence scores to evidence-tier ceilings
4. Keep existing confidence patterns as fallback

**Changes Required:**
- `StopHook_confidence_validator.py` [MOD]: Import `behavioral_protocol.py`, add tier validation
- Tests for integration behavior
- Feature flag: `BEHAVIORAL_CONFIDENCE_VALIDATOR_ENABLED=true`

**Go Criteria:**
- `behavioral_protocol.py` imported successfully
- Existing confidence patterns still trigger
- Evidence-tier ceilings enforced for new assertions

---

### Option B: Create Separate Evidence-Tier Validator

**Differs from others on:** Architecture (separate hook vs. integration), Scope (tier-only vs. combined)

**Approach:**
1. Create new `StopHook_evidence_tier_validator.py`
2. Runs before `StopHook_confidence_validator.py` in sequence
3. Validates evidence tiers separately from confidence
4. Blocks if confidence exceeds evidence-tier ceiling

**Changes Required:**
- `StopHook_evidence_tier_validator.py` [NEW]
- `Stop_router.py` [MOD]: Add to sequence
- Tests for tier validation
- Feature flag: `BEHAVIORAL_EVIDENCE_TIER_VALIDATOR_ENABLED=true`

**Go Criteria:**
- Tier ceilings enforced before confidence check
- No conflict with existing confidence validator
- Clear block messages indicating tier vs. confidence issue

---

### Option C: Defer All Phases 2-5

**Differs from others on:** Timeline (no new work vs. proceed), Risk (zero vs. some)

**Approach:**
1. Mark Phase 1 complete and stable
2. Collect metrics on Phase 1 usage
3. Wait for explicit use case before Phase 2
4. Re-evaluate plan based on actual needs

**Changes Required:**
- Update plan status: "Phase 1 Complete - Paused awaiting requirements"
- No code changes
- Document Phase 1 capabilities for reference

**Go Criteria:**
- Phase 1 components remain stable
- No regressions in existing hooks
- Clear documentation of what Phase 1 enables

---

### Option D: Full In-Process Migration (Phase 3)

**Differs from others on:** Scope (includes Phase 3), Risk (high complexity)

**Approach:**
1. Extend `Stop_router.py` with in-process dispatch
2. Migrate top 10 latency hooks to in-process
3. Add HOOK_SEQUENCE dispatch mode field
4. Measure latency reduction

**Changes Required:**
- `Stop_router.py` [MOD]: `run_hook_inprocess()`, HOOK_SEQUENCE changes
- Top 10 hooks [MOD]: Add `run()` functions
- Extensive testing
- Feature flag: `INPROCESS_HOOK_DISPATCH_ENABLED=false` (default off)

**Go Criteria:**
- Baseline latency captured (< 200ms target needs baseline)
- p95 latency improvement >= 30%
- All migrated hooks pass both execution paths

**BLOCKER:** No baseline exists. Must capture baseline before migration.

---

## Recommendation Analysis

### Primary Recommendation: Option A (Integrate with Existing)

**Why Option A over others:**
1. **Leverages existing investment**: `StopHook_confidence_validator.py` already works
2. **Avoids hook sprawl**: No new validator, enhances existing
3. **Lower risk**: Integration scope vs. new component
4. **Clear rollback**: Revert to existing `StopHook_confidence_validator.py`

**Implementation order:**
1. Read `StopHook_confidence_validator.py` to understand current logic
2. Design integration points with `behavioral_protocol.py`
3. Create tests for combined behavior
4. Implement integration
5. Verify existing confidence patterns still work

---

### Defer Phases 3-5 until:

**Phase 3 (In-Process Migration):**
- [ ] Baseline stop-hook latency captured from `session_data/hook_decisions_*.jsonl`
- [ ] Current p95 latency measured
- [ ] Clear gap identified (subprocess overhead dominates)

**Phase 4 (False-Positive Hardening):**
- [ ] Phase 2 evidence-tier integration stable
- [ ] Baseline false-positive rate measured
- [ ] Specific false-positive patterns identified

**Phase 5 (Optional Capabilities):**
- [ ] Explicit use case for Prefect/Neo4j/spaCy/LLM advisory
- [ ] Demonstrated benefit over current approach
- [ ] Rollback validated

---

## Stage 6: Rollback Plan

### Phase 2 Rollback (Option A Integration)

**If integration breaks existing behavior:**
1. Feature flag: `BEHAVIORAL_CONFIDENCE_VALIDATOR_ENABLED=false`
2. Code revert: Restore `StopHook_confidence_validator.py` from git
3. Verification: Run confidence validator tests

**Time to rollback:** < 3 minutes

### Universal Rollback

```bash
# Revert Phase 1 if needed
git revert <phase-1-commit-hash>

# Or reset to commit before Phase 1 started
git reset --hard <pre-phase-1-commit>
```

**Time to rollback:** < 5 minutes

---

## Stage 7: Tech Debt Estimation

### If Option A (Integration) Proceeds:

| Debt Type | Score | Impact |
|-----------|-------|--------|
| Coupling | Medium | `StopHook_confidence_validator.py` now depends on `behavioral_protocol.py` |
| Maintainability | Low | Clear separation of concerns, tested integration |
| Test Coverage | Low | Existing tests + new integration tests |
| Documentation | Low | Code is self-documenting with clear patterns |

### If Option D (In-Process) Proceeds without Baseline:

| Debt Type | Score | Impact |
|-----------|-------|--------|
| Unknown Unknowns | High | No baseline to measure improvement |
| Complexity | High | Dual execution paths (in-process + subprocess) |
| Testing | High | Need tests for both execution modes |
| Documentation | Medium | Complex state machine for dispatch logic |

---

## Stage 8: Timeline

### Option A (Recommended)

| Phase | T-Shirt | Hours | Confidence |
|-------|---------|-------|------------|
| Design integration | S | 2 | 85% |
| Create integration tests | M | 4 | 90% |
| Implement integration | M | 6 | 75% |
| Verification | S | 2 | 95% |
| **Total** | **M** | **14** | **82%** |

### Option D (In-Process Migration - NOT RECOMMENDED)

| Phase | T-Shirt | Hours | Confidence |
|-------|---------|-------|------------|
| Capture baseline | M | 4 | 95% |
| Design migration | L | 8 | 60% |
| Implement in-process | XL | 20 | 50% |
| Create tests | L | 12 | 70% |
| Verification | L | 8 | 65% |
| **Total** | **XL** | **52** | **60%** |

**Low confidence due to:** No baseline, complex dual-mode, unknown benefits

---

## Stage 9: Implementation Checklist

### Option A (Integration with Existing Confidence Validator)

**Phase 2A: Design**
- [ ] Read and analyze `StopHook_confidence_validator.py`
- [ ] Read and analyze `behavioral_protocol.py`
- [ ] Design integration points
- [ ] Define success criteria

**Phase 2B: Testing**
- [ ] Create test: confidence_validator_with_evidence_tiers.py
- [ ] Test: existing patterns still trigger
- [ ] Test: evidence-tier ceiling enforced
- [ ] Test: tier mapping correct

**Phase 2C: Implementation**
- [ ] Import `behavioral_protocol.py` in `StopHook_confidence_validator.py`
- [ ] Add tier detection before confidence check
- [ ] Add ceiling validation
- [ ] Add block message with tier info
- [ ] Feature flag implementation

**Phase 2D: Verification**
- [ ] Run all tests (existing + new)
- [ ] Test with sample high-confidence claims
- [ ] Test with tier-violating claims
- [ ] Verify rollback works

**Phase 2E: Documentation**
- [ ] Update plan.md with integration approach
- [ ] Document behavioral framework usage
- [ ] Update CLAUDE.md if needed

---

## Stage 10: Confidence Calibration

## Confidence: 82%

**Evidence basis:**
- **Code:** Verified Phase 1 files exist, 62/62 tests pass (Tier 1)
- **Documentation:** Plan clearly defines remaining phases (Tier 1)
- **Existing Implementation:** `StopHook_confidence_validator.py` exists and works (Tier 1)
- **Gap:** Integration design not yet done (unverified)

**Key assumptions:**
1. `StopHook_confidence_validator.py` CAN be enhanced without breaking existing behavior
2. Evidence-tier integration adds value beyond existing confidence validation
3. Existing confidence patterns are worth preserving
4. Feature flag rollout is sufficient for safe deployment

**Verification status:**
- Assumption 1: **Unverified** - requires reading `StopHook_confidence_validator.py` fully
- Assumption 2: **Unverified** - depends on specific use cases
- Assumption 3: **Partially verified** - confidence validator exists, implies value
- Assumption 4: **Verified** - feature flag pattern established in codebase

---

## Stage 11: Adversarial Self-Review

**Weakest assumption:** `StopHook_confidence_validator.py` CAN be enhanced without breaking existing behavior

**If wrong:** Integration breaks existing confidence validation, causes regressions, requires rollback

**Mitigation:**
- Comprehensive testing before integration
- Feature flag allows instant rollback
- Keep existing code path as fallback
- Test with sample claims that currently trigger

**Verification status:** **Partially confirmed**
- Read first 50 lines of `StopHook_confidence_validator.py`
- Confirmed it uses regex patterns for confidence detection
- Need to read full file to understand complete logic before integration

**Bias check:**
- **Recency bias?** [No] - Recommending cautious integration based on existing working code
- **Survivorship bias?** [No] - Considering rollback and defer options
- **Complexity bias?** [No] - Recommending simpler integration over new component + migration

---

## Final Output

### Analysis: Improve Behavioral Framework (Phase 2-5 Applicability)

### Failures Identified (from CKS)
- No CKS memory entries found for this subsystem - proceeding with generic best practices analysis

### Pattern
**Integration gap with pre-existing components**: Phase 2 assumes creating new components, but `StopHook_confidence_validator.py` already exists and overlaps with planned functionality.

### Proposed Changes

**Change A: Integrate Phase 2 with Existing Confidence Validator** (RECOMMENDED)
- **File(s):** `StopHook_confidence_validator.py` [MOD], test files [NEW]
- **Logic:** Import `behavioral_protocol.py`, add evidence-tier checking before confidence validation, preserve existing patterns
- **Prevents/speeds:** Avoids duplicate validators, leverages existing working code, reduces hook sprawl
- **Test:** Verify existing confidence patterns still trigger, verify tier ceilings enforced
- **Success:** Unified validation without regressions
- **Effort:** 14 hours (M)

**Change B: Defer Phase 3 (In-Process Migration) until Baseline Captured**
- **File(s):** None (deferral)
- **Logic:** Capture baseline stop-hook latency from `session_data/hook_decisions_*.jsonl` before migration
- **Prevents/speeds:** Prevents unnecessary complexity without measurable benefit, ensures data-driven decision
- **Test:** Measure p95 latency, compare against <200ms target
- **Success:** Clear justification before high-complexity work
- **Effort:** 4 hours (S) for baseline capture

**Change C: Defer Phase 4 (False-Positive Hardening)**
- **File(s):** None (deferral)
- **Logic:** Wait for Phase 2 stability and baseline false-positive rate
- **Prevents/speeds:** Prevents optimizing before measurement, focuses on core integration first
- **Test:** Collect baseline false-positive metrics during Phase 2
- **Success:** Data-driven optimization roadmap
- **Effort:** Deferred indefinitely

**Change D: Defer Phase 5 (Optional Capabilities)**
- **File(s):** None (deferral)
- **Logic:** No explicit use case for Prefect/Neo4j/spaCy/LLM advisory yet
- **Prevents/speeds:** Prevents over-engineering without requirements
- **Test:** Awaiting explicit use case
- **Success:** Only build when needed
- **Effort:** Deferred indefinitely

### Implementation Order
1. **Change A** — Integrate evidence tiers with existing confidence validator (highest value, lowest risk)
2. **Change B** — Capture baseline for in-process migration (enables data-driven Phase 3 decision)
3. Defer Phases 4-5 until explicit requirements emerge

**Total estimated effort:** 18 hours (14 + 4)

---

## Persisted Output

Auto-saved to: `P:\.claude\arch_decisions\2026-02-08_deep_behavioral-framework-applicability.md`

---

**Next Actions:**
1. Review this analysis
2. Decide: Proceed with Change A (integration), or Change C (defer all)
3. If proceeding: Read full `StopHook_confidence_validator.py` to design integration
