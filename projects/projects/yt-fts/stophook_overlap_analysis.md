# StopHook Overlap Analysis

**Created**: 2026-03-10
**Task**: TASK-000-A (E2E Verification Enforcement Plan)
**Status**: COMPLETE

---

## Executive Summary

Two Stop hooks were analyzed for pattern overlap:
1. `Stop_verification_gate.py` (141 lines)
2. `StopHook_unverified_stance.py` (563 lines)

**Decision**: KEEP SEPARATE (coordinate, don't merge)

**Rationale**: Hooks serve different purposes with minimal actual overlap.

---

## Hook 1: Stop_verification_gate.py

**Purpose**: Block responses that violate systematic diagnostic protocols.

**Patterns**:
- BEHAV-001: Premature solution jump without verification
- BEHAV-002: Acceptance of first plausible explanation
- BEHAV-003: Insufficient verification before claims
- BEHAV-004: Jumping between diagnostic approaches

**Implementation**: Simple regex-based, no evidence store integration, exits with code 1.

---

## Hook 2: StopHook_unverified_stance.py

**Purpose**: Detect anti-sycophancy patterns and completion claims without runtime evidence.

**Patterns**:
- Unfounded system claims (8 patterns)
- Completion claims (5 patterns)
- E2E workflow claims (4 patterns)
- Anti-sycophancy stance (external module)

**Implementation**: Evidence store integration, session-scoped verification, caching, telemetry, JSON output.

---

## Overlap Analysis

### Apparent Overlap: BEHAV-003 vs Completion Claims

**BEHAV-003**: "The problem is X" (without test evidence) - Diagnostic workflow violation

**COMPLETION_PATTERNS**: "all tests pass", "fixed" (without runtime tools) - Success declaration violation

**Key Difference**: Different phases with different expectations
- Investigation phase: State hypotheses, test systematically
- Completion phase: Demonstrate actual runtime success

### No Double-Blocking Risk

Both hooks can run without conflict because:
1. Different trigger patterns
2. Different enforcement purposes
3. Settings.json runs both in parallel (any block blocks response)

---

## Comparison Matrix

| Aspect | Stop_verification_gate | StopHook_unverified_stance |
|--------|------------------------|----------------------------|
| Primary purpose | Diagnostic workflow | Anti-sycophancy + completion |
| Lines of code | 141 | 563 |
| Evidence store | No | Yes |
| Session awareness | No | Yes |
| Caching | No | Yes (<10ms) |
| Telemetry | No | Yes |
| Configurable mode | No | Yes (warn/block) |
| JSON output | No | Yes |
| Complexity | Simple (regex) | Complex (evidence queries) |
| Tier 3 (E2E) support | No | Yes |

---

## Conflicts Identified

**NO CONFLICTS DETECTED**

1. Pattern separation: Different regex patterns
2. Phase separation: Investigation vs Completion
3. Complementary enforcement: Both can run independently
4. No shared state: Independent execution paths

---

## Recommendation: KEEP SEPARATE

**Reasons**:

1. Different purposes (diagnostic workflow vs anti-sycophancy)
2. Different sophistication levels (simple vs complex)
3. Different implementations (regex vs evidence store)
4. Evolution path (legacy vs actively developed)
5. Performance (zero overhead vs <10ms with caching)

**Coordination Strategy**:

Both hooks registered in settings.json and run in **parallel**:
- StopHook_unverified_stance: Evidence-backed, session-aware, catches completion claims
- Stop_verification_gate: Lightweight behavioral patterns, catches diagnostic workflow violations

**Parallel execution**: Both hooks run simultaneously. If either blocks, response is blocked.

**No coordination needed**: Different trigger patterns mean they catch different violations. When both detect violations in same response, user sees one violation message (implementation detail).

---

## Alternative Rejected: Merge

**Why NOT to merge**:

1. Complexity explosion (563 lines already complex)
2. Single responsibility violation
3. Performance regressions
4. Testing burden
5. Deployment risk

Merge would require multi-week refactoring effort (out of scope for TASK-000-A).

---

## Action Items

**Completed (TASK-000-A)**:
- Documented BEHAV-001 through BEHAV-004 patterns
- Documented completion claim patterns
- Identified overlapping patterns (BEHAV-003 vs COMPLETION_PATTERNS)
- Decision: Keep separate, parallel execution via settings.json registration

---

## Appendix: Pattern Examples

**BEHAV-003 Violations**:
- "The problem is a missing import."
- "This is caused by the thread race condition."

**COMPLETION_PATTERNS Violations**:
- "All tests pass."
- "Bug fixed and tested."

**Anti-Sycophancy Violations**:
- "That sounds like an exaggeration." (no verification)
- "I doubt that's correct." (no evidence)

---

**Analysis complete. No merge required.**
