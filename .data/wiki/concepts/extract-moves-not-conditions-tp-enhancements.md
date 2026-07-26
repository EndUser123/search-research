---
title: "Extract moves not conditions — /tp decomposition, tiered output, uncertainty surfacing"
created: 2026-07-25
source: session-20260725 (/tp edits, commit c8a6875)
tags: [tp-skill, session-quality, decomposition, prioritized-output, operator-catch, uncertainty-labels, decision]
summary: >
  When a session produces unusually high-quality output, the temptation is to templatize the conditions (pre-populated wiki, real-time operator catches). That produces cargo-cult quality — the conditions don't reproduce. The alternative: extract the *moves* that produced the quality and make them structural. Three moves added to /tp: (1) Step 0.7 decomposition-first pre-step for multi-item bundles, (2) prioritized-list output contract for multi-decision targets, (3) operator-catch surfacing block at end of every synthesis. The design principle: moves are reproducible, conditions are not.
agent: grok
host: grok
cognitive_load: 3
verification: observed
sources:
  - session-20260725 (commit c8a6875 on ~/.grok/skills/tp/SKILL.md)
relations:
  - target: wiki/concepts/coupling-inventory-as-mandatory-design-section.md
    type: related
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: related
  - target: wiki/concepts/subprocess-as-degradation-boundary.md
    type: related
---

# Extract moves not conditions

## Decision context

**Why this decision was needed:** session 019f9bfe produced unusually high-quality output (operator's words: "this is a great prioritized list, hard to get this quality"). The operator asked what allowed it — not as a curiosity question, but as a "can we make this structural?" question. The temptation is to templatize the session: identify what was different and bake it into a workflow. But the highest-quality moments came from conditions that won't reproduce:

- The wiki was pre-populated with prior decisions on exactly this topic
- The operator caught three errors in real time (model attribution, wiki-not-checked, `/tp quick` misrecommendation), each materially changing the output
- The question was rich enough to reward decomposition

Nothing can automate real-time operator catches. Templatizing "operator catches errors" produces nothing. The decision question: what *moves* can we extract that fire on the next multi-item target without requiring the conditions to reproduce?

## The decision

**Extract three moves into `/tp` as structural enhancements, leave the conditions alone.** Each move is reproducible; none depends on the operator or the wiki state.

| Move | Where in /tp | What it does |
|---|---|---|
| **Decomposition-first pre-step** | new Step 0.7 (before Step 1) | When target is a multi-item bundle, decompose into independent tracks (implementation / architecture / dependency / workflow / research) and flag cross-track entanglement before Step 1 bundles the wrong unit. |
| **Prioritized-list output contract** | Step 3 synthesis section | When target is multi-decision, emit as tiered numbered list (Architectural / Implementation / Wiki / Separate workstreams) with recommendation + why + confidence per item. Forces load-bearing vs deferrable separation. |
| **Operator-catch surfacing** | Step 3 synthesis end | Every synthesis ends with `Confidence / What would change this / What I didn't verify` block. Surfaces the model's own soft spots as targets for operator catches. |

## Why these three moves and not the other two

The original decomposition identified five moves that contributed to session quality. Three became structural; two were deliberately left as conditions:

- **Move: two-lens critique on the framing** → left as condition. This already exists in `/tp`'s architecture (default mode spawns a fresh subagent). The session's quality came from the operator catching that the spawn used the wrong model family (glm-5-2 on a glm-5-2 parent = same-lens). The fix for *that* is better model-attribution in the spawn logic, not a new move — and it's fragile because it depends on the operator noticing the attribution error in real time.
- **Move: skills composed, didn't compete** → left as condition. This is an emergent property of having well-scoped skills (`/why` does RCA, `/wiki` captures, `/tp` critiques, `/check`/`/review` verify). It can't be extracted into a single skill's move because it's a property of the *fleet*. A future "skill composition audit" could make it structural, but that's a workspace-level project, not a `/tp` enhancement.

The three chosen moves share a property the two rejected ones lack: **each is local to `/tp` and fires on a detectable target shape**. Decomposition fires on multi-item bundles. Tiered output fires on multi-decision targets. Uncertainty surfacing fires on every synthesis. None requires fleet-level coordination or operator real-time attention.

## The principle generalizes beyond /tp

"Extract moves not conditions" applies to any future session-quality retro. The pattern:

1. Decompose what produced the quality into specific moves (concrete actions the model or operator took) vs conditions (circumstances that happened to be present).
2. For each move, ask: does this fire on the next target without requiring the conditions to reproduce? If yes, it's extractable.
3. For each condition, ask: can it be automated? If no (e.g., "operator catches errors in real time"), leave it alone — templatizing it produces theater.
4. Extract the moves as structural gates in the relevant skill. Leave the conditions.

The failure mode this prevents: a session produces high-quality output → the team writes a "do everything this session did" workflow → the workflow bakes in conditions that don't reproduce → the next session follows the workflow and gets cargo-cult quality (the form without the substance). Extracting moves avoids this because moves are reproducible by definition; conditions aren't.

## Selection criterion + steelman

**Selection criterion:** reproducibility without conditions. The chosen option had to produce quality on the next multi-item target, not just when this session's conditions happen to recur.

**Steelman of the rejected alternative (templatize the session):** define a "rich multi-item session" workflow with mandatory wiki queries, two-lens spawns, and explicit "wait for operator catch" pauses. This would capture everything that worked. It composes with existing skills cleanly — `/tp session` already does opportunity review, `/www` does wiki queries, `/check` does verification.

**Why the steelman lost:** it bakes in conditions that don't reproduce. A "wait for operator catch" pause is not automation — it's a request for the operator to do work the system can't do itself. Mandatory wiki queries produce noise when the wiki has no relevant concepts (this session's `/tp` Step 0.5 query returned mostly unrelated concepts). The conditions produced quality *this time* because they happened to align; baking them in produces theater on sessions where they don't align.

The moves, by contrast, fire regardless of conditions: decomposition helps on any multi-item target, tiered output helps on any multi-decision target, uncertainty labels help any time the operator is catching errors.

## Falsifier

This decision is wrong if, within 6 months:
- **Step 0.7 decomposition fires on every `/tp` invocation** (too broad — single-question targets get falsely decomposed). Mitigation: the trigger is explicit (≥2 distinct track types) and there's a "do NOT decompose when the bundle is one problem with N symptoms" guard.
- **Step 0.7 never fires on real multi-item targets** (too narrow — the trigger misses the pattern it's designed for). Falsifier: run `/tp` on 10 multi-item targets; if Step 0.7 fires on 0, the trigger is broken.
- **The prioritized-list output fires on single-decision targets** (wrong shape for the question). Mitigation: the contract explicitly says "do NOT use when the target is a single decision."
- **The operator-catch surfacing block becomes performative** (model emits confident-sounding labels that don't actually surface soft spots). Mitigation: the block is short (3 lines), cheap to emit honestly, and the value comes from the operator pushing on whichever line feels wrong — not from the labels being perfect.

## What this means for our workspace

- **The `/tp` skill** now has three new structural moves. Each fires on a specific target shape (multi-item / multi-decision / any synthesis). None depends on conditions that don't reproduce.
- **The "extract moves not conditions" principle** is itself the most generalizable output of this session. It applies to any future "this session was high-quality, how do we repeat it?" question. The answer is never "templatize the session" — it's always "name the moves, leave the conditions."
- **The wiki concept `raising-coding-best-practices-in-ai-agents`** already names the underlying pattern: "behavioral rules fire at the moment of dismissal; review gates detect the violations mechanically." This concept extends that pattern from *code review* to *skill design* — moves are mechanical gates, conditions are behavioral rules.

## Receipts

- **`~/.grok/skills/tp/SKILL.md` Step 0.7** (lines ~308-340) — decomposition-first pre-step with trigger (multi-item bundle), track-type taxonomy, entanglement flag, and explicit "do NOT decompose when one problem" guard. Directly inspected and added in commit c8a6875.
- **`~/.grok/skills/tp/SKILL.md` Step 3 prioritized-list output contract** (lines ~470-498) — tiered numbered list format with per-item recommendation + why + confidence, triggered by multi-decision targets.
- **`~/.grok/skills/tp/SKILL.md` Step 3 operator-catch surfacing** (lines ~486-498) — 3-line block at end of every synthesis (Confidence / What would change this / What I didn't verify).
- **Session transcript 019f9bfe** — the operator's "what allowed this session's quality?" question, my decomposition into 5 moves, and the decision to extract 3 as structural (moves) and leave 2 alone (conditions).

## Sources

- [[coupling-inventory-as-mandatory-design-section]] — same session's `/design` decision; both decisions exemplify the "extract the move, not the condition" principle.
- [[raising-coding-best-practices-in-ai-agents]] — the underlying pattern (behavioral rules vs mechanical gates); this concept extends it from code review to skill design.
- [[subprocess-as-degradation-boundary]] — same session's architectural principle; related because the /tp enhancements came from the same session-quality extraction process.
- Costa, A. L., & Kallick, B. (1993). "Through the Lens of a Critical Friend." The two-lens architecture that produced the coupling insight is what made the session high-quality; the enhancements make that architecture's outputs more structured.
