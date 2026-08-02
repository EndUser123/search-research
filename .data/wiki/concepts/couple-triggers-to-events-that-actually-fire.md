---
title: "Couple Triggers to Events That Actually Fire"
created: 2026-08-02
source: session-2026-08-02
tags: [design-pattern, anti-pattern, triggers, lifecycle, structural-fix]
summary: >
  When designing a trigger for a feature (cache refresh, suggestion generation,
  health check), couple it to an event that actually happens in the operator's
  workflow — not to a command that theoretically exists but is never invoked.
  The failure mode: machinery built around a trigger that doesn't fire is dead
  code that looks alive in documentation.
agent: grok
host: both
cognitive_load: 1
verification: observed
confidence: 0.9
last_verified: 2026-08-02
half_life_days: 365
relations:
  - target: wiki/concepts/epistemic-knowledge-system-design-2026.md
    type: related
  - target: wiki/concepts/passive-monitoring-over-active-probing.md
    type: related
  - target: wiki/concepts/inference-in-code-blind-spot.md
    type: related
---

# Couple Triggers to Events That Actually Fire

## Decision context

**The problem:** during the epistemic knowledge system design, I coupled the debt cache refresh to `/wiki lint` Phase 4. The operator pointed out: "I don't think I've ever used it." The cache would never refresh — the feature was dead code from day one.

**The pattern:** this is the same structural failure as the session-start health probes (coupled to a trigger — session start — that would have caused harm) and the old tool-failure awareness (coupled to lint, not to research). In all three cases, the design assumed a trigger would fire when it doesn't.

## The anti-pattern

```
Feature designed → coupled to Trigger X → Trigger X never fires → Feature is dead code
```

Symptoms:
- Documentation says "this runs when X happens" but X doesn't happen
- The feature works when manually invoked but never fires automatically
- The operator doesn't know the feature exists because it never surfaced

## The fix

**Couple to events that actually fire in the operator's workflow.** The operator's actual workflow:
- Invokes `/www` frequently (research)
- Invokes `/wiki` frequently (knowledge capture)
- Invokes `/go` frequently (implementation)
- Invokes `/tp` frequently (critique)
- Does NOT invoke `/wiki lint`
- Does NOT invoke `/main --fix`

**Decision rule:** before coupling a feature to a trigger, ask: "has the operator invoked this trigger in the last 7 days?" If no, find a different trigger.

## Applied to the epistemic debt cache

| Trigger | Fires? | Coupled? |
|---|---|---|
| `/wiki lint` Phase 4 | ❌ Never invoked | Was coupled (removed) |
| `/www` Phase 1 | ✅ Every research run | Now coupled (cache read + stale check) |
| `/wiki` post-write | ✅ Every concept write | Now coupled (cache refresh) |
| Standalone manual | ✅ On-demand | Available |

## Falsifier

This concept is wrong if:
- The operator starts using `/wiki lint` regularly (then coupling to lint is fine)
- The triggers I claim "fire" actually don't (verify against transcript evidence)
- The overhead of refreshing on every write is too costly (currently 2s — negligible)

## What this means for our workspace

1. **Audit existing features for dead triggers.** Several features in the skill ecosystem may be coupled to `/wiki lint` or `/main --fix` — both of which the operator rarely or never invokes. If a feature's trigger doesn't fire, the feature doesn't exist.

2. **Default trigger coupling:** `/www` Phase 1 and `/wiki` post-write are the two highest-frequency events in this fleet. New features that need automatic triggering should default to one of these.

3. **The `/wiki lint` coupling itself isn't wrong** — lint IS the right place for comprehensive maintenance. The problem is that lint is manual and infrequent. Features that need real-time data should couple to writes, not to maintenance passes.

## Receipts

- **Operator never uses /wiki lint:** [FACT] Operator stated directly in session 2026-08-02: "I don't think I've ever used it." Session transcript 019fbf77, user_query prompt_58.
- **Debt cache was coupled to lint:** [FACT] Commit 4c0be5b wired epistemic_debt.py into wiki SKILL.md as "Run as part of /wiki lint Phase 4." Decoupled in commit abfb379.
- **/www and /wiki are high-frequency:** [INFERENCE] based on session frequency — this session invoked /www 5+ times and /wiki 3+ times. Not mechanically verified across all sessions.
- **Cache refresh cost (2s):** [FACT] measured: `python epistemic_debt.py --cache` runtime after O(n) optimization = ~2s for 843 concepts.

## Related

- [[epistemic-knowledge-system-design-2026]] — where this pattern surfaced
- [[passive-monitoring-over-active-probing]] — same pattern (coupled to a trigger that would cause harm)
- [[inference-in-code-blind-spot]] — the session that started the meta-analysis
