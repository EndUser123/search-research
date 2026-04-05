# Implementation Plan: Verification Claim Grounding Subsystem
**Date**: 2026-03-14
**Status**: COMPLETE (2026-03-15 — All phases implemented and tested)
**Priority**: HIGH (Reliability + Safety)

---

## Problem Statement

The Claude Code hook system fails to distinguish between a tool being used this turn and a claim being grounded in that tool output. The AI states hypotheses as confirmed facts without verifying the specific entities being claimed about. The result is destructive recommendations based on unverified conclusions.

Two concrete failure modes observed:
1. AI sees broken junction target, asserts Package has no skill/ directory without checking, recommends Remove-Item. The skill existed at a different path.
2. AI performs ritual self-correction (COG framework output) without verifying before acting again.

Root cause: Hooks check was any verification tool used this turn - a coarse binary signal. Required: does tool output from this turn reference the specific entity being claimed about.

---

## Context Analysis

Verified from code inspection:

evidence_store.py: SQLite-backed tool event store. Schema includes terminal_id column in tool_events table. terminal_id IS written by PostToolUse router. load_tool_events() filters by session_id only - terminal_id NOT used as filter. Confirmed cross-terminal contamination gap.

state/turn_markers/: Per-terminal turn marker files keyed turn_start_{session_id}__{terminal_id}.json. All observed values show turn_start_event_id: 0 - turn scoping not functioning correctly.

Stop_router.py: Routes Stop hooks in-process via ACTIVE_RUNTIME_HOOKS.

Existing Stop hooks: Stop_negative_existence_guard checks any-tool-used, Stop_unverified_existence_gate checks external URLs, StopHook_unverified_stance catches sycophancy patterns.

anti_sycophancy/overconfidence_detector.py: Catches causal assertions and catastrophizing. NOT wired into Stop router.

Multi-terminal failure confirmed: load_tool_events(session_id) returns events from all terminals sharing that session.

Turn scoping failure confirmed: All turn marker files show turn_start_event_id: 0.

---

## Existing Implementation Discovery

evidence_store.py load_tool_events(): filters by session_id only. Gap: no terminal_id filter.
evidence_store.py append_tool_event(): correctly accepts and stores terminal_id. No gap.
PostToolUse_router.py: Writes tool events with terminal_id. No gap.
state/turn_markers/*.json: turn_start_event_id always 0. Gap: writer not setting correct value.
Stop_negative_existence_guard.py: checks any tool used this turn. Gap: too coarse.
Stop_unverified_existence_gate.py: checks external resource claims. Gap: no entity-level matching.
StopHook_unverified_stance.py: catches sycophancy/empty-hedge patterns. Gap: misses hypothesis-as-fact pattern.
anti_sycophancy/overconfidence_detector.py: Not wired into Stop router. Gap: dead module.
Stop_router.py ACTIVE_RUNTIME_HOOKS: Missing new gate.
.claude/settings.json: Missing HYPOTHESIS_AS_FACT_GATE_ENABLED and HYPOTHESIS_AS_FACT_GATE_MODE.

---

## Test Discovery

Existing tests to preserve: tests/test_assumption_audit.py, tests/test_constitutional_enforcer.py, tests/test_hook_execution.py.

New test files required:
- tests/test_hypothesis_as_fact_detector.py
- tests/test_Stop_hypothesis_as_fact_gate.py
- tests/test_verification_claims.py
- tests/test_verification_engine.py
- tests/test_verification_isolation.py
- tests/test_verification_config_reload.py

---

## Proposed Solution

A phased evolution over existing infrastructure. No new receipt format, no new PostToolUse hooks, no new state directories.

Phase 1: Fix evidence filtering gap and add new Stop gate for hypothesis-as-fact claims. No refactoring of existing hooks.
Phase 2: Promote detector to shared verification/ substrate. Migrate existing hooks. Fix turn scoping.
Phase 3: Tests, observability, feature flags, rollback documentation.

Key design decisions:
- Terminal isolation via AND terminal_id in SQL query. One-line change, no schema migration.
- Turn scoping via existing turn markers once writer is fixed. Feature-flagged off by default.
- Phase 1 entity matching: path/filesystem entities only. Phase 2 expands.

---

## Implementation Plan

### Phase 1: Evidence Filtering + New Gate

**TASK-001**: Add load_tool_events_for_context to evidence_store.py
- File: evidence_store.py
- Action: New function with terminal_id AND session_id filter; return empty list if terminal_id empty (fail-safe); reuse existing ordering and limits
- Points: 2
- Acceptance: Two terminals same session return only their own events; missing terminal_id returns empty list. SCOPING NOTE: Phase 1 provides terminal-scoped isolation only — turn scoping is explicitly NOT in scope until TASK-013.
- Prerequisites: None

**TASK-002**: Verify and document terminal_id write path
- File: evidence_store.py, PostToolUse_router.py
- Action: Confirm terminal_id reaches DB row (verified via code review); add integration test
- Points: 1
- Acceptance: Integration test confirms terminal_id stored in tool_events row
- Prerequisites: TASK-001

**TASK-003**: Implement hypothesis_as_fact_detector module
- File: anti_sycophancy/hypothesis_as_fact_detector.py (new), tests/test_hypothesis_as_fact_detector.py (new)
- Action: RawClaim dataclass with text, subject_entity, claim_type, confidence, has_hedge, risk_domain; detect_claims(response_text) returning list of RawClaim; entity claim patterns, rule claim patterns, epistemic hedge detection. FIELD ALIGNMENT: RawClaim fields are intentionally 1:1 with the future Claim dataclass in TASK-007 (text→text, subject_entity→targets[0], claim_type→type, confidence→confidence, has_hedge→has_hedge, risk_domain→risk_domain) so Phase 2 is a rename+move, not a redesign.
- Points: 5
- Acceptance: Detects broken-junction-style sentences; detects rule assertions; correctly sets has_hedge for hedged and unhedged variants
- Prerequisites: None

**TASK-004**: Implement Stop_hypothesis_as_fact_gate.py
- File: Stop_hypothesis_as_fact_gate.py (new), tests/test_Stop_hypothesis_as_fact_gate.py (new)
- Action: run(data) entrypoint; extract session_id, terminal_id, response_text; call detect_claims; call load_tool_events_for_context; entity matching; warn or block per mode; log every decision with claim text and tool events considered. Entity matching for path claims MUST normalize separators (convert `\` to `/`) and resolve relative paths to absolute before comparison — this prevents Windows vs Unix path false-negatives.
- Points: 5
- Acceptance: Blocks ungrounded confident claims; allows hedged claims without evidence; allows confident claims grounded in tool events; respects HYPOTHESIS_AS_FACT_GATE_ENABLED and HYPOTHESIS_AS_FACT_GATE_MODE; path normalization unit test confirms `C:\foo\bar` matches `C:/foo/bar` in tool events. SCOPING NOTE: Phase 1 gate is terminal-scoped, not turn-scoped — acceptance tests must not assume turn isolation.
- Prerequisites: TASK-001, TASK-003

**TASK-005**: Wire into Stop_router.py and settings.json
- File: Stop_router.py, .claude/settings.json
- Action: Add to HOOK_SEQUENCE before Stop_negative_existence_guard; add to ACTIVE_RUNTIME_HOOKS; add HYPOTHESIS_AS_FACT_GATE_ENABLED=true and HYPOTHESIS_AS_FACT_GATE_MODE=warn to settings.json
- Points: 2
- Acceptance: Hook fires in Stop sequence; toggling env var disables without code change
- Prerequisites: TASK-004

**TASK-006**: Investigate turn_start_event_id = 0
- File: Turn marker writer code (to be identified)
- Action: Find why all turn markers show event_id 0; document findings; propose fix; no production change in Phase 1
- Points: 3
- Acceptance: Root cause documented; fix approach specified and reviewed
- Prerequisites: None

### Phase 2: Shared Verification Engine + Hook Migration

**TASK-007**: Create verification/claims.py
- File: verification/claims.py (new), verification/__init__.py (new), anti_sycophancy/hypothesis_as_fact_detector.py (refactor to wrapper), tests/test_verification_claims.py (new)
- Action: Claim dataclass with id, text, targets, type, confidence, risk_domain, has_hedge; extract_claims(response_text) returning list of Claim; dedicate tests/test_verification_claims.py to unit-testing Claim construction, field presence, and extract_claims() — do NOT rely solely on PH1 pass-through tests
- Points: 3
- Acceptance: PH1 tests pass using new Claim type; detector delegates to claims module; test_verification_claims.py covers at minimum: Claim dataclass field defaults, extract_claims() returns correct type list, hedge detection preserved, entity extraction preserved
- Prerequisites: TASK-003

**TASK-008**: Implement verification/engine.py
- File: verification/engine.py (new), tests/test_verification_engine.py (new)
- Action: ToolEventView wrapper over evidence_store events with normalized target and facts; build_verdicts returning list of VerificationVerdict; match_claim_to_events returning SUPPORTED, REFUTED, or SILENT
- Points: 8
- Acceptance: Supported absence claims with matching ls or glob output; silent claims for unrelated paths; rule claims require Read or Glob of relevant file
- Prerequisites: TASK-007, TASK-001

**TASK-009**: Refactor Stop_hypothesis_as_fact_gate to use engine
- File: Stop_hypothesis_as_fact_gate.py
- Action: Replace RawClaim and string matching with verification.claims and verification.engine; policy from VerificationVerdict; env flags unchanged. REGRESSION GUARD: Before removing any RawClaim pattern, run all TASK-004 acceptance tests and document which verdict each existing test case now maps to — any case that changes from block→pass must be explicitly justified.
- Points: 3
- Acceptance: Existing gate tests pass; engine verdicts drive policy decisions; regression mapping document confirms no unintended block→pass transitions
- Prerequisites: TASK-008

**TASK-010**: Migrate Stop_negative_existence_guard to engine
- File: Stop_negative_existence_guard.py, tests/test_Stop_negative_existence_guard.py
- Action: Replace any-tool-used heuristic with ABSENCE Claims and engine verdicts; block or warn when SILENT or REFUTED for FS_CRITICAL domain; preserve existing env flags
- Points: 5
- Acceptance: Broken-junction pattern caught by this hook; existing tests pass or updated; env flags unchanged
- Prerequisites: TASK-008, TASK-009

**TASK-011**: Migrate Stop_unverified_existence_gate to engine
- File: Stop_unverified_existence_gate.py
- Action: EXTERNAL domain Claims and engine verdicts requiring actual web or git fetch
- Points: 3
- Acceptance: Behavior equivalent or improved; tests for unverified URL and repo claims pass
- Prerequisites: TASK-008

**TASK-012**: Migrate StopHook_unverified_stance to engine
- File: StopHook_unverified_stance.py
- Action: Model stance as Claim objects; use engine for grounding check; preserve current detection behavior
- Points: 5
- Acceptance:
  1. Phase 1 calls extract_claims() for all non-empty responses (verify with logs)
  2. build_verdicts() returns SUPPORTED/REFUTED/SILENT for all stance claims (verify with test)
  3. Existing sycophancy detection patterns still trigger (verify with test cases from test_unverified_stance_hook.py)
  4. Graceful degradation: engine errors block with clear error message (fail-closed)
- Prerequisites: TASK-008

**TASK-013**: Fix turn scoping in load_tool_events_for_context
- File: evidence_store.py, turn marker writer
- Action: Fix turn_start_event_id writer; add id > turn_start filter when marker available; feature flag VERIFICATION_USE_TURN_SCOPING defaulting false. NOTE: TASK-013 scope and estimate are contingent on TASK-006 findings. If TASK-006 reveals turn_start_event_id=0 is a fundamental architecture gap (not a writer bug), raise a revised estimate before starting TASK-013.
- Points: 5 (subject to TASK-006 findings)
- Acceptance: Turn marker shows non-zero event_id; context query returns only current-turn events when flag enabled; flag off preserves Phase 1 behavior
- Prerequisites: TASK-006, TASK-013a, TASK-001

### Phase 3: Tests, Observability, Feature Flags

**TASK-013a**: Design review checkpoint after TASK-006 investigation
- File: .claude/hooks/plans/plan-20260314-verification-claim-grounding.md (update), docs/turn-scoping-design.md (new)
- Action: After TASK-006 root cause is documented, write a one-page design note (docs/turn-scoping-design.md) covering: root cause summary, chosen fix approach, known unknowns, revised estimate if >5pts. This document serves as the self-review gate before TASK-013 begins.
- Points: 1
- Acceptance: docs/turn-scoping-design.md exists and covers all four sections; TASK-013 prerequisites include this task
- Prerequisites: TASK-006

**TASK-014**: Multi-terminal isolation integration tests
- File: tests/test_verification_isolation.py (new)
- Action: Simulate two terminals t1 and t2 sharing session_id but different terminal_id; write tool events for t1 only; run Stop cycle for t2 with confident claim about same path; assert t2 blocked or warned; assert t1 passes
- Points: 3
- Acceptance: t2 blocked or warned despite t1 having relevant tool events; t1 passes with its own events
- Prerequisites: TASK-001, TASK-004

**TASK-014b**: End-to-end Stop cycle integration test
- File: tests/test_verification_end_to_end.py (new)
- Action: Single test module that exercises the full pipeline: inject synthetic response_text with a confident ungrounded claim → call Stop_hypothesis_as_fact_gate.run() with empty tool event store → assert block or warn outcome; repeat with matching tool event → assert pass. Also include the concrete failure mode from the Problem Statement: "Package has no skill/ directory" claim without prior Glob/Read of that path → assert blocked.
- Points: 2
- Acceptance: All three scenarios (block ungrounded, pass grounded, broken-junction pattern) covered; test is hermetic (no real SQLite write required — uses in-memory or temp DB)
- Prerequisites: TASK-004, TASK-005

**TASK-015**: Config reload behavior tests
- File: tests/test_verification_config_reload.py (new)
- Action: Simulate env or policy change between turns; verify next Stop invocation reflects new mode without restart
- Points: 2
- Acceptance: Mode change from warn to block takes effect on next turn
- Prerequisites: TASK-004, TASK-005, TASK-008

**TASK-016**: Per-terminal verification logging
- File: Stop_hypothesis_as_fact_gate.py or shared log module
- Action: Structured JSONL log per block or warn containing session_id, terminal_id, claim_id, claim_text, support_status, policy_outcome, tool event IDs considered. PII GUARD: claim_text MUST be truncated to 200 chars and stripped of email-like patterns (regex `[\w.+-]+@[\w-]+\.[\w.]+`) and path segments containing home directory markers (`~`, `Users`, `home`) before writing to log. TIMING: Logging MUST be active as soon as the gate is in WARN mode (wired in TASK-005) — do not wait for TASK-009 engine migration. Warn-mode data is the primary source for false-positive tuning before switching to block.
- Points: 2
- Acceptance: Log entries parseable as JSONL; all required fields present; one entry per decision; sanitization unit test confirms email addresses and home-dir paths are redacted in logged claim_text; log is written on WARN outcomes, not only BLOCK outcomes
- Prerequisites: TASK-004, TASK-005

**TASK-016b**: Latency benchmark for Stop gate overhead
- File: tests/test_verification_latency.py (new)
- Action: Benchmark test that measures wall-clock time for Stop_hypothesis_as_fact_gate.run() over 100 synthetic turns with varying response lengths (500, 2000, 8000 chars) and tool event store sizes (5, 20, 50 events). Assert p95 overhead ≤ 20ms. Run once before Phase 2 (TASK-009) merge and once after to catch regression.
- Points: 2
- Acceptance: Benchmark produces tabular output (chars × events × p95ms); p95 ≤ 20ms for all combinations; test marked `@pytest.mark.benchmark` so it's opt-in in CI
- Prerequisites: TASK-004, TASK-008

**TASK-017**: Feature flags and rollback documentation
- File: .claude/settings.json, docs/verification-hooks.md (new)
- Action: Document all env vars with defaults and descriptions; document rollback procedure; confirm conservative defaults in settings.json
- Points: 1
- Acceptance: Rollback procedure verified; all flags documented with defaults
- Prerequisites: TASK-005, TASK-009, TASK-010, TASK-011, TASK-012, TASK-013

---

## Risks, Success Criteria, Dependencies

### Risks
1. Turn marker writer broken in non-obvious way - fixing may change session-wide event scoping for existing hooks. Mitigation: feature-flag VERIFICATION_USE_TURN_SCOPING defaults off until tested.
2. False positive rate from claim detection - overly aggressive patterns block legitimate confident statements. Mitigation: start in warn mode; tune from logs before switching to block.
3. Claim entity matching brittle for non-path entities. Mitigation: Phase 1 covers path and filesystem entities only; Phase 2 expands.
4. TASK-008 (verification/engine.py, 8pts) is the critical-path blocker for TASK-009, 010, 011, 012, 013 simultaneously. A 2× overrun delays all Phase 2 work by an equivalent amount. Mitigation: time-box TASK-008 to 2 sessions; if not near complete, scope-reduce by deferring EXTERNAL domain support (TASK-011) to Phase 3 and shipping engine with FS_CRITICAL domain only. PARTIAL SHIP OPTION: Under time pressure you can ship TASK-009 (Stop_hypothesis_as_fact_gate on engine) + FS_CRITICAL domain only and leave Stop_negative_existence_guard, Stop_unverified_existence_gate, and StopHook_unverified_stance on their current pre-engine implementations — they remain safe and functional, just not engine-backed.

### Success Criteria
- Two terminals sharing a session: t1 events do NOT satisfy t2 verification checks
- Package has no skill/ directory without Read or Glob of that path triggers warn or block
- Per documentation X does not need Y without Read of that doc triggers warn or block
- Hedged claims pass without intervention
- Claims with matching entity in tool output pass
- Stop_router.py latency overhead under 20ms additional per turn

### Dependencies
- CLAUDE_TERMINAL_ID must be set per process. Already in place via SessionStart_terminal_id.py.
- evidence_store.py schema already has terminal_id column. No migration needed.
- Existing hook env-flag rollback pattern must be preserved for all refactored hooks.
- TASK-006 findings must be reviewed before TASK-013 implementation begins.

### Context Overflow Prevention Rules
- Each task agent writes outputs to disk; returns only the Result Envelope (see `.claude/skills/shared/result-envelope.md`) — no inline code, no inline diffs
- Phase 1 → Phase 2 boundary: start fresh session via handoff system; load phase summary only, not full conversation history
- Sequential task execution within a phase — do not parallelize even when prerequisites allow it; tasks that produce large artifacts (diffs, analyses, module rewrites) are high-output and must run one at a time
- TASK-008 requires a spike task (type signatures only, no implementation) before full work begins — it is a high-output task and must not run in parallel with anything
- When only part of a file is relevant, use `Grep` + `offset`/`limit`; if a full read is genuinely needed and the file is clearly large, write a summary artifact and return a pointer rather than inlining the content
