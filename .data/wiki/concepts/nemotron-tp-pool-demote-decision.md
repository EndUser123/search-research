---
title: "Decision: demote nvidia-nemotron-3-ultra from /tp pool position 1 to 4"
created: 2026-07-25
source: session-2026-07-25-tp-pool-alignment
tags: [decision, model-pool, nemotron, serialization-failure, tp-skill, reliability, operational]
summary: >
  Decision (2026-07-25): demote `nvidia-nemotron-3-ultra` from
  position 1 (primary) to position 4 (last-resort before
  parent-inherited) in the /tp Step 2 spawn_subagent pool. Trivial
  READY probes pass (~7.5s) but real /tp-sized prompts (~90-98k
  tokens) fail with `serialization error: invalid type: null,
  expected u32` — reconfirmed 2026-07-23 and 2026-07-25. Aligns
  runtime with wiki guidance; glm-5-2 becomes primary.
agent: grok
host: grok
cognitive_load: 1
verification: observed
sources:
  - session-019f9a89 (Nemotron serde retest, 2026-07-25)
  - P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md (canonical failure doc)
  - C:/Users/brsth/.grok/tool-fallbacks.md (operational table)
relations:
  - target: wiki/concepts/model-tool-calling-capability-matrix.md
    type: implements — runtime change to align with the wiki's canonical guidance
  - target: wiki/concepts/model-pool-not-chain.md
    type: applies-to — pool composition decision per the pool-not-chain principle
  - target: wiki/concepts/tp-parallel-improvement-solution-space.md
    type: related — that concept proposed pool race as mitigation; this decision reduces the need
---

# Decision: demote nvidia-nemotron-3-ultra from /tp pool position 1 to 4

## Decision context

**The problem:** `/tp` Step 2's spawn_subagent pool listed `nvidia-nemotron-3-ultra` as position 1 (the default first try for every `/tp` critique). Trivial READY probes passed (~7.5s, documented 2026-07-22). But real `/tp`-sized prompts (~90-98k tokens) consistently failed with `serialization error: invalid type: null, expected u32` — observed 2026-07-23 and reconfirmed 2026-07-25. Every default `/tp` invocation wasted ~20-50s on a nemotron failure before falling through to glm-5-2.

The wiki canonical page (`model-tool-calling-capability-matrix`) documented the failure as unsolved. The runtime (`/tp` SKILL.md) still had nemotron at position 1. Inconsistent.

**Operational impact of the inconsistency:** the `/tp` skill is the workspace's primary critical-friend instrument. When its first pool member fails on every real invocation, the skill's wall-clock latency doubles (try nemotron → wait ~20-50s for failure → fall through to glm). Operators notice the latency and begin defaulting to `/tp quick` (same-agent, weaker lens) to avoid the wait — which degrades critique quality across the workspace. The demotion restores `/tp`'s default-path reliability.

## The decision

**Pool order changed from:** nemotron → glm → inkling → mimo → parent
**Pool order changed to:** glm → inkling → mimo → nemotron → parent

Nemotron stays in the pool as last-resort before parent-inherited (it may still work on `/tp quick` small prompts). It is no longer the default first try.

## Selection criterion

**Reliability on real prompts.** Cost (free vs paid) is secondary; a free model that fails on every real prompt is more expensive than a paid model that works. Latency is secondary; a fast failure is still a failure.

The criterion is deliberately "reliability" not "quality" — nemotron's reasoning quality may be high (its leaderboard scores are strong), but that quality is inaccessible when the response cannot be parsed. A model that produces excellent analysis that the framework cannot deserialize is equivalent to a model that produces nothing. The criterion reflects what the pool actually depends on: parseable, reliable responses on real-prompt shapes.

## Rationale

1. **Nemotron fails deterministically on real /tp prompts.** The same error (`invalid type: null, expected u32`) reproduced across two sessions, two different prompts, two different invocation paths. Not transient.
2. **glm-5-2 works reliably.** Verified 2026-07-22 (8.0s), 2026-07-23, 2026-07-25 (8.1s on a trivial probe). Subscription-rationed but available.
3. **The position-1 slot determines what every default `/tp` invocation tries first.** Keeping a known-failing model there wastes 20-50s per invocation and risks the pool falling to inline fallback if the operator cancels mid-wait.
4. **Demotion is reversible.** The falsifier (below) names the condition for re-promotion. The edit is one table row; no architectural commitment.

The decision is conservative on purpose: nemotron stays in the pool rather than being removed entirely, because it may work on small `/tp quick` prompts and because removing it loses the optionality entirely. Demotion to last-resort-before-parent preserves the option while making the default path reliable.

## Steelman of the rejected alternative (keep nemotron at position 1)

**Argument for keeping:** nemotron is free; glm is subscription-rationed. On a high-volume `/tp` workload, keeping nemotron first conserves glm quota for when nemotron happens to work (small prompts). The free tier is strategically valuable for a solo operator managing a fleet — every free-model invocation saves rationed quota for tasks where only a paid model will do.

Additionally, the serialization failure might be transient. NVIDIA updates their API; Grok Build updates its serde deserializer. If the failure is fixed next week, having kept nemotron at position 1 means zero re-promotion cost. Demoting and re-promoting is churn.

**Why rejected:** the evidence shows nemotron fails on real /tp prompts, not just large ones. `/tp` critiques are reasoning-lane tasks with substantial context — exactly the prompt shape that triggers the failure. The "small prompt" case rarely arises in default `/tp`. Cost savings from a model that fails are negative (you pay in latency + retry overhead). The quota conservation argument would hold if nemotron worked on a meaningful fraction of real /tp prompts; it doesn't.

The transience argument is addressed by the falsifier: re-promotion is one edit when the condition fires. The cost of demotion now (glm quota consumption) is lower than the cost of keeping nemotron first (latency + inline-fallback risk on every `/tp`). The asymmetry favors demotion.

## Falsifier

Re-promote nemotron to position 1 (or higher) ONLY when this condition is observed:

> **Real tool / large-prompt spawn_subagent succeeds reliably on this host.**

"Reliably" = 3+ consecutive real-prompt successes without serialization errors, across different prompt shapes. A single success is insufficient (could be a small prompt that happens to work). Trivial READY probes do not count (they have always passed and are not representative).

This falsifier is identical to the "solved" condition in [[model-tool-calling-capability-matrix]]. The decision is downstream of the wiki's status: if the wiki says "solved," re-promote; until then, keep demoted.

## What this means for our workspace

- **`/tp` default invocations now try glm-5-2 first.** Lower latency variance, no serialization failures on real prompts. Operators should notice fewer "fresh subagent failed, trying next" cascades.
- **The pool still includes nemotron** as a fallback — if glm is quota-exhausted and inkling/mimo are unavailable, nemotron gets a shot (and may work on small `/tp quick` prompts). This preserves optionality without making a known-broken model the default.
- **The wiki and runtime are now consistent.** The wiki documents the failure; the runtime reflects it in pool ordering. Future sessions grepping either source will find the same guidance, avoiding the "wiki says broken, runtime says primary" confusion that persisted for 2 days.
- **The decision is reversible** when the falsifier fires. No permanent commitment. If NVIDIA fixes the response envelope or Grok Build fixes the serde deserializer, nemotron re-promotes to position 1 in one edit.
- **Cost impact:** glm-5-2 is subscription-rationed; nemotron was free. The shift increases glm quota consumption per `/tp` invocation. This is acceptable because a free model that fails on every real prompt costs more (in latency + retry + inline-fallback risk) than a rationed model that works. The quota tradeoff is the right one.
- **Signals for re-evaluation:** if `/tp` invocations start showing glm quota exhaustion (429s), OR if nemotron trivial-probe latency drops below 5s (suggesting an API change), re-test nemotron on a real prompt to see if the falsifier fires.

### Broader implications beyond /tp

This decision sets a precedent for pool composition across other skills that use `spawn_subagent` with model pools (`/check` verifier pool, `/red-team` specialist pool, future `/review` cross-model pool). The principle: **pool order should reflect reliability on real prompts, not cost tier.** A free model that fails deterministically is more expensive than a paid model that works. Other skills with nemotron in their pools should audit whether the same demotion applies. The `/check` SKILL.md and `/red-team` SKILL.md are the next candidates for this audit.

## Methodology roots

- Operator flagged the runtime/wiki inconsistency in the `/close` summary as a deferred item
- Decision made and shipped in commit `b75a32e` (2026-07-25)
- Aligns with [[model-pool-not-chain]] principle: pool membership adapts to evidence
- The [[multi-producer-cross-model-synthesis]] run later in the same session provided independent confirmation (nemotron failed on the /why assignment with the same error)
- The falsifier mirrors the "solved" condition in [[model-tool-calling-capability-matrix]] — if the wiki says solved, re-promote
- Pool race as alternative mitigation documented in [[tp-parallel-improvement-solution-space]]; this decision reduces the need for racing by putting a reliable model first

## Receipts

- **Nemotron failure on /tp critique (2026-07-23):** `serialization error: invalid type: null, expected u32 at line 1 column 331` on a ~98k-token prompt. Receipt: `C:/Users/brsth/.grok/tool-fallbacks.md` line 79 (the known-broken table).
- **Nemotron failure reconfirmed (2026-07-25):** same error family at column 330 on the /why multi-model assignment (~90k tokens). Receipt: session-019f9a89 spawn_subagent task `019f9ae4` (failed, 10s).
- **glm-5-2 working (2026-07-25):** `READY - glm-5-2 online` trivial probe, 8.1s. Receipt: session-019f9a89 spawn_subagent task `019f9a92` (completed).
- **Pool table state before/after:** `C:/Users/brsth/.grok/skills/tp/SKILL.md` lines 340-346. Before: nemotron at position 1. After: glm at position 1, nemotron at position 4. Receipt: commit `b75a32e` diff.
- **Wiki canonical status:** `P:/.data/wiki/concepts/model-tool-calling-capability-matrix.md` § "Nemotron status: NOT SOLVED" — documents the failure as open with root cause `[UNKNOWN]`. [Receipt: direct read this session]
