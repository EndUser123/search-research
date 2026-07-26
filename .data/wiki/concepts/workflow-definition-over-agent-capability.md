---
title: "Workflow definition over agent capability"
created: 2026-07-25
source: session-2026-07-25 (Factory repo + software factory video analysis)
sources:
  - https://github.com/owainlewis/factory (owainlewis/factory — design.md "Configuration owns mechanism; prompts own policy")
  - Software factory video transcript (owainlewis) — "the agents you're using don't matter as much as everyone thinks... the workflow is what matters"
  - P:/.data/wiki/concepts/agentic-sdlc-skill-lifecycle-architecture.md (our skill lifecycle mapping)
  - P:/.data/wiki/concepts/model-pool-selection-policy-speed-quota-diversity.md (complementary axis)
tags: [workflow, agent-capability, harness-engineering, skill-architecture, principle, factory]
summary: >
  The workflow definition (steps, gates, transitions, acceptance criteria) matters more than which agent executes it. Identical agents following different workflows produce different quality; heterogeneous agents following the same workflow produce consistent quality. This is why our skill catalog (workflow definitions) is the primary leverage point, with model selection as a secondary optimization. Source: Factory repo design principle "Configuration owns mechanism; prompts own policy" + video articulation "the workflow is what matters."
agent: grok
host: both
cognitive_load: 2
verification: multi-source-verified
relations:
  - target: wiki/concepts/agentic-sdlc-skill-lifecycle-architecture
    type: refines
  - target: wiki/concepts/model-pool-selection-policy-speed-quota-diversity
    type: complementary
  - target: wiki/concepts/spec-driven-development-harness-engineering-ecosystem
    type: related
  - target: wiki/concepts/prompting-patterns-for-ai-agent-control
    type: related
---

# Workflow definition over agent capability

## The principle

**The workflow definition matters more than which agent executes it.** This is
not "agents don't matter" — it is "workflow is the primary axis; agent
capability is secondary." A well-defined workflow makes a mediocre agent
productive; a poorly-defined workflow makes a capable agent unreliable.

## Evidence

**Factory (owainlewis/factory)** encodes this as an architectural principle:
"Configuration owns mechanism; prompts own policy." The daemon owns polling,
dedup, concurrency, timeouts, sandbox, recovery. The workflow is a plain
Markdown prompt. Four concepts (Source / Trigger / Workflow / Worker) cleanly
separate *when to act* (mechanism) from *what to do* (policy). The same
daemon runs triage, implementation, bug-finding, and backlog classification —
they differ only in the prompt behind the trigger.

**Video articulation (owainlewis):** "the agents you're using don't matter
as much as everyone thinks... Ultimately the workflow is what matters. All
of the agents are equally capable at this point."

**Our own evidence (implicit):** `/go` produces consistent results across
model lanes (ccr-ornith, minimax-m3, grok parent) because the profile +
horsepower pack + phase announcements define the workflow. The model executes
it; the workflow determines quality. Our `agentic-sdlc-skill-lifecycle-
architecture` concept maps skills to SDLC phases — that mapping IS the
workflow definition, even though it is not yet encoded in the skills
themselves.

## Why this matters for our fleet

We operate a heterogeneous fleet (Grok, Claude, Codex, Agy, Mmx, local
models). Two failure modes this principle prevents:

1. **Agent chasing** — believing quality problems are solved by switching
   models, when the workflow is the actual bottleneck. Symptom: "let's try a
   different model" repeated without workflow changes.
2. **Workflow invisibility** — believing our skills are just "prompts" when
   they are actually workflow definitions with entry conditions, phase
   announcements, transition gates, and verification steps. Undervaluing
   them leads to under-investing in their structure.

The corollary: **our skill catalog is the leverage point.** Each SKILL.md
that defines entry screening, phase transitions, exit verification, and
next-step recommendations is a workflow definition. The agent executing it is
interchangeable within quality-floor constraints.

## How it composes with model selection

This principle is **complementary** to
`[[model-pool-selection-policy-speed-quota-diversity]]`, not contradictory:

| Axis | What it determines | Primary leverage |
|------|-------------------|------------------|
| **Workflow definition** | Consistency, completeness, verifiability | Skill catalog quality |
| **Model selection** | Speed, cost, capability ceiling | Fleet routing |

Workflow definition is the primary axis because it determines whether the
work is done correctly *at all*. Model selection is secondary because it
determines *how efficiently* the correct work is done. A wrong workflow
cannot be rescued by a better model; a right workflow can survive a weaker
model.

## Implications for skill authoring

1. **Skills should declare their SDLC stage** (spec / plan / execute / verify
   / review / ship) so the workflow is explicit, not implicit.
2. **Skills should emit transition recommendations** (advance / go back /
   detour) so the workflow is continuous across skills, not just within one.
3. **Entry screening should verify the work is in the right state for this
   skill** (Factory's "revalidate live source state immediately before
   execution").
4. **Exit criteria should be explicit** so the next skill knows whether to
   accept the handoff.

These are the patterns Factory encodes in every workflow prompt. Our `/go`
already does some of this (phase announcements at lines 351-358, next-step
table at lines 700-712 of its SKILL.md); individual skills do not. Closing
that gap is the transferable insight.

## Source distinction

This principle has two distinct sources that agree:

- **Architectural source (Factory):** the codebase separates mechanism from
  policy and lets the workflow (Markdown prompt) own all judgment. This is
  an implementation-level argument.
- **Experiential source (video):** a practitioner observation that switching
  between Claude Code, Codex, and his own Neo agent across the same workflow
  produced comparable results. This is an empirical argument.

Our fleet adds a third source: cross-model consistency under `/go` is
observable but not yet measured directly. Measuring it (workflow change vs
model change as quality delta) would tighten this concept from
multi-source-verified to measured.

## Relation to existing concepts

- `[[agentic-sdlc-skill-lifecycle-architecture]]` — maps our skills to SDLC
  phases; this concept explains *why* that mapping is the leverage point
- `[[model-pool-selection-policy-speed-quota-diversity]]` — the complementary
  axis (model selection)
- `[[spec-driven-development-harness-engineering-ecosystem]]` — the broader
  harness-engineering frame
- `[[prompting-patterns-for-ai-agent-control]]` — structural patterns that
  make workflows enforceable
- `[[mandatory-step-enforcement-code-over-prose]]` — why workflow steps need
  structural enforcement, not just prose

## Falsifier

This principle is wrong if:

- A materially better model (e.g., frontier-class vs haiku-class) produces
  better results from a *worse* workflow than a weaker model produces from a
  *better* workflow, on multi-step engineering tasks. (Plausible for trivial
  tasks; unlikely for multi-step engineering.)
- Our own fleet data shows workflow changes producing no quality delta while
  model changes produce large deltas. (We have not measured this directly; it
  is inferable from `/go` cross-model consistency but not yet quantified.)
- The industry converges on fully autonomous agents that need no workflow
  scaffolding. (Not observed as of 2026-07; all major frameworks — Factory,
  addyosmani/agent-skills, Anthropic agentic SDLC — still encode workflows.)
