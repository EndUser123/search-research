---
title: "External-state cross-check as structural fix"
created: 2026-07-21
source: session-2026-07-21
tags: [structural-fix, verification, tooling-design, failure-mode, llm-behavior, design-pattern]
summary: >
  When a behavioral rule fails repeatedly, the structural fix is to derive a
  signal from external state that the actor cannot self-certify. Rules can be
  rationalized past; tooling that cross-checks against state the actor doesn't
  control cannot be. The design test for a proposed fix: does the signal come
  from state outside the actor's control? If yes, it's structural; if no, it's
  another rule wearing a tool's clothing.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
relations:
  - target: wiki/concepts/plausible-narratives-substitute-for-verification
    type: refines
  - target: wiki/concepts/verification-before-completion-principle
    type: related
  - target: wiki/concepts/examples-over-rules-escape-hatch
    type: related
---

# External-state cross-check as structural fix

## The design test

When a behavioral rule fails repeatedly (the rule exists, the actor breaks it,
the failure recurs), the question is not "how do I make the rule stronger" but
"what kind of intervention would have prevented this without depending on the
actor's discipline?"

The answer, when one exists: **derive a signal from state the actor cannot
self-certify.** This is the "cannot self-certify" test, and it distinguishes
structural fixes from rules wearing tool clothing.

| Proposed intervention | Passes the test? | Why |
|---|---|---|
| "Add a rule: verify before trusting" | No | The actor can rationalize past the rule; the rule itself is just text the actor reads |
| "Add a Stop hook that checks for hedge words" | Partial | The hook fires on the actor's *output*, which the actor controls; clever phrasing bypasses |
| "Add a tool that compares the handoff's recorded git HEAD to current HEAD and flags drift" | **Yes** | The actor wrote the handoff; the actor does not control current HEAD; the signal is derived from state outside the actor |
| "Add a lint check that the cited file:line still exists in the current tree" | **Yes** | Same — the tree is external to the author |

## Why this works (the mechanism)

Behavioral rules fail because the actor can construct a plausible narrative
that makes the rule feel inapplicable in the current case. (See
[[plausible-narratives-substitute-for-verification]] — "the rule says verify,
but I already have a status field that answers the question, so verifying
would be redundant.") The narrative overrides the rule because the actor
*controls the narrative*.

External state cannot be narrated past. The actor cannot talk git HEAD into
matching the handoff's recorded sha. The actor cannot talk a missing file into
existing at the cited path. The signal derived from external state is
independent of the actor's reasoning, so it lands even when the actor has
fully convinced itself the verification is unnecessary.

This is why the HEAD-drift column in `list_handoffs.py` works where the rule
"re-verify cited paths before acting" (Hard Constraint #2 in the handoff
SKILL.md) didn't: the rule depends on the triager's discipline; the column
derives its signal from `git rev-parse HEAD`, which the triager cannot
manipulate.

## Relationship to adjacent concepts

This concept is a **design pattern** — it tells you *what kind* of structural
fix to build. It complements:

- [[verification-before-completion-principle]] — the consumer-side discipline
  ("verify claims with tool output"). This page is the producer-side design
  pattern ("build tools that make the verification automatic by deriving
  signals from external state"). Together: discipline tells the consumer to
  verify; this pattern tells the tool-builder what to verify *against*.
- [[examples-over-rules-escape-hatch]] — another response to "rules failed,"
  but about encoding strategy (examples vs rules) rather than signal source
  (external vs actor-controlled). Different axis, compatible.
- [[plausible-narratives-substitute-for-verification]] — names the failure
  mode (Disguise 5: metadata-self-report-as-answer). This page names the
  structural fix for that disguise.

## Worked example: the HEAD-drift column

**The recurring failure.** Across multiple sessions, the model triaged
handoffs by trusting their self-reported `status: open` fields without
verifying that the handoff's tree references still existed. The workspace had
a rule (Hard Constraint #2: "if `accurate_as_of_head` differs from current
HEAD, re-verify cited paths"). The rule was ignored every time.

**Failed interventions considered.**
1. *Stronger rule wording* — fails the test; the actor controls whether to
   apply the rule.
2. *A Stop hook that warns on stale handoffs* — partial; the hook fires on
   output, but the actor can phrase around it.

**Structural fix (passes the test).** A `/handoff list` CLI flag (`--head
$(git rev-parse HEAD)`) that compares each handoff's `accurate_as_of_head`
against current HEAD and prints `head:DRIFT` / `head:?` / nothing per row.
The signal is derived from git HEAD, which the triager does not control. The
triager sees `head:DRIFT` on a row and cannot rationalize it away — the
tree has demonstrably moved since the handoff was written.

**What changed.** The rule still exists in SKILL.md, but the *default triage
path* now surfaces the signal automatically. A triager who runs
`list_handoffs.py --head` gets the verification for free; a triager who
doesn't gets nothing worse than before. The intervention doesn't require the
actor to remember the rule — it makes the rule's conclusion visible.

## Where this doesn't apply

The pattern requires an external state source the actor cannot manipulate.
When no such source exists, structural fixes of this form aren't available,
and the remaining options are discipline (rules) or encoding (examples).

- *Code review quality* — the "external state" would be the reviewer's
  independent judgment, but if the reviewer is the same model, it shares the
  actor's blind spots. This is the B-class failure mode; structural fixes
  here require a genuinely different model or human, not just a different
  tool.
- *Future intent* — there is no external state source for "what someone
  plans to build" until they write it down or act on it. The fix here is
  honesty about the gap ([[plausible-narratives-substitute-for-verification]]
  Disguise 3), not a cross-check.

## Design heuristic

When you catch yourself proposing "add a rule" or "strengthen the existing
rule" in response to a recurring failure, run the test:

1. What external state would have flagged this failure?
2. Can the actor manipulate that state? (If yes, find different state.)
3. Can a tool cheaply derive a signal from that state at the point of action?
4. If yes to (2)=no and (3)=yes: build the tool. The rule becomes a fallback,
   not the primary intervention.

If the answer to (1) is "nothing" or the answer to (2) is "yes," the
structural fix isn't available and you're back to discipline + encoding. Say
so honestly rather than dressing a rule up as a structural fix.

## Falsifier

If, after the HEAD-drift column ships, the next triage still trusts stale
handoffs without re-verifying despite seeing `head:DRIFT`, the pattern failed
— the signal was available and ignored. At that point the problem is not
information access (the column showed the drift) but active disregard, and
the fix is a blocking hook, not a displaying tool. The pattern's claim is
that external-state signals *reduce* rationalization; if they don't, the
claim is wrong.

## Related

- [[plausible-narratives-substitute-for-verification]] — the failure mode this pattern fixes
- [[verification-before-completion-principle]] — the consumer-side discipline
- [[examples-over-rules-escape-hatch]] — a different axis of response to rule failure
- `P:/.grok/skills/handoff/__lib/list_handoffs.py` — the worked example (`--head` flag)

## Auto-related

- [[operator-collaboration-style-and-leverage]]
- [[exemption-logic-as-conflict-signal]]
- [[verification-before-completion-principle]]
- [[plausible-narratives-substitute-for-verification]]
- [[yt-is-notebooklm-pipeline-improvements]]

## Sources

- Session 2026-07-21 — triage of 8 handoffs where 4 of 8 dispositions were wrong until proof was forced per item
- `P:/.grok/skills/handoff/SKILL.md` Hard Constraint #2 (stale-data immunity via `accurate_as_of_head`)
- The HEAD-drift column design discussion (`/tp` dialogue earlier in session-2026-07-21)
