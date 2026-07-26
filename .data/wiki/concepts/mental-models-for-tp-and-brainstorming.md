---
title: "Mental Models for /tp and /brainstorming: Critical Friend, Double Diamond, and Pre-Mortem"
created: 2026-07-20
source: session-2026-07-20 (/www research on mental models for tp and brainstorming)
tags: [mental-models, tp, brainstorming, critical-friend, double-diamond, pre-mortem, divergent-convergent, devil-advocate, confirmation-bias]
agent: grok
host: both
cognitive_load: 4
verification: multi-source-verified
summary: >
  Six mental models underpin /tp and /brainstorming. /tp already implements
  three (critical friend, steelman/devil's advocate, double-loop learning via
  framing challenge). Three are missing or underutilized: the Double Diamond
  (diverge-converge cycles for ideation), pre-mortem (prospective hindsight),
  and second-order thinking ("and then what?"). The most impactful additions:
  (1) make /brainstorming use the Double Diamond explicitly, (2) add pre-mortem
  as a mandatory step before any hard-to-reverse implementation, (3) add
  second-order thinking questions to /tp's core domain 2.
relations:
  - target: wiki/concepts/mental-models-for-handoff-and-aar
    type: related
---

## Summary

Our `/tp` and `/brainstorming` skills are built on several established mental models — some explicit in the skill design, some implicit. This analysis maps each model, rates its implementation, and identifies what would improve outcomes.

## Six mental models and where they appear

### 1. Critical Friend (explicit — core of /tp)

**What it is:** A trusted colleague who asks challenging questions and provides candid feedback, combining support with critique. The relationship is advocacy, not adversity.

**Where we use it:**
- `/tp` SKILL.md: the entire skill is framed as "critical friend dialogue"
- `/design` Step 5.5: the critical friend step challenges premises, not implementation
- `/red-team`: the adversarial variant — same posture, more aggressive

**Quality:** Strong. The `/tp` skill cites Costa & Kallick (1993), the originators of the concept. The two-lens architecture (fresh subagent + same-agent synthesis) structurally implements the "you cannot refocus your own glasses" insight.

**Source:** Costa, A. L., & Kallick, B. (1993). "Through the Lens of a Critical Friend." ASCD Educational Leadership.

### 2. Steelman / Devil's Advocate (explicit — /tp + /red-team)

**What it is:** Deliberately arguing the strongest version of the opposing position (steelman) or against the current consensus (devil's advocate). Counteracts confirmation bias.

**Where we use it:**
- `/tp` core domain 4 (anchoring): "What premise did the writer bring in that wasn't examined?"
- `/red-team`: entire skill is adversarial multi-agent review
- `/design` Step 5.5: the critical friend checks for "unexamined anchor"

**Quality:** Moderate. `/tp` challenges the anchor but doesn't systematically construct the steelman. The user has to prompt for it explicitly. `/red-team` does this better — it dispatches specialists who independently verify claims.

**Research validation:** Chiang et al. (IUI 2024, 195 citations): LLM-powered devil's advocate reduces confirmation bias in group decision-making. The key finding: the devil's advocate must argue from a genuinely different position, not from a superficially oppositional stance. Our `/tp` sometimes falls into the latter — it agrees too quickly when the user pushes back.

**Source:** Chiang et al. (2024); Kahneman & Tversky (confirmation bias research).

### 3. Double-Loop Learning (explicit in /tp, missing in /brainstorming)

**What it is:** Single-loop asks "how to do better." Double-loop asks "why do we think this is right?" — challenges governing assumptions, not just actions.

**Where we use it:**
- `/tp` core domain 1 (problem framing): "State the problem the design is actually solving. Does that match what the user asked for?"
- `/tp` core domain 4 (anchoring): "What's the assumed-but-not-verified belief the whole design rests on?"
- `/design` Step 5.5: critical friend challenges premises

**Quality:** Strong in `/tp`. Missing in `/brainstorming` — the brainstorming skill doesn't challenge the problem framing before generating solutions. It assumes the user's stated problem is correct and generates solutions for it.

**Source:** Chris Argyris (1976); Esther Derby (double-loop in retrospectives).

### 4. Double Diamond (MISSING — would transform /brainstorming)

**What it is:** A design thinking framework with two diverge-converge cycles:
1. **Discover** (diverge): explore the problem space broadly — multiple framings, user research, analogies
2. **Define** (converge): synthesize into a clear problem statement
3. **Develop** (diverge): generate many solution ideas without judgment
4. **Deliver** (converge): select and refine the best solution

**Where we DON'T use it (but should):**
- `/brainstorming` currently generates solutions without first diverging on the problem framing. It jumps to Diamond 2 (solution ideation) without completing Diamond 1 (problem exploration).
- This is the exact failure that caused this session's problems: I proposed solutions (MCP server, packet runner) without diverging on the problem framing first (what does "invoke Codex from Grok" actually mean? What are the constraints? What existing patterns solve similar problems?)

**What it would look like:**
```
/brainstorming <topic>
  Phase 1 (Discover): Generate 5+ different framings of the problem.
                     "What if the real problem is X? Or Y? Or Z?"
                     Use analogies from other domains.
  Phase 2 (Define): User selects or synthesizes the framing.
  Phase 3 (Develop): Generate 10+ solution ideas for the selected framing.
                     No judgment. Wild ideas encouraged.
  Phase 4 (Deliver): Evaluate top 3-5 ideas against criteria.
                     Select. Refine.
```

**Source:** Design Council UK (Double Diamond, 2005); multiple design thinking curricula. The IxDF (Interaction Design Foundation) has the most comprehensive treatment.

### 5. Pre-Mortem / Prospective Hindsight (MISSING — would catch failures before they happen)

**What it is:** "Imagine this project has failed catastrophically. Why did it fail?" By assuming failure and working backward, teams surface risks they would otherwise miss due to optimism bias.

**Where we DON'T use it systematically:**
- `/tp` touches this in core domain 3 (falsifiability): "What would make this design wrong?" But it's a single question, not a systematic exercise.
- `/wargame` implements this for hard-to-reverse decisions (the move schema with failure signals and countermoves). But `/wargame` is only invoked for trigger 5/6 in `/plan`.
- `/red-team pre-mortem` mode exists but is rarely invoked.

**What it would look like in `/tp`:** Add a "pre-mortem" block to core domain 3:

```
## Pre-Mortem (mandatory when the decision is hard to reverse)
Imagine it's 3 months from now. The recommendation was implemented and
it failed catastrophically. List 3 plausible failure scenarios:
1. [Most likely failure mode]
2. [Edge case not considered]
3. [Assumption that turned out to be false]
For each: what evidence could you have gathered beforehand to prevent it?
```

**Source:** Gary Klein (pre-mortem, 2007); Mitchell et al. (brainwriting premortem, 2018, 61 citations).

### 6. Second-Order Thinking (MISSING — would catch downstream consequences)

**What it is:** "And then what happens?" — considering not just the immediate consequence of an action, but the second-order, third-order effects. Charlie Munger's hallmark.

**Where we DON'T use it:**
- `/tp` evaluates the recommendation on its own merits but doesn't systematically trace downstream effects.
- `/design` includes "risks and mitigations" but doesn't ask "if we implement this, what new problems does it create?"

**What it would look like in `/tp` core domain 2:**

```
## Second-Order Analysis
For the recommended approach:
1. What is the immediate consequence? (first-order)
2. What happens after that? (second-order)
3. And then? (third-order)
4. At which order does the consequence become negative?
```

This would have caught the exec-gate friction problem: first-order effect (blocks mutations until discovery) → second-order effect (blocks all bash reads because run_terminal_command is gated) → third-order effect (user disables the plugin entirely).

**Source:** Charlie Munger; Ray Dalio (second-order thinking in Principles); Shane Parrish (Farnam Street mental models).

## What /tp does well

| Pattern | Source | Our implementation |
|---|---|---|
| Two-lens architecture | Costa & Kallick (critical friend) | Fresh subagent + same-agent synthesis |
| Disciplined openness | /tp SKILL.md §disciplined-openness | Test alternatives before converging |
| Outcome labeling | /tp SKILL.md §outcome-labels | 7-label precedence taxonomy |
| Proportional confirmation | /tp SKILL.md §proportional-confirmation | Match confirmation to reversibility |
| Assignment adequacy | /tp SKILL.md §assignment-adequacy | 5-dimension evaluation before action |

## What /brainstorming does well

| Pattern | Source | Our implementation |
|---|---|---|
| User intent exploration | Superpowers brainstorming skill | Explores intent before generating ideas |
| Progressive disclosure | Anthropic skill pattern | Loads context as needed |
| Constraint surfacing | Design thinking | Identifies constraints before ideation |

## What's missing and worth adding

| Gap | Skill | Impact | Effort |
|---|---|---|---|
| **Double Diamond framing** | `/brainstorming` | High — prevents solutioning before problem-framing is complete | Medium — add Discover/Define phases before Develop/Deliver |
| **Pre-mortem block** | `/tp` (core domain 3) | High — catches failure modes before commitment | Low — 5 questions, triggered by reversibility |
| **Second-order thinking** | `/tp` (core domain 2) | Medium — catches downstream consequences | Low — 4 questions per recommendation |
| **Systematic steelman** | `/tp` (core domain 4) | Medium — currently asks "what's the anchor?" but doesn't construct the steelman | Low — add "construct the strongest argument FOR the rejected alternative" |
| **Confirmation bias loop** | `/brainstorming` | Medium — AI-generated ideas cluster around obvious solutions; need deliberate divergence techniques | Medium — add "worst idea first" and "analogy from another domain" techniques |

## The connection to handoff and AAR

These mental models are not isolated to `/tp` and `/brainstorming`. They feed into the handoff and AAR cycle:

1. **Double-loop learning** (from the AAR wiki concept) is what `/tp` does during the session; the AAR should do it after the session
2. **Pre-mortem** findings from `/tp` should be captured in the handoff so the next session knows the identified failure modes
3. **Second-order effects** discovered during `/tp` should be promoted to wiki concepts (they're durable lessons)
4. **The Double Diamond** ensures that brainstorming produces solutions grounded in problem understanding — which makes the handoff's "objective" field more accurate

## Related

- [[wiki/concepts/mental-models-for-handoff-and-aar]] — companion analysis; this extends to /tp and /brainstorming
- [[wiki/concepts/mandatory-step-enforcement-code-over-prose]] — the prose-vs-code distinction is itself a double-loop + pre-mortem finding

## Sources

- Costa & Kallick (1993), "Through the Lens of a Critical Friend" — ASCD
- Chiang et al. (2024), "Enhancing AI-Assisted Group Decision Making through LLM-Powered Devil's Advocate" — IUI, 195 citations
- Design Council UK (2005), Double Diamond — via IxDF
- Gary Klein (2007), "Performing a Project Premortem" — Harvard Business Review
- Charlie Munger / Shane Parrish (Farnam Street), second-order thinking
- Chris Argyris (1976), double-loop learning
- Rosenbaum et al. (2025), "Scaffolding Creativity: How Divergent and Convergent LLM Personas..." — arxiv
- Liu (2025), "Creative as IDEO experts: LLM-agent-based design thinking workshop" — ICCC
