<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# This file has both skills for code quality and architecture quality.  skill-ship is supposed to optimize the target skills or orchestrators, but it doesn't.  How can we apply what you surfaced previously in our chat to optimize our skills, orchtestrators, and outcomes.

Yes: the file strongly suggests `/skill-ship` is good at **process coordination**, but weak at **outcome optimization**. It enforces phases, freshness, and dynamic discovery, yet nothing in the surfaced bundle says it selects the *best* review strategy, adapts validation depth to risk, or closes the loop using measured outcomes.[^1]

## Main gap

`/skill-ship` appears to orchestrate creation through fixed phases—Context, Discovery, Knowledge Retrieval, Creation, Validation, Eval, Optimization, Distribution—but its validation is still mostly workflow-centric (`3a` spec, `3b` quality, `3c` integration) rather than solution-centric or architecture-risk-centric.[^1]
By contrast, `/rca` already has the stronger pattern you want: explicit adversarial dispatch, evidence tiers, and confidence calibration, while `/arch` has template routing and `/sqa` has gated layered analysis.[^1]

That means the best move is not “make `/skill-ship` smarter in general,” but: **turn it into a strategy router and evaluator-of-evaluators** that chooses among `/sqa`, `/arch`, `/rca`, and SDLC primitives based on risk, scope, and desired outcome.[^1]

## What to change

### 1. Add a solution-quality gate

Right now `/skill-ship` validates implementation/spec/integration, but it needs a separate **solution-quality** pass before and after creation.[^1]

Add a new gate between 1.5 and 2, and again before 4:

- **1.6 Solution framing gate**
    - What problem is this skill/orchestrator actually solving?
    - What failure modes matter most?
    - What would make this embarrassing or costly in 6 months?
    - Which qualities matter most: adaptability, composability, low context cost, low false-positive rate, explainability, recovery, portability?
- **3.4 Architecture/Outcome gate**
    - Did the produced skill improve the target outcome, not just pass structure checks?
    - Did it increase coupling, context bloat, rigidity, or hidden assumptions?
    - Can it degrade safely when upstream tools, builtins, or repo shape change?

This is the missing distinction we discussed earlier: implementation quality vs solution quality.[^2][^1]

### 2. Replace fixed validation with risk-based validation

The bundle says `/skill-ship` runs parallel `3a` and `3b`, then `3c`, but that is static orchestration.[^1]
Instead, make validation **conditional** on artifact risk:


| Situation | Validation to invoke |
| :-- | :-- |
| Prompt-only skill, low blast radius | `3a + 3b` light |
| New orchestrator / dispatcher | `3a + 3b + 3c + adversarial architecture review` |
| Dynamic config / agent discovery / hooks | add stale-data, fallback, and drift checks |
| Anything changing routing logic | run `/arch` + `/rca` adversarial lenses |
| Anything touching contracts / primitives | run `/sqa` full + SDLC contract checks |

That gives you adaptable validation instead of the same checklist for every artifact.[^1]

### 3. Make `/skill-ship` choose strategies, not just phases

Your own bundle shows good ingredients already exist:

- `/arch` has template-based routing.[^1]
- `/rca` has adversarial specialists and confidence tiers.[^1]
- `/sqa` has layered halting gates.[^1]

So `/skill-ship` should decide things like:

- Should this target get **fast**, **deep**, or **adversarial** review?
- Should it optimize for **correctness**, **architecture durability**, **token efficiency**, or **operational resilience**?
- Should it call `/arch` first, or `/sqa`, or both?
- Is this a **skill problem**, an **orchestrator problem**, a **contract problem**, or an **evidence problem**?

In other words, `/skill-ship` needs a **policy engine**, not just a phase engine.[^1]

## Best-practice architecture

A better model for `/skill-ship` is a small adversarial review board:

- **Planner agent**
    - Classifies request type: skill creation, skill refactor, orchestrator repair, validation hardening.
- **Solution architect agent**
    - Designs the intended improvement path and selects which existing skills to compose.
- **Adversarial evaluator**
    - Tries to break the proposal: rigidity, hard-coded assumptions, context blowup, hidden coupling, stale configs, false confidence.
- **Judge agent**
    - Scores proposal on outcome rubric and chooses pass / conditional pass / fail.

This pattern mirrors what makes `/rca` stronger than ordinary review: separate generation from judgment and require evidence-backed findings.[^3][^4][^1]

## Outcome rubric

Add an explicit scoring rubric to `/skill-ship` so optimization means something measurable.

Score every produced skill/orchestrator on 1–5:

- **Problem fit**: Solves the real user/system need.
- **Adaptability**: Avoids hard-coded assumptions, static lists, fragile thresholds.
- **Composability**: Reuses `/sqa`, `/arch`, `/rca`, `sdlc` instead of cloning logic.
- **Context efficiency**: Minimal token footprint for same or better outcome.
- **Observability**: Emits enough state/evidence to debug failures.
- **Failure tolerance**: Graceful fallback when inputs, builtins, or paths change.
- **6-month maintainability**: Future-you can understand and modify it safely.

Then define hard gates such as:

- Any score <3 on adaptability or failure tolerance = fail.
- Mean score <4 for orchestrators = revise.
- Any critical adversarial finding = block distribution.

That turns “optimize” from a vague instruction into a governed decision.

## Concrete improvements to `/skill-ship`

Based on the bundle, these are the highest-leverage changes:

- **Add a routing matrix** in `SKILL.md` or references:
    - request type × risk × artifact type → required validators and depth.[^1]
- **Promote `/arch` and `/rca` to first-class validators** for orchestrators, not optional adjuncts.[^1]
- **Require an assumptions register** for every generated skill:
    - dynamic vs fixed inputs,
    - config sources,
    - expected repo topology,
    - fallback behavior if tools/configs are missing.
- **Add anti-rigidity checks**:
    - hard-coded thresholds,
    - static lists,
    - path assumptions,
    - tool-name coupling,
    - fixed ordering where policy should decide.
- **Persist evaluation outcomes**
    - which generated skills were later revised,
    - common failure classes,
    - recurring architecture drifts.
This lets `/skill-ship` optimize from history instead of recreating mistakes.


## Better prompt for `/skill-ship`

Use a governing prompt like this when improving skills or orchestrators:

```text
Optimize this skill/orchestrator for outcomes, not just implementation completion.

Evaluate at two levels:

1. Solution quality
- Is this solving the right problem?
- What assumptions does it make about repo shape, tools, agents, config, workflow, and user intent?
- What will break if those assumptions change?
- Is there a simpler or more composable design using existing skills/primitives?

2. Implementation quality
- Any hard-coded values, brittle thresholds, static lists, fixed paths, or non-adaptive routing?
- Any duplicated logic that should be delegated to /sqa, /arch, /rca, or sdlc?
- Any context bloat, hidden coupling, or weak observability?

Then run adversarial review:
- Try to prove the design is too rigid, too clever, too expensive, too coupled, or too fragile.
- Score it on problem fit, adaptability, composability, context efficiency, observability, failure tolerance, and 6-month maintainability.

Output only:
- recommended architecture changes
- required validator/routing changes
- assumptions to externalize
- pass/conditional pass/fail with reasons
```

That is much closer to the “smart solution validation” pattern you were after earlier.

## Recommended operating model

Best-practice shape for your ecosystem:

- `/skill-ship` = meta-orchestrator and policy router.
- `/sqa` = implementation-quality certifier.
- `/arch` = solution/architecture-quality evaluator.
- `/rca` = adversarial falsifier and evidence calibrator.
- `/sdlc` = contracts and primitives.

If `/skill-ship` tries to “optimize” by itself, it will stay shallow. If it routes to the right evaluator set, scores outcomes, and learns from failures, it becomes the architecture VerificationGate for your whole skill system.[^1]

Most important change: stop treating optimization as Phase 4 polish. Treat optimization as **strategy selection + adversarial validation + measurable outcome scoring** from the start.[^1]

Would you like me to turn this into a concrete redesign spec for `/skill-ship` with:

1. new phases,
2. routing matrix,
3. evaluator roles,
4. pass/fail rubric,
5. suggested file/module changes?

<div align="center">⁂</div>

[^1]: review_bundle_skills_2026-04-05.md

[^2]: https://www.unosquare.com/blog/the-crucial-difference-between-verification-and-validation-in-testing/

[^3]: https://www.infoq.com/articles/evaluating-ai-agents-lessons-learned/

[^4]: https://www.braintrust.dev/articles/ai-agent-evaluation-framework

