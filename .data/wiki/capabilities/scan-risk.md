---
title: "scan-risk"
node_type: capability
created: 2026-08-13
domain: review
---

# scan-risk

**Inputs:** code diff, plan, decision, config change, commit, design proposal
**Outputs:** risk assessment with severity × likelihood, early warning signals, verdict

## Procedure

Adaptive depth: inline scan first. Escalate to critique (fresh subagent)
or attack (specialists) only when severity warrants. Produce verdict
(PROCEED / REVISE / BLOCK).

## Providers

- `/risk` (adaptive: scan → critique → attack)
- `/tp` (two-lens critical-friend: fresh subagent + synthesis)
