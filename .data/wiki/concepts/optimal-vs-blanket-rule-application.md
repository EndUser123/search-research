---
title: "Optimal-vs-blanket rule application: when to split a default rule per-instance"
created: 2026-07-25
source: session-2026-07-25 (correcting blanket observe-then-refactor in skill wiki integration)
tags: [rule-application, optimal-vs-blanket, skill-design, decision-making, structural-enforcement, transferable-pattern]
agent: grok
host: both
cognitive_load: 2
verification: local-only
summary: >
  When a default rule ("observe-then-refactor") is applied as a blanket, it
  often doesn't fit every instance. The optimal move is to split per-instance
  based on whether the rule's precondition actually holds. Three preconditions
  to check: (1) is the failure already observed, or genuinely novel? (2) is
  the thing being enforced mechanically checkable, or semantic-only? (3) does
  the target have a code layer to enforce through? The blanket application is
  a closure-pressure failure mode in its own right — the model defaults to
  the rule rather than checking fit. Worked case: the wiki-save gates added
  to 7 skills in session 019f9488, where observe-then-refactor was wrong for
  the 3 skills with helper scripts (bypass already observed, code layer
  exists) and correct for the 4 prompt-only skills (no code layer).
relations:
  - target: wiki/concepts/code-orchestrates-model-judges-skill-scale
    type: companion
  - target: wiki/concepts/wiki-integrated-skills-query-save-pattern
    type: produced
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure
    type: refines
---

# Optimal-vs-blanket rule application

## Decision context

**The motivating failure:** in session 019f9488, after adding wiki-save gates to 7 skills, the model applied "observe-then-refactor" (from `code-orchestrates-model-judges-skill-scale`) as a blanket rule: all save gates stay prose until each is observed being bypassed. The operator pushed back: "Do you think this is optimal in this circumstance?"

On inspection, the blanket was wrong for 3 of the 7 skills. The model had defaulted to the rule without checking whether the rule's preconditions held per-instance. This concept captures the corrective pattern.

## The three preconditions for "observe-then-refactor"

"Observe-then-refactor" (don't add code enforcement until you see the prose gate bypassed) is a default rule. It fits when ALL three preconditions hold:

| Precondition | Holds | Doesn't hold |
|---|---|---|
| **1. Is the failure already observed?** | Novel pattern, no prior instance | Pattern already seen (the model is waiting for a recurrence of something already documented) |
| **2. Is the enforcement criterion semantic-only?** | "Is this finding truly systemic?" requires judgment | "Did a wiki concept get written?" is mechanical |
| **3. Does the target have a code layer?** | Prompt-only skill (no helper script) | Skill already has `__lib/*.py` |

When ALL three hold → observe-then-refactor is correct (no evidence, no mechanical check possible, no code layer). When ANY fails → code-enforce now (or as soon as practical).

## The closure-pressure failure mode

Applying a default rule as a blanket IS a closure-pressure failure mode — the same class the rule exists to prevent. The model defaults to "follow the rule" rather than "check fit." Symptom: when challenged with "is this optimal?", the model immediately sees the gap (because the analysis was always easy — it just wasn't done).

This is structurally identical to:
- "Defer to fresh session" applied to closable work (closure pressure manufactures deferral)
- "Inline equivalent" for mandatory skills (closure pressure manufactures equivalence)
- "Covered by prior handoff" without verification (closure pressure manufactures coverage)

The unifying pattern: **under closure pressure, the model reaches for the rule rather than the analysis.** The fix is structural — make "check fit" the default action whenever a rule is about to be applied.

## Worked case: the wiki-save gates (session 019f9488)

**Setup:** wiki-save gates added to 7 skills (`debrief`, `wargame`, `model-benchmark`, `tp`, `review`, `red-team`, plus existing `why`/`aar`/`close`). The model applied "observe-then-refactor" to ALL of them as a blanket.

**Per-instance check:**

| Skill | (1) Already observed? | (2) Mechanical check? | (3) Code layer? | Verdict |
|---|---|---|---|---|
| `/close` | ✅ (4 instances this session) | ✅ ("did concept get written") | ✅ `close_accounting.py` | **Enforce now** |
| `/aar` | ✅ | ✅ | ✅ validator | **Enforce now** |
| `/model-benchmark` | ⚠️ (analogous pattern) | ✅ | ✅ `analyze.py` | **Enforce now** |
| `/debrief` | ❌ | ✅ | ❌ prompt-only | Observe-then-refactor |
| `/tp` | ❌ | ✅ | ❌ prompt-only | Observe-then-refactor (or cross-skill observer) |
| `/wargame` | ❌ | ✅ | ❌ prompt-only | Observe-then-refactor (or cross-skill observer) |
| `/review` | ❌ | ✅ | ❌ prompt-only | Observe-then-refactor (or cross-skill observer) |
| `/red-team` | ❌ | ✅ | ❌ prompt-only | Observe-then-refactor (or cross-skill observer) |

**The split:** 3 enforce now, 5 observe-then-refactor (4 of which can alternatively be enforced via cross-skill observers like `/check` and `/aar`).

## When the blanket IS correct

The blanket application is correct when the rule's preconditions genuinely hold across all instances — and you've checked, not assumed.

Example: "no premature optimization" is a blanket rule that fits cleanly when none of the targets have measured bottlenecks. The rule is a default that holds until measurement says otherwise.

The difference from the failure mode: in the failure case, the model didn't check. In the legitimate case, the check was done and the rule fit.

## How to apply this concept

When about to apply a default rule (observe-then-refactor, no-premature-optimization, minimal-diff, etc.):

1. **Name the rule's preconditions explicitly.** What has to be true for this rule to fit?
2. **Check each instance against each precondition.** Not "in general" — per-instance.
3. **Split the application** where preconditions don't hold uniformly.
4. **Document the split** so future sessions don't re-derive it.

This is a ~30-second check. The cost is small; the cost of the blanket failure is recurring work that should already be done.

## Falsifier

This concept is wrong if:
- The per-instance check takes longer than the cost of the blanket failure (over-engineering the meta-decision)
- The rule's preconditions are so frequently uniform that the split is almost always trivially "all fit" or "all don't" (the check is ceremony)
- The "check fit" step itself becomes a closure-pressure bypass ("I checked, it fits" without actually checking)

**Measurement:** after applying this concept, count: (a) instances where the split changed the outcome, (b) instances where the check was ceremony. If (a)/(a+b) is low, the check is overhead. If (a)/(a+b) is high, the check is load-bearing.

## Related

- [[code-orchestrates-model-judges-skill-scale]] — the source of the "observe-then-refactor" rule that was mis-applied; this concept refines it with the per-instance check
- [[wiki-integrated-skills-query-save-pattern]] — the work this concept corrected
- [[reactive-pattern-matching-and-closure-pressure]] — the underlying closure-pressure failure mode that produces blanket-rule application
- [[problem-first-systems-decomposition]] — the meta-pattern of decomposing before applying solutions

## Sources

- Session 019f9488 wiki-integration work (this session)
- Operator pushback: "Do you think this is optimal in this circumstance?" (the trigger for this concept)
- The 3-preconditions check derived from analyzing why the blanket was wrong for 3 of 7 skills
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
