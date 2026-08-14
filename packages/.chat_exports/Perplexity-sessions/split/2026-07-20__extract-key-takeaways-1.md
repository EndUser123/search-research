---
title: "Extract key takeaways"
date: "2026-07-20"
mode: "COPILOT"
uuid: "9105483f-2faf-4d42-9b88-9029b99a2cc1"
entry_count: 2
---

## Human

Extract key takeaways

## Assistant

Claude’s “compete mode” is a structured tournament pattern where multiple sub‑agents tackle the same task in isolation, then a blind judge selects and refines the best result; it produces noticeably better outputs for important, high‑leverage tasks but at a clear time and token cost tradeoff.[1]

## What “compete mode” actually is

- You run one main Claude Code agent as a **tournament controller**, not as the worker.[1]
- It spawns multiple sub‑agents (contestants) in parallel, all using the same model and brief, but with different roles or perspectives (e.g. operator, strategist, skeptic).[1]
- Each contestant works in isolation (no transcript sharing) to produce a full solution to the same task.[1]
- A separate blind judge agent then evaluates all contestants against explicit criteria and picks a winner, optionally with a scored ranking.[1]

## How they tested it

- Control: one Claude Code agent is explicitly told “do not create sub‑agents, variants, judges or critics” and just builds the Night Owl landing page end‑to‑end from the brief.[1]
- Tournament: a “tournament controller” prompt spins up three contestants with distinct personas (operator, strategist, skeptic), enforces isolation rules, then hands all outputs to a blind judge agent with scoring criteria.[1]
- The judge scores each page (A=91, B=93, C=92), declares a winner (the strategist), and provides feedback that can be used to further refine the winning page or merge in strengths from the others.[1]

## Observed quality differences

- The control page is “pretty decent” for a single one‑shot prompt: solid sales copy, basic visuals, but some awkward design choices (e.g. poor color contrast, slightly clunky interactions, more waffle‑y, text‑heavy sections).[1]
- The winning tournament page is clearly more polished: better color choices, more readable demo section, more interactive elements (e.g. playable call demo, calendar interaction), cleaner copy focused on what matters and less long, texty paragraphs.[1]
- The creator’s subjective verdict: the tournament page is “much better” and more honed, especially in visual design and brevity, though the score difference between contestants is small and the main impact is in the refinement loop after judging.[1]

## Tradeoffs and when to use it

- Running a competition takes **longer** and burns **more tokens** than a single‑agent one‑shot.[1]
- It’s recommended only for tasks that are “really meaningful for your work” where the incremental quality gain justifies extra cost and latency (e.g. key sales pages, major product copy, important system prompts).[1]
- As models improve, the marginal benefit of tournament prompting may shrink, but it remains a useful strategy for high‑stakes problems where small quality differences matter.[1]

## How it ranks vs other strategies

- The creator rates this strategy as impactful (about “90” on their internal scale) but explicitly says it’s weaker than:  
  - Omnipresent setups.[1]
  - Heavy context supercharging.[1]
  - Boris Cherny–style loop engineering, which they call “nowhere near as powerful” relative to tournament competition.[1]
- In their personal hierarchy, tournament competition sits roughly fourth behind those other Claude Code optimization strategies.[1]

If you want, I can sketch a Claude Code tournament controller prompt tailored to your own multi‑agent harness so you can test this on one of your production‑grade workflows rather than just landing pages.

## Human

Can we turn the content into a reusable skill that can be used across a range of use cases?

## Assistant

Yes — the content maps cleanly to a reusable **skill**, but it should be turned into a narrow orchestration skill, not a generic “make outputs better” skill. The reusable core is the tournament pattern: isolated parallel candidates, explicit judging criteria, and optional synthesis/refinement of the winner.[1]

## Reusable core

The video’s method is not really “website generation”; it is an orchestration pattern where one controller agent spawns multiple isolated workers, each solves the same task from a different angle, and a blind judge scores the results against criteria. That means the skill can generalize to prompts, code plans, architecture options, docs, landing pages, copy, and debugging strategies, as long as the task benefits from alternative approaches rather than a single deterministic answer.[1]

A good abstraction is: “For high-value tasks, generate \(N\) independent candidates, preserve isolation, evaluate with a rubric, then either return the winner or merge strengths into a final revision.” That is the part worth encoding into a reusable skill.[1]

## Where it fits

Best-fit use cases are tasks with subjective quality dimensions such as clarity, design, persuasion, maintainability, architecture tradeoffs, or solution elegance. The video’s own test used a landing page and found the tournament output more polished, less text-heavy, and more interactive, but also slower and more token-expensive.[1]

Poor-fit use cases are tasks with a single verifiable answer, simple transformations, or low-stakes work, because the video explicitly notes the method takes longer and costs more tokens, and recommends saving it for meaningful work. FACT: the speaker also ranks it below stronger strategies like heavy context, omnipresent setup, and loop-based methods, so it should be one tool in a stack rather than your default execution mode.[1]

## Skill design

I would define the skill around decision rules, role templates, and judge rubrics rather than around any one domain. The skill should contain: activation criteria; candidate role patterns such as builder, strategist, skeptic, operator, editor, verifier; isolation rules; a scoring rubric; and a final synthesis phase that either selects, patches, or merges outputs.[1]

A practical structure would look like this:

- Trigger when task value is high, evaluation is partly subjective, and at least two plausible solution shapes exist.[1]
- Default to 3 candidates, because the example used three isolated contestants and a judge; make \(N\) configurable but keep 3 as the safe baseline.[1]
- Require explicit evaluation criteria before spawning candidates, since the judge in the video used a defined rubric and returned scores for each candidate.[1]
- Support three exit modes: winner-only, winner-plus-fixes, or merged-final, which matches the video’s advice to optionally combine pieces like header/footer ideas and revise the champion using judge feedback.[1]

## Recommended template

A reusable skill prompt should read more like an operator manual than a one-off task prompt. Here is a compact version you can adapt:[1]

- Role: “You are a tournament controller. Do not solve the task directly unless entering final synthesis.”[1]
- Objective: “Produce the strongest final result for the task by running isolated parallel candidates and a blind evaluation.”[1]
- Candidate generation: “Spawn 3 candidates using the same base task, same constraints, and differentiated working styles: pragmatic builder, strategic optimizer, skeptical critic.”[1]
- Isolation: “Candidates must not see each other’s work, critiques, scores, or transcripts.”[1]
- Judging: “Blind-judge all outputs against a rubric: correctness, usefulness, constraint satisfaction, clarity, depth, and risk.”[1]
- Synthesis: “Return the winning candidate, key judge notes, and a revised final that incorporates only justified improvements.”[1]
- Guardrail: “Use tournament mode only when expected quality gain justifies extra latency and token cost.”[1]

## Important caveats

FACT: the evidence here is a single live demonstration plus the presenter’s judgment, not a broad benchmark across tasks, so the quality gain is plausible but not proven as universal. CONSENSUS: as an orchestration pattern, this is sound because independent exploration plus comparative evaluation usually improves results on ambiguous tasks, but the benefit depends heavily on rubric quality and candidate diversity.[1]

My recommendation is to package it as a reusable skill named something like `tournament-orchestrator` or `compete-mode`, with domain adapters for code, writing, design, and planning rather than one monolithic prompt. Confidence: high on reusability of the pattern, medium on universal payoff across workloads because the source explicitly highlights cost and situational usefulness.[1]

Concrete next step: I can draft the actual skill file in a Claude Code–style format with sections for triggers, candidate roles, rubrics, and per-domain variants for code, prompts, architecture, and documentation.[1]
