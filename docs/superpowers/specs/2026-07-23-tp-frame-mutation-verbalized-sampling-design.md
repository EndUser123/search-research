---
title: "/tp improvement: adversarial-environment domain + verbalized sampling as observable block"
created: 2026-07-23
updated: 2026-07-23
source: session-2026-07-23 (brainstorming → red-team review → revised spec)
tags: [tp, design-spec, frame-diversity, verbalized-sampling, adversarial-environment, independently-revertible]
host: both
agent: grok
revision: 2 (post-red-team: replaced 4-lens system + coupled synthesis with 3 independent layers)
---

# /tp improvement: adversarial-environment domain + VS as observable block

## Problem

/tp's two-lens architecture produces a single critique from a single lens (verbatim bundle). The diversity research (wiki concept `tp-parallel-improvement-solution-space.md`) showed that frame diversity is the cheapest diversity win. This spec captures how to add frame diversity to /tp.

## Red-team revision history

**Revision 1 (original):** 4-lens selection system + VS pipeline + 5-check synthesis (one atomic spec). Red-team BLOCK (SIMPL-1): the lens system duplicated the subagent's existing conditional domains (steelman mandatory at SKILL.md:537, pre-mortem conditional at SKILL.md:529, concurrency/multi-terminal at SKILL.md:469). Making them mutually exclusive REDUCED per-invocation rigor. VS was coupled into the synthesis, preventing independent reversion.

**Revision 2 (this spec):** 3 independently-revertible layers. No lens system (the existing conditional domains already cover steelman/pre-mortem/concurrency). The only genuinely-new frame (adversarial-environment) added as a conditional domain. VS preserved as an observable separate block — always shown, even when empty, to collect baseline data.

## Design — three independent layers

### Layer 1: Adversarial-environment conditional domain (~3 lines)

**Location:** SKILL.md line 469, appended to the context-derived domain list.

**The addition:**

> - **Adversarial-environment (mandatory when the target involves hooks, plugins, concurrent agents, flaky networks, or quota exhaustion):** Assume deployment in the most hostile environment — concurrent agents editing shared files, flaky network, quota exhaustion, stale data, race conditions. What breaks first?

**Why this is the only genuinely-new frame:** the existing conditional domains cover steelman (mandatory), pre-mortem (conditional on reversibility), and concurrency/multi-terminal (checklist item). The adversarial-environment frame is different — it's a **deployment-assumption mutation**, not a checklist item. It asks "what if the environment itself is hostile?" which the current concurrency domain doesn't do (it asks "consider concurrency," not "assume everything is broken").

**Cost:** ~3 lines, no new parameters, no auto-detection, no orchestrator-side selection.

**Reverts independently:** delete the 3 lines.

### Layer 2: VS as a separate output block (additive to subagent prompt)

**Location:** SKILL.md subagent prompt template, appended AFTER the existing output format (after the Information Asymmetry section).

**The addition to the subagent prompt:**

```
### VS Candidates (separate from your primary critique)

After completing your primary critique above, generate 3-5 alternative
critique angles that approach the target from different perspectives.
For each, assign a confidence level (high/medium/low) and state whether
it agrees or disagrees with your primary critique's findings.

Format:
1. [confidence] [agree/disagree with primary] Alternative angle: <one sentence>
2. [confidence] [agree/disagree with primary] Alternative angle: <one sentence>
3. [confidence] [agree/disagree with primary] Alternative angle: <one sentence>
...
```

**What this does NOT do:**
- Does NOT replace the primary critique (the primary critique is unchanged)
- Does NOT require the synthesis to process the candidates as mandatory checks
- Does NOT add a "5-check synthesis" or agreement/blind-spot gating
- Does NOT change the existing 3-check synthesis (verification, novelty, integration)

**What it DOES do:**
- The subagent produces 3-5 alternative perspectives as a separate section
- The orchestrator can observe whether the alternatives add value
- The orchestrator can compare agreement/disagreement patterns
- Data is collected for every run (always shown, even when empty)

**Cost:** ~20 extra prompt words, ~30% longer subagent output. Same 1 spawn.

**Reverts independently:** remove the VS instruction block from the subagent prompt.

### Layer 3: VS comparison observation (additive to synthesis)

**Location:** SKILL.md Step 3 synthesis, appended as an OPTIONAL informational section after the existing synthesis.

**The addition to the synthesis output:**

```markdown
### VS comparison (informational — always shown, does not gate the verdict)

- Convergence: <N>/<total> alternatives agree with the primary critique's main findings
- Divergence: <list any alternatives that disagree with the primary, or "none">
- Unique catches: <list any findings from alternatives the primary missed, or "none">
- Assessment: <one sentence — did VS add value this run? yes/no/marginal>
```

**What this does NOT do:**
- Does NOT upgrade/downgrade the primary critique's confidence based on VS
- Does NOT gate the verdict (PROCEED/REVISE/BLOCK) based on VS candidates
- Does NOT replace the existing 3-check synthesis

**What it DOES do:**
- Always shown (even when all alternatives converge — that's baseline data)
- Provides per-run observability of VS value
- After 10+ runs, the pattern data answers: "does VS add value?" empirically

**Cost:** ~5 lines of inline reasoning. 0 extra spawns.

**Reverts independently:** remove the VS comparison section from the synthesis.

## Layer interaction diagram

```
/tp invocation
  │
  ├─ Step 0.5: Preflight (unchanged)
  ├─ Step 1: Context extraction (unchanged)
  ├─ Step 2: Spawn subagent
  │    ├─ [existing] Primary critique (all existing domains, including NEW adversarial-environment)
  │    └─ [Layer 2] VS candidates block (3-5 alternative angles, separate section)
  │
  └─ Step 3: Synthesis
       ├─ [existing] 3-check synthesis (verification, novelty, integration) — UNCHANGED
       └─ [Layer 3] VS comparison observation (informational, always shown)
```

**Independence:** Layer 1, 2, and 3 can each be reverted independently:
- Remove Layer 1 → subagent stops doing adversarial-environment analysis. VS and comparison continue.
- Remove Layer 2 → subagent stops producing VS candidates. Layer 3 comparison section shows "N/A — VS not active." Layer 1 continues.
- Remove Layer 3 → synthesis stops showing VS comparison. VS candidates still produced (Layer 2) but not observed. Layer 1 continues.

## Falsifier

This design is wrong if:

- **Layer 1:** adversarial-environment analysis adds no value on hook/plugin/concurrency questions across 10 invocations. Revert: delete the 3 lines.
- **Layer 2:** the VS candidates block is consistently empty or the alternatives are trivially different from the primary across 10 invocations. Revert: remove the VS instruction.
- **Layer 3:** the VS comparison shows "no unique catches" across 10+ runs (VS adds no value). Revert: remove both Layer 2 and Layer 3 (Layer 1 stays).

## Implementation surface

All changes are to `~/.grok/skills/tp/SKILL.md`:

| Layer | Edit location | Lines changed |
|---|---|---|
| 1 | Line 469: append to context-derived domain list | +3 |
| 2 | After line 575 (after Information Asymmetry section): append VS block | +10 |
| 3 | After line 645 (after existing 3-check synthesis): append VS comparison | +8 |

Total: ~21 lines added to SKILL.md. No code changes. No new skills. No new hooks.

## Out of scope (future work)

- Cross-family parallel multi-model (Priority 3 in the solution space)
- Parallel racing (Priority 4)
- Pool composition changes (handed off to `tp-pool-composition-review-20260723`)
- Promoting VS from observational to gating (decide after 10+ runs of data)
