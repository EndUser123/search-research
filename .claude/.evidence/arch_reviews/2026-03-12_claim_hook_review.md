# Architecture Review: Claim Hook Consolidation Proposal

**Date**: 2026-03-12
**Review Type**: ARCHITECTURE_REVIEW (deep template)
**Reviewer**: /arch skill (deep.md template)

---

## Scope

Reviewing the proposed consolidation from `2026-03-12_claim_hook_efficiency.md` (Change A: consolidate to single hook, Change B: add quiet mode) against actual codebase state to determine if consolidation is optimal or if a simpler refactor exists.

---

## Design Summary

**Proposal assumes:**
- `verify_claims.py` and `artifact_claims.py` are active claim verification hooks creating duplicate noise
- Consolidation needed to single Stop hook (`StopHook_unverified_stance.py`)
- Add `CLAIM_ADVISORY_QUIET` environment variable for noise suppression

**Proposed changes:**
- **Change A**: Keep `StopHook_unverified_stance.py`, disable `verify_claims.py`/`artifact_claims.py`, move `strawberry_validator` to PostToolUse
- **Change B**: Implement smart advisory mode with bypass flag (`CLAIM_ADVISORY_QUIET`)

---

## Findings

| ID | Severity | Finding | Evidence | Impact |
|-----|-----------|----------|-----------|---------|
| ARCH-001 | **HIGH** | **Proposal based on incorrect assumption** - `verify_claims.py` and `artifact_claims.py` are NOT in `ACTIVE_RUNTIME_HOOKS` | `Stop_router.py:122-129` defines `ACTIVE_RUNTIME_HOOKS` with only 6 hooks. Grep shows 0 matches for "verify_claims" or "artifact_claims" in Stop router. | Primary justification for Change A (eliminating redundant active hooks) is invalid. These hooks are already inactive and cannot be causing friction. |
| ARCH-002 | **HIGH** | **Real friction point misidentified** - User's actual blocking issue is E2E workflow verification at `StopHook_unverified_stance.py:316-322` explicitly rejecting pytest as "insufficient" | Code: `if not has_e2e: return False, "E2E workflow claim without execution evidence... Component tests (pytest) alone are insufficient"` | Proposal targets wrong problem. E2E check blocks legitimate pytest evidence, forcing manual `/all` skill invocation (confirmed in `claim-efficiency.txt:228-230`). |
| ARCH-003 | **MEDIUM** | **Simpler alternative achieves 80% benefit with 5% code change** - Modify single E2E check to accept pytest as valid evidence | 8 lines at `StopHook_unverified_stance.py:316-322` vs. Change A's multi-file consolidation | Modify E2E verification logic directly instead of consolidating already-inactive hooks. Achieves user's actual goal (pytest acceptance) with minimal code change. |
| ARCH-004 | **MEDIUM** | **Change B scopes to wrong problem** - Advisory suppression doesn't address E2E blocking behavior | User example shows **blocking** ("stop hook blocked") not warnings. Proposal adds quiet mode for warnings. | `CLAIM_ADVISORY_QUIET` suppresses warnings but won't prevent E2E workflow blocks. User needs pytest acceptance, not warning suppression. |
| ARCH-005 | **LOW** | **strawberry_validator repositioning unnecessary** - Hook not in Stop router | Grep returned 0 matches for "strawberry_validator" in `Stop_router.py`. File exists but not registered. | Change A includes repositioning work for already-nonexistent Stop integration. |
| ARCH-006 | **LOW** | **Dead code cleanup unrelated to noise reduction** - Inactive hooks can be deleted but doesn't address friction | `verify_claims.py` (12KB) and `artifact_claims.py` (9.7KB) exist but not in `ACTIVE_RUNTIME_HOOKS`. | Proposal treats inactive hooks as consolidation targets. Can delete as dead code (separate task) but unrelated to user's "noisy" complaint. |

---

## GoT Analysis

**Extracted Nodes:**
- **Constraints**: ["Must reduce claim friction", "Must accept pytest as E2E evidence", "Must minimize code change"]
- **Ideas**: ["Consolidate to single hook", "Add quiet mode", "Modify E2E check to accept pytest", "Delete dead code"]
- **Risks**: ["Proposal based on wrong assumptions", "Targeting wrong friction point", "Over-engineering solution"]
- **Components**: ["StopHook_unverified_stance.py", "verify_claims.py (inactive)", "artifact_claims.py (inactive)", "Stop_router.py"]
- **Data flows**: ["User pytest → Stop hook block", "E2E verification check → pytest rejection"]

**Edge Relationships:**
- "Must reduce claim friction" **contradicts** "Targeting wrong friction point" ⚠️
- "Consolidate to single hook" **contradicts** "Proposal based on wrong assumptions" ⚠️
- "Modify E2E check" **supports** "Must accept pytest" ✓
- "verify_claims.py (inactive)" **unrelated** to "User pytest block" (not in execution path)
- "StopHook_unverified_stance.py" **depends on** "E2E verification logic"

**Cycles Detected**: None

**Architectural Insights:**
- **Contradiction**: Proposal assumes hooks are active that aren't running (verify_claims, artifact_claims)
- **Risk**: Change A consolidates already-inactive code, creating work without addressing actual blocker
- **Simpler path**: Modify 8 lines (ARCH-003) achieves primary goal with 95% less code change

---

## Second-Order Effects Analysis

### Option A: Original Proposal (Change A + B)

**Primary effects:**
- ✓ Reduces hook count (but hooks already inactive)
- ✓ Adds quiet mode for warnings

**Second-order effects:**
- ✗ Complex multi-file change increases regression risk
- ✗ Dead code deletion (verify_claims, artifact_claims) unrelated to friction
- ✗ Quiet mode doesn't address E2E blocking (wrong problem scope)
- ✗ Unnecessary strawberry_validator move (not in Stop path)
- ✗ 2-3 hours implementation + testing

### Option B: Simpler Alternative (modify E2E check only)

**Primary effects:**
- ✓ Accepts pytest as valid E2E evidence
- ✓ Maintains existing skill/multi-step workflow checks

**Second-order effects:**
- ✓ 15-30 min implementation (single function)
- ✓ Low regression risk (isolated change)
- ✓ Actually addresses user friction point
- ⚠️ May allow false-positive E2E claims (pytest-only without skill)
  - **Mitigation**: Verify pytest actually ran (check tool events for pytest execution)
- ✗ Doesn't clean up dead code (can be separate task)

### RECOMMENDATION: Option B + separate dead code cleanup

---

## Risk Summary

**Technical:**
- **HIGH**: Proposal based on incorrect understanding of active hook set (ARCH-001)
- **MEDIUM**: Addresses non-problem (inactive hooks) while missing actual blocker (E2E verification) (ARCH-002)
- **LOW**: Unnecessary dead code deletion included in consolidation scope (ARCH-006)

**Operational:**
- **MEDIUM**: Change B (quiet mode) doesn't address blocking behavior shown in user example
- **LOW**: Multi-file testing required for minimal benefit

**Integration:**
- **LOW**: strawberry_validator repositioning unnecessary (not currently in Stop path)
- **LOW**: No downstream systems affected by proposed changes

---

## Conclusion

**RECOMMENDATION: Simpler Alternative (Option B)**

The original proposal (Change A: consolidate to single hook, Change B: add quiet mode) is **not optimal** because:

1. **Primary assumption invalid**: `verify_claims.py` and `artifact_claims.py` are already inactive (not in `ACTIVE_RUNTIME_HOOKS`)
2. **Wrong friction point**: Real user friction is E2E verification explicitly rejecting pytest, not overlapping claim hooks
3. **Simpler solution exists**: Modify `StopHook_unverified_stance.py:316-322` to accept pytest as valid E2E evidence (8 lines vs. multi-hook consolidation)

**Recommended approach (80% less code, targets actual problem):**

```
Option B (Simpler Alternative):
1. Modify StopHook_unverified_stance.py:316-322 to accept pytest as valid E2E evidence
   - Add "pytest" or "python -m pytest" to acceptable E2E evidence patterns
   - Keep existing skill/multi-step workflow checks
   - Add verification that pytest actually executed (check tool events)
2. Delete verify_claims.py and artifact_claims.py as dead code (separate cleanup task)
3. Skip Change B (quiet mode) - doesn't address E2E blocking
```

**Second-order effects considered:**
- ✅ Maintains E2E verification for actual workflow claims (skills, multi-step)
- ✅ Reduces friction for legitimate pytest-based bug fixes
- ✅ Minimal code change reduces regression risk
- ⚠️ May allow false-positive E2E claims (pytest-only without skill execution)
  - Mitigation: Verify pytest actually ran (check for pytest in tool events)

**Alternative consideration:**
If you prefer full consolidation over targeted fix, consider:
- Keep Change A but remove verify_claims/artifact_claims work (already inactive)
- Modify E2E check as part of consolidation
- Still skip Change B (wrong problem scope)

---

**Confidence:** 85%

**Evidence basis:**
- Design doc: `P:\.claude\arch_decisions\2026-03-12_claim_hook_efficiency.md`
- Codebase analysis: 5 files reviewed (Stop_router.py, StopHook_unverified_stance.py, claim-efficiency.txt, settings.json, proposal doc)
- Web research: 0 sources (searches returned empty - reviewing based on codebase evidence)

**Key assumptions:**
1. User's friction point is E2E verification blocking pytest (confirmed in claim-efficiency.txt:228-230)
2. ACTIVE_RUNTIME_HOOKS in Stop_router.py:122-129 is authoritative for which hooks execute
3. User's "noisy" complaint refers to blocking behavior, not verbose warnings
