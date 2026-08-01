---
title: "Close-check workflow replaces close for session readiness gating"
created: 2026-08-01
source: session-019f902a-621d-7711-9436-7c6003c57793
tags: [close-check, session-readiness, workflow, lifecycle, grok-build]
summary: >
  The close-check workflow is a session readiness gate that replaces
  the older /close command. It runs a pre-close sweep across all
  lifecycle domains (git-state, harvest, close-gates, workspace-health,
  doc-check, wiki-health, fmea, friction, obligation-coverage,
  lifecycle-artifacts, lifecycle-skill-coverage) and resolves every
  gate mechanically before the operator is prompted for judgment.
  The workflow is invoked via a command wrapper that resolves the
  session ID and model pool automatically.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - P:/.grok/commands/close-check.md (command wrapper)
  - P:/.data/wiki/concepts/command-wrapper-pattern-for-workflows.md
  - P:/.data/wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
relations:
  - target: wiki/concepts/command-wrapper-pattern-for-workflows.md
    type: extends
  - target: wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md
    type: related
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md
    type: related
  - target: wiki/concepts/agent-consolidation-in-parallel-workflows.md
    type: related
  - target: wiki/concepts/close-pipeline-completeness-vs-priority-gap.md
    type: related
---

# Close-check workflow replaces close for session readiness gating

## Decision context

**Why this matters:** Session close-out is a critical lifecycle
boundary. The old `/close` command relied on the operator to
manually run checks and interpret gate states. The close-check
workflow automates the scanning and gate-resolution phases,
collapsing to a 10-line output when all gates are pre-satisfied,
and only surfacing judgment fields when a concrete gap is
detected. This is a significant reliability improvement for
session cleanup.

**The trigger:** The operator invoked `/close-check` at the end of
a session. The command wrapper resolved the session ID and model
pool, launched the close-check workflow in the background, and
produced a readiness report. This is the first real-world
invocation of the close-check workflow in this session.

## Key findings

1. **Close-check replaces /close** — it is a dedicated workflow
   that runs a pre-close sweep across 11 lifecycle domains
   before asking the operator for judgment. The operator's role
   shifts from "run checks and interpret" to "review the report
   and decide."

2. **Command wrapper resolves session context** —
   `~/.grok/commands/close-check.md` extracts the session ID
   from the prompt file path or session directory, resolves the
   model pool via `pick_model.py`, and launches the workflow
   with both values. This eliminates manual context gathering.

3. **The workflow runs in the background** — the operator is not
   blocked while the sweep runs. The workflow is a background
   process that produces a readiness report when complete.

4. **Lifecycle skills are classified by remediation mode** —
   each lifecycle skill declares `remediation_mode` in its
   SKILL.md frontmatter (auto-act vs surface-only). Close-check
   Phase 3 reads this field to determine how to handle each
   skill's output. This is a skill-graph property, not a
   close-check-specific config.

## What this means for our workspace

- The close-check workflow is the new standard for session
  readiness. The old `/close` command should be considered
  deprecated or superseded.
- The command wrapper pattern (`close-check.md`) is a reusable template for other workflows that need session ID and model pool resolution, following the same pattern as [[command-wrapper-pattern-for-workflows]].
  reusable template for other workflows that need session ID
  and model pool resolution.
- The lifecycle skill remediation modes classification ([[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]]) is a skill-graph property documented in that concept. ([[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]])
  (`lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md`)
  is a supporting concept that close-check depends on. The close pipeline completeness vs priority gap is documented in [[close-pipeline-completeness-vs-priority-gap]]. The close pipeline completeness vs priority gap is documented in [[close-pipeline-completeness-vs-priority-gap]].
- Operators should use `/close-check` instead of `/close` for
  all session wrap-ups going forward.

## Falsifier

This concept is wrong if:
- The close-check workflow is found to have gaps that `/close`
  caught but close-check missed (measured by comparing
  readiness reports across sessions).
- The command wrapper fails to resolve session ID or model
  pool correctly in a significant number of cases.
- The lifecycle skill remediation modes classification ([[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]]) is a skill-graph property documented in that concept. ([[lifecycle-skill-remediation-modes-auto-act-vs-surface-only]]) is found
  to be inaccurate or incomplete for the skills in use.

## Receipts

- `P:/.grok/commands/close-check.md` -- the command wrapper (verified by read_file via session skill catalog)
- Session transcript line 576 -- operator invoked `/close-check`
- `P:/.data/wiki/concepts/command-wrapper-pattern-for-workflows.md` -- existing concept for command wrapper pattern
- `P:/.data/wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md` -- lifecycle skill remediation modes concept
- `P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md` -- skill lifecycle architecture concept

## Sources

- `P:/.grok/commands/close-check.md` — the command wrapper
- Session transcript line 576 (operator invoked `/close-check`)
- `P:/.data/wiki/concepts/command-wrapper-pattern-for-workflows.md`
- `P:/.data/wiki/concepts/lifecycle-skill-remediation-modes-auto-act-vs-surface-only.md`
