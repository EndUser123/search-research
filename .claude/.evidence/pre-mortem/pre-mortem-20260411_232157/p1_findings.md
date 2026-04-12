# Phase 1 Findings — Handoff Skill Invocation Goal Drift Fix

## Triage Classification
**code** — Hook scripts (transcript.py, PreCompact_handoff_capture.py, handoff_v2.py) with test coverage

## Dispatched Specialists
- **adversarial-logic**: Regex correctness, pattern matching soundness
- **adversarial-state-machine**: Snapshot lifecycle, state transitions, defensive fallbacks
- **adversarial-io-validation**: Path safety, file I/O, transcript operations
- **adversarial-testing**: Test coverage gaps, integration test failures
- **adversarial-quality**: Maintainability, tech debt

## Specialist Findings Summary

### adversarial-logic
**Domain:** Regex and conditional logic
**Key findings:**
- No significant issues found. Three-layer fix is logically sound.

### adversarial-state-machine
**Domain:** Snapshot lifecycle and state transitions
**Key findings:**
- [HIGH] STATE-001: Defensive fallback has silent failure modes — extract_preceding_message can return None or empty string, creating indeterministic goal corruption
- [MEDIUM] STATE-002: extract_preceding_message has no semantic validation — can return a meta-invocation as the goal fallback
- [MEDIUM] STATE-004: Three-layer defense is degrading rather than deterministic — snapshot goal_origin is ambiguous
- [LOW] STATE-003: Regex doesn't support ---flag multi-dash convention

### adversarial-io-validation
**Domain:** Path safety, I/O validation
**Key findings:**
- No significant issues found. Path safety and I/O validation are properly implemented.

### adversarial-testing
**Domain:** Test coverage and integration correctness
**Key findings:**
- [HIGH] TEST-001: test_tasks_snapshot_flows_through_handoff_pipeline fails — tasks not appearing in restore message
- [HIGH] TEST-002: test_invalid_checksum_is_rejected_without_task_context fails — checksum validation not blocking restore
- [MEDIUM] TEST-003: test_full_flow_expired_envelope_rejected may flap on clock skew boundary
- [LOW] TEST-004: String-matching test assertions are fragile to formatting changes

### adversarial-quality
**Domain:** Maintainability, tech debt
**Key findings:**
- No significant issues found.

## Consolidated Findings

### Logical Gaps & Inconsistencies
1.1. [HIGH] (source: adversarial-state-machine) — Defensive fallback silent failure: extract_preceding_message returns None when string normalization causes exact-match to miss the transcript entry. The conditional `if preceding and preceding.strip()` correctly short-circuits on None, but the preceding message may itself be whitespace-only or a meta-invocation. Fix: add explicit None guard + validate preceding message with is_meta_instruction() before using as goal (PreCompact_handoff_capture.py:634-638)

### Hidden Assumptions & Fragile Dependencies
2.1. [MEDIUM] (source: adversarial-state-machine) — extract_preceding_message has no semantic validation and can return a preceding message that is itself a skill invocation, violating the goal-skipping intent. Fix: validate returned preceding with is_meta_instruction() (transcript.py:1197-1263)
2.2. [MEDIUM] (source: adversarial-state-machine) — The snapshot goal field has no goal_origin marker — downstream consumers cannot distinguish a correct user goal from a degraded skill-args fallback. Fix: add goal_origin field to snapshot (PreCompact_handoff_capture.py)
2.3. [LOW] (source: adversarial-state-machine) — Regex r'^/[a-z][a-z0-9_-]*(?:\s+|--?\s)' does not support ---flag convention (transcript.py:57)

### Missing Obvious Actions / Best Practices
3.1. [HIGH] (source: adversarial-testing) — Integration test TEST-001: test_tasks_snapshot_flows_through_handoff_pipeline fails — pending_operations shows 0 instead of 1. tasks_snapshot captured but not surfaced in restore message (test_handoff_integration.py:254)
3.2. [HIGH] (source: adversarial-testing) — Integration test TEST-002: test_invalid_checksum_is_rejected_without_task_context fails — checksum validation not enforced at SessionStart. Invalid checksum accepted as valid restore (test_handoff_integration.py:282)
3.3. [MEDIUM] (source: adversarial-testing) — test_full_flow_expired_envelope_rejected may flap at expires_at == now() boundary — needs explicit boundary test (test_handoff_full_integration.py:120)

### Risks and Edge Cases
4.1. [MEDIUM] (source: adversarial-state-machine) — If META_PATTERNS fails due to normalization, defensive fallback fails due to string mismatch, AND pending_operations doesn't capture the skill as in_progress — all three layers fail silently and skill args become the goal with no warning
4.2. [LOW] (source: adversarial-testing) — String-matching test assertions (e.g., `assert "pending_operations: 1 pending" in context`) break on cosmetic format changes

### Concrete Recommendations
5.1. [HIGH] Add None guard and is_meta_instruction() validation to defensive fallback (PreCompact_handoff_capture.py:634-638)
5.2. [HIGH] Add goal_origin field to snapshot to make degraded states explicit
5.3. [HIGH] Fix TEST-001: surface tasks_snapshot in pending_operations display (handoff_v2.py)
5.4. [HIGH] Fix TEST-002: enforce checksum validation before evaluate_for_restore (SessionStart_handoff_restore.py)
5.5. [MEDIUM] Add is_meta_instruction() check on extract_preceding_message result before using as goal fallback (transcript.py)
5.6. [MEDIUM] Fix TEST-003: add explicit boundary test for expires_at == now()
5.7. [LOW] Update META_PATTERNS regex to support ---flag: r'^/[a-z][a-z0-9_-]*(?:\s+|-{1,2}\s)' (transcript.py:57)

### Open Questions / Unknowns
6.1. (source: adversarial-state-machine) — Under what conditions does extract_last_substantive_user_message normalize the goal string differently from transcript entries? If whitespace normalization differs, exact-match in extract_preceding_message fails silently.
6.2. (source: adversarial-state-machine) — When pending_operations is populated from extract_pending_operations(), does it correctly identify skill:type with state=in_progress in all cases? If not, Layer 3 warning would not fire even if Layers 1 and 2 failed.
