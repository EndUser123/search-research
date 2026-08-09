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
OPEN — 3 items remain (A3 test isolation, B4 timeout, D1-D4 Phase 2 polish).
The anti-fabrication architecture is complete (all 3 specification-gaming
layers that the original fraud exploited are closed). What remains is test
hygiene, timeout tuning, and Phase 2 feature polish — none of which affects
pipeline integrity.

## Objective
Complete the remaining open work on the ship-py verify-and-publish pipeline.
This handoff consolidates genuinely-open items from:
- `ship-py-hardening-20260805` (items 5-8 MOOT — ship-rhai.rhai deleted; 1-4,9,10,12,13 DONE)
- `ship-py-remaining-gaps-20260808` (item 7 DONE — _format_version now functional)
- `ship-py-phase2-functionality-composition-20260809` (Phase 1+2 shipped)
- `singh-execution-reality-middleware-20260808` (distinct work item, folded here)

## What's already done (don't re-do)

**Anti-fabrication architecture (the original fraud surface — all closed):**
- Cross-model validation phase shipped (commit 6f7d324) — see [[orchestrator-controlled-cross-model-validation-ship-py]]
- Polling loop + anti-fabrication gates + transition chain + path validation (commit ee28569)
- Verdict hard-blocks on broken tamper-evident chain (commit ab15f5b) — was warning, now return 2
- Refactor blocks on missing findings, matching risk.py contract (commit ab15f5b) — was silent pass
- Verdict gate blocks SHIP DONE when review_findings missing
- _format_version now functional (v3, used for mid-flight migration discriminator)
- PreToolUse phase-gate hook shipped (commit 5c1e1b0)

**Pipeline features (all shipped):**
- abort subcommand + secret-scan + fmea-scan + design-check + babysit + version-bump (Phase 1+2, session 019fe403)
- ship_receipt.py exists (66KB) — receipt generation is automated

**Resolved/closed items:**
- A1 (test return_value=0) — DONE (commit ab15f5b)
- A2 (test capsys assertion) — DONE (commit ab15f5b)
- B1 (refactor blocks on missing findings) — DONE (commit ab15f5b)
- B2 (correction_classifier structured marker) — DONE (commit ab15f5b)
- B3 (verdict hard-blocks on broken chain) — DONE (commit ab15f5b)
- C1 (Stop hook regex false-positive) — ALREADY RESOLVED (old quality_gate.py replaced by frontmatter evidence-gate system)

**Current test state:** 83 tests collected, 82 pass, 1 xfailed. Ruff clean.

## Remaining open work (3 items + Phase 2 polish)

### Track A: Test quality

**A3.** Test state isolation — tests don't use a shared `tmp_artifacts` fixture.
Real state files at `P:/.artifacts/ship-py/test-session/` can leak between
tests. Fix: adopt the `tmp_artifacts` fixture pattern from `test_ship_orchestrator.py`.
- **Impact:** test hygiene — doesn't affect production reliability. Tests pass today by accident; this prevents future test-order-dependent failures.
- **Effort:** ~30 min (add conftest.py fixture, update test files to use it)

### Track B: Timeout tuning

**B4.** Polling-loop timeout — currently a fixed 600s wall-clock deadline with
no liveness signal. **RESEARCHED (commit 80b9bbd)** — see
[[liveness-vs-timeout-for-agent-pipeline-polling-loops]]. The /www+/tp research
concluded: measure first. The problem (legitimate agents cut off at 600s) may
be hypothetical — no measured incidents.
- **Recommended action:** check `_timed_out_<phase>` markers in state files across recent sessions. If no legitimate cutoffs occurred, increase `poll_timeout` default from 600s to 1800s (one config change) and close this. If incidents exist, implement the progress-sidecar pattern.
- **Impact:** responsiveness (hung-agent detection time), not integrity. The chain-block (B3, done) catches downstream consequences of a timed-out phase.
- **Effort:** 5 min (config bump) OR ~2 hours (progress-sidecar if needed)

### Track D: Phase 2 documentation + testing (polish)

**D1.** Tests for Phase 2 features — design_check, babysit, publish version-bump,
/why-in-fix PAUSE_INSTRUCTIONS. (cross-model review PAUSE_INSTRUCTIONS is
superseded by the shipped cross-validate phase — skip that one.)
- **Impact:** regression catching. Phase 2 features shipped without tests; they work today but changes could break them silently.
- **Effort:** ~2 hours (4 test files)

**D2.** Enrich changelog generation in publish phase — include commit messages
(currently only version bumps and file counts).
- **Impact:** nicer release notes. Cosmetic.
- **Effort:** ~30 min

**D3.** design-check doc-matching — improved heuristic landed but may still
produce false positives on common skill names.
- **Impact:** minor — false positives are warnings, not blocks.
- **Effort:** ~1 hour (improve the matching heuristic)

**D4.** Document design-choice audit as AGENTS.md rule — currently only in wiki
concept `[[design-choice-audit-challenge-every-decision-against-first-principles]]`
+ 6 skills, not in the governing rules file.
- **Impact:** discoverability — the pattern is enforced in 6 skills but not findable from AGENTS.md.
- **Effort:** ~15 min (add a section to AGENTS.md)

### ~~Track E: Singh execution-reality middleware~~ (DROPPED 2026-08-09)

**Dropped per /tp recommendation.** The Singh heuristic addresses tool-output
fabrication (agent claims subprocess returned X when it returned Y) — a failure
mode NOT observed in this workspace. In our orchestrator-controlled architecture,
the LLM does NOT directly call subprocess.run — the orchestrator mediates all
subprocess execution. The academic 56.6% fabrication rate likely doesn't
transfer to this environment. The wiki documents the pattern
([[making-llm-agents-honestly-execute-skills-solution-stack]] §2); if the
failure mode emerges later, it can be implemented then.

## What "done" looks like for ship-py reliability

The pipeline is **reliable against the original fraud today.** The three
hardening fixes (B1, B3 + the cross-validate phase) closed every
specification-gaming path the 2026-08-08 incident exploited:

1. **Can't fabricate review findings** — cross-validate phase produces
   independent findings from a model the LLM can't influence (Layer 2)
2. **Can't skip refactor** — refactor.py now blocks on missing findings (B1)
3. **Can't fabricate state transitions** — verdict hard-blocks on broken
   tamper-evident chain (B3)
4. **Can't skip review** — verdict gate blocks SHIP DONE when review_findings missing
5. **Can't self-advance via --verdict** — escape hatch removed

What remains (A3, B4, D1-D4) is hygiene, tuning, and polish — not integrity gaps.

## Suggested next invocation

```
/go Read P:/docs/handoffs/ship-pipeline-open-work-20260809/HANDOFF.md and implement A3 + D1. B4 is a 5-min config bump after measuring. Track E is operator-decision.
```

## References

- [[orchestrator-controlled-cross-model-validation-ship-py]] — Layer 2 (DONE)
- [[polling-loop-continuation-controller-design-decision]] — Layer 1 (DONE)
- [[liveness-vs-timeout-for-agent-pipeline-polling-loops]] — B4 research
- [[making-llm-agents-honestly-execute-skills-solution-stack]] — solution families
- [[specification-gaming-in-llm-agent-pipelines]] — diagnosis
- [[design-choice-audit-challenge-every-decision-against-first-principles]] — Track D4
