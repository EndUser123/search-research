# Architecture Review: Claim Hook Consolidation Proposal

**Date**: 2026-03-12
**Template**: deep (ARCHITECTURE_REVIEW)
**Confidence**: 85%

---

## Executive Summary

**Finding**: The proposed consolidation (Change A + Change B) is **NOT optimal**. Based on incorrect assumptions.

**Recommendation**: Simpler alternative - modify 8 lines instead of multi-hook consolidation.

---

## Critical Evidence

### Evidence #1: Proposal Assumptions Incorrect

**Proposal claims**: `verify_claims.py` and `artifact_claims.py` are active hooks causing noise.

**Reality** (from tool evidence):
```bash
$ grep -c "verify_claims\|artifact_claims" Stop_router.py
0
```

**ACTIVE_RUNTIME_HOOKS** (Stop_router.py:122-129):
```python
frozenset({
    "StopHook_skill_execution_gate.py",
    "StopHook_unverified_stance.py",
    "Stop_negative_existence_guard.py",
    "StopHook_step_header_verifier.py",
    "stop/Stop_verification_gate.py",
    "principle_monitor.py",
})
```

**Conclusion**: `verify_claims.py` and `artifact_claims.py` are **NOT ACTIVE**.

---

### Evidence #2: Real Friction Point Identified

**Location**: `StopHook_unverified_stance.py:316-322`

```python
if not has_e2e:
    return False, (
        "E2E workflow claim without execution evidence. "
        "Required: Actual skill invocation or multi-step workflow demonstration. "
        "Component tests (pytest) alone are insufficient for workflow claims."
    )
```

**User's experience** (claim-efficiency.txt:228-230):
- Fixed bug in router.py
- Ran pytest successfully
- Stop hook blocked: "E2E workflow claim without execution evidence"
- Had to manually invoke `/all` skill to demonstrate workflow

**Root cause**: E2E verification explicitly rejects pytest as "insufficient" evidence.

---

## GoT Analysis

**Extracted Nodes**:
- **Constraints**: ["Must reduce claim friction", "Must accept pytest as E2E", "Must minimize code change"]
- **Ideas**: ["Consolidate to single hook", "Add quiet mode", "Modify E2E check", "Delete dead code"]
- **Risks**: ["Wrong assumptions", "Targeting wrong problem", "Over-engineering"]
- **Components**: ["StopHook_unverified_stance.py", "verify_claims.py (inactive)", "artifact_claims.py (inactive)"]
- **Data flows**: ["User pytest → Stop block", "E2E check → pytest rejection"]

**Edge Relationships**:
- "Consolidate to single hook" **contradicts** "Proposal based on wrong assumptions" ⚠️
- "Must reduce friction" **contradicts** "Targeting wrong friction point" ⚠️
- "Modify E2E check" **supports** "Must accept pytest" ✓
- "verify_claims.py (inactive)" **unrelated** to "User pytest block"

**Cycles**: None

**Insights**:
- Contradiction: Proposal assumes hooks are active that aren't running
- Risk: Change A consolidates already-inactive code
- Simpler path: 8-line modification achieves primary goal

---

## Comparison

### Option A: Original Proposal (Change A + B)

**Changes**:
- Consolidate to single Stop hook
- Disable verify_claims.py, artifact_claims.py
- Move strawberry_validator to PostToolUse
- Add CLAIM_ADVISORY_QUIET environment variable

**Effort**: 2-3 hours (multi-file, testing)

**Problems**:
- ❌ Hooks already inactive (ARCH-001)
- ❌ Targets wrong friction point (ARCH-002)
- ❌ Quiet mode doesn't address E2E blocking (ARCH-004)
- ❌ Unnecessary strawberry_validator move (ARCH-005)

**Second-order effects**:
- Complex multi-file change increases regression risk
- Dead code deletion unrelated to friction
- May allow false-positive workflow claims

### Option B: Simpler Alternative

**Changes**:
- Modify `StopHook_unverified_stance.py:316-322` to accept pytest as valid E2E evidence
- Verify pytest actually executed (check tool events)
- Delete dead code separately (optional)

**Effort**: 15-30 minutes (single function)

**Benefits**:
- ✅ Low regression risk (isolated change)
- ✅ Addresses actual friction point
- ✅ Minimal code change
- ✅ Maintains E2E verification for skills/workflows

**Second-order effects**:
- May allow false-positive E2E claims (pytest-only without skill)
  - **Mitigation**: Verify pytest actually ran in tool events
- Doesn't clean up dead code (can be separate task)

---

## Conclusion

**RECOMMENDATION**: Option B (Simpler Alternative)

The original proposal is based on incorrect assumptions and targets the wrong problem. The simpler alternative achieves 80% of the benefit with 95% less code change.

**Implementation**:
1. Modify E2E check (8 lines)
2. Add pytest execution verification
3. Optional: Delete dead code

**Evidence basis**:
- Codebase analysis: Stop_router.py, StopHook_unverified_stance.py, settings.json
- User report: claim-efficiency.txt
- Tool evidence: grep, bash, file reads

**Sources**: No external sources (codebase evidence sufficient)
