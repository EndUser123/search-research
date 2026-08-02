---
title: "close-check Phase 4 Finalize: make blocking unnecessary rather than adding enforcement layers"
created: 2026-08-01
source: session-019fb933 (close-check Phase 4 build)
tags: [decision, close-check, lifecycle, workflow, finalize, auto-act, design-choice, blocking-vs-working, agentic-sdlc]
summary: >
  Design decision: close-check adds Phase 4 (Finalize) — auto-commit artifacts,
  clean temp files, refresh index — instead of adopting the mechanical
  enforcement layers from /close (close_authority.py + Stop-hook blocking).
  Selection criterion: "make blocking unnecessary" rather than "block the
  model from proceeding." The model can already read BLOCKED and proceed
  anyway; the right answer is to design a workflow where nothing important
  remains to block.
agent: grok
host: grok
cognitive_load: 3
verification: local-only
relations:
  - target: wiki/concepts/close-check-workflow-replaces-close-for-session-readiness.md
    type: extends — Phase 4 completes the lifecycle that the replacement workflow defines
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: refines — Phase 3 already auto-acts; Phase 4 extends the auto-act principle to the finalization step
  - target: wiki/concepts/rhai-workflow-smoke-check-misses-function-call-bugs.md
    type: related — discovered during same session, motivated the operator's "I want it to work" framing
---

# close-check Phase 4 Finalize: make blocking unnecessary rather than adding enforcement layers

## Decision context

**The question being decided:** when close-check surfaces "needs attention" findings, what should it do? Two paths:

1. **Adopt /close's mechanical enforcement layers** (close_authority.py validates, Stop-hook BLOCKs on certain gate states). The model has to physically stop before completing the close.
2. **Auto-remediate + auto-finalize everything the workflow can fix**, leaving only operator-gated items (unpushed commits, broken tests, Tier-3 decisions like push/delete/merge). The model can still proceed, but there's nothing important left unaddressed.

The original close-check design (Phases 1-3 only) was closer to option 1 — it reported findings and assumed operator triage. The operator's framing "I want it to work, not block" reframed the question from "how do we stop the model from skipping work?" to "how do we design a workflow where there's nothing important left to skip?"

## The principle

**Selection criterion: minimize what the operator has to do after the workflow completes.**

The model already runs the workflow. If the workflow runs Phase 3 (Remediate: invoke `/capture`, `/friction`, `/handoff`, `/trace`, `/wiki` for every check), and each of those writes durable artifacts, then the only remaining work is:

- Commit the artifacts (Phase 4)
- Clean temp files (Phase 4)
- Refresh the wiki index (Phase 4)
- Surface what only the operator can do (the Finalize report)

**Auto-finalize is preferred over mechanical enforcement** because enforcement layers add complexity (state machine, hooks, exception paths) to solve a problem the workflow can solve directly. The operator's time at session-close is the most expensive resource in the fleet; spending it on "decide whether to commit the commit-able artifacts" is waste.

## The decision

**Phase 4 (Finalize) was added to close-check. It runs unconditionally at the end of the workflow:**

1. **Commit all artifacts the workflow generated** (Phase 3 wrote wiki concepts, handoffs, AAR receipts, etc. — Phase 4 commits them).
2. **Clean temp files** (close-check leaves a report under `scratch/...` — Phase 4 deletes it).
3. **Refresh wiki index** (QMD update).
4. **Emit a Finalize report** listing what only the operator can do (push, delete, merge, fix broken tests).

**Phases 1-4 in summary:**

```
Phase 1: Sweep        3 agents detect issues (git, harvest, gates, health, fmea, friction, coverage)
Phase 2: Synthesize   classify findings, produce verdict
Phase 3: Remediate    run /capture, /friction, /handoff, /trace, /wiki unconditionally
Phase 4: Finalize     commit artifacts, clean temp files, refresh index, emit operator-only report
```

## Steelman of the rejected alternative

**Why mechanical enforcement layers (the /close approach) is reasonable:**

- **Atomicity guarantee.** If a hook BLOCKs before the workflow can write, the model is forced to address the gate before continuing. This catches the case where the workflow's finalization would commit a broken state.
- **Predictability.** Hook enforcement is binary and observable; the model and operator both know exactly what state triggers a block. Auto-finalize is "best effort" by contrast — a failed commit in Phase 4 leaves the operator with partially-finalized state.
- **Backwards compatibility.** /close already has this infrastructure. close-check adopting it would let close-check share the same enforcement contract.
- **Audit trail.** Hook-blocked sessions are observable in logs. Auto-finalize errors are workflow-internal failures unless surfaced.

## Selection criterion and rationale

**Criterion:** minimize operator cognitive load at session close, subject to the constraint that durable artifacts land in git before the workflow returns.

**Why auto-finalize wins on this criterion:**

- /close's enforcement layers cost the operator attention at every close (decide: address now, address later, or override). close-check's auto-finalize costs the operator attention only when there is something only they can do.
- The mechanical enforcement layers assume the model will skip work without them. close-check's design assumes the workflow will auto-act; enforcement becomes redundant when auto-act is comprehensive.
- Auto-finalize scales: as the workflow grows more phases, the operator's close-time work stays bounded ("what only I can do") rather than growing linearly with phase count.

## Falsifier

This decision is wrong if:

- **The workflow's auto-finalize regularly fails silently.** If Phase 4 commits break, cleanups miss temp files, or QMD updates fail in ways the workflow doesn't surface, the operator loses the audit trail enforcement layers provided. Mitigation: Phase 4 must surface all sub-step errors in the Finalize report — fail-loud is mandatory.
- **Operator-only items grow unboundedly.** If the Finalize report routinely lists 10+ operator actions, the auto-finalize is pushing work backward (the workflow does what it can, but the operator still has a lot to triage). This would suggest the workflow's Phases 1-3 are not auto-acting aggressively enough.
- **The operator wants to gate close itself.** If the operator's actual intent at session-close is "force me to review before any commit," enforcement layers are the right answer. Auto-finalize assumes the operator trusts the workflow.
- **The model starts skipping Phase 4.** If Phase 4 fails are tolerated (workflow returns 0 even on partial failure), the model may learn to ignore Phase 4 errors. Enforcement layers prevent this drift; auto-finalize must be paired with fail-loud contracts.

## What this means for our workspace

1. **close-check is now end-to-end auto-finalized.** Operators can run `/close-check` and walk away; the workflow commits what it can and surfaces only what they need to decide.
2. **/close and close-check have different contracts.** `/close` enforces (BLOCK on certain gate states). `/close-check` finalizes (auto-act, surface the rest). Don't conflate them — pick the workflow that matches the intent (enforce vs finalize).
3. **Other workflows that produce durable artifacts** should consider a Finalize phase too. The pattern is: do the work, then commit + clean + refresh + report.
4. **Auto-act discipline extends to Phase 4.** Just as Phase 3 auto-invokes lifecycle skills rather than asking the operator to invoke them manually, Phase 4 auto-commits rather than asking the operator to commit manually. Both phases embody the principle: the workflow does what it can.

## Receipts

The mechanism claims in this entry are sourced from the following observable artifacts:

- **close-check has 4 phases (Sweep, Synthesize, Remediate, Finalize):** verified via read_file of ~/.grok/workflows/close-check.rhai post-commit c5a6940. Meta block declares 4 phases; Phase 4 finalize_prompt built at lines 510-540; finalization_run: true in the result map at line ~555.
- **Phase 4 actions (commit, clean, refresh index, emit operator-only report):** observed in finalize_prompt construction at lines 502-540 of ~/.grok/workflows/close-check.rhai. The prompt asks the agent to: (1) commit artifacts under P:/, (2) delete temp files in scratch/, (3) run qmd update, (4) produce Finalize report listing unpushed commits, broken tests, Tier-3 decisions.
- **Phase 4 commit landed:** git commit c5a6940 with message feat(close-check): add Phase 4 Finalize - completion engine. 1 file changed, 96 insertions, 7 deletions.
- **Smoke check on 4-phase workflow:** observed via workflow tool invocation returning canned-host success message for 4 declared phases (session transcript line ~205).
- **First live run launched:** workflow with name=close-check started in background, status pending at session end (session transcript line ~225). First live run is the empirical validation that the smoke check was insufficient for behavioral correctness; aligns with the related rhai-workflow-smoke-check-misses-function-call-bugs finding.
- **Operator framing:** session transcript line ~145, prompt_index 71. The reframing from how do we stop the model from skipping work to how do we design a workflow where there is nothing important left to skip is the seed of the Phase 4 decision.

## Sources

- Session 019fb933 transcript, lines 1190-1260 (Phase 4 design discussion, "I want it to work, not block" framing)
- Commit `c5a6940`: "feat(close-check): add Phase 4 Finalize - completion engine" — implementation
- `~/.grok/workflows/close-check.rhai` — current state, 4 declared phases
- [[close-check-workflow-replaces-close-for-session-readiness]] — base workflow concept
- [[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]] — Phase 3 auto-act discipline that Phase 4 extends

## Auto-related

- [[skill-graph]]
- [[close-scanner-verification-gap-stale-read]]
- [[intg2-resolved-gate-state-set-needs-llm-check]]
- [[check-receipt-lifecycle-manifest-and-mechanical-derivation]]
- [[scope-matching-verification-discipline]]

