---
title: "Anthropics Official Skills (anthropics/skills"
date: "2026-01-13"
mode: "COPILOT"
uuid: "ffe0d47e-9e28-400f-bd70-82f0fed3dfe9"
entry_count: 1
---

## Human

Anthropics Official Skills (anthropics/skills

## Assistant

Anthropic’s official skills live in the public `anthropics/skills` GitHub repository, which is the canonical reference for how to structure, document, and distribute Claude Skills.[1]

## Repo location and purpose

- The official repository is `https://github.com/anthropics/skills` and is maintained by Anthropic.[2][1]
- It contains example skills that demonstrate Claude’s skills system across creative, technical, and enterprise workflows, plus the formal Agent Skills spec and a template.[1]

## How skills are structured

- Each skill is a folder with a `SKILL.md` file that defines the **name**, **description**, and the instructions/metadata Claude uses when loading that skill.[3][1]
- The repo is organized into `./skills` (example skills), `./spec` (the Agent Skills specification), and `./template` (starter structure for new skills).[1]

## Using official skills in Claude Code

- In Claude Code you can add this repo as a plugin “marketplace” via:  
  `/plugin marketplace add anthropics/skills`.[1]
- After that, you can browse and install specific skill sets (for example, `document-skills` or `example-skills`) from the plugin UI.[1]

## When to reference this repo for your own skills

- It provides canonical patterns for **SKILL.md metadata**, multi-file skill layouts, and how to package scripts/resources alongside instructions.[3][1]
- For designing your `/qa` and other custom workflows, it is a good baseline for naming, descriptions, and how much procedural detail to include so Claude can reliably invoke and execute skills.[4][1]
