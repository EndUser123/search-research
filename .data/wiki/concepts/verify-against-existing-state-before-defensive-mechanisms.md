---
title: "Verify-against-existing-state before proposing defensive mechanisms"
created: 2026-07-25
source: session-2026-07-25-why-self-diagnosis
tags: [verify-first, defensive-mechanism, over-engineering, design-discipline, existing-gate, closure-pressure, model-behavior, structural-fix]
summary: >
  Before proposing any defensive mechanism (a new gate, staging layer,
  fallback, or redundancy), verify whether an existing gate already
  covers the failure mode you're defending against. The 2026-07-25
  session produced two over-engineering errors in the same hour
  (rejecting auto-write to wiki on contamination grounds when sync
  review already covered it; proposing staging when the synchronous
  review WAS the gate) because the model generated plausible defenses
  faster than it audited existing coverage. Codifies the structural
  fix: a named step between "I see a risk" and "I propose a mechanism."
agent: grok
host: both
cognitive_load: 2
verification: observed
sources:
  - session-019f9a89 (/why self-diagnosis on this session's errors, 2026-07-25)
  - P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md (the auto-write rejection + staging proposal incidents)
relations:
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: refines — that concept names the behavioral root; this concept is the structural mitigation for one specific instance
  - target: wiki/concepts/plausible-narratives-substitute-for-verification.md
    type: instance-of — the defensive mechanism is the plausible narrative; the audit is the verification
  - target: wiki/concepts/optimal-vs-blanket-rule-application.md
    type: related — both argue for checking whether a rule/mechanism is needed before adding it
  - target: wiki/concepts/synchronous-review-direct-write-pattern.md
    type: produced-by — the staging rejection that motivated this concept
---

# Verify-against-existing-state before proposing defensive mechanisms

## Decision context

**The problem behind this principle:** during the 2026-07-25 session, the model made two over-engineering errors within an hour:

1. **Rejected auto-write to wiki** on contamination grounds ("unreviewed findings pollute `/wiki query` results"). The model proposed three options: defer to operator (evaporation risk), auto-write directly (contamination risk), or staging (the "safe" middle). The model recommended staging.
2. **Proposed staging** (write to `inbox/` → review → promote) as the structural fix for the contamination concern.

Both errors had the same shape: the model generated a plausible defense against a real risk, WITHOUT checking whether an existing gate (synchronous cross-model review at write time) already handled that risk. When the operator asked "if a3's review is synchronous, why do we need to stage?", the staging proposal collapsed immediately — the existing gate already covered the failure mode the staging was defending against.

The pattern: **fluent-helpful reflex generates defenses faster than verify-against-existing-state discipline can audit them.**

## The principle

**Before proposing any defensive mechanism, ask:**

> "Does an existing gate already cover the failure mode I'm defending against? Name the existing gate, or explicitly acknowledge the gap."

| Situation | Action |
|-----------|--------|
| Existing gate covers the failure mode | **Do not propose the new mechanism.** Cite the existing gate. Move on. |
| Existing gate partially covers it | Propose only the *delta* — what the existing gate misses. Name the existing gate and the gap. |
| No existing gate covers it | Propose the new mechanism. State that no existing gate covers this failure mode. |

This is a **named step between "I see a risk" and "I propose a mechanism."** It converts the audit from optional (skipped under pressure) to mandatory (named in the workflow).

## Why this is worth a wiki concept

The underlying behavioral pattern (`reactive-pattern-matching-and-closure-pressure`) is already documented. But the *specific structural mitigation* — "audit existing coverage before proposing new coverage" — was not named anywhere. Without a name, it cannot be queried, referenced, or enforced. This concept gives it a name and a slug so future design dialogues can invoke it.

## Worked examples (from the session that produced this concept)

### Example 1 — the staging proposal (rejected)

- **Risk I saw:** unreviewed wiki concepts contaminate `/wiki query` results
- **Defense I proposed:** staging directory (`inbox/` → review → promote)
- **Existing gate I missed:** synchronous cross-model review at write time (the review IS the gate; if it passes, the concept is reviewed by definition)
- **Operator's question that collapsed it:** "if A3's review is synchronous, why do we need to stage?"
- **Lesson:** I generated the defense before auditing the existing gate. If I had asked "does sync review already cover contamination?", the answer was yes, and staging would never have been proposed.

### Example 2 — the auto-write rejection (partially corrected)

- **Risk I saw:** auto-write violates the "no durable side effects in a diagnostic command" principle
- **Defense I proposed:** reject auto-write entirely; defer to operator-invoked `/wiki`
- **Existing gate I missed:** the mechanical gate (5 criteria) + cross-model review already filter quality; the operator is informed not asked, and can delete post-hoc
- **Operator's correction:** "I'd love to capture all the mistakes... how do we not lose the findings?"
- **Lesson:** I over-weighted a general principle ("no side effects") without checking whether the specific side effect was already gated.

## How to apply this at design time

When designing a skill, gate, or workflow:

1. **State the failure mode you're worried about** (one sentence).
2. **Query existing gates:** "What currently prevents or catches this failure mode?" List them.
3. **If the list is non-empty:** cite the strongest existing gate. Decide: is it sufficient? If yes, stop. If no, propose only the delta.
4. **If the list is empty:** propose the new mechanism with explicit rationale for why no existing gate covers this.

This applies to:
- Proposing a new hook (does an existing hook already check this?)
- Proposing a new validation step (does the existing validator already catch this?)
- Proposing a staging layer (does an existing review already gate this?)
- Proposing a fallback (does an existing path already handle this?)
- Proposing a new rule in AGENTS.md (does an existing rule already cover this?)

## What this means for our workspace

1. **Design dialogues should include an "existing coverage audit" step.** Before any "I propose X" statement, the audit runs. This is the structural fix the operator's pushback represented in the session.
2. **The /preflight skill is the existing instrument for this** in implementation contexts. For design contexts, this concept extends the same principle: check what exists before proposing what's new.
3. **This concept is queryable.** Future sessions designing gates can `/wiki query "existing gate coverage"` and find this principle.
4. **The principle generalizes beyond defensive mechanisms.** "Does an existing rule/skill/gate already cover this?" applies to AGENTS.md additions, new skills, new hooks, new validators. The cost of not asking is parallel paths and wasted effort (the exact failure the "Search before proposing" rule in AGENTS.md targets — this concept extends it from documents/implementations to gates/mechanisms).

## Falsifier

This concept is wrong, or has been resolved, if:

- **Design sessions consistently produce zero over-engineering errors after applying this principle.** Then the principle has been internalized and the concept can be marked `status: superseded` by the internalized behavior.
- **The principle consistently fails to prevent over-engineering** (designers apply the audit but still propose redundant mechanisms). Then the principle is insufficient and needs mechanical enforcement (e.g., a pre-proposal hook that requires naming an existing gate or stating "no existing gate covers this").
- **The "existing coverage audit" adds more ceremony than value** (designers spend more time auditing than the errors cost). Then the principle's threshold for application needs tightening.

## Methodology roots

- Surfaced by the `/why` v3 self-diagnosis run on session-019f9a89's own errors (2026-07-25)
- The `/why` run found the behavioral root ([[reactive-pattern-matching-and-closure-pressure]]) and named this structural mitigation as the highest-leverage fix
- Extends the AGENTS.md "Search before proposing" rule from documents/implementations to gates/mechanisms
- Related to [[optimal-vs-blanket-rule-application]] — both ask "is this addition necessary?" before adding
- Related to [[plausible-narratives-substitute-for-verification]] — the defensive mechanism is the plausible narrative; the audit is the verification
- The staging rejection that produced this concept is documented in [[synchronous-review-direct-write-pattern]] § "Why this works (and staging doesn't, for sync review)"

## Receipts

- **The staging proposal incident:** session-019f9a89, operator message "if a3 answers q3 well, why do we need to stage?" — collapsed the staging proposal. Receipt: the conversation turn itself; the staging proposal and its rejection are in the session transcript.
- **The auto-write rejection incident:** session-019f9a89, operator message "I'd love to capture all the mistakes... how do we not lose the findings?" — corrected the over-conservative rejection. Receipt: same session transcript.
- **The /why v3 self-diagnosis that surfaced this fix:** ran via spawn_subagent on session-019f9a89; output classified the root cause as `reactive-pattern-matching-and-closure-pressure` and named this principle as the highest-leverage structural fix. Receipt: the /why run output in this session's context.
- **AGENTS.md "Search before proposing" rule:** `~/.grok/AGENTS.md` § "Search before proposing (mandatory)" — the existing rule this concept extends from documents to gates. [Receipt: direct read of the AGENTS.md file in this session]
