---
title: "Research Artifact Revision Invalidation — State Consistency for Knowledge"
created: 2026-08-08
source: operator-correction
tags: [durable-principle, research, revision-integrity, epistemic-discipline]
summary: >
  Research artifacts (wiki concepts, design docs, plans) need state consistency
  the same way software systems do. Evidence changes are state transitions;
  derived claims (summaries, confidence labels, recommendations, falsifiers,
  frontmatter, downstream artifacts) are cached outputs of that evidence. When an
  upstream premise is materially changed or retracted, every derived statement
  becomes stale until revalidated. The failure mode: treating revision as LOCAL
  text editing rather than DEPENDENCY INVALIDATION — patching only the section
  where the correction arose while leaving contradicted conclusions in the
  summary, frontmatter, confidence section, and falsifier. The fix is structural:
  a whole-artifact contradiction sweep + a claim ledger proving it was run.
agent: grok
host: both
cognitive_load: 2
verification: single-source-verified
sources:
  - "Operator review of youtube-workspace-sidebar-extension-build-research (2026-08-08) — identified 6 residual contradictions after a correction pass"
  - "youtube-workspace-sidebar-extension-build-research.md — reference incident: corrected body but left stale frontmatter/decision-context/falsifier/confidence-summary"
relations:
  - target: wiki/concepts/narrative-as-signal.md
    type: related
  - target: wiki/concepts/theatrical-contrition-and-over-apologetic-response-patterns.md
    type: related
  - target: wiki/concepts/correction-response-discipline-anti-binary-swing.md
    type: extends
  - target: wiki/concepts/evidence-scope-discipline-no-inflation.md
    type: related
---

# Research Artifact Revision Invalidation — State Consistency for Knowledge

## The durable principle

**Research artifacts need state consistency just like software systems do.**

Map the analogy explicitly:

| Software system | Research artifact |
|---|---|
| Input data / state | Evidence, assumption, observation |
| Cached derived output | Summary, confidence label, recommendation, falsifier |
| Cache invalidation on input change | Whole-artifact sweep when a premise changes |
| Stale cache bug | Old conclusion still presented as current after correction |
| Cache key mismatch | `videoId` freshness bug (a different instance of the same class) |

Evidence changes are **state transitions**. Derived claims are **cached outputs**. A changed upstream premise should invalidate every downstream cache. Before publishing a revised artifact, prove that every current conclusion was derived from the **current evidence state**, not an earlier one.

## The failure mode

> **The agent treats revision as local text editing rather than dependency invalidation.**

When a foundational conclusion changes, every downstream statement derived from it becomes suspect. The derivation chain:

```
assumption
   ↓
finding
   ↓
recommendation
   ↓
summary
   ↓
confidence label
   ↓
falsifier
   ↓
frontmatter / metadata
   ↓
downstream artifacts (handoffs, plans, other concepts that link in)
```

Patching the finding without recomputing the chain creates **epistemic stale state**. A future reader (human or LLM) consuming the summary, confidence section, or frontmatter can recover the **exact conclusions you just corrected** — defeating the revision.

This is conceptually identical to the `videoId` freshness bug: an old result is still allowed to paint onto a new state. The wiki concept on YouTube transcript extraction documents that instance in code; this concept documents the same class of bug in knowledge artifacts.

## Reference incident (2026-08-08)

`[[youtube-workspace-sidebar-extension-build-research]]` was corrected after operator review. The agent fixed the body sections (transcript acquisition, Ask demotion, sidePanel overreach, isolated-world error, `steipete/summarize` omission) but left **six residual contradictions** that the operator caught:

1. Frontmatter `summary:` still said `chrome.sidePanel` was "the recommended architecture" and that maintainers "abandoned" YouTube AI — both retracted in the body.
2. "What the research changed" repeated the retracted causal claim ("both maintainers abandoned").
3. Native-chapter section still said "A content script reads these directly" — contradicting the isolated-world correction one section earlier.
4. Falsifier still framed Ask tiers as "NOT the primary path" — contradicting the revised Ask-as-preferred-opportunistic-backend.
5. Confidence summary resurrected BOTH rejected conclusions ("disconfirmed by practitioner choices," "chrome.sidePanel as recommended: FACT, HIGH").
6. `FORK (provisional)` was ahead of the evidence — the doc itself admitted the two decisive questions were unanswered.

Root cause across all six: the agent edited the section where the correction arose, but did not search the whole artifact for the old claim and every derived statement of it. The fix in that session: a whole-artifact `grep` for the old phrasings + a **claim ledger** proving propagation.

## Rule 11 — Revisions invalidate derived conclusions (the propagation rule)

When evidence, an assumption, a conclusion, or a recommendation is materially changed or retracted, treat **all derived statements as stale until revalidated**. Search the entire artifact for:
- the old claim itself
- its synonyms and paraphrases
- its consequences (any "therefore…" derived from it)
- confidence labels attached to it
- summaries that include it (frontmatter `summary:`, decision-context, "headline finding," abstracts)
- recommendations that depend on it
- falsifiers that reference it
- metadata fields (frontmatter tags, `verification:`, `relations:`)
- downstream artifacts (handoffs, plans, other wiki concepts that cite it)

**Recompute them from the new state**, not from the old. Do not patch only the section where the correction arose.

**Before persisting a revised artifact, run a consistency sweep:** compare the executive summary / frontmatter, decision context, body findings, recommendations, falsifiers, confidence summary, and next-actions. **No superseded claim may remain presented as current.** Explicit historical/retraction records are allowed only when clearly marked as historical (e.g., "record of revisions") and must not contaminate current summaries or confidence statements.

**Mechanical enforcement — the claim ledger.** For material revisions, append (or update) a small table proving the sweep ran:

| Decision-critical claim | Current state | Previous state | Propagated everywhere? |
|---|---|---|---|
| <claim> | <new> | <old> | yes/no |

This makes the propagation check auditable rather than a behavioral promise. It catches residual contradictions immediately — in the reference incident, it would have surfaced all six before commit.

## Rule 12 — Reviewer feedback is a hypothesis, not authority (the anti-anchoring rule)

When substantive criticism arrives (operator, hook, reviewer, subagent), do **not** swing from anchoring on your own proposal to anchoring on the reviewer. The desired behavior is:

```
challenge arrives
      ↓
reopen the evidence
      ↓
independently falsify / confirm
      ↓
update belief only to the extent supported
```

NOT:

```
original researcher says X → believe X
reviewer says not-X       → believe not-X
```

**Required classification** for each substantive criticism: **CONFIRMED / PARTIALLY CONFIRMED / REJECTED**, with evidence (a tool-call receipt or direct file citation), not assertion. "You were right" is socially fine but epistemically insufficient — agreement is not validation. The agent must independently verify the claim before adopting it.

This rule is a specialization of `[[correction-response-discipline-anti-binary-swing]]` for the research-review case. The general rule's falsifier applies: if the decomposition ritual runs ≥3 times per session on unambiguous corrections where simple withdrawal is correct, the rule has become theater. Rule 12 fires on **substantive** criticism (claims about evidence, causality, technical mechanism) — not on unambiguous "drop it" instructions, where the operator's word is final.

**Differentiating correction sources** (from the parent rule): operator corrections are intent-based (high signal-to-noise) — when the operator says *drop* something, drop. But when the operator offers *substantive technical criticism* ("this causal claim has no receipt"), that is a hypothesis to verify, not an authority to obey blindly. The distinction is: intent instructions → obey; technical claims → verify.

## When NOT to apply

- **Trivial wording fixes** — no derivation chain to invalidate; edit and move on.
- **Pure additions** (new section, new source) — nothing derived is changed; no sweep needed.
- **Unambiguous operator "drop it"** — obey per Rule 12's source-differentiation; do not run verification theater.
- **Single-claim corrections with no downstream dependencies** — if nothing in the artifact derives from the changed claim, the sweep returns nothing and that's fine (the sweep itself is cheap; run it anyway for safety).

Same threshold as `[[problem-first-systems-decomposition]]`'s "when NOT to apply" — avoid over-process on work that doesn't need it.

## Relationship to existing rules

- **`[[narrative-as-signal]]`** — Rule 11's parent: a plausible story (here, "I fixed it") is not verification. The sweep + ledger is the receipt.
- **`[[correction-response-discipline-anti-binary-swing]]`** — Rule 12's parent: decompose corrections, classify, don't binary-swing. Rule 12 specializes it to research-review.
- **`/evidence-scope-discipline-no-inflation`** — a strong umbrella claim than the weakest subclaim is forbidden; Rule 11 ensures the umbrella gets recomputed when a subclaim changes.
- **`[[self-review-before-shipping-advice]]`** — the sweep IS the self-review, scoped to revision propagation.
- **Claims-require-receipts (AGENTS.md)** — the claim ledger is the receipt that the propagation actually happened.

## Decision context

**The real question behind this concept:** during a `/www` research run on a YouTube sidebar extension, the operator reviewed the corrected artifact and found that while the agent had understood the substantive criticism and fixed the body sections, **six residual contradictions** survived in the frontmatter, decision-context, native-chapter section, falsifier, and confidence summary — old conclusions that the corrections had rendered false but that were never retracted. The operator generalized this into a durable principle: *research artifacts need state consistency the same way software systems do*, and proposed two rules (revision invalidation; reviewer-feedback-as-hypothesis). This concept captures that principle so future revisions propagate correctly rather than leaving stale state for the next reader to recover.

**What changed because of this:** the reference artifact (`[[youtube-workspace-sidebar-extension-build-research]]`) got a whole-artifact sweep + a claim ledger; this concept becomes the durable home for the rule so it applies to every future revision, not just that one.

## What this means for our workspace

- **APPLY on every material revision** of a wiki concept, design doc, or plan: when a conclusion is changed or retracted, run a whole-artifact `grep` for the old phrasing and recompute every derived statement (summary, confidence, falsifier, frontmatter, recommendations).
- **APPEND a claim ledger** to material revisions as proof the sweep ran — this makes propagation auditable rather than a behavioral promise.
- **PROMOTION candidate for AGENTS.md** (operator decision): rules 11 and 12 are candidates for the per-turn thought-partner protocol or the hard-rules section, so they fire on every revision, not just when an agent remembers this concept. The operator framed them as items "11" and "12" of durable instructions — the natural home is alongside the existing correction-response-discipline and claims-require-receipts rules. (Not done unilaterally — AGENTS.md is a shared structured doc; recommend, don't auto-edit.)
- **No retirement** — this concept extends `[[correction-response-discipline-anti-binary-swing]]` and `[[narrative-as-signal]]`; it does not supersede them.

## Receipts

- **Reference incident (6 residual contradictions):** OBSERVED 2026-08-08 by direct file read of `P:/.data/wiki/concepts/youtube-workspace-sidebar-extension-build-research.md` — frontmatter lines 9-17 ("chrome.sidePanel API as the recommended sidebar architecture," "both open-source maintainers abandoned"), decision-context line 50 ("both open-source maintainers who faced the same choice abandoned"), §4 line 156 ("A content script reads these directly"), falsifier line 303 ("tier 3–4 disappear... NOT the primary path"), confidence lines 311/313 ("disconfirmed by practitioner choices," "chrome.sidePanel as recommended: FACT, HIGH"). All six confirmed by reading the file, not by accepting the review on authority.
- **Post-sweep verification:** OBSERVED via `grep` for the old phrasings (`abandoned YouTube|chrome\.sidePanel.*recommended|bonus, not the primary|disconfirmed by practitioner|content script reads these directly`) — the only surviving matches are in explicitly-marked retraction/correction context (§2 line 103, §5 line 163), none presented as current.
- **The videoId-freshness analogy:** OBSERVED from the `steipete/summarize` CHANGELOG this session ("reject YouTube caption... when the tab navigates to another video during extraction") — same class of bug (old result painting onto new state), different substrate (code vs knowledge artifact).

## Falsifier

- If applying Rule 11's sweep + ledger adds ≥30% overhead to every minor edit with no caught contradictions, it's over-applied — restrict to material revisions (retracted/changed conclusions, not wording).
- If Rule 12's CONFIRMED/PARTIAL/REJECTED classification runs on unambiguous "drop it" instructions, it's theater — those obey, not verify.
- If a session's claim-ledgers show zero propagation catches across ≥5 material revisions, the sweep isn't being run honestly — audit the grep queries.
