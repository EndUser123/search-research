---
title: "Value-Conditional Automation Escalation: Blanket Rules to Contextual Rules"
date: 2026-08-13
tags: [pattern, automation, skill-authoring, rule-design, adaptive-automation, conditional-autonomy]
host: both
confidence: SUPPORTED
source_quality: multi-source
---

# Value-Conditional Automation Escalation: Blanket Rules to Contextual Rules

## Context

Derived from session 019ffb95 (2026-08-13), where four separate rule changes
all followed the same meta-pattern: blanket rule → context-conditional rule,
where the condition is a value calculation (insurance value vs overhead cost).

## The pattern

**Blanket rules** apply the same behavior in every context regardless of
whether the behavior is optimal for that context. They are safe — they
never over-fire — but they leave value on the table when the behavior would
be beneficial in specific contexts but prohibited by the blanket.

**Context-conditional rules** apply different behavior based on a
distinguishing condition that separates "rule should fire" from "rule should
not fire." The condition is an explicit value calculation, not a heuristic.

The generalization:

```
BEFORE: "Always do X" / "Never do X"
AFTER:  "When <condition>, do X. When not-<condition>, do Y."
```

Where `<condition>` is a value calculation: does the benefit of automation
exceed the cost of the friction it prevents?

## Why this produces better outcomes

Blanket rules exist for good reasons — they prevent over-firing, they're
simple to follow, they don't require judgment. But they have a hidden cost:
**when the rule's rationale doesn't apply in a specific context, the rule
still fires, producing friction or leaving value unrealized.**

The four instances this session:

| Rule | Before (blanket) | After (conditional) | Condition |
|---|---|---|---|
| `/refine` auto-invocation | "Suggest, never auto-invoke" | Auto-invoke for non-trivial tasks | Insurance value > overhead (session failure risk) |
| `/www` search tool | "Use DDG first, always" | Parent uses MCP, subagent uses DDG | Who has tool access (parent vs subagent) |
| `/go` readiness gate | "On failure: suggest only" | Auto-invoke /refine | Task is non-trivial vs trivial |
| `/handoff` needs-refinement | "Suggest /refine" | Auto-invoke /refine | Status field is explicit signal |

In each case, the blanket rule was correct for SOME contexts but suboptimal
for others. The distinguishing condition was already known (task complexity,
tool access, explicit status signal) — it just wasn't wired into the rule.

## The domain: adaptive automation

This belongs to **adaptive automation** from human factors research
(Parasuraman, Sheridan & Wickens, 2000, "A Model for Types and Levels of
Human Interaction with Automation"). Their framework defines multiple
levels of automation, and the core insight is: **the optimal automation
level depends on the task's risk, reliability, and consequence profile —
not on a blanket policy.**

The specific technique is **value-conditional automation escalation**:
moving a decision from human-in-the-loop (suggest) to automated (auto-invoke)
in the specific context where the value calculation is clear and the risk
is low. The operator's "It's our rule, so we can change that" directive
(2026-08-13) is the policy-level authorization to apply this pattern
when the insurance value justifies it.

## Existing instances in this workspace

The workspace already has infrastructure for conditional autonomy — it just
wasn't applied consistently:

| Instance | What it does | Pattern |
|---|---|---|
| Trust escalation ladder (Rungs 1-4) | Agent autonomy scales with risk | Reversibility-conditional |
| Action manifest table (allow/ask/deny) | Same decision, tabular | Risk-class-conditional |
| Advisory vs blocking enforcement | Measurement-first graduated enforcement | FP-rate-conditional |
| `--lite` / `--skip-*` flags | Operator opt-out strips ceremony | Signal-conditional |
| Delegation-packet detection (score ≥4) | Strips H2/H3/H4 horsepower | Task-shape-conditional |
| Adaptive ceremony level (Light/Standard/Deep) | Pipeline depth varies | Prompt-density-conditional |

## When to apply this pattern

Apply when ALL of these are true:

1. A blanket rule exists ("always X" or "never X")
2. The rule's rationale doesn't apply equally in all contexts
3. A distinguishing condition can be identified that separates "rule should fire" from "rule should not fire"
4. The condition is checkable at decision time (not just retrospectively)
5. The value of context-specific behavior exceeds the complexity cost of the conditional

## When NOT to apply

- **Safety-critical rules** — destructive git operations, credential handling. The blanket prohibition is the safety boundary; contextualizing it introduces risk.
- **Rules where the distinguishing condition is genuinely unknowable** — if you can't tell at decision time whether the condition holds, the conditional adds ambiguity without value.
- **Rules where the blanket is already optimal** — some rules are genuinely context-independent (e.g., "verify every edit by reading it back"). Don't add ceremony.

## The meta-process

1. **Observe friction** — a rule fires but the outcome is suboptimal (suggestion gets ignored, budget gets wasted, session dies and work is lost)
2. **Identify the distinguishing condition** — what separates "rule should fire" from "rule should not fire"?
3. **Check the value calculation** — does the benefit of context-specific behavior exceed the complexity cost of the conditional?
4. **Make the rule conditional** — replace blanket with "When X, do Y. When not-X, do Z."
5. **Preserve the original intent** — the old behavior still exists for cases where the condition doesn't hold

## Anti-pattern: theater conditionals

Not every conditional adds value. A conditional that always fires (the
condition is always true) or never fires (always false) is a blanket rule
in disguise — it adds complexity without behavioral change. Check: does
the conditional actually produce different behavior in different contexts?
If not, it's theater.

Example of theater: "When the task is complex, do deep analysis. When not,
do shallow analysis." — if every task is classified as complex, this is
just "always do deep analysis" with extra steps.

## Integration into skill authoring

When writing or editing a SKILL.md rule:

- **Specify the condition, not just the rule.** Instead of "suggest /refine," write "auto-invoke /refine when <condition>; suggest for other cases."
- **State the value calculation.** Why does the condition justify different behavior? What's the insurance value? What's the overhead cost?
- **Preserve the escape hatch.** The operator can still override with explicit signals (--lite, "just do it," "I've already evaluated alternatives").

## Relationship to existing concepts

- [[mechanical-enforcement-over-behavioral-reminder]] — structural fixes over prose. This concept extends that: the structure itself should be conditional, not just mechanical.
- [[advisory-vs-blocking-enforcement-decision-2026]] — measurement-first graduated enforcement. The closest existing instance; this concept generalizes it.
- [[trust-escalation-ladder-autonomous-agent-work]] — rung-based autonomy. This pattern is how individual rules move between rungs.
- [[designing-harnesses-that-make-good-behavior-the-path-of-least-resistance]] — make the right thing easy. Conditional rules make the right thing easy in the specific context where it's right.
- [[invariants-beat-environment-comfort]] — invariants are the ceiling on contextualization. You cannot contextualize away an invariant; you CAN contextualize everything else.

## Sources

- Parasuraman, R., Sheridan, T. B., & Wickens, C. D. (2000). "A Model for Types and Levels of Human Interaction with Automation." IEEE Transactions on Systems, Man, and Cybernetics — Part A: Systems and Humans, 30(3), 286-297.
- Session 019ffb95 (2026-08-13): four instances of the pattern applied to /go, /handoff, /www, and the /refine auto-invocation policy change.
- Operator directive 2026-08-13: "It's our rule, so we can change that" — authorizing policy-level changes when the insurance value justifies it.

## Falsifier

This pattern is wrong if:
- Contextualizing rules introduces more friction than it removes (the complexity cost exceeds the behavioral benefit)
- The distinguishing conditions are unreliable (fire when they shouldn't, or fail to fire when they should)
- Operators consistently override the conditional back to the blanket (the conditional is not trusted)

If any of these recur across 3+ instances, the pattern needs refinement — either better conditions or a return to blanket rules for the affected category.
