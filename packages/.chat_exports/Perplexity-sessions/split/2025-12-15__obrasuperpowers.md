---
title: "obra/superpowers"
date: "2025-12-15"
mode: "COPILOT"
uuid: "7d0b9e5c-3a78-4e59-b6c7-64c6375e2d86"
entry_count: 1
---

## Human

obra/superpowers

## Assistant

obra/superpowers is a Claude Code skills library and plugin that turns Claude into a more systematic “senior dev” by enforcing structured workflows like brainstorming, planning, TDD, and verification before completion.[1][2]

## What obra/superpowers is

Superpowers is an open‑source repo by Jesse Vincent (“obra”) that defines a large set of Claude Code skills plus thin slash‑command wrappers such as `/superpowers:brainstorm`, `/superpowers:write-plan`, and `/superpowers:execute-plan`. It plugs into Claude Code’s first‑party Skills system so Claude can auto‑discover those skills in your workspace and treat them as mandatory workflows rather than optional suggestions.[3][4][1]

## How it gives Claude “superpowers”

The core idea is “if a skill exists for this task, Claude must use it,” which forces behaviors like test‑driven development, systematic debugging, and verification‑before‑completion instead of ad‑hoc coding. The library includes skills for collaboration (brainstorming, plan writing, executing plans, parallel subagents, structured code review) and for disciplined engineering patterns (TDD, root‑cause tracing, simplification, finishing branches, etc.).[5][2][1][3]

## Using it in Claude Code

You install the repo (or marketplace plugin) into your Claude Code project, often via the documented `.codex/INSTALL.md` or marketplace instructions, and then invoke commands like `/superpowers:brainstorm` or let automatic skill activation kick in when you start coding or debugging. Once installed, many users report it reduces meta‑prompting overhead and makes Claude feel more like a consistent development partner than a generic chatbot.[4][6][7][8][9][1]

## “Superpowers” vs generic prompting

Compared to writing long, custom prompts every time, Superpowers externalizes those patterns into reusable skills files that Claude reads and follows, giving you repeatable, auditable workflows. Blog posts and write‑ups describe using it to coordinate subagents, upgrade real projects (e.g., Next.js migrations), and maintain quality gates without constantly re‑explaining your process to the model.[2][8][10][1]
