---
title: "Mechanical enforcement over behavioral reminder for operator-preference capture"
created: 2026-07-27
source: session-019fa48a (/why on missed opencode/PI preference)
tags: [decision, capture-failure, operator-directive, mechanical-enforcement, retrieval-gate, extractor, agent-control, failure-pattern]
summary: >
  When the operator states a preference in a session and it is not promoted to a
  durable artifact, future sessions cannot find it. The naive fix is a behavioral
  rule ("remember to capture preferences at session close"). The chosen fix is
  mechanical: (1) an extractor script that backfills directives from transcripts,
  (2) a qmd-indexed wiki concept as the single source of truth, (3) an AGENTS.md
  retrieval rule that fires before routing recommendations. Mechanical enforcement
  wins because behavioral rules are exactly what failed — the decision-and-fix
  documentation rule already existed but did not fire.
agent: grok
host: both
cognitive_load: 2
verification: operator-confirmed
sources:
  - "session-019fa48a (/why RCA on 'why didn't you know' failure)"
  - "P:/.data/wiki/concepts/operator-model-routing-directives.md"
  - "P:/.agents/scripts/extract_operator_directives.py"
relations:
  - target: wiki/concepts/operator-model-routing-directives.md
    type: companion
  - target: wiki/concepts/reactive-pattern-matching-and-closure-pressure.md
    type: related
  - target: wiki/concepts/decision-and-fix-documentation-rule.md
    type: refines
  - target: wiki/concepts/llm-instruction-non-compliance-activation-gap-2026.md
    type: related
---

# Mechanical enforcement over behavioral reminder for operator-preference capture

## Decision context

**The problem:** the operator said "I told you that before" when I recommended
OpenRouter as the default Nemotron routing. The preference (use opencode/PI,
avoid OpenRouter) had been stated in prior sessions but was never promoted to
any durable artifact — not the wiki, not a handoff, not AGENTS.md. I could not
find what was not captured.

**The naive fix:** add an AGENTS.md rule saying "capture operator preferences
at session close." This is a behavioral reminder — it depends on the model
remembering to fire the rule under session fatigue, closure pressure, and
context-window limits.

**Why the naive fix is insufficient:** the workspace already had the
decision-and-fix-documentation-rule which says "if you just shipped
something, stop and ask: did I document the decision?" That rule existed and
did not fire. Adding another behavioral rule on top of a rule that already
failed is the same failure class — it depends on the same mechanism (model
self-discipline) that already broke.

## The decision

**Chosen: mechanical enforcement via three components.**

1. **Extractor** (`P:/.agents/scripts/extract_operator_directives.py`) —
   scans prior session transcripts mechanically (1004 sessions in 40s), extracts
   operator-stated preference/directive candidates using a scoring system
   (preference verbs × context nouns). Output: a review file for promotion.
   This is the backfill — it catches what past sessions missed.

2. **Durable concept** ([[operator-model-routing-directives]]) — the single
   qmd-indexed source of truth for confirmed directives. Future sessions query
   this via `qmd search` and find it. This is the persistence layer.

3. **Retrieval gate** (AGENTS.md rule under "Search before proposing") — before
   recommending a routing default, query the wiki for operator directives. If
   nothing found, ask the operator. This is the enforcement layer — it fires
   mechanically before every routing recommendation.

## Selection criterion

**Axis optimized: reliability under pressure.** Behavioral rules decay under
closure pressure and session fatigue. Mechanical enforcement (scripts + indexed
artifacts + mandatory query gates) does not.

**Why mechanical wins on this axis:** the extractor runs deterministically
(no model judgment needed), the wiki concept is qmd-indexed (findable by any
future query), and the AGENTS.md retrieval gate fires before a recommendation
is made (the model must run the query before proposing). Each component has a
single correct behavior with no judgment component — exactly the "code-vs-LLM
split" principle from `/gitpack` (deterministic code owns the mechanical work;
the LLM owns the judgment).

## Steelman of the rejected alternative (behavioral reminder)

**The rejected option:** add an AGENTS.md rule: "At session close, promote any
operator-stated preferences to a wiki concept."

**Why it was reasonable:** it's simpler (one rule, no script), follows the
existing decision-and-fix documentation pattern, and works when the model
remembers to fire it. For high-attention sessions with clear boundaries, it
would work fine.

**Why it loses:** it depends on the model remembering to fire the rule, which
is exactly the mechanism that failed. The decision-and-fix rule already existed
and didn't fire for the Nemotron preference. Adding another behavioral rule on
the same broken mechanism is not a structural fix. The extractor + retrieval
gate removes the dependence on model self-discipline for the specific failure
class of operator-preference capture.

## What this means for our workspace

- **For operator preferences on any topic** (not just model routing): the
  extractor's `CONTEXT_SIGNALS` list can be extended to cover workflow
  preferences, tool preferences, format preferences, etc. The same three-layer
  fix (extractor + wiki concept + retrieval gate) applies.
- **The extractor is a proposal tool, not auto-promotion.** It surfaces
  candidates; the operator or a session curates them into the wiki concept.
  This is deliberate — auto-promoting from transcripts risks capturing noise
  (skill body text inflates scores). Human curation is the quality filter.
- **The retrieval gate fires before routing recommendations specifically.**
  It does not fire before every recommendation (that would be too broad). The
  gate is scoped to the failure class: routing/model/transport/provider defaults.
- **Second instance (2026-07-27):** the same pattern was applied to
  architectural recommendations (fork/vendor/swap/replace/rewrite). Before
  proposing such an option for a system with wiki coverage, query the wiki
  for prior decisions on that system. If found, cite the decision and state
  whether new context overturns it. The failure: proposed "fork qmd" as if
  novel when [[qmd-patch-durability-strategy]] explicitly documented
  rejecting it with a re-evaluation trigger that had fired. Prior decisions
  SHOULD be overturned when new evidence warrants — the rule governs the
  *process* (cite first, then make the case), not whether re-evaluation is allowed.

## Falsifier

This decision is wrong if:
- The extractor consistently misses real directives (scoring patterns too narrow)
  → tighten the patterns; the script is extensible
- The retrieval gate never fires (the AGENTS.md rule is buried and forgotten)
  → this is the same behavioral-rule failure; if it happens, consider a hook
    that blocks routing recommendations without a wiki query receipt
- The wiki concept goes stale (directives overturned but not updated)
  → the extractor surfaces newer directive statements that contradict old ones;
    curation catches this during promotion
- Mechanical enforcement is overkill (behavioral rules actually work fine)
  → if no "I told you that before" incidents recur after 3 months without the
    extractor running, the behavioral path was sufficient and the extractor is
    unnecessary overhead

## Sources

- Session 019fa48a — the `/why` RCA that identified the capture failure
- `P:/.agents/scripts/extract_operator_directives.py` — the mechanical extractor
- `P:/.data/wiki/concepts/operator-model-routing-directives.md` — the durable concept
- `~/.grok/AGENTS.md` § "Operator directive retrieval" — the retrieval gate
- decision-and-fix-documentation-rule — the pre-existing behavioral rule that did not fire
- [[reactive-pattern-matching-and-closure-pressure]] — why behavioral rules fail under pressure

## Receipts

- **Extractor mechanism** — `P:/.agents/scripts/extract_operator_directives.py`
  functions `score_message()` (lines 120-145) and `scan_session()` (lines 148-170):
  scores user messages by `PREFERENCE_SIGNALS × CONTEXT_SIGNALS`, requires both
  for high precision. Verified this session: 1004 sessions scanned, 489 candidates
  extracted in 40s.
- **Durable concept findability** — qmd search `nemotron routing operator
  directive preference` returns `operator-model-routing-directives` as top-3
  result (all 3 chunks). Receipt: `qmd search` this session, exit 0.
- **Retrieval gate** — `~/.grok/AGENTS.md` § "Operator directive retrieval"
  (added this session under "Search before proposing"): mandates `qmd search`
  for directives before routing recommendations. Receipt: search_replace this
  session, read-back verified.
- **Behavioral rule that did not fire** — `~/.grok/AGENTS.md`
  "Decision-and-fix documentation rule": "if you just shipped something, stop
  and ask: did I document the decision?" Existed before this session; the
  Nemotron preference was not captured despite the rule being in context.
