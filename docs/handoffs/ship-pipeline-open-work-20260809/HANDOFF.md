---
thread_id: ship-pipeline-open-work-20260809
parent_handoff_path: none
current_session_id: 019fe4c1-43c3-7432-b211-926e806dd7a6
produced_at: 2026-08-09T00:00:00Z
last_updated_at: 2026-08-09T00:00:00Z
status: OPEN
handoff_type: implementation_plan
---

# HANDOFF: ship-pipeline open work (consolidated 2026-08-09)

## Status
OPEN — consolidated from 4 prior handoffs. All done/superseded ship handoffs
were deleted; this is the single source of truth for remaining ship-pipeline work.

## Objective
Complete the remaining open work on the ship-py verify-and-publish pipeline.
This handoff consolidates genuinely-open items from:
- `ship-py-hardening-20260805` (items 5-8 MOOT — ship-rhai.rhai deleted; 1-4,9,10,12,13 DONE)
- `ship-py-remaining-gaps-20260808` (item 7 DONE — _format_version now functional)
- `ship-py-phase2-functionality-composition-20260809` (Phase 1+2 shipped)
- `singh-execution-reality-middleware-20260808` (distinct work item, folded here)

## What's already done (don't re-do)

- Cross-model validation phase shipped (commit 6f7d324) — see [[orchestrator-controlled-cross-model-validation-ship-py]]
- Polling loop + anti-fabrication gates + transition chain + path validation (commit ee28569)
- abort subcommand + secret-scan + fmea-scan + design-check + babysit + version-bump (Phase 1+2, session 019fe403)
- ship_receipt.py exists (66KB) — receipt generation is automated
- _format_version now functional (v3, used for mid-flight migration)
- PreToolUse phase-gate hook shipped (commit 5c1e1b0)
- Verdict gate blocks SHIP DONE when review_findings missing
- 80 tests passing, ruff clean

## Remaining open work

### Track A: Test quality (from ship-py-remaining-gaps)

**A1.** `test_pauses_at_review_when_no_review_findings` — still uses unfixed
`patch('phases.run_all._execute_phase')` without `return_value=0` in at least
one test case. Works by accident; crashes if a deterministic phase is added
between check and review. Fix: ensure ALL `_execute_phase` patches use
`return_value=0`.
- File: `~/.grok/skills/ship-py/tests/test_run_all.py`

**A2.** `test_pause_emits_findings_path` — asserts only `result == 0`, never
checks the canonical path appears in output. Fix: use `capsys` to capture
stdout and assert the path string.
- File: `~/.grok/skills/ship-py/tests/test_run_all_integration.py`

**A3.** Test state isolation — tests don't use a shared `tmp_artifacts` fixture.
Real state files at `P:/.artifacts/ship-py/test-session/` can leak between
tests. Fix: adopt the `tmp_artifacts` fixture pattern from `test_ship_orchestrator.py`.

### Track B: Phase consistency + enforcement (from ship-py-remaining-gaps)

**B1.** `refactor.py` silently passes when findings file is missing (unlike
`risk.py` which blocks). When `has_code_files=True` but no findings file
exists, refactor.py falls through to empty default. Fix: block rather than
silently passing.
- File: `~/.grok/skills/ship-py/__lib/phases/refactor.py`

**B2.** `correction_classifier.py` uses substring match for `no_detector_types`
— `[ft for ft, det in detector_map.items() if "NO DETECTOR" in det]` is fragile
to renaming. Fix: use a structured marker.
- File: `~/.grok/scripts/correction_classifier.py`

**B3.** Verdict phase only WARNS on chain breakage — `chain_warning` is added
to summary but doesn't change return code. A broken tamper-evident chain at
verdict time should be a hard block (return 2), not a warning.
- File: `~/.grok/skills/ship-py/__lib/phases/verdict.py` (~line 117)

**B4.** Polling-loop timeout has no retry cap — re-invocation retries
indefinitely with no exponential backoff. Fix: add retry counter and hard
block after N timeouts.
- File: `~/.grok/skills/ship-py/__lib/phases/run_all.py`

### Track C: Stop hook regex (from ship-py-hardening Finding 11)

**C1.** Stop hook `quality_gate.py` regex `_SHIP_PY_CLAIM_PATTERNS` false-positive
matches "ship-py cannot complete" as a completion claim. The ABORTED verdict
recognition (commit 083e493) prevents the worst feedback loop, but the regex
fix (negative lookahead for "cannot/unable") is still needed for non-aborted cases.
- File: `~/.grok/hooks/scripts/quality_gate.py:163-164`

### Track D: Phase 2 documentation + testing (from ship-py-phase2)

**D1.** Tests for Phase 2 features — design_check, babysit, publish version-bump,
/why-in-fix PAUSE_INSTRUCTIONS, cross-model review PAUSE_INSTRUCTIONS.
**Note:** cross-model review PAUSE_INSTRUCTIONS (P2-1) is now superseded by the
shipped cross-validate phase — skip that test, write tests for the other 4.

**D2.** Enrich changelog generation in publish phase — include commit messages
(currently only version bumps and file counts).

**D3.** design-check doc-matching — improved heuristic landed but may still
produce false positives on common skill names.

**D4.** Document design-choice audit as AGENTS.md rule — currently only in wiki
concept `[[design-choice-audit-challenge-every-decision-against-first-principles]]`
+ 6 skills, not in the governing rules file.

### Track E: Singh execution-reality middleware (distinct work item)

**E1.** Design + implement the Singh payload-response misalignment heuristic
(~30 lines of Python). This is the THIRD specification-gaming layer:
- Layer 1 (DONE): polling loop — prevents continuation abandonment
- Layer 2 (DONE): cross-model validation — prevents review-finding fabrication
- Layer 3 (OPEN): Singh heuristic — prevents tool-output fabrication (agent
  claims tool returned X when it returned Y)

**Source:** Singh KDD 2026 Workshop — 56.6% fabrication rate measured; heuristic
catches with 0% false positive rate under neutral prompts.
**Wiki:** [[making-llm-agents-honestly-execute-skills-solution-stack]] §2
**Pattern:** for every (tool_payload, agent_response) pair, if payload is
null/malformed AND response contains data claims → flag as Fabrication.

This is a distinct work item with its own design needs. It was a separate
handoff (`singh-execution-reality-middleware-20260808`) folded here for
consolidation. If the operator prefers to split it back out, that's fine —
the point of consolidation is one place to look, not forcing unrelated work
into one implementation pass.

## Acceptance criteria

- Track A: 3 test-quality fixes; all tests still pass
- Track B: refactor.py blocks on missing findings; verdict returns 2 on broken chain; polling has retry cap
- Track C: quality_gate.py regex excludes "cannot/unable" patterns
- Track D: Phase 2 tests written (4 of 5; skip P2-1 superseded)
- Track E: Singh heuristic designed (separate /design run) + implemented

## Suggested next invocation

```
/go Read P:/docs/handoffs/ship-pipeline-open-work-20260809/HANDOFF.md and implement Tracks A-D. Track E (Singh heuristic) is a separate /design run — do not bundle.
```

## References

- [[orchestrator-controlled-cross-model-validation-ship-py]] — Layer 2 (DONE)
- [[polling-loop-continuation-controller-design-decision]] — Layer 1 (DONE)
- [[making-llm-agents-honestly-execute-skills-solution-stack]] — solution families
- [[specification-gaming-in-llm-agent-pipelines]] — diagnosis
- [[design-choice-audit-challenge-every-decision-against-first-principles]] — Track D4
