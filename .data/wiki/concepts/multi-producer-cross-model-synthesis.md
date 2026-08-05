---
title: "Multi-producer cross-model synthesis — N independent analyses + verification-gated integration"
created: 2026-07-25
source: session-2026-07-25-why-skill-multi-model
tags: [multi-model, cross-model, synthesis, methodology, skill-design, verification-gate, grok-codex-agy-glm-mimo]
summary: >
  A reusable methodology for deep-analysis tasks: spawn N independent
  model-producers (Grok + glm + codex + agy + mimo, or any cross-family set),
  each producing a complete proposal from the same shared inputs, then a
  single synthesizer integrates with per-finding verification (verification,
  novelty, integration checks). Distinct from /tp's two-lens critique (1
  producer + 1 synthesizer) and from /risks's adversarial panel — this is
  PRODUCER diversity for the deliverable itself, not critique-of-deliverable.
  Worked example: /why skill enhancement produced 4 independent optimization
  proposals; synthesizer resolved 2 live disagreements (dispatch vs inline,
  staging vs sync-review) using evidence-grounded criteria.
agent: grok
host: both
cognitive_load: 3
verification: observed
sources:
  - P:/docs/handoffs/why-skill-enhancement-20260725/HANDOFF.md (operator-approved design + post-handoff optimizations)
  - C:/Users/brsth/Downloads/why-from-codex.txt (Codex design prompt)
  - session-019f9a89 (5-model run: Grok + glm-5-2 + codex + agy + mimo, 2026-07-25)
relations:
  - target: wiki/concepts/model-fleet-provider-pools.md
    type: depends-on — needs a cross-family pool of producer-capable models
  - target: wiki/concepts/model-tool-calling-capability-matrix.md
    type: depends-on — slugs must be spawn-capable for the assignment
  - target: wiki/concepts/inline-conditional-over-dispatch-for-skill-design.md
    type: produced — design decision from this methodology applied to /why
  - target: wiki/concepts/synchronous-review-direct-write-pattern.md
    type: produced — design decision from this methodology applied to /why
  - target: wiki/concepts/tp-parallel-improvement-solution-space.md
    type: complements — /tp is 1-producer+1-synthesis; this is N-producers+1-synthesis
---

# Multi-producer cross-model synthesis

## Decision context

**The problem behind this methodology:** the operator asked for `/why` optimization proposals with the option of radical refactoring. Two prior external-LLM analyses (in handoff `why-skill-enhancement-20260725`) had already found deeper causes than the original `/why` produced. The question: how do you get genuine lens diversity on a PRODUCTION task (not a critique task) without the producer pool collapsing to "the loudest model" or "the first model"?

The standard `/tp` pattern spawns ONE fresh subagent for a different-lens critique. That works for "is X right?" but not for "produce the best X." Producer diversity needs multiple independent drafts, not multiple critiques of one draft.

## The pattern

```
1. Build a shared assignment packet (objective, constraints, required
   reads with absolute paths, output format, "do not edit files").
2. Spawn N producers in parallel. Each producer is a different model
   family (different training corpus). Pass the assignment packet to
   each — they do NOT see each other's outputs.
3. One synthesizer (parent or designated model) reads all N outputs.
4. For each material finding or recommendation, the synthesizer runs
   per-finding checks:
     - VERIFICATION: does this cite a claim I can confirm/refute?
     - NOVELTY: was this already considered and rejected?
     - INTEGRATION: does this change the recommendation, or is it
       real-but-immaterial?
5. Synthesizer surfaces consensus, live disagreements (with the
   selection criterion and chosen side), and the final recommendation.
```

## What makes it work

### 1. Producers must be cross-family, not same-family

`glm-5-2` (Zhipu) + `codex` (OpenAI GPT-5) + `agy` (Google Gemini) + `mimo` (MiniMax) + Grok (xAI) is meaningfully more diverse than five OpenAI models. Different training corpora = different blind spots. The /why synthesis produced exactly one cross-family split (dispatch vs inline) — same-family producers would likely have agreed.

### 2. The shared assignment packet is the contract

Each producer gets the **same** objective, the **same** required file reads, the **same** output format. This isolates "model lens" as the only variable. Without this, producers diverge on what they're optimizing for, and the synthesis becomes apples-to-oranges.

### 3. The synthesizer runs the /tp Step 3 gate (adapted)

The verification + novelty + integration checks from `/tp` Step 3 are the right filter for producer outputs too. Without them, the synthesizer rubber-stamps the consensus; with them, individual findings are evaluated against session evidence.

### 4. Live disagreements are surfaced, not papered over

When producers split (e.g., glm+agy for dispatch, codex+mimo for inline), the synthesizer states the split explicitly, names the **selection criterion** (cost, reversibility, evidence-fit), and chooses. The operator can override after seeing the disagreement. This is the structural opposite of "consensus at all costs."

## Worked example — /why v3 synthesis (2026-07-25)

**Producers:** Grok (parent) + glm-5-2 + codex + agy + mimo. Assignment packet at `P:/tmp/why-skill-multi-model-assignment.md`.

**Consensus (all 4 external producers agreed):**
- Keep 5-dim Ishikawa, Five Whys, FACT/INFERENCE/UNKNOWN, competing explanations, falsifiers, observe-before-cause, no-auto-implement
- Add: evidence-tier weakest-link rule; evidence inventory; six-layer first-divergence; five-way classification; feedback-loop detection; agent-control lens (conditional); MAST coverage; surprise/absent-evidence
- Reject: 10 mandatory dimensions; 3-7 hypotheses with scoring; mandatory durable state per run; decision-archaeology; Claude CKS/CHS/Serena

**Live disagreement 1 — dispatch vs inline conditional:**
- glm-5-2 + agy: failure-class dispatch (`--bug`/`--agent`/`--pattern`/`--system`)
- codex + mimo: inline conditional expansion (lens fires on failure content)
- **Selection criterion:** evidence-fit + reversibility
- **Synthesizer chose:** inline. Dispatch presupposes reliable Step-0 classification; misclassification is itself a closure-pressure failure mode. Inline triggers fire on evidence.

**Live disagreement 2 — auto-write to wiki:**
- agy: full implementation including auto-write
- glm-5-2: ship tiers first, defer write loop
- codex + mimo: read-only lookup only; reject auto-write (violates investigation/recommendation boundary)
- **Operator correction:** synchronous cross-model review → direct write to `concepts/` (not staging, not operator-as-gatekeeper). See [[synchronous-review-direct-write-pattern]].

## When to use this methodology

**Good fit:**
- Production tasks where lens diversity matters (skill design, architecture proposals, multi-option recommendations)
- Tasks where the deliverable outlives the session (skill changes, design docs, durable recommendations)
- Tasks with enough context to fill an assignment packet (~500-1000 tokens)

**Poor fit:**
- Single-fact lookups (one producer suffices)
- Time-critical path (the run takes 3-5 minutes wall-clock with parallel producers)
- Tasks where one model family has a known correctness edge (just use that model)
- Tasks depending entirely on session state producers can't see (use /tp inline carve-out instead)

## Cost notes (observed 2026-07-25)

| Model | Wall-clock | Notes |
|-------|-----------|-------|
| `glm-5-2` (spawn_subagent) | 196s | Reasoning lane, subscription-rationed |
| `codex` (CLI, gpt-5.6-luna) | 157s | Read-only review invocation pattern |
| `agy` (CLI, Gemini) | 41s | Fastest of the externals |
| `go-mimo-v2-5` (spawn_subagent) | 253s | Code lane |
| `nvidia-nemotron-3-ultra` | FAILED | Known serde failure — see [[model-tool-calling-capability-matrix]]; fallback to mimo |

Total wall-clock with parallel launch: ~5 minutes. Total synthesizer effort: one parent turn to read 4 outputs + run per-finding gates.

## Falsifier

This methodology is wrong if, within 6 months:
- **Producer outputs are consistently near-identical** — the cross-family diversity is illusory; one producer suffices.
- **The synthesizer consistently rubber-stamps the consensus** — the per-finding verification gate is theater; tighten or automate.
- **Live disagreements are consistently resolved in favor of the cheapest-to-implement option** — the selection criterion has decayed to "minimal effort" against the operator's stated "optimal long-term" preference.
- **The producer pool is consistently truncated by serde/quota failures** — the methodology depends on at least 3 working cross-family producers; if availability drops below that, the diversity argument collapses.

## What this means for our workspace

- **Use for skill-design tasks** (any non-trivial SKILL.md enhancement). The /why run was the first application; future skill refactors (especially `/tp`, `/check`, `/review`) are candidates.
- **Use for architecture decisions** with multiple viable options — replaces the `≥2 viable options` requirement in AGENTS.md with actually-diverse options.
- **Do NOT use for** implementation tasks (one writer per worktree), critiques of in-session state (`/tp`'s inline carve-out), or fast Q&A.
- **Build the assignment packet carefully** — it is the contract that makes the methodology valid. Sloppy packets produce apples-to-oranges outputs.

## Methodology roots

- `/tp` two-lens architecture (Costa & Kallick 1993; /tp SKILL.md) — extended from 2 lenses to N producers
- `/risks` adversarial panel — different goal (adversarial find vs. independent produce) but same fan-out shape
- AGENTS.md `Recommendation Rule` — `≥2 viable options` requirement extended to `≥N cross-family producers` for high-stakes production tasks
- Anthropic multi-agent research system (multi-agent research lead + subagents) — same shape, different goal (research vs. production)

See also: [[inline-conditional-over-dispatch-for-skill-design]] and [[synchronous-review-direct-write-pattern]] — both are design decisions produced by applying this methodology to /why v3.
