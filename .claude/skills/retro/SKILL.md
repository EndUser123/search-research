---
name: retro
description: Identify what went wrong, what went right, and what to do differently next time. Chains 5 skills: recap → gap analysis → opportunities → adversarial review → actions.
version: 1.0.0
triggers:
  - "retro"
  - "/retro"
  - "run self-contrast"
  - "retrospective protocol"
  - "self-contrast"
suggest:
  - /recap
  - /gto
  - /ideas
  - /pre-mortem
  - /rns
  - /critique
depends_on_skills: [recap, gto, ideas, pre-mortem, rns]
enforcement: advisory
---

# RETRO — SELF-CONTRAST Orchestrator

## Purpose

Run the full SELF-CONTRAST protocol in sequence: retrospective → gap/opportunity analysis → adversarial validation → prioritized actions. Produces a structured output with named score axes.

## When to Use

- End of session: "run /retro"
- After major implementation: "let's retrospective this"
- Before planning next phase: "what gaps do we have?"

## FLOW

```
1. /recap          → Session retrospective (what happened, problem vs optimal)
2. /gto            → Gap analysis (code/process gaps from session)
3. /ideas          → Opportunity analysis (positive flips, ROI ranking)
4. /pre-mortem     → Adversarial validation (what WILL fail)
5. /rns             → Action extraction (recover/prevent/realize)
```

### Red-Team Trigger

If any SCORES axis is below 8, invoke `/critique` for adversarial red-team before finalizing actions:
- completeness_score < 8 → red-team gaps in coverage
- optimality_score < 8 → red-team approach quality
- satisfaction_score < 8 → red-team process/experience

## OUTPUT Format

```
RECAP: [2-paragraph session summary — problem vs optimal]

GAPS: [top 3 gaps identified]
  1. [gap description]
  2. [gap description]
  3. [gap description]

IDEAS: [top 3 opportunities]
  1. [opportunity — ROI: high/med/low]
  2. [opportunity — ROI: high/med/low]
  3. [opportunity — ROI: high/med/low]

SCORES:
  c:[0-10]  Completeness — were all gaps found?
  o:[0-10]  Optimality  — was the approach best possible?
  s:[0-10]  Satisfaction — smooth process?

ACTIONS: [prioritized RNS list]
  [recover/high] ACT-001 ...
  [prevent/med]  ACT-002 ...
  [realize/low]  ACT-003 ...
```

## Step Execution

1. **Call `/recap`** — get session summary with problem/optimal contrast
2. **Call `/gto gap`** — extract top gaps from session evidence
3. **Call `/ideas`** — extract top opportunities (or invert top-problems output)
4. **Call `/pre-mortem`** — adversarial validation of approach
5. **Evaluate SCORES** — rate each axis 0-10:
   - If any axis < 8: invoke `/critique` red-team before proceeding
6. **Call `/rns`** — extract prioritized recover/prevent/realize actions

## Red-Team Protocol

When SCORES reveals weakness:
1. Invoke `/critique` targeting the weak axis
2. Incorporate critique findings into GAPS
3. Re-score with critique data
4. Proceed to ACTIONS only after gaps are addressed or deferred

## Retrospective-Integrity Prompts

Before finalizing the retrospective, `/retro` should run a short internal retrospective-integrity check:

- What did we treat as a process win even though the outcome was suboptimal?
- What gap or opportunity is duplicated across `/recap`, `/gto`, `/ideas`, `/pre-mortem`, and `/rns` rather than being synthesized once?
- What score is being inflated or deflated without strong evidence from the chained skills?
- What action list would mis-sequence work by treating symptoms as the primary problem?
- What recommendation becomes misleading if the adversarial review surfaced a deeper failure mode?
- What positive takeaway is actually a workaround that should not be repeated?
- What would a weaker model smooth over instead of preserving as a real tradeoff or unresolved tension?
- What step in the chain returned weak or partial evidence, and did I compensate for that explicitly?
- What ownership boundary is still unclear between architecture, planning, verification, and implementation?
- What would make this retro feel complete while still teaching the wrong lesson?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/retro` is genuinely blocked and cannot proceed safely without clarification.

## Trace, Emerge, And Graduate

`/retro` should use three internal helper passes:

- `trace`: reconstruct how the session or project path evolved, including the moments that most changed the outcome
- `emerge`: identify latent patterns across recap, gap analysis, pre-mortem, and action extraction that no single sub-skill named explicitly
- `graduate`: promote repeated retrospective findings into durable process changes, validators, hooks, or workflow rules when warranted

Use `trace` when the retrospective depends on a sequence of decisions or turning points.
Use `emerge` when multiple chained skills are pointing at the same hidden theme.
Use `graduate` when the same class of retro lesson keeps recurring and should become durable enforcement or policy.

Reference: `P:/.claude/skills/__lib/sdlc_internal_modes.md`

## Constraints

- Do NOT fabricate scores — derive from evidence in each step
- Do NOT skip steps — each feeds the next
- If a step returns no findings, note "none found" and proceed
- Red-team is advisory if scores are 6-7, mandatory if < 6
