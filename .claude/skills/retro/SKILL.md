---
name: retro
description: "Identify what went wrong, what went right, and what to do differently next time. Chains 6 skills: recap → gap analysis → friction → pre-mortem → actions."
version: 1.2.0
category: orchestration
triggers:
  - "retro"
  - "/retro"
  - "run self-contrast"
  - "retrospective protocol"
  - "self-contrast"
contract_type: workflow
aliases:
  - /retro
  - /self-contrast
suggest:
  - /friction
depends_on_skills: [recap, gto, friction, pre-mortem, rns]
workflow_steps:
  - step_1: Call /recap — get session summary with problem/optimal contrast
  - step_2: Call /gto gap — extract top gaps from session evidence
  - step_3: Call /friction — identify workflow friction and automation opportunities
  - step_4: Call /pre-mortem — adversarial validation of approach
  - step_5: Evaluate SCORES — rate completeness/optimality/satisfaction 0-10; invoke red-team if any axis < 8
  - step_6: Call /rns — extract prioritized actions from all findings
  - step_7: Aggregate ALL findings from all chained skills into the RNS; group by domain
enforcement: strict
workflow_binding: exclusive
workflow_enforcement: hard
phase_recovery_mode: resumable
user_override: explicit
layer1_enforcement: true
required_phase_artifacts:
  - /recap
  - /gto
  - /friction
  - /pre-mortem
  - /rns
usage_markers:
  - "RECAP:"
  - "GAPS:"
  - "FRICTION:"
  - "SCORES:"
  - "ACTIONS:"
---

# RETRO — SELF-CONTRAST Orchestrator

## Purpose

Run the full SELF-CONTRAST protocol in sequence: retrospective → gap analysis → friction detection → adversarial validation → prioritized actions. Produces a structured output with named score axes.

## When to Use

- End of session: "run /retro"
- After major implementation: "let's retrospective this"
- Before planning next phase: "what gaps do we have?"

## FLOW

```
1. /recap          → Session retrospective (what happened, problem vs optimal)
2. /gto            → Gap analysis (code/process gaps from session)
3. /friction       → Friction analysis (what blocked progress, what could be automated)
4. /pre-mortem     → Adversarial validation (what WILL fail)
5. /rns            → Action extraction (recover/prevent/realize)
```

### Red-Team Trigger

If any SCORES axis is below 8, invoke `/rns` with adversarial framing before finalizing actions:
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

FRICTION: [top 3 friction points]
  1. [friction description — category: automation/manual/repeated]
  2. [friction description — category]
  3. [friction description — category]

SCORES:
  c:[0-10]  Completeness — were all gaps found?
  o:[0-10]  Optimality  — was the approach best possible?
  s:[0-10]  Satisfaction — smooth process?

ACTIONS: [prioritized RNS list — see RNS Aggregation Rule below]
  [recover/high] ACT-001 ...
  [prevent/med]  ACT-002 ...
  [realize/low]  ACT-003 ...
```

### RNS Aggregation Rule (Critical)

**The RNS must include ALL findings from ALL chained skills, not just /pre-mortem.**

When building the ACTIONS list, aggregate findings from:
- `/recap` — work already done, completed, or committed (do not include as actionable unless something was left incomplete)
- `/gto gap` — internal technical debt in the target itself (own by GTO if the target is GTO, otherwise own by the retro's target)
- `/friction` — workflow friction and automation opportunities (include all automation-potential items)
- `/pre-mortem` — adversarial findings by domain
- `/rns` — extracted actions from above

Group by domain (security, correctness, quality, testing, performance, internal). Within each domain sort CRITICAL > HIGH > MEDIUM > LOW.

**Every finding from every skill must appear in the RNS with an owner and action.** If a finding is dropped, state why explicitly in the retro output.

**Failure mode this prevents:** RNS was previously built only from /pre-mortem findings, dropping GTO internal gaps (CAUSE-001/002/003, 7 TODOs in GTO test files) and workflow friction that no upstream skill flagged. The retro felt complete but was systematically incomplete.

## Step Execution

1. **Call `/recap`** — get session summary with problem/optimal contrast
2. **Call `/gto gap`** — extract top gaps from session evidence
3. **Call `/friction`** — identify workflow friction and automation opportunities
4. **Call `/pre-mortem`** — adversarial validation of approach
5. **Evaluate SCORES** — rate each axis 0-10:
   - If any axis < 8: re-run `/rns` with adversarial framing before proceeding
6. **Call `/rns`** — extract prioritized recover/prevent/realize actions
7. **Aggregate** — merge ALL findings from all chained skills into the final RNS

## Red-Team Protocol

When SCORES reveals weakness:
1. Re-examine the weak axis with adversarial framing
2. Incorporate findings into GAPS or FRICTION as appropriate
3. Re-score with new data
4. Proceed to ACTIONS only after gaps are addressed or deferred

## Retrospective-Integrity Prompts

Before finalizing the retrospective, `/retro` should run a short internal retrospective-integrity check:

- What did we treat as a process win even though the outcome was suboptimal?
- What gap or friction point is duplicated across `/recap`, `/gto`, `/friction`, `/pre-mortem`, and `/rns` rather than being synthesized once?
- What score is being inflated or deflated without strong evidence from the chained skills?
- What action list would mis-sequence work by treating symptoms as the primary problem?
- What recommendation becomes misleading if the adversarial review surfaced a deeper failure mode?
- What positive takeaway is actually a workaround that should not be repeated?
- What workflow friction did we treat as normal even though it could be automated or eliminated?
- What would a weaker model smooth over instead of preserving as a real tradeoff or unresolved tension?
- What step in the chain returned weak or partial evidence, and did I compensate for that explicitly?
- What ownership boundary is still unclear between architecture, planning, verification, and implementation?
- What would make this retro feel complete while still teaching the wrong lesson?

These are internal self-check prompts. They are not default user-facing questions and should only surface to the user when `/retro` is genuinely blocked and cannot proceed safely without clarification.

## Trace, Emerge, Graduate, and Friction

`/retro` should use four internal helper passes:

- `trace`: reconstruct how the session or project path evolved, including the moments that most changed the outcome
- `emerge`: identify latent patterns across recap, gap analysis, friction, pre-mortem, and action extraction that no single sub-skill named explicitly
- `graduate`: promote repeated retrospective findings into durable process changes, validators, hooks, or workflow rules when warranted
- `friction`: actively scan chained results for repeated manual steps, missing automations, and workflow gaps that no upstream skill flagged

Use `trace` when the retrospective depends on a sequence of decisions or turning points.
Use `emerge` when multiple chained skills are pointing at the same hidden theme.
Use `graduate` when the same class of retro lesson keeps recurring and should become durable enforcement or policy.
Use `friction` when the session reveals manual patterns that could be automated or eliminated.

Reference: `P:/.claude/skills/__lib/sdlc_internal_modes.md`

## Constraints

- Do NOT fabricate scores — derive from evidence in each step
- Do NOT skip steps — each feeds the next
- If a step returns no findings, note "none found" and proceed
- Red-team is advisory if scores are 6-7, mandatory if < 6
