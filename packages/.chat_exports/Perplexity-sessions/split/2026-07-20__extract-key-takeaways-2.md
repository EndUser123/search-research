---
title: "Extract key takeaways"
date: "2026-07-20"
mode: "COPILOT"
uuid: "52e32902-ba64-4466-974c-bdaea00a7678"
entry_count: 2
---

## Human

Extract key takeaways

## Assistant

Karpathy-style loops turn Claude from a one-shot task executor into an autonomous experimenter that iteratively optimizes toward a measurable goal using /loop and /goal, with you defining the objective and evaluation cartridges.[1]

## Problem with traditional prompting

Most people still use Claude in a synchronous, single-shot way: give a prompt, Claude responds once, and you manually decide what to do next.[1]
This makes the human the bottleneck; your “meat suit” has to inspect results, think of next steps, and re-prompt, which limits how far the system can improve a solution.[1]
Karpathy’s Auto Research challenges this pattern by having agents continuously run experiments without you in the loop, finding improvements humans wouldn’t see.[1]

## Essence of Karpathy’s Auto Research

Karpathy’s loop gives Claude a clear objective (e.g., “speed up my website”), a metric, constraints, and then lets it run repeated experiments.[1]
The agent iteratively tweaks only the allowed artifact (e.g., a single config/file), measures performance, and keeps going every few minutes, building on prior results.[1]
Over 650 experiments in two days, the loop improved a website beyond what Karpathy had achieved manually, illustrating that continuous, autonomous optimization can surpass human tuning.[1]

## Loops now built into Claude (/loop and /goal)

Claude now has native loop features that operationalize this pattern: `/loop` to “wake Claude up” repeatedly, and `/goal` to work until a condition is met.[1]
The distilled pattern is: define an objective, a metric, boundaries of what can and cannot be changed, then let the loop run until the evaluator says the goal is reached.[1]
Practically, this means Claude keeps optimizing a task—content, code, systems—until you or your evaluator criteria tell it to stop, rather than just returning a single attempt.[1]

## Race simulator example: pure autonomous optimization

In the visual race simulator, Claude is set up as an “autonomous race engineer” with a goal: reduce median lap time from about 60 seconds to under 40 seconds.[1]
The loop prompt constrains Claude to change only `driver.js`, not the scoring or physics engine, enforcing a clean optimization boundary.[1]
Across four controlled experiment phases, the loop first worsens performance, then installs a predictive safety package, eventually dropping lap time by ~23 seconds and surpassing the sub-40-second goal without any human intervention during the run.[1]

## Newsletter loop example: evaluator cartridges

The newsletter loop uses `/goal` plus a “Claude prompt.md” to define a controlled improvement loop for a specific email draft.[1]
Three evaluator “cartridges” score each draft: a Humanify cartridge (voice/variety/predictability), a Hormozi-style marketing cartridge trained on public content, and an open-rate analytics engine using historical email data.[1]
The loop’s goal is a total score of at least 27 out of 30, with each cartridge scoring ≥8, plus structural constraints (≤150-word body, ≤45-character subject, one CTA, no spam phrases, stop after five attempts, save as draft only).[1]

## Results dynamics: iterative scoring and near-miss

The initial email is generic “AI slop,” scoring only 7.1/30 across the cartridges and showing cliched CTAs like “buy now” and “learn more.”[1]
Over five attempts, the loop dramatically improves the email: one attempt nearly triples the score, later attempts reach a best of ~26.8/30, with high Humanify and open-rate scores and a much more concise, personal style.[1]
Interestingly, the best attempt still falls just short of the 27/30 goal, illustrating that loops can converge very close but not always hit strict thresholds within bounded attempts.[1]

## Core design principles for Karpathy-style loops

The agent must only touch the artifact you intend to optimize (e.g., driver file, email draft) and never the scoring or evaluation logic.[1]
You define a clear, deterministic metric or composite score, plus guardrails and stopping rules (time/attempt limits, thresholds, structural constraints).[1]
Your role shifts from “prompter” to “system designer”: you architect objectives and cartridges so agents can run for long periods without you, working toward business goals while you do something else.[1]

## Practical implications for your work

Almost any business artifact can be looped: social content, websites, landing pages, products, and customer service flows can be continuously improved against custom evaluators.[1]
The value comes from building high-quality cartridges (e.g., style, marketing effectiveness, behavioral analytics) and wiring them into goal-based loops that you trust.[1]
The video positions this as the beginning of a larger shift where “autonomous swarms of AI agents” run research and optimization continuously, with humans mostly specifying goals and constraints.[1]

If you want, I can help you design a concrete `/goal` loop for one of your existing Claude Code projects—what artifact (code, prompts, emails, docs) would be most valuable for you to start looping first?  

## Human

Can we turn the content in the video into a reusable skill that can be used across a range  of use cases?

## Assistant

Yes — the video’s content can be distilled into a reusable **skill**, but not as a universal “prompt template.” The transferable part is a pattern: define a goal, define evaluators, constrain what can change, run iterative attempts, and stop only when a threshold or budget is reached.[1]

## Skill structure

A reusable skill from this video should encode five stable components: objective, mutable artifact, evaluator set, loop controller, and stop conditions.[1]
That is the core pattern shown both in the race example and the newsletter example: Claude gets a target, can only modify a bounded artifact, gets scored after each attempt, and keeps iterating until it either passes or exhausts limits.[1]
So the “skill” is less “make Claude act like Karpathy” and more “run bounded optimization loops against explicit metrics.”[1]

## What generalizes

The video shows the pattern working across at least two very different domains: code optimization in a race simulator and copy optimization for newsletters.[1]
It also explicitly claims the same structure can be applied to social content, websites, landing pages, products, and customer service workflows, which suggests the abstraction is domain-agnostic as long as you can define an evaluator.[1]
FACT: the common reusable elements are objective, metric, allowed changes, evaluator cartridges, and a capped iteration process.[1]

## What does not generalize

The weak point is evaluation quality. The video’s loop works because the system has deterministic or semi-structured evaluators, like lap-time thresholds or cartridge scores for “Humanify,” “Hormozi-style marketing,” and predicted open rate.[1]
If your use case lacks a credible evaluator, the loop can optimize toward noise, style over substance, or a proxy metric that looks good while degrading real outcomes.[1]
So a reusable skill is only as good as its scoring functions; that is the main failure mode and the main design burden.[1]

## Reusable spec

Here is the most reusable version of the skill, based directly on the video’s pattern.[1]

1. Define the **goal**: a measurable success condition, like “median lap under 40 seconds” or “total score at least 27/30.”[1]
2. Define the mutable artifact: the one file, draft, config, or asset the agent is allowed to change. In the race example, it could change `driver.js` but not the scoring or physics engine.[1]
3. Define evaluators: one or more scoring cartridges that return structured feedback and numeric scores. The newsletter example used three cartridges with per-cartridge minimums plus a total-score target.[1]
4. Define constraints: word count, subject length, one CTA, no spam phrases, save as draft only, maximum five attempts.[1]
5. Define stop logic: stop on success, budget exhaustion, regression, or max attempts. The video’s newsletter loop stopped after five attempts even though it narrowly missed the target.[1]

## Skill template

Below is a portable skill skeleton you could use across Claude Code, prompt libraries, or an internal agent framework:

```md
# Skill: bounded-optimization-loop

Purpose:
Run iterative improvement loops on a single bounded artifact until explicit evaluator thresholds are met or budgets are exhausted.

Inputs:
- objective: clear measurable target
- artifact: path or object allowed to change
- evaluators: list of scoring functions/cartridges
- constraints: forbidden changes, structural rules, budgets
- max_attempts: integer
- stop_conditions: thresholds, plateau, regression, timeout

Protocol:
1. Inspect current artifact and baseline score.
2. Propose one targeted improvement hypothesis.
3. Modify only the permitted artifact.
4. Run evaluators and capture structured results.
5. Compare against prior best.
6. Keep best-performing version.
7. Repeat until stop condition is met.

Hard rules:
- Never modify evaluator logic or scoring harness.
- Never optimize against unstated goals.
- Log each attempt with hypothesis, diff summary, scores, and outcome.
- Stop early on repeated regression or diminishing returns.
- Preserve best-known artifact even if later attempts are worse.

Outputs:
- best artifact
- attempt log
- score trajectory
- final decision: success / near miss / fail
```

This captures the strongest transferable ideas from the video without inheriting the marketing framing around it.[1]

## Use cases

A single skill like this can cover technical notes, prompt refinement, email outreach, landing pages, code tuning, and support macros, as long as each use case swaps in different evaluators.[1]
For example, technical YouTube notes could optimize for factual coverage, compression ratio, terminology accuracy, and actionability; Claude prompts could optimize for determinism, token efficiency, and pass rate on a benchmark set.[1]
CONSENSUS: the abstraction is reusable; SPECULATION with high confidence: the best implementation for your workflow is a small family of related skills built on one shared loop engine, not one monolithic skill for everything.[1]

The practical next step is to define one canonical schema for evaluators and artifacts, then create domain packs on top of it: `loop-core`, `loop-notes`, `loop-prompts`, `loop-outreach`.[1]
Would you like me to draft that as an actual Claude Code skill file set, with folder structure, frontmatter, evaluator interfaces, and 3 concrete variants?
