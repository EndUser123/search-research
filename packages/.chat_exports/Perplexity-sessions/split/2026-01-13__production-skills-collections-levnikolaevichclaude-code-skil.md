---
title: "Production Skills Collections (levnikolaevich/claude-code-skills"
date: "2026-01-13"
mode: "COPILOT"
uuid: "ccf5fbbd-496d-4165-8afe-67ba2a2acac1"
entry_count: 1
---

## Human

Production Skills Collections (levnikolaevich/claude-code-skills

## Assistant

Production Skills Collections refers to the open-source GitHub repository `levnikolaevich/claude-code-skills`, which is a large, opinionated set of Claude Code skills designed to automate a full Agile-style software delivery workflow.[1]

## What this collection is

- The repo contains **dozens of production-ready skills** (the README currently advertises 80+), each packaged as a Claude Code Skill folder with SKILL metadata and supporting templates.[1]
- The skills cover the entire development lifecycle: epic/story planning, task coordination, implementation support, testing/QA, code quality checks, dependency upgrades, and infrastructure generation.[1]

## Example capabilities

- Planning and project management: skills like `ln-220-story-coordinator` and `ln-221-story-creator` take epics and generate INVEST-compliant stories, update Linear, and maintain a kanban board markdown.[1]
- Execution orchestration: coordinator skills such as `ln-300-task-coordinator` analyze a story, construct a task plan, and delegate to worker skills for creation or replanning.[1]
- Quality and maintenance: skills like `ln-501-code-quality-checker`, `ln-711-npm-upgrader`, `ln-712-nuget-upgrader`, and `ln-731-docker-generator` provide code-quality analysis, dependency upgrades, and generation of Docker/CICD scaffolding.[1]

## Structure and usage

- Each skill lives in a structured folder with `SKILL.md`, a Mermaid diagram HTML, and `references/` containing templates and guides, aligning with current Claude Code skill best practices.[2][1]
- The repo README includes quick-start examples that show how to invoke skills (e.g., `ln-100-documents-pipeline`, `ln-220-story-coordinator`, `ln-330-story-executor`) from Claude Code to drive documentation, epic decomposition, and story execution.[1]

## Why it’s useful to you

- It provides a **canonical “production-grade” pattern** for multi-skill orchestration: coordinators vs workers, shared templates, and visual workflow docs, which lines up well with your /qa v2-style architecture.[1]
- You can:
  - Copy the folder structure and SKILL metadata style for your own skills.[1]
  - Lift specific ideas (e.g., story/task coordinators, quality-gate skills) into your ecosystem.[1]
  - Study how it wires Linear and Agile concepts into Claude Code skills as a reference for your own integrations.[1]

If you want, the next step could be: map your existing `/qa` and related skills into this coordinator/worker pattern and define where in your pipeline skills like `ln-501`-style checkers or `ln-731`-style generators would sit.
