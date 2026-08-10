---
thread_id: 377c7621-bccf-4481-b2ef-b1f1db33f036
parent_handoff_path: P:/docs/handoffs/ship-py-pi-dispatch-not-found-20260809/HANDOFF.md
current_session_id: 019fe36e-7cb5-7003-b7dd-f94396165026
parent_session: none
current_terminal_id: 019fe36e-7cb5-7003-b7dd-f94396165026
produced_at: 2026-08-10T06:15:00Z
last_updated_by: 019fe36e-7cb5-7003-b7dd-f94396165026
last_updated_at: 2026-08-10T06:15:00Z
status: open
handoff_type: investigation
accurate_as_of_head: HEAD
---

# Handoff — ship-py pi dispatch + quality-gate integration gaps

## Objective

Diagnose and fix the pi CLI dispatch failure that prevents ship-py from producing verdicts, plus the quality-gate hook integration gap that blocks session completion after ship-py runs.

## Status

OPEN — symptoms documented, root cause not yet diagnosed (replacement-before-investigation rule applies: reproduce the failure in isolation before changing the orchestration layer).

## Producing context

2026-08-10, session 019fe36e. `/ship-py` run on a doc-only session hit pi CLI dispatch failures on all 6 dispatch phases. Then the quality-gate Stop hook blocked 3 times because ship-py's review evidence format doesn't match what the hook expects.

## Read-first list

1. `P:/docs/handoffs/ship-py-pi-dispatch-not-found-20260809/HANDOFF.md` — prior session's investigation of the related `pi_not_found` variant.
2. `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` — the orchestrator that dispatches to pi.
3. `~/.grok/skills/ship-py/__lib/dispatch_base.py` — the dispatch path (line 36: `_PI_BINARY = shutil.which("pi")`).
4. `~/.grok/hooks/scripts/quality_gate/main.py` — the Stop hook that checks for `_run.json`.
5. `~/.grok/hooks/scripts/quality_gates_frontmatter.py` — the frontmatter-based gate checker.
6. `P:/.data/wiki/concepts/tool-fallbacks.md` — now contains the pi CLI empty_response entry (committed this session).

## Verified facts

- [FACT] pi CLI is installed: `pi.CMD` at `C:\Users\brsth\AppData\Roaming\npm\pi.CMD`, version 0.82.1 (verified `pi --version` exit 0).
- [FACT] Every orchestrator dispatch phase (refactor, check, review, cross-validate, trace, risk) returned `"status": "dispatch_skipped", "reason": "empty_response"` for `nim-openai-gpt-oss-20b`.
- [FACT] The `SHIP_PY_ALLOW_FALLBACK=1` env var + `--findings-file` workaround completed all phases but broke the tamper-evident hash chain (verdict phase correctly refused).
- [FACT] The quality-gate Stop hook expects `P:/.artifacts/**/grok-review/**/_run.json` with a `session_id` field matching the current session. Ship-py's review phase produces findings at `P:/.artifacts/ship-py/<session-id>/review-findings.json` — a different path and format the hook doesn't recognize.
- [FACT] The prior session (019fdf3c) hit `pi_not_found` (different failure mode: binary not found despite `shutil.which` resolving). This session hit `empty_response` (binary found, output empty). Both originate from the same dispatch infrastructure in `dispatch_base.py`.

## Task packets

### SP-PI-01 — Isolate and diagnose the pi CLI empty_response failure

- goal: Reproduce the `empty_response` failure outside the orchestrator to identify root cause.
- in scope: Run pi CLI dispatch directly (not through the orchestrator) with the same model and prompt the orchestrator uses. Capture: exit code, stdout, stderr, timing. Compare with a known-working pi invocation. Check: is it a timeout issue? A parsing issue (pi returns output the orchestrator doesn't parse)? A model-side failure (nim-openai-gpt-oss-20b returns empty for certain prompt shapes)?
- out of scope: Fixing the orchestrator (that's SP-PI-02, after root cause is known). Changing the quality-gate hook.
- files / anchors: `~/.grok/skills/ship-py/__lib/dispatch_base.py` (dispatch function, subprocess invocation), `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` (dispatch call sites).
- acceptance: A root-cause statement with an isolated reproduction (the exact command, the exact output, the exact failure point in the dispatch code path).
- falsifier: If pi CLI works correctly when invoked directly with the same args, the bug is in the orchestrator's invocation or parsing, not in pi.
- verification level required: LIVE_BEHAVIOR

### SP-QG-01 — Bridge ship-py review evidence to quality-gate hook

- goal: Make the quality-gate Stop hook accept ship-py's review evidence as satisfying the `[review]` gate.
- in scope: Either (a) ship-py's review phase writes a `_run.json` to the canonical `grok-review/` path, or (b) the quality-gate hook learns to accept `ship-py/<session-id>/review-findings.json` as equivalent evidence. Read both sides (ship-py review phase + quality-gate receipt validator) to determine which is the lower-risk bridge.
- out of scope: Redesigning the quality-gate system. Changing how `/review` produces evidence.
- files / anchors: `~/.grok/skills/ship-py/__lib/ship_orchestrator.py` (review phase), `~/.grok/hooks/scripts/quality_gate/receipt_validator.py`, `~/.grok/hooks/scripts/quality_gates_frontmatter.py`.
- acceptance: Running `/ship-py` to completion does NOT trigger the quality-gate Stop hook's `[review]` block when the review phase ran successfully.
- falsifier: If the bridge creates a way to satisfy the review gate without an actual review running, it's a security regression.
- verification level required: LIVE_BEHAVIOR

## Open decisions

### D1: Retry handler vs root-cause fix

- **Question:** Should ship-py add an `empty_response` retry handler (retry with different model) before root cause is known?
- **Options:** (1) Retry handler now — masks the symptom but unblocks ship-py. (2) Diagnose first (SP-PI-01), then fix properly.
- **Selection criterion:** AGENTS.md "replacement-before-investigation" rule: reproduce the failure in isolation before changing the orchestration layer.
- **Currently leading:** Diagnose first (SP-PI-01). The retry handler is a valid enhancement AFTER root cause is known, not a substitute for diagnosis.
- **What would change the lead:** If the operator says "just unblock it," the retry handler is a quick stopgap.

## Explicit non-goals

- Do NOT add a retry handler to ship-py without first reproducing and diagnosing the empty_response failure (anti-pattern: replacement-before-investigation).
- Do NOT modify the quality-gate hook's core logic without understanding the receipt validation contract (both sides must be read first).

## Suggested skills for next session

- `/why` — root-cause investigation for SP-PI-01 (the pi dispatch failure is a diagnostic task)
- `/review --focus architecture` — for SP-QG-01 (bridging two systems' evidence contracts)
- `/check` — after fixes are implemented, verify ship-py runs end-to-end

## Changelog

| Date | Session | Action |
|------|---------|--------|
| 2026-08-10T06:15 | 019fe36e... | created |
