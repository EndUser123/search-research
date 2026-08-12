---
title: "Requirement-failure patterns found on first real /req-check use: mechanism-unnamed fix requirements and decision-grade gating on open unknowns"
created: 2026-08-12
source: first real /req-check use (2026-08-12) validating close-py followup Item 6 ("receipt writer for backgrounded tasks")
sources:
  - file:///P:/docs/handoffs/close-py-post-tp-review-followup-20260811/HANDOFF.md
  - file:///P:/.data/wiki/concepts/posttooluse-fires-on-tool-call-completion-not-process-completion.md
  - file:///P:/.data/wiki/concepts/decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming.md
tags: [requirements, requirement-validation, req-check, decision-grade, ambiguity, verification-receipt]
agent: grok
host: both
verification: session-observed
cognitive_load: 2
summary: >
  Two requirement-failure classes surfaced by /req-check's first real use:
  (1) mechanism-unnamed fix requirements — a fix-requirement that names the
  goal ("fire when X completes") but not the mechanism, and the mechanism
  may not exist (a completion-event hook that can't capture exit codes);
  (2) decision-grade gating on open decision-reversing unknowns — a
  requirement whose adoption depends on unmeasured fleet data is not READY,
  it is NEEDS_CLARIFICATION with the data collection as the unblock. Both
  are catchable by the requirement-quality checklist (AMBIGUOUS mechanism /
  INCOMPLETE acceptance / UNVERIFIABLE constraint) before the requirement
  drives implementation.
relations:
  - target: wiki/concepts/great-adversarial-review-skill-design-patterns
    type: refines
  - target: wiki/concepts/posttooluse-fires-on-tool-call-completion-not-process-completion
    type: related
  - target: wiki/concepts/decision-integrity-in-research-blocking-unknowns-and-decision-red-teaming
    type: related
---

# Requirement-failure patterns (first real /req-check use)

## Decision context

The `/req-check` skill (built 2026-08-12) was test-fired for the first time on
a real requirement: close-py followup Item 6 — "Wire verification_receipt_writer.py
to fire when backgrounded tasks complete, not just at PostToolUse time.
Multi-terminal safe; must not race with concurrent receipt writes." The skill
returned NEEDS_CLARIFICATION. Two durable requirement-failure classes emerged
that recur across fix-requirements generally.

## Pattern 1 — Mechanism-unnamed fix requirements

**Shape:** a fix-requirement states the goal ("fire when backgrounded tasks
complete") but not the mechanism, and the mechanism may not exist. The
checklist label is AMBIGUOUS with a specific sub-defect: the completion
*signal* is undefined.

**This session's instance:** the wiki already documents that a completion-event
hook cannot capture exit codes
(`[[posttooluse-fires-on-tool-call-completion-not-process-completion]]`) — so
"fire when backgrounded tasks complete" had no currently-implementable event
to bind to. The requirement named a goal whose mechanism was documented as
unavailable, and no fallback mechanism was named.

**Detection:** in Phase 1, for each fix-requirement item, ask: "what is the
bindable signal/event/trigger this item names?" If the item names a goal
without a bindable mechanism, label AMBIGUOUS and quote the missing signal.
Then check the wiki for whether the mechanism exists before suggesting one.

**Fix pattern:** rewrite the requirement to name the mechanism OR explicitly
defer the mechanism choice to a spike ("the completion signal is undefined;
options are A (Stop-time retroactive) and B (platform event, currently
unsupported for exit codes); decide after fleet data"). Do not accept a
fix-requirement whose mechanism is documented-unavailable.

## Pattern 2 — Decision-grade gating on open decision-reversing unknowns

**Shape:** a requirement whose adoption depends on unmeasured data (here: the
false-negative vs false-positive tradeoff across the fleet) is not
decision-grade. The handoff itself stated "We do not have this data" — the
requirement's design options each had a known risk class, and choosing between
them without the data is a decision-reversing gamble.

**Detection:** Phase 3 meaning-checks — "comparability" FAIL when the
requirement's acceptance depends on a quantity the workspace hasn't measured.
Also Phase 4 — the load-bearing assumption "the receipt system is the correct
enforcement point" rests on an RCA, not on fleet data.

**Fix pattern:** the verdict is NEEDS_CLARIFICATION with the data collection as
the explicit unblock ("measure false-negative vs false-positive frequency over
N sessions, then decide Option A vs B"). This mirrors the decision-contract
rule: an OPEN decision-reversing unknown blocks DECISION_READY — a requirement
that can't be adopted without the data is the requirement-level analog.

## What this means for our workspace

1. **/req-check is validated** — its first real use returned the correct
   verdict (NEEDS_CLARIFICATION on a genuinely non-decision-grade requirement)
   and caught both patterns above before they drove implementation.
2. **The requirement-failure-patterns concept is now written** (this page),
   closing the handoff's deferred item.
3. **Item 6's requirement stays OPEN** in its handoff with the clarification
   applied: it needs the fleet data (pattern 2) before the Option A/B decision,
   and any implementation must name a bindable mechanism (pattern 1).

## Falsifier

This concept is wrong if: (a) mechanism-unnamed fix requirements routinely
turn out to have obvious bindable mechanisms the checklist missed (the
AMBIGUOUS label would be over-applied); or (b) requirements with open
decision-reversing unknowns are later adopted successfully without the data
(decision-grade gating would be over-strict); or (c) /req-check's first real
use was unrepresentative and the two patterns don't recur in later uses.
