---
title: "Multi-dimensional matrix as skill-design organization pattern"
created: 2026-07-25
source: session-2026-07-25 (/tp rewrite around 4D matrix)
tags: [skill-design, organizing-principle, routing-matrix, mental-model, tp, intent-classification, transferable-pattern]
agent: grok
host: both
cognitive_load: 3
verification: local-only
summary: >
  When an AI-agent skill has multiple intersecting decision dimensions (who
  thinks, when to focus, what to target, how to engage), organizing the
  SKILL.md around an explicit multi-dimensional matrix is cleaner than an
  accreted variant list. The /tp rewrite (2026-07-25) crystallized this:
  the old 847-line SKILL.md had grown to 13 named variants across 5+ sessions,
  each adding another axis without naming it. Reframing around a 4D matrix
  (lens × horizon × target × posture) collapsed the variant list into a
  single navigable space. The pattern generalizes to any skill where the
  user's intent selects a point in a multi-axis decision space.
relations:
  - target: wiki/concepts/mental-models-for-tp-and-brainstorming
    type: refines
  - target: wiki/concepts/intent-based-routing-for-ai-agent-skills-2026
    type: extends
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later
    type: related
---

## Summary

The dominant failure mode for AI-agent skills that grow across sessions is
**accretion without structure**: each new variant, parameter, or carve-out
gets appended as another row in the variant table, until the SKILL.md reads
as a list of special cases rather than a coherent system. The `/tp` skill
hit this at 847 lines / 13 variants, accumulated over 5+ sessions.

The operator identified the correct organizing principle: every `/tp`
invocation is a point in a **4-dimensional space** — LENS (who thinks) ×
HORIZON (when to focus) × TARGET (what to critique) × POSTURE (how to
engage). Reframing the SKILL.md around this matrix made the variant table
derive from the matrix rather than the reverse: each named variant
(`/tp session`, `/tp check`, `/tp quick`) is just a labeled point in the
space, and the semantic classifier picks the point automatically from the
user's phrasing.

## Key findings

- **The matrix replaces the variant list, not the variants themselves.**
  Every named variant still exists (`/tp session`, `/tp check`, etc.) and
  can be invoked explicitly. The matrix gives the model a navigable
  decision space so it can route novel phrasings to the right point without
  enumerating every possible phrasing as a trigger phrase. The 13-variant
  list collapsed to a 4D matrix with named points.

- **Each dimension must be a real decision axis, not a label.** A dimension
  qualifies if (a) the value changes the routing decision, AND (b) multiple
  values are reachable. /tp's four dimensions all qualify:
  - LENS: two-lens (spawn) vs. same-agent (inline) — changes who generates
    the critique
  - HORIZON: now/next/later/all — changes which critique domains fire
  - TARGET: live question / prior turn / session state / file / workspace —
    changes what the critique operates on
  - POSTURE: critique / diagnostic / opportunity review / dialogue —
    changes the engagement mode

  A non-qualifying "dimension" would be one with only one reachable value
  (cosmetic, not a routing axis).

- **Dimensions compose; explicit overrides auto-detection.** The matrix's
  power is that dimensions compose: `horizon=now AND confidence=high` means
  "core domains only," while `horizon=later OR confidence=low` means
  "full depth." The more demanding dimension wins. Explicit invocation
  (`/tp session`) bypasses the classifier entirely. This composition is
  what makes the matrix strictly more expressive than a variant list — the
  variant list cannot represent "horizon=now AND target=session-state" as
  a single row.

- **Confidence as a composable depth dimension (from /reason).** The 5th
  dimension considered was `confidence` (high/medium/low), borrowed from
  the `/reason` skill's routing table. Rather than adding it as a 5th axis,
  it composes with horizon as a depth calibrator: whichever demands more
  depth wins. This avoids axis proliferation — adding dimensions
  multiplicatively increases the routing space. The right move was to
  compose confidence with horizon (depth sub-space) rather than treat it
  as independent.

- **The matrix is the help output, not just the design.** `/tp help` now
  shows the matrix inline. This is not decoration — it teaches the user
  the model the skill uses, so they can either invoke a named point
  (`/tp session`) or just phrase the question in a way the classifier
  routes correctly ("what should I do right now?" → horizon=now).

- **EVIDENCE_GAP:** the matrix rewrite is structurally complete and
  committed (commit `91e56a2`), but **behavioral validation is pending**.
  The rewrite has not been smoke-tested end-to-end in a fresh session.
  The structural claim (matrix is cleaner than variant list) is verified;
  the behavioral claim (matrix produces better routing in practice) is
  not yet measured.

## When this pattern applies

Use the multi-dimensional matrix pattern when a skill exhibits **accretion
without structure** — symptoms include:

1. The variant table has grown past ~7 rows across multiple sessions
2. New parameters are added as new columns without a principled reason
3. The same routing decision gets made in 3+ places (trigger phrases,
   variant table, screening logic)
4. The skill author has trouble explaining why a given phrasing routes
   where it does

Do NOT apply when the skill has a single decision axis (one dimension is
just a routing table, not a matrix), or when the variants are sequential
phases rather than parallel options (a phase sequence is a pipeline, not
a routing space).

## Generalization beyond /tp

The pattern transfers to any skill where intent selects a point in a
multi-axis decision space. Candidates on this host:

- **`/check`** (designed, not yet implemented): could organize around
  detector × scope × verdict-action rather than a flat detector list
- **`/review`**: lens (correctness/integrity/maintainability/security/
  architecture) × target (diff/branch/PR/path) × depth
- **`/design`**: design-doc-writer vs. design-doc-reviewer × domain ×
  consensus-loop depth

The /tp case is the first concrete instantiation; the pattern's value
should be validated on at least one more skill before treating it as a
universal.

## Anti-pattern: dimension proliferation

Resist adding a dimension for every parameter. The threshold question:
"does this parameter change the routing decision, or just tune a value
within a fixed route?" Horizon changes which domains fire (routing);
temperature tunes generation (not routing). A skill with 8 dimensions is
usually worse than one with 4 — the routing space grows multiplicatively,
the classifier has more to disambiguate, and the help output becomes
unreadable.

If a candidate dimension fails the "real decision axis" test (multiple
reachable values + changes routing), fold it into an existing dimension
as a sub-parameter, or drop it.

## Related

- [[mental-models-for-tp-and-brainstorming]] — the mental models /tp implements; this concept refines by adding the organizing principle
- [[intent-based-routing-for-ai-agent-skills-2026]] — the LLM-based semantic classification that picks the matrix point automatically
- [[ai-thought-partner-industry-expectations-and-now-next-later]] — the Now-Next-Later horizon continuum that became dimension 2 of the matrix
- [[skill-rewrite-preserve-tested-behavior-protocol]] — the rewrite protocol that produced the 4D-matrix /tp

## Sources

- Session 2026-07-25 /tp rewrite: commit `91e56a2` in dotgrok repo
- Handoff: `P:/docs/handoffs/tp-rewrite-20260725/HANDOFF.md`
- Prior skill state: `~/.grok/skills/tp/SKILL-old.md` (847 lines, preserved as fallback)
- New skill state: `~/.grok/skills/tp/SKILL.md` (463 lines, 4D-matrix-structured)
## Falsifier

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory Falsifier section. State what observation or evidence would make this
concept wrong or obsolete. If the concept is purely descriptive (not a claim),
state that explicitly: "This is a reference document, not a claim — no falsifier applies."
## What this means for our workspace

TODO (auto-generated by wiki_validator_sweep 2026-07-30): This concept predates the
mandatory workspace-implications section. State what should be updated, created, or
retired in our infrastructure based on this finding. If the concept is reference-only
with no actionable implication, state: "Reference document — no workspace action needed."
