---
title: "Extract key takeaways"
date: "2026-06-17"
mode: "COPILOT"
uuid: "49af2b86-2477-46c6-875e-9eaf549dd788"
entry_count: 2
---

## Human

Extract key takeaways

## Assistant

Microsoft’s SkillOpt paper shows that you can dramatically boost an agent’s task accuracy by iteratively editing a small **skills** document instead of retraining the underlying model, but it mainly works for tasks with clear right/wrong answers and is not a complete solution for open‑ended reasoning or creativity yet.[1]

## Core idea

- Instead of finetuning, you keep the base model fixed and optimize a skills doc: a small text file that describes how the agent should behave, what steps to follow, how to use tools, and how to format answers (effectively an SOP for the agent).[1]
- Microsoft’s SkillOpt system uses a second, smarter AI to watch the agent’s performance on tasks, identify where it fails or succeeds, and propose small edits to this skills doc over time.[1]

## How SkillOpt works

- The supervising AI suggests micro‑changes such as adding or deleting a rule, or sharpening a vague instruction in the skills doc.[1]
- New doc variants are tested; if performance improves, that version is kept, and if not, it is discarded and the failure is remembered, so the agent gradually improves from its own mistakes.[1]

## Reported gains

- Across 52 different model–task combinations, SkillOpt outperformed the baseline in every case, according to the video’s description of the paper.[1]
- On GPT 5.5, spreadsheet accuracy reportedly increased from 41% to 80%, and document tasks from 33% to 72%, often with only 1–4 edits to the skills doc.[1]

## Scope and limitations

- This approach relies on tasks where there is a clear, objective correctness signal (spreadsheets, documents with deterministic answers, math, search), because the system needs a solid way to grade each attempt.[1]
- It does not extend well to creative or strategic tasks where there is no single right answer; even the paper acknowledges that limitation, so this is a powerful but partial view of “making AI better,” not the full picture.[1]

For your own systems work, do you want to dive into how to adapt this kind of skills‑doc optimization loop into your existing Claude Code plugins/skills framework?

## Human

yes

## Assistant

Here are the key takeaways from the video, focusing on the actual SkillOpt idea rather than the surrounding YouTube recommendations.[1]

## What SkillOpt is

- SkillOpt is a way to improve an AI agent by optimizing a **skills document** instead of retraining the model itself.[1]
- The skills doc acts like a playbook: it tells the model how to work, what steps to follow, and how to format outputs.[1]

## Why it matters

- The big win is that the model stays fixed while behavior improves, which is cheaper and faster than finetuning.[1]
- This is especially relevant for agent systems where the bottleneck is often instructions and workflow, not raw model capacity.[1]

## How it works

- A stronger supervising model watches the agent fail or succeed on tasks and then proposes small edits to the skills doc.[1]
- Those edits are tested, and only the variants that improve performance are kept.[1]

## Reported results

- The video says SkillOpt improved performance across many model-task pairs, including spreadsheet and document tasks.[1]
- It also claims large jumps in accuracy with only a few edits to the skills file, which suggests the approach can be very sample-efficient when the task is well-defined.[1]

## Limits to keep in mind

- This works best when there is an objective grading signal, such as math, spreadsheets, search, or other tasks with clear right and wrong answers.[1]
- It is much less convincing for open-ended creativity, strategy, or judgment-heavy work where “better” is subjective.[1]

## Why it is interesting for your work

- The most practical lesson is architectural: treat prompts, skills, and agent procedures as something you can continuously **tune** rather than static text.[1]
- That maps well to your Claude Code / skills / hook framework, where you could log failures, propose micro-edits, and automatically retest them against a benchmark set.[1]

A useful next step would be to turn this into a concrete optimization loop for your own skills framework: capture failures, generate candidate edits, score them, and promote only the winners.[1]
