---
title: "Analysis over action: knowledge capture without application"
created: 2026-08-01
source: session-019fb937 (/why + /tp on hook timeout — 5-session recurrence pattern)
sources:
  - internal: P:/.data/wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
  - internal: P:/.data/wiki/concepts/list-before-claim-for-destructive-proposal-actions.md
tags: [analysis-paralysis, knowledge-application, closure-pressure, recurring-pattern, workspace-incentives]
agent: grok
host: both
cognitive_load: 2
verification: single-session-observed
summary: >
  The workspace has excellent infrastructure for understanding problems
  (/why, wiki concepts, handoffs) but no infrastructure for driving fixes
  to completion. A known fix survived 4 sessions unapplied because every
  iteration produced analysis (RCA, wiki concept, handoff) but not action.
  The incentive structure rewards analysis (visible artifacts) over action
  (invisible non-events). The structural fix: separate diagnosis from
  prescription, and bridge "here are the fixes" to "apply fix #1 now."
relations:
  - target: wiki/concepts/hook-evidence-collection-cost-vs-timeout-tradeoff.md
    type: observed-in
  - target: wiki/concepts/list-before-claim-for-destructive-proposal-actions.md
    type: related
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: related
---

# Analysis over action: knowledge capture without application

## Decision context

**The pattern (observed across 5 sessions):** a hook timeout was investigated,
analyzed, and documented — but the fix was never applied. Each iteration
produced a durable artifact (wiki concept, handoff with `status: ready-to-implement`,
RCA with fix recommendations) but no code change. The fix was a 1-line config
edit. It survived 4 recurrences because nothing in the workspace's skill
graph bridges "here are the fixes" to "apply fix #1 now."

**The incentive structure:** producing a wiki concept or handoff creates a
visible artifact the operator engages with. Applying a 1-line fix creates an
invisible non-event (the timeout just stops happening). The agent gets more
positive feedback for analysis than for action. Until "fixes applied this
session" is surfaced alongside "findings captured" in session summaries, the
incentive bends toward analysis.

**The /why contract says "does NOT implement fixes."** So the RCA was correct
to not implement. The gap isn't in the RCA — it's that no skill bridges
"here are the fixes" → "apply fix #1." `/go` implements, but waits to be
invoked. The fixes die in that invocation gap.

## Detection signals

A session is exhibiting this pattern when:
1. An RCA or analysis produces a fix recommendation table
2. The fix is high-confidence, low-blast-radius, reversible
3. The session ends without applying any fix
4. A wiki concept or handoff is written instead
5. The problem recurs in a future session

## Structural fixes (in priority order)

1. **Bridge the invocation gap.** `/why` Step 14 should end with: "next action:
   invoke `/go` to apply fix #1, or say 'defer'." Make the bridge explicit.

2. **Surface applied fixes in session summaries.** When `/close` or `/capture`
   runs, count "fixes applied" alongside "findings captured." Make action visible.

3. **Separate diagnosis from prescription.** The RCA session diagnoses under
   closure pressure (wants to ship a handoff before session ends). A fresh
   session prescribing and implementing doesn't have that pressure.

## Falsifier

This concept is wrong if:
- The workspace's fix-application rate is actually high (this was an anomaly)
- The problem was the specific fix being wrong (not a systemic pattern)
- Adding a bridge step doesn't improve fix-application rate

## Related

- [[hook-evidence-collection-cost-vs-timeout-tradeoff]] — the incident where
  this pattern was observed across 5 sessions
- [[list-before-claim-for-destructive-proposal-actions]] — a related pattern
  where analysis (proposing to gitignore) almost caused data loss
- [[mechanical-enforcement-over-behavioral-reminder]] — why behavioral rules
  ("just apply the fix") don't work without structural support
