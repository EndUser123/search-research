---
title: "Matrix model for session review: content type × time horizon"
created: 2026-07-27
source: session-2026-07-27 (/tp session protocol redesign)
tags: [skill-design, session-review, tp-session, matrix-model, two-dimensional, decision]
agent: grok
host: both
cognitive_load: 2
verification: observed
summary: >
  /tp session's protocol was restructured from a linear list of passes
  (NOW → NEXT → LATER → FILTER) to a two-dimensional matrix: content type
  (CONTINUE/STOP/FRICTION/OPPORTUNITY/SURPRISE/LEARNED/OBLIGATION) × time
  horizon (NOW/NEXT/LATER/NOTED). Each finding gets both tags and appears
  once, eliminating the false either/or that forced "keep using the
  isolation strategy" into either CONTINUE or LATER when it's both. The
  matrix was chosen over a two-layer model (observation layer → action
  layer) because it doesn't require a promotion step — findings are tagged
  at observation time. Connects to [[retrospective-questions-for-ai-agent-sessions]]
  and [[compound-skill-improvement-patterns]].
relations:
  - target: wiki/concepts/retrospective-questions-for-ai-agent-sessions.md
    type: extends
  - target: wiki/concepts/compound-skill-improvement-patterns.md
    type: related
  - target: wiki/concepts/ai-thought-partner-industry-expectations-and-now-next-later.md
    type: refines
  - target: wiki/concepts/visible-output-contracts-for-behavioral-skill-steps.md
    type: related
---

# Matrix model for session review: content type × time horizon

## Decision context

**Why this decision was needed:** the original `/tp session` protocol used linear passes: NOW → NEXT → LATER → FILTER. When CONTINUE, STOP, SURPRISES, and LEARNED passes were added (from [[retrospective-questions-for-ai-agent-sessions]] research), the linear list grew to 10 passes. The operator noticed the structural problem: "should 'keep using the isolation strategy' go in CONTINUE or LATER?" The answer was both — it's a content observation (what worked) AND a time-horizon decision (remember for future, no action now). The linear model forced a false either/or.

## The decision

**Chosen: two-dimensional matrix.** Each finding is tagged on two orthogonal dimensions:
- **Content type** (7 values): CONTINUE (what worked), STOP (what to retire), FRICTION (recurring failures), OPPORTUNITY (improvements possible), SURPRISE (unexpected events), LEARNED (durable knowledge), OBLIGATION (incomplete work)
- **Time horizon** (4 values): NOW (before session ends), NEXT (next session), LATER (architectural/strategic), NOTED (no action needed)

Findings appear ONCE with both tags. The output groups by time horizon; the content type is visible as a tag.

**How the content types were derived:** CONTINUE and STOP come from Start-Stop-Continue (the most widely used retrospective format). SURPRISE comes from Atlassian's "significant events" technique. LEARNED comes from 4Ls (Liked, Learned, Lacked, Longed For). FRICTION and OPPORTUNITY are workspace-specific (from the original NEXT and LATER passes). OBLIGATION replaces the old NOW pass. The 7 types are not invented — they're synthesized from established retrospective practice, adapted for solo AI agent sessions.

**How the decision was made:** the operator proposed a two-layer model (observation layer → action layer) first. I proposed the matrix as an alternative that doesn't require a promotion step.

The operator chose the matrix after seeing that it eliminates both the false-either/or (linear) and the promotion overhead (two-layer).

The matrix was implemented in commit `15eb083` on ~/.grok main. The decision took 3 turns of dialogue — the operator's instinct to find the right structure before implementing prevented rework.

This is the same design-dialogue pattern that produced the [[inline-conditional-over-dispatch-for-skill-design]] decision: the operator pushes for the right structure, the agent proposes alternatives, the operator chooses.

### Selection criterion

**Orthogonal completeness over linear simplicity.** The criterion is: can every finding be placed without compromise? In the linear model, ~30% of findings don't fit cleanly into any single pass. In the matrix, every finding has a natural content type and a natural time horizon.

### Steelman of the rejected alternatives

**Why the linear model was reasonable:** it's simpler to implement and simpler to read. NOW/NEXT/LATER is the dominant product-management framework (Intercom popularization). Adding more passes (CONTINUE, STOP, etc.) to the linear list is the natural extension. The operator can scan top-to-bottom.

**Why the two-layer model (observation → action) was reasonable:** it separates observations (what happened) from actions (what to do). Observations are open-ended notes; actions are time-bounded. The operator proposed this first, and it's cleaner conceptually.

**Why they lose to the matrix:** the linear model forces false either/or (demonstrated by the operator's question). The two-layer model requires a "promotion" step — an observation must be manually promoted to an action. The matrix eliminates both problems: findings are tagged once at observation time, no promotion needed.

**Concrete example of the false either/or:** during this session, the 3-layer isolation strategy (worktree + state_dir + scan window) worked perfectly for Phase 3 acceptance. In the linear model, this finding would go in CONTINUE ("what worked") OR LATER ("remember for future sessions"). In the matrix, it's CONTINUE + NOTED — observed, filed, no action needed because it already happened. The finding appears once with both tags. The NOTED table shows it so the operator knows it was seen.

**Concrete example of the promotion overhead:** in the two-layer model, "the obligation check requires a single receipt covering all paths" is an observation. To make it actionable, the operator would need to promote it to the action layer with a disposition. But it doesn't NEED an action — it's knowledge for the next session, not a task. The promotion step is wasted work. In the matrix, it's LEARNED + NOTED — no promotion needed.

## Key findings

- **The matrix eliminates duplication.** In the linear model, "stop using `python -c` with nested quotes" could appear in both STOP and NOW. In the matrix, it appears once: type=STOP, horizon=NOW. This reduces the finding count and makes the output scannable — the operator sees each issue exactly once.
- **NOTED as a first-class horizon** is the critical addition. Without it, observations that need no action (CONTINUE, LEARNED) silently disappear. The NOTED table makes them visible — the operator knows they were observed, even though no action is needed. This prevents the "did we miss anything?" anxiety that triggers unnecessary `/tp do?` re-runs.
- **The content types map to established retrospective frameworks.** CONTINUE/STOP come from Start-Stop-Continue (the most widely used retro format). SURPRISES/LEARNED come from 4Ls (Liked, Learned, Lacked, Longed For). FRICTION/OPPORTUNITY/OBLIGATION are workspace-specific additions. The matrix is the intersection of retrospective tradition with time-horizon planning — not a novel invention but a synthesis of two established frameworks. See [[retrospective-questions-for-ai-agent-sessions]] for the research backing.
- **The time horizons compose with the content types, not replace them.** A SURPRISE can be NOW (immediate investigation needed) or NOTED (observed, filed for future). A FRICTION can be NOW (fix immediately) or LATER (architectural fix needed). The composition produces 7×4=28 cells, but most findings land in ~8 common cells. The matrix is sparse in practice — not every combination appears.
- **The NOTED horizon is the operator's favorite.** The operator specifically called out that NOTED gives observations "a visible home" — they no longer silently disappear. The NOTED table says "we saw this, it's fine" — exactly what the ADHD brain needs to stop looping on "did we miss something?" This is the single highest-impact addition from the matrix restructuring.

## Implications

The matrix model changes how `/tp session` output is consumed. Instead of reading top-to-bottom through linear passes, the operator scans by time horizon (NOW first, then NEXT, then LATER, then NOTED). Within each horizon, the content-type tag tells them what kind of action is needed. This is faster for the operator — they can triage NOW items in 30 seconds, then decide whether to read NEXT/LATER. The linear model forced reading all passes to find the NOW items buried among NEXT/LATER content.

The model also enables the enhanced recommendation format: the `[TYPE]` tag in each recommendation comes directly from the content-type dimension. The operator sees `[FIX]` vs `[STOP]` vs `[CAPTURE]` and processes each differently — a FIX is a code change, a STOP is a behavioral commitment, a CAPTURE is a wiki write. This is the same pattern as [[visible-output-contracts-for-behavioral-skill-steps]]: visible metadata that changes how the operator processes the output.

The matrix also solves the "NOTED items have no home" problem that the `/tp review` of the refactor plan identified. In the linear model, observations like "the 3-layer isolation strategy worked well" (CONTINUE) and "the obligation check requires a single receipt covering all paths" (LEARNED) had nowhere to go — they weren't actions, so they didn't fit NOW/NEXT/LATER, but they weren't nothing either. The NOTED horizon gives them a visible home. The operator sees they were observed — no silent disappearance, no anxiety about "did we miss anything?"

## Trade-offs

**What works well:** the matrix is self-documenting. Each finding's tags explain both what it is and when to act. The operator doesn't need to read a legend — STOP+NOW is self-explanatory.

**What's harder:** the matrix requires the model to assign TWO tags per finding instead of one. This is more cognitive work during the review. In practice, the content type is usually obvious (the finding's shape tells you), and the time horizon is usually obvious (is this actionable now or not?). The extra tag is ~1 second of thought per finding.

**What doesn't change:** the recommendation list format. The matrix tags feed INTO the recommendation format (the [TYPE] tag), but the numbered list + `0 - Proceed` pattern is unchanged. The operator's interaction model doesn't change — they still scan the list and type `0` or pick a number.

## What this means for our workspace

Any skill that produces a review or assessment can adopt the matrix model. The pattern: tag findings on two orthogonal dimensions, group output by the dimension the operator scans first (time horizon), display the other dimension as a tag. This generalizes beyond `/tp session` to `/check` (which could tag findings as correctness/integrity/maintainability × severity), `/review` (which already has lens × severity), and `/debrief` (which could tag as root-cause/quality/friction/knowledge × NOW/NEXT/LATER).

The matrix also creates a natural audit trail. Because each finding has both a content type and a time horizon, the operator can reconstruct "what did we decide about X?" by filtering the matrix. In the linear model, that decision could be anywhere in the 10-pass list. In the matrix, it's at the intersection of its content type and time horizon — a single cell.

The NOTED horizon is the most impactful addition for the ADHD operator. It transforms the review from "what do I need to do?" (anxiety-inducing) to "here's everything, including what you don't need to do" (grounding). The NOTED table says "we saw this, it's fine, move on" — which is exactly what the ADHD brain needs to hear to stop looping on "did we miss something?"

The recommendation format also benefits: each item now carries a `[TYPE]` tag (FIX/STOP/CAPTURE/VERIFY/RESEARCH), an effort estimate (S/M/L), and a total estimated effort line. This gives the operator a one-glance cost signal before typing `0 - Proceed with All recommendations.` The matrix makes the recommendation format possible — without the content-type dimension, there's no tag to display. The two improvements were designed together in the same session.

## Falsifier

This decision is wrong if:
- **The matrix is too complex for the model to use correctly.** If findings end up miscategorized (wrong content type or wrong horizon), the matrix adds overhead without accuracy. Test: after 5 sessions, check whether the matrix tags are consistent.
- **The linear model was actually sufficient.** If the operator never encounters the false-either/or problem in practice, the matrix is over-engineering. Refuted by this session: the operator asked "should this go in CONTINUE or LATER?" — the exact question the matrix eliminates.
- **The 7 content types are too many.** If the model over-splits findings (creating multiple types for what's really one finding), the matrix fragments instead of organizing. Mitigation: the types are derived from established frameworks, not invented — they map to patterns the retrospective literature already validated.
- **NOTED becomes a dumping ground.** If the model puts everything in NOTED to avoid committing to an action, the horizon loses its signal. Mitigation: NOTED is for CONTINUE and LEARNED only — findings that genuinely need no action. FRICTION and OBLIGATION findings can never be NOTED.

## Receipts

- **"Operator asked 'should this go in CONTINUE or LATER?'":** receipt — session 019fa23d, operator turn asking about the matrix model design.
- **"Linear model had 10 passes":** receipt — `/tp` SKILL.md before the matrix restructuring (session 019fa23d commit `15eb083`).
- **"NOTED table makes observations visible":** receipt — the NOTED table was added in the same commit and prevents CONTINUE/LEARNED items from disappearing.
