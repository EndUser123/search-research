# Architecture Decision: Loop-Core Integration

**Date:** 2025-03-15
**Template:** fast (Python domain)
**Query:** what can we integrate loop-core with? What should we integrate loop-core with?

---

## Decision Statement

Loop-core should integrate with verification systems (TASK-016) and workflow orchestration skills (/code, /plan-workflow) to enable PRD/spec-driven behavior and deterministic exit logic. The goal is to close the feedback loop between autonomous execution and requirement validation.

## Options

**Option A: Integrate loop-core with verification workflow** (proposed)
- **Pro**: Enables PRD-driven behavior (original plan requirement TASK-007, TASK-015, TASK-016), closes feedback loop, allows exit policy to require verification pass
- **Con**: Adds verification latency to each loop iteration (complexity increase), requires prd-verifier skill implementation (2-8 hours estimated)
- **Differs on:** Verification-first vs execution-only approach

**Option B: Keep loop-core as pure state/orchestration layer** (status quo)
- **Pro**: Maintains separation of concerns (loop-core = state/policy only), lower complexity, faster iteration cycles
- **Con**: Cannot enforce PRD/spec requirements at loop boundaries, missing key Ralph Loop requirement (deterministic exit based on verification), requires external verification calls
- **Differs on:** Stateless state machine vs verified state machine

## Recommendation

**Option A is better than Option B** because the Ralph Loop Platform architecture explicitly requires "PRD/spec-driven verification" and "deterministic exit logic" as stated in the plan (lines 21-26, 147-148). Loop-core cannot fulfill its core mission without verification integration—Option B leaves the job half-done.

## Implementation

**Before (current state):**
```python
# scripts/loop_policy.py (TASK-005)
def should_exit(tasks, loop_state, config) -> bool:
    """Check exit conditions: completion_indicators, EXIT_SIGNAL, verification"""
    # Current: checks completion_indicators and EXIT_SIGNAL
    # Missing: verification pass requirement
```

**After (Option A):**
```python
# scripts/loop_policy.py (enhanced)
def should_exit(tasks, loop_state, config) -> bool:
    """Check exit conditions: completion_indicators, EXIT_SIGNAL, verification"""

    # Load exit policy from config
    policy = config.get("exit_policy", {})

    # Check completion indicators
    min_indicators = policy.get("min_completion_indicators", 2)
    completion_count = sum(1 for t in tasks if t.get("status") == "complete")

    # Check EXIT_SIGNAL (manual override)
    exit_signal = loop_state.get("loop_metadata", {}).get("exit_signal", False)

    # NEW: Check verification requirement
    verification_required = policy.get("require_verification_pass", False)
    verification_passed = loop_state.get("verification_status", {}).get("passed", False)

    # Dual-condition gate: (indicators AND signal) OR (verification passed)
    exit_on_completion = (
        completion_count >= min_indicators and
        exit_signal
    )

    exit_on_verification = (
        verification_required and
        verification_passed
    )

    return exit_on_completion or exit_on_verification

def should_run_verifier(loop_state, config) -> bool:
    """Check if verification should run this iteration"""
    policy = config.get("verification", {})

    # Only run if verification is enabled
    if not policy.get("enabled", False):
        return False

    # Check if already passed (skip re-verification)
    verification_status = loop_state.get("verification_status", {})
    if verification_status.get("passed", False):
        return False

    # Check if we're in exit zone (completion indicators met)
    completion_indicators = loop_state.get("completion_indicators", 0)
    min_indicators = config.get("exit_policy", {}).get("min_completion_indicators", 2)

    # Run verification when near completion
    return completion_indicators >= (min_indicators - 1)
```

**New integration point:**
```python
# skills/loop-core/SKILL.md (enhanced workflow)
# After task completion check, before exit decision:

if loop_policy.should_run_verifier(loop_state, config):
    # Call prd-verifier skill
    verification_result = await run_verification(
        plan_path=loop_state["metadata"]["plan_path"],
        prd_path=config.get("verification", {}).get("prd_path")
    )

    # Update loop state with verification result
    loop_state["verification_status"] = {
        "passed": verification_result["passed"],
        "timestamp": datetime.now().isoformat(),
        "report_path": verification_result["report_path"]
    }

    # Log decision
    loop_observability.log_decision(
        terminal_id=terminal_id,
        event="verification_completed",
        payload={
            "passed": verification_result["passed"],
            "findings": verification_result.get("findings", [])
        }
    )
```

**Rollback:** Revert to current implementation (remove verification checks), keep verification as external workflow step.

## Quick Ramifications

- **Break anything?**: No—verification is optional (config flag), backward compatible
- **Edge cases**: Verification timeout/crash handling (should fail gracefully, continue loop), verification cost/quota management (may need rate limiting)
- **Constraints**: LLM API quota for verification calls, iteration latency increase (verification adds 30-60 seconds per exit-bound iteration)

## Confidence

Confidence: 75% — Based on plan requirements (explicit verification requirements in lines 21-26, 147-148) and architectural coherence (verification is explicit Layer 4 component in plan), but prd-verifier skill is currently stub-only (TASK-015 marked optional, TASK-016 pending), requiring estimated 2-8 hours implementation before integration works.

## Adversarial Self-Review

Weakest assumption: prd-verifier skill can be implemented effectively within 2-8 hours. If wrong: TASK-015 and TASK-016 may be significantly larger (20+ hours), delaying integration benefit. Mitigation: Implement verification as optional feature flag (can ship loop-core without verification enabled, add verification later when prd-verifier is ready).

---

## Implementation Order

1. **Implement prd-verifier skill** (TASK-015) — 2-8 hours
   - Create `skills/prd-verifier/` structure
   - Implement verification logic (compare implementation against PRD)
   - Add test coverage

2. **Wire verification into exit policy** (TASK-016) — 1-2 hours
   - Enhance `loop_policy.py` with verification checks
   - Update `/loop-core` skill workflow
   - Add tests for verification integration

3. **Update config schema** — 30 minutes
   - Add `verification.enabled` field
   - Add `verification.prd_path` field
   - Add `exit_policy.require_verification_pass` field

4. **Add observability** — 1 hour
   - Log verification decisions to `decision.log`
   - Update metrics with verification status
   - Add tests for observability

Estimated total effort: 4.5-11.5 hours

---

**Sources:**
- Plan requirements: P:/packages/loop-core/plans/plan-20260314-ralph-loop-platform.md
- Current implementation: P:/packages/loop-core/scripts/loop_policy.py
- Verification contract: P:/packages/loop-core/skills/prd-verifier/SKILL.md
