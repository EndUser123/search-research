---
title: "No question theater — answer instead of asking"
created: 2026-07-26
tags: [decision, question-theater, anti-pattern, empowerment, trigger-cases]
host: both
agent: grok
verification: local-only
cognitive_load: 2
summary: >
  Don't ask questions you can answer yourself. When you've already done the analysis and
  stated a recommendation, act on it — don't ask for confirmation on reversible actions.
  Each ambiguity trigger has a decision protocol so the model has somewhere to go other
  than asking.
---

# No question theater

## Rule

This is empowerment over prohibition. Instead of blocking on ambiguity, give each trigger type a decision protocol:

- **Vague identity** → use host-level default (Grok Build → `grok`), state assumption
- **Ambiguous scope** → pick larger interpretation, label as work scope, proceed
- **Missing parameter with default** → use default, state it
- **Reversible config edit** → make the edit, report what was done
- **/go (or orchestrator) phase boundary** → did the original invocation authorize the full loop? If yes (e.g., `/go <handoff>` without a single-phase scope like `/go design`), continue to the next phase without asking. The design→implement boundary is the highest-risk point: completing a design artifact and emitting "Recommended next steps" offloads execution the operator already authorized. Reference: session 019fde3e (2026-08-07), AAR `aar-trajectory-validity-layer3-019fde3e`. **Measured compliance ceiling:** the rule was loaded and the operator corrected it once (L4), then it failed again in the same session (L136) — N=2 within-session, firing 0/2 times. This is direct evidence that the prose rule has the documented ~50% compliance ceiling under session pressure. The structural fix is a `/go`-skill-level phase-boundary check, not more prose.
- **Genuinely unanswerable** → ask ONE focused question and stop

## Anti-pattern

The model investigates, derives an answer, states "I'd default to X" — then asks "who is the assignee?" or "should I proceed?" The analysis was done; the question offloads a decision already made. This costs one user turn per asked-to-confirm default.

## Falsifier

Wrong if acting on defaults causes more damage than asking. Test: track whether operator overrides defaults vs confirms them — if >80% confirm, asking was theater.

## Relations

- [[agents-md-construction-best-practices]]
- [[behavioral-detection-approaches-practitioner-survey]] — UNNECESSARY_CONFIRMATION pattern detects this
## What this means for our workspace

The general prose rule is loaded but does not fire reliably at `/go` phase boundaries
(session 019fde3e: the agent offloaded execution despite `/go` authorization). The
actionable implication: add a phase-boundary authorization check to the `/go` skill
itself — "did the original invocation authorize the next phase? if yes, continue" —
rather than relying on general AGENTS.md prose to fire under session pressure. This
is opportunity O1 in AAR `aar-trajectory-validity-layer3-019fde3e` (disposition
INVESTIGATE, pending confirmation of /go's internal phase model). The friction-taxonomy
gap ("needless-confirmation" is not one of the six friction categories in
[[friction-detection-operator-pushback-as-trigger]]) is a secondary monitoring item.
