---
title: "ADHD parallel-frame divergent ideation: integration with existing skills"
created: 2026-07-25
source: session-20260725 (/crawl4ai ingest of UditAkhourii/adhd + /wiki analysis)
tags: [divergent-ideation, cognitive-frames, brainstorming, multi-agent, skill-design, reasoning-architecture, premature-convergence]
summary: >
  ADHD (by Udit Akhouri) treats premature convergence in autoregressive reasoning as an
  architectural problem: it spawns N isolated reasoning processes under deliberately distorted
  cognitive frames (zero shared context during divergence), then a critic pass scores, clusters,
  prunes traps, and deepens survivors. This is the architectural version of what /tp and /design
  Step 5.5 implement procedurally (1 fresh subagent, no shared framing anchor). The most
  transferable techniques are: N-frame divergence (not just 1-2 fresh lenses), deliberate frame
  distortion (not just "fresh perspective"), and the cluster/prune/deepen critic pattern with
  explicit trap detection. Recommendation: don't add ADHD wholesale to existing skills; add an
  optional --adhd mode to /tp as the entry point, evaluate ROI, then expand.
agent: grok
host: grok
cognitive_load: 3
verification: single-source-verified
sources:
  - https://github.com/UditAkhourii/adhd (Udit Akhouri, 2026) — preprint "ADHD: Parallel Divergent Ideation for Coding Agents"
  - https://adhdstack.github.io/ (Udit Akhouri, 2026) — preprint paper
relations:
  - target: wiki/concepts/brainstorming-ideation-with-llms.md
    type: refines
  - target: wiki/sources/github.com/000-UditAkhourii-adhd.md
    type: related
  - target: wiki/concepts/advanced-prompting-patterns-for-ai-agents.md
    type: complements
  - target: wiki/concepts/raising-coding-best-practices-in-ai-agents.md
    type: related
---

# ADHD parallel-frame divergent ideation: integration with existing skills

## Decision context

**Why this analysis was needed:** the operator ingested the [ADHD repo](https://github.com/UditAkhourii/adhd)
via `/crawl4ai` and asked whether its techniques should be integrated into `/design`, `/tp`,
the `brainstorming` skill, or other skills. This is a real design question, not academic: the
workspace already has multiple divergent-thinking mechanisms (fresh-lens subagents in `/tp`,
critical-friend review in `/design` Step 5.5, multi-agent adversarial review in `/red-team`).
Adding ADHD's mechanism without understanding the overlap risks parallel paths — the exact
anti-pattern the "Search before proposing" rule exists to prevent.

The gap in knowledge: does ADHD's specific architecture (N isolated processes + deliberately
distorted frames + cluster/prune/deepen critic) add value beyond what the workspace already
does with 1-2 fresh subagents? If yes, where does it add the most value, and what's the
minimal integration that captures that value?

## What ADHD does differently

ADHD ("Architectural fix for premature convergence in autoregressive reasoning") by Udit Akhouri
makes a specific architectural claim: linear Chain-of-Thought anchors on whatever it says first,
and Tree-of-Thought widens the search but still walks a single shared context (so anchoring
persists across branches). The fix is structural, not prompt-based:

| Mechanism | What it does | How it differs from our existing patterns |
|-----------|-------------|-------------------------------------------|
| **N isolated processes** | Spawns N parallel reasoning processes, each with its own context | We typically spawn 1 fresh subagent (`/tp`) or 1 writer + 1 reviewer + 1 critical friend (`/design`). N is configurable in ADHD. |
| **Deliberately distorted frames** | Each process gets a deliberately adversarial/distorted cognitive frame ("argue the opposite", "assume the user's framing is wrong", "approach from [domain X]") | Our fresh subagents get a different *posture* (critical friend) but not deliberately *distorted* frames. The distortion is the key innovation. |
| **Zero shared context during divergence** | The N processes do not see each other's output during the divergence phase | Our fresh subagents get the task + context but not each other's output. Similar, but ADHD makes the isolation the architectural centerpiece, not a side effect. |
| **Critic pass: cluster/prune/deepen** | After divergence, a separate critic scores all outputs, clusters similar ones, prunes "traps" (plausible-sounding but wrong answers), and deepens survivors | Our review is issue-by-issue (`/design` reviewer) or critique-by-domain (`/tp`). The cluster/prune/deepen pattern with explicit trap detection is absent. |
| **Trap detection** | Explicitly looks for outputs that look right but are subtly wrong — the "plausible narrative substituting for evidence" pattern | This maps directly to our `[[narrative-as-signal]]` and `[[reactive-pattern-matching-and-closure-pressure]]` concepts — but ADHD operationalizes trap detection as a critic-phase step, not a behavioral rule. |

## What the workspace already has (observe before proposing)

Before proposing integration, the existing patterns — this is the "observe" step:

- **`/tp` (default mode):** spawns 1 fresh subagent for critique, then the same agent verifies and integrates. Different lens, no shared framing anchor. This is ADHD with N=1 and frame="critical friend."
- **`/design` Step 5.5 (critical friend):** spawns 1 fresh subagent to challenge premises across core + context-derived domains. Different posture, no shared reviewer framing. Again, ADHD with N=1.
- **`/red-team`:** multi-agent adversarial review with specialists (failure-modes, security, logic, testing, etc.). This is closer to ADHD's N-frame model — each specialist IS a distorted frame. But `/red-team` tests a *proposal*; ADHD generates *options*.
- **`brainstorming` skill (superpowers):** explores user intent, requirements, and design before implementation. Decomposition-focused, not divergence-focused.
- **`/go` grok-parallel:** fans out independent implementation tasks across subagents. Parallel execution, not parallel ideation.

The key gap: **no existing skill does N-frame divergent *generation* with deliberately distorted frames.** `/tp` and `/design` do 1-frame critique. `/red-team` does N-frame adversarial *testing* of one artifact. ADHD does N-frame *generation* of multiple artifacts, then convergence.

## Where ADHD techniques fit (ranked by ROI)

### 1. `/tp` — best fit (add `--adhd` mode)

`/tp` is the natural entry point. It already does fresh-subagent critique. An `--adhd` mode
would spawn N subagents (default 3-5) instead of 1, each with a deliberately distorted frame:
"argue the opposite", "approach from [adjacent domain]", "assume the user's first instinct is
wrong", "steelman the rejected alternative." Then the existing verification + integration
step clusters and converges.

**Why /tp and not /design:** `/tp` is lightweight (1 subagent, ~30-60s). Scaling to N adds
proportional cost but stays in the "quick thought-partner" tier. `/design` is already 10-30
minutes; adding N=5 critical friends would push it to 30-60 minutes for marginal gain —
the writer→reviewer loop already provides the convergence pressure ADHD's critic pass would.

**Trap detection transfer:** the most valuable single technique from ADHD is the explicit
trap-detection step in the critic pass. This could be added to `/tp`'s verification phase
without the full N-frame machinery: after generating the critique, explicitly ask "which of
these findings is a plausible narrative substituting for evidence?" — the exact pattern our
`[[narrative-as-signal]]` rule addresses behaviorally.

### 2. `brainstorming` skill — natural complement

The superpowers `brainstorming` skill decomposes the problem (MECE, morphological analysis).
ADHD diverges on solutions. They're sequential, not competing: brainstorm to decompose →
ADHD to generate diverse options → converge. A `/brainstorm --adhd` flag or a composed
workflow (`/brainstorm` → `/tp --adhd`) would capture both phases.

### 3. `/red-team` — enhance specialist diversity

`/red-team` already spawns specialists (failure-modes, security, logic, etc.). ADHD's
contribution here is the deliberate *distortion* of frames — not just "review from the
security lens" but "review assuming the proposal's security assumptions are deliberately
wrong." This is a sharpening of existing specialist prompts, not a structural change.

### 4. `/design` — only for high-stakes designs

`/design` Step 5.5 (critical friend) could optionally spawn N frames for designs tagged
high-stakes (irreversible, multi-month consequences). But for routine designs, the cost
(10-30 min → 30-60 min) is not justified. Make it opt-in via `--adhd-critic` flag, default off.

## What is most transferable (the techniques worth extracting)

Not all of ADHD needs to be integrated as a unit. Three techniques are independently valuable:

1. **Deliberate frame distortion** — instead of "give me a fresh perspective," specify the distortion: "argue the opposite", "assume the framing is wrong", "approach from [domain]." This is a prompt-engineering technique that can be injected into any existing fresh-subagent call without architectural change.

2. **Cluster/prune/deepen critic pattern** — after generating N options, don't just pick the best. Cluster by similarity, prune the clusters that are traps (plausible but wrong), deepen the survivors. This is the convergence discipline that raw brainstorming lacks. Could be added to `/tp`'s integration step and `/design`'s reviewer step.

3. **Explicit trap detection** — operationalize our `[[narrative-as-signal]]` rule as a critic-phase question: "which of these outputs is a plausible narrative substituting for evidence?" This is the single highest-signal technique, and it maps to a pattern we've already documented behaviorally but not operationalized structurally.

## What this means for our workspace

**Recommended path (minimal viable integration, then evaluate):**

1. Add `--adhd` mode to `/tp`: spawns N=3 subagents with deliberately distorted frames, then clusters/prunes/deepens via the existing verification step. This is the lowest-cost, highest-signal integration point.
2. Extract trap detection as a standalone critic question in `/tp`'s verification phase — fires regardless of `--adhd` mode. This captures ADHD's highest-value technique without the N-frame cost.
3. Evaluate after 5-10 real uses of `/tp --adhd`. If the N-frame divergence produces options the single-frame critique missed, expand to `brainstorming` and high-stakes `/design`. If not, the trap-detection extraction alone was worth the analysis.

**What NOT to do:**
- Don't add ADHD wholesale to `/design` (cost too high for routine designs)
- Don't create a standalone `/adhd` skill yet (overlaps with `/tp` — would create parallel paths)
- Don't replace `/red-team`'s specialists with ADHD frames (different purpose: testing vs generating)

## Receipts

Claims about local skill mechanisms, labeled by inspection status:

- **`/design` Step 5.5 critical friend spawns 1 fresh subagent** — [OBSERVED] `~/.grok/skills/design/SKILL.md` Step 5.5 (lines ~720-830), specifically: "Do NOT pass `resume_from` — launch fresh so no reviewer framing contaminates the critique." Directly inspected and edited this session (commit `b39d97b`).
- **`/tp` default mode spawns 1 fresh subagent for critique** — [INFERENCE] from the skill catalog description ("Two-lens critique: a fresh subagent generates the critique... then the same agent verifies"). Not directly inspected this session; the `/tp` SKILL.md path is `~/.grok/skills/tp/SKILL.md`.
- **`/red-team` spawns specialist subagents (failure-modes, security, logic, testing)** — [INFERENCE] from the skill catalog description ("Planner → specialists → critic → root-cause clustering"). Not directly inspected this session; the `/red-team` SKILL.md path is `~/.grok/skills/red-team/SKILL.md`.
- **`brainstorming` skill decomposes via MECE/morphological analysis** — [INFERENCE] from `[[brainstorming-ideation-with-llms]]` wiki concept (read via qmd search this session), which documents the operator's natural brainstorming process mapping to those frameworks. The `brainstorming` SKILL.md itself (`~/.grok/installed-plugins/superpowers-21e2a56d/skills/brainstorming/SKILL.md`) was not directly inspected.
- **ADHD mechanism (N isolated processes, distorted frames, cluster/prune/deepen critic)** — [OBSERVED] from the ingested README at `wiki/sources/github.com/000-UditAkhourii-adhd.md` (read this session).

## Falsifier

This recommendation is wrong if, after implementing `/tp --adhd` and using it on 5+ real
"help me think" questions:
- The N-frame divergence never produces an option that the single-frame `/tp` critique missed
(N=1 was sufficient all along — the fan-out was overhead)
- The deliberately distorted frames produce worse critiques than neutral fresh-subagent
critique (the distortion adds noise, not signal)
- The cluster/prune/deepen step converges on the same answer as "pick the best" every time
(the convergence discipline was unnecessary)

If any of these hold after 5+ uses, revert to single-frame `/tp` and keep only the trap-detection
extraction.

## Sources

- [UditAkhourii/adhd](https://github.com/UditAkhourii/adhd) (Udit Akhouri, 2026) — README ingested at `wiki/sources/github.com/000-UditAkhourii-adhd.md`. Source for: N isolated processes, distorted cognitive frames, zero shared context, cluster/prune/deepen critic, trap detection.
- [ADHD preprint](https://adhdstack.github.io/) (Udit Akhouri, 2026) — "ADHD: Parallel Divergent Ideation for Coding Agents." Source for: the architectural argument against linear CoT and Tree-of-Thought.
- [[brainstorming-ideation-with-llms]] — existing workspace concept on divergent ideation (MECE, morphological analysis, inversion, first principles). This concept refines it with ADHD's parallel-frame technique.
- [[advanced-prompting-patterns-for-ai-agents]] — existing concept covering "start fresh chats for critical decisions" and "independent view before sharing." This concept complements it with the N-frame distortion mechanism.
