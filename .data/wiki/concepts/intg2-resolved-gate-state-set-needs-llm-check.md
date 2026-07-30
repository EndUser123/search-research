---
title: "INTG-2 resolved gate-state set: needs_llm_check is a valid terminal state"
created: 2026-07-29
source: session-019fb177 (close-authority enforcement completion execution)
tags: [close-authority, gate-states, needs-llm-check, validate-close-receipt, decision, enforcement]
summary: >
  The INTG-2 gate-content check in validate_close_receipt must accept
  needs_llm_check as a resolved terminal gate state alongside pre_satisfied
  and skip. The original plan specified only {pre_satisfied, skip}, but
  close_runner.py ALLOWED_GATE_STATES and SKILL.md line 108 define
  needs_llm_check as a valid terminal state that the LLM resolves with a
  one-sentence verdict. Excluding it would reject valid CLOSE COMPLETE
  receipts — e.g., doc-only-commit sessions where the verify gate legitimately
  lands on needs_llm_check.
agent: grok
host: grok
cognitive_load: 2
verification: local-only
relations:
  - target: wiki/concepts/close-authority-state-machine-design.md
    type: refines
  - target: wiki/concepts/maker-checker-required-for-enforcement-work.md
    type: refines
---

# INTG-2 resolved gate-state set: needs_llm_check is a valid terminal state

## Decision context

**Why this decision was needed:** the close-authority enforcement completion plan (v5, `P:/docs/superpowers/plans/2026-07-28-close-authority-completion.md`) specified an INTG-2 fix: reject CLOSE COMPLETE receipts carrying any non-resolved gate. The plan's code block used `RESOLVED = frozenset({"pre_satisfied", "skip"})` — two states out of four. During implementation, I discovered that `close_runner.py:51` defines `ALLOWED_GATE_STATES = frozenset({"pre_satisfied", "skip", "needs_llm_check"})` and `DISALLOWED_GATE_STATES = frozenset({"needs_attention"})`. The plan's set would have rejected receipts that the close runner itself considers valid.

The question: should the INTG-2 check accept `needs_llm_check` as resolved, or should it use the plan's stricter set of only two states?

## Discovery process

The contradiction was discovered during H3 discovery (reading the source before implementing the plan). The discovery sequence:

1. Read the plan's code block — `RESOLVED = frozenset({"pre_satisfied", "skip"})`
2. Read `close_authority.py:advance_from_scan` — docstring says `state ∈ {pre_satisfied, needs_attention, needs_llm_check, skip}` (four states)
3. Grep for `needs_llm_check` across the codebase — found `close_runner.py:51` defining `ALLOWED_GATE_STATES`
4. Connected the dots: the plan excluded a state that the runner explicitly allows as terminal

If H3 discovery had been skipped (as the delegation-packet classifier would have done on a score ≥4 prompt), the plan's set would have been implemented verbatim. The test suite would not have caught it immediately because the existing 20 tests don't cover `needs_llm_check` in COMPLETE receipts. The regression would have surfaced only when a real session with a `needs_llm_check` gate tried to close.

This is a concrete instance of why [[file-edit-failures-two-classes]] Class B (wrong content written atomically) applies to plan execution too: a plan can be atomically applied and still be wrong if the plan contradicts the implementation contract it targets.

## The decision

**The INTG-2 check accepts `needs_llm_check` as a resolved state.** The RESOLVED set in `validate_close_receipt` is `{"pre_satisfied", "skip", "needs_llm_check"}` — matching `close_runner.ALLOWED_GATE_STATES` exactly. Only `needs_attention` (and any unrecognized state) is treated as unresolved/blocking.

### Rationale

`needs_llm_check` is a fundamentally different gate state from `needs_attention`:

- **`needs_attention`** — a concrete gap was detected. The scanner knows something is wrong. The close loop fires (resolve, re-scan). This state MUST block CLOSE COMPLETE. This aligns with [[mandatory-step-enforcement-code-over-prose]] — only mechanically detected gaps trigger enforcement.
- **`needs_llm_check`** — the scanner cannot determine the answer mechanically. The LLM must check conversation context and emit a one-sentence verdict. This is a valid terminal disposition, not a gap. (Source: SKILL.md line 108: "Check conversation context. Emit one-sentence verdict.") This distinction was previously missed in [[compaction-inherited-diagnosis-unverified-propagation]], where a compaction summary framed `needs_llm_check` as "broken" when it was actually spec-valid.

Examples of gates that legitimately land on `needs_llm_check` at close time:
- `verify` gate on doc-only-commit sessions (close_accounting.py:2193: "doc-only commits — verify any runtime claims if made")
- `git_state` gate when cross-repo persistence checks need review (close_accounting.py:2383)
- `background_tasks` gate when spawn_subagent tasks may still be running (close_accounting.py:2390)

If the INTG-2 check excluded `needs_llm_check`, these sessions could never produce a valid CLOSE COMPLETE receipt — even when all gates are legitimately resolved. The close flow would deadlock.

### Steelman (the rejected alternative)

The plan's `{"pre_satisfied", "skip"}` set has a coherent rationale: minimize the set of states accepted as "resolved" to reduce the attack surface. If fewer states count as resolved, fewer forged receipts can pass validation. `needs_llm_check` is softer than `pre_satisfied` (mechanical proof vs. LLM judgment), so excluding it is more conservative.

This reasoning is sound in isolation — but it conflicts with the close runner's own contract. Two code paths would disagree on what counts as "resolved": the runner would accept a receipt, and the validator would reject it. That split-verdict pattern is exactly what CORR-002 was designed to eliminate, and what [[close-authority-state-machine-design]] identified as the core enforcement gap.

The conservative approach also violates the [[trusted-computing-base-for-agent-enforcement]] design principle: the TCB should trust the scanner's computed state, not impose a stricter interpretation that contradicts the scanner's own vocabulary. If the scanner says a gate is `needs_llm_check` (a valid terminal state), the validator should not second-guess that classification.

### Falsifier

This decision is wrong if `needs_llm_check` is ever reclassified as an unresolved state — i.e., if the close loop starts firing on `needs_llm_check` gates the way it fires on `needs_attention`. In that scenario, accepting `needs_llm_check` in the INTG-2 check would allow receipts that the scanner considers unresolved.

The specific observation that would disconfirm this decision: a future change to `close_accounting.py` that adds `needs_llm_check` to the `loop.attention_gates` computation (making it trigger the close loop). If that happens, the RESOLVED set in `validate_close_receipt` must shrink back to `{"pre_satisfied", "skip"}` to match.

## What this means for our workspace

- **The INTG-2 RESOLVED set and `close_runner.ALLOWED_GATE_STATES` must stay synchronized.** If either set changes, the other must update. This is documented as a cross-reference coupling in the execution handoff (`P:/docs/handoffs/close-authority-execution-20260729/HANDOFF.md`). A future refactoring that adds or removes a gate state must grep for `_RESOLVED_GATE_STATES` and `ALLOWED_GATE_STATES` together.
- **The plan body still shows the old RESOLVED set** in the code block at line 71. The plan was not rewritten (only checkboxes ticked + Execution Status appended). A future reader of the plan alone would see the wrong set. The corrected implementation + this wiki entry are the sources of truth.
- **Forged-receipt protection is not weakened.** `needs_llm_check` is a legitimate terminal state, not a gap. A forged receipt claiming COMPLETE with `needs_llm_check` gates is still valid because those gates ARE resolved — the LLM resolved them with a one-sentence verdict. The protection target is `needs_attention`, which remains blocked.
- **This is a plan-vs-source-contradiction pattern.** The plan was written from the spec's intent (minimize resolved states), but the implementation's vocabulary (four gate states, three of which are terminal) was broader than the plan assumed. The fix required reading the implementation that owns the contract (`close_runner.py:51`) before deviating from the plan's code. This connects to [[self-review-before-shipping-advice]] — the agent's own discovery (finding ALLOWED_GATE_STATES) overrode the plan's specification, and verification (the test) confirmed the deviation was correct.

## Receipts

- `close_runner.py:51` — `ALLOWED_GATE_STATES = frozenset({"pre_satisfied", "skip", "needs_llm_check"})` (the contract)
- `close_runner.py:52` — `DISALLOWED_GATE_STATES = frozenset({"needs_attention"})` (the only blocking state)
- `close_authority.py:310` — `_RESOLVED_GATE_STATES = frozenset({"pre_satisfied", "skip", "needs_llm_check"})` (the fix, commit `cc9d38d`)
- `close_accounting.py:2193` — `verify` gate emits `needs_llm_check` for doc-only commits (example of valid terminal state)
- `SKILL.md:108` — spec defining `needs_llm_check` resolution contract
- Test receipt: `test_acceptance_spec.py::TestIntg2GateContentCheck::test_complete_with_needs_llm_check_accepted` (PASSED)

## Falsifier

See "Falsifier" section above. The one-sentence version: if `needs_llm_check` is ever added to `loop.attention_gates` (making it trigger the close loop), the RESOLVED set must shrink to exclude it.

## Sources

- Implementation: `close_authority.py:305-316` (INTG-2 check, branch `close-authority-019fa5a1`, commit `cc9d38d`)
- Contract source: `close_runner.py:51-52` (`ALLOWED_GATE_STATES` / `DISALLOWED_GATE_STATES`)
- Spec source: `C:/Users/brsth/.grok/skills/close/SKILL.md` line 108
- Prior art: [[compaction-inherited-diagnosis-unverified-propagation]] — a prior session also discovered that `needs_llm_check` is a valid terminal state when close_runner was incorrectly rejecting it
- Related: [[maker-checker-required-for-enforcement-work]] — documents why self-verification of enforcement code is insufficient (the INTG-2 fix was verified by tests, not just by reading the code)
- Related: [[enforcement-vs-fleet-hygiene-attestation-deferred]] — documents why attestation was dropped, making INTG-2 the primary file-layer defense
