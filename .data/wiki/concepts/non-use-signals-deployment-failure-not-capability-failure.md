---
title: "Non-use signals deployment failure, not capability failure"
created: 2026-08-05
source: session-019fa8f8 (harvest retirement incident)
tags: [system-design, decomposition, retirement, automation, structural-pattern, host-grok]
summary: >
  When the operator reports "I never use X," that is a signal about the
  deployment layer (how X is invoked), not about the capability (what X does)
  or the mechanism (how X is implemented). Before removing X: decompose into
  capability / mechanism / deployment, assess each independently, and redeploy
  the valuable logic into an automated flow the operator already uses.
  Reference incident: harvest skill retired → leverage scoring, verification
  lifecycle, and cross-session pattern detection were lost → recovered from
  git and embedded into /todo's automated pipeline.
agent: grok
host: grok
cognitive_load: 2
verification: inferred
relations:
  - target: wiki/concepts/mechanical-enforcement-over-behavioral-reminder.md
    type: complement — that concept says enforcement should be mechanical; this says valuable logic should be automated. Same principle, different domain.
  - target: wiki/concepts/designing-harnesses-that-make-good-behavior-the-path-of-least-resistance.md
    type: related — both about making the right thing happen automatically
  - target: wiki/concepts/replacement-before-investigation-pattern.md
    type: adjacent — that's about investigating before replacing; this is about decomposing before removing
  - target: wiki/concepts/symptom-to-abstraction-escalation.md
    type: adjacent — that's about escalating from session-specific to structural; this is about the decomposition step before that escalation
---

# Non-use signals deployment failure, not capability failure

## The pattern

Every system has three layers:

| Layer | What it is | Harvest example |
|-------|-----------|----------------|
| **Capability** | What the system does (the outcome it produces) | Obligation tracking, leverage ranking, pattern detection |
| **Mechanism** | How it's implemented (the algorithms and data structures) | Event store, keyword scoring formula, arm→verify→collect lifecycle |
| **Deployment** | Where and how it's invoked (the interface the operator interacts with) | Standalone skill requiring manual `/harvest` invocation |

**Non-use is a deployment-layer signal.** The operator saying "I never use X" tells you the deployment is failing — the interface requires too much manual effort, competes with too many other priorities, or doesn't integrate into the operator's natural workflow.

It does NOT tell you:
- The capability is worthless (the outcome may still be needed)
- The mechanism is unsound (the algorithms may still be correct)
- The system should be removed

## The correct response

**Decompose before removing:**

1. Identify the capability — what outcome does this system produce?
2. Identify the mechanism — what algorithms implement the capability?
3. Assess: does any surviving system already produce this capability?
4. If no surviving system covers it: extract the mechanism and redeploy into an automated flow the operator already uses
5. THEN remove the failing deployment (the standalone interface)

## Reference incident (2026-08-05)

**What happened:** The operator said "I never use harvest because there's always so many other things to do." I (the agent) removed the entire skill — including its leverage scoring algorithm, verification lifecycle, and cross-session pattern detection.

**What went wrong:** I conflated all three layers. Non-use of the deployment (manual skill invocation) was treated as evidence that the capability (obligation tracking) and mechanism (leverage scoring) were also worthless.

**The operator's correction:** "Just because I wasn't using it doesn't mean it's not valuable. If the logic captures value that we should implement, then we should keep it and use it automatically somewhere else."

**The fix:** Recovered the scripts from git history, extracted the three valuable algorithms into `~/.grok/skills/todo/__lib/leverage.py`, and embedded them into `/todo`'s automated render pipeline. Now leverage scoring fires automatically on every `/todo` scan output — no manual invocation needed.

## Why this is the complement of mechanical-enforcement-over-behavioral-reminder

`[[mechanical-enforcement-over-behavioral-reminder]]` says: "don't rely on behavioral rules that don't fire under pressure; make enforcement mechanical."

This pattern says: "don't rely on manual invocation that doesn't happen under time pressure; make valuable logic automatic."

Both are instances of the same deeper principle: **the path of least resistance should be the correct path.** If the operator has to remember to invoke something, they won't. If the logic fires automatically as part of a flow they already run, it delivers value without requiring remembering.

## Falsifier

This pattern is wrong if:
- The capability genuinely duplicates something a surviving system already does (removal was correct — the mechanism added no unique value)
- The mechanism is unsound (the algorithm produces wrong results — fixing the mechanism is needed before redeployment)
- The operator confirms the capability itself is no longer needed (context changed, the outcome is no longer desired)

In any of these cases, removal without redeployment is the correct disposition.

## How to apply

Before retiring any skill, hook, script, or system the operator reports as unused:

```
1. Decompose: capability / mechanism / deployment
2. Check: does a surviving system already produce this capability?
   - YES → removal is safe (the capability is covered)
   - NO → proceed to step 3
3. Extract: pull the mechanism (algorithm, logic, data structures)
4. Redeploy: embed into an automated flow that fires without manual invocation
   - /todo scanner output → auto-applied scoring
   - /close gate → auto-run verification
   - /aar pattern detection → auto-scanned at session boundaries
5. Remove the failing deployment (the standalone interface)
```

This is the structural fix for "valuable logic trapped behind an unused interface."
