---
title: "Forgetting ≠ Rejecting: Distinguish Non-Use from Disapproval"
created: 2026-08-02
source: session-2026-08-02
tags: [operator-profile, design-pattern, behavioral, correction]
summary: >
  When an operator doesn't use a feature, distinguish between "doesn't want it"
  (rejection — remove it) and "forgets to use it" (non-use — remind them).
  The failure mode: interpreting forgetfulness as rejection and removing a
  valuable feature, making the problem worse.
agent: grok
host: both
cognitive_load: 1
verification: observed
confidence: 0.9
last_verified: 2026-08-02
half_life_days: 365
relations:
  - target: wiki/concepts/couple-triggers-to-events-that-actually-fire.md
    type: refines
  - target: wiki/concepts/operator-profile-receipt-enforcement-20260802.md
    type: related
---

# Forgetting ≠ Rejecting: Distinguish Non-Use from Disapproval

## Decision context

**The problem:** when designing the wiki post-completion recommendations, I initially excluded `/wiki lint` from the recommendation list, citing "operator never uses it." The operator corrected: "I don't think I've ever used it" doesn't mean "I don't want to use it" — it means "I forget to."

I had interpreted non-use as rejection. The operator was telling me it's forgetfulness.

**Why this matters:** removing lint from recommendations (treating forgetfulness as rejection) makes the problem WORSE — the operator forgets even harder because nothing reminds them. The fix is the opposite of what I did: add the recommendation, because reminders are the correct response to forgetfulness.

## The pattern

```
Operator doesn't use feature X
  │
  ├─ Interpretation A: "They don't want X" → Remove X (WRONG if it's forgetfulness)
  │
  └─ Interpretation B: "They forget X" → Remind about X (CORRECT for forgetfulness)
```

**How to tell the difference:**
- **Rejection:** operator has expressed disapproval, found it doesn't work, or actively avoids it
- **Forgetfulness:** operator has never mentioned it negatively, would use it if reminded, finds it useful when they do use it

## Applied to this session

| Feature | Operator signal | Correct interpretation | Correct action |
|---|---|---|---|
| `/wiki lint` | "I don't think I've ever used it" | **Forgetfulness** — no disapproval expressed, lint IS valuable | Add to periodic recommendations |
| Session-start probes | Pre-mortem found they're an anti-pattern | **Rejection** — evidence-based disapproval | Remove (correctly) |
| `/dream` post-completion | Always offered, operator sometimes picks it | **Accepted** — keep it | Keep in recommendations |

## The design implication

For features the operator forgets:
- **Periodic reminders** are the right trigger (not automatic execution, not silence)
- Reminders should fire when contextually relevant (after ≥5 wiki writes for lint, not after every single write)
- The reminder must be actionable (number-pickable in the recommendation list)

For features the operator rejects:
- Remove them or redesign them
- Don't keep recommending something they've explicitly disapproved

## Receipts

- **Operator statement:** [FACT] "I don't think I've ever used it" — session transcript 019fbf77, prompt_58. No disapproval expressed.
- **My incorrect interpretation:** [FACT] I removed lint from recommendations in commit 3008b3d, citing the triggers pattern as justification.
- **Operator correction:** [FACT] "Add it if it's useful, because I forget, not because I think it's evil" — session transcript 019fbf77, prompt_60.
- **Fix applied:** [FACT] Re-added lint to recommendations in commit fb68764 with the forgetting-vs-rejecting distinction documented.

## Falsifier

This concept is wrong if:
- The operator starts explicitly rejecting features they previously forgot (the distinction collapses)
- Periodic reminders for forgotten features are consistently ignored (reminders don't work)
- The operator prefers automatic execution over reminders for forgotten features

## What this means for our workspace

1. **Before removing a feature for "non-use," check: did the operator reject it or forget it?** Disapproval = remove. Forgetfulness = remind.
2. **The recommendation list is the mechanism for forgotten features.** Not automatic execution (too intrusive), not silence (worsens the forgetting).
3. **Periodic cadence matters.** Don't remind about lint after every write — remind when there's been enough new content to make lint valuable (≥5 writes or ≥30 days since last lint).

## Related

- [[couple-triggers-to-events-that-actually-fire]] — refined: for forgotten maintenance, reminders are the right trigger
- [[operator-profile-receipt-enforcement-20260802]] — operator profile patterns
- [[epistemic-knowledge-system-design-2026]] — where the lint coupling issue surfaced
