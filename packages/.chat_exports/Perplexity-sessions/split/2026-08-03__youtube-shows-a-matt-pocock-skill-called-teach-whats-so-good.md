---
title: "YouTube shows a Matt pocock skill called teach.  What’s so good about it?"
date: "2026-08-03"
mode: "COPILOT"
uuid: "24550a02-fe7f-44b2-a38f-826049ab4f6d"
entry_count: 1
---

## Human

YouTube shows a Matt pocock skill called teach.  What’s so good about it?

## Assistant

Matt Pocock's `/teach` skill turns Claude Code into a stateful, personalized tutor rather than a one-off Q&A tool — it builds a persistent "teaching workspace" on your filesystem that remembers your progress and adapts future lessons accordingly.[1][2]

## Core mechanics

The skill is designed around a "mission" concept: it first captures *why* you want to learn something and *your* current skill level, then tailors everything to that goal rather than generating generic course content. It sources knowledge only from vetted, high-trust external resources rather than the model's own parametric memory, treating the model's built-in knowledge as untrusted and grounding every claim in a citation before it teaches it to you.[3][4][5]

## Why it's stateful (the key differentiator)

Most videos covering this skill single out statefulness as its standout feature — unlike a stateless tool that "forgets you the second the bell rings," `/teach` persists a whole workspace: the mission, gathered resources, numbered lessons, a learning record, and a glossary. This means each session picks up exactly where the last one left off, so lessons build on what you've already covered instead of repeating or restarting.[6][2][5][1]

## Lesson design

- Lessons are self-contained interactive HTML files (numbered like 0001-topic-name.html), not plain text, so they can embed diagrams, quizzes, callouts, and interactive practice elements.[4][6]
- It targets your "zone of proximal development" — keeping content challenging but not overwhelming based on tracked progress.[1][6]
- It follows a knowledge → skills → wisdom progression: pull vetted knowledge, build real hands-on practice, then push toward deeper judgment/application rather than passive reading.[2]
- A persistent glossary and cheat sheets accumulate in the workspace for quick reference in later sessions.[6]

## Practical use cases

Reviewers highlight it for learning goal-oriented projects (not just abstract technologies), codebase onboarding for new developers, and open-ended topics like languages or even solving a Rubik's cube. It's installed via `npx skills@latest add mattpocock/skills` as part of Pocock's broader open-source skills repo, which also includes tools like `grill-me`.[7][8][9][2][6]

Given your interest in Claude Code skill architecture and multi-agent design, the notable engineering choice here is `disable-model-invocation: true` in its frontmatter — meaning it's explicitly a user-triggered mode, not something the model invokes autonomously, plus its file-based state design mirrors patterns you'd likely want in your own epistemological-validation or knowledge-base systems.[4]
