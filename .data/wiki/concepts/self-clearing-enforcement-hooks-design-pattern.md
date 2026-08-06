---
title: "Self-clearing enforcement hooks: the design pattern that makes blocking viable"
created: 2026-08-06
source: session-2026-08-06 (PreToolUse ship phase gate build + /tp critique)
tags: [enforcement, hook-design, pretooluse, fail-open, agent-self-recovery, transferable-technique]
agent: grok
host: grok
cognitive_load: 2
verification: observed-verified
summary: >
  The key difference between exec-gate (disabled for false-positive friction)
  and the ship phase gate (accepted) is not the blocking mechanism — both use
  exit 2. The difference is the self-clearing property: when the ship phase
  gate blocks, the stderr message tells the agent exactly how to unblock itself
  (complete the remaining pipeline phases). The agent runs the phases, the
  phase state advances to merge-ready, and the next push attempt succeeds —
  all without operator intervention. This is the transferable design pattern:
  enforcement hooks must be self-clearing to be viable on an agent-operated host.
relations:
  - target: wiki/concepts/ship-pipeline-enforcement-pretooluse-phase-state-hooks.md
    type: applies — the ship phase gate is the reference implementation
  - target: wiki/concepts/best-practices-enforcement-mechanism-grok-build.md
    type: extends — adds the self-clearing property to the detection+enforcement architecture
  - target: wiki/concepts/advisory-vs-blocking-enforcement-decision-2026.md
    type: refines — explains WHEN blocking is viable (when self-clearing) vs when advisory is better
  - target: wiki/concepts/close-check-finalize-phase-make-blocking-unnecessary.md
    type: complements — that concept says "make blocking unnecessary"; this one says "when you DO block, make it self-clearing"
---

# Self-clearing enforcement hooks

## Decision context

**The problem:** the operator disabled exec-gate (2026-07-20) because it
blocked commands and waited for operator intervention — "false positives and
over-aggressive friction." This created a prior decision
([[close-check-finalize-phase-make-blocking-unnecessary]]) preferring auto-act
over block. When the ship phase gate was proposed (also exit 2 blocking), the
tension was real: would this repeat the exec-gate failure?

**What resolved it:** the operator asked "are these things that can be fixed
automatically?" The answer is yes — and that property is what makes the ship
phase gate viable where exec-gate was not.

## The self-clearing property

A self-clearing enforcement hook has three properties:

1. **The block message is actionable by the agent** — it tells the agent
   exactly what to do to clear the block, not just what went wrong.
2. **The clearing action is within the agent's capability** — the agent can
   run the required steps (e.g., `/review`, `/check`, `ship_receipt.py`)
   without operator involvement.
3. **The state advances mechanically** — when the agent completes the
   clearing action, the state file updates and the next attempt succeeds
   automatically.

### The ship phase gate as reference implementation

```
Agent tries: git push
Hook blocks: exit 2
Stderr: "SHIP PHASE GATE: git push blocked — current phase is 'review'.
         Complete /review and /check first, then run ship_receipt.py to
         advance to merge-ready. To override, delete the phase state file."

Agent reads stderr → runs /review → runs /check → runs ship_receipt.py
Phase state advances: review → verify → merge-ready
Agent retries: git push → succeeds
Operator involvement: zero
```

Contrast with exec-gate:

```
Agent tries: <any command matching exec-gate's broad matcher>
Hook blocks: exit 2
Stderr: "Permission required for this command"
Agent: can't clear it — the block requires operator permission decision
Operator: must intervene to approve or deny
```

## When blocking is viable vs when it isn't

| Property | Blocking IS viable | Blocking IS NOT viable |
|---|---|---|
| Can the agent clear it? | Yes — agent runs the required steps | No — requires operator decision |
| Is the clearing action deterministic? | Yes — run X, Y, Z | No — subjective judgment needed |
| Is the block scoped narrowly? | Yes — only fires on the exact command | No — broad matcher catches unrelated commands |
| Is the default fail-open? | Yes — no state = allow | No — blocks on unknown state |

**Ship push:** blocking is viable because the agent can run the pipeline.
**Session close:** blocking is NOT viable because the agent can't decide
whether to commit, push, or defer — those are operator decisions
([[close-check-finalize-phase-make-blocking-unnecessary]]).

## The fail-open default

Self-clearing hooks must fail-open: if the state file is missing, corrupt,
or the session can't be resolved, the hook allows the action. This prevents
the hook from becoming a permanent block when the state file gets stuck
(e.g., the agent abandons the pipeline mid-execution).

The escape hatch is always documented in the stderr message: "delete the
phase state file or set phase to 'inactive'." This ensures that even a stuck
state is recoverable without operator intervention — the agent reads the
instructions and clears it.

## What this means for our workspace

1. **The ship phase gate is viable because it is self-clearing.** The
   close-check-finalize principle ("make blocking unnecessary") is NOT
   contradicted — it applies to contexts where the agent can't self-clear.
   Ship-push is a context where the agent CAN self-clear.

2. **Future enforcement hooks should be evaluated against the self-clearing
   property.** The question is not "should we block?" but "can the agent
   clear the block without operator intervention?" If yes, blocking is
   viable. If no, use advisory or auto-act instead.

3. **The stderr message IS the recovery protocol.** It must contain: what
   was blocked, why, what to do to clear it, and how to override in an
   emergency. A block message without recovery instructions is exec-gate
   territory — it generates friction, not enforcement.

## Falsifier

This pattern is wrong if:
- The ship phase gate is disabled within 30 days of deployment for being
  too friction-heavy (same failure mode as exec-gate). This would mean the
  self-clearing property is insufficient in practice.
- The agent consistently fails to read the stderr message and clear the
  block (stuck in a retry loop without running the clearing action). This
  would mean the message isn't actionable enough.
- A future enforcement need arises where blocking is necessary but the
  agent genuinely can't self-clear, and this pattern provides no guidance.
  (This would not invalidate the pattern — it would define its boundary.)

## Receipts

- Hook implementation: `~/.grok/hooks/PreToolUse_ship_phase_gate.py` —
  stderr message at lines 95-102, fail-open logic at lines 60-80
- Acceptance tests: 70 explicit assertions across 3 test suites (verifier
  report, session 2026-08-06)
- exec-gate disabled: `~/.grok/active-surface.last.md` provenance notes,
  "disabled due to false positives and over-aggressive friction (operator,
  2026-07-20)"
- Operator resolution of the close-check tension: session 2026-08-06,
  "if we need to block then block... Blocking sounds like the LLM halts
  and nothing happens after that until I wake up" → resolved by explaining
  the self-clearing property

## Sources

- Session 2026-08-06: ship phase gate build + /tp critique + operator Q&A
- [[ship-pipeline-enforcement-pretooluse-phase-state-hooks]] — architecture decision
- [[close-check-finalize-phase-make-blocking-unnecessary]] — the prior decision this pattern complements
- [[best-practices-enforcement-mechanism-grok-build]] — the detection+enforcement framework this extends

## Auto-related

- [[skill-graph]]
- [[I'm-going-to-create-a-hook-to-enforce-discovery-be]]
- [[skill-catalog]]
- [[Python-Behavior-Tree-Framework-for-Autonomous-LLM-Agents--Technical-Specificatio]]
- [[claude-code-cli-agent-configuration-and-workflow-patterns]]

