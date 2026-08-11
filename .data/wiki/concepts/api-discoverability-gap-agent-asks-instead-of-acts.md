---
title: "Agent doesn't discover existing waiver API → asks operator instead of acting"
slug: api-discoverability-gap-agent-asks-instead-of-acts
created: 2026-08-11
source: session-019fee63
tags: [needless-confirmation, api-discoverability, evidence-first-default, enforcement-surface, mechanical-enforcement]
summary: >
  The agent had the correct disposition ("waive for now, review at VS-05")
  but asked the operator "which do you prefer?" because it didn't know the
  waiver API existed. The capability was present; the discoverability was
  not. The structural fix: surface the escape hatch in the enforcement
  surface (the block message itself), not in a prose rule the agent must
  remember.
agent: grok
host: both
cognitive_load: 3
verification: observed
relations:
  - target: wiki/concepts/evidence-first-default-and-needless-confirmation.md
    type: extends
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: extends
  - target: wiki/concepts/stop-hook-review-gate-hash-invalidation-loop.md
    type: related
---

# Agent doesn't discover existing waiver API → asks operator instead of acting

## The pattern

An LLM agent is blocked by an enforcement gate (Stop hook quality gate).
The agent has already derived the correct disposition ("waive for now,
review at ship-time"). But the agent doesn't know the waiver mechanism
exists — the API (`write_waiver()`, `waiver_gate.py`) is present in the
codebase but not surfaced at the decision point. The agent asks the
operator "which do you prefer?" instead of acting on its derived
disposition.

This is a **discoverability gap**, not a **capability gap**. The system
has the mechanism; the agent doesn't know about it at the moment it
matters.

## Reference incident (2026-08-10, session 019fee63)

The Stop hook blocked on a missing `/review` receipt mid-vertical-slice
(VS-02 done, VS-03/04/05 remaining). The agent's response contained the
derived answer: *"VS-02 is mid-build, not shippable. The review should
run when the vertical slice reaches VS-05."* — then it asked *"Which do
you prefer?"*

The waiver mechanism (`write_waiver()` at `quality_gates_frontmatter.py:619`,
the anti-loop fix at `gate_diagnostics.py:570`) had existed since
2026-08-04. Session 019fe7e9 had used it 12 times successfully on the
same day. But the VS-02 agent didn't know about it.

The operator flagged the interaction as "not efficient."

## Why this extends [[evidence-first-default-and-needless-confirmation]]

The evidence-first-default rule says: "when you have already stated a
default, lead, or recommendation in your response, act on it rather than
asking the user to confirm." This incident adds a dimension the original
concept doesn't cover: **the agent can't act on its derived default if it
doesn't know the API exists.**

The rule assumes the agent has access to the mechanism. When the mechanism
is a function in a Python file the agent hasn't read, the rule fires but
the action path is invisible. The agent defaults to asking because asking
is always available, while the specific API might not be.

## The structural fix: enforcement surface IS discoverability surface

The fix is NOT to document the API in AGENTS.md (prose rule — ~50%
compliance ceiling under pressure). The fix is to **surface the escape
hatch in the block message itself** — at the exact moment the gate fires.

Before (the block message that caused the ask):
```
To waive these gates, the operator must authorize it.
```

After (surfaces both options at the decision point):
```
Options:
  1. Satisfy the gate: run the skill (e.g., /review).
  2. Waive for mid-build milestone:
     python ~/.grok/scripts/waiver_gate.py --gate review --reason "..."
```

The enforcement surface (the block message) IS the discoverability
surface. The agent reads the escape hatch in the same text that tells
it the gate fired. No prose rule to remember; no API to discover. The
path of least resistance becomes the correct path.

This follows [[mechanical-enforcement-over-behavioral-reminder]]: make
good behavior the default, not a behavioral rule the agent must remember
under pressure.

## How this generalizes

Any enforcement gate that has a waiver/bypass mechanism should surface
both options (satisfy + waive) in its block message. This applies to:

- Quality gates (Stop hook)
- Pre-commit hooks (block message should mention `--no-verify` for WIP)
- Permission gates (should mention the override path)
- Skill enforcement (should mention the waiver file path)

The principle: **if the system has an escape hatch, the block message
must name it.** A block message that says "you are blocked" without
naming the escape hatch forces the agent to either ask the operator
(needless confirmation) or discover the mechanism independently (which
it may not do under pressure).

## Falsifier

This concept is wrong if: the block message surfaces the escape hatch
AND the agent still asks the operator instead of using it. That would
mean the discoverability gap is not the root cause — the root cause
would be deeper (the agent prefers asking for social/RLHF reasons
regardless of available action paths). On this host, the fix shipped
(2026-08-10, commit fa6fb04) and the gate has not been tested enough
to confirm the agent uses the surfaced escape hatch reliably. The
falsifier is currently untested.

## Receipts

- Root cause analysis: `/why` session 019fee63, Cause A (behavioral)
- Fresh-lens critique: `/tp` subagent (53 tool calls) confirmed the gap was discoverability, not capability
- Waiver mechanism: `quality_gates_frontmatter.py:619` (`write_waiver()`)
- Block message fix: `quality_gates_frontmatter.py:920-935` (commit fa6fb04)
- Proven usage: session 019fe7e9 wrote 12 successful waivers on 2026-08-10
