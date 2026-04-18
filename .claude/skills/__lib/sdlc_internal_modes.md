# Shared SDLC Internal Modes

Canonical definitions for four internal reasoning modes used across SDLC-oriented skills.

These are **internal helper modes**, not user-facing slash commands and not default user interview prompts.

## 1. `trace`

Use `trace` when the current decision depends on how evidence, requirements, blockers, or design choices evolved over time.

Purpose:
- reconstruct the sequence of relevant decisions or observations
- identify what changed the current recommendation
- prevent solving an outdated version of the problem

Good use cases:
- architecture decisions inherited from prior ADRs or blockers
- plans rewritten after nested `/design` remediation
- RCA where "what changed?" matters
- implementation work constrained by earlier corrections or contracts

Questions to ask internally:
- What earlier decision or observation most changed the current answer?
- Which prior artifact is still authoritative, and which is stale?
- What sequence of events explains why the current state exists?

## 2. `challenge`

Use `challenge` when the current recommendation, diagnosis, or artifact needs adversarial pressure before it is trusted.

Purpose:
- test the strongest counter-argument
- surface contradictory evidence, simpler alternatives, or hidden failure modes
- reduce overconfidence in the first coherent answer

Good use cases:
- architecture and planning decisions
- transfer/reuse analysis
- RCA and diagnosis
- readiness/shipping decisions for nontrivial skills

Questions to ask internally:
- What is the strongest objection to my current answer?
- What evidence would falsify this recommendation?
- What simpler alternative or overlapping mechanism did I underweight?

## 3. `emerge`

Use `emerge` when multiple findings or lessons may imply a latent pattern that has not yet been named explicitly.

Purpose:
- identify repeated but unnamed themes
- cluster findings into more durable pattern language
- convert scattered signals into a clearer failure class or opportunity

Good use cases:
- audit transcript mining
- retrospectives and reflection
- lesson capture
- repeated implementation or workflow failures

Questions to ask internally:
- What pattern is visible across these findings that I have not named yet?
- Which repeated signals likely share a deeper cause?
- What hidden theme would best explain these separate incidents?

## 4. `graduate`

Use `graduate` when a repeated manual insight should be promoted into a durable artifact or enforcement layer.

Purpose:
- convert repeated lessons into validators, hooks, tests, or workflow rules
- move from folklore to reusable contract
- reduce recurrence of already-understood failures

Good use cases:
- shipping repeated fixes
- planning verifier improvements
- audit improvement signals
- learn/reflect promotion into durable artifacts

Questions to ask internally:
- What repeated issue should now become a validator, hook, test, or rule?
- What should stop living only in prose?
- Which lesson has enough recurrence to deserve promotion?

## Usage Guidance

- Do not add all four modes to every skill just for symmetry.
- Prefer role fit over completeness:
  - `trace` for history/evolution-sensitive reasoning
  - `challenge` for adversarial pressure
  - `emerge` for latent-pattern discovery
  - `graduate` for promotion into durable enforcement
- Keep them internal unless the user explicitly asks for this kind of meta-analysis.
